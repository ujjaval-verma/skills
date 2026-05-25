# CLAUDE.md — skills repo

This repo holds reusable, repo-agnostic AgentSkills. Each skill is a single `SKILL.md` under a category folder. The README has the public-facing description and design principles; this file is the agent-facing operating manual.

**Read first:** [`README.md`](README.md) — categories, skill index, design principles, "what not to include".

## Layout

```
<category>/<skill-name>/SKILL.md
<category>/<skill-name>/scripts/   # optional, only if a script is referenced by SKILL.md
```

Categories: `engineering/`, `product/`, `productivity/`. Skill folder names are hyphen-case and match the `name:` in frontmatter. Add/rename/delete in one PR — never let folder and `name:` drift.

## Frontmatter conventions

Every engineering `SKILL.md` should carry:

```yaml
---
name: <hyphen-case, matches folder>
description: <trigger-oriented; what the skill is for and when to invoke it>
updated: YYYY-MM-DD   # ISO date of last material edit
wave: <int>           # optional; only when the skill belongs to a deliberate refactor wave
---
```

Bump `updated:` when the body changes materially (typo/link fixes don't count). When introducing the field on a previously-undated skill, set it to the date the field is added; this is a known approximation — the value going forward will reflect material edits.

Don't assign `wave:` retroactively. A wave number is meaningful only when paired with a defined refactor cohort (e.g., wave 3 = the "collapse tracker SOPs onto `slice-delivery`" pass in May 2026). Future waves should document themselves in their first introducing PR's description; if a `WAVES.md` accrues, point to it here.

Enforcement is currently social, not mechanical. Adding a lint/CI check that engineering skills declare `updated:` is a worthwhile follow-up.

## Composition (engineering)

Skills layer rather than overlap. When a task fits multiple skills, pick the highest layer and let it delegate:

- **Tracker SOPs** — `linear-sop` (Linear), `td-sop` (Markdown + GitHub Issues). Own *which* slice ships and the tracker artifacts (issues, build-progress, PRD).
- **Multi-slice loop (optional, operator-invoked)** — `delivery-loop`. A separate entry point the operator invokes directly (never auto-promoted from `slice-delivery`) that runs `slice-delivery` across a pre-flight slice queue, with a per-slice T0 spec-review gate substituting for human approval and hard pause conditions inside the loop. Requires a repo with a runnable Definition of Done harness, ADRs/invariants, and spec/code-review templates; not used in this skills repo.
- **Execution wrapper** — `slice-delivery`. Owns *how* a slice ships: tracer bullet, per-cycle refactor scan, deep-module design, TDD scope table, adversarial (Ralph) review loop, slice lifecycle gate.
- **PR mechanics** — `pr-discipline`. Iteration loop (orient → isolate → implement → verify → commit → open/update PR → watch CI → merge prep) + safety rules (branch protection, lockfiles, auto-merge, force-pushes, hook bypass, stuck PRs).
- **Tactical** — `github-ci-triage`, `repo-hygiene`, `network-connectivity-troubleshoot`, `validate-infra-change`, `model-routing`.

Tracker SOPs delegate per-slice rigor directly to `slice-delivery`. `delivery-loop` is a parallel operator-invoked path that composes `slice-delivery` N times for autonomous multi-slice runs — tracker SOPs do not hand off to it. `slice-delivery` delegates PR mechanics to `pr-discipline`. Duplication across layers is a refactor trigger.

## Adversarial review (Ralph) — contract

Every non-trivial PR (any change beyond a typo / link fix / single-line config tweak) must show an adversarial review trail before merge. This is a contract, not a suggestion.

1. **Dispatch** an independent code-reviewer subagent against the PR diff, with explicit instruction to be adversarial and to check the contracts in `slice-delivery` / `CLAUDE.md` / any repo-local invariants.
2. **Post** its findings as a Markdown PR comment, grouped as Blocking / Non-blocking / Nits.
3. **Disposition** every finding: `Fixed` (commit reference), `Deferred` (with a tracked follow-up), or `Rejected` (with reasoning). Record dispositions on the PR — comment, commit body, or both.
4. **Block merge** until every Blocking finding is `Fixed` or has documented `Rejected` reasoning.
5. Reviewer model selection: use `model-routing`. Reviewer must not be the same model + same thinking level that authored the change.

Local confidence + green CI is not sufficient evidence to merge a non-trivial change in this repo. The PR comment trail must show adversarial observations and dispositions.

## `scripts/` folder

Optional. Add one only when the script is referenced from `SKILL.md` by a relative path the agent will actually execute (e.g., `linear-sop/scripts/linear_sop_audit.py`). Don't add a `scripts/` folder speculatively — empty or single-trivial-helper directories are noise.

## Editing skills

- Keep `SKILL.md` concise. Cut prose the agent already knows without the skill present.
- Surface destructive candidates before acting; make external writes explicit and permission-aware (see [Design principles](README.md#design-principles)).
- Never include secrets, private repo names, user paths, or repo-specific assumptions unless the skill is explicitly scoped to that repo (see [What not to include](README.md#what-not-to-include)).
- Update the README skill index in the same PR as any add/rename/delete.
- Update cross-references (`Related skills`, delegation lines in other skills) in the same PR as any rename or scope change.

## Commit conventions

Conventional Commits, scoped by category or skill name where useful: `feat(slice-delivery): ...`, `docs(readme): ...`, `refactor(linear-sop): ...`. One concern per commit.
