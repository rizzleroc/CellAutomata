"""BOXED ep4 'THE CAVE' -- owner 'game': the cave game show.

  T022_gameshow  'GUESS THAT SHADOW!' -- a glitzy 1970s game show staged inside the cave: marquee sting, the firelit
                 cave wall as the game board, the host as quizmaster at a lectern, Gary chained to a sparkly podium;
                 bunny -> horsey -> CORRECT! -> a lifetime supply of more shadows -> tears of joy.
  T037_cant_see  Gary comes back from the sunlight and can't see in the dark: his near-black POV, fumbling back to the
                 podium, the sad dingy sting, 'I can't see the bunny! ... It said hi to me!', WRONG!, everyone laughs.

Everything here is local to this module (helpers prefixed by what they draw); the CAVE KIT comes from shots_ep4_base.
"""
from .shots_ep4_base import *          # noqa: F401,F403
from .shots_ep4_base import (P_, R, PAL, INK, W, H, paint, poly_path, cr_closed, cr_open, ell, blob, line, brush, dots, hsh, mix,
                             jit, sparkle, rect_pts, tube, stipple, core, w, sets, paint_text, measure, draw_host, ease, pop, lerp,
                             loud_at, vis_at, spk_loud, CV_ROCK, CV_ROCK2, CV_ROCK_DK, CV_WALL, CV_WALL2, CV_SHADOW, wall_surface,
                             rock_mass, chain, crystal, glow_mushroom, firelight, shadow_shape, SHAPES, darkness, vignette)
from .zee import _hand
from .letters import _font, _contours
import math
import numpy as np
import skia

SEQ = (196, 30, 150)          # podium sequin magenta
GOLD = P_["gold"]
BULB = (255, 248, 214)        # warm white bulb


# ===================================================================== small utilities
def cl(x, a=0.0, b=1.0):
    return float(min(b, max(a, x)))


def sm(t, a, b):
    """Smoothstep 0->1 as t goes a->b."""
    return ease((t - a) / max(1e-6, b - a))


def imp(t, t0, dur=0.3):
    """Impulse: 0 before t0, 1 at t0, exponential decay after."""
    return 0.0 if t < t0 else math.exp(-(t - t0) / dur)


def jolt(t, hits, amp=22.0, dur=0.28, seed=0):
    """Camera-shake offset (dx, dy) from a list of impact times."""
    k = sum(imp(t, h, dur) for h in hits)
    if k < 0.01:
        return 0.0, 0.0
    return (float(hsh(core.D * 1.37 + seed)) - 0.5) * 2 * amp * k, (float(hsh(core.D * 2.11 + seed + 5)) - 0.5) * 2 * amp * k


def lerp_cam(keys, t):
    """keys: list of (t, x, y, z, ease_dur). Holds each key; eases from the previous key over ease_dur after its t."""
    cur = keys[0][1:4]
    for i in range(1, len(keys)):
        t0, x, y, z, d = keys[i]
        if t < t0:
            break
        u = ease((t - t0) / max(1e-6, d))
        cur = (lerp(cur[0], x, u), lerp(cur[1], y, u), lerp(cur[2], z, u))
    return dict(x=cur[0], y=cur[1], z=cur[2])


def _pts(P):
    return [skia.Point(float(x), float(y)) for x, y in P]


def resample(P, spacing, closed=True):
    """Points every `spacing` px along a polyline (closed loop by default)."""
    P = np.asarray(P, float)
    Q = np.vstack([P, P[:1]]) if closed else P
    d = np.hypot(*np.diff(Q, axis=0).T)
    L = np.concatenate([[0.0], np.cumsum(d)])
    tot = float(L[-1]) or 1.0
    n = max(1, int(tot / spacing))
    s = np.arange(n) * (tot / n) if closed else np.linspace(0, tot, n + 1)
    return np.stack([np.interp(s, L, Q[:, 0]), np.interp(s, L, Q[:, 1])], 1)


def rrect(x0, y0, x1, y1, r, n=5):
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return np.array(pts)


def flash(cv, a, rgb=None):
    if a > 0.004:
        cv.drawRect(R(-50, -50, W + 50, H + 50), paint(rgb or P_["white"], int(255 * cl(a))))


_SMK = {}


def smoke(cv, x, y, r, rgb, a):
    """A soft, blurred smoke puff."""
    if a <= 3 or r <= 1:
        return
    key = (tuple(rgb), int(a) // 8, int(r) // 4)
    p = _SMK.get(key)
    if p is None:
        p = skia.Paint(AntiAlias=True, Color=core.C(rgb, (int(a) // 8) * 8))
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, max(1.0, (int(r) // 4) * 4 * 0.38)))
        _SMK[key] = p
    cv.drawOval(R(x - r, y - r * 0.82, x + r, y + r * 0.82), p)


_LM = []


def light_mask(cv, lights, ambient=14, T=0.0):
    """Multiply the frame by a light map: a dark ambient plus additive radial pools (x, y, r, k, rgb) in screen space --
    darkness that keeps lit things saturated instead of greying everything out."""
    if not _LM:
        _LM.append(skia.Surface.MakeRaster(skia.ImageInfo.Make(W, H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType)))
    srf = _LM[0]
    c = srf.getCanvas()
    a = int(max(0, min(255, ambient)))
    c.clear(skia.ColorSetARGB(255, a, a, int(min(255, a * 1.3))))
    for (x, y, r, k, rgb) in lights:
        fl = 1.0 + 0.04 * math.sin(T * 13.0 + x * 0.01)
        p = skia.Paint(AntiAlias=True)
        p.setBlendMode(skia.BlendMode.kPlus)
        c1 = tuple(int(min(255, v * k * fl)) for v in rgb)
        p.setShader(skia.GradientShader.MakeRadial(skia.Point(x, y), max(1.0, r), [core.C(c1), core.C(tuple(int(v * 0.45) for v in c1)), core.C((0, 0, 0))],
                                                   [0.0, 0.42, 1.0]))
        c.drawCircle(x, y, r, p)
    mp = skia.Paint()
    mp.setBlendMode(skia.BlendMode.kMultiply)
    cv.drawImage(srf.makeImageSnapshot(), 0, 0, skia.SamplingOptions(), mp)


# ===================================================================== marquee bulbs
_GP = {}


def _glow(rgb, a, rad):
    key = (tuple(int(v) for v in rgb), int(a), round(rad * 2) / 2)
    p = _GP.get(key)
    if p is None:
        p = skia.Paint(AntiAlias=True, Color=core.C(rgb, a))
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(max(1.0, 2 * key[2]))
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, max(0.6, key[2] * 0.5)))
        _GP[key] = p
    return p


def bulbs(cv, P, r, lit, rgb=None, glow=1.0, off=None):
    """Marquee bulbs at points P: lit ones get a soft halo, an inked bright core and a hot highlight; dead ones are dull."""
    P = np.asarray(P, float).reshape(-1, 2)
    if len(P) == 0:
        return
    lit = np.broadcast_to(np.asarray(lit, bool), (len(P),))
    rgb = rgb or BULB
    ink = r + 2.2 * core.INKMUL
    on, of = P[lit], P[~lit]
    if len(of):
        dots(cv, of, ink, INK)
        dots(cv, of, r, off or (96, 70, 110))
        dots(cv, of + np.array([-r * 0.3, -r * 0.3]), r * 0.3, (150, 130, 165))
    if len(on):
        if glow > 0:
            cv.drawPoints(skia.Canvas.kPoints_PointMode, _pts(on), _glow(rgb, int(min(255, 150 * glow)), r * 2.9))
        dots(cv, on, ink, INK)
        dots(cv, on, r, rgb)
        dots(cv, on + np.array([-r * 0.28, -r * 0.3]), r * 0.42, P_["white"])


def chase(n, t, speed=9.0, period=3, phase=0):
    idx = np.arange(n)
    return ((idx + int(t * speed) + phase) % period) != 0


def bulb_states(n, t, mode="chase", seed=0, dead=0.0, speed=9.0):
    """lit-mask for n bulbs: chase | all | flash (alternate drawings) | off | sparkle (random twinkle)."""
    if mode == "all":
        lit = np.ones(n, bool)
    elif mode == "flash":
        lit = np.full(n, core.D % 2 == 0)
    elif mode == "alt":
        lit = (np.arange(n) + core.D) % 2 == 0
    elif mode == "off":
        lit = np.zeros(n, bool)
    elif mode == "sparkle":
        lit = hsh(np.arange(n) * 1.913 + core.D * 0.37 + seed) > 0.45
    else:
        lit = chase(n, t, speed)
    if dead > 0:
        dd = hsh(np.arange(n) * 3.71 + seed) < dead
        flick = hsh(np.arange(n) * 5.3 + core.D * 0.91 + seed) > 0.5
        lit = lit & ~dd | (dd & flick & (hsh(np.arange(n) * 7.7 + seed) < dead * 0.25))
    return lit


_BT = {}


def bulb_layout(text, font, size, spacing):
    """Bulb sockets running down the middle of each letter stroke (one row, evenly spaced), relative to the centred
    baseline origin. Found by marching inward from the outline to the far side of the stroke; cached per text/size."""
    key = (text, font, round(float(size), 1), round(float(spacing), 1))
    if key in _BT:
        return _BT[key]
    f = _font(font, size)
    gl = f.textToGlyphs(text)
    wd = f.getWidths(gl)
    total = float(sum(wd))
    pen = -total / 2
    out = []
    stp = max(1.0, size * 0.012)
    for i, g in enumerate(gl):
        path = f.getPath(int(g))
        if path is not None and path.countPoints() > 0:
            cand = []
            for Cc in _contours(font, size, g, 2.0):
                S = resample(Cc, spacing * 0.34)
                if len(S) < 3:
                    continue
                Tg = np.roll(S, -1, 0) - np.roll(S, 1, 0)
                N = np.stack([-Tg[:, 1], Tg[:, 0]], 1)
                N /= (np.hypot(N[:, 0], N[:, 1])[:, None] + 1e-9)
                for (px, py), (nx, ny) in zip(S, N):
                    sg = 1.0 if path.contains(float(px + nx * stp * 1.5), float(py + ny * stp * 1.5)) else \
                        (-1.0 if path.contains(float(px - nx * stp * 1.5), float(py - ny * stp * 1.5)) else 0.0)
                    if sg == 0.0:
                        continue
                    d = stp * 1.5
                    while d < size * 0.6 and path.contains(float(px + sg * nx * (d + stp)), float(py + sg * ny * (d + stp))):
                        d += stp
                    if d < size * 0.05:
                        continue
                    cand.append((px + sg * nx * d * 0.5, py + sg * ny * d * 0.5))
            kept = []
            for q in cand:                                                # greedy de-dup -> evenly spaced single row
                if all((q[0] - k[0]) ** 2 + (q[1] - k[1]) ** 2 > (spacing * 0.82) ** 2 for k in kept):
                    kept.append(q)
            out += [(qx + pen, qy) for qx, qy in kept]
        pen += wd[i]
    res = (np.array(out, float).reshape(-1, 2), total)
    _BT[key] = res
    return res


def bulb_text(cv, text, x, y, font, size, t, fill=None, fills=None, shadow_rgb=None, seed=0, mode="chase", dead=0.0,
              bulb_rgb=None, glow=1.0, ink_w=None, shadow=None, speed=9.0, drips=0, spacing=None, a=255):
    """Marquee lettering: hand-painted letters (no jitter so the sockets line up) studded with chasing bulbs."""
    paint_text(cv, text, x, y, font=font, size=size, fill=fill, fills=fills, ink_w=ink_w or max(3.0, size * 0.04),
               shadow=shadow if shadow is not None else (size * 0.055, size * 0.055), shadow_rgb=shadow_rgb, seed=seed, wobble=1.3,
               rot_jit=0, scale_jit=0, base_jit=0, streaks=False, drips=drips, a=a)
    P, tot = bulb_layout(text, font, size, spacing or size * 0.135)
    if len(P) == 0:
        return tot
    lit = bulb_states(len(P), t, mode, seed=seed, dead=dead, speed=speed)
    bulbs(cv, P + np.array([x, y]), max(2.0, size * 0.026), lit, rgb=bulb_rgb, glow=glow * 0.7)
    return tot


def marquee_ring(cv, poly, spacing, r, t, mode="chase", seed=0, dead=0.0, colors=None, glow=1.0, speed=9.0):
    """Bulbs every `spacing` px around a closed polygon; optional colour cycle per bulb."""
    P = resample(poly, spacing)
    lit = bulb_states(len(P), t, mode, seed=seed, dead=dead, speed=speed)
    if colors:
        idx = np.arange(len(P)) % len(colors)
        for k, c in enumerate(colors):
            m = idx == k
            bulbs(cv, P[m], r, lit[m], rgb=c, glow=glow)
    else:
        bulbs(cv, P, r, lit, glow=glow)
    return P


# ===================================================================== light + atmosphere
def spot_cone(cv, x0, y0, x1, y1, w0, w1, rgb, a=70):
    """A soft volumetric light cone from (x0, y0) to a pool at (x1, y1)."""
    d = np.array([x1 - x0, y1 - y0], float)
    L = float(np.hypot(*d)) or 1.0
    d /= L
    n = np.array([-d[1], d[0]])
    pts = [np.array([x0, y0]) + n * w0, np.array([x1, y1]) + n * w1, np.array([x1, y1]) - n * w1, np.array([x0, y0]) - n * w0]
    g = skia.Paint(AntiAlias=True)
    g.setShader(skia.GradientShader.MakeLinear([skia.Point(x0, y0), skia.Point(x1, y1)],
                                               [core.C(rgb, a), core.C(rgb, int(a * 0.45)), core.C(rgb, int(a * 0.15))], [0.0, 0.6, 1.0]))
    cv.drawPath(poly_path(pts), g)
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(x1, y1), w1 * 1.1, [core.C(rgb, int(a * 1.3)), core.C(rgb, 0)]))
    cv.save(); cv.translate(x1, y1); cv.scale(1.0, 0.28); cv.translate(-x1, -y1)
    cv.drawCircle(x1, y1, w1 * 1.1, p)
    cv.restore()


def burst_lines(cv, x, y, r0, r1, n, k, rgb=None, wdt=7.0, seed=0, rot0=0.0):
    """Radiating speed lines (impact burst), k = 0..1 life."""
    if k <= 0.01:
        return
    rgb = rgb or P_["white"]
    for j in range(n):
        a = rot0 + j * 2 * math.pi / n + 0.2 * float(hsh(seed + j))
        ra = r0 + (r1 - r0) * (1 - k) * 0.6
        rb = ra + (r1 - r0) * (0.35 + 0.3 * float(hsh(seed + j * 3))) * k
        line(cv, [(x + ra * math.cos(a), y + ra * math.sin(a)), (x + rb * math.cos(a), y + rb * math.sin(a))], wdt * (0.5 + k * 0.5), rgb,
             seed=seed + j, boil=0.6, n=2, taper=(0.1, 0.6), a=int(255 * min(1.0, k * 1.6)))


def ring_pulse(cv, x, y, r, k, rgb=None, wdt=10.0):
    if k <= 0.01:
        return
    cv.drawCircle(x, y, r, paint(rgb or P_["white"], int(220 * k), stroke=wdt * (0.3 + k)))


def puff(cv, x, y, s, k, seed=0, rgb=None):
    """Little cartoon dust puffs, k = 0..1 life."""
    if k <= 0.01:
        return
    rgb = rgb or P_["lilac"]
    for j in range(5):
        a = math.pi + j * math.pi / 4
        rr = (30 + 70 * (1 - k)) * s
        px, py = x + rr * math.cos(a) * 1.6, y + rr * math.sin(a) * 0.5
        blob(cv, ell(px, py, 22 * s * k + 4, 18 * s * k + 3, n=8), rgb, w=3.0, seed=seed + j, boil=0.8)


def confetti_burst(cv, t, t0, x, y, ang, spread=38.0, n=70, speed=1500.0, seed=0, life=4.0, scale=1.0):
    """A confetti-cannon blast from (x, y) towards angle `ang` (deg, screen); ballistic + flutter."""
    tt = t - t0
    if tt <= 0 or tt > life:
        return
    cols = [P_["magenta"], P_["yellow"], P_["teal"], P_["acid"], P_["orange"], P_["hotpink"], P_["cream"], P_["lilac"]]
    j = np.arange(n, dtype=np.float64)
    a = np.radians(ang + (hsh(seed + j * 1.7) - 0.5) * 2 * spread)
    v = speed * (0.45 + 0.75 * hsh(seed + j * 2.9))
    drag = 2.2
    f = (1 - np.exp(-drag * tt)) / drag
    X = x + np.cos(a) * v * f + 40 * np.sin(tt * 4 + j) * min(1.0, tt)
    Y = y + np.sin(a) * v * f + 140 * tt * tt + 60 * tt
    sp = tt * (6 + 6 * hsh(seed + j * 4.1)) + j
    for k in range(n):
        if Y[k] > H + 40 or X[k] < -40 or X[k] > W + 40:
            continue
        c = cols[k % len(cols)]
        sz = (9 + 6 * float(hsh(seed + k * 5.3))) * scale
        dx, dy = sz * math.cos(sp[k]), sz * 0.45 * math.sin(sp[k] * 1.3)
        cv.drawPath(poly_path([(X[k] - dx, Y[k] - dy), (X[k] + dy, Y[k] - dx * 0.5), (X[k] + dx, Y[k] + dy), (X[k] - dy, Y[k] + dx * 0.5)]),
                    paint(c, 255 if tt < life - 0.6 else int(255 * (life - tt) / 0.6)))


def confetti_rain(cv, t, seed=0, n=60, a=1.0, x0=0, x1=W):
    cols = [P_["magenta"], P_["yellow"], P_["teal"], P_["acid"], P_["orange"], P_["hotpink"]]
    for k in range(n):
        x = x0 + hsh(seed + k) * (x1 - x0) + 40 * math.sin(t * 2 + k)
        y = ((hsh(seed + 100 + k) * H + t * (150 + 110 * hsh(seed + 200 + k))) % (H + 80)) - 40
        ang = t * 5 + k
        dx, dy = 12 * math.cos(ang), 6 * math.sin(ang * 1.3)
        cv.drawPath(poly_path([(x - dx, y - dy), (x + dy, y - dx), (x + dx, y + dy), (x - dy, y + dx)]), paint(cols[k % 6], int(255 * a)))


def drop(cv, x, y, r, rgb=None, ang=0.0, a=255, ink=3.0):
    """A cartoon water drop pointing along ang (deg; 0 = point up)."""
    rgb = rgb or P_["mint"]
    cv.save(); cv.translate(x, y); cv.rotate(ang)
    p = skia.Path()
    p.moveTo(0, -r * 2.0)
    p.cubicTo(r * 0.4, -r * 1.2, r * 1.0, -r * 0.4, r * 1.0, r * 0.15)
    p.cubicTo(r * 1.0, r * 0.75, r * 0.55, r * 1.05, 0, r * 1.05)
    p.cubicTo(-r * 0.55, r * 1.05, -r * 1.0, r * 0.75, -r * 1.0, r * 0.15)
    p.cubicTo(-r * 1.0, -r * 0.4, -r * 0.4, -r * 1.2, 0, -r * 2.0)
    cv.drawPath(p, paint(rgb, a))
    if ink > 0:
        cv.drawPath(p, paint(INK, a, stroke=ink * core.INKMUL))
    cv.drawCircle(-r * 0.35, -r * 0.05, r * 0.28, paint(P_["white"], int(a * 0.85)))
    cv.restore()


def tear_fountain(cv, x, y, s, t, side, rate=14.0, power=1.0, seed=0, rgb=None):
    """A comic tear fountain: an arc of drops spraying out of the eye corner at (x, y) towards `side` (-1 / +1)."""
    rgb = rgb or (120, 220, 255)
    life = 0.9
    n = int(rate * life)
    for j in range(n):
        age = ((t * rate + j) % n) / rate
        born = t - age
        jit_ = float(hsh(seed + math.floor(born * rate) * 1.31))
        vx = side * (420 + 240 * jit_) * s * power
        vy = -(380 + 200 * float(hsh(seed + math.floor(born * rate) * 2.7))) * s * power
        px = x + vx * age
        py = y + vy * age + 0.5 * 2400 * s * age * age
        ang = math.degrees(math.atan2(vy + 2400 * s * age, vx)) + 90
        drop(cv, px, py, (8 + 5 * jit_) * s * 1.6 + 2, rgb, ang=ang + 180, ink=2.5)
    # the gush at the eye corner
    blob(cv, ell(x + side * 10 * s, y, 26 * s, 18 * s, n=8), rgb, w=3.0, seed=seed + 99, boil=1.2)


def sweat_spray(cv, x, y, s, t, seed=0, n=6, k=1.0):
    """Anime sweat drops flying off a head of radius ~150*s centred at (x, y)."""
    for j in range(n):
        ph = (t * 1.8 + j / n) % 1.0
        a = math.radians(-160 + j * (140 / max(1, n - 1)) + 10 * math.sin(j * 3.1))
        rr = (165 + 120 * ph) * s
        px, py = x + rr * math.cos(a), y + rr * math.sin(a) + 160 * s * ph * ph
        if k * (1 - ph) > 0.05:
            drop(cv, px, py, (10 + 4 * (j % 2)) * s * 1.4, (170, 240, 255), ang=math.degrees(a) + 90, a=int(255 * min(1.0, k * (1 - ph) * 1.5)), ink=2.5)


def strain_marks(cv, x, y, r, t, seed=0, k=1.0):
    """Little stress lines around a head (the 'strain' crackle)."""
    for j in range(5):
        a = math.radians(-150 + j * 30)
        jj = 4 * math.sin(t * 30 + j)
        r0, r1 = r * 1.12 + jj, r * 1.3 + jj
        line(cv, [(x + r0 * math.cos(a), y + r0 * math.sin(a)), (x + r1 * math.cos(a), y + r1 * math.sin(a))], 5, INK, seed=seed + j, boil=0.8,
             n=2, taper=(0.2, 0.2), a=int(255 * k))


# ===================================================================== Gary, fully actable
def arm_num(spec, T, side):
    """Gary arm spec -> (hand_x, hand_y, hand_angle, pose) in units of s from his eye centre (None stays None)."""
    if spec is None:
        return None
    if callable(spec):
        return spec(T)
    if isinstance(spec, str):
        if spec == "hang":
            return (side * 140, 330, 100 if side < 0 else 80, "open")
        if spec == "wave":
            return (side * 205 + 16 * math.sin(T * 8), -100, -90 + 14 * math.sin(T * 8), "open")
        if spec == "up":
            return (side * 190, -150 + 10 * math.sin(T * 9 + side), -90 - side * 20, "spread")
    return spec


def arm_track(keys, t, T, side):
    """Blend an arm between key poses. keys = [(t0, spec, dur), ...]: from t0 the arm moves from the previous pose to spec
    over dur seconds (eased, ~5% overshoot), so joints never snap between drawings."""
    i = -1
    for j, k in enumerate(keys):
        if t >= k[0]:
            i = j
    if i < 0:
        return arm_num(keys[0][1], T, side)
    t0, spec, dur = keys[i]
    b = arm_num(spec, T, side)
    if i == 0 or dur <= 0.0:
        return b
    a = arm_num(keys[i - 1][1], T, side)
    u = (t - t0) / dur
    if u >= 1.0 or a is None or b is None:
        return b
    v = u - 1.0
    e = 1.0 + 2.2 * v ** 3 + 1.2 * v * v
    da = ((b[2] - a[2] + 180.0) % 360.0) - 180.0
    return (lerp(a[0], b[0], e), lerp(a[1], b[1], e), a[2] + da * e, b[3] if u > 0.4 else a[3])


def gary2(cv, x, y, s, T, loud=None, seed=4400, lid=None, look=(0.0, 0.0), pupil=None, mouth=None, armL="hang", armR=None,
          collar=True, chain_to=None, tremble=0.0, legs=None, squint=0.0, iris_kind=None, part="all", happy=0.0, bob=1.0,
          squash=1.0, tilt=0.0, tears_pool=0.0):
    """Gary the eyeball in his striped cream sweater (same drawing as the show's eyeball_creature) with acting controls:
      lid 0..1 (upper lid closure; None = his sleepy default + blinks), squint (strain lines + a lower crease),
      look (dx, dy) -1..1, pupil (radius factor), mouth None (lip-sync from loud) | 'smile' | 'grin' | 'sob' | 'o' | 'frown',
      armL/armR None | 'hang' | 'wave' | 'up' | (hx, hy, hand_angle, pose) in units of s relative to the eye centre,
      collar (iron neck collar) + chain_to (x, y), tremble (px), legs (walk phase or None), iris_kind None | 'dollar' | 'heart',
      happy 0..1 (joy-squint lower lid), part 'all' | 'body' | 'arms'.  (x, y) = eye centre."""
    loud = spk_loud("AUD", T) if loud is None else loud
    if tremble > 0:
        x += (float(hsh(core.D * 1.9 + seed)) - 0.5) * 2 * tremble
        y += (float(hsh(core.D * 2.7 + seed)) - 0.5) * tremble
    bobv = 6 * math.sin(T * 3.1) * s * bob
    if part in ("all", "body"):
        cv.save()
        if tilt or squash != 1.0:
            cv.translate(x, y + 360 * s); cv.rotate(tilt); cv.scale(1.0 + (1.0 - squash) * 0.5, squash); cv.translate(-x, -(y + 360 * s))
        if legs is not None:
            for side in (-1, 1):
                sw = math.sin(legs * 2 * math.pi + (0 if side < 0 else math.pi)) * 26 * s
                lift = max(0.0, math.sin(legs * 2 * math.pi + (0 if side < 0 else math.pi))) * 14 * s
                tube(cv, [(x + side * 46 * s, y + 340 * s), (x + side * 48 * s + sw * 0.5, y + 390 * s - lift), (x + side * 50 * s + sw, y + 436 * s - lift)],
                     20 * s + 2, P_["cream"], w=4.0, seed=seed + 90 + side, boil=0.7, n=5)
                blob(cv, ell(x + side * 50 * s + sw + side * 10 * s, y + 444 * s - lift, 30 * s, 15 * s, n=8), P_["red"], w=4, seed=seed + 92 + side, boil=0.6)
        blob(cv, [(x - 128 * s, y + 360 * s), (x - 110 * s, y + 170 * s), (x - 55 * s, y + 112 * s), (x + 55 * s, y + 112 * s), (x + 110 * s, y + 170 * s),
                  (x + 128 * s, y + 360 * s)], P_["cream"], w=5, seed=seed, boil=1.0, n=6,
             shade=lambda c: [c.drawRect(R(x - 140 * s, y + (232 + k * 46) * s, x + 140 * s, y + (250 + k * 46) * s), paint(P_["orange"])) for k in range(3)])
        paint_text(cv, "G", x, y + 300 * s, font="shrik", size=76 * s, fill=P_["red"], ink_w=4, shadow=None, seed=seed + 30, streaks=False)
        ey0 = y + bobv
        eye_pts = ell(x, ey0, 150 * s, 150 * s, n=14)
        blob(cv, eye_pts, P_["white"], w=6, seed=seed + 4, boil=1.2,
             shade=lambda c: [line(c, [(x + 150 * s * math.cos(a), ey0 + 150 * s * math.sin(a)), (x + 100 * s * math.cos(a + 0.25), ey0 + 100 * s * math.sin(a + 0.25))],
                                   3.5, P_["red"], seed=seed + 10 + k, boil=0.8, n=3) for k, a in enumerate(np.linspace(0, 6.0, 8))])
        ir = 66 * s
        ex, ey = x - 4 * s + look[0] * 44 * s, ey0 - 22 * s + look[1] * 40 * s
        blob(cv, ell(ex, ey, ir, ir, n=11), P_["teal"], w=4.5, seed=seed + 5, boil=0.8,
             shade=lambda c: c.drawPath(poly_path(cr_closed(ell(ex + 10 * s, ey + 12 * s, ir * 0.8, ir * 0.75, n=8), 4)), paint(P_["tealdk"])))
        pr = ir * ((0.42 + 0.22 * min(1.0, loud)) if pupil is None else pupil)
        if iris_kind == "dollar":
            paint_text(cv, "$", ex, ey + ir * 0.42, font="bangers", size=ir * 1.25, fill=P_["yellow"], ink_w=3.5, shadow=None, seed=seed + 7, streaks=False)
        elif iris_kind == "heart":
            hr = ir * 0.62 * (1 + 0.08 * math.sin(T * 14))
            hp = [(ex, ey + hr), (ex - hr * 1.15, ey - hr * 0.1), (ex - hr * 0.62, ey - hr * 0.95), (ex, ey - hr * 0.45), (ex + hr * 0.62, ey - hr * 0.95),
                  (ex + hr * 1.15, ey - hr * 0.1)]
            blob(cv, hp, P_["magenta"], w=3.5, seed=seed + 7, boil=0.6, n=4)
        else:
            blob(cv, ell(ex, ey, pr, pr, n=9), INK, w=0, seed=seed + 6, boil=0.5, misreg=(0, 0))
        dots(cv, [(ex - ir * 0.32, ey - ir * 0.36)], max(2.0, ir * 0.16), P_["white"])
        if tears_pool > 0:                                        # glassy wet eye: a quivering pool along the lower rim
            dots(cv, [(ex + ir * 0.3, ey + ir * 0.2)], max(1.5, ir * 0.08), P_["white"])
            cv.save(); cv.clipPath(poly_path(cr_closed(eye_pts, 4)), doAntiAlias=True)
            wy = ey0 + 150 * s * (1 - 0.32 * tears_pool) + 4 * s * math.sin(T * 9)
            cv.drawPath(poly_path(cr_closed([(x - 170 * s, wy), (x - 60 * s, wy - 10 * s), (x + 60 * s, wy - 10 * s), (x + 170 * s, wy),
                                             (x + 170 * s, ey0 + 170 * s), (x - 170 * s, ey0 + 170 * s)], 4)), paint((150, 230, 255), 170))
            cv.restore()
        # lids (clipped to the eyeball)
        if lid is None:
            L = (0.25 + 0.2 * math.sin(T * 0.7)) * 0.35
            if (T * 0.37 + hsh(seed) * 2.0) % 3.3 < 0.11:
                L = 0.78
        else:
            L = lid
        cv.save()
        cv.clipPath(poly_path(cr_closed(ell(x, ey0, 153 * s, 153 * s, n=14), 4)), doAntiAlias=True)
        ly = ey0 - 150 * s + 300 * s * L
        up = [(x - 200 * s, ey0 - 220 * s), (x + 200 * s, ey0 - 220 * s), (x + 200 * s, ly - 46 * s), (x + 90 * s, ly - 10 * s), (x, ly), (x - 90 * s, ly - 10 * s),
              (x - 200 * s, ly - 46 * s)]
        blob(cv, up, P_["violet"], w=5, seed=seed + 7, boil=1.0, n=4)
        if happy > 0:
            hy = ey0 + 150 * s - 170 * s * happy
            lo = [(x - 200 * s, ey0 + 220 * s), (x - 200 * s, hy + 40 * s), (x - 90 * s, hy + 6 * s), (x, hy), (x + 90 * s, hy + 6 * s), (x + 200 * s, hy + 40 * s),
                  (x + 200 * s, ey0 + 220 * s)]
            blob(cv, lo, P_["violet"], w=5, seed=seed + 8, boil=1.0, n=4)
        cv.restore()
        if squint > 0:
            line(cv, [(ex - ir * 1.05, ey + ir * 1.0), (ex, ey + ir * 1.25), (ex + ir * 1.05, ey + ir * 1.0)], 4.5, INK, seed=seed + 9, boil=0.8, n=4,
                 a=int(255 * min(1.0, squint * 1.5)))
            for side in (-1, 1):
                for j in range(3):
                    a = math.radians((0 if side > 0 else 180) + (j - 1) * 22)
                    r0, r1 = 156 * s, (182 + 8 * (j == 1)) * s
                    line(cv, [(x + r0 * math.cos(a), ey0 - 20 * s + r0 * math.sin(a)), (x + r1 * math.cos(a), ey0 - 20 * s + r1 * math.sin(a))], 4.5, INK,
                         seed=seed + 20 + j + side * 5, boil=0.8, n=2, taper=(0.2, 0.2), a=int(255 * min(1.0, squint * 1.5)))
        # mouth (on the white, under the iris)
        mx, my = x + 6 * s, ey0 + 92 * s
        if happy > 0.3:
            my = min(my, ey0 + 150 * s - 170 * s * happy - 30 * s) if mouth in (None, "o") else my
        mo = min(1.0, loud * 1.5)
        mk = mouth
        if mk is None and mo > 0.08:
            mh = (5 + 30 * mo) * s
            blob(cv, ell(mx, my + mh * 0.3, 34 * s, mh, n=10), P_["mouth"], w=4.5, seed=seed + 40, boil=0.7,
                 shade=lambda c: blob(c, ell(mx + 4 * s, my + mh * 1.1, 22 * s, mh * 0.6, n=8), P_["tongue"], w=0, seed=seed + 41, boil=0.5, misreg=(0, 0)))
        elif mk == "sob":
            q = 0.6 + 0.4 * max(mo, 0.55)
            pts = [(mx - 58 * s, my - 8 * s), (mx - 28 * s, my - 16 * s + 3 * s * math.sin(T * 40)), (mx + 28 * s, my - 16 * s - 3 * s * math.sin(T * 40)),
                   (mx + 58 * s, my - 8 * s), (mx + 40 * s, my + 40 * s * q), (mx, my + 52 * s * q), (mx - 40 * s, my + 40 * s * q)]
            blob(cv, pts, P_["mouth"], w=4.5, seed=seed + 43, boil=1.6, n=5,
                 shade=lambda c: blob(c, ell(mx, my + 44 * s * q, 30 * s, 16 * s, n=8), P_["tongue"], w=0, seed=seed + 44, boil=0.6, misreg=(0, 0)))
        elif mk == "grin":
            pts = [(mx - 64 * s, my - 14 * s), (mx, my - 4 * s), (mx + 64 * s, my - 14 * s), (mx + 44 * s, my + 30 * s), (mx, my + 44 * s), (mx - 44 * s, my + 30 * s)]
            blob(cv, pts, P_["mouth"], w=4.5, seed=seed + 45, boil=0.9, n=5,
                 shade=lambda c: (c.drawRect(R(mx - 70 * s, my - 30 * s, mx + 70 * s, my + 2 * s), paint(P_["white"])),
                                  blob(c, ell(mx, my + 40 * s, 30 * s, 14 * s, n=8), P_["tongue"], w=0, seed=seed + 46, boil=0.6, misreg=(0, 0))))
        elif mk == "o":
            blob(cv, ell(mx, my + 8 * s, 16 * s, 20 * s, n=8), P_["mouth"], w=4.5, seed=seed + 47, boil=0.7)
        elif mk == "frown":
            line(cv, [(mx - 30 * s, my + 8 * s), (mx, my - 4 * s), (mx + 30 * s, my + 8 * s)], 4.5, seed=seed + 48, boil=0.6, n=6, taper=(0.3, 0.3))
        elif mk == "wobble":
            line(cv, [(mx - 34 * s, my), (mx - 17 * s, my - 6 * s), (mx, my + 2 * s), (mx + 17 * s, my - 6 * s), (mx + 34 * s, my)], 4.5, seed=seed + 49,
                 boil=1.4, n=5, taper=(0.3, 0.3))
        else:
            line(cv, [(mx - 30 * s, my - 4 * s), (mx, my + 8 * s), (mx + 30 * s, my - 4 * s)], 4.5, seed=seed + 42, boil=0.6, n=6, taper=(0.3, 0.3))
        if collar:
            cy_ = ey0 + 136 * s
            blob(cv, ell(x, cy_, 84 * s, 20 * s, n=12), (130, 130, 160), w=4, seed=seed + 60, boil=0.6,
                 shade=lambda c: c.drawRect(R(x - 90 * s, cy_ + 2 * s, x + 90 * s, cy_ + 24 * s), paint((86, 86, 116))))
            for k in range(5):
                dots(cv, [(x - 60 * s + k * 30 * s, cy_)], 3.2 * s + 0.8, (200, 200, 220))
            if chain_to is not None:
                chain(cv, (x + 70 * s, cy_ + 8 * s), chain_to, seed=seed + 61, link=max(8.0, 22 * s), sag=30 * s, w=max(1.8, 3.4 * s))
        cv.restore()
    if part in ("all", "arms"):
        for side, spec in ((-1, armL), (1, armR)):
            if spec is None:
                continue
            sh = (x + side * 104 * s, y + 190 * s)
            spec = arm_num(spec, T, side)
            hx, hy, ang, pose = x + spec[0] * s, y + spec[1] * s, spec[2], spec[3]
            mxp, myp = (sh[0] + hx) / 2, (sh[1] + hy) / 2
            dx, dy = hx - sh[0], hy - sh[1]
            Ld = math.hypot(dx, dy) + 1e-6
            bend = max(0.0, 220 * s - Ld) * 0.35 + 14 * s
            nx, ny = -dy / Ld, dx / Ld
            if ny + 0.8 * side * nx < 0:                          # the natural elbow: low and outward
                nx, ny = -nx, -ny
            el = (mxp + nx * bend + side * 8 * s, myp + ny * bend)
            tube(cv, [sh, el, (hx, hy)], 22 * s, P_["cream"], w=4.5, seed=seed + 50 + side, boil=0.8, n=8)
            cv.save(); cv.translate(hx, hy); cv.scale(s * 1.15, s * 1.15)
            old = core.INKMUL; core.INKMUL = old / max(s * 1.15, 0.2) ** 0.5
            _hand(cv, 0, 0, ang, pose, 1 if side < 0 else -1, seed + 52 + side, rgb=P_["white"])
            core.INKMUL = old
            cv.restore()


# ===================================================================== the other contestants / audience
PRIS_RGB = [(64, 30, 110), (110, 50, 120), (46, 20, 86), (90, 40, 150), (130, 60, 140), (70, 34, 124)]
PRIS_EYE = [(200, 255, 230), (255, 200, 240), (255, 240, 170), (190, 220, 255)]


def contestant(cv, x, y, s, T, seed=4500, rgb=None, eye_rgb=None, look=(0.0, 0.0), mood="neutral", k=1.0, collar=True, blink=None, rim=None):
    """A chained eyeball prisoner seen from the front (the BOXED audience creature). (x, y) = floor point under the body.
    mood: neutral | cheer | laugh | stare | gasp | squint."""
    rgb = rgb or PRIS_RGB[int(hsh(seed) * len(PRIS_RGB))]
    eye_rgb = eye_rgb or PRIS_EYE[int(hsh(seed + 1) * 4)]
    r = 70 * s
    shake = 0.0
    if mood == "laugh":
        shake = math.sin(T * 38 + seed) * 5 * s * k
    bob = (2.5 * math.sin(T * 1.7 + seed) + (abs(math.sin(T * 11 + seed)) * 14 * k if mood in ("cheer", "laugh") else 0)) * s
    sq = 1.0 + (0.06 * math.sin(T * 22 + seed) * k if mood == "laugh" else 0.0)
    cx, cy = x + shake, y - r * 1.15 - bob
    body = [(cx - r * 1.05 / sq, y), (cx - r * 1.1 / sq, cy), (cx - r * 0.7, cy - r * 0.95 * sq), (cx, cy - r * 1.12 * sq), (cx + r * 0.7, cy - r * 0.95 * sq),
            (cx + r * 1.1 / sq, cy), (cx + r * 1.05 / sq, y)]
    blob(cv, body, rgb, w=5.0 * min(1.0, s * 1.4) + 1.5, seed=seed, boil=1.0, n=5,
         shade=lambda c: (c.drawPath(poly_path(cr_closed(ell(cx + r * 0.45, cy + r * 0.3, r * 0.9, r * 1.1, n=10), 3)), paint(mix(rgb, INK, 0.3))),
                          c.drawPath(poly_path(cr_closed(ell(cx, cy - r * 1.05, r * 0.95, r * 0.34, n=10), 3)), paint(rim, 110)) if rim else None))
    ex, ey, er = cx, cy - r * 0.18, r * 0.5
    bl = blink if blink is not None else (1.0 if (T * 0.4 + hsh(seed) * 3) % 3.1 < 0.12 else 0.0)
    if mood == "laugh" or (mood == "cheer" and k > 0.5):
        line(cv, [(ex - er, ey + er * 0.25), (ex - er * 0.5, ey - er * 0.45), (ex, ey - er * 0.6), (ex + er * 0.5, ey - er * 0.45), (ex + er, ey + er * 0.25)],
             max(4.0, 11 * s), INK, seed=seed + 5, boil=0.7, n=4, taper=(0.2, 0.2))
        if mood == "laugh":                                        # tears of laughter
            for side in (-1, 1):
                ph = (T * 2.2 + seed * 0.1 + (0.5 if side > 0 else 0)) % 1.0
                drop(cv, ex + side * (er * 1.05 + 30 * s * ph), ey + 50 * s * ph * ph, 7 * s + 2, (140, 225, 255), ang=side * 30, a=int(255 * (1 - ph)), ink=2)
    elif bl > 0.5:
        line(cv, [(ex - er, ey), (ex, ey + er * 0.3), (ex + er, ey)], 4, seed=seed + 5, boil=0.6, n=4)
    else:
        big = 1.25 if mood in ("stare", "gasp") else 1.0
        blob(cv, ell(ex, ey, er * big, er * 1.05 * big, n=10), P_["white"], w=4, seed=seed + 5, boil=0.7)
        pk = 0.55 if mood in ("stare", "gasp") else 1.0
        ix, iy = ex + look[0] * er * 0.45, ey + look[1] * er * 0.4
        dots(cv, [(ix, iy)], er * 0.55 * pk, eye_rgb)
        dots(cv, [(ix, iy)], er * 0.28 * pk, INK)
        dots(cv, [(ix - er * 0.15, iy - er * 0.2)], er * 0.1 + 0.8, P_["white"])
        if mood == "squint":
            cv.drawRect(R(ex - er * 1.2, ey - er * 1.2, ex + er * 1.2, ey - er * 0.25), paint(rgb))
            line(cv, [(ex - er, ey - er * 0.25), (ex + er, ey - er * 0.3)], 4, seed=seed + 9, boil=0.6, n=2)
    my = ey + er * 1.4
    if mood == "laugh":
        my = ey + er * 0.75
        mh = er * (0.95 + 0.4 * abs(math.sin(T * 19 + seed)))
        blob(cv, [(ex - er * 1.15, my - er * 0.15), (ex + er * 1.15, my - er * 0.15), (ex + er * 0.75, my + mh * 0.7), (ex, my + mh), (ex - er * 0.75, my + mh * 0.7)],
             P_["mouth"], w=4, seed=seed + 6, boil=0.9, n=5,
             shade=lambda c: (c.drawRect(R(ex - er, my - er * 0.3, ex + er, my), paint(P_["white"])),
                              blob(c, ell(ex, my + mh * 0.85, er * 0.45, er * 0.25, n=8), P_["tongue"], w=0, seed=seed + 7, boil=0.5, misreg=(0, 0))))
    elif mood in ("gasp", "cheer"):
        blob(cv, ell(ex, my + er * 0.2, er * 0.32, er * 0.42, n=8), P_["mouth"], w=3.5, seed=seed + 6, boil=0.7)
    elif mood == "stare":
        line(cv, [(ex - er * 0.35, my), (ex + er * 0.35, my)], 3.5, seed=seed + 6, boil=0.5, n=2)
    if collar:
        ny = cy + r * 0.86
        blob(cv, ell(cx, ny, r * 0.92, r * 0.19, n=10), (120, 120, 150), w=3.5, seed=seed + 8, boil=0.6,
             shade=lambda c: c.drawRect(R(cx - r * 1.1, ny, cx + r * 1.1, ny + r * 0.3), paint((80, 80, 110))))
    return (cx, cy, r)


def audience_backs(cv, T, y0=1066, x0=600, x1=1980, n=9, r=88, seed=7300, cheer=0.0, laugh=0.0):
    """Foreground row of chained prisoners seen from behind (dark heads + collars), rim-lit by the wall."""
    pts = []
    for k in range(n):
        px = x0 + k * (x1 - x0) / max(1, n - 1) + 10 * math.sin(k * 2.3)
        hop = abs(math.sin(T * 9 + k * 1.7)) * 34 * cheer + abs(math.sin(T * 16 + k)) * 16 * laugh
        yy = y0 + 14 * (k % 2) + 3 * math.sin(T * 1.6 + k) - hop
        pts.append((px, yy, r * (0.92 + 0.12 * (k % 3) / 2)))
    for k in range(len(pts) - 1):
        chain(cv, (pts[k][0] + pts[k][2] * 0.7, pts[k][1] + pts[k][2] * 0.55), (pts[k + 1][0] - pts[k + 1][2] * 0.7, pts[k + 1][1] + pts[k + 1][2] * 0.55),
              seed=seed + 100 + k, link=18, sag=22, w=3.2)
    for k, (px, yy, rr) in enumerate(pts):
        if cheer > 0.05:                                          # little hands up (chains rattling)
            for side in (-1, 1):
                hx = px + side * rr * 0.95
                hy = yy - rr * (0.9 + 0.5 * cheer) - 10 * math.sin(T * 14 + k + side)
                tube(cv, [(px + side * rr * 0.6, yy - rr * 0.1), (hx, hy + 40)], 16, (40, 18, 66), w=3.5, seed=seed + 300 + k * 3 + side, boil=0.7, n=4)
                _hand(cv, hx, hy + 30, -90 + side * 15, "spread", 1 if side < 0 else -1, seed + 320 + k * 3 + side, rgb=P_["white"])
        blob(cv, ell(px, yy, rr, rr * 1.05, n=12), (26, 12, 44), w=5, seed=seed + 60 + k, boil=1.0,
             shade=lambda c, px=px, yy=yy, rr=rr: c.drawPath(poly_path(cr_closed(ell(px, yy - rr * 0.95, rr * 0.9, rr * 0.32, n=10), 3)), paint(P_["orange"], 90)))
        blob(cv, ell(px, yy + rr * 0.55, rr * 0.8, rr * 0.2, n=10), (110, 110, 140), w=3.5, seed=seed + 80 + k, boil=0.6)
        line(cv, [(px - rr * 0.5, yy - rr * 0.66), (px, yy - rr * 0.78), (px + rr * 0.5, yy - rr * 0.66)], 4, P_["yellow"], seed=seed + 90 + k, boil=0.6, n=4, a=190)


# ===================================================================== the set pieces
def lectern(cv, x, y, s, T, t, seed=7400, mode="chase", dead=0.0):
    """The host's 1970s lectern (x, y = bottom centre; top at y - 232*s): teal drum with a starburst eye emblem, gold top, bulbs."""
    hw_t, hw_b, ht = 190 * s, 150 * s, 232 * s
    body = [(x - hw_t, y - ht), (x + hw_t, y - ht), (x + hw_b, y), (x - hw_b, y)]

    def sh(c):
        for k in range(7):
            xx = x - hw_t + (k + 0.5) * 2 * hw_t / 7
            c.drawLine(xx, y - ht, xx + (x - xx) * 0.2, y, paint(P_["tealdk"], stroke=5 * s + 1))
        c.drawPath(poly_path([(x + hw_t * 0.55, y - ht - 10), (x + hw_t + 20, y - ht - 10), (x + hw_b + 20, y + 10), (x + hw_b * 0.5, y + 10)]), paint(P_["tealdk"]))
        stipple(c, P_["tealdk"], (x - hw_t, y - ht, x + hw_t, y), spacing=11 * s + 2, r=1.6 * s + 0.4, seed=seed + 1,
                fn=lambda X, Y: np.clip((X - x) / hw_t + 0.3, 0, 1) * 0.8)
    blob(cv, rect_pts(body, 3), P_["teal"], w=6, seed=seed, boil=0.9, n=3, shade=sh)
    ex, ey = x - 8 * s, y - ht * 0.52                                     # starburst emblem with an eye
    w.sunburst(cv, ex, ey, 74 * s, 12, [P_["yellow"], P_["orange"]], rot_deg=T * 40, seed=seed + 3)
    blob(cv, ell(ex, ey, 52 * s, 52 * s, n=10), P_["magenta"], w=4.5, seed=seed + 4, boil=0.7)
    w.eye_glyph(cv, ex, ey, 0.62 * s, look=(math.sin(T * 0.9), 0.0), seed=seed + 5)
    top = [(x - hw_t - 30 * s, y - ht + 4 * s), (x - hw_t, y - ht - 22 * s), (x + hw_t, y - ht - 22 * s), (x + hw_t + 30 * s, y - ht + 4 * s), (x + hw_t, y - ht + 14 * s),
           (x - hw_t, y - ht + 14 * s)]
    blob(cv, top, GOLD, w=5, seed=seed + 6, boil=0.8, n=4, shade=lambda c: c.drawRect(R(x - hw_t - 40, y - ht + 2 * s, x + hw_t + 40, y - ht + 20 * s), paint(P_["orange"])))
    P = np.array([(x - hw_t + 14 * s + k * (2 * hw_t - 28 * s) / 9, y - ht + 30 * s) for k in range(10)] +
                 [(x - hw_t + 12 * s + (hw_t - hw_b) * u, y - ht + 30 * s + (ht - 50 * s) * u) for u in np.linspace(0.12, 1, 5)] +
                 [(x + hw_t - 12 * s - (hw_t - hw_b) * u, y - ht + 30 * s + (ht - 50 * s) * u) for u in np.linspace(0.12, 1, 5)])
    bulbs(cv, P, 7 * s + 1, bulb_states(len(P), t, mode, seed=seed, dead=dead), glow=0.8)


def podium(cv, x, y, s, T, t, name="GARY", seed=7500, mode="chase", dead=0.0, press=0.0, buzz=0.0, rgb=None, name_rgb=None, buzzer=True):
    """Sparkly contestant podium (x, y = bottom centre on the floor; top at y - 270*s) with a name plate, bulbs and a big red
    buzzer. press 0..1 squashes the buzzer; buzz 0..1 lights it up. Returns the buzzer-top point and the chain ring point."""
    rgb = rgb or SEQ
    hw_t, hw_b, ht = 165 * s, 128 * s, 270 * s
    body = [(x - hw_t, y - ht), (x + hw_t, y - ht), (x + hw_b, y), (x - hw_b, y)]

    def sh(c):
        stipple(c, mix(rgb, P_["hotpink"], 0.6), (x - hw_t, y - ht, x + hw_t, y), spacing=10 * s + 2, r=2.2 * s + 0.5, seed=seed + 1)
        tw = hsh(np.arange(26) * 3.3 + seed + core.D * 0.29)
        for k in range(26):
            if tw[k] > 0.62:
                px = x - hw_t * 0.85 + hsh(seed + k * 1.7) * hw_t * 1.7
                py = y - ht * 0.55 + hsh(seed + k * 2.9) * ht * 0.5
                sparkle(c, px, py, (6 + 7 * (tw[k] - 0.62) / 0.38) * s + 2, P_["white"], w=1.5, seed=seed + k)
        c.drawPath(poly_path([(x + hw_t * 0.6, y - ht - 10), (x + hw_t + 20, y - ht - 10), (x + hw_b + 20, y + 10), (x + hw_b * 0.55, y + 10)]), paint(mix(rgb, INK, 0.3), 160))
        for side in (-1, 1):
            c.drawLine(x + side * hw_t * 0.82, y - ht, x + side * hw_b * 0.8, y, paint(GOLD, stroke=6 * s + 1))
    blob(cv, rect_pts(body, 3), rgb, w=6, seed=seed, boil=0.9, n=3, shade=sh)
    blob(cv, rect_pts([(x - hw_b - 14 * s, y - 34 * s), (x + hw_b + 14 * s, y - 34 * s), (x + hw_b + 18 * s, y), (x - hw_b - 18 * s, y)], 2), P_["maroon"], w=5,
         seed=seed + 2, boil=0.7, n=3)
    top = [(x - hw_t - 26 * s, y - ht + 6 * s), (x - hw_t, y - ht - 24 * s), (x + hw_t, y - ht - 24 * s), (x + hw_t + 26 * s, y - ht + 6 * s), (x + hw_t, y - ht + 16 * s),
           (x - hw_t, y - ht + 16 * s)]
    blob(cv, top, GOLD, w=5, seed=seed + 3, boil=0.8, n=4, shade=lambda c: c.drawRect(R(x - hw_t - 40, y - ht + 3 * s, x + hw_t + 40, y - ht + 22 * s), paint(P_["orange"])))
    py0 = y - ht + 44 * s                                                    # name plate
    plate = rrect(x - 118 * s, py0, x + 118 * s, py0 + 76 * s, 20 * s, n=3)
    blob(cv, plate, P_["cream"], w=5, seed=seed + 4, boil=0.7, n=2)
    if name:
        paint_text(cv, name, x, py0 + 60 * s, font="shrik", size=54 * s, fill=name_rgb or P_["red"], ink_w=3.5, shadow=(3 * s, 3 * s), shadow_rgb=P_["maroon"],
                   seed=seed + 5, streaks=False, rot_jit=2, base_jit=2)
    P = np.array([(x - hw_t + 10 * s + k * (2 * hw_t - 20 * s) / 11, y - ht + 30 * s) for k in range(12)] +
                 [(x - hw_t + 14 * s + (hw_t - hw_b) * u, y - ht + 140 * s + (ht - 180 * s) * u) for u in np.linspace(0, 1, 4)] +
                 [(x + hw_t - 14 * s - (hw_t - hw_b) * u, y - ht + 140 * s + (ht - 180 * s) * u) for u in np.linspace(0, 1, 4)])
    P = np.vstack([P[:12], P[12:]])
    lit = bulb_states(len(P), t, mode, seed=seed, dead=dead)
    cols = [P_["yellow"], P_["hotpink"], P_["teal"]]
    for k, c in enumerate(cols):
        m = (np.arange(len(P)) % 3) == k
        bulbs(cv, P[m], 7 * s + 1, lit[m], rgb=c if mode != "red" else P_["red"], glow=0.9)
    bx, by = x + 104 * s, y - ht - 20 * s                                  # the buzzer
    ring = (x - hw_t - 6 * s, y - ht + 30 * s)
    if buzzer:
        blob(cv, rect_pts([(bx - 52 * s, by - 26 * s), (bx + 52 * s, by - 26 * s), (bx + 56 * s, by + 4 * s), (bx - 56 * s, by + 4 * s)], 2), (40, 34, 50), w=4.5,
             seed=seed + 6, boil=0.6, n=2)
        sqz = 1.0 - 0.55 * press
        dome = [(bx - 44 * s, by - 24 * s), (bx - 38 * s, by - 24 * s - 30 * s * sqz), (bx, by - 24 * s - 50 * s * sqz), (bx + 38 * s, by - 24 * s - 30 * s * sqz),
                (bx + 44 * s, by - 24 * s)]
        if buzz > 0.05:
            firelight(cv, bx, by - 50 * s, 160 * s, T, a=int(200 * buzz), rgb=P_["red"], seed=seed + 7)
        blob(cv, dome, mix(P_["red"], P_["hotpink"], 0.5 * buzz), w=4.5, seed=seed + 7, boil=0.7, n=4,
             shade=lambda c: c.drawPath(poly_path(cr_closed(ell(bx - 14 * s, by - 24 * s - 32 * s * sqz, 12 * s, 7 * s * sqz + 1, n=8), 3)), paint(P_["white"], 200)))
    return (bx, by - 24 * s - 50 * s), ring


def stone_coin(cv, x, y, r, T, seed=0, look=(0.0, 0.0), ang=0.0):
    """A round cave-dollar: a chunky lilac stone wheel with a hole, a carved C$ and two googly eyes."""
    cv.save(); cv.translate(x, y); cv.rotate(ang)
    blob(cv, ell(4, 6, r, r, n=12), (90, 70, 130), w=0, seed=seed, boil=0.6, misreg=(0, 0))
    blob(cv, ell(0, 0, r, r, n=12), (178, 160, 210), w=4.5, seed=seed + 1, boil=0.8,
         shade=lambda c: (stipple(c, (130, 110, 170), (-r, -r, r, r), spacing=7, r=1.3, seed=seed + 2),
                          c.drawPath(poly_path(cr_closed(ell(r * 0.25, r * 0.3, r * 0.9, r * 0.85, n=10), 3)), paint((150, 130, 190)))))
    brush(cv, cr_closed(jit(ell(0, 0, r * 0.72, r * 0.72, n=10), 0.6, seed + 3), 4), 2.6, (110, 90, 150), closed=True, seed=seed + 4)
    for side in (-1, 1):
        exx, eyy = side * r * 0.32, -r * 0.12
        er = r * 0.27
        bl = (T * 0.6 + hsh(seed) * 4 + side * 0.03) % 2.7 < 0.1
        if bl:
            line(cv, [(exx - er, eyy), (exx + er, eyy)], 3, seed=seed + 5 + side, boil=0.4, n=2)
        else:
            blob(cv, ell(exx, eyy, er, er * 1.05, n=8), P_["white"], w=3, seed=seed + 5 + side, boil=0.5)
            dots(cv, [(exx + look[0] * er * 0.45, eyy + look[1] * er * 0.45 + er * 0.1)], er * 0.48, INK)
    line(cv, [(-r * 0.25, r * 0.36), (0, r * 0.46), (r * 0.25, r * 0.36)], 3, seed=seed + 8, boil=0.5, n=3)
    cv.restore()


def coin_pile(cv, x, y, s, T, k=1.0, seed=7600):
    """A pyramid of googly-eyed stone coins on a velvet pedestal, sparkling (x, y = pedestal base). k = rise 0..1."""
    if k <= 0.01:
        return
    yk = y + (1 - k) * 260 * s
    blob(cv, rect_pts([(x - 190 * s, yk - 70 * s), (x + 190 * s, yk - 70 * s), (x + 160 * s, yk + 120 * s), (x - 160 * s, yk + 120 * s)], 3), P_["maroon"], w=5,
         seed=seed, boil=0.8, n=3, shade=lambda c: c.drawRect(R(x - 200 * s, yk - 74 * s, x + 200 * s, yk - 44 * s), paint(P_["red"])))
    r = 46 * s
    rows = [5, 4, 3, 2, 1]
    j = 0
    for ri, nr in enumerate(rows):
        for ci in range(nr):
            cx = x + (ci - (nr - 1) / 2) * r * 1.85
            cy = yk - 70 * s - r * 0.95 - ri * r * 1.55
            lk = (math.sin(T * 1.3 + j * 1.9), 0.3 * math.cos(T * 1.1 + j))
            stone_coin(cv, cx, cy, r, T, seed=seed + 10 + j * 7, look=lk, ang=8 * math.sin(j * 2.3))
            j += 1
    for q in range(6):
        a = T * 2.2 + q * 1.05
        sparkle(cv, x + 230 * s * math.cos(a), yk - 260 * s + 150 * s * math.sin(a * 1.3), (10 + 6 * math.sin(T * 9 + q)) * s + 4, P_["yellow"], seed=seed + 90 + q)


def crate(cv, x, y, s, T, lid=0.0, seed=7700, leak=1.0):
    """A giant wooden crate stamped SHADOWS, dark wisps leaking out of the slats and little eyes peeking through the gaps
    (x, y = bottom centre). lid 0..1 pops the lid off (it flies up and away, tumbling)."""
    hw, ht = 230 * s, 300 * s
    for k in range(5):                                                       # leaking wisps: soft curls of shadow-smoke, rising and fading
        for q in range(3):
            ph = (T * 0.33 + k * 0.21 + q / 3.0) % 1.0
            sx = x - hw * 0.8 + k * hw * 0.4 + 30 * s * math.sin(T * 0.9 + k * 2.0 + q)
            sy = y - ht + 30 * s - ph * 300 * s
            rr = (22 + 40 * ph) * s
            curl = math.sin(T * 1.3 + k + q * 2.1) * 40 * s * ph
            smoke(cv, sx + curl, sy, rr * 1.15, (60, 14, 84), int(240 * (1 - ph) * leak))
            smoke(cv, sx + curl, sy + rr * 0.1, rr * 0.62, (24, 4, 36), int(255 * (1 - ph) * leak))
            if (k + q) % 4 == 0 and ph < 0.7:
                dots(cv, [(sx + curl - rr * 0.3, sy - rr * 0.1), (sx + curl + rr * 0.3, sy - rr * 0.1)], 3.5 * s + 1, P_["yellow"], a=int(255 * (1 - ph / 0.7)))
    if lid > 0.02:                                                           # the open top: a dark interior full of shadow
        blob(cv, rect_pts([(x - hw + 10 * s, y - ht - 26 * s), (x + hw - 10 * s, y - ht - 26 * s), (x + hw - 4 * s, y - ht + 12 * s), (x - hw + 4 * s, y - ht + 12 * s)], 3),
             (26, 6, 34), w=5, seed=seed + 9, boil=0.8, n=3)

    def sh(c):
        for k in range(4):
            yy = y - ht + (k + 1) * ht / 5
            c.drawRect(R(x - hw, yy - 4 * s, x + hw, yy + 7 * s), paint((40, 10, 50), 235))
        for side in (-1, 1):
            c.drawRect(R(x + side * hw - (40 * s if side > 0 else 0), y - ht, x + side * hw + (40 * s if side < 0 else 0), y), paint((160, 88, 44)))
        c.drawPath(poly_path([(x - hw, y - ht), (x - hw + 54 * s, y - ht), (x + hw, y - 54 * s), (x + hw, y), (x + hw - 54 * s, y), (x - hw, y - ht + 54 * s)]),
                   paint((160, 88, 44)))
        stipple(c, (150, 76, 40), (x - hw, y - ht, x + hw, y), spacing=12 * s + 2, r=1.6 * s + 0.5, seed=seed + 2)
    blob(cv, rect_pts([(x - hw, y - ht), (x + hw, y - ht), (x + hw, y), (x - hw, y)], 3), (214, 136, 72), w=6, seed=seed, boil=0.9, n=3, shade=sh)
    for k in range(3):                                                       # eyes peeking through the slat gaps
        gx = x - hw * 0.55 + k * hw * 0.55 + 8 * s * math.sin(k * 3.1)
        gy = y - ht + (k % 2 + 1) * ht / 5 + 1.5 * s
        if (T * 0.5 + k * 0.37) % 1.7 > 0.15:
            dots(cv, [(gx - 9 * s, gy), (gx + 9 * s, gy)], 4.5 * s + 1, P_["yellow"])
    cv.save(); cv.translate(x, y - ht * 0.5); cv.rotate(-8)
    blob(cv, rrect(-206 * s, -58 * s, 206 * s, 58 * s, 14 * s, n=3), None, w=7, ink=P_["red"], seed=seed + 3, boil=0.8, n=2)
    paint_text(cv, "SHADOWS", 0, 36 * s, font="bangers", size=100 * s, fill=P_["red"], ink_w=0, shadow=None, seed=seed + 4, streaks=False, a=240)
    cv.restore()
    paint_text(cv, "LIFETIME SUPPLY", x, y - ht * 0.13, font="londrina", size=36 * s, fill=(70, 20, 40), ink_w=0, shadow=None, seed=seed + 5, streaks=False)
    # the lid: sits on top, then pops up and away, tumbling (lid = seconds since it popped)
    if lid > 1.7:
        return
    ly = y - ht - 1500 * s * lid + 1900 * s * lid * lid
    lx = x - 520 * s * lid
    cv.save(); cv.translate(lx, ly); cv.rotate(-330 * lid)
    blob(cv, rect_pts([(-hw - 16 * s, -38 * s), (hw + 16 * s, -38 * s), (hw + 16 * s, 6 * s), (-hw - 16 * s, 6 * s)], 3), (194, 116, 60), w=6, seed=seed + 6, boil=0.8, n=3,
         shade=lambda c: (c.drawRect(R(-hw - 20 * s, -10 * s, hw + 20 * s, 8 * s), paint((140, 76, 40))),
                          [c.drawLine(-hw + k * hw / 3, -38 * s, -hw + k * hw / 3, 6 * s, paint((120, 60, 34), stroke=3)) for k in range(1, 6)]))
    cv.restore()
    if 0.02 < lid < 0.5:
        ring_pulse(cv, x, y - ht - 20 * s, (80 + 500 * lid) * s, 1 - lid / 0.5, P_["lilac"], 12)


def shadow_swarm(cv, x, y, s, T, tau, seed=7800, n=16):
    """Shadows bursting out of the crate (tau = seconds since the lid popped): a fountain of silhouettes (bunny, horse, bird,
    fish, star...) that then flutter around the stage like bats."""
    if tau <= 0:
        return
    kinds = ["bunny", "bird", "horse", "fish", "star", "bird", "jug", "bunny", "bird", "tree", "fish", "bird", "horse", "star", "bunny", "bird"]
    n = min(n, 11)
    for j in range(n):
        kind = kinds[j % len(kinds)]
        a = math.radians(-90 + (float(hsh(seed + j)) - 0.5) * 150)
        v = (700 + 900 * float(hsh(seed + j * 2.3))) * s
        f = (1 - math.exp(-2.4 * tau)) / 2.4
        px = x + math.cos(a) * v * f
        py = y + math.sin(a) * v * f
        fl = min(1.0, tau / 0.8)
        px += fl * (170 * math.cos(T * (1.1 + 0.4 * hsh(seed + j * 5)) + j) * s)
        py += fl * (90 * math.sin(T * (1.7 + 0.5 * hsh(seed + j * 7)) + j * 1.3) * s) - max(0.0, tau - 1.2) ** 1.6 * (260 + 200 * float(hsh(seed + j * 9))) * s
        if py < -200:
            continue
        sc = (0.34 + 0.22 * float(hsh(seed + j * 3))) * s * min(1.0, tau * 4)
        flap = 1.0 + (0.25 * math.sin(T * 16 + j) if kind == "bird" else 0.0)
        cv.save(); cv.translate(px, py); cv.scale(1.0, flap); cv.rotate(10 * math.sin(T * 3 + j)); cv.translate(-px, -py)
        shadow_shape(cv, kind, px, py, sc, T, rgb=(40, 10, 54), a=240, seed=seed + j * 5)
        cv.restore()


# ===================================================================== the game-show set
BOARD_DX = 90.0                        # the board sits right of centre so the host (title-safe) never crowds its frame
BOARD = (560 + BOARD_DX, 190, 1360 + BOARD_DX, 616)   # the firelit cave wall used as the game board (layer 0.75 world coords)
SIGN_CX = 960 + BOARD_DX
HOST_X, HOST_Y, HOST_S = 330.0, 1110.0, 0.86
GARY_X, GARY_EY, GARY_S = 1400.0, 560.0, 0.52
POD_Y, POD_S = 905.0, 0.85
CONT = [dict(x=1640, fy=874, ps=0.7, seed=4520, rgb=(110, 50, 120), eye=(255, 200, 240)),
        dict(x=1845, fy=846, ps=0.6, seed=4560, rgb=(70, 34, 124), eye=(255, 240, 170))]


def _stalactites(cv, T, seed, y0=-10, x0=-200, x1=2120, n=16, col=None, lights=True, t=0.0, dead=0.0):
    col = col or CV_ROCK2
    tips = []
    for k in range(n):
        sx = x0 + (k + 0.5) * (x1 - x0) / n + 40 * math.sin(k * 2.3)
        sl = 70 + 110 * float(hsh(seed + k))
        blob(cv, [(sx - 34, y0), (sx + 34, y0), (sx + 6, y0 + sl), (sx - 2, y0 + sl + 6)], col, w=4, seed=seed + 30 + k, boil=0.8, n=3,
             shade=lambda c, sx=sx, sl=sl: c.drawPath(poly_path([(sx + 6, y0), (sx + 34, y0), (sx + 6, y0 + sl)]), paint(mix(col, INK, 0.3))))
        tips.append((sx, y0 + sl * 0.62))
    if lights:                                                            # festive string lights draped between the tips
        P = []
        for k in range(len(tips) - 1):
            a, b = tips[k], tips[k + 1]
            for u in np.linspace(0, 1, 5, endpoint=False):
                P.append((lerp(a[0], b[0], u), lerp(a[1], b[1], u) + 40 * math.sin(math.pi * u)))
            line(cv, [a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + 40), b], 2.4, INK, seed=seed + 80 + k, boil=0.5, n=4, taper=(0, 0))
        P = np.array(P)
        cols = [P_["magenta"], P_["yellow"], P_["teal"], P_["acid"], P_["orange"]]
        lit = bulb_states(len(P), t, "chase" if dead < 0.3 else "sparkle", seed=seed, dead=dead, speed=5)
        for j, c in enumerate(cols):
            m = (np.arange(len(P)) % len(cols)) == j
            bulbs(cv, P[m], 7, lit[m], rgb=c, glow=0.9)


def game_set(cv, T, t, cam, st=None):
    """The 'GUESS THAT SHADOW!' stage inside the cave (back layers only: cavern, board + sign, stage floor, spotlights).
    st keys: mode (bulb mode), dead (dead-bulb fraction), board (fn(cv) drawn on the wall, clipped), sign (0..3 words lit),
    sign_flash, spots (list of (x0, y0, x1, y1, w0, w1, rgb, a) in layer-1 world coords), fire (0..1 wall glow)."""
    st = st or {}
    mode = st.get("mode", "chase")
    dead = st.get("dead", 0.0)
    C = sets.Cam(cv, cam)
    with C.layer(0.45):                                                  # the cavern
        w.field(cv, CV_ROCK_DK)
        rock_mass(cv, [(-400, -300), (2400, -300), (2400, 1100), (-400, 1100)], seed=7011, rgb=(40, 16, 78), ink=3)
        firelight(cv, 960, 760, 1200, T, a=int(80 * st.get("fire", 1.0)), seed=7012)
        for side in (-1, 1):                                             # flanking rock pillars, rim-lit
            bx = 960 + side * 1020
            pts = [(bx - 260, -300), (bx + 260, -300), (bx + 200 * (1 if side < 0 else 1), 300), (bx + 280, 700), (bx + 260, 1100), (bx - 260, 1100), (bx - 200, 600),
                   (bx - 240, 200)]
            rock_mass(cv, pts, seed=7020 + side, rgb=CV_ROCK, rim=P_["magenta"] if side < 0 else P_["orange"], rim_side=-side)
        for k, (cx_, cy_, sc) in enumerate(((-30, 700, 0.9), (150, 640, 0.6), (1780, 660, 0.8), (1950, 720, 0.7), (240, 560, 0.5), (1650, 560, 0.5))):
            crystal(cv, cx_, cy_, sc, T, seed=7030 + k)
        _stalactites(cv, T, 7040, y0=-30, t=t, dead=dead)
    with C.layer(0.75):                                                  # the game board = the firelit cave wall
        x0, y0, x1, y1 = BOARD
        firelight(cv, (x0 + x1) / 2, (y0 + y1) / 2, 760, T, a=int(90 * st.get("fire", 1.0)), rgb=P_["orange"], seed=7050)
        frame = rrect(x0 - 34, y0 - 34, x1 + 34, y1 + 34, 54, n=4)
        blob(cv, frame, P_["magenta"], w=6, seed=7051, boil=0.8, n=3,
             shade=lambda c: (c.drawPath(poly_path(rrect(x0 - 22, y0 - 22, x1 + 22, y1 + 22, 44, n=4)), paint((200, 20, 130))),
                              stipple(c, P_["hotpink"], (x0 - 40, y0 - 40, x1 + 40, y1 + 40), spacing=11, r=1.6, seed=7052)))
        inner = rrect(x0, y0, x1, y1, 30, n=4)
        wall_surface(cv, inner, T, seed=7053, cx=(x0 + x1) / 2, cy=y1 - 60, glow=st.get("fire", 1.0))
        fn = st.get("board")
        if fn is not None:                                               # board content is authored centred on x=960
            cv.save(); cv.clipPath(poly_path(inner), doAntiAlias=True); cv.translate(BOARD_DX, 0)
            fn(cv)
            cv.restore()
        marquee_ring(cv, rrect(x0 - 17, y0 - 17, x1 + 17, y1 + 17, 42, n=4), 31, 7.5, t, mode=mode, seed=7054, dead=dead,
                     colors=[BULB, P_["yellow"]] if mode != "red" else [P_["red"]])
        # the marquee sign
        sx0, sx1, sy0, sy1 = 455 + BOARD_DX, 1465 + BOARD_DX, 62, 172
        sign = [(sx0, sy1), (sx0 + 20, sy0 + 26), (SIGN_CX, sy0 - 4), (sx1 - 20, sy0 + 26), (sx1, sy1), (SIGN_CX, sy1 + 12)]
        blob(cv, sign, P_["night"], w=6, seed=7060, boil=0.9, n=6,
             shade=lambda c: stipple(c, P_["vdark"], (sx0, sy0 - 10, sx1, sy1 + 20), spacing=10, r=1.8, seed=7059))
        brush(cv, cr_closed(jit([(sx0 + 18, sy1 - 8), (sx0 + 34, sy0 + 32), (SIGN_CX, sy0 + 8), (sx1 - 34, sy0 + 32), (sx1 - 18, sy1 - 8), (SIGN_CX, sy1 + 2)], 0.8, 7061), 6),
              6.0, GOLD, closed=True, seed=7062)
        lit_words = st.get("sign", 3)
        words = [("GUESS", -326), ("THAT", -24), ("SHADOW!", 306)]
        sf = st.get("sign_flash", 0.0)
        for i, (wd, dx) in enumerate(words):
            on = i < lit_words
            fl = sf if (on and i == lit_words - 1) else 0.0
            if fl > 0.05:
                firelight(cv, SIGN_CX + dx, 120, 190 * (1 + fl), T, a=int(200 * fl), rgb=P_["yellow"], seed=7063 + i)
            bulb_text(cv, wd, SIGN_CX + dx, 146, "shrik", 70 * (1 + 0.08 * fl), t, fill=P_["yellow"] if on else (120, 90, 110),
                      shadow_rgb=P_["magenta"] if on else INK, seed=7064 + i, mode=(st.get("sign_mode", mode) if on else "off"), dead=dead, glow=1.0 if on else 0)
        for side in (-1, 1):
            sparkle(cv, SIGN_CX + side * 530, 118 + 8 * math.sin(T * 3 + side), 22 + 6 * math.sin(T * 7 + side), P_["yellow"], seed=7068 + side)
    with C.layer(0.9):                                                   # the stage floor: a sunburst disc on the cave floor
        rock_mass(cv, [(-300, 690), (600, 676), (1300, 690), (2300, 670), (2300, 1300), (-300, 1300)], seed=7070, rgb=CV_ROCK2, rim=P_["orange"], ink=4.5)
        fx, fy, frx, fry = 980, 905, 1180, 205
        disc = ell(fx, fy, frx, fry, n=36)
        cv.save(); cv.clipPath(poly_path(cr_closed(disc, 3)), doAntiAlias=True)
        w.sunburst(cv, fx, fy + 60, 1500, 32, [mix(CV_ROCK2, P_["magenta"], 0.45), mix(CV_ROCK2, P_["violet"], 0.25)], rot_deg=0, seed=7071)
        for k, (rx_, c_) in enumerate(((0.62, P_["magenta"]), (0.4, P_["orange"]), (0.2, P_["yellow"]))):
            cv.drawPath(poly_path(cr_closed(ell(fx, fy + 30, frx * rx_, fry * rx_ * 1.1, n=24), 3)), paint(c_, 150, stroke=10))
        cv.restore()
        brush(cv, cr_closed(jit(disc, 1.0, 7072), 3), 6, closed=True, seed=7073)
        back = [(fx + frx * math.cos(a), fy + fry * math.sin(a)) for a in np.linspace(math.pi * 1.02, math.pi * 1.98, 24)]
        bl = np.array(back)
        bulbs(cv, bl, 8, bulb_states(len(bl), t, mode, seed=7074, dead=dead, speed=7), rgb=P_["yellow"] if mode != "red" else P_["red"], glow=0.9)
        for k, (mx_, my_) in enumerate(((60, 1000), (1880, 990), (1700, 1040))):
            glow_mushroom(cv, mx_, my_, 0.9, T, seed=7080 + k)
    for sp in st.get("spots", []):                                         # spotlight cones (layer 1.0 world coords)
        with C.layer(1.0):
            spot_cone(cv, *sp)


def host_mic(cv, hands):
    """Prop: a skinny 1970s stick microphone in the host's right glove."""
    wx, wy, ang = hands["aR"]
    a = math.radians(ang - 10)
    gx, gy = wx + 22 * math.cos(math.radians(ang)), wy + 22 * math.sin(math.radians(ang))
    d = np.array([math.cos(a), math.sin(a)])
    p0 = np.array([gx, gy]) - d * 34
    p1 = np.array([gx, gy]) + d * 80
    line(cv, [p0, p1], 13, INK, seed=8801, boil=0.4, n=2, taper=(0, 0))
    line(cv, [p0, p1], 7, (200, 200, 215), seed=8801, boil=0.4, n=2, taper=(0, 0))
    line(cv, [p0 - d * 30, p0 - d * 60 + np.array([-10, 30])], 4, (40, 40, 50), seed=8802, boil=0.6, n=3)
    hx, hy = p1 + d * 14
    blob(cv, ell(hx, hy, 18, 18, n=9), (150, 150, 170), w=4, seed=8803, boil=0.6,
         shade=lambda c: [c.drawLine(hx - 20, hy - 12 + k * 6, hx + 20, hy - 12 + k * 6, paint((90, 90, 110), stroke=1.6)) for k in range(5)])
    dots(cv, [(hx - 6, hy - 6)], 4, P_["white"])


def game_host(A, x=HOST_X, y=HOST_Y, s=HOST_S, **kw):
    h = dict(A["HOST"])
    h.update(x=x, y=y, s=s, legs=False, aR_pose="hold", prop=host_mic)
    h.update(kw)
    return h


def gameshow_scene(cv, t, T, A, cam, st=None):
    """Draw the full stage with everyone on it. st (all optional): see game_set + host (dict overrides), gary (gary2 kwargs),
    press/buzz (Gary's buzzer), pod_mode, cont (list of mood dicts), coins (0..1), crate (dict x, lid, k), cheer, laugh,
    swarm (0..1), aud (bool)."""
    st = st or {}
    game_set(cv, T, t, cam, st)
    C = sets.Cam(cv, cam)
    mode = st.get("mode", "chase")
    dead = st.get("dead", 0.0)
    with C.layer(1.0):
        ci = st.get("cont", [{}, {}])
        cpos = []
        for k in (1, 0):                                                   # the other two contestants (far first)
            c = CONT[k]
            m = ci[k] if k < len(ci) else {}
            ps = c["ps"]
            top = c["fy"] - 270 * ps
            cs = ps * 1.12
            r = 70 * cs
            contestant(cv, c["x"] - 18 * ps, top - 116 * ps + r * 1.33, cs, T, seed=c["seed"], rgb=c["rgb"], eye_rgb=c["eye"],
                       look=m.get("look", (-0.6, -0.2)), mood=m.get("mood", "neutral"), k=m.get("k", 1.0))
            cpos.append((k, c, ps, top, r))
        g = dict(st.get("gary", {}))
        gx = g.pop("x", GARY_X)
        gy = g.pop("y", GARY_EY)
        gs = g.pop("s", GARY_S)
        chain_to = g.pop("chain_to", "ring")
        gary2(cv, gx, gy, gs, T, part="body", chain_to=None, **g)          # Gary behind the podium row
        for k, c, ps, top, r in cpos:
            podium(cv, c["x"], c["fy"], ps, T, t, name=["ZORP", "BLIB"][k], seed=7520 + k * 40, mode=st.get("pod_mode", mode), dead=dead,
                   rgb=[(40, 110, 200), (230, 110, 30)][k], name_rgb=[P_["blue"], P_["orange"]][k], buzzer=True)
            ny = top - 116 * ps + r * 1.33 - r * 1.15 + r * 0.86
            chain(cv, (c["x"] - 18 * ps - r * 0.6, ny + r * 0.1), (c["x"] - 165 * ps - 6 * ps, top + 30 * ps), seed=7530 + k, link=max(8.0, 20 * ps), sag=18 * ps, w=2.6)
        bt, ring = podium(cv, GARY_X, POD_Y, POD_S, T, t, name="GARY", seed=7500, mode=st.get("pod_mode", mode), dead=dead,
                          press=st.get("press", 0.0), buzz=st.get("buzz", 0.0))
        if chain_to is not None and g.get("collar", True):
            c0 = (gx + 70 * gs, gy + 6 * math.sin(T * 3.1) * gs * g.get("bob", 1.0) + 144 * gs)
            chain(cv, c0, ring if chain_to == "ring" else chain_to, seed=4461, link=max(8.0, 22 * gs), sag=26 * gs, w=max(1.8, 3.4 * gs))
            blob(cv, ell(ring[0], ring[1], 9, 7, n=8), (130, 130, 160), w=3, seed=4462, boil=0.4)
        gary2(cv, gx, gy, gs, T, part="arms", **{k: v for k, v in g.items() if k in ("armL", "armR", "tremble", "seed")})
        if st.get("gary_fx") is not None:
            st["gary_fx"](cv, gx, gy, gs)
        h = game_host(A, **st.get("host", {}))
        draw_host(cv, h)
        lectern(cv, HOST_X, HOST_Y - 6, HOST_S, T, t, mode=mode, dead=dead)
        if st.get("coins", 0) > 0:
            coin_pile(cv, 900, 1010, 0.95, T, k=st["coins"])
        cr = st.get("crate")
        if cr is not None:
            crate(cv, cr["x"], cr.get("y", 1050), cr.get("s", 0.95), T, lid=cr.get("lid", 0.0), leak=cr.get("leak", 1.0))
            shadow_swarm(cv, cr["x"], cr.get("y", 1050) - 300, 1.0, T, cr.get("swarm", 0.0))
    if st.get("aud", True):
        with C.layer(1.2):
            audience_backs(cv, T, cheer=st.get("cheer", 0.0), laugh=st.get("laugh", 0.0))


# ===================================================================== the sting
def _rock_frame(cv, hole, T, seed=7900, rgb=None, rim=None, glow=True):
    """Cave rock filling the frame around an irregular opening `hole` (inked along the opening), crystals in the corners."""
    rgb = rgb or CV_ROCK
    Hp = cr_closed(jit(hole, 1.2, seed), 5)
    p = poly_path(np.array([(-80, -80), (W + 80, -80), (W + 80, H + 80), (-80, H + 80)]))
    p.addPoly(_pts(Hp), True)
    p.setFillType(skia.PathFillType.kEvenOdd)
    cv.drawPath(p, paint(rgb))
    cv.save(); cv.clipPath(p, doAntiAlias=True)
    for k in range(6):
        yy = 60 + k * 190
        line(cv, [(-40, yy + 20 * math.sin(k * 1.9)), (960, yy - 16 * math.sin(k + seed)), (1960, yy + 12 * math.sin(k * 2.7))], 3.0, mix(rgb, INK, 0.35),
             seed=seed + 20 + k, boil=0.8, n=6, taper=(0.1, 0.1), a=170)
    stipple(cv, mix(rgb, INK, 0.45), (-40, -40, W + 40, H + 40), spacing=17, r=2.2, seed=seed + 2,
            fn=lambda X, Y: np.clip(0.3 + 0.7 * np.sin(X * 0.013 + Y * 0.02 + seed) ** 2, 0, 1) * 0.8)
    brush(cv, Hp, 40, rim or P_["magenta"], closed=True, seed=seed + 4, a=120)
    cv.restore()
    brush(cv, Hp, 7, closed=True, seed=seed + 3)
    if glow:
        for k, (cx_, cy_, sc, ang) in enumerate(((80, 1040, 1.0, 0), (1840, 1040, 1.0, 0), (60, 600, 0.7, 0), (1860, 560, 0.7, 0), (960, 1068, 0.8, 0))):
            crystal(cv, cx_, cy_, sc, T, seed=seed + 40 + k)


def _sting_hole():
    """The cave-mouth opening of the sting: heavy rock with stalactites above, stalagmites below."""
    pts = [(120, 190), (190, 168), (232, 300), (276, 166), (420, 160), (466, 262), (500, 230), (532, 158), (760, 150), (812, 236), (850, 150),
           (1080, 146), (1128, 286), (1176, 148), (1420, 154), (1468, 252), (1492, 222), (1522, 156), (1690, 162), (1736, 270), (1770, 170), (1806, 196)]
    for k in range(1, 6):
        pts.append((1800 + 26 * math.sin(k * 1.7), 196 + k * 770 / 6))
    pts += [(1806, 972), (1700, 978), (1652, 890), (1606, 980), (1260, 990), (960, 982), (700, 992), (404, 984), (352, 900), (300, 986), (120, 972)]
    for k in range(5, 0, -1):
        pts.append((120 + 26 * math.sin(k * 2.3), 196 + k * 770 / 6))
    return pts


def spiky_star(cv, x, y, r0, r1, n, rot, fill, seed=0, ink=6.0, inner=None):
    pts = []
    for k in range(2 * n):
        a = math.radians(rot) + k * math.pi / n
        rr = r1 if k % 2 == 0 else r0
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    blob(cv, rect_pts(pts, 2), fill, w=ink, seed=seed, boil=1.0, n=3)
    if inner is not None:
        q = [(x + (px - x) * 0.82, y + (py - y) * 0.82) for px, py in pts]
        blob(cv, rect_pts(q, 2), inner, w=0, seed=seed + 1, boil=0.8, n=3, misreg=(0, 0))


def _slam(t, t0, dur=0.2):
    """Scale + squash for a word slamming in at t0: returns (visible, scale, sx, sy, alpha)."""
    if t < t0:
        return False, 0, 1, 1, 0
    u = (t - t0) / dur
    if u < 1:
        sc = 1 + 2.4 * (1 - u) ** 2
        return True, sc, 1.0, 1.0, int(255 * min(1.0, u * 3))
    tt = t - t0 - dur
    wob = math.exp(-tt * 7) * math.cos(tt * 34)
    return True, 1.0, 1 + 0.14 * wob, 1 - 0.14 * wob, 255


def sting(cv, t, T, sad=False, seed=7200):
    """'GUESS THAT SHADOW!' marquee sting on the cave wall. sad=True -> the dingy RETURN version (dead bulbs, flicker,
    crooked sagging letters, an O that falls off)."""
    hits = [0.22, 0.62, 1.05] if not sad else [0.55, 1.35]
    dx, dy = jolt(t, hits, amp=26 if not sad else 8, seed=seed)
    z = 1.0 + 0.02 * t + (0.0 if sad else 0.03 * sum(imp(t, h, 0.18) for h in hits))
    cv.save()
    cv.translate(W / 2 + dx, H / 2 + dy); cv.scale(z, z); cv.translate(-W / 2, -H / 2)
    if not sad:
        w.field(cv, P_["night"])
        cols = [P_["magenta"], P_["violet"]] if t < 1.05 else [P_["magenta"], P_["violet"], P_["orange"], P_["violet"]]
        w.sunburst(cv, 960, 560, 1500, 28, cols, rot_deg=t * 28, seed=seed)
        w.stars(cv, seed + 3, (60, 60, 1860, 1020), n=90, big=6)
        pul = 1 + 0.06 * math.sin(t * 9) + 0.12 * sum(imp(t, h, 0.15) for h in hits)
        spiky_star(cv, 960, 560, 330 * pul, 500 * pul, 18, -t * 40, P_["yellow"], seed=seed + 1, inner=P_["orange"])
        spiky_star(cv, 960, 560, 230 * pul, 330 * pul, 14, t * 55, P_["hotpink"], seed=seed + 2, inner=mix(P_["hotpink"], P_["magenta"], 0.5), ink=5)
        for side in (-1, 1):                                              # two sweeping searchlights
            ang = math.radians(-90 + side * (28 + 22 * math.sin(t * 2.2 + side)))
            spot_cone(cv, 960 + side * 760, 1080, 960 + side * 760 + 1300 * math.cos(ang), 1080 + 1300 * math.sin(ang), 20, 170, P_["cream"], 55)
    else:
        w.field(cv, (40, 26, 52))
        w.sunburst(cv, 960, 560, 1500, 28, [(96, 60, 96), (66, 44, 80)], rot_deg=t * 3, seed=seed)
        spiky_star(cv, 960, 560, 330, 500, 18, -6 + t * 2, (150, 130, 80), seed=seed + 1, inner=(130, 100, 70))
        spiky_star(cv, 960, 560, 230, 330, 14, 3, (130, 90, 110), seed=seed + 2, inner=(110, 80, 100), ink=5)
    hole = _sting_hole()
    ring = rrect(170, 214, 1750, 940, 56, n=4)
    if not sad:                                                           # the marquee bulbs chasing around the wall
        allon = any(0 <= t - h < 0.16 for h in hits)
        marquee_ring(cv, ring, 44, 10, t, mode="all" if allon else "chase", seed=seed + 5, colors=[BULB, P_["yellow"], P_["hotpink"]], speed=12)
    else:
        marquee_ring(cv, ring, 44, 10, t, mode="all", seed=seed + 5, dead=0.55, colors=[(230, 220, 170)], glow=0.5)
    layout = [("GUESS", "bangers", 196, 760, 470, -6, P_["yellow"], P_["magenta"]),
              ("THAT", "bangers", 168, 1190, 478, 4, P_["cream"], P_["blue"]),
              ("SHADOW!", "shrik", 190, 960, 772, -3, P_["yellow"], P_["maroon"])]
    for i, (wd, fnt, sz, x, y, rot_, fill, shad) in enumerate(layout):
        if not sad:
            vis, sc, sx, sy, al = _slam(t, hits[i])
            if not vis:
                continue
            k_imp = imp(t, hits[i], 0.25)
            ring_pulse(cv, x, y - sz * 0.35, 120 + 900 * (1 - k_imp), k_imp, P_["white"], 16)
            burst_lines(cv, x, y - sz * 0.35, sz * 1.3, sz * 2.6, 14, k_imp, P_["yellow"], 10, seed=seed + 10 + i)
            cv.save(); cv.translate(x, y - sz * 0.3); cv.rotate(rot_); cv.scale(sc * sx, sc * sy); cv.translate(-x, -(y - sz * 0.3))
            old = core.INKMUL; core.INKMUL = old / max(0.3, sc) ** 0.5
            fills = [P_["yellow"], P_["orange"]] * 4 if fnt == "shrik" else None
            bulb_text(cv, wd, x, y, fnt, sz, t, fill=fill, fills=fills, shadow_rgb=shad, seed=seed + 20 + i,
                      mode="chase" if t > hits[i] + 0.25 else "all", speed=11, a=al, ink_w=7)
            core.INKMUL = old
            cv.restore()
        else:
            dull = mix(fill, (110, 100, 110), 0.55)
            if i == 0:
                cv.save(); cv.translate(x - 200, y - 120); cv.rotate(-13); cv.translate(-(x - 200), -(y - 120))
                bulb_text(cv, wd, x, y + 30, fnt, sz, t, fill=dull, shadow_rgb=(60, 30, 50), seed=seed + 20, mode="all", dead=0.6, glow=0.4)
                cv.restore()
            elif i == 1:                                                  # hanging by one corner, swinging
                sw = 26 + 5 * math.sin(t * 2.3)
                cv.save(); cv.translate(x - 130, y - 140); cv.rotate(sw); cv.translate(-(x - 130), -(y - 140))
                bulb_text(cv, wd, x, y, fnt, sz, t, fill=dull, shadow_rgb=(40, 40, 80), seed=seed + 21, mode="all", dead=0.65, glow=0.4)
                cv.restore()
                line(cv, [(x - 140, y - 250), (x - 132, y - 140)], 3, (190, 190, 200), seed=seed + 40, boil=0.4, n=2)
            else:                                                         # SHAD W! -- the O has fallen off
                for part_, px_ in (("SHAD", x - 300), ("W!", x + 330)):
                    bulb_text(cv, part_, px_, y + (12 if part_ == "W!" else 0), fnt, sz, t, fill=dull, fills=None, shadow_rgb=(60, 20, 40),
                              seed=seed + 22 + len(part_), mode="all", dead=0.55, glow=0.4)
                fall = sm(t, 0.35, 0.75)
                ox = x + 64 + 300 * sm(t, 0.75, 2.4)
                oy = lerp(y, 930, fall) - (60 * abs(math.sin((t - 0.75) * 7)) * math.exp(-(t - 0.75) * 2.5) if t > 0.75 else 0)
                ang = (t - 0.35) * 220 * (1 - sm(t, 2.0, 2.6)) if t > 0.35 else 0
                cv.save(); cv.translate(ox, oy - sz * 0.32); cv.rotate(ang); cv.translate(-ox, -(oy - sz * 0.32))
                bulb_text(cv, "O", ox, oy, fnt, sz, t, fill=dull, shadow_rgb=(60, 20, 40), seed=seed + 29, mode="off", glow=0)
                cv.restore()
    if not sad and t > 1.55:                                                # the bunny pops up beside the title
        k = pop(t, 1.55, 0.4)
        hop = abs(math.sin((t - 1.55) * 5.5)) * 40
        shadow_shape(cv, "bunny", 1500, 860 - hop - (1 - k) * 160, 1.15 * k, T, rgb=CV_SHADOW, seed=seed + 50)
        shadow_shape(cv, "hand_bunny", 440, 850 - abs(math.sin((t - 1.55) * 5.5 + 1.4)) * 30 - (1 - k) * 160, 0.95 * k, T, rgb=CV_SHADOW, seed=seed + 51)
        for q in range(5):
            sparkle(cv, 960 + 700 * math.cos(t * 1.4 + q * 1.26), 560 + 330 * math.sin(t * 1.4 + q * 1.26), 16 + 6 * math.sin(t * 9 + q), P_["cream"],
                    seed=seed + 60 + q)
    if sad:                                                                 # a moth at the one flickering bulb, a cobweb
        bx, by = 1520, 230
        for q in range(2):
            ph = t * 7 + q * 3
            mxp, myp = bx + 40 * math.cos(ph), by + 26 * math.sin(ph * 1.3)
            blob(cv, [(mxp - 12, myp), (mxp, myp - 9), (mxp + 12, myp), (mxp, myp + 6)], (190, 180, 160), w=2.5, seed=seed + 70 + q, boil=0.8, n=3)
        cx0, cy0 = 170, 214
        for j in range(1, 5):
            f = j / 5
            line(cv, [(cx0 + 208 * f, cy0), (cx0 + 140 * f, cy0 + 140 * f), (cx0, cy0 + 194 * f)], 2.0, (220, 220, 230), seed=seed + 80 + j, boil=0.5, n=4, a=150)
        for j in range(5):
            a = math.radians(j * 22.5)
            line(cv, [(cx0, cy0), (cx0 + 260 * math.cos(a), cy0 + 260 * math.sin(a))], 2.0, (220, 220, 230), seed=seed + 90 + j, boil=0.4, n=2, a=150)
    _rock_frame(cv, hole, T, seed=seed + 7, rgb=CV_ROCK if not sad else (44, 30, 60), rim=P_["magenta"] if not sad else (90, 70, 90), glow=not sad)
    cv.restore()
    if not sad:
        flash(cv, 0.55 * sum(imp(t, h, 0.06) for h in hits))
    else:
        fl = 1.0 if hsh(core.D * 0.77 + 3) > 0.78 else 0.0                   # fluorescent flicker
        light_mask(cv, [(960, 560, 1000, 0.62 - 0.25 * fl, (255, 236, 190)), (1520, 230, 260, 0.9 * (1 - fl), (255, 240, 200))], ambient=78 - 30 * fl, T=T)


def star_wipe(cv, u, draw_old, seed=7990):
    """70s star wipe: the new picture (already drawn) shows inside a star growing from the centre; outside it draw_old()."""
    if u >= 1:
        return
    rr = 40 + 1500 * ease(u)
    pts = []
    rot0 = -90 + 40 * u
    for k in range(10):
        a = math.radians(rot0 + k * 36)
        r_ = rr if k % 2 == 0 else rr * 0.45
        pts.append((960 + r_ * math.cos(a), 540 + r_ * math.sin(a)))
    p = poly_path(np.array([(-80, -80), (W + 80, -80), (W + 80, H + 80), (-80, H + 80)]))
    p.addPoly(_pts(pts), True)
    p.setFillType(skia.PathFillType.kEvenOdd)
    cv.save(); cv.clipPath(p, doAntiAlias=True)
    draw_old()
    cv.restore()
    Pp = cr_closed(jit(pts, 1.0, seed), 2)
    brush(cv, Pp, 16, P_["yellow"], closed=True, seed=seed + 1)
    brush(cv, Pp, 6, closed=True, seed=seed + 2)
    bulbs(cv, resample(np.array(pts), 70), 9, np.ones(len(resample(np.array(pts), 70)), bool), glow=1.0)


# ===================================================================== graphics
def correct_graphic(cv, x, y, k, T, t, seed=8100):
    """CORRECT! -- huge flashing marquee lettering with ring pulses, speed lines and sparkles (no backing card)."""
    if k <= 0.01:
        return
    sc = pop(k, 0.0, 1.0)
    for j in range(3):
        kk = cl(1 - ((t * 1.6 + j / 3) % 1.0))
        ring_pulse(cv, x, y - 60, 160 + 520 * (1 - kk), kk * k, [P_["acid"], P_["yellow"], P_["hotpink"]][j], 14)
    burst_lines(cv, x, y - 60, 420 * sc, 760 * sc, 22, k * (0.6 + 0.4 * math.sin(t * 20) ** 2), P_["yellow"], 9, seed=seed, rot0=t * 0.6)
    cv.save(); cv.translate(x, y - 60); cv.rotate(-5 + 2 * math.sin(T * 5)); cv.scale(sc, sc); cv.translate(-x, -(y - 60))
    old = core.INKMUL; core.INKMUL = old / max(0.3, sc) ** 0.5
    bulb_text(cv, "CORRECT!", x, y, "shrik", 176, t, fills=[P_["acid"], P_["yellow"]] * 4, shadow_rgb=P_["magenta"], seed=seed + 2,
              mode="flash" if t % 0.8 < 0.4 else "chase", speed=14, ink_w=7)
    core.INKMUL = old
    cv.restore()
    for q in range(8):
        a = q * math.pi / 4 + T * 1.5
        sparkle(cv, x + 560 * sc * math.cos(a), y - 60 + 200 * sc * math.sin(a), 18 + 8 * math.sin(T * 8 + q), [P_["yellow"], P_["cream"]][q % 2], seed=seed + 10 + q)


def wrong_graphic(cv, x, y, k, T, seed=8200, s=1.0):
    if k <= 0.01:
        return
    sc = pop(k, 0.0, 1.0) * s
    cv.save(); cv.translate(x, y); cv.scale(sc, sc); cv.rotate(4 * math.sin(T * 40))
    old = core.INKMUL; core.INKMUL = old / max(0.3, sc) ** 0.5
    for j in range(10):                                                    # buzz zig-zags
        a = j * math.pi / 5 + 0.3
        r0, r1 = 300, 420
        pts = [(r0 * math.cos(a) + (r1 - r0) * u * math.cos(a) + (14 if q % 2 else -14) * math.sin(a), r0 * math.sin(a) * 0.62 + (r1 - r0) * u * math.sin(a) * 0.62 -
                (14 if q % 2 else -14) * math.cos(a)) for q, u in enumerate(np.linspace(0, 1, 6))]
        line(cv, pts, 7, P_["red"], seed=seed + j, boil=1.0, n=2, taper=(0, 0))
    for side in (-1, 1):
        line(cv, [(-230, -200 * side), (230, 200 * side)], 86, INK, seed=seed + 20 + side, boil=1.4, n=3, taper=(0.06, 0.06))
        line(cv, [(-222, -194 * side), (222, 194 * side)], 62, P_["red"], seed=seed + 20 + side, boil=1.4, n=3, taper=(0.06, 0.06))
    paint_text(cv, "WRONG!", 0, 70, font="bangers", size=210, fill=P_["red"], fills=[P_["red"], (255, 70, 60)], ink_w=8, shadow=(10, 10), shadow_rgb=INK, seed=seed + 30,
               outline_rgb=INK)
    core.INKMUL = old
    cv.restore()


def zap(cv, x, y, s, k, seed=8300):
    """BZZT! fat little lightning bolts jumping out sideways from the buzzer, plus a hot flash."""
    if k <= 0.01:
        return
    firelight(cv, x, y, 220 * s * (0.6 + 0.4 * k), 0.0, a=int(220 * k), rgb=P_["yellow"], seed=seed)
    for j, a0 in enumerate((-95, -70, -45, -20, 5, 30)):
        a = math.radians(a0 + 6 * math.sin(core.D * 1.3 + j))
        n_ = np.array([-math.sin(a), math.cos(a)])
        d_ = np.array([math.cos(a), math.sin(a)])
        L = (90 + 50 * float(hsh(seed + j + core.D * 0.1))) * s * (0.7 + 0.5 * k)
        pts = [np.array([x, y]) + d_ * 50 * s]
        for q in range(1, 4):
            pts.append(np.array([x, y]) + d_ * (50 * s + L * q / 3) + n_ * (16 if q % 2 else -16) * s)
        line(cv, pts, 14 * s + 3, INK, seed=seed + j, boil=1.2, n=2, taper=(0, 0.7), a=int(255 * k))
        line(cv, pts, 8 * s + 2, P_["yellow"], seed=seed + j, boil=1.2, n=2, taper=(0, 0.7), a=int(255 * k))


# ===================================================================== T022 'GUESS THAT SHADOW!'
def _bunny_hop(t, t0, t1, x0, x1, y, hops=4, hh=70):
    u = cl((t - t0) / (t1 - t0))
    x = lerp(x0, x1, u)
    ph = u * hops * math.pi
    return x, y - abs(math.sin(ph)) * hh * (1 if u < 1 else 0)


def T022_gameshow(cv, t, T, A):
    # beats (shot time): S01 'It's time for' 3.77 | GUESS 5.03 | THAT 6.20 | SHADOW 6.60 | Gary! 7.20 | one million cave dollars 8.19-9.81
    #                    | what comes after the bunny 10.44-11.39 | S02 um 12.0 / um 13.17 / a horsey 14.21 | S03 CORRECT 15.66
    #                    | lifetime supply of 16.58-18.16 | more shadows 18.7-19.7 | S04 best day of my life 20.18-22.51
    if t < 3.69:
        if t < 3.33:
            sting(cv, t, T)
            return
        u = (t - 3.33) / 0.36
        _t022_set(cv, 3.69, T, A)
        star_wipe(cv, u, lambda: sting(cv, t, T))
        return
    _t022_set(cv, t, T, A)


T022_KEYS = [  # (t, x, y, z, ease): the host is either wholly inside title-safe (x >= 96 px) or wholly out of frame
    (3.69, -120, -10, 1.0, 0.1), (3.75, -60, -20, 1.07, 1.3),
    (5.03, -80, -60, 1.12, 0.12), (6.20, -112, -80, 1.17, 0.12), (6.60, -150, -100, 1.22, 0.12),   # GUESS! THAT! SHADOW! punch-ins
    (7.20, 360, 20, 1.75, 0.0),                                                                     # smash-cut (with whip streaks) to Gary
    (8.19, -150, 145, 1.2, 0.0), (8.2, -155, 150, 1.22, 2.0),                                       # cut: host + coins + Gary
    (10.25, 372, -150, 1.36, 0.0), (10.26, 382, -160, 1.42, 1.6),                                    # cut: the board + Gary
    (11.88, 380, 30, 2.05, 0.0), (12.0, 400, 10, 2.25, 3.0),                                         # Gary sweats
    (15.58, -135, -20, 1.08, 0.0), (16.6, -162, 40, 1.15, 1.4), (18.7, -132, 20, 1.08, 0.3),        # CORRECT! wide
    (20.10, 380, 10, 2.0, 0.0), (20.2, 385, 0, 2.12, 2.6), (22.75, 330, 20, 1.45, 0.75)]           # tears of joy


def _t022_cam(t):
    cam = lerp_cam(T022_KEYS, t)
    dx, dy = jolt(t, [5.03, 6.20, 6.60, 7.20, 14.21, 15.66, 18.75], amp=12, seed=22)
    cam["x"] += dx; cam["y"] += dy
    return cam


def whip_streaks(cv, k, seed=7990, dirn=1):
    """Speed streaks for a whip-pan (k 0..1)."""
    if k <= 0.02:
        return
    for j in range(26):
        y = 30 + j * 40 + 14 * float(hsh(seed + j + core.D * 0.3))
        x0 = float(hsh(seed + j * 3.1 + core.D * 0.7)) * W
        L = (300 + 600 * float(hsh(seed + j * 5.3))) * k
        cv.drawRect(R(x0 - L / 2, y, x0 + L / 2, y + 3 + 7 * float(hsh(seed + j))), paint([P_["white"], P_["hotpink"], P_["yellow"]][j % 3], int(150 * k)))


def _t022_set(cv, t, T, A):
    GUESS, THAT, SHADOW, GARY_T = 5.03, 6.20, 6.60, 7.20
    LAND = (5.55, 6.52, 7.12)                                                # each shouted word flies up into the sign
    st = dict(mode="chase", sign=0, sign_flash=0.0, cont=[{}, {}])
    # ---- the sign lights up word by word as GUESS! THAT! SHADOW! land in it
    lit = sum(1 for h in LAND if t >= h)
    st["sign"] = 3 if t >= 8.0 else lit
    st["sign_flash"] = max(imp(t, LAND[0], 0.3), imp(t, LAND[1], 0.3), imp(t, LAND[2], 0.35))
    if 4.9 <= t < GUESS:
        st["mode"] = "off"
    if any(0 <= t - h < 0.2 for h in (GUESS, THAT, SHADOW)):
        st["mode"] = "all"
    # ---- camera
    cam = _t022_cam(t)
    # ---- board content
    def board(c):
        if t < 10.2:
            if t >= 8.4:                                                     # the prize on the board
                paint_text(c, "$1,000,000", 960, 440, font="bangers", size=150 * pop(t, 8.5, 0.35) + 1, fill=P_["yellow"], ink_w=6, shadow=(8, 8),
                           shadow_rgb=P_["maroon"], seed=7104)
                if t > 8.8:
                    paint_text(c, "CAVE DOLLARS", 960, 520, font="londrina", size=58, fill=P_["cream"], ink_w=4, shadow=(5, 5), shadow_rgb=P_["maroon"], seed=7105,
                               reveal=cl((t - 8.8) / 0.4))
            else:                                                            # idle: the host's hand-bunny from the cold open
                shadow_shape(c, "hand_bunny", 960 + 30 * math.sin(T * 0.8), 470, 1.2, T, seed=7106, a=150)
            return
        if t < 15.62:                                                        # the bunny hops on and waits... '?'
            bx, by = _bunny_hop(t, 10.2, 11.25, 420, 900, 480, hops=4, hh=80)
            shadow_shape(c, "bunny", bx, by, 1.45, T, seed=7101)
            if t > 11.3:
                k = pop(t, 11.3, 0.3)
                paint_text(c, "?", 1170 - BOARD_DX, 540, font="shrik", size=260 * k + 1, fill=P_["cream"], ink_w=6, shadow=(8, 8), shadow_rgb=P_["maroon"], seed=7102)
            return
        if t < 17.9:                                                         # the bunny hops off, the horse gallops after it
            ub = sm(t, 15.62, 16.9)
            bx = 900 + 760 * ub
            by = 480 - abs(math.sin(ub * 4 * math.pi)) * 80
            if bx < 1560:
                shadow_shape(c, "bunny", bx, by, 1.45, T, seed=7101)
            u = cl((t - 15.62) / 2.2)
            hx = lerp(240, 1640, u)
            hy = 540 - abs(math.sin(u * 9 * math.pi)) * 34
            c.save(); c.translate(hx, hy); c.rotate(-6 * math.sin(u * 18 * math.pi)); c.translate(-hx, -hy)
            shadow_shape(c, "horse", hx, hy, 1.5, T, seed=7103)
            c.restore()
        if 17.55 <= t < 18.75:                                               # drum roll...
            k = pop(t, 17.55, 0.3)
            wob = 3 * math.sin(T * 40)
            paint_text(c, "A LIFETIME", 960 + wob, 380, font="bangers", size=118 * k + 1, fill=P_["cream"], ink_w=5, shadow=(7, 7), shadow_rgb=P_["maroon"],
                       seed=7107)
            if t > 17.85:
                paint_text(c, "SUPPLY OF...", 960 - wob, 500, font="bangers", size=118 * pop(t, 17.85, 0.3) + 1, fill=P_["cream"], ink_w=5, shadow=(7, 7),
                           shadow_rgb=P_["maroon"], seed=7108)
        if t >= 18.72:                                                       # MORE SHADOWS: a crowded parade on the wall
            kinds = ["bird", "horse", "bunny", "tree", "fish", "person", "jug", "star"]
            for j, kind in enumerate(kinds):
                ph = ((t - 18.72) * 0.22 + j / len(kinds)) % 1.0
                px = 1480 - ph * 1040
                py = 420 - abs(math.sin(ph * 30 + j)) * 26 + (j % 2) * 40
                shadow_shape(c, kind, px, py, 0.62, T, seed=7120 + j, a=int(230 * min(1.0, (t - 18.72) / 0.3)))
    st["board"] = board
    # ---- spotlights
    sw = math.sin(T * 0.9)
    spots = [(250 + 60 * sw, -60, 520 + 260 * sw, 980, 26, 170, P_["magenta"], 46), (1700 - 60 * sw, -60, 1350 - 240 * sw, 980, 26, 170, P_["teal"], 40)]
    spots.append((HOST_X + 80, -60, HOST_X, 1000, 30, 210, P_["yellow"], 50))
    if t >= GARY_T:
        spots.append((GARY_X - 40, -60, GARY_X, 930, 28, 200, P_["white"], int(70 * min(1.0, (t - GARY_T) / 0.08))))
    st["spots"] = spots
    # ---- Gary
    g = dict(look=(-0.75, -0.1), armL="hang", armR=(78, 120, 80, "flat"))
    if t < GARY_T:
        hopk = sum(imp(t, h, 0.25) for h in (GUESS, THAT, SHADOW))
        g.update(y=GARY_EY - 22 * hopk, pupil=0.5 + 0.1 * hopk, mouth="smile")
    elif t < 8.19:                                                           # 'Gary!' -- startled in the spotlight
        k = imp(t, GARY_T, 0.4)
        g.update(y=GARY_EY - 40 * k, lid=0.0, pupil=0.3 + 0.25 * (1 - k), look=(-0.5, -0.3), armL="up", armR="up", mouth="o")
    elif t < 10.2:                                                           # one million cave dollars: $$$
        g.update(iris_kind="dollar" if t > 8.5 else None, lid=0.02, look=(-0.5, 0.1), mouth="grin", armL="hang", armR=(60, 100, 60, "flat"),
                 y=GARY_EY - 8 * abs(math.sin(T * 6)))
    elif t < 11.88:                                                          # the bunny! (heart eyes)
        g.update(iris_kind="heart" if t > 10.5 else None, look=(-0.6, -0.65), lid=0.0, mouth="smile", armL=(-150, 40, -60, "open"), armR=(150, 40, -120, "open"))
    elif t < 15.58:                                                          # S02: sweating, straining
        u = t - 11.88
        dart = math.sin(T * 7.3) * 0.5
        g.update(look=(dart * 0.6 - 0.2, -0.45), pupil=0.32, lid=0.14 + 0.05 * math.sin(T * 3), squint=0.7 if t < 14.2 else 0.0, tremble=6 if t < 14.2 else 0,
                 armL="hang")
        if t >= 14.21:
            g.update(look=(0.1, -0.4), lid=0.0, pupil=0.5, mouth=None)
        st["press"] = sm(t, 14.21, 14.28) * (1 - sm(t, 14.8, 15.0))
        st["buzz"] = imp(t, 14.21, 0.6)
    elif t < 20.1:                                                           # CORRECT! / more shadows
        k = imp(t, 15.66, 0.5)
        g.update(y=GARY_EY - 50 * k - 10 * abs(math.sin(T * 7)), lid=0.0, pupil=0.62, look=(-0.4, -0.4), mouth="grin", armL="up", armR="up")
        if t > 16.6:
            g.update(look=(-0.7, 0.4), iris_kind="heart" if t > 18.7 else None)
    else:                                                                    # S04: sobbing with joy
        g.update(mouth="sob", happy=0.42, lid=0.3, look=(0.0, 0.0), pupil=0.5, tears_pool=1.0, armL=(-120, 40, -40, "open"), armR=(120, 40, -140, "open"),
                 tremble=3)
    LK = [(3.69, "hang", 0), (GARY_T, "up", 0.16), (8.19, "hang", 0.3), (10.25, (-150, 40, -60, "open"), 0.3), (11.88, "hang", 0),
          (15.62, "up", 0.18), (20.1, (-120, 40, -40, "open"), 0)]
    RK = [(3.69, (78, 120, 80, "flat"), 0), (GARY_T, "up", 0.16), (8.19, (60, 100, 60, "flat"), 0.3), (10.25, (150, 40, -120, "open"), 0.3),
          (11.88, (78, 120, 80, "flat"), 0), (13.9, (178, -70, -80, "fist"), 0.28), (14.21, (140, 120, 80, "flat"), 0.08), (15.62, "up", 0.18),
          (20.1, (120, 40, -140, "open"), 0)]
    g["armL"] = arm_track(LK, t, T, -1)
    g["armR"] = arm_track(RK, t, T, 1)
    st["gary"] = g
    # ---- contestants
    cont_mood = "neutral"
    if 15.66 <= t < 20.1:
        cont_mood = "cheer"
    elif 11.88 <= t < 15.58:
        cont_mood = "stare"
    elif t >= 20.1:
        cont_mood = "gasp"
    st["cont"] = [dict(mood=cont_mood, look=(-0.8, -0.1)), dict(mood=cont_mood, look=(-0.8, 0.0))]
    # ---- props / crowd
    st["coins"] = sm(t, 8.4, 8.85) * (1 - sm(t, 10.0, 10.25)) if 8.0 < t < 10.3 else 0.0
    if t >= 16.5:
        k = sm(t, 16.55, 17.35)
        bx_ = lerp(2350, 900, k) + (12 * math.sin((t - 17.35) * 18) * math.exp(-(t - 17.35) * 4) if t > 17.35 else 0)
        st["crate"] = dict(x=bx_, lid=max(0.0, t - 18.72), swarm=max(0.0, t - 18.76), leak=1.0 - sm(t, 18.8, 19.8))
    st["cheer"] = 1.0 if 15.66 <= t < 20.1 else (0.4 if t >= 20.1 else 0.0)
    if 15.66 <= t < 16.2 or (20.1 <= t and (core.D % 2 == 0)):
        st["pod_mode"] = "flash"
    if 15.66 <= t < 16.4:
        st["mode"] = "flash"
    elif t >= 15.66:
        st["mode"] = "chase"
    gameshow_scene(cv, t, T, A, cam, st)
    # ---- overlays
    C = sets.Cam(cv, cam)
    if GARY_T <= t < GARY_T + 0.3:
        whip_streaks(cv, 1.0 - cl((t - GARY_T) / 0.3))
    if GARY_T <= t < 8.5:                                                    # 'Gary!' -- the stage dims to one spotlight
        dip = sm(t, GARY_T, GARY_T + 0.06) * (1 - sm(t, 8.1, 8.45))
        gx_, gy_ = C.to_screen(GARY_X, GARY_EY + 40)
        light_mask(cv, [(gx_, gy_, 560, 1.0, (255, 250, 235))], ambient=255 - 150 * dip, T=T)
    for i, (wd, t0, t1, dxs, fill) in enumerate((("GUESS!", GUESS, LAND[0], -326, P_["yellow"]), ("THAT!", THAT, LAND[1], -24, P_["cream"]),
                                                  ("SHADOW!", SHADOW, LAND[2], 306, P_["yellow"]))):
        if not (t0 <= t < t1):
            continue
        fly = sm(t, t1 - 0.2, t1)
        vis, sc, sx_, sy_, al = _slam(t, t0, 0.14)
        tx, ty = C.to_screen(SIGN_CX + dxs, 146 - 24, 0.75)
        size0 = 170
        size = lerp(size0, 70 * C.zoom(0.75), fly)
        cx_, cy_ = lerp(930, tx, fly), lerp(420, ty, fly)
        kimp = imp(t, t0, 0.22)
        ring_pulse(cv, 930, 420, 140 + 800 * (1 - kimp), kimp, P_["white"], 14)
        burst_lines(cv, 930, 420, 300, 640, 16, kimp, P_["yellow"], 10, seed=7140 + i)
        k = size / size0 * sc
        cv.save(); cv.translate(cx_, cy_); cv.rotate([-6, 4, -3][i] * (1 - fly)); cv.scale(k * sx_, k * sy_)
        old = core.INKMUL; core.INKMUL = old / max(0.15, k) ** 0.5
        bulb_text(cv, wd, 0, size0 * 0.36, "shrik", size0, t, fill=fill, shadow_rgb=P_["magenta"], seed=7150 + i, mode="all", ink_w=7, a=al)
        core.INKMUL = old
        cv.restore()
    if 14.21 <= t < 15.3:
        C = sets.Cam(cv, cam)
        bx, by = C.to_screen(GARY_X + 104 * POD_S, POD_Y - 270 * POD_S - 60 * POD_S)
        zp = sets.Cam(cv, cam).zoom(1.0)
        zap(cv, bx, by, zp * 0.9, imp(t, 14.21, 0.5), seed=8301)
        k = pop(t, 14.25, 0.25) * (1 - sm(t, 14.95, 15.2))
        if k > 0.01:
            cv.save(); cv.translate(bx + 300, by - 210); cv.rotate(-10); cv.scale(k, k)
            paint_text(cv, "BZZT!", 0, 0, font="bangers", size=150, fill=P_["yellow"], ink_w=6, shadow=(8, 8), shadow_rgb=P_["red"], seed=8302)
            cv.restore()
    if 15.62 <= t < 17.4:
        correct_graphic(cv, 960, 400, cl((t - 15.62) / 0.35) * (1 - sm(t, 17.0, 17.4)), T, t)
    for (t0, x, y, ang) in ((15.66, -20, 1010, -62), (15.66, 1940, 1010, -118), (18.75, -20, 1060, -55), (18.75, 1940, 1060, -125)):
        confetti_burst(cv, t, t0, x, y, ang, spread=20, n=60, speed=1700, seed=int(t0 * 10 + x), life=4.6)
    if t >= 16.0:
        confetti_rain(cv, t, seed=8400, n=50, a=min(1.0, (t - 16.0) / 0.6))
    if t >= 20.1:                                                            # tears of joy (screen space over the CU)
        C = sets.Cam(cv, cam)
        zp = C.zoom(1.0)
        gx, gy = C.to_screen(GARY_X, GARY_EY + 6 * math.sin(T * 3.1) * GARY_S)
        for side in (-1, 1):
            tear_fountain(cv, gx + side * 140 * GARY_S * zp, gy + 10 * GARY_S * zp, GARY_S * zp, t + side * 0.37, side, rate=16, power=1.1, seed=8500 + side * 7)
        if t < 22.75:
            k = pop(t, 20.4, 0.3)
            cv.save(); cv.translate(gx - 420 * GARY_S * zp, gy - 280 * GARY_S * zp); cv.rotate(-8); cv.scale(k, k)
            paint_text(cv, "WAAAH!", 0, 0, font="bangers", size=110, fills=[P_["cream"], (150, 230, 255)], ink_w=5, shadow=(6, 6), shadow_rgb=P_["blue"], seed=8501)
            cv.restore()
    if 11.88 <= t < 14.21:
        C = sets.Cam(cv, cam)
        zp = C.zoom(1.0)
        gx, gy = C.to_screen(GARY_X, GARY_EY)
        sweat_spray(cv, gx, gy, GARY_S * zp, t, seed=8600, n=6, k=sm(t, 11.9, 12.3))
        strain_marks(cv, gx, gy, 150 * GARY_S * zp, t, seed=8601, k=sm(t, 12.6, 13.0))
        if t > 12.0:
            paint_text(cv, "UM...", gx + 330 * GARY_S * zp, gy - 190 * GARY_S * zp, font="marker", size=74, fill=P_["cream"], ink_w=4, shadow=(5, 5), seed=8602,
                       reveal=cl((t - 12.0) / 0.4), streaks=False)
        if t > 13.17:
            paint_text(cv, "UM...", gx + 400 * GARY_S * zp, gy + 10 * GARY_S * zp, font="marker", size=92, fill=P_["cream"], ink_w=4, shadow=(5, 5), seed=8603,
                       reveal=cl((t - 13.17) / 0.4), streaks=False)
    vignette(cv, a=120)


# ===================================================================== T037 helpers
def tunnel_set(cv, T, cam, seed=8700):
    """The steep passage back down into the cave: the sunlit exit blazing top-right, darkness swallowing the left."""
    C = sets.Cam(cv, cam)
    with C.layer(0.5):
        w.field(cv, (18, 8, 36))
        rock_mass(cv, [(-400, -300), (2400, -300), (2400, 1100), (-400, 1100)], seed=seed, rgb=(34, 14, 66), ink=3)
        g = skia.Paint(AntiAlias=True)                                   # daylight pouring down the passage
        g.setShader(skia.GradientShader.MakeRadial(skia.Point(1880, 60), 980, [core.C(P_["white"]), core.C(P_["yellow"], 230), core.C(P_["orange"], 90),
                                                                                core.C(P_["orange"], 0)], [0.0, 0.18, 0.55, 1.0]))
        cv.drawRect(R(700, -300, 2500, 1100), g)
        sun_rays(cv, 1880, 40, 1700, T, n=14, a=60, ang0=150, span=60)
        rock_mass(cv, [(-400, -300), (1500, -300), (1650, -60), (1560, 120), (1300, 220), (900, 180), (400, 240), (-400, 200)], seed=seed + 1, rgb=CV_ROCK,
                  rim=P_["orange"], rim_side=1)
        _stalactites(cv, T, seed + 2, y0=150, x0=-200, x1=1400, n=9, lights=False)
    with C.layer(0.8):
        path = [(1000, 1000), (1300, 860), (1560, 640), (1760, 420), (1940, 260), (2300, 200), (2300, 1000)]
        blob(cv, path, mix(CV_ROCK2, P_["orange"], 0.35), w=5, seed=seed + 3, boil=1.0, n=4,
             shade=lambda c: [blob(c, ell(1350 + k * 90, 880 - k * 74, 34, 13, n=8, rot=-38), mix(CV_ROCK2, P_["yellow"], 0.4), w=3, seed=seed + 10 + k, boil=0.5)
                              for k in range(9)])
        rock_mass(cv, [(-400, 820), (600, 800), (1200, 840), (2400, 820), (2400, 1300), (-400, 1300)], seed=seed + 4, rgb=CV_ROCK2, rim=P_["orange"], ink=4.5)
        for k, (mx_, my_) in enumerate(((200, 900), (640, 930), (1500, 950))):
            glow_mushroom(cv, mx_, my_, 0.9, T, seed=seed + 20 + k)
        crystal(cv, 90, 860, 0.9, T, seed=seed + 30)
    with C.layer(1.0):
        sx = 1010                                                         # the stalagmite he walks into
        blob(cv, [(sx - 70, 900), (sx - 40, 700), (sx - 10, 560), (sx + 14, 548), (sx + 40, 690), (sx + 76, 900)], CV_ROCK2, w=5.5, seed=seed + 40, boil=0.9, n=4,
             shade=lambda c: c.drawPath(poly_path([(sx + 10, 540), (sx + 90, 540), (sx + 90, 910), (sx + 20, 910)]), paint(mix(CV_ROCK2, INK, 0.3))))


def afterimage(cv, x, y, r, T, a=1.0, seed=0):
    """A cartoon 'seeing spots' afterimage of the ringed sun: a soft magenta disc in an acid-green ring, drifting."""
    smoke(cv, x, y, r * 1.25, P_["acid"], int(120 * a))
    smoke(cv, x, y, r * 0.95, (40, 10, 50), int(160 * a))
    smoke(cv, x, y, r * 0.7, P_["magenta"], int(200 * a))
    cv.save(); cv.translate(x, y); cv.rotate(-16); cv.scale(1.0, 0.3)
    cv.drawCircle(0, 0, r * 1.75, paint(P_["teal"], int(150 * a), stroke=r * 0.35))
    cv.restore()


def spots(cv, x, y, s, T, k=1.0, seed=0):
    """Little dancing coloured spots around a dazzled head."""
    cols = [P_["acid"], P_["magenta"], P_["teal"], P_["yellow"], P_["hotpink"]]
    for j in range(7):
        a = T * (1.4 + 0.3 * j) + j * 0.9
        rr = (190 + 40 * math.sin(T * 2 + j)) * s
        px, py = x + rr * math.cos(a) * 1.2, y - 40 * s + rr * math.sin(a) * 0.55
        sz = (14 + 8 * (j % 3)) * s
        blob(cv, ell(px, py, sz, sz, n=8), cols[j % len(cols)], w=3.0, seed=seed + j, boil=0.8, a=int(230 * k))
        if j % 2 == 0:
            sparkle(cv, px + sz * 1.6, py - sz, sz * 0.8, P_["cream"], seed=seed + 20 + j, a=int(255 * k))


def eyelid_mask(cv, open_, T, seed=8800, rgb=None):
    """POV squint: two dark violet lids leaving an eye-shaped opening (open_ 0 = shut .. 1 = wide)."""
    rgb = rgb or (30, 10, 46)
    hgt = 30 + 560 * cl(open_)
    top = [(-60, -60), (W + 60, -60), (W + 60, 540 - hgt * 0.35)] + [(W - k * W / 8, 540 - hgt * math.sin(math.pi * (1 - k / 8)) * 0.95 - 4) for k in range(1, 8)] + \
          [(-60, 540 - hgt * 0.35)]
    bot = [(-60, H + 60), (W + 60, H + 60), (W + 60, 540 + hgt * 0.35)] + [(W - k * W / 8, 540 + hgt * math.sin(math.pi * (1 - k / 8)) * 0.85 + 4) for k in range(1, 8)] + \
          [(-60, 540 + hgt * 0.35)]
    for j, P in enumerate((top, bot)):
        blob(cv, P, rgb, w=8, seed=seed + j, boil=1.2, n=4)
        edge = np.array(P[3:-1])
        brush(cv, cr_open(jit(edge, 1.0, seed + 30 + j), 6), 10, P_["magenta"], seed=seed + 32 + j, taper=(0.3, 0.3), a=110)
    for k in range(9):                                                    # lashes on the upper lid
        u = (k + 1) / 10
        x = W * u
        y = 540 - hgt * math.sin(math.pi * u) * 0.95 - 4
        line(cv, [(x, y), (x + (u - 0.5) * 60, y - 34 - 10 * math.sin(k))], 6, INK, seed=seed + 10 + k, boil=0.8, n=2, taper=(0.1, 0.6))


def pov_dark(cv, t, T, seed=8900):
    """Gary's eyes after the sunlight: the cave is near-black -- the firelit board a faint smear, bulbs specks, the host's
    screen a dim green ghost -- and the sun's afterimage floats over everything. Seen through a squint."""
    w.field(cv, (10, 5, 18))
    drift = 30 * math.sin(t * 0.8)
    smoke(cv, 960 + drift, 360, 420, (90, 40, 30), 120)                 # the board: a dim orange smear
    smoke(cv, 960 + drift, 380, 260, (130, 60, 36), 110)
    smoke(cv, 900 + drift, 400, 90, (40, 14, 30), 120)                   # a smudge that might be a bunny
    smoke(cv, 880 + drift, 300, 40, (40, 14, 30), 120)
    smoke(cv, 930 + drift, 296, 40, (40, 14, 30), 120)
    smoke(cv, 330 + drift * 0.6, 520, 120, (30, 70, 70), 120)           # the host's screen glow
    for k in range(18):                                                   # bulbs: faint specks
        a = k / 18 * 2 * math.pi
        bx, by = 960 + drift + 520 * math.cos(a), 380 + 260 * math.sin(a)
        dots(cv, [(bx, by)], 4 + 2 * math.sin(t * 6 + k), (120, 100, 70), a=90)
    for k in range(5):                                                    # dark shapes of heads
        smoke(cv, 300 + k * 330, 980, 150, (4, 2, 8), 200)
    for j, (ax, ay, ar, ph) in enumerate(((760, 470, 120, 0.0), (1260, 560, 60, 1.7), (560, 640, 36, 3.1))):
        afterimage(cv, ax + 180 * math.sin(t * 0.5 + ph) - t * 40, ay + 60 * math.cos(t * 0.7 + ph), ar * (1 + 0.08 * math.sin(t * 3 + j)), T,
                   a=0.85 - 0.12 * j, seed=seed + j)
    bl = 1.0
    for tb in (0.85, 1.9):                                                # blinks
        if tb <= t < tb + 0.18:
            bl = abs((t - tb) / 0.09 - 1.0)
    eyelid_mask(cv, (0.42 + 0.06 * math.sin(t * 2.3)) * bl, T, seed=seed + 10)


def outside_bubble(cv, x, y, rx, ry, T, t, k, hi=0.0, sun_zoom=0.0, seed=9000, tail_to=None):
    """Thought bubble showing the world up there: a dawn sky, green hills, flowers, trees -- and the ringed sun-planet,
    who says hi."""
    if k <= 0.01:
        return
    sc = pop(k, 0.0, 1.0)

    def content(c):
        g = skia.Paint(AntiAlias=True)
        g.setShader(skia.GradientShader.MakeLinear([skia.Point(0, -ry), skia.Point(0, ry)], [core.C(P_["hotpink"]), core.C(P_["peach"]), core.C(P_["yellow"])],
                                                   [0.0, 0.5, 1.0]))
        c.drawRect(R(-rx * 1.3, -ry * 1.3, rx * 1.3, ry * 1.3), g)
        zr = 1.0 + 0.75 * sun_zoom
        px, py, pr = lerp(rx * 0.32, rx * 0.22, sun_zoom), lerp(-ry * 0.32, -ry * 0.12, sun_zoom), 70 * zr
        w.sunburst(c, px, py, rx * 2.2, 20, [mix(P_["yellow"], P_["white"], 0.4), P_["peach"]], rot_deg=T * 12, seed=seed)
        w.planet(c, px, py, pr, P_["orange"], bands=[(-0.55, 0.22, P_["red"]), (-0.1, 0.18, P_["yellow"]), (0.32, 0.24, P_["magenta"])],
                 ring=dict(rx=1.75, ry=0.33, rgb=P_["teal"], rgb2=P_["cream"], tilt=-16),
                 face=dict(look=(-0.5, 0.3), smile=0.45 + 0.4 * hi, lids=0.45 if hi < 0.5 else 0.3, lid_rgb=P_["orange"]), seed=seed + 1)
        if sun_zoom < 0.95:
            a_ = 1.0 - sun_zoom
            for j, col in enumerate((P_["acid"], P_["acid_dk"])):
                pts = [(-rx * 1.3, ry * (0.25 + 0.18 * j))] + [(-rx * 1.3 + q * rx * 0.26, ry * (0.25 + 0.18 * j) - 40 * math.sin(q * 0.9 + j * 2)) for q in range(12)] + \
                      [(rx * 1.4, ry * 1.4), (-rx * 1.3, ry * 1.4)]
                c.save(); c.translate(0, 200 * sun_zoom)
                blob(c, pts, col, w=4, seed=seed + 10 + j, boil=0.8, n=4)
                c.restore()
            for j in range(4):                                            # lollipop trees
                tx, ty = -rx * 0.7 + j * rx * 0.42, ry * 0.42 + 200 * sun_zoom + 10 * (j % 2)
                line(c, [(tx, ty), (tx, ty - 60)], 9, (120, 70, 40), seed=seed + 20 + j, boil=0.6, n=2, taper=(0, 0))
                blob(c, ell(tx, ty - 80, 34, 30, n=9), [P_["acid"], P_["teal"]][j % 2], w=3.5, seed=seed + 24 + j, boil=0.8)
            for j in range(9):                                            # flowers
                fx, fy = -rx * 0.9 + j * rx * 0.22, ry * 0.75 + 200 * sun_zoom + 12 * math.sin(j * 2)
                for q in range(5):
                    a = q * 2 * math.pi / 5 + T
                    dots(c, [(fx + 9 * math.cos(a), fy + 9 * math.sin(a))], 6, [P_["magenta"], P_["white"], P_["orange"]][j % 3])
                dots(c, [(fx, fy)], 5, P_["yellow"])
        if hi > 0.05:                                                     # "HEY, GARY."
            hk = pop(hi, 0.0, 1.0)
            bx_, by_ = -rx * 0.42, ry * 0.3
            blob(c, [(bx_ + 70 * hk, by_ - 30 * hk), (px - pr * 0.8, py + pr * 0.4), (bx_ + 100 * hk, by_ - 6 * hk)], P_["white"], w=4, seed=seed + 41, boil=0.5, n=2)
            blob(c, ell(bx_, by_, 124 * hk, 54 * hk, n=10), P_["white"], w=4.5, seed=seed + 40, boil=0.8)
            paint_text(c, "HEY, GARY.", bx_, by_ + 14 * hk, font="marker", size=40 * hk + 1, fill=INK, ink_w=0, shadow=None, seed=seed + 42, streaks=False)

    cv.save(); cv.translate(x, y); cv.scale(sc, sc)
    old = core.INKMUL; core.INKMUL = old / max(0.3, sc) ** 0.5
    pts = []
    n = 16
    for j in range(n):
        ang = j / n * 2 * math.pi
        bump = 1.0 + 0.09 * math.sin(ang * 7 + seed)
        pts.append((rx * bump * math.cos(ang), ry * bump * math.sin(ang)))
    if tail_to is not None:
        tx_, ty_ = (tail_to[0] - x) / max(0.3, sc), (tail_to[1] - y) / max(0.3, sc)
    else:
        tx_, ty_ = 0.0, ry * 1.9
    dl = math.hypot(tx_, ty_) + 1e-6
    ux_, uy_ = tx_ / dl, ty_ / dl
    edge = 1.0 / math.sqrt((ux_ / rx) ** 2 + (uy_ / ry) ** 2)
    for j, (f, r) in enumerate(((0.18, 26), (0.45, 18), (0.72, 11))):
        d_ = edge + (dl - edge) * f
        blob(cv, ell(ux_ * d_, uy_ * d_, r, r * 0.82, n=8), P_["cream"], w=4.5, seed=seed + 50 + j, boil=0.8)
    blob(cv, pts, P_["cream"], w=6.5, seed=seed + 60, boil=1.0, n=6)
    inner = [(px_ * 0.9, py_ * 0.88) for px_, py_ in pts]
    cv.save(); cv.clipPath(poly_path(cr_closed(inner, 6)), doAntiAlias=True)
    content(cv)
    cv.restore()
    brush(cv, cr_closed(jit(inner, 1.0, seed + 61), 6), 4.5, closed=True, seed=seed + 62)
    core.INKMUL = old
    cv.restore()


def ha_letters(cv, t, T, k=1.0, seed=9100, n=12, box=(80, 120, 1840, 860)):
    """'HA!' / 'HA HA!' popping up all over and floating away."""
    if k <= 0.01:
        return
    x0, y0, x1, y1 = box
    words = ["HA!", "HA HA!", "HA!", "HAHA!", "HA!", "HEE!"]
    cols = [P_["yellow"], P_["cream"], P_["acid"], P_["hotpink"], P_["orange"], P_["teal"]]
    for j in range(n):
        life = 0.9
        ph = (t / life + hsh(seed + j)) % 1.0
        cyc = math.floor(t / life + hsh(seed + j))
        x = x0 + (x1 - x0) * float(hsh(seed + j * 3.1 + cyc * 7.3))
        y = y0 + (y1 - y0) * float(hsh(seed + j * 5.7 + cyc * 3.9)) - ph * 80
        sz = (60 + 50 * float(hsh(seed + j * 2.3 + cyc))) * pop(ph, 0.0, 0.25)
        a = int(255 * k * min(1.0, (1 - ph) * 3))
        if sz < 4 or a < 10:
            continue
        cv.save(); cv.translate(x, y); cv.rotate((float(hsh(seed + j + cyc)) - 0.5) * 30)
        paint_text(cv, words[j % len(words)], 0, 0, font="shrik", size=sz, fill=cols[j % len(cols)], ink_w=4, shadow=(4, 4), shadow_rgb=P_["maroon"],
                   seed=seed + j, streaks=False, a=a)
        cv.restore()


def crowd_laugh(cv, t, T, seed=9200):
    """Reverse angle: the whole chained audience facing us (they face the stage -- and Gary), howling with laughter,
    the fire blazing behind them."""
    cam = dict(x=0, y=0, z=1.0 + 0.03 * t)
    C = sets.Cam(cv, cam)
    with C.layer(0.5):
        w.field(cv, CV_ROCK_DK)
        rock_mass(cv, [(-400, -300), (2400, -300), (2400, 1100), (-400, 1100)], seed=seed, rgb=(40, 16, 78), ink=3)
        _stalactites(cv, T, seed + 1, y0=-30, lights=False)
        firelight(cv, 960, 660, 1100, T, a=150, seed=seed + 2)
        blob(cv, rect_pts([(300, 560), (1620, 560), (1640, 700), (280, 700)], 3), mix(CV_ROCK2, P_["maroon"], 0.3), w=5, seed=seed + 3, boil=0.8, n=3)
        cave_fire(cv, 960, 600, 0.75, T, seed=seed + 4)
    rows = [(0.8, 690, 7, 0.6), (1.1, 850, 6, 0.75), (1.45, 1062, 4, 0.9)]
    for ri, (s_, y_, n_, lp) in enumerate(rows):
        with C.layer(lp + 0.1 * ri):
            xs = [160 + (1600) * (k + 0.5 * (ri % 2)) / (n_ - (0.5 if ri % 2 else 1)) for k in range(n_)]
            heads = []
            for k, x_ in enumerate(xs):
                cx, cy, r = contestant(cv, x_, y_, s_, T + k * 0.13, seed=seed + 100 + ri * 20 + k, look=(0, 0), mood="laugh", k=1.0, rim=P_["orange"])
                heads.append((cx, cy, r))
            for k in range(len(heads) - 1):
                (ax, ay, ar), (bx, by, br) = heads[k], heads[k + 1]
                chain(cv, (ax + ar * 0.85, ay + ar * 0.92), (bx - br * 0.85, by + br * 0.92), seed=seed + 300 + ri * 20 + k, link=16 * s_ + 4, sag=14 * s_, w=2.6 * s_ + 0.8)
    ha_letters(cv, t, T, seed=seed + 500, n=9, box=(120, 150, 1800, 560))
    vignette(cv, a=150)


# ===================================================================== T037 'I can't see the bunny!'
def T037_cant_see(cv, t, T, A):
    # beats (shot time): Z22 'Well...' 0.08 | 'after all that sunlight' 1.08-2.38 | 'his eyes can't see in the dark anymore' 3.0-4.96
    #   | 'So when he sits back down...' 5.58-7.04 | 'he's terrible at the shadow game' 7.71-9.96 | RETURN sting 10.0-13.49
    #   | S05 'Gary!' 13.57 'Welcome back!' 14.0-15.2 'What comes after the bunny?' 15.62-16.70
    #   | G07 'I can't see the bunny!' 17.36-18.82 'Guys,' 19.24 'the bunny isn't real!' 20.03-21.24 'There's a whole world up there!' 21.74-23.20
    #   'There's a sun!' 23.61-24.53 'It said hi to me!' 24.86-26.07 | WRONG! 26.25 | LAUGH 26.73-28.73
    if t < 3.0:
        _t037_tunnel(cv, t, T, A)
    elif t < 5.58:
        pov_dark(cv, t - 3.0, T)
    elif t < 10.0:
        _t037_fumble(cv, t, T, A)
    elif t < 13.49:
        sting(cv, t - 10.0, T, sad=True)
    elif t < 17.1:
        _t037_host(cv, t, T, A)
    elif t < 26.73:
        _t037_plea(cv, t, T, A)
    elif t < 27.75:
        crowd_laugh(cv, t - 26.73, T)
    else:
        _t037_deflated(cv, t, T, A)


def _t037_tunnel(cv, t, T, A):
    cam = dict(x=150 - 60 * t, y=-20, z=1.12 + 0.02 * t)
    tunnel_set(cv, T, cam)
    C = sets.Cam(cv, cam)
    bump = 2.45
    gx = 1750 - 250 * min(t, bump) + (30 * sm(t, bump, bump + 0.15) if t > bump else 0)
    gs = 0.74
    gy = 476 - 6 * abs(math.sin(t * 5.6))
    grope = math.sin(T * 6)
    with C.layer(1.0):
        k_b = imp(t, bump, 0.4)
        gary2(cv, gx, gy, gs, T, loud=0.0, lid=0.5 + 0.4 * k_b, squint=1.0, pupil=0.26, look=(-0.3, 0.1), mouth="wobble" if t < bump else "o",
              armL=(-250 + 20 * grope, 10 - 20 * grope, 180, "spread"), armR=(240 - 20 * grope, 20 + 20 * grope, 0, "spread"), collar=True, chain_to=None,
              legs=t * 1.9 if t < bump else bump * 1.9, tears_pool=0.5)
        if t > bump:
            k = imp(t, bump, 0.35)
            hx = gx - 250 * gs
            for q in range(5):
                a = q * 2 * math.pi / 5 + t * 6
                sparkle(cv, hx + 60 * math.cos(a), gy - 40 + 40 * math.sin(a), 20 * k + 6, P_["yellow"], seed=8710 + q, a=int(255 * min(1.0, k * 2)))
            if t < bump + 0.5:
                kk = pop(t, bump, 0.2)
                paint_text(cv, "BONK!", hx - 60, gy - 150, font="bangers", size=96 * kk + 1, fill=P_["yellow"], ink_w=5, shadow=(6, 6), shadow_rgb=P_["red"],
                           seed=8720)
        spots(cv, gx, gy, gs, T, k=1.0, seed=8730)
    ex, ey = C.to_screen(1880, 60, 0.5)
    sx, sy = C.to_screen(gx, gy)
    lights = [(ex, ey, 1500, 1.15, (255, 232, 196)), (sx + 60, sy + 40, 560, 0.62, (255, 200, 160))]
    for k, (mx_, my_, col) in enumerate(((200, 860, P_["acid"]), (640, 890, P_["teal"]), (1500, 910, P_["hotpink"]), (90, 820, P_["teal"]))):
        lx, ly = C.to_screen(mx_, my_, 0.8)
        lights.append((lx, ly, 230, 0.8, col))
    light_mask(cv, lights, ambient=26, T=T)
    vignette(cv, a=120)


def _t037_cam(t):
    """Stage cameras of T037 (the host is either wholly inside title-safe or wholly out of frame)."""
    if t < 7.71:
        return dict(x=lerp(560, 430, sm(t, 5.58, 7.4)), y=30, z=1.5)
    if t < 10.0:
        return dict(x=lerp(380, 400, sm(t, 7.71, 10.0)), y=-60, z=1.3 + 0.026 * (t - 7.71))
    if t < 17.1:
        return dict(x=-305 - 8 * (t - 13.49), y=120, z=1.6 + 0.02 * (t - 13.49))
    return None


def _t037_fumble(cv, t, T, A):
    seat = 6.92
    st = dict(mode="chase", sign=3, cont=[{}, {}], aud=True)
    if t < 7.71:                                                          # fumbling back to the podium
        cam = _t037_cam(t)
        u = sm(t, 5.6, 6.7)
        gx = lerp(2120, GARY_X, u)
        walking = t < 6.7
        sit = sm(t, 6.7, seat)
        gy = lerp(GARY_EY - 50, GARY_EY, sit) + (10 * math.sin((t - seat) * 20) * math.exp(-(t - seat) * 6) if t > seat else 0)
        LK = [(5.58, lambda TT: (-240 + 20 * math.sin(TT * 6), -20 * math.sin(TT * 6), 180, "spread"), 0), (6.7, (-90, 130, 100, "flat"), 0.28)]
        RK = [(5.58, lambda TT: (230 - 20 * math.sin(TT * 6), 10 + 20 * math.sin(TT * 6), 0, "spread"), 0), (6.7, (90, 130, 80, "flat"), 0.28)]
        g = dict(x=gx, y=gy, lid=0.5, squint=1.0, pupil=0.26, look=(0.3 if t < 6.4 else -0.2, 0.1), mouth="wobble", tears_pool=0.4,
                 armL=arm_track(LK, t, T, -1), armR=arm_track(RK, t, T, 1))
        if t < seat:
            g["chain_to"] = None
        st["gary"] = g
        st["cont"] = [dict(mood="stare", look=(-0.9, 0.0) if gx < 1640 else (0.9, 0.0)), dict(mood="stare", look=(-0.9, 0.0) if gx < 1845 else (0.9, -0.2))]

        def fx(c, x, y, s):
            spots(c, x, y, s, T, k=0.8, seed=8740)
            if t > seat:
                k = imp(t, seat, 0.3)
                rx, ry = GARY_X - 171 * POD_S, POD_Y - 270 * POD_S + 30 * POD_S
                for q in range(4):
                    sparkle(c, rx + 40 * math.cos(q * 1.57 + t * 5), ry + 40 * math.sin(q * 1.57 + t * 5), 16 * k + 4, P_["cream"], seed=8750 + q, a=int(255 * min(1, k * 2)))
                if t < seat + 0.55:
                    paint_text(c, "CLINK!", rx - 70, ry - 40, font="bangers", size=60 * pop(t, seat, 0.2) + 1, fill=(200, 210, 230), ink_w=4, shadow=(4, 4), seed=8760)
        st["gary_fx"] = fx
        st["board"] = lambda c: shadow_shape(c, "hand_bunny", 960 + 30 * math.sin(T * 0.8), 470, 1.2, T, seed=7106, a=150)
    else:                                                                 # ...he's terrible at the shadow game
        cam = _t037_cam(t)
        u = cl((t - 7.71) / 2.2)
        guess = 8.85
        RK = [(7.71, lambda TT: (240, -40 + 20 * math.sin(TT * 4), -10, "point"), 0),        # pointing the wrong way
              (guess - 0.28, (178, -70, -80, "fist"), 0.28), (guess, (140, 120, 80, "flat"), 0.08)]
        g = dict(lid=0.52, squint=1.0, pupil=0.24, look=(0.85, 0.35), mouth="wobble" if t < guess else "grin", tears_pool=0.4, tremble=2.5,
                 armL=(-95, 130, 100, "flat"), armR=arm_track(RK, t, T, 1))
        st["gary"] = g
        st["press"] = sm(t, guess + 0.04, guess + 0.1) * (1 - sm(t, guess + 0.5, guess + 0.7))
        st["buzz"] = imp(t, guess + 0.05, 0.5)
        st["cont"] = [dict(mood="stare", look=(-0.9, 0.0)), dict(mood="stare", look=(-0.9, 0.1))]

        def board(c):
            bx = lerp(1500, 420, u)
            by = 380 + 60 * math.sin(u * 7)
            c.save(); c.translate(bx, by); c.scale(1.0, 1.0 + 0.3 * math.sin(T * 14)); c.translate(-bx, -by)
            shadow_shape(c, "bird", bx, by, 1.3, T, seed=7130)
            c.restore()
            if t > guess + 0.35:                                          # a big red X on the board
                k = pop(t, guess + 0.35, 0.25)
                for side in (-1, 1):
                    line(c, [(960 - 160 * k, 410 - 150 * k * side), (960 + 160 * k, 410 + 150 * k * side)], 54, INK, seed=7131 + side, boil=1.2, n=2,
                         taper=(0.05, 0.05))
                    line(c, [(960 - 154 * k, 410 - 144 * k * side), (960 + 154 * k, 410 + 144 * k * side)], 36, P_["red"], seed=7131 + side, boil=1.2, n=2,
                         taper=(0.05, 0.05))
        st["board"] = board
        if t > guess + 0.35:
            st["mode"] = "red"
            st["pod_mode"] = "red"

        def fx(c, x, y, s):
            spots(c, x, y, s, T, k=0.6, seed=8740)
            if guess + 0.05 < t < guess + 0.8:
                bx_, by_ = GARY_X + 104 * POD_S, POD_Y - 270 * POD_S - 60 * POD_S
                zap(c, bx_, by_, 0.8, imp(t, guess + 0.05, 0.4), seed=8770)
        st["gary_fx"] = fx
    spots_ = [(GARY_X - 40, -60, GARY_X, 930, 28, 200, P_["white"], 55), (HOST_X + 80, -60, HOST_X, 1000, 30, 210, P_["yellow"], 45)]
    st["spots"] = spots_
    gameshow_scene(cv, t, T, A, cam, st)
    vignette(cv, a=140)


def _t037_host(cv, t, T, A):
    cam = _t037_cam(t)
    st = dict(mode="chase", sign=3, cont=[{}, {}])

    def board(c):
        if t > 15.75:
            bx, by = _bunny_hop(t, 15.75, 16.6, 420, 900, 480, hops=3, hh=80)
            shadow_shape(c, "bunny", bx, by, 1.45, T, seed=7101)
        else:
            shadow_shape(c, "hand_bunny", 960 + 30 * math.sin(T * 0.8), 470, 1.2, T, seed=7106, a=120)
    st["board"] = board
    st["spots"] = [(HOST_X + 80, -60, HOST_X, 1000, 30, 210, P_["yellow"], 55), (250 + 60 * math.sin(T), -60, 520, 980, 26, 170, P_["magenta"], 40)]
    st["gary"] = dict(lid=0.5, squint=1.0, pupil=0.26, look=(0.6, 0.3), mouth="wobble", armL=(-90, 130, 100, "flat"), armR=(90, 130, 80, "flat"))
    gameshow_scene(cv, t, T, A, cam, st)
    if 13.55 < t < 14.4:                                                   # 'Gary!' -- a sparkle burst from the host
        k = imp(t, 13.6, 0.4)
        burst_lines(cv, 450, 330, 200, 420, 12, k, P_["yellow"], 8, seed=9301)
    vignette(cv, a=120)


def _t037_plea(cv, t, T, A):
    W1, W2 = 18.88, 26.22                                                  # WRONG! buzzes
    keys = [(17.1, 330, -10, 1.72, 0.01), (17.2, 340, -10, 1.8, 1.5),
            (19.2, 520, 10, 1.5, 0.45),
            (21.7, 470, -120, 1.3, 0.6), (23.6, 520, -150, 1.4, 0.5), (26.15, 360, -10, 1.75, 0.15)]
    cam = lerp_cam(keys, t)
    dx, dy = jolt(t, [W1, W2], amp=18, seed=37)
    cam["x"] += dx; cam["y"] += dy
    st = dict(mode="chase", sign=3)
    red = (W1 <= t < W1 + 0.9) or t >= W2
    if red:
        st["mode"] = "red"; st["pod_mode"] = "red"

    def board(c):
        shadow_shape(c, "bunny", 900, 480 - 4 * abs(math.sin(T * 2)), 1.45, T, seed=7101)
    st["board"] = board
    # ---- Gary's performance (arm poses eased between beats)
    LK = [(17.1, lambda TT: (-240 + 30 * math.sin(TT * 9), -60 - 30 * math.sin(TT * 9), -150, "spread"), 0), (W1, "up", 0.14),
          (19.2, (-200, -30, -160, "point"), 0.26), (21.7, (-60, 120, 100, "flat"), 0.3), (23.6, "up", 0.22), (24.85, (-60, 120, 100, "flat"), 0.26),
          (W2, "hang", 0.16)]
    RK = [(17.1, lambda TT: (170 - 20 * math.sin(TT * 9), -150 + 25 * math.sin(TT * 9), -60, "spread"), 0), (W1, "up", 0.14),
          (19.2, (200, 20, -20, "spread"), 0.26), (21.7, lambda TT: (150, -300 + 10 * math.sin(TT * 7), -70, "point"), 0.3), (23.6, "up", 0.22),
          (24.85, "wave", 0.26), (W2, (90, 130, 80, "flat"), 0.16)]
    g = dict(lid=0.34, squint=1.0, pupil=0.26, mouth=None, tears_pool=0.5, tremble=2.0, armL=arm_track(LK, t, T, -1), armR=arm_track(RK, t, T, 1))
    if t < 18.85:                                                         # I can't see the bunny! -- waving at the wall
        g.update(look=(-0.9, -0.2))
    elif t < 19.2:                                                        # WRONG! -- flinch
        k = imp(t, W1, 0.3)
        g.update(y=GARY_EY + 14 * k, lid=0.2, squint=0.3, pupil=0.2, look=(0.0, 0.0), tremble=8)
    elif t < 21.7:                                                        # Guys, the bunny isn't real!
        g.update(look=(0.95, -0.1))
    elif t < 23.6:                                                        # There's a whole world up there!
        g.update(look=(0.5, -0.9), lid=0.3)
    elif t < 24.85:                                                       # There's a sun!
        g.update(look=(0.5, -0.9), lid=0.24)
    elif t < 26.2:                                                        # It said hi to me!
        g.update(look=(0.55, -0.85), lid=0.24)
    else:
        k = imp(t, W2, 0.3)
        g.update(y=GARY_EY + 14 * k, lid=0.2, squint=0.3, pupil=0.2, look=(0.0, 0.0), tremble=8, mouth="o")
    st["gary"] = g
    stare = "stare"
    if t > 24.9:
        stare = "gasp"
    st["cont"] = [dict(mood=stare, look=(-0.95, -0.1)), dict(mood=stare, look=(-0.95, 0.0))]
    st["spots"] = [(GARY_X - 40, -60, GARY_X, 930, 28, 200, P_["white"], 60)]

    def fx(c, x, y, s):
        if t < 23.6:
            sweat_spray(c, x, y, s, t, seed=9400, n=5, k=0.8)
    st["gary_fx"] = fx
    gameshow_scene(cv, t, T, A, cam, st)
    C = sets.Cam(cv, cam)
    zp = C.zoom(1.0)
    gx, gy = C.to_screen(GARY_X, GARY_EY)
    if 21.74 <= t < 26.2:                                                  # the world up there
        bk = cl((t - 21.85) / 0.4)
        bx, by = C.to_screen(GARY_X + 360, GARY_EY - 300)
        hx, hy = C.to_screen(GARY_X + 60, GARY_EY - 150 * GARY_S - 20)
        outside_bubble(cv, bx, by, 330 * zp / 1.3, 220 * zp / 1.3, T, t, bk, hi=cl((t - 24.95) / 0.35), sun_zoom=sm(t, 23.6, 24.2), seed=9500,
                       tail_to=(hx, hy))
    for tw in (W1, W2):
        if tw <= t < tw + 0.85:
            k = cl((t - tw) / 0.25) * (1 - sm(t, tw + 0.6, tw + 0.85))
            wrong_graphic(cv, 640 if tw == W2 else 560, 400 if tw == W2 else 370, k, T, seed=9600 + int(tw), s=0.8 if tw == W1 else 1.0)
    vignette(cv, a=120)


def _t037_deflated(cv, t, T, A):
    tt = t - 27.75
    cam = dict(x=390, y=10, z=1.85 + 0.06 * tt)
    st = dict(mode="chase", sign=3, laugh=1.0)
    sink = sm(t, 27.85, 28.6)
    st["gary"] = dict(y=GARY_EY + 34 * sink, lid=0.62, squint=0.0, pupil=0.3, look=(0.0, 0.55), mouth="frown", armL=None, armR=None, tears_pool=0.6, bob=0.3)
    st["cont"] = [dict(mood="laugh", k=1.0), dict(mood="laugh", k=1.0)]
    st["board"] = lambda c: shadow_shape(c, "bunny", 900, 480, 1.45, T, seed=7101)
    st["spots"] = [(GARY_X - 40, -60, GARY_X, 930, 28, 200, P_["white"], 45)]

    def fx(c, x, y, s):
        ph = (t * 1.2) % 1.0
        drop(c, x - 120 * s, y + 20 * s + 80 * s * ph, 9 * s + 2, (140, 225, 255), a=int(255 * (1 - ph)))
    st["gary_fx"] = fx
    gameshow_scene(cv, t, T, A, cam, st)
    C = sets.Cam(cv, cam)
    gx, gy = C.to_screen(GARY_X, GARY_EY + 34 * sink)
    light_mask(cv, [(gx, gy, 420, 1.0, (255, 245, 225))], ambient=255 - 140 * sink, T=T)
    ha_letters(cv, t, T, seed=9700, n=7, box=(1330, 170, 1840, 560))
    vignette(cv, a=150)
