# Progress & backlog

**2026-07-12: read `VISION.md` before picking up any new work.** The
product vision was substantially expanded in a planning discussion (a
daily-habit/lesson system + real-conversation coaching via screenshot
import, not just the roleplay-practice app described below) and
implementation is deliberately paused for planning as of this commit. The
backlog/blocked items below still describe Phase 0 (the roleplay-practice
foundation, already built) accurately — keep polishing those if you want,
they're not wasted — but do not start any new *feature* work without
checking `VISION.md`'s Phase 2 section first, since several items there
change what "done" means for pieces already built (e.g. the grading
engine's output needs to eventually double as a lesson router).

**2026-07-18: build-loop model rules changed — final.** The brain/worker
harness now lives in `.claude/skills/brain-worker-loop/` (SKILL.md protocol
+ `worker.sh` runner): brain = Claude Fable 5 only (plans, delegates,
reviews, accepts — never implements), workers = Codex (GPT 5.6) only
(`gpt-5.6-terra` default, `gpt-5.6-luna` allowed), enforced in `worker.sh`.
Decision record: `smalltalk-coach-planning/DECISIONS.md` ("2026-07-18 —
Worker Model Locked to Codex (GPT 5.6)"). The Fable-5+Sonnet-5 loop
described in the next paragraph and the two skills in
`~/.claude/scheduled-tasks/` (smalltalk-brain-worker-loop,
smalltalk-coach-loop-resume) are **superseded — do not start a cycle from
them.** No scheduled loop is active as of this note (CronList and crontab
checked 2026-07-18). The loop stays dormant until the planning repo's
`VALIDATION_PLAN.md` thresholds are met (scope gate in
`smalltalk-coach-planning/ORCHESTRATION.md`).

State file for the automated brain-worker-loop (previously Fable-5
coordinator + Sonnet-5 workers, "Plan big, execute small" cost-tiering
pattern — see
ARCHITECTURE.md and `backend/app/agents_setup.py`). Every scheduled cycle:
reads this file, does the next actionable item, runs tests, commits, pushes
to `master`, then appends a cycle log entry below. If every open item is
blocked, log that and stop — don't invent busywork.

## Blocked on human action (do not attempt these autonomously)

- **CMA-enabled Anthropic API key**: `backend/scripts/provision_agents.py`
  needs a key with Claude Managed Agents beta access
  (`managed-agents-2026-04-01`) in `~/.env`. Without it, no live CMA call
  (agent/session/environment creation) can succeed.
- **Xcode**: the iOS target has only ever been syntax-checked
  (`swiftc -parse`) and xcodegen-validated, never compiled or run in
  Simulator — this machine has Command Line Tools only. Needs a Mac with the
  full Xcode app.

## Backlog (actionable now, no human gate)

1. Backend: expand test coverage for edge cases in `recommend.py` /
   `progress.py` beyond the current 120-test baseline (e.g. empty-history
   users, ties in scenario scoring).
2. Backend: review `agents_setup.py` / `coach.py` / `partner.py` for any
   dead code or TODOs left from the T9-T11 push.
3. iOS: continue syntax-level polish and `swiftc -parse` verification of
   any new Core package consumers; keep `ios/Core` the single source of
   truth for shared models (don't let SmallTalkCoach app-target files drift
   back into duplicating them).
4. Docs: keep ARCHITECTURE.md and README.md in sync with any schema/endpoint
   changes made during a cycle.
5. Re-evaluate this backlog each cycle — pull in whatever's the smallest
   next real improvement rather than treating this list as exhaustive.

## Once the human-gated items are cleared

6. Run `provision_agents.py` against the real API, confirm every CMA agent
   provisions successfully, commit the resulting `.provisioned.json` state
   (id/version bookkeeping only — no secrets in it).
7. First real Simulator run of the chat flow end to end; fix whatever
   breaks on actual compilation (expect some — iOS code has never been
   built, only parsed).
8. First live end-to-end coaching-report run (session end → coordinator →
   4 workers → synthesized report) against real CMA.

## Cycle log

<!-- Each automated cycle appends one entry here: date, what changed, what's next. -->

- **2026-07-12**: Backlog item 1 (recommend.py/progress.py edge-case test
  coverage). Found a real, previously-untested gap: `_scenario_difficulty()`
  in `recommend.py` has a documented fallback to `"medium"` for a
  scenario_id that no longer exists in the current `SCENARIOS` catalog
  (stale historical data after a catalog edit), but nothing exercised that
  path. Added two tests in `test_recommend.py`:
  `test_stale_scenario_id_falls_back_to_medium_for_step_up` and
  `test_stale_scenario_id_falls_back_to_medium_for_default_rotation`,
  covering both the step-up and default-rotation branches with a stale id.
  Verified gates before starting: Xcode is still Command Line Tools only
  (`xcodebuild -version` fails) -- iOS gate stays blocked. The
  `ANTHROPIC_API_KEY`/CMA-beta gate could not be actively re-verified this
  cycle (the sandbox's permission layer denies any Bash read of `~/.env`,
  even a value-free `grep -q` existence check) -- treated as unchanged/
  still blocked per the "if neither has changed" fallback rule, so no
  CMA-gated items were attempted. Test status: full backend suite green,
  139 passed (up from 137 before this cycle; 2 new). Next actionable item:
  keep working backlog item 1 -- e.g. add a test for
  `_pick_scenario_for_dimension`'s "no candidates stress this dimension"
  fallback branch (currently marked "should not happen in practice" with no
  direct test), or move to backlog item 2 (dead-code/TODO review of
  `agents_setup.py`/`coach.py`/`partner.py`).

- **2026-07-12 (separate session, same worker/brain loop)**: T12 (session
  history detail/transcript replay), T13 (staged grading UX — fixed
  `APIClient.endPractice`, which had been decoding a raw `CoachReport` from
  `/end` even though `/end` returns `202 {"status":"grading"}`; added
  `GradingPhase` state machine + polling with a 90s timeout, staged waiting
  UI, "Practice again"/"Back to scenarios" actions), and T14 (onboarding: 3
  screens + a `POST /users/{id}/onboarding` endpoint recording a struggle
  pick into the user's memory store) all implemented and independently
  brain-reviewed. Two brain-review follow-ups also fixed: a `GET
  .../report` ownership gap (no owner check at all — now matches the
  session-detail endpoint's guard), and two T13 UX bugs (a post-report dead
  end when the report sheet is dismissed via Done/swipe instead of the
  action buttons; `ChatView` constructing its view model inline via
  `@ObservedObject` instead of `@StateObject`, risking silent state loss on
  parent re-render). Backend suite: 145 passed. Both human-gated items
  (CMA key, Xcode) remain blocked, re-checked and unchanged. Backlog items
  1-4 above are still fair game and don't overlap with this work. Next
  actionable item for either loop: T18 launch hardening (app icon, a
  shared-secret auth token between the app and backend — right now the
  backend is an open relay to whatever Anthropic key it holds — ATS/LAN-IP
  device config, privacy disclosure copy) is the only remaining unblocked
  item from the original T1-T18 plan; sequence it after, not before, if
  more product-feature backlog turns up first.
