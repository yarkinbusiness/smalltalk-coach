# Progress & backlog

State file for the automated brain-worker-loop (Fable-5 coordinator +
Sonnet-5 workers, "Plan big, execute small" cost-tiering pattern — see
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

<!-- Each automated cycle appends one entry here: date, what changed, what's next. -->
