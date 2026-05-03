---
name: figma-product-analysis
description: Analyze local Figma .fig files and related design exports for product planning or implementation. Use when inspecting .fig files, fig2sketch output, refig/Grida exports, design-to-build workflows, or turning incomplete Figma mockups into aligned product workflows and UI specs.
---

# Figma Product Analysis

Use this skill when a `.fig` file or Figma-derived artifact needs to inform product design, UX workflows, UI implementation, or asset extraction.

## Core stance

Treat Figma as evidence, not product truth.

- Do **not** blindly recreate mockups.
- First infer the intended product, workflows, states, and missing screens.
- Call out gaps, contradictions, and ambiguous flows before implementation.
- Preserve design intent: hierarchy, spacing, visual language, components, typography, colors, and responsive patterns.

## Preferred hybrid workflow

1. **Inventory inputs**
   - Locate `.fig`, HTML exports, screenshots, images, fonts, and assets.
   - Record paths and sizes.
   - Avoid destructive conversion; write outputs to an analysis directory.

2. **Structural analysis with `fig2sketch`**
   - Use `fig2sketch` for deep `.fig` understanding: pages, frames, nodes, names, component hierarchy, dimensions, and text.
   - Parse/summarize generated JSON instead of loading huge files into context.
   - Extract page/frame index tables: name, type, size, child count, likely purpose.

3. **Targeted visual exports with `refig` / Grida-style tools**
   - Use targeted frame exports for screenshots/assets.
   - Prefer specific page/frame IDs or names.
   - Do not rely on broad `--export-all` behavior; it may fail on large files or SECTION nodes.

4. **Compare structure vs visuals**
   - Match frame names/hierarchy to visual screenshots.
   - Identify canonical screens, duplicate explorations, variants, mobile/desktop breakpoints, and stale experiments.
   - Extract tokens/components only when repeated enough to matter.

5. **Product synthesis**
   - Produce markdown specs that separate:
     - confirmed design evidence
     - inferred workflow requirements
     - open product questions
     - implementation recommendations
   - Include screenshots/assets by relative path where useful.

## Useful commands

Always adapt paths to the local project. Keep outputs out of the source asset folder when possible.

```bash
# Inventory
find . -maxdepth 3 -type f \( -name '*.fig' -o -name '*.html' -o -name '*.png' -o -name '*.jpg' -o -name '*.svg' \) -print

# Inspect available tool flags
fig2sketch --help
refig --help

# Decode .fig structurally; output path depends on fig2sketch version
fig2sketch path/to/file.fig --output /tmp/fig-analysis

# Summarize large JSON without loading it all
python3 - <<'PY'
import json, pathlib
p = pathlib.Path('/tmp/fig-analysis')
for f in p.rglob('*.json'):
    print(f, f.stat().st_size)
PY
```

## Output format for product/design alignment

Prefer committing these docs into the target repo:

```text
docs/product/
  vision.md
  workflows.md
  information-architecture.md
  screen-inventory.md
  open-questions.md
docs/design/
  figma-analysis.md
  visual-language.md
  assets.md
```

Each workflow should include:

- Actors
- Entry points
- Happy path
- Empty/loading/error states
- Payment/permission gates if relevant
- Admin/support implications
- Analytics/audit events worth tracking
- Open questions

## Gotchas

- Large `.fig` JSON can be 100MB+. Summarize with scripts; do not paste/load whole files.
- Design files often contain duplicate explorations. Determine canonical screens before building.
- SECTION nodes and broad exports may fail in `refig`; target concrete frames instead.
- If Rust/Cargo is missing and a converter needs it, install it only with user approval unless already requested.
