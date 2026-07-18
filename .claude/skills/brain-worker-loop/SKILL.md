---
name: brain-worker-loop
description: Run one brain/worker build cycle — Claude Fable 5 brain plans, delegates to a Codex (GPT 5.6) worker via worker.sh, reviews the diff, accepts or reassigns. Use for any implementation task on this repo once the validation gate is cleared.
---

# Brain/Worker Build Loop

Spec: `smalltalk-coach-planning/ORCHESTRATION.md`. Model rules locked in that
project's `DECISIONS.md` ("2026-07-18 — Worker Model Locked to Codex (GPT 5.6)")
— final, not open to change:

- **Brain / orchestrator: Claude Fable 5 only.** The session running this skill
  must be Fable 5; if it is not, stop and tell the user. The brain plans, breaks
  work into tasks with acceptance criteria, delegates, reviews, and decides
  accept or iterate. **The brain never implements directly** — no source edits
  by the brain, even to "quickly fix" a near-miss.
- **Workers: Codex (GPT 5.6) only** — standard config `gpt-5.6-terra` at
  `model_reasoning_effort=high` (this is the CLI's thinking control for
  GPT 5.6 — no separate toggle — so thinking is enabled and deep at high).
  `gpt-5.6-luna` is allowed only when the brain explicitly picks it for a
  routine task. Enforced by `worker.sh`, which prints the effective
  model/effort at the start of every run; do not bypass it by calling other
  models or the Agent tool for implementation.

## Activation guard (mandatory, every run)

1. Check for existing scheduled loops touching this repo: `CronList`, plus
   `crontab -l`. If any active loop exists, defer to it and stop.
2. Read `PROGRESS.md` at the repo root and defer to its current state; a prior
   automated loop has committed to `master` before.
3. Scope gate: **no app code until the planning repo's `VALIDATION_PLAN.md`
   thresholds are met and the v1 lesson path is defined.** Until then this
   skill may only be used for non-app work the user explicitly requests.
4. First action of any new loop: update `PROGRESS.md` (what the loop is doing,
   under which model rules) — not as an afterthought.
5. Automated runs require a clean working tree (`git status --porcelain`
   empty) — refuse to start otherwise. Then capture the run baseline:
   `BASELINE="$(git rev-parse HEAD)"` (needed by auto-push, step 4 below).

## Project-resident memory (single source of truth)

The brain (`.claude`) and Codex workers (`.codex`) have disjoint native
memory systems — neither can read the other's. All shared loop memory
therefore lives in this repository (decision: repo `DECISIONS.md`,
"2026-07-18 — Project-Resident Memory for the Build Loop"):

- `PROGRESS.md` — status, backlog, cycle log. The brain updates it after
  every accepted work unit and at loop start/stop.
- `DECISIONS.md` (repo root) — append-only engineering decisions. Product
  decisions go to `smalltalk-coach-planning/DECISIONS.md` instead; the brain
  routes each decision to the right file.
- `WORKER_LOG.md` (repo root) — append-only, one structured entry per worker
  task, format documented at the top of the file. `worker.sh` injects this
  requirement into every spec and **exits 4** when a worker finishes without
  appending — treat exit 4 as an automatic reject, with the missing log
  entry named in the feedback.

**Cycle start (every cycle, before defining any task):** the brain reads
`PROGRESS.md`, both `DECISIONS.md` files, and the recent tail of
`WORKER_LOG.md`. **After each review:** the brain writes its verdict and
feedback into `PROGRESS.md` (cycle log), appends durable lessons to the
right `DECISIONS.md`, and mirrors durable lessons to its persistent memory
(auto-memory files; a claude-mem/cmem observation when that plugin is
active). Mirrors are best-effort copies — the repository is the source of
truth, and no loop state may live only in a mirror.

## Loop protocol (per work unit)

1. **Brain defines the task.** Write a precise spec: exact files/areas, expected
   behavior, constraints (patterns to follow, files not to touch), and explicit
   acceptance criteria including which tests must pass. Save it to a file under
   the session scratchpad.
2. **Delegate to the worker:**

   ```bash
   .claude/skills/brain-worker-loop/worker.sh \
     -C "/Users/yarkinyavuz/Desktop/untitled folder/smalltalk-coach" \
     -o /path/to/report.txt \
     - < /path/to/spec.md
   ```

   The worker executes and reports back (`report.txt`, the diff it leaves in
   the working tree, and its `WORKER_LOG.md` entry — worker.sh injects the
   memory protocol into the spec automatically and exits 4 if the entry is
   missing).
3. **Brain reviews.** Read the actual `git diff` (including the new
   `WORKER_LOG.md` entry — it must be a true append matching the documented
   format) and run the acceptance checks yourself (e.g. `cd backend &&
   source .venv/bin/activate && pytest`);
   never accept the worker's self-report as evidence. Known repo trap: `swift
   test` on this machine always exits 0 without running tests — verify Swift
   via `swiftc` compile-and-run of a standalone harness, or `swiftc -parse`
   plus explicit "not build-verified" wording.
4. **Accept or iterate.** Accept → record the result in `PROGRESS.md` (cycle
   log entry: date, what shipped, test status, next item), commit, then
   auto-push:

   ```bash
   .claude/skills/brain-worker-loop/auto_push.sh -b "$BASELINE" \
     -C "/Users/yarkinyavuz/Desktop/untitled folder/smalltalk-coach"
   ```

   Auto-push policy (verbatim, decision: repo `DECISIONS.md` "2026-07-18 —
   Safe Auto-Push After Verified Runs"): "After every successful verified
   run, if and only if the run created a commit, auto-push the current
   branch to its configured upstream. Refuse automated runs on a dirty
   tree. Never force-push or retry endlessly. Keep the local commit if push
   fails and surface the failure. AUTO_PUSH=0 disables this behavior;
   default is AUTO_PUSH=1."
   Exit codes: 0 = pushed or clean no-op; 3 = dirty tree; 4 = detached
   HEAD/no remote; 5 = push failed (local commit kept — surface the error,
   do not retry). Tests: `tests/test_auto_push.sh`. Then move on.
   Reject → write specific, itemized feedback (exact files/lines/problems),
   append it to the spec, and re-run the worker with the combined spec.
5. **Cap: 3 worker rounds per task.** If not converged, do NOT implement it
   yourself — halt, leave the tree in the last reviewed state, and escalate to
   the user with the round-by-round history. The brain never implements; a
   non-converging task means the spec or the task split needs the founder.

## Conventions

- One task in flight at a time; the brain reviews before defining the next.
  (`WORKER_LOG.md`'s append-only model assumes this single-writer setup.)
- Commits happen only after brain acceptance, message describing the
  increment; the accepted work's `WORKER_LOG.md` entries commit with it.
- Never commit red tests; never fabricate verification claims.
- Secrets stay in `~/.env` (which Bash cannot read here — check keys only via
  tools that work, or ask the user); never inline them or let a worker spec
  reference their values.
