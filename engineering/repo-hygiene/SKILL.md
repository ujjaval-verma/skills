---
name: repo-hygiene
description: Inspect and safely clean local git repository hygiene: stale/merged local branches, gone upstreams, old worktrees, and forgotten uncommitted changes. Use when asked about branch cleanup, worktree cleanup, or repo housekeeping.
updated: 2026-10-04
---

# Repo Hygiene

Surface candidates first. Delete only when the safety conditions below are verifiably true or the user approves.

Start read-only: `git status --short --branch`, `git worktree list --porcelain`, then `git fetch --prune --quiet` if touching the network is acceptable. When the tree is unclean or an agent/process is running against the repo, report candidates only and run no destructive cleanup.

## Local branch deletion

Delete without asking only if every condition is true, each checked by command rather than judgment:
- upstream is gone (`git branch -vv` shows `: gone]`) or the user explicitly selected the branch
- not checked out in any worktree (`git worktree list`)
- not the head of an open PR (`gh pr list --state open --json number,headRefName,title`); an abandoned PR's head branch needs explicit approval
- merged to base by ancestry (`git merge-base --is-ancestor <branch> <base>` exits 0)

Then use `git branch -d`, which itself refuses unmerged branches. Local-only, ambiguous, and squash-merged-looking branches (upstream gone but not an ancestor of base) need explicit approval. `git branch -D` needs explicit approval every time.

Branch age is a signal to investigate, never authorization: route every age-based candidate to approval instead of deleting on "old" or "recent".

## Worktrees

A worktree is a removal candidate only if it has no uncommitted changes, its branch is merged to base or its PR is closed, and no agent/process is using the path. Remove only after approval, unless the worktree is missing or broken and `git worktree prune --dry-run` lists it as pruneable. If a `trash` command exists, prefer it over `rm -rf` for worktree directories; otherwise ask before deleting the directory.

## Uncommitted work

Never discard uncommitted changes without explicit approval. Report modification age as a signal, never as grounds to discard, and suggest commit, stash, discard, or leave.

## Reporting

Group candidates as **safe-delete** / **needs approval** / **do not touch**, each with the evidence for its classification. When asking for approval, show exactly what will be deleted.
