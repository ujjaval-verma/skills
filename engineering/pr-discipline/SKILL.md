---
name: pr-discipline
description: Safety rules and mechanics for opening, iterating on, rebasing, auto-merging, or landing pull requests, and for triaging red CI on a PR, on main, or on any branch. Use before branch protection edits, required-check changes, auto-merge, lockfile conflict resolution, force-pushes, when PRs are stuck/dirty/blocked, or when CI is failing. Triggers on "auto-merge", "lockfile", "force-push", "branch protection", "stuck PR", "DIRTY", "CI is red on main", "why is this check failing", "is this flaky".
updated: 2026-10-04
---

# PR Discipline

Prefer slow correct merges over fast broken `main`. Repo-agnostic; repo-specific gates live in the repo's `CLAUDE.md`. Per-slice rigor belongs to `slice-delivery`. Procedures for CI failures (on a PR, `main`, or any branch), required-check changes, auto-merge, lockfile regeneration, content conflicts, repo-settings edits, and stuck/DIRTY PRs live in [references/recovery.md](references/recovery.md); read it when one of them appears.

## Definition of "shipped"

Other skills defer to this definition. A change is **shipped** when both hold:

1. The PR is `MERGED` (`gh pr view <n> --json state`).
2. CI on the merge commit on the target branch is green (`gh run list --branch <base> --commit <merge_sha>`).

Local `HEAD` green is not sufficient; don't report a change as shipped, merged, or done until both hold. Armed auto-merge is not shipped: confirm `MERGED` within ~15 minutes of the gate clearing, and chase if it hasn't landed.

## Safety

- **Never weaken a test or protection to get green.** No loosened assertions, skipped tests, or relaxed protection; fix the first real cause with the smallest change that preserves the test's intent.
- **Fix a broken pre-commit/pre-push hook in a separate commit** with a one-line rationale, then retry; don't bypass it. A bypass needs explicit user authorization and a note in the PR body.
- **Required checks go producer-first.** Never make a check required before its producing workflow is on the base branch and has run green.
- **Check flake history before re-running a red check.** A single red is not a flake.
- **Stop and ask** before changing branch protection, required checks, or repo visibility, before force-pushing a branch someone else has pushed to, and before merging a high-risk PR without independent review.

## Branch and PR conventions

- Branch names carry the scope: `feat/<slice-id>-<slug>`, `fix/<slice-id>-<slug>`, `refactor/<area>-<slug>`.
- Concurrent agents or people on one repo each get their own `git worktree`, at a repo-adjacent or user-approved path rather than a temp directory.
- Justify generated or lockfile changes in the commit body.
- Non-trivial PRs get the adversarial (Ralph) review per `slice-delivery`.
- Arm auto-merge only after checks are green and branch-protection state is understood.

## Related skills

- `slice-delivery` delegates PR mechanics here.
- `repo-hygiene` handles post-merge worktree and branch cleanup.
