# Agent Skills

Reusable, repo-agnostic AgentSkills for coding agents.

Each skill lives in its own directory and contains a single required `SKILL.md` file:

```text
<skill-name>/
  SKILL.md
```

## Skills

- `model-routing` — choose model, thinking level, and review lane for delegated work.
- `pr-iterate` — run a disciplined pull-request implementation loop.
- `pr-discipline` — safety rules for PR review, merge, branch protection, lockfiles, and auto-merge.
- `github-ci-triage` — diagnose GitHub Actions / PR check failures with `gh`.
- `repo-hygiene` — safely inspect stale branches, worktrees, and cleanup candidates.
- `figma-product-analysis` — analyze Figma `.fig` files and design exports for product/workflow/UI specs.

## Design principles

- Keep skills generic and parameterized.
- Avoid private repo names, local paths, secrets, or user-specific assumptions.
- Keep `SKILL.md` concise; add references/scripts only when they materially improve reuse.
- Prefer surfacing destructive candidates before acting.
- Make external writes explicit and permission-aware.

## Adding a skill

1. Create a hyphen-case folder name under the repo root.
2. Add `SKILL.md` with YAML frontmatter:

   ```markdown
   ---
   name: example-skill
   description: Clear trigger-oriented description of when to use this skill.
   ---
   ```

3. Keep the body focused on reusable workflow instructions.
4. Check for private names/paths before publishing.
5. Commit each skill independently when possible.

## What not to include

- Secrets, tokens, API keys, or private endpoints.
- Repo-specific rules unless the skill is explicitly scoped to that repo.
- Long prose that an agent already knows without the skill.
- Extra files inside a skill folder unless they are used by that skill.
