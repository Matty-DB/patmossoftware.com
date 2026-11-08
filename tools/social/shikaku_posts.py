"""Generate unique-solution Shikaku puzzles and render Instagram posts in the Patmos style.

Writes puzzle and solution PNGs (1080x1350) and a puzzles.json with the boards.
"""
import json, random, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- generation

def random_partition(w, h, rng, max_area):
    """Cover a w x h grid with rectangles by repeatedly growing from the first empty cell."""
    owner = [[-1] * w for _ in range(h)]
    rects = []
    while True:
        empty = [(x, y) for y in range(h) for x in range(w) if owner[y][x] < 0]
        if not empty:
            return rects
        x0, y0 = empty[0]
        # largest width available on this row from x0
        maxw = 0
        while x0 + maxw < w and owner[y0][x0 + maxw] < 0:
            maxw += 1
        options = []
        for rw in range(1, maxw + 1):
            for rh in range(1, h - y0 + 1):
                if rw * rh > max_area:
                    break
                if all(owner[y0 + dy][x0 + dx] < 0 for dy in range(rh) for dx in range(rw)):
                    options.append((rw, rh))
                else:
                    break
        # prefer mid-size rectangles, avoid lots of 1x1
        weights = [(1 if a == 1 else min(a, 6)) for a in (rw * rh for rw, rh in options)]
        rw, rh = rng.choices(options, weights=weights)[0]
        idx = len(rects)
        for dy in range(rh):
            for dx in range(rw):
                owner[y0 + dy][x0 + dx] = idx
        rects.append((x0, y0, rw, rh))


def candidates(w, h, cx, cy, area, clues):
    """Every rectangle of the given area containing (cx, cy) and no other clue."""
    out = []
    for rw in range(1, area + 1):
        if area % rw:
            continue
        rh = area // rw
        if rw > w or rh > h:
            continue
        for x in range(cx - rw + 1, cx + 1):
            for y in range(cy - rh + 1, cy + 1):
                if x < 0 or y < 0 or x + rw > w or y + rh > h:
                    continue
                if any(x <= ox < x + rw and y <= oy < y + rh and (ox, oy) != (cx, cy) for ox, oy, _ in clues):
                    continue
                out.append((x, y, rw, rh))
    return out


def count_solutions(w, h, clues, limit=2):
    cands = [candidates(w, h, cx, cy, a, clues) for cx, cy, a in clues]
    used = [[False] * w for _ in range(h)]
    count = 0
    solution = None
    order = sorted(range(len(clues)), key=lambda i: len(cands[i]))

    def fits(r):
        x, y, rw, rh = r
        return all(not used[y + dy][x + dx] for dy in range(rh) for dx in range(rw))

    def mark(r, v):
        x, y, rw, rh = r
        for dy in range(rh):
            for dx in range(rw):
                used[y + dy][x + dx] = v

    chosen = [None] * len(clues)

    def rec(k):
        nonlocal count, solution
        if count >= limit:
            return
        if k == len(order):
            count += 1
            solution = list(chosen)
            return
        i = order[k]
        for r in cands[i]:
            if fits(r):
                mark(r, True)
                chosen[i] = r
                rec(k + 1)
                mark(r, False)
                chosen[i] = None
                if count >= limit:
                    return

    rec(0)
    return count, solution


def make_puzzle(w, h, seed, max_area, min_rects, max_rects):
    rng = random.Random(seed)
    for attempt in range(5000):
        rects = random_partition(w, h, rng, max_area)
        if not (min_rects <= len(rects) <= max_rects):
            continue
        clues = []
        for x, y, rw, rh in rects:
            cx, cy = x + rng.randrange(rw), y + rng.randrange(rh)
            clues.append((cx, cy, rw * rh))
        n, sol = count_solutions(w, h, clues)
        if n == 1:
            return {"w": w, "h": h, "clues": clues, "solution": sol, "seed": seed, "attempts": attempt + 1}
    raise RuntimeError("no unique puzzle found")


# ----------------------------------------------------------------- rendering

W, H = 1080, 1350
BG_TOP, BG_BOTTOM = (237, 235, 255), (250, 237, 245)
INK = (92, 82, 158)
INK_DARK = (63, 55, 111)
ACCENT = [(123, 92, 224), (61, 123, 240)]  # Shikaku: violet -> blue
PINK = (255, 59, 115)
FILLS = [(255, 214, 102), (126, 217, 181), (255, 168, 168), (160, 196, 255), (205, 180, 255),
         (255, 196, 140), (150, 222, 225), (255, 186, 222), (196, 228, 140), (245, 205, 255),
         (180, 210, 245), (255, 224, 170), (170, 235, 200), (230, 200, 180)]
ROUND = "/System/Library/Fonts/SFNSRounded.ttf"


def font(size, weight="Heavy"):
    f = ImageFont.truetype(ROUND, size)
    try:
        f.set_variation_by_name(weight)
    except Exception:
        pass
    return f


def background():
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(round(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * t) for i in range(3)))
    return img


def gradient_text(img, xy, text, fnt):
    d = ImageDraw.Draw(img)
    l, t, r, b = d.textbbox(xy, text, font=fnt)
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).text(xy, text, font=fnt, fill=255)
    grad = Image.new("RGB", img.size)
    gd = ImageDraw.Draw(grad)
    for y in range(t, b + 1):
        k = (y - t) / max(1, b - t)
        gd.line([(l, y), (r, y)], fill=tuple(round(ACCENT[0][i] + (ACCENT[1][i] - ACCENT[0][i]) * k) for i in range(3)))
    # white sticker edge, as PatmosTitle does
    ImageDraw.Draw(img).text((xy[0], xy[1] + 4), text, font=fnt, fill=(255, 255, 255))
    img.paste(grad, (0, 0), mask)


def centered(d, y, text, fnt, fill):
    tw = d.textlength(text, font=fnt)
    d.text(((W - tw) / 2, y), text, font=fnt, fill=fill)


def mark(d, y):
    a, b, c = font(30, "Semibold"), font(33, "Black"), font(30, "Semibold")
    parts = [("a ", a), ("Patmos", b), (" game", c)]
    total = sum(d.textlength(t, font=f) for t, f in parts) + 40
    x = (W - total) / 2
    # sparkle
    cx, cy, s = x + 14, y + 20, 14
    d.polygon([(cx, cy - s), (cx + s * .3, cy - s * .3), (cx + s, cy), (cx + s * .3, cy + s * .3),
               (cx, cy + s), (cx - s * .3, cy + s * .3), (cx - s, cy), (cx - s * .3, cy - s * .3)], fill=PINK)
    x += 40
    col = tuple(round(INK[i] * .55 + BG_BOTTOM[i] * .45) for i in range(3))
    for t, f in parts:
        d.text((x, y + (2 if f is b else 4)), t, font=f, fill=col)
        x += d.textlength(t, font=f)


def board(img, p, solved):
    d = ImageDraw.Draw(img)
    w, h = p["w"], p["h"]
    size = 820
    cell = size // max(w, h)
    bw, bh = cell * w, cell * h
    ox, oy = (W - bw) // 2, 340 + (size - bh) // 2
    pad = 26
    # card with hard drop shadow
    d.rounded_rectangle([ox - pad, oy - pad + 12, ox + bw + pad, oy + bh + pad + 12], 40, fill=(213, 205, 238))
    d.rounded_rectangle([ox - pad, oy - pad, ox + bw + pad, oy + bh + pad], 40, fill=(255, 255, 255))
    line = (226, 222, 242)
    for i in range(w + 1):
        d.line([ox + i * cell, oy, ox + i * cell, oy + bh], fill=line, width=3)
    for j in range(h + 1):
        d.line([ox, oy + j * cell, ox + bw, oy + j * cell], fill=line, width=3)
    if solved:
        for i, (x, y, rw, rh) in enumerate(p["solution"]):
            inset = 5
            d.rounded_rectangle([ox + x * cell + inset, oy + y * cell + inset,
                                 ox + (x + rw) * cell - inset, oy + (y + rh) * cell - inset],
                                18, fill=FILLS[i % len(FILLS)])
    nf = font(int(cell * .5), "Black")
    for cx, cy, a in p["clues"]:
        t = str(a)
        tw = d.textlength(t, font=nf)
        l, tt, r, bb = d.textbbox((0, 0), t, font=nf)
        d.text((ox + cx * cell + (cell - tw) / 2, oy + cy * cell + (cell - (bb - tt)) / 2 - tt), t,
               font=nf, fill=INK_DARK)


def render(p, title_top, title_rest, footer, solved, path):
    img = background()
    d = ImageDraw.Draw(img)
    big = font(92, "Black")
    rest = font(64, "Heavy")
    tw = d.textlength(title_top, font=big)
    gradient_text(img, ((W - tw) / 2, 90), title_top, big)
    centered(d, 205, title_rest, rest, INK_DARK)
    board(img, p, solved)
    centered(d, 1205, footer, font(38, "Bold"), INK)
    mark(d, 1265)
    img.save(path, "PNG", optimize=True)


if __name__ == "__main__":
    specs = [
        ("01", 5, 5, 11, 6, 5, 8, "Warm-up", "Easy"),
        ("02", 6, 6, 23, 8, 6, 10, "Getting there", "Medium"),
        ("03", 7, 7, 37, 10, 7, 11, "Proper think", "Hard"),
        ("04", 8, 8, 52, 14, 8, 12, "Weekend boss", "Expert"),
    ]
    meta = []
    for key, w, h, seed, max_area, mn, mx, tag, level in specs:
        p = make_puzzle(w, h, seed, max_area, mn, mx)
        p.update({"key": key, "level": level, "tag": tag})
        assert sum(rw * rh for _, _, rw, rh in p["solution"]) == w * h
        render(p, "Can you", "solve this?", f"{level} · {w}×{h} · one answer", False, OUT / f"shikaku-{key}-puzzle.png")
        render(p, "Solved", "how did you do?", "Every number is its rectangle's size", True, OUT / f"shikaku-{key}-answer.png")
        meta.append(p)
        print(key, level, f"{w}x{h}", len(p["clues"]), "rects, unique, attempts", p["attempts"])
    (OUT / "puzzles.json").write_text(json.dumps(meta, indent=1))
