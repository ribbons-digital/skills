#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/post_merge.sh [--dry-run] <pr-number>

Verifies that the PR is merged, fast-forwards main, deletes the PR branch
locally and remotely when present, then syncs installed skills.
USAGE
}

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DRY_RUN=0

if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
  shift
fi

PR="${1:-}"
if [[ -z "$PR" ]]; then
  usage >&2
  exit 2
fi

run() {
  if [[ "$DRY_RUN" == "1" ]]; then
    printf 'DRY-RUN:'
    printf ' %q' "$@"
    printf '\n'
  else
    "$@"
  fi
}

state="$(gh pr view "$PR" --json state --jq '.state')"
branch="$(gh pr view "$PR" --json headRefName --jq '.headRefName')"
merge_commit="$(gh pr view "$PR" --json mergeCommit --jq '.mergeCommit.oid // ""')"

if [[ "$state" != "MERGED" ]]; then
  echo "PR #$PR is $state, not MERGED" >&2
  exit 1
fi

cd "$ROOT"

if [[ -n "$(git status --porcelain)" ]]; then
  echo "working tree is not clean; commit or stash before post-merge cleanup" >&2
  git status --short >&2
  exit 1
fi

echo "confirmed PR #$PR merged: $merge_commit"

run git switch main
run git pull --ff-only origin main

if git show-ref --verify --quiet "refs/heads/$branch"; then
  run git branch -d "$branch"
else
  echo "local branch $branch not present; skipping local delete"
fi

if [[ "$branch" != "main" && "$branch" != "master" ]]; then
  if [[ "$DRY_RUN" == "1" ]]; then
    run git push origin --delete "$branch"
  elif git push origin --delete "$branch"; then
    echo "deleted remote branch $branch"
  else
    echo "remote branch $branch not deleted; it may already be gone or origin may be unreachable" >&2
  fi
fi

run "$ROOT/scripts/sync_skills.sh"

echo "post-merge cleanup complete for PR #$PR"
