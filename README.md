<div align="center">

# 🛠️ Agent Skills

> *A composable harness of reusable, repo-agnostic AgentSkills — small Markdown files that teach a coding agent how to ship work the way a senior engineer would.*

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="MIT License"/>
  <img src="https://img.shields.io/badge/skills-13-purple?style=flat-square" alt="13 skills"/>
  <img src="https://img.shields.io/badge/format-SKILL.md-success?style=flat-square" alt="SKILL.md format"/>
  <img src="https://img.shields.io/badge/branch--protected-main-green?style=flat-square" alt="main is branch-protected"/>
  <img src="https://img.shields.io/badge/PRs-welcome-orange?style=flat-square" alt="PRs welcome"/>
</p>

<p align="center">
  <a href="#-skills"><strong>Skills</strong></a> ·
  <a href="#-composition-engineering"><strong>Composition</strong></a> ·
  <a href="#-design-principles"><strong>Principles</strong></a> ·
  <a href="#-adding-a-skill"><strong>Add a skill</strong></a> ·
  <a href="CONTRIBUTING.md"><strong>Contributing</strong></a>
</p>

</div>

---

**What this is.** A curated library of [AgentSkills](https://github.com/mattpocock/skills) — single-file Markdown playbooks an LLM coding agent loads on demand. Each skill encodes a *workflow*: when to invoke it, what discipline to apply, what artifact to produce. They layer rather than overlap, so an agent picks the highest layer that fits and lets it delegate downward.

**Why a library.** Discipline doesn't survive context resets. Skills do.

```text
<category>/
  <skill-name>/
    SKILL.md          ← the playbook
    scripts/          ← optional helpers referenced by SKILL.md
```

Inspired by [mattpocock/skills](https://github.com/mattpocock/skills).

## 📚 Skills

### 🏗️ Engineering

| Skill | What it owns |
|---|---|
| [`engineering/delivery-loop`](engineering/delivery-loop/SKILL.md) | Multi-slice autonomous wrapper around `slice-delivery`: pre-flight slice queue, per-slice T0 spec-review gate, hard pause conditions, final Definition-of-Done gate. |
| [`engineering/github-ci-triage`](engineering/github-ci-triage/SKILL.md) | Diagnose GitHub Actions / PR check failures with `gh`. |
| [`engineering/linear-sop`](engineering/linear-sop/SKILL.md) | Linear tracker / org workflow: parent-as-lane, sub-issue-as-slice, dependency edges, drift audit. |
| [`engineering/model-routing`](engineering/model-routing/SKILL.md) | Choose model, thinking level, and review lane for delegated work. |
| [`engineering/network-connectivity-troubleshoot`](engineering/network-connectivity-troubleshoot/SKILL.md) | Diagnose public-network, DNS, `gh`, or Tailscale connectivity failures. |
| [`engineering/pr-discipline`](engineering/pr-discipline/SKILL.md) | PR iteration loop + merge safety: open → watch CI → fix → merge, branch protection, lockfiles, auto-merge, force-pushes, stuck PRs. |
| [`engineering/repo-hygiene`](engineering/repo-hygiene/SKILL.md) | Safely inspect stale branches, worktrees, and cleanup candidates. |
| [`engineering/slice-delivery`](engineering/slice-delivery/SKILL.md) | Tracker-agnostic vertical-slice execution: tracer bullets, per-cycle refactor scan, deep modules, TDD scope table, adversarial (Ralph) review, slice lifecycle. |
| [`engineering/td-sop`](engineering/td-sop/SKILL.md) | Tech Dolphins Markdown + GitHub execution wrapper: PRD/build-progress, Mermaid dependency graphs, velocity/rigor/hygiene gates. |
| [`engineering/validate-infra-change`](engineering/validate-infra-change/SKILL.md) | Safely live-smoke Kubernetes/IaC PR changes in dev/staging while preserving GitOps ownership and rollback paths. |

### 🎨 Product

| Skill | What it owns |
|---|---|
| [`product/figma-product-analysis`](product/figma-product-analysis/SKILL.md) | Analyze Figma `.fig` files and design exports for product/workflow/UI specs. |
| [`product/product-inception`](product/product-inception/SKILL.md) | Turn product ideas, legacy assets, and designs into reusable inception docs before implementation. |

### ⚡ Productivity

| Skill | What it owns |
|---|---|
| [`productivity/timesheet`](productivity/timesheet/SKILL.md) | Generate a formatted 80-column timesheet from GitHub activity for a date range. |

## 🧩 Composition (engineering)

The engineering skills are deliberately **layered**, not flat. Tracker SOPs decide *what* ships; `delivery-loop` chains multiple slices autonomously; `slice-delivery` decides *how* a single slice ships; `pr-discipline` owns the PR loop; tactical skills are leaf utilities the higher layers call into.

```text
   ┌─────────────────────────────────────────────────────────────────────────┐
   │  tracker SOPs        linear-sop  (Linear)         td-sop  (MD + GH)     │
   └──────────────────────────────┬──────────────────────────┬───────────────┘
                                  │                          │
                                  ▼                          ▼
   ┌─────────────────────────────────────────────────────────────────────────┐
   │  multi-slice loop         delivery-loop  (optional)                     │
   │                           (queue → T0 spec-review → slice → DoD gate)   │
   └─────────────────────────────────┬───────────────────────────────────────┘
                                     │
                                     ▼
   ┌─────────────────────────────────────────────────────────────────────────┐
   │  execution wrapper        slice-delivery                                │
   │                           (tracer bullet → refactor scan → Ralph → DoD) │
   └─────────────────────────────────┬───────────────────────────────────────┘
                                     │
                                     ▼
   ┌─────────────────────────────────────────────────────────────────────────┐
   │  PR mechanics             pr-discipline                                 │
   │                           (the loop + the safety rules)                 │
   └─────────────────────────────────┬───────────────────────────────────────┘
                                     │
                                     ▼
   ┌─────────────────────────────────────────────────────────────────────────┐
   │  tactical    github-ci-triage · repo-hygiene · model-routing            │
   │              network-connectivity-troubleshoot · validate-infra-change  │
   └─────────────────────────────────────────────────────────────────────────┘
```

Pick the highest layer that fits the task and let it delegate. Duplication across layers is a refactor trigger — not a feature.

## 🎯 Design principles

- **Generic and parameterized.** No private repo names, local paths, secrets, or user-specific assumptions.
- **Concise.** Cut prose the agent already knows without the skill present. `SKILL.md` is not a tutorial; it's a runbook.
- **Trigger-oriented.** Every `description:` answers *when should the agent invoke this?* — not *what is this about?*
- **Surface destructive candidates before acting.** External writes are explicit and permission-aware.
- **Layered, not overlapping.** A new skill earns its slot only when no existing skill can absorb it.

## ✍️ Adding a skill

1. Pick a category: `engineering/`, `product/`, or `productivity/`.
2. Create a hyphen-case folder whose name matches the `name:` you'll put in frontmatter.
3. Write `SKILL.md`:

   ```yaml
   ---
   name: example-skill
   description: Trigger-oriented description of when to use this skill.
   updated: 2026-05-21
   ---
   ```

   Engineering skills should declare `updated:` (ISO date of the last material edit). `wave:` is optional — only set it when the skill belongs to a deliberate refactor cohort. See [`CLAUDE.md`](CLAUDE.md#frontmatter-conventions) for the full rule and backfill convention.

4. Keep the body focused on reusable workflow instructions.
5. Check for private names/paths before publishing.
6. Update the skill index above in the same PR.

Full guidelines: [`CONTRIBUTING.md`](CONTRIBUTING.md).

## 🚫 What not to include

- Secrets, tokens, API keys, or private endpoints.
- Repo-specific rules unless the skill is explicitly scoped to that repo.
- Long prose that an agent already knows without the skill.
- Extra files inside a skill folder unless they are used by that skill.

## 📜 License

[MIT](LICENSE) © Ujjaval Verma
