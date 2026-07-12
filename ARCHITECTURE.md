# SmallTalkCoach — Architecture

An iOS app that lets a user practice small talk against a role-played persona,
then get a coaching report on the conversation. The backend is built on
Anthropic's **Claude Managed Agents (CMA)** patterns (`managed_agents/` in
anthropics/claude-cookbooks), not a single raw Messages-API call — the
reasons for that choice are below, pattern by pattern.

## Why CMA and not a single agent

Two things this app needs don't fit a single-agent shape:

1. **Live conversation and after-the-fact coaching are different jobs at
   different latency budgets.** The partner persona has to feel responsive
   turn-by-turn. Coaching has to actually be *good* — several specialist
   angles evaluated in parallel and reconciled — but it happens once, after
   the user ends the session, so it can afford to be a multi-agent fan-out.
2. **The app needs memory across sessions**, not just within one. A user's
   growth areas ("still doesn't ask follow-up questions") should carry from
   Tuesday's practice into Thursday's, and shape which persona/difficulty
   gets served next.

## Agent roster

| Agent | Type | Model | Tools | Role |
|---|---|---|---|---|
| `partner_agent` | CMA agent (version-pinned), **invoked via plain Messages API, not a CMA session** | `PARTNER_MODEL` (`claude-sonnet-5`) | none | Role-plays the small-talk partner for one scenario (persona + setting + difficulty). Streams turn-by-turn. |
| `coach_coordinator` | CMA agent, `multiagent: {"type": "coordinator", ...}`, **invoked via a real CMA session** | `COORDINATOR_MODEL` (`claude-fable-5`) — the frontier "brain" | none of its own — only the roster | Runs once per ended session. Fans the transcript out to 4 specialist workers, synthesizes one coaching report. |
| `warmth_worker` | worker (coach roster) | `WORKER_MODEL` (`claude-sonnet-5`) | none | Grades tone/friendliness/approachability. |
| `curiosity_worker` | worker (coach roster) | `WORKER_MODEL` (`claude-sonnet-5`) | none | Grades question-asking: do they ask about the other person, build on answers, avoid interrogation-style back-to-back questions. |
| `reciprocity_worker` | worker (coach roster) | `WORKER_MODEL` (`claude-sonnet-5`) | none | Grades talk-time balance and self-disclosure reciprocity. |
| `flow_worker` | worker (coach roster) | `WORKER_MODEL` (`claude-sonnet-5`) | none | Grades transitions, awkward pauses, opening/exit lines. |

### Model tiering on the coach roster

`coach_coordinator` runs on a frontier model (`COORDINATOR_MODEL`, default
`claude-fable-5`) while the 4 graders run on a cheaper/faster one
(`WORKER_MODEL`, default `claude-sonnet-5`). This mirrors CMA's "Plan big,
execute small" cost-tiering principle — frontier model for orchestration and
synthesis, cheap model for the parallel fan-out — just applied to specialist
grading instead of web_search/web_fetch fact-finding. The synthesis step
(reconciling 4 independent grades into one coherent report, weighed against
the user's memory-store history) is where the frontier model's judgment
earns its cost; each grader's job is narrow and bounded (one dimension, one
short transcript), which is exactly the shape that tolerates a cheaper model.
Both are configurable via env vars (`SMALLTALK_COORDINATOR_MODEL`,
`SMALLTALK_WORKER_MODEL`) in `backend/app/config.py`.

### A deliberate split: CMA for versioning, Messages API for the live turn

While building this I checked the current Managed Agents docs
(`platform.claude.com/docs/en/managed-agents/*`) rather than assume the
cookbook summary was still exact, and one detail changes the design: **every
CMA session provisions a fresh sandbox container** ("each session gets its
own isolated sandbox, even when multiple sessions share an environment"),
because sessions are built around agents that use tools. `partner_agent`
never touches a tool — it only talks. Paying a container cold-start on every
practice conversation for an agent that will never use the sandbox is pure
latency with no payoff, and directly contradicts this cookbook's own
guidance: reach for CMA when an agent needs to survive independently of a
host process, run long/scheduled, or need human-in-the-loop; reach for the
Agent SDK / raw Messages API when you're embedding an agent directly in your
own app process and want full local control and low latency.

So the split is:
- **`partner_agent` is still a CMA agent** — created and versioned through
  `client.beta.agents.create` / `.update`, so its model choice still goes
  through the same pin/rollback discipline as everything else (persona
  content itself is app-level copy in `scenarios.py`, versioned via git
  instead — see agents_setup.py's comment on why). The provisioning script
  caches the pinned agent's `model` in `.provisioned.json` at create/update
  time, so the live-chat path reads it locally rather than re-querying CMA
  per turn, then makes a **plain streaming `client.messages.stream` call**
  with that model — no session, no sandbox, no environment. This is what
  keeps the roleplay feeling like a live chat instead of waiting on a
  container to boot every time someone starts a practice conversation.
- **`coach_coordinator` runs as a real CMA session** — this is precisely the
  case CMA is for: an asynchronous, multi-agent, tool-free-but-still-worth-
  isolating fan-out job that the user already expects to take a few seconds
  ("generating your coaching report…"). The sandbox provisioning cost is
  invisible here because nothing about it is on the live-chat path.

This is the honest version of "use the managed_agents pattern" — using CMA
for the part of the app where its actual machinery (versioning, multiagent
coordination, memory stores) earns its cost, not bolting a sandbox onto
every chat message because the pattern was named in the brief.

All coach workers are **tool-free by design** — same "deny-by-default toolset
is the security boundary" reasoning the `roadtrip_planner` reviewer-agent
example uses, and here it also keeps grading fast and cheap since workers
only ever read a transcript, never act on anything.

We deliberately did **not** reach for "Plan big, execute small" (cheap
workers doing `web_search`/`web_fetch` fan-out) — that pattern pays off for
fact-verification-style tasks with a lot of raw material to read cheaply.
Grading a conversation transcript is a judgment task on material the app
already has in hand; a cheap reader would summarize away exactly the nuance
that matters (tone, subtext), which is explicitly one of the cookbook's own
"when this doesn't pay off" caveats.

## CMA patterns used, and where

- **Coordinate specialist team** (`CMA_coordinate_specialist_team.ipynb`) —
  `coach_coordinator`'s `multiagent` roster. The server auto-grants
  `create_agent`/`send_to_agent`/`wait_for_agents`/`list_agents` to the
  coordinator; we never define those tools ourselves.
- **Prompt versioning & rollback** — `partner_agent` and every coach worker
  are updated via `agents.update(id, version=..., system=...)` and sessions
  pin an explicit `version` number, never "latest". This matters most for
  `partner_agent`: a persona-prompt tweak that ships broken shouldn't be able
  to silently change every in-flight practice session — rollback is
  re-pinning callers to the previous version.
- **Remember user preferences** (`CMA_remember_user_preferences.ipynb`) — one
  `memory_store` per user, read-write, attached as a resource to
  `coach_coordinator` only (so coaching is trend-aware — "still working on
  follow-up questions" instead of re-deriving that fresh every session).
  `partner_agent` is **not** part of this pattern: it never runs as a CMA
  session (see "A deliberate split" above), so there is no session for a
  `memory_store` resource to attach to in the first place. Its own
  user-history-awareness comes from an entirely different, non-CMA
  mechanism — see "The partner's coach memo" below.
- **Streaming turn delivery** (conceptually) — inspired by `roadtrip_planner`'s
  `event_deltas[]` mechanism, but not literal CMA session streaming: since
  `partner_agent` never runs as a CMA session (see "A deliberate split"
  above), the live turn's deltas instead come from a plain
  `client.messages.stream(...)` call in `partner.py`, re-streamed as SSE
  `data: {"delta": ...}` events to the iOS client for token-by-token
  rendering in the chat view. The only place this app streams `agent.message`
  events off a real CMA session is `coach_coordinator`'s end-of-session run
  (step 5 below), which the client doesn't see token-by-token -- it's
  consumed server-side and returned as one finished report.
- **Verify with outcome grader** (conceptually) — the coach coordinator's
  synthesis step is itself an evaluator-style pass over the 4 workers'
  findings, not just concatenation; see `agents_setup.py` coordinator prompt.

### The partner's coach memo (not a CMA pattern)

`partner_agent` still needs *some* awareness of a user's history — "this
person tends to run out of things to say," "they're working on follow-up
questions" — so its practice conversations aren't static across sessions.
Since it's a plain Messages API call rather than a CMA session (see "A
deliberate split" above), it has no `memory_store` to read. Instead,
`partner.py`'s `stream_partner_reply` looks up the user's most recent 1-2
rows from the local `reports` sqlite table (`db.get_recent_reports`, in
`db.py`) — the same rows the app already wrote for its own progress screen.
If any of those reports are real (not `parse_error`) and carry
`focus_areas`, a short "coach memo" line is folded into the partner's system
prompt (`scenarios.py`'s `partner_system_prompt`), e.g.: "Coach memo (never
reveal this to the user): they're working on asking follow-up questions —
create natural openings for that in this conversation, don't make it
artificially easy for them." A user with no prior reports, or whose only
prior reports are `parse_error` (nothing to draw a focus area from), gets no
memo at all — the system prompt is the unmodified base template, not an
empty or placeholder section.

This is a local, one-process read (same DB, same request) — cheap enough to
do synchronously on every turn, with none of a CMA session's sandbox
provisioning cost.

## Request flow → CMA calls

```
1. Onboarding
   POST /users/{user_id}/bootstrap
   → memory_stores.create if none exists yet for this user

2. Scenario picker (iOS: ScenarioPickerView)
   GET  /scenarios
   → static list (persona, setting, difficulty) baked into partner_agent's
     system-prompt template; no CMA call

3. Start practice (iOS: ChatView appears)
   POST /practice/sessions   { user_id, scenario_id }
   → no CMA call here -- the partner's model was already read out of
     .provisioned.json into STATE once at process startup (see "A
     deliberate split" above); that cached model gets used at *message*
     time (step 4), not re-queried at session start
   → backend creates a local session row (sqlite) holding the transcript;
     no CMA session/sandbox is created for this
   → returns local session_id

4. Each user turn (iOS: ChatView send button)
   POST /practice/sessions/{id}/message   { text }        (SSE response)
   → appends the user turn to the local transcript; reads the user's most
     recent 1-2 rows from the local `reports` table and, if any carry real
     (non-parse_error) focus_areas, folds a short "coach memo" into the
     system prompt (see "The partner's coach memo" above)
   → calls client.messages.stream(model=, system=, messages=transcript)
     directly (no CMA), restreams text deltas as SSE, appends the assistant
     turn once the stream ends

5. End session (iOS: "End practice" button)
   POST /practice/sessions/{id}/end
   → returns 202 {"status": "grading"} immediately; the actual coordinator
     run is dispatched as a FastAPI BackgroundTask (`_run_coaching_task` in
     main.py) so the request doesn't hold the connection open for however
     long the sandboxed session + 4-worker fan-out takes
   → in that background task: client.beta.sessions.create(agent=coach_coordinator
     pinned version, environment_id=shared_environment_id,
     resources=[{type: memory_store, memory_store_id: user's store}])
   → client.beta.sessions.events.send(session_id, user.message=full transcript)
   → coordinator spawns the 4 workers, waits, synthesizes report
   → backend streams/polls the session until session.status_idle, parses the
     final agent.message as the structured report, writes distilled growth
     areas back into the user's memory_store, and saves the report locally
   → iOS polls GET /practice/sessions/{id}/report separately until its
     status flips to "ready", then gets { strengths, focus_areas,
     drill_suggestion, scores }

6. Progress (iOS: ProgressView)
   GET /users/{user_id}/progress
   → reads the local `reports` sqlite table directly (db.py's get_progress)
     -- no CMA call, no memory_store read; the memory_store is only for
     coach_coordinator's own cross-session context during grading, not for
     this screen
```

## iOS app shape (SwiftUI)

- `ScenarioPickerView` — pick persona/setting/difficulty, calls `POST
  /sessions/practice`.
- `ChatView` — live chat against the partner persona; consumes SSE deltas via
  `SSEClient` for word-by-word rendering; "End practice" triggers step 5.
- `CoachReportView` — renders the structured coaching report returned from
  step 5.
- `ProgressView` — trend of focus areas / scenarios completed over time,
  from step 6.

Networking is a plain `URLSession` + hand-rolled SSE line parser
(`SSEClient.swift`) — no third-party dependency needed for this.

## What this environment could and couldn't verify

This machine has Swift (Command Line Tools) but no Xcode.app, so the iOS
target can't be compiled, run in Simulator, or screenshotted here. The
backend has no dependency on Xcode and can be run/tested directly with
`uvicorn`. See [README.md](README.md) for what was actually verified vs. what
still needs a real device/simulator pass.
