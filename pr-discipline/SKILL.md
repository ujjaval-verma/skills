---
name: pr-discipline
description: Safety rules for opening, reviewing, rebasing, auto-merging, or landing pull requests. Use before branch protection edits, required-check changes, auto-merge, lockfile conflict resolution, force-pushes, merge queue nudges, or when PRs are stuck/dirty/blocked.
---

# PR Discipline

Hard rules for high-velocity repositories. Prefer slow correct merges over fast broken main.

## Required-check changes

Never add a required status check before the workflow that emits it is already on the protected branch and has reported green at least once.

Correct sequence:
1. Merge workflow/check producer without making it required.
2. Wait for a protected-branch run.
3. Confirm the exact check name.
4. Patch branch protection.
5. Verify a fresh PR sees the required check.

If you invert this, every PR can become blocked waiting for a check that cannot exist yet.

## Auto-merge discipline

After enabling auto-merge, verify the PR actually lands.

Check for:
- `DIRTY` / conflicts after another PR merged
- required checks pending forever
- failed checks that are required indirectly
- branch protection mismatch
- merge queue state

Do not report “merged” until the hosting platform says merged.

## Lockfile conflicts

Regenerate lockfiles through the repo’s package manager; do not hand-merge conflict markers. First inspect repo docs, package-manager choice, and CI expectations so you do not rewrite a lockfile with the wrong tool or version.

Generic recipe, after confirming the package-manager policy:

```bash
git fetch origin
git rebase origin/<base>
# on lockfile conflict, if the repo policy supports regeneration:
# remove or checkout the conflicted lockfile as appropriate for that package manager
<package-manager install command>
git add <lockfile>
git rebase --continue
git push --force-with-lease origin HEAD:<branch>
```

Use the repo’s package manager and lockfile policy. If unsure, inspect existing CI/docs before choosing npm/pnpm/yarn/bun/cargo/go/etc.

## Real content conflicts

- Read both sides before resolving.
- Keep additive changes from both branches when compatible.
- Treat contradictory logic as a design conflict, not a mechanical merge.
- Run affected tests after resolution.
- Use `--force-with-lease`, never blind `--force`.

## Branch protection and merge settings

Before editing branch protection:
- dump current settings
- record required contexts before/after
- understand strict/up-to-date requirements
- confirm admin bypass expectations
- avoid changing multiple policy dimensions at once

Do not weaken protection just to land a PR unless the user explicitly approves and understands the risk.

## Parallel agents

If multiple agents will touch one repo, each must use a separate `git worktree`.

Safe pattern:

```bash
git worktree add ../<repo>-WORKTREE-<slug> -b <branch> origin/<base>
```

Avoid temporary directories if the execution environment restricts access or may clean them; prefer a repo-adjacent or user-approved worktree path.

## Review discipline

Non-trivial PRs need independent review. Watch especially for:
- weakened assertions
- deleted tests
- mocks replacing the behavior under test
- swallowed errors
- migration/rollback gaps
- missing telemetry for silent failure modes
- changed defaults or branch protection side effects

## Stuck PR checklist

1. List open PRs.
2. For each, inspect mergeability, conflicts, checks, review state, and auto-merge state.
3. Classify:
   - **DIRTY**: rebase/resolve.
   - **BLOCKED**: identify missing required check or review gate.
   - **FAILURE**: fetch logs and fix first real error.
   - **PENDING**: determine running vs never-started.
   - **MERGEABLE but idle**: arm auto-merge if policy allows.
4. Act on one class at a time.
5. Re-check after each merge because the queue state changes.

## Never do these casually

- Hand-edit generated lockfiles with conflict markers.
- Add required checks before producer workflows are live.
- Force-push shared branches without lease.
- Merge red CI because “probably flaky” without evidence.
- Let parallel agents share one checkout.
