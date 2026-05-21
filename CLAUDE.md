# CLAUDE.md — skills repo

This repo holds reusable, repo-agnostic AgentSkills. Each skill is a single `SKILL.md` under a category folder. The README has the public-facing description and design principles; this file is the agent-facing operating manual.

**Read first:** [`README.md`](README.md) — categories, skill index, design principles, "what not to include".

## Layout

```
<category>/<skill-name>/SKILL.md
<category>/<skill-name>/scripts/   # optional, only if a script materially supports the skill
```

Categories: `engineering/`, `product/`, `productivity/`. Skill folder names are hyphen-case and match the `name:` in frontmatter.

## Frontmatter conventions

Every engineering `SKILL.md` must carry:

```yaml
---
name: <hyphen-case, matches folder>
description: <trigger-oriented; what the skill is for and when to invoke it>
updated: YYYY-MM-DD   # ISO date of last material edit; required on engineering skills
wave: <int>           # optional; only set when the skill belongs to a deliberate refactor wave
---
```

When editing a skill, bump `updated:` if and only if the body changed materially (typos and link fixes don't count). Don't assign `wave:` retroactively — it should mean something, not be a timestamp.

## Composition (engineering)

Skills layer rather than overlap. When a task fits multiple skills, pick the highest layer and let it delegate:

- **Tracker SOPs** — `sd-sop` (Linear), `td-sop` (Markdown + GitHub Issues). Own *which* slice ships and the tracker artifacts (issues, build-progress, PRD).
- **Execution wrapper** — `slice-delivery`. Owns *how* a slice ships: tracer bullet, per-cycle refactor scan, deep-module design, TDD scope table, adversarial (Ralph) review loop, slice lifecycle gate.
- **PR mechanics** — `pr-iterate` (the open→watch→merge loop), `pr-discipline` (the safety rules: branch protection, lockfiles, auto-merge, force-pushes).
- **Tactical** — `github-ci-triage`, `repo-hygiene`, `network-connectivity-troubleshoot`, `validate-infra-change`, `model-routing`.

Tracker SOPs should delegate per-slice rigor to `slice-delivery`, not duplicate it. `slice-delivery` should delegate PR mechanics to `pr-iterate` / `pr-discipline`, not duplicate them. Duplication across layers is a refactor trigger.

## `scripts/` folder

Optional. Only add one when a script materially supports the skill's workflow (e.g., `sd-sop/scripts/sd_sop_audit.py`). Keep scripts alongside `SKILL.md` in the skill's folder; reference them by relative path from the skill body. Don't add a `scripts/` folder speculatively — empty or single-trivial-helper directories are noise.

## Editing skills

- Keep `SKILL.md` concise. Cut prose the agent already knows without the skill present.
- Surface destructive candidates before acting; make external writes explicit and permission-aware (see README §"Design principles").
- Never include secrets, private repo names, user paths, or repo-specific assumptions unless the skill is explicitly scoped to that repo (see README §"What not to include").
- Update the README skill index in the same PR as any add/rename/delete.
- Update cross-references (`Related skills`, delegation lines in other skills) in the same PR as any rename or scope change.

## Commit conventions

Conventional Commits, scoped by category or skill name where useful: `feat(slice-delivery): ...`, `docs(readme): ...`, `refactor(sd-sop): ...`. One concern per commit.
