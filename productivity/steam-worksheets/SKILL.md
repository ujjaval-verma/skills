---
name: steam-worksheets
description: >-
  Generate print-ready, full-colour A4 STEAM worksheets for an early learner
  (ages ~4-7, Ontario Kindergarten / WRDSB aligned): one page, ~15 minutes, left
  binding margin. Use for any worksheet, practice sheet, activity sheet or
  printable for a young child ("a counting sheet", "a maths practice page",
  "a Level 2 space worksheet", "a weekly pack"), and for handwriting practice
  ("letter tracing", "trace and write" sets) via a separate generator.
updated: 2026-10-04
---

# STEAM Worksheets

Single-page, full-colour A4 worksheets drawn as inline SVG by a Python engine.

## Before you generate — confirm the inputs

- **Level (difficulty)** — `1`, `2`, or `3`. See "Levels" below. Default `2`.
- **Theme** — `space`, `animals`, `indian`, or `mixed`. Default `space`.
- **Topics** — any of `math, literacy, patterns, problemsolving, arts, science`.
  Default `math,literacy,patterns,problemsolving` (a balanced sheet).
- **Child's name** — personalises the title (e.g. "Asha's Space Worksheet").
  Optional; omit for a blank name line.
- **Number of activities** — `3` or `4` (the engine accepts only these values).
  Default `4` (≈15 min).
- **How many worksheets** — `--count N` for a one-theme pack (one call plans
  the whole pack); one call per theme for mixed themes.

## How to generate

The engine lives in `scripts/generate.py`. Run it from `scripts/` with
`uv run` (PEP 723 deps; fall back to `python3` + `weasyprint`).

```bash
cd <skill>/scripts
uv run generate.py \
  --out "<output folder>/Asha Space L2.pdf" \
  --level 2 --theme space --name Asha \
  --topics math,literacy,patterns,problemsolving \
  --activities 4 --seed 7
```

Notes:
- `--seed` makes content reproducible (pack sheet *i* uses `seed + i`); a
  single sheet and sheet 1 of a same-seed pack differ, so reproduce a pack with
  the same seed and `--count`.
- For a **pack of one theme**, add `--count N`. `--out` is treated as a base
  name and each sheet is written as `name 1.pdf … name N.pdf`. One shared planner
  rotates vowels, pattern shapes (AAB/ABB/ABC), activity variants (addition vs
  ten-frame, word-build vs sound-search), and colour scenes across the sheets,
  and excludes already-used words/icons so the pack does not repeat itself:

  ```bash
  uv run generate.py --out "<folder>/Asha Space.pdf" \
    --level 2 --theme space --count 5 --seed 1
  ```

## Handwriting practice (a second engine)

For pure writing practice — "big letters and numbers, traced and free-hand" —
use `scripts/handwriting.py` instead of `generate.py`. Same guarantees
(see below), different sheet shape: big
characters on three-line handwriting rules, a grey model to copy, a dashed
outline to trace, and an empty ruled line to write free-hand.

```bash
cd <skill>/scripts
uv run handwriting.py --out "<output folder>/Handwriting Practice.pdf"
```

Defaults give the whole alphabet plus digits: `--letters A-Z --numbers 0-9
--case both --layout grid` → 62 characters, 12 per page in a 3×4 grid, 6 pages.
Deliver the tricky-character set as its **own PDF**, not extra pages in the main
one:

```bash
uv run handwriting.py --layout tricky \
  --out "<output folder>/Handwriting Practice - Tricky Characters.pdf"
```

- `--layout grid` (default) — 12 characters a page: capitals, then small
  letters, then digits. Two rows per cell (trace, then write). Cover page is
  opt-in via `--cover`.
- `--layout tricky` — a separate, dedicated set for the reversal-prone
  characters: **4 a page** in a 2×2 grid, each with a spoken stroke cue
  ("b: line down, then the ball in front"), a bigger trace row (model + 2
  dashed) and **two** free-hand rows. Defaults to
  `b,d,p,q,g,a,e,s,n,u,m,w,2,5,6,9` (look-alikes paired on the same page) →
  4 pages; override with `--chars`. Cover is opt-in via `--cover`. Cues live in
  `TRICKY_CUES` — add one whenever you add a character.
- `--layout page` — one full page per letter and per number, with the key word
  to trace, a draw box, dot-counting, and free-hand review pages at the end.
  Ships a parent cover page unless `--no-cover`.
- `--case upper|lower|both`, `--letters 'A-F,S,T'`, `--numbers '1-10'|none`
  narrow the set; `--name` personalises the header; `--split` also writes one
  single-page PDF per sheet.

Every run prints the page count and **warns if any worksheet overflowed onto a
second page** — one worksheet must be exactly one page, so treat that warning as
a failure and shrink a row (`GRID_FS`) or drop a row before delivering.

Engine notes (both are WeasyPrint quirks, don't "fix" them back):
- Glyphs are SVG `<text>` with an explicit baseline, and those row SVGs carry
  **no `viewBox`** — WeasyPrint mis-scales stroked text inside a viewBox.
- `stroke-dasharray` on text with **more than one character** compresses glyph
  advances, so multi-character strings (words, `10`) trace as solid hollow
  outlines instead of dashed ones.
- Rule positions come from measured Comic Sans MS metrics (`CAP`/`XH`/`DESC`).
  The font stack prefers primary-school faces with a single-storey `a` and `g`;
  if you change it, re-measure those three constants or the letters will float
  off the rules.

## Levels (difficulty)

Match the level to the child, not the age.

- **Level 1 — emerging (typical start of Senior Kindergarten).** Counting and
  number tracing to ~5, single-letter tracing with a key word, simple AB
  patterns with one blank, a "trace the trail" path, colour-by-number.
- **Level 2 — developing (confident SK / start of Grade 1).** Addition within 10
  with picture support *or* a ten-frame count; CVC word building (write the
  missing middle vowel) *or* a sound search (initial phoneme); AAB/ABB/ABC
  patterns with two blanks; a real maze with dead ends; colour-by-number.
- **Level 3 — extending (strong SK / Grade 1).** Addition within 20 (abstract,
  no picture crutch), spell the whole CVC word from a picture, growing patterns,
  a larger maze.

See `references/curriculum.md` for how each topic maps to the Ontario
Kindergarten program and what "good enough" looks like at each level.

## Topics → activities

Topics map onto the activities in Levels above, plus:

- **arts** — colour-by-number scene; each theme has two scenes that alternate
  across a pack (space → rocket/star, animals → fish/butterfly,
  indian → rangoli/flower, mixed → butterfly/flower)
- **science** — "which one is different?" observation/sorting

## Design guarantees (don't break these)

These are baked into the engine:
- **A4 with an 18 mm left margin** for ring-binder punching.
- **Full colour**, all artwork vector — verify a render shows no empty boxes
  (missing glyphs). If you ever hand-edit and see `.notdef` warnings, you've
  introduced an emoji/character with no font; replace it with an SVG icon.
- **One page**, ~15 minutes, with a parent answer key in the footer. The
  engine accepts at most 4 activities to keep this guarantee.

Extending the skill (themes, icons, words, scenes, activities): see
`references/extending.md`.
