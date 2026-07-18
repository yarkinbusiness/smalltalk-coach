#!/usr/bin/env bash
# Tests for auto_push.sh. Uses throwaway repos and a local bare "remote"
# under a temp directory — no network, nothing touches the real repo.
set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
AP="$HERE/../auto_push.sh"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/autopush-test.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT
PASS=0
FAIL=0

check() { # check <expected-exit> <actual-exit> <description>
  if [ "$1" = "$2" ]; then
    PASS=$((PASS + 1)); echo "ok   (exit $2) $3"
  else
    FAIL=$((FAIL + 1)); echo "FAIL (want exit $1, got $2) $3"
    sed 's/^/     | /' "$TMP/out"
  fi
}

mkrepo() { # mkrepo <dir> — new repo with one commit, main branch
  git init -q -b main "$1"
  ( cd "$1" &&
    git config user.email test@test && git config user.name test &&
    echo one > file.txt && git add file.txt && git commit -qm "init" )
}

# --- 1. dirty tree is rejected (exit 3), nothing pushed ---
mkrepo "$TMP/dirty"
( cd "$TMP/dirty" && echo change >> file.txt )
BASE="$(cd "$TMP/dirty" && git rev-parse HEAD)"
"$AP" -b "$BASE" -C "$TMP/dirty" > "$TMP/out" 2>&1
check 3 $? "dirty tree rejected"

# --- 2. AUTO_PUSH=0 disables (exit 0, no push attempted) ---
AUTO_PUSH=0 "$AP" -b "$BASE" -C "$TMP/dirty" > "$TMP/out" 2>&1
check 0 $? "AUTO_PUSH=0 disables (clean no-op even before other checks)"
grep -q "disabled" "$TMP/out" || { FAIL=$((FAIL + 1)); echo "FAIL: expected 'disabled' message"; }

# --- 3. no commit created this run -> no push (exit 0) ---
mkrepo "$TMP/nocommit"
BASE="$(cd "$TMP/nocommit" && git rev-parse HEAD)"
"$AP" -b "$BASE" -C "$TMP/nocommit" > "$TMP/out" 2>&1
check 0 $? "no commit created -> nothing to push"
grep -q "nothing to push" "$TMP/out" || { FAIL=$((FAIL + 1)); echo "FAIL: expected 'nothing to push' message"; }

# --- 4. commit created but no remote at all -> exit 4 ---
mkrepo "$TMP/noremote"
BASE="$(cd "$TMP/noremote" && git rev-parse HEAD)"
( cd "$TMP/noremote" && echo two > two.txt && git add two.txt && git commit -qm "second" )
"$AP" -b "$BASE" -C "$TMP/noremote" > "$TMP/out" 2>&1
check 4 $? "no remote configured -> refused"

# --- 5. success: missing upstream is set safely (-u), push lands ---
git init -q --bare "$TMP/remote.git"
mkrepo "$TMP/happy"
( cd "$TMP/happy" && git remote add origin "$TMP/remote.git" )
BASE="$(cd "$TMP/happy" && git rev-parse HEAD)"
( cd "$TMP/happy" && echo two > two.txt && git add two.txt && git commit -qm "second" )
"$AP" -b "$BASE" -C "$TMP/happy" > "$TMP/out" 2>&1
check 0 $? "push with missing upstream sets upstream and succeeds"
LOCAL="$(cd "$TMP/happy" && git rev-parse HEAD)"
REMOTE_HEAD="$(cd "$TMP/remote.git" && git rev-parse refs/heads/main)"
[ "$LOCAL" = "$REMOTE_HEAD" ] && { PASS=$((PASS + 1)); echo "ok   remote HEAD matches local HEAD after -u push"; } \
  || { FAIL=$((FAIL + 1)); echo "FAIL remote HEAD != local HEAD"; }
UP="$(cd "$TMP/happy" && git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null)"
[ "$UP" = "origin/main" ] && { PASS=$((PASS + 1)); echo "ok   upstream now origin/main"; } \
  || { FAIL=$((FAIL + 1)); echo "FAIL upstream not set (got '$UP')"; }

# --- 6. success: existing upstream, current branch only ---
BASE="$LOCAL"
( cd "$TMP/happy" && echo three > three.txt && git add three.txt && git commit -qm "third" )
"$AP" -b "$BASE" -C "$TMP/happy" > "$TMP/out" 2>&1
check 0 $? "push to existing upstream succeeds"
LOCAL="$(cd "$TMP/happy" && git rev-parse HEAD)"
REMOTE_HEAD="$(cd "$TMP/remote.git" && git rev-parse refs/heads/main)"
[ "$LOCAL" = "$REMOTE_HEAD" ] && { PASS=$((PASS + 1)); echo "ok   remote HEAD matches after upstream push"; } \
  || { FAIL=$((FAIL + 1)); echo "FAIL remote HEAD != local HEAD"; }

# --- 7. push failure: broken remote -> exit 5, local commit kept ---
BASE="$LOCAL"
( cd "$TMP/happy" && git remote set-url origin "$TMP/does-not-exist.git" &&
  echo four > four.txt && git add four.txt && git commit -qm "fourth" )
NEWHEAD="$(cd "$TMP/happy" && git rev-parse HEAD)"
"$AP" -b "$BASE" -C "$TMP/happy" > "$TMP/out" 2>&1
check 5 $? "push failure reported as exit 5"
grep -q "push FAILED" "$TMP/out" || { FAIL=$((FAIL + 1)); echo "FAIL: expected clear failure message"; }
AFTER="$(cd "$TMP/happy" && git rev-parse HEAD)"
[ "$AFTER" = "$NEWHEAD" ] && { PASS=$((PASS + 1)); echo "ok   local commit kept after failed push"; } \
  || { FAIL=$((FAIL + 1)); echo "FAIL local commit lost"; }

echo "----------------------------------------"
echo "passed: $PASS  failed: $FAIL"
[ "$FAIL" = "0" ]
