"""BOXED shot helpers (episode 1 lineage): easing, prop drawings for the performers (pages, a jar, a small box), the
standard positions/cameras for the talk-show set, lower-third name tags, ribbon wipes, a thought bubble and the
cosmic brain."""
import math
import numpy as np
import skia
from .core import (PAL, INK, W, H, paint, poly_path, cr_closed, cr_open, ell, blob, line, brush, dots, hsh, mix, jit, rot,
                   stipple, sparkle, rect_pts)
from . import core
from . import world as w
from .letters import paint_text

P_ = PAL
HOST_POS = dict(x=640, y=930, s=0.78, legs=False)
GUEST_POS = dict(x=1350, y=975, s=0.72, legs=False)
CAM_ZEE = dict(x=390, y=40, z=1.85)
CAM_HOST = dict(x=-320, y=-20, z=1.85)


def ease(x):
    x = min(max(float(x), 0.0), 1.0)
    return x * x * (3 - 2 * x)


def pop(t, t0, dur=0.35):
    """0 before t0, then a springy back-out 0 -> 1 over dur seconds."""
    k = (t - t0) / dur
    if k <= 0:
        return 0.0
    if k >= 1:
        return 1.0
    c1 = 1.9
    c3 = c1 + 1
    return 1 + c3 * (k - 1) ** 3 + c1 * (k - 1) ** 2


def lerp(a, b, u):
    return a + (b - a) * u


def page(cv, cx, cy, wd, ht, ang=0.0, seed=0, stack=0, stamp=0.0, lines=True, fill=None):
    """A sheet of cream paper (optionally a stack behind it, a red stamp) centred at cx, cy, rotated ang degrees."""
    cv.save()
    cv.translate(cx, cy)
    cv.rotate(ang)
    for k in range(int(stack), 0, -1):
        off = k * 7
        blob(cv, rect_pts([(-wd / 2 + off, -ht / 2 + off), (wd / 2 + off, -ht / 2 + off), (wd / 2 + off, ht / 2 + off), (-wd / 2 + off, ht / 2 + off)], 3),
             mix(P_["cream"], P_["cream_sh"], 0.4), w=4, seed=seed + 20 + k, boil=0.8, n=3)
    blob(cv, rect_pts([(-wd / 2, -ht / 2), (wd / 2, -ht / 2), (wd / 2, ht / 2), (-wd / 2, ht / 2)], 3), fill or P_["cream"], w=5, seed=seed, boil=0.9, n=3,
         shade=lambda c: stipple(c, P_["cream_sh"], (-wd / 2, -ht / 2, wd / 2, ht / 2), spacing=11, r=1.4, seed=seed + 1,
                                 fn=lambda X, Y: np.clip((X + Y) / (wd + ht) + 0.1, 0, 1) * 0.7))
    if lines:
        for k in range(int((ht - 50) / 22)):
            y = -ht / 2 + 30 + k * 22
            L = wd * (0.55 + 0.3 * float(hsh(seed + k * 1.7)))
            line(cv, [(-wd / 2 + 22, y), (-wd / 2 + 22 + L * 0.5, y + 2 * math.sin(k)), (-wd / 2 + 22 + L, y)], 2.4, mix(INK, P_["cream"], 0.35),
                 seed=seed + 5 + k, boil=0.8, n=4, taper=(0.1, 0.2))
    if stamp > 0.01:
        k = pop(stamp, 0.0, 0.5)
        cv.save(); cv.rotate(-14); cv.scale(k, k)
        blob(cv, ell(0, 10, wd * 0.36, ht * 0.16, n=12), None, w=6, ink=P_["red"], seed=seed + 40, boil=1.0)
        paint_text(cv, "REAL?", 0, 26, font="bangers", size=46, fill=P_["red"], ink_w=0, shadow=None, seed=seed + 41, streaks=False)
        cv.restore()
    cv.restore()


def jar(cv, x, y, s, seed=0, t=0.0):
    """A glass jar with a little pink brain floating in green goo (s = jar radius)."""
    hw, ht = s * 1.0, s * 1.5
    body = [(x - hw, y - ht), (x + hw, y - ht), (x + hw * 1.05, y + ht * 0.8), (x + hw * 0.8, y + ht), (x - hw * 0.8, y + ht), (x - hw * 1.05, y + ht * 0.8)]
    blob(cv, body, mix(P_["mint"], P_["acid"], 0.3), w=5, seed=seed, boil=0.9, n=4, a=235,
         shade=lambda c: [dots(c, [(x + hw * 0.6 * math.sin(k * 2.3 + t), y + ht - ((t * 30 + k * 23) % (ht * 1.8)))], 3 + k % 3, P_["white"], a=150) for k in range(6)])
    bob = 4 * math.sin(t * 1.7)
    blob(cv, ell(x, y + bob, hw * 0.62, hw * 0.48, n=10), P_["hotpink"], w=4, seed=seed + 2, boil=0.8,
         shade=lambda c: [line(c, [(x - hw * 0.4 + k * hw * 0.2, y + bob - hw * 0.3), (x - hw * 0.3 + k * hw * 0.2, y + bob + hw * 0.1)], 2.4,
                               P_["magenta"], seed=seed + 3 + k, boil=0.6, n=3) for k in range(5)])
    blob(cv, rect_pts([(x - hw * 1.1, y - ht - s * 0.3), (x + hw * 1.1, y - ht - s * 0.3), (x + hw * 1.1, y - ht + 4), (x - hw * 1.1, y - ht + 4)], 3),
         P_["gold"], w=4.5, seed=seed + 4, boil=0.6, n=3)
    line(cv, [(x - hw * 0.7, y - ht * 0.7), (x - hw * 0.75, y + ht * 0.5)], 6, P_["white"], seed=seed + 5, boil=0.5, n=3, a=120)


def small_box(cv, cx, cy, wdt, seed=0, t=0.0, blob_k=1.0):
    """A small open cardboard box with a tiny glowing simulated world peeking out."""
    if blob_k > 0.02:
        r = wdt * 0.22 * blob_k
        cv.drawCircle(cx, cy - wdt * 0.3, r * 1.8, paint(P_["yellow"], 50))
        blob(cv, ell(cx, cy - wdt * 0.28 - 6 * math.sin(t * 2), r, r, n=10), P_["teal"], w=4, seed=seed + 50, boil=0.8,
             shade=lambda c: c.drawPath(poly_path(ell(cx - r * 0.3, cy - wdt * 0.28, r * 0.7, r * 0.4, n=8)), paint(P_["acid"])))
        for side in (-1, 1):
            dots(cv, [(cx + side * r * 0.32, cy - wdt * 0.3 - 6 * math.sin(t * 2))], r * 0.12 + 1, INK)
    w.box(cv, cx, cy, wdt, wdt * 0.62, seed=seed, open_amt=0.9, ink=4.5)


def guest_prop(g, t, extra=None):
    kind = g.get("prop")
    extra = extra or {}
    if not kind:
        g["prop"] = None
        return g
    if callable(kind):                      # a ready-made prop function fn(cv, hands): keep it
        return g

    def fn(cv, hands):
        (lx, ly, la), (rx, ry, ra) = hands["aL"], hands["aR"]
        cx, cy = (lx + rx) / 2, (ly + ry) / 2
        ang = math.degrees(math.atan2(ry - ly, rx - lx))
        k = g.get("prop_k", 1.0)
        if kind == "paper":
            page(cv, cx, cy + 10, max(150, abs(rx - lx) + 20) * (0.6 + 0.4 * k), 200 * (0.6 + 0.4 * k), ang * 0.6, seed=7700,
                 stack=extra.get("stack", 0), stamp=extra.get("stamp", 0.0))
        elif kind == "jar":
            jar(cv, cx, cy - 20, 70 * (0.5 + 0.5 * k), seed=7800, t=t)
        elif kind == "box":
            small_box(cv, cx, cy + 30, 150, seed=7900, t=t, blob_k=extra.get("blob_k", 1.0))
    g["prop"] = fn
    return g


def host_prop(h, t):
    kind = h.get("prop")
    if not kind:
        h["prop"] = None
        return h
    if callable(kind):
        return h

    def fn(cv, hands):
        (lx, ly, la), (rx, ry, ra) = hands["aL"], hands["aR"]
        if kind == "card":
            page(cv, rx + 20, ry - 96, 170, 226, -8, seed=8100)
        elif kind == "card2":
            page(cv, (lx + rx) / 2, (ly + ry) / 2 - 20, max(190, abs(rx - lx) + 30), 240, 0, seed=8200)
    h["prop"] = fn
    return h


def G(A, t, **kw):
    g = dict(A["GUEST"]); g.update(GUEST_POS); g.update(kw)
    return guest_prop(g, t, kw.get("_extra"))


def Hh(A, t, **kw):
    h = dict(A["HOST"]); h.update(HOST_POS); h.update(kw)
    return host_prop(h, t)


# ------------------------------------------------------------------ overlays
def tag(cv, text, sub, x, y, t, t0, t1, color, align="left", seed=0):
    k = pop(t, t0) * (1 - ease((t - (t1 - 0.3)) / 0.3))
    if k <= 0.01:
        return
    cv.save(); cv.translate(x, y); cv.scale(k, k)
    wdt = 380
    sx = 1 if align == "left" else -1
    pts = [(0, -54), (sx * wdt, -66), (sx * (wdt + 30), 22), (0, 30)]
    blob(cv, pts, color, w=5.5, seed=seed, boil=1.0, n=3, misreg=(3, 2))
    pts2 = [(sx * 34, 30), (sx * (wdt - 6), 24), (sx * (wdt - 16), 76), (sx * 26, 80)]
    blob(cv, pts2, P_["night"], w=4.5, seed=seed + 1, boil=0.9, n=3)
    paint_text(cv, text, sx * (wdt + 15) / 2, 6, font="londrina", size=64, fill=P_["cream"], ink_w=5, shadow=(5, 5), seed=seed + 2,
               reveal=min(1.0, max(0.0, (t - t0) / 0.5)), stagger=0.06)
    paint_text(cv, sub, sx * (wdt + 10) / 2, 64, font="marker", size=27, fill=P_["cream"], ink_w=0, shadow=(2, 2), shadow_rgb=INK,
               seed=seed + 3, wobble=0.6, streaks=False)
    cv.restore()


def ribbon_wipe(cv, u, seed=0):
    """Full-frame striped ribbon sweeping left->right; u in [0,1], covers the frame around u=0.5."""
    x = lerp(-1500, W + 1500, u)
    pts = [(x - 900, H + 300), (x - 300, H * 0.6), (x + 200, H * 0.4), (x + 900, -300)]
    w.ribbon(cv, pts, 1500, [P_["magenta"], P_["orange"], P_["yellow"], P_["teal"], P_["violet"], P_["acid"]], flow=u * 6, seed=seed, wav=0.08)


def thought_bubble(cv, x, y, rx, ry, seed=0, a=255, fill=None):
    pts = []
    n = 14
    for k in range(n):
        ang = k / n * 2 * math.pi
        bump = 1.0 + 0.12 * math.sin(ang * 5 + seed)
        pts.append((x + rx * bump * math.cos(ang), y + ry * bump * math.sin(ang)))
    blob(cv, pts, fill or P_["white"], w=6, seed=seed, boil=1.2, n=6, a=a)
    for k, (dx, dy, r) in enumerate(((-rx * 0.75, ry * 1.05, 26), (-rx * 0.95, ry * 1.45, 16))):
        blob(cv, ell(x + dx, y + dy, r, r * 0.8, n=8), fill or P_["white"], w=4.5, seed=seed + 5 + k, boil=0.8, a=a)
    return poly_path(cr_closed(jit(pts, 0.0, seed), 6))


def cosmic_brain(cv, x, y, s, t=0.0, seed=0):
    """A pink brain with orbiting planets and sparkles."""
    pts = []
    for k in range(14):
        a = k / 14 * 2 * math.pi
        r = 1 + 0.08 * math.sin(a * 7 + seed)
        pts.append((x + 150 * s * r * math.cos(a), y + 110 * s * r * math.sin(a)))
    blob(cv, pts, P_["hotpink"], w=6, seed=seed, boil=1.2, n=6,
         shade=lambda c: [line(c, [(x + 120 * s * math.cos(k), y + 80 * s * math.sin(k * 1.3)), (x + 40 * s * math.cos(k + 1), y + 30 * s * math.sin(k)),
                                   (x + 100 * s * math.cos(k + 2), y + 70 * s * math.sin(k + 2))], 3.0, P_["magenta"], seed=seed + 3 + k, boil=0.8, n=4)
                          for k in range(7)])
    line(cv, [(x, y - 104 * s), (x + 6 * s, y), (x, y + 100 * s)], 3.5, P_["magenta"], seed=seed + 20, boil=0.8, n=4)
    for k in range(3):
        a = t * (0.8 + 0.3 * k) + k * 2.1
        px, py = x + 230 * s * math.cos(a), y + 70 * s * math.sin(a)
        w.planet(cv, px, py, (16 + 8 * k) * s, [P_["acid"], P_["teal"], P_["orange"]][k], seed=seed + 30 + k, crater=False)
    for k in range(5):
        sparkle(cv, x + 220 * s * math.cos(k * 1.3 + 0.5), y - 140 * s + 40 * s * math.sin(k * 2.1), 10 * s + 4, P_["yellow"], seed=seed + 40 + k)
