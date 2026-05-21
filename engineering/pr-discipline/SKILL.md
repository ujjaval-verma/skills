---
name: pr-discipline
description: Safety rules and tactical mechanics for opening, iterating on, reviewing, rebasing, auto-merging, or landing pull requests. Use before branch protection edits, required-check changes, auto-merge, lockfile conflict resolution, force-pushes, merge queue nudges, when PRs are stuck/dirty/blocked, or when running the open → push → watch CI → fix → merge loop on a feature branch. Triggers on "PR", "pull request", "auto-merge", "lockfile", "force-push", "branch protection", "CI failure", "stuck PR", "DIRTY".
updated: 2026-05-21
wave: 3
---

# PR Discipline

Hard rules + tactical mechanics for shipping pull requests in high-velocity repositories. Prefer slow correct merges over fast broken `main`. This skill is repo-agnostic — repo-specific gates live in the repo's `CLAUDE.md` or its tracker SOP (`linear-sop`, `td-sop`).

This skill owns PR-shaped concerns end to end: the iteration loop, the safety rules, the recovery procedures. It does **not** own per-slice rigor (tracer bullets, refactor scan, TDD, Ralph review) — that's `slice-delivery`.

## Definition of "shipped"

A change is **shipped** when:

1. The PR is `MERGED` on the hosting platform (`gh pr view <n> --json state` returns `MERGED`).
2. CI on the merge commit on the target branch is green (`gh run list --branch <base> --commit <merge_sha>` shows success).

Local `HEAD` green is necessary but not sufficient. Do not report a change as shipped, complete, or done before both conditions hold. Auto-merge being armed is not shipped — verify the platform reports `MERGED` within 15 minutes of the gate clearing, and chase if it doesn't.

## Pre-push hooks — never `--no-verify`

Pre-commit and pre-push hooks are part of the contract. Do not pass `--no-verify` (or platform equivalents). If a hook is wrong or out of date, fix the hook in a **separate** commit with a one-line rationale, then re-attempt the original commit/push. Bypassing hooks "just this once" routinely lands the exact failure the hook was designed to catch.

This applies to `git push`, `git commit`, and any wrapper script. The only exception is when the user explicitly authorizes a one-shot bypass and the bypass is recorded in the PR body.

## Commits

One concern per commit. Refactor commits are separate from feature commits. The `slice-delivery` rule "refactor-then-feature is two commits" applies at PR-time too: when CI surfaces a refactor opportunity mid-iteration, land it as its own commit, not folded into the next push.

Conventional Commits unless the repo overrides — `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`. Scope by slice ID or skill name where useful.

## The iteration loop

Use this for end-to-end PR work. Keep the loop tight: small change, real verification, clear handoff.

### 1. Orient

- `git status --short --branch` — confirm clean tree before starting.
- Identify base branch and remote (`git rev-parse --abbrev-ref --symbolic-full-name @{u}`).
- Read the issue / spec / PR context the change implements.
- Choose a branch name that reflects the scope (`feat/<slice-id>-<slug>`, `fix/<slice-id>-<slug>`, `refactor/<area>-<slug>`).

### 2. Isolate

If another agent or person may touch the repo concurrently, create a worktree:

```bash
git worktree add ../<repo>-WORKTREE-<slug> -b <branch> origin/<base>
```

Otherwise use the current checkout only if it's clean or explicitly approved. Never share a checkout between parallel agents. Avoid temporary directories that may be cleaned or made inaccessible — prefer a repo-adjacent or user-approved path.

### 3. Implement

- Make the smallest coherent change that moves the PR's stated scope forward.
- Justify generated/lockfile changes in the commit body.
- Update docs/tests only when relevant to the change.

### 4. Verify locally

- Run the narrowest meaningful test first.
- Then the repo's standard lint/type/test gate (commonly `make verify`, `npm test`, `cargo test`, etc.) if cheap enough.
- Capture exact commands and outcomes for the PR body.

### 5. Commit

- Review diff before committing (`git diff --staged`).
- Conventional summary; body explains *why* if non-obvious.
- Do not mix unrelated cleanup. Refactor surfaced mid-iteration → its own commit.

### 6. Open or update PR

If opening:

```markdown
## Summary
- <one or two bullets>

## Tests
- [ ] `<command>` — result

## Risk / rollout
- <blast radius, rollback path, follow-ups>
```

If updating: push and comment only if useful (e.g., "addressed review finding X in <sha>"). Don't comment to announce a force-push.

### 7. Watch CI

Classify failures (see CI failure triage below) and fix actionable ones in a fresh small commit.

### 8. Review and merge prep

- For non-trivial PRs, dispatch the adversarial (Ralph) review per `slice-delivery`.
- Arm auto-merge only after checks are green and branch-protection state is understood (see Auto-merge discipline below).
- Verify the `MERGED` state per the "shipped" definition above.

## CI failure triage

When CI is red or stuck, classify before reacting:

| Class | Signal | Action |
|---|---|---|
| **FAILURE** | Check completed with non-success conclusion. | Fetch logs (`gh run view <run-id> --log-failed`), find the first real error, reproduce locally, fix in a new commit. |
| **CANCELLED** | Check was cancelled. | Determine whether superseded by a newer run. If yes, ignore. If no, investigate why. |
| **PENDING (excessive)** | Check pending for far longer than its usual duration. | Check runner capacity, required-check naming, missing producer workflow. |
| **DIRTY / CONFLICT** | `mergeStateStatus: DIRTY` or merge conflict markers. | Rebase or merge the base branch, resolve, force-push with lease. See "Lockfile conflicts" or "Real content conflicts" below depending on file type. |
| **MISSING REQUIRED** | A required check is not running because the producer workflow doesn't exist or wasn't triggered. | Per "Required-check changes" below — fix the producer, do not weaken the requirement. |
| **FLAKE** | Failure with strong evidence (history, known issue) of non-determinism. | Re-run only after verifying flake history. Never label a single red as flaky. Address the flake itself in a separate PR. |

`gh pr checks <n>` and `gh run list --branch <branch> --limit 10` are the two highest-value triage commands.

## Required-check changes

Never add a required status check before the workflow that emits it is already on the protected branch and has reported green at least once.

Correct sequence:

1. Merge the workflow/check producer without making it required.
2. Wait for a protected-branch run.
3. Confirm the exact check name.
4. Patch branch protection.
5. Verify a fresh PR sees the required check.

If you invert this, every PR can become blocked waiting for a check that cannot exist yet.

## Auto-merge discipline

After enabling auto-merge, verify the PR actually lands within 15 minutes of the merge gate clearing. Check for:

- `DIRTY` / conflicts after another PR merged.
- Required checks pending forever.
- Failed checks that are required indirectly.
- Branch protection mismatch.
- Merge queue state.

Do not report "merged" until the hosting platform says merged. See the "Definition of shipped" above for the exact verification.

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
4. **Never change multiple policy dimensions in one operation.** One setting per change so each is reversible.
5. **Never flip visibility from private → public** without explicit user confirmation. Some workflows appear to require it (GitHub features like Pages on free tier); if you see that prompt, stop and ask.

Do not weaken any setting just to land a PR unless the user explicitly approves and understands the risk.

## Parallel agents

If multiple agents will touch one repo, each must use a separate `git worktree`. See the iteration loop's "Isolate" step. Never share a checkout.

## Review discipline

Non-trivial PRs need independent adversarial review (the Ralph loop in `slice-delivery`). Watch especially for:

- weakened assertions
- deleted tests
- mocks replacing the behavior under test
- swallowed errors
- migration/rollback gaps
- missing telemetry for silent failure modes
- changed defaults or branch protection side effects

## Stuck PR checklist

1. List open PRs (`gh pr list --author @me --state open --json number,title,mergeStateStatus,statusCheckRollup`).
2. For each, inspect mergeability, conflicts, checks, review state, and auto-merge state.
3. Classify:
   - **DIRTY** → rebase/resolve.
   - **BLOCKED** → identify missing required check or review gate.
   - **FAILURE** → fetch logs and fix first real error (see CI failure triage).
   - **PENDING** → determine running vs never-started.
   - **MERGEABLE but idle** → arm auto-merge if policy allows; verify per "Definition of shipped".
4. Act on one class at a time.
5. Re-check after each merge because the queue state changes.

## Stop and ask

Before:

- destructive cleanup (`git reset --hard`, `git push --force` without lease, `gh repo delete`);
- force-pushing over unfamiliar history;
- changing branch protection, required checks, or repo visibility;
- broad refactors beyond requested scope;
- merging high-risk PRs without independent review.

## Never do these casually

- Hand-edit generated lockfiles with conflict markers.
- Add required checks before producer workflows are live.
- Force-push shared branches without `--force-with-lease`.
- Merge red CI because "probably flaky" without evidence.
- Let parallel agents share one checkout.
- `--no-verify` to bypass hooks. Fix the hook in a separate commit instead.
- Mix refactor and feature in one commit.
- Report "merged" before the platform reports `MERGED` and CI is green on the merge commit.

## Final report (when handing off)

Always include:

- branch / PR link or local branch name;
- commits made;
- tests run with result;
- CI status if applicable;
- blockers / follow-ups.

## Handoffs

- CI failures, missing checks, pending/cancelled runs → also see `github-ci-triage` for `gh` triage commands.
- Worktree/branch cleanup after merge → `repo-hygiene`.
- Model/delegation choices for parallel sub-agents → `model-routing`.
- Adversarial review loop → `slice-delivery`.

## Related skills

- `slice-delivery` — per-slice execution discipline (tracer bullets, refactor scan, Ralph review, DoD). `pr-discipline` is what `slice-delivery` delegates PR mechanics to.
- `linear-sop` / `td-sop` — tracker mechanics. They delegate PR mechanics here.
- `github-ci-triage` — deeper `gh` workflows for CI triage.
- `repo-hygiene` — post-merge worktree/branch cleanup.
