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
- `engineering/pr-discipline` — PR iteration loop + merge safety rules: open → watch CI → fix → merge, branch protection, lockfiles, auto-merge, force-pushes, hook bypass policy, stuck PRs.
- `engineering/repo-hygiene` — safely inspect stale branches, worktrees, and cleanup candidates.
- `engineering/linear-sop` — Linear tracker / org-level workflow: parent-as-lane, sub-issue-as-slice, dependency edges, status transitions, drift audit. Delegates per-slice rigor to `slice-delivery` and PR mechanics to `pr-discipline`.
- `engineering/slice-delivery` — tracker-agnostic vertical-slice execution discipline: tracer bullets, per-cycle refactor scan, deep modules, TDD scope table, adversarial (Ralph) review loop, slice lifecycle.
- `engineering/td-sop` — Tech Dolphins markdown + GitHub execution wrapper for PRD/build-progress tracking, Mermaid dependencies, and velocity/rigor/hygiene gates.
- `engineering/validate-infra-change` — safely live-smoke Kubernetes/IaC PR changes in dev/staging while preserving GitOps ownership and rollback paths.

### Product

- `product/figma-product-analysis` — analyze Figma `.fig` files and design exports for product/workflow/UI specs.
- `product/product-inception` — turn product ideas, legacy assets, and designs into reusable inception docs before implementation.

### Productivity

- `productivity/timesheet` — generate a formatted 80-column timesheet from GitHub activity for a date range.

## Composition (engineering)

The engineering skills form a layered harness:

```
 tracker SOPs       linear-sop  (Linear)        td-sop  (Markdown + GitHub Issues)
                         \                    /
                          \                  /
 execution wrapper          slice-delivery   (tracer bullet → refactor scan → Ralph → DoD)
                                  |
                                  v
 PR mechanics              pr-discipline   (the loop + the rules)
                                  |
                                  v
 tactical skills         github-ci-triage · repo-hygiene · network-connectivity-troubleshoot · validate-infra-change · model-routing
```

Pick the highest layer that fits the task and let it delegate downward. Tracker SOPs own *what* to ship and which tracker artifact to update; `slice-delivery` owns *how* to ship it; `pr-discipline` owns the PR iteration loop and merge mechanics; tactical skills are leaf utilities the higher layers call into.

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
   updated: YYYY-MM-DD
   ---
   ```

   Engineering skills should declare `updated:` (ISO date of the last material edit). `wave:` is optional — only set it when the skill belongs to a deliberate refactor wave. See [`CLAUDE.md`](CLAUDE.md#frontmatter-conventions) for the full rule and backfill convention.

4. Keep the body focused on reusable workflow instructions.
5. Check for private names/paths before publishing.
6. Commit each skill independently when possible.

## What not to include

- Secrets, tokens, API keys, or private endpoints.
- Repo-specific rules unless the skill is explicitly scoped to that repo.
- Long prose that an agent already knows without the skill.
- Extra files inside a skill folder unless they are used by that skill.
