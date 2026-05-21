---
name: slice-delivery
description: Tracker-agnostic vertical-slice delivery discipline for any repo. Use when implementing, reviewing, or shipping a non-trivial change. Covers the three pillars (velocity, rigor, hygiene), the per-cycle refactor scan, deep-module design, tracer-bullet sequencing, the adversarial Ralph review loop, the per-surface TDD scope table pattern, and the start-lane / PR lifecycle gates. Triggers on "slice", "tracer bullet", "deep module", "refactor scan", "Ralph loop", "per-cycle refactor", "vertical slice", "definition of done".
wave: 3
updated: 2026-05-21
---

# Slice delivery

The execution wrapper for any non-trivial change. Tracker-agnostic — applies whether your repo uses Linear, GitHub Issues, a Markdown tracker, or `git log` alone.

This skill is the **how** of shipping a single slice well. It assumes a higher-level skill (or repo-local doc) has already told you **which** slice to ship. For tracker-specific workflows, see `linear-sop` (Linear) or `td-sop` (Markdown + GitHub).

For the underlying TDD philosophy, defer to your repo's TDD skill or to `tdd` if no local one exists.

## What is a slice

A slice is one PR-sized change that crosses every layer it needs to and produces working behavior end-to-end, however thin. Not "all the types this week, all the adapters next week." Layers-first is horizontal slicing; it produces shelves of code that don't ship and tests that verify imagined behavior.

A good slice:

- Has a single concern that can be stated in one sentence.
- Ships behind a complete (if minimal) public path — the tracer bullet proves the path before you scale it.
- Owns exactly one branch (or worktree), one PR, one merge.
- Is rollback-safe by itself.

## Three pillars

### 1. Velocity — small, verifiable chunks

- Slice = delivery unit. One concern per slice; one slice per PR; one concern per commit.
- Tracer bullet first. The first work in any slice is one test that proves the end-to-end path with the minimum possible implementation. Everything after thickens this skeleton.
- The tracker is whatever your repo already uses. Do not invent a parallel one. If a tracker entry doesn't exist for the slice, create it before opening the PR — not after.
- Commits carry the slice scope: `feat(<slice-id>): ...`. This lets `git log --grep='(<slice-id>)'` reconstruct slice progress in seconds.
- "Shipped" means the slice is on the default integration branch with CI green. Locally green is not shipped.

### 2. Rigor — prove the change

- **Tracer bullet end-to-end, then incrementally**. One test red → one test green → refactor scan → next test. Never write all the tests first. Never write all the implementation first. The vertical (RED→GREEN per behavior) ordering is what produces tests that verify actual behavior instead of imagined behavior.
- **Deep modules over shallow**. Small interface, rich implementation. Before adding a parameter to an interface, ask: "can this be one method instead of three?" Before adding a new module, ask: "is the public surface describable in two sentences?"
- **Refactor scan after every green**, not at PR time. Candidates:
  - Duplication → extract function / value object.
  - Long methods → break into private helpers (tests stay on the public interface).
  - Shallow modules → combine or deepen.
  - Feature envy → move logic to where the data lives.
  - Primitive obsession → introduce a typed value.
  - **What does new code reveal about existing code?** The most powerful candidate. Your new code often makes a previously-tolerable wart obvious. Fix it now, in this slice, as a separate commit. Do not accumulate a cleanup PR backlog.
- Refactors are separate commits from features. Refactor-then-feature is two commits.
- **Adversarial (Ralph) review on non-trivial PRs**, before merge. Spawn an independent code-reviewer subagent with: the PR diff, the relevant spec / invariants / DOD, and explicit instruction to be adversarial. Post its findings as a Markdown PR comment. Address blocking findings with fix commits and verification; record dispositions (fixed / deferred / rejected) in commit bodies or a follow-up comment. Local confidence + green CI is not enough — the PR's comment trail must show adversarial observations and dispositions, or the merge is blocked.
- Honesty gates always apply: no fake-live behavior, no mocked-but-presented-as-real data paths, no logs containing sensitive raw input.

### 3. Hygiene — keep the repo operable

- Worktrees for parallel work. Cap typically 3–4 active. Each worktree owns one slice.
- One concern per commit. Diff-time SOLID is a quality gate, not an abstraction incentive.
- No `TODO`/`FIXME`/`XXX` in source. Either fix now or promote to a durable follow-ups doc.
- After each merge or merge wave, run the repo's closeout/hygiene script. Get back under steady-state thresholds before opening more slices.
- Do not leave dev servers, workers, or local dependency stacks running after verification.

## TDD scope table — the contract for your repo

Different surfaces deserve different discipline. Without a per-surface contract, agents either over-test trivial glue or under-test complex logic. The remedy is a table in the repo (typically `docs/engineering/testing.md`) that names each surface and tells you the discipline, test type, and explicit out-of-scope:

| Surface | Discipline | Test type | Out of scope |
|---------|-----------|-----------|--------------|

Make this table the contract. When you add a new surface that doesn't match a row, add the row in the same PR.

Common discipline values: `TDD strict`, `Fixture-backed`, `TDD when non-trivial`, `Scenario-driven`, `E2E only`, `Migration tests only`, `Visual + a11y`, `No tests`. The label is less important than naming the surface and being explicit about what test type belongs there.

## Durable vs transient artifacts

Three classes of repo artifact:

- **Durable** — `ARCHITECTURE.md`, `INVARIANTS.md` (or equivalent), `DEFINITION-OF-DONE.md`, `TESTING.md`, ADRs. Tracked. Edited via PR.
- **Transient** — session-scoped plans, scratchpads, intermediate analysis. Should be gitignored or live under `docs/scratch/`. Net-new top-level `.md` files should be rejected by a pre-commit hook.
- **Mutable status** — slice tracker / build-progress / PHASES. Tracked. Updated in every implementation PR.

Decide which class a new doc belongs to before writing it. If it's transient, do not check it in.

## Start-lane gate (before opening a slice)

1. Sync the integration branch to latest base.
2. Read the repo's invariants / architecture / DOD / testing contracts. If any are missing, that's a slice in itself — fix that first.
3. Check open PRs and worktree/branch hygiene. If hygiene is already out of bounds, run closeout before opening new work.
4. Pick one slice from the tracker that moves a stated acceptance bullet forward.
5. **Design the public interface first**. Identify the deep-module candidate. If there isn't one, ask whether the slice is really needed or whether it's three smaller slices.
6. **Get explicit user approval of the scope and the chosen behaviors to test** before writing any code. "You can't test everything. Confirm with the user exactly which behaviors matter most." This is a gate, not a footnote — skipping it produces tests for imagined behavior.
7. Create a dedicated branch/worktree from latest base.

## Slice lifecycle gate

1. **Tracer bullet**: one end-to-end test → minimal code → green.
2. **Incremental loop**: for each next behavior, RED → GREEN → **refactor scan**. The refactor scan runs every cycle, not just at the end.
3. Run the repo's fast verification command continuously while iterating.
4. Run the repo's full local CI gate before push.
5. Commit with conventional format + slice scope (`feat(<slice-id>): ...`).
6. Open the PR. PR body lists: slice ID, scope, non-scope, verification evidence, evidence for any addendum that applies (UI screenshots / AI fixtures+evals / migration up+down / deploy rollback).
7. **Ralph review loop** for non-trivial PRs: dispatch an adversarial code-reviewer subagent against the repo's invariants / DOD; post findings as a PR comment; address blocking findings as fix commits with verification; record dispositions. Repeat until no blocking findings remain.
8. Watch hosted CI and review until green + LGTM-level confidence.
9. Merge. Update the tracker if not already part of the slice's PR.
10. Closeout: run repo hygiene; remove the worktree if used; QA wave gate if applicable.

## Anti-patterns this skill prevents

- **Horizontal slicing** — writing all tests then all implementation; tests verify imagined behavior.
- **Layers-first delivery** — shipping shelves of code that don't reach the user.
- **Cleanup PR backlog** — refactor candidates discovered mid-slice are deferred to a future cleanup PR that never lands.
- **Local-green = shipped** — confidence without the integration branch + CI + adversarial review.
- **Tracker drift** — implementation diverges from the tracker; status reconciliation PRs become a thing.
- **Shallow modules** — interfaces grow new parameters faster than they grow new methods, hiding nothing.
- **Mock-everything tests** — tests pass because everything is mocked; production breaks because nothing was real.

## What this skill does not cover

- Picking which slice to ship next — that's a planning / tracker skill.
- Tracker-specific mechanics (Linear sub-issues, GitHub Issues automation, Markdown tracker conventions) — see `linear-sop` or `td-sop` or the repo's local execution doc.
- PR mechanics that are independent of slice content — see `pr-discipline`.
- Repo-agnostic CI / merge-queue strategy — separate concern.

## Related skills

- `tdd` — the underlying red-green-refactor discipline this skill wraps.
- `linear-sop` — Linear-based tracker mechanics.
- `td-sop` — Markdown + GitHub Issues hybrid tracker mechanics.
- `pr-discipline` — PR iteration loop + merge mechanics (rebase, lockfile, auto-merge, branch protection, force-push, stuck PRs).
- `repo-hygiene` — worktree/branch cleanup.
