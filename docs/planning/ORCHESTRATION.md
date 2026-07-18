# Smalltalk Coach — Build Orchestration (Brain/Worker Loop)

Decision records: `DECISIONS.md` → "2026-07-17 — Brain/Worker Orchestration for Build Phase" (Confirmed) and "2026-07-18 — Worker Model Locked to Codex (GPT 5.6)" (Confirmed, final).

## Roles

- **Brain / orchestrator — Claude Fable 5 only.** Thinks, plans, breaks work into tasks with acceptance criteria, assigns them, reviews all worker output, and decides accept or iterate. Owns architecture and product-intent decisions; never delegates judgment and **never implements directly**.
- **Worker / executor — Codex (GPT 5.6) only** — CLI slugs `gpt-5.6-terra` (default) or `gpt-5.6-luna` for routine tasks. Executes exactly the assigned task and reports output plus any blockers back to the brain. Does not make product or architecture decisions. (The earlier per-task choice including Sonnet 5 is superseded by the 2026-07-18 decision entry.)

## Loop Protocol

1. Brain defines a task with explicit acceptance criteria.
2. Worker executes and reports its output.
3. Brain reviews the output against the criteria.
4. Accept → next task. Reject → brain writes specific feedback and the worker iterates.
5. Repeat until the work unit is complete; brain records progress in the app repo's coordination file.

## Explicitly Not CLAUDE.md-Only

A static CLAUDE.md-instructions-only setup is not the mechanism for this project. The brain/worker loop with active per-task review is the core setup; instruction files supplement it but do not replace the review loop.

## Activation Guard (required before starting any loop)

- Check for existing scheduled loops or cron jobs touching the app repo (e.g., CronList) before starting or resuming autonomous work.
- Read the app repo's `PROGRESS.md` (or equivalent coordination file) and defer to it — an independent automated loop has committed to the smalltalk-coach repo before.
- If starting a new loop, create or update that coordination file as the first step, not an afterthought.

## Implementation (built 2026-07-18)

- The harness lives in the app repo (`smalltalk-coach/.claude/skills/brain-worker-loop/`): `SKILL.md` carries the brain-side loop protocol and activation guard; `worker.sh` invokes workers via `codex exec` and enforces the GPT 5.6-only rule in code.
- Verified: Codex CLI 0.144.5 with existing ChatGPT auth; `gpt-5.6-terra` smoke task and a full `worker.sh` end-to-end run both passed; the script refuses non-GPT-5.6 models.
- The two pre-existing scheduled-task loop skills (Fable-5 + Sonnet-5 workers, in `~/.claude/scheduled-tasks/`) are marked superseded; the app repo's `PROGRESS.md` records the handover. No scheduled loop is active.
- Project-resident memory layer (added 2026-07-18, founder decision; record: app repo `DECISIONS.md` → "Project-Resident Memory for the Build Loop"): the repo's `PROGRESS.md`, `DECISIONS.md`, and `WORKER_LOG.md` are the loop's single source of truth across the brain's and workers' disjoint native memories; `worker.sh` injects the read-then-log protocol into every worker spec and rejects unlogged work (exit 4). Brain-side mirrors to persistent memory are best-effort copies only.
- Safe auto-push (added 2026-07-18, founder decision; record: app repo `DECISIONS.md` → "Safe Auto-Push After Verified Runs"): after a successful verified run that created a commit, `auto_push.sh` pushes the current branch to its upstream — dirty tree refused, never force, single attempt, local commit kept on failure, `AUTO_PUSH=0` disables. Covered by `tests/test_auto_push.sh` against a local bare remote.
- Built as harness/tooling only — the loop has not been activated (see Scope below).

## Scope

- This planning folder stays documentation-only.
- No app code until the v1 lesson path is defined and the founder explicitly approves build start. See root `DECISIONS.md` → "2026-07-18 — Build Scope Gate Narrowed (Interview Thresholds Waived)" and `docs/planning/DECISIONS.md` → "2026-07-18 — Validation Interviews Deferred; Build Gate Waived (Founder)".
