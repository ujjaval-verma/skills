#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["weasyprint"]
# ///
"""Generate a print-ready, full-colour A4 STEAM worksheet PDF for early learners.

Usage:
  uv run generate.py --out PATH.pdf --level 2 --theme space \
      --topics math,literacy,patterns,problemsolving --name Asha --seed 7

All flags are optional except --out. Sensible defaults produce a balanced sheet.
Run with --help for details. `uv run` resolves weasyprint automatically (PEP 723
inline metadata); with plain python3, weasyprint must already be installed.
"""
import argparse, os, random, sys
from html import escape
from string import Template

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from icons import THEMES                                    # noqa: E402
import activities as A                                      # noqa: E402

CSS = """
@page { size: A4; margin: 12mm 12mm 12mm 18mm; }
* { box-sizing: border-box; }
html, body { margin:0; padding:0; }
body { font-family:"Noto Sans","DejaVu Sans",sans-serif; color:#2b2d42; }
.head { display:flex; align-items:center; justify-content:space-between;
  background:linear-gradient(90deg,$grad1,$grad2); color:#fff; border-radius:14px; padding:8px 14px; }
.head h1 { margin:0; font-size:20px; line-height:1.15; }
.head .sub { font-size:12px; opacity:.92; margin-top:2px; }
.head .badge { font-size:11px; background:rgba(255,255,255,.22); padding:5px 11px; border-radius:20px; font-weight:700; }
.meta { display:flex; gap:18px; margin:7px 2px 3px; font-size:12.5px; color:#555; }
.meta .line { flex:1; border-bottom:2px dotted #b8b8c8; padding-bottom:2px; }
.act { border:2px solid #eceaf3; border-radius:14px; padding:8px 12px 9px; margin-top:8px; page-break-inside:avoid; }
.act .t { display:flex; align-items:center; gap:8px; margin-bottom:5px; }
.act .num { width:24px; height:24px; border-radius:50%; background:$accent; color:#fff; font-weight:700;
  font-size:14px; display:flex; align-items:center; justify-content:center; flex:none; }
.act .ttl { font-size:15.5px; font-weight:700; color:$title_accent; }
.act .hint { font-size:11.5px; color:#777; }
.ico { vertical-align:middle; }
.countrow { display:flex; align-items:center; gap:14px; margin:4px 0; }
.objs { flex:1; display:flex; align-items:center; gap:9px; flex-wrap:wrap; }
.trace-num { font-size:34px; line-height:1; font-weight:700; color:#dadae3; width:40px; text-align:center; }
.answerbox { width:40px; height:40px; border:2.5px solid #4361ee; border-radius:10px; flex:none; }
.traceline { font-size:36px; line-height:1.15; font-weight:700; color:#dedee7; letter-spacing:18px; margin:3px 0 0 4px; }
.lettercap { display:flex; align-items:center; gap:16px; }
.lettercap .word { font-size:14px; color:#555; }
.sum { display:flex; align-items:center; gap:10px; margin:7px 0; }
.grp { display:flex; gap:3px; }
.op,.eq { font-size:26px; font-weight:700; color:$title_accent; }
.op2 { font-size:26px; color:$title_accent; margin-left:6px; }
.sumbox { width:44px; height:44px; border:2.5px solid #4361ee; border-radius:10px; flex:none; }
.ns { margin-left:12px; font-size:18px; color:#b6b6c2; letter-spacing:1px; }
.big3 .bigq { font-size:30px; font-weight:700; color:#2b2d42; }
.words { display:flex; gap:24px; flex-wrap:wrap; margin-top:6px; align-items:flex-end; }
.wcard { text-align:center; }
.wcard .lbl { font-size:30px; font-weight:700; letter-spacing:10px; color:#2b2d42; margin-top:4px; }
.wcard .blank { display:inline-block; width:24px; border-bottom:3px solid $accent; }
.pat { display:flex; align-items:center; gap:8px; font-size:24px; margin:5px 0; flex-wrap:wrap; }
.pat .qbox { width:46px; height:46px; border:2.5px dashed $accent; border-radius:10px; flex:none; }
.oddrow { display:flex; gap:14px; margin-top:4px; }
.oddbox { width:56px; height:56px; border:2px solid #d7d7e2; border-radius:12px; display:flex;
  align-items:center; justify-content:center; }
.legend { display:flex; gap:14px; margin:5px 0 6px; font-size:12.5px; flex-wrap:wrap; }
.sw { display:flex; align-items:center; gap:6px; }
.chip { width:18px; height:18px; border-radius:5px; border:1px solid #999; }
.foot { margin-top:9px; display:flex; justify-content:space-between; align-items:center; font-size:11px; color:#888; gap:10px; }
.key { background:#fbf6ff; border:1px dashed #d9a7e0; border-radius:10px; padding:5px 10px; color:#8a4a93; }
"""

DEFAULT_TOPICS = ["math", "literacy", "patterns", "problemsolving"]


def build_html(level, theme_name, topics, name, seed, n_acts):
    rng = random.Random(seed)
    theme = THEMES[theme_name]
    # resolve & expand topics to the requested number of activities
    chosen = [A.TOPIC_ALIASES.get(t.strip().lower()) for t in topics if t.strip()]
    chosen = [t for t in chosen if t]
    if not chosen:
        chosen = list(DEFAULT_TOPICS)
    pool = DEFAULT_TOPICS + ["arts", "science"]
    # fill up to n_acts from the pool without duplicating activity types
    for cand in pool:
        if len(chosen) >= n_acts:
            break
        if cand not in chosen:
            chosen.append(cand)
    chosen = chosen[:n_acts]

    blocks, keys = [], []
    for idx, topic in enumerate(chosen, 1):
        fn = A.builder_for(topic, level)
        if fn is None:
            continue
        r = fn(level, theme, rng)
        blocks.append(
            f'<div class="act"><div class="t"><div class="num">{idx}</div>'
            f'<div class="ttl">{r["title"]}</div><div class="hint">&nbsp;{r["hint"]}</div></div>'
            f'{r["body"]}</div>')
        if r.get("key"):
            keys.append(f'{idx}) {r["key"]}')

    title_word = escape(theme["word"])  # theme data; child name is escaped below
    if name:
        title = f"{escape(name)}&rsquo;s {title_word} Worksheet"
    else:
        title = f"{title_word} Worksheet"
    from icons import icon
    head_icon = icon(theme["emoji_icon"], 22)
    badge = f"Level {level}"
    # builder keys are pre-escaped (theme data) or ASCII-safe (ints/literals); not re-escaped here
    keytext = " &middot; ".join(keys) if keys else "see activities"

    css = Template(CSS).substitute(
        grad1=theme["grad"][0], grad2=theme["grad"][1],
        title_accent=theme["title_accent"], accent=theme["accent"])
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><style>{css}</style></head><body>
<div class="head"><div><h1>{head_icon} {title}</h1>
<div class="sub">STEAM Worksheet &middot; ~15 minutes</div></div>
<div class="badge">{badge}</div></div>
<div class="meta"><div class="line">Name:</div><div class="line">Date:</div>
<div class="line">Stars earned: &#9734; &#9734; &#9734;</div></div>
{''.join(blocks)}
<div class="foot"><div>&copy; Family STEAM Worksheets &middot; Print on A4</div>
<div class="key">Parent key: {keytext}</div></div>
</body></html>"""


def main():
    p = argparse.ArgumentParser(description="Generate an A4 STEAM worksheet PDF.")
    p.add_argument("--out", required=True, help="output PDF path")
    p.add_argument("--level", type=int, default=2, choices=[1, 2, 3])
    p.add_argument("--theme", default="space", choices=list(THEMES))
    p.add_argument("--topics", default=",".join(DEFAULT_TOPICS),
                   help="comma list: math,literacy,patterns,problemsolving,arts,science")
    p.add_argument("--activities", type=int, default=4, choices=[3, 4], help="number of activity blocks")
    p.add_argument("--name", default="", help="child's name for the title (optional)")
    p.add_argument("--seed", type=int, default=None, help="seed for reproducible content")
    args = p.parse_args()

    try:
        from weasyprint import HTML
    except ModuleNotFoundError:
        sys.exit("weasyprint is not installed. Re-run as `uv run generate.py ...` "
                 "(resolves dependencies automatically), or install it first "
                 "(`uv pip install weasyprint` / `pip install weasyprint`).")

    seed = args.seed if args.seed is not None else random.randint(1, 10 ** 6)
    html = build_html(args.level, args.theme,
                      args.topics.split(","), args.name, seed, args.activities)
    HTML(string=html, base_url=".").write_pdf(args.out)
    print(f"wrote {args.out} (level {args.level}, theme {args.theme}, seed {seed})")


if __name__ == "__main__":
    main()
