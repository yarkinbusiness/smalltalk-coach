import json
import logging
import uuid
from functools import lru_cache

from anthropic import Anthropic
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from app import coach, db, memory
from app.config import load_provisioned
from app.partner import generate_opening_line, stream_partner_reply
from app.progress import build_progress_summary
from app.recommend import recommend_next_scenario
from app.scenarios import SCENARIOS, SCENARIOS_BY_ID
from app.schemas import (
    CoachReport,
    EndPracticeResponse,
    OnboardingRequest,
    OnboardingResponse,
    ProgressSummaryResponse,
    RecommendationResponse,
    ReportStatusResponse,
    SendMessageRequest,
    SessionDetailResponse,
    StartPracticeRequest,
    StartPracticeResponse,
)

logger = logging.getLogger(__name__)

app = FastAPI(title="SmallTalkCoach backend")

# A genuinely tiny conversation (e.g. one "hey") isn't worth spinning up a
# full CMA coach_coordinator session over -- POST .../end 422s below this.
MIN_USER_TURNS_TO_GRADE = 3

# Session states that already have a grading run in flight or completed --
# a second POST .../end on either is rejected (409) rather than re-running
# the coordinator and re-writing the saved report / memory-store entry a
# second time. `failed` is deliberately *not* in this set: retrying from a
# failed attempt is the whole point of that state.
_ALREADY_GRADING_OR_DONE = {"grading", "ended"}

# Maps the session's `status` column (db.py's state machine) to the
# `status` field GET .../report actually exposes to the client -- "ended"
# reads as "ready" there, since that's the meaningful thing for a polling
# client (a report is ready to fetch), not an implementation detail of how
# db.py names the terminal-success state.
_SESSION_STATUS_TO_REPORT_STATUS = {
    "active": "active",
    "grading": "grading",
    "ended": "ready",
    "failed": "failed",
}


# --- Injectable singletons -------------------------------------------------
#
# `client` (the Anthropic SDK instance) and `STATE` (provisioned agent
# ids/versions from .provisioned.json) used to be created at *module import
# time*, which made the app impossible to import — let alone test — without
# a real ANTHROPIC_API_KEY and a real .provisioned.json on disk.
#
# They're now FastAPI dependency functions instead. Each is `@lru_cache`d so
# it still behaves like a singleton: the underlying Anthropic()/
# load_provisioned() call happens exactly once per process, on first
# resolution, and every route depends on it via `Depends(...)`. Tests can
# swap either one out per-app via `app.dependency_overrides[...]`.
#
# `_startup()` below resolves both eagerly (honoring any overrides) so that
# a real deployment still fails fast at boot with the same errors as before
# if the key or the provisioned-state file is missing — misconfiguration is
# never silently deferred to the first incoming request.
@lru_cache
def get_anthropic_client() -> Anthropic:
    return Anthropic()


@lru_cache
def get_provisioned_state() -> dict:
    return load_provisioned()


## Client-safe message stamped onto any session recovered by the startup
# sweep below -- same rationale as `_safe_error_message`: short, safe to show
# a user, never leaks process/exception internals. Defined here (not in
# db.py) so db.py's `recover_stale_grading_sessions` stays purely mechanical
# (just the SQL), matching how `mark_session_failed` takes the message as a
# parameter rather than owning its wording.
_STALE_GRADING_RECOVERY_MESSAGE = (
    "Grading was interrupted by a server restart. You can retry."
)


@app.on_event("startup")
def _startup() -> None:
    db.init_db()
    # Any session still 'grading' at this exact moment -- before this
    # process has served a single request -- cannot have a background
    # grading task actually running for it in this process. It's either a
    # leftover from a previous process that died mid-grade (crash, restart,
    # deploy) or, at minimum, nothing in *this* process has dispatched a
    # coordinator run for it yet. Left alone, that session would be stuck
    # forever: 'grading' is deliberately not retryable (see
    # `db.mark_session_grading`'s WHERE clause), so POST .../end would 409
    # forever and GET .../report would report "grading" forever with
    # nothing actually working on it. Sweeping it to 'failed' here makes it
    # retryable again via the normal failed -> grading path.
    recovered = db.recover_stale_grading_sessions(_STALE_GRADING_RECOVERY_MESSAGE)
    if recovered:
        logger.warning(
            "Recovered %d session(s) stuck in 'grading' at startup (marked 'failed', retryable)",
            recovered,
        )
    # Resolve through dependency_overrides (if a test has set any) rather
    # than calling the module-level functions directly, so tests get their
    # fakes here too instead of the real Anthropic()/provisioned-file path
    # running during startup.
    app.dependency_overrides.get(get_anthropic_client, get_anthropic_client)()
    app.dependency_overrides.get(get_provisioned_state, get_provisioned_state)()


@app.get("/scenarios")
def list_scenarios():
    return SCENARIOS


@app.post("/users/{user_id}/bootstrap")
def bootstrap_user(user_id: str, client: Anthropic = Depends(get_anthropic_client)):
    memory_store_id = memory.ensure_user_memory_store(client, user_id)
    return {"user_id": user_id, "memory_store_id": memory_store_id}


@app.post("/users/{user_id}/onboarding", response_model=OnboardingResponse)
def onboard_user(
    user_id: str,
    req: OnboardingRequest | None = None,
    client: Anthropic = Depends(get_anthropic_client),
):
    """T14: called once, at the end of the iOS app's first-run
    `OnboardingView` (see ios/SmallTalkCoach/Views/OnboardingView.swift),
    right before the main `TabView` ever appears -- whether the user stated
    a struggle on the third screen or tapped "Skip".

    `req` is optional (defaults to `None`, not an empty-but-required body)
    so a bare `POST .../onboarding` with no JSON body at all -- the "Skip"
    case -- is valid rather than a 422 for a missing request body.

    Two things happen here, both safe to call more than once (matching
    every other route in this file that touches a user's memory store):

    1. `ensure_user_memory_store(...)` -- exactly the same idempotent call
       `bootstrap_user` above and `POST /practice/sessions` (lazily, on a
       user's first session) already make. Kept here too rather than
       relying on the client to also call `.../bootstrap` first, so
       onboarding is a single, self-contained network call from the iOS
       flow: one request, and the user's memory store is guaranteed to
       exist by the time it returns, regardless of which pick (if any) was
       made.
    2. If `req.struggle` is a stated pick (one of `memory.STRUGGLE_OPTIONS`,
       not the "Skip" case), record it into that same memory store via
       `memory.record_struggle_pick` -- the exact same
       `client.beta.memory_stores.memories.create(...)` mechanism
       `memory.record_session_summary` already uses to write a session's
       report, just a different `path`. An unrecognized `struggle` value is
       rejected with a 422 (the closed-set-of-known-values convention this
       app already uses for `scenario_id` -- see `start_practice` above --
       rather than silently normalizing or storing an arbitrary string.

    Skipping (`req` is `None`, or `req.struggle` is `None`) still runs step
    1 -- the memory store exists either way -- but never calls
    `record_struggle_pick`, so no bogus/empty struggle-pick memory is ever
    written for a user who tapped "Skip".
    """
    memory_store_id = memory.ensure_user_memory_store(client, user_id)

    struggle = req.struggle if req is not None else None
    struggle_recorded = False
    if struggle is not None:
        if struggle not in memory.STRUGGLE_OPTIONS:
            raise HTTPException(422, f"Unknown struggle option {struggle!r}")
        memory.record_struggle_pick(client, memory_store_id, user_id, struggle)
        struggle_recorded = True

    return OnboardingResponse(
        user_id=user_id,
        memory_store_id=memory_store_id,
        struggle_recorded=struggle_recorded,
    )


@app.post("/practice/sessions", response_model=StartPracticeResponse)
def start_practice(
    req: StartPracticeRequest,
    client: Anthropic = Depends(get_anthropic_client),
    state: dict = Depends(get_provisioned_state),
):
    scenario = SCENARIOS_BY_ID.get(req.scenario_id)
    if not scenario:
        raise HTTPException(404, f"Unknown scenario_id {req.scenario_id!r}")

    memory.ensure_user_memory_store(client, req.user_id)  # idempotent
    session_id = str(uuid.uuid4())
    db.create_practice_session(session_id, req.user_id, req.scenario_id)

    # T9: a `partner_opens` scenario (see scenarios.py) has the practice
    # partner speak first -- generated here, synchronously, before the 200
    # goes out, so the opening line is already persisted as the transcript's
    # first turn and handed back in the same response the client uses to
    # seed its chat view (see PracticeSessionViewModel.start()). Every other
    # scenario skips this block entirely: no Messages API call at session
    # start, `opening_message` stays None, and behavior is unchanged from
    # before this field existed.
    opening_message = None
    if scenario.get("partner_opens"):
        partner_model = state["partner_agent"]["model"]
        opening_message = generate_opening_line(client, partner_model, scenario)
        db.append_turn(session_id, "assistant", opening_message)

    return StartPracticeResponse(
        session_id=session_id, scenario=scenario, opening_message=opening_message
    )


@app.post("/practice/sessions/{session_id}/message")
def send_message(
    session_id: str,
    req: SendMessageRequest,
    client: Anthropic = Depends(get_anthropic_client),
    state: dict = Depends(get_provisioned_state),
):
    session_row = db.get_practice_session(session_id)
    if not session_row:
        raise HTTPException(404, "Unknown session_id")
    if session_row["status"] != "active":
        raise HTTPException(409, "Session already ended")

    scenario = SCENARIOS_BY_ID[session_row["scenario_id"]]
    db.append_turn(session_id, "user", req.text)

    def event_stream():
        full_reply = []
        try:
            transcript = db.get_transcript(session_id)
            partner_model = state["partner_agent"]["model"]
            for delta in stream_partner_reply(
                client, partner_model, scenario, transcript, session_row["user_id"]
            ):
                full_reply.append(delta)
                yield f"data: {json.dumps({'delta': delta})}\n\n"
            db.append_turn(session_id, "assistant", "".join(full_reply))
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as exc:  # noqa: BLE001 - deliberately broad, see docstring below
            # The partner-reply stream failed partway through (e.g. the
            # Messages API call errors mid-stream, after some `delta` events
            # were already flushed to the client above). Two things need to
            # happen so the client gets a real signal and a retry is safe:
            #
            #   1. Emit a final `error` event instead of just letting the
            #      exception kill the connection -- without this, the iOS
            #      client sees the SSE connection drop with no way to tell
            #      "the partner finished" from "something broke". A `done`
            #      event is deliberately NOT sent in this branch, so the
            #      client can distinguish success from failure by which
            #      terminal event it received.
            #   2. Roll back the dangling user turn appended above, before
            #      this generator ever started -- `full_reply` was never
            #      appended as an assistant turn (that line is skipped by
            #      the exception), so the transcript right now ends in a
            #      lone user turn with no matching reply. Removing it
            #      restores the transcript to exactly its pre-request
            #      state: the chosen "consistent" end-state is that a
            #      failed POST .../message leaves the transcript as if it
            #      had never been called at all, so a retry (same text)
            #      reproduces the normal single-user-turn-then-reply shape
            #      instead of ever producing two consecutive user turns.
            #
            # `except Exception` (not `except BaseException`) deliberately
            # does not catch `GeneratorExit` -- a client disconnecting mid-
            # stream should still close this generator normally rather than
            # being treated as a stream failure needing rollback/an error
            # event that can no longer reach anyone.
            logger.exception(
                "Partner reply stream failed for session %s", session_id
            )
            db.remove_last_turn(session_id)
            yield f"data: {json.dumps({'error': _safe_stream_error_message(exc)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _count_user_turns(transcript: list[dict]) -> int:
    return sum(1 for turn in transcript if turn["role"] == "user")


def _safe_error_message(exc: Exception) -> str:
    """A short, safe-to-expose hint for GET .../report's `error` field --
    deliberately just the exception's type name, never `str(exc)`/`repr(exc)`,
    which could carry request bodies, SDK internals, or other detail that
    shouldn't leak to the client. The full exception is logged server-side
    (see the `except` block in `_run_coaching_task`) for real debugging."""
    return f"Grading failed ({type(exc).__name__}). You can retry."


def _safe_stream_error_message(exc: Exception) -> str:
    """Same safe-hint philosophy as `_safe_error_message` above (short,
    exception-type-name only, never `str(exc)`/`repr(exc)`) but worded for
    POST .../message's SSE stream (see `event_stream`'s `except` block)
    rather than the grading pipeline -- kept as a separate function instead
    of reusing `_safe_error_message` since "Grading failed" would be a
    misleading message for a failure that has nothing to do with grading."""
    return f"Message failed ({type(exc).__name__}). You can retry."


def _run_coaching_task(
    client: Anthropic,
    session_id: str,
    coordinator_id: str,
    coordinator_version: int,
    environment_id: str,
    memory_store_id: str,
    transcript: list[dict],
) -> None:
    """The actual CMA coach_coordinator run — everything that used to happen
    inline inside the POST .../end request handler now happens here instead,
    scheduled via FastAPI `BackgroundTasks` so the request can return a 202
    immediately (see end_practice below) rather than holding the connection
    open for however long the coordinator's sandboxed session + 4-worker
    fan-out takes (potentially far past an iOS client's default 60s
    URLSession timeout).

    Never lets an exception escape: this runs after the HTTP response has
    already been sent, so an uncaught exception here wouldn't reach any
    client anyway -- it would just be swallowed by Starlette with nothing to
    show for it. Catching broadly and recording status='failed' (with a
    retryable, safe error hint) is strictly more useful than that silent
    failure.
    """
    try:
        raw_report = coach.run_coaching_session(
            client,
            coordinator_id=coordinator_id,
            coordinator_version=coordinator_version,
            environment_id=environment_id,
            memory_store_id=memory_store_id,
            transcript=transcript,
        )
        # The coordinator's output (already run through coach._extract_report
        # inside run_coaching_session) is a raw, untrusted dict — normalize_report
        # coerces it into something that reliably satisfies CoachReport (int
        # scores clamped 1-5, list[str] strengths/focus_areas, etc.) without
        # raising, and then constructing CoachReport(**report) explicitly is a
        # second line of defense: if normalize_report ever has a bug, pydantic's
        # own validation catches it here rather than an unvalidated dict being
        # saved as if it were a successful report.
        report = coach.normalize_report(raw_report)
        CoachReport(**report)

        # Only reached on full success -- a failure at any point above (the
        # coordinator call, normalization, or CoachReport validation) skips
        # all three of these and falls into the except block below instead,
        # so a partially-graded session is never saved/recorded as done.
        db.save_report(session_id, report)
        memory.record_session_summary(client, memory_store_id, session_id, report)
        db.mark_session_ended(session_id)
    except Exception as exc:  # noqa: BLE001 - deliberately broad, see docstring
        logger.exception("Coaching session %s failed during grading", session_id)
        db.mark_session_failed(session_id, _safe_error_message(exc))


@app.post(
    "/practice/sessions/{session_id}/end",
    response_model=EndPracticeResponse,
    status_code=202,
)
def end_practice(
    session_id: str,
    background_tasks: BackgroundTasks,
    client: Anthropic = Depends(get_anthropic_client),
    state: dict = Depends(get_provisioned_state),
):
    session_row = db.get_practice_session(session_id)
    if not session_row:
        raise HTTPException(404, "Unknown session_id")

    status = session_row["status"]
    if status in _ALREADY_GRADING_OR_DONE:
        raise HTTPException(
            409,
            {
                "message": f"Session is already {status}.",
                "report_url": f"/practice/sessions/{session_id}/report",
            },
        )

    transcript = db.get_transcript(session_id)
    user_turns = _count_user_turns(transcript)
    if user_turns < MIN_USER_TURNS_TO_GRADE:
        raise HTTPException(
            422,
            f"At least {MIN_USER_TURNS_TO_GRADE} user turns are required before ending a "
            f"session for coaching (got {user_turns}).",
        )

    # `status` here is 'active' or 'failed' (a retry) -- both are allowed to
    # (re)start grading. ensure_user_memory_store is cheap/idempotent (a
    # lookup, not a create, once the user's store already exists) so it's
    # fine to run synchronously here rather than inside the background task.
    memory_store_id = memory.ensure_user_memory_store(client, session_row["user_id"])

    # The status check above (`session_row["status"]`) and this write are
    # NOT one atomic operation -- session_row was read before this line, so
    # two near-simultaneous POST .../end requests for the same session_id
    # (a client double-tap, or a retry racing an in-flight request) can both
    # read 'active' above and both reach this point. db.mark_session_grading
    # is what actually closes that race: it's a single SQL
    # UPDATE ... WHERE id = ? AND status IN ('active', 'failed'), so sqlite
    # serializes the two calls and only one of them can flip the row to
    # 'grading' -- the other's UPDATE affects zero rows because by the time
    # it runs the status is no longer 'active'/'failed'. Whichever call gets
    # `False` back lost the race and must 409 exactly like the early
    # already-grading/already-ended check above, rather than proceeding to
    # dispatch a second coordinator run / second memory-store write for the
    # same session.
    won_race = db.mark_session_grading(session_id)
    if not won_race:
        raise HTTPException(
            409,
            {
                "message": "Session is already grading.",
                "report_url": f"/practice/sessions/{session_id}/report",
            },
        )
    background_tasks.add_task(
        _run_coaching_task,
        client,
        session_id,
        state["coach_coordinator"]["id"],
        state["coach_coordinator"]["version"],
        state["environment_id"],
        memory_store_id,
        transcript,
    )
    return EndPracticeResponse(status="grading")


@app.get("/practice/sessions/{session_id}/report", response_model=ReportStatusResponse)
def get_report(session_id: str, user_id: str):
    """GET .../report's coaching report (scores, focus_areas,
    drill_suggestion) is exactly as sensitive as the transcript/report
    GET /practice/sessions/{session_id} (see `get_session_detail`) already
    guards -- so it uses the identical ownership-guard pattern rather than
    inventing a second one: a required `user_id` query parameter that must
    match `session_row["user_id"]`, and a plain 404 (never a 403) for a
    session that exists but belongs to someone else, indistinguishable from
    an unknown session_id. See `get_session_detail`'s docstring for the full
    403-vs-404 reasoning -- it applies here verbatim.
    """
    session_row = db.get_practice_session(session_id)
    if not session_row or session_row["user_id"] != user_id:
        raise HTTPException(404, "Unknown session_id")

    status = session_row["status"]
    report_status = _SESSION_STATUS_TO_REPORT_STATUS[status]
    body: dict = {"status": report_status, "report": None}
    if report_status == "ready":
        body["report"] = db.get_report(session_id)
    elif report_status == "failed":
        body["error"] = session_row["report_error"]
    return ReportStatusResponse(**body)


@app.get("/practice/sessions/{session_id}", response_model=SessionDetailResponse)
def get_session_detail(session_id: str, user_id: str):
    """T12: full transcript + scenario + report for the iOS session-detail /
    replay screen -- the conversation that produced a given coaching report
    was previously stored in sqlite (practice_sessions.transcript_json) and
    never exposed to the client at all; this is the first endpoint that
    hands it back.

    Access control: this app has no real auth (see README/ARCHITECTURE.md).
    `user_id` is a required query parameter that must match
    `session_row["user_id"]` -- the same "a matching user_id is the closest
    thing to access control that exists" convention every other user-scoped
    route here already relies on (e.g. GET /users/{user_id}/progress trusts
    whatever user_id is in its URL). The difference here is that
    `session_id` alone -- unlike a user_id-scoped path -- doesn't already
    imply ownership the way `/users/{user_id}/...` does, so this route has
    to check it explicitly instead of getting it for free from the URL
    shape.

    404, not 403, for a session that exists but belongs to someone else:
    returning 403 would *confirm* session_id is a real, valid session just
    owned by someone else -- a session-id enumeration/probing leak this app
    has no reason to offer given it has no real auth to begin with. Folding
    the "wrong owner" case into the same 404 as "no such session_id" makes
    the two indistinguishable from the outside, which is the strictly safer
    default. Same reasoning shapes the 404 body: a plain, generic string
    detail, never the transcript or report -- so a wrong-user_id probe can't
    scrape data out of the error response either.
    """
    session_row = db.get_practice_session(session_id)
    if not session_row or session_row["user_id"] != user_id:
        raise HTTPException(404, "Unknown session_id")

    return SessionDetailResponse(
        transcript=db.get_transcript(session_id),
        scenario=SCENARIOS_BY_ID[session_row["scenario_id"]],
        report=db.get_report(session_id),
    )


@app.get("/users/{user_id}/progress")
def get_progress(user_id: str):
    return db.get_progress(user_id)


@app.get("/users/{user_id}/progress/summary", response_model=ProgressSummaryResponse)
def get_progress_summary(user_id: str):
    """T11: per-dimension score trend + summary stats behind the iOS
    progress screen's new chart header (see ProgressListView.swift /
    ProgressViewModel.swift). Reuses db.get_progress exactly like
    GET .../recommendation does below -- no new db.py query needed. See
    progress.build_progress_summary for the actual derivation:
    chronological ordering, parse_error exclusion, the per-dimension "gap"
    representation, and how current_focus_area is shared with
    recommend.py so this screen and GET .../recommendation never disagree
    about the user's current weak spot."""
    return build_progress_summary(db.get_progress(user_id))


@app.get("/users/{user_id}/recommendation", response_model=RecommendationResponse)
def get_recommendation(user_id: str):
    """T10: "what should I practice next?" -- see recommend.py's
    `recommend_next_scenario` docstring for the full algorithm. Reuses
    db.get_progress (no new db.py query function needed) since it already
    returns exactly what the algorithm needs per session: scenario_id,
    created_at, and the report itself."""
    return recommend_next_scenario(db.get_progress(user_id))
