---
name: pr-discipline
description: Safety rules and tactical mechanics for opening, iterating on, reviewing, rebasing, auto-merging, or landing pull requests. Use before branch protection edits, required-check changes, auto-merge, lockfile conflict resolution, force-pushes, when PRs are stuck/dirty/blocked, or when running the open → push → watch CI → fix → merge loop. Triggers on "auto-merge", "lockfile", "force-push", "branch protection", "stuck PR", "DIRTY".
updated: 2026-07-15
wave: 3
---

# PR Discipline

Hard rules + tactical mechanics for shipping pull requests in high-velocity repositories. Prefer slow correct merges over fast broken `main`. This skill is repo-agnostic — repo-specific gates live in the repo's `CLAUDE.md` or its tracker SOP (`linear-sop`, `td-sop`).

This skill owns PR-shaped concerns end to end: the iteration loop, the safety rules, the recovery procedures. It does **not** own per-slice rigor (tracer bullets, refactor scan, TDD, Ralph review) — that's `slice-delivery`.

The branch-gated recovery procedures (CI triage, required-check changes, auto-merge, lockfile and content conflicts, repo-settings preflight, stuck-PR triage) live in [references/recovery.md](references/recovery.md) and are reached from the steps below when a specific failure appears.

## Safety

These apply on every invocation. They are the conservative baseline; a more permissive mode requires explicit user authorization for this lane. Each is stated once here — the recovery reference and iteration loop point back rather than restate.

- **Remote writes need consent.** Local commits are fine; push, comment, request review, or arm auto-merge only when the user asked for external writes or the repo workflow clearly expects it (e.g. the user said "open a PR for this").
- **Protect uncommitted work.** Before any operation that could clobber the working tree (`git checkout <file>`, `git reset --hard`, `git stash drop`), confirm the tree is clean or surface what would be lost.
- **Keep PRs small and single-concern.** Split a multi-concern change before opening. One concern per commit; refactor-then-feature is two commits.
- **Force-push only with `--force-with-lease`, and only on your own branch.** Stop and ask before force-pushing over shared or unfamiliar history.
- **Regenerate lockfiles through the package manager** (see recovery reference), rather than editing conflict markers by hand.
- **Fix pre-commit/pre-push hooks in place, never bypass them** — see *Pre-push hooks* below.
- **Give each parallel agent its own `git worktree`** — a shared checkout corrupts concurrent work. See the iteration loop's worktree rule.
- **Land a required check producer-first** — add the requirement only after its workflow is green on the protected branch (see recovery reference).
- **Merge on green CI with real evidence** — verify flake history before re-running a red check, and report "merged" only once the platform reports `MERGED` (see *Definition of "shipped"*).

**Stop and ask** before: destructive cleanup (`git reset --hard`, `gh repo delete`); force-pushing over unfamiliar history; changing branch protection, required checks, or repo visibility; refactors beyond the requested scope; or merging a high-risk PR without independent review.

## Definition of "shipped"

This is the canonical "shipped" definition for the whole skills repo; other skills that say "shipped" defer here.

A change is **shipped** when:

1. The PR is `MERGED` on the hosting platform (`gh pr view <n> --json state` returns `MERGED`).
2. CI on the merge commit on the target branch is green (`gh run list --branch <base> --commit <merge_sha>` shows success).

Local `HEAD` green is necessary but not sufficient. Report a change as shipped, complete, or done only once both conditions hold. Auto-merge being armed is not shipped — verify the platform reports `MERGED` within 15 minutes of the gate clearing, and chase if it doesn't.

## Pre-push hooks — never `--no-verify`

Pre-commit and pre-push hooks are part of the contract. Keep `--no-verify` (and platform equivalents) out of `git push`, `git commit`, and any wrapper script. If a hook is wrong or out of date, fix the hook in a **separate** commit with a one-line rationale, then re-attempt the original commit/push. Bypassing hooks "just this once" routinely lands the exact failure the hook was designed to catch. The only exception is when the user explicitly authorizes a one-shot bypass and the bypass is recorded in the PR body.

## The iteration loop

Orient → isolate → implement → verify → commit → open/update PR → watch CI → merge prep. The first five stages need no script; their non-default parts:

- Branch names carry the scope: `feat/<slice-id>-<slug>`, `fix/<slice-id>-<slug>`, `refactor/<area>-<slug>`.
- If another agent or person may touch the repo concurrently, take a worktree — one checkout per agent (see Safety):

  ```bash
  git worktree add ../<repo>-WORKTREE-<slug> -b <branch> origin/<base>
  ```

  Prefer a repo-adjacent or user-approved path over temporary directories that may be cleaned or made inaccessible.
- **One concern per commit**, per `slice-delivery` — a refactor surfaced mid-iteration lands as its own commit ahead of the next feature push. Conventional Commits unless the repo overrides; scope by slice ID or skill name; justify generated/lockfile changes in the commit body.
- Capture exact verification commands and outcomes for the PR body.

### Open or update PR

If opening:

```markdown
## Summary
- <one or two bullets>

## Tests
- [ ] `<command>` — result

## Risk / rollout
- <blast radius, rollback path, follow-ups>
```

If updating: push and comment only if useful (e.g. "addressed review finding X in <sha>"). A force-push needs no announcement comment.

### Watch CI

Classify failures per [CI failure triage](references/recovery.md#ci-failure-triage) and fix actionable ones in a fresh small commit.

### Review and merge prep

- For non-trivial PRs, dispatch the adversarial (Ralph) review per `slice-delivery`.
- Arm auto-merge only after checks are green and branch-protection state is understood ([auto-merge discipline](references/recovery.md#auto-merge-discipline)).
- Verify the `MERGED` state per the *Definition of "shipped"* above.

## Related skills

- `slice-delivery` — per-slice execution discipline (tracer bullets, refactor scan, Ralph review, DoD). `pr-discipline` is what `slice-delivery` delegates PR mechanics to; the adversarial review loop lives there.
- `linear-sop` / `td-sop` — tracker mechanics. They delegate PR mechanics here.
- `github-ci-triage` — deeper `gh` workflows for CI failures, missing checks, and pending/cancelled runs.
- `repo-hygiene` — post-merge worktree/branch cleanup.
- `model-routing` — model/delegation choices for parallel sub-agents.
