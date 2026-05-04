---
name: sd-sop
description: Deterministic software-delivery SOP workflow for keeping issue trackers, pull requests, CI/review, dependencies, worktrees, and merge state synchronized across velocity, rigor, and hygiene pillars. Use when creating, splitting, updating, or closing issues/sub-issues; opening, stacking, rebasing, reviewing, or merging PRs; mapping issue-to-PR work; enforcing one-issue-one-PR discipline; recording blocks/blocked-by relations; running PR iteration; checking mandatory hooks/tests/E2E evidence; limiting/pruning worktrees; running SD-SOP audits; or fixing stuck green/open PRs.
---

# SD-SOP

Use SD-SOP as a hard delivery gate. Optimize three pillars: **velocity**, **rigor**, and **hygiene**. When a gate fails, repair state before continuing or surface the exact blocker.

## Mental model

- **Parent tracker issue = lane/objective.** It names the product/workstream goal.
- **Child/sub-issue = independently mergeable implementation slice.** If it cannot own a PR, keep it as parent acceptance criteria instead.
- **One implementation sub-issue → one branch/worktree → one PR → one verified merge.**
- **Status follows evidence, never intent.**

## Pillar 1 — Velocity: small, verifiable chunks

- Split work into PR-sized tracker children. Prefer several small reversible PRs over one broad PR.
- Every implementation PR closes exactly one child issue. Parent/epic issues may appear only as context.
- Model dependencies before implementation:
  - record `blocks` / `blocked-by` for issue dependencies;
  - mention stack/dependency state in PR bodies;
  - do not open dependent PRs early unless the stack is explicit and actively driven.
- Green owned PRs do not sit idle. Once local gates + CI + review/meta-review imply LGTM, merge or arm auto-merge and verify `MERGED` within 15 minutes.
- Stop only for real product/security/access/team-evaluation blockers. Otherwise continue PR iteration through merge.

## Pillar 2 — Rigor: prove the change

- Run mandatory repo hooks/checks. Do not bypass Husky/pre-push hooks unless the reason is explicit and documented in the PR.
- Practice TDD where practical:
  - bugfix: add/confirm failing regression coverage first;
  - refactor: pin existing behavior before moving code;
  - feature: add focused contract tests.
- Use E2E/UX evidence when behavior is user-visible: screenshot, local smoke, authorized database/log evidence, or manual smoke artifacts.
- Attach useful screenshot/evidence artifacts to tracker issues for UX bugs.
- Treat review/meta-review feedback as part of the work. Fix actionable feedback on the PR branch; defer only if clearly out-of-scope and tracked.

## Pillar 3 — Hygiene: keep the lane clean

- Use at most **4 active worktrees per repo** unless the owner explicitly approves a larger sprint:
  1. foundation/base lane
  2. implementation lane A
  3. implementation lane B
  4. QA/E2E/rebase lane
- Never run parallel agents in the same checkout. Each parallel implementation gets a dedicated worktree under the repo parent.
- After verified merge: delete/confirm remote branch deletion, remove local worktree, delete local branch, fetch/prune, and reconcile tracker state.
- Before context-switching or starting a new lane, audit for green open PRs, dirty stacked PRs, active child issues without PRs, and worktree count >4.

## Start-lane gate

1. Verify ownership/assignee before touching existing work.
2. Fetch live parent/children issues and GitHub PRs.
3. Convert vague child issues into PR-sized slices, or collapse non-PR-worthy children into parent acceptance criteria.
4. Record dependency graph in the tracker.
5. Allocate worktrees intentionally; do not exceed 4 active WTs per repo.
6. Maintain a lane ledger: `issue → repo → branch/worktree → PR → status → merge commit`.

## Per-PR gate

Before opening a PR:

- Confirm the exact child issue closed by the PR.
- Confirm no other implementation child is bundled.
- Run the smallest meaningful local checks plus mandatory hooks.
- Include issue link, scope, gates run, and dependency/stack note in the PR body.
- Move tracker status to review only after the PR exists and is linked.

## PR-iteration gate

1. Push PR.
2. Watch CI + automated review.
3. Fix failing checks and actionable feedback on the branch.
4. Repeat until local evidence + CI + review imply LGTM.
5. Merge directly or arm auto-merge unless a true blocker remains.
6. Verify the hosting platform reports `MERGED` and capture merge time/commit when available.
7. Move child issue to done only after merge verification.
8. Clean branch/worktree immediately.

## Stacked PR repair gate

When a base PR merges and a stacked PR remains:

1. Fetch latest base branch.
2. Rebase the stacked branch onto the base.
3. Resolve conflicts explicitly; regenerate lockfiles instead of hand-merging.
4. Force-push with lease.
5. Re-run/watch checks.
6. Merge once green and clean.
7. Clean branch/worktree and update dependency/status state.

## Drift audit

Run the bundled audit script before/after large lane changes, before context switches, and whenever drift is suspected:

```bash
python3 path/to/sd-sop/scripts/sd_sop_audit.py \
  --repo /path/to/repo \
  --github-repo owner/name \
  --linear-parent TEAM-1234 \
  --author @me
```

The script is read-only. It checks open PR health, issue→PR mapping, stacked PR dependency evidence, active child issues without PRs, worktree count, and gone local branches. Use `--json` for machine-readable output and `--fail-on-findings` for CI-style gating.

Repair drift in this order:
1. green/mergeable PRs with no merge/auto-merge action;
2. dirty/conflicting stacked PRs;
3. active tracker children without PRs;
4. stale tracker status;
5. branch/worktree cleanup.

## Related skills

- Use a PR-discipline skill for merge/rebase/branch-protection/lockfile conflict mechanics.
- Use a model-routing skill before spawning review or implementation sub-agents.
- Use live GitHub/tracker state; do not rely on memory for mutable status.
