---
name: sd-sop
description: Deterministic software-delivery SOP workflow for keeping issue trackers, pull requests, CI/review, dependencies, worktrees, and merge state synchronized across velocity, rigor, and hygiene pillars. Use when creating, splitting, updating, or closing issues/sub-issues; opening, stacking, rebasing, reviewing, or merging PRs; mapping issue-to-PR work; enforcing one-issue-one-PR discipline; recording blocks/blocked-by relations; running PR iteration; checking mandatory hooks/tests/E2E evidence; limiting/pruning worktrees; or fixing stuck green/open PRs.
---

# SD-SOP

Use this as a delivery gate, not optional guidance. SD-SOP optimizes three pillars: **velocity**, **rigor**, and **hygiene**. If a gate fails, repair bookkeeping/state before continuing or surface the exact blocker.

## Pillar 1 — Velocity: small, verifiable chunks

- Parent tracker issue = lane/objective. Child/sub-issue = independently mergeable implementation slice.
- **One implementation sub-issue → one branch/worktree → one PR → one merge.** If a change is not worth its own PR, keep it as acceptance criteria, not a sub-issue.
- Every PR closes exactly one implementation sub-issue. Parent/epic issues may appear only as context.
- Model dependencies explicitly before work starts. If issue/PR B needs A, add `blocked-by` / `blocks` before opening B.
- Prefer sequential merge over stacking. Stacked PRs are exception-only and require explicit dependency relations plus a written stack plan in the PR body.
- Green owned PRs do not sit idle. Once local gates + CI + review/meta-review imply LGTM, merge or arm auto-merge and verify `MERGED` within 15 minutes.

## Pillar 2 — Rigor: prove the change

- Run mandatory repo hooks/checks. Do not bypass Husky/pre-push hooks unless there is an explicit, documented reason.
- Practice TDD where practical:
  - bugfix: add/confirm failing regression coverage first;
  - refactor: pin current behavior before moving code;
  - feature: add focused tests for the new contract.
- Use E2E/UX evidence where applicable: screenshots, local smoke notes, database/log evidence when authorized, or manual smoke artifacts.
- Attach useful screenshots/evidence to tracker issues for UX bugs; keep issue text concise.
- Run PR iteration: implement → local gates → PR → CI/review/meta-review → fix feedback → repeat → merge.
- Address actionable review feedback on the PR branch. Defer only when clearly non-blocking/out-of-scope and tracked.
- Stop for real product/security/access/team-evaluation ambiguity; do not guess through ambiguous product behavior.

## Pillar 3 — Hygiene: keep the lane clean

- Use at most **4 active worktrees per repo** unless the owner explicitly approves a larger sprint.
  1. foundation/base lane
  2. implementation lane A
  3. implementation lane B
  4. QA/E2E/rebase lane
- Never run parallel agents in the same checkout. Each parallel implementation gets its own worktree under the repo parent.
- After every verified merge: delete/confirm remote branch deletion, remove the local worktree, delete the local branch, fetch/prune, and reconcile tracker status.
- Before starting a new lane or context-switching, audit for open green PRs, dirty stacked PRs, tracker `In Review` with no PR, and worktree count >4.
- Do not let local branches/worktrees accumulate as hidden state.

## Start-lane gate

1. Verify ownership/assignee before touching existing work.
2. Fetch live parent + child issues and current PRs.
3. Split children only into PR-worthy slices; otherwise keep items as parent acceptance criteria.
4. Record dependency graph in the tracker.
5. Allocate up to 4 worktrees and name branches after the owning child issue.
6. Create/update a lane ledger: `issue → repo → branch/worktree → PR → status → merge commit`.

## Per-PR gate

Before opening a PR:

- Confirm the exact child issue closed by the PR.
- Confirm the PR does not bundle multiple implementation children.
- Run the smallest meaningful local checks plus mandatory hooks.
- Include in the PR body: issue link, scope, gates run, and stack/dependency note if any.
- Move tracker status to review only after the PR exists and is linked.

## PR iteration and merge gate

1. Watch CI + automated review after push.
2. Fix failures or actionable review feedback on the branch.
3. Repeat until checks and review imply LGTM.
4. Merge directly or arm auto-merge unless a real blocker remains.
5. Verify the hosting platform reports `MERGED` and capture merge time/commit when available.
6. Move the child issue to done only after merge verification.
7. Clean branch/worktree immediately.

## Stacked PR repair gate

When a base PR merges and a stacked PR remains:

1. Fetch latest base branch.
2. Rebase the stacked branch onto the base.
3. Resolve conflicts explicitly; regenerate lockfiles instead of hand-merging them.
4. Force-push with lease.
5. Re-run/watch checks.
6. Merge once green and clean.
7. Clean branch/worktree and update dependency/status state.

## Drift audit checklist

Run this whenever SOP drift is suspected:

- List parent + child issues and statuses.
- List open owned PRs in relevant repos.
- List active repo worktrees and local branches.
- For each child issue, record `issue → repo → branch/worktree → PR → status → merge commit`.
- Flag:
  - child issue in progress/review with no branch/PR;
  - PR covering multiple implementation child issues;
  - stacked PR with no dependency relation;
  - green/mergeable PR with no merge/auto-merge action;
  - issue done with no verified merge/artifact;
  - repo with >4 active worktrees;
  - merged PR branch/worktree still present locally.
- Repair in risk order: green stuck PRs, dirty stacked PRs, stale tracker status, then branch/worktree cleanup.

## Related skills

- Use a PR-discipline skill for merge/rebase/branch-protection/lockfile conflict mechanics.
- Use a model-routing skill before spawning review or implementation sub-agents.
- Use live tracker/GitHub state; do not rely on memory for mutable status.
