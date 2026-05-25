---
name: linear-sop
description: Linear tracker / org-level workflow for Linear-tracked repos. Use when creating, splitting, updating, or closing Linear issues/sub-issues; mapping Linear issue-to-PR work; recording blocks/blocked-by relations; transitioning Linear status (Backlog → In Progress → In Review → Done); running the Linear drift audit; or deciding how a Linear-tracked repo differs from a Markdown-tracker (td-sop) repo. **For per-slice execution discipline (tracer bullets, refactor scan, TDD scope, Ralph review, slice lifecycle), use the `slice-delivery` skill instead. For PR mechanics (rebase, lockfiles, auto-merge, force-push), use `pr-discipline`.** Triggers on "Linear", "sub-issue", "blocks/blocked-by", "In Review", "linear-sop audit", "SD-SOP" (legacy alias — renamed to linear-sop in wave 3).
updated: 2026-05-25
wave: 3
---

# linear-sop — Linear tracker / org-level workflow

Use this skill when **Linear is the delivery tracker**. It owns the tracker shape and Linear-specific mechanics. It does **not** own per-slice rigor or PR mechanics — those are delegated.

**Scope boundary.** This skill owns the *tracker* and *org-level* concerns: Linear parent/child issue modelling, dependency edges, status transitions, the drift audit, and one-issue-one-PR enforcement. It does **not** own:

- Per-slice execution (tracer bullet, deep modules, per-cycle refactor scan, TDD scope table, Ralph review loop, slice lifecycle) → use `slice-delivery`.
- PR mechanics — iteration loop, merge mechanics, lockfile conflicts, branch protection, auto-merge, force-push, stuck PRs → use `pr-discipline`.

## Mental model

- **Parent Linear issue = lane / objective.** Names the product or workstream goal.
- **Child Linear sub-issue = independently mergeable implementation slice.** If it cannot own a PR, keep it as parent acceptance criteria instead.
- **One implementation sub-issue → one branch/worktree → one PR → one verified merge.**
- **Status follows evidence, never intent.**

## Source-of-truth order

Before non-trivial work, fetch live state — do not rely on memory for mutable status:

1. Linear parent issue + its children (status, blocks/blocked-by, assignee).
2. Open GitHub PRs on the relevant repo(s) and their merge state.
3. The repo's invariants / architecture docs (delegated to `slice-delivery`'s start-lane gate).

Reconcile drift before acting. If Linear and GitHub disagree, GitHub merge state is authoritative for "shipped"; Linear status must catch up.

## Tracker shape

### Parent / child decomposition

Convert vague children into PR-sized slices, or collapse non-PR-worthy children into parent acceptance criteria. Two failure modes to avoid:

- **Over-decomposition** — every sentence becomes a sub-issue. Sub-issues that don't own a PR pollute the queue.
- **Under-decomposition** — a single "implement feature X" child that should have been three sequential PRs. Causes broad PRs and review bottlenecks.

A sub-issue is PR-sized when it has a one-sentence concern and a verifiable acceptance bullet.

### Dependency edges

Record `blocks` / `blocked-by` in Linear *before* implementation, not retroactively. Mention stack/dependency state in PR bodies too. Do not open dependent PRs early unless the stack is explicit and actively driven by the same author.

### Status transitions

Each trigger must be externally verifiable — an auditor inspecting only Linear + GitHub state must be able to confirm the transition was legitimate. Local-only state (uncommitted changes, in-flight thinking) never moves status.

| Linear status | Trigger (externally verifiable) | How to verify |
|---|---|---|
| `Todo` / `Backlog` → `In Progress` | Feature branch exists on the remote with at least one commit ahead of the base. | `gh api repos/$OWNER/$REPO/branches/<branch>` returns 200 and `git rev-list origin/<base>..origin/<branch>` is non-empty. |
| `In Progress` → `In Review` | PR is open, linked to the Linear issue, and the first CI run has started. | `gh pr view <n> --json state,linkedIssues,statusCheckRollup`. |
| `In Review` → `Done` | Hosting platform reports `MERGED` **and** target-branch CI is green on the merge commit. | `gh pr view <n> --json state,mergeCommit` + `gh run list --branch <base> --commit <merge_sha>`. |

A green local gate is necessary but not sufficient. Do not mark `Done` from intent.

Workflows that use `Backlog` and `Todo` as separate states should treat both as pre-start; the trigger to `In Progress` is the same (first push to remote).

## When to create a Linear sub-issue vs. parent acceptance criteria

Create a sub-issue when:

- the item is independently mergeable as one PR;
- it has a one-sentence concern and at least one acceptance bullet;
- it needs its own status / assignee / dependency edge.

Keep as parent acceptance criteria when:

- the item is verification ("confirm X still passes") rather than implementation;
- the item can't own a PR on its own;
- removing the item from the parent's acceptance list would not prevent any sibling sub-issue from merging independently — i.e., it has no merge-graph standing of its own.

## Org-level start gate

The per-slice start-lane gate (sync base, read invariants/architecture/DOD, design the public interface, negotiate scope with the user, create the worktree) lives in `slice-delivery`. The two org-level additions on top of it are:

1. Confirm the slice exists as a Linear sub-issue (or create it before opening the PR). The PR must close exactly one implementation sub-issue.
2. Confirm Linear dependency edges (`blocks` / `blocked-by`) are recorded for any sub-issue that depends on another in-flight or unmerged sub-issue.

Then hand off to `slice-delivery` for the implementation lifecycle.

## Org-level merge gate

After `slice-delivery`'s lifecycle says the slice is ready, this skill owns the closing tracker work:

1. PR is open and linked to the Linear sub-issue. Linear is `In Review`.
2. Adversarial (Ralph) review dispositions are on the PR (delegated to `slice-delivery`).
3. Merge per `pr-discipline` (direct merge or armed auto-merge with `MERGED` verification within 15 minutes).
4. Move Linear sub-issue to `Done` only after merge verification — `gh pr view <n> --json state` returns `MERGED` and target-branch CI on the merge commit is green.
5. Clean branch/worktree per `repo-hygiene`.

## Drift audit

Run the bundled audit before/after large lane changes, before context switches, and whenever drift is suspected. The script is read-only.

```bash
python3 engineering/linear-sop/scripts/linear_sop_audit.py \
  --repo /path/to/repo \
  --github-repo owner/name \
  --linear-parent TEAM-1234 \
  --author @me
```

Use `--json` for machine-readable output and `--fail-on-findings` for CI-style gating.

It checks open PR health, Linear issue→PR mapping, stacked PR dependency evidence, active child issues without PRs, worktree count, and gone local branches.

Repair drift in this order:

1. Green/mergeable PRs with no merge/auto-merge action.
2. Dirty/conflicting stacked PRs (delegate the rebase mechanics to `pr-discipline`).
3. Active Linear children without PRs.
4. Stale Linear status (issues marked `In Review` whose PR is merged, etc.).
5. Branch/worktree cleanup (delegate to `repo-hygiene`).

## Related skills

- **`slice-delivery`** — per-slice execution discipline. Tracer bullets, deep modules, refactor scan, Ralph review, slice lifecycle, TDD scope table. linear-sop delegates to it.
- **`pr-discipline`** — PR iteration loop + merge mechanics (rebase, lockfile, auto-merge, branch protection, force-push, stuck PRs).
- **`td-sop`** — Markdown + GitHub Issues equivalent. Do not mix with linear-sop in the same repo.
- **`repo-hygiene`** — worktree and branch cleanup.
- **`model-routing`** — pick the right model/lane before spawning implementation/review subagents.
