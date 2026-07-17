# Worker Log — SmallTalkCoach build loop

Append-only. Every Codex worker appends exactly one entry per task, after
finishing — whether the task succeeded, partially succeeded, or got blocked.
Never edit or delete earlier entries. The brain reads the recent tail at
every cycle start and reviews the newest entry as part of accepting the
task. Enforced by `.claude/skills/brain-worker-loop/worker.sh`, which exits
with code 4 (automatic reject) when a worker finishes without appending.

Entry format (keep an entry under ~15 lines):

```
## YYYY-MM-DD HH:MM UTC — <task title>
- **Model:** gpt-5.6-terra | gpt-5.6-luna
- **Status:** done | partial | blocked
- **What was done:** <1–3 lines>
- **Files touched:** <paths>
- **Result / verification:** <tests run and their real outcomes — never fabricated>
- **Open issues:** <anything the brain should know; "none" if none>
```

---
