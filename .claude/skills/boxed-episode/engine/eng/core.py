"""BOXED core drawing kit: the palette, the per-drawing 'boil', Catmull-Rom shapes, variable-width brush ink,
off-register flat cel fills, printed stipple, sparkles, and the paper + grain finish.

Everything is drawn into a 1920x1080 skia raster surface. Animation is on twos: `set_drawing(d)` sets the drawing
index D (12 drawings/s) and every jitter / boil / twinkle is a pure function of (seed, D), so any drawing can be
re-rendered identically by any worker.
"""
import math
import numpy as np
import skia

W, H = 1920, 1080

PAL = dict(
    ink=(20, 10, 26), white=(255, 252, 240), cream=(255, 238, 196), cream_sh=(246, 196, 132),
    magenta=(255, 46, 166), hotpink=(255, 120, 196), violet=(126, 56, 255), vdark=(78, 28, 170),
    blue=(34, 96, 255), deepblue=(22, 30, 120), night=(26, 10, 58), void=(14, 6, 34),
    orange=(255, 120, 24), red=(214, 22, 48), maroon=(110, 8, 38), teal=(28, 226, 200),
    tealdk=(0, 150, 150), acid=(170, 255, 0), acid_dk=(90, 180, 0), yellow=(255, 214, 0),
    gold=(255, 170, 30), lilac=(200, 150, 255), mint=(150, 255, 210), peach=(255, 176, 120),
    mouth=(92, 8, 40), tongue=(255, 96, 140),
)
INK = PAL["ink"]

# ---------------------------------------------------------------- drawing clock (boil)
D = 0                      # current drawing index (frame // 2)
INKMUL = 1.0               # pen-weight compensation for camera zoom / character scale


def set_drawing(d):
    global D
    D = int(d)


def hsh(x):
    x = np.sin(np.asarray(x, dtype=np.float64) * 12.9898 + 4.1414) * 43758.5453
    return x - np.floor(x)


def jit(P, amp, seed):
    """Fresh per-drawing jitter of control points (the boil)."""
    P = np.asarray(P, dtype=np.float64)
    if amp <= 0:
        return P
    n = P.shape[0]
    k = np.arange(n * 2, dtype=np.float64)
    r = hsh(k * 1.6180339 + seed * 7.1309 + D * 3.7731 + 0.5) - 0.5
    return P + r.reshape(n, 2) * (2.0 * amp)


def snoise(u, seed, k=3):
    """Smooth 1-D noise in about [-1, 1] along a normalised arc length u (re-seeded every drawing)."""
    u = np.asarray(u, dtype=np.float64)
    out = np.zeros_like(u)
    norm = 0.0
    for i in range(k):
        f = 1.3 + 2.6 * float(hsh(seed * 3.137 + i * 7.71))
        ph = 6.2831853 * float(hsh(seed * 5.311 + i * 1.913 + D * 0.377))
        a = 1.0 / (i + 1)
        out += a * np.sin(u * f * 6.2831853 + ph)
        norm += a
    return out / norm


def C(rgb, a=255):
    return skia.ColorSetARGB(int(max(0, min(255, a))), int(rgb[0]), int(rgb[1]), int(rgb[2]))


_P = {}


def paint(rgb, a=255, stroke=None, blend=None):
    key = (tuple(int(v) for v in rgb), int(a), None if stroke is None else round(stroke * 2) / 2, blend)
    p = _P.get(key)
    if p is None:
        p = skia.Paint(AntiAlias=True, Color=C(rgb, a))
        if stroke is not None:
            p.setStyle(skia.Paint.kStroke_Style)
            p.setStrokeWidth(max(0.5, key[2]))
            p.setStrokeCap(skia.Paint.kRound_Cap)
            p.setStrokeJoin(skia.Paint.kRound_Join)
        if blend is not None:
            p.setBlendMode(blend)
        _P[key] = p
    return p


def mix(a, b, t):
    t = float(t)
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def _cr(P0, P1, P2, P3, n, last=False):
    t = np.linspace(0.0, 1.0, n, endpoint=last)[:, None]
    t2, t3 = t * t, t * t * t
    return 0.5 * ((2 * P1) + (-P0 + P2) * t + (2 * P0 - 5 * P1 + 4 * P2 - P3) * t2 + (-P0 + 3 * P1 - 3 * P2 + P3) * t3)


def cr_closed(P, n=10):
    """Closed Catmull-Rom loop through the control points, n samples per segment."""
    P = np.asarray(P, dtype=np.float64)
    m = len(P)
    if m < 3:
        return P
    i = np.arange(m)
    P0, P1, P2, P3 = P[(i - 1) % m], P[i], P[(i + 1) % m], P[(i + 2) % m]
    t = np.linspace(0.0, 1.0, n, endpoint=False)[None, :, None]
    t2, t3 = t * t, t * t * t
    P0, P1, P2, P3 = (A[:, None, :] for A in (P0, P1, P2, P3))
    out = 0.5 * ((2 * P1) + (-P0 + P2) * t + (2 * P0 - 5 * P1 + 4 * P2 - P3) * t2 + (-P0 + 3 * P1 - 3 * P2 + P3) * t3)
    return out.reshape(-1, 2)


def cr_open(P, n=10):
    """Open Catmull-Rom curve through the control points (ends duplicated), n samples per segment."""
    P = np.asarray(P, dtype=np.float64)
    m = len(P)
    if m < 2:
        return P
    if m == 2:
        t = np.linspace(0, 1, n + 1)[:, None]
        return P[0] * (1 - t) + P[1] * t
    Q = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    i = np.arange(m - 1)
    P0, P1, P2, P3 = Q[i], Q[i + 1], Q[i + 2], Q[i + 3]
    t = np.linspace(0.0, 1.0, n, endpoint=False)[None, :, None]
    t2, t3 = t * t, t * t * t
    P0, P1, P2, P3 = (A[:, None, :] for A in (P0, P1, P2, P3))
    out = 0.5 * ((2 * P1) + (-P0 + P2) * t + (2 * P0 - 5 * P1 + 4 * P2 - P3) * t2 + (-P0 + 3 * P1 - 3 * P2 + P3) * t3)
    return np.vstack([out.reshape(-1, 2), P[-1:]])


def ell(cx, cy, rx, ry, n=10, rot=0.0, phase=0.0):
    a = np.linspace(0, 2 * math.pi, n, endpoint=False) + phase
    x, y = rx * np.cos(a), ry * np.sin(a)
    if rot:
        r = math.radians(rot)
        c, s = math.cos(r), math.sin(r)
        x, y = x * c - y * s, x * s + y * c
    return np.stack([cx + x, cy + y], 1)


def rect_pts(pts, per_edge=3):
    """Densify a polygon's edges (per_edge points per edge) so a Catmull-Rom loop through it keeps straight sides."""
    P = np.asarray(pts, dtype=np.float64)
    out = []
    m = len(P)
    for i in range(m):
        a, b = P[i], P[(i + 1) % m]
        for k in range(per_edge):
            out.append(a + (b - a) * (k / per_edge))
    return np.array(out)


def rot(P, deg, cx=0.0, cy=0.0):
    P = np.asarray(P, dtype=np.float64)
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    X, Y = P[:, 0] - cx, P[:, 1] - cy
    return np.stack([cx + X * c - Y * s, cy + X * s + Y * c], 1)


def poly_path(Pts, closed=True, evenodd=False):
    p = skia.Path()
    Pts = np.asarray(Pts, dtype=np.float64)
    p.addPoly([skia.Point(float(x), float(y)) for x, y in Pts], closed)
    if evenodd:
        p.setFillType(skia.PathFillType.kEvenOdd)
    return p


def open_path(Pts):
    p = skia.Path()
    Pts = np.asarray(Pts, dtype=np.float64)
    p.moveTo(float(Pts[0][0]), float(Pts[0][1]))
    for x, y in Pts[1:]:
        p.lineTo(float(x), float(y))
    return p


def _arclen(Cp, closed):
    d = np.hypot(*np.diff(Cp, axis=0).T)
    if closed:
        d = np.append(d, math.hypot(*(Cp[0] - Cp[-1])))
        u = np.concatenate([[0.0], np.cumsum(d)[:-1]])
    else:
        u = np.concatenate([[0.0], np.cumsum(d)])
    tot = (d.sum() if closed else u[-1]) or 1.0
    return u / tot


def _normals(Cp, closed):
    T = (np.roll(Cp, -1, 0) - np.roll(Cp, 1, 0)) if closed else np.gradient(Cp, axis=0)
    n = np.hypot(T[:, 0], T[:, 1]) + 1e-9
    T = T / n[:, None]
    return np.stack([-T[:, 1], T[:, 0]], 1)


# ---------------------------------------------------------------- ink
def brush(cv, Cp, w, rgb=INK, taper=(0.2, 0.2), var=0.3, seed=0, closed=False, a=255, minw=0.35):
    """Variable-width brush stroke along a dense centerline (pointed, pressure-varied ends)."""
    Cp = np.asarray(Cp, dtype=np.float64)
    if len(Cp) < 2:
        return
    u = _arclen(Cp, closed)
    prof = w * INKMUL * (1 + var * snoise(u, seed))
    if not closed:
        t0, t1 = max(taper[0], 1e-3), max(taper[1], 1e-3)
        prof = prof * np.clip(u / t0, minw, 1) ** 0.6 * np.clip((1 - u) / t1, minw, 1) ** 0.6
    N = _normals(Cp, closed)
    Lp = Cp + N * (prof[:, None] / 2)
    Rp = Cp - N * (prof[:, None] / 2)
    if closed:
        p = poly_path(Lp)
        p.addPoly([(float(x), float(y)) for x, y in Rp[::-1]], True)
        p.setFillType(skia.PathFillType.kEvenOdd)
    else:
        p = poly_path(np.vstack([Lp, Rp[::-1]]))
    cv.drawPath(p, paint(rgb, a))


def line(cv, ctrl, w, rgb=INK, seed=0, boil=1.2, n=10, taper=(0.2, 0.2), var=0.3, a=255):
    brush(cv, cr_open(jit(ctrl, boil, seed), n), w, rgb, taper, var, seed, False, a)


def blob(cv, ctrl, fill, w=5.0, ink=INK, seed=0, boil=1.4, n=10, misreg=(2.2, 1.6), shade=None,
         inkvar=0.3, a=255):
    """Closed cel shape: off-register flat fill (+ optional clipped shading) under a brush outline."""
    Pts = cr_closed(jit(ctrl, boil, seed), n)
    fp = None
    if fill is not None:
        Pf = cr_closed(jit(ctrl, boil * 0.7, seed + 917), n) + np.asarray(misreg)
        fp = poly_path(Pf)
        cv.drawPath(fp, paint(fill, a))
        if shade is not None:
            cv.save()
            cv.clipPath(fp, doAntiAlias=True)
            shade(cv)
            cv.restore()
    if w > 0:
        brush(cv, Pts, w, ink, var=inkvar, seed=seed + 3, closed=True, a=a)
    return Pts


def tube(cv, ctrl, width, rgb, w=5.0, ink=INK, seed=0, boil=1.2, n=10, misreg=(1.8, 1.2)):
    """Rubber-hose limb: ink stroke with a narrower, slightly off-register colour stroke on top."""
    Pts = cr_open(jit(ctrl, boil, seed), n)
    p = open_path(Pts)
    cv.drawPath(p, paint(ink, stroke=width + 2 * w * INKMUL))
    cv.save()
    cv.translate(*misreg)
    cv.drawPath(p, paint(rgb, stroke=width))
    cv.restore()
    return Pts


def dots(cv, pts, r, rgb, a=255):
    if len(pts) == 0:
        return
    p = paint(rgb, a, stroke=2 * r)
    cv.drawPoints(skia.Canvas.kPoints_PointMode, [skia.Point(float(x), float(y)) for x, y in pts], p)


def stipple(cv, rgb, box, spacing=11, r=1.7, seed=0, a=255, fn=None):
    """Field of printed dots inside box (x0,y0,x1,y1); fn(x,y)->0..1 scales the dot radius."""
    x0, y0, x1, y1 = box
    xs = np.arange(x0, x1, spacing)
    ys = np.arange(y0, y1, spacing * 0.87)
    if len(xs) == 0 or len(ys) == 0:
        return
    X, Y = np.meshgrid(xs, ys)
    X = X + (np.arange(len(ys))[:, None] % 2) * spacing / 2
    X = X.ravel(); Y = Y.ravel()
    if fn is None:
        dots(cv, np.stack([X, Y], 1), r, rgb, a)
        return
    s = np.clip(np.asarray(fn(X, Y), dtype=np.float64) * np.ones_like(X), 0, 1)
    lv = np.round(s * 4) / 4
    for q in (0.25, 0.5, 0.75, 1.0):
        m = np.abs(lv - q) < 1e-6
        if m.any():
            dots(cv, np.stack([X[m], Y[m]], 1), r * q, rgb, a)


def sparkle(cv, x, y, r, rgb=None, w=3.0, seed=0, a=255):
    """Four-point cartoon star with an ink outline; twinkles a little from drawing to drawing."""
    rgb = rgb or PAL["yellow"]
    tw = 0.82 + 0.3 * float(hsh(seed * 1.7 + D * 0.61))
    R = r * tw
    k = 0.28
    pts = []
    for i in range(8):
        ang = i * math.pi / 4 - math.pi / 2
        rr = R if i % 2 == 0 else R * k
        pts.append((x + rr * math.cos(ang), y + rr * math.sin(ang)))
    P = np.array(pts)
    path = skia.Path()
    path.moveTo(*P[0])
    for i in range(0, 8, 2):
        c = P[(i + 1) % 8]
        e = P[(i + 2) % 8]
        path.quadTo(float(c[0]), float(c[1]), float(e[0]), float(e[1]))
    path.close()
    cv.drawPath(path, paint(rgb, a))
    if w > 0:
        cv.drawPath(path, paint(INK, a, stroke=w * INKMUL))


# ---------------------------------------------------------------- surface + finish
def new_surface():
    s = skia.Surface.MakeRaster(skia.ImageInfo.Make(W, H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType))
    s.getCanvas().clear(C(PAL["night"]))
    return s


_PAPER = None


def _value_noise(h, w, cells, seed):
    rng = np.random.default_rng(seed)
    g = rng.random((cells[0] + 3, cells[1] + 3)).astype(np.float32)
    ys = np.linspace(0, cells[0], h, endpoint=False) + 1
    xs = np.linspace(0, cells[1], w, endpoint=False) + 1
    yi, xi = ys.astype(int), xs.astype(int)
    fy, fx = (ys - yi)[:, None], (xs - xi)[None, :]
    fy = fy * fy * (3 - 2 * fy); fx = fx * fx * (3 - 2 * fx)
    a = g[yi][:, xi]; b = g[yi][:, xi + 1]; c = g[yi + 1][:, xi]; d = g[yi + 1][:, xi + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def _paper():
    """Warm mottled printing paper (cached): multiplicative texture around 1.0."""
    global _PAPER
    if _PAPER is None:
        n = (0.55 * _value_noise(H, W, (9, 16), 11) + 0.3 * _value_noise(H, W, (27, 48), 12) + 0.15 * _value_noise(H, W, (81, 144), 13))
        n = (n - n.mean()) / (n.std() + 1e-6)
        rng = np.random.default_rng(14)
        fib = rng.normal(0, 1, (H, W)).astype(np.float32)
        fib = (fib + np.roll(fib, 1, 1) + np.roll(fib, 2, 1) + np.roll(fib, -1, 1)) / 4      # faint horizontal fibres
        m = 1.0 + 0.032 * n + 0.012 * fib
        tint = np.array([1.0, 0.992, 0.972], np.float32)
        _PAPER = (m[..., None] * tint[None, None, :]).astype(np.float32)
    return _PAPER


def _grain(d):
    """Per-drawing analog grain (2x2 clumps) + a few dust specks."""
    rng = np.random.default_rng(1000 + int(d))
    g = rng.normal(0, 4.2, (H // 2, W // 2, 1)).astype(np.float32).repeat(2, 0).repeat(2, 1)
    return g


def finish(surface, d):
    """Snapshot -> uint8 RGB HxWx3 with paper texture, grain and dust applied."""
    a = surface.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)[:, :, :3].astype(np.float32)
    out = a * _paper() + _grain(d)
    rng = np.random.default_rng(5000 + int(d))
    k = rng.integers(6, 14)
    ys = rng.integers(0, H - 3, k); xs = rng.integers(0, W - 3, k)
    for y, x in zip(ys, xs):                                       # dust: tiny dark specks
        out[y:y + 2, x:x + 3] *= 0.55
    return np.clip(out, 0, 255).astype(np.uint8)
