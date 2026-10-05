# Extending steam-worksheets

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
