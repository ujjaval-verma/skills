---
name: repo-hygiene
description: Inspect and safely clean local git repository hygiene: stale/merged local branches, gone upstreams, old worktrees, and forgotten uncommitted changes. Use when asked about branch cleanup, worktree cleanup, or repo housekeeping.
updated: 2026-07-07
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

When the tree is unclean (`git status --short` non-empty) or an agent/process is running against the repo, report candidates only — do not run destructive cleanup.

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

Auto-delete only if every condition below is verifiably true — each is a checkable command, not a judgment call:
- upstream is gone (`git branch -vv` shows `: gone]`) or the user explicitly selected the branch for cleanup
- not checked out in any worktree (`git worktree list`)
- not the head of an open PR (`gh pr list --state open`)
- merged to base by ancestry (`git merge-base --is-ancestor <branch> <base>` exits 0)

Ancestry-merged plus not-checked-out already guarantees no unique commits are stranded, so `git branch -d` (which itself refuses to delete unmerged branches) is safe here.

Ambiguous branches, local-only branches, and squash-merged-looking branches require explicit approval.

Command:

```bash
git branch -d <branch>
```

Use `-D` only with explicit approval. Treat branch age as a signal to investigate, never as authorization — route every age-based candidate to approval rather than deleting on "old" or "recent".

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
- branch is merged to base or its PR is closed
- no active agent/process is using the path

Remove only after approval unless the worktree is missing/broken and `git worktree prune --dry-run` shows it as pruneable.

## Forgotten work

Find old uncommitted changes:

```bash
git status --porcelain
# report modification age as a signal to surface for the user; never discard on age
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
