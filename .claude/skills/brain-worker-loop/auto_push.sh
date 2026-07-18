#!/usr/bin/env bash
# Deterministic post-commit auto-push for the brain/worker loop.
#
# Policy (repo DECISIONS.md, "2026-07-18 — Safe Auto-Push After Verified
# Runs"): after every successful verified run, if and only if the run
# created a commit, auto-push the current branch to its configured
# upstream. Refuse automated runs on a dirty tree. Never force-push or
# retry endlessly. Keep the local commit if push fails and surface the
# failure. AUTO_PUSH=0 disables this behavior; default is AUTO_PUSH=1.
#
# Usage: auto_push.sh -b <baseline-commit> [-C <repo-dir>]
#   <baseline-commit> is HEAD captured at the start of the run; a push
#   happens only when current HEAD differs (the run created a commit).
#
# Exit codes:
#   0  pushed, or clean no-op (AUTO_PUSH=0, or no commit created this run)
#   2  usage error (missing/invalid arguments, not a git repo)
#   3  dirty working tree — automated run must stop, nothing pushed
#   4  not pushable: detached HEAD, or no remote configured
#   5  push failed — local commit kept; do NOT retry automatically
set -euo pipefail

BASELINE=""
REPO="."

usage() { echo "usage: auto_push.sh -b <baseline-commit> [-C <repo-dir>]"; }

while getopts "b:C:h" opt; do
  case "$opt" in
    b) BASELINE="$OPTARG" ;;
    C) REPO="$OPTARG" ;;
    h) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
done

[ -n "$BASELINE" ] || { echo "auto_push: -b <baseline-commit> is required (HEAD at run start)" >&2; exit 2; }
cd "$REPO" 2>/dev/null || { echo "auto_push: cannot cd to '$REPO'" >&2; exit 2; }
git rev-parse --git-dir >/dev/null 2>&1 || { echo "auto_push: '$REPO' is not a git repository" >&2; exit 2; }

if [ "${AUTO_PUSH:-1}" = "0" ]; then
  echo "auto_push: disabled (AUTO_PUSH=0) — not pushing"
  exit 0
fi

if [ -n "$(git status --porcelain)" ]; then
  echo "auto_push: working tree is dirty — automated runs must not push; commit or clean up first" >&2
  exit 3
fi

BASELINE_SHA="$(git rev-parse --verify --quiet "${BASELINE}^{commit}")" || { echo "auto_push: baseline '$BASELINE' is not a commit in this repo" >&2; exit 2; }
HEAD_SHA="$(git rev-parse HEAD)"
if [ "$HEAD_SHA" = "$BASELINE_SHA" ]; then
  echo "auto_push: no commit created this run (HEAD unchanged since baseline) — nothing to push"
  exit 0
fi

BRANCH="$(git symbolic-ref --quiet --short HEAD)" || { echo "auto_push: detached HEAD — refusing to push" >&2; exit 4; }

PUSH_FAIL_MSG="auto_push: push FAILED — local commit(s) kept on branch; fix the cause (network, auth, remote ahead) and push manually. No automatic retry, never force-push."

if UPSTREAM="$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null)"; then
  REMOTE="${UPSTREAM%%/*}"
  echo "auto_push: pushing '$BRANCH' to upstream '$UPSTREAM'"
  if ! git push "$REMOTE" "$BRANCH"; then
    echo "$PUSH_FAIL_MSG" >&2
    exit 5
  fi
else
  if git remote get-url origin >/dev/null 2>&1; then
    REMOTE="origin"
  elif [ "$(git remote | wc -l | tr -d ' ')" = "1" ]; then
    REMOTE="$(git remote)"
  else
    echo "auto_push: no upstream configured for '$BRANCH' and no single usable remote — refusing to push" >&2
    exit 4
  fi
  echo "auto_push: no upstream for '$BRANCH' — pushing with -u to '$REMOTE'"
  if ! git push -u "$REMOTE" "$BRANCH"; then
    echo "$PUSH_FAIL_MSG" >&2
    exit 5
  fi
fi

echo "auto_push: pushed '$BRANCH' at $HEAD_SHA"
