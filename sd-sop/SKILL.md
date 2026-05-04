---
name: sd-sop
description: Deterministic software-delivery SOP workflow for keeping issue trackers, pull requests, CI/review, dependencies, and merge state synchronized. Use when creating, splitting, updating, or closing issues/sub-issues; opening, stacking, rebasing, reviewing, or merging PRs; mapping issue-to-PR work; running PR iteration; handling one-issue-one-PR discipline; recording blocks/blocked-by relations; or fixing stuck green/open PRs.
---

# SD-SOP

Follow this as a delivery gate, not optional guidance. If a step fails, stop the lane, repair bookkeeping/state, or surface the exact blocker.

## Core invariants

1. **One implementation issue → one PR → one merge.** If a change is not worth its own PR, keep it as acceptance criteria/checklist text inside a parent issue; do not create a tracker sub-issue for it.
2. **Parent issues track lanes, not code delivery.** Parent/epic issues may be referenced in PR bodies for context, but child implementation issues carry the PR/merge evidence.
3. **Status follows evidence.** Move issue status only after the matching artifact exists:
   - `In Progress`: branch/worktree exists or active implementation has begun.
   - `In Review`: PR exists and links the issue.
   - `Done`: PR is verified `MERGED`, or the issue is explicitly non-code and its artifact is complete.
4. **No invisible dependencies.** If a PR or issue depends on another, record tracker `blocks` / `blocked-by` relations before opening dependent work.
5. **Stacked PRs are exception-only.** Prefer merging the base PR first. A stacked PR is allowed only with explicit tracker relations, PR body stack notes, and an active plan to rebase/merge immediately after the base lands.
6. **Green owned PRs do not sit idle.** Once CI + review imply LGTM and no product/security blocker remains, merge or arm auto-merge, then verify `MERGED` within 15 minutes.

## Before creating issues

- Verify ownership/assignee before taking over existing work.
- Decide whether each proposed child is independently PR-worthy.
  - PR-worthy → create a child implementation issue.
  - Not independently PR-worthy → keep as acceptance criteria in the parent or a sibling issue.
- For product/security behavior with multiple acceptable choices, create a team-evaluation issue instead of a PR; state that the larger team should evaluate first.
- Use concise Markdown descriptions with actual newlines. Never write literal `\\n` sequences.

## Before opening a PR

- Confirm exactly which implementation issue the PR closes.
- Use a dedicated branch/worktree when parallel work exists.
- Link the issue in the PR body and include local gates run.
- If the PR references multiple implementation issues, stop and either:
  1. split the PR, or
  2. collapse the extra tracker children into acceptance criteria before continuing.
- If the PR is stacked, record `blocked-by` / `blocks` in the tracker and put the stack plan in the PR body.

## PR iteration loop

1. Run the smallest meaningful local gates before push.
2. Push and watch CI + automated review.
3. Address actionable CI/review/meta-review feedback on the PR branch.
4. Repeat until CI + review imply LGTM.
5. Merge without asking for human approval unless blocked by a real product/security/access decision.
6. Verify the hosting platform reports `MERGED` and capture merge time/commit when available.
7. Move the implementation issue to `Done` only after merge verification.

## Dependency and stack repair

When a base PR merges and a stacked PR remains:

1. Fetch latest base branch.
2. Rebase stacked branch onto the base.
3. Resolve conflicts explicitly; regenerate lockfiles instead of hand-merging them.
4. Force-push with lease.
5. Re-run/watch checks.
6. Merge once green and clean.
7. Remove stale branch/worktree if safe.

## Lane audit checklist

Use this whenever SOP drift is suspected:

- List parent + child issues and statuses.
- List open owned PRs in the relevant repo(s).
- For each child issue, record: `issue → repo → branch → PR → status → merge commit`.
- Flag:
  - child issue `In Progress`/`In Review` with no PR,
  - PR covering multiple implementation child issues,
  - stacked PR with no dependency relation,
  - green/mergeable PR with no merge/auto-merge action,
  - issue `Done` with no verified merge/artifact.
- Repair the highest-risk mismatch first: stuck green PRs, dirty stacked PRs, then stale tracker status.

## Interaction with related skills

- Use a PR-discipline skill for merge/rebase/branch-protection/lockfile conflict mechanics.
- Use a model-routing skill before spawning review or implementation sub-agents.
- Use live tracker/GitHub state; do not rely on memory for mutable status.
