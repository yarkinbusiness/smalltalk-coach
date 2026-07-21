# Progress & backlog

**2026-07-21 (newest): STANDING INSTRUCTION — loop becomes perpetual once
the UI Improvement Plan backlog is exhausted (founder-issued, mid-cycle
52/53).** Verbatim intent: after every quick win and every deeper
redesign in `docs/planning/UI_IMPROVEMENT_PLAN.md` is shipped, do **not**
stop and report back — instead (1) build + run live on the iPhone 16
simulator, verify end to end (backend health, learning path, lesson
states), fixing any build/runtime failure first; (2) the brain researches
further UI/UX polish opportunities (layout, motion, copy, habit loops),
comparing current screens against `docs/research/smalltalk-coach-research.pdf`
and the (by then fully-actioned) UI Improvement Plan for anything newly
relevant; (3) hand each finding to the worker as one small, well-scoped
task at a time via the existing loop protocol; (4) after each task,
build + verify again, log to `WORKER_LOG.md`, and loop back to (2) —
continuously, indefinitely, not a fixed backlog. Same guardrails as
always: founder-deferred items (paywall-sequencing; Coach-tab/free-draft
IA placement) still get flagged and stopped on, not decided unilaterally;
never commit without a `PROGRESS.md` note; existing spec docs still
govern. **Mechanism note (not yet actioned — decide when actually
reached):** `CronList` checked 2026-07-21, no conflicting scheduled jobs
on this repo. When the fixed backlog below is actually exhausted, use
`ScheduleWakeup`'s dynamic-loop mechanism (or `CronCreate` if
cross-session persistence beyond a single conversation turns out to be
needed) to keep the cycle firing rather than just stopping — don't
over-build this until that point is actually reached.

**2026-07-21 (earlier): LOOP ACTIVE — UI Improvement Plan execution
begun (founder-approved).** The v3 roadmap (T-K, T-L, and the follow-up
privacy-policy fix) is fully shipped — see the cycle log below. The
founder then commissioned UI/UX research (`docs/research/`, condensed
into `docs/planning/UI_IMPROVEMENT_PLAN.md`) and approved it in full.
The loop is now executing that plan's backlog in its exact written
order — quick wins first, then deeper redesigns — under the same locked
model rules and mandatory-verification protocol as before. Two items in
the plan (paywall-sequencing trigger logic; the Coach-tab / free-draft-
grading IA placement question) are explicitly founder-deferred — flag
and stop when reached rather than deciding unilaterally. Cycle numbering
continues from 46.

**2026-07-20 (later): LOOP ACTIVE — v2 execution begun (founder
instruction).** The loop is executing the v2 backlog below tier by tier
(P0 → P1 → P2) under the locked model rules (brain: Claude Fable 5;
workers: `gpt-5.6-terra` via `worker.sh` — DECISIONS: "2026-07-18 —
Worker Model Locked to Codex (GPT 5.6)"). Founder-gated items (T-K
pricing/free-tier, T-L free-draft budget, the real-screenshot vision
eval) are **deferred, not blocking** — the loop skips to the next
actionable task. Haiku-only lock, no new API spend, and mandatory
simulator verification per cycle all remain in force. Cycle numbering
continues from 23.

**2026-07-20: ROADMAP REFRESHED — v2 backlog adopted
(founder-approved).** The brain ran a full roadmap strength review against
VISION.md, PRODUCT_BRIEF.md, ARCHITECTURE.md, both DECISIONS.md logs, and
WORKER_LOG.md. Verdict: the v1 build backlog is complete and the rest of
this file's backlog sections were stale (they reference Phase 0 files
deleted in the 2026-07-18 Full Restart) — see
`docs/planning/ROADMAP_REVIEW_2026-07-20.md` for the full report, task
rationale, and acceptance criteria, and root `DECISIONS.md` →
"2026-07-20 — v2 Backlog Adopted After Roadmap Strength Review". The
**v2 backlog** below is now the single actionable list. The sections
"Blocked on human action", "Backlog (actionable now)", and "Once the
human-gated items are cleared" further down are **HISTORICAL — do not
action them.**

## v2 backlog (current, maintained by the brain each cycle — adopted 2026-07-20)

Task IDs, rationale, and acceptance criteria live in
`docs/planning/ROADMAP_REVIEW_2026-07-20.md`. Execution order: P0 → P1 →
P2, one loop cycle each; P3 items are founder decisions scheduled in
parallel. All tasks respect the Haiku-only lock (P1 tasks are fully
deterministic — no new API calls) and the existing loop protocol.

- **P0 (hygiene/unblocking): ~~ALL DONE~~ (cycles 24–26, 2026-07-20/21)**
  1. ~~**T-A** — retire stale roadmap sections + sync stale docs~~ — done.
  2. ~~**T-B** — vision-eval harness~~ — done; founder gate is now "drop
     screenshots into backend/eval/vision_cases/real/, run one command."
  3. ~~**T-C** — diagnosis retry hardening~~ — done.
- **P1 (retention loop): ~~ALL DONE~~ (cycles 27–34, 2026-07-21)**
  4. ~~**T-D** — daily habit loop v1~~ — done (streak/freezes/Today card/
     opt-in local reminders).
  5. ~~**T-E** — skill profile v1~~ — done (profile endpoint + Home
     surface).
  6. ~~**T-F** — reflection loop~~ — done (Flow D end to end).
  7. ~~**T-G** — review/spaced repetition~~ — done; the recorded
     deviation (static content-level variation instead of runtime
     shuffling, root `DECISIONS.md` → "2026-07-21 — T-G Shuffle
     Criterion Deviation Recorded") is now itself resolved — see T-G2
     below.
- **P2 (activation + v1 Must-Haves): T-H and T-I done; T-J code done,
  one owed action remains (below).**
  8. ~~**T-H** — onboarding + baseline (BRIEF Flow A), hosts notification
     opt-in~~ — done (cycle 35; also completes T-D's deferred
     "opt-in during onboarding" placement).
  9. ~~**T-I** — privacy policy/ToS, account-wide deletion, App Store
     disclosure + Nutrition Label mapping~~ — done (cycles 37–39;
     founder decisions recorded in `docs/planning/DECISIONS.md`). One
     audit follow-up → cycle 40: screenshot-mode consent copy must name
     the image sent to Anthropic.
  10. ~~**T-J** — backend auth (shared-secret bearer), rate limiting on
      coaching endpoints, deploy readiness~~ — code done (cycles 41–42).
      **One item this task cannot close by code: rotating the
      `ANTHROPIC_API_KEY` test key**, owed since the cycle-19 live
      smoke (test keys transited chat at founder's explicit
      acceptance). This requires the Anthropic console (no brain
      access) and an edit to `~/.env` (Bash cannot read that file by
      design). Founder action, whenever convenient: generate a new key
      → replace the value in `~/.env` → revoke the old one. Does not
      block anything else in the loop.
- ~~**T-G2** — deterministic runtime answer-option permutation~~ — done
  (cycle 43; root `DECISIONS.md` → "2026-07-21 — T-G2 Resolved").
  Backend-only, zero iOS changes needed.

## v3 roadmap — founder decisions resolved 2026-07-21, executing now

All four founder gates from the v2 backlog were resolved in one session
(decisions recorded in `docs/planning/DECISIONS.md`, four entries dated
2026-07-21: "Screenshot Vision-Quality Eval Deferred...", "T-K Paywall:
Infrastructure Now...", "T-L Free-Draft Grading Approved...", "Anthropic
Test-Key Rotation Scheduled..."). Two are pure deferrals (no code work);
two are now actionable and scoped below.

- **Deferred, not actionable (tracked, not blocking):**
  1. Real-screenshot vision eval — trigger: before wider/public launch.
  2. Anthropic test-key rotation — trigger: same as above; founder action
     only (console + `~/.env`), not reachable from this loop.
- **Actionable now, in priority order:**
  3. ~~**T-K (scoped): StoreKit 2 paywall infrastructure, flag off.**~~
     — done (cycle 44). Real StoreKit 2 purchase/restore/entitlement
     machinery shipped, flag off by default (app behavior unchanged).
     3 StoreKitTest-driven tests are an honest, documented `XCTSkip`
     (Apple platform limitation: `SKTestSession` needs Xcode's
     interactive Cmd+U path, not `xcodebuild test` CLI) — **run them
     manually via Xcode's Test navigator before ever flipping the flag
     on.**
  4. ~~**T-L (scoped): free-draft grading + $5/mo cost ceiling.**~~ —
     done (cycle 45). New `backend/app/draft_grading.py`: Haiku-locked
     grading adapter (reuses `COACHING_MODEL`) plus an in-memory
     UTC-calendar-month `DraftGradingBudget` (same architectural pattern
     as T-J's `_RateLimiter`) metering real per-token cost from every
     API response — including refused/failed attempts, which still cost
     money — against a hard $5/month ceiling. Budget admission is
     checked once per grading operation, before any retries; exceeding
     it fails closed (503, zero API calls made) rather than silently
     ungrading. `POST /lessons/{id}/draft-grading` serves it. iOS:
     `free_draft` parts gained an optional "Get feedback" flow
     (`LessonDetailViewModel.gradeDraft`, 5-state UI) fully orthogonal
     to lesson completion — completion gating is unchanged.
  Sequenced T-K before T-L: T-K is scoped, low-risk, self-contained
  infrastructure; T-L is new-surface work with a new cost-tracking
  mechanism, closer in nature to a feature build than scaffolding.

  **Both actionable v3 items are now done.** Only the two deferred,
  founder-gated items remain (real-screenshot vision eval; Anthropic
  test-key rotation) — neither is reachable from this loop; see above.

**2026-07-18: BUILD MODE — build start approved, scope gate
lifted.** Founder delegated the go/no-go to the brain (records: root
`DECISIONS.md` → "2026-07-18 — Build Start Approved; Content-Model-First
Sequencing"; `docs/planning/DECISIONS.md` → "2026-07-18 — Build Start
Approved (Founder Delegation)"). The loop now runs autonomous bounded
cycles under the existing safety rules (never force-push, clean-tree gate,
3-round cap, brain reviews everything before commit/push).

## v1 build backlog (COMPLETE 2026-07-19 — superseded by the v2 backlog above)

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
   b. ~~Lesson detail + completion flow~~ — done, accepted 2026-07-18
      (cycle 13). 10 tests green on sim (brain-run); narration model fix
      included. **The full learning loop is now usable in-app.**
   c. Coaching tab real UI once the pipeline exists.
7. Coaching pipeline: ~~design doc~~ (cycle 12); ~~text-path backend
   implementation~~ — done, accepted 2026-07-18 (cycle 14, 2 rounds).
   ~~(c) iOS Coaching tab~~ — done, accepted 2026-07-18 (cycle 15).
   **LOOP PAUSED — remaining work is founder-gated:** **(a)** live smoke
   run once founder confirms the key is in `~/.env` (watch-item: schema
   `minLength` is SDK-stripped — confirm the real call succeeds);
   **(b)** screenshot path — implementation could start mocked, but
   pinning the vision model requires the real-screenshot eval
   (COACHING_PIPELINE_V1 §6), which needs the key and founder-provided
   consented screenshots.

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

## Blocked on human action — HISTORICAL (Phase 0; superseded 2026-07-20, see v2 backlog)

- **CMA-enabled Anthropic API key**: `backend/scripts/provision_agents.py`
  needs a key with Claude Managed Agents beta access
  (`managed-agents-2026-04-01`) in `~/.env`. Without it, no live CMA call
  (agent/session/environment creation) can succeed.
- **Xcode**: the iOS target has only ever been syntax-checked
  (`swiftc -parse`) and xcodegen-validated, never compiled or run in
  Simulator — this machine has Command Line Tools only. Needs a Mac with the
  full Xcode app.

## Backlog (actionable now, no human gate) — HISTORICAL: DO NOT ACTION
<!-- Every file referenced below (recommend.py, progress.py, agents_setup.py,
coach.py, partner.py, ios/Core) was deleted in the 2026-07-18 Full Restart.
Kept for the record only; the v2 backlog at the top of this file is the
actionable list. -->

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

## Once the human-gated items are cleared — HISTORICAL: DO NOT ACTION
<!-- Superseded twice over: COACHING_PIPELINE_V1 §7 defers the CMA upgrade
entirely, and the 2026-07-19 Haiku-only lock removes the model tiering these
items assume. -->

6. Run `provision_agents.py` against the real API, confirm every CMA agent
   provisions successfully, commit the resulting `.provisioned.json` state
   (id/version bookkeeping only — no secrets in it).
7. First real Simulator run of the chat flow end to end; fix whatever
   breaks on actual compilation (expect some — iOS code has never been
   built, only parsed).
8. First live end-to-end coaching-report run (session end → coordinator →
   4 workers → synthesized report) against real CMA.

## Cycle log

- **2026-07-21 (no cycle dispatched — FOUNDER FLAG, two deeper-redesign
  items blocked, not deciding unilaterally):** Started reviewing
  `UI_IMPROVEMENT_PLAN.md`'s "Deeper redesigns" tier now that all 8 quick
  wins are done. Two items directly hit the founder's own standing
  deferral ("Defer the paywall-sequencing and Coach-tab structural
  decisions; flag them when you reach them instead of deciding myself,"
  approval message, this UI-plan execution):
  - **#1, Split navigation into Today/Learn/Coach:** the plan doc's own
    text (written before this deferral was reiterated) already flags a
    real open question inside this item — the research defines the new
    "Coach" tab as including free-draft grading, but that feature's
    actual UI entry point today lives inside `LessonDetailView` (reached
    via Learn, not Coach). Deciding whether to surface a Coach-tab link
    to it, or accept it stays contextually inside a lesson, IS the
    Coach-tab structural decision the founder reserved. Blocked.
  - **#2, Visual learning path:** structurally depends on #1's new
    `LearnView.swift` existing first. Blocked transitively.
  - **#5, Sequence the paywall after value, not before:** literally
    titled "paywall-sequencing" work. (The item's own text argues it
    "does not reopen" the T-K pricing/flag decision and needs no founder
    input to *plan* — that reasoning predates the founder's later,
    broader "defer... flag when you reach them" instruction, which names
    "paywall-sequencing" specifically and wins here. Deferring rather
    than relying on my own earlier annotation.) Blocked.
  - **#6, completion/streak/milestone motion:** partially depends on #1
    for its "new LearnView.swift" unit-completion piece only; the
    `TodayCard`/`LessonDetailView` streak-flame and lesson-completion
    motion pieces don't depend on #1. Will scope narrowly to the
    unblocked pieces when reached.
  - **#7, preview/snapshot matrix:** not an independently-dispatchable
    item — an ambient discipline to apply while rebuilding the other
    components, per its own text.
  - **#8, five usability sessions:** not a code task at all; requires the
    founder to actually recruit and run sessions with real users. Left on
    the backlog, not actionable by this loop.
  **Not stopping the whole loop over this** — proceeding with the
  unblocked items in written order: **#3 (step-based lesson flow) next**,
  then **#4 (narrative report reveal + trend visualization)**. Both are
  fully self-contained, don't touch the tab structure, and were already
  read/verified in full when the plan was written. Will re-check whether
  #1/#5 have been unblocked before reaching #6.

- **2026-07-21 (no cycle dispatched — quick win #8 closed as already
  done):** Re-read `UI_IMPROVEMENT_PLAN.md`'s "8. Empty-state copy pass
  for coaching history" against the current
  `CoachingHistoryView.coachingHistoryEmptyState` (shipped cycle 51,
  quick win #5a). #8's entire stated acceptance criterion — "show one
  sample report card and 'Analyze your first conversation'" replacing
  the bare `ContentUnavailableView` — is already fully delivered
  verbatim: the sample "Focus: Curiosity" report-row mockup and the
  "Analyze your first conversation" button both exist today, screenshot-
  verified in cycle 51. #8's own "current state" description (the bare
  `ContentUnavailableView`) is stale, describing pre-#5a code. No worker
  dispatched — nothing left to build. **All 8 quick wins are now
  complete** (1–4, 5a, 5b, 6, 7 shipped across cycles 47–54; 8 subsumed
  by 5a). **Next:** deeper redesigns, starting with #1 — split navigation
  into Today / Learn / Coach.

- **2026-07-21 (cycle 54 — UI quick win #7: defer the notification-
  permission ask; ONE ROUND, accepted as specified):** Worker:
  `gpt-5.6-terra`. Onboarding shortened from 4 steps
  (`goal → context → baseline → reminder`) to 3
  (`goal → context → baseline`) — the `.reminder` step (which embedded
  `ReminderSettingsControls` and could trigger the real
  `UNUserNotificationCenter` OS prompt before the user had done anything
  in the app) is gone entirely. No functionality lost: `TodayCard`'s
  always-visible bell icon (Home tab, first screen after onboarding)
  already reaches the exact same `ReminderSettingsControls` /
  `ReminderSettingsViewModel` flow independently — confirmed untouched.
  `canAdvance`, the terminal-step button branch (now `.baseline` shows
  "Get started" instead of `.reminder`), and `OnboardingView`'s now-dead
  `reminderViewModel`/`reminderScheduler` property and init parameter all
  correctly removed. Worker grepped for other `OnboardingView(` call
  sites before deleting the init parameter (only `RootView.swift`, which
  doesn't pass it explicitly, so no other call site broke). Test fix:
  `testOnboardingViewModelProgressesAndPostsExactPayload`'s now-invalid
  extra `advance()` + `.reminder` assertion replaced with a direct
  `.baseline` assertion before `submit()`; worker additionally caught and
  cleaned up a second, harmless-but-now-redundant `advance()` call in
  `testOnboardingStateFreshSuiteSkipAndFinishPersist` (would have been a
  silent no-op under the new 3-case enum, not a failure, but correctly
  tidied anyway) — broader and more thorough than what the spec
  explicitly named.
  **Brain verification:** full source review found no bugs. `xcodegen
  generate` + `xcodebuild build`/`test` — 76 passed, 3 pre-existing
  skips, 0 failures. Visual check via fresh onboarding state: discovered
  along the way that `xcrun simctl uninstall` on this simulator reports
  success but does **not** actually clear the app's `UserDefaults` (a
  simulator/tooling characteristic, not a product bug — confirmed by
  reading the flag immediately after uninstall, before any reinstall,
  and finding it unchanged) — noted for future cycles' own verification
  hygiene; likely means cycle 51's "fresh install" empty-state check
  worked because that persistent user genuinely had zero reports, not
  because the install was actually fresh. Worked around by deleting the
  specific `smalltalkCoach.hasCompletedOnboarding` key directly via
  `defaults delete`, which does work reliably. Confirmed: (1) fresh
  onboarding entry shows the `.goal` step with a progress bar correctly
  reflecting 3 total steps, not 4; (2) via a temporary, fully-reverted
  one-line default-value change (`step: Step = .goal` → `.baseline`, the
  same class of temporary diagnostic edit used in prior cycles, reverted
  and confirmed clean via `git diff` before finalizing), the terminal
  `.baseline` step correctly shows a full progress bar, a "Get started"
  button (not "Continue"), a "Back" button, and no reminder content
  anywhere. Final real (non-diagnostic) build reinstalled and left with
  onboarding reachable, so the founder can see the shortened flow
  firsthand on next launch. **Next:** quick win #8 — empty-state copy
  pass for coaching history. **Scoping note carried forward:** #8's
  entire acceptance criterion (sample report card + "Analyze your first
  conversation" CTA replacing the generic `ContentUnavailableView`) was
  already fully delivered by #5a's `CoachingHistoryView` rework (cycle
  51) — will confirm against the plan's exact wording and either mark #8
  done-via-#5a with no new dispatch, or dispatch only a narrow residual
  if the plan's text asks for anything #5a didn't cover.

- **2026-07-21 (cycle 53 — UI quick win #6: MotionPolicy + Dynamic Type
  spot-check; ONE ROUND, accepted as specified):** Worker: `gpt-5.6-terra`.
  New `ios/SmallTalkCoach/MotionPolicy.swift`: a pure
  `MotionPolicy.animation(_:reduceMotion:) -> Animation?` helper, and a
  `motionAwareAnimation(_:value:)` View modifier (reads
  `@Environment(\.accessibilityReduceMotion)` centrally, so call sites
  that only need "animate this unless reduced" no longer need their own
  environment read). Both existing hand-rolled call sites now route
  through it: `SkeletonBlock`'s pulse `.animation(...)` call uses
  `MotionPolicy.animation(...)` directly (keeps its own `@Environment`
  read — still needed for `opacity`/`onAppear`/`onChange`, so this is a
  consistency win not a full rewrite); `ExampleResponseSuggestion`'s
  `setCopied` dropped its manual `if reduceMotion {...} else {
  withAnimation {...} }` branch entirely in favor of
  `.motionAwareAnimation(AppTheme.Motion.quick, value: isCopied)` on the
  view, simplifying `setCopied` to a single line (its now-unused
  `@Environment` property was correctly removed, not left dangling).
  **A real, previously-ungated gap closed:** `CardStyle`'s `.interactive`
  press feedback (`.scaleEffect`/`.brightness` on press) had zero Reduce
  Motion accommodation before this cycle. Now: `.scaleEffect` is pinned
  to `1` (no spatial squish at all) whenever Reduce Motion is on —
  exactly the "travel/scale" effect the research calls out — `.brightness`
  is kept unconditionally (a subtle tint change, not spatial, judged fine
  either way), and the animation call itself now routes through
  `.motionAwareAnimation`, so under Reduce Motion the remaining
  brightness-only feedback applies as an immediate state change rather
  than animated, matching the research's "or immediate state changes"
  wording precisely. Dynamic Type spot-check (bounded, per spec) across
  the seven files touched by quick wins #1–#5b: worker reported no clear
  clipping risk found, no files needed changing — **independently
  verified**, not taken on faith: `grep` for `.lineLimit(` and any fixed
  `.frame(height:...)`/`.frame(width:...height:...)` across all seven
  files returned zero matches for either pattern.
  **SDK note, consistent with cycle 51's finding:** the worker
  independently hit the same read-only `accessibilityReduceMotion`
  preview-override constraint (Xcode 26.6/iOS 26.5 SDK) — and this time,
  critically, did **not** reach for the private `_accessibilityReduceMotion`
  SPI workaround that had to be rejected twice last cycle. Instead
  `MotionPolicy.swift`'s two previews demonstrate the pure helper
  function directly with an explicit `reduceMotion: Bool` preview
  parameter rather than trying to force the real environment key —
  compiles clean on public API only. Trade-off, disclosed rather than
  hidden: this means the previews prove the helper's nil/non-nil logic
  correctly, but don't exercise the modifier's actual environment-read
  path end-to-end in Xcode's canvas — judged acceptable given
  environment-*reading* (as opposed to the write/override side that
  actually failed) is long-established, reliable SwiftUI behavior used
  correctly at every real call site.
  **Brain verification:** full source review of all four parts found no
  bugs. `xcodegen generate` + `xcodebuild build`/`test` — 76 passed, 3
  pre-existing skips, 0 failures, matching baseline. **Honest scoping
  note:** this cycle's actual behavior change is animation-gating logic
  (`Animation` vs. `nil`), which a static screenshot cannot distinguish —
  both an animated and an instant transition settle at the identical
  final visual state, and the affected components' settled appearance was
  already screenshot-verified in cycles 51–52. Did the mandatory real
  simulator launch check instead (required every cycle regardless): app
  launched clean, Home tab rendered correctly with live streak/lesson
  data, no crash, no visual regression (incidentally also confirmed the
  pre-existing "How did it go?" reflection prompt — v2-backlog Flow D,
  unrelated to this cycle — correctly triggering from this session's own
  repeated test launches). **Next:** quick win #7 — move the
  notification-permission prompt later in onboarding
  (`OnboardingView.swift`).

- **2026-07-21 (cycle 52 — UI quick win #5b: copy-to-clipboard + toast +
  haptic; ONE ROUND, accepted as specified):** Worker: `gpt-5.6-terra`.
  `ExampleResponseSuggestion` (in `CoachingView.swift`, previously plain
  quoted text with no copy action) gained a trailing icon button
  (`doc.on.doc`, teal, `AppTheme.Spacing.minimumTapTarget`-sized hit
  area). Tapping it: copies the exact source `text` via
  `UIPasteboard.general.string`; fires `.sensoryFeedback(.success,
  trigger: copyCount)` (`copyCount` increments on every tap rather than
  toggling a `Bool`, so the haptic correctly re-fires even on rapid
  repeat taps — better than the letter of the spec, which just asked for
  "some Equatable state that flips"); swaps the icon to a checkmark with
  a "Copied" label for ~1.5s via a cancellable `Task` (cancels any
  in-flight revert before starting a new one, avoiding a race where a
  stale revert could fire after a newer tap); and posts a live
  `UIAccessibility.post(.announcement, "Copied")` in addition to
  updating the button's own `.accessibilityLabel`/`.accessibilityHint` —
  exceeds the spec, which only asked for the label update. Reduce Motion
  respected via the same `@Environment(\.accessibilityReduceMotion)`
  read established in `SkeletonBlock.swift`: animated with
  `AppTheme.Motion.quick` when off, state changes instantly with no
  transition when on. No new dependency added (per spec — built native
  rather than adopting `exyte/PopupView`, consistent with the
  `SkeletonBlock`-over-`SwiftUI-Shimmer` precedent from the previous
  cycle). Existing outer `.accessibilityLabel("Example response to
  adapt: …")`, padding, background, and corner radius all left
  untouched as required.
  **Brain verification:** full source review found no bugs. `xcodegen
  generate` + `xcodebuild build`/`test` on iPhone 16/iOS 18.2 — 76
  passed, 3 pre-existing skips, 0 failures, matching baseline, and this
  time the build compiled clean on the first pass (no SDK surprises like
  cycle 51's). Visual check via a temporary diagnostic-harness swap
  (`SmallTalkCoachApp.swift` repointed, `ExampleResponseSuggestion`'s
  `private` briefly relaxed to reach it directly, both fully reverted
  after): idle-state button renders correctly in light and dark — clean
  teal icon, no crowding from the 44pt tap target inside the card's 12pt
  padding, consistent with the existing quote icon's styling. **Honest
  scoping note:** the live tap → copy → checkmark/"Copied" → revert
  interaction cycle itself was not exercised end to end — same
  structural limitation noted all session (no Accessibility permission
  for scripted simulator taps, and standing up a throwaway XCUITest
  target just for this one low-risk check wasn't judged worth the added
  infrastructure). Confidence instead rests on the idle-state visual
  confirmation plus a line-by-line review of the tap handler, state
  machine, and cancellation logic, all of which are straightforward and
  use standard, SDK-verified-compiling APIs (unlike cycle 51's private-API
  near-miss, nothing here is exotic). **Next:** quick win #6 — Reduce
  Motion + XXL Dynamic Type scaffolding (`MotionPolicy`).

- **2026-07-21 (cycle 51 — UI quick win #5a: skeleton loading states +
  richer coaching-history empty state; THREE ROUNDS, accepted):** Worker:
  `gpt-5.6-terra`. New `SkeletonBlock` primitive (subtle
  `AppTheme.Colors.primary`-tinted rounded rect, pulse animation,
  static Reduce-Motion fallback) applied to all five scoped loading
  spots (`HomeView` curriculum, `CoachingView`'s `.checking` state,
  `CoachingHistoryView` loading, `ProfileView`, `LessonDetailView`),
  each composed into a shape-appropriate silhouette (row/card stacks
  matching the eventual content) rather than one undifferentiated
  block. `CoachingHistoryView`'s empty state replaced with a headline,
  a static sample report-row mockup, supporting copy, and an "Analyze
  your first conversation" button wired through a new
  `onStartComposing` closure (default `{}`, threaded from
  `CoachingView`'s `NavigationLink("History")` call site) that resets
  the composer and dismisses back via `NavigationStack`'s
  `@Environment(\.dismiss)`. `ProfileView`'s existing empty-state copy
  left untouched per spec.
  **Round 1** (worker self-reported "partial," sandbox had no simulator
  runtime): source review of all five files found the composition,
  token usage, and accessibility collapsing (`.accessibilityElement
  (children: .ignore)` + a single descriptive label, so VoiceOver
  doesn't read out placeholder blocks) all correct — but the brain's
  own independent `xcodebuild build`/`test` (Xcode 26.6, iOS 26.5 SDK)
  failed outright: `SkeletonBlock.swift`'s second `#Preview` used
  `.environment(\.accessibilityReduceMotion, true)`, and
  `accessibilityReduceMotion` has no public setter in this SDK
  (`KeyPath` vs required `WritableKeyPath`) — confirmed not a local
  shadowing issue (no custom `EnvironmentValues` extension anywhere in
  the codebase). This failed the whole target, so 0 of 76 tests ran;
  the worker's own sandbox couldn't have caught it (its log already
  flagged that Preview-macro type-checking is blocked there). Also
  flagged in the same round: `opacity` computed `1.15` for the pulsed
  state, outside SwiftUI's valid `0...1` range (silently clamped, not
  broken, just imprecise). Rejected with both itemized.
  **Round 2:** fixed the opacity bound to `1.0` correctly, but "fixed"
  the compile error by switching to `\._accessibilityReduceMotion` — a
  leading-underscore SwiftUI symbol, i.e. private/unsupported SPI, not
  public API. It compiles and is confined to a `#Preview` block (never
  ships in the archived binary, so zero App Store risk), but the brain
  rejected it anyway: private-API patterns shouldn't sit in the
  codebase even in dead preview code, since it invites copy-paste into
  code that does ship, and a fully safe fallback (delete the one
  preview variant) was already pre-approved in the round-2 spec.
  **Round 3 (final, at the loop's 3-round cap):** worker deleted the
  `.environment(\._accessibilityReduceMotion, true)` line and the
  `#Preview("Skeleton blocks — Reduce Motion")` block it lived in,
  leaving the primary preview and the legitimate public, read-only
  `@Environment(\.accessibilityReduceMotion)` production usage
  untouched. Verified clean: `grep` confirms zero `_accessibilityReduceMotion`
  references remain and exactly one `#Preview` block.
  **Brain verification (independent):** `xcodegen generate` +
  `xcodebuild build`/`test` on iPhone 16/iOS 18.2 — 76 passed, 3
  pre-existing skips, 0 failures, matching baseline exactly. Visual
  check via three diagnostic-harness swaps (`SmallTalkCoachApp.swift`
  temporarily repointed, plus a temporary, fully-reverted
  `private struct` → `struct` relaxation on `CoachingHistoryView` to
  reach it directly), each reverted before finalizing: (1)
  `SkeletonBlock`'s own preview content, light + dark — clean, subtle
  placeholder blocks, pulse cap looks correct; (2) `CoachingHistoryView`'s
  new empty state on a fresh install (zero reports, real backend),
  light + dark — headline, sample "Focus: Curiosity" card, supporting
  copy, and the full-width "Analyze your first conversation" button all
  render correctly and legibly, "Delete all coaching data" still
  present below and unbroken; (3) the real `HomeView` curriculum
  loading skeleton via a temporary `UserDefaults` base-URL override
  (`smalltalkCoach.apiBaseURL` → a non-routable address, so the fetch
  hangs indefinitely instead of failing fast) on a real app launch —
  title/header lines, a Today-card-shaped block, and three lesson-row
  shapes (leading circle, two lines, trailing badge) all in correct
  proportion, tab bar intact. Override removed and app relaunched
  against the real backend afterward to confirm a normal working state
  (Today card, skill-profile prompt, Unit 1 list all rendering live
  data correctly, no regression from cycles 47–50). The remaining two
  skeleton spots (`CoachingView`'s `.checking` state,
  `LessonDetailView`) were not individually screenshotted — same
  primitive, same established composition pattern already visually
  confirmed twice above, and both passed full source review.
  **Side finding, not a defect in this cycle, worth a future backlog
  line:** `AppSurface`/`.appSurface()` (the full-screen branded
  background built in cycle 47) is applied in zero real screens today —
  `grep` shows it used only inside component `#Preview` blocks; `RootView.swift`'s
  `TabView` doesn't apply it either. Every screen (`HomeView`,
  `CoachingView`, `ProfileView`, `LessonDetailView`) currently renders
  on the plain system background in every state. Not blocking — quick
  win #2 only asked for `TodayCard`'s own card-level surface, not a
  screen-wide rollout — but flagging so it doesn't stay silently unused
  indefinitely; candidate for a future quick win or one of the deeper
  redesigns. **Next:** quick win #5b — copy-to-clipboard + toast +
  success haptics for `ExampleResponseSuggestion` in
  `CoachingReportView` (explicitly deferred out of 5a's scope).

- **2026-07-21 (cycle 50 — UI quick win #4: reorder the coaching report;
  ONE ROUND, accepted as specified):** Worker: `gpt-5.6-terra`. Pure
  `Section` reorder inside `CoachingReportView` — no internals touched,
  verified by tracing the diff line-by-line: intro (unchanged) →
  Takeaway (moved up from position 7) → How to respond (moved up from
  position 6) → interpretation (moved down from position 2) →
  strengths → improvements (both unchanged relative position) → scores
  (moved down from position 3, now second-to-last before practice/
  lesson) → practice action → recommended lesson. Exact match to spec.
  Brain verification: full test suite re-run clean on the diff alone
  (76 passed, 3 pre-existing skips, 0 failures, matching baseline) run
  *before* adding any diagnostic scaffolding, to keep that signal
  uncontaminated. For the visual check, built a temporary diagnostic
  harness that calls the real `APIClient().diagnose(...)` against the
  live local backend and feeds the actual `CoachingReport` response
  into `CoachingReportView` directly — reusing production code instead
  of hand-constructing a mock report. A `with_user_reply` test (real
  "Me:" reply included, expected to exercise the now-relocated scores
  section) hit the same pre-existing diagnosis-validation bug flagged
  during last week's live E2E verification session (focus_dimension
  frequently doesn't match the weakest score, exhausting all retries) —
  confirmed unrelated to this cycle (that bug lives entirely in
  `backend/app/diagnosis.py`, untouched here, and the failure mode is
  identical to what was already documented). Fell back to a
  `stimulus_only` request (no scores expected), which succeeded and
  showed the report opening with Takeaway then How to respond exactly
  as reordered — live confirmation of the first two moved sections.
  The scores section's new position is accepted on the strength of the
  line-by-line diff trace alone, not a live screenshot, because the
  only way to exercise it today runs into the separate, already-known,
  not-yet-fixed backend bug. Documented honestly rather than either
  blocking this UI cycle on an unrelated backend fix or silently
  claiming visual verification that didn't happen. **Standing
  reminder, restated:** that diagnosis bug is still unfixed and still
  the founder's call — offered during the live E2E session, not yet
  answered. **Next:** quick win #5 — skeleton loading states, richer
  empty states, copy toast, and success haptics across `HomeView`,
  `CoachingView`'s history, `ProfileView`, and `LessonDetailView`.

- **2026-07-21 (cycle 49 — UI quick win #3: explicit Coach mode cards;
  ACCEPTED, unusual provenance):** Worker: `gpt-5.6-terra`. The worker's
  own dispatch process was externally killed mid-run (status: "killed" —
  a harsher variant than every prior cycle's "no simulator runtime
  available": this time `CoreSimulatorService connection became
  invalid" mid-command, still the same underlying sandbox limitation,
  just a worse symptom of it), before it could append its own
  `WORKER_LOG.md` entry. `git status` showed the two authorized files
  (`CoachingView.swift`, `CoachingViewModel.swift`) already modified and
  nothing else — the code changes themselves were complete, only the
  process supervising them wasn't. The brain read the resulting diff in
  full rather than discarding and re-dispatching from scratch: it
  matched spec closely enough (verbatim research copy for the mode-card
  subtitles, `CoachingReplyMode` correctly reset in
  `beginNewComposition()`, mode-aware text/screenshot prompts, a "Change"
  affordance, three previews) to be worth verifying rather than
  redoing. Brain appended an explicitly self-labeled brain-authored
  `WORKER_LOG.md` entry in place of the missing worker one — honest
  about provenance rather than backfilling as if the worker had written
  it — then ran the loop's normal full acceptance bar itself: full
  build + test suite (76 passed, 3 pre-existing skips, 0 failures,
  matching baseline), and real simulator screenshots via a temporary
  diagnostic entry-point swap (reverted after) covering the
  mode-selection screen and the "Review my reply" composer state in
  both light and dark mode. Everything rendered correctly — mode cards
  legible and correctly styled, mode-aware placeholder copy exactly as
  specified, disclosure/consent/submit sections untouched. A brain
  verification follow-up entry was appended to `WORKER_LOG.md`
  documenting the completed check (append-only — the original entry
  wasn't edited). ACCEPTED. **Process note:** a killed worker process
  with a partial-but-complete diff doesn't automatically mean redo from
  scratch — reading the actual diff before deciding saved a full cycle
  here, but the honesty obligation (don't claim work is worker-verified
  when it wasn't) still has to be met explicitly, not skipped. **Next:**
  quick win #4 — reorder the coaching report so takeaway and next move
  come before scores (`CoachingView.swift`'s `CoachingReportView`).

- **2026-07-21 (cycle 48 — UI quick win #2: branded Today header +
  elevated Daily Mission card; ONE ROUND, accepted as specified):**
  Worker: `gpt-5.6-terra`. First cycle to actually apply quick-win-#1's
  tokens to a real, already-shipped screen. `TodayCard.swift`: wrapped in
  `.cardStyle(.highlighted)`, full `AppTheme.Typography`/`.Spacing`
  adoption, the lesson/review `NavigationLink` restyled as a full-width
  primary CTA (brand-indigo background, white text, correctly *not*
  forced through `PrimaryActionButton` — that component's closure/state
  shape doesn't fit a navigation link, and the spec said not to bend it).
  A real content-model gap surfaced during the plan review carried
  through correctly: there is no duration field anywhere in
  `CONTENT_MODEL_V1.md` or the lesson JSON (verified by grep before
  writing the spec), so rather than fabricate per-lesson precision the
  card shows a rough, honestly-`~`-prefixed type estimate ("~3 min"
  lesson / "~2 min" review) — flagged in both the spec and the worker's
  own log as a placeholder pending a real content-model decision, not a
  finished measurement. The "why it matters" line — previously shown
  only when onboarding-personalization data existed, silently blank for
  anyone who skipped onboarding — now always renders: the personalized
  line when available, an honest generic fallback otherwise.
  `HomeView.swift`'s only change was `.listRowBackground(Color.clear)` +
  `.listRowSeparator(.hidden)` on the Today row so the new elevated card
  doesn't sit inside conflicting default List chrome — no section/
  navigation restructuring, exactly as scoped. Brain verification:
  grepped the diff for stray `Color.primary`/system-color usage (the
  exact bug class from cycle 47) — clean, none found. Full test suite
  re-run independently: 76 passed, 3 pre-existing skips, 0 failures,
  matching baseline. Real simulator screenshots (not a diagnostic
  harness this time — `RootView` itself now renders the change) in both
  light and dark mode: elevated card reads clearly distinct from the
  plain "Your skills"/unit-list rows below it, CTA button fully legible
  in both appearances, dark-mode indigo correctly uses the asset
  catalog's dark variant. Even the pre-existing reminder-bell icon
  picked up the new brand indigo automatically via the `AccentColor`
  asset set in cycle 47 — an unplanned, welcome consistency win from
  having the token system in place before touching real screens. One
  unrelated finding during verification, not a regression: a stale
  "How did it go?" reflection sheet appeared on first screenshot,
  traced to leftover `PendingReflectionStore` (`UserDefaults`-backed)
  state from earlier sessions' testing on the same simulator, not
  anything this cycle touched — resolved by a clean uninstall/reinstall,
  which is now the standing practice for future screenshot checks in
  this plan's remaining cycles. ACCEPTED as specified — zero rounds of
  rejection. **Next:** quick win #3 — explicit Coach mode cards ("Help
  me reply" / "Review my reply") in `CoachingView.swift`.

- **2026-07-21 (cycle 47 — UI quick win #1: design tokens foundation;
  TWO ROUNDS, accepted after fix):** Worker: `gpt-5.6-terra`. Round 1
  added `AppTheme` (colors/spacing/radii/typography/motion tokens),
  a new `Assets.xcassets` catalog (9 colorsets — verified every single
  light/dark hex value byte-for-byte against spec, including the
  Okabe-Ito colorblind-safe skill-dimension palette), `AppSurface`,
  `CardStyle`, and `PrimaryActionButton` — all foundation-only, zero
  existing screens touched. Reading the code alone, everything looked
  right. It wasn't: the brain built a temporary, uncommitted diagnostic
  harness (a scratch view wired briefly into the app's entry point,
  reverted before either round's diff was finalized) specifically to
  *see* the new components rendered, rather than trusting the code read
  — and caught a real bug that pure review missed. `CardStyle`'s
  `.standard`/`.interactive` background used SwiftUI's system
  `Color.primary` (adaptive black/white foreground color) instead of
  the new `AppTheme.Colors.primary` (brand indigo) — rendering as a
  near-black card with near-illegible near-black text in light mode,
  and the inverse in dark mode. `PrimaryActionButton`, written in the
  same round, correctly used `AppTheme.Colors.primary` throughout,
  confirming this was a naming mix-up rather than a knowledge gap.
  Rejected with a precise, isolated spec (one file, two fix paths
  offered). Round 2 used a 6% brand-indigo tint instead, computed and
  reported contrast ratios (18.03:1 light, 17.27:1 dark — both far
  above WCAG AA), and the brain re-verified this claim the same way it
  caught the original bug: rebuilt the same diagnostic harness,
  screenshotted both appearances again, confirmed both variants now
  render as legible, subtly-tinted cards with no regression to the
  already-correct `.highlighted`/`.warning` variants or to
  `AppSurface`/`PrimaryActionButton`. Full iOS suite re-run after
  cleanup: 76 passed, 3 pre-existing skips, 0 failures — identical to
  the pre-cycle baseline, confirming this foundation-only cycle changed
  zero existing behavior as intended. File scope both rounds matched
  spec exactly. ACCEPTED. **Process note for future foundation-style
  cycles:** build-and-screenshot beat code-review alone here — worth
  defaulting to a quick throwaway render check on any new visual
  component, not just screens with existing users to protect.
  **Next:** quick win #2 — branded Today header + elevated Daily
  Mission card (`HomeView.swift`, `TodayCard.swift`), the first cycle
  that actually applies these tokens somewhere real.

- **2026-07-21 (cycle 46 — micro-cycle: disclose free-draft grading in
  the privacy policy; ONE ROUND, accepted as specified):** Worker:
  `gpt-5.6-terra`. Closed the gap cycle 45 flagged: `PRIVACY_POLICY.md`'s
  "How AI coaching works" section named only conversation text and
  screenshots as sent to Anthropic, and asserted "this is the only
  third-party sharing described in this policy" — false the moment
  free-draft grading shipped. New paragraph discloses the draft-grading
  flow accurately (separate from the coaching consent toggle — there
  isn't one for this feature, matching the actual code; draft text +
  practice prompt sent to Anthropic; nothing persisted server-side).
  The self-contradicting sentence was replaced with a standalone true
  claim ("Anthropic is the only third party we share data with") that
  stays true regardless of how many distinct scenarios involve
  Anthropic, rather than patched with a second, competing "only"
  claim. Verified myself: the non-persistence claim is true against
  `grade_lesson_draft` (no `store.*` call in that function — confirmed
  by re-reading the code, not by trusting the worker's report, which
  itself said it had checked the same code before writing the claim);
  diff scope limited to the two allowed files; read the full updated
  section end-to-end for internal consistency. ACCEPTED as specified —
  zero rounds of rejection. **Next:** none — the v3 roadmap's two
  actionable items and this follow-up are all shipped; only the two
  deferred founder-gated items remain (real-screenshot vision eval,
  Anthropic test-key rotation), neither reachable from this loop.

- **2026-07-21 (cycle 45 — T-L: free-draft grading + $5/mo cost ceiling;
  ONE ROUND, accepted as specified):** Worker: `gpt-5.6-terra`. Backend:
  `draft_grading.py` mirrors `diagnosis.py`'s adapter/retry structure
  (lazy client, 3-attempt bounded retry, 5xx/429-retry vs.
  other-4xx-raise-immediately, refusal never retried) with its own
  minimal 2-field JSON schema (`met_criteria`, `feedback`) rather than
  reusing the diagnosis contract, which doesn't fit an open-ended
  writing exercise. `DraftGradingBudget` is Lock-guarded, resets on UTC
  calendar-month rollover (December→January verified by test), and the
  brain's spec called for a specific, easy-to-get-wrong ordering that
  the worker implemented exactly: budget admission (`has_room`) is
  checked once before the retry loop begins, but `record_cost` runs
  immediately after every `adapter.request()` call returns — before
  parsing or validating the payload — so a refused or malformed
  response still meters its real cost; only a request that never
  reaches the provider (budget already exhausted) costs nothing.
  Verified this specific invariant myself: budget-exceeded makes zero
  adapter calls (asserted via a call counter), and a refusal both
  raises `DraftGradingRefusedError` *and* increases recorded spend in
  the same test. Pricing verified live against
  `platform.claude.com/docs/en/about-claude/models/overview` the same
  session before writing the spec — Haiku 4.5 is $1.00/MTok input,
  $5.00/MTok output, matching the cached skill data with no drift.
  `POST /lessons/{id}/draft-grading` follows its sibling
  `/complete`/`/review` endpoints' conventions exactly (404
  `lesson_not_found`/`content_pending`, 422 for bad part index/kind/
  draft length) plus new 422 `draft_grading_refused` and 503
  `draft_grading_budget_exceeded` (with `resets_at`) — deliberately
  *not* rate-limited like `/coaching/diagnoses`, matching its immediate
  siblings rather than the differently-shaped coaching router. iOS:
  `LessonDetailViewModel` gained `draftGradingStates` and `gradeDraft`;
  `LessonDetailView` gained a conditional "Get feedback" button and a
  5-state render (idle/grading/graded/budgetExceeded/failed) with
  copy updated off the old "not submitted" framing. Worker's own test
  for the `.grading` transition used a `CheckedContinuation` to
  deterministically suspend the fake adapter and assert the
  intermediate state — beyond what the spec asked for, and correctly
  reasoned given that state is otherwise a race to observe. Both new
  ViewModel tests and the endpoint tests explicitly re-assert
  `canSubmit`/`submissionAnswers` are byte-for-byte unaffected by
  draft-grading state, matching the spec's hard orthogonality
  constraint. Brain verification (own run, not the worker's — worker's
  sandbox lacked a simulator runtime): backend 128 passed / 1
  pre-existing unrelated skip (`test_live_smoke.py`, gated on
  `SMALLTALK_LIVE_SMOKE=1`); iOS 76 passed / 3 pre-existing skips (the
  T-K StoreKit skips, correctly untouched) / 0 failures, all 3 new
  tests independently re-run in isolation to confirm; full diff read
  file-by-file against the spec; fresh build + install + launch on
  iPhone 16 clean (Home screen renders, no crash) — did not attempt
  deeper UI-automation navigation into the lesson screen itself
  (`simctl` has no synthetic-tap primitive; judged the marginal
  confidence not worth the fragility given compilation success +
  thorough ViewModel-level state-transition coverage already
  constrain the residual risk to pure SwiftUI rendering, which a
  launch-clean build partially covers via shared Codable/Models.swift
  paths). File scope matched the spec exactly (`diagnosis.py`,
  `coaching.py`, and all completion-gating logic untouched). ACCEPTED
  as specified — zero rounds of rejection. **Follow-up flagged by the
  worker, not yet actioned:** `docs/legal/PRIVACY_POLICY.md`'s
  Anthropic-disclosure wording currently names conversation
  text/screenshots but not practice drafts; drafts are now genuinely
  sent to Anthropic for grading, so this is a real wording gap, not
  speculative. **Next:** a small, separately-scoped docs-only
  micro-cycle to close that gap — this is a doc-completeness fix
  syncing disclosure to founder-approved functionality already shipped
  in this cycle, not a new product decision, so no founder gate blocks
  it.

- **2026-07-21 (cycle 44 — T-K: StoreKit 2 paywall infrastructure, flag
  off; FOUR ROUNDS — 3-round cap + one correctly-scoped follow-up):**
  Worker: `gpt-5.6-terra`. Round 1 shipped real StoreKit 2 mechanics
  (`PurchaseManager`: verify-before-grant via `checkVerified`, finish
  strictly after entitlement confirmed, continuous `Transaction.updates`
  observation, `currentEntitlements` as source of truth, restore via
  `AppStore.sync()`; `PaywallView`; `FeatureFlags.paywallEnabled = false`
  compile-time constant; Units 2–4 gated behind the flag via a pure,
  independently-tested `LessonPaywallAccess.isGated` function, Unit 1
  and coaching left ungated per the founder decision; local
  `.storekit` config file, no App Store Connect) — but brain's own
  simulator run (not the worker's, whose sandbox can't reach
  CoreSimulatorService) found 3 real StoreKitTest failures. Round 2:
  brain's own fix hypothesis (wire `storeKitConfiguration` into the
  scheme's `test:` action) was WRONG — asserted from memory without
  checking, violating the project's own vendor-verification discipline;
  confirmed wrong by inspecting the generated `.xcscheme` XML directly
  (no `StoreKitConfigurationFileReference` under `<TestAction>`).
  Round 3 (final under the cap): brain fetched XcodeGen's actual
  `Scheme.swift` source from GitHub — confirmed `Test` has no
  `storeKitConfiguration` property at all (only `Run` does) — and
  redirected to the real fix (explicit test-target resource entry,
  mirroring the existing l01-JSON precedent). Verified empirically that
  the file DID land in the built `.xctest` bundle — yet the identical
  XPC error persisted. Root-caused via research to a documented Apple
  platform limitation: `SKTestSession` requires Xcode's interactive
  Cmd+U test path to sync a StoreKit Configuration into the simulator;
  `xcodebuild test` from the CLI does not, producing exactly this XPC
  error — a tooling gap, not a code defect (confirmed via careful
  independent line-by-line review of `PurchaseManager.swift`, which
  correctly implements every required pattern). A 4th, differently-
  scoped micro-cycle (not a 4th attempt at the same fix — the cap
  wasn't violated) marked the 3 environment-blocked tests as an honest
  `XCTSkip` with the documented reason, original assertions preserved
  as unreachable documentation of intent. Brain verification: **73
  tests, 0 failures, 3 documented skips** (own run); flag-off identical
  behavior confirmed both structurally (code short-circuits before
  `isPremium`/unit checks) and via live launch screenshot matching
  every prior session capture; mandatory simulator launch clean —
  ACCEPTED. **Follow-up for whoever eventually verifies a real
  purchase/restore flow before enabling the flag: run the 3 skipped
  tests manually via Xcode's Test navigator (Cmd+U), not CI/CLI.**
  **Next:** T-L (free-draft grading + $5/mo ceiling).

- **2026-07-21 (cycle 43 — T-G2: deterministic runtime answer
  permutation; v2 backlog's actionable items now exhausted):** Worker:
  `gpt-5.6-terra`, one round. New `_shuffled_lesson_content()` (backend
  only, `random.Random(f"{user}:{lesson}:{attempt}:{part}").shuffle`,
  builds entirely fresh dicts/lists — never mutates
  `app.state.curriculum`) called identically by `GET /lessons/{id}` and
  both completion endpoints, keyed on the new `store.review_count()`;
  confirmed pre-implementation that iOS needs zero changes since the
  client already submits array-position-of-what-was-shown with no
  notion of an original order. Scope: `completion_check.parts` choice
  items only (`exercise` is client-side-only self-check, out of scope
  by design). 5 new tests: determinism, non-degeneracy across attempt
  indices, no-shared-state-mutation (identity-checked), option
  text/feedback pairing preserved, and an endpoint-level property test
  proving served-correct-index always grades correct and
  served-wrong-index always grades wrong with matching feedback across
  3 users × 4 attempt indices spanning both complete and review paths.
  Brain verification (elevated rigor — grading correctness is the
  highest-severity failure class in this codebase): **117 passed, 1
  skipped** (own run); every new test individually re-run and
  confirmed passing in isolation; **independent live manual round-trip
  on a real running server** (not reusing any test scaffinding) —
  hand-read served orders via curl for two fresh users on l01, showed
  genuinely different orderings with correct grading for both; drove
  l02 through 3 real review cycles, confirming options actually
  reordered between rounds (parts 1 and 2 both changed) and grading
  matched the freshly-served order every time; mandatory simulator
  launch clean — ACCEPTED. Decision recorded (root `DECISIONS.md` →
  "2026-07-21 — T-G2 Resolved"). **This exhausts every actionable item
  in the v2 backlog.** Remaining open items are all founder-gated and
  correctly parked: real-screenshot vision eval (needs consented
  screenshots), T-K paywall (needs pricing/free-tier decision), T-L
  free-draft grading (needs a budget ceiling decision), and the owed
  Anthropic test-key rotation (needs founder console access — not a
  loop blocker). **Next:** none scheduled; awaiting founder direction
  or new backlog input.

- **2026-07-21 (cycle 42 — T-J iOS half: API token config + bearer
  header; T-J CODE COMPLETE):** Worker: `gpt-5.6-terra`, one round,
  honest partial (sandbox blocks simulator; brain ran tests).
  `APIConfiguration` gains `apiToken`/`setAPITokenOverride`, mirroring
  the existing (already-shipped, still-unused-by-any-UI)
  `baseURLOverride` pattern exactly — same UserDefaults mechanism, same
  nil-by-default shape. Header injected at the single `sendData(_:)`
  choke point every API call already funnels through — zero per-method
  changes, so it covers every current and future endpoint
  automatically. Default (no override) sends no Authorization header,
  matching the backend's default-open state with zero config needed.
  4 new tests reusing the existing URLProtocol request-interception
  mechanism. Brain verification: **67 XCTests, 0 failures** (own run,
  3 new — spec asked for 4 scenarios, worker delivered 3 test functions
  covering them, one combining two assertions); build succeeded; live
  simulator launch against the real (unconfigured, open) backend —
  Home/Today/reflection data loaded from an actual network call,
  confirming the no-token path still works end to end — ACCEPTED.
  **T-J's code scope (opt-in auth + coaching rate limit + iOS token
  plumbing) is now fully shipped.** The only remaining T-J item is the
  owed Anthropic test-key rotation, which is a founder action outside
  the loop's reach (see backlog note above) — not a blocker for
  anything else. **Next:** T-G2 (deterministic runtime answer
  permutation, sequenced after T-J per the cycle-36 decision record).

- **2026-07-21 (cycle 41 — T-J backend half: bearer auth + coaching rate
  limit):** Worker: `gpt-5.6-terra`, one round. `SMALLTALK_API_TOKEN`
  read once per `create_app()`: unset → auth OFF (today's behavior,
  zero config break, one startup WARNING logged), set → single HTTP
  middleware guards every route except `/health` with
  `hmac.compare_digest` constant-time comparison, 401
  `{"detail": "unauthorized"}` on missing/wrong/malformed header, no
  route logic executed on rejection; `/health` gains additive
  `auth_enabled`. Coaching rate limit: thread-safe in-memory
  `_RateLimiter` (same `Lock`-guarded pattern as `jobs.py`) applied only
  to `POST /coaching/diagnoses` (the sole budget-spending endpoint),
  per-`user_id` fixed window, configurable via
  `SMALLTALK_COACHING_RATE_LIMIT` / `_WINDOW_SECONDS` (safe env
  fallback), 429 `{"detail": "rate_limited"}` + `Retry-After`, failed
  diagnoses still count, isolated per app instance, every other
  coaching route unaffected even when exhausted. 10 new tests
  (deterministic via frozen-clock monkeypatching, no real sleeps).
  Brain verification: **112 passed, 1 skipped** (own run); live probes
  on a real uvicorn process — unset-token 200s, set-token 401×3 +
  200 + health-always-200 — all matched exactly; mandatory simulator
  launch clean against the restored open-dev backend (iOS has no token
  yet — that's cycle 42) — ACCEPTED. **Next:** cycle 42, T-J iOS half
  (base URL + token from build config, header on every request).

- **2026-07-21 (cycle 40 — micro-fix: mode-aware screenshot consent
  disclosure; App Store Nov-2025 gap closed):** Worker: `gpt-5.6-terra`,
  one round, honest partial (sandbox blocks simulator; brain ran
  tests). `CoachingDisclosureCopy.lines(for:)` extracted as a pure
  function keyed on `CoachingCompositionMode` (the same binding already
  driving the composer's TextEditor/PhotosPicker switch); `.text`
  line kept byte-identical to the pre-existing copy (regression-tested);
  `.screenshot` line now explicitly names both Anthropic and the image
  itself ("Your screenshot image is sent to Anthropic... to extract the
  conversation text and provide analysis"), third line adjusted
  ("share a screenshot" vs "paste"). 3 new tests assert exact substrings
  per mode. Brain verification: **64 XCTests, 0 failures** (own run,
  3 new); mandatory simulator launch clean — ACCEPTED. **Verification
  note (honest, not inflated):** the interactive toggle-and-observe
  click-through was not performed this cycle — this environment's
  `simctl` has no tap/touch-injection primitive, and standing up a new
  XCUITest target was out of scope for a text-only fix. Confidence
  instead rests on: the copy is driven by the exact same
  `viewModel.compositionMode` binding already proven reactive (it
  already switches the composer's input UI, shipped and
  screenshot-verified since cycle 19), and Swift's exhaustive `switch`
  over the two-case enum makes an unhandled mode a compile error, not a
  runtime risk. `docs/legal/APP_STORE_PRIVACY.md`'s follow-up item is
  now resolved in-app. **T-I is now fully closed, including its
  audit-surfaced follow-up.** **Next:** T-J — backend auth, rate
  limiting, key rotation (the hard gate before any exposed deployment).

- **2026-07-21 (cycle 39 — T-I docs half; T-I COMPLETE):** Worker:
  `gpt-5.6-terra`, one round, docs-only. Shipped `docs/legal/`:
  PRIVACY_POLICY.md (controller Yarkin Yavuz /
  yarkin.business@gmail.com; keep-until-deleted retention; honest
  inventory — anonymous UUID, no accounts, raw screenshots never
  stored, reflection notes never modeled/logged; other-person consent
  caution), TERMS_OF_SERVICE.md (not-therapy, acceptable use,
  AI-imperfection disclaimer, subscription placeholder), and
  APP_STORE_PRIVACY.md (conservative Nutrition Label mapping — data
  LINKED via persistent device UUID, tracking: none — plus a
  third-party-AI disclosure audit quoting the real consent copy).
  Brain verification: quoted copy confirmed verbatim in
  CoachingView.swift:123; claims spot-checked against backend code;
  **102 passed, 1 skipped** untouched — ACCEPTED. Founder decisions
  recorded in `docs/planning/DECISIONS.md` (retention/deletion +
  controller; Open Decision closed). **The audit found a real
  compliance gap:** screenshot-mode consent says "conversation text"
  only — the image itself isn't disclosed. That's a correctness item
  under the Nov 2025 rule → **cycle 40 (copy fix) jumps ahead of
  T-J.**

- **2026-07-21 (cycle 38 — micro-fix: onboarding cover presentation):**
  Fixes the cycle-35 latent bug caught by cycle 37's launch check.
  Worker: `gpt-5.6-terra`, one round. RootView's get-only no-op
  `Binding` (which desynchronized SwiftUI presentation state when the
  first present attempt misfired) replaced with writable `@State` armed
  in `.onAppear`, closed via `.onChange` of the store, plus
  `interactiveDismissDisabled()` so swipe cannot bypass onboarding;
  decision expression extracted testable. Brain verification: **61
  XCTests, 0 failures** (own run); decisive live check — fresh install,
  3 terminate/relaunch cycles, cover presented EVERY time
  (screenshot-verified); completion key set → straight to Home —
  ACCEPTED. **Lesson recorded:** never drive SwiftUI presentation from
  a computed Binding with a no-op setter — same never-re-fires family
  as the cycle-16 `.task`-on-EmptyView trap. **Next:** T-I docs half —
  paused at the founder gate (entity/contact + retention policy).

- **2026-07-21 (cycle 37 — T-I code half: account-wide deletion):**
  Worker: `gpt-5.6-terra`, one round, honest partial (sandbox blocks
  simulator; brain ran tests). `DELETE /users/{id}/coaching-data` wipes
  coaching_reports + reflections in one transaction (counts returned,
  idempotent, ownership-safe); learning data (completions, reviews,
  onboarding → streaks) explicitly survives; iOS "Delete all coaching
  data" control with keep/delete confirmation, clears report state +
  pending reflection on success only. 4 backend + 3 iOS tests. Brain
  verification: **102 backend passed, 1 skipped** + **60 XCTests, 0
  failures** (own runs); live probes (counts, idempotent zeros, streak
  survival) correct; simulator launch clean — ACCEPTED. **Launch
  verification also surfaced a latent cycle-35 bug** (logged as cycle
  38): RootView presents onboarding via a get-only no-op Binding, and
  when SwiftUI's first presentation attempt misfires it writes into the
  no-op setter and never retries — app defaults confirmed unset yet no
  cover presented on relaunch. Feature-logic fix routed to a worker
  micro-cycle, not brain-implemented. **Next:** cycle 38 micro-fix,
  then the T-I docs half (founder question pending).

- **2026-07-21 (cycle 36 — truth-sync; audit-response complete):**
  External audit response, executed under the founder's instruction.
  Worker: `gpt-5.6-terra`, one round. VISION.md Phase 2 annotations
  corrected (T-D and T-E now marked BUILT with cycle references; streak
  rule marked implemented); SKILL.md accept-path now REQUIRES sibling-
  doc sync in the same commit (a cycle that ships a feature while a
  sibling doc calls it unbuilt is a defective cycle); new mechanical
  audit test — every lesson with ≥2 choice parts must vary correct-
  answer positions — which **caught L01** (all answers at one index)
  and fixed it content-level. Brain-side records added at acceptance:
  DECISIONS.md "T-G Shuffle Criterion Deviation Recorded" + backlog
  T-G2; P1 backlog line softened accordingly. Brain verification: **98
  backend passed, 1 skipped** + **57 XCTests, 0 failures** (own runs);
  mandatory simulator launch clean — ACCEPTED. Audit findings now all
  addressed or formally recorded; remaining audit items are founder-
  gated (real-screenshot set, T-K, T-L). **Next:** T-I (privacy policy,
  ToS, account-wide deletion, App Store disclosure).

- **2026-07-21 (cycle 35 — T-H onboarding + baseline; closes the T-D
  placement caveat):** Worker: `gpt-5.6-terra`, one round, honest
  partial (sandbox blocks simulator; brain ran tests). Backend:
  `onboarding` table (INSERT OR REPLACE), POST with stable 422 codes
  (`invalid_goal`/`invalid_context`/`invalid_baseline`), GET with 404
  `not_onboarded` and manifest-derived `emphasis` (lowest baseline
  dimension, DIMENSIONS-order tie-break, first routed lesson from
  `curriculum.routing` — no hardcoded ids); 5 new tests. iOS:
  `OnboardingView` 4-step skippable flow (goal/context/baseline/
  reminder opt-in reusing ReminderSettingsViewModel — **the T-D
  "opt-in during onboarding" acceptance item is now properly placed**),
  `OnboardingStateStore` (skip and finish both permanent), full-screen
  cover from RootView, POST-failure non-blocking, Today card emphasis
  line from a concurrent non-blocking fetch; 6 new tests. Brain
  verification: **97 backend passed, 1 skipped** + **57 XCTests, 0
  failures** (own runs); fresh-install simulator launch shows the
  onboarding welcome step (screenshot-verified; first frame was the
  cover transition on a cold-booted simulator). ACCEPTED. This cycle
  ran under the audit-response plan (see the 2026-07-21 audit note
  below). **Next:** truth-sync cycle (audit items: VISION.md
  re-annotation, T-G deviation record, protocol amendment, answer-index
  audit test).

- **2026-07-21 (cycle 34 — T-G iOS: review mode; T-G COMPLETE — P1 TIER
  COMPLETE):** Worker: `gpt-5.6-terra`, one round. LessonDetail gains a
  review mode (submits to `POST /lessons/{id}/review`; passing reviews
  never arm a reflection — that stays first-completion/report-only),
  Today card renders `kind: "review"` targets, Home gains a "Review due"
  section (top 3, overdue + dimension tags, review-mode deep links),
  TodayViewModel fetches streak + queue concurrently with non-blocking
  failures; extracted testable `TodayCardTargetState`. Brain
  verification: **51 XCTests, 0 failures** (own run; 4 new, first
  round); mandatory simulator launch clean — ACCEPTED. **The v2 P1
  retention loop is now fully shipped: streak/freezes/Today +
  reminders (T-D), longitudinal skill profile (T-E), reflection Flow D
  (T-F), spaced review (T-G) — all deterministic, zero new API spend
  under the Haiku lock.** **Next:** P2 — cycle 35, T-H onboarding +
  baseline (Flow A).

- **2026-07-21 (cycle 33 — T-G backend: spaced review):** Worker:
  `gpt-5.6-terra`, one round. Shipped `backend/app/review.py` (3/7/21-
  then-21 ladder measured in user-local days from most recent
  completion/review; queue ordered priority-dimension-match → overdue
  desc → path order), `review_completions` table + streak integration
  (review = activity day, never earns freezes), grading refactored into
  one `_grade_completion` helper shared by completion AND the new
  `POST /lessons/{id}/review` (409 `not_completed`, failing attempts
  record nothing), `GET /users/{id}/review-queue?tz=`, streak `today`
  now yields `kind: "review"` from the queue head when the path is
  complete (falls back to `all_complete` only when nothing is due), and
  the L02 content fix (correct indices now varied [1,0,1] — cycle-6 nit
  cleared). 8 new tests. Brain verification: **92 passed, 1 skipped**
  (own run); live probes (empty queue, 422 tz, 409) correct; mandatory
  simulator launch clean — ACCEPTED. **Next:** cycle 34, T-G iOS
  (review flow + Today review kind), which completes P1.

- **2026-07-21 (cycle 32 — T-F iOS: reflection prompt; T-F COMPLETE;
  FIRST REJECTION THIS RUN):** Worker: `gpt-5.6-terra`, **two rounds**.
  Round 1 shipped the feature set (PendingReflectionStore with
  per-cold-launch session token so the prompt only surfaces on a LATER
  open; markers armed on lesson completion + fresh coaching reports,
  most-recent-wins; sheet with three outcomes, capped optional note,
  "Not now" clears for good; submit failure keeps pending for retry;
  pluralization fix) but brain test run found 3 failures: `let
  reflections: ProfileReflections? = nil` — a `let` with a default is
  excluded from synthesized Codable decoding, so the additive profile
  block never decoded. Round 2 fix as prescribed (default removed).
  (Ops note: my first round-2 dispatch failed on a relative worker.sh
  path from the wrong cwd — not a worker round.) Brain verification:
  **47 XCTests, 0 failures** (own run); simulator launch clean AND the
  prompt surfaced live on cold launch from the prior session's report
  (screenshot-verified), singular copy confirmed — ACCEPTED. **Lesson
  recorded:** Swift `let` + default value silently disables decoding —
  a recurring-hazard class with this worker (cf. cycle-14 timestamps).
  **Next:** cycle 33, T-G review/spaced repetition (backend), which
  completes P1.

- **2026-07-21 (cycle 31 — T-F backend: reflection records):** Worker:
  `gpt-5.6-terra`, one round. Reflections table (id/user/subject_kind
  lesson|report/subject_id/outcome went_well|partly|avoided/note ≤500
  chars/isoformat created_at), POST with stable 422 detail codes +
  404 `unknown_subject` (report ownership enforced), GET newest-first,
  additive profile `reflections` block (all-outcome counts + last-5
  recent, notes structurally excluded), streak untouched. 6 new tests.
  Brain verification: **84 passed, 1 skipped** (own run); live probes —
  201 with unicode note verbatim, profile block note-free, 404, streak
  isolation confirmed (reflection user stays 0) — and mandatory
  simulator launch clean — ACCEPTED. **Next:** cycle 32, T-F iOS
  (post-practice reflection prompt; includes the cycle-30 pluralization
  nit).

- **2026-07-21 (cycle 30 — T-E iOS: skill-profile surface; T-E
  COMPLETE):** Worker: `gpt-5.6-terra`, one round, honest partial
  (sandbox blocks simulator; brain ran tests). Shipped
  `ProfileView.swift` (ProfileViewModel; `ProfileSummaryRow` on Home
  under Today with three summary states via testable `ProfileSummary`
  helper; detail view: recurring-weakness callout, four dimensions in
  fixed order with latest score + "3 → 4 → 4" history, not-yet-scored
  copy, recommended-not-taken deep links into LessonDetailView),
  ProfileAPI + models (unknown dimension keys tolerated), shared
  refreshHome now reloads profile too. Brain verification: **39
  XCTests, 0 failures on iPhone 16** (own run; 4 new); simulator launch
  clean — "Your skills" row renders with real persisted data
  (screenshot-verified) — ACCEPTED. **Nit for next iOS cycle:**
  pluralization ("1 conversations analyzed"). **Next:** cycle 31, T-F
  backend (reflection records + endpoint).

- **2026-07-21 (cycle 29 — T-E backend: skill-profile endpoint):**
  Worker: `gpt-5.6-terra`, one round. Shipped `backend/app/profile.py`
  (strict per-row validation with defensive skips — malformed rows never
  500; deterministic (datetime, id) ordering reusing
  `parse_activity_timestamp`; per-dimension score histories capped at
  10; all-time `flagged_count` per weakest dimension; recurring
  weakness = same dimension flagged ≥3 of last 5 reports;
  `recommended_not_taken` deduped to most recent, completed/unknown ids
  excluded), `store.coaching_report_rows` raw read, and
  `GET /users/{id}/profile`. Zero API calls; `DIMENSIONS` imported, not
  redeclared. 6 new tests covering all 7 spec points. Brain
  verification: **78 passed, 1 skipped** (own run); live probe of the
  empty-profile contract matched verbatim; mandatory simulator launch
  clean with the Today card intact — ACCEPTED. **Next:** cycle 30, T-E
  iOS surface (profile section on Home).

- **2026-07-21 (cycle 28 — T-D iOS: Today card + reminders; T-D
  COMPLETE):** Worker: `gpt-5.6-terra`, one round, honest partial
  (sandbox blocks simulator; brain ran tests). Shipped `TodayCard.swift`
  (TodayViewModel + ReminderSettingsViewModel; streak/freeze/done-today
  states, "Today: <lesson>" deep link into LessonDetailView, unknown
  `kind` tolerated as all_complete, endpoint failure shows inline note —
  never blocks curriculum), `ReminderScheduler.swift`
  (ReminderScheduling protocol; UNUserNotificationCenter impl with one
  repeating calendar trigger, static content — no user data; UserDefaults
  prefs, default OFF at 19:00), StreakAPI on APIClient, Home integration
  with shared refresh (lesson completion refreshes curriculum + streak;
  cycle-16 `.task` placement preserved). Brain verification: **35
  XCTests, 0 failures on iPhone 16 / iOS 18.2** (own run; 10 new);
  mandatory simulator launch clean — Today card renders with streak
  line, bell (off), and lesson link (screenshot-verified; one re-run
  after the simulator was shut down externally, and note: install must
  exclude DerivedData `Index.noindex` bundles). **The VISION.md daily
  habit loop is now implemented.** **Next:** cycle 29, T-E backend
  (deterministic skill-profile aggregation endpoint).

- **2026-07-21 (cycle 27 — T-D backend: streak/freeze/today endpoint):**
  Worker: `gpt-5.6-terra`, one round. Shipped `backend/app/streak.py`
  (dual-format UTC timestamp parser — the cycle-14 mixed-format trap
  handled explicitly, malformed rows skipped; pure deterministic replay:
  activity days from lesson completions + coaching reports, freeze
  earned per completed unit capped at 2, gap days consume a freeze only
  when a streak exists, today-in-progress never consumes or resets),
  `store.activity_timestamps` raw read, and
  `GET /users/{id}/streak?tz=<IANA>` (zoneinfo DST-correct day
  boundaries, invalid tz → 422 `invalid_timezone`, `today` target
  reusing `_unlocked_lesson_id` — no duplicated unlock logic;
  `all_complete` state; `kind` extensible for T-G "review"). 8 new
  tests incl. US spring-forward day and mixed-format dedup. Zero API
  calls. Brain verification: **72 passed, 1 skipped** (own run); live
  endpoint probe matched the contract exactly (200 shape + 422); helper
  reuse and int-unit formatting checked in source; mandatory simulator
  launch clean — ACCEPTED. **Next:** cycle 28, T-D iOS half (Today
  card + streak display + opt-in local notifications).

- **2026-07-20 (cycle 26 — T-C diagnosis retry hardening; P0 TIER
  COMPLETE):** Worker: `gpt-5.6-terra`, one round. `diagnose()` now runs
  a bounded retry loop: default 3 attempts
  (`SMALLTALK_DIAGNOSIS_ATTEMPTS`, clamped 1–5, lazy env read, garbage →
  default), retries invalid output AND transient provider errors
  (5xx/429/connection/timeout — the cycle-21 live 502 pattern now
  recovers), never retries refusals or non-transient statuses (schema
  400s fail fast per the cycle-21/23 lesson), per-attempt content-free
  ERROR logs (`attempt=n/N`, fixed reason slugs) + exhaustion line;
  external taxonomy unchanged (502 `ai_unavailable` verified at HTTP
  layer). 7 new tests incl. both cycle-21 regression patterns and a
  caplog assertion that transcript content never reaches logs. Brain
  verification: **64 passed, 1 skipped** (own run); retry-focused subset
  green; mandatory simulator launch clean against the restarted
  cycle-26 backend — ACCEPTED. **Next:** P1 begins — T-D daily habit
  loop, backend half first (streak/freeze/today endpoint).

- **2026-07-20 (cycle 25 — T-B vision-eval harness):** Worker:
  `gpt-5.6-terra`, one round. Shipped `backend/eval/vision_eval.py`
  (stdlib-only CLI: greedy difflib turn alignment; recall/fidelity/order/
  attribution vs recorded thresholds 0.95/0.90/1.0/1.0; per-case +
  aggregate report; `--out` JSON redacts transcript text by default),
  double-gated live mode (`SMALLTALK_VISION_EVAL=1` + key, refused
  before adapter construction), mock adapter reading per-case canned
  payloads, 2 synthetic fixtures (one passing, one deliberately
  failing), gitignored `real/` case dir + consent/anonymization
  checklist in `backend/eval/README.md`, 6 new tests. Reuses
  `extract_transcript`/`AnthropicVisionAdapter` — model lock untouched,
  zero API spend. Brain verification: **57 passed, 1 skipped** (own
  run); mock CLI exit 1 with the intended PASS/FAIL split (own run);
  ungated live exit 2 (own run); gitignore probe blocked; mandatory
  simulator launch clean — ACCEPTED. The founder screenshot gate is now
  "drop image + expected.json into backend/eval/vision_cases/real/, run
  one command." **Next:** T-C, diagnosis retry hardening.

- **2026-07-20 (cycle 24 — T-A docs sync; v2 execution begins):** First
  cycle of the founder-ordered v2 execution (T-K/T-L and the
  real-screenshot eval stay deferred as founder-gated). Worker:
  `gpt-5.6-terra`, one round. VISION.md's stale status ("paused for
  planning") replaced with the post-restart/post-rebuild state; Phase 0
  section marked historical (tag `phase0-archive`); all 7 Phase 2 items
  and 4 open questions annotated with 2026-07-20 status;
  ARCHITECTURE.md banner now names COACHING_PIPELINE_V1.md as the
  implemented design of record (Haiku lock supersedes its tiering);
  decision entry appended ("Stale VISION/ARCHITECTURE Status Synced to
  Rebuilt v1"). Brain verification: diff read in full, every annotation
  traced to its source record; **51 passed, 1 skipped** (own run, from
  repo root); mandatory simulator launch clean against the key-loaded
  backend (curriculum renders, both tabs) — ACCEPTED. **Next:** T-B,
  vision-eval harness.

- **2026-07-19 (cycle 23 — vision schema live-API fix):** Founder's first
  real screenshot submission surfaced `coaching vision provider_error=400`
  (job → ai_unavailable → app's "temporarily unavailable" error). Cause:
  `"minimum": 0` on the turn-index integer in vision.py's extraction
  schema — numerical constraints are API-unsupported (same class as
  cycle 21's maxItems; that fix only covered diagnosis.py). Worker
  micro-cycle: constraint removed, non-negative/contiguous indices
  enforced app-side with a regression test. Brain verification: 51 tests
  (own run); live screenshot job with a real PNG now traverses the API
  and correctly returns `unreadable_transcript` for a non-chat image;
  mandatory simulator launch clean — ACCEPTED. Lesson generalized: ALL
  structured-output schemas must stay within the supported constraint
  set; both schemas now audited. Founder can retest with a real chat
  screenshot (the open vision-quality eval).

- **2026-07-19 (cycle 22 — iOS response-coaching UI; role-fix complete):**
  Worker: `gpt-5.6-terra`, one round, honest partial (sandbox blocks
  simulator; brain ran tests). Schema-v2 models (nullable dimensions),
  report cards in product order: "What they're really saying"
  (interpretation) → optional "Your reply, scored" (hidden entirely in
  stimulus_only mode, double-gated) → strengths/improvements when
  non-empty → "How to respond" with 1–2 adaptable example replies →
  emphasized Takeaway card → recommendation + practice action; composer
  hint teaches the stimulus default + `Me:` convention. Brain
  verification: **25 XCTests passed on iPhone 16 / iOS 18.2** (own run);
  mandatory simulator launch clean against the live key-loaded backend
  (one re-run after the simulator had been shut down externally) —
  ACCEPTED. The founder's role-confusion fix is now live end to end:
  backend contract, live-API verified in both modes, and rendered in-app.

- **2026-07-19 (cycle 21 — response-oriented coaching, 2 rounds):**
  Implements the founder's "teach the user to fish" correction (product
  decision recorded). Round 1: stimulus default for unlabeled text
  (speaker "other"), schema v2 (mode, incoming_interpretation,
  response_coaching + 1–2 examples, transferable_takeaway,
  focus_dimension, nullable dimensions), mode derived from transcript
  attribution — never trusted from the model, evidence turn-indices
  restricted to user turns, role-bound prompt, focus-dimension routing
  fallback, doc amended. Round 2 (reviewer rejection): live API 400 —
  `maxItems` unsupported on arrays; removed, cardinality enforced
  app-side; dimensions nullability moved to anyOf form. Brain
  verification: 50 tests (own run) + BOTH modes verified live —
  stimulus-only: bare incoming question → no scores, interpretation,
  2 example replies, takeaway, focus routing to l04; with_user_reply:
  scores bind to the user's turn only with verbatim quotes → reciprocity
  → l04 — ACCEPTED. Known operational note: scored-mode validation
  occasionally fails both attempts on Haiku (one 502 observed between
  successes); backlog: code-only validation-failure reason logging +
  consider third attempt. **Next:** cycle 22 — iOS rendering of the new
  report fields.

- **2026-07-19 (cycle 20 — Haiku-tolerance fix; first live 201):** The
  founder-requested live run exposed a production bug no mocked test hit:
  real Haiku payloads 502'd because (a) absence-observations carry empty
  quotes arrays and (b) the model over-returns improvements (3–4).
  Diagnosed by capturing a live payload via scratchpad harness. Worker
  fix: validation tolerates empty quotes (present quotes still
  exact-substring — hallucination guard intact), improvements coerced to
  top-2 by priority and renumbered, strengths truncated to 3, prompt
  tightened; COACHING_PIPELINE_V1 §2.2 amended citing the Haiku lock.
  Brain verification: **45 passed** (own run); live re-test → **201
  Created**: curiosity diagnosed weakest → routed to
  `l03-easy-first-question`, 2 improvements, report persisted; mandatory
  simulator launch clean against the key-loaded backend
  (`coaching_enabled: true`) — ACCEPTED. Lesson: mocked fixtures encode
  the contract's ideal; the cheapest model needs boundary tolerance —
  live verification is where that gap shows.

- **2026-07-19 (cycle 19 — iOS screenshot upload; coaching feature
  COMPLETE):** Worker: `gpt-5.6-terra`, one round, honest partial
  (sandbox blocks simulator; brain ran the tests). Shipped screenshot
  mode in the Coaching composer: PhotosPicker + preview, message-side
  picker (right/left/unknown), size-aware JPEG recompression behind a
  testable encoder, typed 202/poll models, 2s polling with 90s timeout
  and retry, taxonomy-mapped friendly failures, consent gating shared
  across both modes (defaults off, resets per composition). Brain
  verification: **24 XCTests passed on iPhone 16 / iOS 18.2** (own run);
  consent/poll logic source-reviewed; mandatory simulator launch clean,
  screenshot-verified — ACCEPTED. The full VISION.md closed loop (real
  conversation → screenshot → diagnosis → lesson → practice) is now
  implemented end to end under the Haiku-only lock. **Remaining
  founder-gated:** vision quality eval on real consented screenshots;
  test-key rotation before production.

- **2026-07-19 (cycle 18 — screenshot backend path):** Worker:
  `gpt-5.6-terra`, one round. Shipped `vision.py` (Haiku-only structured
  extraction via imported COACHING_MODEL, §4-faithful prompt rules,
  app-side extraction validation incl. no-guessing attribution),
  `jobs.py` (in-memory thread-safe job store — metadata and report
  references only, raw image bytes never on records, restart fails
  jobs by design), async 202+poll endpoints reusing the shared
  diagnose→route→persist pipeline, full image taxonomy (415/413/422
  with magic-number checks and `del` in finally). Brain verification:
  **41 passed, 1 skipped** (own run); image-validation ordering, job
  outcome paths, and model-lock scan reviewed line-level; mandatory
  simulator verification executed — clean launch, screenshot-verified —
  ACCEPTED. **Next:** iOS screenshot-upload UI (cycle 19), then the
  founder-gated vision quality eval on real consented screenshots.

- **2026-07-19 (milestone — live smoke PASSED):** Founder added a working
  test key to `~/.env` (after cleaning stale entries; one earlier key was
  invalid at the API — 401 handled exactly as designed, code-only
  logging). `SMALLTALK_LIVE_SMOKE=1` run: **1 passed in 14.8s** — first
  real `claude-haiku-4-5` diagnosis through the adapter, structured
  output accepted by the live API (minLength watch-item CLEARED; SDK
  strips unsupported constraints as documented), response passed full
  app-side validation. Coaching text path is verified live end to end.
  Key-handling note: test keys transited the chat at founder's explicit
  acceptance; rotation recommended before production keys — production
  keys go in via the read -s flow only.

- **2026-07-19 (cycle 17 — Haiku-only lock + protocol amendment):** Two
  founder decisions recorded and implemented: (1) ALL backend Anthropic
  calls locked to `claude-haiku-4-5` (strict budget rule; supersedes the
  sonnet pinning) — `COACHING_MODEL` constant, forbidden-name grep clean,
  and a mechanical enforcement test that scans backend/app for
  sonnet/opus/fable/mythos substrings; (2) every cycle now ends with a
  mandatory iPhone 16 simulator build+launch verification (SKILL.md loop
  protocol updated; brain fixes launch errors directly under a scoped
  founder exception). Worker: `gpt-5.6-terra`, one round. Brain
  verification: 28 tests passed (own run) + full simulator verification
  executed and screenshot-verified (app launches cleanly, curriculum
  renders) — ACCEPTED. Founder confirmed the API key is in `~/.env`; the
  brain's sandbox cannot read it (by design), so the live smoke run is
  handed to the founder as a `!` command. **Next:** live smoke result,
  then screenshot path (vision also Haiku-4.5 per the lock).

- **2026-07-19 (cycle 16 — first live simulator run; two runtime bugs
  fixed):** Founder-requested run session: backend via uvicorn + app in
  the iPhone 16 simulator. First launch rendered a blank letterboxed Home
  tab. Brain diagnosis (empirical: zero /curriculum requests while the
  Coaching health probe succeeded; app UserDefaults domain absent):
  (1) missing `UILaunchScreen` in the generated Info.plist forced legacy
  compatibility mode — fixed via worker micro-cycle adding
  `INFOPLIST_KEY_UILaunchScreen_Generation` to project.yml; (2) HomeView
  attached `.task` to content whose initial `.idle`/nil state resolved to
  `EmptyView` (explicit `else { EmptyView() }`), and SwiftUI never fires
  `.task` on EmptyView — the load could never start. Fixed via worker
  micro-cycle: `.task` moved onto the NavigationStack, `.idle` and nil
  states render the loading view, EmptyView branch removed. Verified
  live: app fetches /curriculum with its persisted UUID and renders all
  4 units with correct lock states (screenshot-verified); 16 XCTests
  still green. Lesson recorded: SwiftUI `.task` on possibly-empty
  content is a load-never-starts trap; unit tests cannot catch it —
  only a real launch does.

- **2026-07-18 (cycle 15 — iOS Coaching tab; founder-independent queue
  complete):** Worker: `gpt-5.6-terra`, one round, honest partial
  (sandbox blocks CoreSimulatorService). Shipped `CoachingView` +
  `CoachingViewModel` + typed `CoachingAPI` seam: consent-gated compose
  (all four §5 disclosure elements, toggle defaults off and resets per
  composition, visual attention state on consent_required),
  201-report / 200-safety_guidance discriminated handling, report view
  with quoted evidence + recommendation card deep-linking into
  LessonDetailView, history list/detail/delete, coaching-disabled state
  from /health, full error-taxonomy mapping. Brain verification:
  regenerated project, built, and ran **16 tests — all passed on
  iPhone 16 / iOS 18.2** (own run); consent copy and reset behavior
  verified in source — ACCEPTED. **Loop paused: remaining items are
  founder-gated (key for live smoke; key + consented screenshots for
  the vision eval gating the screenshot path).**

- **2026-07-18 (cycle 14 — coaching backend, text path; FIRST REJECTION
  ROUND):** Worker: `gpt-5.6-terra`, **two rounds**. Round 1 implemented
  COACHING_PIPELINE_V1's text path (normalization, sonnet-4-6 structured
  diagnosis via output_config.format with lazy env-key client, app-side
  contract validation incl. quote fidelity + forbidden lesson-term sweep,
  deterministic routing with fixed tie-break, report persistence with
  get/list/delete, full error taxonomy, escalation persists nothing,
  double-gated live smoke; anthropic==0.117.0 pinned). Brain review
  REJECTED round 1 for one real bug: `completed_lesson_ids_at` compared
  sqlite `CURRENT_TIMESTAMP` ("YYYY-MM-DD HH:MM:SS") against Python
  isoformat ("...T...+00:00") lexicographically — space < 'T' means
  same-day later completions passed the `<=` check, so re-fetched reports
  could flip recommendation_kind "new"→"review". Round 2 fix (as
  prescribed): `recommendation_kind` persisted immutably at creation,
  reconstruction deleted, regression test added. Brain verification:
  **27 passed, 1 skipped** (own run), fix + regression confirmed —
  ACCEPTED. Watch-item for live smoke: schema `minLength` relies on
  SDK-side stripping. **Next:** screenshot path or iOS Coaching tab;
  live smoke on founder key confirmation.

- **2026-07-18 (cycle 13 — iOS lesson detail + completion flow):** Worker:
  `gpt-5.6-terra`, one round, honest partial (sandbox still blocks
  CoreSimulatorService; in-sandbox build + build-for-testing green).
  Shipped `LessonDetailView` (six blocks, interactive exercise with
  per-option feedback, choice parts with server feedback by string key,
  free-draft TextEditor labeled ungraded/on-device),
  `LessonDetailViewModel` behind a new `LessonAPI` protocol (injectable,
  unit-tested), Home navigation gated to
  contentAvailable && (unlocked||completed), models fixed for
  narration-only examples, curriculum refresh on return. Brain
  verification: regenerated project, built, and ran **10 tests — all
  passed on iPhone 16 / iOS 18.2** (brain's own run) — ACCEPTED.
  **Next:** coaching backend implementation, text path first
  (mocked-API; live smoke test stays gated on founder key confirmation).

- **2026-07-18 (cycle 12 — coaching pipeline design doc):** Worker:
  `gpt-5.6-terra`, one round. Shipped
  `docs/planning/COACHING_PIPELINE_V1.md` (350 lines): plain-Messages-API
  v1 (no CMA dependency, upgrade path preserved), transcript/diagnosis
  JSON contracts with quote-backed observation-vs-inference rules,
  deterministic manifest routing (fixed tie-break, fail-closed), sync-text
  / async-screenshot API surface with full error taxonomy, safety &
  privacy section (per-request consent, no raw-image persistence, crisis
  escalation suppresses report+routing), mocked-API test strategy + opt-in
  live smoke test + the real-screenshot eval gating vision-model pinning.
  Brain review: read in full against locked decisions and PRODUCT_BRIEF
  §6/§11/§12 — ACCEPTED. **Next:** iOS lesson detail + completion flow
  (backlog 6b); coaching implementation queued behind founder key
  confirmation.

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
