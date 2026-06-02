"""Activity builders. Each returns a dict: {title, hint, body, key}.

`key` is the short parent answer-key fragment shown in the footer. Builders take
(level, theme, rng) so content varies per worksheet while staying on-theme and
at the right difficulty. Difficulty scales explicitly by `level` so a future
Level 3 slots in without redesigning anything.
"""
from icons import icon, SCENES, maze_svg, trail_svg, CVC


def _groups(name, n):
    return "".join(icon(name, 32) for _ in range(n))


def count_and_write(level, theme, rng):
    lo, hi = 1, 5  # only routed at level 1; levels 2-3 math use addition()
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


def addition(level, theme, rng):
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


def letter_trace(level, theme, rng):
    cap, word, ic = rng.choice(theme["letter"])
    low = cap.lower()
    body = (
        f'<div class="lettercap">{icon(ic, 46)}'
        f'<div class="word">Say the sound: <b>/{low}/</b> &middot; <b>{low}</b>&ndash;{word.lower()[1:]}</div></div>'
        f'<div class="traceline">{cap}&nbsp;{cap}&nbsp;{cap}&nbsp;{cap}</div>'
        f'<div class="traceline">{low}&nbsp;{low}&nbsp;{low}&nbsp;{low}</div>')
    return {"title": f"Letter of the Day: {cap} is for {word}", "hint": "Trace the grey letters with your pencil.",
            "body": body, "key": f"trace {cap}{low}"}


def word_build(level, theme, rng):
    picks = rng.sample(CVC, 3)
    cards, ans = [], []
    for word, vowel, ic in picks:
        if level == 2:  # blank the middle vowel
            lbl = f'{word[0]}<span class="blank">&nbsp;</span>{word[2]}'
            ans.append(vowel.upper())  # card shows uppercase letters, key matches
        else:           # level 3: spell the whole word
            lbl = '<span class="blank">&nbsp;</span>' * 3
            ans.append(word.lower())
        cards.append(f'<div class="wcard">{icon(ic, 46)}<div class="lbl">{lbl}</div></div>')
    hint = ("Say the picture. Write the missing middle letter." if level == 2
            else "Say the picture. Spell the whole word.")
    return {"title": "Finish the Word", "hint": hint,
            "body": f'<div class="words">{"".join(cards)}</div>', "key": ", ".join(ans)}


def pattern(level, theme, rng):
    a, b = rng.sample(theme["icons"], 2)
    if level == 1:                       # AB, one blank
        seq = [a, b, a, b, a]
        blanks = 1
        keytxt = b
    elif level == 2:                     # AAB, two blanks
        seq = [a, a, b, a, a, b]
        blanks = 2
        keytxt = f"{a}+{a}"
    else:                                # growing pattern 1,2,3,_ on a single row
        cells = "".join(
            f'{_groups(a, n)}<span class="op2">&rarr;</span>' for n in (1, 2, 3))
        return {"title": "Pattern Power", "hint": "The groups grow by one. Draw the next group.",
                "body": f'<div class="pat">{cells}<div class="qbox"></div></div>', "key": "4"}
    cells = "".join(f'<span>{icon(s, 30)}</span>' for s in seq)
    qb = '<div class="qbox"></div>' * blanks
    hint = "Look at the pattern. Draw what comes next." if blanks == 1 else "This pattern repeats. Draw the next TWO."
    return {"title": "Pattern Power", "hint": hint, "body": f'<div class="pat">{cells}{qb}</div>', "key": keytxt}


def maze(level, theme, rng):
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


def colour_scene(level, theme, rng):
    svg, legend, colors = SCENES[theme["scene"]]()
    names = legend.split()
    chips = "".join(
        f'<div class="sw"><span class="chip" style="background:{c}"></span>{n}</div>'
        for c, n in zip(colors, names))
    body = f'<div class="legend">{chips}</div><div style="text-align:center">{svg}</div>'
    return {"title": "Colour by Number", "hint": "Colour each part using the key.", "body": body, "key": None}


def odd_one_out(level, theme, rng):
    same = rng.choice(theme["icons"])
    diff = rng.choice([i for i in theme["icons"] if i != same])
    n = 4 if level == 1 else 5
    odd = rng.randint(0, n - 1)
    cells = "".join(
        f'<div class="oddbox">{icon(diff if i == odd else same, 40)}</div>' for i in range(n))
    return {"title": "Which One is Different?", "hint": "Circle the one that does not belong.",
            "body": f'<div class="oddrow">{cells}</div>', "key": f"#{odd + 1}"}


# topic -> builder chosen by level
def builder_for(topic, level):
    table = {
        "math": count_and_write if level == 1 else addition,
        "literacy": letter_trace if level == 1 else word_build,
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
