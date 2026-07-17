#!/usr/bin/env bash
# Codex worker runner for the brain/worker build loop (see SKILL.md in this
# directory and smalltalk-coach-planning/ORCHESTRATION.md).
#
# Model rule is FINAL (planning DECISIONS.md, 2026-07-18 entry): every worker
# runs Codex GPT 5.6 only — gpt-5.6-terra (default) or gpt-5.6-luna. The brain
# (Claude Fable 5) never implements; it only writes the spec this script hands
# to the worker, then reviews the resulting diff.
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

case "$MODEL" in
  gpt-5.6-*) ;;
  *) echo "worker.sh: refusing model '$MODEL' — workers are Codex (GPT 5.6) only, final rule" >&2; exit 2 ;;
esac

command -v codex >/dev/null || { echo "worker.sh: codex CLI not installed (npm install -g @openai/codex)" >&2; exit 3; }

OUT="${OUT:-$(mktemp -t worker-report)}"

# workspace-write keeps the worker sandboxed to the workdir (no network); the
# brain widens this per task only when the spec genuinely needs it.
codex exec \
  -m "$MODEL" \
  -c "model_reasoning_effort=\"$EFFORT\"" \
  --sandbox workspace-write \
  -C "$WORKDIR" \
  -o "$OUT" \
  "$SPEC"

echo "worker-report: $OUT"
