# Waves

A *wave* is a deliberate refactor cohort — a group of skills that move together to a new layering or contract. Skills that belong to a wave declare it in frontmatter (`wave: <n>`). Skills that don't belong to a wave omit the field.

Two rules:

1. **Don't assign `wave:` retroactively.** A wave number is meaningful only when paired with a documented cohort. Adding `wave: 2` to an old skill three months later is noise.
2. **Document the wave in this file as part of the introducing PR.** Future readers need to know what the number means.

## Wave 3 — collapse tracker SOPs onto `slice-delivery`; introduce `delivery-loop`

**Window:** May 2026 (commits `89e234d` … `3e6737b`, PRs #1–#10).

**Goal.** Stop letting tracker SOPs duplicate per-slice execution discipline, and introduce a single autonomous multi-slice entry point so that operators with a runnable Definition-of-Done harness can ship without per-slice approval gates.

**Cohort (5 skills, all carry `wave: 3`):**

| Skill | Wave-3 change |
|---|---|
| [`slice-delivery`](engineering/slice-delivery/SKILL.md) | New skill (`89e234d`). Owns *how* a single slice ships — tracer bullet, per-cycle refactor scan, deep-module design, TDD scope table, Ralph review, lifecycle gate. Later: T0 spec-review added to start-lane (`392cca4`). |
| [`td-sop`](engineering/td-sop/SKILL.md) | Collapsed to org-level only (`89e234d`, `adfc9b9`). Per-slice rigor delegates to `slice-delivery`. |
| [`linear-sop`](engineering/linear-sop/SKILL.md) | Renamed from `sd-sop` (`b79b0b2`). Same collapse pattern as `td-sop`: tracker mechanics only, delegates per-slice rigor downward. |
| [`pr-discipline`](engineering/pr-discipline/SKILL.md) | Folded `pr-iterate` into `pr-discipline` (`0f42c5f`). One skill for both the iteration loop and the safety rules. |
| [`delivery-loop`](engineering/delivery-loop/SKILL.md) | New skill (`0c6e80a`). Operator-invoked autonomous wrapper around `slice-delivery` for multi-slice runs. Composes — does not replace — the execution wrapper. |

**Resulting layering:** see [`README.md` → Composition](README.md#-composition-engineering) (Mermaid) and [`CLAUDE.md` → Composition (engineering)](CLAUDE.md#composition-engineering) (ASCII). Those two diagrams are the authoritative source — keeping a third copy here would just drift.

**Companion documentation work** (not in the cohort, but landed in the same window): public-repo hygiene (`LICENSE`, `CONTRIBUTING.md`, `CLAUDE.md`), README flamboyance refresh + Triggers table + composition diagram correction (PRs #7–#10). These are docs, not skills, so they do not carry `wave:` frontmatter.

## Earlier waves

Wave 3 is the first formally numbered wave. Earlier skill additions (visible in `git log`) were not grouped into cohorts and do not carry `wave:` frontmatter.
