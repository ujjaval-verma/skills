---
name: product-inception
description: Turn a new product idea, legacy repo, design dump, prototype, or vague business direction into a reusable product inception package: product thesis, target customer, workflows, IA, screen inventory, assumptions, open questions, technical starting point, and implementation-ready docs. Use before scaffolding or heavily implementing a new product, especially when building multiple products from repeatable playbooks.
---

# Product Inception

Use this skill when the task is to clarify what to build before serious implementation.

## Output contract

Create or update a compact inception pack, usually under `docs/product/`:

- `vision.md` — product thesis, target customer, value proposition, v1 scope, non-goals.
- `workflows.md` — critical user/admin/operator workflows as stepwise flows.
- `information-architecture.md` — navigation, primary objects, routes/screens, permissions.
- `screen-inventory.md` — known screens from designs/prototypes plus missing screens.
- `assumptions.md` — facts assumed for now, confidence, and validation path.
- `open-questions.md` — decisions that block product/technical direction.
- `pricing-and-packaging.md` — buyer, paid moment, plans, packaging risks.
- `implementation-plan.md` — first build slices, gates, and sequencing.

If the repo already has equivalent docs, adapt to the existing structure instead of duplicating.

## Workflow

1. **Inventory evidence**
   - Inspect product brief, legacy repos, prototypes, design exports, docs, tickets, and deployment notes.
   - Separate evidence from inference. Mark unknowns explicitly.

2. **Run three parallel lenses mentally or with subagents**
   - Legacy/code forensics: what exists, what is reusable, what is deprecated, what behavior matters.
   - Design/product forensics: screens, flows, visual language, missing states, mockup gaps.
   - Market/business self-grill: buyer, user, paid moment, alternatives, wedge, risks.

3. **Choose a v1 default**
   - Name the primary user and buyer.
   - Define the first workflow that must feel excellent.
   - Preserve viable alternatives as explicit strategic forks, not hidden ambiguity.

4. **Document product before code**
   - Prefer concise Markdown with concrete flows over abstract prose.
   - Include non-goals and missing decisions to prevent accidental overbuild.
   - Add an implementation plan only after the product shape is clear.

5. **Gate implementation**
   - Safe to scaffold if docs identify a coherent v1, first workflow, and technical shape.
   - Pause or create a decision issue if buyer, monetization, permissions, or safety posture has multiple plausible answers.

## Reuse rules

- Keep docs repo-agnostic unless the product requires specifics.
- Do not blindly copy design mockups; treat them as evidence for a product workflow.
- Do not reuse a legacy codebase by default. First decide whether it is source, reference, or deprecated.
- Prefer reversible scaffolding and docs over premature domain implementation.

## Bundled template

A reusable docs pack lives at `assets/product-docs-template/`. Copy it into new repos when they lack product docs, then replace placeholders with product-specific content.
