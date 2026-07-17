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
- **Workers: Codex (GPT 5.6) only** — `gpt-5.6-terra` (default) or
  `gpt-5.6-luna` for routine tasks. Enforced by `worker.sh`; do not bypass it
  by calling other models or the Agent tool for implementation.

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

   The worker executes and reports back (`report.txt` + the diff it leaves in
   the working tree).
3. **Brain reviews.** Read the actual `git diff` and run the acceptance
   checks yourself (e.g. `cd backend && source .venv/bin/activate && pytest`);
   never accept the worker's self-report as evidence. Known repo trap: `swift
   test` on this machine always exits 0 without running tests — verify Swift
   via `swiftc` compile-and-run of a standalone harness, or `swiftc -parse`
   plus explicit "not build-verified" wording.
4. **Accept or iterate.** Accept → record the result in `PROGRESS.md` (cycle
   log entry: date, what shipped, test status, next item) and move on.
   Reject → write specific, itemized feedback (exact files/lines/problems),
   append it to the spec, and re-run the worker with the combined spec.
5. **Cap: 3 worker rounds per task.** If not converged, do NOT implement it
   yourself — halt, leave the tree in the last reviewed state, and escalate to
   the user with the round-by-round history. The brain never implements; a
   non-converging task means the spec or the task split needs the founder.

## Conventions

- One task in flight at a time; the brain reviews before defining the next.
- Commits happen only after brain acceptance, message describing the increment.
- Never commit red tests; never fabricate verification claims.
- Secrets stay in `~/.env` (which Bash cannot read here — check keys only via
  tools that work, or ask the user); never inline them or let a worker spec
  reference their values.
