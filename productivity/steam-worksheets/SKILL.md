---
name: steam-worksheets
description: >-
  Generate print-ready, full-colour A4 STEAM worksheets for an early learner
  (ages ~4-7, Ontario Kindergarten / WRDSB aligned). Each sheet is one page, ~15
  minutes of focused work, with a left binding margin for a ring binder. Use this
  skill WHENEVER the user wants a worksheet, practice sheet, activity sheet, or
  printable for a young child — including requests like "make a worksheet for my
  daughter", "a maths practice page", "some letter tracing", "a counting sheet",
  "a colouring + puzzle page", "a Level 2 space worksheet", or a daily/weekly
  pack of practice pages. Trigger even if they don't say the word "worksheet"
  but clearly want a printable learning activity for a young kid. Handles inputs
  for level (difficulty), theme, topics, child's name, and number of activities.
updated: 2026-06-15
---

# STEAM Worksheets

Generate single-page, full-colour A4 worksheets for an early learner. Every
sheet is built from a Python engine that draws all artwork as inline SVG (no
emoji font needed — it prints clean in colour), keeps an 18 mm left margin for
ring-binder punching, and includes a discreet parent answer key in the footer.

## Before you generate — confirm the inputs

Ask the user (or infer from the request) these, then proceed. Don't over-ask;
sensible defaults exist for everything except where noted.

- **Level (difficulty)** — `1`, `2`, or `3`. See "Levels" below. Default `2`.
- **Theme** — `space`, `animals`, `indian`, or `mixed`. Default `space`.
- **Topics** — any of `math, literacy, patterns, problemsolving, arts, science`.
  Default `math,literacy,patterns,problemsolving` (a balanced sheet).
- **Child's name** — personalises the title (e.g. "Asha's Space Worksheet").
  Optional; omit for a blank name line.
- **Number of activities** — `3` or `4` (the engine accepts only these values).
  Default `4` (≈15 min). The 4-activity maximum keeps the sheet on one page.
- **How many worksheets** — for several sheets of one theme, use `--count N`
  (preferred): one invocation plans the whole pack so it *covers* the vowels,
  pattern shapes, activity variants, and colour scenes instead of repeating them.
  For a pack that spans **different themes**, call the engine once per theme
  (each call is internally varied).

If the user has set a difficulty preference for their child before, reuse it.

## How to generate

The engine lives in `scripts/generate.py`. Run it from the skill's `scripts/`
directory with `uv run` — the script declares its own dependency (`weasyprint`)
via PEP 723 inline metadata, so nothing is installed into the system Python.
If `uv` isn't available, install `weasyprint` yourself and use `python3` instead.

```bash
cd <skill>/scripts
uv run generate.py \
  --out "<output folder>/Asha Space L2.pdf" \
  --level 2 --theme space --name Asha \
  --topics math,literacy,patterns,problemsolving \
  --activities 4 --seed 7
```

Notes:
- `--seed` makes content reproducible. Omit it for fresh content each run; pass
  a fixed number to regenerate an identical sheet (or an identical pack — pack
  sheet *i* uses `seed + i`). Note: a single sheet (`--count 1`) and sheet 1 of a
  pack with the same seed are *not* identical — the pack planner fixes the
  rotation deterministically, while a single sheet randomises it. Reproduce a
  pack the same way you made it (same seed + same `--count`).
- Save the PDF directly into the user's worksheets folder, then show it with the
  file-presentation tool so they can open and print it.
- For a **pack of one theme**, add `--count N`. `--out` is treated as a base
  name and each sheet is written as `name 1.pdf … name N.pdf`. One shared planner
  rotates vowels, pattern shapes (AAB/ABB/ABC), activity variants (addition vs
  ten-frame, word-build vs sound-search), and colour scenes across the sheets,
  and excludes already-used words/icons so the pack does not repeat itself:

  ```bash
  uv run generate.py --out "<folder>/Asha Space.pdf" \
    --level 2 --theme space --count 5 --seed 1
  ```

- For a **pack of different themes**, call the engine once per theme.

Each run prints the level/theme/seed used — record the seed if the user might
want that exact sheet again.

## Levels (difficulty)

The same activity types scale by level, so a child can progress without the
sheets changing character. Match the level to the child, not the age.

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

- **math** — counting & writing (L1) / addition *or* ten-frame count (L2) /
  abstract addition (L3)
- **literacy** — letter-of-the-day tracing (L1) / CVC word building *or* sound
  search (L2) / whole-word spelling (L3)
- **patterns** — repeating (AAB/ABB/ABC, two blanks) at L2, AB at L1, growing at L3
- **problemsolving** — trace-the-trail (L1) / maze (L2–3)
- **arts** — colour-by-number scene; each theme has two scenes that alternate
  across a pack (space → rocket/star, animals → fish/butterfly,
  indian → rangoli/flower, mixed → butterfly/flower)
- **science** — "which one is different?" observation/sorting

At L2 the math and literacy variants rotate within a pack (and are chosen at
random for a single sheet), so two sheets rarely show the same activity shape.

Pick topics to vary the sheet. A good default mixes one math, one literacy, one
thinking puzzle (patterns or problemsolving), and a creative finisher (arts).

## Design guarantees (don't break these)

These are baked into the engine and the user relies on them:
- **A4 with an 18 mm left margin** for ring-binder punching.
- **Full colour**, all artwork vector — verify a render shows no empty boxes
  (missing glyphs). If you ever hand-edit and see `.notdef` warnings, you've
  introduced an emoji/character with no font; replace it with an SVG icon.
- **One page**, ~15 minutes, with a parent answer key in the footer. The
  engine accepts at most 4 activities to keep this guarantee.

## Extending the skill

- **New theme**: add an entry to `THEMES` in `scripts/icons.py` (palette, icon
  list, letter words, and a `scenes` list). The hard minimum is **3 distinct
  icons** (patterns sample 3 without replacement), but use **6+** so a multi-sheet
  pack does not repeat the same trio. Provide **at least 2 scenes** so the
  creative finisher varies across a pack.
- **New icon**: add an SVG to `_ICONS` in `scripts/icons.py` (auto-normalises to
  a square) and a spoken name to `ICON_NAME` (used by Sound Search / sorting).
- **More words**: extend `CVC_BY_VOWEL` (keyed by short vowel) — each new word is
  `(WORD, icon)` and needs a matching icon. More words per vowel = less repetition
  in a long pack.
- **New scene**: add a builder returning `(svg, legend, colors)` and register it
  in `SCENES`; reference it from a theme's `scenes` list. Ensure **every colour
  region carries a visible numeral** (place the number at the region's centre).
- **New activity**: add a builder to `scripts/activities.py` with signature
  `(level, theme, rng, ctx=None)` returning `{title, hint, body, key}`, and
  register it in `builder_for`. To make it pack-aware, read rotation hints from
  `ctx` and call `ctx.take_unused(...)` for exclusion; keep it working with
  `ctx=None` for standalone calls.

After any change, regenerate a sheet and eyeball the PDF before delivering.
