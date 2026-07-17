# SmallTalkCoach — Engineering Decision Log (build repo)

Append-only: one dated entry per real engineering/build decision, never
rewritten or restructured. Product-level decisions live in the planning
project (`smalltalk-coach-planning/DECISIONS.md`) — do not mix them here.
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
