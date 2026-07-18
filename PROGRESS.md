# Progress & backlog

**2026-07-18 (latest): BUILD MODE — build start approved, scope gate
lifted.** Founder delegated the go/no-go to the brain (records: root
`DECISIONS.md` → "2026-07-18 — Build Start Approved; Content-Model-First
Sequencing"; `docs/planning/DECISIONS.md` → "2026-07-18 — Build Start
Approved (Founder Delegation)"). The loop now runs autonomous bounded
cycles under the existing safety rules (never force-push, clean-tree gate,
3-round cap, brain reviews everything before commit/push).

## v1 build backlog (current, maintained by the brain each cycle)

1. ~~**Cycle A (docs):** CONTENT_MODEL_V1.md + l01 fixture + gate sync~~ —
   done, accepted 2026-07-18 (cycle 4 below).
2. ~~**Cycle B (code):** backend skeleton + curriculum serving~~ — done,
   accepted 2026-07-18 (cycle 5 below). 10 tests green.
3. ~~Author remaining Unit 1 content (`l02`, `l03`)~~ — done, accepted
   2026-07-18 (cycle 6 below). Unit 1 fully authored.
4. ~~Author remaining units~~ — ALL DONE. Unit 2 (cycle 7), Unit 3
   (cycle 8), Unit 4 (cycle 9). **Full 12-lesson curriculum authored and
   served.**
5. ~~Persistence/code hardening~~ — done, accepted 2026-07-18 (cycle 10).
6. **LOOP RESUMED (2026-07-18, founder update): Xcode 26.6 installed and
   verified (xcodebuild, xcodegen 2.45.4, iOS 18.2 simulators) — iOS
   unblocked.** iOS track, one cycle at a time:
   a. ~~iOS scaffold~~ — done, accepted 2026-07-18 (cycle 11). Builds +
      4 unit tests green on iPhone 16 sim (brain-run).
   b. Lesson detail view (content blocks) + completion-check flow. Note
      for this cycle: make `LessonExample.dialogue` optional + add
      `narration` (schema allows narration-only lessons).
   c. Coaching tab real UI once the pipeline exists.
7. Coaching pipeline — founder is providing a test Anthropic key (to
   `~/.env`, never in the repo). Order: design doc cycle first, then
   implementation once the key is confirmed present. Key handling rules:
   the key value never appears in specs, code, logs, worker output, or
   git; backend reads it from the environment at runtime only.

**2026-07-18: LOOP ACTIVATED — interview gate waived (founder
decision).** The validation-interview gate is consciously skipped (records:
`docs/planning/DECISIONS.md` → "2026-07-18 — Validation Interviews Deferred;
Build Gate Waived (Founder)" and root `DECISIONS.md` → "2026-07-18 — Build
Scope Gate Narrowed"). The brain/worker loop is now active for
**documentation-only** roadmap work: first a small round-trip verification
task (SKILL.md stale-path fix), then the v1 lesson-path definition
(`docs/planning/LESSON_PATH_V1.md`). App code remains gated on the lesson
path being accepted **plus an explicit founder go-ahead**. Brain: Claude
Fable 5 (interactive session, founder present); worker: `gpt-5.6-terra` via
`worker.sh`. Run baseline for auto-push: `9485fa7`.

**2026-07-18: FULL RESTART EXECUTED (founder-approved).** The Phase 0
implementation (`backend/` 38 files, `ios/` 27 files) has been removed
from `master`; the complete pre-cleanup tree is archived at tag
`phase0-archive` (recovery: `git checkout phase0-archive -- backend ios`).
Decision record: `DECISIONS.md` → "2026-07-18 — Full Restart". Every
section below that references backend/iOS files, their backlog items, or
their blocked gates is **historical** — kept for the record, not
actionable. Current actionable state: planning/validation only, per
`docs/planning/VALIDATION_PLAN.md`; the brain/worker loop harness
(`.claude/skills/brain-worker-loop/`) is active for approved non-app work.

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

**2026-07-18 (later): project-resident memory layer added (founder
decision).** Shared loop memory lives in this repo, not in either model's
native memory: this file (status), `DECISIONS.md` at the repo root
(engineering decisions, append-only), and `WORKER_LOG.md` (one structured
entry per worker task, enforced by `worker.sh` — exit 4 = worker didn't
log = automatic reject). Brain and workers read these at every cycle
start. Record: repo `DECISIONS.md` → "2026-07-18 — Project-Resident Memory
for the Build Loop".

**2026-07-18 (later still): safe auto-push enabled (founder decision).**
After a successful verified run that created a commit, the brain runs
`.claude/skills/brain-worker-loop/auto_push.sh -b <run-start HEAD>` —
current branch to its upstream only, never force, no retries, dirty tree
refused, `AUTO_PUSH=0` to disable. Record: repo `DECISIONS.md` →
"2026-07-18 — Safe Auto-Push After Verified Runs".

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

- **2026-07-18 (cycle 11 — iOS scaffold, first iOS cycle post-Xcode):**
  Worker: `gpt-5.6-terra`, one round, honest partial report (sandbox
  blocks CoreSimulatorService — tests written, not executed in-sandbox;
  in-sandbox `xcodegen generate` + simulator build succeeded). Shipped
  `ios/`: xcodegen project.yml (xcodeproj stays gitignored), two-tab
  SwiftUI shell (Home + Coaching placeholder per ARCHITECTURE v1), Codable
  models mirroring every backend shape (incl. kind-discriminated
  completion-check parts), async APIClient (configurable base URL,
  persisted UUID user id), Home curriculum list with unit sections and
  state badges, 4 XCTests (one decodes the real l01 file embedded as a
  test resource). Brain verification: regenerated project, simulator
  build, and **all 4 tests executed and passed on iPhone 16 / iOS 18.2**
  (brain's own run) — ACCEPTED. Known gap for cycle b:
  `LessonExample.dialogue` non-optional though schema allows
  narration-only. **Next:** coaching-pipeline design doc (key-independent),
  then iOS lesson detail.

- **2026-07-18 (cycle 10 — backend hardening; unblocked backlog complete):**
  Worker: `gpt-5.6-terra`, one round. sqlite connections now explicitly
  closed (`contextlib.closing` around each per-call connection, transaction
  `with` preserved inside); `PRACTICE_TYPES` map removed from code — the
  manifest carries `practice_type` ×12 (verified identical to
  LESSON_PATH_V1) and the loader enforces lesson↔manifest equality, with a
  new mismatch-rejection test; CONTENT_MODEL_V1.md gains a "Path manifest"
  section so the manifest shape is documented. Brain verification: suite
  run independently — **12 passed**; all diffs read in full — ACCEPTED.
  **Loop state: paused with unblocked backlog exhausted.** Remaining items
  are founder-gated (Anthropic key for coaching pipeline; Xcode for iOS)
  or need a new design pass (coaching pipeline, free-draft grading).

- **2026-07-18 (cycle 9 — Unit 4 content: L10–L12; CURRICULUM COMPLETE):**
  Worker: `gpt-5.6-terra`. Note: the first dispatch of this task was
  externally stopped mid-run — tree verified clean (worker died in its
  read phase, nothing written), re-dispatched identical spec, one working
  round. Authored `l10-build-on-common-ground` (topic-thread ordering
  check), `l11-end-warmly` (exit-quality: appreciation/reason/clean-end),
  `l12-make-continuity-easy` (safety-reviewed: declining modeled as a fine
  outcome, persistence marked wrong). Tests restructured: full l01→l12
  walk asserting final `unlocked_next: null` + all-completed curriculum;
  content_pending coverage moved to a tmp-fixture test. Brain
  verification: suite run independently — 11 passed; all three lessons
  read in full — ACCEPTED. **Next:** hardening cycle (backlog item 5),
  which exhausts the unblocked backlog.

- **2026-07-18 (cycle 8 — Unit 3 content: L07–L09):** Worker:
  `gpt-5.6-terra`, one round. Authored `l07-share-and-make-space`,
  `l08-handle-the-pause` (three-pause scenario-judgment check, cues named
  in every feedback), `l09-read-the-room` (safety-reviewed: observable
  cues only, no intent claims, give-space modeled as a good outcome per
  PRODUCT_BRIEF §12) + minimal test updates (lessons_loaded 9, chain
  probes l10). Brain verification: suite run independently — 10 passed;
  all three lessons read in full — ACCEPTED. **Next:** Unit 4 (l10–l12),
  which completes the curriculum; content_pending test coverage moves to
  a synthetic fixture since the chain will exhaust the path.

- **2026-07-18 (cycle 7 — Unit 2 content: L04–L06):** Worker:
  `gpt-5.6-terra`, one round. Authored `l04-answer-and-return`,
  `l05-show-you-heard`, `l06-follow-the-thread` (metadata verbatim,
  loader-validated; turn-balance / evidence-spotting / branching-response
  check types faithfully implemented; correct-option positions varied per
  the cycle-6 nit) + minimal test updates (lessons_loaded 6, chain probes
  l07). Brain verification: suite run independently — 10 passed; all three
  lessons read in full — ACCEPTED. **Next:** Unit 3 content (l07–l09).

- **2026-07-18 (cycle 6 — Unit 1 content complete: L02 + L03):** Worker:
  `gpt-5.6-terra`, one round. Authored `l02-use-the-setting.json` and
  `l03-easy-first-question.json` (metadata verbatim vs LESSON_PATH_V1,
  validated by the loader; completion checks faithfully implement the
  locked situation-match and revise-and-reason types) and made the minimal
  test updates (lessons_loaded 3, content set, content_pending probe moved
  to l04 via a programmatic completion chain using derived correct
  answers). Brain verification: suite run independently — 10 passed;
  both lessons read in full against the L01 quality bar — ACCEPTED.
  Nit: L02's correct answers all sit at index 0 (L03 varies placement);
  randomize/shuffle placement in a later content pass. **Next:** Unit 2
  content (l04–l06).

- **2026-07-18 (cycle 5 — backend skeleton + curriculum serving, first app
  code):** Worker: `gpt-5.6-terra`, one round. Shipped
  `content/lesson_path.json` (machine mirror of LESSON_PATH_V1, validated
  for self-consistency), `backend/app/` (FastAPI; content loader enforcing
  all seven CONTENT_MODEL_V1 §4 rules incl. per-lesson practice-type check;
  sqlite3 progress store; curriculum/lesson/completion endpoints with
  sequential unlock, 423-locked / 404-content_pending semantics, idempotent
  deterministic grading), and a 10-test pytest suite. Brain verification:
  suite run independently — **10 passed** (0.37s); manifest routing sizes
  and spot-checked fields match the doc verbatim; no venv/db/pycache
  leakage. ACCEPTED. Hardening notes for later: per-request sqlite
  connections are never explicitly closed; PRACTICE_TYPES map duplicated in
  code rather than manifest; no auth (documented in backend/README.md).
  **Next:** author `l02`/`l03` content against the proven schema.

- **2026-07-18 (cycle 4 — content model + L01 fixture; build phase begins):**
  First build-phase cycle after the founder delegated build start and the
  brain selected content-model-first sequencing. Worker: `gpt-5.6-terra`,
  one round. Shipped `docs/planning/CONTENT_MODEL_V1.md` (static-JSON
  lesson schema: six content blocks, deterministic `choice` +
  `deferred-v1` `free_draft` completion checks, load-time validation
  rules) and `content/lessons/l01-first-hello.json` (first fully-authored
  lesson, metadata verbatim-matched to LESSON_PATH_V1 §3); gate text in
  ORCHESTRATION.md/SKILL.md now reflects the active build phase. Brain
  review: JSON parses, schema/fixture conform field-for-field, quality
  bar met — ACCEPTED. **Next:** Cycle B, backend skeleton + curriculum
  serving against this schema.

- **2026-07-18 (cycle 3 — v1 lesson path defined):** Task: write
  `docs/planning/LESSON_PATH_V1.md` (the locked v1 beginner path) + sync
  the stale scope-gate text in ORCHESTRATION.md and SKILL.md to the
  2026-07-18 waiver decisions. Worker: `gpt-5.6-terra`, one round, no
  iteration needed. Brain review: all 6 acceptance criteria verified
  against the diff, including full routing-table/lesson-mapping
  cross-consistency (12 lessons, 4 units, every dimension routed) and
  assumption labeling (7 assumptions, each with a revisit trigger) —
  ACCEPTED. Known nit for a future content pass: three lesson section
  headings differ from their canonical `title:` fields (L02/L04/L09).
  Resolves the open product decision "the first 5–10 lessons in the
  beginner path". **Next:** the scope gate's remaining condition is an
  explicit founder go-ahead for build start; until then, candidate
  docs-only work includes a v1 build-sequencing plan and the lesson
  content-authoring approach.

- **2026-07-18 (cycle 2 — loop round-trip verification, founder-requested):**
  Small real task to prove the loop end to end before the main cycle: fix
  the two stale `untitled folder` repo paths in
  `.claude/skills/brain-worker-loop/SKILL.md`. Worker: `gpt-5.6-terra`,
  one round. Brain verified the diff touched only the two path strings,
  `git grep "untitled folder"` returned nothing, and the WORKER_LOG.md
  entry was a true, correctly formatted append — ACCEPTED, committed,
  auto-pushed (`35a3b89`). Round trip confirmed: spec → worker.sh →
  worker edit → log append → brain review → accept → push.

- **2026-07-18 (brain/worker loop v2 — first cycle, end-to-end test):**
  First real cycle of the Fable-5-brain / Codex-GPT-5.6-worker harness,
  run on founder request as a full-loop test. Task: fix README.md intro
  drift against the v1 ARCHITECTURE.md (docs-only; app code remains
  gated on VALIDATION_PLAN.md). Worker: `gpt-5.6-terra` via `worker.sh`;
  one round, no iteration needed. Brain review: diff scope, v1 accuracy
  (including the "v1 UI not yet implemented" caveat), and the
  WORKER_LOG.md entry all verified independently — ACCEPTED. Pushed via
  `auto_push.sh`. The full protocol (activation guard → spec →
  delegate → review → accept → log → push) is now proven working.

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
