# SmallTalkCoach

A subscription app concept that helps people build durable small-talk and
conversation skills: a structured, Duolingo-style learning path (the
primary experience) plus an AI coaching utility whose primary flow is
screenshot diagnosis of real conversations, feeding users back into the
right lesson. See `VISION.md` for the product direction.

**Current state: planning-first, pre-implementation.** On 2026-07-18 the
founder approved a full restart: the Phase 0 implementation (a FastAPI
backend and SwiftUI iOS app built around the earlier roleplay-practice
concept) was removed from `master`. No application code exists in this
repository right now, and none gets written until the validation
thresholds in `docs/planning/VALIDATION_PLAN.md` are met and the
v1 lesson path is defined.

The removed implementation is archived, not lost — tag `phase0-archive`
holds the full pre-cleanup tree. Recovery is one command:
`git checkout phase0-archive -- backend ios`

## Source of truth

- `VISION.md` — product direction (two-tab v1: Home learning path + AI Coaching)
- `ARCHITECTURE.md` — v1 design reference (describes the removed Phase 0
  implementation and how v1 was planned to grow out of it; kept as design
  input for the rebuild)
- `DECISIONS.md` — append-only engineering decision log
- `PROGRESS.md` — current status and backlog
- `WORKER_LOG.md` — append-only per-task worker execution log
- `.claude/skills/brain-worker-loop/` — build orchestration: `SKILL.md`
  (protocol), `worker.sh` (Codex GPT 5.6 worker runner), `auto_push.sh`
  (safe post-commit push), `tests/`

## How this repo gets built

Development runs as a brain/worker loop: Claude Fable 5 is the brain —
it plans, delegates, reviews, and accepts work, and never implements
directly. Codex (GPT 5.6, `gpt-5.6-terra` at high reasoning effort)
workers execute assigned tasks and report back; every worker task must
append a structured entry to `WORKER_LOG.md` (enforced by `worker.sh`).
Accepted work is committed and pushed via `auto_push.sh` — current branch
to its upstream only, never forced, dirty trees refused.

## Next steps

1. Run the validation interviews defined in
   `docs/planning/VALIDATION_PLAN.md` (10–15 Relocated Newcomers,
   willingness-to-pay probe) and evaluate against its thresholds.
2. If thresholds hold: define the v1 lesson path, then re-derive the
   implementation plan from `VISION.md`/`ARCHITECTURE.md` and start
   brain/worker build cycles.
3. Until then: documentation and planning changes only.
