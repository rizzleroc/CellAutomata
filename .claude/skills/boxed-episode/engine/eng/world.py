"""BOXED world kit: the psychedelic set dressing. Every element is flat cel colour under boiling brush ink.
Sky pieces (field, sunburst, halo, stars, wavy bands, ribbons, hills, floaters), cosmic characters (faced planets,
skull moon, pyramid eye, eyeball walkers, eye-bats, jellies, worms, ghosts, mushrooms, wizard) and studio
props (rug, retro TV, lamp, couch, plant, box, padlock, door, floating island)."""
import math
import numpy as np
import skia
from .core import (PAL, INK, W, H, paint, poly_path, open_path, cr_closed, cr_open, ell, blob, line, brush, tube, dots,
                   hsh, mix, jit, rot, stipple, sparkle, rect_pts, snoise)
from . import core

P_ = PAL


def T(x0, y0, x1, y1):
    return skia.Rect.MakeLTRB(float(x0), float(y0), float(x1), float(y1))


def field(cv, rgb):
    cv.drawRect(T(-400, -400, W + 400, H + 400), paint(rgb))


def sunburst(cv, x, y, r, n, colors, rot_deg=0.0, seed=0, ink=0.0):
    """n wedges alternating through colors, radiating from (x, y)."""
    a0 = math.radians(rot_deg)
    for k in range(n):
        a1 = a0 + k * 2 * math.pi / n
        a2 = a0 + (k + 1) * 2 * math.pi / n
        wob = 1 + 0.015 * math.sin(core.D * 0.7 + k)
        pts = [(x, y), (x + r * wob * math.cos(a1), y + r * wob * math.sin(a1)), (x + r * wob * math.cos(a2), y + r * wob * math.sin(a2))]
        cv.drawPath(poly_path(pts), paint(colors[k % len(colors)]))
        if ink > 0:
            line(cv, [(x, y), pts[1]], ink, seed=seed + k, boil=0.6, n=2, taper=(0.05, 0.5))


def halo(cv, x, y, radii, colors, seed=0, ink=5.0, wob=6.0):
    for k, (r, c) in enumerate(zip(radii, colors)):
        pts = ell(x, y, r, r, n=18, phase=k * 0.3)
        pts = pts + np.stack([np.cos(np.arange(18) * 2.1 + k) * wob, np.sin(np.arange(18) * 1.7 + k) * wob], 1)
        blob(cv, pts, c, w=ink, seed=seed + k * 7, boil=1.2, n=6)


def stars(cv, seed, box=(0, 0, W, H), n=220, colors=None, big=10, rmax=2.6):
    x0, y0, x1, y1 = box
    colors = colors or [P_["cream"], P_["white"], P_["mint"], P_["hotpink"], P_["yellow"]]
    i = np.arange(n, dtype=np.float64)
    X = x0 + hsh(seed * 1.31 + i * 7.17) * (x1 - x0)
    Y = y0 + hsh(seed * 2.17 + i * 3.71) * (y1 - y0)
    R = 0.6 + (rmax - 0.6) * hsh(seed * 0.73 + i * 5.31) ** 2.2
    tw = 0.45 + 0.55 * np.abs(np.sin(core.D * (0.15 + 0.25 * hsh(i * 1.9 + seed)) + i))
    for k, c in enumerate(colors):
        m = (i % len(colors)) == k
        for lo, hi in ((0.0, 0.5), (0.5, 0.8), (0.8, 1.01)):
            mm = m & (tw >= lo) & (tw < hi)
            if mm.any():
                for rr in (1.0, 1.8, rmax):
                    sel = mm & (np.abs(R - rr) <= np.max([0.5, rr * 0.4]))
                    if sel.any():
                        dots(cv, np.stack([X[sel], Y[sel]], 1), rr, c, a=int(255 * (lo + hi) / 2))
    for k in range(big):
        bx = x0 + float(hsh(seed * 4.1 + k * 9.3)) * (x1 - x0)
        by = y0 + float(hsh(seed * 5.7 + k * 4.9)) * (y1 - y0)
        sparkle(cv, bx, by, 6 + 8 * float(hsh(seed + k * 2.3)), [P_["cream"], P_["yellow"], P_["white"]][k % 3], w=2.0, seed=seed + k)


# ---------------------------------------------------------------- planets
def _face(cv, x, y, r, face, seed):
    look = face.get("look", (0.0, 0.0))
    smile = face.get("smile", 0.3)
    lids = face.get("lids", 0.45)
    lid_rgb = face.get("lid_rgb", None)
    ex = r * 0.3
    er = r * 0.2
    ey = y - r * 0.12
    for side in (-1, 1):
        cx = x + side * ex
        blob(cv, ell(cx, ey, er, er * 1.08, n=12), P_["white"], w=max(3.0, r * 0.022), seed=seed + 40 + side, boil=0.7)
        pr = er * 0.42
        dots(cv, [(cx + look[0] * er * 0.42, ey + look[1] * er * 0.4)], pr, INK)
        dots(cv, [(cx + look[0] * er * 0.42 - pr * 0.35, ey + look[1] * er * 0.4 - pr * 0.4)], pr * 0.3, P_["white"])
        if lids > 0.02:
            ly = ey - er * 1.08 + 2 * er * 1.08 * min(1.0, lids)
            c = lid_rgb or mix(P_["orange"], INK, 0.15)
            lid = [(cx - er * 1.12, ey - er * 1.25), (cx + er * 1.12, ey - er * 1.25), (cx + er * 1.12, ly - er * 0.05), (cx + er * 0.5, ly + er * 0.14),
                   (cx - er * 0.5, ly + er * 0.14), (cx - er * 1.12, ly - er * 0.05)]
            cv.save()
            cv.clipPath(poly_path(cr_closed(ell(cx, ey, er + 1.5, er * 1.08 + 1.5, n=12), 4)), doAntiAlias=True)
            blob(cv, lid, c, w=0, seed=seed + 50 + side, boil=0.4, n=4, misreg=(0, 0))
            cv.restore()
            line(cv, [(cx - er * 1.02, ly - er * 0.02), (cx, ly + er * 0.16), (cx + er * 1.02, ly - er * 0.02)], max(3.0, r * 0.024), seed=seed + 52 + side,
                 boil=0.5, n=5, taper=(0.2, 0.2))
        line(cv, [(cx - er * 0.8, ey - er * 1.45 - 3), (cx, ey - er * 1.62 - 3), (cx + er * 0.8, ey - er * 1.45 - 3)], max(2.5, r * 0.018),
             seed=seed + 54 + side, boil=0.5, n=4, taper=(0.3, 0.3))
    my = y + r * 0.3
    sw = r * 0.26
    line(cv, [(x - sw, my - smile * r * 0.06), (x, my + smile * r * 0.13), (x + sw, my - smile * r * 0.06)], max(3.0, r * 0.024), seed=seed + 60,
         boil=0.6, n=6, taper=(0.25, 0.25))
    for side in (-1, 1):
        dots(cv, [(x + side * r * 0.56, y + r * 0.16)], r * 0.08, P_["hotpink"], a=150)


def _ring(cv, x, y, r, ring, seed, half):
    rx, ry = r * ring.get("rx", 1.7), r * ring.get("ry", 0.32)
    tilt = ring.get("tilt", -14)
    c1, c2 = ring.get("rgb", P_["teal"]), ring.get("rgb2", P_["cream"])
    outer = rot(ell(x, y, rx, ry, n=36), tilt, x, y)
    mid = rot(ell(x, y, rx * 0.86, ry * 0.8, n=36), tilt, x, y)
    inner = rot(ell(x, y, rx * 0.74, ry * 0.62, n=36), tilt, x, y)
    cv.save()
    clip = skia.Path()
    if half == "back":
        clip.addRect(T(x - rx * 2, y - ry * 3 - r, x + rx * 2, y))
        m = skia.Matrix(); m.setRotate(tilt, x, y); clip.transform(m)
    else:
        clip.addRect(T(x - rx * 2, y, x + rx * 2, y + ry * 3 + r))
        m = skia.Matrix(); m.setRotate(tilt, x, y); clip.transform(m)
    cv.clipPath(clip, doAntiAlias=True)
    band = poly_path(cr_closed(jit(outer, 0.8, seed), 2))
    band.addPoly([skia.Point(float(px), float(py)) for px, py in cr_closed(jit(inner, 0.8, seed + 1), 2)[::-1]], True)
    band.setFillType(skia.PathFillType.kEvenOdd)
    cv.drawPath(band, paint(c1))
    st = poly_path(cr_closed(jit(mid, 0.6, seed + 2), 2))
    st.addPoly([skia.Point(float(px), float(py)) for px, py in cr_closed(jit(rot(ell(x, y, rx * 0.8, ry * 0.71, n=36), tilt, x, y), 0.6, seed + 3), 2)[::-1]], True)
    st.setFillType(skia.PathFillType.kEvenOdd)
    cv.drawPath(st, paint(c2))
    brush(cv, cr_closed(jit(outer, 0.8, seed), 2), max(4.0, r * 0.024), closed=True, seed=seed + 4)
    brush(cv, cr_closed(jit(inner, 0.8, seed + 1), 2), max(3.0, r * 0.018), closed=True, seed=seed + 5)
    cv.restore()


def planet(cv, x, y, r, base, bands=(), tilt=-14, ring=None, face=None, seed=0, shade_rgb=None, crater=True, lid=None):
    if ring:
        _ring(cv, x, y, r, ring, seed + 300, "back")
    disc = ell(x, y, r, r, n=20)
    sh = shade_rgb or mix(base, INK, 0.28)

    def shade(c):
        cr = math.radians(tilt)
        for pos, wd, col in bands:
            yy = pos * r
            pts = []
            for k in range(13):
                u = -1.2 + 2.4 * k / 12
                pts.append((x + u * r, y + yy + r * 0.04 * math.sin(u * 4 + seed)))
            for k in range(12, -1, -1):
                u = -1.2 + 2.4 * k / 12
                pts.append((x + u * r, y + yy + wd * r + r * 0.04 * math.sin(u * 4 + seed + 1)))
            c.save(); c.rotate(tilt, x, y)
            c.drawPath(poly_path(pts), paint(col))
            c.restore()
        c.drawPath(poly_path(cr_closed(ell(x + r * 0.42, y + r * 0.38, r * 1.02, r * 0.98, n=16), 3)), paint(sh, 0))
        crescent = skia.Path()
        crescent.addCircle(x, y, r * 1.02)
        cut = skia.Path(); cut.addCircle(x - r * 0.22, y - r * 0.24, r * 1.04)
        cres = skia.Op(crescent, cut, skia.PathOp.kDifference_PathOp)
        if cres is not None:
            c.drawPath(cres, paint(sh, 170))
        stipple(c, sh, (x - r, y - r, x + r, y + r), spacing=max(7, r * 0.06), r=max(1.2, r * 0.012), seed=seed + 5,
                fn=lambda X, Y: np.clip(((X - x) * 0.6 + (Y - y) * 0.8) / r, 0, 1))
        if crater:
            for k in range(6):
                a = float(hsh(seed + k * 3.3)) * 6.28
                rr = r * (0.25 + 0.6 * float(hsh(seed + k * 5.1)))
                cx, cy = x + rr * math.cos(a), y + rr * math.sin(a)
                if face and abs(cx - x) < r * 0.62 and cy > y - r * 0.5 and cy < y + r * 0.55:
                    continue
                cs = r * (0.06 + 0.07 * float(hsh(seed + k * 7.7)))
                blob(c, ell(cx, cy, cs, cs * 0.8, n=8), mix(base, INK, 0.2), w=max(2.0, r * 0.014), seed=seed + 10 + k, boil=0.5)
        hl = ell(x - r * 0.42, y - r * 0.5, r * 0.22, r * 0.11, n=8, rot=-30)
        c.drawPath(poly_path(cr_closed(hl, 3)), paint(P_["white"], 70))
    blob(cv, disc, base, w=max(4.0, r * 0.03), seed=seed, boil=max(0.8, r * 0.006), n=6, shade=shade)
    if face:
        _face(cv, x, y, r, face, seed + 100)
    if ring:
        _ring(cv, x, y, r, ring, seed + 300, "front")


def ribbon(cv, ctrl, width, stripes, flow=0.0, seed=0, ink=6.0, starband=None, wav=0.05):
    """A thick striped cosmic ribbon along a spline; stripes ripple and flow."""
    C = cr_open(np.asarray(ctrl, dtype=np.float64), 14)
    d = np.diff(C, axis=0)
    L = np.concatenate([[0], np.cumsum(np.hypot(d[:, 0], d[:, 1]))])
    N = core._normals(C, False)
    ns = len(stripes)
    edges = []
    for i in range(ns + 1):
        f = -0.5 + i / ns
        rip = width * wav * np.sin(L / 140.0 - flow * 2.2 + i * 0.9 + seed) if 0 < i < ns else width * 0.02 * np.sin(L / 300.0 + i + seed)
        edges.append(C + N * (f * width + rip)[:, None])
    for i, col in enumerate(stripes):
        poly = np.vstack([edges[i], edges[i + 1][::-1]])
        cv.drawPath(poly_path(poly), paint(col))
        if starband is not None and i == starband:
            k = np.arange(0, len(C), 6)
            sp = (edges[i][k] + edges[i + 1][k]) / 2
            sp = sp + N[k] * ((hsh(k * 1.7 + seed) - 0.5) * width / ns * 0.6)[:, None]
            dots(cv, sp, max(1.5, width * 0.012), P_["white"], a=220)
    for e in (edges[0], edges[-1]):
        brush(cv, e, ink, taper=(0.02, 0.02), seed=seed + 7)


def hills(cv, y, amp, colors, seed=0, freq=1.0, spacing=24):
    for k, col in enumerate(colors):
        top = y + k * spacing
        xs = np.linspace(-200, W + 200, 40)
        ys = top - amp * (0.55 + 0.45 * np.sin(xs / W * math.pi * 2 * freq + seed + k * 1.3)) * (1 - 0.12 * k)
        pts = list(zip(xs, ys)) + [(W + 200, H + 300), (-200, H + 300)]
        cv.drawPath(poly_path(pts), paint(col))
        brush(cv, np.stack([xs, ys], 1), 5.0, taper=(0.02, 0.02), seed=seed + k * 3)


def wavy_band(cv, y, height, rgb, amp=24, freq=1.5, seed=0):
    xs = np.linspace(-200, W + 200, 48)
    ys = y + amp * np.sin(xs / W * math.pi * 2 * freq + seed * 1.7) + amp * 0.35 * np.sin(xs / W * math.pi * 6 * freq + seed)
    pts = list(zip(xs, ys)) + [(W + 200, y + height), (-200, y + height)]
    cv.drawPath(poly_path(pts), paint(rgb))
    brush(cv, np.stack([xs, ys], 1), 4.0, taper=(0.02, 0.02), seed=seed + 11, a=200)


# ---------------------------------------------------------------- cosmic creatures
def pyramid(cv, x, y, s, rgb=None, rgb2=None, eye=True, look=(0, 0), seed=0, lid=0.0, rays=True):
    rgb = rgb or P_["yellow"]
    rgb2 = rgb2 or P_["orange"]
    ax, ay = x, y - 300 * s
    if rays:
        for k in range(9):
            a = math.radians(-160 + k * 17.5)
            r0, r1 = 50 * s, (110 + 30 * (k % 2)) * s
            line(cv, [(ax + r0 * math.cos(a), ay + r0 * math.sin(a)), (ax + r1 * math.cos(a), ay + r1 * math.sin(a))], 4.5 * s + 1.5, P_["yellow"],
                 seed=seed + k, boil=0.8, n=2, taper=(0.1, 0.4))
    L, R, Bm = (x - 200 * s, y), (x + 200 * s, y), (x + 40 * s, y)

    def sh(c):
        c.drawPath(poly_path([(ax, ay), Bm, R]), paint(rgb2))
        for k in range(1, 6):
            yy = ay + (y - ay) * k / 6
            hw = 200 * s * k / 6
            c.drawLine(x - hw, yy, x + hw, yy, paint(mix(rgb, INK, 0.25), stroke=2.5))
    blob(cv, [(ax, ay), R, L], rgb, w=5.5, seed=seed + 20, boil=0.9, n=2, shade=sh)
    if eye:
        eye_glyph(cv, x, y - 140 * s, s * 1.1, look=look, seed=seed + 30, lid=lid)


def eye_glyph(cv, x, y, s, look=(0, 0), seed=0, lid=0.0, iris=None):
    w_, h_ = 62 * s, 30 * s
    pts = [(x - w_, y), (x - w_ * 0.4, y - h_), (x + w_ * 0.4, y - h_), (x + w_, y), (x + w_ * 0.4, y + h_), (x - w_ * 0.4, y + h_)]

    def sh(c):
        ir = h_ * 0.85
        ix, iy = x + look[0] * w_ * 0.3, y + look[1] * h_ * 0.25
        c.drawCircle(ix, iy, ir, paint(iris or P_["teal"]))
        c.drawCircle(ix, iy, ir * 0.45, paint(INK))
        c.drawCircle(ix - ir * 0.3, iy - ir * 0.35, ir * 0.18, paint(P_["white"]))
        if lid > 0:
            c.drawRect(T(x - w_ * 1.2, y - h_ * 1.3, x + w_ * 1.2, y - h_ + 2 * h_ * lid), paint(P_["violet"]))
    blob(cv, pts, P_["white"], w=4.0 * s + 1.5, seed=seed, boil=0.6, n=6, shade=sh)


def eyeball_walker(cv, x, y, s, phase, seed=0):
    bob = abs(math.sin(phase * 2)) * 10 * s
    for side in (-1, 1):
        sw = math.sin(phase * 2 + (0 if side < 0 else math.pi)) * 22 * s
        tube(cv, [(x + side * 18 * s, y - 40 * s - bob), (x + side * 18 * s + sw * 0.5, y - 15 * s), (x + side * 22 * s + sw, y)], 7 * s + 2, P_["cream"],
             w=3.5, seed=seed + side, boil=0.6, n=5)
        blob(cv, ell(x + side * 22 * s + sw + side * 6 * s, y + 2 * s, 14 * s, 7 * s, n=8), P_["red"], w=3, seed=seed + 5 + side, boil=0.5)
    cy = y - 80 * s - bob
    blob(cv, ell(x, cy, 46 * s, 46 * s, n=12), P_["white"], w=4.5, seed=seed + 10, boil=0.8,
         shade=lambda c: [c.drawLine(x + 46 * s * math.cos(a), cy + 46 * s * math.sin(a), x + 30 * s * math.cos(a + 0.2), cy + 30 * s * math.sin(a + 0.2),
                                     paint(P_["red"], stroke=2)) for a in np.linspace(0, 6, 6)])
    lk = math.sin(phase * 0.7) * 10 * s
    dots(cv, [(x + lk, cy)], 20 * s, P_["acid"])
    dots(cv, [(x + lk, cy)], 9 * s, INK)
    dots(cv, [(x + lk - 6 * s, cy - 6 * s)], 3.5 * s, P_["white"])


def eye_bat(cv, x, y, s, phase, seed=0):
    flap = math.sin(phase * 3)
    for side in (-1, 1):
        wy = -30 * s * flap
        pts = [(x + side * 30 * s, y - 5 * s), (x + side * 70 * s, y - 40 * s + wy), (x + side * 120 * s, y - 30 * s + wy * 1.3),
               (x + side * 105 * s, y + 5 * s + wy * 0.6), (x + side * 85 * s, y + wy * 0.4), (x + side * 70 * s, y + 18 * s + wy * 0.3), (x + side * 45 * s, y + 12 * s)]
        blob(cv, pts, P_["violet"], w=4, seed=seed + side, boil=0.8, n=4)
    blob(cv, ell(x, y, 36 * s, 36 * s, n=12), P_["cream"], w=4.5, seed=seed + 5, boil=0.8)
    dots(cv, [(x, y)], 17 * s, P_["acid_dk"])
    dots(cv, [(x, y)], 8 * s, INK)
    dots(cv, [(x - 5 * s, y - 5 * s)], 3 * s, P_["white"])


def ghost(cv, x, y, s, phase, seed=0, rgb=None):
    rgb = rgb or P_["white"]
    bob = math.sin(phase * 2) * 10 * s
    pts = [(x - 60 * s, y + 70 * s + bob)]
    for k in range(7):
        pts.append((x - 60 * s + k * 20 * s, y + (82 if k % 2 else 64) * s + bob + 6 * s * math.sin(phase * 3 + k)))
    pts += [(x + 60 * s, y + 70 * s + bob), (x + 64 * s, y - 20 * s + bob), (x, y - 90 * s + bob), (x - 64 * s, y - 20 * s + bob)]
    blob(cv, pts, rgb, w=4.5, seed=seed, boil=0.9, n=5)
    for side in (-1, 1):
        dots(cv, [(x + side * 22 * s, y - 20 * s + bob)], 11 * s, INK)
    blob(cv, ell(x, y + 14 * s + bob, 12 * s, 16 * s, n=8), INK, w=0, seed=seed + 3, boil=0.6, misreg=(0, 0))


def worm(cv, x, y, s, phase, seed=0, rgb=None, rgb2=None, length=8):
    rgb = rgb or P_["hotpink"]
    rgb2 = rgb2 or P_["acid"]
    for k in range(length - 1, -1, -1):
        cx = x - k * 34 * s
        cy = y - abs(math.sin(phase * 2 - k * 0.6)) * 18 * s
        blob(cv, ell(cx, cy, 26 * s, 26 * s, n=10), rgb if k % 2 == 0 else rgb2, w=4, seed=seed + k, boil=0.7)
    hx, hy = x + 14 * s, y - abs(math.sin(phase * 2)) * 18 * s - 8 * s
    blob(cv, ell(hx, hy, 32 * s, 30 * s, n=10), rgb, w=4.5, seed=seed + 50, boil=0.7)
    for side in (-1, 1):
        dots(cv, [(hx + 4 * s + side * 12 * s, hy - 6 * s)], 8 * s, P_["white"])
        dots(cv, [(hx + 6 * s + side * 12 * s, hy - 5 * s)], 4 * s, INK)
        line(cv, [(hx + side * 10 * s, hy - 26 * s), (hx + side * 18 * s, hy - 46 * s)], 3, seed=seed + 60 + side, boil=0.5, n=2)
        dots(cv, [(hx + side * 18 * s, hy - 48 * s)], 5 * s, P_["yellow"])
    line(cv, [(hx - 8 * s, hy + 10 * s), (hx + 4 * s, hy + 16 * s), (hx + 16 * s, hy + 10 * s)], 3, seed=seed + 70, boil=0.4, n=3)


def skull_moon(cv, x, y, r, seed=0):
    jaw = [(x - r * 0.62, y + r * 0.42), (x - r * 0.5, y + r * 0.92), (x + r * 0.5, y + r * 0.92), (x + r * 0.62, y + r * 0.42)]
    blob(cv, jaw, P_["cream"], w=4.5, seed=seed + 1, boil=0.8, n=4)
    for k in range(5):
        tx = x - r * 0.4 + k * r * 0.2
        cv.drawLine(tx, y + r * 0.55, tx, y + r * 0.88, paint(INK, stroke=max(2.0, r * 0.035)))
    blob(cv, ell(x, y, r, r * 0.92, n=14), P_["cream"], w=max(4.0, r * 0.05), seed=seed, boil=0.9,
         shade=lambda c: c.drawPath(poly_path(cr_closed(ell(x + r * 0.35, y + r * 0.3, r * 0.9, r * 0.8, n=10), 3)), paint(P_["cream_sh"], 140)))
    for side in (-1, 1):
        ex, ey = x + side * r * 0.36, y + r * 0.02
        blob(cv, ell(ex, ey, r * 0.26, r * 0.28, n=9), INK, w=0, seed=seed + 5 + side, boil=0.6, misreg=(0, 0))
        glow = 0.75 + 0.25 * math.sin(core.D * 0.4 + side)
        dots(cv, [(ex, ey + r * 0.02)], r * 0.1 * glow, P_["acid"])
    blob(cv, [(x, y + r * 0.26), (x - r * 0.1, y + r * 0.44), (x + r * 0.1, y + r * 0.44)], INK, w=0, seed=seed + 8, boil=0.4, n=2, misreg=(0, 0))


def mushroom(cv, x, y, s, cap=None, seed=0, face=True):
    cap = cap or P_["red"]
    blob(cv, [(x - 30 * s, y), (x - 24 * s, y - 120 * s), (x + 24 * s, y - 120 * s), (x + 32 * s, y)], P_["cream"], w=4.5, seed=seed, boil=0.8, n=4)
    if face:
        for side in (-1, 1):
            dots(cv, [(x + side * 11 * s, y - 70 * s)], 5 * s, INK)
        line(cv, [(x - 10 * s, y - 50 * s), (x, y - 44 * s), (x + 10 * s, y - 50 * s)], 3, seed=seed + 3, boil=0.4, n=3)
    pts = [(x - 110 * s, y - 108 * s), (x - 92 * s, y - 175 * s), (x, y - 212 * s), (x + 92 * s, y - 175 * s), (x + 110 * s, y - 108 * s), (x, y - 120 * s)]

    def sh(c):
        for k in range(6):
            sx = x - 70 * s + k * 28 * s
            sy = y - 160 * s + 20 * s * math.sin(k * 2.1)
            c.drawCircle(sx, sy, (11 + 5 * (k % 2)) * s, paint(P_["white"]))
    blob(cv, pts, cap, w=5, seed=seed + 10, boil=0.9, n=6, shade=sh)


def wizard(cv, x, y, s, seed=0, phase=0.0):
    sway = math.sin(phase) * 6 * s
    blob(cv, [(x - 60 * s, y), (x - 36 * s, y - 150 * s), (x + 36 * s, y - 150 * s), (x + 60 * s, y)], P_["blue"], w=4.5, seed=seed, boil=0.8, n=4,
         shade=lambda c: [sparkle(c, x - 20 * s + k * 22 * s, y - 100 * s + 30 * s * (k % 2), 7 * s, P_["yellow"], w=1.5, seed=seed + k) for k in range(3)])
    blob(cv, [(x - 34 * s, y - 158 * s), (x, y - 90 * s), (x + 34 * s, y - 158 * s), (x, y - 150 * s)], P_["white"], w=3.5, seed=seed + 2, boil=0.6, n=4)
    blob(cv, ell(x, y - 175 * s, 26 * s, 24 * s, n=9), P_["peach"], w=3.5, seed=seed + 3, boil=0.5)
    for side in (-1, 1):
        dots(cv, [(x + side * 8 * s, y - 180 * s)], 3 * s, INK)
    blob(cv, [(x - 50 * s, y - 192 * s), (x + 50 * s, y - 192 * s), (x + 8 * s + sway, y - 300 * s)], P_["blue"], w=4.5, seed=seed + 4, boil=0.7, n=3)
    line(cv, [(x + 70 * s, y), (x + 74 * s, y - 210 * s)], 6 * s + 2, (120, 80, 50), seed=seed + 5, boil=0.5, n=2, taper=(0, 0))
    dots(cv, [(x + 74 * s, y - 218 * s)], 13 * s, P_["acid"])


def jelly(cv, x, y, s, phase, seed=0, rgb=None):
    rgb = rgb or P_["hotpink"]
    for k in range(5):
        tx = x - 34 * s + k * 17 * s
        pts = [(tx, y)]
        for j in range(1, 5):
            pts.append((tx + 10 * s * math.sin(phase * 2 + j * 0.9 + k), y + j * 22 * s))
        line(cv, pts, 4 * s + 1, rgb, seed=seed + k, boil=0.6, n=5, taper=(0, 0.6))
    blob(cv, [(x - 50 * s, y + 4 * s), (x - 42 * s, y - 36 * s), (x, y - 56 * s), (x + 42 * s, y - 36 * s), (x + 50 * s, y + 4 * s)], rgb, w=4.5,
         seed=seed + 10, boil=0.8, n=5, shade=lambda c: c.drawPath(poly_path(cr_closed(ell(x - 14 * s, y - 34 * s, 16 * s, 8 * s, n=8), 3)), paint(P_["white"], 120)))
    for side in (-1, 1):
        dots(cv, [(x + side * 13 * s, y - 16 * s)], 5 * s, INK)


# ---------------------------------------------------------------- studio props
def rug(cv, x, y, rx, ry, seed=0):
    for k, col in enumerate((P_["magenta"], P_["orange"], P_["yellow"], P_["teal"])):
        f = 1 - k * 0.2
        blob(cv, ell(x, y, rx * f, ry * f, n=20), col, w=4.0 if k == 0 else 2.5, seed=seed + k, boil=1.0, n=4)


def tv(cv, x, y, s, seed=0, screen=None, body=None):
    body = body or P_["teal"]
    wd, ht = 320 * s, 230 * s
    for side in (-1, 1):
        line(cv, [(x + side * wd * 0.35, y + ht / 2), (x + side * wd * 0.42, y + ht / 2 + 60 * s)], 8 * s + 2, seed=seed + side, boil=0.6, n=2, taper=(0, 0))
        line(cv, [(x + side * 30 * s, y - ht / 2), (x + side * 120 * s, y - ht / 2 - 110 * s)], 4 * s + 1.5, (200, 200, 220), seed=seed + 5 + side, boil=0.6, n=2, taper=(0, 0))
        dots(cv, [(x + side * 120 * s, y - ht / 2 - 112 * s)], 10 * s, P_["orange"])
    blob(cv, rect_pts([(x - wd / 2, y - ht / 2), (x + wd / 2, y - ht / 2), (x + wd / 2, y + ht / 2), (x - wd / 2, y + ht / 2)], 3), body, w=6, seed=seed + 10,
         boil=0.9, n=3, shade=lambda c: c.drawRect(T(x + wd * 0.3, y - ht, x + wd, y + ht), paint(mix(body, INK, 0.25))))
    sx0, sy0, sx1, sy1 = x - wd * 0.42, y - ht * 0.38, x + wd * 0.22, y + ht * 0.38
    cv.drawRect(T(sx0, sy0, sx1, sy1), paint((16, 34, 52)))
    if screen is not None:
        cv.save()
        cv.clipRect(T(sx0, sy0, sx1, sy1), doAntiAlias=True)
        screen(cv, ((sx0 + sx1) / 2, (sy0 + sy1) / 2, sx1 - sx0, sy1 - sy0))
        cv.restore()
    for k in range(int((sy1 - sy0) / 6)):
        cv.drawRect(T(sx0, sy0 + k * 6, sx1, sy0 + k * 6 + 2), paint(INK, 40))
    brush(cv, np.array([(sx0, sy0), (sx1, sy0), (sx1, sy1), (sx0, sy1)]), 5, closed=True, seed=seed + 12)
    for k in range(2):
        blob(cv, ell(x + wd * 0.36, y - ht * 0.18 + k * ht * 0.34, 18 * s, 18 * s, n=8), P_["orange"], w=3.5, seed=seed + 20 + k, boil=0.5)


def lamp(cv, x, y, s, seed=0):
    radial = skia.Paint(AntiAlias=True)
    radial.setShader(skia.GradientShader.MakeRadial(skia.Point(x, y - 300 * s), 260 * s, [core.C(P_["hotpink"], 70), core.C(P_["hotpink"], 0)]))
    cv.drawCircle(x, y - 300 * s, 260 * s, radial)
    blob(cv, ell(x, y, 50 * s, 12 * s, n=10), P_["yellow"], w=4, seed=seed, boil=0.6)
    line(cv, [(x, y), (x, y - 300 * s)], 6 * s + 1.5, INK, seed=seed + 1, boil=0.4, n=2, taper=(0, 0))
    pts = [(x - 40 * s, y - 300 * s), (x - 80 * s, y - 330 * s + 0), (x - 70 * s, y - 380 * s), (x + 70 * s, y - 380 * s), (x + 80 * s, y - 330 * s), (x + 40 * s, y - 300 * s)]
    pts = [(x - 90 * s, y - 300 * s), (x - 60 * s, y - 400 * s), (x + 60 * s, y - 400 * s), (x + 90 * s, y - 300 * s)]
    blob(cv, rect_pts(pts, 3), P_["hotpink"], w=5, seed=seed + 2, boil=0.8, n=3,
         shade=lambda c: [c.drawLine(x - 80 * s + k * 18 * s, y - 300 * s, x - 55 * s + k * 13 * s, y - 400 * s, paint(P_["magenta"], stroke=3 * s + 1)) for k in range(10)])


def couch(cv, x, y, s, seed=0, rgb=None, rgb2=None, part="all"):
    rgb = rgb or P_["orange"]
    rgb2 = rgb2 or P_["red"]
    if part in ("all", "back"):
        back = [(x - 300 * s, y - 60 * s), (x - 300 * s, y - 250 * s), (x - 250 * s, y - 300 * s), (x + 250 * s, y - 300 * s), (x + 300 * s, y - 250 * s),
                (x + 300 * s, y - 60 * s)]
        blob(cv, rect_pts(back, 3), rgb, w=6, seed=seed, boil=1.0, n=3,
             shade=lambda c: [c.drawLine(x - 160 * s + k * 160 * s, y - 290 * s, x - 160 * s + k * 160 * s, y - 80 * s, paint(mix(rgb, INK, 0.22), stroke=4)) for k in range(3)])
        blob(cv, rect_pts([(x - 280 * s, y - 110 * s), (x + 280 * s, y - 110 * s), (x + 280 * s, y - 60 * s), (x - 280 * s, y - 60 * s)], 3), mix(rgb2, rgb, 0.3),
             w=5, seed=seed + 1, boil=0.9, n=3)
    if part in ("all", "front"):
        seat = [(x - 300 * s, y - 90 * s), (x + 300 * s, y - 90 * s), (x + 310 * s, y - 10 * s), (x - 310 * s, y - 10 * s)]
        blob(cv, rect_pts(seat, 3), rgb2, w=6, seed=seed + 2, boil=1.0, n=3,
             shade=lambda c: c.drawRect(T(x - 320 * s, y - 40 * s, x + 320 * s, y), paint(mix(rgb2, INK, 0.2))))
        for side in (-1, 1):
            arm = [(x + side * 300 * s, y - 10 * s), (x + side * 300 * s, y - 170 * s), (x + side * 330 * s, y - 200 * s), (x + side * 370 * s, y - 180 * s),
                   (x + side * 370 * s, y - 10 * s)]
            blob(cv, arm, rgb, w=6, seed=seed + 5 + side, boil=0.9, n=4,
                 shade=lambda c, side=side: c.drawRect(T(x + side * 300 * s - 40 * s * (side < 0), y - 210 * s, x + side * 300 * s + 40 * s * (side > 0) + side * 0.1,
                                                          y), paint(mix(rgb, INK, 0.15))))
        for side in (-1, 1):
            line(cv, [(x + side * 330 * s, y - 10 * s), (x + side * 330 * s, y + 20 * s)], 8 * s + 2, seed=seed + 9 + side, boil=0.4, n=2, taper=(0, 0))


def floaters(cv, seed, box=(0, 0, W, H), n=14, t=0.0):
    x0, y0, x1, y1 = box
    cols = [P_["hotpink"], P_["acid"], P_["yellow"], P_["teal"], P_["orange"], P_["lilac"]]
    for k in range(n):
        kind = int(hsh(seed + k * 1.9) * 4)
        x = x0 + (hsh(seed + k * 3.3) * (x1 - x0) + t * 12 * (hsh(seed + k * 5.5) - 0.5)) % (x1 - x0)
        y = y0 + hsh(seed + k * 7.1) * (y1 - y0) + 10 * math.sin(t * 0.7 + k)
        c = cols[k % len(cols)]
        sz = 8 + 10 * hsh(seed + k * 9.7)
        if kind == 0:
            cv.drawCircle(x, y, sz, paint(c, stroke=3.5))
        elif kind == 1:
            pts = [(x + (2 + u * 1.3) * math.cos(u * 1.4 + t), y + (2 + u * 1.3) * math.sin(u * 1.4 + t)) for u in np.linspace(0, 9, 24)]
            brush(cv, np.array(pts), 2.6, c, seed=seed + k, taper=(0.1, 0.3))
        elif kind == 2:
            blob(cv, ell(x, y, sz * 0.7, sz * 0.7, n=7), c, w=2.5, seed=seed + k, boil=0.6)
        else:
            blob(cv, [(x, y - sz), (x + sz * 0.9, y + sz * 0.6), (x - sz * 0.9, y + sz * 0.6)], c, w=2.5, seed=seed + k, boil=0.6, n=2)


def plant(cv, x, y, s, seed=0, phase=0.0):
    for k in range(5):
        a = -1.2 + k * 0.6
        sway = math.sin(phase * 2 + k) * 10 * s
        tip = (x + math.sin(a) * 120 * s + sway, y - 110 * s - (150 + 30 * (k % 2)) * s * math.cos(a * 0.6))
        line(cv, [(x, y - 90 * s), (x + math.sin(a) * 60 * s + sway * 0.5, y - 170 * s), tip], 5 * s + 1.5, P_["acid_dk"], seed=seed + k, boil=0.7, n=5, taper=(0, 0))
        blob(cv, ell(tip[0], tip[1], 20 * s, 20 * s, n=9), P_["white"], w=3.5, seed=seed + 10 + k, boil=0.6)
        dots(cv, [(tip[0] + 3 * s, tip[1])], 8 * s, INK)
    blob(cv, [(x - 60 * s, y - 100 * s), (x + 60 * s, y - 100 * s), (x + 44 * s, y), (x - 44 * s, y)], P_["red"], w=5, seed=seed + 20, boil=0.8, n=3)


def box(cv, x, y, w, h, seed=0, open_amt=0.0, rgb=None, rgb2=None, label=None, ink=6.5):
    rgb = rgb or (205, 150, 90)
    rgb2 = rgb2 or (170, 115, 60)
    fl = 0.4 * h * open_amt
    for side in (-1, 1):
        flap = [(x + side * w / 2, y - h), (x, y - h), (x + side * w * 0.15, y - h - fl), (x + side * w * 0.6, y - h - fl * 0.8)]
        blob(cv, flap, rgb2, w=ink * 0.8, seed=seed + 3 + side, boil=0.8, n=2)
    blob(cv, rect_pts([(x - w / 2, y - h), (x + w / 2, y - h), (x + w / 2, y), (x - w / 2, y)], 3), rgb, w=ink, seed=seed, boil=0.9, n=3,
         shade=lambda c: c.drawRect(T(x - w / 2, y - h, x - w / 2 + w * 0.12, y), paint(rgb2)))
    if label:
        from .letters import paint_text
        paint_text(cv, label, x, y - h * 0.4, font="londrina", size=h * 0.22, fill=P_["night"], ink_w=0, shadow=None, seed=seed + 9, streaks=False)


def padlock(cv, x, y, s, seed=0):
    tube(cv, [(x - 30 * s, y - 20 * s), (x - 30 * s, y - 70 * s), (x, y - 95 * s), (x + 30 * s, y - 70 * s), (x + 30 * s, y - 20 * s)], 12 * s + 2,
         (190, 190, 205), w=4, seed=seed, boil=0.6, n=5)
    blob(cv, rect_pts([(x - 50 * s, y - 25 * s), (x + 50 * s, y - 25 * s), (x + 50 * s, y + 55 * s), (x - 50 * s, y + 55 * s)], 3), P_["yellow"], w=5,
         seed=seed + 1, boil=0.7, n=3)
    dots(cv, [(x, y + 10 * s)], 10 * s, INK)
    cv.drawLine(x, y + 10 * s, x, y + 34 * s, paint(INK, stroke=6 * s))


def door(cv, x, y, s, open_amt=0.0, seed=0, rgb=None, light=None):
    rgb = rgb or P_["orange"]
    wd, ht = 160 * s, 300 * s
    blob(cv, rect_pts([(x - wd / 2 - 16 * s, y - ht - 16 * s), (x + wd / 2 + 16 * s, y - ht - 16 * s), (x + wd / 2 + 16 * s, y), (x - wd / 2 - 16 * s, y)], 3),
         P_["maroon"], w=5, seed=seed, boil=0.8, n=3)
    cv.drawRect(T(x - wd / 2, y - ht, x + wd / 2, y), paint(light or P_["yellow"]))
    ox = x - wd / 2 + wd * (1 - open_amt * 0.8)
    pts = [(x - wd / 2, y - ht), (ox, y - ht - 12 * s * open_amt), (ox, y + 12 * s * open_amt), (x - wd / 2, y)]
    blob(cv, pts, rgb, w=5, seed=seed + 1, boil=0.7, n=2)
    dots(cv, [(x - wd / 2 + (ox - (x - wd / 2)) * 0.82, y - ht / 2)], 7 * s, P_["yellow"])


def island(cv, x, y, rx, ry, seed=0, top=None, strata=None, depth=200, drips=True):
    top = top or P_["violet"]
    strata = strata or [P_["orange"], P_["red"], P_["maroon"], P_["night"]]
    n = len(strata)
    for k in range(n - 1, -1, -1):
        f0 = k / n
        yy = y + ry * 0.3 + depth * f0
        pts = []
        for j in range(21):
            u = j / 20
            ax = x - rx + 2 * rx * u
            pts.append((ax, y + ry * 0.2 * math.sin(math.pi * u)))
        for j in range(20, -1, -1):
            u = j / 20
            taper = (1 - f0 * 0.25)
            ax = x + (-rx + 2 * rx * u) * taper * (1 - 0.35 * (k + 1) / n)
            ay = yy + depth / n + 22 * math.sin(u * 7 + seed + k) + (depth * 0.25 * math.sin(math.pi * u) if k == n - 1 else 0)
            pts.append((ax, ay))
        blob(cv, pts, strata[k], w=5, seed=seed + k * 5, boil=1.0, n=3)
    blob(cv, ell(x, y, rx, ry, n=24), top, w=6, seed=seed + 50, boil=1.2, n=4,
         shade=lambda c: c.drawPath(poly_path(cr_closed(ell(x + rx * 0.2, y + ry * 0.35, rx * 0.95, ry * 0.7, n=16), 3)), paint(mix(top, INK, 0.18))))
    if drips:
        for k in range(7):
            dx = x - rx * 0.7 + k * rx * 0.23
            L = 40 + 60 * float(hsh(seed + k * 3.7)) + 8 * math.sin(core.D * 0.1 + k)
            dy = y + ry * 0.2 + depth * 0.9
            blob(cv, [(dx - 10, dy - 30), (dx + 10, dy - 30), (dx + 6, dy + L), (dx, dy + L + 10), (dx - 6, dy + L)], strata[-1], w=3.5, seed=seed + 70 + k,
                 boil=0.6, n=4)
