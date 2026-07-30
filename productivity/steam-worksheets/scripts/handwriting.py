#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["weasyprint"]
# ///
"""Generate a print-ready A4 handwriting-practice PDF set for a kindergarten child.

Big letters and numbers on three-line handwriting rules: a solid grey model to
copy, dashed outlines to trace, then empty ruled rows for free-hand writing.

Usage:
  uv run handwriting.py --out PATH.pdf [--name Asha] [--letters A-Z] \
      [--numbers 0-10] [--case both|upper|lower] [--no-cover]

Every glyph is drawn as SVG <text> with an explicit baseline, so the letters sit
exactly on the rules. Font stack prefers primary-school print faces with a
single-storey 'a' and 'g' (Comic Sans MS / Chalkboard SE / Andika).
"""
import argparse
import os
import sys
from html import escape

# ---------------------------------------------------------------- metrics ----
# Fractions of font-size, measured from Comic Sans MS glyph bounds (upem 2048):
# 'A' top 0.722, 'H' top 0.759, x-height 0.51-0.54, 'p'/'g' bottom -0.28.
# The rules are placed from these so tall letters just touch the top line, small
# letters touch the dashed midline, and descenders reach the dotted line.
CAP = 0.77
XH = 0.52
DESC = 0.30

FONT = "'Comic Sans MS','Chalkboard SE','Andika','Century Gothic','Noto Sans',sans-serif"

W = 680          # usable content width in CSS px (A4 minus 18mm/12mm margins)
RULE = "#8ecae6"  # handwriting rules
RULE_STRONG = "#219ebc"  # baseline
MODEL = "#d2d2e0"  # solid grey model glyph (dark enough to trace over in pencil)
TRACE = "#adadc4"  # dashed outline glyph

LETTER_WORDS = {
    "A": "apple", "B": "ball", "C": "cat", "D": "dog", "E": "egg", "F": "fish",
    "G": "goat", "H": "hat", "I": "igloo", "J": "jam", "K": "kite", "L": "leaf",
    "M": "moon", "N": "nest", "O": "orange", "P": "pig", "Q": "queen",
    "R": "rain", "S": "sun", "T": "tree", "U": "umbrella", "V": "van",
    "W": "web", "X": "box", "Y": "yak", "Z": "zip",
}
NUMBER_WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven",
                "eight", "nine", "ten", "eleven", "twelve"]

# --------------------------------------------------------------- grid mode ---
# 12 characters per page in a 3-across x 4-down grid (the default layout).
GRID_COLS = 3
GRID_ROWS = 4
GRID_GAP = 10
CELL_W = (W - GRID_GAP * (GRID_COLS - 1)) // GRID_COLS
CELL_PAD = 7
CELL_ROW_W = CELL_W - 2 * CELL_PAD - 4      # drawable width inside a cell
GRID_FS = 76                                # big enough to fill a third of the page

# ------------------------------------------------------------- tricky mode ---
# 4 reversal-prone characters per page in a 2x2 grid, with a stroke cue and two
# free-hand rows each. Wider cells, bigger glyphs, more repetitions.
TRICKY_COLS = 2
TRICKY_ROWS = 2
TRICKY_CELL_W = (W - GRID_GAP * (TRICKY_COLS - 1)) // TRICKY_COLS
TRICKY_ROW_W = TRICKY_CELL_W - 2 * CELL_PAD - 4
TRICKY_FS = 96

# The characters young writers most often reverse or muddle, and how to say the
# strokes out loud. Order pairs the look-alikes on the same page (b/d, p/q, ...).
TRICKY_DEFAULT = "b,d,p,q,g,a,e,s,n,u,m,w,2,5,6,9"
TRICKY_CUES = {
    "b": "Line down, then the ball in front &mdash; the bat comes first.",
    "d": "Ball first (start like a c), then the line up and down.",
    "p": "Line down below the baseline, then the ball at the top.",
    "q": "Ball first, then a line down below the baseline.",
    "g": "Circle like a c, then a tail that hooks back to the left.",
    "a": "Circle like a c, then a straight line down beside it.",
    "e": "Line across first, then curve up and around.",
    "s": "Curve one way, then back the other &mdash; like a snake.",
    "n": "Line down, back up the same line, then over one hump.",
    "u": "Down, curve along the baseline, up &mdash; then a line down.",
    "m": "Line down, back up, then over two humps.",
    "w": "Down, up, down, up &mdash; all sharp corners, no curves.",
    "2": "Curve over the top, slide down, then a line along the baseline.",
    "5": "Line down, tummy out to the right, then a hat across the top.",
    "6": "Slide down from the top line, then loop around at the bottom.",
    "9": "Circle at the top, then a straight line down past the baseline.",
}

# pastel header gradients, rotated page to page so the set stays cheerful
GRADS = [("#4361ee", "#4cc9f0"), ("#ef476f", "#ffd166"), ("#06d6a0", "#118ab2"),
         ("#9b5de5", "#f15bb5"), ("#f4845f", "#f7b267"), ("#2a9d8f", "#8ab17d")]

CSS = f"""
@page {{ size: A4; margin: 12mm 12mm 12mm 18mm; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; }}
body {{ font-family: {FONT}; color: #2b2d42; }}
.page {{ page-break-after: always; }}
.page:last-child {{ page-break-after: auto; }}
.head {{ display: flex; align-items: center; justify-content: space-between;
  color: #fff; border-radius: 14px; padding: 9px 16px; }}
.head h1 {{ margin: 0; font-size: 21px; line-height: 1.15; }}
.head .sub {{ font-size: 12px; opacity: .93; margin-top: 2px; }}
.head .badge {{ font-size: 26px; font-weight: 700; background: rgba(255,255,255,.24);
  padding: 2px 16px; border-radius: 14px; letter-spacing: 2px; }}
.meta {{ display: flex; gap: 18px; margin: 8px 2px 2px; font-size: 12.5px; color: #555; }}
.meta .line {{ flex: 1; border-bottom: 2px dotted #b8b8c8; padding-bottom: 2px; }}
.lbl {{ font-size: 13px; font-weight: 700; color: #52527a; margin: 9px 0 1px 2px; }}
.lbl .tip {{ font-weight: 400; color: #8a8aa3; font-size: 11.5px; }}
.row {{ display: block; }}
.foot {{ margin-top: 10px; display: flex; justify-content: space-between;
  align-items: center; font-size: 11.5px; color: #888; gap: 10px; }}
.draw {{ margin-top: 8px; border: 2px dashed #cfcfe0; border-radius: 12px;
  height: 78px; padding: 5px 9px; font-size: 12px; color: #9a9ab0; }}
.strip {{ font-size: 15px; letter-spacing: 3.5px; color: #52527a; line-height: 1.7; }}
.cover h2 {{ font-size: 17px; margin: 14px 0 4px; color: #3a3a5c; }}
.cover ul {{ margin: 4px 0 0 18px; padding: 0; font-size: 13.5px; line-height: 1.65; color: #4a4a63; }}
.card {{ border: 2px solid #eceaf3; border-radius: 14px; padding: 8px 13px 11px; margin-top: 10px; }}
.boxes {{ display: flex; gap: 12px; margin-top: 6px; }}
.box {{ width: 52px; height: 52px; border: 2.5px solid #4361ee; border-radius: 10px; flex: none; }}
.dots {{ display: flex; gap: 9px; flex-wrap: wrap; align-items: center; flex: 1; }}
.dot {{ width: 26px; height: 26px; border-radius: 50%; background: #ffd166;
  border: 2px solid #f3a712; flex: none; }}
.countrow {{ display: flex; align-items: center; gap: 14px; margin-top: 4px; }}
.grid {{ display: flex; flex-wrap: wrap; gap: {GRID_GAP}px; margin-top: 8px; }}
.cell {{ width: {CELL_W}px; border: 2px solid #eceaf3; border-radius: 12px;
  padding: 3px {CELL_PAD}px 5px; }}
.cell .cap {{ font-size: 11.5px; font-weight: 700; color: #7a7a99; margin: 0 0 1px 2px; }}
.cell .cap .hint {{ font-weight: 400; color: #a9a9bd; }}
.cell.wide {{ width: {TRICKY_CELL_W}px; }}
.cell .cue {{ font-size: 11.5px; color: #6c6c8a; background: #f7f5ff;
  border-radius: 8px; padding: 4px 8px; margin: 1px 0 3px; }}
"""


def _dash(text):
    """Dashed outline for a single glyph; solid outline for longer strings.

    WeasyPrint compresses glyph advances when stroke-dasharray is applied to SVG
    text with more than one character, so words are traced as solid hollow
    outlines instead (same activity, correct spacing).
    """
    return ' stroke-dasharray="5 5"' if len(text) == 1 else ""


def _lines(y_top, baseline, y_desc, xh_px, width=W):
    """Three-line handwriting rules + a dotted descender line."""
    mid = baseline - xh_px
    return (
        f'<line x1="0" y1="{y_top:.1f}" x2="{width}" y2="{y_top:.1f}" '
        f'stroke="{RULE}" stroke-width="1.6"/>'
        f'<line x1="0" y1="{mid:.1f}" x2="{width}" y2="{mid:.1f}" stroke="{RULE}" '
        f'stroke-width="1.6" stroke-dasharray="7 7"/>'
        f'<line x1="0" y1="{baseline:.1f}" x2="{width}" y2="{baseline:.1f}" '
        f'stroke="{RULE_STRONG}" stroke-width="2.2"/>'
        f'<line x1="0" y1="{y_desc:.1f}" x2="{width}" y2="{y_desc:.1f}" stroke="{RULE}" '
        f'stroke-width="1.2" stroke-dasharray="2 6"/>')


def rule_row(text, fs=94, count=6, models=1, width=W, start_dot=True):
    """One ruled writing row.

    `text` is the glyph (or short string) to practise; `count` copies are laid
    out across the row. The first `models` copies are solid grey (copy me), the
    rest are dashed outlines (trace me). `count == models == 0` gives an empty
    row for free-hand writing.
    """
    cap, desc = CAP * fs, DESC * fs
    pad = 5
    baseline = pad + cap
    y_desc = baseline + desc
    h = y_desc + 3
    # NOTE: no viewBox — WeasyPrint mis-scales stroked (outline) SVG text inside a
    # viewBox, so all row coordinates are plain CSS px matching width/height.
    svg = [f'<svg class="row" width="{width}" height="{h:.0f}">',
           _lines(pad, baseline, y_desc, XH * fs, width)]
    if start_dot:
        svg.append(f'<circle cx="6" cy="{baseline:.1f}" r="4" fill="#06d6a0"/>')
    if count:
        left = 16
        step = (width - left - 8) / count
        for i in range(count):
            x = left + i * step
            if i < models:
                svg.append(f'<text x="{x:.1f}" y="{baseline:.1f}" font-family={FONT!r} '
                           f'font-size="{fs}" fill="{MODEL}">{escape(text)}</text>')
            else:
                svg.append(f'<text x="{x:.1f}" y="{baseline:.1f}" font-family={FONT!r} '
                           f'font-size="{fs}" fill="none" stroke="{TRACE}" '
                           f'stroke-width="1.8"{_dash(text)}>{escape(text)}</text>')
    svg.append("</svg>")
    return "".join(svg)


def word_row(word, fs=54, width=W):
    """A single dashed-outline word to trace, on its own rules."""
    cap, desc = CAP * fs, DESC * fs
    pad = 4
    baseline = pad + cap
    y_desc = baseline + desc
    h = y_desc + 3
    return (f'<svg class="row" width="{width}" height="{h:.0f}">'   # no viewBox: see rule_row
            f'{_lines(pad, baseline, y_desc, XH * fs, width)}'
            f'<text x="14" y="{baseline:.1f}" font-family={FONT!r} font-size="{fs}" '
            f'fill="none" stroke="{TRACE}" stroke-width="1.6"{_dash(word)}>'
            f'{escape(word)}</text></svg>')


def head(title, sub, badge, grad):
    g1, g2 = grad
    return (f'<div class="head" style="background:linear-gradient(90deg,{g1},{g2})">'
            f'<div><h1>{title}</h1><div class="sub">{sub}</div></div>'
            f'<div class="badge">{escape(badge)}</div></div>')


def meta_row(name):
    who = f"Name: {escape(name)}" if name else "Name:"
    return (f'<div class="meta"><div class="line">{who}</div><div class="line">Date:</div>'
            '<div class="line">Stars: &#9734; &#9734; &#9734;</div></div>')


def label(text, tip=""):
    tip = f' <span class="tip">&middot; {tip}</span>' if tip else ""
    return f'<div class="lbl">{text}{tip}</div>'


def grid_cell(ch):
    """One character in the grid: a trace row (grey model + dashed copy) above an
    empty ruled row to write it free-hand."""
    kind = "number" if ch.isdigit() else ("big" if ch.isupper() else "small")
    return (f'<div class="cell"><div class="cap">{escape(ch)} '
            f'<span class="hint">&middot; {kind}</span></div>'
            f'{rule_row(ch, fs=GRID_FS, count=2, models=1, width=CELL_ROW_W)}'
            f'{rule_row("", count=0, fs=GRID_FS, width=CELL_ROW_W)}</div>')


def tricky_cell(ch):
    """One tricky character: the stroke cue, a trace row, then two free-hand rows."""
    cue = TRICKY_CUES.get(ch, "Say the strokes out loud as you write.")
    kind = "number" if ch.isdigit() else "letter"
    return (f'<div class="cell wide"><div class="cap">{escape(ch)} '
            f'<span class="hint">&middot; tricky {kind}</span></div>'
            f'<div class="cue">{cue}</div>'
            f'{rule_row(ch, fs=TRICKY_FS, count=3, models=1, width=TRICKY_ROW_W)}'
            f'{rule_row("", count=0, fs=TRICKY_FS, width=TRICKY_ROW_W)}'
            f'{rule_row("", count=0, fs=TRICKY_FS, width=TRICKY_ROW_W)}</div>')


def tricky_page(chars, name, grad, page_no, pages):
    cells = "".join(tricky_cell(ch) for ch in chars)
    shown = " ".join(chars)
    return (f'<div class="page">'
            f'{head("Tricky Characters", "The ones that are easy to flip &mdash; slow and steady", shown, grad)}'
            f'{meta_row(name)}'
            f'{label("Read the cue, trace the greys, then write two lines yourself", "start on the green dot")}'
            f'<div class="grid">{cells}</div>'
            f'<div class="foot"><div>Tricky Characters &middot; page {page_no} of {pages} '
            f'&middot; print on A4</div>'
            f'<div>Grown-up tip: if it comes out backwards, say the cue and try again.</div>'
            f'</div></div>')


def grid_page(chars, name, grad, page_no, pages):
    cells = "".join(grid_cell(ch) for ch in chars)
    first, last = chars[0], chars[-1]
    return (f'<div class="page">'
            f'{head("Writing Practice", "Trace the grey letter, then write your own", f"{first} \u2013 {last}", grad)}'
            f'{meta_row(name)}'
            f'{label("Trace &rarr; then write it yourself on the empty line", "start on the green dot")}'
            f'<div class="grid">{cells}</div>'
            f'<div class="foot"><div>Handwriting Practice &middot; page {page_no} of {pages} '
            f'&middot; print on A4</div>'
            f'<div>Grown-up tip: watch the pencil grip, not the speed.</div></div></div>')


def letter_page(ch, name, grad, case="both"):
    low = ch.lower()
    word = LETTER_WORDS.get(ch, "")
    parts = [head(f"Letter {ch}{low}", "Trace, then write on your own",
                  f"{ch} {low}", grad), meta_row(name)]
    if case in ("both", "upper"):
        parts += [label(f"1. Trace the big {ch}", "start on the green dot"),
                  rule_row(ch, fs=94, count=6, models=1),
                  rule_row(ch, fs=94, count=6, models=0)]
    if case in ("both", "lower"):
        parts += [label(f"2. Trace the small {low}"),
                  rule_row(low, fs=94, count=6, models=1),
                  rule_row(low, fs=94, count=6, models=0)]
    # one free-hand row only: a second row overflows the letter page onto page 2
    parts += [label("3. Now write them yourself", "as many as you can"),
              rule_row("", count=0)]
    if word:
        parts += [label(f"4. {ch} is for {word} &mdash; trace the word"),
                  word_row(word)]
        parts.append(f'<div class="draw">Draw something that starts with '
                     f'<b>{ch}{low}</b>:</div>')
    parts.append('<div class="foot"><div>Handwriting Practice &middot; print on A4</div>'
                 '<div>Grown-up tip: watch the pencil grip, not the speed.</div></div>')
    return f'<div class="page">{"".join(parts)}</div>'


def number_page(n, name, grad):
    word = NUMBER_WORDS[n] if n < len(NUMBER_WORDS) else str(n)
    d = str(n)
    parts = [head(f"Number {d}", "Trace, then write on your own", d, grad),
             meta_row(name),
             label(f"1. Trace the number {d}", "start on the green dot"),
             rule_row(d, fs=94, count=6, models=1),
             rule_row(d, fs=94, count=6, models=0),
             label("2. Now write it yourself", "fill the line"),
             rule_row("", count=0),
             rule_row("", count=0),
             label(f"3. Trace the word &ldquo;{word}&rdquo;"),
             word_row(word)]
    if n == 0:
        counting = ('<div class="countrow"><div class="dots">'
                    '<span style="font-size:13px;color:#7a7a94">nothing to count &mdash; '
                    'zero means none!</span></div>'
                    '<div class="box"></div><div class="box"></div></div>')
    else:
        dots = "".join('<div class="dot"></div>' for _ in range(n))
        counting = (f'<div class="countrow"><div class="dots">{dots}</div>'
                    '<div class="box"></div><div class="box"></div></div>')
    parts.append(f'<div class="card">{label("4. Count the dots and write the number")}'
                 f'{counting}</div>')
    parts.append('<div class="foot"><div>Handwriting Practice &middot; print on A4</div>'
                 '<div>Grown-up tip: say the number out loud while writing it.</div></div>')
    return f'<div class="page">{"".join(parts)}</div>'


def review_letters_page(chars, name, grad, title):
    parts = [head(title, "Free-hand writing &mdash; no tracing", "abc", grad),
             meta_row(name),
             label("Write each letter twice: big, then small",
                   "look at the model, then write on the empty line")]
    for ch in chars:
        parts.append(rule_row(f"{ch}{ch.lower()}", fs=66, count=1, models=1))
    parts.append('<div class="foot"><div>Handwriting Practice &middot; print on A4</div>'
                 '<div>Grown-up tip: two neat letters beat ten rushed ones.</div></div>')
    return f'<div class="page">{"".join(parts)}</div>'


def review_numbers_page(numbers, name, grad):
    parts = [head("Numbers review", "Free-hand writing &mdash; no tracing", "123", grad),
             meta_row(name),
             label("Write each number on the empty line", "count out loud as you go")]
    for n in numbers:
        parts.append(rule_row(str(n), fs=66, count=1, models=1))
    parts.append('<div class="foot"><div>Handwriting Practice &middot; print on A4</div>'
                 '<div>Grown-up tip: numbers all start at the top line.</div></div>')
    return f'<div class="page">{"".join(parts)}</div>'


GRID_CONTENTS = f"""<ul>
<li><b>{GRID_COLS} &times; {GRID_ROWS} = {GRID_COLS * GRID_ROWS} characters a page</b>
&mdash; capitals first, then small letters, then the digits.</li>
<li><b>Each box</b> has a big grey letter to trace, a dashed copy beside it, and an
empty ruled line underneath to write it free-hand.</li>
</ul>"""

PAGE_CONTENTS = """<ul>
<li><b>One page per letter</b> &mdash; big capital and small letter: a grey model to
copy, dashed outlines to trace, an empty line to write on your own, the key word
to trace, and a box to draw in.</li>
<li><b>One page per number</b> &mdash; trace, write free-hand, trace the number word,
then count the dots and write the number.</li>
<li><b>Review pages</b> at the end &mdash; free-hand only, no tracing.</li>
</ul>"""


def cover_page(name, letters, numbers, layout="grid"):
    who = f" for {escape(name)}" if name else ""
    az = " ".join(letters) if letters else "&mdash;"
    nums = " ".join(str(n) for n in numbers) if numbers else "&mdash;"
    return f"""<div class="page cover">
{head(f"Handwriting Practice{who}", "Big letters and numbers &middot; trace and free-hand",
      "A1", GRADS[0])}
<div class="card"><h2>What is in this set</h2>
{GRID_CONTENTS if layout == "grid" else PAGE_CONTENTS}</div>
<div class="card"><h2>How to use it</h2>
<ul>
<li>One page a day is plenty &mdash; about 10&ndash;15 minutes.</li>
<li>Start every letter on the <b>green dot</b> and finish on the blue baseline.</li>
<li>Tall letters touch the top line; small letters stop at the dashed line;
letters like <b>g</b>, <b>p</b>, <b>y</b> hang below the baseline.</li>
<li>Trace with a pencil first, then try the empty line. Print extra copies of any
page that is still wobbly.</li>
<li>A4 with an 18&nbsp;mm left margin &mdash; punches cleanly into a ring binder.</li>
</ul></div>
<div class="card"><h2>In this set</h2>
<div class="strip">Letters: {az}<br>Numbers: {nums}</div></div>
<div class="foot"><div>Handwriting Practice &middot; print on A4, single-sided</div>
<div>Made at home &middot; reprint any page as often as you like.</div></div>
</div>"""


def parse_letters(spec):
    if not spec or spec.lower() in ("none", ""):
        return []
    out = []
    for part in spec.split(","):
        part = part.strip().upper()
        if not part:
            continue
        if "-" in part and len(part) == 3:
            a, b = part.split("-")
            out += [chr(c) for c in range(ord(a), ord(b) + 1)]
        else:
            out += list(part)
    seen, uniq = set(), []
    for ch in out:
        if ch.isalpha() and ch not in seen:
            seen.add(ch)
            uniq.append(ch)
    return uniq


def parse_numbers(spec):
    if not spec or spec.lower() in ("none", ""):
        return []
    out = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-")
            out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    seen, uniq = set(), []
    for n in out:
        if 0 <= n <= 12 and n not in seen:
            seen.add(n)
            uniq.append(n)
    return uniq


def characters(letters, numbers, case):
    """Flat practice sequence for grid mode: capitals, then small letters, then
    digits. 26 + 26 + 10 = 62 characters -> 6 pages of 12."""
    chars = []
    if case in ("both", "upper"):
        chars += letters
    if case in ("both", "lower"):
        chars += [ch.lower() for ch in letters]
    chars += [str(n) for n in numbers]
    return chars


def _wrap(pages):
    return (f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
            f"<style>{CSS}</style></head><body>{''.join(pages)}</body></html>")


def build_html(name, letters, numbers, case, cover, review, layout="grid",
               chars=None):
    """Return (html, expected_page_count). One worksheet == exactly one A4 page,
    so the caller can assert the rendered page count and catch any overflow."""
    pages = []
    if cover:
        pages.append(cover_page(name, letters, numbers, layout))

    if layout == "tricky":
        per_page = TRICKY_COLS * TRICKY_ROWS
        chunks = [chars[i:i + per_page] for i in range(0, len(chars), per_page)]
        for i, chunk in enumerate(chunks):
            pages.append(tricky_page(chunk, name, GRADS[i % len(GRADS)],
                                     i + 1, len(chunks)))
        return _wrap(pages), len(pages)

    if layout == "grid":
        chars = characters(letters, numbers, case)
        per_page = GRID_COLS * GRID_ROWS
        chunks = [chars[i:i + per_page] for i in range(0, len(chars), per_page)]
        for i, chunk in enumerate(chunks):
            pages.append(grid_page(chunk, name, GRADS[i % len(GRADS)],
                                   i + 1, len(chunks)))
        return _wrap(pages), len(pages)

    for i, ch in enumerate(letters):
        pages.append(letter_page(ch, name, GRADS[i % len(GRADS)], case))
    for i, n in enumerate(numbers):
        pages.append(number_page(n, name, GRADS[(i + 3) % len(GRADS)]))
    if review:
        for i in range(0, len(letters), 9):
            chunk = letters[i:i + 9]
            title = f"Letters {chunk[0]}&ndash;{chunk[-1]} review"
            pages.append(review_letters_page(chunk, name, GRADS[i % len(GRADS)], title))
        for i in range(0, len(numbers), 9):
            pages.append(review_numbers_page(numbers[i:i + 9], name,
                                            GRADS[(i + 2) % len(GRADS)]))
    return _wrap(pages), len(pages)


def main():
    p = argparse.ArgumentParser(description="Generate an A4 handwriting-practice PDF set.")
    p.add_argument("--out", required=True, help="output PDF path")
    p.add_argument("--name", default="", help="child's name for the header (optional)")
    p.add_argument("--letters", default="A-Z", help="letters to cover, e.g. 'A-Z', 'A-F,S,T', 'none'")
    p.add_argument("--numbers", default="0-9", help="numbers to cover, e.g. '0-9', '1-10', 'none'")
    p.add_argument("--case", default="both", choices=["both", "upper", "lower"],
                   help="practise capitals, small letters, or both (default both)")
    p.add_argument("--layout", default="grid", choices=["grid", "page", "tricky"],
                   help="grid: 12 characters a page in a 3x4 grid (default); "
                        "page: one full page per letter and per number; "
                        "tricky: 4 reversal-prone characters a page with stroke cues")
    p.add_argument("--chars", default=TRICKY_DEFAULT,
                   help="comma list of characters for --layout tricky "
                        f"(default '{TRICKY_DEFAULT}')")
    p.add_argument("--cover", action="store_true",
                   help="add a parent cover page in front (grid layout omits it by default)")
    p.add_argument("--no-cover", action="store_true",
                   help="skip the parent cover page (page layout includes it by default)")
    p.add_argument("--no-review", action="store_true",
                   help="skip the free-hand review pages (page layout only)")
    p.add_argument("--split", action="store_true",
                   help="also write one PDF per page next to --out")
    args = p.parse_args()

    letters, numbers = parse_letters(args.letters), parse_numbers(args.numbers)
    tricky = [c.strip() for c in args.chars.split(",") if c.strip()]
    if args.layout == "tricky":
        if not tricky:
            sys.exit("nothing to generate: --chars is empty")
    elif not letters and not numbers:
        sys.exit("nothing to generate: --letters and --numbers are both empty")

    try:
        from weasyprint import HTML
    except ModuleNotFoundError:
        sys.exit("weasyprint is not installed. Re-run as `uv run handwriting.py ...` "
                 "(resolves dependencies automatically), or install it first.")

    # grid layout is a compact set, so the cover is opt-in; page layout ships it
    # by default and --no-cover removes it
    cover = args.cover if args.layout in ("grid", "tricky") else not args.no_cover
    html, expected = build_html(args.name, letters, numbers, args.case, cover,
                                not args.no_review, args.layout, tricky)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    doc = HTML(string=html, base_url=".").render()
    doc.write_pdf(args.out)
    if args.layout == "tricky":
        print(f"wrote {args.out} ({len(doc.pages)} pages, tricky layout: "
              f"{len(tricky)} characters - {' '.join(tricky)})")
    else:
        n_chars = len(characters(letters, numbers, args.case))
        print(f"wrote {args.out} ({len(doc.pages)} pages, {args.layout} layout: "
              f"{len(letters)} letters, {len(numbers)} numbers"
              f"{f', {n_chars} characters' if args.layout == 'grid' else ''})")
    if len(doc.pages) != expected:
        print(f"WARNING: {len(doc.pages) - expected} worksheet(s) overflowed onto a "
              f"second page (expected {expected} pages). Trim a row or reduce the "
              f"glyph size before printing.", file=sys.stderr)

    if args.split:
        root, ext = os.path.splitext(args.out)
        for i, page in enumerate(doc.pages, 1):
            out = f"{root} p{i:02d}{ext or '.pdf'}"
            doc.copy([page]).write_pdf(out)
        print(f"wrote {len(doc.pages)} single-page PDFs next to {args.out}")


if __name__ == "__main__":
    main()
