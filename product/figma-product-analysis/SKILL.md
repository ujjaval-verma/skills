---
name: figma-product-analysis
description: Analyze Figma files (live via the Figma MCP server, or offline .fig exports) for product planning or implementation. Use when inspecting Figma designs or .fig files, fig2sketch/refig/Grida output, design-to-build workflows, or turning incomplete Figma mockups into aligned product workflows and UI specs.
updated: 2026-10-04
---

# Figma Product Analysis

Treat Figma as evidence, not product truth: infer the intended product, workflows, states and missing screens, and call out gaps and contradictions before building. Identify the canonical screens first; design files are full of duplicate explorations, variants and stale experiments.

## Source

- Figma URL or live file, MCP server connected: use it for files, frames and variables.
- Figma URL, no MCP: ask the user to connect the MCP server or export a `.fig`.
- Local `.fig`: decode structure with `fig2sketch` and export visuals with `refig`. Check `--help` for current flags; output paths vary by version. If a converter needs a Rust toolchain, get approval before installing it.

## Gotchas

- `.fig` JSON can exceed 100MB. Summarize with scripts (page/frame index: name, type, size, children); never load a whole file.
- Export individual frames, not SECTION nodes, and avoid `refig --export-all`; either may fail on large files.
- Write conversion output to the session scratchpad, not `/tmp` or the source asset folder.

## Output

Produce the `docs/product/` pack defined by [`product-inception`](../product-inception/SKILL.md), keeping confirmed design evidence, inferred requirements and open questions separate. Put design-side output (visual language, repeated tokens/components, exported asset paths) in `docs/design/`.
