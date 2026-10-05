---
name: product-inception
description: Turn a new product idea, legacy repo, design dump, prototype, or vague business direction into a reusable product inception package: product thesis, target customer, workflows, IA, screen inventory, assumptions, open questions, technical starting point, and implementation-ready docs. Use before scaffolding or heavily implementing a new product, especially when building multiple products from repeatable playbooks.
updated: 2026-10-04
---

# Product Inception

Clarify what to build before serious implementation.

## Output contract

Create or update a compact inception pack, usually under `docs/product/`. If the repo already has equivalent docs, adapt to them instead of duplicating.

- `vision.md` — product thesis, target customer, value proposition, v1 scope, non-goals.
- `workflows.md` — critical user/admin/operator workflows as stepwise flows.
- `information-architecture.md` — navigation, primary objects, routes/screens, permissions.
- `screen-inventory.md` — known screens from designs/prototypes plus missing screens.
- `assumptions.md` — facts assumed for now, confidence, and validation path.
- `open-questions.md` — decisions that block product/technical direction.
- `pricing-and-packaging.md` — buyer, paid moment, plans, packaging risks.
- `implementation-plan.md` — first build slices, gates, and sequencing; write it only once the product shape is clear.

A starter pack lives at `assets/product-docs-template/`; copy it into repos that lack product docs and replace the placeholders.

## Workflow

1. **Run three lenses** over the brief, legacy repos, prototypes and design exports:
   - Legacy/code forensics: what exists, what is reusable, what is deprecated, what behavior matters.
   - Design/product forensics: screens, flows, visual language, missing states, mockup gaps. Treat mockups as evidence for a workflow, not something to copy.
   - Market/business self-grill: buyer, user, paid moment, alternatives, wedge, risks.

2. **Commit to one v1 default**: name the primary user and buyer, and the first workflow that must feel excellent. Record viable alternatives as explicit strategic forks in `open-questions.md`, not hidden ambiguity.

3. **Classify legacy code** as source, reference, or deprecated before reusing any of it; never reuse by default.

4. **Gate implementation**: scaffold only when the docs identify a coherent v1, first workflow, and technical shape. Pause or open a decision issue if buyer, monetization, permissions, or safety posture has multiple plausible answers.
