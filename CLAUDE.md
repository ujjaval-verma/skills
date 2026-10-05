# CLAUDE.md — skills repo

This repo holds reusable, repo-agnostic AgentSkills: one `SKILL.md` per skill under a category folder. This file is the agent-facing operating manual; contribution steps live in [`CONTRIBUTING.md`](CONTRIBUTING.md).

**Read first:** [`README.md`](README.md) — categories, skill index, design principles, "what not to include".

## Layout

```
<category>/<skill-name>/SKILL.md
<category>/<skill-name>/scripts/      # optional, only if SKILL.md references a script the agent will execute
<category>/<skill-name>/references/   # optional, docs SKILL.md links to (read on demand)
<category>/<skill-name>/assets/       # optional, templates or static files SKILL.md references (e.g. product-inception)
scripts/                              # repo-level tooling (not skill-specific)
```

Categories: `engineering/`, `product/`, `productivity/`. Folder names are hyphen-case and match `name:`; add/rename/delete in one PR so they never drift.

Per-skill `scripts/` is never speculative: no empty or single-trivial-helper folders. The root `scripts/` holds tooling for the library itself (e.g. `link-user-skills.sh`, which symlinks the curated roster into `~/.claude/skills` and `~/.agents/skills`); same bar.

## Frontmatter

Every engineering `SKILL.md` carries `name`, `description` (trigger-oriented: what it is for and when to invoke it) and `updated: YYYY-MM-DD`. Bump `updated:` when the body changes materially; typo and link fixes don't count.

## Composition (engineering)

Pick the highest layer that fits and let it delegate; duplication across layers is a refactor trigger. Diagram: [README](README.md#-composition-engineering).

- `delivery-loop` — optional, operator-invoked entry point that runs `slice-delivery` across a queue; never auto-promoted.
- `slice-delivery` — how one slice ships.
- `pr-discipline` — PR safety rails, definition of shipped, CI triage and recovery.
- Tactical — `repo-hygiene`, `validate-infra-change`.

`productivity/create-tracker-issue` sits outside the stack and carries no delivery workflow.

## Adversarial review (Ralph) — contract

Every non-trivial PR (beyond a typo, link fix or single-line config tweak) must show an adversarial review trail before merge. Local confidence and green CI are not sufficient.

1. **Dispatch** an independent reviewer subagent against the PR diff, framed as adversarial (its job is to find what is wrong, not to approve) and told to check `slice-delivery`, this file and any repo-local invariants. Its model and thinking level must differ from the author's (e.g. Sonnet-authored, Opus-reviewed).
2. **Post** its findings as a PR comment grouped Blocking / Non-blocking / Nits.
3. **Disposition** every finding on the PR (comment, commit body or both): `Fixed` (commit ref), `Deferred` (tracked follow-up) or `Rejected` (reasoning).
4. **Block merge** until every Blocking finding is `Fixed` or has documented `Rejected` reasoning.

## Editing skills

- Keep `SKILL.md` concise; cut prose the agent already knows without the skill.
- Surface destructive candidates before acting and make external writes explicit (see [Design principles](README.md#design-principles)).
- No secrets, private repo names, user paths or repo-specific assumptions unless the skill is scoped to that repo ([What not to include](README.md#what-not-to-include)).
- Update the README index and any `Related skills` or delegation lines in the same PR as an add, rename or scope change.
- Commits: Conventional Commits, scoped, one concern each (see CONTRIBUTING).
