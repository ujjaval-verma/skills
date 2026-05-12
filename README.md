# Agent Skills

Reusable, repo-agnostic AgentSkills for coding agents.

Each skill lives in its own category subfolder and contains a single required `SKILL.md` file:

```text
<category>/
  <skill-name>/
    SKILL.md
```

Inspired by [mattpocock/skills](https://github.com/mattpocock/skills).

## Skills

### Engineering

- `engineering/github-ci-triage` — diagnose GitHub Actions / PR check failures with `gh`.
- `engineering/model-routing` — choose model, thinking level, and review lane for delegated work.
- `engineering/network-connectivity-troubleshoot` — diagnose public-network, DNS, `gh`, or Tailscale connectivity failures.
- `engineering/pr-discipline` — safety rules for PR review, merge, branch protection, lockfiles, and auto-merge.
- `engineering/pr-iterate` — run a disciplined pull-request implementation loop.
- `engineering/repo-hygiene` — safely inspect stale branches, worktrees, and cleanup candidates.
- `engineering/sd-sop` — org-agnostic Linear issue-to-PR delivery SOP for one-issue-one-PR mapping, dependencies, statuses, audits, and merge verification.
- `engineering/td-sop` — Tech Dolphins markdown + GitHub execution wrapper for PRD/build-progress tracking, Mermaid dependencies, and velocity/rigor/hygiene gates.
- `engineering/validate-infra-change` — safely live-smoke Kubernetes/IaC PR changes in dev/staging while preserving GitOps ownership and rollback paths.

### Product

- `product/figma-product-analysis` — analyze Figma `.fig` files and design exports for product/workflow/UI specs.
- `product/product-inception` — turn product ideas, legacy assets, and designs into reusable inception docs before implementation.

### Productivity

- `productivity/timesheet` — generate a formatted 80-column timesheet from GitHub activity for a date range.

## Design principles

- Keep skills generic and parameterized.
- Avoid private repo names, local paths, secrets, or user-specific assumptions.
- Keep `SKILL.md` concise; add references/scripts only when they materially improve reuse.
- Prefer surfacing destructive candidates before acting.
- Make external writes explicit and permission-aware.

## Adding a skill

1. Identify the right category (`engineering`, `product`, or `productivity`).
2. Create a hyphen-case folder under the category.
3. Add `SKILL.md` with YAML frontmatter:

   ```markdown
   ---
   name: example-skill
   description: Clear trigger-oriented description of when to use this skill.
   ---
   ```

4. Keep the body focused on reusable workflow instructions.
5. Check for private names/paths before publishing.
6. Commit each skill independently when possible.

## What not to include

- Secrets, tokens, API keys, or private endpoints.
- Repo-specific rules unless the skill is explicitly scoped to that repo.
- Long prose that an agent already knows without the skill.
- Extra files inside a skill folder unless they are used by that skill.
