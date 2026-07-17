#!/usr/bin/env bash
# Codex worker runner for the brain/worker build loop (see SKILL.md in this
# directory and smalltalk-coach-planning/ORCHESTRATION.md).
#
# Model rule is FINAL (planning DECISIONS.md, 2026-07-18 entry): every worker
# runs Codex GPT 5.6 only — gpt-5.6-terra (default) or gpt-5.6-luna. The brain
# (Claude Fable 5) never implements; it only writes the spec this script hands
# to the worker, then reviews the resulting diff.
#
# Project-resident memory (repo DECISIONS.md, 2026-07-18 entry): the memory
# protocol below is injected into every spec, and after the run this script
# verifies the worker appended to WORKER_LOG.md.
#
# Exit codes: 2 usage/model violation, 3 codex CLI missing,
#             4 worker finished without appending WORKER_LOG.md (brain must
#               treat the task as non-compliant and reject).
set -euo pipefail

MODEL="${WORKER_MODEL:-gpt-5.6-terra}"
EFFORT="${WORKER_REASONING:-high}"
WORKDIR=""
OUT=""

usage() {
  echo "usage: worker.sh -C <workdir> [-m gpt-5.6-terra|gpt-5.6-luna] [-o report-file] '<task spec>'" >&2
  echo "       (pass '-' as the task spec to read it from stdin)" >&2
}

while getopts "C:m:o:h" opt; do
  case "$opt" in
    C) WORKDIR="$OPTARG" ;;
    m) MODEL="$OPTARG" ;;
    o) OUT="$OPTARG" ;;
    h) usage; exit 0 ;;
    *) usage; exit 2 ;;
  esac
done
shift $((OPTIND - 1))
SPEC="${1:-}"

[ -n "$WORKDIR" ] || { echo "worker.sh: -C <workdir> is required" >&2; exit 2; }
[ -d "$WORKDIR" ] || { echo "worker.sh: workdir '$WORKDIR' does not exist" >&2; exit 2; }
[ -n "$SPEC" ] || { echo "worker.sh: task spec required (argument, or '-' for stdin)" >&2; exit 2; }
[ "$SPEC" = "-" ] && SPEC="$(cat)"

case "$MODEL" in
  gpt-5.6-*) ;;
  *) echo "worker.sh: refusing model '$MODEL' — workers are Codex (GPT 5.6) only, final rule" >&2; exit 2 ;;
esac

command -v codex >/dev/null || { echo "worker.sh: codex CLI not installed (npm install -g @openai/codex)" >&2; exit 3; }

# Project-resident memory: seed a minimal log if the workdir has none (the
# real repo ships a full WORKER_LOG.md with the format documented on top).
LOG_FILE="$WORKDIR/WORKER_LOG.md"
if [ ! -f "$LOG_FILE" ]; then
  printf '# Worker Log\n\nAppend-only: one structured entry per worker task.\n\n---\n' > "$LOG_FILE"
fi
LOG_HASH_BEFORE="$(shasum "$LOG_FILE" | cut -d' ' -f1)"

PROTOCOL="== Project memory protocol (mandatory) ==
Shared memory for this project lives in the repository, not in your session.
1. Before starting: read PROGRESS.md and DECISIONS.md at the repo root (if
   present) and the most recent entries of WORKER_LOG.md.
2. After finishing the task — whether it succeeded, partially succeeded, or
   got blocked — APPEND exactly one entry to WORKER_LOG.md at the repo root,
   following the entry format documented at the top of that file (task title,
   model, status, what was done, files touched, result/verification, open
   issues). Never edit or delete earlier entries. Never fabricate
   verification claims.
The log entry is part of the task's acceptance criteria: the task counts as
incomplete without it, and the reviewer rejects unlogged work automatically.
== End memory protocol =="

FULL_SPEC="$PROTOCOL

$SPEC"

OUT="${OUT:-$(mktemp -t worker-report)}"

# workspace-write keeps the worker sandboxed to the workdir (no network); the
# brain widens this per task only when the spec genuinely needs it.
codex exec \
  -m "$MODEL" \
  -c "model_reasoning_effort=\"$EFFORT\"" \
  --sandbox workspace-write \
  -C "$WORKDIR" \
  -o "$OUT" \
  "$FULL_SPEC"

LOG_HASH_AFTER="$(shasum "$LOG_FILE" | cut -d' ' -f1)"
if [ "$LOG_HASH_BEFORE" = "$LOG_HASH_AFTER" ]; then
  echo "worker.sh: worker finished WITHOUT appending WORKER_LOG.md — non-compliant, reject this round (exit 4)" >&2
  echo "worker-report: $OUT" >&2
  exit 4
fi

echo "worker-report: $OUT"
