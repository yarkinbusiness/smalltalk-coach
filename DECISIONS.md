# SmallTalkCoach — Engineering Decision Log (build repo)

Append-only: one dated entry per real engineering/build decision, never
rewritten or restructured. Product-level decisions live in
`docs/planning/DECISIONS.md` (migrated 2026-07-18 from the
smalltalk-coach-planning project) — do not mix them here.
Read by the brain and by every Codex worker at cycle start (see
`.claude/skills/brain-worker-loop/SKILL.md`).

### 2026-07-18 — Project-Resident Memory for the Build Loop

- **Status:** Confirmed (founder decision)
- **Decision:** The brain (Claude Fable 5, `.claude` memory) and the workers
  (Codex GPT 5.6, `.codex` sessions) have disjoint native memory systems, so
  all shared loop memory lives in this repository: `PROGRESS.md`
  (status/backlog/cycle log), this file (engineering decisions),
  `WORKER_LOG.md` (one structured append-only entry per worker task). The
  brain reads all three at every cycle start; `worker.sh` injects the same
  read-then-log protocol into every worker spec and exits 4 when a worker
  finishes without appending its log entry (automatic reject). The brain
  may mirror durable lessons to its own persistent memory (auto-memory
  files; the claude-mem/cmem plugin when it is active) — mirrors are
  best-effort copies only, and the repository stays the single source of
  truth for loop state.
- **Why:** Neither model can read the other's native memory; the repo is the
  only surface both are guaranteed to see, it survives model/CLI changes,
  and it travels with the code in git.
- **Revisit trigger:** Cycle-start reads become unwieldy from log growth
  (then add a compaction step), or the loop ever runs more than one worker
  concurrently (then the single-writer append assumption needs revisiting).

### 2026-07-18 — Safe Auto-Push After Verified Runs

- **Status:** Confirmed (founder decision)
- **Decision (brain policy, verbatim):** "After every successful verified
  run, if and only if the run created a commit, auto-push the current
  branch to its configured upstream. Refuse automated runs on a dirty
  tree. Never force-push or retry endlessly. Keep the local commit if push
  fails and surface the failure. AUTO_PUSH=0 disables this behavior;
  default is AUTO_PUSH=1."
- **Why:** Accepted work that only exists locally is invisible to the
  founder and to any other authorized session; pushing deterministically
  after acceptance closes that gap without letting automation force-push,
  push half-done work (dirty tree), or thrash on failures.
- **Implementation:** `.claude/skills/brain-worker-loop/auto_push.sh` —
  takes the run-start HEAD as `-b <baseline>` so "this run created a
  commit" is checked mechanically, pushes only the current branch to its
  upstream (setting upstream with `push -u` only when missing), one
  attempt, never `--force`. Exit codes: 0 pushed/clean no-op, 2 usage,
  3 dirty tree, 4 detached HEAD or no remote, 5 push failed (commit kept).
  Tests with a local bare remote: `tests/test_auto_push.sh` (11
  assertions, all passing at adoption time).
- **Revisit trigger:** The repo gains collaborators or branch protection
  (then push targets a PR branch, not master), or repeated exit-5 failures
  show the remote/auth setup needs rework.

### 2026-07-18 — Full Restart: Phase 0 Implementation Removed

- **Status:** Confirmed (founder decision, explicitly approved after brain
  review surfaced the contradiction with prior framing)
- **Decision:** The Phase 0 implementation — `backend/` (38 files: FastAPI
  service, CMA grading engine, memory store, recommendation logic, ~145
  tests) and `ios/` (27 files: SwiftUI app + Core package) — is removed
  from `master`. The repo becomes planning-first: loop harness plus
  planning/coordination docs only, until the planning project's
  `VALIDATION_PLAN.md` thresholds are met and the v1 lesson path is
  defined. This supersedes the "Phase 0 carries into v1 as the foundation"
  framing in `ARCHITECTURE.md` (2026-07-16) and PROGRESS.md's earlier
  "they're not wasted" note — v1 will be re-derived from
  `VISION.md`/`ARCHITECTURE.md` as design references, not built directly
  on the old tree.
- **Recovery:** Annotated tag `phase0-archive` (at `67ead32`, pushed to
  origin) holds the complete pre-cleanup tree.
  One-command rollback: `git checkout phase0-archive -- backend ios`.
- **Why:** Founder wants a clean-slate repo where only the new
  brain/worker loop and planning system exist, with no legacy code
  implying the old app is active.
- **Revisit trigger:** Validation passes and the rebuild would genuinely
  reuse Phase 0 components — then restore selectively from
  `phase0-archive` instead of rewriting from scratch.

### 2026-07-18 — One-Time History Rewrite (Authorized Force-Push Exception)

- **Status:** Confirmed (founder-approved, explicitly scoped)
- **Decision:** A one-time `git filter-repo` rewrite of `master`'s last two
  commits removed 1,478 accidentally committed build artifacts
  (`ios/Core/.build/` SwiftPM output, `**/__pycache__/**`, `*.pyc`,
  `ios/SmallTalkCoach.xcodeproj/`) that entered history via `git add -A`
  during the restart cleanup, then were untracked in the follow-up commit.
  Pushed with `--force-with-lease` under a founder-granted one-time
  exception to the standing never-force-push rule; that rule remains in
  force for all future work, automated and manual. Founder also explicitly
  waived a separate backup clone; the pre-rewrite history remained in the
  local working repo until verification passed.
- **Result:** `294f296` → rewritten `6dbf73a`; final tree byte-identical
  (verified by tree hash `548e80c`); all pre-junk commit hashes and the
  `phase0-archive` tag unchanged; zero junk objects in any ref; `git fsck`
  clean; fresh-clone `.git` size 59 MB → 332 KB.
- **Why:** 112.5 MB of pure build-artifact blobs in a repo intended to be
  a minimal planning/loop repo taxed every future clone; blast radius was
  exactly two commits with no collaborators or secrets involved.
- **Revisit trigger:** None — the exception is spent. Any future
  force-push requires a new explicit founder authorization and entry here.

### 2026-07-18 — Build Scope Gate Narrowed (Interview Thresholds Waived)

- **Status:** Confirmed (founder decision)
- **Decision:** The loop's scope gate changes from "no app code until
  `docs/planning/VALIDATION_PLAN.md` thresholds are met AND the v1 lesson
  path is defined" to "**no app code until the v1 lesson path is defined
  and the founder explicitly approves build start**." Product-side record:
  `docs/planning/DECISIONS.md` → "2026-07-18 — Validation Interviews
  Deferred; Build Gate Waived (Founder)". Documentation-only roadmap work
  (starting with `docs/planning/LESSON_PATH_V1.md`) proceeds now under the
  normal loop protocol.
- **Why:** Founder waived the interview gate on 2026-07-18; the engineering
  gate text must track the real rule or future cycles will refuse valid
  work.
- **Consequence:** `docs/planning/ORCHESTRATION.md` (Scope section) and
  `.claude/skills/brain-worker-loop/SKILL.md` (activation guard #3) need
  their gate text synced to this entry — assigned to a worker task in the
  same cycle that writes `LESSON_PATH_V1.md`.
- **Revisit trigger:** Founder reinstates the interview gate; or the lesson
  path is accepted and the founder gives build go-ahead (the gate then
  lifts entirely and this entry becomes historical).

### 2026-07-18 — Build Start Approved; Content-Model-First Sequencing

- **Status:** Confirmed (founder delegation + brain decision)
- **Decision:** The founder granted build-start approval contingent on the
  brain's expert judgment (instruction, 2026-07-18); the brain selects
  **build start** with exactly one prerequisite planning cycle: define the
  lesson content schema and authoring approach
  (`docs/planning/CONTENT_MODEL_V1.md` + one fully-authored sample lesson
  as a schema fixture) before the first app-code cycle (backend skeleton +
  curriculum serving). The scope gate is **lifted** — its remaining
  condition (explicit founder approval) is met via the delegated grant.
- **Why:** Curriculum-serving code cannot be correctly specified against an
  undefined content model — the schema is the single blocking dependency
  between `LESSON_PATH_V1.md` and the backend, and data-model rework is the
  expensive failure mode. Everything else that "more planning" would cover
  (implementation sequencing) lives as a maintained backlog in
  `PROGRESS.md` instead of a standalone doc — planning bloat is the other
  failure mode. Environment constraints reinforce backend-first: iOS is
  Xcode-blocked and live coaching needs the CMA key; curriculum serving
  needs neither.
- **Consequence:** Gate text in `docs/planning/ORCHESTRATION.md` and
  `SKILL.md` gets synced (worker task, same cycle as the content model).
  The backend is rebuilt fresh; `phase0-archive` is consulted selectively
  only where a component genuinely fits (per the Full Restart entry).
  Coaching pipeline and iOS remain sequenced after curriculum serving.
- **Revisit trigger:** The content schema proves unstable across the first
  authored lessons (pause serving work and fix the schema), or the founder
  redirects the build order.

### 2026-07-20 — v2 Backlog Adopted After Roadmap Strength Review

- **Status:** Confirmed (founder-approved plan, 2026-07-20)
- **Decision:** The brain's roadmap strength review
  (`docs/planning/ROADMAP_REVIEW_2026-07-20.md`) is adopted. Verdict: the
  v1 build backlog is complete and the remaining PROGRESS.md backlog
  sections are stale (they reference Phase 0 files deleted in the Full
  Restart, or CMA work deferred by COACHING_PIPELINE_V1 §7). PROGRESS.md
  now carries a v2 backlog of 12 tasks (T-A…T-L) in four priority tiers:
  P0 hygiene/unblocking (doc sync, vision-eval harness, diagnosis retry
  hardening), P1 retention loop (streak/Today surface with local
  notifications, deterministic skill profile, reflection loop,
  spaced-repetition review), P2 activation/Must-Haves (onboarding +
  baseline, privacy/deletion completeness, backend auth + deploy
  readiness), P3 founder-gated decisions (paywall scaffolding, free-draft
  grading proposal). All tasks respect the Haiku-only lock — P1 features
  are fully deterministic with no new API calls — and the existing
  brain/worker loop protocol.
- **Why:** The loop had exhausted every actionable item while substantial
  v1 scope from PRODUCT_BRIEF §10 and VISION.md Phase 2 (habit loop,
  longitudinal profile, reflection, onboarding, privacy, auth, paywall)
  had no roadmap representation; stale backlog sections risked a future
  cycle acting on deleted files. Task selection grounded in fresh
  competitor research (Gleam feature set and paywall complaints; Duolingo
  streak-retention evidence) — sources in the review doc.
- **Revisit trigger:** Founder reprioritizes; the vision-quality eval
  fails on real screenshots (then screenshot-path work outranks the
  retention tier); or any P1 task turns out to require model calls after
  all (then it needs a costed founder decision first, per the Haiku lock).

### 2026-07-21 — T-G2 Resolved: Deterministic Runtime Answer Permutation Shipped

- **Status:** Confirmed (executes T-G2, backlogged by the entry directly
  below this one)
- **Decision:** Completion-check choice options are now served in a
  deterministic per-`(user_id, lesson_id, review_count, part_index)`
  seeded permutation (`random.Random(seed).shuffle`, stdlib, not
  security-sensitive) via one shared helper
  (`_shuffled_lesson_content` in `backend/app/main.py`) called
  identically by `GET /lessons/{id}` (serve) and both
  `POST /lessons/{id}/complete` / `.../review` (grade) — a single choke
  point makes served/graded inconsistency structurally impossible. The
  `exercise` block (client-side-only self-check, never submitted to the
  server) is intentionally out of scope. Confirmed to need zero iOS
  changes: the client already submits "array index of whatever was
  displayed," with no notion of an original order.
- **Why:** Closes the original T-G "option-order shuffling for reused
  checks" criterion properly, superseding the cycle-33 static-content
  workaround for the repeat-review case it was meant to cover.
- **Evidence:** Automated: determinism, non-degeneracy across attempt
  indices, no-mutation-of-shared-curriculum-state, and option
  text/feedback pairing all unit-tested; live GET→submit-correct→
  GET-again→submit-new-correct round trip run independently by the
  brain against a real server across multiple users and 3 real review
  cycles on `l02-use-the-setting`, confirming genuine reordering between
  rounds (parts 1 and 2 both changed) with grading always matching
  whatever was actually served.
- **Consequence:** The cycle-33 static reordering (L01, L02) remains in
  place as content-level hygiene (harmless, now redundant for the
  shuffle concern specifically) but is no longer load-bearing for it.
- **Revisit trigger:** None expected; if `_shuffled_lesson_content`'s
  seed inputs ever change shape, its two call-site families (serve,
  grade) must be updated together.

### 2026-07-21 — T-G Shuffle Criterion Deviation Recorded

- **Status:** Confirmed (brain decision under the founder's audit-response
  execution instruction; flagged for founder override)
- **Decision:** v2 task T-G's written acceptance criterion "option-order
  shuffling for reused checks" was implemented as **static content-level
  answer-position variation**, not runtime shuffling: grading is
  index-based end to end (client submits option indices; the server
  compares against `correct_option_index`), so a naive serve-time shuffle
  would desynchronize submitted answers from the key. Cycle 33 varied
  L02's positions; cycle 36 added a mechanical audit test (every lesson
  with ≥2 choice parts must use ≥2 distinct correct indices — this caught
  and fixed L01, whose exercise + check answers all sat at one position).
  True review-time permutation is backlogged as **T-G2**: deterministic
  per-(user, lesson, review-count) seeded permutation applied at both
  serve and grade time — sequenced after T-J.
- **Why:** The 2026-07-21 external audit correctly flagged that this
  deviation was decided in a worker spec but never recorded here, and
  that PROGRESS.md's "done" label hid it. Deviations from written
  acceptance criteria must be decision-logged, not buried in specs.
- **Revisit trigger:** Founder orders T-G2 sooner; or repeat-review
  usage shows memorization is degrading review value (then T-G2 or
  variant question pools become priority).

### 2026-07-20 — Stale VISION/ARCHITECTURE Status Synced to Rebuilt v1

- **Status:** Confirmed (executes task T-A of the founder-approved v2
  backlog)
- **Decision:** VISION.md's status header, Phase 0 section, Phase 2 list,
  and open questions are annotated to post-restart/post-rebuild reality;
  ARCHITECTURE.md's banner now names COACHING_PIPELINE_V1.md as the
  implemented design of record and marks the CMA design as a
  future-upgrade reference only. Historical content was annotated, never
  deleted.
- **Why:** Living docs contradicted the running system (ROADMAP_REVIEW
  §1.3); a reader landing on either doc first got a wrong model of the app.
- **Revisit trigger:** Any future architecture change that makes
  COACHING_PIPELINE_V1.md itself stale (then re-sync or rewrite under a
  new decision entry).

### 2026-07-19 — Coaching Models Locked to Haiku 4.5 Only (Founder Cost Constraint)

- **Status:** Confirmed (founder decision — strict rule)
- **Decision:** ALL Anthropic API calls made by the backend use model id
  `claude-haiku-4-5` and nothing else — no Sonnet, Opus, or any
  higher-tier model anywhere in backend code, now or in future cycles
  (including the eventual screenshot vision-extraction call, where Haiku
  4.5 was already the recorded candidate and is vision-capable).
  **Supersedes** "2026-07-18 — Coaching Diagnosis Model Pinned:
  claude-sonnet-4-6" below. Enforced mechanically: a backend test scans
  `backend/app/` source for forbidden model-name substrings and fails if
  any appears.
- **Why:** Founder instruction 2026-07-19: very limited API budget; cost
  floor takes priority over per-call quality. Haiku 4.5 supports
  structured outputs and vision per the current model catalog, so the
  pipeline design is unchanged — only the model id.
- **Revisit trigger:** Founder relaxes the budget constraint, or diagnosis
  quality on real transcripts is unacceptable (then the founder decides
  the cost/quality trade, not the brain).

### 2026-07-19 — Mandatory Simulator Launch Verification Ends Every Cycle

- **Status:** Confirmed (founder decision)
- **Decision:** From now on, every accepted loop cycle ends with a full
  build and launch of the app in the iPhone 16 simulator (backend running)
  as a mandatory verification step, screenshot-verified, before the cycle
  counts as complete. Build or launch errors found in this step are
  **diagnosed and fixed directly by the brain** — a founder-granted scoped
  exception to the brain-never-implements rule, limited to making the app
  build and launch cleanly during verification — and the launch is
  re-run until clean. (The brain may still route larger fixes through a
  worker micro-cycle when practical; the obligation is that the cycle
  does not close until a clean launch.)
- **Why:** Founder instruction 2026-07-19, grounded in cycle 16's evidence:
  a real launch surfaced two runtime bugs (compatibility-mode letterboxing;
  `.task` on EmptyView never firing) that unit tests could not catch.
- **Consequence:** `.claude/skills/brain-worker-loop/SKILL.md` loop
  protocol gains the verification step (synced in the same cycle that
  records this entry).
- **Revisit trigger:** Founder amends; or the loop starts producing
  backend-only changes where a simulator launch adds no information (then
  propose narrowing to cycles that touch app-visible behavior — founder
  call).

### 2026-07-18 — Coaching Diagnosis Model Pinned: claude-sonnet-4-6

- **Status:** Confirmed (brain decision under recorded cost-tiering policy)
- **Decision:** The coaching pipeline's text-diagnosis call (COACHING_PIPELINE_V1
  stage 2) is implemented with model id `claude-sonnet-4-6` via the plain
  Messages API with structured JSON output (`output_config.format`,
  json_schema). No thinking parameter (bounded judgment task). The Python
  SDK (`anthropic==0.117.0`, pinned in backend/requirements.txt) reads
  `ANTHROPIC_API_KEY` from the process environment via
  `anthropic.Anthropic()` — never from code or config files.
- **Why:** Verified against the current claude-api reference (not memory):
  Sonnet 4.6 is the current mid-tier ($3/$15 per MTok), supports structured
  outputs, and matches ARCHITECTURE.md's recorded model-tiering decision
  (frontier reserved for synthesis-class work; diagnosis is a bounded,
  schema-constrained judgment call). This is the project's documented
  cost-tiering choice, not a silent downgrade. Vision extraction (later
  cycle) keeps Haiku 4.5 (`claude-haiku-4-5`, confirmed vision-capable) as
  the candidate pending the real-screenshot eval required by
  COACHING_PIPELINE_V1 §6.
- **Revisit trigger:** Diagnosis quality on real transcripts proves
  insufficient (then step up a tier and re-baseline cost per diagnosis), or
  model catalog changes retire/supersede the id.

### 2026-07-18 — Planning Docs Migrated Into This Repo

- **Status:** Confirmed (founder-approved migration, pre-archival)
- **Decision:** All five planning-project markdown documents were copied
  byte-exact (checksum-verified) into `docs/planning/`:
  `VALIDATION_PLAN.md` (the validation gate this repo's scope rules
  depend on), `PRODUCT_BRIEF.md` (full product definition),
  `DECISIONS.md` (product decision log), `ORCHESTRATION.md` (the
  brain/worker loop spec that `SKILL.md` and `worker.sh` cite), and
  `CLAUDE_DISCOVERY_PROMPT.md` (reusable discovery process prompt). The
  two decision logs are deliberately separate and complementary: this
  root file = engineering/build decisions; `docs/planning/DECISIONS.md`
  = product decisions. Neither replaces the other. No merges were
  performed — copies are exact; forward-looking references in README,
  PROGRESS, SKILL.md, and worker.sh now point at the in-repo paths, while
  dated historical entries keep their original wording.
- **Why:** The repo referenced planning documents it did not contain; the
  planning project is slated for archival, so the repo must be
  self-contained first.
- **Revisit trigger:** The planning project is archived — remaining
  references to it become historical-only.
