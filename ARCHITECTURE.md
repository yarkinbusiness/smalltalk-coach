# SmallTalkCoach — Architecture

**Implemented v1 status (2026-07-21):** this document now leads with the
architecture that exists on `master`. The detailed coaching contract is
`docs/planning/COACHING_PIPELINE_V1.md`; curriculum contracts are
`docs/planning/CONTENT_MODEL_V1.md` and `docs/planning/LESSON_PATH_V1.md`.
`PROGRESS.md` and `DECISIONS.md` are authoritative for live status and locked
decisions.

## Implemented v1 at a glance

- **Backend:** FastAPI served locally on port 8000, with SQLite persistence
  and `GET /health` for service/configuration status.
- **iOS client:** SwiftUI, using `http://127.0.0.1:8000` by default, verified
  on an iPhone 16 simulator running iOS 18.2.
- **Product surfaces:** Home provides the curriculum, daily habit, skill
  profile, reflection, and review loop; AI Coaching accepts real-conversation
  text or screenshots and returns coaching plus a lesson recommendation.
- **Model boundary:** Claude Haiku 4.5 through the plain Anthropic Messages
  API. V1 provisions no CMA agents, workers, coordinator, session,
  environment, sandbox, or memory store.
- **Storage boundary:** normalized transcripts, validated reports, curriculum
  progress, streak/review data, profile aggregates, and reflections are stored
  in SQLite. Raw screenshot bytes and image metadata are not persisted.

## Implemented coaching pipeline, v1

The coaching flow is implemented under `/coaching` and tracked by
`docs/planning/COACHING_PIPELINE_V1.md`:

```text
User pastes conversation text or uploads one chat screenshot
        │
        ▼
User identifies their own side when needed
        │
        ▼
User explicitly consents to third-party AI processing
        │
        ▼
Input normalization
  - text: normalized locally
  - screenshot: one bounded Haiku vision-extraction call
        │
        ▼
One bounded Haiku structured-diagnosis call
  - with_user_reply: score warmth/curiosity/reciprocity/flow
  - stimulus_only: teach response construction without scoring the sender
        │
        ▼
Strict backend validation and safety handling
        │
        ▼
Deterministic routing selects the relevant curriculum lesson
        │
        ▼
SQLite persistence and response assembly
        │
        ▼
iOS renders interpretation, guidance, examples, transferable takeaway,
practice action, and lesson recommendation
```

This is a **single-model, Haiku-only, no-CMA design**. Pasted text uses one
model call for diagnosis. Screenshots use two bounded calls to the same Haiku
model family: vision extraction, then diagnosis. The model never chooses a
lesson, writes directly to storage, or owns user progress.

### Request behavior

- `POST /coaching/diagnoses` accepts exactly one source: pasted text or a PNG,
  JPEG, or WebP screenshot.
- Text diagnosis is synchronous and returns the completed report after one
  bounded diagnosis call.
- Screenshot diagnosis is asynchronous: the API returns a job for polling
  while vision extraction and diagnosis run outside the request lifecycle.
- Consent failure, invalid attribution, unreadable input, malformed model
  output, and safety escalation fail closed; partial coaching is not stored.
- Reports can be read and deleted individually. Raw screenshots are disposed
  after processing and are never written to SQLite.

### Responsibility boundaries

- **SwiftUI app:** input selection, screenshot-side marking, consent UI,
  request/polling state, report rendering, lesson navigation, and local
  notification scheduling.
- **FastAPI application:** input validation, job lifecycle, model adapters,
  schema validation, safety behavior, deterministic lesson routing, API
  response assembly, and persistence orchestration.
- **Claude Haiku 4.5:** screenshot-to-transcript extraction and structured
  coaching only.
- **SQLite:** curriculum completion, coaching reports, streak/review state,
  profile aggregates, and reflections.
- **Static JSON content:** lesson definitions, ordering, prerequisites, and
  dimension-to-lesson routing.

## Local runtime and verification baseline

Run the backend from the repository root with:

```sh
backend/.venv/bin/python -m uvicorn backend.app.main:app --reload --port 8000
```

The iOS app defaults to `http://127.0.0.1:8000`. Its documented simulator
target is `platform=iOS Simulator,name=iPhone 16,OS=18.2`.

# Historical — superseded five-scenario/four-worker CMA design

Everything below this heading preserves the pre-restart architecture and the
2026-07-16 CMA-based v1 proposal for decision history. It does **not** describe
the implemented v1. The Phase 0 tree was removed in the 2026-07-18 Full
Restart and remains available at tag `phase0-archive`; the CMA design is only
a possible future upgrade path.

## Product shape, v1

Two tabs:

1. **Home — the structured learning path.** A fixed, Duolingo-style
   curriculum: sequential lessons that take a user from basic to advanced
   skill in approaching people, starting conversations, and related social
   skills. Each topic pairs learning material with a test/quiz before a
   user advances. **This is the primary experience** — the thing a user
   opens the app to do most days, and the thing a daily streak is anchored
   on.
2. **AI Coaching — a utility tool, not the main experience.** Three things
   live here, in priority order:
   - **Screenshot diagnosis** (primary use of this tab). The user imports a
     screenshot of a real conversation. The backend extracts a clean
     transcript, diagnoses it with the same 4-dimension grading engine used
     elsewhere in this document, and returns feedback explaining what went
     wrong — paired with a pointer back into the Home tab's learning path:
     "this is your reciprocity dimension again — go do the reciprocity
     lesson, then come back."
   - **Talk with the coach** (optional, secondary). A conversational
     interface to the coaching assistant itself, distinct from roleplaying
     a persona. Not yet scoped — see "Deferred" below.
   - **Daily practice** (optional, secondary). The roleplay-against-a-
     persona chat that was the entire app in the previous version of this
     document. Still built, still works, but is no longer the primary loop
     a user is expected to return to daily — the learning path fills that
     role now.

The defining technical relationship between the two tabs: **the AI
Coaching tab's output is designed to always terminate in a Home-tab lesson
recommendation, never as a standalone answer.** The two tabs are one
product loop, not two independent features — see the loop below.

## The screenshot → diagnosis → lesson-recommendation loop

This is the AI Coaching tab's primary flow, and the reason the two tabs are
architecturally coupled:

```
User imports a screenshot of a real conversation (AI Coaching tab)
        │
        ▼
Vision-extraction call → clean transcript
        │
        ▼
coach_coordinator + 4 workers diagnose it (same engine that graded
daily-practice transcripts under the old structure; this is now its
primary input, not a secondary one)
        │
        ▼
Coordinator's synthesis produces TWO things:
  1. A coaching report explaining the mistake(s), in the user's own
     words (quote-backed, as before)
  2. A lesson recommendation: which Home-tab lesson addresses the
     weakest dimension this diagnosis surfaced
        │
        ▼
UI surfaces both, with the lesson recommendation as a deep link into
the Home tab ("go take this lesson and come back")
        │
        ▼
User completes the lesson + its test/quiz in the Home tab (content
model and test mechanics TBD — see "Deferred" below)
        │
        ▼
Completion is recorded against the user's memory_store, so the next
diagnosis (next screenshot, or next daily-practice session) is sharper
```

This mirrors `VISION.md`'s original closed-loop diagram; what's new here is
architectural, not conceptual: the loop's entry point is explicitly a
secondary tab (AI Coaching) and its exit point is explicitly the primary
tab (Home).

## Agent roster

| Agent | Type | Model | Tools | Role |
|---|---|---|---|---|
| `coach_coordinator` | CMA agent, `multiagent: {"type": "coordinator", ...}`, invoked via a real CMA session | `COORDINATOR_MODEL` (`claude-fable-5`) | none of its own — only the roster | **The app's core agent under v1.** Runs once per diagnosis event — either a screenshot import or an ended daily-practice session. Fans the transcript out to 4 specialist workers, synthesizes one coaching report, and (new in v1) attaches a lesson recommendation mapping the weakest dimension to a specific Home-tab lesson id. |
| `warmth_worker` / `curiosity_worker` / `reciprocity_worker` / `flow_worker` | worker (coach roster) | `WORKER_MODEL` (`claude-sonnet-5`) | none | Unchanged — each grades one dimension off whatever transcript the coordinator hands it, regardless of whether that transcript came from a screenshot or a live practice session. |
| *(new, v1)* vision-extraction step | plain Messages API call, not a CMA agent | candidate: `claude-haiku-4-5` — **not finalized**, see below | none | Screenshot → clean transcript. Feeds the coordinator above; the coordinator never sees the raw image. |
| `partner_agent` | CMA agent (version-pinned), invoked via plain Messages API, not a CMA session | `PARTNER_MODEL` (`claude-sonnet-5`) | none | **Demoted in v1.** Powers only the optional "daily practice" feature inside the AI Coaching tab. No longer the app's central agent; the streaming and coach-memo mechanics described later in this document are otherwise unchanged. |
| *(unscoped)* "talk with the coach" | not yet designed | not yet decided | not yet decided | New conversational surface implied by the v1 direction; distinct from `partner_agent`, which roleplays a persona rather than speaking as the coach. See "Deferred" below. |

## Why CMA and not a single agent

Two things this app needs don't fit a single-agent shape. This reasoning
predates the v1 restructuring and still holds, with the trigger for
"after-the-fact coaching" now broader than it used to be:

1. **Live conversation and after-the-fact coaching are different jobs at
   different latency budgets.** Previously this was justified almost
   entirely by `partner_agent`'s live chat. Under v1 it's justified more by
   the screenshot path: the vision-extraction call should feel close to
   instant, while the diagnosis fan-out that follows it can afford a
   "generating your coaching report…" wait, exactly as before. The optional
   daily-practice chat still exercises the same live/batch split, just as a
   secondary feature now rather than the primary one.
2. **The app needs memory across sessions, not just within one.** This
   matters more under v1, not less: a screenshot diagnosed Monday and a
   lesson completed Tuesday should inform Thursday's diagnosis of a new
   screenshot. This longitudinal, cross-surface profile is now central to
   the product's differentiation (see `VISION.md`), and
   `coach_coordinator`'s `memory_store` is the mechanism that carries it.

### Model tiering on the coach roster

Unchanged from the prior version: `coach_coordinator` runs on a frontier
model (`COORDINATOR_MODEL`, default `claude-fable-5`) while the 4 graders
run on a cheaper/faster one (`WORKER_MODEL`, default `claude-sonnet-5`).
This mirrors CMA's "Plan big, execute small" cost-tiering principle —
frontier model for orchestration and synthesis, cheap model for the
parallel fan-out — applied to specialist grading instead of
web_search/web_fetch fact-finding. The synthesis step (reconciling 4
independent grades into one coherent report and a lesson recommendation,
weighed against the user's memory-store history) is where the frontier
model's judgment earns its cost; each grader's job is narrow and bounded
(one dimension, one short transcript), which tolerates a cheaper model.
Both are configurable via env vars (`SMALLTALK_COORDINATOR_MODEL`,
`SMALLTALK_WORKER_MODEL`) in `backend/app/config.py`.

### Model choice for vision extraction (new, not finalized)

The screenshot → transcript step needs a model with confirmed API vision
support — a wrong transcript poisons everything downstream. A
cost/capability comparison (2026-07-16) evaluated DeepSeek V4 Pro/Flash,
Kimi K2.5/K2.6/K2.7, GLM-5.2, Claude Haiku 4.5, and GPT-5.6 Luna:

- **DeepSeek V4 (Pro/Flash) has no vision support via its public API** — a
  real "Vision (Beta)" mode exists only in DeepSeek's own consumer chat
  product, not the developer API. Confirmed by a live test: sending an
  `image_url` content block to both `deepseek-v4-pro` and
  `deepseek-v4-flash` returns an HTTP 400 schema-level rejection
  (`unknown variant 'image_url', expected 'text'`) before the image is
  even inspected — ruled out.
- Kimi (K2.5/K2.6/K2.7), GLM-5.2, Claude Haiku 4.5, and GPT-5.6 Luna all
  have confirmed API vision support.
- **Claude Haiku 4.5 is the leading candidate, not yet locked in.** Same
  vendor as the rest of this app (no new SDK/vendor relationship),
  documented "near-Sonnet quality" vision, and a modeled cost of roughly
  $0.006–0.008 per screenshot analyzed end to end (vision extraction +
  diagnosis + lesson recommendation) — well under a cent per use, or
  ~$0.20/user/month at one screenshot a day.
- Kimi K2.5 prices lower on paper, and both Kimi and GLM are already
  confirmed multimodal, but neither has been quality-tested on this app's
  actual input shape (small chat-bubble text, avatars), and both add a
  second vendor plus a Chinese-jurisdiction data question on top of the
  third-party-AI disclosure this feature already needs for the other
  person's identity in the screenshot.
- Before locking Haiku 4.5 in, run a real quality test against actual chat
  screenshots — the cost model above assumes vision quality holds up on
  this specific input shape, which hasn't been empirically verified the
  way the DeepSeek rejection was.

### A deliberate split: CMA for versioning, Messages API for the live turn

While building this we checked the current Managed Agents docs
(`platform.claude.com/docs/en/managed-agents/*`) rather than assume the
cookbook summary was still exact, and one detail changes the design:
**every CMA session provisions a fresh sandbox container** ("each session
gets its own isolated sandbox, even when multiple sessions share an
environment"), because sessions are built around agents that use tools.
Neither `partner_agent` nor the vision-extraction step ever touches a tool
— they only talk, or only read an image and return text. Paying a
container cold-start for an agent that will never use the sandbox is pure
latency with no payoff, and directly contradicts this cookbook's own
guidance: reach for CMA when an agent needs to survive independently of a
host process, run long/scheduled, or need human-in-the-loop; reach for the
Agent SDK / raw Messages API when embedding an agent directly in your own
app process and wanting full local control and low latency.

So the split is:
- **`partner_agent` is still a CMA agent** — created and versioned through
  `client.beta.agents.create` / `.update`, so its model choice still goes
  through the same pin/rollback discipline as everything else. The
  provisioning script caches the pinned agent's `model` in
  `.provisioned.json` at create/update time, so the live-chat path reads it
  locally rather than re-querying CMA per turn, then makes a **plain
  streaming `client.messages.stream` call** with that model — no session,
  no sandbox, no environment. This is what keeps the optional daily-practice
  feature feeling like a live chat instead of waiting on a container to
  boot.
- **The vision-extraction step follows the same pattern** — a single
  bounded, tool-free call, made as a plain (non-streaming, since it returns
  a bounded transcript rather than an open-ended reply) `client.messages.create`
  call. No CMA session is warranted here either.
- **`coach_coordinator` runs as a real CMA session** — this is precisely
  the case CMA is for: an asynchronous, multi-agent, tool-free-but-still-
  worth-isolating fan-out job that the user already expects to take a few
  seconds ("generating your coaching report…"), whether it was triggered by
  a screenshot import or an ended daily-practice session.

This is the honest version of "use the managed_agents pattern" — using CMA
for the part of the app where its actual machinery (versioning, multiagent
coordination, memory stores) earns its cost, not bolting a sandbox onto
every chat message or every screenshot because the pattern was named in the
brief.

All coach workers are **tool-free by design** — same "deny-by-default
toolset is the security boundary" reasoning the `roadtrip_planner`
reviewer-agent example uses, and here it also keeps grading fast and cheap
since workers only ever read a transcript, never act on anything.

We deliberately did **not** reach for "Plan big, execute small" (cheap
workers doing `web_search`/`web_fetch` fan-out) for the coach roster — that
pattern pays off for fact-verification-style tasks with a lot of raw
material to read cheaply. Grading a conversation transcript is a judgment
task on material the app already has in hand; a cheap reader would
summarize away exactly the nuance that matters (tone, subtext).

## CMA patterns used, and where

- **Coordinate specialist team** (`CMA_coordinate_specialist_team.ipynb`) —
  `coach_coordinator`'s `multiagent` roster. The server auto-grants
  `create_agent`/`send_to_agent`/`wait_for_agents`/`list_agents` to the
  coordinator; we never define those tools ourselves.
- **Prompt versioning & rollback** — `partner_agent` and every coach worker
  are updated via `agents.update(id, version=..., system=...)` and sessions
  pin an explicit `version` number, never "latest". This matters most for
  `partner_agent`: a persona-prompt tweak that ships broken shouldn't be
  able to silently change every in-flight practice session — rollback is
  re-pinning callers to the previous version.
- **Remember user preferences** (`CMA_remember_user_preferences.ipynb`) —
  one `memory_store` per user, read-write, attached as a resource to
  `coach_coordinator` only (so coaching is trend-aware across both
  screenshot diagnoses and daily-practice sessions — "still working on
  follow-up questions" instead of re-deriving that fresh every time, and
  now also aware of which Home-tab lessons the user has already completed).
  `partner_agent` and the vision-extraction step are **not** part of this
  pattern: neither runs as a CMA session, so there is no session for a
  `memory_store` resource to attach to. `partner_agent`'s own
  user-history-awareness comes from a different, non-CMA mechanism — see
  "The partner's coach memo" below.
- **Streaming turn delivery** (conceptually) — inspired by
  `roadtrip_planner`'s `event_deltas[]` mechanism, but not literal CMA
  session streaming: since `partner_agent` never runs as a CMA session, the
  live turn's deltas come from a plain `client.messages.stream(...)` call
  in `partner.py`, re-streamed as SSE `data: {"delta": ...}` events to the
  iOS client. The only place this app streams `agent.message` events off a
  real CMA session is `coach_coordinator`'s run, which the client doesn't
  see token-by-token — it's consumed server-side and returned as one
  finished report + lesson recommendation.
- **Verify with outcome grader** (conceptually) — the coach coordinator's
  synthesis step is itself an evaluator-style pass over the 4 workers'
  findings, not just concatenation; see `agents_setup.py`'s coordinator
  prompt.

### The partner's coach memo (not a CMA pattern)

`partner_agent`, in its demoted role as the optional daily-practice
feature, still needs *some* awareness of a user's history — "this person
tends to run out of things to say," "they're working on follow-up
questions" — so its practice conversations aren't static across sessions.
Since it's a plain Messages API call rather than a CMA session, it has no
`memory_store` to read. Instead, `partner.py`'s `stream_partner_reply`
looks up the user's most recent 1-2 rows from the local `reports` sqlite
table (`db.get_recent_reports`, in `db.py`) — the same rows the app
already writes for both screenshot diagnoses and practice sessions. If any
of those reports are real (not `parse_error`) and carry `focus_areas`, a
short "coach memo" line is folded into the partner's system prompt
(`scenarios.py`'s `partner_system_prompt`), e.g.: "Coach memo (never
reveal this to the user): they're working on asking follow-up questions —
create natural openings for that in this conversation, don't make it
artificially easy for them." A user with no prior reports gets no memo at
all — the system prompt is the unmodified base template.

This is a local, one-process read (same DB, same request) — cheap enough
to do synchronously on every turn, with none of a CMA session's sandbox
provisioning cost.

## Request flow → CMA calls

### Home tab — structured learning path

```
1. Onboarding
   POST /users/{user_id}/bootstrap
   → memory_stores.create if none exists yet for this user (unchanged)

2. Browse curriculum
   GET /curriculum   (endpoint name/shape TBD)
   → returns the fixed lesson sequence and the user's progress through it
   → no CMA call expected; curriculum content is authored/generated once
     and served as static content (see VISION.md: "the single biggest
     available cost lever")

3. Open a lesson → complete material → take test/quiz
   → content model, test format, and grading approach are not yet
     specified — the biggest open implementation question in v1, see
     "Deferred" below

4. Lesson completion recorded
   → written to the user's memory_store (and/or a local progress table)
     so coach_coordinator's next diagnosis can reference it: "already did
     the reciprocity lesson, still shows up — try a different angle" vs.
     "never addressed"
```

### AI Coaching tab

```
5a. Screenshot diagnosis (primary path)
    POST /coaching/screenshots   { user_id, image }
    → vision-extraction call → clean transcript (not necessarily shown
      to the user as an intermediate step, unless useful for
      confirmation/correction — TBD)
    → client.beta.sessions.create(agent=coach_coordinator pinned version,
      environment_id=shared_environment_id,
      resources=[{type: memory_store, memory_store_id: user's store}])
    → client.beta.sessions.events.send(session_id, user.message=transcript)
    → coordinator spawns the 4 workers, waits, synthesizes report +
      lesson recommendation
    → backend polls until session.status_idle, parses the structured
      report + recommendation, writes distilled growth areas to the
      user's memory_store, saves the report locally
    → iOS polls a status endpoint, then renders { strengths, focus_areas,
      lesson_recommendation, scores } with a deep link into the Home tab

5b. Talk with the coach (optional, secondary)
    → not yet specified, see "Deferred" below

5c. Daily practice (optional, secondary — mechanically unchanged from the
    prior version of this document; only its place in the product changed)
    POST /practice/sessions   { user_id, scenario_id }
    POST /practice/sessions/{id}/message   { text }   (SSE response)
    POST /practice/sessions/{id}/end
    → identical mechanics to before — see "A deliberate split" and
      `partner_agent`'s row in the roster above
```

## iOS app shape (SwiftUI)

**Not yet implemented — current code reflects the pre-v1 structure.** The
app currently ships a `Practice` tab (`ScenarioPickerView` → `ChatView`)
and a `Progress` tab (`ProgressListView`), per `RootView.swift`. Under v1
this becomes:

- **Home tab** — a new curriculum/learning-path view (not yet built);
  replaces `Progress` as one of the two top-level tabs. Progress tracking
  doesn't disappear, but folds into this surface (a user's progress *is*
  their position in the learning path) rather than standing alone.
- **AI Coaching tab** — replaces `Practice` as the other top-level tab. Its
  primary screen is screenshot import/diagnosis (not yet built);
  `ScenarioPickerView` → `ChatView` (the existing practice flow) moves here
  as the secondary "daily practice" entry point rather than disappearing.

This is a real, not-yet-done implementation gap, not a naming change —
flagged here so it isn't mistaken for already-shipped work.

## Deferred — not yet specified

Per the 2026-07-16 product-direction discussion, these are explicitly out
of scope for this document and need their own design pass before
implementation starts:

- **Lesson/curriculum content model.** What a lesson actually consists of
  (text, structured steps, embedded roleplay drill?), how topics are
  authored, and how basic-to-advanced sequencing and prerequisites work.
- **Tests/quizzes.** Format, grading (deterministic vs. model-graded), and
  how a passing result unlocks the next lesson.
- **"Talk with the coach."** Whether this is a new agent, a mode of
  `coach_coordinator`, or something else; whether it needs its own
  `memory_store` access or session model.
- **Vision-extraction model choice.** Haiku 4.5 is the leading candidate
  (see above) but not yet empirically validated on real chat-screenshot
  input.
- **Screenshot-triggered vs. practice-triggered diagnosis prompt
  differences**, if any. `coach_coordinator`'s system prompt was written
  assuming a live-practice transcript; whether it needs adjustment for
  screenshot-derived transcripts (different tone, no partner-agent
  context) hasn't been checked.

## What this environment could and couldn't verify

This machine has Swift (Command Line Tools) but no Xcode.app, so the iOS
target can't be compiled, run in Simulator, or screenshotted here. The
backend has no dependency on Xcode and can be run/tested directly with
`uvicorn`. See [README.md](README.md) for what was actually verified vs.
what still needs a real device/simulator pass.

## Revision history

- **2026-07-16 — v1 restructuring (this revision).** Product direction
  changed from "practice-mode app with a coaching feature" to "structured
  learning-path app (Home) with a coaching utility (AI Coaching) that feeds
  weaknesses back into the learning path." `partner_agent` demoted from the
  app's central agent to an optional feature. See `VISION.md` for the
  product reasoning behind this change.
- **2026-07-12 — expanded vision recorded.** `VISION.md` created,
  documenting the Duolingo-style habit loop + real-conversation coaching
  direction that led to this revision.
- **Original version.** This document was originally written around a
  single-surface practice app: pick a scenario, chat with `partner_agent`,
  get a coaching report. That framing is superseded by the above, but the
  underlying CMA patterns (coordinator/worker fan-out, memory_store,
  version-pinning, the CMA-vs-plain-Messages-API split) carry over
  unchanged into v1.
