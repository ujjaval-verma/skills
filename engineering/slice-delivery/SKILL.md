---
name: slice-delivery
description: Tracker-agnostic vertical-slice delivery discipline. Use when the work is framed in slice terms or per-slice execution is delegated here. Triggers on "slice", "tracer bullet", "deep module", "refactor scan", "Ralph", "definition of done".
updated: 2026-10-04
---

# Slice delivery

The **how** of shipping one slice well, in any repo and any tracker. It assumes the operator or a repo-local doc has already said **which** slice. PR mechanics and the definition of "shipped" belong to `pr-discipline` (see its `Definition of "shipped"` section).

## What is a slice

One PR-sized change that crosses every layer it needs and produces working behavior end to end, however thin. Layers-first (all types this week, all adapters next) ships nothing and tests imagined behavior.

- One concern, statable in one sentence; one branch or worktree, one PR, one merge; rollback-safe alone.
- Scope budget: default at most 8 tasks and 3 new production modules (a repo may override).
- Commits carry the slice scope, `feat(<slice-id>): ...`, so `git log --grep='(<slice-id>)'` reconstructs progress.

## Start-lane gate

1. If more than 3-4 slice worktrees are active or repo hygiene is out of bounds, close out (`repo-hygiene`) before opening a new slice.
2. Read the repo's invariants, architecture, definition of done and testing contracts. If one is missing, writing it is the first slice.
3. Design the public interface first and name the deep-module candidate (`codebase-design` if installed). If there is none, ask whether the slice is needed or is three smaller ones.
4. Lock scope and the behaviors to test before writing code. When scope is open or behavior choices are contested, confirm them with the user in a `grilling` session (one question at a time, with a recommended answer); sharpen fuzzy terms with `domain-modeling` first.
5. T0 adversarial spec-review: mandatory when the repo has a spec-review template, recommended otherwise. Dispatch an adversarial reviewer with that template, or these lenses: (A) consistency of spec and plan with invariants, ADRs and the definition of done; (B) value judgments needing human sign-off; (C) scope against the slice budget. Disposition each finding as BLOCKING / NIT / DEFERRED. BLOCKING here means fix the spec or plan, never code, since none exists yet. T0 does not count against the task budget. Skipping needs a reason recorded in the plan.

## Slice lifecycle gate

1. Tracer bullet first: one end-to-end test, minimal code, green. Everything after thickens it.
2. Then per behavior: one test red, green, refactor scan. The scan runs on every green, not at PR time, on the code you just touched and its neighbours. Ask what the new code reveals about existing code: a tolerable wart that is now obvious gets fixed in this slice, as its own commit, never banked as a cleanup backlog. Refactors are separate commits from features.
3. Honesty gates: no fake-live behavior, no mocked data path presented as real, no sensitive raw input in logs.
4. Open the PR per `pr-discipline`. Body lists slice ID, scope, non-scope, verification evidence, and the evidence for any addendum that applies: UI screenshots, AI fixtures and evals, migration up and down, deploy rollback.
5. Ralph review on non-trivial PRs, before merge: dispatch an adversarial reviewer (a different model or thinking level than the author) against the PR diff, invariants and definition of done. Post findings as a PR comment grouped Blocking / Non-blocking / Nits, disposition each as fixed, deferred (tracked) or rejected (with reasoning). Fix Blocking findings as their own commits, then re-dispatch a fresh reviewer, and repeat until no Blocking finding is open. Block merge until then. Green CI alone is not enough.
6. Merge and close out per `pr-discipline`; run the repo's hygiene script and remove the worktree.

## TDD scope table

Keep a table in the repo (typically `docs/engineering/testing.md`) as the contract for what discipline each surface gets, so agents neither over-test glue nor under-test logic:

| Surface | Discipline | Test type | Out of scope |
|---------|-----------|-----------|--------------|

A new surface with no matching row gets its row in the same PR. Typical disciplines: `TDD strict`, `Fixture-backed`, `TDD when non-trivial`, `Scenario-driven`, `E2E only`, `Migration tests only`, `Visual + a11y`, `No tests`.

## Artifact classes

- **Durable**: `ARCHITECTURE.md`, invariants, definition of done, testing doc, ADRs. Tracked, edited via PR.
- **Transient**: session plans and scratch analysis. Gitignored or under `docs/scratch/`; never checked in. A pre-commit hook should reject net-new top-level `.md` files.
- **Mutable status**: slice tracker, build progress. Tracked, updated in every implementation PR.

Decide the class before writing a doc.

## Related skills

Skills outside this library (`superpowers:*`, `codebase-design`, `grilling`, `domain-modeling`) are used when installed; otherwise apply the discipline inline or use the repo-local equivalent.

- `pr-discipline`: PR loop, merge mechanics, definition of shipped.
- `superpowers:test-driven-development`: the red-green-refactor discipline this wraps (a repo-local TDD skill wins).
- `repo-hygiene`: worktree and branch cleanup.
- `delivery-loop`: operator-invoked multi-slice wrapper that composes this skill via subagents.
