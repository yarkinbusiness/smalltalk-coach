"""T6b: fixes for two gaps in the T6 async grading state machine.

1. TOCTOU race in the idempotency guard -- POST .../end used to read the
   session's status and then, in a *separate* statement, write 'grading'.
   Two near-simultaneous requests (client double-tap, or a retry racing an
   in-flight request) could both observe 'active' and both dispatch a
   coordinator run + memory-store write for the same session. Fixed by
   making the active/failed -> grading transition a single atomic SQL
   compare-and-set (`db.mark_session_grading`, see its docstring).

2. No recovery from a stuck 'grading' state -- if the process dies between
   marking a session 'grading' and the background task finishing, that
   session is stuck forever (grading isn't retryable, only failed is).
   Fixed by a startup-time sweep (`db.recover_stale_grading_sessions`,
   wired into `main.py`'s `_startup`) that marks any session still
   'grading' at boot as 'failed' (safe to do -- if the process is only now
   starting, nothing in it can have a background task already running for
   that session).

This file has three tests:
  - test_mark_session_grading_is_atomic_under_concurrent_threads: a
    deterministic, db-level proof of (1) -- two real threads racing the
    same compare-and-set, no HTTP/timing luck involved.
  - test_concurrent_end_requests_only_dispatch_coordinator_once: an
    end-to-end proof of (1) over real HTTP against a real uvicorn server
    (same harness as test_end_session_async.py), with a barrier forcing a
    genuine overlap of two concurrent POST .../end calls for the same
    session, rather than hoping OS thread scheduling happens to race them.
  - test_stale_grading_session_recovered_at_fresh_app_startup_and_retryable:
    proof of (2) -- seeds a session directly into 'grading', then opens a
    *second*, independent TestClient lifecycle (a fresh app startup) against
    the same on-disk db file, standing in for a process restart.
"""

import copy
import json
import socket
import threading
import time

import httpx
import uvicorn

from app import db
from app.main import _STALE_GRADING_RECOVERY_MESSAGE
from fake_anthropic import agent_message_event, idle_event

# --- (1a) db-level atomicity, no HTTP/server involved -----------------------


def test_mark_session_grading_is_atomic_under_concurrent_threads(tmp_path, monkeypatch):
    """Proves db.mark_session_grading's active/failed -> grading transition
    is a genuine atomic compare-and-set under real concurrent access, not
    merely "correct when called once and reasoned about on paper".

    Two real OS threads, each with their own sqlite connection (opened
    fresh inside `db._conn()`, per the module's connection-per-call
    pattern) but pointed at the same on-disk db file, call
    `db.mark_session_grading` for the *same* session_id, released by a
    `threading.Barrier` so they hit the UPDATE as close to simultaneously as
    the OS scheduler allows. Under the old check-then-write implementation
    this would have been a real race with a real chance of both threads
    seeing 'active' and both winning. Under the fixed implementation,
    sqlite's single-writer semantics mean the two UPDATE statements cannot
    both match the WHERE clause regardless of interleaving -- whichever
    commits first flips the row out of ('active', 'failed'), so the other's
    UPDATE (evaluated against the now-current on-disk state) necessarily
    affects zero rows. This is a structural guarantee, not a probabilistic
    one -- but the barrier is still used here to make sure the two calls are
    actually contending for the same lock rather than trivially running
    one-after-another with no overlap at all.
    """
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "race_unit.sqlite3")
    db.init_db()
    db.create_practice_session("sess-race", "user-race", "coffee-shop-line")

    barrier = threading.Barrier(2)
    results: list[bool | None] = [None, None]
    errors: list[BaseException] = []

    def attempt(i: int) -> None:
        try:
            barrier.wait(timeout=5)
            results[i] = db.mark_session_grading("sess-race")
        except BaseException as exc:  # noqa: BLE001 - surface any thread failure to the test
            errors.append(exc)

    threads = [threading.Thread(target=attempt, args=(i,)) for i in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5)

    assert not errors, f"worker thread(s) raised: {errors}"
    # Exactly one thread won the compare-and-set (True) and exactly one lost
    # (False) -- never both True (double-dispatch) and never both False
    # (session stuck, nobody transitions it).
    assert sorted(results) == [False, True]

    row = db.get_practice_session("sess-race")
    assert row["status"] == "grading"
    assert row["report_error"] is None


def test_mark_session_grading_rejects_already_grading_or_ended(tmp_path, monkeypatch):
    """Sanity check on the WHERE clause itself: a session already in
    'grading' or 'ended' must not be re-armed by a second call -- only
    'active'/'failed' are valid starting states."""
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "race_unit2.sqlite3")
    db.init_db()

    db.create_practice_session("sess-ended", "user", "coffee-shop-line")
    db.mark_session_ended("sess-ended")
    assert db.mark_session_grading("sess-ended") is False

    db.create_practice_session("sess-grading", "user", "coffee-shop-line")
    assert db.mark_session_grading("sess-grading") is True  # active -> grading
    assert db.mark_session_grading("sess-grading") is False  # already grading


# --- (1b) end-to-end race over real HTTP, real uvicorn, real sockets --------
#
# Same rationale as test_end_session_async.py for why TestClient can't be
# used here: httpx's ASGITransport awaits the whole app call, BackgroundTasks
# included, before `.post()` returns, so two "concurrent" TestClient calls
# from two threads would never actually overlap inside the request handler.
# A real uvicorn server serving sync endpoints via Starlette's
# `run_in_threadpool` genuinely runs two in-flight requests concurrently.

_PROVISIONED_STATE = {
    "environment_id": "env-test",
    "partner_agent": {"id": "agent-partner", "version": 1, "hash": "h", "model": "claude-sonnet-5"},
    "warmth_worker": {"id": "agent-warmth", "version": 1, "hash": "h", "model": "claude-sonnet-5"},
    "curiosity_worker": {"id": "agent-curiosity", "version": 1, "hash": "h", "model": "claude-sonnet-5"},
    "reciprocity_worker": {
        "id": "agent-reciprocity",
        "version": 1,
        "hash": "h",
        "model": "claude-sonnet-5",
    },
    "flow_worker": {"id": "agent-flow", "version": 1, "hash": "h", "model": "claude-sonnet-5"},
    "coach_coordinator": {
        "id": "agent-coordinator",
        "version": 1,
        "hash": "h",
        "model": "claude-fable-5",
    },
}


def _free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class _LiveServer:
    """Runs the real `app.main.app` on a real uvicorn server (real TCP
    socket, real event loop, real background thread) -- duplicated from
    test_end_session_async.py's `_LiveServer` rather than imported, matching
    that file's own stated reasoning for not depending on another test
    module's import mechanics."""

    def __init__(self, tmp_path, fake_client):
        import app.db as db_module
        from app.main import app as fastapi_app
        from app.main import get_anthropic_client, get_provisioned_state

        self._db_module = db_module
        self._fastapi_app = fastapi_app
        self.fake_client = fake_client
        self.provisioned_state = copy.deepcopy(_PROVISIONED_STATE)

        self._original_db_path = db_module.DB_PATH
        db_module.DB_PATH = tmp_path / "race_http.sqlite3"

        fastapi_app.dependency_overrides[get_anthropic_client] = lambda: self.fake_client
        fastapi_app.dependency_overrides[get_provisioned_state] = lambda: self.provisioned_state

        self.port = _free_port()
        config = uvicorn.Config(fastapi_app, host="127.0.0.1", port=self.port, log_level="warning")
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(target=self.server.run, daemon=True)

    def __enter__(self):
        self.thread.start()
        deadline = time.monotonic() + 5
        while not self.server.started and time.monotonic() < deadline:
            time.sleep(0.01)
        assert self.server.started, "uvicorn server never started within 5s"
        self.client = httpx.Client(base_url=f"http://127.0.0.1:{self.port}", timeout=10.0)
        return self

    def __exit__(self, *exc_info):
        self.client.close()
        self.server.should_exit = True
        self.thread.join(timeout=5)
        self._fastapi_app.dependency_overrides.clear()
        self._db_module.DB_PATH = self._original_db_path


def test_concurrent_end_requests_only_dispatch_coordinator_once(tmp_path, monkeypatch, fake_client):
    """The actual race this whole fix is about: two near-simultaneous POST
    .../end calls for the *same* session must result in exactly one
    coordinator session-create call and exactly one memory-store write --
    never two.

    To make the race deterministic rather than hoping two threads happen to
    be scheduled closely enough together, `memory.ensure_user_memory_store`
    (called synchronously inside the route, just before the atomic
    compare-and-set) is wrapped so each call blocks on a two-party
    `threading.Barrier` before proceeding. Both concurrent requests reach
    this point *before* either has attempted the compare-and-set (neither
    has 409'd yet, since neither has transitioned the session out of
    'active'), so releasing the barrier guarantees both requests attempt
    `db.mark_session_grading` at essentially the same instant -- a real,
    forced overlap, not a probabilistic one.
    """
    import app.memory as memory_module

    with _LiveServer(tmp_path, fake_client) as live:
        start_resp = live.client.post(
            "/practice/sessions",
            json={"user_id": "race-user", "scenario_id": "coffee-shop-line"},
        )
        assert start_resp.status_code == 200
        session_id = start_resp.json()["session_id"]

        for text in ["hi", "how's it going", "nice to meet you"]:
            resp = live.client.post(f"/practice/sessions/{session_id}/message", json={"text": text})
            assert resp.status_code == 200

        # Only gate `ensure_user_memory_store` *after* setup -- start_practice
        # above also calls it once (to bootstrap the user's memory store),
        # and that single call has no second party to rendezvous with at a
        # 2-party barrier. The gate needs to be in place only for the two
        # concurrent POST .../end calls below.
        barrier = threading.Barrier(2, timeout=5)
        original_ensure = memory_module.ensure_user_memory_store

        def gated_ensure(client, user_id):
            barrier.wait()
            return original_ensure(client, user_id)

        monkeypatch.setattr(memory_module, "ensure_user_memory_store", gated_ensure)

        report_payload = {"scores": {"warmth": 4}, "focus_areas": ["Ask a follow-up"]}
        live.fake_client.queue_session_events(
            [agent_message_event(json.dumps(report_payload)), idle_event()]
        )

        responses: list[httpx.Response | None] = [None, None]
        errors: list[BaseException] = []

        def call_end(i: int) -> None:
            try:
                responses[i] = live.client.post(f"/practice/sessions/{session_id}/end")
            except BaseException as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [threading.Thread(target=call_end, args=(i,)) for i in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert not errors, f"request thread(s) raised: {errors}"
        statuses = sorted(r.status_code for r in responses)
        # Exactly one request won the race (202, dispatched to grading) and
        # exactly one lost it (409, told to poll the report) -- never 202
        # twice, which is exactly the bug this fix closes.
        assert statuses == [202, 409], (
            f"expected exactly one 202 and one 409, got {[r.status_code for r in responses]}"
        )

        loser = next(r for r in responses if r.status_code == 409)
        assert loser.json()["detail"]["report_url"] == f"/practice/sessions/{session_id}/report"

        # Let the winner's background grading run finish.
        deadline = time.monotonic() + 5
        final_body = None
        while time.monotonic() < deadline:
            final_body = live.client.get(
                f"/practice/sessions/{session_id}/report", params={"user_id": "race-user"}
            ).json()
            if final_body["status"] != "grading":
                break
            time.sleep(0.02)

        assert final_body["status"] == "ready"
        assert final_body["report"]["scores"] == {"warmth": 4}

        # The crux: only ONE coordinator session and ONE memory-store write,
        # no matter that two requests raced for the same session_id.
        assert len(live.fake_client.sessions_create_calls) == 1
        assert len(live.fake_client.memories_create_calls) == 1


# --- (2) stale 'grading' recovery at startup --------------------------------


def test_stale_grading_session_recovered_at_fresh_app_startup_and_retryable(tmp_path, monkeypatch):
    """Simulates a process crash: a session is forced straight into
    'grading' (standing in for a first POST .../end whose background task
    was dispatched, then the process died before that task finished -- no
    background task for it exists anywhere anymore). A *second*, independent
    TestClient lifecycle against the same on-disk db file stands in for the
    process restarting: FastAPI's startup event re-runs from scratch,
    including the new `db.recover_stale_grading_sessions` sweep.

    Proves: (a) the stuck session is swept to 'failed' with a safe,
    retryable message by the time the new process's startup completes, and
    (b) a subsequent POST .../end on it is accepted (not 409'd) and can
    succeed, exactly like any other failed -> grading retry.
    """
    import app.db as db_module
    from app.main import app as fastapi_app
    from app.main import get_anthropic_client, get_provisioned_state
    from fastapi.testclient import TestClient

    from fake_anthropic import FakeAnthropic

    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "recovery.sqlite3")

    # --- "process 1": starts a session, sends turns, then "crashes" mid-grade.
    fake1 = FakeAnthropic()
    state1 = copy.deepcopy(_PROVISIONED_STATE)
    fastapi_app.dependency_overrides[get_anthropic_client] = lambda: fake1
    fastapi_app.dependency_overrides[get_provisioned_state] = lambda: state1

    with TestClient(fastapi_app) as client1:
        start_resp = client1.post(
            "/practice/sessions",
            json={"user_id": "stuck-user", "scenario_id": "coffee-shop-line"},
        )
        assert start_resp.status_code == 200
        session_id = start_resp.json()["session_id"]

        for i in range(3):
            fake1.queue_message_stream(["ok"])
            resp = client1.post(
                f"/practice/sessions/{session_id}/message", json={"text": f"turn {i}"}
            )
            assert resp.status_code == 200

        # Simulate: a first POST .../end ran `db.mark_session_grading` and
        # dispatched a background task, then the process died before that
        # task ever reached `mark_session_ended`/`mark_session_failed`. We
        # force the state directly rather than going through a real /end +
        # killing a background task mid-flight, since there is no clean way
        # to kill a real BackgroundTask from inside a test -- the *end state*
        # (a row stuck in 'grading' with nothing running for it) is
        # identical either way, which is exactly what the recovery sweep is
        # built to detect and fix, regardless of how the row got there.
        assert db.mark_session_grading(session_id) is True
        row = db.get_practice_session(session_id)
        assert row["status"] == "grading"

    fastapi_app.dependency_overrides.clear()

    # --- "process 2": a fresh app startup pointed at the same db file.
    fake2 = FakeAnthropic()
    state2 = copy.deepcopy(_PROVISIONED_STATE)
    fastapi_app.dependency_overrides[get_anthropic_client] = lambda: fake2
    fastapi_app.dependency_overrides[get_provisioned_state] = lambda: state2

    try:
        with TestClient(fastapi_app) as client2:
            # The startup sweep already ran by the time TestClient's __enter__
            # returns (FastAPI's startup event fires during ASGI lifespan
            # startup, before any request can be served).
            row = db.get_practice_session(session_id)
            assert row["status"] == "failed"
            assert row["report_error"] == _STALE_GRADING_RECOVERY_MESSAGE

            report_resp = client2.get(
                f"/practice/sessions/{session_id}/report", params={"user_id": "stuck-user"}
            )
            assert report_resp.status_code == 200
            body = report_resp.json()
            assert body["status"] == "failed"
            assert body["error"] == _STALE_GRADING_RECOVERY_MESSAGE

            # And it's retryable: a fresh POST .../end must be accepted (not
            # 409'd) and can succeed, exactly like any other failed -> grading
            # retry.
            report_payload = {"scores": {"warmth": 5}, "focus_areas": ["Keep it up"]}
            fake2.queue_session_events(
                [agent_message_event(json.dumps(report_payload)), idle_event()]
            )
            retry = client2.post(f"/practice/sessions/{session_id}/end")
            assert retry.status_code == 202
            assert retry.json() == {"status": "grading"}

            row_after_retry = db.get_practice_session(session_id)
            assert row_after_retry["status"] == "ended"
            assert row_after_retry["report_error"] is None

            report_resp2 = client2.get(
                f"/practice/sessions/{session_id}/report", params={"user_id": "stuck-user"}
            )
            body2 = report_resp2.json()
            assert body2["status"] == "ready"
            assert body2["report"]["scores"] == {"warmth": 5}
    finally:
        fastapi_app.dependency_overrides.clear()


def test_recover_stale_grading_sessions_only_touches_grading_rows(tmp_path, monkeypatch):
    """Narrower db-level check on the sweep's WHERE clause: 'active',
    'ended', and 'failed' sessions must be left completely alone -- only
    'grading' rows are recovered."""
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "sweep_scope.sqlite3")
    db.init_db()

    db.create_practice_session("s-active", "u", "coffee-shop-line")

    db.create_practice_session("s-ended", "u", "coffee-shop-line")
    db.mark_session_ended("s-ended")

    db.create_practice_session("s-failed", "u", "coffee-shop-line")
    db.mark_session_failed("s-failed", "some earlier failure")

    db.create_practice_session("s-grading", "u", "coffee-shop-line")
    db.mark_session_grading("s-grading")

    recovered = db.recover_stale_grading_sessions("swept: server restarted")

    assert recovered == 1
    assert db.get_practice_session("s-active")["status"] == "active"
    assert db.get_practice_session("s-ended")["status"] == "ended"
    failed_row = db.get_practice_session("s-failed")
    assert failed_row["status"] == "failed"
    assert failed_row["report_error"] == "some earlier failure"  # untouched, not overwritten
    swept_row = db.get_practice_session("s-grading")
    assert swept_row["status"] == "failed"
    assert swept_row["report_error"] == "swept: server restarted"
