---
name: pr-iterate
description: Run a disciplined repo-agnostic pull-request iteration loop: create/use an isolated worktree, implement a scoped change, test it, commit, open or update a PR, monitor CI, fix failures, request or perform review, and prepare auto-merge when safe.
---

# PR Iterate

Use this for end-to-end PR work. Keep the loop tight: small change, real verification, clear handoff.

## Safety defaults

- Never overwrite uncommitted user work.
- Use a separate git worktree for parallel or delegated work.
- Prefer small PRs over broad mixed changes.
- Do not push, comment, request review, or enable auto-merge unless the user asked for external writes or repo workflow clearly expects it.
- Never mark done until tests/checks are verified or a blocker is named.

## Loop

1. **Orient**
   - `git status --short --branch`
   - identify base branch and remote
   - inspect issue/spec/PR context
   - choose branch name

2. **Isolate**
   - If another agent/person may touch the repo, create a worktree in a stable repo-adjacent or user-approved location; avoid temporary directories that may be cleaned or inaccessible:
     `git worktree add ../<repo>-WORKTREE-<slug> -b <branch> origin/<base>`
   - Otherwise use the current checkout only if clean or explicitly approved.

3. **Implement**
   - Make the smallest coherent change.
   - Keep generated/lockfile changes justified.
   - Update docs/tests only when relevant.

4. **Verify locally**
   - Run the narrowest meaningful test first.
   - Then run the repo’s standard lint/type/test gate if cheap enough.
   - Capture exact commands and outcomes.

5. **Commit**
   - Review diff before commit.
   - Commit message: concise imperative summary.
   - Do not mix unrelated cleanup.

6. **Open/update PR**
   - Include summary, tests, risk notes, and follow-ups.
   - Link issue if known.
   - If PR already exists, push update and comment only if useful.

7. **Watch CI**
   - Classify failures: test, lint, type, build, infra, flaky, merge conflict, missing required check.
   - Fix actionable failures in another small commit.
   - Re-run or wait only when there is evidence it is useful.

8. **Review / merge prep**
   - For non-trivial work, run independent review before merge.
   - Auto-merge only after checks are green and branch protection state is understood.
   - Verify merged state after arming auto-merge.

## PR body template

```markdown
## Summary
- 

## Tests
- [ ] `<command>`

## Risk / rollout
- 
```

## Handoffs

- CI failures, missing checks, pending/cancelled runs → use `github-ci-triage`.
- Auto-merge, branch protection, DIRTY PRs, lockfile conflicts, force-pushes → use `pr-discipline`.
- Model/delegation choices → use `model-routing`.

## CI failure triage

- **Failure**: fetch logs, find first real error, fix locally if reproducible.
- **Cancelled**: check whether superseded by newer run.
- **Pending too long**: check runner capacity and required-check naming.
- **DIRTY/conflict**: rebase/merge base branch, resolve, force-with-lease.
- **Flake**: verify history before rerun; do not label flaky from one data point.

## Stop and ask

Ask before:
- destructive cleanup
- force-pushing over unfamiliar history
- changing branch protection or required checks
- broad refactors beyond requested scope
- merging high-risk PRs without review

## Final report

Always include:
- branch / PR link or local branch name
- commits made
- tests run with result
- CI status if applicable
- blockers / follow-ups
