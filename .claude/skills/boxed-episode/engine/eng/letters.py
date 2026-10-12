"""Hand-painted lettering. Font glyph outlines are resampled into dense contours (PathMeasure), wobbled with smooth
per-drawing noise (the boil), given small per-letter rotation / scale / baseline jitter, then painted as:
drop shadow -> flat fill (+ light brush streaks) -> brush ink outline -> optional paint drips.
`reveal` 0..1 pops the letters in one after another (`stagger`)."""
import math
import os
import numpy as np
import skia
from .core import PAL, INK, paint, hsh, brush, poly_path, snoise, mix
from . import core

FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts")
FILES = dict(shrik="Shrikhand-Regular.ttf", londrina="LondrinaSolid-Black.ttf", londrina_r="LondrinaSolid-Regular.ttf",
             marker="PermanentMarker-Regular.ttf", bagel="BagelFatOne-Regular.ttf", chewy="Chewy-Regular.ttf",
             bangers="Bangers-Regular.ttf", titan="TitanOne-Regular.ttf", wet="RubikWetPaint-Regular.ttf",
             caveat="CaveatBrush-Regular.ttf")
_TF = {}
_CONT = {}


def _font(name, size):
    tf = _TF.get(name)
    if tf is None:
        tf = skia.Typeface.MakeFromFile(os.path.join(FONT_DIR, FILES.get(name, FILES["londrina"])))
        _TF[name] = tf
    f = skia.Font(tf, float(size))
    f.setEdging(skia.Font.Edging.kAntiAlias)
    return f


def _contours(font, size, gid, step):
    """Glyph outline as a list of closed (N,2) polylines sampled every ~step px (cached)."""
    key = (font, round(float(size), 1), int(gid), float(step))
    c = _CONT.get(key)
    if c is not None:
        return c
    out = []
    path = _font(font, size).getPath(int(gid))
    if path is not None and path.countPoints() > 0:
        pm = skia.PathMeasure(path, True)
        while True:
            L = pm.getLength()
            if L > 1.0:
                n = max(6, int(L / step))
                pts = []
                for i in range(n):
                    p, _t = pm.getPosTan(L * i / n)
                    pts.append((p.x(), p.y()))
                out.append(np.array(pts, dtype=np.float64))
            if not pm.nextContour():
                break
    _CONT[key] = out
    return out


def measure(text, font="londrina", size=120, spacing=0.0):
    f = _font(font, size)
    g = f.textToGlyphs(text)
    w = f.getWidths(g)
    return float(sum(w) + spacing * max(0, len(w) - 1))


def _pop(k):
    """0..1 -> scale with a small overshoot (back-out ease)."""
    if k <= 0:
        return 0.0
    if k >= 1:
        return 1.0
    c1 = 1.9
    c3 = c1 + 1
    return 1 + c3 * (k - 1) ** 3 + c1 * (k - 1) ** 2


def _wobble(C, amp, seed):
    if amp <= 0 or len(C) < 4:
        return C
    d = np.diff(np.vstack([C, C[:1]]), axis=0)
    tot = np.hypot(d[:, 0], d[:, 1]).sum() or 1.0
    u = np.concatenate([[0.0], np.cumsum(np.hypot(d[:, 0], d[:, 1]))[:-1]]) / tot
    T = np.roll(C, -1, 0) - np.roll(C, 1, 0)
    n = np.hypot(T[:, 0], T[:, 1]) + 1e-9
    N = np.stack([-T[:, 1] / n, T[:, 0] / n], 1)
    return C + N * (amp * snoise(u * (1.0 + tot / 400.0), seed, 3))[:, None]


def paint_text(cv, text, x, y, font="londrina", size=120, fill=None, ink_w=6.0, shadow=(7, 7), shadow_rgb=None,
               seed=0, wobble=2.0, rot_jit=5.0, scale_jit=0.07, base_jit=6.0, align="center", spacing=0.0,
               reveal=1.0, stagger=0.06, fills=None, streaks=True, drips=0, outline_rgb=None, step=4.0, a=255):
    """Draw hand-painted text with its baseline at y. reveal 0..1 pops letters in left to right."""
    fill = fill or PAL["yellow"]
    shadow_rgb = shadow_rgb or INK
    outline_rgb = outline_rgb or INK
    f = _font(font, size)
    gl = f.textToGlyphs(text)
    wd = f.getWidths(gl)
    total = sum(wd) + spacing * max(0, len(wd) - 1)
    pen = x - total / 2 if align == "center" else (x - total if align == "right" else x)
    n = len(gl)
    if n == 0 or reveal <= 0:
        return total
    step = max(1.5, step * (size / 120.0) ** 0.6)
    vis = [i for i in range(n) if text[i:i + 1] != " "] if len(text) == n else list(range(n))
    nv = max(1, len(vis))
    win = max(0.18, 1.0 - stagger * (nv - 1))
    delay = stagger if win > 0.18 else (1.0 - 0.18) / max(1, nv - 1)
    letters = []
    px = pen
    vi = 0
    for i in range(n):
        adv = wd[i]
        cs = _contours(font, size, gl[i], step)
        if cs:
            k = min(1.0, max(0.0, (reveal - vi * delay) / win)) if reveal < 1 else 1.0
            vi += 1
            if k > 0:
                h1, h2, h3, h4 = (float(hsh(seed * 13.7 + i * 7.31 + j * 3.3)) for j in range(4))
                ang = (h1 - 0.5) * 2 * rot_jit
                sc = (1 + (h2 - 0.5) * 2 * scale_jit) * _pop(k)
                by = (h3 - 0.5) * 2 * base_jit * (size / 120.0)
                cx, cy = px + adv / 2, y - size * 0.34
                ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
                amp = wobble * 0.45 * (size / 120.0) ** 0.5
                polys = []
                for j, C in enumerate(cs):
                    P = _wobble(C, amp, seed * 31 + i * 17 + j) if amp > 0 else C
                    X = P[:, 0] + px - cx
                    Y = P[:, 1] + y + by - cy
                    polys.append(np.stack([cx + sc * (X * ca - Y * sa), cy + sc * (X * sa + Y * ca)], 1))
                col = fills[(vi - 1) % len(fills)] if fills else fill
                letters.append((i, polys, col, h4, k))
        px += adv + spacing

    def path_of(polys, dx=0.0, dy=0.0):
        p = skia.Path()
        for P in polys:
            p.addPoly([skia.Point(float(u + dx), float(v + dy)) for u, v in P], True)
        return p

    if shadow is not None:                                         # pass 1: drop shadows (behind every letter)
        for i, polys, col, h4, k in letters:
            cv.drawPath(path_of(polys, shadow[0], shadow[1]), paint(shadow_rgb, a))
    for i, polys, col, h4, k in letters:                           # pass 2: fill, streaks, drips, ink
        p = path_of(polys)
        cv.drawPath(p, paint(col, a))
        allp = np.vstack(polys)
        x0, y0 = allp.min(0)
        x1, y1 = allp.max(0)
        if streaks and size >= 34:
            cv.save()
            cv.clipPath(p, doAntiAlias=True)
            light = mix(col, PAL["white"], 0.42)
            for s in range(2):
                yy = y0 + (y1 - y0) * (0.22 + 0.2 * s + 0.08 * h4)
                pts = np.array([(x0 - 4, yy + 3 * math.sin(s + h4 * 6)), ((x0 + x1) / 2, yy - size * 0.02), (x1 + 4, yy + size * 0.01)])
                brush(cv, core.cr_open(pts, 8), max(2.0, size * 0.035), light, taper=(0.3, 0.3), seed=seed + i * 5 + s, a=int(a * 0.8))
            cv.restore()
        if drips and h4 < 0.55:
            Pm = polys[0]
            bot = Pm[np.argsort(Pm[:, 1])[-max(3, len(Pm) // 12):]]
            bx, byy = bot[int(h4 * 997) % len(bot)]
            L = size * 0.2 * drips * (0.45 + float(hsh(seed + i * 2.9)))
            dw = max(4.0, size * 0.055)
            grow = 0.85 + 0.15 * math.sin(core.D * 0.15 + i)
            L *= grow
            dp = skia.Path()
            dp.moveTo(bx - dw, byy - dw)
            dp.cubicTo(bx - dw * 0.7, byy + L * 0.4, bx - dw * 0.45, byy + L * 0.75, bx - dw * 0.5, byy + L)
            dp.lineTo(bx + dw * 0.5, byy + L)
            dp.cubicTo(bx + dw * 0.45, byy + L * 0.75, bx + dw * 0.7, byy + L * 0.4, bx + dw, byy - dw)
            dp.close()
            dp.addCircle(bx, byy + L, dw * 0.78)
            cv.drawPath(dp, paint(col, a))
            if ink_w > 0:
                cv.drawPath(dp, paint(outline_rgb, a, stroke=max(1.0, ink_w * 0.55)))
                cv.drawPath(p, paint(col, a))                       # keep the letter clean over the drip's top edge
        if ink_w > 0:
            for j, P in enumerate(polys):
                brush(cv, P, ink_w, outline_rgb, var=0.35, seed=seed + i * 11 + j, closed=True, a=a)
    return total


def wrap_lines(text, font, size, maxw):
    words = text.split()
    lines, cur = [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if measure(trial, font, size) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines
