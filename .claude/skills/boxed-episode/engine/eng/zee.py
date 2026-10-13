"""ZEE — the lead. A lanky violet simulant: egg head, no nose, enormous turquoise eyes with heavy lids,
magenta fringe, two spring-loaded antennae, cream turtleneck with the triangle-eye emblem, orange
bell-bottoms, acid-green sneakers, rubber-hose arms and four-finger mitten hands.

draw_zee(cv, P) draws one drawing from a channel dict P (see DEFAULTS); everything boils.
Local space: origin at the feet, y down, ~790 px tall at s=1.
"""
import math
import numpy as np
import skia
from .core import (PAL, INK, jit, cr_open, cr_closed, ell, rot, poly_path, open_path, brush, line, blob,
                   tube, dots, stipple, paint, hsh, mix)
from . import core

SKIN, SKIN_SH = PAL["violet"], PAL["vdark"]
HAIR, HAIR_SH = PAL["magenta"], (196, 18, 118)
SWT, SWT_SH = PAL["cream"], PAL["cream_sh"]
PANTS, PANTS_SH = PAL["orange"], PAL["red"]
SHOE, SHOE_SH = PAL["acid"], PAL["acid_dk"]
IRIS, IRIS_DK = PAL["teal"], PAL["tealdk"]
ORB = PAL["yellow"]
HEAD_K = 1.17

DEFAULTS = dict(
    x=960.0, y=1000.0, s=1.0, lean=0.0, breath=0.0, hip=0.0,
    head_tilt=0.0, head_turn=0.0, head_dy=0.0, squash=1.0,
    blinkL=0.0, blinkR=0.0, lid=0.32, px=0.0, py=0.0, pupil=1.0,
    browL=0.0, browR=0.0, brow_ang=0.0,
    vis="X", mo=0.0, smile=0.25,
    aL_sh=112.0, aL_el=-10.0, aL_hand=0.0, aL_pose="open",
    aR_sh=68.0, aR_el=10.0, aR_hand=0.0, aR_pose="open",
    antL=(0.0, 0.0), antR=(0.0, 0.0), blush=1.0, prop=None, legs=True, sweat=0.0,
)

# finger tables: (angle deg rel. hand axis, length, curl) — thumb separately
POSES = {
    "open":   dict(f=[(-40, 25, 0.15), (-6, 29, 0.10), (28, 25, 0.15)], th=(80, 20, 0.2)),
    "flat":   dict(f=[(-14, 28, 0.0), (0, 30, 0.0), (14, 28, 0.0)], th=(62, 18, 0.1)),
    "spread": dict(f=[(-58, 27, 0.05), (-12, 32, 0.0), (34, 27, 0.05)], th=(98, 22, 0.1)),
    "point":  dict(f=[(-2, 38, 0.0), (-36, 9, 0.9), (-60, 8, 0.9)], th=(58, 10, 0.6)),
    "fist":   dict(f=[(-32, 9, 0.9), (0, 10, 0.9), (30, 9, 0.9)], th=(62, 10, 0.8)),
    "pinch":  dict(f=[(16, 25, 0.55), (-28, 21, 0.2), (-58, 18, 0.2)], th=(66, 23, -0.6)),
    "hold":   dict(f=[(-28, 15, 0.75), (0, 16, 0.75), (28, 15, 0.75)], th=(74, 17, 0.5)),
    "peace":  dict(f=[(-16, 34, 0.0), (14, 34, 0.0), (-50, 9, 0.9)], th=(70, 9, 0.7)),
}


def _hand(cv, wx, wy, ang, pose, mirror, seed, rgb=None, cuff=None):
    rgb = rgb or SKIN
    cv.save()
    cv.translate(wx, wy)
    cv.rotate(ang)
    cv.scale(1.0, mirror)
    spec = POSES.get(pose, POSES["open"])
    pc = np.array([19.0, 0.0])

    def finger(a, L, curl, k, width=13.0):
        ar = math.radians(a)
        d = np.array([math.cos(ar), math.sin(ar)])
        nrm = np.array([-d[1], d[0]])
        base = pc + 15 * d
        mid = base + d * L * 0.55 + nrm * curl * L * 0.55
        tip = base + d * L * (1 - 0.45 * abs(curl)) + nrm * curl * L * 0.9
        tube(cv, [base, mid, tip], width, rgb, w=4.0, seed=seed + k * 13, boil=0.9, n=6, misreg=(1.2, 0.8))

    for k, (a, L, c) in enumerate(spec["f"]):
        finger(a, L, c, k)
    blob(cv, ell(pc[0], pc[1], 21, 18, n=8), rgb, w=4.5, seed=seed + 50, boil=1.0, misreg=(1.4, 1.0))
    if cuff is not None:
        blob(cv, [(-6, -17), (8, -19), (8, 19), (-6, 17)], cuff, w=4.5, seed=seed + 55, boil=0.8, n=3)
    a, L, c = spec["th"]
    finger(a, L, c, 9, width=12.5)
    cv.restore()


def arm_points(sx, sy, a_sh, a_el, upper=92.0, fore=92.0):
    r1, r2 = math.radians(a_sh), math.radians(a_sh + a_el)
    ex, ey = sx + upper * math.cos(r1), sy + upper * math.sin(r1)
    wx, wy = ex + fore * math.cos(r2), ey + fore * math.sin(r2)
    return (ex, ey), (wx, wy), math.degrees(r2)


def _arm(cv, sx, sy, a_sh, a_el, seed):
    (ex, ey), (wx, wy), fdir = arm_points(sx, sy, a_sh, a_el)
    pts = cr_open(jit([(sx, sy), (ex, ey), (wx, wy)], 1.1, seed), 14)
    path = open_path(pts)
    cv.drawPath(path, paint(INK, stroke=24 + 9))
    cv.save(); cv.translate(1.4, 1.0); cv.drawPath(path, paint(SKIN, stroke=24)); cv.restore()
    k = int(len(pts) * 0.52)
    sl = pts[:k]
    sp = open_path(sl)
    cv.drawPath(sp, paint(INK, stroke=36 + 9))
    cv.save(); cv.translate(1.4, 1.0); cv.drawPath(sp, paint(SWT, stroke=36)); cv.restore()
    c = sl[-1]; d = sl[-1] - sl[-3]; d = d / (np.hypot(*d) + 1e-6); n = np.array([-d[1], d[0]])
    line(cv, [c + n * 19 - d * 3, c - n * 19 - d * 3], 4.0, seed=seed + 7, boil=0.8, n=4, taper=(0.1, 0.1))
    return wx, wy, fdir


MOUTHS = {  # width, depth, roundness, teeth-top, teeth-bottom, tongue (0 none, 1 low, 2 raised)
    "A": (82, 54, 0.25, 1, 0, 1), "E": (90, 34, 0.10, 1, 1, 0), "I": (92, 18, 0.0, 1, 1, 0),
    "O": (50, 46, 1.0, 0, 0, 1), "U": (32, 28, 1.0, 0, 0, 0), "F": (72, 16, 0.0, 1, 0, 0),
    "L": (74, 44, 0.3, 1, 0, 2), "M": (58, 0, 0.0, 0, 0, 0), "X": (66, 0, 0.0, 0, 0, 0),
}


def mouth_shape(vis, mo, smile, wk=1.0):
    """Open-mouth outline (10 control points, left corner first, over the top lip) or None when closed."""
    mo = float(np.clip(mo, 0, 1))
    w, dep, rnd, tt, tb, tg = MOUTHS.get(vis, MOUTHS["X"])
    w *= wk
    dep = dep * mo
    if dep < 3.5 or vis in ("X", "M"):
        return None
    cy = -smile * 11
    hw = w / 2 * (1 - 0.2 * (1 - mo) * rnd)
    sm = smile * 6
    flat = np.array([(-hw, cy - sm), (-hw * 0.55, cy - 2), (0, cy - 3), (hw * 0.55, cy - 2), (hw, cy - sm),
                     (hw * 0.8, cy + dep * 0.55), (hw * 0.42, cy + dep * 0.92), (0, cy + dep),
                     (-hw * 0.42, cy + dep * 0.92), (-hw * 0.8, cy + dep * 0.55)], float)
    ry = max(dep * 0.6, 6.0)
    oy = cy + dep * 0.4
    ang = np.array([180, 222, 270, 318, 360, 36, 64, 90, 116, 144], float)
    a = np.radians(ang)
    rx = hw * (0.9 if rnd > 0.5 else 1.0)
    rnd_pts = np.stack([rx * np.cos(a), oy + ry * np.sin(a)], 1)
    return flat * (1 - rnd) + rnd_pts * rnd


def _mouth(cv, vis, mo, smile, seed, wk=1.0, inside=None, tongue=None, teeth=None, ink=INK, iw=5.0):
    mo = float(np.clip(mo, 0, 1))
    cy = -smile * 11
    w, dep, rnd, tt, tb, tg = MOUTHS.get(vis, MOUTHS["X"])
    w *= wk
    dep = dep * mo
    if dep < 3.5 or vis in ("X", "M"):
        sag = -smile * 13
        hw = w / 2 * (1 + 0.12 * smile)
        if vis == "M":
            hw *= 0.9
        pts = [(-hw, cy + sag * 0.15), (-hw * 0.5, cy - sag * 0.7), (0, cy - sag), (hw * 0.5, cy - sag * 0.7), (hw, cy + sag * 0.15)]
        line(cv, pts, iw * (1.15 if vis == "M" else 1.0), ink, seed=seed + 700, boil=0.8, n=6, taper=(0.22, 0.22))
        if smile > 0.32:                                          # dimple ticks
            for sd in (-1, 1):
                line(cv, [(sd * (hw - 5), cy + sag * 0.15 - 7), (sd * (hw + 5), cy + sag * 0.15 + 3)], iw * 0.6, ink,
                     seed=seed + 705 + sd, boil=0.6, n=3, taper=(0.3, 0.3))
        elif smile < -0.1:                                        # frown corners
            for sd in (-1, 1):
                line(cv, [(sd * (hw - 2), cy + sag * 0.15), (sd * (hw + 6), cy + sag * 0.15 + 7)], iw * 0.6, ink,
                     seed=seed + 707 + sd, boil=0.6, n=3, taper=(0.3, 0.3))
        return
    S = mouth_shape(vis, mo, smile, wk)
    Pf = cr_closed(jit(S, 0.7, seed + 711), 8) + np.array([1.2, 0.9])
    fp = poly_path(Pf)
    cv.drawPath(fp, paint(inside or PAL["mouth"]))
    cv.save()
    cv.clipPath(fp, doAntiAlias=True)
    x0, y0 = S.min(0); x1, y1 = S.max(0)
    if tt:
        th = max(8.0, (y1 - y0) * 0.26)
        p = poly_path(cr_open([(x0 - 10, y0 - 10), (x0 - 10, y0 + th), (0, y0 + th + 3), (x1 + 10, y0 + th), (x1 + 10, y0 - 10)], 6))
        cv.drawPath(p, paint(teeth or PAL["white"]))
    if tb:
        th = max(6.0, (y1 - y0) * 0.2)
        p = poly_path(cr_open([(x0 - 10, y1 + 10), (x0 - 10, y1 - th), (0, y1 - th - 2), (x1 + 10, y1 - th), (x1 + 10, y1 + 10)], 6))
        cv.drawPath(p, paint(teeth or PAL["white"]))
    if tg:
        ty = y1 - (y1 - y0) * (0.12 if tg == 1 else 0.38)
        cv.drawPath(poly_path(ell(2, ty, (x1 - x0) * 0.32, max(7.0, (y1 - y0) * 0.38), n=16)), paint(tongue or PAL["tongue"]))
    cv.restore()
    brush(cv, cr_closed(jit(S, 0.9, seed + 713), 8), iw, ink, var=0.35, seed=seed + 714, closed=True)


# ---------------------------------------------------------------- head (local: head centre origin, before HEAD_K)
def _head_ctrl():
    a = np.radians(np.arange(-90, 270, 24.0))
    x = 144 * np.cos(a) * (1 + 0.03 * np.sin(a))
    y = np.where(np.sin(a) < 0, 150, 146) * np.sin(a)
    return np.stack([x, y], 1)


HEAD = _head_ctrl()
# fringe: magenta points come down between violet arches (left to right)
FRINGE = np.array([(-160, -8), (-141, -20), (-128, -46), (-110, -58), (-94, -82), (-70, -86), (-46, -72), (-28, -54),
                   (-12, -78), (8, -90), (30, -78), (48, -58), (70, -84), (96, -84), (114, -60), (130, -44),
                   (142, -20), (160, -8)], float)


def _eye(cv, ex, ey, rx, ry, P, side, blink, seed):
    """One huge eye: cream sclera, teal iris with a dark crescent, pupil + two highlights, heavy violet lid, lashes."""
    lid = float(np.clip(P["lid"] + (1 - P["lid"]) * blink, 0, 1))
    S = ell(ex, ey, rx, ry, n=12, phase=0.3 * side)
    if lid > 0.97:                                               # fully shut: a curved lash line
        ys = ey + ry * 0.25
        line(cv, [(ex - rx * 0.95, ys - 6), (ex - rx * 0.4, ys + 6), (ex + rx * 0.4, ys + 6), (ex + rx * 0.95, ys - 6)],
             6.5, seed=seed + 1, boil=0.7, n=6, taper=(0.15, 0.15))
        o = side
        for k in range(3):
            bx = ex + o * rx * (0.62 + 0.16 * k)
            line(cv, [(bx, ys + 1 - 3 * k), (bx + o * 10, ys + 10 - 2 * k)], 3.2, seed=seed + 4 + k, boil=0.5, n=3, taper=(0.2, 0.4))
        return
    Pf = cr_closed(jit(S, 0.8, seed + 917), 8) + np.array([1.4, 1.0])
    fp = poly_path(Pf)
    cv.drawPath(fp, paint(PAL["white"]))
    cv.save()
    cv.clipPath(fp, doAntiAlias=True)
    # gaze
    ir = rx * 0.66
    gx = ex + P["px"] * (rx - ir * 0.72) + P.get("head_turn", 0.0) * 6
    gy = ey + ry * 0.1 + P["py"] * (ry - ir * 0.8)
    cv.drawPath(poly_path(ell(gx, gy, ir, ir * 1.02, n=24)), paint(IRIS))
    sh = skia.Path.Circle(gx, gy, ir)
    cv.save()
    cv.clipPath(sh, doAntiAlias=True)
    cv.drawPath(poly_path(ell(gx - ir * 0.12, gy + ir * 0.62, ir * 1.05, ir * 0.62, n=20)), paint(IRIS_DK))
    cv.restore()
    brush(cv, ell(gx, gy, ir, ir * 1.02, n=24), 3.0, seed=seed + 11, closed=True, var=0.2)
    pr = ir * 0.5 * float(np.clip(P["pupil"], 0.4, 1.6))
    cv.drawCircle(gx, gy, pr, paint(INK))
    cv.drawCircle(gx - ir * 0.36, gy - ir * 0.38, max(3.0, ir * 0.2), paint(PAL["white"]))
    cv.drawCircle(gx + ir * 0.22, gy + ir * 0.1, max(1.6, ir * 0.08), paint(PAL["white"]))
    # lid: violet sheet from the top down to the lid line
    yl = ey - ry + 2 * ry * lid
    if lid > 0.03:
        lp = poly_path(cr_open([(ex - rx - 20, ey - ry - 30), (ex - rx - 20, yl + 6 * side * 0), (ex, yl + ry * 0.12 * (1 - lid)),
                                (ex + rx + 20, yl), (ex + rx + 20, ey - ry - 30)], 6))
        cv.drawPath(lp, paint(SKIN))
        cv.drawPath(poly_path(ell(ex + rx * 0.35, ey - ry, rx * 0.9, max(4.0, (yl - ey + ry) * 0.7), n=14)), paint(SKIN_SH, 90))
    cv.restore()
    if lid > 0.03:                                               # lid edge
        line(cv, [(ex - rx * 0.98, yl + 4), (ex - rx * 0.5, yl + ry * 0.1 * (1 - lid)), (ex + rx * 0.5, yl + ry * 0.1 * (1 - lid)), (ex + rx * 0.98, yl + 4)],
             5.0, seed=seed + 21, boil=0.7, n=6, taper=(0.12, 0.12))
    brush(cv, cr_closed(jit(S, 1.0, seed + 23), 8), 6.0, var=0.45, seed=seed + 24, closed=True)
    # lashes at the outer top corner
    o = side
    ang0 = math.radians(-58 if o > 0 else -122)
    for k in range(3):
        a = ang0 + o * math.radians(16 * k)
        bx, by = ex + rx * 0.96 * math.cos(a), ey + ry * 0.96 * math.sin(a)
        L = 13 + 2 * k
        line(cv, [(bx, by), (bx + o * L * 0.6, by - L * 0.55), (bx + o * L * 1.05, by - L * 0.62)], 3.4,
             seed=seed + 30 + k, boil=0.5, n=4, taper=(0.15, 0.6))


def _head(cv, P, seed):
    turn = float(P.get("head_turn", 0.0))
    fx = turn * 20.0
    # antennae (behind the head)
    for side, key in ((-1, "antL"), (1, "antR")):
        dx, dy = P[key]
        base = np.array([side * 52.0, -132.0])
        tip = np.array([side * 98.0 + dx + turn * 10, -238.0 + dy])
        mid = (base + tip) / 2 + np.array([side * -10.0, -6.0])
        line(cv, [base, mid, tip], 4.2, seed=seed + 600 + side, boil=0.9, n=6, taper=(0.05, 0.05), var=0.15)
        blob(cv, ell(tip[0], tip[1], 15, 15, n=8), ORB, w=4.0, seed=seed + 604 + side, boil=0.8, misreg=(1.2, 0.8))
        cv.drawCircle(tip[0] - 5, tip[1] - 5, 3.6, paint(PAL["white"]))
    # head mass
    Pts = cr_closed(jit(HEAD, 1.3, seed + 610), 8)
    Pf = cr_closed(jit(HEAD, 0.9, seed + 1527), 8) + np.array([2.0, 1.4])
    fp = poly_path(Pf)
    cv.drawPath(fp, paint(SKIN))
    cv.save()
    cv.clipPath(fp, doAntiAlias=True)
    cres = skia.Op(poly_path(ell(0, 0, 150, 160, n=24)), poly_path(ell(-26 + fx * 0.4, -18, 150, 160, n=24)), skia.PathOp.kDifference_PathOp)
    if cres is not None:
        cv.drawPath(cres, paint(SKIN_SH, 150))
    Fr = FRINGE.copy()
    Fr[:, 0] = Fr[:, 0] + fx * 0.5 * (1 - np.abs(Fr[:, 0]) / 170)
    hair = np.vstack([Fr, [(170, -40), (170, -200), (-170, -200), (-170, -40)]])
    hp = poly_path(cr_closed(jit(hair, 1.0, seed + 620), 4))
    cv.drawPath(hp, paint(HAIR))
    cv.save()
    cv.clipPath(hp, doAntiAlias=True)
    hc = skia.Op(poly_path(ell(0, 0, 150, 160, n=24)), poly_path(ell(-30, -14, 150, 160, n=24)), skia.PathOp.kDifference_PathOp)
    if hc is not None:
        cv.drawPath(hc, paint(HAIR_SH))
    line(cv, [(-96, -118), (-60, -136), (-20, -142)], 9.0, mix(HAIR, PAL["white"], 0.35), seed=seed + 624, boil=0.6, n=5, taper=(0.4, 0.4), a=200)
    cv.restore()
    # freckles + blush
    bl = float(np.clip(P["blush"], 0, 2))
    for side in (-1, 1):
        bx, by = side * 100 + fx * 0.6, 70
        cv.drawPath(poly_path(ell(bx, by, 28 * (0.8 + 0.2 * bl), 15 * (0.8 + 0.2 * bl), n=14)), paint(PAL["hotpink"], int(min(255, 150 * bl))))
        dots(cv, [(bx - 9, by - 2), (bx + 4, by - 5), (bx + 12, by + 3)], 1.7, PAL["magenta"], a=int(min(255, 200 * bl)))
    fr = []
    for k in range(14):
        h1, h2 = float(hsh(seed * 0.17 + k * 3.1)), float(hsh(seed * 0.29 + k * 5.7))
        fr.append((56 + h1 * 44 + fx * 0.6, 92 + h2 * 26))
    dots(cv, fr, 1.9, SKIN_SH)
    cv.restore()
    brush(cv, Pts, 6.5, var=0.35, seed=seed + 612, closed=True)
    # fringe ink (only inside the head silhouette)
    cv.save()
    cv.clipPath(poly_path(cr_closed(HEAD, 6)), doAntiAlias=True)
    brush(cv, cr_open(jit(Fr, 1.0, seed + 620), 4), 4.6, var=0.3, seed=seed + 626, taper=(0.02, 0.02))
    cv.restore()
    # brows (on the hair)
    for side, key in ((-1, "browL"), (1, "browR")):
        b = float(P[key])
        ang = float(P["brow_ang"])
        bx = side * 70 + fx
        by = -100 - 12 * b
        inner = (bx - side * 34, by + 3 + side * 0 + 12 * ang)
        outer = (bx + side * 38, by + 6 - 4 * ang)
        midp = (bx, by - 6 - 3 * b)
        line(cv, [inner, midp, outer], 7.0, seed=seed + 640 + side, boil=0.8, n=6, taper=(0.35, 0.3))
    # eyes
    for side, key in ((-1, "blinkL"), (1, "blinkR")):
        _eye(cv, side * 64 + fx, 8, 53, 55, P, side, float(P[key]), seed + 660 + side * 10)
    # cheek lines under the eyes
    for side in (-1, 1):
        cx = side * 72 + fx * 0.8
        line(cv, [(cx - 14, 72), (cx, 76), (cx + 14, 72)], 3.0, seed=seed + 690 + side, boil=0.5, n=4, taper=(0.3, 0.3))
    # mouth
    cv.save()
    cv.translate(fx * 1.3, 96)
    _mouth(cv, P["vis"], P["mo"], P["smile"], seed)
    cv.restore()
    # sweat bead
    sw = float(P.get("sweat", 0.0))
    if sw > 0.02:
        ph = (core.D * 0.09) % 1.0
        sx_, sy_ = 122, -40 + 40 * ph
        drop = [(sx_, sy_ - 22), (sx_ + 11, sy_ + 2), (sx_, sy_ + 12), (sx_ - 11, sy_ + 2)]
        blob(cv, drop, PAL["mint"], w=3.5, seed=seed + 695, boil=0.6, n=6, a=int(255 * min(1.0, sw)))


# ---------------------------------------------------------------- legs
def _legs(cv, P, seed):
    hip = P["hip"]
    for side in (-1, 1):
        x0 = hip * 0.8 + side * 30
        xb = side * 40
        ctrl = [(x0 - 32, -200), (x0 + 32, -200), (x0 * 0.5 + xb * 0.5 + 22, -104), (xb + 44, -22), (xb - 44, -22),
                (x0 * 0.5 + xb * 0.5 - 22, -104)]
        if side > 0:
            ctrl = [ctrl[1], ctrl[0], ctrl[5], ctrl[4], ctrl[3], ctrl[2]]

        def shade(c, x0=x0, xb=xb, side=side):
            c.drawPath(poly_path([(x0 - side * 34, -210), (x0 - side * 8, -210), (xb - side * 8, -10), (xb - side * 50, -10)]),
                       paint(PANTS_SH))
        blob(cv, ctrl, PANTS, w=5.5, seed=seed + 100 + side * 7, boil=1.2, n=6, shade=shade)
        line(cv, [(xb - 30, -40), (xb + 30, -40)], 3.0, seed=seed + 110 + side, boil=0.7, n=3)
        # sneaker
        sh = [(xb - side * 30, -30), (xb + side * 34, -32), (xb + side * 58, -12), (xb + side * 52, 2), (xb - side * 34, 2)]
        blob(cv, sh, SHOE, w=5.0, seed=seed + 120 + side * 5, boil=1.0, n=6,
             shade=lambda c, xb=xb, side=side: c.drawPath(poly_path([(xb - side * 50, -6), (xb + side * 70, -6), (xb + side * 70, 8), (xb - side * 50, 8)]), paint(PAL["white"])))
        line(cv, [(xb - side * 6, -26), (xb + side * 8, -18)], 3.0, seed=seed + 130 + side, boil=0.6, n=3)
        line(cv, [(xb + side * 8, -28), (xb + side * 20, -18)], 3.0, seed=seed + 132 + side, boil=0.6, n=3)


# ---------------------------------------------------------------- the whole drawing
def draw_zee(cv, P0):
    P = dict(DEFAULTS)
    P.update(P0)
    seed = int(P.get("seed", 300))
    s = float(P["s"])
    old = core.INKMUL
    core.INKMUL = old / max(s, 0.15) ** 0.5
    try:
        cv.save()
        cv.translate(P["x"], P["y"])
        cv.scale(s, s)
        hands = _body(cv, P, seed)
        return hands
    finally:
        core.INKMUL = old


def _body(cv, P, seed):
    hip = P["hip"]
    if P["legs"]:
        _legs(cv, P, seed)
    cv.save()
    cv.rotate(P["lean"], hip, -186)
    br = 1 + 0.014 * math.sin(P["breath"] * 2 * math.pi)
    ctrl = np.array([(-54, -342), (-78, -304), (-84, -244), (-80, -196), (-66, -172), (0, -164), (66, -172),
                     (80, -196), (84, -244), (78, -304), (54, -342), (0, -352)], float)
    ctrl[:, 0] = ctrl[:, 0] * br + hip
    ctrl[:, 1] = -170 + (ctrl[:, 1] + 170) * br
    blob(cv, ctrl, SWT, w=6.0, seed=seed + 200, boil=1.4, n=8,
         shade=lambda c: (c.drawPath(poly_path(cr_closed([(30 + hip, -340), (100 + hip, -330), (100 + hip, -160), (40 + hip, -160), (62 + hip, -250)], 5)), paint(SWT_SH)),
                          stipple(c, SWT_SH, (-90 + hip, -330, 40 + hip, -170), spacing=12, r=1.6, seed=seed + 7,
                                  fn=lambda X, Y: np.clip((X - (hip - 20)) / 60, 0, 1) * 0.0 + 0.0)))
    for k in range(7):                               # hem ribbing
        x = -60 + k * 20 + hip
        line(cv, [(x, -186), (x + 1, -168)], 3.0, seed=seed + 210 + k, boil=0.8, n=3, taper=(0.2, 0.2))
    cy = -264 - 4 * (br - 1) * 100                   # emblem: triangle with an eye
    blob(cv, [(hip, cy - 38), (hip + 34, cy + 22), (hip - 34, cy + 22)], PANTS, w=4.5, seed=seed + 230, boil=0.9, n=3)
    blob(cv, ell(hip, cy + 4, 14, 8, n=8), PAL["white"], w=3.0, seed=seed + 231, boil=0.6)
    dots(cv, [(hip + 1, cy + 4)], 4.5, PAL["teal"])
    blob(cv, ell(hip, -350, 54, 21, n=10), SWT, w=5.5, seed=seed + 240, boil=1.0,
         shade=lambda c: [line(c, [(hip + x, -364), (hip + x, -336)], 2.6, seed=seed + 241 + i, boil=0.6, n=3) for i, x in enumerate(range(-36, 40, 12))])
    # head
    cv.save()
    cv.translate(hip, -536 + P["head_dy"])
    cv.rotate(P["head_tilt"])
    sq = P["squash"]
    cv.scale(HEAD_K * (1 + (1 - sq) * 0.6), HEAD_K * sq)
    _head(cv, P, seed)
    cv.restore()
    # arms (in front)
    hands = {}
    for side, pre in ((-1, "aL"), (1, "aR")):
        sx, sy = side * 60 + hip, -324
        wx, wy, fdir = _arm(cv, sx, sy, P[pre + "_sh"], P[pre + "_el"], seed + 400 + side * 20)
        hands[pre] = (wx, wy, fdir + P[pre + "_hand"])
    if P["prop"] is not None and callable(P["prop"]):
        P["prop"](cv, hands)
    for side, pre in ((-1, "aL"), (1, "aR")):
        wx, wy, ang = hands[pre]
        _hand(cv, wx, wy, ang, P[pre + "_pose"], 1 if side < 0 else -1, seed + 500 + side * 30)
    cv.restore()
    cv.restore()
    return hands
