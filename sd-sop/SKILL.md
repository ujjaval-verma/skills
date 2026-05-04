---
name: sd-sop
description: Deterministic Linear-based SD-SOP workflow for clamshell-ai-style delivery lanes. Use when creating, splitting, updating, or closing Linear issues/sub-issues; opening, stacking, rebasing, reviewing, or merging PRs; running PR iteration; mapping Linear issue-to-PR work; enforcing velocity/rigor/hygiene gates; running SD-SOP audits; or handling work where Linear, GitHub PRs, CI, review, dependencies, worktrees, and merge state must stay synchronized. Triggers on “SD-SOP”, “Linear issue”, “sub-issue”, “one issue one PR”, “stacked PR”, “blocks/blocked by”, “In Progress”, “In Review”, “Done”, “pr-iterate”, “husky”, “E2E”, “worktree”, “audit”, and stuck green/open PRs.
---

# SD-SOP — Linear execution

Use SD-SOP for Linear-driven delivery.

SD-SOP optimizes three pillars: **velocity**, **rigor**, and **hygiene**. When a gate fails, repair state before continuing or surface the exact blocker.

## Mental model

- **Parent Linear issue = lane/objective.** It names the product/workstream goal.
- **Child Linear sub-issue = independently mergeable implementation slice.** If it cannot own a PR, keep it as parent acceptance criteria instead.
- **One implementation sub-issue → one branch/worktree → one PR → one verified merge.**
- **Status follows evidence, never intent.**

## Pillar 1 — Velocity: small, verifiable chunks

- Split work into PR-sized Linear children. Prefer several small reversible PRs over one broad PR.
- Every implementation PR closes exactly one child issue. Parent issues may appear only as context.
- Model dependencies before implementation:
  - record Linear `blocks` / `blocked-by` for issue dependencies;
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
- Use E2E/UX evidence when behavior is user-visible. Prefer screenshot, local smoke, authorized DB/log evidence, or manual smoke artifacts.
- Attach useful screenshot/evidence artifacts to Linear for UX bugs.
- Treat review/meta-review feedback as part of the work. Fix actionable feedback on the PR branch; defer only if clearly out-of-scope and tracked.

## Pillar 3 — Hygiene: keep the lane clean

- Use at most **4 active worktrees per repo** unless the owner explicitly approves a larger sprint.
- Never run parallel agents in the same checkout. Each parallel implementation gets a dedicated worktree under the repo parent.
- After verified merge: delete/confirm remote branch deletion, remove local worktree, delete local branch, fetch/prune, and reconcile Linear.
- Before context-switching or starting a new lane, audit for green open PRs, dirty stacked PRs, active Linear children without PRs, and worktree count >4.

## Start-lane gate

1. Verify ownership/assignee before touching existing work.
2. Fetch live Linear parent/children and GitHub PRs.
3. Convert vague child issues into PR-sized slices, or collapse non-PR-worthy children into parent acceptance criteria.
4. Record dependency graph in Linear.
5. Allocate worktrees intentionally; do not exceed 4 active WTs per repo.
6. Maintain a lane ledger: `issue → repo → branch/worktree → PR → status → merge commit`.

## Per-PR gate

Before opening a PR:

- Confirm the exact Linear child issue closed by the PR.
- Confirm no other implementation child is bundled.
- Run the smallest meaningful local checks plus mandatory hooks.
- Include issue link, scope, gates run, and dependency/stack note in the PR body.
- Move Linear to `In Review` only after the PR exists and is linked.

## PR-iteration gate

1. Push PR.
2. Watch CI + automated review.
3. Fix failing checks and actionable feedback on the branch.
4. Repeat until local evidence + CI + review imply LGTM.
5. Merge directly or arm auto-merge unless a true blocker remains.
6. Verify the hosting platform reports `MERGED` and capture merge time/commit when available.
7. Move child issue to `Done` only after merge verification.
8. Clean branch/worktree immediately.

## Stacked PR repair gate

When a base PR merges and a stacked PR remains:

1. Fetch latest base branch.
2. Rebase the stacked branch onto the base.
3. Resolve conflicts explicitly; regenerate lockfiles instead of hand-merging.
4. Force-push with lease.
5. Re-run/watch checks.
6. Merge once green and clean.
7. Clean branch/worktree and update Linear dependency/status state.

## Drift audit

Run the bundled audit script before/after large lane changes, before context switches, and whenever drift is suspected. The script is read-only. It checks open PR health, Linear issue→PR mapping, stacked PR dependency evidence, active child issues without PRs, worktree count, and gone local branches. Use `--json` for machine-readable output and `--fail-on-findings` for CI-style gating.

Repair drift in this order:
1. green/mergeable PRs with no merge/auto-merge action;
2. dirty/conflicting stacked PRs;
3. active Linear children without PRs;
4. stale Linear status;
5. branch/worktree cleanup.

## Related skills

- Use `td-sop` for Markdown+GitHub tracker repos.
- Use a PR-discipline skill for merge/rebase/branch-protection/lockfile conflict mechanics.
- Use a model-routing skill before spawning review or implementation sub-agents.
- Use live GitHub/Linear state; do not rely on memory for mutable status.
