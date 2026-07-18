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
