"""BOXED ep4 'THE CAVE' -- owner `ad`: the CAVE PHONE PRO infomercial (T033), the 'ancient history' modern montage (T044)
and 'everybody's watching some kind of wall' (T047).

All drawing is BOXED ink/boil style (blob / line / brush / paint_text) on top of a few 1980s-infomercial set pieces written
here: chrome letters with an extruded side, a neon perspective grid, a striped synth sun, Memphis confetti, a glossy
rotating smartphone whose screen is a tiny firelit cave wall, gold SmartChains, a rapid legal crawl."""
from .shots_ep4_base import *          # noqa: F401,F403
from .shots_ep4_base import (P_, R, PAL, INK, W, H, paint, poly_path, cr_closed, cr_open, ell, blob, line, brush, dots, hsh, mix, jit,
                             rot, stipple, sparkle, rect_pts, tube, core, w, sets, paint_text, measure, wrap_lines, draw_zee, draw_host,
                             ease, pop, lerp, Hh, G, CAM_HOST, CAM_ZEE, studio, spk_loud, loud_at, vis_at, vignette, darkness,
                             firelight, cave_fire, rock_mass, chain, prisoner, statue, shadow_shape, crystal, glow_mushroom, handprint,
                             wall_surface, sun_rays, SHAPES, CV_ROCK, CV_ROCK2, CV_ROCK_DK, CV_WALL, CV_WALL2, CV_SHADOW, CV_FIRE)
from .zee import _hand
from .letters import _font, _contours, _wobble, _pop
from .cast import melting_clock
import math
import numpy as np
import skia

ROSE = (255, 168, 150)
ROSE_DK = (196, 100, 96)
GOLD_DK = (176, 104, 10)
GLASS = (14, 12, 30)


def _ph(t, a, b):
    """0..1 progress of t through [a, b] (clamped)."""
    return float(np.clip((t - a) / max(1e-6, b - a), 0.0, 1.0))


def _ink(scale):
    """Context: pen-weight compensation for a drawing scaled by `scale` (returns the old INKMUL to restore)."""
    old = core.INKMUL
    core.INKMUL = old / max(scale, 0.05) ** 0.5
    return old


def _lin(x0, y0, x1, y1, cols, pos=None, a=255):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(x0, y0), skia.Point(x1, y1)], [core.C(c, a) for c in cols], pos))
    return p


def _rad(x, y, r, cols, pos=None, a=255):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(x, y), max(1.0, r), [core.C(c, a) for c in cols], pos))
    return p


def _glow(cv, x, y, r, rgb, a=120):
    cv.drawCircle(x, y, r, _rad2(x, y, r, rgb, a))


def _rad2(x, y, r, rgb, a):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(x, y), max(1.0, r), [core.C(rgb, a), core.C(rgb, int(a * 0.35)), core.C(rgb, 0)], [0.0, 0.4, 1.0]))
    return p


def rrect_pts(x0, y0, x1, y1, r, n=4, sx=1.0):
    """Rounded-rectangle control polygon (corner radius r, corners compressed in x by sx) for blob/brush."""
    rx = max(1.0, r * sx)
    ry = r
    pts = []
    for cx, cy, a0 in ((x1 - rx, y0 + ry, -90), (x1 - rx, y1 - ry, 0), (x0 + rx, y1 - ry, 90), (x0 + rx, y0 + ry, 180)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
    return np.array(pts)


def rrect_path(x0, y0, x1, y1, r):
    p = skia.Path()
    p.addRRect(skia.RRect.MakeRectXY(R(x0, y0, x1, y1), r, r))
    return p


# ===================================================================== lettering: 80s chrome
CHROME = ([(226, 252, 255), (128, 206, 255), (60, 120, 230), (255, 255, 255), (64, 20, 104), (208, 44, 168), (255, 190, 120)],
          [0.0, 0.3, 0.47, 0.5, 0.53, 0.8, 1.0])
GOLDC = ([(255, 252, 216), (255, 214, 0), (240, 150, 10), (255, 255, 236), (140, 64, 10), (255, 150, 24), (255, 232, 140)],
         [0.0, 0.32, 0.47, 0.5, 0.53, 0.8, 1.0])
ROSEC = ([(255, 240, 236), (255, 168, 150), (220, 96, 120), (255, 252, 246), (120, 30, 60), (255, 120, 150), (255, 214, 190)],
         [0.0, 0.32, 0.47, 0.5, 0.53, 0.8, 1.0])
NEONC = ([(255, 255, 255), (255, 120, 196), (255, 46, 166)], [0.0, 0.5, 1.0])


def letter_polys(text, x, y, font="titan", size=120, seed=0, wobble=1.4, rot_jit=3.0, scale_jit=0.04, base_jit=3.0,
                 align="center", spacing=0.0, reveal=1.0, stagger=0.06, step=4.0):
    """The glyph contours of paint_text (same wobble/boil + pop-in), returned as [[poly, ...] per visible letter], width."""
    f = _font(font, size)
    gl = f.textToGlyphs(text)
    wd = f.getWidths(gl)
    total = sum(wd) + spacing * max(0, len(wd) - 1)
    pen = x - total / 2 if align == "center" else (x - total if align == "right" else x)
    n = len(gl)
    out = []
    if n == 0 or reveal <= 0:
        return out, total
    step = max(1.5, step * (size / 120.0) ** 0.6)
    vis = [i for i in range(n) if text[i:i + 1] != " "] if len(text) == n else list(range(n))
    nv = max(1, len(vis))
    win = max(0.18, 1.0 - stagger * (nv - 1))
    delay = stagger if win > 0.18 else (1.0 - 0.18) / max(1, nv - 1)
    px = pen
    vi = 0
    for i in range(n):
        adv = wd[i]
        cs = _contours(font, size, gl[i], step)
        if cs:
            k = min(1.0, max(0.0, (reveal - vi * delay) / win)) if reveal < 1 else 1.0
            vi += 1
            if k > 0:
                h1, h2, h3 = (float(hsh(seed * 13.7 + i * 7.31 + j * 3.3)) for j in range(3))
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
                out.append(polys)
        px += adv + spacing
    return out, total


def chrome_text(cv, text, x, y, size, font="titan", seed=0, grad=CHROME, depth=None, ext=(0.45, 1.0), side=None, ink=5.0,
                reveal=1.0, stagger=0.05, wobble=1.2, shine=None, glints=2, skew=-0.12, a=255, align="center", spacing=0.0,
                glow=None, outline2=None):
    """1980s chrome lettering: hard-horizon chrome gradient face, an extruded block side, a brush ink outline, a travelling
    shine band (shine = 0..1 position, None = off) and twinkling glints. y = baseline. Returns the text width."""
    letters, total = letter_polys(text, x, y, font, size, seed, wobble=wobble, align=align, spacing=spacing, reveal=reveal, stagger=stagger)
    if not letters:
        return total
    cv.save()
    if skew:
        cv.translate(x, y); cv.skew(skew, 0); cv.translate(-x, -y)
    path = skia.Path()
    for polys in letters:
        for P in polys:
            path.addPoly([skia.Point(float(u), float(v)) for u, v in P], True)
    b = path.computeTightBounds()
    y0, y1 = b.top(), b.bottom()
    depth = size * 0.11 if depth is None else depth
    if glow is not None:
        gp = skia.Paint(AntiAlias=True, Color=core.C(glow, int(a * 0.55)))
        gp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, size * 0.12))
        cv.drawPath(path, gp)
    if depth > 0:
        n = max(2, int(depth / 2.2))
        L = math.hypot(*ext) or 1.0
        ex, ey = ext[0] / L, ext[1] / L
        sc = side or [P_["vdark"], P_["night"], P_["magenta"]]
        sp = _lin(0, y0, 0, y1 + depth, sc, a=a)
        ip = paint(outline2 or INK, a, stroke=ink * 2.0 * core.INKMUL)
        for k in range(n, 0, -1):
            cv.save(); cv.translate(ex * depth * k / n, ey * depth * k / n); cv.drawPath(path, ip); cv.restore()
        for k in range(n, 0, -1):
            cv.save(); cv.translate(ex * depth * k / n, ey * depth * k / n); cv.drawPath(path, sp); cv.restore()
    cv.drawPath(path, _lin(0, y0, 0, y1, grad[0], grad[1], a=a))
    if shine is not None and 0.0 <= shine <= 1.0:
        cv.save(); cv.clipPath(path, doAntiAlias=True)
        sx = b.left() - size + (b.width() + 2 * size) * shine
        cv.drawPath(poly_path([(sx, y0 - 20), (sx + size * 0.35, y0 - 20), (sx + size * 0.05, y1 + 20), (sx - size * 0.3, y1 + 20)]), paint(P_["white"], int(a * 0.75)))
        cv.restore()
    for li, polys in enumerate(letters):
        for j, P in enumerate(polys):
            brush(cv, P, ink, var=0.3, seed=seed + li * 11 + j, closed=True, a=a)
    for g in range(glints):
        li = int(hsh(seed + g * 3.7 + int(core.D / 5)) * len(letters))
        P = letters[li][0]
        pt = P[int(hsh(seed + g * 5.1 + int(core.D / 5)) * len(P))]
        tw = 0.5 + 0.5 * math.sin(core.D * 0.9 + g * 2.0)
        sparkle(cv, pt[0], pt[1], size * (0.1 + 0.08 * tw), P_["white"], w=2.0, seed=seed + 90 + g, a=a)
    cv.restore()
    return total


def neon_text(cv, text, x, y, size, rgb, font="londrina", seed=0, a=255, reveal=1.0, align="center", flicker=0.0, ink=4.0):
    """Glowing neon-tube lettering: blurred halo + a dark tube shadow + white-hot core fill."""
    letters, total = letter_polys(text, x, y, font, size, seed, wobble=1.0, align=align, reveal=reveal, stagger=0.04)
    if not letters:
        return total
    on = 1.0 if flicker <= 0 else (0.35 if hsh(core.D * 1.37 + seed) < flicker else 1.0)
    path = skia.Path()
    for polys in letters:
        for P in polys:
            path.addPoly([skia.Point(float(u), float(v)) for u, v in P], True)
    gp = skia.Paint(AntiAlias=True, Color=core.C(rgb, int(a * 0.8 * on)))
    gp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, size * 0.16))
    cv.drawPath(path, gp)
    cv.save(); cv.translate(size * 0.04, size * 0.05); cv.drawPath(path, paint(INK, int(a * 0.6))); cv.restore()
    cv.drawPath(path, paint(mix(rgb, P_["white"], 0.55 * on), a))
    for li, polys in enumerate(letters):
        for j, P in enumerate(polys):
            brush(cv, P, ink, rgb=mix(rgb, INK, 0.25), var=0.25, seed=seed + li * 7 + j, closed=True, a=a)
    return total


# ===================================================================== 80s infomercial set pieces
def synth_sun(cv, x, y, r, t, seed=0, cols=None, bands=7, ink=5.0, a=255, glow=True):
    """A striped retro sun: hot vertical gradient, horizontal slots sliding down through its lower half, boiling outline."""
    cols = cols or [P_["yellow"], P_["orange"], P_["magenta"]]
    if glow:
        cv.drawCircle(x, y, r * 1.9, _rad2(x, y, r * 1.9, cols[1], int(110 * a / 255)))
    circ = poly_path(cr_closed(jit(ell(x, y, r, r, n=26), r * 0.006 + 0.6, seed), 4))
    cut = skia.Path()
    for k in range(bands):
        u = (k + (t * 0.35) % 1.0) / bands
        yy = y - r * 0.05 + r * 1.05 * u
        hh = r * (0.015 + 0.11 * u)
        cut.addRect(R(x - r - 20, yy, x + r + 20, yy + hh))
    sun = skia.Op(circ, cut, skia.PathOp.kDifference_PathOp) or circ
    cv.drawPath(sun, _lin(0, y - r, 0, y + r, cols, a=a))
    cv.drawPath(sun, paint(INK, a, stroke=ink * core.INKMUL))


def neon_grid(cv, hy, t, speed=0.55, col=None, floor=None, nx=14, nz=11, cx=960.0, x0=-300, x1=2220, y1=1120, seed=0, a=255, spread=2.6):
    """The neon perspective floor: a dark gradient plane with glowing converging rails and cross-lines rushing at the viewer."""
    col = col or P_["magenta"]
    floor = floor or (34, 8, 66)
    cv.drawRect(R(x0, hy, x1, y1), _lin(0, hy, 0, y1, [mix(floor, col, 0.5), floor, mix(floor, INK, 0.55)], [0.0, 0.22, 1.0], a=a))
    for k in range(-nx, nx + 1):
        xb = cx + k * (x1 - x0) / nx * spread * 0.5
        xt = cx + k * 30
        line(cv, [(xt, hy), (xb, y1)], 9, col, seed=seed + k, boil=0.4, n=2, taper=(0.9, 0.0), a=int(a * 0.22))
        line(cv, [(xt, hy), (xb, y1)], 3.0, mix(col, P_["white"], 0.35), seed=seed + k, boil=0.4, n=2, taper=(0.9, 0.0), a=a)
    for j in range(nz):
        u = (j + (t * speed) % 1.0) / nz
        yy = hy + (y1 - hy) * u ** 2.1
        wdt = 1.2 + 4.0 * u
        line(cv, [(x0, yy), (cx, yy + 1.5 * math.sin(j + t)), (x1, yy)], wdt * 3, col, seed=seed + 40 + j, boil=0.4, n=3, taper=(0, 0), a=int(a * 0.2 * u ** 0.5))
        line(cv, [(x0, yy), (cx, yy + 1.5 * math.sin(j + t)), (x1, yy)], wdt, mix(col, P_["white"], 0.35), seed=seed + 40 + j, boil=0.4, n=3, taper=(0, 0),
             a=int(a * min(1.0, 0.3 + u * 1.4)))
    cv.drawRect(R(x0, hy - 6, x1, hy + 30), _lin(0, hy - 6, 0, hy + 30, [P_["white"], mix(col, P_["white"], 0.4), col], [0.0, 0.3, 1.0], a=int(a * 0.55)))
    brush(cv, np.array([(x0, hy), (cx, hy + 1), (x1, hy)]), 4.0, taper=(0.02, 0.02), seed=seed + 99, a=a)


def wire_mountains(cv, hy, t, seed=0, col=None, a=255):
    """Distant 80s wireframe mountains standing on the horizon."""
    col = col or P_["teal"]
    for k, (mx, mh, mw) in enumerate(((150, 170, 330), (430, 250, 300), (700, 140, 260), (1240, 190, 300), (1530, 270, 320), (1800, 160, 280))):
        pts = [(mx - mw, hy), (mx - mw * 0.35, hy - mh * 0.7), (mx, hy - mh), (mx + mw * 0.4, hy - mh * 0.62), (mx + mw, hy)]
        blob(cv, pts, mix(P_["night"], col, 0.18), w=3.5, seed=seed + k, boil=0.7, n=3, a=a)
        for j in range(1, 4):
            line(cv, [(mx - mw * (1 - j * 0.22), hy), (mx, hy - mh)], 2.0, col, seed=seed + 20 + k * 5 + j, boil=0.5, n=2, taper=(0, 0.2), a=int(a * 0.7))
            line(cv, [(mx + mw * (1 - j * 0.22), hy), (mx, hy - mh)], 2.0, col, seed=seed + 40 + k * 5 + j, boil=0.5, n=2, taper=(0, 0.2), a=int(a * 0.7))


def sky80(cv, hy, t, seed=0, cols=None, stars=True):
    """Gradient night->violet->magenta->orange sky down to the horizon line hy, with stars + scattered sparkles."""
    cols = cols or [P_["void"], P_["night"], P_["vdark"], P_["magenta"], P_["orange"]]
    cv.drawRect(R(-300, -300, W + 300, hy + 40), _lin(0, -100, 0, hy, cols, [0.0, 0.25, 0.5, 0.82, 1.0]))
    if stars:
        w.stars(cv, seed + 3, (-200, -100, W + 200, hy - 80), n=170, big=0)
        for k in range(7):
            tw = 0.5 + 0.5 * math.sin(t * 3 + k * 1.9)
            sparkle(cv, hsh(seed + k) * W, 40 + hsh(seed + 20 + k) * (hy - 260), 6 + 12 * tw, [P_["cream"], P_["mint"], P_["hotpink"]][k % 3], w=2.0, seed=seed + 30 + k)


def memphis(cv, t, seed, n=16, box=(0, 0, W, H), s=1.0, cols=None, a=255, drift=1.0):
    """Floating 1980s Memphis confetti: triangles, squiggles, zigzags, rings, dot patches and plus signs (all boiling)."""
    cols = cols or [P_["yellow"], P_["teal"], P_["hotpink"], P_["acid"], P_["orange"], P_["lilac"]]
    x0, y0, x1, y1 = box
    for k in range(n):
        kind = int(hsh(seed + k * 1.7) * 6)
        x = x0 + (hsh(seed + k * 3.1) * (x1 - x0) + t * 30 * drift * (hsh(seed + k * 4.4) - 0.5)) % (x1 - x0)
        y = y0 + hsh(seed + k * 5.3) * (y1 - y0) + 16 * math.sin(t * 0.9 + k)
        r = (16 + 20 * hsh(seed + k * 7.7)) * s
        ang = t * 50 * (hsh(seed + k * 2.2) - 0.5) + 360 * hsh(seed + k)
        c = cols[k % len(cols)]
        sd = seed + 100 + k * 7
        if kind == 0:
            blob(cv, rot(np.array([(x, y - r), (x + r * 0.9, y + r * 0.6), (x - r * 0.9, y + r * 0.6)]), ang, x, y), c, w=3.0, seed=sd, boil=0.6, n=2, a=a)
        elif kind == 1:
            pts = rot(np.array([(x - r * 1.4 + j * r * 0.35, y + r * 0.35 * math.sin(j * 1.6 + t * 2)) for j in range(9)]), ang, x, y)
            line(cv, pts, 9 * s + 2, INK, seed=sd, boil=0.5, n=4, taper=(0, 0), a=a)
            line(cv, pts, 6 * s, c, seed=sd, boil=0.5, n=4, taper=(0, 0), a=a)
        elif kind == 2:
            pts = rot(np.array([(x - r * 1.2 + j * r * 0.4, y + (r * 0.3 if j % 2 else -r * 0.3)) for j in range(7)]), ang, x, y)
            brush(cv, pts, 8 * s + 2, INK, taper=(0, 0), seed=sd, a=a)
            brush(cv, pts, 5 * s, c, taper=(0, 0), seed=sd, a=a)
        elif kind == 3:
            pp = cr_closed(jit(ell(x, y, r * 0.8, r * 0.8, n=10), 0.8, sd), 3)
            brush(cv, pp, 11 * s + 3, INK, closed=True, seed=sd, a=a)
            brush(cv, pp, 7 * s, c, closed=True, seed=sd, a=a)
        elif kind == 4:
            pts = [(x + (i - 1) * r * 0.55, y + (j - 1) * r * 0.55) for i in range(3) for j in range(3)]
            dots(cv, rot(np.array(pts), ang, x, y), 3.5 * s + 1.2, c, a=a)
        else:
            for dd in (0, 90):
                pts = rot(np.array([(x - r * 0.7, y), (x + r * 0.7, y)]), ang + dd, x, y)
                line(cv, pts, 9 * s + 3, INK, seed=sd + dd, boil=0.4, n=2, taper=(0, 0), a=a)
                line(cv, pts, 6 * s, c, seed=sd + dd, boil=0.4, n=2, taper=(0, 0), a=a)


def laser_beams(cv, t, seed=0, cols=None, a=40, n=6, y0=1100, spread=0.006):
    """Sweeping stage lasers fanning up from the floor corners."""
    cols = cols or [P_["teal"], P_["hotpink"], P_["acid"]]
    for k in range(n):
        side = -1 if k % 2 == 0 else 1
        bx = 960 + side * 1100
        ang = math.radians(-90 + side * (-38 + 26 * math.sin(t * (0.7 + 0.15 * k) + k * 1.3)))
        L = 2200
        p1 = (bx + L * math.cos(ang - spread), y0 + L * math.sin(ang - spread))
        p2 = (bx + L * math.cos(ang + spread), y0 + L * math.sin(ang + spread))
        cv.drawPath(poly_path([(bx, y0), p1, p2]), _lin(bx, y0, (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2, [cols[k % len(cols)], cols[k % len(cols)]], a=a))


def starburst(cv, x, y, r, t, rgb=None, rgb2=None, seed=0, n=16, text=None, text2=None, size=44, tcol=None, rot_deg=-10.0, a=255):
    """A yellow infomercial starburst badge ('ALL NEW!') with jaunty text."""
    rgb = rgb or P_["yellow"]
    pts = []
    for k in range(n * 2):
        ang = k * math.pi / n + t * 0.4
        rr = r * (1.0 if k % 2 == 0 else 0.78)
        pts.append((x + rr * math.cos(ang), y + rr * math.sin(ang)))
    blob(cv, pts, rgb, w=5, seed=seed, boil=0.9, n=2, a=a,
         shade=lambda c: c.drawCircle(x + r * 0.2, y + r * 0.25, r * 0.85, paint(rgb2 or P_["orange"], 90)))
    cv.save(); cv.translate(x, y); cv.rotate(rot_deg)
    if text:
        paint_text(cv, text, 0, (-size * 0.12 if text2 else size * 0.36), font="bangers", size=size, fill=tcol or P_["red"], ink_w=3.5, shadow=(3, 3),
                   shadow_rgb=INK, seed=seed + 3, streaks=False, a=a)
    if text2:
        paint_text(cv, text2, 0, size * 0.92, font="bangers", size=size * 0.8, fill=tcol or P_["red"], ink_w=3.0, shadow=(3, 3), seed=seed + 4,
                   streaks=False, a=a)
    cv.restore()


def lens_flare(cv, x, y, t, k=1.0, seed=0):
    """A cheesy anamorphic flare: hot core, horizontal streak and a row of ghost discs."""
    if k <= 0.01:
        return
    cv.drawCircle(x, y, 180 * k, _rad2(x, y, 180 * k, P_["white"], int(200 * k)))
    cv.drawRect(R(x - 700 * k, y - 4, x + 700 * k, y + 4), _lin(x - 700 * k, y, x + 700 * k, y, [P_["teal"], P_["white"], P_["teal"]], [0.0, 0.5, 1.0], a=int(170 * k)))
    for u, r, c in ((0.35, 26, P_["hotpink"]), (0.6, 14, P_["acid"]), (0.85, 40, P_["teal"]), (1.2, 20, P_["yellow"])):
        gx, gy = x + (960 - x) * u * 2, y + (540 - y) * u * 2
        cv.drawCircle(gx, gy, r * k * 1.6, paint(c, int(60 * k)))
    sparkle(cv, x, y, 60 * k, P_["white"], w=2.5, seed=seed)


def tv_static(cv, rect, seed=0, a=255, density=900):
    x0, y0, x1, y1 = rect
    rng = np.random.default_rng(int(core.D) * 13 + seed)
    xs = rng.uniform(x0, x1, density); ys = rng.uniform(y0, y1, density); g = rng.uniform(0, 1, density)
    for lo, hi in ((0.0, 0.33), (0.33, 0.66), (0.66, 1.01)):
        m = (g >= lo) & (g < hi)
        dots(cv, np.stack([xs[m], ys[m]], 1), 2.6, mix(P_["night"], P_["white"], 0.2 + hi * 0.8), a=a)


# ===================================================================== the product
def cave_screen(cv, rect, T, seed=7100, kinds=("bunny", "horse", "bird"), speed=0.1, heads=2, fire=True, ss=None, y_rel=0.42):
    """THE CAVE PHONE SCREEN: a tiny firelit cave wall (wall_surface) with puppet shadows drifting across, a little fire
    licking up from the bottom bezel and the silhouettes of two tiny prisoners' heads."""
    x0, y0, x1, y1 = rect
    wd, ht = x1 - x0, y1 - y0
    wall_surface(cv, [(x0 - 6, y0 - 6), (x1 + 6, y0 - 6), (x1 + 6, y1 + 6), (x0 - 6, y1 + 6)], T, seed=seed, cx=(x0 + x1) / 2, cy=y0 + ht * 0.72)
    ss = ss or wd / 230.0
    for k, kind in enumerate(kinds):
        ph = (T * speed + k / len(kinds)) % 1.0
        sx = x1 + wd * 0.7 - ph * wd * 2.4
        shadow_shape(cv, kind, sx, y0 + ht * (y_rel + 0.07 * math.sin(k * 2.1)) + 6 * math.sin(T * 2 + k), ss, T, seed=seed + 10 + k)
    firelight(cv, (x0 + x1) / 2, y1 + ht * 0.04, wd * 0.95, T, a=150, seed=seed)
    if fire:
        old = _ink(wd / 600)
        cave_fire(cv, (x0 + x1) / 2, y1 + 4, wd / 700, T, seed=seed + 30, logs=False)
        core.INKMUL = old
    for k in range(heads):
        hx = x0 + wd * (0.3 + 0.4 * k)
        hr = wd * 0.16
        hy = y1 + hr * 0.25 + 2 * math.sin(T * 1.6 + k)
        blob(cv, ell(hx, hy, hr, hr * 1.05, n=10), (24, 10, 40), w=3, seed=seed + 50 + k, boil=0.8)
        line(cv, [(hx - hr * 0.5, hy - hr * 0.66), (hx, hy - hr * 0.78), (hx + hr * 0.5, hy - hr * 0.66)], 2.5, P_["yellow"], seed=seed + 60 + k, boil=0.5, n=4, a=170)


def feed_screen(cv, rect, T, offset, seed=7300, blur=0.0, likes=True):
    """INFINITE SCROLL: a vertical feed of shadow 'posts' (little firelit walls with a shadow, a like count), scrolled by
    `offset` px. blur 0..1 smears it into speed streaks."""
    x0, y0, x1, y1 = rect
    wd, ht = x1 - x0, y1 - y0
    cv.drawRect(R(x0 - 5, y0 - 5, x1 + 5, y1 + 5), paint((40, 14, 30)))
    kinds = ["bunny", "horse", "bird", "fish", "tree", "person", "jug", "star", "hand_bunny"]
    ph = wd * 1.12
    j0 = int(math.floor(offset / ph)) - 1
    for j in range(j0, j0 + int(ht / ph) + 3):
        py0 = y0 + j * ph - offset
        if py0 > y1 or py0 + ph < y0:
            continue
        cx0, cx1 = x0 + wd * 0.06, x1 - wd * 0.06
        cy0, cy1 = py0 + wd * 0.18, py0 + ph - wd * 0.1
        cv.drawRect(R(cx0, cy0, cx1, cy1), _rad((cx0 + cx1) / 2, cy1, (cy1 - cy0) * 1.2, [P_["yellow"], CV_WALL, CV_WALL2, mix(CV_WALL2, P_["red"], 0.5)],
                                               [0.0, 0.3, 0.7, 1.0]))
        kind = kinds[int(hsh(seed + j * 1.3) * len(kinds)) % len(kinds)]
        shadow_shape(cv, kind, (cx0 + cx1) / 2 + 6 * math.sin(T * 2 + j), (cy0 + cy1) / 2 + 4, (cx1 - cx0) / 260, T, seed=seed + j * 3, wobble=0.6)
        brush(cv, np.array([(cx0, cy0), (cx1, cy0), (cx1, cy1), (cx0, cy1)]), 3.0, closed=True, seed=seed + j * 5)
        dots(cv, [(cx0 + wd * 0.06, py0 + wd * 0.09)], wd * 0.045, [P_["teal"], P_["hotpink"], P_["acid"]][j % 3])
        line(cv, [(cx0 + wd * 0.14, py0 + wd * 0.09), (cx0 + wd * 0.5, py0 + wd * 0.09)], wd * 0.03, P_["cream"], seed=seed + j * 7, boil=0.3, n=2, taper=(0, 0), a=200)
        if likes:
            hx, hy, hs = cx0 + wd * 0.07, cy1 + wd * 0.05, wd * 0.035
            hp = [(hx, hy + hs), (hx - hs * 1.3, hy - hs * 0.2), (hx - hs * 0.7, hy - hs * 1.1), (hx, hy - hs * 0.4), (hx + hs * 0.7, hy - hs * 1.1), (hx + hs * 1.3, hy - hs * 0.2)]
            cv.drawPath(poly_path(cr_closed(hp, 3)), paint(P_["hotpink"]))
            n = int(hsh(seed + j * 9.1) * 990) + 9
            paint_text(cv, f"{n}K", hx + wd * 0.06, hy + hs * 0.9, font="londrina", size=wd * 0.07, fill=P_["cream"], ink_w=0, shadow=None, seed=seed + j,
                       streaks=False, align="left", wobble=0.3)
    if blur > 0.02:
        for k in range(int(10 * blur)):
            xx = x0 + wd * hsh(k * 3.3 + core.D * 0.7)
            line(cv, [(xx, y0), (xx, y1)], 3 + 9 * hsh(k), P_["cream"], seed=seed + 200 + k, boil=0.3, n=2, taper=(0.2, 0.2), a=int(90 * blur))
        cv.drawRect(R(x0, y0, x1, y1), paint(CV_WALL, int(110 * blur)))


def phone(cv, cx, cy, h, T, yaw=0.0, roll=0.0, screen=None, seed=7500, rim=None, body=None, glow=0.0, ink=5.5, logo=True):
    """THE CAVE PHONE PRO: a glossy slab (height h, centre cx, cy) that can spin about its vertical axis (yaw degrees,
    0 = facing camera) and roll. Front: black glass + gold rim + the screen callback screen(cv, (x0, y0, x1, y1)) drawn
    in screen-local coords (clipped). Back: violet cave-rock with a chrome CAVE logo and a camera bump with a flame lens."""
    rim = rim or P_["gold"]
    body = body or CV_ROCK2
    wdt = h * 0.49
    d = h * 0.075
    ca, sa = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    fw = max(2.0, wdt * abs(ca))
    sw = d * abs(sa)
    sgn = 1 if sa >= 0 else -1
    cv.save()
    cv.translate(cx, cy)
    cv.rotate(roll)
    if glow > 0:
        cv.drawCircle(0, 0, h * 0.95, _rad2(0, 0, h * 0.95, P_["orange"], int(120 * glow)))
    fx = -sgn * sw / 2
    hh = h / 2
    rr = h * 0.11
    if sw > 1.5:                                                  # the edge band (metal) with its buttons
        ex0, ex1 = (fx + fw / 2 - 2, fx + fw / 2 + sw) if sgn > 0 else (fx - fw / 2 - sw, fx - fw / 2 + 2)
        band = rrect_pts(ex0, -hh, ex1, hh, rr, n=3, sx=min(1.0, sw / (2 * rr) + 0.05))
        blob(cv, band, mix(rim, INK, 0.25), w=ink, seed=seed + 1, boil=0.7, n=3,
             shade=lambda c: (c.drawRect(R(ex0, -hh, ex1, hh), _lin(ex0, 0, ex1, 0, [mix(rim, P_["white"], 0.5), rim, mix(rim, INK, 0.45)]))))
        for k in range(2):
            by0 = -hh * 0.55 + k * h * 0.13
            c0 = (ex0 + ex1) / 2
            blob(cv, rect_pts([(c0 - sw * 0.25, by0), (c0 + sw * 0.25, by0), (c0 + sw * 0.25, by0 + h * 0.09), (c0 - sw * 0.25, by0 + h * 0.09)], 2),
                 mix(rim, INK, 0.4), w=2.5, seed=seed + 5 + k, boil=0.4, n=2)
    fr = rrect_pts(fx - fw / 2, -hh, fx + fw / 2, hh, rr, n=4, sx=abs(ca))
    front = ca >= 0
    if front:
        def sh(c):
            c.drawRect(R(fx - fw / 2 - 10, -hh - 10, fx + fw / 2 + 10, hh + 10), _lin(fx - fw / 2, -hh, fx + fw / 2, hh, [mix(rim, P_["white"], 0.55), rim, GOLD_DK, rim]))
        blob(cv, fr, rim, w=ink, seed=seed + 10, boil=0.8, n=3, shade=sh)
        inset = h * 0.022
        g0 = rrect_pts(fx - fw / 2 + inset * abs(ca), -hh + inset, fx + fw / 2 - inset * abs(ca), hh - inset, rr * 0.82, n=4, sx=abs(ca))
        blob(cv, g0, GLASS, w=2.5, seed=seed + 11, boil=0.5, n=3)
        sx0, sy0, sx1, sy1 = -wdt / 2 + h * 0.045, -hh + h * 0.07, wdt / 2 - h * 0.045, hh - h * 0.05
        clip = rrect_path(fx + sx0 * abs(ca), sy0, fx + sx1 * abs(ca), sy1, rr * 0.55)
        cv.save()
        cv.clipPath(clip, doAntiAlias=True)
        cv.translate(fx, 0)
        cv.scale(max(0.02, abs(ca)), 1.0)
        if screen is not None:
            screen(cv, (sx0, sy0, sx1, sy1))
        else:
            cv.drawRect(R(sx0, sy0, sx1, sy1), paint(P_["night"]))
        cv.restore()
        cv.save()
        cv.clipPath(clip, doAntiAlias=True)                       # glass sheen
        cv.drawPath(poly_path([(fx - fw * 0.6, -hh), (fx - fw * 0.05, -hh), (fx - fw * 0.6, hh * 0.15)]), paint(P_["white"], 46))
        cv.drawPath(poly_path([(fx + fw * 0.1, -hh), (fx + fw * 0.22, -hh), (fx - fw * 0.5, hh * 0.6), (fx - fw * 0.62, hh * 0.6)]), paint(P_["white"], 26))
        cv.restore()
        brush(cv, cr_closed(rrect_pts(fx + sx0 * abs(ca), sy0, fx + sx1 * abs(ca), sy1, rr * 0.55, n=3, sx=abs(ca)), 3), 3.0, closed=True, seed=seed + 12)
        pw = h * 0.16 * abs(ca)                                   # the notch pill: speaker + camera
        blob(cv, rrect_pts(fx - pw / 2, -hh + h * 0.03, fx + pw / 2, -hh + h * 0.058, h * 0.014, n=2, sx=abs(ca)), INK, w=0, seed=seed + 13, boil=0.3, n=3,
             misreg=(0, 0))
        dots(cv, [(fx + pw * 0.3, -hh + h * 0.044)], h * 0.007 + 0.5, (60, 80, 140))
    else:
        bc = body

        def shb(c):
            stipple(c, mix(bc, INK, 0.4), (fx - fw / 2, -hh, fx + fw / 2, hh), spacing=max(6, h * 0.025), r=max(1.0, h * 0.004), seed=seed + 20,
                    fn=lambda X, Y: np.clip(0.3 + 0.7 * np.sin(X * 0.03 + Y * 0.02) ** 2, 0, 1) * 0.8)
            for k in range(5):
                yy = -hh + h * (0.15 + 0.17 * k)
                c.drawLine(fx - fw / 2, yy, fx + fw / 2, yy + h * 0.02 * math.sin(k * 2), paint(mix(bc, INK, 0.3), stroke=max(1.5, h * 0.006)))
            c.drawRect(R(fx + fw * 0.2, -hh, fx + fw / 2 + 4, hh), paint(P_["magenta"], 60))
        blob(cv, fr, bc, w=ink, seed=seed + 21, boil=0.8, n=3, shade=shb)
        brush(cv, cr_closed(fr, 3), max(2.0, h * 0.012), rgb=rim, closed=True, seed=seed + 22)
        bx, by, bs = fx + fw * 0.18 * (1 if ca < 0 else -1), -hh + h * 0.14, h * 0.13
        blob(cv, rrect_pts(bx - bs * abs(ca), by - bs, bx + bs * abs(ca), by + bs, bs * 0.4, n=3, sx=abs(ca)), mix(bc, INK, 0.35), w=3.5, seed=seed + 23, boil=0.5, n=3)
        for k, (lx, ly) in enumerate(((-0.45, -0.45), (0.45, -0.45), (-0.45, 0.45))):
            px_, py_ = bx + lx * bs * abs(ca), by + ly * bs
            blob(cv, ell(px_, py_, bs * 0.36 * abs(ca) + 1, bs * 0.36, n=8), INK, w=2.5, seed=seed + 24 + k, boil=0.4)
            if k == 2:
                dots(cv, [(px_, py_)], bs * 0.2, P_["orange"])
                dots(cv, [(px_, py_ - bs * 0.06)], bs * 0.1, P_["yellow"])
            else:
                dots(cv, [(px_ - bs * 0.08 * abs(ca), py_ - bs * 0.08)], bs * 0.08, P_["white"])
        if logo and abs(ca) > 0.35:
            cv.save(); cv.translate(fx, h * 0.05); cv.scale(abs(ca), 1.0)
            blob(cv, [(0, -h * 0.13), (h * 0.06, -h * 0.03), (h * 0.035, h * 0.04), (-h * 0.035, h * 0.04), (-h * 0.06, -h * 0.03)], P_["orange"], w=3.5,
                 seed=seed + 30, boil=0.7, n=4)
            blob(cv, [(0, -h * 0.07), (h * 0.03, -h * 0.01), (0, h * 0.03), (-h * 0.03, -h * 0.01)], P_["yellow"], w=0, seed=seed + 31, boil=0.6, n=4, misreg=(0, 0))
            chrome_text(cv, "CAVE", 0, h * 0.2, h * 0.11, font="titan", seed=seed + 32, depth=h * 0.012, ink=2.5, glints=1, skew=0)
            cv.restore()
    cv.restore()


def pedestal(cv, x, y, wdt, t, seed=7600, top=None, rgb=None):
    """A glossy turntable pedestal with a neon ring (top surface centred at x, y)."""
    top = top or P_["violet"]
    rgb = rgb or P_["night"]
    ht = wdt * 0.42
    blob(cv, [(x - wdt / 2, y), (x - wdt * 0.42, y + ht), (x + wdt * 0.42, y + ht), (x + wdt / 2, y)], rgb, w=5, seed=seed, boil=0.8, n=3,
         shade=lambda c: (c.drawRect(R(x - wdt / 2, y, x + wdt / 2, y + ht), _lin(x - wdt / 2, 0, x + wdt / 2, 0, [mix(rgb, P_["teal"], 0.5), rgb, mix(rgb, P_["magenta"], 0.4)])),
                          [c.drawLine(x - wdt * 0.46 + k * wdt * 0.1, y, x - wdt * 0.38 + k * wdt * 0.085, y + ht, paint(mix(rgb, P_["white"], 0.15), stroke=2)) for k in range(10)]))
    blob(cv, ell(x, y, wdt / 2, wdt * 0.09, n=16), top, w=5, seed=seed + 1, boil=0.8,
         shade=lambda c: c.drawPath(poly_path(cr_closed(ell(x, y + wdt * 0.02, wdt * 0.42, wdt * 0.05, n=12), 3)), paint(mix(top, P_["white"], 0.3))))
    for k in range(10):
        a = t * 2.0 + k * 0.628
        if math.sin(a) > 0:
            dots(cv, [(x + wdt * 0.47 * math.cos(a), y + wdt * 0.085 * math.sin(a) + 3)], 5, [P_["teal"], P_["hotpink"], P_["yellow"]][k % 3])
    cv.drawRect(R(x - wdt / 2, y + ht * 0.55, x + wdt / 2, y + ht * 0.62), paint(P_["teal"], 200))


# ===================================================================== eyeball folk (the audience/prisoners, now modern)
def eyefolk(cv, x, y, s, T, seed=8000, look=(0.0, 0.0), lid=0.2, rgb=None, iris=None, glow=None, phone_at=None, arms=True, squint=0.0,
            pupil=1.0, mouth=0.0, nod=0.0, sweat=0.0, brace=False, bow=None, phone_scr=None, eye_r=None, body_h=1.0, tilt=0.0, phone_back=True,
            collar=None, smile=0.0):
    """A squat eyeball creature (the BOXED audience / cave prisoners) sitting at floor point (x, y): dome body, one huge eye
    with a lid, stubby rubber-hose arms. phone_at=(px, py) puts a glowing phone in its mitts (light rakes up its eye).
    glow=rgb tints it with screen light. nod 0..1 bobs the head-body. brace adds a foam neck brace."""
    rgb = rgb or [(64, 30, 110), (90, 40, 150), (46, 20, 86), (110, 50, 120)][int(hsh(seed) * 4)]
    iris = iris or [P_["teal"], P_["hotpink"], P_["acid"], P_["orange"]][int(hsh(seed + 1) * 4)]
    bob = (2.5 * math.sin(T * 1.7 + seed) + 10 * nod) * s
    r = 70 * s
    cx, cy = x, y - r * 1.15 * body_h + bob
    cv.save()
    if tilt:
        cv.rotate(tilt, x, y)
    body = [(x - r * 1.05, y), (x - r * 1.12, cy), (x - r * 0.7, cy - r * 0.95), (x, cy - r * 1.12), (x + r * 0.7, cy - r * 0.95), (x + r * 1.12, cy),
            (x + r * 1.05, y)]
    blob(cv, body, rgb, w=5.0 * min(1.0, s * 1.4) + 1.2, seed=seed, boil=1.0, n=5,
         shade=lambda c: c.drawPath(poly_path(cr_closed(ell(cx + r * 0.45, cy + r * 0.3, r * 0.9, r * 1.1, n=10), 3)), paint(mix(rgb, INK, 0.3))))
    if bow is not None:
        bx, by = cx + r * 0.55, cy - r * 0.95
        for sd in (-1, 1):
            blob(cv, [(bx, by), (bx + sd * r * 0.4, by - r * 0.22), (bx + sd * r * 0.42, by + r * 0.2)], bow, w=3, seed=seed + 70 + sd, boil=0.5, n=2)
        dots(cv, [(bx, by)], r * 0.09, mix(bow, INK, 0.2))
    er = eye_r if eye_r is not None else r * 0.5
    ex, ey = cx + look[0] * r * 0.12, cy - r * 0.2 + look[1] * r * 0.06
    blob(cv, ell(ex, ey, er, er * 1.05, n=11), P_["white"], w=3.5 * min(1.0, s * 1.5) + 1, seed=seed + 5, boil=0.7,
         shade=lambda c: [c.drawLine(ex + er * math.cos(a), ey + er * math.sin(a), ex + er * 0.7 * math.cos(a + 0.2), ey + er * 0.7 * math.sin(a + 0.2),
                                     paint(P_["red"], 150, stroke=max(1.0, 1.6 * s))) for a in (0.6, 2.3, 3.6, 5.1)])
    ir = er * 0.56
    ix, iy = ex + look[0] * er * 0.38, ey + look[1] * er * 0.38
    dots(cv, [(ix, iy)], ir, iris)
    dots(cv, [(ix, iy)], ir * 0.5 * pupil, INK)
    dots(cv, [(ix - ir * 0.32, iy - ir * 0.36)], ir * 0.2 + 0.6, P_["white"])
    ld = float(np.clip(max(lid, squint), 0, 1))
    if ld > 0.03:                                                  # the lid sheet (squints come down hard)
        cv.save(); cv.clipPath(poly_path(cr_closed(ell(ex, ey, er + 1.5, er * 1.05 + 1.5, n=12), 4)), doAntiAlias=True)
        yl = ey - er * 1.05 + 2 * er * 1.05 * ld
        cv.drawRect(R(ex - er - 4, ey - er * 1.2, ex + er + 4, yl), paint(mix(rgb, P_["white"], 0.12)))
        cv.restore()
        line(cv, [(ex - er * 0.98, yl + 1), (ex, yl + er * 0.08), (ex + er * 0.98, yl + 1)], 3.0 * min(1.0, s * 1.5) + 1, seed=seed + 7, boil=0.5, n=4)
    if squint > 0.4:
        for sd in (-1, 1):
            for j in range(2):
                line(cv, [(ex + sd * er * (1.1 + 0.05 * j), ey - er * 0.3 + j * er * 0.4), (ex + sd * er * (1.45 + 0.05 * j), ey - er * 0.45 + j * er * 0.55)],
                     2.6, seed=seed + 40 + j + sd * 3, boil=0.5, n=2, taper=(0.2, 0.2))
    if mouth > 0.05:
        blob(cv, ell(cx, cy + r * 0.48, r * 0.2, r * 0.06 + r * 0.2 * mouth, n=8), P_["mouth"], w=2.5, seed=seed + 8, boil=0.5)
    elif smile > 0.05:
        line(cv, [(cx - r * 0.3, cy + r * 0.44), (cx, cy + r * (0.44 + 0.16 * smile)), (cx + r * 0.3, cy + r * 0.44)], 3.0 * min(1.0, s * 1.5) + 1, seed=seed + 8,
             boil=0.5, n=4, taper=(0.25, 0.25))
    if sweat > 0.02:
        ph = (T * 1.3 + seed) % 1.0
        sx_, sy_ = ex + er * 1.1, ey - er * 0.6 + er * 0.8 * ph
        blob(cv, [(sx_, sy_ - 12 * s), (sx_ + 7 * s, sy_ + 2 * s), (sx_, sy_ + 8 * s), (sx_ - 7 * s, sy_ + 2 * s)], P_["mint"], w=2.5, seed=seed + 9, boil=0.5, n=4,
             a=int(255 * min(1, sweat)))
    if collar is not None:
        ny = cy + r * 0.62
        cpts = [(cx - r * 1.08, ny - r * 0.1), (cx, ny + r * 0.08), (cx + r * 1.08, ny - r * 0.1), (cx + r * 1.1, ny + r * 0.02), (cx, ny + r * 0.2),
                (cx - r * 1.1, ny + r * 0.02)]
        blob(cv, cpts, collar, w=3.5, seed=seed + 11, boil=0.6,
             shade=lambda c: c.drawPath(poly_path([(cx - r * 1.2, ny + r * 0.02), (cx, ny + r * 0.12), (cx + r * 1.2, ny + r * 0.02), (cx + r * 1.2, ny + r * 0.3),
                                                   (cx - r * 1.2, ny + r * 0.3)]), paint(mix(collar, INK, 0.3))))
        blob(cv, ell(cx + r * 0.3, ny + r * 0.24, r * 0.1, r * 0.13, n=8), collar, w=3, seed=seed + 13, boil=0.4)
    if brace:
        by = cy + r * 0.42
        blob(cv, rrect_pts(cx - r * 0.95, by - r * 0.2, cx + r * 0.95, by + r * 0.22, r * 0.2, n=3), P_["cream"], w=3.5, seed=seed + 12, boil=0.6, n=3,
             shade=lambda c: [c.drawLine(cx - r * 0.8 + k * r * 0.32, by - r * 0.2, cx - r * 0.8 + k * r * 0.32, by + r * 0.22, paint(P_["cream_sh"], stroke=2.5))
                              for k in range(6)])
    cv.restore()
    if isinstance(phone_at, str):
        phone_at = (cx + 4 * s, cy + r * 0.8)
    if phone_at is not None:
        px, py = phone_at
        ph_h = 64 * s
        if glow is not None:
            cv.drawCircle(px, py - ph_h * 0.4, r * 2.2, _rad2(px, py - ph_h * 0.4, r * 2.2, glow, 70))
        if arms:
            for sd in (-1, 1):
                sh = (cx + sd * r * 0.85, cy + r * 0.35)
                hand = (px + sd * ph_h * 0.32, py + ph_h * 0.22)
                tube(cv, [sh, ((sh[0] + hand[0]) / 2 + sd * 10 * s, (sh[1] + hand[1]) / 2 + 12 * s), hand], 13 * s + 1, rgb, w=3.0, seed=seed + 20 + sd, boil=0.6, n=5)
        ph_w = ph_h * 0.52
        scr = phone_scr or glow or P_["mint"]
        if phone_back:
            blob(cv, rrect_pts(px - ph_w / 2, py - ph_h / 2, px + ph_w / 2, py + ph_h / 2, ph_h * 0.12, n=2), mix(GLASS, scr, 0.15), w=2.5 + s, seed=seed + 25,
                 boil=0.5, n=3, shade=lambda c: c.drawRect(R(px + ph_w * 0.25, py - ph_h, px + ph_w, py + ph_h), paint(scr, 90)))
            dots(cv, [(px - ph_w * 0.22, py - ph_h * 0.33)], ph_h * 0.06 + 0.5, (70, 70, 100))
            line(cv, [(px - ph_w * 0.5, py - ph_h * 0.52), (px + ph_w * 0.5, py - ph_h * 0.52)], 3 + 2 * s, mix(scr, P_["white"], 0.6), seed=seed + 26, boil=0.3, n=2,
                 taper=(0.2, 0.2), a=200)
        else:
            blob(cv, rrect_pts(px - ph_w / 2, py - ph_h / 2, px + ph_w / 2, py + ph_h / 2, ph_h * 0.12, n=2), GLASS, w=2.5 + s, seed=seed + 25, boil=0.5, n=3)
            cv.drawRect(R(px - ph_w * 0.38, py - ph_h * 0.4, px + ph_w * 0.38, py + ph_h * 0.4), paint(mix(scr, P_["white"], 0.45)))
        if arms:
            for sd in (-1, 1):
                blob(cv, ell(px + sd * ph_w * 0.55, py + ph_h * 0.22, 9 * s + 1, 11 * s + 1, n=7), rgb, w=2.5, seed=seed + 27 + sd, boil=0.5)
    if glow is not None:                                          # screen light raking the face
        cv.drawCircle(ex, ey, er * 1.7, _rad2(ex, ey + er * 0.6, er * 1.7, glow, 60))


def gary_bent(cv, x, y, s, T, neck=0.0, look=(0.0, 0.0), loud=None, seed=4400, lid=None, arm_l=None, arm_r=None, thumbs=0.0, strain=0.0, glow=None):
    """GARY (same build as eyeball_creature: striped cream sweater, red G, violet lid, teal iris, mouth under the iris) with
    a controllable gaze and a bendable neck: the eyeball rotates `neck` degrees about the collar (positive = toward screen
    right). arm_r=(hx, hy) draws his right arm reaching to that point (world coords) holding something there.
    thumbs 0..1 raises his left hand in a thumbs-up."""
    loud = spk_loud("AUD", T) if loud is None else loud
    bob = 4 * math.sin(T * 3.1) * s
    blob(cv, [(x - 128 * s, y + 360 * s), (x - 110 * s, y + 170 * s), (x - 55 * s, y + 112 * s), (x + 55 * s, y + 112 * s), (x + 110 * s, y + 170 * s),
              (x + 128 * s, y + 360 * s)], P_["cream"], w=5, seed=seed, boil=1.0, n=6,
         shade=lambda c: [c.drawRect(R(x - 140 * s, y + (232 + k * 46) * s, x + 140 * s, y + (250 + k * 46) * s), paint(P_["orange"])) for k in range(3)])
    paint_text(cv, "G", x, y + 300 * s, font="shrik", size=76 * s, fill=P_["red"], ink_w=4, shadow=None, seed=seed + 30, streaks=False)
    # left arm: hanging, or a thumbs-up
    sh = (x - 104 * s, y + 190 * s)
    if thumbs > 0:
        k = ease(thumbs)
        hx, hy = lerp(x - 140 * s, x - 215 * s, k), lerp(y + 330 * s, y + 60 * s, k)
        el = (lerp(x - 150 * s, x - 215 * s, k), lerp(y + 250 * s, y + 200 * s, k))
        tube(cv, [sh, el, (hx, hy)], 22 * s, P_["cream"], w=4.5, seed=seed + 50, boil=0.8, n=8)
        cv.save(); cv.translate(hx, hy); cv.scale(s * 1.15, s * 1.15)
        _hand(cv, 0, 0, -90, "fist", 1, seed + 52, rgb=P_["white"])
        tube(cv, [(16, -10), (18, -34), (14, -52)], 13, P_["white"], w=4.0, seed=seed + 53, boil=0.6, n=4)
        cv.restore()
    elif arm_l is not None:
        hx, hy = arm_l
        tube(cv, [sh, ((sh[0] + hx) / 2 - 30 * s, (sh[1] + hy) / 2 + 40 * s), (hx, hy)], 22 * s, P_["cream"], w=4.5, seed=seed + 50, boil=0.8, n=8)
        cv.save(); cv.translate(hx, hy); cv.scale(s * 1.15, s * 1.15)
        _hand(cv, 0, 0, -30, "hold", 1, seed + 52, rgb=P_["white"])
        cv.restore()
    else:
        tube(cv, [sh, (x - 150 * s, y + 250 * s), (x - 140 * s, y + 330 * s)], 22 * s, P_["cream"], w=4.5, seed=seed + 50, boil=0.8, n=8)
        cv.save(); cv.translate(x - 140 * s, y + 330 * s); cv.scale(s * 1.15, s * 1.15)
        _hand(cv, 0, 0, 100, "open", 1, seed + 52, rgb=P_["white"])
        cv.restore()
    # the eyeball head, bent about the collar
    piv = (x + 6 * s, y + 118 * s)
    cv.save()
    cv.rotate(neck, piv[0], piv[1])
    blob(cv, ell(x, y + bob, 150 * s, 150 * s, n=14), P_["white"], w=6, seed=seed + 4, boil=1.2,
         shade=lambda c: [line(c, [(x + 150 * s * math.cos(a), y + bob + 150 * s * math.sin(a)), (x + 100 * s * math.cos(a + 0.25), y + bob + 100 * s * math.sin(a + 0.25))],
                               3.5, P_["red"], seed=seed + 10 + k, boil=0.8, n=3) for k, a in enumerate(np.linspace(0, 6.0, 8))])
    ir = 66 * s
    ex, ey = x - 4 * s + look[0] * 46 * s, y + bob - 22 * s + look[1] * 40 * s
    blob(cv, ell(ex, ey, ir, ir, n=11), P_["teal"], w=4.5, seed=seed + 5, boil=0.8,
         shade=lambda c: c.drawPath(poly_path(cr_closed(ell(ex + 10 * s, ey + 12 * s, ir * 0.8, ir * 0.75, n=8), 4)), paint(P_["tealdk"])))
    pr = ir * (0.42 + 0.22 * min(1.0, loud))
    blob(cv, ell(ex, ey, pr, pr, n=9), INK, w=0, seed=seed + 6, boil=0.5, misreg=(0, 0))
    dots(cv, [(ex - pr * 0.45, ey - pr * 0.5)], pr * 0.28, P_["white"])
    if glow is not None:
        cv.drawCircle(ex, ey + ir * 0.6, ir * 1.8, _rad2(ex, ey + ir * 0.6, ir * 1.8, glow, 90))
    ld = (0.25 + 0.2 * math.sin(T * 0.7)) if lid is None else lid
    blob(cv, [(x - 152 * s, y + bob - 20 * s), (x - 120 * s, y + bob - 110 * s), (x, y + bob - 156 * s), (x + 120 * s, y + bob - 110 * s), (x + 152 * s, y + bob - 20 * s),
              (x, y + bob - 150 * s + 300 * s * ld * 0.35)], P_["violet"], w=5, seed=seed + 7, boil=1.0, n=5)
    mo = min(1.0, loud * 1.5)
    mx, my = x + 6 * s + look[0] * 20 * s, y + bob + 92 * s
    if mo > 0.08:
        mh = (5 + 30 * mo) * s
        blob(cv, ell(mx, my + mh * 0.3, 34 * s, mh, n=10), P_["mouth"], w=4.5, seed=seed + 40, boil=0.7,
             shade=lambda c: blob(c, ell(mx + 4 * s, my + mh * 1.1, 22 * s, mh * 0.6, n=8), P_["tongue"], w=0, seed=seed + 41, boil=0.5, misreg=(0, 0)))
    else:
        line(cv, [(mx - 30 * s, my - 4 * s), (mx, my + 8 * s), (mx + 30 * s, my - 4 * s)], 4.5, seed=seed + 42, boil=0.6, n=6, taper=(0.3, 0.3))
    if strain > 0.05:
        for k in range(3):
            a = math.radians(-150 + k * 30)
            line(cv, [(x + 165 * s * math.cos(a), y + 165 * s * math.sin(a)), (x + (190 + 20 * strain) * s * math.cos(a), y + (190 + 20 * strain) * s * math.sin(a))],
                 5, seed=seed + 60 + k, boil=0.8, n=2, taper=(0.1, 0.4), a=int(255 * min(1.0, strain * 2)))
    cv.restore()
    if arm_r is not None:                                         # right arm reaching to the phone
        hx, hy = arm_r
        shr = (x + 104 * s, y + 190 * s)
        tube(cv, [shr, ((shr[0] + hx) / 2 + 40 * s, (shr[1] + hy) / 2 + 50 * s), (hx, hy)], 22 * s, P_["cream"], w=4.5, seed=seed + 64, boil=0.8, n=8)


# ===================================================================== legal crawl
LEGAL = ("Cave Phone Pro is a wall. It is not a window. Shadows shown are simulated; actual shadows may vary. Puppets sold separately. "
         "Fire not included. Battery lasts until the fire goes out. Not responsible for sunlight, enlightenment, philosophy, or the sudden "
         "understanding of Plato. SmartChains are non-removable by design. Do not turn around. Do not ask who is carrying the puppets. "
         "Do not look up. Infinite scroll is infinite. Side effects may include stiff neck, mistaking shadows for reality, forgetting the sun, "
         "mild Platonism, chronic nodding, believing everything, and the slow realization that you are the product. If your neck remains bent "
         "for more than six years, congratulations. Ask your cave if Cave Phone Pro is right for you. By looking at this screen you agree to keep "
         "looking at this screen. Void where enlightened. Some assembly of reality required. Your data will be used to make better shadows. "
         "Shadows are non-refundable. Cave Phone Pro, SmartChains and Don't Look Up are trademarks of Cave Corp., a subsidiary of The Wall. "
         "Offer not valid outside the cave. Consult your fire before starting any new reality. ")
_LEGAL_IMG = {}


def _legal_strip(wd, size):
    """The fine print rendered once per process into a tall transparent strip (drawing index pinned -> identical everywhere)."""
    key = (int(wd), int(size))
    if key not in _LEGAL_IMG:
        lines_ = wrap_lines((LEGAL * 2).upper(), "londrina_r", size, wd - 40)
        lh = size * 1.18
        ht = int(len(lines_) * lh + size)
        surf = skia.Surface.MakeRaster(skia.ImageInfo.Make(int(wd), ht, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType))
        c = surf.getCanvas()
        c.clear(skia.ColorTRANSPARENT)
        oldD = core.D
        core.D = 0
        try:
            for j, ln in enumerate(lines_):
                paint_text(c, ln, 20, (j + 1) * lh, font="londrina_r", size=size, fill=P_["cream"], ink_w=0, shadow=None, seed=9100 + (j % 40),
                           wobble=0.0, rot_jit=0.6, scale_jit=0.0, base_jit=0.6, streaks=False, align="left")
        finally:
            core.D = oldD
        _LEGAL_IMG[key] = (surf.makeImageSnapshot(), ht)
    return _LEGAL_IMG[key]


def legal_crawl(cv, rect, t, speed=320.0, size=23, seed=9100, a=255, rgb=None):
    """Tiny fine print racing upward inside rect (clipped), on a dark translucent panel."""
    x0, y0, x1, y1 = rect
    img, ht = _legal_strip(x1 - x0, size)
    cv.drawRect(R(x0, y0, x1, y1), paint(INK, int(a * 0.62)))
    cv.save(); cv.clipRect(R(x0, y0, x1, y1))
    m = (t * speed + (y1 - y0)) % ht
    jit_y = (hsh(core.D * 0.37) - 0.5) * 1.2
    for k in (-1, 0, 1):
        yy = y1 - m + k * ht + jit_y
        if yy < y1 and yy + ht > y0:
            cv.drawImage(img, x0, yy)
    cv.restore()
    cv.drawRect(R(x0, y0, x1, y0 + 18), paint(INK, int(a * 0.4)))


def gold_chain(cv, p0, p1, rgb=None, link=28.0, sag=30.0, w=5.0, seed=9400, glint=True, a=255, taut=0.0):
    """A chunky designer chain: alternating face-on rings and edge-on capsule links, inked, with a hot highlight and glints.
    taut 0..1 removes the sag (snapped tight)."""
    rgb = rgb or P_["gold"]
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = p1 - p0
    L = float(np.hypot(*d)) or 1.0
    n = max(2, int(L / (link * 0.78)))
    hi = mix(rgb, P_["white"], 0.6)
    dk = mix(rgb, INK, 0.35)
    sag = sag * (1 - taut)
    pts = []
    for k in range(n + 1):
        u = k / n
        pts.append(p0 + d * u + np.array([0.0, sag * math.sin(math.pi * u)]))
    for k in range(n):
        q0, q1 = pts[k], pts[k + 1]
        c = (q0 + q1) / 2
        dd = q1 - q0
        ang = math.degrees(math.atan2(dd[1], dd[0]))
        if k % 2 == 0:
            P = ell(c[0], c[1], link * 0.62, link * 0.4, n=12, rot=ang)
            Pc = cr_closed(jit(P, 0.5, seed + k), 3)
            brush(cv, Pc, link * 0.26 + w * 1.6, INK, closed=True, seed=seed + k, a=a)
            brush(cv, Pc, link * 0.22, rgb, closed=True, seed=seed + k, a=a)
            brush(cv, cr_closed(ell(c[0] - 1.5, c[1] - 2, link * 0.55, link * 0.32, n=12, rot=ang), 3)[:14], link * 0.06 + 0.8, hi, taper=(0.3, 0.3), seed=seed + k + 50, a=a)
        else:
            a0 = c - dd * 0.62
            a1 = c + dd * 0.62
            cv.drawLine(a0[0], a0[1], a1[0], a1[1], paint(INK, a, stroke=link * 0.3 + w * 1.6))
            cv.drawLine(a0[0], a0[1], a1[0], a1[1], paint(dk, a, stroke=link * 0.3))
            cv.drawLine(a0[0], a0[1] - link * 0.05, a1[0], a1[1] - link * 0.05, paint(rgb, a, stroke=link * 0.16))
            cv.drawLine(a0[0] + dd[0] * 0.1, a0[1] - link * 0.08, a1[0] - dd[0] * 0.3, a1[1] - link * 0.08, paint(hi, a, stroke=link * 0.05 + 0.6))
    if glint:
        for g in range(2):
            k = int(hsh(seed + g * 7 + int(core.D / 4)) * n)
            q = pts[k]
            sparkle(cv, q[0], q[1] - link * 0.2, link * (0.45 + 0.3 * math.sin(core.D * 0.8 + g)), P_["white"], w=1.6, seed=seed + 80 + g, a=a)


def stars_row(cv, x, y, size, t, t0, n=5, seed=9200, gap=None):
    """Five yellow review stars popping in one after another from shot time t0."""
    gap = gap or size * 1.15
    for k in range(n):
        kk = pop(t, t0 + k * 0.12, 0.3)
        if kk <= 0:
            continue
        cx = x + k * gap
        r = size * 0.5 * kk * (1 + 0.06 * math.sin(t * 6 + k))
        pts = []
        for j in range(10):
            ang = -math.pi / 2 + j * math.pi / 5
            rr = r if j % 2 == 0 else r * 0.45
            pts.append((cx + rr * math.cos(ang), y + rr * math.sin(ang)))
        blob(cv, pts, P_["yellow"], w=3.5, seed=seed + k, boil=0.6, n=2,
             shade=lambda c, cx=cx: c.drawPath(poly_path([(cx, y - size), (cx + size, y - size), (cx + size, y + size), (cx, y + size)]), paint(P_["gold"])))


def gloss_panel(cv, x0, y0, x1, y1, cols, seed=0, ink=5.0, r=24, a=255):
    """A glossy rounded 80s panel: vertical gradient + a top highlight band, brush-inked."""
    pts = rrect_pts(x0, y0, x1, y1, r, n=3)
    blob(cv, pts, cols[0], w=ink, seed=seed, boil=0.8, n=3, a=a,
         shade=lambda c: (c.drawRect(R(x0 - 10, y0 - 10, x1 + 10, y1 + 10), _lin(0, y0, 0, y1, cols, a=a)),
                          c.drawRect(R(x0 + r * 0.6, y0 + (y1 - y0) * 0.08, x1 - r * 0.6, y0 + (y1 - y0) * 0.3), paint(P_["white"], int(55 * a / 255)))))


def checkmark(cv, x, y, s, rgb=None, seed=9300, a=255):
    pts = [(x - 40 * s, y), (x - 10 * s, y + 32 * s), (x + 48 * s, y - 40 * s)]
    line(cv, pts, 26 * s + 6, INK, seed=seed, boil=0.6, n=3, taper=(0.1, 0.1), a=a)
    line(cv, pts, 18 * s, rgb or P_["acid"], seed=seed, boil=0.6, n=3, taper=(0.1, 0.1), a=a)


def red_x(cv, x, y, s, k=1.0, seed=9310, a=255):
    for j, (p0, p1) in enumerate((((-1, -1), (1, 1)), ((1, -1), (-1, 1)))):
        kk = float(np.clip(k * 2 - j, 0, 1))
        if kk <= 0:
            continue
        a0 = (x + p0[0] * 90 * s, y + p0[1] * 90 * s)
        a1 = (a0[0] + (p1[0] - p0[0]) * 90 * s * kk, a0[1] + (p1[1] - p0[1]) * 90 * s * kk)
        line(cv, [a0, a1], 44 * s + 8, INK, seed=seed + j, boil=0.8, n=2, taper=(0.1, 0.1), a=a)
        line(cv, [a0, a1], 34 * s, P_["red"], seed=seed + j, boil=0.8, n=2, taper=(0.1, 0.1), a=a)


def bw_layer(cv, contrast=1.35, bright=0.0):
    """saveLayer that renders everything until the matching restore() as contrasty black-and-white."""
    c = contrast
    o = 0.5 * (1 - c) + bright
    m = [0.3 * c, 0.59 * c, 0.11 * c, 0, o] * 3 + [0, 0, 0, 1, 0]
    cv.saveLayer(None, skia.Paint(ColorFilter=skia.ColorFilters.Matrix(m)))


# ===================================================================== T033 · THE INFOMERCIAL
def eyeguy(cv, x, y, s, T, seed=8500, walk=0.0, look=(0.0, 0.0), squint=0.0, shield=0.0, hold=1.0, dizzy=0.0, fall=0.0, mouth=0.0, sweat=0.0,
           flail=0.0, pupil=1.0):
    """The infomercial everyman: a big eyeball head on a shirt-and-tie bean body with rubber-hose limbs (x, y = feet).
    walk = walk-cycle phase; shield 0..1 lifts a hand over the eye; hold 0..1 = still carrying the groceries + coffee;
    fall 0..1 topples him onto his back; dizzy = spiral eye; flail waves the arms about."""
    cv.save()
    if fall > 0:
        cv.rotate(-94 * ease(fall), x - 50 * s, y)
    st = math.sin(walk * 2 * math.pi)
    lift = abs(math.cos(walk * 2 * math.pi)) * 8 * s if walk else 0.0
    for sd in (-1, 1):
        hip = (x + sd * 26 * s, y - 128 * s - lift)
        fx = x + sd * 30 * s + st * sd * 34 * s + (sd * 40 * s * ease(fall))
        knee = ((hip[0] + fx) / 2 + 10 * s, y - 64 * s - lift - 30 * s * ease(fall))
        tube(cv, [hip, knee, (fx, y - 12 * s)], 26 * s, (52, 64, 150), w=4.0, seed=seed + sd, boil=0.7, n=5)
        blob(cv, [(fx - 22 * s, y - 22 * s), (fx + 32 * s, y - 24 * s), (fx + 42 * s, y), (fx - 24 * s, y + 2 * s)], (36, 26, 30), w=3.5, seed=seed + 4 + sd,
             boil=0.6, n=3)
    bx, by = x, y - 128 * s - lift

    def tsh(c):
        c.drawRect(R(bx + 34 * s, by - 150 * s, bx + 100 * s, by + 20 * s), paint(P_["cream_sh"]))
        c.drawPath(poly_path([(bx - 15 * s, by - 136 * s), (bx + 15 * s, by - 136 * s), (bx + 12 * s, by - 34 * s), (bx, by - 14 * s), (bx - 12 * s, by - 34 * s)]),
                   paint(P_["red"]))
        for k in range(4):
            c.drawLine(bx - 14 * s, by - (122 - k * 24) * s, bx + 14 * s, by - (110 - k * 24) * s, paint(P_["maroon"], stroke=4.5 * s))
    blob(cv, [(bx - 66 * s, by + 8 * s), (bx - 82 * s, by - 80 * s), (bx - 50 * s, by - 138 * s), (bx + 50 * s, by - 138 * s), (bx + 82 * s, by - 80 * s),
              (bx + 66 * s, by + 8 * s)], P_["cream"], w=5, seed=seed + 10, boil=0.9, n=4, shade=tsh)
    for sd in (-1, 1):
        blob(cv, [(bx, by - 136 * s), (bx + sd * 38 * s, by - 142 * s), (bx + sd * 26 * s, by - 112 * s)], P_["white"], w=3.5, seed=seed + 12 + sd, boil=0.5, n=2)
    hx, hy, hr = bx, by - 236 * s, 104 * s
    # arms (behind the head when shielding)
    shL, shR = (bx - 70 * s, by - 112 * s), (bx + 70 * s, by - 112 * s)
    fl = math.sin(T * 14) * flail
    if shield > 0.01:
        k = ease(shield)
        hR = (lerp(bx + 120 * s, hx + 60 * s, k), lerp(by - 40 * s, hy - hr * 1.05, k))
        elR = (lerp(bx + 112 * s, bx + 150 * s, k), lerp(by - 70 * s, by - 190 * s, k))
    else:
        hR = (bx + 122 * s + 40 * s * fl, by - 36 * s - 120 * s * flail - 20 * s * fl)
        elR = (bx + 114 * s + 20 * s * flail, by - 70 * s - 70 * s * flail)
    hL = (bx - 124 * s - 40 * s * fl, by - 30 * s - 110 * s * flail + 20 * s * fl)
    elL = (bx - 118 * s - 20 * s * flail, by - 70 * s - 60 * s * flail)
    tube(cv, [shL, elL, hL], 20 * s, P_["cream"], w=4.0, seed=seed + 20, boil=0.8, n=6)
    if hold > 0.5:                                                # groceries in the left arm
        gx, gy = hL[0] + 6 * s, hL[1] + 26 * s
        for k, (ox, col) in enumerate(((-26, P_["acid"]), (0, P_["red"]), (24, P_["yellow"]))):
            blob(cv, ell(gx + ox * s, gy - 66 * s - 10 * s * (k % 2), 20 * s, 20 * s, n=8), col, w=3, seed=seed + 30 + k, boil=0.5)
        line(cv, [(gx + 18 * s, gy - 60 * s), (gx + 40 * s, gy - 150 * s)], 16 * s, (230, 190, 120), seed=seed + 34, boil=0.4, n=2, taper=(0.2, 0.3))
        blob(cv, rect_pts([(gx - 52 * s, gy - 70 * s), (gx + 52 * s, gy - 70 * s), (gx + 44 * s, gy + 40 * s), (gx - 44 * s, gy + 40 * s)], 2), (200, 160, 110),
             w=4, seed=seed + 35, boil=0.7, n=2, shade=lambda c: c.drawRect(R(gx + 14 * s, gy - 80 * s, gx + 60 * s, gy + 50 * s), paint((170, 130, 90))))
    _hand_s(cv, hL, 150 + 30 * fl, "fist" if hold > 0.5 else "spread", 1, seed + 40, s)
    # head
    blob(cv, ell(hx, hy, hr, hr * 1.02, n=14), P_["white"], w=5.5, seed=seed + 50, boil=1.0,
         shade=lambda c: [c.drawLine(hx + hr * math.cos(a), hy + hr * math.sin(a), hx + hr * 0.62 * math.cos(a + 0.25), hy + hr * 0.62 * math.sin(a + 0.25),
                                     paint(P_["red"], 170, stroke=3 * s)) for a in np.linspace(0.3, 6.0, 7)])
    ex, ey = hx + look[0] * hr * 0.3, hy + look[1] * hr * 0.3
    ir = hr * 0.5
    if dizzy > 0.3:
        pts = [(ex + (2 + u * 4.5) * s * math.cos(u + T * 9), ey + (2 + u * 4.5) * s * math.sin(u + T * 9)) for u in np.linspace(0, 13, 44)]
        brush(cv, np.array(pts), 6 * s, INK, seed=seed + 51, taper=(0.1, 0.1))
    else:
        dots(cv, [(ex, ey)], ir, P_["teal"])
        dots(cv, [(ex, ey)], ir * 0.45 * pupil, INK)
        dots(cv, [(ex - ir * 0.35, ey - ir * 0.38)], ir * 0.18, P_["white"])
    if squint > 0.02:
        cv.save(); cv.clipPath(poly_path(cr_closed(ell(hx, hy, hr + 2, hr * 1.02 + 2, n=14), 4)), doAntiAlias=True)
        yl = hy - hr + 2 * hr * 0.42 * squint + (ey - hy) * 0.5
        blob(cv, [(hx - hr * 1.2, hy - hr * 1.4), (hx + hr * 1.2, hy - hr * 1.4), (hx + hr * 1.2, yl), (hx, yl + hr * 0.12), (hx - hr * 1.2, yl)],
             (150, 130, 210), w=0, seed=seed + 52, boil=0.5, n=3, misreg=(0, 0))
        yb = hy + hr - 2 * hr * 0.36 * squint + (ey - hy) * 0.5
        blob(cv, [(hx - hr * 1.2, hy + hr * 1.4), (hx + hr * 1.2, hy + hr * 1.4), (hx + hr * 1.2, yb), (hx, yb - hr * 0.1), (hx - hr * 1.2, yb)],
             (150, 130, 210), w=0, seed=seed + 53, boil=0.5, n=3, misreg=(0, 0))
        cv.restore()
        line(cv, [(hx - hr * 0.95, yl + 4 * s), (hx, yl + hr * 0.14), (hx + hr * 0.95, yl + 4 * s)], 5.5 * s + 1, seed=seed + 54, boil=0.6, n=5)
        line(cv, [(hx - hr * 0.9, yb - 3 * s), (hx, yb - hr * 0.1), (hx + hr * 0.9, yb - 3 * s)], 4.5 * s + 1, seed=seed + 59, boil=0.6, n=5)
        if squint > 0.5:
            for sd in (-1, 1):
                for j in range(3):
                    a = math.radians(-30 + j * 30) if sd > 0 else math.radians(210 - j * 30)
                    line(cv, [(hx + hr * 1.08 * math.cos(a), hy + hr * 1.08 * math.sin(a)), (hx + hr * 1.32 * math.cos(a), hy + hr * 1.32 * math.sin(a))], 4.5 * s + 1,
                         seed=seed + 55 + j + sd * 5, boil=0.6, n=2, taper=(0.2, 0.3))
    brush(cv, cr_closed(jit(ell(hx, hy, hr, hr * 1.02, n=14), 1.0, seed + 50), 6), 5.5, closed=True, seed=seed + 56)
    if mouth > 0.05:
        blob(cv, ell(hx + 4 * s, hy + hr * 0.72, hr * 0.22, hr * 0.06 + hr * 0.2 * mouth, n=8), P_["mouth"], w=3.5, seed=seed + 57, boil=0.6)
    if sweat > 0.02:
        for j in range(2):
            ph = (T * 1.4 + j * 0.5) % 1.0
            sx_, sy_ = hx + (hr * 1.05 if j == 0 else -hr * 1.0), hy - hr * 0.5 + hr * 0.9 * ph
            blob(cv, [(sx_, sy_ - 16 * s), (sx_ + 10 * s, sy_ + 3 * s), (sx_, sy_ + 12 * s), (sx_ - 10 * s, sy_ + 3 * s)], P_["mint"], w=3, seed=seed + 58 + j, boil=0.5,
                 n=4, a=int(255 * min(1, sweat) * (1 - ph * 0.6)))
    tube(cv, [shR, elR, hR], 20 * s, P_["cream"], w=4.0, seed=seed + 60, boil=0.8, n=6)
    if hold > 0.5 and shield < 0.3:                               # the coffee
        cx_, cy_ = hR[0] + 8 * s, hR[1] - 30 * s
        blob(cv, [(cx_ - 22 * s, cy_ - 36 * s), (cx_ + 22 * s, cy_ - 36 * s), (cx_ + 16 * s, cy_ + 26 * s), (cx_ - 16 * s, cy_ + 26 * s)], P_["white"], w=3.5,
             seed=seed + 61, boil=0.5, n=3, shade=lambda c: c.drawRect(R(cx_ - 30 * s, cy_ - 14 * s, cx_ + 30 * s, cy_ + 4 * s), paint(P_["maroon"])))
        for j in range(2):
            line(cv, [(cx_ - 6 * s + j * 12 * s + 5 * s * math.sin(T * 4 + j + u), cy_ - 44 * s - u * 14 * s) for u in range(4)], 2.6, P_["white"], seed=seed + 62 + j,
                 boil=0.5, n=4, taper=(0.3, 0.6), a=180)
    _hand_s(cv, hR, -60 if shield > 0.3 else (-150 - 30 * fl), "flat" if shield > 0.3 else ("hold" if hold > 0.5 else "spread"), -1, seed + 64, s)
    cv.restore()


def _hand_s(cv, p, ang, pose, mirror, seed, s, rgb=None):
    cv.save(); cv.translate(p[0], p[1]); cv.scale(s * 1.1, s * 1.1)
    _hand(cv, 0, 0, ang, pose, mirror, seed, rgb=rgb or P_["white"])
    cv.restore()


def signboard(cv, x, y, s, text, side=1, rgb=None, seed=8800, k=1.0, ang=0.0, tcol=None):
    """An arrow signboard pointing left (-1) or right (+1), centred at x, y, popping with k."""
    if k <= 0.01:
        return
    rgb = rgb or P_["yellow"]
    tw = max(150.0, measure(text, "bangers", 40) + 60) * s
    cv.save(); cv.translate(x, y); cv.rotate(ang); cv.scale(k, k)
    hw, hh = tw / 2, 34 * s
    pts = [(-hw * side, -hh), (hw * side, -hh), ((hw + 36 * s) * side, 0), (hw * side, hh), (-hw * side, hh)]
    blob(cv, pts, rgb, w=5, seed=seed, boil=0.8, n=2)
    paint_text(cv, text, 8 * s * side, 14 * s, font="bangers", size=40 * s, fill=tcol or INK, ink_w=0, shadow=None, seed=seed + 1, streaks=False, wobble=0.6)
    cv.restore()


def _problem_world(cv, t, T):
    """The blinding, over-complicated sunny world of the B&W 'problem' footage (drawn in colour; the layer greys it)."""
    w.field(cv, (110, 150, 200))
    glare = 0.6 + 0.4 * _ph(t, 2.1, 3.0) - 0.3 * _ph(t, 3.7, 4.3)
    w.sunburst(cv, 1560, 150, 2600, 30, [(255, 255, 236), (120, 160, 210)], rot_deg=t * 14, seed=8601)
    for k in range(4):
        cv.drawCircle(1560, 150, 260 + k * 120 + 25 * math.sin(t * 6 + k), paint(P_["white"], int(70 * glare)))
    blob(cv, ell(1560, 150, 170 + 14 * math.sin(t * 9), 170 + 14 * math.sin(t * 9), n=16), (255, 250, 210), w=6, seed=8602, boil=1.6)
    for k in range(16):                                           # the sun's spiky corona
        a = k / 16 * 2 * math.pi + t * 0.9
        line(cv, [(1560 + 200 * math.cos(a), 150 + 200 * math.sin(a)), (1560 + (300 + 40 * math.sin(t * 8 + k)) * math.cos(a), 150 + (300 + 40 * math.sin(t * 8 + k)) * math.sin(a))],
             14, (255, 250, 200), seed=8603 + k, boil=1.0, n=2, taper=(0.1, 0.8))
    w.hills(cv, 760, 70, [(150, 220, 120), (110, 190, 90)], seed=8610, freq=1.2, spacing=40)
    blob(cv, [(-100, 1100), (500, 820), (1400, 820), (2100, 1100)], (150, 150, 160), w=5, seed=8611, boil=0.8, n=3)
    for k in range(5):
        yy = 860 + k * 50
        line(cv, [(960 - 60 - k * 40, yy), (960 + 60 + k * 40, yy)], 6 + k * 2, P_["white"], seed=8612 + k, boil=0.6, n=2, taper=(0, 0), a=160)
    # the house he came out of
    blob(cv, rect_pts([(40, 860), (40, 480), (420, 480), (420, 860)], 3), (230, 150, 110), w=6, seed=8620, boil=0.8, n=3,
         shade=lambda c: c.drawRect(R(330, 470, 430, 870), paint((190, 110, 90))))
    blob(cv, [(10, 490), (230, 330), (450, 490)], (150, 60, 60), w=6, seed=8621, boil=0.8, n=3)
    blob(cv, rect_pts([(250, 860), (250, 640), (370, 640), (370, 860)], 2), (90, 40, 40), w=5, seed=8622, boil=0.6, n=2)
    blob(cv, rect_pts([(80, 560), (200, 560), (200, 660), (80, 660)], 2), (190, 230, 255), w=5, seed=8623, boil=0.6, n=2)
    for k, (tx, sc) in enumerate(((620, 0.9), (1780, 1.1), (1300, 0.7))):
        line(cv, [(tx, 840), (tx + 6, 700)], 26 * sc, (120, 80, 60), seed=8630 + k, boil=0.6, n=2, taper=(0, 0))
        blob(cv, ell(tx, 640 - 40 * sc, 110 * sc, 100 * sc, n=10), (90, 170, 80), w=5, seed=8633 + k, boil=1.2)
    for k in range(5):                                            # birds circling
        a = t * 1.8 + k * 1.3
        bx_, by_ = 900 + 300 * math.cos(a) + k * 60, 260 + 70 * math.sin(a * 1.3)
        fl = math.sin(t * 14 + k) * 14
        line(cv, [(bx_ - 30, by_ - fl), (bx_, by_ + 6), (bx_ + 30, by_ - fl)], 5, INK, seed=8640 + k, boil=0.6, n=3)


def _ad_problem(cv, t, T):
    shake = (hsh(core.D * 1.31) - 0.5) * 7, (hsh(core.D * 2.17) - 0.5) * 7
    zoom = 1.0 + 0.04 * _ph(t, 1.9, 4.9) + 0.16 * ease(_ph(t, 4.96, 5.25))
    gx = 780.0
    walk_x = lerp(330, gx, ease(_ph(t, 1.9, 2.9)))
    fall = ease(_ph(t, 5.0, 5.35))
    focus = (lerp(960, walk_x + 40, ease(_ph(t, 4.96, 5.25))), lerp(540, 700, ease(_ph(t, 4.96, 5.25))))
    frozen = t >= 5.72
    tt = 5.72 if frozen else t
    bw_layer(cv, contrast=1.4, bright=0.02)
    cv.save()
    cv.translate(W / 2 + shake[0] * (0 if frozen else 1), H / 2 + shake[1] * (0 if frozen else 1))
    cv.scale(zoom, zoom)
    cv.translate(-focus[0], -focus[1])
    _problem_world(cv, tt, T if not frozen else T - (t - 5.72))
    # TOO COMPLICATED: a forest of contradictory signposts sprouting around him
    signs = [("THIS WAY", -1, 560, 520, 3.78, -6), ("NO, THAT WAY", 1, 1110, 470, 3.86, 5), ("TAXES", 1, 1250, 640, 3.94, -4),
             ("PASSWORDS", -1, 470, 700, 4.02, 7), ("TERMS & CONDITIONS", 1, 1130, 330, 4.1, -3), ("UPDATE REQUIRED", -1, 520, 360, 4.18, 4),
             ("FEELINGS?", 1, 1290, 810, 4.26, -8), ("ERROR 404", -1, 300, 450, 4.34, 6), ("2-STEP VERIFY", 1, 1480, 520, 4.42, 3)]
    for j, (txt, sd, sx, sy, t0, ang) in enumerate(signs):
        k = pop(tt, t0, 0.3)
        if k > 0:
            line(cv, [(sx, sy), (sx + 4, sy + 400)], 14, (120, 90, 60), seed=8700 + j, boil=0.5, n=2, taper=(0, 0))
            signboard(cv, sx, sy, 0.9, txt, side=sd, rgb=[P_["yellow"], P_["orange"], P_["cream"], P_["hotpink"]][j % 4], seed=8710 + j * 3, k=k,
                      ang=ang + 4 * math.sin(tt * 5 + j))
    if 3.75 <= tt:
        for k in range(7):                                        # question marks orbiting his head
            a = tt * 3.2 + k * 0.9
            qx, qy = walk_x + 190 * math.cos(a), 470 + 60 * math.sin(a)
            paint_text(cv, "?", qx, qy, font="bangers", size=70, fill=P_["red"], ink_w=4, shadow=None, seed=8750 + k, streaks=False,
                       a=int(255 * min(1, (tt - 3.75 - k * 0.06) / 0.2)) if tt - 3.75 - k * 0.06 > 0 else 0)
    # dropped stuff: apples bounce away, the coffee splashes, papers flutter
    drop = 4.28
    if tt >= drop:
        u = tt - drop
        for k in range(3):
            vx = (-260 + k * 210)
            x_ = walk_x - 150 + vx * u
            y_ = 760 - 300 * u + 900 * u * u
            if y_ > 900:
                bounce = (u - (0.55 + 0.05 * k))
                y_ = 900 - abs(math.sin(bounce * 9)) * 60 * math.exp(-bounce * 3)
            blob(cv, ell(x_, y_, 22, 22, n=8), [P_["acid"], P_["red"], P_["yellow"]][k], w=3, seed=8760 + k, boil=0.5)
        cupx, cupy = walk_x + 140 + 80 * u, min(905, 560 + 1400 * u * u)
        blob(cv, rot(np.array([(cupx - 20, cupy - 34), (cupx + 20, cupy - 34), (cupx + 15, cupy + 24), (cupx - 15, cupy + 24)]), u * 500, cupx, cupy), P_["white"],
             w=3.5, seed=8765, boil=0.5, n=3)
        if cupy >= 905:
            blob(cv, [(cupx - 120, 915), (cupx - 60, 890), (cupx + 30, 880), (cupx + 130, 900), (cupx + 70, 930), (cupx - 40, 935)], P_["maroon"], w=3.5, seed=8766,
                 boil=0.8, n=4)
        for k in range(6):
            px_ = walk_x - 200 + k * 80 + 60 * math.sin(u * 3 + k)
            py_ = 520 + u * 160 + 30 * math.sin(u * 5 + k * 2)
            sheet_ = rot(np.array([(px_ - 26, py_ - 34), (px_ + 26, py_ - 34), (px_ + 26, py_ + 34), (px_ - 26, py_ + 34)]), 30 * math.sin(u * 4 + k), px_, py_)
            blob(cv, rect_pts(sheet_, 3), P_["white"], w=3, seed=8770 + k, boil=0.6, n=2)
            for j in range(3):
                q0 = sheet_[0] + (sheet_[3] - sheet_[0]) * (0.25 + 0.22 * j) + (sheet_[1] - sheet_[0]) * 0.15
                q1 = q0 + (sheet_[1] - sheet_[0]) * 0.7
                cv.drawLine(q0[0], q0[1], q1[0], q1[1], paint((120, 120, 140), stroke=2.5))
    squint = ease(_ph(tt, 2.15, 2.5)) * (1 - ease(_ph(tt, 3.62, 3.82)))
    shield = ease(_ph(tt, 2.25, 2.7)) * (1 - ease(_ph(tt, 3.65, 3.85)))
    look = (math.sin(tt * 7) * 0.8, -0.2) if 3.8 < tt < 4.95 else ((0.4, -0.3) if tt < 3.8 else (0.0, 0.0))
    eyeguy(cv, walk_x, 900, 1.25, T, walk=(tt * 1.6 if tt < 2.9 else 0.0), look=look, squint=squint, shield=shield,
           hold=1.0 if tt < drop else 0.0, flail=_ph(tt, 4.28, 4.4) * (1 - fall), fall=fall, dizzy=1.0 if tt > 5.3 else 0.0,
           mouth=0.6 if 4.28 < tt < 5.3 else (0.3 if tt > 5.3 else 0.0), sweat=1.0 if tt > 2.4 else 0.0, pupil=0.45 if 2.2 < tt < 3.8 else 1.0)
    if tt > 5.1:                                                  # a bird lands on his belly. Too real.
        u = ease(_ph(tt, 5.1, 5.5))
        bx_, by_ = lerp(walk_x - 500, walk_x - 60, u), lerp(420, 760, u) + 6 * math.sin(tt * 9) * (1 - u)
        fl = math.sin(tt * 18) * 22 * (1 - u)
        blob(cv, ell(bx_, by_, 30, 22, n=9), (70, 70, 90), w=3.5, seed=8790, boil=0.6)
        line(cv, [(bx_ - 26, by_ - fl), (bx_ - 4, by_ - 6), (bx_ + 18, by_ - fl * 0.8)], 6, (50, 50, 70), seed=8791, boil=0.5, n=3)
        blob(cv, [(bx_ + 26, by_ - 8), (bx_ + 46, by_ - 2), (bx_ + 26, by_ + 4)], P_["orange"], w=2.5, seed=8792, boil=0.4, n=2)
        dots(cv, [(bx_ + 14, by_ - 8)], 4, INK)
    cv.restore()
    for k in range(3):                                            # film scratches + dust
        if hsh(core.D * 0.7 + k) > 0.45:
            xx = hsh(core.D * 1.9 + k * 3) * W
            line(cv, [(xx, -10), (xx + 8, H * 0.5), (xx - 4, H + 10)], 2.2, P_["white"], seed=8800 + k, boil=2.0, n=3, taper=(0.1, 0.1), a=120)
    vignette(cv, a=210, inner=0.35)
    fl = 0.06 + 0.06 * hsh(core.D * 3.3)
    cv.drawRect(R(0, 0, W, H), paint(P_["white"], int(255 * fl * 0.5)))
    cv.restore()
    # colour captions over the B&W footage
    caps = [("TOO BRIGHT?", 2.12, 3.72, 120, 150, -4, P_["yellow"]), ("TOO COMPLICATED?", 3.78, 4.95, 960, 150, 3, P_["hotpink"])]
    for j, (txt, t0, t1, x, y, ang, col) in enumerate(caps):
        if t0 <= t < t1:
            cv.save(); cv.translate(x, y); cv.rotate(ang)
            paint_text(cv, txt, 0, 0, font="bangers", size=118, fill=col, ink_w=6, shadow=(8, 8), shadow_rgb=P_["violet"], seed=8820 + j,
                       reveal=_ph(t, t0, t0 + 0.35), stagger=0.04, align="left" if j == 0 else "center")
            cv.restore()
    if t >= 4.96:
        paint_text(cv, "TOO...", 150, 200, font="bangers", size=130, fill=P_["acid"], ink_w=6, shadow=(8, 8), shadow_rgb=P_["violet"], seed=8830, align="left",
                   reveal=_ph(t, 4.96, 5.2))
    if t >= 5.72:
        kk = pop(t, 5.72, 0.3)
        cv.save(); cv.translate(560, 340); cv.rotate(-8); cv.scale(kk, kk)
        paint_text(cv, "REAL?", 0, 60, font="bangers", size=210, fill=P_["red"], ink_w=8, shadow=(10, 10), shadow_rgb=INK, seed=8831)
        cv.restore()
        red_x(cv, 1560, 700, 1.6, k=_ph(t, 5.8, 6.05))


def _ad_break(cv, t, T):
    """AD_IN: hand-inked colour bars + the 'WE'LL BE RIGHT BACK' card; a shadow bunny hops across; then VHS glitch + PLAY."""
    cols = [P_["cream"], P_["yellow"], P_["teal"], P_["acid"], P_["magenta"], P_["red"], P_["blue"]]
    bw = W / 7
    for k, c in enumerate(cols):
        blob(cv, rect_pts([(k * bw - 4, -10), ((k + 1) * bw + 4, -10), ((k + 1) * bw + 4, 700), (k * bw - 4, 700)], 3), c, w=5, seed=9500 + k, boil=0.8, n=2)
    for k, c in enumerate([P_["blue"], INK, P_["magenta"], INK, P_["teal"], INK, P_["cream"]]):
        blob(cv, rect_pts([(k * bw - 4, 700), ((k + 1) * bw + 4, 700), ((k + 1) * bw + 4, 800), (k * bw - 4, 800)], 3), c, w=5, seed=9510 + k, boil=0.8, n=2)
    blob(cv, rect_pts([(-10, 800), (W + 10, 800), (W + 10, H + 10), (-10, H + 10)], 3), P_["night"], w=5, seed=9520, boil=0.8, n=2,
         shade=lambda c: [c.drawRect(R(k * W / 9, 800, k * W / 9 + W / 18, H), paint(P_["vdark"])) for k in range(9)])
    # the hand-shadow bunny (running gag) hops across the bars
    if 0.15 < t < 1.75:
        u = (t - 0.15) / 1.6
        bx = lerp(-150, 2050, u)
        by = 460 - abs(math.sin(u * math.pi * 4)) * 170
        shadow_shape(cv, "hand_bunny", bx, by, 1.4, T, rgb=CV_SHADOW, a=200, seed=9530)
    k = pop(t, 0.05, 0.4)
    cv.save(); cv.translate(960, 470); cv.scale(k, k)
    gloss_panel(cv, -700, -170, 700, 170, [P_["night"], P_["vdark"], P_["night"]], seed=9540, ink=7, r=50)
    paint_text(cv, "WE'LL BE RIGHT BACK", 0, 40, font="londrina", size=128, fills=[P_["cream"], P_["yellow"]], ink_w=6.5, shadow=(8, 8), shadow_rgb=P_["magenta"],
               seed=9541, wobble=2.0)
    paint_text(cv, "BOXED  ·  EP. 4  ·  THE CAVE", 0, 128, font="londrina", size=46, fill=P_["teal"], ink_w=3.5, shadow=(4, 4), seed=9542)
    cv.restore()
    paint_text(cv, "BOXED", 960, 985, font="shrik", size=130, fill=P_["yellow"], ink_w=6, shadow=(8, 8), shadow_rgb=P_["magenta"], seed=9543, wobble=2.0, drips=1)
    if t > 1.2:                                                   # the tape kicks in
        g = _ph(t, 1.2, 1.9)
        for j in range(int(3 + 9 * g)):
            yy = hsh(core.D * 1.7 + j) * H
            hh = 6 + 40 * hsh(core.D * 2.9 + j)
            cv.drawRect(R(0, yy, W, yy + hh), paint(mix(P_["white"], P_["magenta"], hsh(j + core.D)), int(80 + 120 * g)))
        if g > 0.5:
            tv_static(cv, (0, 0, W, H), seed=9550, a=int(255 * (g - 0.5) * 2), density=2600)
    if t > 0.9:
        on = int(t * 4) % 2 == 0
        tw_ = paint_text(cv, "PLAY", 110, 120, font="londrina", size=70, fill=P_["acid"], ink_w=0, shadow=(4, 4), shadow_rgb=INK, seed=9560,
                         align="left", streaks=False, wobble=0.5)
        if on:
            for dx, col in ((4, INK), (0, P_["acid"])):
                cv.drawPath(poly_path([(140 + tw_ + dx, 66 + dx), (190 + tw_ + dx, 94 + dx), (140 + tw_ + dx, 122 + dx)]), paint(col))
        paint_text(cv, "SP  0:00:0" + str(int(t * 3) % 10), 1810, 120, font="londrina", size=56, fill=P_["acid"], ink_w=0, shadow=(4, 4), seed=9561, align="right",
                   streaks=False, wobble=0.5)


def set80(cv, t, T, cam=None, hy=650, seed=9600, sun=True, mountains=True, memph=True, lasers=True, sun_r=300, sky=None, grid_col=None):
    """The infomercial stage: gradient sky + stars, synth sun, wireframe mountains on a racing neon grid, Memphis confetti
    and sweeping lasers, as parallax layers of a sets.Cam (returned)."""
    C = sets.Cam(cv, cam or dict(x=0, y=0, z=1.0))
    with C.layer(0.15):
        cv.drawRect(R(-400, hy, W + 400, hy + 700), paint(P_["night"]))
        sky80(cv, hy, t, seed=seed, cols=sky)
    with C.layer(0.25):
        if sun:
            synth_sun(cv, 960, hy - 70, sun_r, t, seed=seed + 1)
    with C.layer(0.5):
        if mountains:
            wire_mountains(cv, hy, t, seed=seed + 2)
        neon_grid(cv, hy, t, seed=seed + 3, col=grid_col)
    with C.layer(0.35):
        if memph:
            memphis(cv, t, seed + 4, n=14, box=(-100, 0, W + 100, hy - 60))
    if lasers:
        laser_beams(cv, t, seed=seed + 5)
    return C


def callout(cv, text, x, y, tip, t, t0, seed=9700, size=58, col=None, ang=-4.0, sub=None):
    """A hand-lettered label in a little ink box with an arrow to `tip`, popping in at t0."""
    k = pop(t, t0, 0.3)
    if k <= 0:
        return
    tw = measure(text, "bangers", size) + 50
    line(cv, [(x, y + 30), ((x + tip[0]) / 2, (y + tip[1]) / 2 - 40), tip], 12, INK, seed=seed, boil=0.8, n=4, taper=(0.0, 0.0), a=int(255 * min(1, k)))
    line(cv, [(x, y + 30), ((x + tip[0]) / 2, (y + tip[1]) / 2 - 40), tip], 7, P_["yellow"], seed=seed, boil=0.8, n=4, taper=(0.0, 0.0), a=int(255 * min(1, k)))
    d = np.array(tip, float) - np.array(((x + tip[0]) / 2, (y + tip[1]) / 2 - 40))
    d = d / (np.hypot(*d) + 1e-6)
    nrm = np.array([-d[1], d[0]])
    head = [tuple(np.array(tip) + d * 18), tuple(np.array(tip) - d * 26 + nrm * 22), tuple(np.array(tip) - d * 26 - nrm * 22)]
    blob(cv, head, P_["yellow"], w=4, seed=seed + 1, boil=0.5, n=2)
    cv.save(); cv.translate(x, y); cv.rotate(ang); cv.scale(k, k)
    hh = size * 0.62 + (size * 0.45 if sub else 0)
    blob(cv, rect_pts([(-tw / 2, -hh), (tw / 2, -hh - 6), (tw / 2 + 8, hh * 0.55), (-tw / 2 - 4, hh * 0.6)], 3), col or P_["hotpink"], w=5, seed=seed + 2, boil=0.8, n=2)
    paint_text(cv, text, 0, size * 0.2 - (size * 0.22 if sub else 0), font="bangers", size=size, fill=P_["white"], ink_w=4, shadow=(4, 4), seed=seed + 3, streaks=False)
    if sub:
        paint_text(cv, sub, 0, size * 0.62, font="londrina", size=size * 0.42, fill=P_["cream"], ink_w=0, shadow=None, seed=seed + 4, streaks=False)
    cv.restore()


def logo_cpp(cv, x, y, s, t, t0, seed=9800, shine_t=None):
    """The CAVE PHONE PRO logo: chrome CAVE PHONE + a slanted gold PRO with a swoosh, slamming in at t0."""
    k = pop(t, t0, 0.35)
    if k <= 0:
        return
    cv.save(); cv.translate(x, y); cv.scale(k, k)
    sh = None if shine_t is None else (t - shine_t) / 0.8
    sw = [(-540, 118), (-100, 86), (300, 92), (560, 52)]
    line(cv, sw, 30, INK, seed=seed, boil=0.8, n=6, taper=(0.05, 0.6))
    line(cv, sw, 20, P_["teal"], seed=seed, boil=0.8, n=6, taper=(0.05, 0.6))
    chrome_text(cv, "CAVE PHONE", 0, 40 * s, 150 * s, font="titan", seed=seed + 1, shine=sh, glints=3, glow=P_["magenta"])
    chrome_text(cv, "PRO", 470 * s, 150 * s, 132 * s, font="shrik", grad=GOLDC, seed=seed + 2, side=[P_["maroon"], P_["red"], P_["orange"]], skew=-0.18,
                shine=None if sh is None else sh - 0.3, glints=2, glow=P_["orange"])
    cv.restore()


def _ad_reveal(cv, t, T):
    push = ease(_ph(t, 9.55, 10.45))
    zf = lerp(1.0 + 0.015 * (t - 6.27), 1.82, push)
    cam = dict(x=0, y=lerp(0, -40, push), z=zf)
    C = set80(cv, t, T, cam, seed=9600)
    rise = ease(_ph(t, 6.3, 7.25))
    py = lerp(1550, 500, rise) + (6 * math.sin((t - 7.25) * 2.4) if t > 7.25 else 0)
    yaw = -540 * (1 - ease(_ph(t, 6.3, 8.12))) + (10 * math.sin((t - 8.12) * 1.6) * (1 - push) if t > 8.12 else 0)
    with C.layer(1.0):
        cv.drawPath(poly_path([(860, -100), (1060, -100), (1380, 1100), (540, 1100)]), _lin(0, -100, 0, 1000, [P_["white"], P_["hotpink"], P_["magenta"]], a=60))
        logo_cpp(cv, 960, 190, 1.0, t, 8.1, seed=9800, shine_t=8.35)
        pedestal(cv, 960, py + 300, 460, t, seed=9620)
        phone(cv, 960, py, 520, T, yaw=yaw, screen=lambda c, r: cave_screen(c, r, T, seed=7100), glow=0.6 + 0.4 * _ph(t, 8.1, 8.4), seed=7500)
        if t < 8.2:                                               # dry-ice fog rolling off the floor; the product rises out of it
            u = _ph(t, 6.27, 8.2)
            fade = 1.0 - ease(_ph(t, 7.3, 8.2))
            for k in range(16):
                side = -1 if k % 2 else 1
                d_ = (k // 2) / 7.0
                px_ = 960 + side * (40 + 620 * d_) * (0.55 + 0.6 * ease(u))
                py_ = 1000 - 70 * math.sin(math.pi * min(1.0, d_ + 0.1)) - 30 * ease(u) + 10 * math.sin(t * 3 + k)
                rr_ = (110 - 30 * d_ + 30 * hsh(9611 + k)) * (0.8 + 0.5 * ease(u))
                col = [(240, 230, 255), P_["lilac"], (255, 200, 236)][k % 3]
                blob(cv, ell(px_, py_, rr_ * 1.2, rr_ * 0.7, n=10), col, w=4, seed=9610 + k, boil=1.3, a=int(240 * fade),
                     shade=lambda c, px_=px_, py_=py_, rr_=rr_: c.drawPath(poly_path(cr_closed(ell(px_ + rr_ * 0.2, py_ + rr_ * 0.45, rr_ * 1.2, rr_ * 0.5, n=8), 3)),
                                                                          paint(P_["hotpink"], 110)))
        for k in range(6):
            a = t * 1.3 + k * 1.05
            sparkle(cv, 960 + 330 * math.cos(a), py + 40 + 300 * math.sin(a), 18 + 10 * math.sin(t * 5 + k), [P_["white"], P_["yellow"], P_["mint"]][k % 3], seed=9630 + k)
    if 6.5 < t < 8.15:
        neon_text(cv, "INTRODUCING...", 960, 200, 120, P_["hotpink"], font="londrina", seed=9640, reveal=_ph(t, 6.5, 7.0), flicker=0.18 if t < 7.0 else 0.0)
    if t > 7.4:
        k = pop(t, 7.4, 0.35) * (1 - push)
        if k > 0.02:
            cv.save(); cv.translate(330, 520); cv.scale(k, k)
            starburst(cv, 0, 0, 175, t, text="ALL", text2="NEW!", size=78, seed=9650)
            cv.restore()
    if 8.08 < t < 8.5:                                            # the logo slam flash
        lens_flare(cv, 1560, 210, t, k=1 - _ph(t, 8.08, 8.5), seed=9660)
        cv.drawRect(R(0, 0, W, H), paint(P_["white"], int(200 * (1 - _ph(t, 8.08, 8.3)))))
    if t > 9.9:
        callout(cv, "100% REAL CAVE WALL!", 1430, 250, (1180, 470), t, 9.9, seed=9670, size=62, sub="(fire not included)")


def denim(cv, rect, seed=9900, col=None):
    x0, y0, x1, y1 = rect
    col = col or (70, 76, 200)
    cv.drawRect(R(x0, y0, x1, y1), _lin(x0, y0, x1, y1, [mix(col, P_["violet"], 0.4), col, mix(col, P_["night"], 0.4)]))
    for k in range(-30, 60):
        xx = x0 + k * 34
        cv.drawLine(xx, y0, xx + (y1 - y0) * 0.6, y1, paint(mix(col, P_["white"], 0.12), stroke=3))
    stipple(cv, mix(col, INK, 0.3), (x0, y0, x1, y1), spacing=16, r=1.7, seed=seed, fn=lambda X, Y: np.clip(0.4 + 0.6 * np.sin(X * 0.01 + Y * 0.013) ** 2, 0, 1) * 0.7)


def _ad_pocket(cv, t, T):
    zf = 1.0 + 0.03 * (t - 11.05)
    cv.save(); cv.translate(W / 2, H / 2); cv.scale(zf, zf); cv.translate(-W / 2, -H / 2)
    denim(cv, (-100, -100, W + 100, H + 100))
    blob(cv, rect_pts([(-50, -60), (W + 50, -60), (W + 50, 150), (-50, 150)], 3), (60, 66, 180), w=6, seed=9910, boil=0.8, n=2,
         shade=lambda c: [c.drawLine(-50, yy, W + 50, yy + 4, paint(P_["orange"], stroke=4)) for yy in (40, 128)])
    for bx in (560, 1660):                                        # belt loops
        blob(cv, rect_pts([(bx - 34, 20), (bx + 34, 20), (bx + 34, 200), (bx - 34, 200)], 2), (64, 70, 186), w=5, seed=9911 + bx, boil=0.6, n=2)
    px, top = 1180, 300
    pk = [(px - 400, top), (px + 400, top), (px + 380, top + 560), (px, top + 700), (px - 380, top + 560)]
    drop = ease(_ph(t, 11.12, 11.55))
    bounce = 18 * math.sin(_ph(t, 11.55, 11.9) * math.pi * 2) * (1 - _ph(t, 11.55, 11.9))
    ph_y = lerp(-500, 430, drop) + bounce
    if t > 11.5:
        firelight(cv, px, top, 620, T, a=170, seed=9920)
    phone(cv, px + 10, ph_y, 600, T, roll=4, screen=lambda c, r: cave_screen(c, r, T, seed=7110), seed=7510)

    def pshade(c):
        denim(c, (px - 420, top - 20, px + 420, top + 720), seed=9930, col=(80, 86, 214))
        if t > 11.5:
            g = _ph(t, 11.5, 11.8)
            c.drawRect(R(px - 420, top, px + 420, top + 720), _lin(0, top, 0, top + 640, [P_["yellow"], P_["orange"], (80, 86, 214)], [0.0, 0.35, 1.0], a=int(150 * g)))
            for k, kind in enumerate(("bunny", "bird")):
                ph = (T * 0.15 + k * 0.5) % 1.0
                shadow_shape(c, kind, px + 330 - ph * 700, top + 260 + 60 * k, 0.9, T, rgb=(40, 30, 110), a=int(150 * g), seed=9940 + k)
    blob(cv, pk, (80, 86, 214), w=6.5, seed=9935, boil=0.9, n=3, shade=pshade)
    for j, off in enumerate((24, 40)):
        q = [(px - 400 + off, top + off * 0.4), (px + 400 - off, top + off * 0.4), (px + 380 - off, top + 560 - off * 0.5), (px, top + 700 - off * 1.1),
             (px - 380 + off, top + 560 - off * 0.5), (px - 400 + off, top + off * 0.4)]
        for a_, b_ in zip(q[:-1], q[1:]):
            n = int(math.hypot(b_[0] - a_[0], b_[1] - a_[1]) / 26)
            for i in range(n):
                u0, u1 = i / n, (i + 0.55) / n
                cv.drawLine(lerp(a_[0], b_[0], u0), lerp(a_[1], b_[1], u0), lerp(a_[0], b_[0], u1), lerp(a_[1], b_[1], u1), paint(P_["orange"] if j == 0 else P_["yellow"], stroke=4))
    for j in range(2):
        line(cv, [(px - 250 + j * 40, top + 300), (px, top + 200 + j * 40), (px + 250 - j * 40, top + 300)], 4, P_["magenta"], seed=9950 + j, boil=0.6, n=5, taper=(0, 0))
    for rx_, ry_ in ((px - 392, top + 6), (px + 392, top + 6)):
        blob(cv, ell(rx_, ry_, 16, 16, n=8), P_["gold"], w=3.5, seed=9955 + int(rx_), boil=0.4)
    cv.restore()
    for j, word in enumerate(("FITS IN", "YOUR", "POCKET!")):
        t0 = 11.2 + j * 0.25
        if t > t0:
            chrome_text(cv, word, 420, 420 + j * 175, 150 if j < 2 else 170, font="titan", seed=9960 + j, reveal=_ph(t, t0, t0 + 0.35),
                        grad=CHROME if j < 2 else GOLDC, side=None if j < 2 else [P_["maroon"], P_["red"], P_["orange"]], glints=1)
    if t > 11.85:
        checkmark(cv, 420, 900, 1.5 * pop(t, 11.85, 0.3))


def thumb_hand(cv, x, y, s, t, swipe=0.0, seed=9970):
    """A big white cartoon glove gripping the phone's lower edge from the right, thumb arcing over the screen."""
    sleeve = [(x + 120 * s, y + 520 * s), (x + 40 * s, y + 140 * s), (x + 260 * s, y + 60 * s), (x + 420 * s, y + 520 * s)]
    blob(cv, sleeve, P_["magenta"], w=6, seed=seed, boil=0.9, n=3, shade=lambda c: c.drawRect(R(x + 250 * s, y, x + 500 * s, y + 600 * s), paint((204, 20, 128))))
    blob(cv, rect_pts([(x + 30 * s, y + 120 * s), (x + 270 * s, y + 40 * s), (x + 290 * s, y + 110 * s), (x + 50 * s, y + 190 * s)], 2), P_["white"], w=5, seed=seed + 1,
         boil=0.7, n=2)
    palm = [(x - 60 * s, y - 10 * s), (x + 20 * s, y - 150 * s), (x + 210 * s, y - 120 * s), (x + 260 * s, y + 60 * s), (x + 60 * s, y + 150 * s), (x - 70 * s, y + 90 * s)]
    blob(cv, palm, P_["white"], w=6, seed=seed + 2, boil=0.9, n=4, shade=lambda c: c.drawPath(poly_path(cr_closed(ell(x + 140 * s, y + 60 * s, 140 * s, 90 * s, n=10), 3)),
                                                                                          paint((226, 222, 232))))
    ang = math.radians(-128 - 26 * swipe)
    base = (x - 10 * s, y - 60 * s)
    tip = (base[0] + 270 * s * math.cos(ang), base[1] + 270 * s * math.sin(ang))
    mid = ((base[0] + tip[0]) / 2 + 30 * s, (base[1] + tip[1]) / 2 + 10 * s)
    tube(cv, [base, mid, tip], 70 * s, P_["white"], w=6, seed=seed + 3, boil=0.8, n=6)
    blob(cv, ell(tip[0] + 4 * s, tip[1] + 6 * s, 22 * s, 16 * s, n=8, rot=math.degrees(ang)), (240, 226, 236), w=3, seed=seed + 4, boil=0.5)


def infinity(cv, x, y, rx, ry, t, seed=9980, col=None, wdt=26, a=255, prog=1.0):
    pts = [(x + rx * math.sin(u), y + ry * math.sin(u) * math.cos(u)) for u in np.linspace(0, 2 * math.pi * prog, 60)]
    if len(pts) < 3:
        return
    P = np.array(pts)
    brush(cv, P, wdt + 12, INK, taper=(0, 0), seed=seed, a=a)
    brush(cv, P, wdt, col or P_["teal"], taper=(0, 0), seed=seed, a=a)
    brush(cv, P + np.array([-3, -4]), wdt * 0.25, P_["white"], taper=(0.2, 0.2), seed=seed + 1, a=int(a * 0.8))


def _ad_scroll(cv, t, T):
    lt = t - 12.55
    set80(cv, t, T, dict(x=60, y=40, z=1.08 + 0.02 * lt), hy=760, seed=9610, mountains=False, sun_r=230,
              sky=[P_["void"], P_["night"], P_["violet"], P_["magenta"], P_["hotpink"]])
    fast = _ph(t, 14.3, 15.3)
    off = 260 * lt + 200 * lt * lt + 1400 * fast * (lt - 1.75)
    swipe = (lt * 2.2) % 1.0
    sw = math.sin(min(1.0, swipe * 1.6) * math.pi) if fast < 0.5 else math.sin(t * 30) * 0.5 + 0.5
    phx, phy, phh = 720, 560, 900
    cv.drawCircle(phx, phy, 620, _rad2(phx, phy, 620, P_["orange"], 90))
    def pour():
        n = int(min(14, (t - 14.32) * 9))
        for k in range(n):
            u = ((t - 14.32) * 0.55 + k / 14.0) % 1.0
            ang = u * 2 * math.pi
            ix = 1460 + 330 * math.sin(ang)
            iy = 660 + 210 * math.sin(ang) * math.cos(ang)
            sx = lerp(phx, ix, min(1.0, u * 4))
            sy = lerp(phy - 470, iy, min(1.0, u * 4)) - 60 * math.sin(min(1.0, u * 4) * math.pi)
            cv.drawCircle(sx, sy, 80, _rad2(sx, sy, 80, P_["orange"], 150))
            shadow_shape(cv, ["bunny", "horse", "bird", "fish", "tree", "person", "jug"][k % 7], sx, sy, 0.75, T, rgb=(70, 10, 50), a=235, seed=9990 + k)
    phone(cv, phx, phy, phh, T, roll=-5 + 1.5 * math.sin(t * 1.3), screen=lambda c, r: feed_screen(c, r, T, off, blur=0.85 * fast), seed=7520, glow=0.3)
    thumb_hand(cv, phx + 120, phy + 330, 1.0, t, swipe=sw)
    if t > 13.6:
        infinity(cv, 1460, 660, 300, 190, t, prog=_ph(t, 13.6, 14.25), col=P_["teal"])
    if t > 14.32:
        pour()
    if t > 12.95:
        chrome_text(cv, "INFINITE", 1460, 230, 132, font="titan", seed=10000, reveal=_ph(t, 12.95, 13.3), glints=2)
    if t > 13.52:
        chrome_text(cv, "SCROLL", 1460, 380, 150, font="titan", seed=10001, reveal=_ph(t, 13.52, 13.85), grad=GOLDC, side=[P_["maroon"], P_["red"], P_["orange"]],
                    glints=2)
    if t > 14.32:
        k = pop(t, 14.32, 0.3)
        cv.save(); cv.translate(1460, 930); cv.scale(k, k)
        gloss_panel(cv, -330, -60, 330, 60, [P_["night"], (10, 40, 30), P_["night"]], seed=10010, r=20)
        paint_text(cv, "SHADOWS LEFT:", -40, 22, font="londrina", size=54, fill=P_["acid"], ink_w=0, shadow=None, seed=10011, streaks=False)
        cnt = "∞" if int(t * 6) % 2 == 0 else "99999"
        if cnt == "∞":
            infinity(cv, 220, 4, 52, 30, t, seed=10012, col=P_["acid"], wdt=9)
        else:
            paint_text(cv, cnt, 220, 22, font="londrina", size=54, fill=P_["acid"], ink_w=0, shadow=None, seed=10013, streaks=False)
        cv.restore()


def velvet(cv, rect, t, seed=10100, col=None):
    x0, y0, x1, y1 = rect
    col = col or P_["maroon"]
    cv.drawRect(R(x0, y0, x1, y1), paint(col))
    for k in range(int((x1 - x0) / 110) + 2):
        xx = x0 + k * 110 + 20 * math.sin(t * 0.6 + k)
        cv.drawRect(R(xx, y0, xx + 55, y1), _lin(xx, 0, xx + 55, 0, [col, mix(col, P_["magenta"], 0.45), col]))
        line(cv, [(xx, y0), (xx + 10 * math.sin(k), (y0 + y1) / 2), (xx, y1)], 3, mix(col, INK, 0.4), seed=seed + k, boil=0.6, n=4, taper=(0, 0), a=180)


def _ad_chains(cv, t, T):
    lt = t - 16.45
    zf = 1.02 + 0.035 * lt
    cv.save(); cv.translate(W / 2, H / 2); cv.scale(zf, zf); cv.translate(-W / 2, -H / 2)
    velvet(cv, (-100, -100, W + 100, H + 100), t)
    cv.drawPath(poly_path([(820, -100), (1100, -100), (1500, 1000), (420, 1000)]), _lin(0, -100, 0, 900, [P_["white"], P_["hotpink"]], a=70))
    blob(cv, ell(960, 940, 640, 120, n=18), P_["night"], w=5, seed=10110, boil=0.8)
    cush = [(560, 760), (620, 640), (960, 610), (1300, 640), (1360, 760), (1300, 860), (960, 890), (620, 860)]
    blob(cv, cush, P_["magenta"], w=6, seed=10111, boil=1.0, n=4,
         shade=lambda c: (c.drawPath(poly_path(cr_closed(ell(1000, 790, 330, 90, n=12), 3)), paint((204, 20, 128))),
                          c.drawPath(poly_path(cr_closed(ell(880, 680, 260, 40, n=12), 3)), paint(P_["hotpink"], 120))))
    for tx, ty in ((570, 765), (1350, 765)):
        line(cv, [(tx, ty), (tx + 4, ty + 40)], 6, P_["gold"], seed=10112 + tx, boil=0.4, n=2)
        blob(cv, [(tx - 16, ty + 40), (tx + 18, ty + 40), (tx + 10, ty + 96), (tx - 10, ty + 96)], P_["gold"], w=3.5, seed=10114 + tx, boil=0.5, n=3)
    gold_chain(cv, (520, 520), (1400, 520), rgb=P_["gold"], link=46, sag=210, w=5, seed=10120)
    gold_chain(cv, (430, 610), (1490, 610), rgb=ROSE, link=40, sag=40, w=5, seed=10121)
    pend_y = 520 + 210 + 70 + 6 * math.sin(t * 2.2)                  # the phone hangs off the gold chain like a pendant
    phone(cv, 960, pend_y, 190, T, roll=4 * math.sin(t * 1.7), screen=lambda c, r: cave_screen(c, r, T, seed=7120, heads=0, fire=False), seed=7530)
    for k in range(9):
        a = t * 0.9 + k * 0.7
        sparkle(cv, 960 + 520 * math.cos(a), 640 + 220 * math.sin(a * 1.3), 12 + 14 * abs(math.sin(t * 4 + k)), P_["white"], w=2, seed=10130 + k)
    cv.restore()
    k = pop(t, 17.2, 0.4)
    if k > 0:
        cv.save(); cv.translate(960, 175); cv.scale(k, k)
        neon_text(cv, "SmartChains", -30, 40, 168, P_["hotpink"], font="caveat", seed=10140)
        paint_text(cv, "TM", 520, -50, font="londrina", size=40, fill=P_["cream"], ink_w=0, shadow=None, seed=10141, streaks=False)
        cv.restore()
    if t > 17.55:
        k = pop(t, 17.55, 0.3)
        cv.save(); cv.translate(960, 300); cv.scale(k, k)
        for j, (lab, col) in enumerate((("24K GOLD", P_["gold"]), ("ROSE GOLD", ROSE))):
            xx = -230 + j * 460
            blob(cv, ell(xx - 120, -16, 22, 22, n=8), col, w=3.5, seed=10150 + j, boil=0.5)
            paint_text(cv, lab, xx + 20, 0, font="londrina", size=50, fill=col, ink_w=3.5, shadow=(3, 3), seed=10152 + j, streaks=False)
        cv.restore()
    if t > 17.7:                                                  # the price tag
        k = pop(t, 17.7, 0.35)
        cv.save(); cv.translate(1580, 640); cv.rotate(10 + 4 * math.sin(t * 2)); cv.scale(k, k)
        line(cv, [(-150, -170), (-60, -110)], 4, P_["white"], seed=10160, boil=0.5, n=2)
        blob(cv, [(-90, -120), (190, -120), (190, 150), (-90, 150), (-150, 15)], P_["cream"], w=5, seed=10161, boil=0.8, n=2)
        dots(cv, [(-100, 15)], 12, P_["maroon"])
        for j, (txt, sz, col) in enumerate((("3 EASY", 54, P_["red"]), ("PAYMENTS", 46, P_["red"]), ("OF $19.99", 52, INK))):
            paint_text(cv, txt, 50, -50 + j * 62, font="bangers", size=sz, fill=col, ink_w=0, shadow=None, seed=10162 + j, streaks=False)
        paint_text(cv, "*plus your freedom", 50, 140, font="caveat", size=30, fill=P_["violet"], ink_w=0, shadow=None, seed=10166, streaks=False)
        cv.restore()


def _ad_turn(cv, t, T):
    lt = t - 18.25
    cv.drawRect(R(0, 0, W, H), _lin(0, 0, W, 0, [P_["orange"], P_["magenta"], P_["night"]], [0.0, 0.45, 1.0]))
    rise = ease(_ph(t, 18.35, 19.0))
    sx, sy = 430, lerp(900, 420, rise)
    w.sunburst(cv, sx, sy, 1700, 22, [mix(P_["yellow"], P_["orange"], 0.4), P_["orange"]], rot_deg=t * 10, seed=10200)
    pg = skia.Paint(AntiAlias=True)
    pg.setShader(skia.GradientShader.MakeLinear([skia.Point(700, 0), skia.Point(1350, 0)], [core.C(P_["magenta"], 0), core.C(P_["night"], 255)]))
    cv.drawRect(R(700, 0, W, H), pg)
    w.planet(cv, sx, sy, 150, P_["yellow"], bands=[(-0.4, 0.2, P_["orange"]), (0.2, 0.22, P_["orange"])], seed=10201, crater=False,
             face=dict(look=(0.8, 0.1), smile=0.7, lids=0.2), ring=dict(rx=1.7, ry=0.3, rgb=P_["teal"], rgb2=P_["cream"], tilt=-14))
    w.hills(cv, 860, 60, [P_["acid"], P_["teal"], P_["violet"]], seed=10202, freq=1.1, spacing=34)
    neon_grid(cv, 900, t, seed=10203, nx=12, col=P_["hotpink"], floor=(40, 10, 60), cx=1400)
    bfx, bfy = 600 + 120 * math.sin(t * 1.8), 520 + 50 * math.sin(t * 3.1)
    if lt > 1.5:
        bfx, bfy = lerp(bfx, 1185, ease(_ph(t, 19.75, 20.2))), lerp(bfy, 470, ease(_ph(t, 19.75, 20.2)))
    for sd in (-1, 1):                                            # a butterfly worth turning around for
        fl = abs(math.sin(t * 16)) * 0.8 + 0.2
        blob(cv, [(bfx, bfy), (bfx + sd * 50 * fl, bfy - 40), (bfx + sd * 60 * fl, bfy + 6), (bfx + sd * 30 * fl, bfy + 34)], [P_["acid"], P_["hotpink"]][sd > 0], w=3,
             seed=10210 + sd, boil=0.6, n=3)
    line(cv, [(bfx, bfy - 14), (bfx, bfy + 22)], 6, seed=10213, boil=0.4, n=2)
    TY = 19.62
    turn = ease(_ph(t, 19.25, 19.58))
    yank = _ph(t, TY, TY + 0.6)
    spring = math.exp(-yank * 4) * math.sin(yank * 18) if t > TY else 0.0
    tilt = (-22 * turn if t < TY else 14 * spring)
    look = ((lerp(0.75, -1.15, turn), lerp(0.6, -0.75, turn)) if t < TY else (0.75, 0.6)) if t > 19.0 else ((-0.4, -0.3) if 18.9 < t else (0.75, 0.6))
    fx, fy, s = 1180, 980, 3.0
    taut = 1.0 if 19.5 < t < TY + 0.3 else 0.0
    px_, py_ = 1530 + (40 * turn if t < TY else 0), 640 + 8 * math.sin(t * 2)
    r = 70 * s
    cy_ = fy - r * 1.15
    collar_pt = (fx + r * 0.85, cy_ + r * 0.66)
    eyefolk(cv, fx, fy, s, T, seed=8300, look=look, lid=0.15, rgb=(96, 44, 160), iris=P_["teal"], tilt=tilt, collar=P_["gold"],
            glow=P_["orange"] if t < 18.9 or t > TY + 0.1 else None, pupil=1.0 if t < 18.9 or t > TY + 0.1 else 1.3)
    gold_chain(cv, collar_pt, (px_ - 60, py_ + 60), rgb=P_["gold"], link=34, sag=60, w=4.5, seed=10220, taut=taut)
    phone(cv, px_, py_, 260, T, roll=-14 + 6 * spring, yaw=-28, screen=lambda c, r: cave_screen(c, r, T, seed=7130, heads=0), seed=7540)
    if 18.85 < t < TY:
        k = pop(t, 18.85, 0.15)
        cv.save(); cv.translate(fx - 120, 520); cv.rotate(-14); cv.scale(k, k)
        paint_text(cv, "!", 0, 0, font="bangers", size=170, fill=P_["yellow"], ink_w=6, shadow=(6, 6), shadow_rgb=P_["red"], seed=10229)
        cv.restore()
    if TY < t < TY + 0.65:
        k = pop(t, TY, 0.2)
        cv.save(); cv.translate(1020, 330); cv.rotate(-12); cv.scale(k, k)
        paint_text(cv, "YANK!", 0, 0, font="bangers", size=150, fill=P_["yellow"], ink_w=7, shadow=(9, 9), shadow_rgb=P_["red"], seed=10230)
        cv.restore()
        for j in range(4):
            line(cv, [(fx - 420, 520 + j * 70), (fx - 260, 540 + j * 70)], 8, P_["white"], seed=10231 + j, boil=0.8, n=2, taper=(0.1, 0.6))
    if t > 18.45:
        k = pop(t, 18.45, 0.35)
        cv.save(); cv.translate(960, 150); cv.scale(k, k)
        chrome_text(cv, "NEVER TURN AROUND", 0, 0, 104, font="titan", seed=10240, glints=2, reveal=_ph(t, 18.45, 19.6), stagger=0.04)
        cv.restore()
    if t > 19.97:
        k = pop(t, 19.97, 0.3)
        cv.save(); cv.translate(960, 290); cv.rotate(-4); cv.scale(k, k)
        chrome_text(cv, "AGAIN!", 0, 0, 120, font="titan", seed=10241, grad=GOLDC, side=[P_["maroon"], P_["red"], P_["orange"]], glints=2)
        cv.restore()
        checkmark(cv, 1700, 800, 1.6 * pop(t, 20.05, 0.3))


def living_room(cv, t, seed=10300):
    """The testimonial set: dreamy pink-violet backdrop with drifting bokeh, venetian blinds, a framed shadow-bunny, a ficus."""
    cv.drawRect(R(-60, -60, W + 60, H + 60), _lin(0, 0, W, H, [P_["hotpink"], P_["lilac"], P_["violet"]]))
    for k in range(14):
        bx = (hsh(seed + k) * 2200 + t * 14 * (hsh(seed + 30 + k) - 0.5)) % 2200 - 140
        by = hsh(seed + 60 + k) * 900 + 18 * math.sin(t * 0.6 + k)
        r = 50 + 90 * hsh(seed + 90 + k)
        cv.drawCircle(bx, by, r, paint([P_["white"], P_["yellow"], P_["mint"], P_["hotpink"]][k % 4], 40))
        cv.drawCircle(bx, by, r, paint(P_["white"], 30, stroke=4))
    x0, y0, x1, y1 = 120, 120, 640, 640
    for k in range(7):                                            # light shafts through the blinds onto the wall
        yy = y0 + 40 + k * 70
        cv.drawPath(poly_path([(x1, yy), (x1, yy + 26), (x1 + 900, yy + 420), (x1 + 900, yy + 370)]), paint(P_["yellow"], 34))

    def wsh(c):
        c.drawRect(R(x0, y0, x1, y1), _lin(0, y0, 0, y1, [P_["orange"], P_["hotpink"], P_["violet"]]))
        c.drawCircle(x0 + 330, y0 + 330, 90, paint(P_["yellow"]))
        line(c, [(x0 + 120, y1), (x0 + 140, y0 + 260)], 16, INK, seed=seed + 3, boil=0.5, n=3)
        for j in range(5):
            a = math.radians(-160 + j * 35)
            line(c, [(x0 + 140, y0 + 260), (x0 + 140 + 110 * math.cos(a), y0 + 260 + 110 * math.sin(a) + 30)], 12, INK, seed=seed + 4 + j, boil=0.5, n=3,
                 taper=(0.1, 0.8))
        for k in range(12):
            c.drawRect(R(x0, y0 + k * 44 + 14, x1, y0 + k * 44 + 40), paint((255, 226, 170)))
            c.drawLine(x0, y0 + k * 44 + 40, x1, y0 + k * 44 + 40, paint((200, 140, 100), stroke=3))
    blob(cv, rect_pts([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 3), (255, 214, 150), w=6, seed=seed + 1, boil=0.8, n=2, shade=wsh)
    blob(cv, rect_pts([(x0 - 30, y0 - 30), (x1 + 30, y0 - 30), (x1 + 30, y0), (x0 - 30, y0)], 3), (150, 90, 60), w=5, seed=seed + 2, boil=0.6, n=2)
    blob(cv, rect_pts([(x0 - 40, y1), (x1 + 40, y1), (x1 + 40, y1 + 30), (x0 - 40, y1 + 30)], 3), (150, 90, 60), w=5, seed=seed + 5, boil=0.6, n=2)
    line(cv, [(x1 - 40, y0), (x1 - 36, y1 - 60)], 3, (90, 60, 40), seed=seed + 6, boil=0.5, n=2, taper=(0, 0))
    fx0, fy0, fx1, fy1 = 1460, 150, 1760, 390
    blob(cv, rect_pts([(fx0 - 24, fy0 - 24), (fx1 + 24, fy0 - 24), (fx1 + 24, fy1 + 24), (fx0 - 24, fy1 + 24)], 3), P_["gold"], w=5, seed=seed + 20, boil=0.7, n=2)
    cv.drawRect(R(fx0, fy0, fx1, fy1), _rad((fx0 + fx1) / 2, fy1, 260, [P_["yellow"], CV_WALL, CV_WALL2]))
    shadow_shape(cv, "hand_bunny", (fx0 + fx1) / 2, (fy0 + fy1) / 2 + 10, 0.85, t, seed=seed + 21)
    brush(cv, np.array([(fx0, fy0), (fx1, fy0), (fx1, fy1), (fx0, fy1)]), 4, closed=True, seed=seed + 22)
    paint_text(cv, "HOME SWEET CAVE", (fx0 + fx1) / 2, fy1 + 70, font="caveat", size=40, fill=P_["night"], ink_w=0, shadow=None, seed=seed + 23, streaks=False)
    cv.drawRect(R(-60, 880, W + 60, H + 60), paint(mix(P_["violet"], P_["night"], 0.5)))
    brush(cv, np.array([(-60, 880), (W + 60, 884)]), 5, taper=(0.02, 0.02), seed=seed + 24)


def _ad_gary(cv, t, T):
    lt = t - 20.55
    zf = 1.0 + 0.012 * lt
    cv.save(); cv.translate(W / 2, H / 2); cv.scale(zf, zf); cv.translate(-W / 2, -H / 2)
    living_room(cv, t)
    w.couch(cv, 900, 1000, 1.25, seed=10310, rgb=P_["orange"], rgb2=P_["red"], part="back")
    w.plant(cv, 200, 1010, 1.3, seed=10311, phase=t * 0.4)
    w.lamp(cv, 1750, 1020, 1.25, seed=10312)
    gx, gy, s = 830, 420, 1.12
    lift = 0.0
    if 22.79 < t < 24.0:
        lift = ease(_ph(t, 22.85, 23.6))
    snap = ease(_ph(t, 23.85, 23.95))
    neck = 52 - 22 * lift * (1 - snap) + (4 * math.exp(-(t - 23.95) * 6) * math.sin((t - 23.95) * 30) if t > 23.95 else 0)
    phx, phy = 1150, 760
    w.couch(cv, 900, 1000, 1.25, seed=10310, rgb=P_["orange"], rgb2=P_["red"], part="front")
    gary_bent(cv, gx, gy, s, T, neck=neck, look=(0.95, 0.15), glow=P_["orange"], arm_r=(phx - 30, phy + 40), thumbs=_ph(t, 24.8, 25.15) if t < 25.95 else 1.0,
              strain=lift * (1 - snap), lid=0.2)
    gold_chain(cv, (gx + 70 * s, gy + 230 * s), (phx - 40, phy + 30), rgb=P_["gold"], link=30, sag=40, w=4, seed=10320)
    phone(cv, phx, phy, 230, T, roll=-24, yaw=-40, screen=lambda c, r: cave_screen(c, r, T, seed=7140, heads=0), seed=7550, glow=0.5)
    _hand_s(cv, (phx - 30, phy + 40), -40, "hold", -1, 10321, s)
    if t < 22.6:                                                  # cobweb strung between the bent head and the shoulder: six years
        a = int(220 * _ph(t, 20.9, 21.4))
        hub = (gx - 70, gy + 175)
        for j in range(5):
            ang_ = math.radians(150 + j * 26)
            cv.drawLine(hub[0], hub[1], hub[0] + 70 * math.cos(ang_), hub[1] + 70 * math.sin(ang_) - 30, paint(P_["white"], a, stroke=2.0))
        for j in range(1, 3):
            pts = [(hub[0] + 24 * j * math.cos(math.radians(a2)), hub[1] + 24 * j * math.sin(math.radians(a2)) - 12 * j) for a2 in np.linspace(150, 254, 5)]
            brush(cv, np.array(pts), 1.6, P_["white"], taper=(0.1, 0.1), seed=10330 + j, a=a)
    if 22.95 < t < 23.85:
        paint_text(cv, "CREEEAK...", gx - 40, gy - 230, font="bangers", size=72, fill=P_["cream"], ink_w=4.5, shadow=(5, 5), seed=10340, reveal=_ph(t, 22.95, 23.3),
                   stagger=0.05)
    if 23.85 < t < 24.6:
        k = pop(t, 23.85, 0.2)
        cv.save(); cv.translate(gx + 300, gy - 160); cv.rotate(14); cv.scale(k, k)
        paint_text(cv, "CRICK!", 0, 0, font="bangers", size=120, fill=P_["yellow"], ink_w=6, shadow=(7, 7), shadow_rgb=P_["red"], seed=10341)
        cv.restore()
    cv.restore()
    if t > 24.9:
        k = pop(t, 24.9, 0.3)
        cv.save(); cv.translate(1500, 330); cv.rotate(-12); cv.scale(k, k)
        blob(cv, ell(0, 0, 170, 120, n=14), P_["red"], w=6, seed=10350, boil=1.0, shade=lambda c: c.drawCircle(0, 0, 100, paint(P_["maroon"], 120)))
        paint_text(cv, "10/10", 0, 34, font="bangers", size=110, fill=P_["white"], ink_w=5, shadow=(5, 5), seed=10351)
        cv.restore()
    # lower third: REAL CUSTOMER + five stars
    k = pop(t, 21.0, 0.4) * (1 - ease(_ph(t, 25.8, 26.05)))
    if k > 0.01:
        cv.save(); cv.translate(110, 900); cv.scale(k, k)
        gloss_panel(cv, 0, -88, 760, 20, [P_["teal"], P_["blue"], P_["vdark"]], seed=10360, r=26)
        gloss_panel(cv, 30, 16, 700, 96, [P_["night"], P_["vdark"], P_["night"]], seed=10361, r=18)
        chrome_text(cv, "REAL CUSTOMER", 380, -12, 74, font="titan", seed=10362, glints=1, depth=6, ink=4)
        paint_text(cv, "GARY  ·  CAVE PHONE USER, 6 YRS", 60, 74, font="londrina", size=40, fill=P_["cream"], ink_w=0, shadow=None, seed=10363, streaks=False,
                   align="left")
        cv.restore()
        stars_row(cv, 960 - 120, 1010 - 110, 64 * k, t, 21.3, seed=10364)
    if 22.4 < t < 24.4 and int(t * 3) % 2 == 0:
        paint_text(cv, "*neck shown at actual angle", 1700, 860, font="caveat", size=34, fill=P_["white"], ink_w=0, shadow=(2, 2), seed=10370, streaks=False,
                   align="right")


def fx_card(cv, cx, cy, wd, ht, title, t, t0, seed, art, col=None):
    """A glossy side-effect card: an illustration window (art(cv, (x0, y0, x1, y1)) clipped) and a caption, popping at t0."""
    k = pop(t, t0, 0.35)
    if k <= 0.01:
        return
    cv.save(); cv.translate(cx, cy); cv.rotate(-2 + 4 * hsh(seed)); cv.scale(k, k)
    x0, y0, x1, y1 = -wd / 2, -ht / 2, wd / 2, ht / 2
    gloss_panel(cv, x0, y0, x1, y1, [P_["cream"], P_["white"], P_["cream_sh"]], seed=seed, r=28)
    ax0, ay0, ax1, ay1 = x0 + 22, y0 + 22, x1 - 22, y1 - 92
    cv.save(); cv.clipPath(rrect_path(ax0, ay0, ax1, ay1, 18), doAntiAlias=True)
    art(cv, (ax0, ay0, ax1, ay1))
    cv.restore()
    brush(cv, cr_closed(rrect_pts(ax0, ay0, ax1, ay1, 18, n=3), 3), 4.5, closed=True, seed=seed + 1)
    paint_text(cv, title, 0, y1 - 30, font="bangers", size=56 if len(title) < 16 else 44, fill=col or P_["red"], ink_w=3.5, shadow=(3, 3), shadow_rgb=P_["night"],
               seed=seed + 2, streaks=False, reveal=_ph(t, t0 + 0.1, t0 + 0.5))
    cv.restore()


def _art_neck(cv, r, t, T):
    x0, y0, x1, y1 = r
    cv.drawRect(R(x0, y0, x1, y1), _lin(0, y0, 0, y1, [P_["teal"], P_["blue"]]))
    w.sunburst(cv, (x0 + x1) / 2, y1, 700, 16, [P_["teal"], mix(P_["teal"], P_["blue"], 0.5)], rot_deg=t * 8, seed=10400)
    cx = (x0 + x1) / 2
    eyefolk(cv, cx - 30, y1 + 10, 1.25, T, seed=8400, look=(0.3, 0.95), lid=0.35, brace=True, sweat=1.0, phone_at=(cx + 10, y1 - 30), glow=P_["mint"],
            rgb=(110, 50, 150), tilt=10)
    for j in range(3):
        line(cv, [(cx - 170 + j * 14, y0 + 60 + j * 26), (cx - 130 + j * 14, y0 + 90 + j * 26)], 6, P_["yellow"], seed=10410 + j, boil=0.8, n=2, taper=(0.1, 0.4))
    paint_text(cv, "ow.", cx + 150, y0 + 70, font="caveat", size=50, fill=P_["white"], ink_w=0, shadow=(2, 2), seed=10413, streaks=False)


def _art_shadow_love(cv, r, t, T):
    x0, y0, x1, y1 = r
    cv.drawRect(R(x0, y0, x1, y1), _rad((x0 + x1) / 2 + 80, y1, (x1 - x0), [P_["yellow"], CV_WALL, CV_WALL2, mix(CV_WALL2, P_["red"], 0.5)]))
    shadow_shape(cv, "bunny", x1 - 170, (y0 + y1) / 2 + 10, 1.2, T, seed=10420)
    eyefolk(cv, x0 + 150, y1 + 10, 1.1, T, seed=8410, look=(1.0, -0.2), lid=0.3, rgb=(80, 40, 140), iris=P_["hotpink"], pupil=1.4, nod=0.3 * math.sin(t * 6))
    for k in range(5):
        u = (t * 0.6 + k / 5) % 1.0
        hx, hy, hs = x0 + 200 + 150 * u + 20 * math.sin(t * 3 + k), y1 - 120 - u * 210, 15 * (1 - u * 0.4)
        hp = [(hx, hy + hs), (hx - hs * 1.3, hy - hs * 0.2), (hx - hs * 0.7, hy - hs * 1.1), (hx, hy - hs * 0.4), (hx + hs * 0.7, hy - hs * 1.1), (hx + hs * 1.3, hy - hs * 0.2)]
        blob(cv, hp, P_["red"], w=2.5, seed=10421 + k, boil=0.5, n=3, a=int(255 * (1 - u)))
    blob(cv, ell(x1 - 160, y0 + 92, 22, 14, n=8), P_["hotpink"], w=0, seed=10430, boil=0.5, misreg=(0, 0), a=200)


def _ad_effects(cv, t, T):
    C = set80(cv, t, T, dict(x=-80, y=0, z=1.0 + 0.008 * (t - 26.1)), seed=9620, lasers=False)
    with C.layer(1.0):
        pedestal(cv, 1430, 800, 400, t, seed=9625)
        phone(cv, 1430, 520, 480, T, yaw=25 * math.sin((t - 26.1) * 0.9), screen=lambda c, r: cave_screen(c, r, T, seed=7150), seed=7560, glow=0.5)
    paint_text(cv, "SIDE EFFECTS MAY INCLUDE:", 120, 118, font="londrina", size=58, fill=P_["cream"], ink_w=4, shadow=(4, 4), shadow_rgb=P_["magenta"], seed=10440,
               align="left", reveal=_ph(t, 26.15, 26.5))
    fx_card(cv, 450, 400, 600, 420, "STIFF NECK", t, 26.3, 10450, lambda c, r: _art_neck(c, r, t, T))
    fx_card(cv, 980, 610, 600, 420, "MISTAKING SHADOWS FOR REALITY", t, 28.64, 10460, lambda c, r: _art_shadow_love(c, r, t, T), col=P_["violet"])
    legal_crawl(cv, (96, 870, 1824, 1030), t - 26.1, speed=330, size=22)


def blister(cv, cx, cy, s, t, T, seed=10500, look=(0.0, 0.0), realize=0.0, card=None, label="YOU"):
    """A blister pack hanging on a peg: printed card backing (NEW! YOU(TM), barcode, FREE* burst) with an eyeball creature
    sealed under a clear plastic bubble, staring at its phone. realize 0..1 = the slow realization (eye widens, sweat)."""
    card = card or P_["yellow"]
    wd, ht = 360 * s, 520 * s
    x0, y0, x1, y1 = cx - wd / 2, cy - ht / 2, cx + wd / 2, cy + ht / 2

    def csh(c):
        c.drawRect(R(x0, y0, x1, y1), _lin(0, y0, 0, y1, [card, mix(card, P_["orange"], 0.5)]))
        w.sunburst(c, cx, cy + 40 * s, 500 * s, 18, [mix(card, P_["white"], 0.35), card], rot_deg=12, seed=seed + 1)
        c.drawRect(R(x0, y1 - 80 * s, x1, y1), paint(P_["magenta"]))
    blob(cv, rect_pts([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 3), card, w=5 * s + 1, seed=seed, boil=0.8, n=2, shade=csh)
    blob(cv, ell(cx, y0 + 34 * s, 40 * s, 14 * s, n=10), P_["night"], w=3, seed=seed + 2, boil=0.4)
    paint_text(cv, "NEW!", x0 + 70 * s, y0 + 100 * s, font="bangers", size=56 * s, fill=P_["red"], ink_w=3.5 * s + 0.5, shadow=(3, 3), seed=seed + 3, streaks=False)
    chrome_text(cv, label, cx + 40 * s, y0 + 112 * s, 80 * s, font="titan", seed=seed + 4, depth=6 * s, ink=3.5 * s + 0.5, glints=1, skew=-0.1)
    paint_text(cv, "TM", cx + 150 * s, y0 + 70 * s, font="londrina", size=24 * s, fill=INK, ink_w=0, shadow=None, seed=seed + 5, streaks=False)
    for k in range(16):
        bw_ = (3 if hsh(seed + k) > 0.5 else 6) * s
        cv.drawRect(R(x1 - 150 * s + k * 8 * s, y1 - 70 * s, x1 - 150 * s + k * 8 * s + bw_, y1 - 20 * s), paint(INK))
    paint_text(cv, "NOW WITH MORE DATA", x0 + 20 * s, y1 - 32 * s, font="londrina", size=26 * s, fill=P_["cream"], ink_w=0, shadow=None, seed=seed + 6, streaks=False,
               align="left")
    bx0, by0, bx1, by1 = x0 + 40 * s, y0 + 140 * s, x1 - 40 * s, y1 - 100 * s
    eyefolk(cv, cx, by1 - 6 * s, 1.15 * s, T, seed=seed + 20, look=look, lid=lerp(0.3, 0.0, realize), pupil=lerp(1.0, 0.45, realize), sweat=realize,
            phone_at=(cx + 6 * s, by1 - 34 * s), glow=P_["orange"], rgb=(90, 40, 150), mouth=0.5 * realize)
    bub = rrect_pts(bx0, by0, bx1, by1, 46 * s, n=4)
    blob(cv, bub, P_["white"], w=4 * s + 1, seed=seed + 30, boil=0.8, n=3, a=50)
    line(cv, [(bx0 + 24 * s, by0 + 70 * s), (bx0 + 18 * s, by1 - 90 * s)], 10 * s, P_["white"], seed=seed + 31, boil=0.5, n=3, taper=(0.3, 0.3), a=170)
    line(cv, [(bx1 - 40 * s, by0 + 30 * s), (bx1 - 20 * s, by0 + 60 * s)], 7 * s, P_["white"], seed=seed + 32, boil=0.5, n=2, taper=(0.3, 0.3), a=170)
    k = 0.92 + 0.08 * math.sin(t * 6 + seed)
    starburst(cv, x1 - 30 * s, y0 + 210 * s, 70 * s * k, t, rgb=P_["red"], rgb2=P_["maroon"], text="FREE!*", size=34 * s, tcol=P_["white"], seed=seed + 40)


def _ad_product(cv, t, T):
    u = ease(_ph(t, 30.95, 33.5))
    z = lerp(3.4, 1.0, u)
    fx_, fy_ = 960, lerp(560, 520, u)
    cv.save(); cv.translate(W / 2, H / 2); cv.scale(z, z); cv.translate(-fx_, -fy_)
    old = _ink(z)
    cv.drawRect(R(-1200, -900, W + 1200, H + 900), paint((236, 222, 196)))
    xs = np.arange(-1180, W + 1180, 46.0)
    ys = np.arange(-880, H + 880, 46.0)
    X, Y = np.meshgrid(xs, ys)
    dots(cv, np.stack([X.ravel(), Y.ravel()], 1), 5, (180, 160, 130))
    vx0, vx1 = fx_ - W / 2 / z - 200, fx_ + W / 2 / z + 200
    vy0, vy1 = fy_ - H / 2 / z - 260, fy_ + H / 2 / z + 260
    for row, yy in enumerate((-260, 520, 1300)):
        for k in range(-3, 4):
            if row == 1 and k == 0:
                continue
            bx = 960 + k * 440
            if not (vx0 < bx < vx1 and vy0 < yy < vy1):
                continue
            line(cv, [(bx, yy - 300), (bx, yy - 230)], 7, (150, 150, 170), seed=10510 + k + row * 9, boil=0.3, n=2, taper=(0, 0))
            blister(cv, bx, yy, 0.82, t, T, seed=10600 + row * 50 + k * 7, look=(0.1, 0.95), card=[P_["yellow"], P_["teal"], P_["hotpink"], P_["acid"]][(k + row) % 4])
    line(cv, [(960, 220), (960, 290)], 7, (150, 150, 170), seed=10520, boil=0.3, n=2, taper=(0, 0))
    real = _ph(t, 31.0, 33.0)
    blister(cv, 960, 520, 0.82, t, T, seed=10530, look=(lerp(0.1, 0.0, real), lerp(0.95, -0.2, real)), realize=real)
    shelf_y = 800
    blob(cv, rect_pts([(-1200, shelf_y), (W + 1200, shelf_y), (W + 1200, shelf_y + 60), (-1200, shelf_y + 60)], 3), (200, 200, 214), w=5, seed=10540, boil=0.6, n=2)
    core.INKMUL = old
    cv.restore()
    if t > 32.0:
        k = pop(t, 32.0, 0.25)
        cv.save(); cv.translate(W / 2 + (1105 - fx_) * z, H / 2 + (330 - fy_) * z); cv.rotate(12); cv.scale(k * max(0.6, z * 0.5), k * max(0.6, z * 0.5))
        paint_text(cv, "!", 0, 0, font="bangers", size=150, fill=P_["red"], ink_w=6, shadow=(5, 5), seed=10552)
        cv.restore()
    if t > 32.55:
        k = pop(t, 32.55, 0.4)
        cv.save(); cv.translate(960, 150); cv.scale(k, k)
        gloss_panel(cv, -560, -70, 560, 60, [P_["red"], P_["maroon"], P_["red"]], seed=10550, r=24)
        paint_text(cv, "*YOU ARE THE PRODUCT", 0, 24, font="bangers", size=84, fill=P_["white"], ink_w=4.5, shadow=(5, 5), seed=10551)
        cv.restore()
    legal_crawl(cv, (96, 870, 1824, 1030), t - 26.1, speed=330, size=22)


def _ad_endcard(cv, t, T):
    lt = t - 34.05
    C = set80(cv, t, T, dict(x=0, y=0, z=1.0 + 0.012 * lt), seed=9630)
    with C.layer(1.0):
        cv.drawPath(poly_path([(860, -100), (1060, -100), (1330, 1000), (590, 1000)]), _lin(0, -100, 0, 900, [P_["white"], P_["hotpink"]], a=55))
        pedestal(cv, 960, 760, 420, t, seed=9635)
        phone(cv, 960, 520, 440, T, yaw=16 * math.sin(lt * 1.4), screen=lambda c, r: cave_screen(c, r, T, seed=7160), seed=7570, glow=0.7)
        for k in range(8):
            a = t * 1.1 + k * 0.785
            sparkle(cv, 960 + 360 * math.cos(a), 520 + 300 * math.sin(a), 14 + 10 * math.sin(t * 5 + k), [P_["white"], P_["yellow"], P_["mint"]][k % 3], seed=9640 + k)
    logo_cpp(cv, 960, 190, 1.0, t, 34.22, seed=9810, shine_t=34.5)
    if 34.2 < t < 34.6:
        cv.drawRect(R(0, 0, W, H), paint(P_["white"], int(220 * (1 - _ph(t, 34.2, 34.45)))))
        lens_flare(cv, 1560, 210, t, k=1 - _ph(t, 34.2, 34.6), seed=9670)
    if t > 35.95:
        k = pop(t, 35.95, 0.45)
        cv.save(); cv.translate(960, 1000); cv.scale(k, k)
        paint_text(cv, "Don't look up.", 0, 0, font="shrik", size=104, fill=P_["cream"], ink_w=5.5, shadow=(7, 7), shadow_rgb=P_["magenta"], seed=9690, wobble=1.4)
        cv.restore()
        sparkle(cv, 1350, 905, 26 + 8 * math.sin(t * 7), P_["white"], seed=9691)
    if t > 34.9:
        k = pop(t, 34.9, 0.3)
        cv.save(); cv.translate(1650, 760); cv.scale(k * (1 + 0.05 * math.sin(t * 9)), k * (1 + 0.05 * math.sin(t * 9)))
        starburst(cv, 0, 0, 130, t, text="CALL", text2="NOW!", size=56, seed=9695)
        cv.restore()


def T033_ad(cv, t, T, A):
    """CAVE PHONE PRO: the commercial break (37.5 s). Break card -> B&W 'problem' footage -> hero reveal -> pocket -> infinite
    scroll -> SmartChains -> the no-turning demo -> Gary's testimonial -> side effects / you are the product -> end card."""
    if t < 1.9:
        _ad_break(cv, t, T)
    elif t < 6.27:
        _ad_problem(cv, t, T)
    elif t < 11.05:
        _ad_reveal(cv, t, T)
        if t < 6.5:
            cv.drawRect(R(0, 0, W, H), paint(P_["white"], int(255 * (1 - _ph(t, 6.27, 6.5)))))
    elif t < 12.55:
        _ad_pocket(cv, t, T)
    elif t < 16.45:
        _ad_scroll(cv, t, T)
    elif t < 18.25:
        _ad_chains(cv, t, T)
    elif t < 20.55:
        _ad_turn(cv, t, T)
    elif t < 26.1:
        _ad_gary(cv, t, T)
    elif t < 30.85:
        _ad_effects(cv, t, T)
    elif t < 34.05:
        _ad_product(cv, t, T)
    else:
        _ad_endcard(cv, t, T)


_AD_CUTS = (1.9, 6.27, 11.05, 12.55, 16.45, 18.25, 20.55, 26.1, 30.85, 34.05)


def _post_ad(img, lt, dur, T):
    """VHS: a little chroma bleed over the whole commercial, tape-tracking tears in the break card and on every cut."""
    o = img.copy()
    o[:, 2:, 0] = img[:, :-2, 0]
    o[:, :-1, 2] = img[:, 1:, 2]
    g = 0.0
    if lt < 1.9:
        g = 0.15 + 0.85 * float(np.clip((lt - 1.1) / 0.8, 0, 1))
    for c in _AD_CUTS[1:]:
        if 0 <= lt - c < 0.1:
            g = max(g, 0.7)
    if g > 0:
        rng = np.random.default_rng(int(round(T * 12)) + 77)
        for _ in range(int(3 + 10 * g)):
            y0 = int(rng.integers(0, H - 40)); hh = int(rng.integers(6, 70)); dx = int(rng.integers(-90, 90) * g)
            o[y0:y0 + hh] = np.roll(o[y0:y0 + hh], dx, axis=1)
    return o


POST = {"T033_ad": _post_ad}


# ===================================================================== T044 · "GOOD THING THAT'S ANCIENT HISTORY"
def dark_room(cv, lx, ly, r, a=235, rgb=(8, 4, 22)):
    """Everything outside the light pool around (lx, ly) sinks into the dark (drawn on top)."""
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(lx, ly), max(1.0, r), [core.C(rgb, 0), core.C(rgb, int(a * 0.55)), core.C(rgb, a)], [0.0, 0.55, 1.0]))
    cv.drawRect(R(-200, -200, W + 200, H + 200), p)


def stone_tablet(cv, x, y, s, t, t0, seed=11000):
    """A cracked marble museum tablet: ANCIENT HISTORY / c. 380 BC, with a Greek-key border and a puff of dust."""
    k = pop(t, t0, 0.35)
    if k <= 0:
        return
    cv.save(); cv.translate(x, y); cv.rotate(6 * math.sin(t * 1.3) * 0.3 + 4); cv.scale(k * s, k * s)
    blob(cv, [(-300, -170), (300, -180), (320, 160), (-310, 175)], P_["cream"], w=6, seed=seed, boil=1.0, n=3,
         shade=lambda c: (stipple(c, P_["cream_sh"], (-320, -190, 330, 190), spacing=13, r=1.8, seed=seed + 1, fn=lambda X, Y: np.clip((X + Y) / 500 + 0.4, 0, 1)),
                          c.drawRect(R(170, -200, 340, 200), paint(P_["cream_sh"], 140))))
    for sd in (-1, 1):
        pts = []
        for j in range(12):
            xx = -260 + j * 47
            yy = sd * 140
            pts += [(xx, yy), (xx, yy - sd * 18), (xx + 24, yy - sd * 18), (xx + 24, yy - sd * 6), (xx + 12, yy - sd * 6)]
        brush(cv, np.array(pts), 4, P_["gold"], taper=(0, 0), seed=seed + 2 + sd)
    line(cv, [(150, -170), (120, -60), (170, 20), (140, 110)], 3, mix(P_["cream_sh"], INK, 0.4), seed=seed + 5, boil=0.6, n=4, taper=(0.1, 0.4))
    paint_text(cv, "ANCIENT", 0, -30, font="titan", size=96, fill=P_["violet"], ink_w=4.5, shadow=(4, 4), shadow_rgb=P_["cream_sh"], seed=seed + 6)
    paint_text(cv, "HISTORY", 0, 70, font="titan", size=96, fill=P_["violet"], ink_w=4.5, shadow=(4, 4), shadow_rgb=P_["cream_sh"], seed=seed + 7)
    paint_text(cv, "c. 380 BC", 0, 122, font="marker", size=34, fill=P_["maroon"], ink_w=0, shadow=None, seed=seed + 8, streaks=False)
    cv.restore()
    u = _ph(t, t0, t0 + 0.8)
    if 0 < u < 1:
        for j in range(7):
            a_ = j / 7 * 2 * math.pi
            blob(cv, ell(x + (300 + 120 * u) * s * math.cos(a_), y + (180 + 80 * u) * s * math.sin(a_), 40 * s, 30 * s, n=8), P_["cream"], w=3, seed=seed + 20 + j,
                 boil=1.0, a=int(220 * (1 - u)))


def _host_cu(cv, t, T, A, z, dx=0.0, dy=0.0, **ov):
    cam = dict(x=CAM_HOST["x"] + dx, y=CAM_HOST["y"] + dy, z=z)
    return studio(cv, T, A, cam, t, host=ov or None)


def _m_bedroom(cv, t, T):
    """Nowadays nobody sits in the dark...: an eyeball up in bed at 3:47 AM, lit only by its phone, its huge shadow on the wall."""
    zf = 1.0 + 0.05 * (t - 2.62)
    cv.save(); cv.translate(W / 2, H / 2); cv.scale(zf, zf); cv.translate(-W / 2 - 40, -H / 2)
    cv.drawRect(R(-100, -100, W + 100, H + 100), _lin(0, 0, 0, H, [(30, 16, 70), (20, 10, 50)]))
    for k in range(9):                                            # wallpaper stars
        sparkle(cv, 120 + k * 210, 120 + 90 * (k % 3), 9, P_["vdark"], w=0, seed=11100 + k)
    wx0, wy0, wx1, wy1 = 140, 150, 600, 640                       # window: night city + moon
    blob(cv, rect_pts([(wx0, wy0), (wx1, wy0), (wx1, wy1), (wx0, wy1)], 3), P_["night"], w=6, seed=11110, boil=0.8, n=2,
         shade=lambda c: (c.drawRect(R(wx0, wy0, wx1, wy1), _lin(0, wy0, 0, wy1, [P_["void"], P_["deepblue"]])),
                          [c.drawRect(R(wx0 + 20 + k * 70, wy1 - 80 - 140 * hsh(11111 + k), wx0 + 80 + k * 70, wy1), paint((10, 8, 30))) for k in range(7)],
                          [dots(c, [(wx0 + 34 + k * 70 + 12 * (j % 2), wy1 - 60 - j * 24)], 3, P_["yellow"]) for k in range(7) for j in range(3) if hsh(k * 5 + j) > 0.5],
                          c.drawCircle(wx1 - 110, wy0 + 110, 50, paint(P_["cream"])), c.drawCircle(wx1 - 90, wy0 + 98, 46, paint(P_["deepblue"]))))
    line(cv, [((wx0 + wx1) / 2, wy0), ((wx0 + wx1) / 2, wy1)], 8, (40, 26, 80), seed=11112, boil=0.5, n=2, taper=(0, 0))
    line(cv, [(wx0, (wy0 + wy1) / 2), (wx1, (wy0 + wy1) / 2)], 8, (40, 26, 80), seed=11113, boil=0.5, n=2, taper=(0, 0))
    for sd in (-1, 1):                                            # curtains
        cx_ = wx0 - 10 if sd < 0 else wx1 + 10
        blob(cv, [(cx_ - 80 * (sd < 0) - 10, wy0 - 60), (cx_ + 80 * (sd > 0) + 10, wy0 - 60), (cx_ + sd * 40, wy1 + 120), (cx_ - sd * 70, wy1 + 120)],
             P_["maroon"], w=5, seed=11114 + sd, boil=0.9, n=3)
    blob(cv, rect_pts([(1180, 170), (1460, 170), (1460, 520), (1180, 520)], 3), (60, 30, 90), w=5, seed=11120, boil=0.8, n=2)     # poster: BOXED
    paint_text(cv, "BOXED", 1320, 300, font="shrik", size=64, fill=P_["magenta"], ink_w=3, shadow=None, seed=11121, streaks=False, a=170)
    w.planet(cv, 1320, 420, 60, mix(P_["orange"], P_["night"], 0.4), seed=11122, crater=False)
    # its huge shadow on the wall behind, cast by the phone (a cave, again)
    cv.drawCircle(1000, 430, 620, _rad2(1000, 430, 620, mix(P_["mint"], P_["teal"], 0.5), 120))
    sh_ = [(700, 760), (690, 380), (820, 170), (1000, 120), (1180, 170), (1310, 380), (1300, 760)]
    hp_ = skia.Paint(AntiAlias=True, Color=core.C((8, 4, 20), 230))
    hp_.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 16))
    cv.drawPath(poly_path(cr_closed(jit(sh_, 2.0, 11130), 5)), hp_)
    for sd in (-1, 1):
        line(cv, [(1000 + sd * 280, 560), (1000 + sd * 150, 640), (1000 + sd * 40, 600)], 60, (8, 4, 20), seed=11131 + sd, boil=1.0, n=4, taper=(0, 0), a=190)
    blob(cv, [(640, 1100), (640, 620), (700, 580), (1500, 580), (1560, 620), (1560, 1100)], (90, 60, 150), w=6, seed=11140, boil=0.8, n=3)       # headboard
    blob(cv, ell(820, 760, 170, 70, n=12), P_["cream"], w=5, seed=11141, boil=0.8)                                                            # pillow
    eyefolk(cv, 1000, 880, 2.0, T, seed=8500, look=(0.1, 0.95), lid=0.45, rgb=(100, 46, 160), iris=P_["teal"], phone_at="auto", glow=P_["mint"],
            phone_scr=P_["mint"], pupil=0.8)
    cv.drawCircle(1004, 640, 300, _rad2(1004, 640, 300, P_["mint"], 80))
    blob(cv, [(560, 1100), (600, 860), (1000, 820), (1450, 860), (1500, 1100)], P_["violet"], w=6, seed=11150, boil=1.0, n=4,                 # blanket
         shade=lambda c: [sparkle(c, 700 + k * 140, 930 + 40 * (k % 2), 14, P_["yellow"], w=2, seed=11151 + k) for k in range(6)])
    blob(cv, rect_pts([(1580, 760), (1820, 760), (1820, 1100), (1580, 1100)], 3), (70, 40, 100), w=5, seed=11160, boil=0.8, n=2)            # nightstand
    blob(cv, rect_pts([(1585, 660), (1720, 660), (1720, 760), (1585, 760)], 3), (24, 14, 34), w=5, seed=11161, boil=0.6, n=2)
    cv.restore()
    dark_room(cv, 990, 560, 1150, a=175)
    cv.drawCircle(990, 700, 560, _rad2(990, 700, 560, P_["mint"], 55))
    cv.save(); cv.translate(W / 2, H / 2); cv.scale(zf, zf); cv.translate(-W / 2 - 40, -H / 2)     # things that glow in the dark
    for k in range(11):
        gx_, gy_ = 120 + (k * 167) % 1700, 70 + (k * 97) % 260
        if 560 < gx_ < 1450 and gy_ > 100:
            continue
        cv.drawCircle(gx_, gy_, 26, _rad2(gx_, gy_, 26, P_["acid"], 120))
        sparkle(cv, gx_, gy_, 12 + 3 * math.sin(t * 3 + k), P_["acid"], w=1.5, seed=11170 + k)
    sets.lava(cv, 1740, 650, 0.62, t, seed=11175)
    cv.drawCircle(1740, 520, 200, _rad2(1740, 520, 200, P_["magenta"], 90))
    colon = ":" if int(T * 2) % 2 == 0 else " "
    paint_text(cv, "3" + colon + "47", 1655, 735, font="londrina", size=72, fill=P_["red"], ink_w=0, shadow=None, seed=11162, streaks=False, wobble=0.4)
    cv.drawCircle(1655, 705, 90, _rad2(1655, 705, 90, P_["red"], 80))
    paint_text(cv, "BOXED", 1320, 300, font="shrik", size=64, fill=P_["magenta"], ink_w=0, shadow=None, seed=11121, streaks=False, a=120)
    cv.restore()


def _m_couch(cv, t, T):
    """...staring at flickering lights: a whole eyeball family on the couch, lit by the TV, their shadows jumping on the wall."""
    zf = 1.3 + 0.05 * (t - 4.4)
    cv.save(); cv.translate(W / 2, H / 2); cv.scale(zf, zf); cv.translate(-W / 2 - 10, -H / 2 - 120)
    fl = 0.65 + 0.35 * hsh(core.D * 0.73)
    tint = [P_["teal"], P_["white"], P_["hotpink"], P_["blue"]][int(hsh(core.D * 0.41) * 4)]
    cv.drawRect(R(-100, -100, W + 100, H + 100), _lin(0, 0, 0, H, [(70, 20, 110), (40, 12, 80)]))
    w.sunburst(cv, 960, 1300, 2200, 24, [(80, 24, 120), (60, 16, 96)], rot_deg=4, seed=11199)
    for k in range(4):                                            # flickering shadows of the family on the back wall
        sx = 560 + k * 270
        sc = 2.0 + 0.25 * fl + (0.6 if k == 0 else 0)
        shadow_shape(cv, "jug", sx + 30 * fl, 330 - 10 * k, sc * (1.0 if k < 3 else 0.7), T, rgb=(14, 6, 30), a=int(150 + 60 * fl), seed=11200 + k, wobble=0.8)
    blob(cv, rect_pts([(1560, 160), (1820, 160), (1820, 420), (1560, 420)], 3), P_["gold"], w=5, seed=11210, boil=0.7, n=2,
         shade=lambda c: (c.drawRect(R(1580, 180, 1800, 400), paint((60, 30, 70))), shadow_shape(c, "horse", 1690, 300, 0.8, T, seed=11211)))
    w.couch(cv, 960, 980, 1.35, seed=11220, rgb=P_["orange"], rgb2=P_["red"], part="back")
    fam = [(620, 900, 1.75, 8600, (110, 50, 150), None, P_["teal"]), (930, 905, 1.45, 8610, (150, 60, 160), P_["hotpink"], P_["acid"]),
           (1180, 910, 1.05, 8620, (90, 40, 150), None, P_["orange"]), (1370, 915, 0.75, 8630, (130, 70, 170), P_["yellow"], P_["hotpink"])]
    for x, y, s, sd, col, bow, iris in fam:
        eyefolk(cv, x, y, s, T, seed=sd, look=(0.0, 0.25), lid=0.4, rgb=col, iris=iris, bow=bow, glow=tint, pupil=1.25, mouth=0.15 if s < 1 else 0.0)
    blob(cv, ell(640, 880, 120, 40, n=12), P_["red"], w=5, seed=11230, boil=0.7,                                                               # popcorn
         shade=lambda c: c.drawRect(R(520, 880, 760, 930), paint(P_["white"], 120)))
    for k in range(9):
        blob(cv, ell(560 + k * 20, 855 - 14 * (k % 3), 14, 12, n=7), P_["cream"], w=2.5, seed=11231 + k, boil=0.6)
    w.couch(cv, 960, 980, 1.35, seed=11220, rgb=P_["orange"], rgb2=P_["red"], part="front")
    cv.restore()
    dark_room(cv, 960, 700, 1200, a=int(110 + 50 * (1 - fl)))
    lp = skia.Paint(AntiAlias=True)
    lp.setShader(skia.GradientShader.MakeRadial(skia.Point(960, 1150), 1100, [core.C(tint, int(120 * fl)), core.C(tint, int(45 * fl)), core.C(tint, 0)], [0.0, 0.5, 1.0]))
    cv.drawRect(R(0, 0, W, H), lp)
    blob(cv, rect_pts([(380, 980), (1540, 980), (1560, 1140), (360, 1140)], 3), (16, 10, 26), w=6, seed=11240, boil=0.7, n=2)                   # the TV, from behind
    for sd in (-1, 1):
        line(cv, [(960 + sd * 60, 990), (960 + sd * 260, 840)], 6, (90, 90, 110), seed=11241 + sd, boil=0.6, n=2, taper=(0, 0))
        dots(cv, [(960 + sd * 262, 836)], 10, P_["orange"])


def _m_subway(cv, t, T):
    """...on a flat rectangle: a whole subway car, everyone lit by their own little rectangle. The camera trucks along."""
    pan = 120 * (t - 5.75)
    sway = 6 * math.sin(t * 5.3)
    cv.save(); cv.translate(-pan, sway + 40); cv.scale(1.2, 1.2)
    cv.drawRect(R(-100, -100, W + 600, H + 100), paint((60, 40, 100)))
    for k in range(4):                                            # windows: black tunnel with streaking lights
        x0 = 40 + k * 560
        blob(cv, rrect_pts(x0, 140, x0 + 460, 480, 40, n=3), (10, 6, 22), w=6, seed=11300 + k, boil=0.8, n=3,
             shade=lambda c, x0=x0: [line(c, [(x0 + ((t * 2600 + j * 230) % 900) - 300, 210 + j * 55), (x0 + ((t * 2600 + j * 230) % 900) - 40, 210 + j * 55)], 12,
                                          [P_["yellow"], P_["hotpink"], P_["teal"], P_["acid"]][j % 4], seed=11310 + j, boil=0.3, n=2, taper=(0.6, 0.3), a=230)
                                     for j in range(5)])
    cv.drawRect(R(-100, 0, 2500, 26), paint(P_["magenta"]))
    cv.drawRect(R(-100, 26, 2500, 120), _lin(0, 26, 0, 120, [P_["magenta"], (60, 40, 100)], a=120))
    for k in range(4):                                            # ad panels above the windows
        x0 = 60 + k * 560
        blob(cv, rect_pts([(x0, 40), (x0 + 420, 40), (x0 + 420, 120), (x0, 120)], 3), [P_["magenta"], P_["teal"], P_["yellow"], P_["orange"]][k], w=4.5,
             seed=11320 + k, boil=0.7, n=2)
        paint_text(cv, ["CAVE PHONE PRO", "DON'T LOOK UP", "SMARTCHAINS", "INFINITE SCROLL"][k], x0 + 210, 98, font="bangers", size=50, fill=P_["white"], ink_w=3,
                   shadow=(3, 3), seed=11330 + k, streaks=False)
    for k in range(9):                                            # grab poles + swinging straps
        px = 260 + k * 300
        line(cv, [(px, 0), (px, 1100)], 14, (190, 190, 210), seed=11340 + k, boil=0.4, n=2, taper=(0, 0))
        sw = 14 * math.sin(t * 5.3 + k)
        line(cv, [(px + 150, 0), (px + 150 + sw, 150)], 5, (140, 140, 160), seed=11350 + k, boil=0.4, n=2, taper=(0, 0))
        blob(cv, ell(px + 150 + sw * 1.2, 175, 24, 22, n=8), None, w=5, seed=11360 + k, boil=0.5)
    blob(cv, rect_pts([(-100, 760), (2500, 760), (2500, 860), (-100, 860)], 3), P_["orange"], w=6, seed=11370, boil=0.8, n=2,       # bench
         shade=lambda c: [c.drawLine(-100 + k * 90, 760, -100 + k * 90, 860, paint(P_["red"], stroke=4)) for k in range(30)])
    cv.drawRect(R(-100, 860, 2500, 1200), paint((40, 26, 70)))
    cols = [(110, 50, 150), (150, 60, 160), (90, 40, 150), (130, 70, 170), (70, 40, 130)]
    for k in range(9):
        x = 200 + k * 250
        eyefolk(cv, x, 800, 1.6, T, seed=8700 + k * 9, look=(0.1, 0.95), lid=0.5, rgb=cols[k % 5], phone_at="auto", glow=P_["mint"], pupil=0.9,
                bow=P_["hotpink"] if k == 3 else None)
    cv.restore()


def _city_windows(cv, x0, y0, x1, y1, T, seed, cell=(56, 70), faces=True, s=1.0):
    """Grid of glowing screen-lit windows, each with an eyeball face bent over a phone."""
    cw, ch = cell
    cols = [P_["mint"], P_["teal"], P_["hotpink"], (150, 180, 255), P_["lilac"]]
    nx = int((x1 - x0 - 16) // cw)
    ny = int((y1 - y0 - 16) // ch)
    for j in range(ny):
        for i in range(nx):
            h = float(hsh(seed + i * 7.3 + j * 3.1))
            if h < 0.12:
                continue
            wx, wy = x0 + 12 + i * cw, y0 + 14 + j * ch
            c = cols[int(h * 97) % 5]
            fl = 0.85 + 0.15 * math.sin(T * (3 + 5 * h) + i + j)
            cv.drawRect(R(wx, wy, wx + cw - 16, wy + ch - 18), paint(mix(c, P_["white"], 0.2 * fl)))
            if faces and h > 0.25:
                fx_, fy_ = wx + (cw - 16) * (0.3 + 0.4 * hsh(seed + i + j * 11)), wy + ch - 18
                r = (cw - 16) * 0.32
                cv.drawCircle(fx_, fy_ - r * 0.7, r, paint((24, 12, 44)))
                cv.drawCircle(fx_ + r * 0.1, fy_ - r * 0.85, r * 0.45, paint(P_["white"]))
                cv.drawCircle(fx_ + r * 0.15, fy_ - r * 0.7, r * 0.22, paint(INK))
                cv.drawRect(R(fx_ - r * 0.3, fy_ - r * 0.25, fx_ + r * 0.3, fy_), paint(mix(c, P_["white"], 0.7)))


def _m_city(cv, t, T):
    """MODERN: a night city where every window is a lit screen with a face in it; charging cables hang like chains;
    a shooting star crosses the psychedelic sky and nobody looks up."""
    lt = t - 7.43
    rise = ease(_ph(t, 7.43, 10.85))
    C = sets.Cam(cv, dict(x=0, y=lerp(300, -330, rise), z=1.04 + 0.03 * lt))
    with C.layer(0.15):
        cv.drawRect(R(-400, -600, W + 400, 1300), _lin(0, -500, 0, 1000, [P_["void"], P_["night"], P_["vdark"], P_["magenta"]], [0.0, 0.35, 0.7, 1.0]))
        w.stars(cv, 11401, (-300, -500, W + 300, 700), n=260, big=10)
        w.sunburst(cv, 960, -300, 1500, 24, [mix(P_["night"], P_["violet"], 0.35), P_["night"]], rot_deg=t * 3, seed=11402)
        w.skull_moon(cv, 330, 110, 70, seed=11403)
        w.planet(cv, 1520, 150, 150, P_["orange"], bands=[(-0.55, 0.22, P_["red"]), (-0.1, 0.18, P_["yellow"]), (0.32, 0.24, P_["magenta"])],
                 ring=dict(rx=1.75, ry=0.33, rgb=P_["teal"], rgb2=P_["cream"], tilt=-16),
                 face=dict(look=(-0.3, 0.9), smile=-0.2, lids=0.55, lid_rgb=P_["orange"]), seed=11404)
        if 9.3 < t < 10.6:                                        # the shooting star nobody sees
            u = _ph(t, 9.3, 10.3)
            sx, sy = lerp(200, 1450, u), lerp(-20, 300, u)
            for j in range(14):
                dots(cv, [(sx - j * 34, sy - j * 7.5)], 15 - j, [P_["white"], P_["yellow"], P_["hotpink"]][j % 3], a=int(255 * (1 - j / 14)))
            sparkle(cv, sx, sy, 48 + 10 * math.sin(t * 20), P_["white"], seed=11405)
        w.eye_bat(cv, 420 + 60 * math.sin(t * 0.7), 380 + 20 * math.sin(t * 1.9), 0.8, t * 2, seed=11406)
    with C.layer(0.4):                                            # far skyline
        for k in range(12):
            bx = -150 + k * 190
            bh = 300 + 260 * hsh(11410 + k)
            blob(cv, rect_pts([(bx, 900 - bh), (bx + 170, 900 - bh), (bx + 170, 1300), (bx, 1300)], 2), (34, 16, 70), w=4, seed=11420 + k, boil=0.6, n=2)
            _city_windows(cv, bx, 900 - bh, bx + 170, 1100, T, 11430 + k * 13, cell=(34, 44), faces=False)
    with C.layer(0.7):                                            # mid buildings + the billboard
        for k in range(7):
            bx = -100 + k * 320
            bh = 420 + 300 * hsh(11440 + k)
            col = [(60, 30, 110), (80, 30, 120), (50, 24, 96)][k % 3]
            blob(cv, rect_pts([(bx, 1000 - bh), (bx + 280, 1000 - bh), (bx + 280, 1400), (bx, 1400)], 2), col, w=5, seed=11450 + k, boil=0.7, n=2)
            _city_windows(cv, bx, 1000 - bh, bx + 280, 1250, T, 11460 + k * 17, cell=(46, 58))
        bbx, bby = 700, 300
        line(cv, [(bbx + 60, bby + 130), (bbx + 60, bby + 260)], 12, (40, 30, 60), seed=11470, boil=0.4, n=2, taper=(0, 0))
        line(cv, [(bbx + 360, bby + 130), (bbx + 360, bby + 260)], 12, (40, 30, 60), seed=11471, boil=0.4, n=2, taper=(0, 0))
        gloss_panel(cv, bbx - 20, bby - 120, bbx + 440, bby + 140, [P_["magenta"], P_["violet"], P_["night"]], seed=11472, r=14)
        chrome_text(cv, "CAVE PHONE PRO", bbx + 210, bby - 30, 60, font="titan", seed=11473, depth=5, ink=3, glints=1)
        paint_text(cv, "DON'T LOOK UP", bbx + 210, bby + 60, font="shrik", size=58, fill=P_["cream"], ink_w=3, shadow=(3, 3), shadow_rgb=P_["night"], seed=11474,
                   streaks=False)
        cv.drawCircle(bbx + 210, bby + 10, 330, _rad2(bbx + 210, bby + 10, 330, P_["magenta"], 60))
    with C.layer(1.0):                                            # near building faces, cables like chains, the street
        for k, (bx, bw_, bh) in enumerate(((-60, 520, 760), (1380, 600, 820))):
            blob(cv, rect_pts([(bx, 1180 - bh), (bx + bw_, 1180 - bh), (bx + bw_, 1500), (bx, 1500)], 2), (40, 18, 80), w=6, seed=11480 + k, boil=0.8, n=2)
            _city_windows(cv, bx, 1180 - bh, bx + bw_, 1400, T, 11490 + k * 23, cell=(104, 120))
            for j in range(5):                                    # charging cables dangling from the windows like chains
                cx_ = bx + 70 + j * (bw_ - 120) / 4
                cy_ = 1180 - bh + 110 + 120 * (j % 3)
                chain(cv, (cx_, cy_), (960 + (cx_ - 960) * 0.25, 1240), seed=11500 + k * 10 + j, link=18, sag=60, rgb=(90, 90, 120), w=2.6)
        blob(cv, rect_pts([(600, 1180), (1320, 1180), (1320, 1240), (600, 1240)], 3), P_["cream"], w=6, seed=11520, boil=0.8, n=2,                  # the power strip
             shade=lambda c: [c.drawCircle(650 + k * 68, 1210, 12, paint(INK)) for k in range(10)])
        cv.drawCircle(960, 1210, 420, _rad2(960, 1210, 420, P_["orange"], 90))
        cv.drawRect(R(-200, 1250, W + 200, 1600), paint((30, 14, 56)))
        brush(cv, np.array([(-200, 1250), (W + 200, 1252)]), 5, taper=(0.02, 0.02), seed=11521)
        for k in range(5):                                        # heads-down walkers; one walks into a lamp post
            ax = 380 + ((t * 60 + k * 230) % 1200)
            agent(cv, ax, 1350, 1.15, phase=t * 1.4 + k * 0.3, rgb=[P_["orange"], P_["teal"], P_["hotpink"], P_["yellow"], P_["lilac"]][k], seed=11530 + k, look=0.6)
            blob(cv, rect_pts([(ax + 6, 1350 - 96), (ax + 22, 1350 - 96), (ax + 22, 1350 - 74), (ax + 6, 1350 - 74)], 2), P_["mint"], w=2.5, seed=11535 + k, boil=0.4, n=2)
        line(cv, [(840, 1360), (840, 1080)], 14, (60, 60, 80), seed=11540, boil=0.5, n=2, taper=(0, 0))
        blob(cv, ell(840, 1070, 36, 20, n=8), P_["yellow"], w=4, seed=11541, boil=0.5)


def _m_timelapse(cv, t, T):
    """...for hours...: the room races through days (window, clock, calendar, pizza boxes, cobwebs) - the eyeball doesn't move."""
    lt = t - 10.85
    spd = 1.0 + 3.0 * _ph(t, 10.85, 11.6)
    dayp = (lt * 1.6 * spd) % 1.0
    cv.save(); cv.translate(W / 2, H / 2); cv.scale(1.12 + 0.03 * lt, 1.12 + 0.03 * lt); cv.translate(-W / 2, -H / 2 + 20)
    cv.drawRect(R(-50, -50, W + 50, H + 50), _lin(0, 0, 0, H, [(70, 40, 110), (50, 26, 86)]))
    wx0, wy0, wx1, wy1 = 1220, 140, 1700, 560
    sky = mix(P_["night"], (120, 200, 255), max(0.0, math.sin(dayp * 2 * math.pi)))
    blob(cv, rect_pts([(wx0, wy0), (wx1, wy0), (wx1, wy1), (wx0, wy1)], 3), sky, w=6, seed=11600, boil=0.8, n=2,
         shade=lambda c: (c.drawCircle(lerp(wx0 - 60, wx1 + 60, dayp), wy1 - 300 * math.sin(dayp * math.pi), 50, paint(P_["yellow"])),
                          c.drawCircle(lerp(wx0 - 60, wx1 + 60, (dayp + 0.5) % 1.0), wy1 - 300 * math.sin(((dayp + 0.5) % 1.0) * math.pi), 40, paint(P_["cream"]))))
    line(cv, [((wx0 + wx1) / 2, wy0), ((wx0 + wx1) / 2, wy1)], 8, (90, 60, 120), seed=11601, boil=0.5, n=2, taper=(0, 0))
    melting_clock(cv, 780, 260, 1.15, phase=lt * 40 * spd, seed=11610)
    k = int(lt * 9 * spd)                                         # calendar pages flying off
    blob(cv, rect_pts([(330, 160), (560, 160), (560, 420), (330, 420)], 3), P_["cream"], w=5, seed=11620, boil=0.7, n=2,
         shade=lambda c: c.drawRect(R(330, 160, 560, 220), paint(P_["red"])))
    paint_text(cv, "DAY", 445, 210, font="londrina", size=44, fill=P_["white"], ink_w=0, shadow=None, seed=11621, streaks=False)
    paint_text(cv, str(1 + k * 3), 445, 360, font="titan", size=110, fill=INK, ink_w=0, shadow=None, seed=11622, streaks=False)
    for j in range(3):
        u = ((lt * 9 * spd) - k + j / 3.0) % 1.0
        px_, py_ = 445 + 300 * u + 40 * j, 290 - 200 * u + 80 * u * u
        blob(cv, rot(rect_pts([(px_ - 70, py_ - 80), (px_ + 70, py_ - 80), (px_ + 70, py_ + 80), (px_ - 70, py_ + 80)], 2), u * 300, px_, py_), P_["cream"], w=4,
             seed=11623 + j, boil=0.6, n=2, a=int(255 * (1 - u)))
    w.couch(cv, 900, 1010, 1.3, seed=11630, rgb=P_["orange"], rgb2=P_["red"], part="back")
    web = _ph(t, 11.0, 12.3)
    tvl = [P_["teal"], P_["hotpink"], P_["white"], P_["blue"]][int(hsh(core.D * 0.53) * 4)]
    eyefolk(cv, 900, 930, 1.8, T, seed=8800, look=(0.0, 0.25), lid=0.55, rgb=(100, 46, 160), glow=tvl, pupil=1.2)
    w.couch(cv, 900, 1010, 1.3, seed=11630, rgb=P_["orange"], rgb2=P_["red"], part="front")
    for j in range(int(7 * web)):                                 # cobwebs growing over him
        a_ = -3.0 + j * 0.5
        line(cv, [(900 + 20 * math.cos(a_), 690 + 20 * math.sin(a_)), (900 + 260 * math.cos(a_), 700 + 200 * math.sin(a_) + 40)], 3.2, P_["white"], seed=11640 + j,
             boil=0.5, n=2, taper=(0.1, 0.1), a=210)
    for j in range(1, 4):
        if web > j / 4:
            brush(cv, cr_closed(ell(900, 700, 70 * j, 55 * j, n=8), 2)[:22], 2.6, P_["white"], taper=(0.1, 0.1), seed=11650 + j, a=190)
    if web > 0.5:
        line(cv, [(1010, 620), (1010, 680 + 10 * math.sin(t * 3))], 2, P_["white"], seed=11655, boil=0.4, n=2, taper=(0, 0))
        blob(cv, ell(1010, 690 + 10 * math.sin(t * 3), 12, 10, n=8), INK, w=0, seed=11656, boil=0.5, misreg=(0, 0))
    nb = min(9, int(lt * 6 * spd))                                # pizza boxes stacking up
    for j in range(nb):
        bx_, by_ = 1500 + 6 * math.sin(j * 1.7), 1040 - j * 44
        blob(cv, rect_pts([(bx_ - 150, by_ - 40), (bx_ + 150, by_ - 40), (bx_ + 150, by_), (bx_ - 150, by_)], 2), (240, 200, 140), w=4, seed=11660 + j, boil=0.6, n=2,
             shade=lambda c, by_=by_, bx_=bx_: c.drawRect(R(bx_ - 150, by_ - 40, bx_ + 150, by_ - 30), paint(P_["red"])))
    cv.restore()
    day = max(0.0, math.sin(dayp * 2 * math.pi))
    cv.drawRect(R(0, 0, W, H), paint(P_["night"], int(110 * (1 - day))))
    cv.drawRect(R(0, 0, W, H), paint(P_["yellow"], int(50 * day)))
    cv.drawRect(R(0, 0, W, H), paint(tvl, 22))
    for dx in (0, 46):                                            # VHS fast-forward
        for o, col in ((4, INK), (0, P_["acid"])):
            cv.drawPath(poly_path([(1500 + dx + o, 90 + o), (1546 + dx + o, 120 + o), (1500 + dx + o, 150 + o)]), paint(col))
    paint_text(cv, "x1000", 1610, 146, font="londrina", size=64, fill=P_["acid"], ink_w=0, shadow=(4, 4), seed=11670, streaks=False, align="left", wobble=0.5)


HEADLINES = [("BREAKING", "SHADOWS NOW 40% MORE REAL"), ("EXPERTS", "LOOKING UP CAUSES NECK"), ("BREAKING", "BUNNY ELECTED MAYOR"),
             ("JUST IN", "SUN DECLARED A HOAX"), ("OPINION", "WALL SAYS: TRUST THE WALL"), ("CONFIRMED", "MOON 100% CHEESE"),
             ("BREAKING", "TURNING AROUND: DANGEROUS?")]


def _m_headlines(cv, t, T):
    """...believing whatever shows up...: an absurd headline feed flips by on a huge screen; three eyeballs nod along."""
    lt = t - 12.4
    zf = 1.0 + 0.04 * lt
    cv.save(); cv.translate(W / 2, H / 2); cv.scale(zf, zf); cv.translate(-W / 2, -H / 2)
    cv.drawRect(R(-60, -60, W + 60, H + 60), paint((26, 12, 50)))
    x0, y0, x1, y1 = 180, 70, 1740, 840
    blob(cv, rect_pts([(x0 - 30, y0 - 30), (x1 + 30, y0 - 30), (x1 + 30, y1 + 30), (x0 - 30, y1 + 30)], 3), (20, 16, 30), w=7, seed=11700, boil=0.8, n=2)
    idx = int(lt / 0.36) % len(HEADLINES)
    k = pop(lt, idx * 0.36 if lt < len(HEADLINES) * 0.36 else (lt // 0.36) * 0.36, 0.22)
    cv.save(); cv.clipRect(R(x0, y0, x1, y1))
    cv.drawRect(R(x0, y0, x1, y1), _lin(0, y0, 0, y1, [P_["blue"], P_["deepblue"]]))
    w.sunburst(cv, (x0 + x1) / 2, (y0 + y1) / 2, 1200, 20, [P_["blue"], mix(P_["blue"], P_["deepblue"], 0.5)], rot_deg=t * 20, seed=11701)
    tag_, head_ = HEADLINES[idx]
    cv.save(); cv.translate((x0 + x1) / 2, (y0 + y1) / 2 - 20); cv.scale(0.7 + 0.3 * k, 0.7 + 0.3 * k)
    gloss_panel(cv, -700, -230, -220, -130, [P_["red"], P_["maroon"], P_["red"]], seed=11702 + idx, r=14)
    paint_text(cv, tag_, -460, -160, font="titan", size=64, fill=P_["white"], ink_w=4, shadow=(4, 4), seed=11703 + idx, streaks=False)
    words = head_.split(" ")
    half = (len(words) + 1) // 2
    for j, ln in enumerate((" ".join(words[:half]), " ".join(words[half:]))):
        paint_text(cv, ln, 0, -10 + j * 150, font="titan", size=128, fill=[P_["yellow"], P_["cream"]][j], ink_w=6, shadow=(8, 8), shadow_rgb=INK,
                   seed=11710 + idx * 3 + j, wobble=1.6)
    cv.restore()
    cv.drawRect(R(x0, y1 - 90, x1, y1), paint(P_["red"]))
    off = (lt * 900) % 2600
    tick = "  ·  ".join(h for _, h in HEADLINES) + "  ·  "
    paint_text(cv, tick, x1 - off, y1 - 26, font="londrina", size=56, fill=P_["white"], ink_w=0, shadow=None, seed=11720, streaks=False, align="left", wobble=0.5)
    for k_ in range(0, (y1 - y0) // 6):
        cv.drawRect(R(x0, y0 + k_ * 6, x1, y0 + k_ * 6 + 2), paint(INK, 35))
    cv.restore()
    cv.drawCircle(960, 500, 900, _rad2(960, 500, 900, P_["blue"], 70))
    cv.restore()
    nod = abs(math.sin(lt * 2 * math.pi * 1.6))
    for j, (hx, hr, col) in enumerate(((420, 210, (60, 26, 100)), (960, 250, (80, 34, 120)), (1500, 210, (54, 22, 92)))):
        hy = 1030 + 34 * nod
        blob(cv, ell(hx, hy, hr, hr * 1.05, n=14), col, w=6, seed=11730 + j, boil=1.0,
             shade=lambda c, hx=hx, hy=hy, hr=hr: c.drawPath(poly_path(cr_closed(ell(hx, hy - hr * 0.95, hr * 0.85, hr * 0.28, n=10), 3)), paint(P_["blue"], 120)))
        line(cv, [(hx - hr * 0.55, hy - hr * 0.7), (hx, hy - hr * 0.84), (hx + hr * 0.55, hy - hr * 0.7)], 5, P_["teal"], seed=11735 + j, boil=0.6, n=4, a=200)
    if lt > 0.5:
        for j in range(3):
            kk = pop(lt, 0.5 + j * 0.25, 0.25)
            if kk > 0:
                cv.save(); cv.translate([560, 960, 1360][j], 690 - 20 * nod); cv.rotate([-8, 4, 9][j]); cv.scale(kk, kk)
                blob(cv, ell(0, 0, 120, 62, n=12), P_["white"], w=5, seed=11740 + j, boil=0.8)
                blob(cv, [(-20, 50), (20, 50), (-40, 100)], P_["white"], w=4, seed=11743 + j, boil=0.5, n=2)
                paint_text(cv, ["SO TRUE", "WOW!", "FACTS"][j], 0, 22, font="bangers", size=64, fill=P_["violet"], ink_w=3, shadow=None, seed=11745 + j, streaks=False)
                cv.restore()


def T044_ancient_history(cv, t, T, A):
    """H20 + MODERN + H21: the host, relieved, calls it ancient history; the montage contradicts him (bedroom phone glow, TV
    family, subway of screens, a city of lit rectangles chained by charging cables, the hours melting, a headline feed and
    nodding eyeballs), and we land back on him just as it starts to sink in."""
    if t < 2.62:
        z = 1.85 + 0.03 * t
        _host_cu(cv, t, T, A, z, smile=max(0.55, float(A["HOST"].get("smile", 0.3))))
        stone_tablet(cv, 330, 500, 0.78, t, 1.45)
        if t < 0.7:
            for j in range(5):
                sparkle(cv, 760 + 420 * hsh(11800 + j), 220 + 300 * hsh(11810 + j), 14 + 8 * math.sin(t * 9 + j), P_["yellow"], seed=11820 + j)
    elif t < 4.4:
        _m_bedroom(cv, t, T)
    elif t < 5.75:
        _m_couch(cv, t, T)
    elif t < 7.43:
        _m_subway(cv, t, T)
    elif t < 10.85:
        _m_city(cv, t, T)
    elif t < 12.4:
        _m_timelapse(cv, t, T)
    elif t < 14.1:
        _m_headlines(cv, t, T)
    else:
        u = _ph(t, 14.25, 14.8)
        hp = dict(A["HOST"])
        z = 2.05 + 0.25 * ease(_ph(t, 14.1, 14.82))
        ov = dict(smile=lerp(float(hp.get("smile", 0.3)), -0.05, u), browL=lerp(0.0, 0.55, u), browR=lerp(0.0, 0.55, u), px=lerp(float(hp.get("px", 0.0)), 0.0, u),
                  py=lerp(float(hp.get("py", 0.0)), 0.0, u), glitch=0.12 * u)
        _host_cu(cv, t, T, A, z, dy=-25, **ov)


# ===================================================================== T047 · "EVERYBODY'S WATCHING SOME KIND OF WALL"
MONSTER = [(-80, 100), (-92, 40), (-118, 10), (-162, -18), (-196, -62), (-172, -56), (-184, -96), (-152, -62), (-140, -100), (-124, -52), (-96, -40),
           (-78, -76), (-98, -132), (-56, -96), (-30, -116), (-14, -170), (4, -112), (40, -104), (96, -88), (134, -98), (108, -70), (126, -56), (90, -58),
           (120, -40), (78, -30), (110, -14), (150, -60), (196, -100), (182, -60), (214, -64), (168, -20), (118, 10), (112, 52), (92, 100), (40, 100),
           (16, 66), (-14, 66), (-30, 100)]


def big_shadow(cv, pts, x, y, s, T, rgb=None, a=230, seed=12000, blur=12):
    rgb = rgb or CV_SHADOW
    fl = 1.0 + 0.03 * math.sin(T * 9 + seed)
    P = np.array([(x + px * s * fl, y + py * s * fl) for px, py in pts])
    path = poly_path(cr_closed(jit(P, 1.5, seed), 4))
    hp = skia.Paint(AntiAlias=True, Color=core.C(rgb, int(a * 0.5)))
    hp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur * s / 3 + 2))
    cv.drawPath(path, hp)
    cv.drawPath(path, paint(rgb, a))


def angel_tv(cv, x, y, s, t, seed=12100, horns=0.0, halo=1.0, face_smile=0.7):
    """A cute retro TV with a smiling face, flapping feathery wings and a gold halo (or, briefly, devil horns)."""
    flap = math.sin(t * 7)
    for sd in (-1, 1):
        cv.save(); cv.translate(x + sd * 150 * s, y - 20 * s); cv.rotate(sd * (10 + 14 * flap)); cv.scale(sd * s, s)
        wing = [(0, -20), (60, -80), (160, -122), (250, -112), (304, -72), (272, -42), (292, -10), (250, 10), (262, 40), (212, 50), (214, 82), (152, 70), (132, 96),
                (72, 60), (0, 30)]
        blob(cv, wing, P_["white"], w=4.5, seed=seed + sd * 10, boil=0.8, n=4,
             shade=lambda c: [c.drawLine(40 + j * 46, 0, 120 + j * 44, -70 + j * 22, paint(P_["lilac"], stroke=3)) for j in range(4)])
        blob(cv, [(0, -14), (60, -60), (150, -86), (200, -60), (150, -30), (80, 10), (0, 20)], (236, 236, 255), w=3, seed=seed + 3 + sd * 10, boil=0.6, n=3)
        cv.restore()
    w.tv(cv, x, y, s, seed=seed + 20, body=P_["teal"],
         screen=lambda c, r: (c.drawRect(R(r[0] - r[2] / 2, r[1] - r[3] / 2, r[0] + r[2] / 2, r[1] + r[3] / 2), paint((30, 70, 90))),
                              [dots(c, [(r[0] + sd * r[2] * 0.2, r[1] - r[3] * 0.12)], r[3] * 0.08, (190, 255, 214)) for sd in (-1, 1)],
                              line(c, [(r[0] - r[2] * 0.2, r[1] + r[3] * 0.12), (r[0], r[1] + r[3] * (0.12 + 0.12 * face_smile)), (r[0] + r[2] * 0.2, r[1] + r[3] * 0.12)],
                                   5, (190, 255, 214), seed=seed + 30, boil=0.6, n=4)))
    if halo > 0.01:
        hy = y - 230 * s - 8 * s * math.sin(t * 2.5)
        cv.drawCircle(x, hy, 160 * s, _rad2(x, hy, 160 * s, P_["yellow"], int(130 * halo)))
        pp = cr_closed(jit(ell(x, hy, 110 * s, 28 * s, n=14), 1.0, seed + 40), 3)
        brush(cv, pp, 28 * s + 8, INK, closed=True, seed=seed + 41, a=int(255 * halo))
        brush(cv, pp, 22 * s, P_["gold"], closed=True, seed=seed + 41, a=int(255 * halo))
        brush(cv, pp[:20] + np.array([0, -4 * s]), 6 * s, P_["white"], taper=(0.3, 0.3), seed=seed + 42, a=int(200 * halo))
    if horns > 0.01:
        for sd in (-1, 1):
            hx, hy = x + sd * 100 * s, y - 120 * s
            blob(cv, [(hx - sd * 30 * s, hy), (hx + sd * 30 * s, hy), (hx + sd * 50 * s * horns, hy - 90 * s * horns)], P_["red"], w=4.5, seed=seed + 50 + sd, boil=0.7, n=3)


def scribble_out(cv, x0, y0, x1, y1, k, seed=12200, rgb=None):
    """A violent marker scribble across a word, drawn on with k 0..1."""
    if k <= 0:
        return
    pts = []
    n = 9
    for j in range(n):
        u = j / (n - 1)
        pts.append((lerp(x0, x1, u), (y0 if j % 2 == 0 else y1) + 6 * math.sin(j * 2.1)))
    m = max(2, int(len(pts) * k))
    line(cv, pts[:m], 22, INK, seed=seed, boil=1.0, n=3, taper=(0.05, 0.05))
    line(cv, pts[:m], 15, rgb or P_["red"], seed=seed, boil=1.0, n=3, taper=(0.05, 0.05))


def _w_angel(cv, t, T):
    zf = 1.0 + 0.03 * (t - 1.25)
    cv.save(); cv.translate(W / 2, H / 2); cv.scale(zf, zf); cv.translate(-W / 2, -H / 2)
    cv.drawRect(R(-60, -60, W + 60, H + 60), paint(P_["hotpink"]))
    w.sunburst(cv, 960, 560, 2400, 26, [mix(P_["yellow"], P_["cream"], 0.4), P_["hotpink"]], rot_deg=t * 9, seed=12300)
    w.halo(cv, 960, 560, [520, 430, 340], [P_["lilac"], P_["cream"], P_["yellow"]], seed=12301, ink=4, wob=8)
    for k in range(7):                                            # clouds
        cx_ = (hsh(12310 + k) * 2200 + t * 40 * (0.5 + hsh(12320 + k))) % 2300 - 200
        cy_ = 700 + 260 * hsh(12330 + k)
        blob(cv, [(cx_ - 160, cy_ + 30), (cx_ - 130, cy_ - 40), (cx_ - 40, cy_ - 80), (cx_ + 60, cy_ - 70), (cx_ + 150, cy_ - 20), (cx_ + 160, cy_ + 30)],
             P_["white"], w=5, seed=12340 + k, boil=1.0, n=4, shade=lambda c, cx_=cx_, cy_=cy_: c.drawRect(R(cx_ - 200, cy_ + 5, cx_ + 200, cy_ + 60), paint(P_["lilac"], 120)))
    horns = ease(_ph(t, 2.95, 3.2)) * (1 - ease(_ph(t, 3.5, 3.6)))
    halo = 1.0 - horns
    angel_tv(cv, 960, 540 + 14 * math.sin(t * 2.2), 1.25, t, horns=horns, halo=halo, face_smile=0.8 - 1.4 * horns)
    if 3.5 < t < 4.05:
        u = _ph(t, 3.5, 4.05)
        for j in range(8):
            a_ = j / 8 * 2 * math.pi
            blob(cv, ell(960 + 160 * u * math.cos(a_), 360 + 90 * u * math.sin(a_), 50 * (1 - u * 0.5), 40 * (1 - u * 0.5), n=8), P_["white"], w=3, seed=12350 + j,
                 boil=1.0, a=int(255 * (1 - u)))
    for k in range(6):
        sparkle(cv, 960 + 520 * math.cos(t + k * 1.05), 520 + 300 * math.sin(t * 1.2 + k), 16 + 8 * math.sin(t * 6 + k), P_["white"], seed=12360 + k)
    cv.restore()
    if t > 2.45:
        paint_text(cv, "SCREENS ARE", 960, 150, font="titan", size=96, fill=P_["cream"], ink_w=5.5, shadow=(6, 6), shadow_rgb=P_["violet"], seed=12370,
                   reveal=_ph(t, 2.45, 2.95))
    if t > 3.18:
        paint_text(cv, "EVIL?", 960, 1000, font="titan", size=150, fill=P_["red"], ink_w=7, shadow=(9, 9), shadow_rgb=INK, seed=12371, reveal=_ph(t, 3.18, 3.4))
        scribble_out(cv, 720, 905, 1200, 975, _ph(t, 3.45, 3.7), seed=12372, rgb=INK)
    if t > 3.62:
        k = pop(t, 3.62, 0.3)
        cv.save(); cv.translate(1430, 860); cv.rotate(-12); cv.scale(k, k)
        blob(cv, rect_pts([(-200, -70), (200, -76), (206, 70), (-196, 74)], 3), P_["acid"], w=5, seed=12373, boil=0.8, n=2)
        paint_text(cv, "NOT EVIL", 0, 30, font="bangers", size=90, fill=INK, ink_w=0, shadow=None, seed=12374, streaks=False)
        cv.restore()


def _w_shadow(cv, t, T):
    """What we see vs. what's real: a terrifying monster shadow on the firelit wall... cast by one tiny critter going 'rawr'."""
    pan = 1150 * ease(_ph(t, 5.3, 6.05))
    zf = 1.0 + 0.04 * (t - 3.9)
    cv.save(); cv.translate(W / 2, H / 2); cv.scale(zf, zf); cv.translate(-W / 2 - pan, -H / 2)
    cv.drawRect(R(-200, -200, 3400, 1400), paint(CV_ROCK_DK))
    wall_surface(cv, [(-200, -100), (1900, -100), (1980, 500), (1900, 1100), (-200, 1100)], T, seed=12400, cx=1300, cy=600)
    rock_mass(cv, [(1860, -200), (3400, -200), (3400, 120), (2600, 60), (2100, 160), (1960, 500), (1900, -200)], seed=12401, rgb=CV_ROCK, rim=P_["magenta"])
    rock_mass(cv, [(-200, 940), (3400, 900), (3400, 1400), (-200, 1400)], seed=12402, rgb=CV_ROCK2, rim=P_["orange"])
    raise_ = 0.5 + 0.5 * math.sin(t * 5)
    big_shadow(cv, MONSTER, 900, 600 - 10 * raise_, 3.2 + 0.12 * raise_, T, rgb=(70, 10, 40), a=235, seed=12410)
    for k, (mx, my) in enumerate(((2160, 930), (3000, 920), (1980, 960))):
        glow_mushroom(cv, mx, my, 1.0, T, seed=12420 + k)
        crystal(cv, mx + 200, my + 10, 0.9, T, seed=12430 + k)
    cx_, cy_ = 2620, 920                                          # the candle
    firelight(cv, cx_, cy_ - 160, 520, T, a=170, seed=12440)
    blob(cv, rect_pts([(cx_ - 34, cy_ - 150), (cx_ + 34, cy_ - 150), (cx_ + 34, cy_), (cx_ - 34, cy_)], 2), P_["cream"], w=5, seed=12441, boil=0.6, n=2,
         shade=lambda c: c.drawRect(R(cx_ + 10, cy_ - 160, cx_ + 40, cy_ + 4), paint(P_["cream_sh"])))
    old = _ink(0.5)
    cave_fire(cv, cx_, cy_ - 150, 0.32, T, seed=12442, logs=False)
    core.INKMUL = old
    for sd in (-1, 1):                                            # the critter, arms up: RAWR
        tube(cv, [(2330 + sd * 50, 860), (2330 + sd * 80, 800 - 30 * raise_), (2330 + sd * 70, 760 - 50 * raise_)], 18, (120, 60, 170), w=4, seed=12450 + sd, boil=0.7)
        for j in range(3):
            line(cv, [(2330 + sd * 70 + (j - 1) * 10, 760 - 50 * raise_), (2330 + sd * 72 + (j - 1) * 14, 738 - 50 * raise_)], 5, P_["white"], seed=12453 + j + sd * 4,
                 boil=0.4, n=2, taper=(0, 0.6))
    eyefolk(cv, 2330, 935, 0.95, T, seed=12460, look=(-0.8, -0.2), lid=0.0, rgb=(120, 60, 170), iris=P_["acid"], mouth=0.6 + 0.4 * raise_, pupil=1.3)
    cv.restore()
    if t > 5.12:
        k = pop(t, 5.12, 0.3)
        cv.save(); cv.translate(380 - pan * 0.25, 170); cv.rotate(-5); cv.scale(k, k)
        gloss_panel(cv, -270, -70, 270, 60, [P_["night"], P_["vdark"], P_["night"]], seed=12470, r=22)
        paint_text(cv, "WHAT WE SEE", 0, 22, font="bangers", size=84, fill=P_["yellow"], ink_w=4, shadow=(4, 4), seed=12471, streaks=False)
        cv.restore()
    if t > 5.85:
        callout(cv, "THE ACTUAL MONSTER", 1380, 240, (1195, 690), t, 5.85, seed=12472, size=70, col=P_["teal"])


def _w_cylinder(cv, t, T):
    """isn't always what's real: one cylinder, two shadows - a SQUARE on the wall, a CIRCLE on the floor."""
    zf = 1.0 + 0.04 * (t - 6.2)
    cv.save(); cv.translate(W / 2, H / 2); cv.scale(zf, zf); cv.translate(-W / 2, -H / 2)
    cv.drawRect(R(-60, -60, W + 60, H + 60), paint(P_["void"]))
    w.stars(cv, 12500, (-60, -60, W + 60, H + 60), n=200, big=8)
    wall = [(330, 60), (1590, 60), (1590, 660), (330, 660)]
    blob(cv, rect_pts(wall, 3), P_["teal"], w=6, seed=12501, boil=0.9, n=2,
         shade=lambda c: (c.drawCircle(960, 380, 520, _rad2(960, 380, 520, P_["white"], 160)),
                          stipple(c, P_["tealdk"], (330, 60, 1590, 660), spacing=16, r=2.0, seed=12502, fn=lambda X, Y: np.clip(np.hypot(X - 960, Y - 380) / 700, 0, 1))))
    floor = [(330, 660), (1590, 660), (1860, 1040), (60, 1040)]
    blob(cv, rect_pts(floor, 3), P_["magenta"], w=6, seed=12503, boil=0.9, n=2,
         shade=lambda c: (c.drawCircle(960, 860, 460, _rad2(960, 860, 460, P_["white"], 120)),
                          [c.drawLine(330 + k * 126, 660, 60 + k * 180, 1040, paint(mix(P_["magenta"], INK, 0.3), stroke=3)) for k in range(11)]))
    big_shadow(cv, rect_pts([(-1, -1), (1, -1), (1, 1), (-1, 1)], 6), 960, 350, 130, T, rgb=(10, 60, 70), a=220, seed=12504, blur=1)
    big_shadow(cv, [(math.cos(a), 0.4 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 16, endpoint=False)], 960, 880, 150, T, rgb=(110, 10, 70), a=220,
               seed=12505, blur=1)
    bob = 8 * math.sin(t * 2.4)
    cx_, top, bot, rr = 960, 380 + bob, 640 + bob, 120
    body = [(cx_ - rr, top), (cx_ + rr, top), (cx_ + rr, bot), (cx_ + rr * 0.7, bot + 26), (cx_, bot + 34), (cx_ - rr * 0.7, bot + 26), (cx_ - rr, bot)]
    blob(cv, body, P_["orange"], w=6, seed=12506, boil=0.8, n=3,
         shade=lambda c: (c.drawRect(R(cx_ - rr, top, cx_ + rr, bot + 40), _lin(cx_ - rr, 0, cx_ + rr, 0, [P_["red"], P_["yellow"], P_["orange"], P_["red"]], [0, 0.3, 0.6, 1])),
                          c.drawRect(R(cx_ - rr * 0.55, top, cx_ - rr * 0.38, bot + 40), paint(P_["white"], 120))))
    blob(cv, ell(cx_, top, rr, 34, n=14), P_["yellow"], w=5, seed=12507, boil=0.7)
    line(cv, [(960, -60), (960, 120 + bob * 0.3)], 4, seed=12508, boil=0.5, n=2, taper=(0, 0))
    blob(cv, ell(960, 150 + bob * 0.3, 34, 40, n=10), P_["yellow"], w=4, seed=12509, boil=0.6)
    cv.drawCircle(960, 150, 120, _rad2(960, 150, 120, P_["yellow"], 120))
    cv.restore()
    if t > 6.4:
        callout(cv, "SQUARE?", 330, 230, (820, 300), t, 6.4, seed=12510, size=76, col=P_["violet"])
    if t > 6.9:
        callout(cv, "CIRCLE?", 1560, 980, (1130, 900), t, 6.9, seed=12511, size=76, col=P_["violet"], ang=4)
    if t > 7.35:
        k = pop(t, 7.35, 0.35)
        cv.save(); cv.translate(1540, 300); cv.rotate(8); cv.scale(k, k)
        chrome_text(cv, "CYLINDER!", 0, 0, 104, font="titan", seed=12512, grad=GOLDC, side=[P_["maroon"], P_["red"], P_["orange"]], glints=2)
        cv.restore()


GALLERY = [("bunny", "folk"), ("tv", "host"), ("chart", "folk"), ("heart", "zee"), ("ball", "gary"), ("news", "folk"), ("selfie", "wizard"), ("static", "folk"),
           ("money", "mush"), ("bird", "folk"), ("cat", "folk"), ("horse", "zee")]


def _wall_content(cv, kind, x0, y0, x1, y1, T, seed):
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    wd, ht = x1 - x0, y1 - y0
    if kind in ("bunny", "horse", "bird", "fish", "tree"):
        cv.drawRect(R(x0, y0, x1, y1), _rad(cx, y1, ht * 1.2, [P_["yellow"], CV_WALL, CV_WALL2]))
        shadow_shape(cv, kind, cx + 8 * math.sin(T * 2 + seed), cy, wd / 300, T, seed=seed)
    elif kind == "tv":
        cv.drawRect(R(x0, y0, x1, y1), paint((30, 70, 90)))
        tv_static(cv, (x0, y0, x1, y1), seed=seed, density=120)
        for sd in (-1, 1):
            dots(cv, [(cx + sd * wd * 0.15, cy - ht * 0.1)], wd * 0.05, (190, 255, 214))
    elif kind == "chart":
        cv.drawRect(R(x0, y0, x1, y1), paint(P_["night"]))
        pts = [(x0 + wd * u, y1 - ht * (0.2 + 0.6 * (0.5 + 0.5 * math.sin(u * 9 + T * 3 + seed)) * u)) for u in np.linspace(0.05, 0.95, 9)]
        line(cv, pts, 5, P_["acid"], seed=seed, boil=0.6, n=3, taper=(0, 0))
    elif kind == "heart":
        cv.drawRect(R(x0, y0, x1, y1), paint(P_["hotpink"]))
        hs = wd * 0.18 * (1 + 0.1 * math.sin(T * 8))
        hp = [(cx, cy + hs), (cx - hs * 1.3, cy - hs * 0.2), (cx - hs * 0.7, cy - hs * 1.1), (cx, cy - hs * 0.4), (cx + hs * 0.7, cy - hs * 1.1), (cx + hs * 1.3, cy - hs * 0.2)]
        blob(cv, hp, P_["red"], w=3, seed=seed, boil=0.6, n=3)
    elif kind == "ball":
        cv.drawRect(R(x0, y0, x1, y1), paint(P_["acid_dk"]))
        bx = cx + wd * 0.3 * math.sin(T * 3 + seed)
        dots(cv, [(bx, cy - ht * 0.2 * abs(math.sin(T * 6)))], wd * 0.06, P_["white"])
        cv.drawLine(cx, y0, cx, y1, paint(P_["white"], 150, stroke=3))
    elif kind == "news":
        cv.drawRect(R(x0, y0, x1, y1), paint(P_["blue"]))
        cv.drawRect(R(x0, y1 - ht * 0.25, x1, y1), paint(P_["red"]))
        paint_text(cv, "!!", cx, cy + ht * 0.08, font="bangers", size=ht * 0.45, fill=P_["yellow"], ink_w=2.5, shadow=None, seed=seed, streaks=False)
    elif kind == "selfie":
        cv.drawRect(R(x0, y0, x1, y1), paint(P_["lilac"]))
        blob(cv, ell(cx, cy, wd * 0.18, wd * 0.18, n=10), P_["peach"], w=2.5, seed=seed, boil=0.6)
        sparkle(cv, cx + wd * 0.25, cy - ht * 0.25, wd * 0.06, P_["white"], w=1.5, seed=seed + 1)
    elif kind == "money":
        cv.drawRect(R(x0, y0, x1, y1), paint((40, 120, 60)))
        paint_text(cv, "$$$", cx, cy + ht * 0.12, font="bangers", size=ht * 0.4, fill=P_["acid"], ink_w=2.5, shadow=None, seed=seed, streaks=False)
    elif kind == "cat":
        cv.drawRect(R(x0, y0, x1, y1), paint(P_["orange"]))
        blob(cv, [(cx - wd * 0.2, cy + ht * 0.25), (cx - wd * 0.2, cy - ht * 0.1), (cx - wd * 0.12, cy - ht * 0.3), (cx - wd * 0.04, cy - ht * 0.12),
                  (cx + wd * 0.04, cy - ht * 0.12), (cx + wd * 0.12, cy - ht * 0.3), (cx + wd * 0.2, cy - ht * 0.1), (cx + wd * 0.2, cy + ht * 0.25)], INK, w=0,
             seed=seed, boil=0.6, n=3, misreg=(0, 0))
    else:
        cv.drawRect(R(x0, y0, x1, y1), paint(P_["night"]))
        tv_static(cv, (x0, y0, x1, y1), seed=seed, density=160)


def _viewer_back(cv, kind, x, y, s, T, seed):
    """A watcher seen from behind (silhouette with rim light): folk dome, the host's TV head, Zee, Gary, a wizard, a mushroom."""
    rim = P_["yellow"]
    dk = (24, 10, 40)
    bob = 2 * math.sin(T * 1.7 + seed) * s
    if kind == "host":
        line(cv, [(x, y), (x, y - 70 * s)], 12 * s, INK, seed=seed, boil=0.5, n=2, taper=(0, 0))
        blob(cv, [(x - 70 * s, y + 10), (x - 60 * s, y - 40 * s), (x + 60 * s, y - 40 * s), (x + 70 * s, y + 10)], P_["magenta"], w=3.5, seed=seed + 1, boil=0.6, n=3)
        blob(cv, rect_pts([(x - 64 * s, y - 150 * s + bob), (x + 64 * s, y - 150 * s + bob), (x + 64 * s, y - 64 * s + bob), (x - 64 * s, y - 64 * s + bob)], 2), P_["tealdk"],
             w=3.5, seed=seed + 2, boil=0.6, n=2)
        for sd in (-1, 1):
            line(cv, [(x + sd * 8 * s, y - 150 * s + bob), (x + sd * 50 * s, y - 210 * s + bob)], 3, (200, 200, 220), seed=seed + 3 + sd, boil=0.5, n=2, taper=(0, 0))
    elif kind == "zee":
        blob(cv, [(x - 60 * s, y + 10), (x - 50 * s, y - 40 * s), (x + 50 * s, y - 40 * s), (x + 60 * s, y + 10)], P_["cream"], w=3.5, seed=seed + 1, boil=0.6, n=3)
        for sd in (-1, 1):
            line(cv, [(x + sd * 30 * s, y - 120 * s + bob), (x + sd * 56 * s, y - 175 * s + bob)], 3, seed=seed + 3 + sd, boil=0.5, n=2, taper=(0, 0))
            dots(cv, [(x + sd * 56 * s, y - 178 * s + bob)], 8 * s, P_["yellow"])
        blob(cv, ell(x, y - 85 * s + bob, 58 * s, 60 * s, n=10), P_["violet"], w=3.5, seed=seed + 2, boil=0.6,
             shade=lambda c: c.drawRect(R(x - 70 * s, y - 160 * s, x + 70 * s, y - 110 * s + bob), paint(P_["magenta"])))
    elif kind == "gary":
        blob(cv, [(x - 70 * s, y + 10), (x - 60 * s, y - 40 * s), (x + 60 * s, y - 40 * s), (x + 70 * s, y + 10)], P_["cream"], w=3.5, seed=seed + 1, boil=0.6, n=3,
             shade=lambda c: c.drawRect(R(x - 80 * s, y - 20 * s, x + 80 * s, y - 8 * s), paint(P_["orange"])))
        blob(cv, ell(x, y - 95 * s + bob, 72 * s, 72 * s, n=12), P_["white"], w=3.5, seed=seed + 2, boil=0.7,
             shade=lambda c: [c.drawLine(x + 72 * s * math.cos(a), y - 95 * s + 72 * s * math.sin(a), x + 40 * s * math.cos(a + 0.3), y - 95 * s + 40 * s * math.sin(a + 0.3),
                                         paint(P_["red"], stroke=2)) for a in (0.5, 1.7, 2.9, 4.2, 5.4)])
    elif kind == "wizard":
        blob(cv, [(x - 60 * s, y + 10), (x - 40 * s, y - 80 * s), (x + 40 * s, y - 80 * s), (x + 60 * s, y + 10)], P_["blue"], w=3.5, seed=seed + 1, boil=0.6, n=3)
        blob(cv, [(x - 50 * s, y - 70 * s), (x + 50 * s, y - 70 * s), (x + 10 * s, y - 190 * s + bob)], P_["blue"], w=3.5, seed=seed + 2, boil=0.6, n=3)
    elif kind == "mush":
        blob(cv, [(x - 26 * s, y + 10), (x - 20 * s, y - 60 * s), (x + 20 * s, y - 60 * s), (x + 26 * s, y + 10)], P_["cream"], w=3.5, seed=seed + 1, boil=0.6, n=3)
        blob(cv, [(x - 80 * s, y - 50 * s), (x - 60 * s, y - 110 * s + bob), (x, y - 130 * s + bob), (x + 60 * s, y - 110 * s + bob), (x + 80 * s, y - 50 * s)], P_["red"],
             w=3.5, seed=seed + 2, boil=0.6, n=4)
    else:
        r = 62 * s
        blob(cv, [(x - r * 1.05, y + 10), (x - r * 1.1, y - r * 1.1 + bob), (x - r * 0.7, y - r * 2.0 + bob), (x, y - r * 2.15 + bob), (x + r * 0.7, y - r * 2.0 + bob),
                  (x + r * 1.1, y - r * 1.1 + bob), (x + r * 1.05, y + 10)], dk, w=3.5, seed=seed, boil=0.8, n=4)
    line(cv, [(x - 40 * s, y - 150 * s), (x, y - 160 * s), (x + 40 * s, y - 150 * s)], 2.5, rim, seed=seed + 9, boil=0.5, n=3, a=120)


def mini_cave(cv, x, y, wd, ht, T, kind, viewer, seed=12600):
    """One little personal cave: a rock arch, its own glowing wall, and its watcher seen from behind."""
    x0, y0, x1, y1 = x - wd / 2, y - ht / 2, x + wd / 2, y + ht / 2
    blob(cv, [(x0, y1), (x0 - wd * 0.04, y0 + ht * 0.3), (x0 + wd * 0.18, y0 - ht * 0.02), (x, y0 - ht * 0.08), (x1 - wd * 0.18, y0 - ht * 0.02), (x1 + wd * 0.04, y0 + ht * 0.3),
              (x1, y1)], CV_ROCK, w=4.5, seed=seed, boil=0.8, n=4,
         shade=lambda c: c.drawRect(R(x1 - wd * 0.2, y0 - ht * 0.2, x1 + wd * 0.1, y1), paint(P_["magenta"], 70)))
    ix0, iy0, ix1, iy1 = x0 + wd * 0.12, y0 + ht * 0.1, x1 - wd * 0.12, y1 - ht * 0.08
    arch = rrect_path(ix0, iy0, ix1, iy1, wd * 0.25)
    cv.save(); cv.clipPath(arch, doAntiAlias=True)
    cv.drawRect(R(ix0, iy0, ix1, iy1), paint(CV_ROCK_DK))
    _wall_content(cv, kind, ix0 + wd * 0.06, iy0 + ht * 0.06, ix1 - wd * 0.06, iy0 + ht * 0.56, T, seed + 5)
    cv.drawRect(R(ix0, iy0 + ht * 0.62, ix1, iy1), paint(CV_ROCK2))
    _viewer_back(cv, viewer, x, iy1 + 4, ht / 330, T, seed + 20)
    cv.restore()
    brush(cv, cr_closed(rrect_pts(ix0, iy0, ix1, iy1, wd * 0.25, n=3), 3), 4.0, closed=True, seed=seed + 30)
    crystal(cv, x0 + wd * 0.08, y1, ht / 500, T, seed=seed + 40)


def _w_gallery(cv, t, T):
    """Everybody's watching some kind of wall: a honeycomb of personal caves, the camera pulling back to show it never ends."""
    u = ease(_ph(t, 8.35, 10.6))
    z = math.exp(lerp(math.log(2.5), math.log(0.62), u))
    sets.cosmos(cv, T, dict(x=0, y=0, z=1.0 + 0.1 * (1 - u)), "deep", seed=12700, planet_xy=(1700, 160), extras=False)
    cv.drawRect(R(0, 0, W, H), paint(P_["void"], 120))
    cv.save(); cv.translate(W / 2, H / 2); cv.scale(z, z); cv.translate(-W / 2, -H / 2 + 20)
    old = _ink(z)
    cw, ch = 380, 330
    for j in range(-3, 4):
        for i in range(-4, 5):
            x = 960 + i * cw + (cw / 2 if j % 2 else 0)
            y = 540 + j * ch
            sx = W / 2 + (x - W / 2) * z
            sy = H / 2 + (y - H / 2 + 20) * z
            if sx < -cw * z or sx > W + cw * z or sy < -ch * z or sy > H + ch * z:
                continue
            kind, viewer = GALLERY[(i * 5 + j * 7 + 40) % len(GALLERY)]
            if i == 0 and j == 0:
                kind, viewer = "bunny", "gary"
            mini_cave(cv, x, y, cw - 30, ch - 30, T, kind, viewer, seed=12800 + (i + 10) * 37 + (j + 10) * 11)
    core.INKMUL = old
    cv.restore()
    if t > 8.5:
        paint_text(cv, "EVERYBODY'S GOT A WALL", 960, 1010, font="titan", size=84, fills=[P_["yellow"], P_["cream"]], ink_w=5.5, shadow=(7, 7), shadow_rgb=P_["violet"],
                   seed=12900, reveal=_ph(t, 8.5, 9.2), stagger=0.02)


def stone_sign(cv, text, x, y, s, t, t0, seed=13000, col=None):
    """A chiselled stone slab label hanging on two little chains, popping in at t0."""
    k = pop(t, t0, 0.35)
    if k <= 0:
        return
    tw = measure(text, "titan", 80) + 90
    cv.save(); cv.translate(x, y); cv.rotate(3 * math.sin(t * 2 + seed)); cv.scale(k * s, k * s)
    for sd in (-1, 1):
        chain(cv, (sd * tw * 0.35, -220), (sd * tw * 0.35, -60), seed=seed + sd, link=16, sag=4, w=2.6)
    blob(cv, [(-tw / 2, -66), (tw / 2, -72), (tw / 2 + 14, 0), (tw / 2, 62), (-tw / 2 - 6, 66), (-tw / 2 - 16, 0)], col or (150, 130, 190), w=6, seed=seed + 3, boil=0.9,
         n=2, shade=lambda c: (stipple(c, (110, 90, 150), (-tw / 2 - 20, -80, tw / 2 + 20, 80), spacing=12, r=1.8, seed=seed + 4),
                               c.drawRect(R(-tw / 2 - 20, 30, tw / 2 + 20, 80), paint((110, 90, 150), 150))))
    paint_text(cv, text, 0, 28, font="titan", size=80, fill=P_["cream"], ink_w=4.5, shadow=(-3, -3), shadow_rgb=(90, 70, 130), seed=seed + 5)
    cv.restore()


def _cave_frame(cv, T, seed=13100, inner=None):
    """A ring of psychedelic violet rock around the frame edges with glowing crystals and mushrooms (a cave mouth vignette)."""
    rock_mass(cv, [(-200, -200), (2120, -200), (2120, 140), (1500, 60), (960, 40), (420, 70), (-200, 160)], seed=seed, rgb=CV_ROCK, rim=P_["magenta"])
    rock_mass(cv, [(-200, -100), (180, -100), (120, 400), (170, 800), (60, 1300), (-200, 1300)], seed=seed + 1, rgb=CV_ROCK2, rim=P_["orange"], rim_side=1)
    rock_mass(cv, [(2120, -100), (1750, -100), (1810, 420), (1760, 820), (1860, 1300), (2120, 1300)], seed=seed + 2, rgb=CV_ROCK2, rim=P_["teal"], rim_side=-1)
    for k, (cx_, cy_) in enumerate(((150, 1000), (1780, 1010), (300, 1040))):
        crystal(cv, cx_, cy_, 1.0, T, seed=seed + 10 + k)
    glow_mushroom(cv, 1660, 1040, 1.1, T, seed=seed + 20)


def _w_habits(cv, t, T):
    """Our habits: a hamster-wheel cave. Round and round, forever, staring at the same looping shadow."""
    lt = t - 10.86
    zf = 1.05 + 0.03 * lt
    cv.save(); cv.translate(W / 2, H / 2); cv.scale(zf, zf); cv.translate(-W / 2, -H / 2)
    cv.drawRect(R(-60, -60, W + 60, H + 60), paint(CV_ROCK_DK))
    wall_surface(cv, [(160, 60), (1760, 60), (1760, 980), (160, 980)], T, seed=13200, cx=960, cy=700)
    hop = abs(math.sin(lt * 4 * math.pi))
    shadow_shape(cv, "bunny", 430, 430 - 120 * hop, 1.5, T, seed=13201)
    shadow_shape(cv, "bunny", 1490, 430 - 120 * hop, 1.5, T, seed=13202)
    paint_text(cv, "AGAIN", 430, 660, font="bangers", size=64, fill=CV_SHADOW, ink_w=0, shadow=None, seed=13203, streaks=False, a=190)
    paint_text(cv, "AND AGAIN", 1490, 660, font="bangers", size=64, fill=CV_SHADOW, ink_w=0, shadow=None, seed=13204, streaks=False, a=190)
    _cave_frame(cv, T, seed=13210)
    cx_, cy_, rr = 960, 590, 360
    for sd in (-1, 1):
        line(cv, [(cx_, cy_), (cx_ + sd * 250, 1080)], 30, INK, seed=13220 + sd, boil=0.6, n=2, taper=(0, 0))
        line(cv, [(cx_, cy_), (cx_ + sd * 250, 1080)], 20, (150, 110, 200), seed=13220 + sd, boil=0.6, n=2, taper=(0, 0))
    spin = lt * 520
    for k in range(10):
        a_ = math.radians(spin + k * 36)
        line(cv, [(cx_, cy_), (cx_ + rr * math.cos(a_), cy_ + rr * math.sin(a_))], 7, (200, 200, 220), seed=13230 + k, boil=0.4, n=2, taper=(0, 0))
    for r_, wdt, col in ((rr, 34, P_["acid"]), (rr - 30, 12, P_["teal"])):
        pp = cr_closed(jit(ell(cx_, cy_, r_, r_, n=24), 1.2, 13240 + r_), 3)
        brush(cv, pp, wdt + 10, INK, closed=True, seed=13241 + r_)
        brush(cv, pp, wdt, col, closed=True, seed=13241 + r_)
    for k in range(18):                                           # rungs
        a_ = math.radians(spin + k * 20)
        p0 = (cx_ + (rr - 30) * math.cos(a_), cy_ + (rr - 30) * math.sin(a_))
        p1 = (cx_ + rr * math.cos(a_), cy_ + rr * math.sin(a_))
        cv.drawLine(p0[0], p0[1], p1[0], p1[1], paint(INK, stroke=6))
    blob(cv, ell(cx_, cy_, 34, 34, n=8), P_["gold"], w=5, seed=13250, boil=0.5)
    run = lt * 14
    fx, fy = cx_, cy_ + rr - 34
    bob_ = 8 * abs(math.sin(run))
    eyefolk(cv, fx, fy - 46 - bob_, 1.4, T, seed=13270, look=(0.0, -0.1), lid=0.45, rgb=(110, 50, 160), iris=P_["orange"], sweat=1.0, pupil=0.8)
    for sd in (-1, 1):                                            # little running legs
        ph = run + (0 if sd < 0 else math.pi)
        foot = (fx + sd * 26 + 44 * math.sin(ph), fy - 4 - 22 * max(0.0, math.cos(ph)))
        tube(cv, [(fx + sd * 30, fy - 52 - bob_), ((fx + sd * 30 + foot[0]) / 2 + 8, fy - 28), foot], 16, (110, 50, 160), w=4, seed=13260 + sd, boil=0.7, n=4)
        blob(cv, ell(foot[0] + 8, foot[1], 22, 12, n=8), P_["acid"], w=3.5, seed=13262 + sd, boil=0.5)
    for j in range(4):
        line(cv, [(fx - 260 - j * 20, fy - 60 - j * 34), (fx - 170 - j * 20, fy - 60 - j * 34)], 6, P_["white"], seed=13280 + j, boil=0.8, n=2, taper=(0.2, 0.6), a=180)
    cv.restore()
    stone_sign(cv, "HABITS", 960, 200, 1.0, t, 10.95, seed=13290)
    paint_text(cv, "LAP " + f"{9990 + int(lt * 9):,}", 1700, 1000, font="londrina", size=56, fill=P_["acid"], ink_w=3, shadow=(4, 4), seed=13295, align="right",
               streaks=False)


def _w_feeds(cv, t, T):
    """Our feeds: a cave wall that never stops scrolling - up and up out of frame."""
    lt = t - 12.0
    zf = 1.05 + 0.04 * lt
    cv.save(); cv.translate(W / 2, H / 2); cv.scale(zf, zf); cv.translate(-W / 2, -H / 2)
    cv.drawRect(R(-60, -60, W + 60, H + 60), paint(CV_ROCK_DK))
    firelight(cv, 960, 900, 1100, T, a=110)
    x0, x1 = 560, 1360
    feed_screen(cv, (x0, -80, 952, 900), T, 900 * lt + 300, seed=13300, blur=0.2)
    feed_screen(cv, (968, -80, x1, 900), T, 900 * lt + 520, seed=13360, blur=0.2)
    cv.drawRect(R(952, -80, 968, 900), paint(CV_ROCK_DK))
    for k in range(int((900 + 80) / 40)):
        cv.drawRect(R(x0, -80 + k * 40, x1, -80 + k * 40 + 3), paint(INK, 30))
    brush(cv, np.array([(x0, -80), (x0, 900)]), 6, seed=13301, taper=(0, 0))
    brush(cv, np.array([(x1, -80), (x1, 900)]), 6, seed=13302, taper=(0, 0))
    for k in range(5):                                            # arrows: up, up, up
        yy = 900 - ((lt * 900 + k * 220) % 1100)
        for xx in (x0 - 90, x1 + 90):
            blob(cv, [(xx, yy - 40), (xx + 34, yy + 10), (xx - 34, yy + 10)], P_["acid"], w=4, seed=13310 + k + int(xx), boil=0.6, n=2, a=200)
    _cave_frame(cv, T, seed=13320)
    rock_mass(cv, [(-200, 900), (2120, 880), (2120, 1300), (-200, 1300)], seed=13330, rgb=CV_ROCK2, rim=P_["orange"])
    eyefolk(cv, 1500, 1010, 1.6, T, seed=13340, look=(-0.7, -1.0), lid=0.15, rgb=(90, 40, 150), iris=P_["teal"], glow=P_["orange"], pupil=1.25, mouth=0.35)
    eyefolk(cv, 420, 1020, 1.3, T, seed=13341, look=(0.6, -1.0), lid=0.2, rgb=(120, 60, 160), iris=P_["hotpink"], glow=P_["orange"], pupil=1.25, bow=P_["acid"])
    cv.restore()
    stone_sign(cv, "FEEDS", 330, 230, 0.9, t, 12.1, seed=13350)


ASSUME = ["OBVIOUSLY", "EVERYONE KNOWS", "ALWAYS BEEN THIS WAY", "COMMON SENSE", "BECAUSE", "DUH", "TRUST ME", "IT'S FINE", "THAT'S JUST HOW IT IS",
          "OBVIOUSLY", "SAYS SO HERE", "EVERYONE KNOWS", "NO NEED TO ASK", "ALWAYS BEEN THIS WAY"]


def _w_bricks(cv, t, T):
    """Our assumptions -> believed for so long -> never thought to check. One brick wall: lettered bricks thunk into place,
    ivy and years grow over it (and over its watcher), then we push in on a dusty, cobwebbed, never-ticked CHECK? box."""
    age = ease(_ph(t, 14.95, 17.4))
    push = ease(_ph(t, 17.55, 18.6))
    plaque = (1480, 300)
    z = lerp(1.0 - 0.06 * age, 3.4 + 0.12 * _ph(t, 18.6, 19.65), push)
    fx_, fy_ = lerp(960, plaque[0], push), lerp(540, plaque[1], push)
    cv.save(); cv.translate(W / 2, H / 2); cv.scale(z, z); cv.translate(-fx_, -fy_)
    old = _ink(z)
    cv.drawRect(R(-400, -400, W + 400, H + 400), paint(CV_ROCK_DK))
    firelight(cv, 960, 700, 1200, T, a=120)
    bh, bw = 92, 300
    rows = 9
    hero = {(5, 1): ("EVERYONE KNOWS", 13.45), (4, 3): ("OBVIOUSLY", 13.7), (3, 3): ("ALWAYS BEEN THIS WAY", 13.95)}
    small = ["BECAUSE", "DUH", "TRUST ME", "IT'S FINE", "SAYS SO HERE", "NO NEED TO ASK", "COMMON SENSE", "OBVIOUSLY"]
    for r in range(rows):                                         # the wall; lettered bricks thunk into place
        y = 860 - (r + 1) * bh
        off = 0 if r % 2 == 0 else bw / 2
        c = -2
        while c < 9:
            hb = hero.get((r, c))
            nc = 2 if hb else 1
            x = -260 + c * bw + off
            wdt = bw * nc
            lettered = hb is not None or ((r * 3 + c * 5) % 4 == 0 and 0 <= c <= 7 and 1 <= r <= 7)
            if hb:
                txt, t_in = hb
            else:
                txt = small[(r * 7 + c * 3) % len(small)]
                t_in = 13.3 + 0.07 * ((r * 5 + c * 3) % 15)
            k = pop(t, t_in, 0.25) if lettered else 1.0
            if k > 0:
                col = (255, 214, 120) if hb else [(230, 120, 90), (240, 150, 100), (210, 100, 90), (250, 170, 120)][(r + c * 3) % 4]
                col = mix(col, (120, 120, 110), 0.35 * age)
                cv.save(); cv.translate(x + wdt / 2, y + bh / 2); cv.scale(k, k)
                blob(cv, rect_pts([(-wdt / 2 + 5, -bh / 2 + 5), (wdt / 2 - 5, -bh / 2 + 5), (wdt / 2 - 5, bh / 2 - 5), (-wdt / 2 + 5, bh / 2 - 5)], 2), col, w=4,
                     seed=13400 + r * 31 + c, boil=0.6, n=2, shade=lambda q, col=col, wdt=wdt: q.drawRect(R(-wdt / 2, bh * 0.15, wdt / 2, bh / 2), paint(mix(col, INK, 0.2))))
                if lettered:
                    base = 62 if hb else 40
                    sz = min(float(base), (wdt - 44) / max(1.0, measure(txt, "bangers", base)) * base)
                    paint_text(cv, txt, 0, sz * 0.36, font="bangers", size=sz, fill=INK if hb else P_["cream"], ink_w=0 if hb else 2.5, shadow=None if hb else (2, 2),
                               seed=13500 + r * 13 + c, streaks=False, wobble=0.6)
                cv.restore()
            c += nc
    cv.drawRect(R(-400, 860, W + 400, H + 400), paint(mix(CV_ROCK2, (110, 110, 100), 0.3 * age)))
    brush(cv, np.array([(-400, 860), (W + 400, 862)]), 5, taper=(0.02, 0.02), seed=13401)
    if age > 0:                                                   # ivy + cracks + moss: years pass
        for v in range(5):
            vx = [120, 520, 980, 1350, 1760][v]
            L = age * (0.6 + 0.4 * hsh(13600 + v))
            pts = [(vx + 40 * math.sin(j * 0.9 + v), 860 - j * 70) for j in range(int(2 + 10 * L))]
            if len(pts) >= 2:
                line(cv, pts, 9, P_["acid_dk"], seed=13610 + v, boil=0.7, n=4, taper=(0.0, 0.7))
                for j, (lx, ly) in enumerate(pts[1:]):
                    sd = 1 if j % 2 else -1
                    blob(cv, [(lx, ly), (lx + sd * 34, ly - 14), (lx + sd * 46, ly + 6), (lx + sd * 20, ly + 16)], P_["acid"], w=3, seed=13620 + v * 20 + j, boil=0.5, n=2)
        for k in range(int(6 * age)):
            cx_, cy_ = 200 + 280 * k, 200 + 90 * (k % 3)
            line(cv, [(cx_, cy_), (cx_ + 20, cy_ + 60), (cx_ - 10, cy_ + 120), (cx_ + 14, cy_ + 170)], 3.5, INK, seed=13650 + k, boil=0.5, n=4, taper=(0.1, 0.5))
        for k in range(3):                                        # cobwebs in the corners
            if age > 0.3 + 0.2 * k:
                cx_, cy_ = [(-200, 0), (2120, 0), (1480 + 160, 300 - 120)][k]
                for j in range(5):
                    a_ = math.radians(10 + j * 20) if k == 0 else math.radians(170 - j * 20) if k == 1 else math.radians(100 + j * 20)
                    cv.drawLine(cx_, cy_, cx_ + 320 * math.cos(a_), cy_ + 320 * math.sin(a_), paint(P_["white"], 150, stroke=2.5))
                for j in range(1, 4):
                    pts = [(cx_ + 90 * j * math.cos(math.radians(a2)), cy_ + 90 * j * math.sin(math.radians(a2))) for a2 in
                           (np.linspace(10, 90, 6) if k == 0 else np.linspace(90, 170, 6) if k == 1 else np.linspace(100, 180, 6))]
                    brush(cv, np.array(pts), 2.2, P_["white"], taper=(0.1, 0.1), seed=13660 + k * 5 + j, a=150)
    # the plaque: a form with a single box, never ticked
    px, py = plaque
    blob(cv, rect_pts([(px - 150, py - 110), (px + 150, py - 110), (px + 150, py + 110), (px - 150, py + 110)], 3), (120, 80, 50), w=5, seed=13700, boil=0.6, n=2)
    blob(cv, rect_pts([(px - 124, py - 86), (px + 124, py - 86), (px + 124, py + 86), (px - 124, py + 86)], 3), mix(P_["cream"], (170, 160, 140), 0.25 + 0.4 * age), w=3.5,
         seed=13701, boil=0.5, n=2, shade=lambda q: stipple(q, (150, 140, 120), (px - 130, py - 90, px + 130, py + 90), spacing=7, r=1.0, seed=13702, a=int(255 * min(1, age + push))))
    blob(cv, rect_pts([(px - 96, py - 40), (px - 26, py - 40), (px - 26, py + 30), (px - 96, py + 30)], 2), P_["white"], w=4, seed=13703, boil=0.5, n=2)
    paint_text(cv, "CHECK?", px + 50, py + 14, font="londrina", size=46, fill=INK, ink_w=0, shadow=None, seed=13704, streaks=False, wobble=0.6)
    for j in range(5):                                            # cobweb across the box
        a_ = math.radians(200 + j * 25)
        cv.drawLine(px - 96, py - 40, px - 96 + 110 * math.cos(a_ + math.pi), py - 40 + 110 * math.sin(a_ + math.pi), paint(P_["white"], int(120 + 100 * push), stroke=1.6))
    for j in range(1, 3):
        pts = [(px - 96 + 30 * j * math.cos(math.radians(a2)), py - 40 + 30 * j * math.sin(math.radians(a2))) for a2 in np.linspace(5, 85, 5)]
        brush(cv, np.array(pts), 1.4, P_["white"], taper=(0.1, 0.1), seed=13705 + j, a=int(140 + 100 * push))
    sy_ = py - 110 + 60 + 26 * math.sin(t * 1.7)                  # the spider on its thread
    cv.drawLine(px + 110, py - 200, px + 110, sy_, paint(P_["white"], 200, stroke=1.4))
    blob(cv, ell(px + 110, sy_ + 8, 9, 8, n=8), INK, w=0, seed=13706, boil=0.4, misreg=(0, 0))
    for sd in (-1, 1):
        for j in range(3):
            cv.drawLine(px + 110, sy_ + 8, px + 110 + sd * 14, sy_ + 2 + j * 6, paint(INK, stroke=1.6))
    line(cv, [(px + 170, py - 60), (px + 186, py + 60)], 3, (90, 80, 60), seed=13707, boil=0.3, n=2, taper=(0, 0))       # the pencil on a string, unused
    blob(cv, rot(rect_pts([(px + 176, py + 54), (px + 192, py + 54), (px + 192, py + 150), (px + 176, py + 150)], 2), -6, px + 184, py + 100), P_["yellow"], w=2.5,
         seed=13708, boil=0.4, n=2)
    # the watcher: sits facing the wall (3/4), grows old with it
    beard = age
    wx_, wy_ = 700, 990
    eyefolk(cv, wx_, wy_, 1.7, T, seed=13710, look=(0.15, 0.1), lid=0.5 + 0.1 * age, rgb=mix((110, 50, 160), (150, 140, 160), 0.4 * age), iris=P_["teal"],
            tilt=-7, smile=1.0 * (1 - beard), nod=0.2 * abs(math.sin(t * 3)) * (1 - age))
    if beard > 0.02:
        r_ = 70 * 1.7
        cy_ = wy_ - r_ * 1.15
        bl = 40 + 260 * beard
        cy_ += r_ * 0.08
        blob(cv, [(wx_ - r_ * 0.5, cy_ + r_ * 0.25), (wx_ + r_ * 0.5, cy_ + r_ * 0.25), (wx_ + r_ * 0.4, cy_ + r_ * 0.25 + bl * 0.6), (wx_ + 10, cy_ + r_ * 0.25 + bl),
                  (wx_ - 20, cy_ + r_ * 0.25 + bl * 0.8), (wx_ - r_ * 0.45, cy_ + r_ * 0.25 + bl * 0.5)], P_["white"], w=4, seed=13720, boil=0.8, n=4,
             shade=lambda q: [q.drawLine(wx_ - 30 + j * 15, cy_ + r_ * 0.3, wx_ - 20 + j * 12, cy_ + r_ * 0.25 + bl * 0.8, paint((210, 210, 225), stroke=2.5)) for j in range(5)])
    if age > 0.5:
        line(cv, [(wx_ + 150, wy_), (wx_ + 140, wy_ - 230)], 9, (150, 100, 60), seed=13725, boil=0.4, n=2, taper=(0, 0))
        line(cv, [(wx_ + 140, wy_ - 230), (wx_ + 110, wy_ - 260), (wx_ + 90, wy_ - 230)], 9, (150, 100, 60), seed=13726, boil=0.4, n=3, taper=(0, 0))
    if push > 0.3:                                                # dust motes drifting in the light
        for k in range(12):
            mx = px - 200 + (hsh(13800 + k) * 420 + t * 12 * (hsh(13810 + k) - 0.5)) % 420
            my = py - 160 + (hsh(13820 + k) * 330 + t * 8) % 330
            dots(cv, [(mx, my)], 1.6 + 1.2 * hsh(13830 + k), P_["cream"], a=int(200 * push))
    core.INKMUL = old
    cv.restore()
    if push > 0.2:
        cv.drawPath(poly_path([(1200, -60), (1500, -60), (1200, 1140), (700, 1140)]), paint(P_["cream"], int(30 * push)))
    if t < 14.95 + 0.4:
        stone_sign(cv, "ASSUMPTIONS", 760, 150, 0.85, t, 13.35, seed=13900)
    if 15.0 < t < 17.6:
        k = pop(t, 15.1, 0.4) * (1 - ease(_ph(t, 17.3, 17.6)))
        if k > 0.01:
            cv.save(); cv.translate(1540, 860); cv.rotate(-6); cv.scale(k, k)
            blob(cv, rect_pts([(-190, -80), (190, -86), (196, 80), (-186, 84)], 3), P_["cream"], w=5, seed=13910, boil=0.8, n=2,
                 shade=lambda q: q.drawRect(R(-200, -90, 200, -30), paint(P_["red"])))
            paint_text(cv, "YEAR", 0, -42, font="londrina", size=40, fill=P_["white"], ink_w=0, shadow=None, seed=13911, streaks=False)
            paint_text(cv, f"{1 + int(age * 2399):,}", 0, 62, font="titan", size=84, fill=INK, ink_w=0, shadow=None, seed=13912, streaks=False)
            cv.restore()


def T047_every_wall(cv, t, T, A):
    """Z29-Z30: Zee: screens aren't evil (a halo TV), what we see isn't always real (a monster shadow cast by a tiny critter;
    one cylinder, a square and a circle), everybody watches some wall (a honeycomb of personal caves); habits (hamster-wheel
    cave), feeds (a wall that scrolls forever), assumptions (lettered bricks) that age for years... and a CHECK? box nobody ticks."""
    if t < 1.25:
        cam = dict(x=CAM_ZEE["x"], y=CAM_ZEE["y"], z=1.85 + 0.08 * t)
        studio(cv, T, A, cam, t)
        for k in range(6):
            u = (t * 0.5 + k / 6) % 1.0
            sparkle(cv, 1300 + 420 * hsh(13950 + k) - 200, 900 - 700 * u, 10 + 8 * math.sin(t * 5 + k), [P_["mint"], P_["white"], P_["lilac"]][k % 3], seed=13960 + k,
                    a=int(220 * math.sin(u * math.pi)))
    elif t < 4.05:
        _w_angel(cv, t, T)
    elif t < 6.2:
        _w_shadow(cv, t, T)
    elif t < 8.35:
        _w_cylinder(cv, t, T)
    elif t < 10.86:
        _w_gallery(cv, t, T)
    elif t < 12.0:
        _w_habits(cv, t, T)
    elif t < 13.2:
        _w_feeds(cv, t, T)
    else:
        _w_bricks(cv, t, T)
