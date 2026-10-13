"""BOXED ep2 'ONE IN BILLIONS' — shots E01–E22.
Elon Musk's viral 2016 argument (Pong -> photoreal -> billions of worlds -> 'one in billions'), acted out
on the BOXED talk show, with Pong, a graphics-evolution montage, a wall of billions of screens, a fork in
the road, Tyson's coin flip, the twist, and a reveal that the show is the ball in a cosmic game of Pong."""
import json
import math
import os
import numpy as np
import skia
from .core import (PAL, INK, W, H, paint, poly_path, cr_closed, cr_open, ell, blob, line, brush, dots, hsh, mix, jit, rot,
                   stipple, sparkle, rect_pts, tube)
from . import core
from . import world as w
from . import sets
from .letters import paint_text
from .zee import draw_zee
from .cast import draw_host, agent, alien, ai_blob, cosmic_hand
from .shots_a import ease, pop, lerp, Hh, G, CAM_HOST, CAM_ZEE, tag

P_ = PAL
EP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ep2")
_LIPS = None


def loud_at(lid, T):
    global _LIPS
    if _LIPS is None:
        _LIPS = json.load(open(os.path.join(EP, "lipsync.json")))
    L = _LIPS[lid]
    fi = int((T - L["t0"]) * 24)
    return float(L["loud"][fi]) if 0 <= fi < L["n"] else 0.0


def R(x0, y0, x1, y1):
    return skia.Rect.MakeLTRB(float(x0), float(y0), float(x1), float(y1))


# ------------------------------------------------------------------ small helpers
DIG = {"0": ["111", "101", "101", "101", "111"], "1": ["010", "110", "010", "010", "111"], "2": ["111", "001", "111", "100", "111"],
       "3": ["111", "001", "111", "001", "111"], "4": ["101", "101", "111", "001", "001"], "5": ["111", "100", "111", "001", "111"],
       "6": ["111", "100", "111", "101", "111"], "7": ["111", "001", "010", "010", "010"], "8": ["111", "101", "111", "101", "111"],
       "9": ["111", "101", "111", "001", "111"], ":": ["0", "1", "0", "1", "0"], " ": ["0", "0", "0", "0", "0"],
       "P": ["110", "101", "110", "100", "100"], "L": ["100", "100", "100", "100", "111"], "A": ["010", "101", "111", "101", "101"],
       "Y": ["101", "101", "010", "010", "010"], "E": ["111", "100", "110", "100", "111"], "R": ["110", "101", "110", "101", "101"]}


def pixel_text(cv, s, x, y, px, rgb, a=255):
    """Blocky arcade digits (3x5 bitmap), top-left at x,y."""
    for ch in s:
        g = DIG.get(ch, DIG[" "])
        for r, row in enumerate(g):
            for c, bit in enumerate(row):
                if bit == "1":
                    cv.drawRect(R(x + c * px, y + r * px, x + (c + 1) * px - 1, y + (r + 1) * px - 1), paint(rgb, a))
        x += (len(g[0]) + 1) * px


def glow_square(cv, x, y, s, rgb=None, a=255):
    rgb = rgb or P_["white"]
    for k in range(4, 0, -1):
        cv.drawRect(R(x - s / 2 - k * 6, y - s / 2 - k * 6, x + s / 2 + k * 6, y + s / 2 + k * 6), paint(rgb, int(a * 0.07)))
    cv.drawRect(R(x - s / 2, y - s / 2, x + s / 2, y + s / 2), paint(rgb, a))


def social_glyph(cv, kind, x, y, s, seed, rgb):
    if kind == 0:     # play button
        blob(cv, rect_pts([(x - 34 * s, y - 24 * s), (x + 34 * s, y - 24 * s), (x + 34 * s, y + 24 * s), (x - 34 * s, y + 24 * s)], 3), P_["red"], w=4, seed=seed, boil=0.8, n=3)
        blob(cv, [(x - 8 * s, y - 12 * s), (x + 12 * s, y), (x - 8 * s, y + 12 * s)], P_["white"], w=0, seed=seed + 1, boil=0.4, n=2, misreg=(0, 0))
    elif kind == 1:   # heart
        hp = [(x, y + 26 * s), (x - 30 * s, y - 2 * s), (x - 22 * s, y - 22 * s), (x, y - 12 * s), (x + 22 * s, y - 22 * s), (x + 30 * s, y - 2 * s)]
        blob(cv, hp, rgb, w=4, seed=seed, boil=0.8, n=4)
    elif kind == 2:   # share arrow
        line(cv, [(x - 24 * s, y + 18 * s), (x - 10 * s, y - 6 * s), (x + 22 * s, y - 14 * s)], 9 * s + 2, rgb, seed=seed, boil=0.8, n=4, taper=(0, 0))
        blob(cv, [(x + 14 * s, y - 30 * s), (x + 36 * s, y - 14 * s), (x + 14 * s, y + 2 * s)], rgb, w=3.5, seed=seed + 1, boil=0.6, n=2)
    else:             # speech bubble
        blob(cv, ell(x, y, 36 * s, 26 * s, n=9), P_["white"], w=4, seed=seed, boil=0.8)
        dots(cv, [(x - 14 * s, y), (x, y), (x + 14 * s, y)], 4 * s, INK)


def audience_rows(cv, t, raise_k=0.0, hi_x=1180, loud=0.0, seed=2600):
    """Foreground rows of eyeball creatures in the dark; one ('Gary') can stand up with a mic."""
    cols = [P_["night"], (40, 20, 70), (54, 26, 90)]
    for row in range(2):
        y = 1080 + 40 - row * 70
        for k in range(14):
            x = -40 + k * 150 + (75 if row else 0)
            if abs(x - hi_x) < 70 and row == 1:
                continue
            r = 64 - row * 6
            bob = 4 * math.sin(t * 2 + k * 1.3 + row)
            blob(cv, ell(x, y + bob, r, r * 1.05, n=10), cols[(k + row) % 3], w=5, seed=seed + k * 7 + row * 100, boil=1.0)
            look = (hsh(seed + k) - 0.5) * 0.6
            dots(cv, [(x + look * 20, y + bob - 6)], 16, (200, 255, 230) if (k + row) % 2 else (255, 200, 240))
            dots(cv, [(x + look * 20, y + bob - 6)], 7, INK)
    if raise_k > 0:
        y = 1100 - 210 * ease(raise_k)
        eyeball_creature(cv, hi_x, y, 0.62, t, loud, seed=seed + 900, mic=raise_k > 0.6)


def eyeball_creature(cv, x, y, s, t, loud=0.0, seed=0, mic=True, wave=0.0):
    """Gary: a big friendly eyeball in a striped cream sweater, a little mouth under his iris, one hand up,
    the other holding a microphone. Pupil and mouth pulse when he talks."""
    from .zee import _hand
    bob = 6 * math.sin(t * 3.1) * s
    blob(cv, [(x - 128 * s, y + 360 * s), (x - 110 * s, y + 170 * s), (x - 55 * s, y + 112 * s), (x + 55 * s, y + 112 * s), (x + 110 * s, y + 170 * s),
              (x + 128 * s, y + 360 * s)], P_["cream"], w=5, seed=seed, boil=1.0, n=6,
         shade=lambda c: [c.drawRect(R(x - 140 * s, y + (232 + k * 46) * s, x + 140 * s, y + (250 + k * 46) * s), paint(P_["orange"])) for k in range(3)])
    paint_text(cv, "G", x, y + 300 * s, font="shrik", size=76 * s, fill=P_["red"], ink_w=4, shadow=None, seed=seed + 30, streaks=False)
    blob(cv, ell(x, y + bob, 150 * s, 150 * s, n=14), P_["white"], w=6, seed=seed + 4, boil=1.2,
         shade=lambda c: [line(c, [(x + 150 * s * math.cos(a), y + bob + 150 * s * math.sin(a)), (x + 100 * s * math.cos(a + 0.25), y + bob + 100 * s * math.sin(a + 0.25))],
                               3.5, P_["red"], seed=seed + 10 + k, boil=0.8, n=3) for k, a in enumerate(np.linspace(0, 6.0, 8))])
    ir = 66 * s
    ex, ey = x - 4 * s, y + bob - 22 * s
    blob(cv, ell(ex, ey, ir, ir, n=11), P_["teal"], w=4.5, seed=seed + 5, boil=0.8,
         shade=lambda c: c.drawPath(poly_path(cr_closed(ell(ex + 10 * s, ey + 12 * s, ir * 0.8, ir * 0.75, n=8), 4)), paint(P_["tealdk"])))
    pr = ir * (0.42 + 0.22 * min(1.0, loud))
    blob(cv, ell(ex, ey, pr, pr, n=9), INK, w=0, seed=seed + 6, boil=0.5, misreg=(0, 0))
    dots(cv, [(ex - pr * 0.45, ey - pr * 0.5)], pr * 0.28, P_["white"])
    lid = 0.25 + 0.2 * math.sin(t * 0.7)
    blob(cv, [(x - 152 * s, y + bob - 20 * s), (x - 120 * s, y + bob - 110 * s), (x, y + bob - 156 * s), (x + 120 * s, y + bob - 110 * s), (x + 152 * s, y + bob - 20 * s),
              (x, y + bob - 150 * s + 300 * s * lid * 0.35)], P_["violet"], w=5, seed=seed + 7, boil=1.0, n=5)
    mo = min(1.0, loud * 1.5)                                    # mouth on the white, under the iris
    mx, my = x + 6 * s, y + bob + 92 * s
    if mo > 0.08:
        mh = (5 + 30 * mo) * s
        blob(cv, ell(mx, my + mh * 0.3, 34 * s, mh, n=10), P_["mouth"], w=4.5, seed=seed + 40, boil=0.7,
             shade=lambda c: blob(c, ell(mx + 4 * s, my + mh * 1.1, 22 * s, mh * 0.6, n=8), P_["tongue"], w=0, seed=seed + 41, boil=0.5, misreg=(0, 0)))
    else:
        line(cv, [(mx - 30 * s, my - 4 * s), (mx, my + 8 * s), (mx + 30 * s, my - 4 * s)], 4.5, seed=seed + 42, boil=0.6, n=6, taper=(0.3, 0.3))
    sh = (x - 104 * s, y + 190 * s)                              # left arm: raised hand (asking) or hanging
    if wave > 0:
        hx, hy = x - 205 * s + 16 * s * math.sin(t * 8) * wave, y - 40 * s - 60 * s * wave
        el = (x - 200 * s, y + 140 * s)
        ang = -90 + 14 * math.sin(t * 8) * wave
    else:
        hx, hy, el, ang = x - 140 * s, y + 330 * s, (x - 150 * s, y + 250 * s), 100
    tube(cv, [sh, el, (hx, hy)], 22 * s, P_["cream"], w=4.5, seed=seed + 50, boil=0.8, n=8)
    cv.save(); cv.translate(hx, hy); cv.scale(s * 1.15, s * 1.15)
    _hand(cv, 0, 0, ang, "open", 1, seed + 52, rgb=P_["white"])
    cv.restore()
    if mic:                                                      # right arm + mic, held up to the mouth
        mhx, mhy = x + 70 * s, y + bob + 150 * s
        gx, gy = x + 110 * s, y + 232 * s
        line(cv, [(gx + 14 * s, gy + 24 * s), (mhx + 8 * s, mhy + 14 * s)], 14 * s + 3, (60, 60, 80), seed=seed + 60, boil=0.5, n=2, taper=(0, 0))
        blob(cv, ell(mhx, mhy, 22 * s, 24 * s, n=9), (170, 170, 190), w=4, seed=seed + 61, boil=0.6,
             shade=lambda c: [line(c, [(mhx - 24 * s, mhy - 20 * s + k * 9 * s), (mhx + 24 * s, mhy - 20 * s + k * 9 * s)], 1.6, (90, 90, 110), seed=seed + 62 + k,
                                   boil=0.3, n=2, taper=(0, 0)) for k in range(5)])
        tube(cv, [(x + 104 * s, y + 190 * s), (x + 168 * s, y + 250 * s), (gx + 20 * s, gy + 20 * s)], 22 * s, P_["cream"], w=4.5, seed=seed + 64, boil=0.8, n=8)
        cv.save(); cv.translate(gx + 12 * s, gy + 16 * s); cv.scale(s * 1.15, s * 1.15)
        _hand(cv, 0, 0, -130, "fist", 1, seed + 66, rgb=P_["white"])
        cv.restore()


def stage_tv_screen(c, rect, t, seed=2100):
    cx, cy, wd, ht = rect
    x0, y0, x1, y1 = cx - wd / 2 - 20, cy - ht / 2 - 20, cx + wd / 2 + 20, cy + ht / 2 + 20
    c.drawRect(R(x0, y0, x1, y1), paint(P_["maroon"]))
    for k in range(12):
        xx = x0 + k * (x1 - x0) / 12
        c.drawRect(R(xx, y0, xx + 8, y1), paint(P_["red"], 120))
    c.drawPath(poly_path([(cx - 30, y0), (cx + 30, y0), (cx + 110, y1 - 40), (cx - 110, y1 - 40)]), paint(P_["yellow"], 60))
    c.drawRect(R(x0, y1 - 46, x1, y1), paint((120, 70, 40)))
    for side in (-1, 1):
        blob(c, [(cx + side * 70 - 24, y1 - 90), (cx + side * 70 + 24, y1 - 90), (cx + side * 70 + 28, y1 - 46), (cx + side * 70 - 28, y1 - 46)], P_["red"], w=3, seed=seed + side, boil=0.6, n=3)
    line(c, [(cx, y1 - 46), (cx, y1 - 110)], 3, seed=seed + 5, boil=0.4, n=2, taper=(0, 0))
    dots(c, [(cx, y1 - 114)], 6, (170, 170, 190))
    c.drawRect(R(cx - 90, y0 + 12, cx + 90, y0 + 40), paint(P_["night"]))
    paint_text(c, "CODE · 2016", cx, y0 + 36, font="londrina", size=24, fill=P_["cream"], ink_w=0, shadow=None, seed=seed + 7, wobble=0.5, streaks=False)
    for k in range(9):
        hx = x0 + 20 + k * (x1 - x0 - 40) / 8
        dots(c, [(hx, y1 - 6)], 14, (20, 10, 26))
    if t > 3.4:
        kk = pop(t, 3.4)
        c.save(); c.translate(x0 + 70, y1 - 60); c.scale(kk, kk)
        blob(c, ell(0, -30, 30, 24, n=8), P_["white"], w=3, seed=seed + 9, boil=0.6)
        paint_text(c, "?", 0, -16, font="shrik", size=34, fill=P_["magenta"], ink_w=0, shadow=None, seed=seed + 10, streaks=False)
        c.restore()


def bezel(cv, x0, y0, x1, y1, seed=0, label="BOXED-OS"):
    m = 40
    blob(cv, rect_pts([(x0 - m, y0 - m), (x1 + m, y0 - m), (x1 + m, y1 + m + 30), (x0 - m, y1 + m + 30)], 4), P_["orange"], w=7, seed=seed, boil=1.0, n=3,
         shade=lambda c: c.drawRect(R(x1 - 20, y0 - m - 10, x1 + m + 20, y1 + m + 40), paint(P_["red"])))
    for k in range(3):
        blob(cv, ell(x1 + 16, y1 + 20 - k * 0, 0.1, 0.1, n=4), None, w=0)
    dots(cv, [(x0 + 30, y1 + m + 6)], 8, P_["acid"])
    paint_text(cv, label, (x0 + x1) / 2, y1 + m + 20, font="londrina", size=28, fill=P_["night"], ink_w=0, shadow=None, seed=seed + 3, streaks=False)


RETRO8 = np.array([INK, P_["white"], P_["magenta"], P_["violet"], P_["blue"], P_["night"], P_["orange"], P_["red"], P_["teal"], P_["acid"],
                   P_["yellow"], P_["cream"]], np.int32)


def quantize(a, pal):
    d = ((a[:, :, None, :].astype(np.int32) - pal[None, None]) ** 2).sum(-1)
    return pal[d.argmin(-1)].astype(np.uint8)


def scene_small(T, w_, h_, seed, levels, zee=None, agents=0, ink=0.55, pal=None):
    """Render the BOXED world small, then posterise (or snap to a console palette) -> an authentic low-res version of it."""
    surf = skia.Surface.MakeRaster(skia.ImageInfo.Make(w_, h_, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType))
    c = surf.getCanvas()
    c.scale(w_ / W, h_ / H)
    old = core.INKMUL; core.INKMUL = old * (W / w_) ** ink
    sets.cosmos(c, T, dict(x=0, y=0, z=1.0), "dusk", seed=seed, planet_xy=(1500, 250), extras=False)
    if zee:
        draw_zee(c, zee)
    for k in range(agents):
        agent(c, 200 + k * 1500 / max(1, agents), 980 - 40 * math.sin(k), 1.6, phase=T * 1.4 + k * 0.37,
              rgb=[P_["orange"], P_["teal"], P_["hotpink"], P_["yellow"]][k % 4], seed=seed + 50 + k)
    core.INKMUL = old
    a = surf.makeImageSnapshot().toarray()[:, :, :3].astype(np.int32)
    if pal is not None:
        return quantize(a, pal)
    q = 256 // levels
    a = (a // q) * q + q // 2
    return np.clip(a, 0, 255).astype(np.uint8)


def scanlines(cv, x0, y0, x1, y1, a=46, step=5):
    for yy in np.arange(y0, y1, step):
        cv.drawRect(R(x0, yy, x1, yy + 2), paint(INK, a))


def blit_nearest(cv, arr, x0, y0, wd, ht):
    fy, fx = max(1, ht // arr.shape[0]), max(1, wd // arr.shape[1])
    big = np.repeat(np.repeat(arr, fy, axis=0), fx, axis=1)
    rgba = np.dstack([big, np.full(big.shape[:2] + (1,), 255, np.uint8)])
    img = skia.Image.fromarray(np.ascontiguousarray(rgba))
    cv.save(); cv.translate(x0, y0); cv.scale(wd / big.shape[1], ht / big.shape[0]); cv.drawImage(img, 0, 0); cv.restore()


def wireframe(cv, x0, y0, x1, y1, t, seed=0):
    cv.drawRect(R(x0, y0, x1, y1), paint((6, 4, 16)))
    cx, hy = (x0 + x1) / 2, y0 + (y1 - y0) * 0.55
    neon, neon2 = (60, 255, 230), (255, 60, 200)
    for k in range(-12, 13):
        line(cv, [(cx + k * 18, hy), (cx + k * 160, y1 + 40)], 2.4, neon, seed=seed + k, boil=0.4, n=2, taper=(0, 0))
    for j in range(1, 9):
        yy = hy + (y1 - hy) * (j / 9) ** 1.7 + ((t * 40) % 30) * (j / 9)
        line(cv, [(x0, yy), (x1, yy)], 2.4, neon, seed=seed + 40 + j, boil=0.4, n=2, taper=(0, 0))
    for k, (mx, mh) in enumerate([(x0 + 140, 170), (x0 + 380, 240), (x1 - 300, 200), (x1 - 120, 140)]):
        pts = [(mx - 150, hy), (mx, hy - mh), (mx + 150, hy)]
        brush(cv, np.array(pts + [pts[0]]), 2.6, neon2, seed=seed + 60 + k, taper=(0, 0))
        line(cv, [(mx, hy - mh), (mx - 40, hy)], 2.0, neon2, seed=seed + 70 + k, boil=0.3, n=2, taper=(0, 0))
    px, py, pr = x1 - 260, y0 + 120, 70
    brush(cv, cr_closed(ell(px, py, pr, pr, n=16), 3), 2.6, neon, closed=True, seed=seed + 80)
    for j in range(1, 4):
        brush(cv, cr_closed(ell(px, py, pr, pr * j / 4, n=16), 3), 1.8, neon, closed=True, seed=seed + 81 + j)
    zx, zy = cx - 40, hy + 90
    for poly in ([(zx - 40, zy - 210), (zx + 40, zy - 210), (zx + 55, zy - 140), (zx, zy - 110), (zx - 55, zy - 140)],
                 [(zx - 30, zy - 110), (zx + 30, zy - 110), (zx + 40, zy - 20), (zx - 40, zy - 20)],
                 [(zx - 30, zy - 20), (zx - 10, zy - 20), (zx - 14, zy + 30)], [(zx + 10, zy - 20), (zx + 30, zy - 20), (zx + 14, zy + 30)]):
        brush(cv, np.array(poly + [poly[0]]), 2.6, (255, 230, 90), seed=seed + 90 + len(poly), taper=(0, 0))
    for k in range(2):
        line(cv, [(zx + (k * 2 - 1) * 18, zy - 210), (zx + (k * 2 - 1) * 34, zy - 260)], 2.4, (255, 230, 90), seed=seed + 95 + k, boil=0.3, n=2, taper=(0, 0))


def hud(cv, x0, y0, x1, y1, a=255, seed=0):
    for k in range(3):
        social_glyph(cv, 1, x0 + 40 + k * 46, y0 + 40, 0.7, seed + k, P_["red"])
    cv.drawRect(R(x1 - 230, y0 + 22, x1 - 30, y0 + 52), paint(INK, int(a * 0.6)))
    pixel_text(cv, "000420", x1 - 222, y0 + 26, 4, P_["yellow"], a)
    blob(cv, ell(x1 - 90, y1 - 90, 60, 60, n=10), (10, 40, 30), w=4, seed=seed + 10, boil=0.6, a=int(a * 0.85))
    dots(cv, [(x1 - 90, y1 - 90)], 6, P_["acid"], a)
    dots(cv, [(x1 - 70, y1 - 110), (x1 - 112, y1 - 72)], 4, P_["red"], a)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        line(cv, [(cx + dx * 14, cy + dy * 14), (cx + dx * 34, cy + dy * 34)], 4, P_["white"], seed=seed + 20 + dx * 2 + dy, boil=0.3, n=2, taper=(0, 0), a=a)
    cv.drawRect(R(x0 + 30, y1 - 50, x0 + 330, y1 - 26), paint(INK, int(a * 0.6)))
    cv.drawRect(R(x0 + 34, y1 - 46, x0 + 34 + 220, y1 - 30), paint(P_["acid"], a))


_THUMBS = None
TINTS = [P_["magenta"], P_["teal"], P_["yellow"], P_["orange"], P_["violet"], P_["acid"], P_["blue"], P_["hotpink"]]
TW, TH = 640, 360


def world_thumbs():
    """Four little BOXED worlds rendered once per process, then eight tinted 'screens' of them (+ their mean colours)."""
    global _THUMBS
    if _THUMBS is None:
        bases = []
        specs = [("dusk", 1010, (1450, 260), 960, 0.0), ("deep", 1137, (520, 240), 1150, 0.5), ("acid", 1274, (1350, 220), 760, -0.5),
                 ("dusk", 1391, (700, 200), 1200, 0.3)]
        for pal, sd, pxy, zx, zpx in specs:
            surf = skia.Surface.MakeRaster(skia.ImageInfo.Make(TW, TH, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType))
            c = surf.getCanvas(); c.scale(TW / W, TH / H)
            old = core.INKMUL; core.INKMUL = old * (W / TW) ** 0.6
            sets.cosmos(c, 2.0, dict(x=0, y=0, z=1.0), pal, seed=sd, planet_xy=pxy, extras=False)
            draw_zee(c, dict(x=zx, y=1100, s=1.05, legs=True, smile=0.5, px=zpx, aR_sh=-40, aR_el=-30, aR_pose="open"))
            core.INKMUL = old
            bases.append(surf.makeImageSnapshot())
        tinted, means = [], []
        for k, col in enumerate(TINTS):
            surf = skia.Surface.MakeRaster(skia.ImageInfo.Make(TW, TH, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType))
            c = surf.getCanvas()
            c.drawImage(bases[k % 4], 0, 0)
            c.drawRect(R(0, 0, TW, TH), paint(col, 150, blend=skia.BlendMode.kColor))
            c.drawRect(R(0, 0, TW, TH), paint(col, 40))
            a = surf.makeImageSnapshot().toarray()[:, :, :3].astype(np.float32)
            gray = a.mean(2, keepdims=True)
            a = np.clip((gray + (a - gray) * 1.45) * 1.12, 0, 255).astype(np.uint8)       # vivid glowing screens
            means.append(a.reshape(-1, 3).mean(0))
            rgba = np.dstack([a, np.full(a.shape[:2] + (1,), 255, np.uint8)])
            tinted.append(skia.Image.fromarray(np.ascontiguousarray(rgba)).withDefaultMipmaps())
        _THUMBS = (tinted, bases[0].withDefaultMipmaps(), np.array(means, np.float32))
    return _THUMBS


def plasma(I, J):
    f = np.sin(I * 0.21 + 0.4) + np.sin(J * 0.29 + 1.1) + np.sin((I + J) * 0.12 + 2.0) + np.sin(np.hypot(I + 7, J - 3) * 0.16)
    return ((f + 4.0) * 1.6).astype(int) % 8


def screen_sea(cv, cell, cx, cy, T, hi=None, dim=0.0, live_center=False):
    """A wall of little screens (pitch cell x 0.6 cell) around (cx, cy), each a whole BOXED world. Tile (0,0) is the world we
    zoomed out of; `hi` is the one real one, which stays lit when the rest dims. Returns hi's centre."""
    tinted, base, means = world_thumbs()
    px, py = cell, cell * 0.6
    i0, i1 = int(math.floor(-cx / px - 1)), int(math.ceil((W - cx) / px + 1))
    j0, j1 = int(math.floor(-cy / py - 1)), int(math.ceil((H - cy) / py + 1))
    I = np.arange(i0, i1 + 1); J = np.arange(j0, j1 + 1)
    V = plasma(I[None, :], J[:, None])
    g = cell * 0.06
    smp = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)
    src = R(0, 0, TW, TH)

    def rect(i, j):
        x, y = cx + i * px, cy + j * py
        return x - px / 2 + g / 2, y - py / 2 + g / 2, x + px / 2 - g / 2, y + py / 2 - g / 2

    if cell >= 6:
        for jj, j in enumerate(J):
            for ii, i in enumerate(I):
                x0, y0, x1, y1 = rect(i, j)
                if i == 0 and j == 0 and live_center and cell > 420:
                    mini_world(cv, x0, y0, x1, y1, T, 1010)
                    continue
                img = base if (i == 0 and j == 0) or (hi is not None and i == hi[0] and j == hi[1]) else tinted[V[jj, ii]]
                cv.drawImageRect(img, src, R(x0, y0, x1, y1), smp)
                if cell > 160:
                    brush(cv, np.array([(x0, y0), (x1, y0), (x1, y1), (x0, y1)]), 4.0 * min(2.0, cell / 300), closed=True, seed=int(i * 31 + j * 17))
    else:                                                     # far away: one colour per screen, gaps folded into brightness
        ii = np.clip(np.floor((np.arange(W) - cx) / px + 0.5).astype(int) - i0, 0, len(I) - 1)
        jj = np.clip(np.floor((np.arange(H) - cy) / py + 0.5).astype(int) - j0, 0, len(J) - 1)
        img = (means[V[jj][:, ii]] * 0.846).astype(np.uint8)
        rgba = np.dstack([img, np.full((H, W, 1), 255, np.uint8)])
        cv.drawImage(skia.Image.fromarray(np.ascontiguousarray(rgba)), 0, 0)
    if dim > 0:
        cv.drawRect(R(-60, -60, W + 60, H + 60), paint(P_["void"], int(255 * dim)))
    if hi is None:
        return None
    hx, hy = cx + hi[0] * px, cy + hi[1] * py
    if dim > 0:
        if cell >= 6:
            cv.drawImageRect(base, src, R(*rect(*hi)), smp)
        else:
            for k in range(4, 0, -1):
                dots(cv, [(hx, hy)], 2.5 + k * 3, P_["cream"], a=int(60 * dim))
            dots(cv, [(hx, hy)], 3.2, P_["white"])
    return hx, hy


# ------------------------------------------------------------------ E01–E05
def E01_hook(cv, t, T, A):
    cam = dict(x=0, y=0, z=1.0 + 0.025 * t)
    sets.cosmos(cv, T, cam, "deep", seed=201, planet_xy=(2900, -900), extras=True)
    C = sets.Cam(cv, cam)
    with C.layer(0.8):
        for k in range(12):
            kind = k % 4
            x = (hsh(210 + k) * 2100 + t * (30 + 25 * hsh(k))) % 2100 - 90
            y = 120 + hsh(220 + k) * 860 + 18 * math.sin(t * 1.3 + k)
            social_glyph(cv, kind, x, y, 0.8 + 0.5 * hsh(230 + k), 240 + k * 9, [P_["hotpink"], P_["acid"], P_["yellow"], P_["teal"]][k % 4])
    with C.layer(1.0):
        w.tv(cv, 600, 610, 1.6, seed=250, screen=lambda c, r: stage_tv_screen(c, r, t), body=P_["teal"])
    items = [("2016.", 0.5, "shrik", 120, P_["yellow"]), ("SOMEONE ASKS ELON MUSK", 1.9, "londrina", 66, P_["cream"]),
             ("IF WE'RE ALL LIVING", 3.55, "londrina", 66, P_["cream"]), ("INSIDE A VIDEO GAME.", 4.4, "londrina", 66, P_["teal"]),
             ("HIS ANSWER", 6.35, "londrina", 70, P_["cream"]), ("WENT VIRAL.", 6.95, "shrik", 120, P_["acid"])]
    for j, (txt, t0, fnt, sz, col) in enumerate(items):
        if t >= t0:
            y = [210, 340, 450, 540, 680, 820][j]
            paint_text(cv, txt, 1430, y, font=fnt, size=sz, fill=col, ink_w=6 if fnt == "shrik" else 4.5, shadow=(7, 7) if fnt == "shrik" else (5, 5),
                       shadow_rgb=P_["magenta"] if j in (0, 5) else INK, seed=260 + j, reveal=float(np.clip((t - t0) / 0.55, 0, 1)), stagger=0.035,
                       drips=1.0 if j == 5 else 0)
    if t > 7.0:
        for k in range(6):
            a = k / 6 * 2 * math.pi + t * 2
            sparkle(cv, 1430 + 330 * math.cos(a), 790 + 60 * math.sin(a), 16 + 6 * math.sin(t * 7 + k), P_["acid"], seed=270 + k)


def E02_title(cv, t, T, A):
    cam = dict(x=0, y=0, z=1.0 + 0.02 * t)
    sets.cosmos(cv, T, cam, "dusk", seed=101, planet_xy=(1580, 230))
    C = sets.Cam(cv, cam)
    with C.layer(0.8):
        w.halo(cv, 960, 560, [470, 390, 310, 230], [P_["magenta"], P_["orange"], P_["yellow"], P_["teal"]], seed=150)
        hits = [0.25, 0.85, 1.45, 2.05, 2.65, 3.25]
        u = t
        k = int(np.clip(np.searchsorted(hits, u) - 1, 0, len(hits) - 2))
        a, b = hits[k], hits[k + 1]
        f = np.clip((u - a) / (b - a), 0, 1)
        xa, xb = (790, -790) if k % 2 == 0 else (-790, 790)
        bx = 960 + lerp(xa, xb, f) if u >= hits[0] else 960
        by = 560 + 150 * math.sin(u * 5.1)
        for side in (-1, 1):                                   # paddles chase the ball
            heading = (xb - xa) * side > 0
            py = 560 + (0.92 if heading else 0.3) * (by - 560)
            px = 960 + side * 820
            for j in range(3, 0, -1):
                cv.drawRect(R(px - 18 - j * 7, py - 140 - j * 7, px + 18 + j * 7, py + 140 + j * 7), paint(P_["white"], 22))
            cv.drawRect(R(px - 18, py - 140, px + 18, py + 140), paint(P_["white"]))
        wob = 2.6 + (4.0 * math.exp(-((u - a) / 0.12) ** 2) if u >= hits[0] else 0)
        paint_text(cv, "BOXED", 960, 620, font="shrik", size=300, fill=P_["yellow"], ink_w=9, shadow=(14, 14), shadow_rgb=P_["magenta"], seed=180,
                   wobble=wob, reveal=float(np.clip(t / 0.9, 0, 1)), stagger=0.12, drips=1.2)
        if t > 1.0:
            paint_text(cv, "EPISODE TWO", 960, 720, font="londrina", size=56, fill=P_["cream"], ink_w=4, shadow=(5, 5), seed=190,
                       reveal=float(np.clip((t - 1.0) / 0.5, 0, 1)), stagger=0.05)
        if t > 1.4:
            paint_text(cv, "ONE IN BILLIONS", 960, 820, font="londrina", size=96, fills=[P_["teal"], P_["yellow"], P_["hotpink"], P_["acid"]], ink_w=6,
                       shadow=(7, 7), seed=200, reveal=float(np.clip((t - 1.4) / 0.8, 0, 1)), stagger=0.04)
        dirn = 1 if xb > xa else -1                            # the ball, in front of everything
        for j in range(1, 6):
            glow_square(cv, bx - dirn * j * 18, by, 28 - j * 3, P_["white"], a=int(160 / j))
        glow_square(cv, bx, by, 30)


def E03_wide(cv, t, T, A):
    cam = dict(x=0, y=30, z=1.02 + 0.01 * t)
    sets.talkshow(cv, T, cam, host=Hh(A, t), guest=G(A, t))
    audience_rows(cv, T, raise_k=ease((t - 3.7) / 0.6) * 0.3 if t > 3.7 else 0.0)
    tag(cv, "THE HOST", "our man on the inside", 90, 160, t, 0.3, 99, P_["magenta"], "left", seed=300)


def E04_eyeball(cv, t, T, A):
    w.field(cv, (24, 12, 44))
    cv.drawPath(poly_path([(860, -40), (1060, -40), (1500, 1100), (420, 1100)]), paint(P_["yellow"], 38))
    for row in range(3):
        for k in range(9):
            x = 60 + k * 230 + (115 if row % 2 else 0)
            y = 420 + row * 210
            if abs(x - 960) < 220 and row >= 1:
                continue
            blob(cv, ell(x, y, 80, 84, n=10), [(40, 20, 70), (54, 26, 90)][(k + row) % 2], w=5, seed=2700 + row * 30 + k, boil=1.0)
            dots(cv, [(x + 10, y - 8)], 20, (200, 255, 230) if (k + row) % 2 else (255, 200, 240))
            dots(cv, [(x + 10, y - 8)], 9, INK)
    k = ease(t / 0.4)
    eyeball_creature(cv, 960, 470 + 60 * (1 - k), 1.45, T, loud=loud_at("A01", T), seed=2800, mic=True, wave=ease(t / 0.5))
    tag(cv, "GARY", "audience member", 90, 980, t, 0.25, 99, P_["orange"], "left", seed=310)


def E05_host_take(cv, t, T, A):
    cam = dict(x=CAM_HOST["x"], y=CAM_HOST["y"], z=1.8 + 0.04 * t)
    sets.talkshow(cv, T, cam, host=Hh(A, t), guest=G(A, t))


# ------------------------------------------------------------------ E06 Pong
def E06_pong(cv, t, T, A):
    w.field(cv, P_["void"])
    w.stars(cv, 601, (0, 0, W, H), n=260, big=8)
    w.planet(cv, 1830, 985, 100, P_["teal"], bands=[(-0.3, 0.3, P_["blue"])], seed=602, face=dict(look=(-0.8, -0.4), smile=0.3))
    w.skull_moon(cv, 200, 160, 60, seed=603)
    for k in range(13):
        sparkle(cv, 960, 90 + k * 72, 10, P_["white"], seed=604 + k, w=2)
    XL, XR = 300, 1620
    contacts = [0.4, 1.1, 1.8, 2.5, 3.2, 3.9]
    u = t
    if u < contacts[0]:
        bx, by = 960 + (XL + 40 - 960) * (u / contacts[0]), 540
    else:
        k = int(np.clip(np.searchsorted(contacts, u) - 1, 0, len(contacts) - 2))
        a, b = contacts[k], contacts[k + 1]
        f = (u - a) / (b - a)
        xa = XL + 40 if k % 2 == 0 else XR - 40
        xb = XR - 40 if k % 2 == 0 else XL + 40
        if u > contacts[-1]:
            xa, xb, f = XR - 40, XR + 500, (u - contacts[-1]) / 0.7
        bx = lerp(xa, xb, f)
        tri = (u * 0.9) % 2
        by = 220 + 640 * (tri if tri < 1 else 2 - tri)
    lp = 540 + 0.85 * (by - 540) if bx < 960 else 540 + 0.3 * (by - 540) * math.sin(t)
    rp = 540 + 0.85 * (by - 540) if (bx >= 960 and u < 3.6) else 540 + 200 * math.sin(t * 1.3)
    for x, y in ((XL, lp), (XR, rp)):
        for k in range(3, 0, -1):
            cv.drawRect(R(x - 22 - k * 8, y - 120 - k * 8, x + 22 + k * 8, y + 120 + k * 8), paint(P_["white"], 22))
        blob(cv, rect_pts([(x - 22, y - 120), (x + 22, y - 120), (x + 22, y + 120), (x - 22, y + 120)], 3), P_["white"], w=5, seed=610 + x, boil=0.8, n=2)
    for j in range(1, 8):
        glow_square(cv, bx - j * 22 * (1 if (int(np.searchsorted(contacts, u)) % 2) else -1), by, 34 - j * 3.5, P_["white"], a=int(130 / j))
    glow_square(cv, bx, by, 36)
    score = "0 1" if u > contacts[-1] + 0.3 else "0 0"
    pixel_text(cv, score[0], 760, 70, 18, P_["white"]); pixel_text(cv, score[-1], 1100, 70, 18, P_["white"])
    paint_text(cv, "1972", 960, 1020, font="shrik", size=80, fill=P_["yellow"], ink_w=5, shadow=(6, 6), shadow_rgb=P_["magenta"], seed=620,
               reveal=float(np.clip((t - 0.2) / 0.5, 0, 1)))
    if t > 2.54:
        r = float(np.clip((t - 2.54) / 0.5, 0, 1))
        paint_text(cv, "TWO RECTANGLES", 960, 330, font="londrina", size=88, fill=P_["cream"], ink_w=5, shadow=(6, 6), seed=630, reveal=r, stagger=0.03)
        paint_text(cv, "AND A DOT.", 960, 440, font="londrina", size=88, fill=P_["acid"], ink_w=5, shadow=(6, 6), seed=631,
                   reveal=float(np.clip((t - 2.95) / 0.4, 0, 1)), stagger=0.04)
        line(cv, [(600, 300), (430, 330 + 0.3 * (lp - 330)), (XL + 48, lp - 70)], 6, P_["yellow"], seed=632, boil=1.0, n=4, taper=(0, 0.4), a=int(255 * r))
        line(cv, [(1320, 300), (1490, 330 + 0.3 * (rp - 330)), (XR - 48, rp - 70)], 6, P_["yellow"], seed=633, boil=1.0, n=4, taper=(0, 0.4), a=int(255 * r))
        if t > 2.95:
            g = pop(t, 2.95, 0.3)
            brush(cv, cr_closed(jit(ell(bx, by, 56 * g, 56 * g, n=10), 2.0, 634), 4), 6, P_["acid"], closed=True, seed=635)


# ------------------------------------------------------------------ E07 evolution
def E07_evolution(cv, t, T, A):
    w.field(cv, P_["night"])
    w.sunburst(cv, 960, 540, 1600, 24, [P_["violet"], P_["night"]], rot_deg=t * 8, seed=700)
    w.stars(cv, 701, (0, 0, W, H), n=200, big=8)
    x0, y0, x1, y1 = 320, 130, 1600, 850
    bezel(cv, x0, y0, x1, y1, seed=702)
    cv.save(); cv.clipPath(poly_path([(x0, y0), (x1, y0), (x1, y1), (x0, y1)]), doAntiAlias=True)
    zee = dict(x=960, y=1060, s=1.0, legs=True, aR_sh=-50, aR_el=-20, aR_pose="open", smile=0.6, px=0.2)
    eras = [(0.0, "1985", "8-BIT"), (0.55, "1995", "16-BIT"), (1.1, "2005", "3D"), (1.7, "TODAY", "PHOTOREAL")]
    era = max(i for i, (a, _, _) in enumerate(eras) if t >= a)
    if era == 0:
        blit_nearest(cv, scene_small(T, 80, 45, 710, 4, zee, ink=0.3, pal=RETRO8), x0, y0, x1 - x0, y1 - y0)
        scanlines(cv, x0, y0, x1, y1)
    elif era == 1:
        blit_nearest(cv, scene_small(T, 160, 90, 710, 16, zee, ink=0.45), x0, y0, x1 - x0, y1 - y0)
        scanlines(cv, x0, y0, x1, y1, a=30)
    elif era == 2:
        wireframe(cv, x0, y0, x1, y1, t, seed=720)
    else:
        cv.save(); cv.translate(x0, y0); cv.scale((x1 - x0) / W, (y1 - y0) / H)
        old = core.INKMUL; core.INKMUL = old * 1.25
        extra = int(np.clip((t - 5.35) / 0.5, 0, 4)) if t > 5.35 else 0
        sets.cosmos(cv, T, dict(x=0, y=0, z=1.0), "dusk", seed=710, planet_xy=(1500, 250), extras=True)
        for k in range(extra):
            w.planet(cv, 300 + k * 380, 200 + 60 * (k % 2), 50 + 10 * k, [P_["acid"], P_["hotpink"], P_["teal"], P_["yellow"]][k], bands=[(-0.2, 0.3, P_["violet"])],
                     seed=730 + k, crater=False, face=dict(look=(0.5, 0.5), smile=0.6))
        n_ag = 0 if t < 2.47 else int(np.clip((t - 2.47) / 1.2, 0, 1) * 60)
        for k in range(n_ag):
            ax = 60 + (k * 137) % 1800
            ay = 900 + (k * 53) % 160
            agent(cv, ax, ay, 0.9 + 0.3 * hsh(k), phase=T * 1.6 + k * 0.21, rgb=[P_["orange"], P_["teal"], P_["hotpink"], P_["yellow"], P_["lilac"]][k % 5], seed=740 + k)
        draw_zee(cv, zee)
        core.INKMUL = old
        cv.restore()
    cv.restore()
    a, yr, lab = eras[era]
    kk = pop(t, a, 0.25)
    cv.save(); cv.translate(x0 + 30, y0 + 30); cv.scale(kk, kk)
    blob(cv, rect_pts([(0, 0), (300, 0), (300, 70), (0, 70)], 3), INK, w=0, seed=750 + era, boil=0.6, n=3, a=200)
    paint_text(cv, f"{yr} · {lab}", 150, 52, font="londrina", size=44, fill=P_["yellow"], ink_w=0, shadow=None, seed=751 + era, streaks=False)
    cv.restore()
    if t > 2.47:
        paint_text(cv, "MILLIONS PLAYING AT ONCE", 960, 1020, font="londrina", size=64, fills=[P_["cream"], P_["acid"]], ink_w=4.5, shadow=(5, 5), seed=760,
                   reveal=float(np.clip((t - 2.47) / 0.7, 0, 1)), stagger=0.02)
    if t > 5.35:
        yr = 2026 + int((t - 5.35) / 0.5)
        cv.drawRect(R(x1 - 330, y0 + 26, x1 - 26, y0 + 96), paint(INK, 200))
        pixel_text(cv, str(yr), x1 - 310, y0 + 36, 10, P_["acid"])
        paint_text(cv, "BETTER EVERY YEAR", 960, 100, font="londrina", size=60, fill=P_["yellow"], ink_w=4.5, shadow=(5, 5), seed=770,
                   reveal=float(np.clip((t - 5.35) / 0.6, 0, 1)), stagger=0.02)


# ------------------------------------------------------------------ E08–E09
def rate_chart(cv, t, seed=800):
    x0, y0, x1, y1 = 110, 190, 820, 800
    k = pop(t, 0.15, 0.35)
    if k <= 0:
        return
    cv.save(); cv.translate((x0 + x1) / 2, (y0 + y1) / 2); cv.scale(k, k); cv.translate(-(x0 + x1) / 2, -(y0 + y1) / 2)
    blob(cv, rect_pts([(x0, y0), (x1, y0 + 10), (x1 - 6, y1), (x0 + 6, y1 - 6)], 3), P_["cream"], w=6, seed=seed, boil=1.0, n=3)
    ax0, ay0, ax1, ay1 = x0 + 80, y0 + 90, x1 - 50, y1 - 80
    line(cv, [(ax0, ay1), (ax1, ay1)], 5, seed=seed + 1, boil=0.6, n=2, taper=(0, 0.1))
    line(cv, [(ax0, ay1), (ax0, ay0)], 5, seed=seed + 2, boil=0.6, n=2, taper=(0, 0.1))
    paint_text(cv, "GRAPHICS", ax0 - 30, ay0 - 20, font="londrina", size=32, fill=P_["night"], ink_w=0, shadow=None, seed=seed + 3, streaks=False, align="left")
    paint_text(cv, "TIME", ax1 - 40, ay1 + 50, font="londrina", size=32, fill=P_["night"], ink_w=0, shadow=None, seed=seed + 4, streaks=False)
    ry = ay0 + 80
    for xx in np.arange(ax0, ax1, 34):
        line(cv, [(xx, ry), (xx + 18, ry)], 4, P_["red"], seed=seed + int(xx), boil=0.4, n=2, taper=(0, 0))
    paint_text(cv, "REALITY", ax0 + 10, ry - 16, font="londrina", size=34, fill=P_["red"], ink_w=0, shadow=None, seed=seed + 5, streaks=False, align="left")

    def curve(hit, prog, col, sd):
        if prog <= 0:
            return
        us = np.linspace(0, prog, int(70 * prog) + 2)
        xs = ax0 + us * (ax1 - ax0)
        ys = ay1 - (ay1 - ry) * np.minimum(1.0, (us / hit) ** 2.4)
        brush(cv, np.stack([xs, ys], 1), 8, col, seed=sd, taper=(0.05, 0.02))
        if prog >= hit:
            hx = ax0 + hit * (ax1 - ax0)
            g = float(np.clip((prog - hit) * 6, 0, 1))
            sparkle(cv, hx, ry, 12 + 16 * g, P_["yellow"], seed=sd + 1)
            dots(cv, [(hx, ry)], 7, col)

    curve(0.40, float(np.clip((t - 0.4) / 1.2, 0, 1)), P_["magenta"], seed + 10)
    curve(0.92, float(np.clip((t - 2.6) / 2.8, 0, 1)), P_["blue"], seed + 20)
    lx, ly = ax0 + 320, ay1 - 76                                        # legend, bottom-right, under both curves
    for j, (lab, col, t0) in enumerate((("NOW", P_["magenta"], 0.6), ("1000x SLOWER", P_["blue"], 2.6))):
        if t > t0:
            line(cv, [(lx, ly + j * 50), (lx + 46, ly + j * 50)], 8, col, seed=seed + 30 + j, boil=0.5, n=2, taper=(0, 0))
            paint_text(cv, lab, lx + 60, ly + 12 + j * 50, font="londrina", size=32, fill=col, ink_w=0, shadow=None, seed=seed + 32 + j, streaks=False,
                       align="left", reveal=float(np.clip((t - t0) / 0.4, 0, 1)))
    cv.restore()


def E08_zee_rate(cv, t, T, A):
    cam = dict(x=CAM_ZEE["x"] - 120, y=CAM_ZEE["y"], z=1.72 + 0.015 * t)
    sets.talkshow(cv, T, cam, host=Hh(A, t), guest=G(A, t))
    rate_chart(cv, t)
    tag(cv, "ZEE", "guest · simulant", W - 90, 980, t, 0.3, 99, P_["teal"], "right", seed=320)
    if t > 6.75:
        r = float(np.clip((t - 6.75) / 0.8, 0, 1))
        paint_text(cv, "INDISTINGUISHABLE", 1240, 160, font="londrina", size=86, fill=P_["yellow"], ink_w=5.5, shadow=(7, 7), shadow_rgb=P_["magenta"], seed=850,
                   reveal=r, stagger=0.025)
        paint_text(cv, "FROM REALITY", 1240, 255, font="londrina", size=86, fill=P_["acid"], ink_w=5.5, shadow=(7, 7), shadow_rgb=P_["magenta"], seed=851,
                   reveal=float(np.clip((t - 7.7) / 0.6, 0, 1)), stagger=0.03)


def E09_host_gfx(cv, t, T, A):
    cam = dict(x=CAM_HOST["x"], y=CAM_HOST["y"], z=1.85 + 0.02 * t)
    sets.talkshow(cv, T, cam, host=Hh(A, t), guest=G(A, t))
    for k, (txt, col, x, y, rot, t0, wd) in enumerate((("4K", P_["yellow"], 1440, 470, -8, 1.3, 120), ("HDR", P_["hotpink"], 1680, 640, 7, 1.55, 160),
                                                        ("ULTRA", P_["acid"], 1450, 830, -5, 1.8, 210))):
        kk = pop(t, t0, 0.3)
        if kk <= 0:
            continue
        cv.save(); cv.translate(x, y); cv.rotate(rot); cv.scale(kk, kk)
        blob(cv, rect_pts([(-wd, -66), (wd, -62), (wd + 4, 64), (-wd + 2, 66)], 3), col, w=6, seed=905 + k, boil=0.9, n=3,
             shade=lambda c, wd=wd: stipple(c, P_["white"], (-wd, -66, wd, 66), spacing=14, r=1.6, seed=909, a=70))
        paint_text(cv, txt, 0, 32, font="shrik", size=92, fill=P_["white"], ink_w=5, shadow=(5, 5), seed=906 + k, streaks=False)
        cv.restore()
        if t < t0 + 0.4:
            for j in range(4):
                a = j / 4 * 2 * math.pi + t * 3
                sparkle(cv, x + (wd + 50) * math.cos(a), y + 100 * math.sin(a), 14, P_["white"], seed=912 + k * 4 + j)


# ------------------------------------------------------------------ E10–E12 billions of worlds
def mini_world(cv, x0, y0, x1, y1, T, seed, zee_px=0.0):
    cv.save(); cv.clipPath(poly_path([(x0, y0), (x1, y0), (x1, y1), (x0, y1)]), doAntiAlias=True)
    cv.translate(x0, y0); cv.scale((x1 - x0) / W, (y1 - y0) / H)
    old = core.INKMUL; core.INKMUL = old * (W / (x1 - x0)) ** 0.5
    sets.cosmos(cv, T, dict(x=0, y=0, z=1.0), "dusk", seed=seed, planet_xy=(1450, 260), extras=False)
    draw_zee(cv, dict(x=960, y=1100, s=1.05, legs=True, smile=0.5, px=zee_px, aR_sh=-40, aR_el=-30, aR_pose="open"))
    core.INKMUL = old
    cv.restore()


def E10_worlds(cv, t, T, A):
    w.field(cv, P_["void"])
    if t < 1.45:
        w.stars(cv, 1001, (0, 0, W, H), n=240, big=10)
        for side, lab in ((-1, "REAL?"), (1, "GAME?")):
            if t > 0.75:
                lab = "GAME?" if side < 0 else "REAL?"
            x0 = 960 + side * 470 - 430; x1 = x0 + 860; y0, y1 = 250, 250 + 484
            mini_world(cv, x0, y0, x1, y1, T, 1010)
            brush(cv, np.array([(x0, y0), (x1, y0), (x1, y1), (x0, y1)]), 7, closed=True, seed=1011 + side)
            if side > 0 and (t < 0.6 or (t > 0.9 and int(t * 10) % 2 == 0)):
                hud(cv, x0, y0, x1, y1, seed=1012)
            paint_text(cv, lab, (x0 + x1) / 2, 200, font="londrina", size=72, fill=P_["yellow"], ink_w=5, shadow=(6, 6), seed=1013 + side)
        paint_text(cv, "CAN YOU TELL?", 960, 900, font="shrik", size=96, fill=P_["acid"], ink_w=6, shadow=(8, 8), shadow_rgb=P_["magenta"], seed=1015,
                   reveal=float(np.clip((t - 0.2) / 0.5, 0, 1)))
        return
    u = t - 1.45
    f = float(np.clip(u / 5.0, 0, 1)); f = f * f * (3 - 2 * f)
    cell = math.exp(math.log(2043.0) + (math.log(3.2) - math.log(2043.0)) * f)
    dim = 0.3 * ease((t - 4.3) / 0.4) if t < 6.0 else 0.3 + 0.32 * ease((t - 6.0) / 0.6)
    hx, hy = screen_sea(cv, cell, 960, 540, T, hi=(37, -21), dim=dim, live_center=True)
    if t > 4.42:
        paint_text(cv, "BILLIONS OF FAKE WORLDS", 960, 150, font="londrina", size=96, fills=[P_["cream"], P_["yellow"]], ink_w=6, shadow=(7, 7), seed=1030,
                   reveal=float(np.clip((t - 4.42) / 0.8, 0, 1)), stagger=0.02)
    if t > 6.0:
        g = pop(t, 6.0, 0.4)
        for k in range(3):
            brush(cv, cr_closed(jit(ell(hx, hy, (34 + k * 16) * g, (34 + k * 16) * g, n=12), 1.5, 1040 + k), 4), 6 - k, P_["yellow"], closed=True, seed=1043 + k)
        line(cv, [(hx + 300, hy + 230), (hx + 140, hy + 120), (hx + 52, hy + 46)], 9, P_["yellow"], seed=1046, boil=1.0, n=4, taper=(0, 0.6))
        paint_text(cv, "...AND ONE REAL ONE", 960, 960, font="londrina", size=96, fill=P_["acid"], ink_w=6, shadow=(7, 7), seed=1047,
                   reveal=float(np.clip((t - 6.0) / 0.7, 0, 1)), stagger=0.03)


def E11_zee_odds(cv, t, T, A):
    cam = dict(x=CAM_ZEE["x"], y=CAM_ZEE["y"], z=1.9 + 0.05 * t)
    sets.talkshow(cv, T, cam, host=Hh(A, t), guest=G(A, t))
    if t > 0.6:
        paint_text(cv, "BASE REALITY?", 520, 260, font="shrik", size=92, fill=P_["yellow"], ink_w=6, shadow=(7, 7), shadow_rgb=P_["magenta"], seed=1100,
                   reveal=float(np.clip((t - 0.6) / 0.6, 0, 1)), stagger=0.04)


def E12_billions(cv, t, T, A):
    w.field(cv, P_["void"])
    shake = (hsh(core.D * 1.7) - 0.5) * 18 * math.exp(-t * 4) if t > 0.1 else 0
    cv.save(); cv.translate(shake, 0)
    hx, hy = screen_sea(cv, 4.2 + 0.5 * t, 960, 540, T, hi=(-130, 55), dim=0.58)
    for k in range(3):
        brush(cv, cr_closed(jit(ell(hx, hy, 30 + k * 14, 30 + k * 14, n=12), 1.5, 1240 + k), 4), 6 - k, P_["yellow"], closed=True, seed=1243 + k)
    k = pop(t, 0.1, 0.35)
    cv.save(); cv.translate(960, 560); cv.scale(k, k)
    for j in range(16):
        a = j / 16 * 2 * math.pi + t
        line(cv, [(math.cos(a) * 420, math.sin(a) * 220), (math.cos(a) * 760, math.sin(a) * 420)], 12, P_["magenta"], seed=1250 + j, boil=1.5, n=2,
             taper=(0.1, 0.8), a=160)
    paint_text(cv, "ONE IN", 0, -40, font="shrik", size=190, fill=P_["yellow"], ink_w=9, shadow=(12, 12), shadow_rgb=P_["magenta"], seed=1260, drips=1.0)
    paint_text(cv, "BILLIONS", 0, 150, font="shrik", size=210, fill=P_["acid"], ink_w=9, shadow=(12, 12), shadow_rgb=P_["magenta"], seed=1261, drips=1.0)
    cv.restore(); cv.restore()
    if t > 0.25:
        paint_text(cv, "— ELON MUSK, CODE CONFERENCE 2016", 960, 1030, font="marker", size=36, fill=P_["cream"], ink_w=0, shadow=(3, 3), seed=1270,
                   streaks=False, reveal=float(np.clip((t - 0.25) / 0.35, 0, 1)))


# ------------------------------------------------------------------ E13 the host realises
def E13_host_console(cv, t, T, A):
    z = 1.85 + 0.03 * t + (0.35 * ease((t - 2.66) / 0.14) if t > 2.66 else 0)
    shake = (hsh(core.D * 1.9) - 0.5) * 12 if 2.66 < t < 3.0 else 0
    cam = dict(x=CAM_HOST["x"] + shake, y=CAM_HOST["y"] - (30 * ease((t - 2.66) / 0.14) if t > 2.66 else 0), z=z)
    h = Hh(A, t)
    if 0.7 < t < 2.66:
        h["face"] = "grid"
    sets.talkshow(cv, T, cam, host=h, guest=G(A, t))
    if t > 2.75:
        k = pop(t, 2.75, 0.3)
        cv.save(); cv.translate(960, 150 + 8 * math.sin(t * 6)); cv.scale(k, k)
        blob(cv, [(-30, -10), (30, -10), (0, 30)], P_["acid"], w=4, seed=1300, boil=0.6, n=2)
        pixel_text(cv, "P1", -38, -84, 12, P_["acid"])
        cv.restore()


# ------------------------------------------------------------------ E14 the fork
def E14_fork(cv, t, T, A):
    cam = dict(x=0, y=0, z=1.0 + 0.02 * t)
    sets.cosmos(cv, T, cam, "dusk", seed=1401, planet_xy=(2900, -900), extras=False)
    C = sets.Cam(cv, cam)
    with C.layer(0.55):
        cv.drawPath(poly_path([(1250, -60), (1990, -60), (1990, 1140), (1390, 1140)]), paint(P_["void"], 175))   # the doom side goes dark
        w.skull_moon(cv, 1640, 190, 80, seed=1450)
        ax, ay = 1800 - 40 * t, 360 + 22 * t
        for j in range(6):
            line(cv, [(ax + 30, ay - 10), (ax + 160 + j * 20, ay - 90 - j * 12)], 18 - j * 2, P_["orange"] if j % 2 else P_["yellow"], seed=1451 + j,
                 boil=2.0, n=2, taper=(0.1, 1.0), a=200)
        blob(cv, ell(ax, ay, 70, 60, n=10), P_["maroon"], w=6, seed=1460, boil=1.2,
             shade=lambda c: [dots(c, [(ax - 20 + i * 24, ay - 10 + 14 * (i % 2))], 9, P_["red"]) for i in range(3)])
        line(cv, [(ax - 36, ay - 24), (ax - 10, ay - 14)], 6, seed=1461, boil=0.6, n=2)
        line(cv, [(ax + 36, ay - 24), (ax + 10, ay - 14)], 6, seed=1462, boil=0.6, n=2)
    with C.layer(0.75):
        w.halo(cv, 420, 470, [400, 320, 240], [P_["magenta"], P_["hotpink"], P_["yellow"]], seed=1409)
        cx0, cy0 = 430, 700                                    # a glowing city made of screens
        for k in range(9):
            bw, bh = 70 + 30 * hsh(1410 + k), 160 + 260 * hsh(1420 + k)
            bx = cx0 - 330 + k * 78
            blob(cv, rect_pts([(bx, cy0 - bh), (bx + bw, cy0 - bh), (bx + bw, cy0), (bx, cy0)], 3), [P_["teal"], P_["violet"], P_["blue"]][k % 3], w=4.5,
                 seed=1430 + k, boil=0.8, n=2,
                 shade=lambda c, bx=bx, bw=bw, bh=bh, k=k: [c.drawRect(R(bx + 10 + i * 18, cy0 - bh + 14 + j * 22, bx + 22 + i * 18, cy0 - bh + 28 + j * 22),
                                                                       paint(P_["yellow"] if hsh(k * 31 + i * 7 + j) > 0.4 else P_["magenta"]))
                                                                for i in range(int(bw // 20)) for j in range(int(bh // 24) - 1)])
        for k in range(5):
            sparkle(cv, cx0 - 300 + k * 150, cy0 - 470 + 40 * math.sin(t + k), 14, P_["acid"], seed=1440 + k)
    with C.layer(1.0):
        cv.drawRect(R(1440, 690, 2000, 1140), paint(P_["void"]))                              # the chasm
        for k in range(4):
            fy = 760 + ((t * 260 + k * 110) % 380)
            blob(cv, ell(1560 + k * 90, fy, 14, 11, n=6), (90, 70, 110), w=3, seed=1475 + k, boil=0.8)
        blob(cv, [(-60, 700), (700, 688), (1440, 698), (1482, 780), (1446, 880), (1504, 990), (1462, 1140), (-60, 1140)], P_["vdark"], w=6, seed=1471, boil=1.0, n=3,
             shade=lambda c: stipple(c, P_["violet"], (0, 700, 1500, 1140), spacing=13, r=1.8, seed=1472, a=120))
        road = (90, 70, 110)
        blob(cv, [(925, 872), (978, 862), (690, 702), (646, 702)], road, w=5, seed=1481, boil=1.0, n=2)                 # to the city
        blob(cv, [(948, 862), (1000, 872), (1452, 712), (1426, 704)], road, w=5, seed=1482, boil=1.0, n=2)               # off the cliff
        blob(cv, [(790, 1140), (1130, 1140), (992, 858), (928, 858)], road, w=6, seed=1480, boil=1.0, n=2)
        for k in range(5):
            yy = 1100 - k * 52
            line(cv, [(960, yy), (960, yy - 26)], 9 - k, P_["yellow"], seed=1483 + k, boil=0.6, n=2, taper=(0, 0))
        line(cv, [(960, 870), (960, 430)], 14, (130, 86, 50), seed=1489, boil=0.7, n=2, taper=(0, 0))                     # the signpost
        for side, t0, txt, col, yy in ((-1, 0.15, "BUILD THE SIMS", P_["teal"], 470), (1, 1.98, "THE END", P_["red"], 566)):
            k = pop(t, t0, 0.3)
            if k <= 0:
                continue
            cv.save(); cv.translate(960, yy); cv.scale(side * k, k)
            blob(cv, rect_pts([(-20, -46), (360, -46), (410, 0), (360, 46), (-20, 46)], 4), P_["cream"], w=5.5, seed=1495 + side, boil=0.9, n=2)
            cv.restore()
            paint_text(cv, txt, 960 + side * 196 * k, yy + 17, font="londrina", size=46 * k, fill=col, ink_w=3.5, shadow=(3, 3), seed=1497 + side, streaks=False)
        g = dict(A["GUEST"]); g.update(x=960, y=1050, s=0.5, legs=True)
        look = -0.9 if t < 1.9 else (0.9 if t < 4.4 else 0.0)
        g["px"] = look; g["head_turn"] = 0.35 * look
        from .shots_a import guest_prop
        draw_zee(cv, guest_prop(g, t))
    if t > 4.48:
        paint_text(cv, "THOSE ARE THE OPTIONS.", 960, 140, font="londrina", size=92, fill=P_["yellow"], ink_w=6, shadow=(7, 7), seed=1499,
                   reveal=float(np.clip((t - 4.48) / 0.7, 0, 1)), stagger=0.02)


# ------------------------------------------------------------------ E15 the coin
def E15_coin(cv, t, T, A):
    cam = dict(x=0, y=0, z=1.0)
    sets.cosmos(cv, T, cam, "acid", seed=1501, planet_xy=(1660, 200), extras=True)
    w.island(cv, 960, 900, 420, 70, seed=1502, top=P_["violet"], depth=160)
    t_up, t_land = 0.2, 2.5
    if t < t_up:
        cy, ang = 900, 0.0
    elif t < t_land:
        u = (t - t_up) / (t_land - t_up)
        cy = 900 - 4 * 290 * u * (1 - u)
        ang = u * 9 * math.pi
    else:
        cy, ang = 900, 9 * math.pi + math.pi / 2 + 0.25 * math.exp(-(t - t_land) * 3) * math.sin((t - t_land) * 18)
    sx = math.cos(ang)
    r = 150
    face_up = sx >= 0
    rimw = 26
    cv.save(); cv.translate(960, cy - r)
    blob(cv, ell(0, 0, max(rimw / 2, r * abs(sx)) + rimw * 0.5 * (1 - abs(sx)), r, n=16), (190, 140, 30), w=6, seed=1510, boil=0.9)
    if abs(sx) > 0.08:
        cv.save(); cv.scale(abs(sx), 1.0)
        blob(cv, ell(0, 0, r - 14, r - 14, n=16), P_["yellow"] if face_up else (200, 200, 215), w=5, seed=1511 if face_up else 1512, boil=0.9)
        if face_up:
            paint_text(cv, "SIM", 0, 26, font="shrik", size=86, fill=P_["orange"], ink_w=5, shadow=(5, 5), seed=1513)
        else:
            paint_text(cv, "REAL", 0, 24, font="shrik", size=72, fill=(110, 110, 130), ink_w=5, shadow=(5, 5), seed=1514)
        cv.restore()
    cv.restore()
    paint_text(cv, "50 / 50", 960, 210, font="shrik", size=150, fill=P_["yellow"], ink_w=8, shadow=(10, 10), shadow_rgb=P_["magenta"], seed=1520,
               reveal=float(np.clip((t - 0.3) / 0.5, 0, 1)), stagger=0.06)
    paint_text(cv, "— NEIL deGRASSE TYSON, 2016", 960, 282, font="marker", size=36, fill=P_["cream"], ink_w=0, shadow=(3, 3), seed=1521, streaks=False,
               reveal=float(np.clip((t - 0.7) / 0.5, 0, 1)))
    if t > t_land + 0.3:
        paint_text(cv, "...IT LANDED ON ITS EDGE.", 960, 1030, font="londrina", size=64, fill=P_["acid"], ink_w=4.5, shadow=(5, 5), seed=1522,
                   reveal=float(np.clip((t - t_land - 0.3) / 0.5, 0, 1)), stagger=0.02)


# ------------------------------------------------------------------ E16–E20 the twist
def E16_zee_twist(cv, t, T, A):
    cam = dict(x=CAM_ZEE["x"], y=CAM_ZEE["y"], z=1.85 + 0.06 * t)
    sets.talkshow(cv, T, cam, host=Hh(A, t), guest=G(A, t))


def E17_host_why(cv, t, T, A):
    cam = dict(x=CAM_HOST["x"], y=CAM_HOST["y"], z=1.9)
    sets.talkshow(cv, T, cam, host=Hh(A, t), guest=G(A, t))


def E18_zee_alt(cv, t, T, A):
    cam = dict(x=CAM_ZEE["x"], y=CAM_ZEE["y"] + 10, z=2.15 + 0.05 * t)
    sets.talkshow(cv, T, cam, host=Hh(A, t), guest=G(A, t))


def E19_asteroid(cv, t, T, A):
    amp = 16 * (t / 1.5) ** 2
    cam = dict(x=(hsh(core.D * 1.3) - 0.5) * amp, y=(hsh(core.D * 2.1 + 5) - 0.5) * amp, z=1.0 + 0.08 * t)
    sets.cosmos(cv, T, cam, "deep", seed=1901, planet_xy=(2900, -900), extras=False)
    C = sets.Cam(cv, cam)
    with C.layer(1.0):
        px, py, pr = 960, 820, 230
        w.planet(cv, px, py, pr, P_["teal"], bands=[(-0.5, 0.25, P_["acid"]), (0.0, 0.2, P_["mint"]), (0.4, 0.2, P_["acid"])], seed=1902,
                 face=dict(look=(0.6, -0.9), smile=-0.4), crater=False)
        blob(cv, [(px + 170, py - 120), (px + 184, py - 92), (px + 170, py - 80), (px + 156, py - 92)], P_["teal"], w=3.5, seed=1903, boil=0.6, n=4)
        u = t / 1.5
        ax, ay = lerp(1780, 1160, u), lerp(-120, 600, u)
        sz = 0.8 + 1.3 * u
        for j in range(7):
            line(cv, [(ax + 20 * sz, ay - 20 * sz), (ax + (150 + j * 22) * sz, ay - (150 + j * 14) * sz)], (22 - j * 2.5) * sz, P_["orange"] if j % 2 else P_["yellow"],
                 seed=1910 + j, boil=2.5, n=2, taper=(0.1, 1.0), a=210)
        blob(cv, ell(ax, ay, 70 * sz, 62 * sz, n=11), P_["maroon"], w=6, seed=1920, boil=1.4,
             shade=lambda c: [dots(c, [(ax - 24 * sz + i * 26 * sz, ay + 10 * sz * (i % 2))], 10 * sz, P_["red"]) for i in range(3)])
        line(cv, [(ax - 40 * sz, ay - 26 * sz), (ax - 10 * sz, ay - 12 * sz)], 6, seed=1921, boil=0.6, n=2)
        line(cv, [(ax + 40 * sz, ay - 26 * sz), (ax + 10 * sz, ay - 12 * sz)], 6, seed=1922, boil=0.6, n=2)
    paint_text(cv, "THE ALTERNATIVE", 900, 170, font="shrik", size=100, fill=P_["yellow"], ink_w=7, shadow=(9, 9), shadow_rgb=P_["red"], seed=1930,
               reveal=float(np.clip((t - 0.1) / 0.5, 0, 1)), stagger=0.04)


def E20_host_brb(cv, t, T, A):
    cam = dict(x=CAM_HOST["x"], y=CAM_HOST["y"] + 10, z=1.75)
    sets.talkshow(cv, T, cam, host=Hh(A, t), guest=G(A, t))
    u = ease((t - 0.9) / 0.35)
    if u > 0:
        y = lerp(1300, 900, u)
        w.ribbon(cv, [(-200, y + 40), (500, y - 20), (1400, y + 30), (2150, y - 10)], 170, [P_["night"], P_["magenta"], P_["yellow"], P_["night"]], flow=t, seed=2010, wav=0.03)
        paint_text(cv, "WE'LL BE RIGHT BACK", 960, y + 30, font="londrina", size=84, fills=[P_["cream"], P_["yellow"]], ink_w=5, shadow=(6, 6), seed=2011)


# ------------------------------------------------------------------ E21 the reveal: cosmic Pong
def E21_button(cv, t, T, A):
    w.field(cv, P_["void"])
    w.stars(cv, 2101, (0, 0, W, H), n=260, big=10)
    zoom = ease((t - 0.3) / 1.2)
    size = lerp(1920, 150, zoom)
    XL, XR = 220, 1700
    contacts = [1.5, 1.7, 3.3, 4.9, 5.5]
    if t < 1.5:
        bx, by = 960, 540
    else:
        k = int(np.clip(np.searchsorted(contacts, t) - 1, 0, len(contacts) - 2))
        a, b = contacts[k], contacts[k + 1]
        f = np.clip((t - a) / (b - a), 0, 1)
        path = [960, XR - 105, XL + 105, XR - 105, XL - 400]
        bx = lerp(path[k], path[k + 1], f)
        by = 540 + 300 * math.sin(t * 2.2)
        if t > 7.4:
            bx, by = 960, 540
    respawn = t > 6.0
    show_ball = not (5.6 < t < 7.4)
    if zoom > 0.02:
        for side, x in ((-1, XL), (1, XR)):
            py = 540 + 0.8 * (by - 540) + (60 * math.sin(t * 3) if side < 0 else 0)
            if side < 0 and 5.0 < t < 5.6:
                py += 260
            a = int(255 * min(1, zoom * 1.5))
            blob(cv, rect_pts([(x - 26, py - 150), (x + 26, py - 150), (x + 26, py + 150), (x - 26, py + 150)], 3), P_["white"], w=5, seed=2110 + side, boil=0.8, n=2, a=a)
            cosmic_hand(cv, x + side * 100, py, 0.7, ang=0 if side < 0 else 180, seed=2115 + side, pose="fist", sleeve=P_["violet"] if side < 0 else P_["hotpink"])
        for k in range(13):
            sparkle(cv, 960, 80 + k * 76, 8, P_["white"], seed=2120 + k, w=2, a=int(200 * zoom))
        sc = "0 1" if t > 5.6 else "0 0"
        pixel_text(cv, sc[0], 780, 70, 16, P_["white"], int(255 * zoom)); pixel_text(cv, sc[-1], 1100, 70, 16, P_["white"], int(255 * zoom))
    if show_ball:
        s = size if t < 1.5 else 150
        kpop = 1.0 if not (7.4 <= t < 7.8) else pop(t, 7.4, 0.35)
        s *= kpop
        k = s / W
        if k > 0.01:
            cv.save(); cv.translate(bx, by)
            if s < 1900:
                for j in range(4, 0, -1):
                    cv.drawRect(R(-s / 2 - j * 8, -s * 0.5625 / 2 - j * 8, s / 2 + j * 8, s * 0.5625 / 2 + j * 8), paint(P_["yellow"], 26))
            cv.clipPath(poly_path([(-s / 2, -s * 0.5625 / 2), (s / 2, -s * 0.5625 / 2), (s / 2, s * 0.5625 / 2), (-s / 2, s * 0.5625 / 2)]), doAntiAlias=True)
            cv.scale(k, k); cv.translate(-W / 2, -H / 2)
            old = core.INKMUL; core.INKMUL = old * max(0.06, k) ** -0.5
            sets.talkshow(cv, T, dict(x=0, y=0, z=1.0), host=Hh(A, t), guest=G(A, t))
            core.INKMUL = old
            cv.restore()
            if s < 1900:
                brush(cv, np.array([(bx - s / 2, by - s * 0.28), (bx + s / 2, by - s * 0.28), (bx + s / 2, by + s * 0.28), (bx - s / 2, by + s * 0.28)]), 5, P_["yellow"],
                      closed=True, seed=2130)
    if 5.6 < t < 7.4:
        paint_text(cv, "PLAYER 2 SCORES!", 960, 330, font="shrik", size=110, fill=P_["hotpink"], ink_w=7, shadow=(9, 9), seed=2140,
                   reveal=float(np.clip((t - 5.65) / 0.4, 0, 1)), stagger=0.04)
    if respawn and t < 7.6:
        prog = np.clip((t - 6.2) / 1.2, 0, 1)
        paint_text(cv, "RESPAWNING UNIVERSE...", 960, 760, font="londrina", size=64, fill=P_["cream"], ink_w=4, shadow=(5, 5), seed=2141)
        cv.drawRect(R(660, 800, 1260, 836), paint(INK, 200))
        cv.drawRect(R(666, 806, 666 + 588 * prog, 830), paint(P_["acid"]))
    if 5.5 < t < 7.2:
        alien(cv, 1760, 1120, 0.75, yawn=0.0, blink=0.0, press=0.0, seed=2150, chew=0.0, look=(-0.9, -0.3))


def E22_endcard(cv, t, T, A):
    w.field(cv, P_["magenta"])
    w.sunburst(cv, 960, 420, 2000, 26, [P_["hotpink"], P_["magenta"]], rot_deg=t * 6, seed=2300)
    w.stars(cv, 2301, (0, 0, W, H), n=200, big=12)
    w.halo(cv, 960, 330, [320, 250, 180], [P_["violet"], P_["orange"], P_["yellow"]], seed=2302)
    paint_text(cv, "BOXED", 960, 390, font="shrik", size=220, fill=P_["yellow"], ink_w=9, shadow=(12, 12), shadow_rgb=P_["night"], seed=2310,
               reveal=float(np.clip(t / 0.8, 0, 1)), stagger=0.1, drips=1.0)
    if t > 0.6:
        paint_text(cv, "EPISODE 2 · ONE IN BILLIONS", 960, 505, font="londrina", size=58, fill=P_["cream"], ink_w=4, shadow=(5, 5), seed=2320,
                   reveal=float(np.clip((t - 0.6) / 0.7, 0, 1)), stagger=0.015)
    if t > 1.2:
        a = int(255 * min(1, (t - 1.2) / 0.5))
        for j, s in enumerate(["Adapted from Elon Musk's viral answer at Recode's Code Conference (2016),",
                               "built on Nick Bostrom's “Are You Living in a Computer Simulation?” (2003).",
                               "Tyson's 50/50: Isaac Asimov Memorial Debate, AMNH, 2016."]):
            paint_text(cv, s, 960, 592 + j * 44, font="londrina_r", size=33, fill=P_["white"], ink_w=0, shadow=(3, 3), shadow_rgb=P_["night"], seed=2330 + j,
                       wobble=0.5, rot_jit=1.2, base_jit=2, streaks=False, a=a)
        paint_text(cv, "original characters · synthesized voices", 960, 742, font="marker", size=30, fill=P_["yellow"], ink_w=0, shadow=(3, 3),
                   shadow_rgb=P_["night"], seed=2334, wobble=0.6, streaks=False, a=a)
    if t > 3.0:
        paint_text(cv, "STAY BOXED.", 960, 900, font="shrik", size=104, fill=P_["acid"], ink_w=7, shadow=(9, 9), shadow_rgb=P_["night"], seed=2340,
                   reveal=float(np.clip((t - 3.0) / 0.6, 0, 1)), stagger=0.06)
    draw_zee(cv, dict(x=240, y=1110, s=0.62, legs=True, aR_sh=-60 + 14 * math.sin(t * 9), aR_el=-40, aR_pose="open", smile=0.7, px=0.3,
                      antL=(4 * math.sin(t * 3), 0), antR=(4 * math.sin(t * 3 + 1), 0)))
    draw_host(cv, dict(x=1690, y=1120, s=0.6, legs=True, aL_sh=-120 - 14 * math.sin(t * 8), aL_el=40, aL_pose="open", smile=0.7, px=-0.3))

