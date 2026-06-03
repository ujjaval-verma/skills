"""SVG icon library, theme palettes, maze generator, and colour-scene builders.

Everything renders as inline SVG so worksheets print in full colour with no
dependency on an emoji font (the print sandbox has none). Each icon is a small
self-contained vector that scales cleanly on A4.
"""
import random

# ---------------------------------------------------------------- icons ------
# name -> (viewBox, inner_svg). Drawn once, reused at any size via icon().
_ICONS = {
    "star": ("0 0 24 24",
        '<path d="M12 2l2.6 6.3 6.8.5-5.2 4.4 1.7 6.6L12 16.8 6.1 20.3l1.7-6.6L2.6 8.8l6.8-.5z" fill="#ffd166" stroke="#f3a712"/>'),
    "moon": ("0 0 24 24",
        '<path d="M18 14A8 8 0 0 1 10 6a6 6 0 1 0 8 8z" fill="#cdb4db" stroke="#9b8bbf"/>'),
    "rocket": ("0 0 40 40",
        '<path d="M20 3 C26 9 27 20 24 28 H16 C13 20 14 9 20 3Z" fill="#e63946"/>'
        '<circle cx="20" cy="15" r="4" fill="#a8dadc" stroke="#1d3557"/>'
        '<path d="M16 24 L10 30 L16 28Z" fill="#f4a261"/><path d="M24 24 L30 30 L24 28Z" fill="#f4a261"/>'
        '<path d="M18 28 h4 l-1 6 h-2Z" fill="#ffb703"/>'),
    "planet": ("0 0 40 40",
        '<circle cx="20" cy="20" r="11" fill="#4cc9f0" stroke="#3a86ff"/>'
        '<ellipse cx="20" cy="20" rx="18" ry="5" fill="none" stroke="#ffb703" stroke-width="2.5" transform="rotate(-20 20 20)"/>'),
    "sun": ("0 0 50 50",
        '<g stroke="#f3a712" stroke-width="3" stroke-linecap="round">'
        '<line x1="25" y1="4" x2="25" y2="11"/><line x1="25" y1="39" x2="25" y2="46"/>'
        '<line x1="4" y1="25" x2="11" y2="25"/><line x1="39" y1="25" x2="46" y2="25"/>'
        '<line x1="10" y1="10" x2="15" y2="15"/><line x1="35" y1="35" x2="40" y2="40"/>'
        '<line x1="40" y1="10" x2="35" y2="15"/><line x1="15" y1="35" x2="10" y2="40"/></g>'
        '<circle cx="25" cy="25" r="11" fill="#ffd166" stroke="#f3a712" stroke-width="2"/>'),
    "cat": ("0 0 50 50",
        '<circle cx="25" cy="28" r="15" fill="#f4a261" stroke="#c97a3a" stroke-width="2"/>'
        '<path d="M12 17 L17 29 L24 21Z" fill="#f4a261" stroke="#c97a3a" stroke-width="2"/>'
        '<path d="M38 17 L33 29 L26 21Z" fill="#f4a261" stroke="#c97a3a" stroke-width="2"/>'
        '<circle cx="20" cy="27" r="2.2" fill="#000"/><circle cx="30" cy="27" r="2.2" fill="#000"/>'
        '<path d="M25 31 l-2.5 3 h5Z" fill="#e76f51"/>'
        '<g stroke="#000" stroke-width="1"><path d="M9 29 h8 M9 33 h8 M33 29 h8 M33 33 h8"/></g>'),
    "dog": ("0 0 50 50",
        '<circle cx="25" cy="28" r="14" fill="#c98a5e" stroke="#8a5a36" stroke-width="2"/>'
        '<ellipse cx="12" cy="26" rx="6" ry="10" fill="#a86c44" stroke="#8a5a36" stroke-width="2"/>'
        '<ellipse cx="38" cy="26" rx="6" ry="10" fill="#a86c44" stroke="#8a5a36" stroke-width="2"/>'
        '<circle cx="20" cy="27" r="2.2" fill="#000"/><circle cx="30" cy="27" r="2.2" fill="#000"/>'
        '<ellipse cx="25" cy="33" rx="3" ry="2.3" fill="#000"/>'),
    "pig": ("0 0 50 50",
        '<circle cx="25" cy="27" r="15" fill="#ff8fab" stroke="#e85d82" stroke-width="2"/>'
        '<path d="M15 15 q-3 -6 6 -4 l-2 8Z" fill="#ff8fab" stroke="#e85d82"/>'
        '<path d="M35 15 q3 -6 -6 -4 l2 8Z" fill="#ff8fab" stroke="#e85d82"/>'
        '<ellipse cx="25" cy="31" rx="8" ry="6" fill="#ffb3c6" stroke="#e85d82"/>'
        '<circle cx="22" cy="31" r="1.6" fill="#a3437a"/><circle cx="28" cy="31" r="1.6" fill="#a3437a"/>'
        '<circle cx="20" cy="23" r="1.8" fill="#000"/><circle cx="30" cy="23" r="1.8" fill="#000"/>'),
    "fish": ("0 0 50 40",
        '<path d="M8 20 C16 6 34 6 40 20 C34 34 16 34 8 20Z" fill="#4cc9f0" stroke="#3a86ff" stroke-width="2"/>'
        '<path d="M40 20 L48 12 L48 28Z" fill="#90e0ef" stroke="#3a86ff" stroke-width="2"/>'
        '<circle cx="18" cy="18" r="2.4" fill="#1d3557"/>'
        '<path d="M22 20 q6 6 12 0" fill="none" stroke="#1d3557" stroke-width="1.5"/>'),
    "elephant": ("0 0 70 56",
        '<ellipse cx="34" cy="30" rx="22" ry="16" fill="#9d8df1" stroke="#5a4fcf" stroke-width="2"/>'
        '<path d="M14 30 q-10 0 -12 14 q6 4 9 -2 q3 6 7 0" fill="#9d8df1" stroke="#5a4fcf" stroke-width="2"/>'
        '<circle cx="20" cy="24" r="3" fill="#2b2d42"/>'
        '<path d="M40 18 q14 -6 18 8 q4 10 -6 12" fill="#b8acff" stroke="#5a4fcf" stroke-width="2"/>'
        '<rect x="26" y="40" width="6" height="10" fill="#9d8df1" stroke="#5a4fcf"/>'
        '<rect x="40" y="40" width="6" height="10" fill="#9d8df1" stroke="#5a4fcf"/>'
        '<path d="M30 22 q8 -3 14 1" fill="none" stroke="#ffd166" stroke-width="3"/>'),
    "peacock": ("0 0 50 52",
        '<path d="M25 30 C5 22 6 4 25 6 C44 4 45 22 25 30Z" fill="#2a9d8f" opacity=".5"/>'
        '<circle cx="15" cy="14" r="3" fill="#e76f51"/><circle cx="25" cy="9" r="3" fill="#e76f51"/><circle cx="35" cy="14" r="3" fill="#e76f51"/>'
        '<ellipse cx="25" cy="34" rx="6" ry="9" fill="#1d3557"/>'
        '<circle cx="25" cy="24" r="5" fill="#118ab2"/>'
        '<path d="M25 20 l0 -6" stroke="#1d3557" stroke-width="2"/><circle cx="25" cy="13" r="2" fill="#06d6a0"/>'),
    "lotus": ("0 0 44 44",
        '<path d="M22 38 C10 34 8 22 22 12 C36 22 34 34 22 38Z" fill="#ff8fab"/>'
        '<path d="M22 38 C16 30 16 20 22 10 C28 20 28 30 22 38Z" fill="#ffb3c6"/>'
        '<path d="M6 30 q4 -10 16 8Z" fill="#ff7096"/><path d="M38 30 q-4 -10 -16 8Z" fill="#ff7096"/>'),
    "diya": ("0 0 48 40",
        '<path d="M22 24 q2 -12 2 -12 q0 0 2 12Z" fill="#ffb703"/>'
        '<ellipse cx="24" cy="22" rx="3.4" ry="6" fill="#f3722c"/>'
        '<path d="M6 26 Q24 40 42 26 Q24 32 6 26Z" fill="#c1121f" stroke="#7a0c16"/>'
        '<ellipse cx="24" cy="26" rx="18" ry="4" fill="#e85d04"/>'),
    "apple": ("0 0 40 40",
        '<path d="M20 12 C12 6 4 12 8 24 C10 32 16 36 20 36 C24 36 30 32 32 24 C36 12 28 6 20 12Z" fill="#e63946" stroke="#a4161a"/>'
        '<path d="M20 12 q1 -6 6 -7" fill="none" stroke="#6a4c2b" stroke-width="2"/>'
        '<path d="M20 12 q4 -3 9 -1 q-3 4 -9 1Z" fill="#52b788"/>'),
    "ball": ("0 0 40 40",
        '<circle cx="20" cy="20" r="15" fill="#ffb703" stroke="#e07a00" stroke-width="2"/>'
        '<path d="M5 20 h30 M20 5 v30 M9 9 q11 11 22 22 M31 9 q-11 11 -22 22" fill="none" stroke="#e07a00" stroke-width="1.5"/>'),
}


def _square_vb(vb):
    """Pad a viewBox to a centred square so every icon renders at a consistent
    visual size in a row, regardless of its native aspect ratio."""
    x0, y0, w, h = [float(v) for v in vb.split()]
    side = max(w, h)
    return f"{x0 - (side - w) / 2:.1f} {y0 - (side - h) / 2:.1f} {side:.1f} {side:.1f}"


def icon(name, size=30, cls="ico"):
    vb, inner = _ICONS[name]
    return (f'<svg class="{cls}" width="{size}" height="{size}" viewBox="{_square_vb(vb)}" '
            f'style="vertical-align:middle">{inner}</svg>')


def icon_marker(name, cx, cy, s=11):
    """An icon placed at a point inside another SVG (for mazes / scenes)."""
    vb, inner = _ICONS[name]
    x0, y0, w, h = [float(v) for v in vb.split()]
    scale = (2 * s) / max(w, h)
    tx = cx - (w * scale) / 2 - x0 * scale
    ty = cy - (h * scale) / 2 - y0 * scale
    return f'<g transform="translate({tx:.1f},{ty:.1f}) scale({scale:.3f})">{inner}</g>'


# ------------------------------------------------------------- themes --------
THEMES = {
    "space": {
        "word": "Space", "emoji_icon": "rocket",
        "grad": ("#3a0ca3", "#4361ee"), "accent": "#f72585", "title_accent": "#3a0ca3",
        "icons": ["star", "rocket", "planet", "moon"],
        "letter": [("R", "Rocket", "rocket"), ("S", "Star", "star"), ("P", "Planet", "planet"), ("M", "Moon", "moon")],
        "scene": "rocket",
    },
    "animals": {
        "word": "Animal Friends", "emoji_icon": "elephant",
        "grad": ("#2a9d8f", "#43aa8b"), "accent": "#f3722c", "title_accent": "#2a7d6f",
        "icons": ["cat", "dog", "pig", "fish"],
        "letter": [("C", "Cat", "cat"), ("D", "Dog", "dog"), ("P", "Pig", "pig"), ("F", "Fish", "fish")],
        "scene": "fish",
    },
    "indian": {
        "word": "Festival of Colours", "emoji_icon": "peacock",
        "grad": ("#b5179e", "#f3722c"), "accent": "#f3722c", "title_accent": "#b5179e",
        "icons": ["peacock", "elephant", "lotus", "diya"],
        "letter": [("E", "Elephant", "elephant"), ("L", "Lotus", "lotus"), ("D", "Diya", "diya"), ("P", "Peacock", "peacock")],
        "scene": "rangoli",
    },
    "mixed": {
        "word": "Discovery", "emoji_icon": "star",
        "grad": ("#3a0ca3", "#7209b7"), "accent": "#f72585", "title_accent": "#3a0ca3",
        "icons": ["star", "cat", "apple", "ball"],
        "letter": [("A", "Apple", "apple"), ("B", "Ball", "ball"), ("C", "Cat", "cat"), ("S", "Star", "star")],
        "scene": "rangoli",
    },
}

# CVC words for word-building: (word, middle vowel, icon). Literacy is theme-neutral.
CVC = [("CAT", "a", "cat"), ("SUN", "u", "sun"), ("PIG", "i", "pig"), ("DOG", "o", "dog")]


# --------------------------------------------------------------- maze --------
def maze_svg(cols=7, rows=5, cell=30, seed=11, start_icon="star", end_icon="rocket"):
    rng = random.Random(seed)
    carved = set()
    visited = [[False] * cols for _ in range(rows)]

    def carve(x, y):
        visited[y][x] = True
        dirs = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        rng.shuffle(dirs)
        for dx, dy in dirs:
            nx, ny = x + dx, y + dy
            if 0 <= nx < cols and 0 <= ny < rows and not visited[ny][nx]:
                carved.add(frozenset({(x, y), (nx, ny)}))
                carve(nx, ny)

    carve(0, 0)
    L = []
    line = lambda a, b, c, d: L.append(f'<line x1="{a}" y1="{b}" x2="{c}" y2="{d}"/>')
    for y in range(rows):
        for x in range(cols):
            x0, y0 = x * cell, y * cell
            north_open = (frozenset({(x, y), (x, y - 1)}) in carved) if y > 0 else (x == 0 and y == 0)
            if not north_open:
                line(x0, y0, x0 + cell, y0)
            west_open = (frozenset({(x, y), (x - 1, y)}) in carved) if x > 0 else False
            if not west_open:
                line(x0, y0, x0, y0 + cell)
    line(cols * cell, 0, cols * cell, rows * cell)          # right border
    line(0, rows * cell, (cols - 1) * cell, rows * cell)    # bottom, exit gap under last cell
    W, H = cols * cell, rows * cell
    return (f'<svg width="{W + 4}" height="{H + 4}" viewBox="-2 -2 {W + 4} {H + 4}">'
            f'<g stroke="#2b2d42" stroke-width="3" stroke-linecap="round">{"".join(L)}</g>'
            + icon_marker(start_icon, cell // 2, cell // 2, s=cell * 0.36)
            + icon_marker(end_icon, (cols - 1) * cell + cell // 2, (rows - 1) * cell + cell // 2, s=cell * 0.36)
            + '</svg>')


def trail_svg(start_icon="elephant", end_icon="lotus"):
    """Level-1 'trace the path' winding trail."""
    path = ("M40 90 C90 90 90 30 140 30 C190 30 190 90 240 90 "
            "C290 90 290 30 340 30 C370 30 380 50 390 60")
    return (f'<svg width="380" height="106" viewBox="0 0 430 120">'
            f'<path d="{path}" fill="none" stroke="#ffe0b3" stroke-width="20" stroke-linecap="round"/>'
            f'<path d="{path}" fill="none" stroke="#f4a261" stroke-width="20" stroke-linecap="round" stroke-dasharray="2 14"/>'
            + icon_marker(start_icon, 22, 86, 16) + icon_marker(end_icon, 404, 64, 16) + '</svg>')


# ------------------------------------------------------- colour scenes -------
def scene_rocket():
    return ('<svg width="195" height="179" viewBox="0 0 240 230">'
        '<g fill="#fff" stroke="#333" stroke-width="2.5">'
        '<path d="M120 12 C150 42 150 62 150 62 L90 62 C90 62 90 42 120 12Z"/>'
        '<rect x="90" y="62" width="60" height="93" rx="6"/>'
        '<path d="M90 122 L58 175 L90 158Z"/><path d="M150 122 L182 175 L150 158Z"/>'
        '<circle cx="120" cy="98" r="15"/>'
        '<path d="M104 155 Q120 188 136 155 Q130 182 120 196 Q110 182 104 155Z"/></g>'
        '<g font-size="20" text-anchor="middle" fill="#9aa0a6" font-family="Noto Sans">'
        '<text x="120" y="50">1</text><text x="120" y="142">2</text><text x="120" y="104">3</text>'
        '<text x="76" y="158">4</text><text x="164" y="158">4</text><text x="120" y="176">1</text></g></svg>',
        "1=Red 2=Blue 3=Yellow 4=Green", ["#e63946", "#4361ee", "#ffd166", "#52b788"])


def scene_rangoli():
    return ('<svg width="165" height="165" viewBox="0 0 210 210">'
        '<g stroke="#333" stroke-width="2" fill="#fff">'
        '<circle cx="105" cy="105" r="98" fill="none"/>'
        '<circle cx="60" cy="60" r="13"/><circle cx="150" cy="60" r="13"/>'
        '<circle cx="60" cy="150" r="13"/><circle cx="150" cy="150" r="13"/>'
        '<path d="M105 78 C92 56 92 44 105 34 C118 44 118 56 105 78Z"/>'
        '<path d="M105 132 C92 154 92 166 105 176 C118 166 118 154 105 132Z"/>'
        '<path d="M78 105 C56 92 44 92 34 105 C44 118 56 118 78 105Z"/>'
        '<path d="M132 105 C154 92 166 92 176 105 C166 118 154 118 132 105Z"/>'
        '<circle cx="105" cy="105" r="17"/>'
        '<circle cx="105" cy="14" r="5"/><circle cx="105" cy="196" r="5"/>'
        '<circle cx="14" cy="105" r="5"/><circle cx="196" cy="105" r="5"/></g>'
        '<g font-size="13" text-anchor="middle" fill="#9aa0a6" font-family="Noto Sans">'
        '<text x="105" y="110">1</text><text x="105" y="58">2</text><text x="105" y="156">2</text>'
        '<text x="56" y="109">2</text><text x="154" y="109">2</text>'
        '<text x="60" y="65">3</text><text x="150" y="65">3</text>'
        '<text x="60" y="155">3</text><text x="150" y="155">3</text><text x="105" y="18">4</text></g></svg>',
        "1=Red 2=Yellow 3=Blue 4=Green", ["#e63946", "#ffb703", "#3a86ff", "#2a9d8f"])


def scene_fish():
    return ('<svg width="205" height="134" viewBox="0 0 260 170">'
        '<g fill="#fff" stroke="#333" stroke-width="2.5">'
        '<path d="M30 85 C70 25 170 25 200 85 C170 145 70 145 30 85Z"/>'
        '<path d="M200 85 L240 50 L240 120Z"/>'
        '<circle cx="70" cy="70" r="13"/>'
        '<path d="M110 55 q20 30 0 60" fill="none"/>'
        '<circle cx="150" cy="40" r="7"/><circle cx="175" cy="30" r="6"/></g>'
        '<g font-size="18" text-anchor="middle" fill="#9aa0a6" font-family="Noto Sans">'
        '<text x="120" y="92">1</text><text x="222" y="90">2</text>'
        '<text x="70" y="75">3</text><text x="150" y="44">4</text><text x="175" y="34">4</text></g></svg>',
        "1=Orange 2=Yellow 3=White 4=Blue", ["#f3722c", "#ffd166", "#ffffff", "#3a86ff"])


SCENES = {"rocket": scene_rocket, "rangoli": scene_rangoli, "fish": scene_fish}
