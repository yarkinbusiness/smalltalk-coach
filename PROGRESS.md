# Progress & backlog

**2026-07-20 (later — latest): LOOP ACTIVE — v2 execution begun (founder
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

- **P0 (hygiene/unblocking):**
  1. **T-A** — retire stale roadmap sections + sync stale docs.
     PROGRESS.md half done in this refresh; remaining: VISION.md status
     header + Phase 2 annotations, ARCHITECTURE.md banner pointing to
     COACHING_PIPELINE_V1 as the implemented design.
  2. **T-B** — vision-eval harness (the non-gated half of the screenshot
     eval): scoring script + synthetic fixtures + consent checklist, so
     the founder gate becomes "drop screenshots, run one command."
  3. **T-C** — diagnosis retry hardening: per-attempt code-only
     failure-reason logging, configurable retry count (default 3).
- **P1 (retention loop — the vision's differentiator):**
  4. **T-D** — daily habit loop v1: streak + earned freezes, "Today"
     card, opt-in local notifications (no APNs).
  5. **T-E** — skill profile v1: deterministic longitudinal aggregation
     of reports + completions, `GET /users/{id}/profile`, iOS surface.
  6. **T-F** — reflection loop ("How did it go?", BRIEF Flow D), feeds
     the profile.
  7. **T-G** — review/spaced-repetition pass: fixed-interval review
     queue, review counts as streak activity, option-order shuffling
     (clears the L02 nit).
- **P2 (activation + v1 Must-Haves):**
  8. **T-H** — onboarding + baseline (BRIEF Flow A), hosts notification
     opt-in.
  9. **T-I** — privacy policy/ToS, account-wide coaching-data deletion,
     App Store third-party-AI disclosure + Privacy Nutrition Label
     mapping.
  10. **T-J** — backend auth (shared-secret bearer), rate limiting on
      coaching endpoints, test-key rotation, deploy readiness.
- **P3 (founder-gated decisions):**
  11. **T-K** — paywall experiment scaffolding (StoreKit 2, flag off) —
      gated on founder pricing + free-tier decision.
  12. **T-L** — free-draft grading costed proposal (docs-only) — gated
      on founder budget approval.
- **Standing founder-gated item:** vision-quality eval on real consented
  screenshots (runs via the T-B harness once the founder provides them).

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
