"""BOXED ep4 'THE CAVE' -- owner 'return'.

  T036_remembers  Gary in the sunshine remembers his chained friends, feels sorry for them, walks back down; 'A hero!'
  T038_mocked     the prisoners laugh at him; a mocking X-eyed shadow puppet; NOPE.
  T040_kill_him   it gets darker: the fire turns blood red, the shadows swell into monsters, the lantern goes out.
  T042_socrates   Athens as a psychedelic Greek vase painting: Socrates' questions, the trial, the hemlock cup.
"""
from .shots_ep4_base import *          # noqa: F401,F403
from .zee import _hand
import math
import numpy as np
import skia


# ===================================================================== small utilities
def clamp01(x):
    return max(0.0, min(1.0, float(x)))


def seg(t, t0, t1):
    """0..1 progress of t through [t0, t1] (clamped)."""
    return clamp01((t - t0) / max(1e-6, t1 - t0))


def eseg(t, t0, t1):
    return ease(seg(t, t0, t1))


def shake(amp, seed=0, f=1.0):
    """Per-drawing camera jolt (dx, dy)."""
    return ((float(hsh(core.D * 1.37 * f + seed)) - 0.5) * 2 * amp, (float(hsh(core.D * 2.11 * f + seed + 7)) - 0.5) * 2 * amp)


def grad_rect(cv, rect, p0, p1, cols, pos=None, a=255):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(*p0), skia.Point(*p1)], [core.C(c, a) for c in cols], pos))
    cv.drawRect(R(*rect), p)


def rad_rect(cv, rect, cx, cy, r, cols, pos=None, a=255):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(cx, cy), max(1.0, r), [core.C(c, a) for c in cols], pos))
    cv.drawRect(R(*rect), p)


def glow(cv, x, y, r, rgb, a=160, mid=0.4):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(x, y), max(1.0, r), [core.C(rgb, a), core.C(rgb, int(a * mid)), core.C(rgb, 0)], [0.0, 0.45, 1.0]))
    cv.drawCircle(x, y, r, p)


def tint(cv, rgb, a):
    if a > 0:
        cv.drawRect(R(-60, -60, W + 60, H + 60), paint(rgb, int(min(255, a))))


def wedge_rays(cv, x, y, r, n, rgb, a, rot_deg=0.0, frac=0.5):
    """Translucent god-ray wedges radiating from x, y."""
    p = paint(rgb, int(a))
    for k in range(n):
        a1 = math.radians(rot_deg + k * 360.0 / n)
        a2 = a1 + math.radians(360.0 / n * frac)
        cv.drawPath(poly_path([(x, y), (x + r * math.cos(a1), y + r * math.sin(a1)), (x + r * math.cos(a2), y + r * math.sin(a2))]), p)


class Ink:
    """Context manager: multiply the pen weight (core.INKMUL) while drawing a scaled sub-scene."""
    def __init__(self, k):
        self.k = k

    def __enter__(self):
        self.old = core.INKMUL
        core.INKMUL = self.old * self.k

    def __exit__(self, *a):
        core.INKMUL = self.old


def silhouette(cv, draw_fn, rgb, rim=None, rim_off=(0, 0), a=255):
    """Draw draw_fn(cv) flattened to one colour (a cut-out silhouette), optionally with an offset rim-light copy first."""
    for col, off in (((rim, rim_off),) if rim is not None else ()) + ((rgb, (0, 0)),):
        cv.saveLayer(None, None)
        cv.translate(*off)
        draw_fn(cv)
        cv.translate(-off[0], -off[1])
        q = skia.Paint(AntiAlias=True, Color=core.C(col, a))
        q.setBlendMode(skia.BlendMode.kSrcIn)
        cv.drawRect(R(-400, -400, W + 400, H + 400), q)
        cv.restore()


def qmark(cv, x, y, s, rgb, seed=0, rot_deg=0.0, a=255, txt="?"):
    """A chunky hand-painted question mark (ink outline + shadow), baseline-centred at x, y."""
    cv.save(); cv.translate(x, y); cv.rotate(rot_deg)
    paint_text(cv, txt, 0, 0, font="shrik", size=110 * s, fill=rgb, ink_w=4.5 if s > 0.5 else 3.0, shadow=(4 * s + 1, 4 * s + 1), seed=seed, streaks=False,
               rot_jit=0.0, a=a)
    cv.restore()


def sparkles(cv, x, y, rx, ry, n, T, seed=0, cols=None, size=12, a=255):
    cols = cols or [P_["yellow"], P_["white"], P_["cream"]]
    for k in range(n):
        ph = (T * (0.6 + 0.3 * hsh(seed + k)) + hsh(seed + k * 3.7)) % 1.0
        if ph > 0.75:
            continue
        sx = x + (hsh(seed + k * 5.1) - 0.5) * 2 * rx
        sy = y + (hsh(seed + k * 7.3) - 0.5) * 2 * ry
        sparkle(cv, sx, sy, size * (0.6 + 0.6 * hsh(seed + k * 9.1)) * math.sin(ph / 0.75 * math.pi), cols[k % len(cols)], w=2.2, seed=seed + k, a=a)


# ===================================================================== GARY (extended rig, on-model with eyeball_creature)
LIDS = {                       # lower edge of the violet upper lid: (left, middle, right) in eye radii from the eye centre (-1 = top)
    "neutral": (-0.13, -0.80, -0.13),
    "happy": (-0.25, -0.92, -0.25),
    "sad": (0.10, -0.50, 0.10),
    "sadder": (0.22, -0.30, 0.22),
    "resolve": (-0.62, -0.30, -0.62),
    "dazed": (-0.05, -0.38, -0.62),
    "wide": (-0.40, -1.05, -0.40),
    "closed": (1.2, 1.2, 1.2),
}


def lid_mix(a, b, u):
    A = LIDS[a] if isinstance(a, str) else a
    Bv = LIDS[b] if isinstance(b, str) else b
    return tuple(A[i] + (Bv[i] - A[i]) * u for i in range(3))


def _limb_elbow(p0, p1, side, s, bend=1.0):
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = p1 - p0
    L = float(np.hypot(*d)) + 1e-6
    nrm = np.array([-d[1], d[0]]) / L
    if nrm[0] * side < 0:
        nrm = -nrm
    k = max(0.0, 150 * s - L * 0.5) * 0.55 + 14 * s
    return p0 + d * 0.5 + nrm * k * bend


def gary_x(cv, x, y, s, T, seed=4400, loud=None, look=(0.0, 0.0), pupil="dot", pk=1.0, lids="neutral", mouth="auto", tear=0.0,
           armL="hang", armR="hang", legs=None, bob=None, iris_art=None, wet=0.0, scarf=None, sweat=0.0, glint=0.0, body=True, mouth_k=1.0):
    """Gary with expressions. x, y = centre of his eye (as eyeball_creature); his sweater hangs ~360*s below.
    lids: LIDS key or (l, m, r) tuple.  pupil: dot | spiral | x | pin.  mouth: auto (talk/smile) | smile | frown | wobble | line | grin | o.
    armL/armR: 'hang' or (hx, hy, ang, pose) in s-units relative to (x, y).  legs: None | 'stand' | 'sit' | ('walk', phase).
    iris_art(c, ex, ey, ir): draws inside the iris (clipped).  scarf: dict(flow, dir, len) -> cape-like striped scarf."""
    loud = spk_loud("AUD", T) if loud is None else loud
    bob = 6 * math.sin(T * 3.1) * s if bob is None else bob * s
    R0 = 150 * s
    ey0 = y + bob
    if scarf is not None:                                          # the cape tail flies behind everything
        _scarf_tail(cv, x, y, s, T, scarf, seed)
    if legs is not None:
        _gary_legs(cv, x, y, s, T, legs, seed)
    if body:
        blob(cv, [(x - 128 * s, y + 360 * s), (x - 110 * s, y + 170 * s), (x - 55 * s, y + 112 * s), (x + 55 * s, y + 112 * s), (x + 110 * s, y + 170 * s),
                  (x + 128 * s, y + 360 * s)], P_["cream"], w=5, seed=seed, boil=1.0, n=6,
             shade=lambda c: ([c.drawRect(R(x - 140 * s, y + (232 + k * 46) * s, x + 140 * s, y + (250 + k * 46) * s), paint(P_["orange"])) for k in range(3)],
                              c.drawPath(poly_path(cr_closed([(x + 60 * s, y + 110 * s), (x + 140 * s, y + 170 * s), (x + 150 * s, y + 380 * s), (x + 80 * s, y + 380 * s)], 3)),
                                         paint(P_["cream_sh"], 120))))
        paint_text(cv, "G", x, y + 300 * s, font="shrik", size=76 * s, fill=P_["red"], ink_w=4 if s > 0.4 else 2.5, shadow=None, seed=seed + 30, streaks=False)
    L = LIDS[lids] if isinstance(lids, str) else lids
    ir = 66 * s
    ex, ey = x - 4 * s + look[0] * 30 * s, ey0 - 22 * s + look[1] * 26 * s
    pr = ir * (0.42 + 0.22 * min(1.0, loud)) * pk

    def eye_shade(c):
        for k, a in enumerate(np.linspace(0, 6.0, 8)):              # veins
            line(c, [(x + R0 * math.cos(a), ey0 + R0 * math.sin(a)), (x + R0 * 0.66 * math.cos(a + 0.25), ey0 + R0 * 0.66 * math.sin(a + 0.25))],
                 3.5, P_["red"], seed=seed + 10 + k, boil=0.8, n=3)
        c.drawPath(poly_path(cr_closed(ell(x + R0 * 0.25, ey0 + R0 * 0.3, R0 * 0.95, R0 * 0.85, n=12), 3)), paint((236, 226, 236), 110))

        def iris_sh(c2):
            c2.drawPath(poly_path(cr_closed(ell(ex + 10 * s, ey + 12 * s, ir * 0.8, ir * 0.75, n=8), 4)), paint(P_["tealdk"]))
            if iris_art is not None:
                iris_art(c2, ex, ey, ir)
        blob(c, ell(ex, ey, ir, ir, n=11), P_["teal"], w=4.5, seed=seed + 5, boil=0.8, shade=iris_sh)
        if pupil == "spiral":
            ang0 = T * 7.0
            pts = [(ex + (u * ir * 0.12) * math.cos(ang0 + u), ey + (u * ir * 0.12) * math.sin(ang0 + u)) for u in np.linspace(0.3, 7.2, 40)]
            line(c, pts, 5.5 * min(1.0, s * 1.2) + 1.5, INK, seed=seed + 6, boil=0.4, n=3, taper=(0.1, 0.1))
        elif pupil == "x":
            for d in (-1, 1):
                line(c, [(ex - ir * 0.45, ey - d * ir * 0.45), (ex + ir * 0.45, ey + d * ir * 0.45)], 9 * s + 2, INK, seed=seed + 6 + d, boil=0.5, n=2, taper=(0.1, 0.1))
        else:
            prr = pr * (0.45 if pupil == "pin" else 1.0)
            blob(c, ell(ex, ey, prr, prr, n=9), INK, w=0, seed=seed + 6, boil=0.5, misreg=(0, 0))
            dots(c, [(ex - prr * 0.45, ey - prr * 0.5)], prr * 0.28 + 1, P_["white"])
            if wet > 0:
                dots(c, [(ex + prr * 0.5, ey + prr * 0.45)], prr * 0.16 + 0.8, P_["white"], a=int(255 * wet))
                c.drawPath(poly_path(cr_closed(ell(ex, ey + ir * 0.62, ir * 0.7, ir * 0.12, n=8), 3)), paint(P_["white"], int(150 * wet)))
        if glint > 0:
            sparkle(c, ex - ir * 0.55, ey - ir * 0.6, 26 * s * glint, P_["white"], w=2.5, seed=seed + 7)
        # upper lid (violet) -- its lower edge carries the expression
        hl, hm, hr = (v * R0 for v in L)
        edge = [(x - R0 * 1.15, ey0 + hl), (x - R0 * 0.55, ey0 + (hl + hm) * 0.5 - (hm - min(hl, hr)) * 0.12), (x, ey0 + hm),
                (x + R0 * 0.55, ey0 + (hr + hm) * 0.5 - (hm - min(hl, hr)) * 0.12), (x + R0 * 1.15, ey0 + hr)]
        lid = [(x - R0 * 1.3, ey0 - R0 * 1.4), (x + R0 * 1.3, ey0 - R0 * 1.4)] + edge[::-1]
        c.drawPath(poly_path(cr_closed(jit(lid, 0.8 * s + 0.3, seed + 8), 4)), paint(P_["violet"]))
        c.drawPath(poly_path(cr_closed(jit([(x - R0 * 1.3, ey0 - R0 * 1.4), (x + R0 * 1.3, ey0 - R0 * 1.4), (x + R0 * 1.2, ey0 - R0 * 0.75),
                                            (x - R0 * 1.2, ey0 - R0 * 0.75)], 0.5, seed + 9), 3)), paint(P_["lilac"], 70))
        line(c, edge, 5.5 * min(1.0, s * 1.3) + 1.0, INK, seed=seed + 11, boil=0.8, n=6, taper=(0.05, 0.05))

    blob(cv, ell(x, ey0, R0, R0, n=14), P_["white"], w=6, seed=seed + 4, boil=1.2, shade=eye_shade)
    if scarf is not None:
        _scarf_knot(cv, x, y, s, T, scarf, seed)
    mx, my = x + 6 * s, ey0 + 92 * s                               # mouth, on the white under the iris
    mo = min(1.0, loud * 1.5) * mouth_k
    m = mouth
    if m == "auto":
        m = "talk" if mo > 0.08 else "smile"
    if m == "talk" or (m in ("frown", "wobble", "line") and mo > 0.1):
        mh = (5 + 30 * max(mo, 0.15)) * s
        blob(cv, ell(mx, my + mh * 0.3, 34 * s, mh, n=10), P_["mouth"], w=4.5, seed=seed + 40, boil=0.7,
             shade=lambda c: blob(c, ell(mx + 4 * s, my + mh * 1.1, 22 * s, mh * 0.6, n=8), P_["tongue"], w=0, seed=seed + 41, boil=0.5, misreg=(0, 0)))
    elif m == "smile":
        line(cv, [(mx - 30 * s, my - 4 * s), (mx, my + 8 * s), (mx + 30 * s, my - 4 * s)], 4.5, seed=seed + 42, boil=0.6, n=6, taper=(0.3, 0.3))
    elif m == "frown":
        line(cv, [(mx - 28 * s, my + 8 * s), (mx, my - 5 * s), (mx + 28 * s, my + 8 * s)], 4.5, seed=seed + 42, boil=0.6, n=6, taper=(0.3, 0.3))
    elif m == "wobble":
        line(cv, [(mx - 28 * s, my + 6 * s), (mx - 14 * s, my - 2 * s), (mx, my + 3 * s), (mx + 14 * s, my - 3 * s), (mx + 28 * s, my + 6 * s)], 4.5,
             seed=seed + 42, boil=0.9, n=5, taper=(0.3, 0.3))
    elif m == "line":
        line(cv, [(mx - 26 * s, my + 2 * s), (mx, my + 1 * s), (mx + 26 * s, my)], 5.0, seed=seed + 42, boil=0.5, n=4, taper=(0.2, 0.2))
    elif m == "grin":
        gp = [(mx - 44 * s, my - 6 * s), (mx + 44 * s, my - 6 * s), (mx + 30 * s, my + 22 * s), (mx, my + 34 * s), (mx - 30 * s, my + 22 * s)]
        blob(cv, gp, P_["mouth"], w=4.5, seed=seed + 43, boil=0.7, n=5,
             shade=lambda c: (c.drawRect(R(mx - 50 * s, my - 10 * s, mx + 50 * s, my + 3 * s), paint(P_["white"])),
                              blob(c, ell(mx + 4 * s, my + 30 * s, 22 * s, 12 * s, n=8), P_["tongue"], w=0, seed=seed + 44, boil=0.5, misreg=(0, 0))))
    elif m == "o":
        blob(cv, ell(mx, my + 6 * s, 13 * s, 17 * s, n=9), P_["mouth"], w=4, seed=seed + 45, boil=0.6)
    if tear > 0:                                                   # a tear wells at the lid corner and rolls down the side of the eyeball
        for side in ((1,) if tear < 0.6 else (1, -1)):
            hc = L[2] if side > 0 else L[0]
            u = clamp01(tear * 1.25 - (0.0 if side > 0 else 0.6))
            if u <= 0:
                continue
            a0 = math.asin(max(-0.9, min(0.9, hc + 0.1)))           # angle down from the equator of the lid corner
            a1 = math.radians(62)
            grow = clamp01(u / 0.3)
            roll = clamp01((u - 0.3) / 0.7) ** 1.6
            ang = a0 + (a1 - a0) * roll
            rr0 = R0 * 1.0
            tx = x + side * rr0 * math.cos(ang)
            ty = ey0 + rr0 * math.sin(ang)
            rr = (6 + 9 * grow) * s + 1.5
            if roll > 0.05:                                          # wet trail
                trail = [(x + side * rr0 * math.cos(a), ey0 + rr0 * math.sin(a)) for a in np.linspace(a0, ang, 6)]
                line(cv, trail, 7 * s + 1.5, P_["mint"], seed=seed + 75 + side, boil=0.4, n=3, taper=(0.4, 0.1), a=170)
            blob(cv, [(tx + side * rr * 0.3, ty - rr * 1.9), (tx + rr, ty), (tx, ty + rr * 1.05), (tx - rr, ty)], P_["mint"], w=3.0, seed=seed + 70 + side, boil=0.5, n=4,
                 shade=lambda c, tx=tx, ty=ty, rr=rr: dots(c, [(tx - rr * 0.3, ty - rr * 0.2)], rr * 0.25 + 0.5, P_["white"]))
    if sweat > 0:
        for k in range(2):
            ph = (T * 1.3 + k * 0.5) % 1.0
            sx = x + (1 if k == 0 else -1) * R0 * 0.95
            sy = ey0 - R0 * 0.55 + ph * R0 * 0.5
            blob(cv, [(sx, sy - 16 * s), (sx + 8 * s, sy + 2 * s), (sx, sy + 9 * s), (sx - 8 * s, sy + 2 * s)], P_["mint"], w=3, seed=seed + 80 + k, boil=0.5, n=4,
                 a=int(255 * sweat * (1 - ph)))
    for side, spec in ((-1, armL), (1, armR)):
        _gary_arm(cv, x, y, s, T, side, spec, seed + 50 + (side + 1) * 10)


def _gary_arm(cv, x, y, s, T, side, spec, seed):
    if spec is None:
        return
    sh = (x + side * 104 * s, y + 190 * s)
    if spec == "hang":
        hx, hy = x + side * 140 * s, y + 330 * s
        el = (x + side * 150 * s, y + 250 * s)
        ang, pose = (90 - side * 10), "open"
    else:
        hx, hy, ang, pose = spec
        hx, hy = x + hx * s, y + hy * s
        el = tuple(_limb_elbow(sh, (hx, hy), side, s))
    tube(cv, [sh, el, (hx, hy)], 22 * s, P_["cream"], w=4.5, seed=seed, boil=0.8, n=8)
    cv.save(); cv.translate(hx, hy); cv.scale(s * 1.15, s * 1.15)
    _hand(cv, 0, 0, ang, pose, -1 if side > 0 else 1, seed + 2, rgb=P_["white"])
    cv.restore()


def _gary_legs(cv, x, y, s, T, legs, seed):
    jeans, shoe = P_["cream"], P_["red"]                         # cream legs + red sneakers: same Gary legs as the escape/out modules
    if legs == "sit":                                             # legs stuck out towards camera, shoe soles showing
        for side in (-1, 1):
            hx, hy = x + side * 62 * s, y + 352 * s
            fx, fy = x + side * 98 * s, y + 388 * s
            tube(cv, [(hx, hy - 10 * s), (fx, fy)], 34 * s, jeans, w=4.5, seed=seed + 90 + side, boil=0.7, n=4)
            blob(cv, ell(fx, fy, 38 * s, 30 * s, n=10, rot=side * 12), P_["white"], w=4.5, seed=seed + 92 + side, boil=0.6,
                 shade=lambda c, fx=fx, fy=fy: (c.drawPath(poly_path(cr_closed(ell(fx, fy, 38 * s, 30 * s, n=10), 3)), paint(shoe, stroke=10 * s + 1)),
                                                [c.drawLine(fx - 18 * s, fy - 12 * s + k * 9 * s, fx + 18 * s, fy - 12 * s + k * 9 * s, paint(mix(shoe, INK, 0.2), stroke=2.5 * s + 0.5))
                                                 for k in range(4)]))
        return
    if legs == "stand":
        mode, ph = "stand", 0.0
    else:
        mode, ph = legs[0], legs[1]
    for side in (-1, 1):
        hx, hy = x + side * 48 * s, y + 345 * s
        if mode == "walk":
            sw = math.sin(ph + (0 if side < 0 else math.pi))
            fx = x + side * 52 * s + sw * 46 * s
            fy = y + 478 * s - max(0.0, -math.cos(ph + (0 if side < 0 else math.pi))) * 30 * s
        elif mode == "dangle":                                     # sitting on a ledge, feet swinging
            fx = x + side * 56 * s
            fy = y + 462 * s - 16 * s * max(0.0, math.sin(ph + (0 if side < 0 else math.pi)))
        else:
            fx, fy = x + side * 62 * s, y + 478 * s
        kx = (hx + fx) / 2 + side * 10 * s
        ky = (hy + fy) / 2
        tube(cv, [(hx, hy), (kx, ky), (fx, fy - 18 * s)], 30 * s, jeans, w=4.5, seed=seed + 90 + side, boil=0.7, n=5)
        blob(cv, [(fx - 30 * s, fy), (fx - 26 * s, fy - 28 * s), (fx + 12 * s, fy - 30 * s), (fx + 40 * s * (1 if side > 0 else 0.6), fy - 10 * s),
                  (fx + 38 * s, fy + 6 * s), (fx - 28 * s, fy + 8 * s)], shoe, w=4.5, seed=seed + 94 + side, boil=0.6, n=4,
             shade=lambda c, fx=fx, fy=fy: c.drawRect(R(fx - 40 * s, fy - 2 * s, fx + 50 * s, fy + 12 * s), paint(P_["white"])))


def _scarf_pts(x, y, s, T, sc):
    flow = sc.get("flow", T * 3.0)
    dr = sc.get("dir", -1)
    Ln = sc.get("len", 520) * s
    nx, ny = x + dr * 60 * s, y + 170 * s
    pts = [(nx, ny)]
    for k in range(1, 7):
        u = k / 6
        pts.append((nx + dr * Ln * u, ny - 80 * s * u + math.sin(flow * 2.0 - u * 4.5) * 78 * s * u))
    return pts


def _scarf_tail(cv, x, y, s, T, sc, seed):
    pts = _scarf_pts(x, y, s, T, sc)
    w.ribbon(cv, pts, sc.get("wd", 104) * s, [P_["magenta"], P_["yellow"], P_["magenta"], P_["yellow"], P_["magenta"]], flow=sc.get("flow", T * 3.0), seed=seed + 120,
             ink=5.5, wav=0.07)


def _scarf_knot(cv, x, y, s, T, sc, seed):
    """The scarf wrapped round his neck (just under the eyeball) with a knot and a short dangling end."""
    blob(cv, [(x - 96 * s, y + 138 * s), (x - 30 * s, y + 160 * s), (x + 30 * s, y + 160 * s), (x + 96 * s, y + 138 * s), (x + 104 * s, y + 178 * s), (x + 30 * s, y + 200 * s),
              (x - 30 * s, y + 200 * s), (x - 104 * s, y + 180 * s)], P_["magenta"], w=4.5, seed=seed + 130, boil=0.8, n=4,
         shade=lambda c: [c.drawRect(R(x - 110 * s + k * 44 * s, y + 130 * s, x - 90 * s + k * 44 * s, y + 210 * s), paint(P_["yellow"])) for k in range(6)])
    sw = math.sin(sc.get("flow", T * 3.0) * 1.7) * 10 * s
    blob(cv, [(x + 40 * s, y + 180 * s), (x + 74 * s, y + 182 * s), (x + 80 * s + sw, y + 280 * s), (x + 50 * s + sw, y + 284 * s)], P_["magenta"], w=4, seed=seed + 132,
         boil=0.7, n=3, shade=lambda c: c.drawRect(R(x + 30 * s, y + 230 * s, x + 100 * s, y + 248 * s), paint(P_["yellow"])))
    blob(cv, ell(x + 56 * s, y + 182 * s, 22 * s, 18 * s, n=8), P_["magenta"], w=4, seed=seed + 134, boil=0.6)


# ===================================================================== bubbles
def cloud_bubble(cv, x, y, rx, ry, k, seed=0, tail_to=None, content=None, fill=None, ink=6.0):
    """Thought cloud popping in with scale k (0..1+). Puffs trail toward tail_to. content(cv) draws clipped inside."""
    if k <= 0.01:
        return
    fill = fill or P_["cream"]
    if tail_to is not None:
        tx, ty = tail_to
        for j, (u, r) in enumerate(((0.72, 30), (0.86, 20), (0.97, 12))):
            if k < 0.3 + 0.2 * j:
                continue
            px = x + (tx - x) * u
            py = y + (ty - y) * u
            blob(cv, ell(px, py, r, r * 0.84, n=8), fill, w=4.5, seed=seed + 7 + j, boil=0.8)
    cv.save(); cv.translate(x, y); cv.scale(k, k); cv.translate(-x, -y)
    pts = []
    n = 16
    for j in range(n):
        ang = j / n * 2 * math.pi
        bump = 1.0 + 0.1 * math.sin(ang * 6 + seed)
        pts.append((x + rx * bump * math.cos(ang), y + ry * bump * math.sin(ang)))
    P = blob(cv, pts, fill, w=0, seed=seed, boil=1.0, n=6, misreg=(0, 0))
    if content is not None:
        cv.save()
        clip = poly_path(cr_closed(ell(x, y, rx * 0.93, ry * 0.9, n=24), 2))
        cv.clipPath(clip, doAntiAlias=True)
        content(cv)
        p = skia.Paint(AntiAlias=True)                               # soft dreamy edge
        p.setShader(skia.GradientShader.MakeRadial(skia.Point(x, y), max(rx, ry) * 0.98, [core.C(fill, 0), core.C(fill, 0), core.C(fill, 235)], [0.0, 0.72, 1.0]))
        cv.save(); cv.translate(x, y); cv.scale(1.0, ry / rx); cv.translate(-x, -y)
        cv.drawCircle(x, y, rx, p)
        cv.restore()
        cv.restore()
    brush(cv, P, ink, closed=True, seed=seed + 3)
    cv.restore()


# ===================================================================== the sunny upper world
SUN_C = dict(base=P_["gold"], bands=[(-0.55, 0.2, P_["yellow"]), (-0.12, 0.16, P_["orange"]), (0.3, 0.22, P_["cream"])])


def sun_planet(cv, x, y, r, T, seed=7300, look=(-0.5, 0.35), smile=0.45, lids=0.45, rays=1.0, rot=0.0):
    """The sun = the show's ringed planet, glowing gold, sleepy face."""
    if rays > 0:
        wedge_rays(cv, x, y, r * 9, 18, P_["white"], 34 * rays, rot_deg=rot, frac=0.45)
        glow(cv, x, y, r * 3.4, P_["yellow"], a=int(170 * rays))
        glow(cv, x, y, r * 1.9, P_["white"], a=int(140 * rays))
        for k in range(3):
            rr = r * (1.28 + 0.22 * k + 0.03 * math.sin(T * 2 + k))
            cv.drawCircle(x, y, rr, paint(P_["cream"], int(70 * rays), stroke=6))
    w.planet(cv, x, y, r, SUN_C["base"], bands=SUN_C["bands"], ring=dict(rx=1.75, ry=0.33, rgb=P_["teal"], rgb2=P_["cream"], tilt=-16),
             face=dict(look=look, smile=smile, lids=lids, lid_rgb=P_["orange"]), seed=seed)


def sky_warm(cv, T, sx, sy, seed=7400):
    rad_rect(cv, (-400, -400, W + 400, H + 400), sx, sy, 1900, [(255, 250, 222), P_["yellow"], P_["gold"], P_["orange"], P_["hotpink"], (150, 60, 210)],
             [0.0, 0.1, 0.22, 0.42, 0.68, 1.0])
    wedge_rays(cv, sx, sy, 2600, 24, P_["white"], 26, rot_deg=T * 3.0, frac=0.5)
    for k in range(5):                                             # drifting psychedelic clouds
        cx = ((-300 + k * 520 + T * (14 + 5 * k)) % (W + 700)) - 350
        cy = 120 + 70 * k % 260 + 20 * math.sin(T * 0.4 + k)
        sc = 0.7 + 0.25 * (k % 3)
        cloud_puff(cv, cx, cy, sc, seed + k * 11)


def cloud_puff(cv, x, y, s, seed):
    pts = []
    for j in range(12):
        ang = j / 12 * 2 * math.pi
        bump = 1.0 + 0.22 * (math.sin(ang * 4 + seed) > 0.2)
        pts.append((x + 170 * s * bump * math.cos(ang), y + 60 * s * bump * math.sin(ang) - (18 * s if math.sin(ang) < 0 else 0)))
    blob(cv, pts, P_["cream"], w=4.5, seed=seed, boil=1.0, n=5,
         shade=lambda c: c.drawPath(poly_path(cr_closed(ell(x + 20 * s, y + 46 * s, 190 * s, 40 * s, n=10), 3)), paint(P_["hotpink"], 150)))


def daisy(cv, x, y, s, T, seed=0, petal=None, face=True):
    petal = petal or P_["white"]
    sway = 6 * s * math.sin(T * 1.8 + seed)
    line(cv, [(x, y), (x + sway * 0.5, y - 40 * s), (x + sway, y - 80 * s)], 6 * s + 1.5, P_["acid_dk"], seed=seed, boil=0.6, n=4, taper=(0, 0.2))
    cx, cy = x + sway, y - 84 * s
    for k in range(7):
        a = k / 7 * 2 * math.pi + seed
        blob(cv, ell(cx + 22 * s * math.cos(a), cy + 22 * s * math.sin(a), 15 * s, 10 * s, n=7, rot=math.degrees(a)), petal, w=3, seed=seed + k, boil=0.5)
    blob(cv, ell(cx, cy, 14 * s, 14 * s, n=8), P_["yellow"], w=3, seed=seed + 9, boil=0.5)
    if face and s > 0.55:
        dots(cv, [(cx - 5 * s, cy - 2 * s), (cx + 5 * s, cy - 2 * s)], 2.2 * s + 0.5, INK)


def lolly_tree(cv, x, y, s, T, seed=0, cols=None):
    cols = cols or [P_["hotpink"], P_["yellow"], P_["magenta"], P_["orange"]]
    line(cv, [(x, y), (x + 6 * s, y - 120 * s), (x, y - 220 * s)], 18 * s + 2, (120, 60, 50), seed=seed, boil=0.6, n=3, taper=(0, 0))
    cx, cy = x + 4 * s * math.sin(T + seed), y - 300 * s
    for k, c in enumerate(cols):
        rr = (110 - k * 26) * s
        blob(cv, ell(cx + k * 4 * s, cy - k * 3 * s, rr, rr * 0.95, n=12), c, w=4.5 if k == 0 else 3, seed=seed + 3 + k, boil=0.9)
    pts = [(cx + (u * 9 * s) * math.cos(u * 0.9 + T * 0.8), cy + (u * 9 * s) * math.sin(u * 0.9 + T * 0.8)) for u in np.linspace(0.5, 9.5, 26)]
    line(cv, pts, 4, INK, seed=seed + 9, boil=0.5, n=3, taper=(0.2, 0.2), a=160)


def butterfly(cv, x, y, s, T, seed=0, c1=None, c2=None):
    c1 = c1 or P_["magenta"]
    c2 = c2 or P_["yellow"]
    fl = abs(math.sin(T * 9 + seed)) * 0.8 + 0.2
    for side in (-1, 1):
        blob(cv, ell(x + side * 20 * s * fl, y - 10 * s, 20 * s * fl + 2, 18 * s, n=8, rot=side * 20), c1, w=3, seed=seed + side, boil=0.5)
        blob(cv, ell(x + side * 14 * s * fl, y + 12 * s, 13 * s * fl + 2, 12 * s, n=8, rot=-side * 20), c2, w=3, seed=seed + 3 + side, boil=0.5)
    line(cv, [(x, y - 16 * s), (x, y + 18 * s)], 5 * s + 1, INK, seed=seed + 7, boil=0.4, n=2, taper=(0.2, 0.2))


def grass_tufts(cv, x0, x1, ybase_fn, T, seed=0, n=30, rgb=None, hgt=34):
    rgb = rgb or P_["acid_dk"]
    for k in range(n):
        gx = x0 + (x1 - x0) * (k + 0.5 * hsh(seed + k)) / n
        gy = ybase_fn(gx)
        sw = 7 * math.sin(T * 2.2 + k * 0.7)
        for j in (-1, 0, 1):
            line(cv, [(gx + j * 7, gy + 4), (gx + j * 12 + sw, gy - hgt * (0.7 + 0.4 * hsh(seed + k * 3 + j)))], 4, rgb, seed=seed + k * 5 + j, boil=0.5, n=2,
                 taper=(0.0, 0.9))


def cave_hole(cv, x, y, wd, ht, T, seed=7500, rim=None):
    """A rocky cave opening in a hillside (x, y = bottom centre of the mouth): violet boulder arch around a pitch-dark mouth."""
    rim = rim or P_["magenta"]
    rock_mass(cv, [(x - wd * 1.1, y + 40), (x - wd * 1.0, y - ht * 0.55), (x - wd * 0.55, y - ht * 1.12), (x + wd * 0.1, y - ht * 1.25),
                   (x + wd * 0.75, y - ht * 1.0), (x + wd * 1.15, y - ht * 0.4), (x + wd * 1.25, y + 40)], seed=seed, rgb=CV_ROCK2, rim=rim, rim_side=1, ink=5.5)
    blob(cv, [(x - wd * 0.9, y - ht * 0.85), (x - wd * 0.4, y - ht * 1.2), (x + wd * 0.2, y - ht * 1.3), (x + wd * 0.8, y - ht * 1.05), (x + wd * 0.5, y - ht * 0.95),
              (x - wd * 0.2, y - ht * 1.02)], mix(P_["acid"], P_["acid_dk"], 0.3), w=4, seed=seed + 1, boil=0.8, n=5)
    mouth = [(x - wd * 0.62, y + 10), (x - wd * 0.6, y - ht * 0.3), (x - wd * 0.38, y - ht * 0.72), (x + wd * 0.05, y - ht * 0.84), (x + wd * 0.45, y - ht * 0.68),
             (x + wd * 0.64, y - ht * 0.25), (x + wd * 0.6, y + 10)]
    blob(cv, mouth, (16, 6, 34), w=6, seed=seed + 3, boil=0.9, n=5,
         shade=lambda c: (c.drawPath(poly_path(cr_closed(ell(x + wd * 0.05, y - ht * 0.5, wd * 0.5, ht * 0.28, n=10), 3)), paint((44, 18, 86), 200)),
                          [dots(c, [(x - wd * 0.15 + k * wd * 0.12, y - ht * 0.35 + 6 * math.sin(k))], 4, [P_["acid"], P_["teal"]][k % 2], a=160) for k in range(4)]))
    crystal(cv, x - wd * 0.85, y + 20, 0.7, T, seed=seed + 20)
    crystal(cv, x + wd * 0.95, y + 24, 0.6, T, seed=seed + 21)
    glow_mushroom(cv, x + wd * 0.75, y + 34, 0.7, T, seed=seed + 22)


def boulder(cv, x, ytop, wd, ht, seed=7560):
    """A mossy violet boulder (top centre x, ytop)."""
    pts = [(x - wd * 0.5, ytop + ht), (x - wd * 0.56, ytop + ht * 0.4), (x - wd * 0.4, ytop + ht * 0.06), (x, ytop - ht * 0.04), (x + wd * 0.42, ytop + ht * 0.08),
           (x + wd * 0.56, ytop + ht * 0.45), (x + wd * 0.52, ytop + ht)]
    rock_mass(cv, pts, seed=seed, rgb=CV_ROCK2, rim=P_["hotpink"], rim_side=1, ink=5.5)
    blob(cv, [(x - wd * 0.48, ytop + ht * 0.2), (x - wd * 0.38, ytop + ht * 0.02), (x, ytop - ht * 0.06), (x + wd * 0.4, ytop + ht * 0.04), (x + wd * 0.5, ytop + ht * 0.2),
              (x + wd * 0.2, ytop + ht * 0.14), (x - wd * 0.1, ytop + ht * 0.2)], mix(P_["acid"], P_["acid_dk"], 0.25), w=4, seed=seed + 1, boil=0.7, n=5)


# ===================================================================== the cave memory (bubble + iris content)
def memory_cave(cv, T, t, chain_k=0.0, q_k=0.0, seed=7600, n=5, glow_k=1.0, shadow_x=None, shadow_kind="hand_bunny"):
    """The prisoners down in the dark, as Gary remembers them: the firelit wall with a shadow puppet, a row of chained
    prisoners in silhouette (collars, chains). Local box -500..500 x -280..280; the readable window is about +-190 in y."""
    fl = 0.93 + 0.05 * math.sin(T * 9.0) + 0.03 * math.sin(T * 17.0)
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(20, 0), 600 * fl, [core.C(mix(P_["yellow"], CV_WALL, 0.3)), core.C(CV_WALL), core.C(CV_WALL2),
                                                                             core.C(mix(CV_WALL2, P_["maroon"], 0.75))], [0.0, 0.3, 0.62, 1.0]))
    cv.drawRect(R(-520, -300, 520, 300), p)
    for k in range(6):                                             # cracks + faded handprints
        sx = -460 + k * 180 + 40 * hsh(seed + k)
        line(cv, [(sx, -190), (sx + 18, -130), (sx - 10, -70), (sx + 12, -20)], 3, mix(CV_WALL2, P_["maroon"], 0.6), seed=seed + k, boil=0.6, n=4,
             taper=(0.3, 0.5), a=140)
    handprint(cv, -360, -60, 0.75, rgb=P_["maroon"], a=70, seed=seed + 8)
    handprint(cv, 390, -80, 0.65, rgb=P_["violet"], a=60, seed=seed + 9, ang=20)
    if shadow_x is None:
        kinds = ["hand_bunny", "horse", "bird", "bunny"]
        ph = (T * 0.11) % 1.0
        shadow_x, shadow_kind = 560 - ph * 1120, kinds[int(T * 0.11) % len(kinds)]
    shadow_shape(cv, shadow_kind, shadow_x, -22, 0.74, T, seed=seed + 20)
    rock_mass(cv, [(-540, -320), (540, -320), (540, -175), (260, -150), (-40, -182), (-300, -152), (-540, -178)], seed=seed + 3, rgb=CV_ROCK, rim=P_["orange"], ink=4)
    for k in range(5):
        sx = -420 + k * 210
        L = 26 + 26 * hsh(seed + k)
        blob(cv, [(sx - 22, -170), (sx + 22, -170), (sx + 4, -150 + L), (sx - 3, -146 + L)], CV_ROCK2, w=3.5, seed=seed + 30 + k, boil=0.6, n=3)
    firelight(cv, 0, 300, 520, T, a=int(130 * glow_k), seed=seed)
    xs = [-380 + k * (760 / max(1, n - 1)) for k in range(n)]
    rat = chain_k * math.sin(T * 40) * 5
    heads = []
    for k, px in enumerate(xs):
        r = 66 + 6 * (k % 2)
        hy = 122 + 10 * (k % 2) + 3 * math.sin(T * 1.6 + k) + rat * (1 if k % 2 else -1)
        heads.append((px, hy, r))
    for k in range(len(heads) - 1):
        a, b = heads[k], heads[k + 1]
        chain(cv, (a[0] + a[2] * 0.72, a[1] + a[2] * 0.55), (b[0] - b[2] * 0.72, b[1] + b[2] * 0.55), seed=seed + 40 + k, link=17, sag=22, w=3.0,
              rgb=mix((150, 150, 175), P_["white"], 0.5 * chain_k))
    for k, (px, hy, r) in enumerate(heads):
        blob(cv, ell(px, hy, r, r * 1.05, n=12), (28, 12, 46), w=5, seed=seed + 60 + k, boil=0.9,
             shade=lambda c, px=px, hy=hy, r=r: c.drawPath(poly_path(cr_closed(ell(px, hy - r * 0.95, r * 0.92, r * 0.32, n=10), 3)), paint(P_["orange"], 90)))
        line(cv, [(px - r * 0.55, hy - r * 0.7), (px, hy - r * 0.86), (px + r * 0.55, hy - r * 0.7)], 4, P_["yellow"], seed=seed + 70 + k, boil=0.6, n=4, a=200)
        blob(cv, ell(px, hy + r * 0.62, r * 0.84, r * 0.21, n=10), mix((120, 120, 150), P_["white"], 0.4 * chain_k), w=3.5, seed=seed + 80 + k, boil=0.6)
    if chain_k > 0:
        for k, (px, hy, r) in enumerate(heads):
            sparkle(cv, px + r * 0.5, hy + r * 0.6, 22 * chain_k, P_["white"], w=2, seed=seed + 90 + k)
            for j in (-1, 1):
                line(cv, [(px + j * r * 1.05, hy - r * 0.2), (px + j * r * 1.3, hy - r * 0.45)], 4, P_["cream"], seed=seed + 95 + k + j, boil=0.5, n=2,
                     taper=(0.2, 0.2), a=int(230 * chain_k))
    if q_k > 0:
        cols = [P_["teal"], P_["yellow"], P_["hotpink"], P_["acid"], P_["lilac"]]
        for k, (px, hy, r) in enumerate(heads):
            kk = pop(q_k * 2.0 - k * 0.2, 0.0, 0.45)
            if kk <= 0.01:
                continue
            qmark(cv, px + 12 * math.sin(T * 3 + k), hy - r - 10 - 14 * abs(math.sin(T * 4 + k)), 0.62 * kk, cols[k % len(cols)], seed=seed + 100 + k,
                  rot_deg=10 * math.sin(T * 2 + k))


# ===================================================================== T036  -- remembers / goes back down / hero / crowd
B36 = dict(down=1.79, chained=3.25, guess=4.83, sorry=6.96, goes=8.79, free=10.75, hero=11.94, crowd=13.32)
SUN_XY = (1500, 225)
CAVE_XY = (1680, 905)


def ground_y(x):
    """Top of the front meadow (world coords of the 0.85 layer)."""
    return 905 + 20 * math.sin(x / 260.0 + 1.0) - 40 * math.exp(-((x - 1680) / 260.0) ** 2)


def sunny_world(cv, T, t, cam, gary_fn=None, sun_face=None, wind=0.0, seed=7700, boulder_on=True):
    C = sets.Cam(cv, cam)
    sf = sun_face or {}
    with C.layer(0.08):
        sky_warm(cv, T, SUN_XY[0], SUN_XY[1], seed=seed)
    with C.layer(0.15):
        sun_planet(cv, SUN_XY[0], SUN_XY[1], 150, T, seed=seed + 10, look=sf.get("look", (-0.6, 0.4)), smile=sf.get("smile", 0.45), lids=sf.get("lids", 0.45),
                   rot=T * 3.0)
        for k in range(4):                                         # birds far away
            bx = (300 + k * 230 + T * 40) % (W + 200) - 100
            by = 420 + 30 * math.sin(k * 2.0) + 6 * math.sin(T * 5 + k)
            fl = 10 * math.sin(T * 9 + k)
            line(cv, [(bx - 16, by - fl * 0.6), (bx, by), (bx + 16, by - fl * 0.6)], 3.5, INK, seed=seed + 20 + k, boil=0.4, n=3, taper=(0.2, 0.2))
    with C.layer(0.3):
        w.hills(cv, 655, 100, [P_["lilac"], mix(P_["lilac"], P_["hotpink"], 0.5)], seed=seed + 30, freq=1.3, spacing=34)
        for k in range(4):
            lolly_tree(cv, 140 + k * 480 + 60 * math.sin(k * 3.3), 700 + 14 * (k % 2), 0.42, T, seed=seed + 40 + k * 5,
                       cols=[[P_["hotpink"], P_["yellow"], P_["magenta"], P_["orange"]], [P_["teal"], P_["mint"], P_["blue"], P_["white"]]][k % 2])
    with C.layer(0.55):
        w.hills(cv, 772, 80, [P_["teal"], mix(P_["acid"], P_["teal"], 0.35)], seed=seed + 60, freq=1.0, spacing=40)
        for k in range(3):
            w.mushroom(cv, 1080 + k * 120, 830 + 10 * (k % 2), 0.3 + 0.06 * k, cap=[P_["red"], P_["magenta"], P_["orange"]][k], seed=seed + 80 + k)
    with C.layer(0.85):
        xs = np.linspace(-400, W + 400, 52)
        top = [(xx, ground_y(xx)) for xx in xs]
        pts = top + [(W + 400, H + 500), (-400, H + 500)]
        cv.drawPath(poly_path(pts), paint(mix(P_["acid"], P_["yellow"], 0.35)))
        cv.save(); cv.clipPath(poly_path(pts), doAntiAlias=True)
        stipple(cv, mix(P_["acid_dk"], P_["acid"], 0.3), (-400, 820, W + 400, H + 200), spacing=17, r=2.4, seed=seed + 90,
                fn=lambda X, Y: np.clip((Y - 880) / 260.0, 0, 1))
        for k in range(4):                                         # a little striped path to the cave
            line(cv, [(820, 960 + k * 16), (1180, 985 + k * 14), (1500, 930 + k * 6), (1640, 905 + k * 4)], 7, P_["peach"], seed=seed + 95 + k, boil=0.6, n=4,
                 taper=(0.1, 0.4), a=150)
        cv.restore()
        brush(cv, np.array(top), 5.5, taper=(0.02, 0.02), seed=seed + 91)
        cave_hole(cv, CAVE_XY[0], CAVE_XY[1], 230, 260, T, seed=seed + 70)
        grass_tufts(cv, -200, W + 200, ground_y, T + wind, seed=seed + 100, n=36)
        for k in range(8):
            dx = 40 + k * 205 + 40 * math.sin(k * 2.7)
            if 560 < dx < 900 or dx > 1450:
                continue
            daisy(cv, dx, ground_y(dx) + 30 + 34 * (k % 2), 0.8 + 0.2 * (k % 3), T, seed=seed + 120 + k * 3,
                  petal=[P_["white"], P_["hotpink"], P_["cream"]][k % 3])
        if boulder_on:
            boulder(cv, 700, 866, 330, 130, seed=seed + 140)
    with C.layer(1.0):
        if gary_fn is not None:
            gary_fn(cv)
        butterfly(cv, 1180 + 120 * math.sin(T * 0.7), 560 + 60 * math.sin(T * 1.3), 1.0, T, seed=seed + 150)
        butterfly(cv, 1000 + 90 * math.sin(T * 0.9 + 2), 760 + 50 * math.sin(T * 1.1), 0.8, T, seed=seed + 160, c1=P_["teal"], c2=P_["hotpink"])
    with C.layer(1.2):
        for k, (fx, fy, sc) in enumerate(((70, 1120, 1.9), (1850, 1110, 1.7), (300, 1150, 1.3), (1600, 1160, 1.2))):
            daisy(cv, fx, fy, sc, T, seed=seed + 170 + k, petal=[P_["hotpink"], P_["white"], P_["yellow"], P_["cream"]][k])
        grass_tufts(cv, -100, 420, lambda xx: 1100.0, T, seed=seed + 180, n=8, hgt=70, rgb=P_["acid_dk"])
        grass_tufts(cv, 1500, 2020, lambda xx: 1100.0, T, seed=seed + 190, n=8, hgt=70, rgb=P_["acid_dk"])


GX36, GY36, GS36 = 700, 562, 0.85


def _gary_sitting(cv, t, T, x, y, s):
    """A1: Gary sitting on a mossy boulder in the sun, remembering; his face goes from content to sad."""
    k_look = eseg(t, 0.3, 1.1)
    sad1 = eseg(t, B36["chained"] - 0.2, B36["chained"] + 0.6)
    sad2 = eseg(t, B36["guess"] + 0.4, B36["sorry"])
    lids = lid_mix(lid_mix("happy", "neutral", k_look), lid_mix("sad", "sadder", sad2 * 0.6), sad1)
    look = (-0.45 * k_look, -0.7 * k_look + 0.75 * sad1)
    if t < 0.35:
        mouth = "smile"
    elif t < B36["chained"]:
        mouth = "line"
    else:
        mouth = "frown" if t < B36["guess"] + 0.5 else "wobble"
    kick = 1.0 - eseg(t, 0.5, 1.5)
    droop = 30 * sad1                                              # the daisy he picked droops as he gets sad
    gary_x(cv, x, y, s, T, seed=4400, loud=0.0, look=look, lids=lids, mouth=mouth, legs=("dangle", T * 6.0 * kick), bob=2.0, wet=sad2,
           armL=(-168, 236 + droop * 0.4, -60 + droop * 2.4, "hold"), armR=(158, 300, 90, "flat"))
    fx, fy = x - 168 * s, y + 236 * s + droop * 0.4 * s
    cv.save(); cv.translate(fx, fy); cv.rotate(-10 + droop * 2.2); cv.translate(-fx, -fy)
    daisy(cv, fx, fy + 24 * s, 0.85 * s / 0.72, T, seed=7790, petal=P_["white"], face=False)
    cv.restore()


def _remember_bubble(cv, t, T, x, y, rx, ry, tail):
    k = pop(t, 0.35, 0.5)

    def content(c):
        c.save()
        sink = 18 * eseg(t, B36["down"], B36["down"] + 1.0)       # 'still down there' -> the memory sinks a little deeper
        sc = rx * 2 / 1000 * 1.08
        c.translate(x, y); c.scale(sc, sc); c.translate(0, -6 - sink)
        with Ink(sc ** -0.55):
            memory_cave(c, T, t, chain_k=eseg(t, B36["chained"], B36["chained"] + 0.3) * (1 - eseg(t, B36["guess"] + 0.4, B36["guess"] + 1.0)),
                        q_k=seg(t, B36["guess"], B36["guess"] + 1.2), shadow_x=lerp(430, -430, t / 6.85), shadow_kind="hand_bunny")
        c.restore()
        a = int(255 * (1 - eseg(t, 0.45, 1.3)))                    # the memory blooms out of the cream
        if a > 0:
            c.drawRect(R(x - rx * 1.2, y - ry * 1.2, x + rx * 1.2, y + ry * 1.2), paint(P_["cream"], a))
    cloud_bubble(cv, x, y, rx, ry, k, seed=7810, tail_to=tail, content=content)


def _t036_a1(cv, t, T):
    u = eseg(t, 0.0, 6.9)
    cam = dict(x=-40 * u, y=-40 * u, z=1.0 + 0.09 * u)
    sun_face = dict(look=(-0.85, 0.5), smile=0.45 - 0.55 * eseg(t, B36["guess"], B36["sorry"]), lids=0.45 - 0.2 * eseg(t, B36["chained"], B36["sorry"]))

    def gfn(c):
        _gary_sitting(c, t, T, GX36, GY36, GS36)
        _remember_bubble(c, t, T, 520, 250, 405, 172, (GX36 + 110, GY36 - 128))
    sunny_world(cv, T, t, cam, gary_fn=gfn, sun_face=sun_face)


def _t036_a2(cv, t, T):
    """'He feels sorry for them.' -- close on his eye; his chained friends reflected in the iris; a tear rolls down."""
    lt = t - 6.85
    z = 1.0 + 0.045 * lt
    cv.save(); cv.translate(W / 2, H / 2); cv.scale(z, z); cv.translate(-W / 2, -H / 2)
    rad_rect(cv, (-100, -100, W + 100, H + 100), 1700, 60, 1800, [(255, 248, 215), P_["yellow"], P_["orange"], P_["hotpink"], (150, 60, 210)],
             [0.0, 0.14, 0.38, 0.68, 1.0])
    wedge_rays(cv, 1700, 60, 2400, 20, P_["white"], 30, rot_deg=T * 3)
    for k in range(10):                                            # warm bokeh drifting
        bx = (hsh(7900 + k) * W + lt * 26 * (k % 3 - 1)) % W
        by = hsh(7910 + k) * H
        rr = 40 + 60 * hsh(7920 + k)
        cv.drawCircle(bx, by, rr, paint([P_["cream"], P_["yellow"], P_["hotpink"]][k % 3], 55))
        cv.drawCircle(bx, by, rr, paint(P_["white"], 60, stroke=3))
    s = 2.6
    x, y = 960, 478
    sadk = eseg(lt, 0.05, 0.8)
    lids = lid_mix((0.0, -0.8, 0.0), (0.12, -0.7, 0.12), sadk)

    def iris_art(c, ex, ey, ir):
        c.save()
        c.translate(ex, ey - ir * 0.05); sc = ir * 2.15 / 1000; c.scale(sc, sc)
        with Ink(sc ** -0.5):
            memory_cave(c, T, t, chain_k=0.0, q_k=0.0, shadow_x=lerp(180, -180, (t - 6.85) / 1.85), shadow_kind="horse")
        c.restore()
        c.drawCircle(ex, ey, ir, paint(P_["teal"], 45))
        p = skia.Paint(AntiAlias=True)
        p.setShader(skia.GradientShader.MakeRadial(skia.Point(ex, ey), ir, [core.C(P_["tealdk"], 0), core.C(P_["tealdk"], 0), core.C(P_["tealdk"], 235)], [0, 0.62, 1.0]))
        c.drawCircle(ex, ey, ir, p)
        c.drawPath(poly_path(cr_closed(ell(ex - ir * 0.42, ey - ir * 0.5, ir * 0.3, ir * 0.15, n=8, rot=-35), 3)), paint(P_["white"], 150))
    gary_x(cv, x, y, s, T, seed=4400, loud=0.0, look=(0.0, 0.3), pupil="pin", pk=0.62, lids=lids, mouth="wobble", tear=eseg(lt, 0.25, 1.85), wet=1.0,
           armL=None, armR=None, bob=1.2, iris_art=iris_art)
    cv.restore()


def _t036_a3(cv, t, T):
    """'So he goes back down...' -- he hops off the boulder with resolve and sets off for the cave."""
    lt = t - 8.7
    hop = seg(lt, 0.0, 0.5)
    resolve = eseg(lt, 0.4, 0.8)
    turn = eseg(lt, 0.95, 1.25)
    walk = max(0.0, lt - 1.15)
    gs = GS36
    gx = GX36 + 70 * ease(hop) + 330 * walk + 60 * walk * walk
    gy = GY36 + 14 - 70 * math.sin(hop * math.pi) - (abs(math.sin(walk * 9.0)) * 12 if walk > 0 else 0)
    land = math.exp(-max(0.0, lt - 0.5) * 14) * (lt > 0.5)
    cam = dict(x=-180 + 0.9 * (gx - GX36), y=60, z=1.28 + 0.04 * seg(lt, 0, 1.9))
    sun_face = dict(look=(-0.9, 0.5), smile=-0.1 + 0.25 * resolve, lids=0.25)

    def gfn(c):
        if hop < 0.15:
            legs = ("dangle", 0.0)
        elif walk > 0:
            legs = ("walk", walk * 9.0)
        else:
            legs = "stand"
        lids = lid_mix((0.16, -0.5, 0.16), "resolve", resolve)
        if walk > 0:
            sw = math.sin(walk * 9.0)
            armL, armR = (-150 - 26 * sw, 300, 100, "fist"), (150 - 26 * sw, 300, 80, "fist")
        elif resolve > 0.4:
            armL, armR = (-140, 320, 100, "fist"), (185, 150 - 30 * pop(lt, 0.5, 0.25), -75, "fist")
        else:
            armL, armR = "hang", "hang"
        gary_x(c, gx, gy + land * 16, gs, T, seed=4400, loud=0.0, look=(0.85 * turn, 0.05 * (1 - turn)), pk=0.9 - 0.3 * resolve, lids=lids,
               mouth="line" if resolve > 0.3 else "wobble", legs=legs, bob=0.0 if walk > 0 else 1.5, glint=pop(lt, 0.55, 0.3) * (1 - eseg(lt, 0.95, 1.2)),
               armL=armL, armR=armR)
    sunny_world(cv, T, t, cam, gary_fn=gfn, sun_face=sun_face, wind=lt * 2)
    if 0.55 < lt < 1.05:                                           # 'ding!' resolve burst
        k = pop(lt, 0.55, 0.25) * (1 - eseg(lt, 0.85, 1.05))
        sx, sy = sets.Cam(cv, cam).to_screen(gx, gy - 10)
        for j in range(10):
            a = j / 10 * 2 * math.pi + 0.3
            r0, r1 = 250 * (0.8 + 0.2 * k), 250 + 110 * k
            line(cv, [(sx + r0 * math.cos(a), sy + r0 * math.sin(a)), (sx + r1 * math.cos(a), sy + r1 * math.sin(a))], 9, P_["white"], seed=7950 + j, boil=0.5, n=2,
                 taper=(0.2, 0.2))


def _t036_a4(cv, t, T):
    """'...to set them free.' -- from inside the cave: Gary a silhouette against the blinding mouth, swallowed by darkness."""
    lt = t - 10.6
    dur = B36["hero"] - 10.6
    u = clamp01(lt / dur)
    z = 1.0 + 0.04 * u
    cv.save(); cv.translate(W / 2, H / 2); cv.scale(z, z); cv.translate(-W / 2, -H / 2)
    w.field(cv, (10, 4, 22))
    mx, my = 960, 330
    mouth = [(mx - 300, my + 130), (mx - 280, my - 60), (mx - 170, my - 210), (mx + 10, my - 250), (mx + 200, my - 200), (mx + 310, my - 50), (mx + 290, my + 140),
             (mx + 110, my + 170), (mx - 130, my + 165)]
    mp = poly_path(cr_closed(jit(mouth, 1.0, 8000), 6))
    cv.save(); cv.clipPath(mp, doAntiAlias=True)
    rad_rect(cv, (mx - 400, my - 300, mx + 400, my + 260), mx + 60, my - 60, 430, [P_["white"], (255, 246, 200), P_["yellow"], P_["orange"]], [0, 0.35, 0.7, 1.0])
    wedge_rays(cv, mx + 120, my - 120, 700, 16, P_["white"], 60, rot_deg=T * 6)
    sun_planet(cv, mx + 120, my - 120, 46, T, seed=8005, look=(-0.4, 0.6), smile=-0.1, lids=0.25, rays=0.0)
    w.hills(cv, my + 95, 40, [mix(P_["acid"], P_["white"], 0.55), mix(P_["yellow"], P_["white"], 0.45)], seed=8001, freq=2.0, spacing=24)
    cv.restore()
    sun_rays(cv, mx, my - 60, 1500, T, n=15, a=int(130 * (1 - 0.6 * u)), ang0=90, span=80)
    path = [(mx - 220, my + 150), (mx + 230, my + 150), (mx + 560, H + 80), (mx - 600, H + 80)]
    blob(cv, path, (60, 26, 96), w=5, seed=8002, boil=0.9, n=4,
         shade=lambda c: (rad_rect(c, (0, 0, W, H + 100), mx, my + 120, 800, [mix(P_["orange"], CV_ROCK2, 0.25), CV_ROCK2, (34, 14, 58)], [0, 0.45, 1.0]),
                          [blob(c, ell(mx - 150 + 90 * k * (1 if k % 2 else -1), my + 230 + k * 92, 30 + 14 * k, 14 + 6 * k, n=8), (48, 20, 80),
                                w=3.0, seed=8010 + k, boil=0.5, shade=lambda c2, k=k: c2.drawPath(poly_path(cr_closed(ell(mx - 150 + 90 * k * (1 if k % 2 else -1),
                                my + 226 + k * 92 - 4 - 2 * k, 26 + 12 * k, 6 + 3 * k, n=8), 3)), paint(P_["orange"], 120))) for k in range(7)]))
    rock_mass(cv, [(-200, -200), (W + 200, -200), (W + 200, H + 200), (mx + 560, H + 200), (mx + 300, my + 150), (mx + 340, my - 50), (mx + 220, my - 220),
                   (mx + 20, my - 280), (mx - 190, my - 230), (mx - 310, my - 70), (mx - 330, my + 150), (mx - 600, H + 200), (-200, H + 200)],
              seed=8020, rgb=(42, 16, 78), rim=P_["magenta"], rim_side=1, ink=6)
    for k in range(7):                                             # stalactites framing the mouth
        sx = 160 + k * 270
        L = 150 + 140 * hsh(8030 + k)
        blob(cv, [(sx - 52, -20), (sx + 52, -20), (sx + 6, L), (sx - 4, L + 14)], (54, 22, 96), w=5, seed=8030 + k, boil=0.8, n=3,
             shade=lambda c, sx=sx, L=L: c.drawPath(poly_path([(sx + 10, -20), (sx + 52, -20), (sx + 6, L)]), paint(P_["magenta"], 70)))
    gp = skia.Paint(AntiAlias=True, Color=core.C(P_["yellow"], int(200 * (1 - 0.5 * u))))      # light bleeding around the rim of the mouth
    gp.setStyle(skia.Paint.kStroke_Style); gp.setStrokeWidth(46); gp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 26))
    cv.drawPath(mp, gp)
    for k, (cx, cy) in enumerate(((190, 900), (1720, 880), (430, 1010), (1500, 1030))):
        crystal(cv, cx, cy, 0.95, T, seed=8040 + k)
    for k, (cx, cy, sc) in enumerate(((600, 760, 0.8), (1330, 740, 0.7), (520, 900, 1.1), (1430, 940, 1.2), (700, 1040, 1.3))):
        glow_mushroom(cv, cx, cy, sc, T, seed=8050 + k)
    gs = lerp(0.2, 0.66, u)
    gx = mx + lerp(30, -90, u)
    gy = lerp(my + 18, 740, u ** 1.2)
    ph = lt * 9.0

    def gfn(c):
        gary_x(c, gx, gy, gs, T, seed=4400, loud=0.0, look=(0.0, 0.2), lids="resolve", mouth="line", legs=("walk", ph), bob=0.0,
               armL=(-150 - 22 * math.sin(ph), 300, 100, "fist"), armR=(150 - 22 * math.sin(ph), 300, 80, "fist"))
    rimc = mix(P_["yellow"], (30, 10, 50), eseg(u, 0.2, 0.9))
    silhouette(cv, gfn, (14, 6, 30), rim=rimc, rim_off=(0, -6))
    p = skia.Paint(AntiAlias=True)                                 # darkness swallows everything, then the mouth too
    inner = lerp(0.6, 0.0, eseg(u, 0.3, 1.0))
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(mx, my - 20), lerp(1500, 560, eseg(u, 0.15, 1.0)),
                                               [core.C((6, 2, 14), 0), core.C((6, 2, 14), 0), core.C((6, 2, 14), 255)], [0.0, inner, 1.0]))
    cv.drawRect(R(-50, -50, W + 50, H + 50), p)
    if u > 0.7:                                                    # the last glint of his eye
        k = 1 - eseg(u, 0.94, 1.0)
        sparkle(cv, gx - 14 * gs, gy - 40 * gs, 26 * k, P_["white"], w=2, seed=8060, a=int(255 * k))
    cv.restore()


def hero_poster(cv, t, T, A):
    """'A hero!' -- a retro heroic poster of Gary: sunburst, halftone, cape-scarf, giant HERO!"""
    lt = t - B36["hero"]
    slam = pop(lt, 0.0, 0.3)
    jx, jy = shake(16 * math.exp(-lt * 7), seed=8100)
    w.field(cv, (52, 18, 84))
    stipple(cv, (80, 34, 120), (0, 0, W, H), spacing=22, r=3.0, seed=8101)
    cv.save()
    cv.translate(W / 2 + jx, H / 2 + jy); cv.rotate(-2.0); sc = 0.94 + 0.3 * (1 - slam); cv.scale(sc, sc); cv.translate(-W / 2, -H / 2)
    x0, y0, x1, y1 = 40, 30, W - 40, H - 30
    blob(cv, rect_pts([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 4), P_["cream"], w=6, seed=8102, boil=1.0, n=3)
    ix0, iy0, ix1, iy1 = x0 + 34, y0 + 34, x1 - 34, y1 - 70
    gx, gy, gs = 1080, 560, 1.08
    armR = (178, -70 + 8 * math.sin(lt * 10), -92, "fist")
    cv.save(); cv.clipRect(R(ix0, iy0, ix1, iy1), doAntiAlias=True)
    w.sunburst(cv, gx, gy - 40, 1700, 26, [P_["gold"], P_["orange"], P_["yellow"], P_["magenta"]], rot_deg=lt * 12, seed=8103)
    stipple(cv, P_["red"], (ix0, iy0, ix1, iy1), spacing=18, r=4.5, seed=8104, fn=lambda X, Y: np.clip(np.hypot(X - gx, Y - gy) / 1100.0, 0, 1) * 0.9)
    glow(cv, gx, gy - 60, 560, P_["white"], a=160)
    for k in range(12):                                            # wind lines
        yy = 180 + k * 70
        xx = ((k * 211 + lt * 2400) % 2400) - 300
        line(cv, [(xx, yy), (xx + 260, yy - 8)], 5, P_["white"], seed=8110 + k, boil=0.5, n=2, taper=(0.4, 0.4), a=200)
    gary_x(cv, gx, gy, gs, T, seed=4400, loud=0.0, look=(-0.15, -0.45), lids="resolve", mouth="grin", legs="stand", bob=0.0, glint=1.0, pk=0.8,
           armL=(-176, 290, 20, "fist"), armR=None, scarf=dict(flow=lt * 9.0, dir=-1, len=820, wd=140))
    paint_text(cv, "HERO!", 560, 330, font="shrik", size=250, fills=[P_["yellow"], P_["cream"], P_["yellow"], P_["cream"], P_["yellow"]], ink_w=8,
               shadow=(12, 12), shadow_rgb=P_["magenta"], seed=8120, reveal=clamp01(lt / 0.45), stagger=0.08, drips=1)
    _gary_arm(cv, gx, gy, gs, T, 1, armR, 4400 + 50 + 20)          # the raised fist, over everything
    for k in range(5):
        sparkle(cv, gx + 190 * gs + 110 * math.cos(k * 1.26 + lt * 3), gy - 110 * gs + 90 * math.sin(k * 1.26 + lt * 3), 18, P_["white"], seed=8130 + k)
    cv.restore()
    brush(cv, np.array([(ix0, iy0), (ix1, iy0), (ix1, iy1), (ix0, iy1)]), 6, closed=True, seed=8140)
    paint_text(cv, "GARY  -  HE WENT BACK DOWN!", 960, y1 - 16, font="londrina", size=44, fill=P_["red"], ink_w=0, shadow=None, seed=8141, streaks=False)
    cv.restore()


def cheer_crowd(cv, t, T, A):
    """'The crowd goes wild!' -- the BOXED eyeball audience on its feet, signs up, confetti, sweeping spotlights."""
    lt = t - B36["crowd"]
    jx, jy = shake(7, seed=8200)
    cv.save(); cv.translate(jx, jy)
    rad_rect(cv, (-60, -60, W + 60, H + 60), 960, 1200, 1500, [P_["violet"], P_["vdark"], P_["night"], P_["void"]], [0, 0.35, 0.7, 1.0])
    w.stars(cv, 8201, (0, 0, W, 600), n=120, big=6)
    for k, (bx, col) in enumerate(((300, P_["magenta"]), (960, P_["teal"]), (1620, P_["yellow"]))):
        ang = math.radians(90 + 28 * math.sin(T * 1.8 + k * 2.1))
        tipx, tipy = bx + 1300 * math.cos(ang), -60 + 1300 * math.sin(ang)
        nx, ny = -math.sin(ang) * 230, math.cos(ang) * 230
        p = skia.Paint(AntiAlias=True)
        p.setShader(skia.GradientShader.MakeLinear([skia.Point(bx, -60), skia.Point(tipx, tipy)], [core.C(col, 120), core.C(col, 0)]))
        cv.drawPath(poly_path([(bx - 20, -60), (bx + 20, -60), (tipx + nx, tipy + ny), (tipx - nx, tipy - ny)]), p)
    rows = ((470, 0.42, 11), (610, 0.56, 9), (770, 0.74, 8), (950, 0.98, 6))
    cols = [(64, 30, 110), (90, 40, 150), (46, 20, 86), (110, 50, 120)]
    irises = [(200, 255, 230), (255, 200, 240), (255, 240, 170), (190, 220, 255)]
    for ri, (yb, s, n) in enumerate(rows):
        for k in range(n):
            x = (k + 0.5 + (0.5 if ri % 2 else 0.0) - 0.25) * W / n
            seed = 8300 + ri * 40 + k * 3
            jump = abs(math.sin(T * (7 + hsh(seed) * 3) + k * 1.7 + ri)) * 34 * s
            held = ri == 3 and k in (1, 4)
            if held:
                sign(cv, x, yb - jump - 362 * s, s, T, ["GARY!", "HERO"][k == 4], seed + 1)
            cheer_fan(cv, x, yb - jump, s, T, seed, cols[(k + ri) % 4], irises[(k * 3 + ri) % 4], k + ri, hold=held)
    cl = [P_["magenta"], P_["yellow"], P_["teal"], P_["acid"], P_["orange"], P_["hotpink"]]
    for k in range(90):
        x = hsh(8400 + k) * W + 40 * math.sin(T * 2 + k)
        y = ((hsh(8500 + k) * H + (lt + 2) * (180 + 120 * hsh(8600 + k))) % (H + 80)) - 40
        ang = T * 5 + k
        dx, dy = 13 * math.cos(ang), 7 * math.sin(ang * 1.3)
        cv.drawPath(poly_path([(x - dx, y - dy), (x + dy, y - dx), (x + dx, y + dy), (x - dy, y + dx)]), paint(cl[k % 6]))
    cv.restore()
    caption(cv, "WOOOO!", 1500, 230, lt, 0.25, size=120, fill=P_["acid"], font="shrik", seed=8700, shadow_rgb=P_["magenta"])


def cheer_fan(cv, x, y, s, T, seed, rgb, iris, k, hold=False):
    """One cheering audience eyeball creature (body base at y), arms waving overhead (or holding up a sign), mouth wide open."""
    r = 110 * s
    cx, cy = x, y - r
    wave = math.sin(T * 10 + k * 1.3)
    for side in (-1, 1):
        sh = (cx + side * r * 0.8, cy + r * 0.1)
        if hold:
            hx, hy = cx + side * r * 0.3, cy - r * 1.5
            el = (cx + side * r * 1.1, cy - r * 0.55)
        else:
            hx = cx + side * r * (1.25 + 0.15 * wave * side)
            hy = cy - r * (1.35 + 0.12 * math.sin(T * 12 + k + side))
            el = (cx + side * r * 1.35, cy - r * 0.45)
        tube(cv, [sh, el, (hx, hy)], 16 * s + 2, rgb, w=4, seed=seed + 10 + side, boil=0.7, n=6)
        cv.save(); cv.translate(hx, hy); cv.scale(s * 0.95, s * 0.95)
        _hand(cv, 0, 0, -90 - side * 30 if hold else -90 + side * 18 + 10 * wave, "fist" if hold else "spread", -side, seed + 12 + side, rgb=P_["white"])
        cv.restore()
    body = [(x - r * 1.05, y + 40 * s), (x - r * 1.1, cy), (x - r * 0.7, cy - r * 0.95), (x, cy - r * 1.12), (x + r * 0.7, cy - r * 0.95), (x + r * 1.1, cy),
            (x + r * 1.05, y + 40 * s)]
    blob(cv, body, rgb, w=5, seed=seed, boil=1.0, n=5,
         shade=lambda c: c.drawPath(poly_path(cr_closed(ell(cx + r * 0.45, cy + r * 0.3, r * 0.9, r * 1.1, n=10), 3)), paint(mix(rgb, INK, 0.3))))
    ex, ey, er = cx, cy - r * 0.25, r * 0.5
    blob(cv, ell(ex, ey, er, er * 1.05, n=10), P_["white"], w=4, seed=seed + 5, boil=0.7)
    if k % 3 == 0:                                                 # eye squeezed shut with joy
        line(cv, [(ex - er * 0.7, ey + er * 0.25), (ex, ey - er * 0.35), (ex + er * 0.7, ey + er * 0.25)], 6 * s + 2.5, seed=seed + 8, boil=0.6, n=4)
    else:
        dots(cv, [(ex, ey - er * 0.1)], er * 0.55, iris)
        dots(cv, [(ex, ey - er * 0.1)], er * 0.3, INK)
        dots(cv, [(ex - er * 0.18, ey - er * 0.3)], er * 0.11 + 0.8, P_["white"])
    mo = 0.6 + 0.4 * abs(math.sin(T * 8 + k))
    blob(cv, ell(ex, ey + er * 1.55, er * 0.6, er * 0.25 + er * 0.45 * mo, n=9), P_["mouth"], w=3.5, seed=seed + 6, boil=0.6,
         shade=lambda c: blob(c, ell(ex + 2, ey + er * 1.55 + er * 0.45 * mo, er * 0.4, er * 0.25, n=8), P_["tongue"], w=0, seed=seed + 7, boil=0.4, misreg=(0, 0)))


def sign(cv, x, y, s, T, text, seed):
    """A hand-painted crowd sign (board centre x, y) on a stick."""
    rot_d = 5 * math.sin(T * 6 + seed)
    cv.save(); cv.translate(x, y); cv.rotate(rot_d)
    line(cv, [(0, 40 * s), (0, 200 * s)], 12 * s + 2, (140, 90, 50), seed=seed, boil=0.5, n=2, taper=(0, 0))
    blob(cv, rect_pts([(-170 * s, -80 * s), (170 * s, -86 * s), (176 * s, 70 * s), (-166 * s, 76 * s)], 3), P_["yellow"] if text == "GARY!" else P_["hotpink"],
         w=5, seed=seed + 1, boil=0.9, n=3)
    paint_text(cv, text, 0, 34 * s, font="shrik", size=108 * s, fill=P_["red"] if text == "GARY!" else P_["cream"], ink_w=4, shadow=(4, 4), seed=seed + 2,
               streaks=False)
    cv.restore()


def T036_remembers(cv, t, T, A):
    if t < 6.85:
        _t036_a1(cv, t, T)
    elif t < 8.7:
        _t036_a2(cv, t, T)
    elif t < 10.6:
        _t036_a3(cv, t, T)
    elif t < B36["hero"]:
        _t036_a4(cv, t, T)
    elif t < B36["crowd"] - 0.05:
        hero_poster(cv, t, T, A)
    else:
        cheer_crowd(cv, t, T, A)
    vignette(cv, a=110)


# ===================================================================== a fuller prisoner rig (kit proportions + arms + faces)
PRIS_COLS = [(64, 30, 110), (90, 40, 150), (46, 20, 86), (110, 50, 120)]
PRIS_IRIS = [(200, 255, 230), (255, 200, 240), (255, 240, 170), (190, 220, 255)]


def pris(cv, x, y, s, T, seed=9000, face=1, view="side", eye="open", look=(0.0, 0.0), mouth=0.0, laugh=0.0, armL=None, armR=None,
         chained=True, anchor=None, rgb=None, iris=None, lean=0.0, squash=0.0, tears=0.0, rim=None, mouth_kind=None, bob=None):
    """A chained prisoner (a squat eyeball creature like the kit's prisoner) with arms and a fuller face.
    x, y = floor point under the body; face -1/+1 (side view).  eye: open | laugh | closed | wide.  mouth 0..1 (laugh-mouth when laugh > 0).
    armL / armR: None or (hx, hy, ang_deg, pose) in absolute coords (armL = screen-left side).  lean: degrees around the base."""
    rgb = rgb or PRIS_COLS[int(hsh(seed) * 4) % 4]
    iris = iris or PRIS_IRIS[int(hsh(seed + 1) * 4) % 4]
    r = 70 * s
    bob = 2.5 * math.sin(T * 1.7 + seed) * s if bob is None else bob
    cv.save()
    cv.translate(x, y); cv.rotate(lean); cv.scale(1.0 + squash * 0.5, 1.0 - squash); cv.translate(-x, -y)
    cx, cy = x, y - r * 1.15 + bob
    if chained:                                                    # chain to the floor ring behind the body
        ax, ay = anchor if anchor is not None else (x - face * r * 1.5, y + 4 * s)
    body = [(x - r * 1.05, y), (x - r * 1.1, cy), (x - r * 0.7, cy - r * 0.95), (x, cy - r * 1.12), (x + r * 0.7, cy - r * 0.95), (x + r * 1.1, cy), (x + r * 1.05, y)]

    def sh(c):
        c.drawPath(poly_path(cr_closed(ell(cx + face * r * 0.45, cy + r * 0.3, r * 0.9, r * 1.1, n=10), 3)), paint(mix(rgb, INK, 0.3)))
        if rim is not None:
            side = rim[1]
            c.drawPath(poly_path(cr_closed(ell(cx + side * r * 1.15, cy - r * 0.1, r * 0.42, r * 1.3, n=10), 3)), paint(rim[0], 150))
    blob(cv, body, rgb, w=5.0 * min(1.0, s * 1.4) + 1.5, seed=seed, boil=1.0, n=5, shade=sh)
    ex = cx + (face * r * 0.32 if view == "side" else 0.0)
    ey = cy - r * (0.34 if view == "front" else 0.3)
    er = r * (0.5 if view == "front" else 0.44)
    if view != "back":
        if eye == "laugh":
            blob(cv, ell(ex, ey, er, er * 1.0, n=10), P_["white"], w=4, seed=seed + 5, boil=0.7)
            line(cv, [(ex - er * 0.72, ey + er * 0.28), (ex, ey - er * 0.4), (ex + er * 0.72, ey + er * 0.28)], 5.5 * min(1.0, s) + 2.5, seed=seed + 8, boil=0.6, n=4,
                 taper=(0.15, 0.15))
        elif eye == "closed":
            blob(cv, ell(ex, ey, er, er * 1.0, n=10), P_["white"], w=4, seed=seed + 5, boil=0.7,
                 shade=lambda c: c.drawRect(R(ex - er * 1.2, ey - er * 1.2, ex + er * 1.2, ey + er * 0.1), paint(mix(rgb, P_["white"], 0.15))))
            line(cv, [(ex - er, ey + er * 0.1), (ex, ey + er * 0.35), (ex + er, ey + er * 0.1)], 4.5, seed=seed + 8, boil=0.6, n=4)
        else:
            k = 1.15 if eye == "wide" else 1.0
            blob(cv, ell(ex, ey, er * k, er * 1.05 * k, n=10), P_["white"], w=4, seed=seed + 5, boil=0.7)
            ix = ex + (face * er * 0.3 if view == "side" else 0) + look[0] * er * 0.42
            iy = ey + look[1] * er * 0.42
            pk = 0.75 if eye == "wide" else 1.0
            dots(cv, [(ix, iy)], er * 0.56 * pk, iris)
            dots(cv, [(ix, iy)], er * 0.28 * pk, INK)
            dots(cv, [(ix - er * 0.15, iy - er * 0.2)], er * 0.1 + 0.8, P_["white"])
        if tears > 0:                                              # tears of laughter squirting out
            for k in range(6):
                ph = (T * 2.2 + k / 6.0 + 0.3 * hsh(seed + k)) % 1.0
                side = 1 if k % 2 else -1
                tx = ex + side * er * (0.95 + 2.0 * ph)
                ty = ey - er * 0.1 - er * 1.9 * ph + er * 3.6 * ph * ph
                rr = er * (0.26 - 0.08 * ph) + 1.5
                blob(cv, [(tx - side * rr * 1.6, ty - rr * 0.6), (tx, ty - rr), (tx + side * rr * 0.4, ty), (tx, ty + rr)], P_["mint"], w=2.5, seed=seed + 20 + k, boil=0.4,
                     n=4, a=int(255 * tears * (1 - ph * 0.6)))
        if laugh > 0 or mouth > 0.05:
            mo = max(mouth, laugh)
            mx, my = ex + (face * er * 0.12 if view == "side" else 0), ey + er * 1.32
            mw, mh = er * (0.8 + 0.5 * laugh), er * (0.22 + 0.62 * mo)
            pts = [(mx - mw, my - mh * 0.25), (mx - mw * 0.5, my - mh * 0.32), (mx + mw * 0.5, my - mh * 0.32), (mx + mw, my - mh * 0.25), (mx + mw * 0.7, my + mh * 0.55),
                   (mx, my + mh), (mx - mw * 0.7, my + mh * 0.55)]
            blob(cv, pts, P_["mouth"], w=3.5 * min(1.0, s) + 1.5, seed=seed + 6, boil=0.6, n=4,
                 shade=lambda c: (c.drawRect(R(mx - mw, my - mh * 0.4, mx + mw, my - mh * 0.08), paint(P_["white"])),
                                  blob(c, ell(mx + er * 0.1, my + mh * 0.85, mw * 0.55, mh * 0.35, n=8), P_["tongue"], w=0, seed=seed + 7, boil=0.4, misreg=(0, 0))))
        elif mouth_kind == "grimace":
            mx, my = ex, ey + er * 1.38
            line(cv, [(mx - er * 0.6, my), (mx - er * 0.3, my - er * 0.12), (mx, my + er * 0.05), (mx + er * 0.3, my - er * 0.12), (mx + er * 0.6, my)],
                 4.5, seed=seed + 9, boil=0.8, n=4, taper=(0.2, 0.2))
    else:
        line(cv, [(cx - r * 0.5, cy - r * 0.5), (cx, cy - r * 0.62), (cx + r * 0.5, cy - r * 0.5)], 3, mix(rgb, P_["white"], 0.25), seed=seed + 3, boil=0.6, n=4)
    if chained:
        ny = cy + r * 0.7
        blob(cv, ell(cx, ny, r * 0.92, r * 0.19, n=10), (120, 120, 150), w=3.5, seed=seed + 8, boil=0.6,
             shade=lambda c: c.drawRect(R(cx - r, ny, cx + r, ny + r * 0.3), paint((80, 80, 110))))
        chain(cv, (cx - face * r * 0.6, ny + r * 0.1), (ax, ay), seed=seed + 9, link=max(8.0, 15 * s), sag=10 * s, w=max(1.6, 2.6 * s))
        blob(cv, ell(ax, ay, 12 * s + 2, 5 * s + 2, n=8), (120, 120, 150), w=3, seed=seed + 10, boil=0.4)
        for side in (-1, 1):
            blob(cv, ell(x + side * r * 0.6, y - 6 * s, r * 0.25, r * 0.1, n=8), (120, 120, 150), w=3, seed=seed + 12 + side, boil=0.4)
    for side, spec in ((-1, armL), (1, armR)):
        if spec is None:
            continue
        hx, hy, ang, pose = spec
        shx, shy = cx + side * r * 0.9, cy + r * 0.22
        el = tuple(_limb_elbow((shx, shy), (hx, hy), side, s * 0.45, bend=0.8))
        tube(cv, [(shx, shy), el, (hx, hy)], 15 * s + 3, rgb, w=4, seed=seed + 30 + side, boil=0.7, n=6)
        cv.save(); cv.translate(hx, hy); cv.scale(s * 0.85, s * 0.85)
        _hand(cv, 0, 0, ang, pose, -1 if side > 0 else 1, seed + 33 + side, rgb=P_["white"])
        cv.restore()
    cv.restore()
    return (ex, ey, er)


def cast_shadow(cv, pts, rgb=None, a=150, blur=14):
    """A soft flat shadow polygon on the wall."""
    rgb = rgb or CV_SHADOW
    halo = skia.Paint(AntiAlias=True, Color=core.C(rgb, int(a * 0.5)))
    halo.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    path = poly_path(cr_closed(jit(pts, 1.5, 9900), 4))
    cv.drawPath(path, halo)
    cv.drawPath(path, paint(rgb, a))


def dome_shadow(cv, x, ybase, s, a=150, wob=0.0):
    r = 70 * s
    cy = ybase - r * 1.15 + wob
    cast_shadow(cv, [(x - r * 1.05, ybase), (x - r * 1.1, cy), (x - r * 0.7, cy - r * 0.95), (x, cy - r * 1.12), (x + r * 0.7, cy - r * 0.95), (x + r * 1.1, cy),
                     (x + r * 1.05, ybase)], a=a)


def ha_pops(cv, t, items, seed=9500):
    """Floating laugh letters: items = [(t0, x, y, text, rgb, size, rot)] -- pop in, drift up, fade."""
    for k, (t0, x, y, txt, rgb, size, rd) in enumerate(items):
        lt = t - t0
        if lt < 0 or lt > 1.6:
            continue
        kk = pop(lt, 0.0, 0.25)
        a = int(255 * (1 - eseg(lt, 1.1, 1.6)))
        cv.save(); cv.translate(x + 10 * math.sin(lt * 9 + k), y - 60 * lt); cv.rotate(rd + 6 * math.sin(lt * 12 + k)); cv.scale(kk, kk)
        paint_text(cv, txt, 0, 0, font="shrik", size=size, fill=rgb, ink_w=5, shadow=(5, 5), shadow_rgb=INK, seed=seed + k, streaks=False, rot_jit=8, a=a)
        cv.restore()


def speech_bubble(cv, x, y, wd, ht, tail, text, k, seed=0, size=64, fill=None, txt_rgb=None, jag=True):
    """A jagged shout bubble centred at x, y, tail pointing to `tail`."""
    if k <= 0.01:
        return
    fill = fill or P_["white"]
    cv.save(); cv.translate(x, y); cv.scale(k, k); cv.translate(-x, -y)
    pts = []
    n = 22
    for j in range(n):
        ang = j / n * 2 * math.pi
        rr = 1.0 + (0.14 if (jag and j % 2) else 0.0)
        pts.append((x + wd / 2 * rr * math.cos(ang), y + ht / 2 * rr * math.sin(ang)))
    tx, ty = tail
    d = math.atan2(ty - y, tx - x)
    base = [(x + wd * 0.3 * math.cos(d + 0.35), y + ht * 0.3 * math.sin(d + 0.35)), (tx, ty), (x + wd * 0.3 * math.cos(d - 0.35), y + ht * 0.3 * math.sin(d - 0.35))]
    blob(cv, base, fill, w=5, seed=seed + 1, boil=0.7, n=2)
    blob(cv, pts, fill, w=5.5, seed=seed, boil=0.9, n=3)
    cv.drawPath(poly_path(base), paint(fill))
    paint_text(cv, text, x, y + size * 0.35, font="shrik", size=size, fill=txt_rgb or P_["red"], ink_w=4, shadow=(4, 4), seed=seed + 2, streaks=False)
    cv.restore()


# ===================================================================== T038 -- mocked
B38 = dict(look=2.5, say=3.38, went=4.62, back=5.55, ruined=6.25, going=7.88, worth=8.42)


def cave_backdrop(cv, T, seed=9100, wall_poly=None, wall_c=(960, 420), floor_y=630, glow_xy=(960, 1300)):
    """Firelit wall behind + rock ceiling + floor: the set for the mocking."""
    w.field(cv, CV_ROCK_DK)
    wall_surface(cv, wall_poly or [(-120, -120), (2040, -120), (2040, floor_y + 20), (-120, floor_y + 50)], T, seed=seed, cx=wall_c[0], cy=wall_c[1])
    rock_mass(cv, [(-200, -200), (2120, -200), (2120, 50), (1640, 100), (1180, 60), (700, 112), (240, 70), (-200, 100)], seed=seed + 1, rgb=CV_ROCK,
              rim=P_["orange"], rim_side=1, ink=5)
    for k in range(9):
        sx = 80 + k * 225 + 30 * math.sin(k * 1.9)
        L = 70 + 90 * hsh(seed + 10 + k)
        y0 = 70 + 25 * math.sin(k * 2.3)
        blob(cv, [(sx - 30, y0), (sx + 30, y0), (sx + 4, y0 + L), (sx - 3, y0 + L + 10)], CV_ROCK2, w=4, seed=seed + 10 + k, boil=0.7, n=3,
             shade=lambda c, sx=sx, y0=y0, L=L: c.drawPath(poly_path([(sx + 8, y0), (sx + 30, y0), (sx + 4, y0 + L)]), paint(P_["orange"], 60)))
    rock_mass(cv, [(-200, floor_y), (700, floor_y - 18), (1300, floor_y + 6), (2120, floor_y - 12), (2120, 1300), (-200, 1300)], seed=seed + 2, rgb=CV_ROCK2,
              rim=P_["orange"], rim_side=1, ink=5)
    firelight(cv, glow_xy[0], glow_xy[1], 900, T, a=120, seed=seed + 3)


def _t038_m1(cv, t, T):
    """The laughing circle: dazed Gary in the middle, the prisoners pointing and howling."""
    zoom = 1.0 + 0.03 * t + 0.06 * pop(t, B38["look"], 0.25)
    jx, jy = shake(2.5 + 2.0 * seg(t, 0, 1.0), seed=9200)
    cv.save(); cv.translate(W / 2 + jx, H / 2 + jy); cv.scale(zoom, zoom); cv.translate(-W / 2, -H / 2 - 30 * seg(t, 0, 4.5))
    cave_backdrop(cv, T, seed=9100, floor_y=690, wall_c=(960, 380))
    lauk0 = eseg(t, 0.15, 0.6)                                     # their big shadows on the wall laugh too
    for k, (sx_, ss_) in enumerate(((140, 2.4), (560, 2.0), (1360, 2.0), (1780, 2.4))):
        hop = abs(math.sin(T * 13 + k * 1.3)) * 30 * lauk0
        dome_shadow(cv, sx_, 690 - hop, ss_, a=95, wob=0.0)
    cast_shadow(cv, [(890, 690), (880, 520), (850, 420), (900, 330), (960, 300), (1020, 330), (1070, 420), (1040, 520), (1030, 690)], a=80)
    for k, (mx, my, sc) in enumerate(((120, 760, 0.9), (1810, 770, 1.0), (760, 720, 0.6), (1190, 715, 0.55))):
        glow_mushroom(cv, mx, my, sc, T, seed=9120 + k)
    crystal(cv, 60, 700, 1.0, T, seed=9130)
    crystal(cv, 1880, 690, 0.9, T, seed=9131)
    lauk = eseg(t, 0.15, 0.6)
    pts_k = eseg(t, B38["look"] - 0.1, B38["look"] + 0.2)
    gx, gy, gs = 960, 540, 0.86
    sway = 4 * math.sin(T * 2.2)
    cast = {"P5": (390, 790, 0.95, 1, PRIS_COLS[3]), "P6": (1530, 790, 0.95, -1, PRIS_COLS[0]), "P2": (590, 960, 1.45, 1, PRIS_COLS[1]),
            "P3": (1330, 960, 1.45, -1, PRIS_COLS[3]), "P1": (215, 1110, 2.05, 1, PRIS_COLS[1]), "P4": (1705, 1110, 2.05, -1, PRIS_COLS[3])}

    def laugher(key, k):
        px, py, ps, f, rgb = cast[key]
        r = 70 * ps
        hop = abs(math.sin(T * 13 + k * 1.3)) * 12 * ps * lauk
        lean = -f * 7 * lauk * (0.6 + 0.4 * math.sin(T * 6.5 + k))
        cy = py - hop - r * 1.15
        shx = px + f * r * 0.9
        if key in ("P2", "P3"):                                     # they point at Gary
            hx_ = lerp(shx + f * r * 0.5, shx + f * r * 0.85, pts_k)
            hy_ = lerp(cy + r * 0.5, cy - r * 0.55, pts_k)
            aim = math.degrees(math.atan2(gy - 20 - hy_, gx - hx_))
            near = (hx_, hy_, aim if pts_k > 0.4 else (0 if f > 0 else 180), "point" if pts_k > 0.4 else "open")
            far = (px - f * r * 0.35, cy + r * 0.75, -40 if f > 0 else -140, "fist")
        elif key in ("P1", "P4"):                                   # clutching their bellies
            near = (px + f * r * 0.55, cy + r * 0.8, 160 if f > 0 else 20, "flat")
            far = (px - f * r * 0.45, cy + r * 0.85, 20 if f > 0 else 160, "flat")
        else:                                                      # back row: hands in the air
            near = (shx + f * r * 0.5, cy - r * 0.7 - 10 * math.sin(T * 9 + k), -60 if f > 0 else -120, "spread")
            far = (px - f * r * 1.4, cy - r * 0.6 - 10 * math.sin(T * 9 + k + 1), -120 if f > 0 else -60, "spread")
        armR, armL = (near, far) if f > 0 else (far, near)
        pris(cv, px, py - hop, ps, T, seed=9300 + k * 17, face=f, eye="laugh" if lauk > 0.3 else "open", look=(f * 0.6, 0),
             laugh=lauk * (0.7 + 0.3 * abs(math.sin(T * 14 + k))), tears=lauk, lean=lean, squash=0.05 * abs(math.sin(T * 13 + k)) * lauk, armL=armL, armR=armR,
             anchor=(px - f * r * 1.25, py + 6), rim=(P_["orange"], -f), rgb=rgb)
    laugher("P5", 4)
    laugher("P6", 5)
    cv.save(); cv.translate(gx, gy + 330); cv.rotate(sway); cv.translate(-gx, -gy - 330)
    gary_x(cv, gx, gy, gs, T, seed=4400, loud=0.0, look=(0, 0), pupil="spiral", lids="dazed", mouth="wobble", legs="sit", bob=1.5, sweat=0.8,
           armL=(-215 - 18 * math.sin(T * 3), 200 + 18 * math.sin(T * 2.3), 200, "open"), armR=(215 + 18 * math.sin(T * 3 + 1), 215, -20, "open"))
    for k in range(3):                                             # dizzy stars orbiting his head
        a = T * 4 + k * 2.09
        sparkle(cv, gx + 175 * math.cos(a), gy - 170 + 36 * math.sin(a), 20, [P_["yellow"], P_["cream"], P_["acid"]][k], w=2.5, seed=9400 + k)
    cv.restore()
    for key, k in (("P2", 1), ("P3", 2), ("P1", 0), ("P4", 3)):
        laugher(key, k)
    cv.restore()
    ha_pops(cv, t, [(0.2, 300, 560, "HA!", P_["yellow"], 110, -12), (0.55, 1640, 540, "HAW!", P_["acid"], 100, 10), (0.95, 560, 700, "HA", P_["hotpink"], 80, -6),
                    (1.3, 1380, 690, "HEE!", P_["teal"], 80, 8), (1.75, 1650, 420, "HAHA!", P_["yellow"], 96, 6), (3.0, 1520, 600, "HA!", P_["acid"], 100, 12),
                    (3.5, 330, 640, "HAW!", P_["teal"], 90, -10), (3.95, 1660, 650, "HA", P_["yellow"], 80, 6)])
    speech_bubble(cv, 470, 300, 660, 200, (560, 520), "LOOK AT HIM!", pop(t, B38["look"], 0.3) * (1 - eseg(t, 4.25, 4.5)), seed=9450, size=72)


def gary_puppet(cv, x, y, s, T, rot_deg=0.0, xeyes=0.0, a=225, seed=9600):
    """A shadow-puppet Gary on the wall: flat silhouette (blurred penumbra), with X-shaped holes for eyes when ruined."""
    def fn(c):
        c.save(); c.translate(x, y + 200 * s); c.rotate(rot_deg); c.translate(-x, -y - 200 * s)
        gary_x(c, x, y, s, T, seed=seed, loud=0.0, legs=("walk", T * 8), armL=(-170, 260 + 30 * math.sin(T * 7), 120, "open"),
               armR=(170, 230 - 30 * math.sin(T * 7), 60, "open"), bob=0.0)
        c.restore()
    cv.saveLayer(None, None)
    fn(cv)
    q = skia.Paint(AntiAlias=True, Color=core.C(CV_SHADOW, a))
    q.setBlendMode(skia.BlendMode.kSrcIn)
    cv.drawRect(R(-400, -400, W + 400, H + 400), q)
    cv.restore()
    if xeyes > 0:                                                  # holes cut in the puppet: the bright wall shows through
        cv.save(); cv.translate(x, y + 200 * s); cv.rotate(rot_deg); cv.translate(-x, -y - 200 * s)
        for d in (-1, 1):
            line(cv, [(x - 60 * s * xeyes, y - 22 * s - d * 60 * s * xeyes), (x + 60 * s * xeyes, y - 22 * s + d * 60 * s * xeyes)], 22 * s + 2,
                 mix(P_["yellow"], CV_WALL, 0.3), seed=seed + 50 + d, boil=0.6, n=2, taper=(0.1, 0.1))
        blob(cv, [(x - 10 * s, y + 92 * s), (x + 26 * s, y + 92 * s), (x + 22 * s, y + 150 * s), (x + 2 * s, y + 156 * s)], mix(P_["yellow"], CV_WALL, 0.3), w=0,
             seed=seed + 60, boil=0.6, n=4, misreg=(0, 0))           # lolling tongue cut-out
        cv.restore()


def _t038_m2(cv, t, T):
    """'He went up there and came back with his eyes ruined.' -- the prisoners stage a mocking shadow play on the wall."""
    lt = t - 4.55
    z = 1.0 + 0.03 * lt
    jx, jy = shake(2.5, seed=9700)
    cv.save(); cv.translate(W / 2 + jx, H / 2 + jy); cv.scale(z, z); cv.translate(-W / 2, -H / 2)
    w.field(cv, CV_ROCK_DK)
    wall_surface(cv, [(-220, -220), (2140, -220), (2140, 1300), (-220, 1300)], T, seed=9701, cx=900, cy=760)
    rock_mass(cv, [(-300, -300), (2300, -300), (2300, -10), (1600, 50), (900, 20), (300, 70), (-300, 30)], seed=9702, rgb=CV_ROCK, rim=P_["orange"])
    # the puppet set: a shadow hill climbing to a shadow sun
    cast_shadow(cv, [(700, 900), (1000, 640), (1250, 430), (1420, 300), (1560, 330), (1700, 560), (1980, 900)], a=170)
    sx, sy = 1560, 190
    for k in range(12):
        ang = k / 12 * 2 * math.pi + T * 0.6
        cast_shadow(cv, [(sx + 92 * math.cos(ang - 0.12), sy + 92 * math.sin(ang - 0.12)), (sx + 150 * math.cos(ang), sy + 150 * math.sin(ang)),
                         (sx + 92 * math.cos(ang + 0.12), sy + 92 * math.sin(ang + 0.12))], a=170, blur=8)
    cast_shadow(cv, list(map(tuple, ell(sx, sy, 84, 84, n=14))), a=170, blur=8)
    cast_shadow(cv, list(map(tuple, rot(ell(sx, sy, 150, 26, n=16), -16, sx, sy))), a=150, blur=8)
    # the puppet's journey: up the hill, a tumble back down, X-eyed and staggering
    up = eseg(lt, B38["went"] - 4.55, B38["back"] - 4.55)
    fall = seg(lt, B38["back"] - 4.55, B38["ruined"] - 4.55)
    ps = 0.62
    if fall <= 0:
        px, py, rd = lerp(560, 1360, up), lerp(640, 210, up), -8 * math.sin(T * 8)
    elif fall < 1:
        px, py = lerp(1360, 760, fall), lerp(210, 520, fall) - 260 * math.sin(fall * math.pi)
        rd = -360 * 1.5 * ease(fall)
    else:
        st = lt - (B38["ruined"] - 4.55)
        px, py, rd = 760 + 40 * math.sin(st * 5), 520 + 10 * abs(math.sin(st * 7)), 14 * math.sin(st * 6)
    xe = eseg(lt, B38["ruined"] - 4.55, B38["ruined"] - 4.55 + 0.25)
    gary_puppet(cv, px, py, ps, T, rot_deg=rd, xeyes=xe)
    line(cv, [(px + 10, py + 300 * ps), (px + 30, 1300)], 9, CV_SHADOW, seed=9710, boil=0.5, n=2, taper=(0, 0), a=170)   # the puppet stick
    if xe > 0:
        for k in range(3):                                         # shadow dizzy-stars
            a = T * 5 + k * 2.1
            cast_shadow(cv, [(px + 140 * math.cos(a) + dx, py - 150 + 30 * math.sin(a) + dy) for dx, dy in
                             ((0, -22), (6, -6), (22, 0), (6, 6), (0, 22), (-6, 6), (-22, 0), (-6, -6))], a=190, blur=4)
    # the audience of prisoners: heads along the bottom, shaking with laughter
    heads = []
    for k in range(7):
        hx = 100 + k * 287
        r = 120 + 14 * (k % 2)
        hy = 1015 + 18 * (k % 2) - abs(math.sin(T * 13 + k * 1.4)) * 22
        heads.append((hx, hy, r))
    for k in range(len(heads) - 1):
        chain(cv, (heads[k][0] + heads[k][2] * 0.7, heads[k][1] + heads[k][2] * 0.6), (heads[k + 1][0] - heads[k + 1][2] * 0.7, heads[k + 1][1] + heads[k + 1][2] * 0.6),
              seed=9720 + k, link=20, sag=26, w=3.5)
    for k, (hx, hy, r) in enumerate(heads):
        blob(cv, ell(hx, hy, r, r * 1.05, n=12), (24, 10, 40), w=5, seed=9730 + k, boil=1.0,
             shade=lambda c, hx=hx, hy=hy, r=r: c.drawPath(poly_path(cr_closed(ell(hx, hy - r * 0.95, r * 0.9, r * 0.3, n=10), 3)), paint(P_["orange"], 70)))
        blob(cv, ell(hx, hy + r * 0.55, r * 0.8, r * 0.2, n=10), (110, 110, 140), w=3.5, seed=9740 + k, boil=0.6)
        line(cv, [(hx - r * 0.5, hy - r * 0.66), (hx, hy - r * 0.78), (hx + r * 0.5, hy - r * 0.66)], 4, P_["yellow"], seed=9750 + k, boil=0.6, n=4, a=190)
    cv.restore()
    ha_pops(cv, lt, [(0.1, 300, 820, "HA!", P_["yellow"], 100, -10), (0.6, 1500, 800, "HAHA!", P_["acid"], 90, 8), (1.3, 700, 840, "HAW!", P_["hotpink"], 90, -6),
                     (1.8, 1200, 860, "HA!", P_["teal"], 100, 10), (2.2, 250, 760, "HEE!", P_["yellow"], 80, -8), (2.5, 1700, 760, "HA!", P_["hotpink"], 100, 6)], seed=9760)
    if lt > B38["ruined"] - 4.55:
        caption(cv, "RUINED!", 760, 170, lt, B38["ruined"] - 4.55 + 0.1, size=110, fill=P_["cream"], font="shrik", seed=9770, shadow_rgb=P_["maroon"])


def _t038_m3(cv, t, T):
    """'Going up isn't even worth thinking about.' -- one prisoner covers its eye; a hand-painted NOPE sign."""
    lt = t - 7.6
    z = 1.0 + 0.025 * lt
    cv.save(); cv.translate(W / 2, H / 2); cv.scale(z, z); cv.translate(-W / 2, -H / 2)
    cave_backdrop(cv, T, seed=9800, floor_y=760, wall_c=(900, 380), glow_xy=(900, 1300))
    cv.save(); cv.clipRect(R(-100, 0, W + 100, 780))
    shadow_shape(cv, "hand_bunny", 400 - lt * 190, 330, 1.3, T, seed=9801)
    cv.restore()
    lk = 0.6 + 0.4 * eseg(lt, B38["going"] - 7.6 - 0.1, B38["going"] - 7.6 + 0.3) * (1 - 0.6 * eseg(lt, B38["worth"] - 7.6, B38["worth"] - 7.6 + 0.4))
    lx_, ly_ = 1690, 120                                           # far up the path: the light he came back from
    sun_rays(cv, lx_, ly_ - 30, 1100, T, n=9, a=int(70 * lk), ang0=118, span=46, rgb=(255, 244, 200))
    glow(cv, lx_, ly_, 230 * lk + 30, (255, 244, 200), a=int(220 * lk))
    blob(cv, [(lx_ - 70, ly_ - 50), (lx_ + 60, ly_ - 56), (lx_ + 76, ly_ + 20), (lx_ + 10, ly_ + 50), (lx_ - 64, ly_ + 26)], (255, 252, 230), w=4.5, seed=9803,
         boil=0.6, n=4)
    for k, (mx, my, sc) in enumerate(((330, 840, 0.9), (1240, 830, 0.8), (1800, 860, 1.1))):
        glow_mushroom(cv, mx, my, sc, T, seed=9805 + k)
    crystal(cv, 1650, 800, 1.0, T, seed=9808)
    for k in range(2):                                             # the others, back to their wall
        bx = [120, 1810][k]
        pris(cv, bx, 1160, 1.9, T, seed=9810 + k * 9, view="back", face=1, chained=True, anchor=(bx + 120, 1170), rgb=PRIS_COLS[k * 2])
    up = eseg(lt, B38["going"] - 7.6, B38["going"] - 7.6 + 0.3) * (1 - eseg(lt, B38["worth"] - 7.6, B38["worth"] - 7.6 + 0.25))
    cover = eseg(lt, B38["worth"] - 7.6, B38["worth"] - 7.6 + 0.3)
    shiver = (1.5 + 3.5 * cover) * math.sin(T * 40)
    px, py, ps = 800 + shiver, 870, 3.3
    r = 70 * ps
    cx, cy = px, py - r * 1.15
    ex, ey = cx, cy - r * 0.2
    shake_no = 6 * math.sin(T * 9) * cover
    if cover > 0:
        armL = (lerp(cx - r * 1.25, ex - 70, cover), lerp(cy + r * 0.35, ey + 40, cover), lerp(120, -40, cover), "flat")
        armR = (lerp(cx + r * 1.25, ex + 70, cover), lerp(cy + r * 0.35, ey + 40, cover), lerp(60, -140, cover), "flat")
    else:
        armL = (cx - r * 1.2, cy + r * 0.5, 110, "open")
        armR = (lerp(cx + r * 1.2, cx + r * 1.35, up), lerp(cy + r * 0.5, cy - r * 0.75, up), lerp(70, -55, up), "point" if up > 0.4 else "open")
    pris(cv, px, py, ps, T, seed=9850, view="front", face=1, eye="wide" if up > 0.2 else "open", look=(0.8 * up, -0.9 * up + 0.25 * (1 - up)),
         mouth_kind="grimace", armL=armL, armR=armR, lean=shake_no, anchor=(px - 300, py + 12), rim=(P_["orange"], 1), rgb=PRIS_COLS[1], iris=PRIS_IRIS[2])
    if cover > 0.5:                                                # sweat drops of pure refusal
        for k in range(3):
            phs = (T * 1.5 + k * 0.33) % 1.0
            sx = cx + (k - 1) * r * 0.75
            sy = cy - r * 1.05 + phs * 50
            blob(cv, [(sx, sy - 18), (sx + 11, sy + 4), (sx, sy + 14), (sx - 11, sy + 4)], P_["mint"], w=3, seed=9860 + k, boil=0.5, n=4, a=int(255 * (1 - phs)))
    nk = pop(lt, B38["worth"] - 7.6 + 0.35, 0.3)                   # the hand-painted NOPE sign, slammed into the floor beside it
    if nk > 0.01:
        sxp, syp = 1420, 520
        drop = (1 - nk) * -600
        cv.save(); cv.translate(sxp, syp + drop); cv.rotate(-6 + 2 * math.sin(T * 3))
        line(cv, [(0, 120), (6, 470)], 26, (130, 80, 46), seed=9870, boil=0.6, n=2, taper=(0, 0))
        board = rect_pts([(-270, -150), (270, -168), (282, 140), (-260, 150)], 3)
        blob(cv, board, P_["cream"], w=7, seed=9871, boil=1.0, n=3,
             shade=lambda c: (stipple(c, P_["cream_sh"], (-280, -170, 290, 160), spacing=12, r=1.6, seed=9872,
                                      fn=lambda X, Y: np.clip((X + Y) / 600.0 + 0.4, 0, 1) * 0.8),
                              [line(c, [(-270, -100 + j * 80), (270, -110 + j * 80)], 3, mix(P_["cream_sh"], INK, 0.2), seed=9873 + j, boil=0.6, n=3, a=120)
                               for j in range(4)]))
        for dx in (-180, 180):
            dots(cv, [(dx, -125)], 9, (90, 90, 110))
        paint_text(cv, "NOPE", 6, 52, font="wet", size=150, fill=P_["red"], ink_w=0, shadow=None, seed=9874, wobble=3.0, rot_jit=8, drips=1.6, streaks=False)
        cv.restore()
        u = clamp01((lt - (B38["worth"] - 7.6 + 0.6)) / 0.5)        # dust puff on impact
        if 0 < u < 1:
            for k in range(6):
                a = math.pi + k / 5 * math.pi
                blob(cv, ell(sxp + 12 + math.cos(a) * 130 * u, syp + 480 + math.sin(a) * 30 * u - 30 * u, 26 + 30 * u, 18 + 20 * u, n=8),
                     mix(CV_ROCK2, P_["lilac"], 0.5), w=3, seed=9880 + k, boil=0.6, a=int(220 * (1 - u)))
    cv.restore()


def T038_mocked(cv, t, T, A):
    if t < 4.55:
        _t038_m1(cv, t, T)
    elif t < 7.6:
        _t038_m2(cv, t, T)
    else:
        _t038_m3(cv, t, T)
    vignette(cv, a=150)


# ===================================================================== T040 -- 'they would kill him'
B40 = dict(darker=1.5, anyone=3.29, light=5.6, hands=7.75, would=10.29, kill=10.88)
FIRE_N = [P_["yellow"], P_["orange"], P_["red"], P_["magenta"]]
FIRE_R = [(255, 120, 90), (230, 30, 50), (150, 0, 34), (80, 0, 24)]


def fire_x(cv, x, y, s, T, cols, seed=10000, intensity=1.0, logs=True):
    """The kit's campfire with a colour ramp (outer -> inner) so it can turn blood red."""
    if logs:
        for k, ang in enumerate((-18, 18, -4)):
            cv.save(); cv.translate(x, y - 12 * s); cv.rotate(ang)
            blob(cv, rect_pts([(-110 * s, -16 * s), (110 * s, -16 * s), (110 * s, 16 * s), (-110 * s, 16 * s)], 3), (90, 40, 40), w=4.5, seed=seed + k, boil=0.8, n=3)
            cv.restore()
    for li, col in enumerate(cols[::-1]):
        k = 1.0 - li * 0.2
        hgt = (230 + 30 * math.sin(T * 3.1 + li)) * s * k * intensity
        wid = 120 * s * k
        pts = [(x - wid, y - 6 * s)]
        n = 7
        for j in range(n):
            u = (j + 0.5) / n
            px = x - wid + 2 * wid * u
            lick = math.sin(T * (6.0 + j) + j * 1.7 + li) * 0.5 + 0.5
            ph = hgt * (0.45 + 0.55 * math.sin(math.pi * u)) * (0.75 + 0.35 * lick)
            pts.append((px + 14 * s * math.sin(T * 5 + j + li), y - ph))
            if j < n - 1:
                pts.append((px + wid / n, y - ph * 0.55))
        pts.append((x + wid, y - 6 * s))
        blob(cv, pts, col, w=4.0 if li == 0 else 2.6, seed=seed + 10 + li, boil=1.6, n=4)
    for k in range(12):
        ph = (T * (0.5 + 0.13 * k) + k * 0.37) % 1.0
        sx = x + (hsh(seed + k * 3.1) - 0.5) * 220 * s + 30 * s * math.sin(T * 2 + k)
        sy = y - 140 * s - ph * 460 * s
        dots(cv, [(sx, sy)], (5 - 3 * ph) * s + 0.8, cols[k % 2], a=int(255 * (1 - ph)))


def wall_tinted(cv, poly, T, red, seed=10100, cx=None, cy=None):
    """The firelit wall; red 0..1 shifts it from hot orange to blood red."""
    P = np.asarray(poly, float)
    x0, y0 = P.min(0); x1, y1 = P.max(0)
    cx = (x0 + x1) / 2 if cx is None else cx
    cy = (y0 + y1) * 0.6 if cy is None else cy
    path = poly_path(cr_closed(jit(P, 0.8, seed), 4))
    fl = 0.93 + 0.05 * math.sin(T * 9.0 + seed) + 0.03 * math.sin(T * 17.0)
    c0 = [mix(P_["yellow"], CV_WALL, 0.35), CV_WALL, CV_WALL2, mix(CV_WALL2, P_["red"], 0.6)]
    c1 = [(255, 70, 50), (200, 16, 40), (120, 4, 30), (40, 2, 14)]
    cols = [mix(a, b, red) for a, b in zip(c0, c1)]
    g = skia.Paint(AntiAlias=True)
    g.setShader(skia.GradientShader.MakeRadial(skia.Point(cx, cy), max(x1 - x0, y1 - y0) * 0.75 * fl * (1 - 0.25 * red), [core.C(c) for c in cols], [0.0, 0.35, 0.7, 1.0]))
    cv.drawPath(path, g)
    cv.save(); cv.clipPath(path, doAntiAlias=True)
    stipple(cv, mix(mix(CV_WALL2, P_["red"], 0.5), (60, 0, 20), red), (x0, y0, x1, y1), spacing=15, r=2.1, seed=seed + 2,
            fn=lambda X, Y: np.clip(np.hypot(X - cx, Y - cy) / (max(x1 - x0, y1 - y0) * 0.6), 0, 1) * 0.9)
    for k in range(9):
        sx = x0 + (x1 - x0) * hsh(seed + k * 2.3)
        sy = y0 + (y1 - y0) * hsh(seed + k * 4.1)
        pts = [(sx, sy)]
        for j in range(4):
            pts.append((pts[-1][0] + 30 * (hsh(seed + k * 7 + j) - 0.5) * 2, pts[-1][1] + 40 + 30 * hsh(seed + k * 5 + j)))
        line(cv, pts, 2.6, mix(mix(CV_WALL2, P_["maroon"], 0.6), (30, 0, 10), red), seed=seed + 20 + k, boil=0.6, n=4, taper=(0.3, 0.5), a=160)
    for k in range(4):
        handprint(cv, x0 + (x1 - x0) * (0.1 + 0.8 * hsh(seed + 40 + k)), y0 + (y1 - y0) * (0.15 + 0.3 * hsh(seed + 50 + k)), 0.8 + 0.4 * hsh(seed + 60 + k),
                  rgb=mix([P_["maroon"], P_["red"], P_["violet"]][k % 3], (30, 0, 10), red), a=70, seed=seed + 70 + k, ang=-20 + 40 * hsh(seed + 80 + k))
    cv.restore()
    brush(cv, cr_closed(jit(P, 0.8, seed), 4), 6.0, closed=True, seed=seed + 3)


_DOME = [(-105, 0), (-110, -50), (-104, -98), (-86, -130), (-62, -150), (-40, -158), (-18, -161), (0, -162), (18, -161), (40, -158), (62, -150), (86, -130),
         (104, -98), (110, -50), (105, 0)]
_MONSTER = [(-120, 0), (-150, -120), (-150, -230), (-118, -300), (-150, -420), (-70, -330), (-30, -350), (0, -352), (30, -350), (70, -330), (150, -430),
            (122, -300), (150, -220), (150, -110), (125, 0)]
SHADOW_K = (34, 4, 16)


def monster_shadow(cv, x, ybase, s, T, morph, lean=0.0, seed=10200, chomp=0.0, eyes=1.0, a=235, wall_rgb=None):
    """A prisoner's shadow on the wall (a dome) that swells into a horned, toothy monster (morph 0..1). lean shears it sideways."""
    m = ease(morph)
    wob = 1.0 + 0.03 * math.sin(T * 7 + seed)
    pts = []
    for (dx0, dy0), (dx1, dy1) in zip(_DOME, _MONSTER):
        dx, dy = dx0 + (dx1 - dx0) * m, dy0 + (dy1 - dy0) * m
        dx += 6 * m * math.sin(T * 5 + dy * 0.05 + seed)
        X = x + dx * s * wob + lean * (-dy) * s * 0.5
        Y = ybase + dy * s * wob
        pts.append((X, Y))
    rgb = SHADOW_K
    halo = skia.Paint(AntiAlias=True, Color=core.C(rgb, int(a * 0.55)))
    halo.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 16 * s + 3))
    path = poly_path(cr_closed(jit(pts, 1.5, seed), 5))
    cv.drawPath(path, halo)
    cv.drawPath(path, paint(rgb, a))
    hx = x + lean * 250 * s * m
    hy = ybase - (120 + 140 * m) * s
    wall_rgb = wall_rgb or (255, 80, 60)
    if m > 0.45 and eyes > 0:                                      # glowing slit eyes
        ek = clamp01((m - 0.45) / 0.3) * eyes
        bl = 1.0 if (T * 0.7 + hsh(seed) * 5) % 3.3 > 0.12 else 0.15
        for side in (-1, 1):
            exx = hx + side * 42 * s
            pts_e = [(exx - side * 34 * s, hy - 10 * s), (exx + side * 30 * s, hy - 24 * s * bl), (exx + side * 26 * s, hy + 4 * s)]
            glow(cv, exx, hy - 8 * s, 50 * s, P_["yellow"], a=int(120 * ek))
            cv.drawPath(poly_path(pts_e), paint(mix(P_["yellow"], P_["white"], 0.3), int(255 * ek)))
    if m > 0.55:                                                   # a jagged grin (holes showing the burning wall)
        tk = clamp01((m - 0.55) / 0.3)
        mw = 95 * s * tk
        mh = (18 + 40 * chomp) * s * tk
        my = hy + 70 * s
        top, bot = [], []
        n = 9
        for j in range(n + 1):
            u = j / n
            xx = hx - mw + 2 * mw * u
            top.append((xx, my - (0 if j % 2 else 16 * s * tk) + 8 * s * math.sin(u * math.pi)))
            bot.append((xx, my + mh * math.sin(u * math.pi) + (0 if j % 2 else -14 * s * tk)))
        cv.drawPath(poly_path(top + bot[::-1]), paint(wall_rgb, int(235 * tk)))


def _union(paths):
    out = None
    for q in paths:
        out = q if out is None else (skia.Op(out, q, skia.PathOp.kUnion_PathOp) or out)
    return out


def shadow_claw(cv, x, y, s, ang, open_k=1.0, seed=10300, a=240, arm_from=None, rim=(255, 120, 80)):
    """A giant shadow hand with long claws (palm centre x, y), fingers pointing along ang (deg). open_k 1 = spread, 0 = clenched.
    A hot rim glow keeps it readable even over other shadows."""
    parts = []
    if arm_from is not None:
        ax, ay = arm_from
        dx, dy = x - ax, y - ay
        L = math.hypot(dx, dy) + 1e-6
        nx, ny = -dy / L, dx / L
        w0, w1 = 82 * s, 52 * s
        mx_, my_ = (ax + x) / 2, (ay + y) / 2 - 40 * s
        arm = [(ax + nx * w0, ay + ny * w0), (mx_ + nx * (w0 + w1) * 0.5, my_ + ny * (w0 + w1) * 0.5), (x + nx * w1, y + ny * w1),
               (x - nx * w1, y - ny * w1), (mx_ - nx * (w0 + w1) * 0.5, my_ - ny * (w0 + w1) * 0.5), (ax - nx * w0, ay - ny * w0)]
        parts.append(poly_path(cr_closed(jit(arm, 2.0, seed + 1), 4)))
    m = skia.Matrix()
    m.setTranslate(x, y); m.preRotate(ang); m.preScale(s, s)
    palm = poly_path(cr_closed(jit(ell(10, 0, 100, 76, n=10), 2.0, seed), 4))
    palm.transform(m)
    parts.append(palm)
    for k, (fa, base_y) in enumerate(((-30, -52), (-10, -18), (10, 18), (30, 52), (78, 64))):
        thumb = k == 4
        spread = math.radians(fa * (0.4 + 0.6 * open_k))
        Lf = (150 if thumb else 270 - 25 * abs(k - 1.5)) * (0.45 + 0.55 * open_k)
        curl = (1 - open_k) * (1.6 if not thumb else 0.9) + 0.22 * math.sin(T_CLAW[0] * 4 + k)
        bx, by = (80, base_y) if not thumb else (30, base_y)
        d1 = (math.cos(spread), math.sin(spread))
        knuck = (bx + d1[0] * Lf * 0.5, by + d1[1] * Lf * 0.5)
        d2 = (math.cos(spread + curl), math.sin(spread + curl))
        tip = (knuck[0] + d2[0] * Lf * 0.55, knuck[1] + d2[1] * Lf * 0.55)
        wdt = 21 if not thumb else 25
        n1 = (-d1[1], d1[0]); n2 = (-d2[1], d2[0])
        finger = [(bx + n1[0] * wdt, by + n1[1] * wdt), (knuck[0] + n1[0] * wdt * 0.8 + n2[0] * 2, knuck[1] + n1[1] * wdt * 0.8), tip,
                  (knuck[0] - n1[0] * wdt * 0.8, knuck[1] - n1[1] * wdt * 0.8), (bx - n1[0] * wdt, by - n1[1] * wdt)]
        fp = poly_path(finger)
        fp.transform(m)
        parts.append(fp)
    path = _union(parts)
    rp = skia.Paint(AntiAlias=True, Color=core.C(rim, int(a * 0.85)))
    rp.setStyle(skia.Paint.kStroke_Style); rp.setStrokeWidth(20 * s + 6); rp.setStrokeJoin(skia.Paint.kRound_Join)
    rp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 8 * s + 3))
    cv.drawPath(path, rp)
    cv.drawPath(path, paint(SHADOW_K, a))


T_CLAW = [0.0]


def lantern(cv, x, y, s, T, flame=1.0, seed=10400, glow_a=1.0):
    """A little hand lantern hanging from a handle at (x, y)."""
    fl = 0.85 + 0.1 * math.sin(T * 13 + seed) + 0.08 * float(hsh(core.D * 0.7 + seed))
    if flame > 0 and glow_a > 0:
        glow(cv, x, y + 70 * s, 420 * s * fl, P_["yellow"], a=int(120 * flame * glow_a))
        glow(cv, x, y + 70 * s, 160 * s * fl, P_["white"], a=int(110 * flame * glow_a))
    line(cv, [(x - 22 * s, y + 24 * s), (x, y), (x + 22 * s, y + 24 * s)], 4.5 * s + 1.5, (90, 90, 110), seed=seed, boil=0.5, n=4, taper=(0, 0))
    blob(cv, rect_pts([(x - 34 * s, y + 24 * s), (x + 34 * s, y + 24 * s), (x + 30 * s, y + 38 * s), (x - 30 * s, y + 38 * s)], 2), (70, 60, 90), w=3.5, seed=seed + 1,
         boil=0.5, n=2)
    glass = rect_pts([(x - 28 * s, y + 38 * s), (x + 28 * s, y + 38 * s), (x + 32 * s, y + 112 * s), (x - 32 * s, y + 112 * s)], 2)
    gc = mix((60, 40, 70), (255, 236, 150), flame)
    blob(cv, glass, gc, w=4, seed=seed + 2, boil=0.5, n=2,
         shade=lambda c: c.drawRect(R(x - 40 * s, y + 30 * s, x - 14 * s, y + 120 * s), paint(P_["white"], int(90 * flame))))
    if flame > 0.02:
        fh = 46 * s * flame * fl
        blob(cv, [(x, y + 100 * s - fh * 1.4), (x + 12 * s, y + 92 * s), (x + 8 * s, y + 104 * s), (x - 8 * s, y + 104 * s), (x - 12 * s, y + 92 * s)],
             P_["orange"], w=2.5, seed=seed + 3, boil=0.8, n=4)
        blob(cv, [(x, y + 100 * s - fh * 0.8), (x + 6 * s, y + 96 * s), (x, y + 104 * s), (x - 6 * s, y + 96 * s)], P_["yellow"], w=0, seed=seed + 4, boil=0.6,
             n=4, misreg=(0, 0))
    for k in (-1, 1):
        line(cv, [(x + k * 30 * s, y + 38 * s), (x + k * 33 * s, y + 112 * s)], 4 * s + 1.5, (70, 60, 90), seed=seed + 5 + k, boil=0.4, n=2, taper=(0, 0))
    blob(cv, rect_pts([(x - 36 * s, y + 112 * s), (x + 36 * s, y + 112 * s), (x + 30 * s, y + 126 * s), (x - 30 * s, y + 126 * s)], 2), (70, 60, 90), w=3.5,
         seed=seed + 8, boil=0.5, n=2)


def T040_kill_him(cv, t, T, A):
    red = eseg(t, B40["darker"] + 0.1, B40["darker"] + 1.3)
    swell = eseg(t, B40["anyone"] + 0.4, 7.3)
    reach = eseg(t, B40["hands"], B40["hands"] + 1.5)
    close = eseg(t, B40["would"] - 0.05, B40["would"] + 0.3)
    black = eseg(t, B40["would"] + 0.3, B40["would"] + 0.42)
    enter = eseg(t, B40["anyone"] - 0.1, B40["anyone"] + 1.3)
    if black < 1.0:
        z = 1.0 + 0.07 * eseg(t, 0, 10.3) + 0.05 * reach
        jx, jy = shake(1.0 + 5.0 * reach * (1 - close), seed=10500)
        cv.save(); cv.translate(W / 2 + jx, H / 2 + jy); cv.scale(z, z); cv.translate(-W / 2 - 50 * eseg(t, 3, 10.3), -H / 2 - 10)
        w.field(cv, mix(CV_ROCK_DK, (20, 0, 8), red))
        wall_tinted(cv, [(-200, -200), (2120, -200), (2120, 790), (-200, 810)], T, red * 0.85, seed=10100, cx=820, cy=560)
        rock_mass(cv, [(-300, -300), (2300, -300), (2300, -40), (1600, 20), (900, -10), (300, 40), (-300, 10)], seed=10110, rgb=mix(CV_ROCK, (46, 6, 26), red),
                  rim=mix(P_["orange"], P_["red"], red))
        lk = 0.35 + 0.65 * eseg(t, B40["light"] - 0.2, B40["light"] + 0.5) * (1 - 0.7 * eseg(t, B40["hands"], B40["hands"] + 1.0))
        lx_, ly_ = 1760, 92
        glow(cv, lx_, ly_, 260 * lk + 40, (255, 240, 190), a=int(200 * lk))     # far up the path: a sliver of daylight
        sun_rays(cv, lx_, ly_ - 20, 900, T, n=7, a=int(70 * lk), ang0=125, span=40, rgb=(255, 240, 190))
        blob(cv, [(lx_ - 66, ly_ - 46), (lx_ + 56, ly_ - 52), (lx_ + 70, ly_ + 14), (lx_ + 8, ly_ + 44), (lx_ - 58, ly_ + 22)], (255, 250, 225), w=4.5, seed=10135,
             boil=0.6, n=4, a=int(255 * min(1.0, lk + 0.3)))
        for k in range(9):                                         # stalactites
            sx = 70 + k * 205 + 30 * math.sin(k * 1.9)
            if abs(sx - lx_) < 120:
                continue
            L = 80 + 90 * hsh(10136 + k)
            y0 = 30 + 20 * math.sin(k * 2.3)
            blob(cv, [(sx - 30, y0), (sx + 30, y0), (sx + 4, y0 + L), (sx - 3, y0 + L + 10)], mix(CV_ROCK2, (60, 8, 30), red), w=4, seed=10140 + k, boil=0.7, n=3,
                 shade=lambda c, sx=sx, y0=y0, L=L: c.drawPath(poly_path([(sx + 8, y0), (sx + 30, y0), (sx + 4, y0 + L)]), paint(mix(P_["orange"], P_["red"], red), 70)))
        if t < B40["darker"] + 1.4:                                  # the ordinary shadow show, before it turns
            ph = (t * 0.16 + 0.15) % 1.0
            shadow_shape(cv, "hand_bunny", 1500 - ph * 900, 330, 1.6, T, seed=10130, a=int(230 * (1 - eseg(t, B40["darker"], B40["darker"] + 1.2))))
        prs = [(250, 1000), (530, 985), (810, 1000), (1090, 985)]
        gx = lerp(2100, 1580, enter) + 50 * reach
        gfeet, gs = 1045, 0.72
        gy = gfeet - 478 * gs
        mons = [(250, 1.45, 0.0), (650, 1.75, 0.35), (1050, 1.55, 0.7)]
        for k, (mx_, ms, lag) in enumerate(mons):                  # the shadows swell into monsters, leaning toward him
            sw = eseg(swell, lag * 0.35, lag * 0.35 + 0.65)
            sc = 1.0 + (ms - 1.0) * sw
            monster_shadow(cv, mx_, 785, sc, T, sw, lean=0.2 * sw + 0.1 * reach, seed=10200 + k * 11, chomp=abs(math.sin(T * 6 + k * 1.3)) * sw,
                           wall_rgb=mix((255, 150, 90), (255, 90, 70), red))
        gshx = gx - 20
        T_CLAW[0] = T
        if reach > 0:                                              # giant shadow hands come for him across the wall
            for k, (ax, ay, sz, ang0) in enumerate(((760, 260, 1.2, 12.0), (1140, 480, 1.05, -14.0))):
                tx, ty = gshx - 40 + 30 * k, 460 + 150 * k + 30 * math.sin(T * 3 + k)
                hx = lerp(ax + 60, tx - 170 * (1 - close), reach)
                hy = lerp(ay + 30, ty, reach)
                shadow_claw(cv, hx, hy, sz, ang0 + 15 * (1 - reach), open_k=1.0 - 0.85 * close, seed=10300 + k * 7, arm_from=(ax, ay),
                            rim=mix((255, 140, 90), (255, 70, 50), red))
        rock_mass(cv, [(-300, 800), (900, 780), (2300, 800), (2300, 1400), (-300, 1400)], seed=10120, rgb=mix(CV_ROCK2, (56, 8, 30), red),
                  rim=mix(P_["orange"], P_["red"], red), ink=5)
        for k, (mx_, my_, sc) in enumerate(((680, 1070, 0.9), (1400, 1060, 0.8))):
            glow_mushroom(cv, mx_, my_, sc, T, seed=10140 + k)
        rattle = reach * (1 - close)
        for k, (px, py) in enumerate(prs):                         # the prisoners from behind, chains rattling once the hands come
            jit_x = rattle * 7 * math.sin(T * 47 + k * 2)
            pris(cv, px + jit_x, py, 1.25, T, seed=10600 + k * 13, view="back", face=1, anchor=(px + 120, py + 8), rgb=mix(PRIS_COLS[k % 4], (36, 4, 22), 0.45 * red),
                 rim=(mix(P_["orange"], P_["red"], red), -1))
        for k in range(len(prs) - 1):
            chain(cv, (prs[k][0] + 70, prs[k][1] - 50), (prs[k + 1][0] - 70, prs[k + 1][1] - 50), seed=10650 + k, link=17, sag=20 + 8 * rattle * math.sin(T * 30 + k),
                  w=3.2, rgb=mix((150, 150, 175), P_["white"], 0.45 * rattle))
            if rattle > 0.2:
                cxm = (prs[k][0] + prs[k + 1][0]) / 2
                for j in (-1, 1):
                    line(cv, [(cxm + j * 34, prs[k][1] - 95), (cxm + j * 54, prs[k][1] - 122)], 4.5, P_["cream"], seed=10660 + k + j, boil=0.6, n=2, taper=(0.2, 0.2),
                         a=int(230 * rattle))
        reach_out = eseg(t, B40["anyone"] + 1.2, B40["anyone"] + 1.7) * (1 - eseg(t, B40["light"], B40["light"] + 0.3))
        point_up = eseg(t, B40["light"], B40["light"] + 0.35) * (1 - eseg(t, B40["hands"] + 0.1, B40["hands"] + 0.4))
        fear = eseg(t, B40["hands"] + 0.3, B40["hands"] + 0.7)
        walking = enter < 0.98 and t > B40["anyone"] - 0.1
        if point_up > 0.3:
            armL = (-110, -175, -95, "point")
        elif reach_out > 0.2:
            armL = (-250, 150, 180, "open")
        elif fear > 0.3:
            armL = (-170, 60, 200, "spread")
        else:
            armL = (-150, 300, 100, "open")
        hand_r = (150, -60 - 20 * fear, -95, "fist")
        swg = 16 * math.sin(T * 2.5) + 22 * fear * math.sin(T * 9)
        if enter > 0.0:
            gary_x(cv, gx, gy, gs, T, seed=4400, loud=0.0, look=(-0.8 + 0.5 * point_up + 0.3 * fear, -0.7 * point_up - 0.4 * fear), pk=1.0 - 0.5 * fear,
                   lids=lid_mix(lid_mix("neutral", "resolve", 0.35), "wide", fear), mouth="o" if fear > 0.5 else "line",
                   legs=("walk", T * 9) if walking else "stand", bob=0.0, armL=armL, armR=hand_r, sweat=fear)
            lhx, lhy = gx + 150 * gs, gy + (-60 - 20 * fear) * gs
            cv.save(); cv.translate(lhx, lhy); cv.rotate(swg); cv.translate(-lhx, -lhy)
            lantern(cv, lhx, lhy + 14 * gs, gs * 1.15, T)
            cv.restore()
        fire_x(cv, 170, 1185, 1.9, T, [mix(a, b, red) for a, b in zip(FIRE_N, FIRE_R)], seed=10700, intensity=1.0 + 0.2 * red)
        firelight(cv, 240, 960, 950, T, a=int(110 + 50 * red), rgb=mix(P_["orange"], P_["red"], red), seed=10710)
        if close > 0:
            darkness(cv, int(200 * close))
        cv.restore()
        vignette(cv, a=int(140 + 70 * red))
        if black > 0:
            tint(cv, (6, 0, 4), int(255 * black))
    if black > 0.02:                                               # the stark beat: only his lantern, then it goes out
        out = eseg(t, B40["kill"] + 0.12, B40["kill"] + 0.3)
        fk = (0.35 + 0.65 * float(hsh(core.D * 1.9))) if t > B40["kill"] - 0.2 else 1.0
        flame = (1 - out) * fk
        if black < 1:
            cv.saveLayerAlpha(None, int(255 * black))
        w.field(cv, (6, 0, 4))
        gx2, gy2, gs2 = 860, 470, 1.3
        lhx, lhy = gx2 + 150 * gs2, gy2 - 70 * gs2
        if flame > 0.01:
            glow(cv, lhx, lhy + 80, 640 * flame, (255, 170, 60), a=int(80 * flame))
            gary_x(cv, gx2, gy2, gs2, T, seed=4400, loud=0.0, look=(0.15, -0.35), pk=0.4, lids="wide", mouth="o", armL=(-170, 60, 200, "spread"),
                   armR=(150, -70, -95, "fist"), bob=0.0, sweat=1.0)
            tint(cv, (255, 150, 40), int(40 * flame))
            pool = skia.Paint(AntiAlias=True)                       # the only light is his lantern
            rr = 260 + 520 * flame
            pool.setShader(skia.GradientShader.MakeRadial(skia.Point(lhx, lhy + 90), rr, [core.C((6, 0, 4), 0), core.C((6, 0, 4), 90), core.C((6, 0, 4), 255)],
                                                          [0.0, 0.45, 1.0]))
            cv.drawRect(R(-50, -50, W + 50, H + 50), pool)
            lantern(cv, lhx, lhy + 18, 1.5, T, flame=flame)
        else:
            silhouette(cv, lambda c: lantern(c, lhx, lhy + 18, 1.5, T, flame=0.0, glow_a=0.0), (26, 14, 30))
        if out > 0:                                                # a thin curl of smoke over a dying ember
            for k in range(3):
                u = clamp01((t - B40["kill"] - 0.2) / 1.0 - k * 0.12)
                if u <= 0:
                    continue
                pts = [(lhx + 20 * math.sin(T * 2.5 + j * 0.9 + k) * (j / 6), lhy + 150 - j * 40 * (0.3 + u)) for j in range(7)]
                line(cv, pts, 7 - k, (130, 120, 140), seed=10800 + k, boil=0.6, n=5, taper=(0.1, 0.8), a=int(160 * (1 - u * 0.5)))
            em = 1 - eseg(t, B40["kill"] + 0.3, 12.2)
            glow(cv, lhx, lhy + 150, 60, (255, 60, 30), a=int(150 * em))
            dots(cv, [(lhx, lhy + 152)], 6, (255, 90, 40), a=int(255 * em))
            ek = eseg(t, B40["kill"] + 0.45, B40["kill"] + 0.9)    # and in the dark, something watching
            for k, (mx_, my_) in enumerate(((420, 330), (1560, 280))):
                bl = 1.0 if (T * 0.8 + k * 1.7) % 2.6 > 0.14 else 0.1
                for side in (-1, 1):
                    exx = mx_ + side * 50
                    glow(cv, exx, my_, 70, (255, 30, 20), a=int(90 * ek))
                    cv.drawPath(poly_path([(exx - side * 38, my_ - 4), (exx + side * 32, my_ - 20 * bl), (exx + side * 28, my_ + 7)]), paint((255, 70, 50), int(230 * ek)))
        if black < 1:
            cv.restore()


# ===================================================================== T042 -- Socrates (a psychedelic Greek vase painting)
B42 = dict(plato=0.17, teacher=2.38, asking=4.12, year=8.42, trial=10.62, death=12.92)
FIG = (28, 10, 38)             # black-figure glaze
FIG2 = (58, 24, 76)            # limbs / heads, a hair lighter so overlaps read
INC = (255, 200, 150)          # incised lines (the clay showing through)
CLAY = (255, 132, 40)
GROUND = 868


def meander(cv, x0, x1, y0, y1, phase=0.0, rgb=None, bg=None, seed=11000):
    """A Greek-key border band from y0 to y1 between x0 and x1."""
    rgb = rgb or CLAY
    bg = bg or FIG
    h = y1 - y0
    cv.drawRect(R(x0 - 10, y0, x1 + 10, y1), paint(bg))
    t0, b0 = y0 + h * 0.2, y1 - h * 0.2
    hh = b0 - t0
    c = hh * 1.15
    p = skia.Path()
    k0 = int(math.floor((x0 - phase) / c)) - 1
    k1 = int(math.ceil((x1 - phase) / c)) + 1
    for k in range(k0, k1):
        xa = phase + k * c
        p.moveTo(xa, b0); p.lineTo(xa, t0); p.lineTo(xa + 0.78 * c, t0); p.lineTo(xa + 0.78 * c, t0 + 0.66 * hh); p.lineTo(xa + 0.34 * c, t0 + 0.66 * hh)
        p.lineTo(xa + 0.34 * c, t0 + 0.33 * hh)
        p.moveTo(xa, b0); p.lineTo(xa + c, b0)
    st = skia.Paint(AntiAlias=True, Color=core.C(rgb))
    st.setStyle(skia.Paint.kStroke_Style); st.setStrokeWidth(max(2.0, hh * 0.13)); st.setStrokeJoin(skia.Paint.kMiter_Join)
    cv.drawPath(p, st)
    for yy in (y0 + h * 0.07, y1 - h * 0.07):
        cv.drawLine(x0 - 10, yy, x1 + 10, yy, paint(P_["hotpink"], stroke=max(2.0, h * 0.05)))


def rosette(cv, x, y, r, rgb, seed=0, T=0.0):
    """A neon filler rosette (vase-painting ornament) that slowly spins."""
    n = 8
    for k in range(n):
        a = k / n * 2 * math.pi + T * 0.4 + seed
        dots(cv, [(x + r * math.cos(a), y + r * math.sin(a))], r * 0.32, rgb)
    dots(cv, [(x, y)], r * 0.38, P_["cream"])
    dots(cv, [(x, y)], r * 0.18, FIG)


def spiral_orn(cv, x, y, r, rgb, seed=0, T=0.0):
    pts = [(x + (u / 9.0) * r * math.cos(u * 1.1 + T * 0.6 + seed), y + (u / 9.0) * r * math.sin(u * 1.1 + T * 0.6 + seed)) for u in np.linspace(0.3, 9, 30)]
    line(cv, pts, max(2.0, r * 0.12), rgb, seed=seed, boil=0.5, n=3, taper=(0.1, 0.4))


def column(cv, x, ytop, ybot, wd, seed=11100, rgb=None):
    """A Doric column, painted in a darker clay tone with incised flutes."""
    rgb = rgb or mix(CLAY, P_["red"], 0.35)
    blob(cv, rect_pts([(x - wd * 0.5, ytop + 40), (x + wd * 0.5, ytop + 40), (x + wd * 0.56, ybot), (x - wd * 0.56, ybot)], 3), rgb, w=4.5, seed=seed, boil=0.7, n=3,
         shade=lambda c: [c.drawLine(x - wd * 0.4 + j * wd * 0.2, ytop + 50, x - wd * 0.45 + j * wd * 0.225, ybot - 6, paint(mix(rgb, FIG, 0.35), stroke=3)) for j in range(5)])
    blob(cv, rect_pts([(x - wd * 0.8, ytop), (x + wd * 0.8, ytop), (x + wd * 0.62, ytop + 42), (x - wd * 0.62, ytop + 42)], 2), rgb, w=4.5, seed=seed + 1, boil=0.6, n=2)
    blob(cv, rect_pts([(x - wd * 0.7, ybot - 4), (x + wd * 0.7, ybot - 4), (x + wd * 0.75, ybot + 16), (x - wd * 0.75, ybot + 16)], 2), rgb, w=4, seed=seed + 2, boil=0.6, n=2)


def greek_fig(cv, x, gy, s, T, facing=1, seed=11200, bald=False, beard="short", robe=None, accent=None, eye="open", look=(0.0, 0.0), mouth=0.0,
              armF=None, armB=None, walk=None, lean=0.0, snub=False, eye_big=False, brow=0.0, helmet=False, woman=False, hair_rgb=None, sit=False):
    """A black-figure person in profile (feet at x, gy; facing +1 = right). Silhouette in glaze, details incised, added neon colours,
    a big white vase-painting eye. armF / armB: (hx, hy, ang, pose) in s-units relative to (x, gy) (front arm drawn over the body)."""
    f = facing
    robe = robe or FIG
    accent = accent or P_["magenta"]
    cv.save()
    cv.translate(x, gy); cv.rotate(lean); cv.translate(-x, -gy)
    r = (84 if bald else 70) * s
    hx, hy = x + 10 * f * s, gy - (505 if not sit else 410) * s
    shy = hy + r + 8 * s
    hem = gy - (78 if not sit else 150) * s
    ph = walk if walk is not None else 0.0

    def arm(spec, seed_, front):
        if spec is None:
            return
        ax, ay, ang, pose = spec
        sx = x + (24 if front else -18) * f * s
        sy = shy + 8 * s
        hxp, hyp = x + ax * s, gy + ay * s
        el = tuple(_limb_elbow((sx, sy), (hxp, hyp), -f if not front else f, s * 0.35, bend=0.7))
        tube(cv, [(sx, sy), el, (hxp, hyp)], 24 * s, FIG2, w=3.5, seed=seed_, boil=0.7, n=6)
        cv.save(); cv.translate(hxp, hyp); cv.scale(s * 0.95, s * 0.95)
        _hand(cv, 0, 0, ang, pose, 1 if f > 0 else -1, seed_ + 2, rgb=FIG2)
        cv.restore()
    arm(armB, seed + 1, False)
    if sit:                                                        # a stool (diphros)
        blob(cv, rect_pts([(x - 90 * s, gy - 150 * s), (x + 70 * s, gy - 150 * s), (x + 64 * s, gy - 130 * s), (x - 84 * s, gy - 130 * s)], 2), FIG, w=3.5, seed=seed + 40,
             boil=0.6, n=2)
        for lx in (-70, 50):
            line(cv, [(x + lx * s, gy - 132 * s), (x + (lx + 6) * s, gy)], 9 * s + 1, FIG, seed=seed + 41 + lx, boil=0.5, n=2, taper=(0, 0))
    for side in (-1, 1):                                           # legs
        if sit:
            kx, ky = x + f * 70 * s + side * 10 * s, gy - 150 * s
            fx_, fy_ = x + f * 80 * s + side * 16 * s, gy - 6 * s
            tube(cv, [(x + side * 14 * s, gy - 150 * s), (kx, ky), (fx_, fy_)], 24 * s, FIG2, w=3.5, seed=seed + 5 + side, boil=0.6, n=4)
        else:
            sw = math.sin(ph + (0 if side < 0 else math.pi)) * 34 * s if walk is not None else side * 12 * s
            lift = max(0.0, -math.cos(ph + (0 if side < 0 else math.pi))) * 16 * s if walk is not None else 0.0
            fx_, fy_ = x + sw, gy - 6 * s - lift
            tube(cv, [(x + side * 16 * s, hem + 10 * s), (fx_, fy_ - 20 * s)], 24 * s, FIG2, w=3.5, seed=seed + 5 + side, boil=0.6, n=3)
        blob(cv, [(fx_ - 14 * s * f, fy_ - 14 * s), (fx_ + 30 * s * f, fy_ - 8 * s), (fx_ + 34 * s * f, fy_ + 4 * s), (fx_ - 16 * s * f, fy_ + 4 * s)], FIG2, w=3, seed=seed + 8 + side,
             boil=0.5, n=3)
        line(cv, [(fx_ - 6 * s * f, fy_ - 12 * s), (fx_ + 10 * s * f, fy_ - 2 * s)], 2.5, INC, seed=seed + 10 + side, boil=0.4, n=2, taper=(0.1, 0.1), a=200)
    sway = 10 * s * math.sin(ph) if walk is not None else 0.0
    rb = [(x - 46 * s * f, shy - 4 * s), (x + 40 * s * f, shy - 6 * s), (x + 58 * s * f, shy + 80 * s), (x + 66 * s * f + sway, hem), (x - 78 * s * f + sway, hem + 4 * s),
          (x - 70 * s * f, shy + 120 * s)]
    if sit:
        rb = [(x - 50 * s * f, shy - 4 * s), (x + 40 * s * f, shy - 6 * s), (x + 56 * s * f, shy + 80 * s), (x + 120 * s * f, hem - 10 * s), (x + 110 * s * f, hem + 30 * s),
              (x - 80 * s * f, hem + 20 * s), (x - 72 * s * f, shy + 100 * s)]

    def robe_sh(c):
        for j in range(4):                                         # incised drapery folds
            yy = shy + 60 * s + j * 70 * s
            line(c, [(x - 50 * s * f, yy - 20 * s), (x + 10 * s * f, yy + 10 * s), (x + 60 * s * f, yy - 30 * s)], 2.6, INC, seed=seed + 20 + j, boil=0.6, n=4,
                 taper=(0.2, 0.2), a=170)
        c.drawRect(R(x - 140 * s, hem - 26 * s, x + 140 * s, hem - 8 * s), paint(accent))
        dots(c, [(x - 120 * s + j * 30 * s, hem - 17 * s) for j in range(9)], 3.5 * s + 0.8, P_["cream"])
        for j in range(5):
            dots(c, [(x + (-40 + 22 * j) * s * f, shy + (90 + 40 * (j % 2)) * s)], 4.5 * s + 0.8, accent)
    blob(cv, rb, robe, w=4.5, seed=seed + 15, boil=0.9, n=4, shade=robe_sh)
    arm_neck = [(hx - 16 * s * f, hy + 30 * s), (hx + 14 * s * f, hy + 34 * s), (hx + 20 * s * f, shy + 6 * s), (hx - 24 * s * f, shy + 6 * s)]
    blob(cv, arm_neck, FIG2, w=3.5, seed=seed + 16, boil=0.6, n=3)
    # head (profile): skull + nose
    head = ell(hx, hy, r, r * (1.05 if bald else 1.0), n=12)
    blob(cv, head, FIG2, w=4.5, seed=seed + 17, boil=0.8)
    if snub:
        blob(cv, ell(hx + f * (r * 0.97), hy + 14 * s, 22 * s, 19 * s, n=8), FIG2, w=3.5, seed=seed + 18, boil=0.5,
             shade=lambda c: c.drawPath(poly_path(cr_closed(ell(hx + f * (r * 0.97 + 6 * s), hy + 20 * s, 7 * s, 5 * s, n=6), 3)), paint(INC, 150)))
    else:
        blob(cv, [(hx + f * r * 0.8, hy - 8 * s), (hx + f * (r + 20 * s), hy + 14 * s), (hx + f * r * 0.8, hy + 18 * s)], FIG2, w=3.5, seed=seed + 18, boil=0.5, n=2)
    if bald:                                                       # a fringe at the back + incised forehead lines
        blob(cv, [(hx - f * r * 0.95, hy - 6 * s), (hx - f * r * 0.7, hy + 30 * s), (hx - f * r * 0.2, hy + 40 * s), (hx - f * r * 0.5, hy + 4 * s)], FIG, w=3, seed=seed + 19,
             boil=0.5, n=3)
        for j in range(3):
            line(cv, [(hx - 6 * s * f + j * 4 * s * f, hy - r * 0.62 + j * 10 * s), (hx + f * r * 0.5, hy - r * 0.6 + j * 10 * s)], 2.2, INC, seed=seed + 21 + j, boil=0.5,
                 n=3, taper=(0.3, 0.3), a=170)
    elif helmet:
        blob(cv, [(hx - r * 1.1, hy + 24 * s), (hx - r * 1.05, hy - r * 0.8), (hx, hy - r * 1.2), (hx + r * 1.05, hy - r * 0.8), (hx + f * r * 1.1, hy + 6 * s),
                  (hx + f * r * 0.35, hy + 4 * s), (hx + f * r * 0.3, hy + 40 * s), (hx - f * r * 0.2, hy + 40 * s)], FIG, w=4, seed=seed + 19, boil=0.6, n=4,
             shade=lambda c: c.drawRect(R(hx - r * 1.2, hy - r * 0.35, hx + r * 1.2, hy - r * 0.22), paint(INC, 160)))
        crest = [(hx - f * r * 1.4, hy - r * 0.6), (hx - f * r * 0.6, hy - r * 1.9), (hx + f * r * 0.7, hy - r * 1.75), (hx + f * r * 0.9, hy - r * 1.05),
                 (hx, hy - r * 1.15)]
        blob(cv, crest, accent, w=4, seed=seed + 22, boil=0.8, n=4,
             shade=lambda c: [c.drawLine(hx - r * 1.4 + j * r * 0.35, hy - r * 2.0, hx - r * 1.2 + j * r * 0.35, hy - r * 1.0, paint(FIG, stroke=2.5)) for j in range(8)])
    else:
        hr = hair_rgb or FIG
        cap = [(hx - f * r * 1.05, hy + (60 if woman else 20) * s), (hx - f * r * 1.05, hy - r * 0.5), (hx - f * r * 0.3, hy - r * 1.08), (hx + f * r * 0.55, hy - r * 0.9),
               (hx + f * r * 0.4, hy - r * 0.45), (hx - f * r * 0.1, hy - r * 0.3), (hx - f * r * 0.3, hy + 10 * s)]
        blob(cv, cap, hr, w=3.5, seed=seed + 19, boil=0.6, n=4,
             shade=lambda c: [line(c, [(hx - f * r * 0.9, hy - r * 0.5 + j * 18 * s), (hx - f * r * 0.4, hy - r * 0.62 + j * 18 * s), (hx + f * r * 0.2, hy - r * 0.6 + j * 16 * s)],
                                   2.2, INC, seed=seed + 23 + j, boil=0.5, n=3, taper=(0.2, 0.2), a=150) for j in range(3)])
        line(cv, [(hx - f * r * 1.0, hy - r * 0.2), (hx - f * r * 0.2, hy - r * 0.75), (hx + f * r * 0.45, hy - r * 0.62)], 6 * s + 1.5, accent, seed=seed + 26, boil=0.5, n=3,
             taper=(0.1, 0.1))
        if woman:
            blob(cv, ell(hx - f * r * 1.05, hy - r * 0.35, r * 0.42, r * 0.36, n=8), hr, w=3.5, seed=seed + 27, boil=0.5)
    if beard:
        if beard == "bushy":
            bd = [(hx - f * r * 0.5, hy + 4 * s), (hx + f * r * 0.8, hy + 34 * s), (hx + f * r * 1.0, hy + r * 0.95), (hx + f * r * 0.6, hy + r * 1.62), (hx - f * r * 0.05, hy + r * 1.8),
                  (hx - f * r * 0.62, hy + r * 1.3), (hx - f * r * 0.78, hy + r * 0.55)]
        else:
            bd = [(hx - f * r * 0.3, hy + 18 * s), (hx + f * r * 0.85, hy + 34 * s), (hx + f * r * 0.72, hy + r * 1.05), (hx + f * r * 0.2, hy + r * 1.28), (hx - f * r * 0.35, hy + r * 0.72)]
        nb = 9 if beard == "bushy" else 4

        def curls(c):
            for j in range(nb):
                cx_ = hx + f * (-0.35 + 0.33 * (j % 3)) * r
                cy_ = hy + (0.45 + 0.36 * (j // 3)) * r
                line(c, [(cx_ - f * 0.12 * r, cy_), (cx_, cy_ + 0.12 * r), (cx_ + f * 0.12 * r, cy_), (cx_ + f * 0.04 * r, cy_ - 0.08 * r)], 3.0, INC, seed=seed + 30 + j,
                     boil=0.5, n=3, taper=(0.2, 0.2), a=200)
        P = blob(cv, bd, FIG, w=0, seed=seed + 28, boil=0.7, n=4, shade=curls, misreg=(0, 0))
        brush(cv, P, 3.0, INC, closed=True, seed=seed + 29, a=170)
    # the eye: added white, enormous for the vase-painting look
    ex, ey = hx + f * r * 0.42, hy - 6 * s
    if eye == "closed":
        blob(cv, ell(ex, ey, 30 * s, 20 * s, n=10), FIG2, w=0, seed=seed + 34, boil=0.3, misreg=(0, 0))
        line(cv, [(ex - 26 * s, ey - 2 * s), (ex, ey + 9 * s), (ex + 26 * s, ey - 2 * s)], 4.5, INC, seed=seed + 35, boil=0.4, n=3, taper=(0.2, 0.2))
    else:
        erx, ery = (31 * s, 31 * s) if eye_big else (33 * s, 19 * s)
        if eye == "roll":
            look = (0.0, -0.9)
        blob(cv, ell(ex, ey, erx, ery, n=10), P_["white"], w=3.0, seed=seed + 35, boil=0.4)
        pr = (12 if eye_big else 10) * s
        dots(cv, [(ex + look[0] * erx * 0.45 + f * 2 * s, ey + look[1] * ery * 0.5)], pr, FIG)
        if eye == "lid":
            cv.drawPath(poly_path([(ex - erx * 1.1, ey - ery * 1.2), (ex + erx * 1.1, ey - ery * 1.2), (ex + erx * 1.1, ey - ery * 0.1), (ex - erx * 1.1, ey + ery * 0.1)]),
                        paint(FIG2))
    if brow:
        line(cv, [(ex - 28 * s, ey - 30 * s - brow * 12 * s * f), (ex + 28 * s, ey - 30 * s + brow * 12 * s * f)], 5, INC, seed=seed + 36, boil=0.4, n=2, taper=(0.2, 0.2))
    mx, my = hx + f * r * 0.62, hy + r * 0.55
    if mouth > 0.05:
        blob(cv, ell(mx, my, 11 * s, (4 + 10 * mouth) * s, n=8), (120, 10, 40), w=2.5, seed=seed + 37, boil=0.4)
    else:
        line(cv, [(mx - 10 * s * f, my), (mx + 6 * s * f, my - 2 * s)], 2.5, INC, seed=seed + 37, boil=0.4, n=2, taper=(0.2, 0.2), a=200)
    arm(armF, seed + 3, True)
    cv.restore()
    return (hx, hy, r)


def kylix(cv, x, y, s, T, seed=11300, wisp=1.0):
    """A black-figure drinking cup (two handles, a stem) with a faint green wisp rising."""
    for side in (-1, 1):
        line(cv, [(x + side * 60 * s, y - 2 * s), (x + side * 84 * s, y - 14 * s), (x + side * 92 * s, y - 2 * s), (x + side * 74 * s, y + 6 * s)], 6 * s + 1.5, FIG, seed=seed + side,
             boil=0.4, n=4, taper=(0, 0))
    blob(cv, [(x - 72 * s, y - 6 * s), (x + 72 * s, y - 6 * s), (x + 50 * s, y + 18 * s), (x, y + 26 * s), (x - 50 * s, y + 18 * s)], FIG, w=3.5, seed=seed + 3, boil=0.5, n=4,
         shade=lambda c: c.drawRect(R(x - 80 * s, y + 2 * s, x + 80 * s, y + 8 * s), paint(P_["acid"], 200)))
    line(cv, [(x, y + 24 * s), (x, y + 50 * s)], 8 * s + 1.5, FIG, seed=seed + 4, boil=0.4, n=2, taper=(0, 0))
    blob(cv, ell(x, y + 54 * s, 26 * s, 7 * s, n=8), FIG, w=3, seed=seed + 5, boil=0.4)
    if wisp > 0:
        for k in range(3):
            pts = [(x - 20 * s + k * 20 * s + 14 * s * math.sin(T * 1.6 + j * 0.8 + k), y - 12 * s - j * 26 * s) for j in range(6)]
            line(cv, pts, 4 * s + 1, P_["acid"], seed=seed + 10 + k, boil=0.5, n=4, taper=(0.3, 0.8), a=int(170 * wisp))


def urn(cv, x, gy, s, seed=11400, label_rgb=None):
    """A voting urn (a little amphora painted on the amphora)."""
    body = [(x - 26 * s, gy - 190 * s), (x + 26 * s, gy - 190 * s), (x + 30 * s, gy - 160 * s), (x + 78 * s, gy - 110 * s), (x + 74 * s, gy - 40 * s), (x + 36 * s, gy - 8 * s),
            (x - 36 * s, gy - 8 * s), (x - 74 * s, gy - 40 * s), (x - 78 * s, gy - 110 * s), (x - 30 * s, gy - 160 * s)]
    for side in (-1, 1):
        line(cv, [(x + side * 28 * s, gy - 176 * s), (x + side * 70 * s, gy - 170 * s), (x + side * 66 * s, gy - 126 * s)], 7 * s + 1.5, FIG, seed=seed + side, boil=0.4, n=4,
             taper=(0, 0))
    blob(cv, body, FIG, w=4, seed=seed, boil=0.7, n=4,
         shade=lambda c: (c.drawRect(R(x - 90 * s, gy - 100 * s, x + 90 * s, gy - 82 * s), paint(label_rgb or P_["teal"])),
                          c.drawRect(R(x - 90 * s, gy - 70 * s, x + 90 * s, gy - 62 * s), paint(INC, 180))))
    blob(cv, ell(x, gy - 192 * s, 34 * s, 9 * s, n=8), FIG, w=3, seed=seed + 4, boil=0.4)


def frieze_view(cv, fx, t, T, socr_fx=None, phase=0.0):
    """One 1920x1080 view of the long painted frieze, starting at frieze-x fx. Everything is placed in frieze coordinates."""
    rad_rect(cv, (0, 0, W, H), 960, 520, 1150, [(255, 196, 70), (255, 150, 40), CLAY, (240, 70, 90)], [0.0, 0.35, 0.7, 1.0])
    stipple(cv, mix(CLAY, P_["red"], 0.4), (0, 100, W, 960), spacing=19, r=2.0, seed=11500, fn=lambda X, Y: np.clip(np.abs(Y - 520) / 600.0, 0, 1) * 0.8)

    def vis(px, half=400):
        return -half < px - fx < W + half
    cols = [P_["hotpink"], P_["teal"], P_["yellow"], P_["cream"], P_["acid"], P_["violet"]]
    for k in range(int(fx // 230) - 1, int((fx + W) // 230) + 2):  # neon filler ornaments
        ox = k * 230 + 60 * math.sin(k * 1.7) - fx
        oy = 200 + 120 * hsh(k * 3.3 + 11)
        if hsh(k * 7.7) > 0.5:
            rosette(cv, ox, oy, 22 + 10 * hsh(k), cols[k % 6], seed=k, T=T)
        else:
            spiral_orn(cv, ox, oy, 34, cols[(k + 2) % 6], seed=k * 1.3, T=T)
    # architecture
    for k in range(12):                                            # the agora stoa
        cxp = 140 + k * 320
        if vis(cxp, 200) and cxp < 3150:
            column(cv, cxp - fx, 150, GROUND, 74, seed=11600 + k)
    if vis(1800, 2200):
        blob(cv, rect_pts([(40 - fx, 108), (3260 - fx, 108), (3260 - fx, 150), (40 - fx, 150)], 6), mix(CLAY, P_["red"], 0.45), w=4.5, seed=11650, boil=0.7, n=3,
             shade=lambda c: [c.drawRect(R(60 - fx + j * 80, 112, 84 - fx + j * 80, 146), paint(FIG, 160)) for j in range(41)])
    for k in range(4):                                             # the law court's pillars
        cxp = 3420 + k * 560
        if vis(cxp, 200):
            column(cv, cxp - fx, 150, GROUND, 90, seed=11700 + k, rgb=mix(CLAY, P_["magenta"], 0.3))
    if vis(WINDOW_X, 600):                                         # the prison: a barred window with a moon
        wx, wy = WINDOW_X - fx, 380
        beam = skia.Paint(AntiAlias=True)
        beam.setShader(skia.GradientShader.MakeLinear([skia.Point(wx, wy), skia.Point(wx - 500, GROUND)], [core.C(P_["cream"], 70), core.C(P_["cream"], 0)]))
        cv.drawPath(poly_path([(wx - 120, wy - 100), (wx + 110, wy + 110), (wx - 420, GROUND), (wx - 820, GROUND)]), beam)
        blob(cv, rect_pts([(wx - 130, wy - 120), (wx + 130, wy - 120), (wx + 130, wy + 120), (wx - 130, wy + 120)], 3), (40, 20, 90), w=5, seed=11750, boil=0.7, n=3,
             shade=lambda c: (w.stars(c, 11751, (wx - 130, wy - 120, wx + 130, wy + 120), n=30, big=2),
                              c.drawPath(poly_path(cr_closed(ell(wx + 40, wy - 30, 44, 44, n=12), 3)), paint(P_["cream"])),
                              c.drawPath(poly_path(cr_closed(ell(wx + 62, wy - 42, 40, 40, n=12), 3)), paint((40, 20, 90)))))
        for j in range(4):
            line(cv, [(wx - 90 + j * 60, wy - 120), (wx - 90 + j * 60, wy + 120)], 10, FIG, seed=11760 + j, boil=0.4, n=2, taper=(0, 0))
    cv.drawRect(R(0, GROUND + 2, W, 960), paint(mix(CLAY, P_["red"], 0.25)))
    line(cv, [(-20, GROUND), (W / 2, GROUND + 3), (W + 20, GROUND)], 7, FIG, seed=11800, boil=0.6, n=4, taper=(0, 0))
    _frieze_figures(cv, fx, t, T, vis, socr_fx)
    meander(cv, -20, W + 20, 0, 104, phase=-fx, seed=11810)
    meander(cv, -20, W + 20, 958, 1080, phase=-fx * 1.0 + 40, seed=11811)


def _socrates(cv, x, gy, s, T, seed=11900, **kw):
    """Socrates: bald dome, bushy beard, snub nose, bulging eye, a robe with a magenta border."""
    return greek_fig(cv, x, gy, s, T, seed=seed, bald=True, beard="bushy", snub=True, eye_big=True, accent=P_["magenta"], robe=(36, 14, 52), **kw)


ASKS = [(4.12, 5.05, "WHAT IS JUSTICE?"), (5.8, 6.6, "BUT... WHY?"), (7.25, 8.1, "HOW DO YOU KNOW?")]
CITIZENS = [(-1.0, -1.0, 4.95, 5.45), (5.2, 5.7, 6.5, 6.95), (6.7, 7.15, 7.95, 8.6)]   # enter0, enter1, exit0, exit1
SOC_AGORA, SPOT, SOC_TRIAL, SOC_CELL, WINDOW_X = 1000, 1450, 3700, 6060, 6520


def socr_fx(t):
    return SOC_AGORA, False


def citizen_off(t, k):
    """How far (frieze px) citizen k is from the questioning spot, and whether walking / leaving."""
    e0, e1, x0, x1 = CITIZENS[k]
    if e0 >= 0 and t < e0:
        return 1000.0, False, False
    if e0 >= 0 and t < e1:
        return lerp(1000, 0, ease(seg(t, e0, e1))), True, False
    if t < x0:
        return 0.0, False, False
    if t < x1:
        return lerp(0, 1000, ease(seg(t, x0, x1))), True, True
    return 1000.0, False, True


def _frieze_figures(cv, fx, t, T, vis, socr_x):
    # --- the agora: Plato taking notes, Socrates
    if vis(560):
        greek_fig(cv, 560 - fx, GROUND, 0.9, T, facing=1, seed=12000, beard="short", accent=P_["teal"], look=(0.6, 0.5),
                  armF=(80, -350 + 6 * math.sin(T * 9), 20, "pinch"), armB=(50, -320, -10, "hold"))
        sx, sy = 560 - fx + 80 * 0.9, GROUND - 320 * 0.9                # the scroll he writes on
        blob(cv, rect_pts([(sx - 10, sy - 44), (sx + 96, sy - 54), (sx + 102, sy + 44), (sx - 4, sy + 50)], 2), P_["cream"], w=3.5, seed=12010, boil=0.5, n=2,
             shade=lambda c: [c.drawLine(sx + 4, sy - 34 + j * 15, sx + 86, sy - 42 + j * 15, paint(FIG, stroke=2)) for j in range(5)])
    sfx, walking = socr_fx(t)
    ask = None
    for (a0, a1, txt) in ASKS:
        if a0 <= t < a1:
            ask = (a0, a1, txt)
    if vis(sfx):
        intro = pop(t, B42["teacher"], 0.4)
        if intro > 0.01 and t < B42["asking"] + 0.5:
            fade = 1 - eseg(t, B42["asking"], B42["asking"] + 0.5)
            glow(cv, sfx - fx + 10, GROUND - 505, 300 * intro, P_["yellow"], a=int(170 * fade))
            wedge_rays(cv, sfx - fx + 10, GROUND - 505, 340 * intro, 14, P_["cream"], 90 * fade, rot_deg=T * 20)
        talking = ask is not None and math.sin(T * 13) > -0.3
        point = ask is not None or (B42["teacher"] + 0.3 < t < B42["asking"])
        shrug = eseg(t, 8.2, 8.5) * (1 - eseg(t, 9.9, 10.1))
        if shrug > 0.05:                                           # left alone again: a cheerful shrug ('what did I say?')
            lift = 12 * abs(math.sin(T * 4))
            armF = (lerp(50, 112, shrug), lerp(-310, -350, shrug) - lift, lerp(90, -35, shrug), "open")
            armB = (lerp(-70, -100, shrug), lerp(-280, -350, shrug) - lift, lerp(120, -145, shrug), "open")
        elif point:
            armF, armB = (130, -520 + 12 * math.sin(T * 6), -80, "point"), (-70, -280, 120, "open")
        else:
            armF, armB = (50, -310, 90, "open"), (-70, -280, 120, "open")
        _socrates(cv, sfx - fx, GROUND, 1.0, T, facing=1, look=(0.75 - 0.6 * shrug, -0.1 - 0.4 * shrug), lean=3 * math.sin(T * 5) if ask is not None else 0,
                  mouth=0.7 * abs(math.sin(T * 11)) if talking else 0.0, armF=armF, armB=armB)
        if shrug > 0.3:
            qmark(cv, sfx - fx + 175, GROUND - 500 - 12 * math.sin(T * 5), 0.9 * pop(t, 8.3, 0.3), P_["yellow"], seed=12090, rot_deg=12 + 8 * math.sin(T * 3))
    for k, (pfx, col_fx, acc) in enumerate(((1712, 1740, P_["yellow"]), (2032, 2060, P_["teal"]))):
        if vis(pfx) and t < 10.2:
            duck = 0.5 + 0.5 * math.sin(T * (1.7 + 0.4 * k) + k * 2.0)
            hide = 80 * ease(clamp01(duck * 1.6 - 0.3))
            px_, py_ = pfx - fx + hide, GROUND - 520 + 60 * k
            blob(cv, ell(px_, py_, 64, 66, n=12), FIG2, w=4, seed=12050 + k, boil=0.7)
            blob(cv, [(px_ - 66, py_ - 4), (px_ - 90, py_ + 14), (px_ - 64, py_ + 22)], FIG2, w=3, seed=12052 + k, boil=0.5, n=2)
            line(cv, [(px_ + 60, py_ - 20), (px_ + 10, py_ - 62), (px_ - 50, py_ - 52)], 6, acc, seed=12054 + k, boil=0.5, n=3, taper=(0.1, 0.1))
            blob(cv, ell(px_ - 28, py_ - 6, 28, 17, n=10), P_["white"], w=3, seed=12056 + k, boil=0.4)
            dots(cv, [(px_ - 40, py_ - 4)], 9, FIG)
            column(cv, col_fx - fx, 150, GROUND, 74, seed=11600 + int((col_fx - 140) / 320))
    # --- the parade of citizens he pesters: each walks in, gets a question, and flees
    for k, (a0, a1, txt) in enumerate(ASKS):
        off, walking_c, leaving = citizen_off(t, k)
        cfx = SPOT + off
        if off >= 999 or not vis(cfx):
            continue
        ann = seg(t, a0 + 0.15, a1 - 0.1)
        x = cfx - fx
        face = 1 if leaving else -1
        wk = T * 10 if walking_c else None
        if k == 0:                                                 # a merchant with his amphora: eye-roll, steam, off he goes
            greek_fig(cv, x, GROUND, 0.95, T, facing=face, seed=12100, beard="short", accent=P_["teal"], walk=wk,
                      eye="roll" if 0.2 < ann < 0.85 and not leaving else ("lid" if ann >= 0.85 else "open"), look=(-0.6, 0), brow=1.0 if ann > 0.2 else 0.0,
                      armF=(face * 70, -300, 0 if face > 0 else 180, "hold"), armB=(face * -40, -280, 100, "open"))
            urn(cv, x + face * 84, GROUND - 200, 0.62, seed=12110, label_rgb=P_["yellow"])
            steam_k = ann
        elif k == 1:                                               # a hoplite hides behind his eye-shield and backs away
            greek_fig(cv, x, GROUND, 1.0, T, facing=-1, seed=12200, beard="short", helmet=True, accent=P_["hotpink"], look=(-0.7, 0.1), walk=wk,
                      eye="open" if ann < 0.4 else "lid", armB=(70, -600, -95, "fist"))
            line(cv, [(x + 80, GROUND - 700), (x + 60, GROUND)], 8, FIG, seed=12210, boil=0.4, n=2, taper=(0, 0))
            blob(cv, [(x + 74, GROUND - 744), (x + 96, GROUND - 700), (x + 64, GROUND - 700)], FIG, w=3, seed=12211, boil=0.4, n=2)
            shy = GROUND - 330 - 200 * ease(clamp01(ann * 1.8))
            blob(cv, ell(x - 70, shy, 130, 140, n=14), FIG, w=5, seed=12220, boil=0.8,
                 shade=lambda c: (c.drawPath(poly_path(cr_closed(ell(x - 70, shy, 108, 118, n=14), 3)), paint(P_["hotpink"])),
                                  c.drawPath(poly_path(cr_closed(ell(x - 70, shy, 86, 96, n=14), 3)), paint(FIG))))
            w.eye_glyph(cv, x - 70, shy, 1.05, look=(-0.6 + 0.3 * math.sin(T * 2), 0), seed=12221)
            if ann > 0.5:
                for j in range(2):
                    ph = (T * 1.4 + j * 0.5) % 1.0
                    yy = shy - 170 + ph * 60
                    blob(cv, [(x + 20 + j * 46, yy - 16), (x + 32 + j * 46, yy + 4), (x + 20 + j * 46, yy + 14), (x + 8 + j * 46, yy + 4)], P_["mint"], w=3, seed=12230 + j,
                         boil=0.4, n=4, a=int(255 * (1 - ph)))
            steam_k = 0.0
        else:                                                      # an orator: hands over his ears, then storms off
            greek_fig(cv, x, GROUND, 1.0, T, facing=face, seed=12300, beard="short", accent=P_["acid"], walk=wk,
                      eye="lid" if ann > 0.3 else "open", look=(-0.5, 0), brow=1.0 if ann > 0.25 else 0.0,
                      armF=(-28 * face * -1, -540, -100, "flat") if ann > 0.3 else (-100, -400, -150, "hold"),
                      armB=(18 * face * -1, -545, -80, "flat") if ann > 0.3 else (20, -300, 100, "open"))
            if ann <= 0.3:
                blob(cv, rect_pts([(x - 170, GROUND - 430), (x - 84, GROUND - 440), (x - 80, GROUND - 350), (x - 166, GROUND - 342)], 2), P_["cream"], w=3.5, seed=12310,
                     boil=0.5, n=2)
            steam_k = ann
        if steam_k > 0.35:                                         # steam puffs of irritation
            for j in range(3):
                ph = (T * 1.3 + j / 3) % 1.0
                blob(cv, ell(x + 10 + (j - 1) * 50 + 24 * ph, GROUND - 650 - ph * 150, 22 + 26 * ph, 16 + 18 * ph, n=8), P_["cream"], w=3, seed=12400 + k * 5 + j,
                     boil=0.6, a=int(230 * (1 - ph)))
    # --- the trial: jurors on two tiers behind panelled benches, pebbles into the voting urns
    if vis(SOC_TRIAL):
        _socrates(cv, SOC_TRIAL - fx, GROUND, 1.0, T, facing=1, seed=12500, eye="closed", armB=(-50, -310, 160, "fist"), armF=(-40, -320, 160, "fist"))
    if vis(4580, 900):
        x0b, x1b = 3980 - fx, 5160 - fx
        for row in (1, 0):
            s_ = 0.8 - row * 0.1
            rail = GROUND - 290 - row * 135
            for j in range(6):
                jx = 4080 + j * 190 + row * 95 - fx
                raise_ = row == 0 and (math.sin(T * 3 + j * 1.7) > 0.2)
                greek_fig(cv, jx, rail + 175 * s_ * 1.0 + (505 - 175) * s_ - 175 * s_, s_, T, facing=-1, seed=12700 + row * 50 + j * 7,
                          beard="short" if (j + row) % 3 else False, accent=[P_["teal"], P_["hotpink"], P_["yellow"]][(j + row) % 3], look=(-0.8, 0.3),
                          brow=0.8 if j % 2 else 0.0, armF=(-60, -620, -110, "pinch") if raise_ else (-70, -360, 160, "open"))
            blob(cv, rect_pts([(x0b + row * 50, rail - 20), (x1b, rail - 20), (x1b, rail + 135 if row else GROUND), (x0b + row * 50, rail + 135 if row else GROUND)], 6),
                 mix(CLAY, P_["red"], 0.45 + 0.1 * row), w=4.5, seed=12790 + row, boil=0.7, n=3,
                 shade=lambda c, rail=rail, row=row: ([c.drawRect(R(x0b + 40 + j * 150, rail + 10, x0b + 58 + j * 150, (rail + 125) if row else GROUND - 10), paint(FIG, 150))
                                                       for j in range(9)],
                                                      dots(c, [(x0b + 115 + j * 150, rail + 60) for j in range(8)], 9, P_["cream"])))
        for k in range(10):                                        # pebbles dropping into the urns
            ph = (T * 0.9 + k * 0.137) % 1.0
            ux = (4280, 4690)[k % 2]
            sx0 = ux + (70 if k % 2 else -50) + 30 * math.sin(k)
            px = lerp(sx0, ux, ph) - fx
            py = lerp(GROUND - 640, GROUND - 250, ph) - 120 * math.sin(ph * math.pi) * 0.4
            dots(cv, [(px, py)], 15, INK)
            dots(cv, [(px, py)], 11, FIG if k % 3 else P_["cream"])
    for k, ux in enumerate((4280, 4690)):
        if vis(ux):
            urn(cv, ux - fx, GROUND, 1.25, seed=12600 + k, label_rgb=[P_["red"], P_["cream"]][k])
    # --- the prison: Socrates with the cup
    if vis(SOC_CELL):
        lt_d = t - B42["death"]
        raise_k = eseg(lt_d, 0.2, 0.9)
        cupx, cupy = SOC_CELL - fx + 175 - 10 * raise_k, GROUND - 255 - 45 * raise_k
        _socrates(cv, SOC_CELL - fx, GROUND, 1.0, T, facing=1, seed=12900, sit=True, eye="closed" if lt_d > 1.3 else "open", look=(0.6, 0.6),
                  armF=(175 - 10 * raise_k, -255 - 45 * raise_k, -20, "hold"), armB=(80, -230, 30, "open"))
        kylix(cv, cupx + 12, cupy - 28, 1.1, T, seed=12950)
    if vis(7000):                                                  # Plato, head bowed, can't bear to watch
        greek_fig(cv, 7000 - fx, GROUND, 0.9, T, facing=-1, seed=12960, beard="short", accent=P_["teal"], eye="closed", lean=-6,
                  armF=(-40, -470, -120, "flat"), armB=(10, -300, 100, "open"))


def amphora(cv, T, k, cx, cy, fx, t, phase=0.0):
    """The whole vase: the frieze is its picture panel. k = panel scale (1 = the panel fills the frame), (cx, cy) = screen pos of the panel centre."""
    cv.save()
    cv.translate(cx, cy); cv.scale(k, k); cv.translate(-960, -540)
    with Ink(max(0.25, k) ** -0.55):
        body = [(960 - 300, -1000), (960 - 900, -820), (960 - 1310, -380), (960 - 1430, 300), (960 - 1380, 1000), (960 - 1150, 1700), (960 - 700, 2150), (960 - 380, 2330),
                (960 + 380, 2330), (960 + 700, 2150), (960 + 1150, 1700), (960 + 1380, 1000), (960 + 1430, 300), (960 + 1310, -380), (960 + 900, -820), (960 + 300, -1000)]
        for side in (-1, 1):                                       # handles
            tube(cv, [(960 + side * 300, -1380), (960 + side * 760, -1560), (960 + side * 1020, -1220), (960 + side * 980, -760)], 120, FIG, w=7, seed=13000 + side, boil=1.0, n=8)
        blob(cv, [(960 - 380, 2300), (960 + 380, 2300), (960 + 540, 2470), (960 + 560, 2560), (960 - 560, 2560), (960 - 540, 2470)], FIG, w=7, seed=13004, boil=0.9, n=4,
             shade=lambda c: c.drawRect(R(960 - 600, 2440, 960 + 600, 2470), paint(CLAY)))
        blob(cv, body, FIG, w=8, seed=13005, boil=1.0, n=6,
             shade=lambda c: (
                 c.drawRect(R(-600, -900, 2600, -720), paint(CLAY)),
                 [blob(c, [(960 - 1500 + j * 150, -900), (960 - 1430 + j * 150, -900), (960 - 1465 + j * 150, -740)], P_["magenta"] if j % 2 else FIG, w=3, seed=13010 + j,
                       boil=0.5, n=2) for j in range(21)],
                 c.drawRect(R(-600, 1640, 2600, 2000), paint(CLAY)),
                 [blob(c, [(960 - 1400 + j * 175, 2000), (960 - 1225 + j * 175, 2000), (960 - 1312 + j * 175, 1660)], FIG, w=3, seed=13040 + j, boil=0.5, n=2) for j in range(17)],
                 meander(c, -600, 2600, 1460, 1600, phase=phase * 0.5, seed=13060),
                 meander(c, -600, 2600, -560, -420, phase=-phase * 0.5, seed=13061),
                 c.drawPath(poly_path(cr_closed([(960 - 900, -600), (960 - 760, -660), (960 - 640, 1900), (960 - 820, 1800)], 4)), paint(P_["white"], 46))))
        neck = [(960 - 300, -1000), (960 - 270, -1500), (960 - 420, -1600), (960 - 400, -1680), (960 + 400, -1680), (960 + 420, -1600), (960 + 270, -1500), (960 + 300, -1000)]
        blob(cv, neck, FIG, w=7, seed=13070, boil=0.9, n=4,
             shade=lambda c: (meander(c, 400, 1520, -1380, -1200, phase=phase, seed=13071), c.drawRect(R(400, -1640, 1520, -1610), paint(CLAY))))
        cv.save(); cv.clipRect(R(0, 0, 1920, 1080))
        frieze_view(cv, fx, t, T, socr_fx=None)
        cv.restore()
        brush(cv, np.array([(0, 0), (1920, 0), (1920, 1080), (0, 1080)]), 7, closed=True, seed=13080)
    cv.restore()


def _socr_cam(t):
    """Frieze camera (left edge in frieze-x) and Socrates' frieze-x."""
    sfx, _ = socr_fx(t)
    if t < B42["asking"]:
        cam = lerp(60, 240, eseg(t, 0, B42["asking"]))
    elif t < 10.0:
        cam = lerp(240, 300, eseg(t, B42["asking"], 7.9)) - 160 * eseg(t, 8.0, 10.0)
    elif t < 10.5:
        cam = lerp(140, 3360, eseg(t, 10.0, 10.5))
    elif t < 12.75:
        cam = lerp(3360, 3430, eseg(t, 10.5, 12.75))
    elif t < 13.2:
        cam = lerp(3430, 5300, eseg(t, 12.75, 13.2))
    else:
        cam = lerp(5300, 5360, eseg(t, 13.2, 15.5))
    return cam, sfx


def T042_socrates(cv, t, T, A):
    cam, sfx = _socr_cam(t)
    if t < 2.3:                                                    # the whole amphora in a psychedelic void, pushing in to its picture panel
        u = eseg(t, 0.0, 2.3)
        rad_rect(cv, (-50, -50, W + 50, H + 50), 960, 540, 1300, [P_["violet"], P_["vdark"], P_["night"], P_["void"]], [0, 0.3, 0.7, 1.0])
        wedge_rays(cv, 960, 560, 2400, 22, P_["magenta"], 50, rot_deg=T * 8)
        w.stars(cv, 13100, (0, 0, W, H), n=140, big=8)
        k = lerp(0.235, 1.0, u ** 1.6)
        cy = lerp(540 + (540 - 470) * 0.235 * 0 + 120, 540, u ** 1.2)
        amphora(cv, T, k, 960, cy, cam, t, phase=-cam)
    else:
        whip = 0.0
        if 10.0 < t < 10.5:
            whip = math.sin(seg(t, 10.0, 10.5) * math.pi)
        elif 12.75 < t < 13.2:
            whip = math.sin(seg(t, 12.75, 13.2) * math.pi)
        frieze_view(cv, cam, t, T, socr_fx=sfx)
        if whip > 0.05:                                            # the vase spins: speed streaks
            for k in range(14):
                yy = 140 + k * 60
                cv.drawRect(R(0, yy, W, yy + 18 + 10 * hsh(k)), paint(P_["cream"], int(70 * whip)))
    # curvature of the vase: edges darken, a glossy sheen
    grad_rect(cv, (-10, -10, W + 10, H + 10), (0, 0), (W, 0), [(10, 0, 20), (10, 0, 20), (10, 0, 20), (10, 0, 20)], [0, 0.2, 0.8, 1.0], a=0)
    if t >= 2.3:
        p = skia.Paint(AntiAlias=True)
        p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(W, 0)], [core.C((20, 4, 30), 150), core.C((20, 4, 30), 0), core.C((20, 4, 30), 0),
                                                                                         core.C((20, 4, 30), 170)], [0.0, 0.16, 0.82, 1.0]))
        cv.drawRect(R(-10, -10, W + 10, H + 10), p)
        cv.drawPath(poly_path([(330, -10), (470, -10), (430, H + 10), (300, H + 10)]), paint(P_["white"], 30))
    # Socrates' questions: a stream of question marks from his mouth to whoever he is pestering, and a scroll
    for (a0, a1, txt) in ASKS:
        if not (a0 <= t < a1 + 0.3):
            continue
        lt = t - a0
        mxs, mys = sfx - cam + 80, GROUND - 430
        kk = pop(lt, 0.05, 0.3) * (1 - eseg(t, a1 - 0.1, a1 + 0.15))
        scroll_banner(cv, mxs + 190, GROUND - 682, txt, kk, seed=13300 + int(a0 * 10))
        tx_, ty_ = SPOT - cam - 60, GROUND - 500
        for j in range(7):
            ph = lt * 1.3 - j * 0.14
            if ph < 0 or ph > 1.0 or t > a1 + 0.2:
                continue
            qx = lerp(mxs + 30, tx_, ph)
            qy = lerp(mys, ty_, ph) - math.sin(ph * math.pi) * (40 + 25 * (j % 3)) + 30
            qmark(cv, qx, qy, 0.7 + 0.5 * ph, [P_["yellow"], P_["teal"], P_["hotpink"], P_["cream"], P_["acid"]][j % 5], seed=13200 + j,
                  rot_deg=-25 + 50 * ph + 9 * j, a=int(255 * min(1.0, (1.0 - ph) * 5)))
    if t >= B42["year"]:                                           # the caption
        kk = pop(t, B42["year"], 0.35) if t < 9.96 else 0.0           # snaps off as the whip pan starts
        if kk > 0.01:
            cartouche(cv, 960, 160, kk * 0.96, seed=13400)
    if t >= B42["death"]:                                          # the painting darkens and cracks
        lt = t - B42["death"]
        dk = eseg(lt, 0.6, 2.2)
        tint(cv, (24, 4, 30), int(150 * dk))
        rad_rect(cv, (-10, -10, W + 10, H + 10), 900, 480, 1100, [(10, 0, 16), (10, 0, 16), (10, 0, 16)], [0.0, 0.45, 1.0], a=0)
        p = skia.Paint(AntiAlias=True)
        p.setShader(skia.GradientShader.MakeRadial(skia.Point(860, 460), 1150, [core.C((10, 0, 16), 0), core.C((10, 0, 16), int(90 * dk)), core.C((10, 0, 16), int(235 * dk))],
                                                   [0.0, 0.5, 1.0]))
        cv.drawRect(R(-10, -10, W + 10, H + 10), p)
        crack(cv, eseg(lt, 1.0, 2.0), T, seed=13500)
    vignette(cv, a=100)


def scroll_banner(cv, x, y, text, k, seed=0):
    """A little unfurling papyrus scroll with Socrates' question."""
    if k <= 0.01:
        return
    from .letters import measure as _measure
    wd = _measure(text, "londrina", 58) + 70
    cv.save(); cv.translate(x, y); cv.scale(k, k)
    blob(cv, rect_pts([(-wd / 2, -46), (wd / 2, -52), (wd / 2 + 6, 40), (-wd / 2 + 4, 46)], 3), P_["cream"], w=5, seed=seed, boil=0.8, n=3,
         shade=lambda c: c.drawRect(R(-wd, 22, wd, 50), paint(P_["cream_sh"])))
    for side in (-1, 1):
        blob(cv, ell(side * wd / 2, 0, 16, 54, n=8), P_["cream_sh"], w=4, seed=seed + 2 + side, boil=0.5)
    paint_text(cv, text, 0, 20, font="londrina", size=58, fill=P_["night"], ink_w=0, shadow=None, seed=seed + 5, streaks=False, wobble=1.2)
    blob(cv, [(-40, 40), (10, 40), (-60, 100)], P_["cream"], w=4, seed=seed + 6, boil=0.5, n=2)
    cv.restore()


def cartouche(cv, x, y, k, seed=0):
    """SOCRATES 470-399 BC, on a painted plaque over the top border."""
    cv.save(); cv.translate(x, y); cv.scale(k, k)
    blob(cv, rect_pts([(-430, -108), (430, -114), (440, 104), (-424, 110)], 4), P_["cream"], w=7, seed=seed, boil=1.0, n=3,
         shade=lambda c: (c.drawRect(R(-460, -120, 460, -92), paint(P_["magenta"])), c.drawRect(R(-460, 88, 460, 120), paint(P_["magenta"]))))
    for side in (-1, 1):
        rosette(cv, side * 372, 0, 26, P_["teal"], seed=seed + side)
    paint_text(cv, "SOCRATES", 0, 6, font="londrina", size=104, fill=FIG, ink_w=0, shadow=None, seed=seed + 2, streaks=False, wobble=1.5)
    paint_text(cv, "470–399 BC", 0, 82, font="londrina", size=60, fill=P_["red"], ink_w=0, shadow=None, seed=seed + 3, streaks=False, wobble=1.2)
    cv.restore()


def crack(cv, k, T, seed=0):
    """A crack running across the painted surface (k 0..1 = how far it has run), with chips."""
    if k <= 0:
        return
    pts = [(1370, 96), (1340, 230), (1410, 330), (1360, 470), (1440, 560), (1400, 700), (1470, 820), (1440, 960)]
    P = cr_open(np.array(pts, float), 6)
    n = max(2, int(len(P) * k))
    Q = P[:n]
    off = np.array([4.0, 3.0])
    line(cv, Q + off, 6, mix(INC, P_["white"], 0.4), seed=seed, boil=0.8, n=1, taper=(0.05, 0.3), a=200)
    line(cv, Q, 9, (8, 0, 10), seed=seed + 1, boil=0.8, n=1, taper=(0.05, 0.3))
    for j, (bi, ang, L) in enumerate(((12, -40, 90), (22, 30, 120), (33, -25, 80), (40, 35, 70))):
        if bi < n:
            bx, by = P[bi]
            a = math.radians(ang)
            line(cv, [(bx, by), (bx + L * 0.5 * math.cos(a) + 10, by + L * 0.5 * math.sin(a)), (bx + L * math.cos(a), by + L * math.sin(a))], 5, (8, 0, 10), seed=seed + 10 + j,
                 boil=0.6, n=3, taper=(0.1, 0.9))
    hx, hy = Q[-1]
    for j in range(5):                                             # chips flying off the crack front
        ph = (T * 2.0 + j * 0.2) % 1.0
        if k >= 1.0 and ph > 0.6:
            continue
        cx_ = hx + (j - 2) * 14 + 60 * ph * (1 if j % 2 else -1)
        cy_ = hy + 120 * ph * ph - 30 * ph
        blob(cv, [(cx_ - 6, cy_ - 4), (cx_ + 7, cy_ - 6), (cx_ + 4, cy_ + 6)], CLAY, w=2, seed=seed + 20 + j, boil=0.4, n=2, a=int(255 * (1 - ph)))
