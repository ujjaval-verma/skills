"""Activity builders. Each returns a dict: {title, hint, body, key}.

`key` is the short parent answer-key fragment shown in the footer. Builders take
(level, theme, rng, ctx) so content varies per worksheet while staying on-theme
and at the right difficulty. Difficulty scales explicitly by `level`.

`ctx` is a per-pack variety context (see Ctx). It carries the rotation hints a
pack planner sets per sheet (which vowels / pattern shape / activity variant /
scene to feature) and an exclusion set so a multi-sheet pack avoids repeating the
same words, icons, and scenes. `ctx` is optional: every builder works standalone
with ctx=None, falling back to plain random choice.

Escaping rule: theme-derived text (letter words, CVC words, icon names, legend
names) is escape()d at the point it is interpolated into HTML. Literal strings
authored in this file may embed entities (&amp;, &middot;) deliberately and are
never escaped.
"""
from html import escape

from icons import (icon, SCENES, maze_svg, trail_svg,
                   CVC_BY_VOWEL, VOWELS, ICON_NAME)


# ---------------------------------------------------------- variety context --
PATTERN_VARIANTS = ["AAB", "ABB", "ABC"]
MATH_VARIANTS = ["addition", "subitize"]
LITERACY_VARIANTS = ["word", "sound"]


class Ctx:
    """Cross-sheet variety state. One Ctx is shared across a pack; a planner sets
    the per-sheet rotation hints before each sheet's builders run, and `used`
    accumulates tokens already shown so the pack avoids repeats."""

    def __init__(self):
        self.used = set()            # words / icons / scenes already shown
        self.vowel_order = None      # preferred vowel order for word_build
        self.pattern_variant = None  # one of PATTERN_VARIANTS
        self.math_variant = None     # one of MATH_VARIANTS
        self.literacy_variant = None # one of LITERACY_VARIANTS
        self.scene_name = None       # colour-scene to feature

    def take_unused(self, options, rng, key=lambda o: o):
        """Pick an option whose key has not been used yet (else any), mark used."""
        fresh = [o for o in options if key(o) not in self.used]
        pick = rng.choice(fresh if fresh else options)
        self.used.add(key(pick))
        return pick


def plan_sheet(ctx, theme, rng, sheet_idx=None):
    """Set per-sheet rotation hints on `ctx`.

    sheet_idx None  -> single sheet: randomise hints so each seed varies.
    sheet_idx int   -> pack member: rotate deterministically so N sheets *cover*
                       the vowels / pattern shapes / variants / scenes instead of
                       repeating them.
    """
    if sheet_idx is None:
        ctx.pattern_variant = rng.choice(PATTERN_VARIANTS)
        ctx.math_variant = rng.choice(MATH_VARIANTS)
        ctx.literacy_variant = rng.choice(LITERACY_VARIANTS)
        ctx.vowel_order = rng.sample(VOWELS, len(VOWELS))
        ctx.scene_name = rng.choice(theme["scenes"])
    else:
        ctx.pattern_variant = PATTERN_VARIANTS[sheet_idx % len(PATTERN_VARIANTS)]
        ctx.math_variant = MATH_VARIANTS[sheet_idx % len(MATH_VARIANTS)]
        ctx.literacy_variant = LITERACY_VARIANTS[sheet_idx % len(LITERACY_VARIANTS)]
        s = (sheet_idx * 3) % len(VOWELS)
        ctx.vowel_order = VOWELS[s:] + VOWELS[:s]
        ctx.scene_name = theme["scenes"][sheet_idx % len(theme["scenes"])]


# --------------------------------------------------------------- helpers -----
def _groups(name, n):
    return "".join(icon(name, 32) for _ in range(n))


def _ten_frame(n, color):
    """A 2x5 ten-frame with the first `n` cells filled — supports subitizing."""
    cell = 22
    w, h = 5 * cell, 2 * cell
    rects = "".join(
        f'<rect x="{c * cell}" y="{r * cell}" width="{cell}" height="{cell}" '
        f'fill="none" stroke="#b8b8c8" stroke-width="1.5"/>'
        for r in range(2) for c in range(5))
    dots = ""
    for i in range(n):
        r, c = divmod(i, 5)
        dots += (f'<circle cx="{c * cell + cell // 2}" cy="{r * cell + cell // 2}" '
                 f'r="{cell * 0.34:.0f}" fill="{escape(color)}"/>')
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'style="vertical-align:middle">{rects}{dots}</svg>')


# ---------------------------------------------------------------- math -------
def count_and_write(level, theme, rng, ctx=None):
    lo, hi = 1, 5  # only routed at level 1; levels 2-3 math use addition/subitize
    picks = rng.sample(theme["icons"], 3)
    counts = []
    while len(counts) < 3:
        c = rng.randint(lo, hi)
        if c not in counts:
            counts.append(c)
    rows, ans = [], []
    for name, c in zip(picks, counts):
        ans.append(str(c))
        rows.append(
            f'<div class="countrow"><div class="objs">{_groups(name, c)}</div>'
            f'<div class="trace-num">{c}</div><div class="answerbox"></div></div>')
    return {"title": "Count &amp; Write", "hint": "Count, trace the number, write it in the box.",
            "body": "".join(rows), "key": ", ".join(ans)}


def addition(level, theme, rng, ctx=None):
    maxsum = 10 if level == 2 else 20
    name = rng.choice(theme["icons"])
    probs, ans = [], []
    used = set()
    while len(probs) < 3:
        a = rng.randint(1, min(6, maxsum - 1))
        b = rng.randint(1, maxsum - a)
        if (a, b) in used:
            continue
        used.add((a, b))
        ans.append(str(a + b))
        if level == 2:
            probs.append(
                f'<div class="sum"><div class="grp">{_groups(name, a)}</div><div class="op">+</div>'
                f'<div class="grp">{_groups(name, b)}</div><div class="eq">=</div><div class="sumbox"></div>'
                f'<div class="ns">{a} + {b} = ___</div></div>')
        else:
            probs.append(
                f'<div class="sum big3"><span class="bigq">{a} + {b} =</span><div class="sumbox"></div></div>')
    hint = ("Count both groups. Write how many in all." if level == 2
            else "Solve each sum and write the answer.")
    return {"title": "Adding Fun", "hint": hint, "body": "".join(probs), "key": ", ".join(ans)}


def subitize(level, theme, rng, ctx=None):
    """Ten-frame 'how many?' — builds number sense and cardinality, anchoring
    quantities against ten (DREME). Small frames also support subitizing."""
    color = theme["accent"]
    lo = 3 if level == 2 else 6
    counts = []
    while len(counts) < 3:
        c = rng.randint(lo, 10)
        if c not in counts:
            counts.append(c)
    rows = [f'<div style="display:flex;align-items:center;gap:18px;margin:5px 0">'
            f'<div>{_ten_frame(c, color)}</div><div class="answerbox"></div></div>'
            for c in counts]
    return {"title": "Ten-Frame Count", "hint": "How many dots? Write the number in the box.",
            "body": "".join(rows), "key": ", ".join(str(c) for c in counts)}


def math_activity(level, theme, rng, ctx=None):
    if level == 1:
        return count_and_write(level, theme, rng, ctx)
    if level >= 3:                       # L3 stays abstract addition within 20
        return addition(level, theme, rng, ctx)
    variant = (ctx.math_variant if ctx and ctx.math_variant else rng.choice(MATH_VARIANTS))
    return (subitize if variant == "subitize" else addition)(level, theme, rng, ctx)


# -------------------------------------------------------------- literacy -----
def letter_trace(level, theme, rng, ctx=None):
    cap, word, ic = rng.choice(theme["letter"])
    low = escape(cap.lower())  # transform raw value first, escape last
    cap, word = escape(cap), escape(word)
    body = (
        f'<div class="lettercap">{icon(ic, 46)}'
        f'<div class="word">Say the sound: <b>/{low}/</b> &middot; <b>{low}</b>&ndash;{word.lower()[1:]}</div></div>'
        f'<div class="traceline">{cap}&nbsp;{cap}&nbsp;{cap}&nbsp;{cap}</div>'
        f'<div class="traceline">{low}&nbsp;{low}&nbsp;{low}&nbsp;{low}</div>')
    return {"title": f"Letter of the Day: {cap} is for {word}", "hint": "Trace the grey letters with your pencil.",
            "body": body, "key": f"trace {cap}{low}"}


def word_build(level, theme, rng, ctx=None):
    order = (ctx.vowel_order if ctx and ctx.vowel_order else rng.sample(VOWELS, len(VOWELS)))
    cards, ans = [], []
    for v in order[:3]:
        opts = CVC_BY_VOWEL[v]
        word, ic = (ctx.take_unused(opts, rng, key=lambda o: o[0]) if ctx else rng.choice(opts))
        if level == 2:  # blank the middle vowel
            lbl = f'{escape(word[0])}<span class="blank">&nbsp;</span>{escape(word[2])}'
            ans.append(escape(v.upper()))  # card shows uppercase letters, key matches
        else:           # level 3: spell the whole word
            lbl = '<span class="blank">&nbsp;</span>' * 3
            ans.append(escape(word.lower()))
        cards.append(f'<div class="wcard">{icon(ic, 46)}<div class="lbl">{lbl}</div></div>')
    hint = ("Say the picture. Write the missing middle letter." if level == 2
            else "Say the picture. Spell the whole word.")
    return {"title": "Finish the Word", "hint": hint,
            "body": f'<div class="words">{"".join(cards)}</div>', "key": ", ".join(ans)}


# Icons whose spoken name is outside a typical 4-7 vocabulary — fine as a maze
# or counting object, but not as the *target* of a "say the picture" sound task
# (they can still appear as distractors).
SOUND_HARD_TARGETS = {"satellite"}


def initial_sound(level, theme, rng, ctx=None):
    """Circle the picture that begins with a target sound — initial-phoneme
    awareness (FCRR phonics strand)."""
    icons = theme["icons"]
    namable = [i for i in icons if i not in SOUND_HARD_TARGETS] or icons
    target = ctx.take_unused(namable, rng) if ctx else rng.choice(namable)
    letter = ICON_NAME[target][0].upper()
    pool = [i for i in icons if i != target and ICON_NAME[i][0].upper() != letter]
    distractors = rng.sample(pool, 3) if len(pool) >= 3 else pool
    shown = [target] + distractors
    rng.shuffle(shown)
    cells = "".join(f'<div class="oddbox">{icon(ic, 40)}</div>' for ic in shown)
    low = escape(letter.lower())
    body = (f'<div class="lettercap"><div class="word">Find the picture that starts with '
            f'<b>{escape(letter)}</b> &middot; the <b>/{low}/</b> sound</div></div>'
            f'<div class="oddrow">{cells}</div>')
    return {"title": "Sound Search", "hint": "Circle the one that begins with the sound.",
            "body": body, "key": f"{escape(letter)} = {escape(ICON_NAME[target])}"}


def literacy_activity(level, theme, rng, ctx=None):
    if level == 1:
        return letter_trace(level, theme, rng, ctx)
    if level >= 3:                       # L3 stays whole-word spelling
        return word_build(level, theme, rng, ctx)
    variant = (ctx.literacy_variant if ctx and ctx.literacy_variant else rng.choice(LITERACY_VARIANTS))
    return (initial_sound if variant == "sound" else word_build)(level, theme, rng, ctx)


# -------------------------------------------------------------- patterns -----
def pattern(level, theme, rng, ctx=None):
    if level == 1:                       # AB, one blank
        a, b = rng.sample(theme["icons"], 2)
        seq = [a, b, a, b, a]
        cells = "".join(f'<span>{icon(s, 30)}</span>' for s in seq)
        return {"title": "Pattern Power", "hint": "Look at the pattern. Draw what comes next.",
                "body": f'<div class="pat">{cells}<div class="qbox"></div></div>', "key": escape(b)}
    if level >= 3:                       # growing pattern 1,2,3,_ on a single row
        a = rng.choice(theme["icons"])
        cells = "".join(
            f'{_groups(a, n)}<span class="op2">&rarr;</span>' for n in (1, 2, 3))
        return {"title": "Pattern Power", "hint": "The groups grow by one. Draw the next group.",
                "body": f'<div class="pat">{cells}<div class="qbox"></div></div>', "key": "4"}
    # level 2: repeating pattern, two blanks, shape chosen by variant
    variant = (ctx.pattern_variant if ctx and ctx.pattern_variant else rng.choice(PATTERN_VARIANTS))
    a, b, c = rng.sample(theme["icons"], 3)
    unit = {"AAB": [a, a, b], "ABB": [a, b, b], "ABC": [a, b, c]}[variant]
    seq = unit * 2
    nxt = unit[:2]                       # the next two elements continue the repeat
    cells = "".join(f'<span>{icon(s, 30)}</span>' for s in seq)
    qb = '<div class="qbox"></div>' * 2
    keytxt = "+".join(escape(x) for x in nxt)
    return {"title": "Pattern Power", "hint": "This pattern repeats. Draw the next TWO.",
            "body": f'<div class="pat">{cells}{qb}</div>', "key": keytxt}


# --------------------------------------------------- problem solving / maze --
def maze(level, theme, rng, ctx=None):
    icons = theme["icons"]
    start, end = icons[0], icons[-1]
    seed = rng.randint(1, 9999)
    if level == 1:
        body = trail_svg(start, end)
        hint = "Draw a line on the trail from start to finish."
    else:
        cols, rows, cell = (7, 5, 30) if level == 2 else (14, 10, 30)
        body = maze_svg(cols, rows, cell, seed, start, end)
        hint = "Draw a path from start to finish. Watch for dead ends!"
    return {"title": "Find the Path", "hint": hint,
            "body": f'<div style="text-align:center">{body}</div>', "key": "maze"}


# ----------------------------------------------------------------- arts ------
def colour_scene(level, theme, rng, ctx=None):
    # Scene rotation is owned by plan_sheet (deterministic per sheet); we must NOT
    # add the scene name to ctx.used, or a scene that shares a name with an icon
    # (e.g. "rocket"/"star"/"fish") would be excluded from later sound/sort tasks.
    scene_name = ctx.scene_name if ctx and ctx.scene_name else rng.choice(theme["scenes"])
    svg, legend, colors = SCENES[scene_name]()
    names = legend.split()
    chips = "".join(
        f'<div class="sw"><span class="chip" style="background:{escape(c)}"></span>{escape(n)}</div>'
        for c, n in zip(colors, names))
    body = f'<div class="legend">{chips}</div><div style="text-align:center">{svg}</div>'
    return {"title": "Colour by Number", "hint": "Colour each part using the key.", "body": body, "key": None}


# --------------------------------------------------------------- science -----
def odd_one_out(level, theme, rng, ctx=None):
    same = rng.choice(theme["icons"])
    diff = rng.choice([i for i in theme["icons"] if i != same])
    n = 4 if level == 1 else 5
    odd = rng.randint(0, n - 1)
    cells = "".join(
        f'<div class="oddbox">{icon(diff if i == odd else same, 40)}</div>' for i in range(n))
    return {"title": "Which One is Different?", "hint": "Circle the one that does not belong.",
            "body": f'<div class="oddrow">{cells}</div>', "key": f"#{odd + 1}"}


# topic -> builder. math/literacy dispatch to a level/variant-specific builder
# internally (see math_activity / literacy_activity).
def builder_for(topic, level):
    table = {
        "math": math_activity,
        "literacy": literacy_activity,
        "patterns": pattern,
        "problemsolving": maze,
        "arts": colour_scene,
        "science": odd_one_out,
    }
    return table.get(topic)


TOPIC_ALIASES = {
    "math": "math", "maths": "math", "number": "math", "counting": "math", "addition": "math",
    "literacy": "literacy", "writing": "literacy", "reading": "literacy", "phonics": "literacy", "words": "literacy",
    "patterns": "patterns", "pattern": "patterns", "logic": "patterns",
    "problemsolving": "problemsolving", "maze": "problemsolving", "problem-solving": "problemsolving",
    "arts": "arts", "art": "arts", "colour": "arts", "coloring": "arts", "colouring": "arts",
    "science": "science", "sorting": "science", "observation": "science",
}
