---
name: repo-hygiene
description: Inspect and safely clean local git repository hygiene: stale branches, gone upstreams, old worktrees, forgotten uncommitted changes, merged branches, large caches, and cleanup candidates. Use when asked about branch cleanup, orphaned branches, worktree cleanup, or repo housekeeping.
---

# Repo Hygiene

Surface candidates first. Delete only when safety conditions are clear or the user approves.

## First checks

Start read-only:

```bash
git status --short --branch
git remote -v
git worktree list --porcelain
```

Then, if network/state mutation is acceptable for the task, update remote-tracking refs:

```bash
git fetch --prune --quiet
```

If there is active uncommitted work, running agents, or recent edits, avoid destructive cleanup and report candidates instead.

## Branch categories

List local branches with upstream state:

```bash
git branch -vv
```

Classify:
- **gone upstream**: upstream deleted after fetch/prune.
- **merged to base**: `git merge-base --is-ancestor <branch> <base>` succeeds.
- **open PR head**: branch still backs an open PR.
- **checked out in worktree**: branch is active elsewhere.
- **recent work**: latest commit or modified files are recent.
- **unknown/squash-merged-looking**: upstream gone but not ancestor of base.

## Safe local branch deletion

Auto-delete only if all are true:
- upstream is gone or the user explicitly selected the branch for cleanup
- not checked out in any worktree
- not the head of an open PR
- merged to base by ancestry
- no uncommitted work depends on it

Ambiguous branches, local-only branches, and squash-merged-looking branches require explicit approval.

Command:

```bash
git branch -d <branch>
```

Use `-D` only with explicit approval. Do not infer disposability from age alone.

## Open PR check

For GitHub repos:

```bash
gh pr list --state open --json number,headRefName,title
```

Never delete a branch that is the head of an open PR unless the PR is intentionally abandoned and the user approves.

## Worktree cleanup

```bash
git worktree list --porcelain
git worktree prune --dry-run
```

Candidate for removal if:
- no uncommitted changes
- branch has no recent commits
- branch is merged or PR closed
- no active agent/process is using the path

Remove only after approval unless the worktree is missing/broken and `git worktree prune --dry-run` shows it as pruneable.

## Forgotten work

Find old uncommitted changes:

```bash
git status --porcelain
# inspect mtimes carefully; do not assume old means unwanted
```

Report:
- repo/path
- changed files
- newest modification age
- suggested action: commit, stash, discard, or leave

Never discard uncommitted changes without explicit approval.

## Suggested report

```markdown
Repo hygiene candidates:

Safe-delete local branches:
- <branch> — upstream gone, merged to <base>, not in worktree/open PR

Needs approval:
- <branch> — upstream gone, not merged by ancestry; maybe squash-merged
- <worktree> — old and clean, branch closed

Do not touch:
- <branch> — open PR #123
- <branch> — checked out in <path>
- <repo> — uncommitted changes
```

## Destructive command checklist

Before deleting branches/worktrees/stashes:
1. Re-run status/fetch checks.
2. Confirm not active in a worktree or open PR.
3. Prefer recoverable commands (`git branch -d`, `trash`) over irreversible ones.
4. Show exactly what will be deleted if asking for approval.
