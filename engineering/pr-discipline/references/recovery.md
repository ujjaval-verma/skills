# PR recovery reference

Disclosed reference for [`pr-discipline`](../SKILL.md). Branch-gated procedures reached from the iteration loop and Safety section only when a specific failure appears — not loaded with the skill body.

## CI failure triage

When CI is red or stuck, classify before reacting:

| Class | Signal | Action |
|---|---|---|
| **FAILURE** | Check completed with non-success conclusion. | Fetch logs (`gh run view <run-id> --log-failed`), find the first real error, reproduce locally, fix in a new commit. |
| **CANCELLED** | Check was cancelled. | Determine whether superseded by a newer run. If yes, ignore. If no, investigate why. |
| **PENDING (excessive)** | Check pending for far longer than its usual duration. | Check runner capacity, required-check naming, missing producer workflow. |
| **DIRTY / CONFLICT** | `mergeStateStatus: DIRTY` or merge conflict markers. | Rebase or merge the base branch, resolve, force-push with lease. See *Lockfile conflicts* or *Real content conflicts* below depending on file type. |
| **MISSING REQUIRED** | A required check is not running because the producer workflow doesn't exist or wasn't triggered. | Per *Required-check changes* below — fix the producer, do not weaken the requirement. |
| **FLAKE** | Failure with strong evidence (history, known issue) of non-determinism. | Re-run only after verifying flake history. Never label a single red as flaky. Address the flake itself in a separate PR. |

`gh pr checks <n>` and `gh run list --branch <branch> --limit 10` are the two highest-value triage commands. For deeper `gh` log workflows, see `github-ci-triage`.

## Required-check changes

Add a required status check only after the workflow that emits it is already on the protected branch and has reported green at least once.

Correct sequence:

1. Merge the workflow/check producer without making it required.
2. Wait for a protected-branch run.
3. Confirm the exact check name.
4. Patch branch protection.
5. Verify a fresh PR sees the required check.

Invert this and every PR can become blocked waiting for a check that cannot exist yet.

## Auto-merge discipline

After enabling auto-merge, verify the PR actually lands within 15 minutes of the merge gate clearing. Check for:

- `DIRTY` / conflicts after another PR merged.
- Required checks pending forever.
- Failed checks that are required indirectly.
- Branch protection mismatch.
- Merge queue state.

Report "merged" only once the hosting platform says merged — see the *Definition of "shipped"* in the skill body for the exact verification.

## Lockfile conflicts

Regenerate lockfiles through the repo's package manager; do not hand-merge conflict markers. First inspect repo docs, package-manager choice, and CI expectations so you do not rewrite a lockfile with the wrong tool or version.

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

Use the repo's package manager and lockfile policy. If unsure, inspect existing CI/docs before choosing npm/pnpm/yarn/bun/cargo/go/etc.

## Real content conflicts

- Read both sides before resolving.
- Keep additive changes from both branches when compatible.
- Treat contradictory logic as a design conflict, not a mechanical merge.
- Run affected tests after resolution.
- Use `--force-with-lease`, never blind `--force`.

## Repo-settings preflight

Before editing branch protection, default branch, merge methods, repo visibility, or any other persistent repo setting:

1. **Dump current settings** — `gh api repos/$OWNER/$REPO --jq '.visibility,.default_branch,.allow_squash_merge,.allow_rebase_merge,.allow_merge_commit'` and `gh api repos/$OWNER/$REPO/branches/$BASE/protection` (when protection exists).
2. **Record required contexts before/after** for branch protection changes.
3. **Confirm admin bypass expectations**.
4. **Change one policy dimension per operation** so each is reversible.
5. **Keep visibility private unless the user explicitly confirms public.** Some workflows appear to require public (GitHub features like Pages on free tier); if you see that prompt, stop and ask.

Weaken a setting to land a PR only when the user explicitly approves and understands the risk.

## Stuck PR checklist

1. List open PRs (`gh pr list --author @me --state open --json number,title,mergeStateStatus,statusCheckRollup`).
2. For each, inspect mergeability, conflicts, checks, review state, and auto-merge state.
3. Classify:
   - **DIRTY** → rebase/resolve.
   - **BLOCKED** → identify missing required check or review gate.
   - **FAILURE** → fetch logs and fix first real error (see *CI failure triage*).
   - **PENDING** → determine running vs never-started.
   - **MERGEABLE but idle** → arm auto-merge if policy allows; verify per *Definition of "shipped"*.
4. Act on one class at a time.
5. Re-check after each merge because the queue state changes.
