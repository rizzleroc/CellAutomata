"""BOXED supporting cast.

HOST — a lanky talk-show MC with a CRT television for a head. His face is phosphor line-art on the
screen (eyes, brows, a lip-synced mouth), with scanlines and the odd rolling glitch; magenta tux with
yellow-piped lapels, white shirt, yellow bowtie, a dark cable neck, blue trousers, white cartoon gloves.

Also: ai_blob, alien, agent (tiny sim people), cosmic_hand, gauge, melting_clock.
Local space for draw_host: origin at the feet, y down.
"""
import math
import numpy as np
import skia
from .core import (PAL, INK, jit, cr_open, cr_closed, ell, rot, poly_path, open_path, brush, line, blob, tube,
                   dots, stipple, sparkle, paint, hsh, mix)
from . import core
from .zee import _hand, arm_points, MOUTHS

SUIT, SUIT_SH = PAL["magenta"], (204, 20, 128)
LAPEL = (226, 28, 146)
PIPING = PAL["yellow"]
SHIRT = PAL["white"]
NECK = (34, 30, 62)
TROU, TROU_SH = PAL["blue"], PAL["deepblue"]
CASE, CASE_SH = PAL["teal"], PAL["tealdk"]
GLOVE = PAL["white"]
PHOS = (190, 255, 214)
SCREEN = (16, 34, 52)
HEAD_S = 1.12
HEAD_Y = -580.0

HOST_DEFAULTS = dict(
    x=960.0, y=1000.0, s=1.0, lean=0.0, breath=0.0, hip=0.0,
    head_tilt=0.0, head_dy=0.0, squash=1.0,
    blinkL=0.0, blinkR=0.0, px=0.0, py=0.0, pupil=1.0, browL=0.0, browR=0.0, brow_ang=0.0,
    vis="X", mo=0.0, smile=0.3, glitch=0.0, face="normal",
    aL_sh=110.0, aL_el=-12.0, aL_hand=0.0, aL_pose="open",
    aR_sh=70.0, aR_el=12.0, aR_hand=0.0, aR_pose="open",
    antL=(0.0, 0.0), antR=(0.0, 0.0), prop=None, legs=True, mic=False,
)


def _host_mouth(cv, vis, mo, smile, seed):
    mo = float(np.clip(mo, 0, 1))
    w, dep, rnd, tt, tb, tg = MOUTHS.get(vis, MOUTHS["X"])
    w *= 0.8; dep *= mo * 0.85
    cy = -smile * 9
    if dep < 3 or vis in ("X", "M"):
        sag = -smile * 12
        line(cv, [(-w / 2, cy), (-w * 0.18, cy - sag), (w * 0.18, cy - sag), (w / 2, cy)], 5.5, PHOS, seed=seed,
             boil=0.8, n=6, taper=(0.2, 0.2))
        return
    hw = w / 2
    up = [(-hw, cy), (-hw * 0.45, cy - 3 - rnd * dep * 0.35), (hw * 0.45, cy - 3 - rnd * dep * 0.35), (hw, cy)]
    lo = [(hw * 0.55, cy + dep * 0.9), (0, cy + dep * 1.05), (-hw * 0.55, cy + dep * 0.9)]
    Pts = cr_closed(jit(up + lo, 0.8, seed), 7)
    cv.drawPath(poly_path(Pts), paint((6, 14, 22)))
    if tt:
        cv.save(); cv.clipPath(poly_path(Pts), doAntiAlias=True)
        cv.drawRect(skia.Rect.MakeLTRB(-hw, cy - 20, hw, cy + 7), paint(PHOS, 200)); cv.restore()
    brush(cv, Pts, 5.0, PHOS, closed=True, seed=seed + 3, var=0.3)


def _screen_face(cv, P, seed, sw, sh):
    """Phosphor face inside the CRT; coordinates centred on the screen."""
    face = P["face"]
    if face == "static":                                # pure TV snow
        rng = np.random.default_rng(int(core.D) * 7 + seed)
        xs = rng.uniform(-128, 128, 1100); ys = rng.uniform(-94, 94, 1100); g = rng.uniform(0.0, 1.0, 1100)
        for lo, hi in ((0.0, 0.35), (0.35, 0.7), (0.7, 1.01)):
            m = (g >= lo) & (g < hi)
            dots(cv, list(zip(xs[m], ys[m])), 2.4, mix(SCREEN, PHOS, 0.25 + hi * 0.75), a=230)
        return
    if face == "sleep":                                 # closed eyes, snoring mouth, Z's drifting up
        for side in (-1, 1):
            ex, ey = side * 52, -14
            line(cv, [(ex - 24, ey - 3), (ex, ey + 7), (ex + 24, ey - 3)], 6, PHOS, seed=seed + side, boil=0.8, n=4)
        br = 0.5 + 0.5 * math.sin(core.D / 12.0 * 2 * math.pi * 0.28)
        mpts = cr_closed(jit(ell(0, 50, 9 + 6 * br, 6 + 9 * br, n=8), 0.6, seed + 30), 5)
        cv.drawPath(poly_path(mpts), paint((6, 14, 22)))
        brush(cv, mpts, 4.5, PHOS, closed=True, seed=seed + 31)
        for k in range(3):
            ph = ((core.D / 12.0) * 0.45 + k / 3.0) % 1.0
            zx, zy, sz = 30 + ph * 60, -30 - ph * 55, 9 + 13 * ph
            line(cv, [(zx - sz / 2, zy - sz / 2), (zx + sz / 2, zy - sz / 2), (zx - sz / 2, zy + sz / 2), (zx + sz / 2, zy + sz / 2)], 4.0,
                 PHOS, seed=seed + 40 + k, boil=0.5, n=2, taper=(0, 0), a=int(255 * (1 - ph) ** 0.7))
        return
    if face == "knife":                                 # stuck on the shopping channel
        blob(cv, [(-70, 40), (10, 40), (16, 70), (-76, 70)], (150, 100, 60), w=3.5, seed=seed + 1, boil=0.6, n=2)
        for k in range(4):
            x = -64 + k * 20
            blob(cv, [(x, 40), (x + 9, 40), (x + 7, -8), (x + 2, -8)], (40, 30, 30), w=2.5, seed=seed + 2 + k, boil=0.4, n=2)
        line(cv, [(30, -60), (100, -60)], 3, PHOS, seed=seed + 9, boil=0.3, n=2, taper=(0, 0))
        from .letters import paint_text
        paint_text(cv, "$19.99", 62, 10, font="bangers", size=40, fill=PAL["yellow"], ink_w=0, shadow=None, seed=seed + 10, streaks=False)
        paint_text(cv, "CALL NOW", 62, 52, font="bangers", size=24, fill=PHOS, ink_w=0, shadow=None, seed=seed + 11, streaks=False)
        return
    if face == "wave":                                  # a curling wave with two little eyes
        ph = core.D * 0.15
        crest = [(-130, 60), (-80, 40 + 6 * math.sin(ph)), (-30, -10), (10, -50), (40, -60), (70, -40), (60, -20), (40, -30),
                 (30, -10), (60, 30), (130, 50), (130, 95), (-130, 95)]
        cv.drawPath(poly_path(cr_closed(crest, 4)), paint(mix(SCREEN, PAL["blue"], 0.6)))
        brush(cv, cr_open(crest[:11], 6), 5.0, PHOS, seed=seed + 5)
        for side in (-1, 1):
            dots(cv, [(-10 + side * 22, 20)], 8, PHOS)
            dots(cv, [(-10 + side * 22 + 2, 21)], 3.5, (6, 14, 22))
        return
    if face == "chord":                                 # BWAAAM: a staff exploding with notes
        for k in range(5):
            line(cv, [(-120, -40 + k * 14), (110, -40 + k * 14)], 2.2, PHOS, seed=seed + k, boil=0.4, n=2, taper=(0, 0), a=150)
        for k, (nx, ny) in enumerate(((-80, -12), (-40, -26), (0, -40), (40, -54), (80, -68))):
            dots(cv, [(nx, ny + 30)], 9, PHOS)
            line(cv, [(nx + 8, ny + 30), (nx + 8, ny - 10)], 3, PHOS, seed=seed + 20 + k, boil=0.3, n=2, taper=(0, 0))
        from .letters import paint_text
        paint_text(cv, "BWAAAM!", 0, 78, font="bangers", size=44, fill=PAL["yellow"], ink_w=0, shadow=None, seed=seed + 30, streaks=False)
        return
    if face == "me":                                    # a tiny host on the host: the TV watching itself
        blob(cv, [(-34, -46), (34, -46), (38, 10), (-38, 10)], PAL["teal"], w=3.5, seed=seed + 1, boil=0.6, n=3)
        cv.drawRect(skia.Rect.MakeLTRB(-26, -38, 22, 2), paint(SCREEN))
        dots(cv, [(-12, -22), (8, -22)], 4, PHOS)
        line(cv, [(-12, -10), (-2, -5), (8, -10)], 3, PHOS, seed=seed + 2, boil=0.3, n=3)
        blob(cv, [(-24, 14), (24, 14), (30, 80), (-30, 80)], PAL["magenta"], w=3.5, seed=seed + 3, boil=0.6, n=3)
        from .letters import paint_text
        paint_text(cv, "ME!", 80, -40, font="bangers", size=34, fill=PAL["yellow"], ink_w=0, shadow=None, seed=seed + 4, streaks=False)
        return
    if face == "grid":                                  # the realisation: an infinite wall of screens on his own screen
        for gy in range(-3, 4):
            for gx in range(-5, 6):
                x0, y0 = gx * 26 - 11, gy * 24 - 10
                k = hsh(gx * 7.1 + gy * 3.3 + core.D * 0.05)
                c = mix(PHOS, (90, 120, 255) if k > 0.5 else (255, 120, 200), 0.35 + 0.3 * k)
                cv.drawRect(skia.Rect.MakeLTRB(x0, y0, x0 + 22, y0 + 19), paint(c, 120))
                cv.drawRect(skia.Rect.MakeLTRB(x0 + 7, y0 + 6, x0 + 15, y0 + 13), paint((10, 20, 30), 160))
        face = "normal"
    for side, key in ((-1, "blinkL"), (1, "blinkR")):
        ex, ey = side * 52, -18
        bl = float(np.clip(P[key], 0, 1))
        if face == "spiral":
            pts = [(ex + (3 + t * 2.2) * math.cos(t + core.D * 0.6), ey + (3 + t * 2.2) * math.sin(t + core.D * 0.6)) for t in np.linspace(0, 14, 40)]
            brush(cv, np.array(pts), 4.0, PHOS, seed=seed + side, taper=(0.1, 0.1))
            continue
        if face == "x":
            line(cv, [(ex - 18, ey - 18), (ex + 18, ey + 18)], 6, PHOS, seed=seed + side, boil=0.8, n=2)
            line(cv, [(ex + 18, ey - 18), (ex - 18, ey + 18)], 6, PHOS, seed=seed + side + 5, boil=0.8, n=2)
            continue
        if bl > 0.85:
            line(cv, [(ex - 26, ey), (ex, ey + 8), (ex + 26, ey)], 6, PHOS, seed=seed + side, boil=0.8, n=4)
        else:
            ry = 30 * (1 - bl * 0.9)
            Pts = cr_closed(jit(ell(ex, ey, 26, ry, n=10), 0.8, seed + 10 + side), 6)
            cv.drawPath(poly_path(Pts), paint(PHOS, 60))
            brush(cv, Pts, 5.0, PHOS, closed=True, seed=seed + 12 + side)
            pr = 11 * P["pupil"]
            px, py = ex + P["px"] * 10, ey + P["py"] * min(10, ry * 0.4)
            if face == "heart":
                hp = [(px, py + pr), (px - pr * 1.3, py - pr * 0.2), (px - pr * 0.6, py - pr * 1.1), (px, py - pr * 0.4),
                      (px + pr * 0.6, py - pr * 1.1), (px + pr * 1.3, py - pr * 0.2)]
                cv.drawPath(poly_path(cr_closed(hp, 4)), paint(PAL["hotpink"]))
            else:
                cv.drawPath(poly_path(cr_closed(ell(px, py, pr, pr * min(1, ry / 26), n=8), 4)), paint(PHOS))
        by = ey - 48 - P["browL" if side < 0 else "browR"] * 16
        ang = P["brow_ang"] * 10
        line(cv, [(ex - side * 26, by + side * 0 + ang * (1 if side < 0 else 1) * 0), (ex + side * 24, by - ang)], 6, PHOS,
             seed=seed + 20 + side, boil=0.8, n=3, taper=(0.2, 0.2))
    cv.save(); cv.translate(0, 46)
    _host_mouth(cv, P["vis"], P["mo"], P["smile"], seed + 40)
    cv.restore()


def _tv_head(cv, P, seed):
    sw, sh = 236.0, 168.0
    for side, key in ((-1, "antL"), (1, "antR")):
        dx, dy = P[key]
        base = np.array([side * 20.0, -126.0])
        tip = base + np.array([side * 92 + dx, -150 + dy])
        line(cv, [base, (base + tip) / 2 + np.array([dx * 0.2, 0]), tip], 6.0, (200, 200, 220), seed=seed + 60 + side, boil=0.9,
             n=6, taper=(0, 0))
        blob(cv, ell(tip[0], tip[1], 11, 11, n=7), PAL["orange"], w=4, seed=seed + 62 + side, boil=0.6)
    blob(cv, ell(0, -126, 34, 16, n=8), CASE_SH, w=5, seed=seed + 64, boil=0.8)
    case = [(-166, -116), (166, -116), (176, -40), (172, 96), (150, 118), (-150, 118), (-172, 96), (-176, -40)]

    def sh(c):
        c.drawPath(poly_path([(110, -130), (190, -130), (190, 130), (96, 130)]), paint(CASE_SH))
        stipple(c, CASE_SH, (-180, -130, 190, 130), spacing=12, r=1.8, seed=seed,
                fn=lambda X, Y: np.clip((X - 40) / 90, 0, 1))
    blob(cv, case, CASE, w=6.5, seed=seed, boil=1.2, n=5, shade=sh)
    for k in range(2):                                   # knobs
        kx, ky = 142, -54 + k * 64
        blob(cv, ell(kx, ky, 15, 15, n=8), PAL["orange"], w=4, seed=seed + 70 + k, boil=0.6)
        line(cv, [(kx, ky), (kx + 9 * math.cos(core.D * 0.3 + k), ky + 9 * math.sin(core.D * 0.3 + k))], 3.5, seed=seed + 72 + k, boil=0.3, n=2)
    for k in range(4):
        line(cv, [(122 + k * 9, 70), (122 + k * 9, 100)], 3.0, seed=seed + 80 + k, boil=0.5, n=2, taper=(0, 0))
    scr = [(-140, -96), (96, -96), (104, -10), (96, 92), (-140, 92), (-150, -2)]
    Ps = cr_closed(jit(scr, 0.9, seed + 5), 6)
    spath = poly_path(Ps)
    cv.drawPath(spath, paint(SCREEN))
    cv.save(); cv.clipPath(spath, doAntiAlias=True)
    cv.drawPath(poly_path(cr_closed(ell(-22, -2, 116, 86, n=12), 4)), paint((26, 60, 80)))
    cv.save(); cv.translate(-22, -4)
    g = P["glitch"]
    if g > 0.05:
        cv.translate((hsh(core.D * 3.1) - 0.5) * 24 * g, 0)
    _screen_face(cv, P, seed + 200, sw, sh)
    cv.restore()
    for k in range(-100, 100, 7):                         # scanlines
        cv.drawRect(skia.Rect.MakeLTRB(-160, k, 110, k + 2.4), paint((0, 0, 0), 70))
    roll = (core.D * 11) % 260 - 130
    cv.drawRect(skia.Rect.MakeLTRB(-160, roll, 110, roll + 18), paint(PHOS, 22 + int(60 * g)))
    if g > 0.2:
        for k in range(int(6 * g)):
            yy = -90 + hsh(core.D * 1.7 + k) * 180
            cv.drawRect(skia.Rect.MakeLTRB(-160, yy, 110, yy + 4 + 8 * hsh(k + core.D)), paint(mix(PHOS, PAL["magenta"], hsh(k)), 150))
    cv.drawPath(poly_path(cr_closed([(-120, -84), (-60, -90), (-110, -40)], 3)), paint((255, 255, 255), 38))
    cv.restore()
    brush(cv, Ps, 6.0, closed=True, seed=seed + 6)


def head_anchor(P):
    """Local position of the TV centre (after lean) — for props / effects that ride on the host's head."""
    hip = P.get("hip", 0.0)
    lean = math.radians(P.get("lean", 0.0))
    x0, y0 = hip, HEAD_Y + P.get("head_dy", 0.0)
    dx, dy = x0 - hip, y0 + 186
    return hip + dx * math.cos(lean) - dy * math.sin(lean), -186 + dx * math.sin(lean) + dy * math.cos(lean)


def _host_legs(cv, P, seed):
    hip = P["hip"]
    for side in (-1, 1):
        x0 = hip * 0.8 + side * 34
        xb = side * 40
        ctrl = [(x0 - 30, -176), (x0 + 30, -176), (xb + 27, -30), (xb - 27, -30)]
        blob(cv, ctrl, TROU, w=5.5, seed=seed + 100 + side * 7, boil=1.0, n=4,
             shade=lambda c, x0=x0, xb=xb, side=side: c.drawPath(poly_path([(x0 + side * 4, -190), (x0 + side * 40, -190), (xb + side * 40, 0), (xb + side * 6, 0)]), paint(TROU_SH)))
        shoe = [(xb - side * 26, -36), (xb + side * 30, -36), (xb + side * 56, -14), (xb + side * 50, 2), (xb - side * 30, 2)]
        blob(cv, shoe, (30, 22, 44), w=5.0, seed=seed + 120 + side * 5, boil=0.9, n=5)
        line(cv, [(xb + side * 6, -28), (xb + side * 30, -20)], 4.0, (255, 255, 255), seed=seed + 125 + side, boil=0.5, n=3, a=150)


def _host_arm(cv, sx, sy, a_sh, a_el, seed):
    (ex, ey), (wx, wy), fdir = arm_points(sx, sy, a_sh, a_el, 100, 96)
    pts = cr_open(jit([(sx, sy), (ex, ey), (wx, wy)], 1.1, seed), 14)
    path = open_path(pts)
    cv.drawPath(path, paint(INK, stroke=27 + 9))
    cv.save(); cv.translate(1.4, 1.0); cv.drawPath(path, paint(SUIT, stroke=27)); cv.restore()
    sh = pts[: max(3, int(len(pts) * 0.35))]
    cv.save(); cv.translate(4.0, 3.0)
    cv.drawPath(open_path(sh), paint(SUIT_SH, 120, stroke=8))
    cv.restore()
    return wx, wy, fdir


def draw_host(cv, P, seed=3000):
    p = dict(HOST_DEFAULTS); p.update(P); P = p
    s = float(P["s"])
    old = core.INKMUL
    core.INKMUL = old / max(s, 0.15) ** 0.5
    try:
        cv.save()
        cv.translate(P["x"], P["y"])
        cv.scale(s, s)
        hip = P["hip"]
        if P["legs"]:
            _host_legs(cv, P, seed)
        cv.save()
        cv.rotate(P["lean"], hip, -186)
        br = 1 + 0.012 * math.sin(P["breath"] * 2 * math.pi)
        # the cable neck (behind the jacket and the set) follows the head
        tilt = math.radians(P["head_tilt"])
        hx, hy = hip, HEAD_Y + P["head_dy"]
        bx, by = hx - math.sin(tilt) * 110 * HEAD_S, hy + math.cos(tilt) * 110 * HEAD_S
        neck = [(hip, -370), (hip + (bx - hip) * 0.4 + 6, (by - 370) * 0.5 - 185), (bx, by)]
        line(cv, neck, 34, INK, seed=seed + 150, boil=0.8, n=6, taper=(0, 0), var=0.05)
        cv.save(); cv.translate(1.2, 0.8)
        line(cv, neck, 24, NECK, seed=seed + 150, boil=0.8, n=6, taper=(0, 0), var=0.05)
        cv.restore()
        line(cv, [(hip + 5, -380), (bx + 5 - math.sin(tilt) * 4, by + 4)], 4.0, (90, 84, 140), seed=seed + 151, boil=0.6, n=3, taper=(0.2, 0.2), a=150)
        # jacket
        ctrl = np.array([(-28, -398), (-80, -394), (-102, -372), (-100, -300), (-92, -220), (-98, -150), (-40, -140),
                         (40, -140), (98, -150), (92, -220), (100, -300), (102, -372), (80, -394), (28, -398)], float)
        ctrl[:, 0] = ctrl[:, 0] * br + hip
        ctrl[:, 1] = -150 + (ctrl[:, 1] + 150) * br

        def jshade(c):
            c.drawPath(poly_path(cr_closed([(44 + hip, -392), (120 + hip, -380), (120 + hip, -130), (52 + hip, -130), (64 + hip, -260)], 5)), paint(SUIT_SH))
            stipple(c, SUIT_SH, (-110 + hip, -400, 110 + hip, -130), spacing=13, r=1.6, seed=seed + 9,
                    fn=lambda X, Y: np.clip(((X - hip) - 10) / 70, 0, 1) * 0.8)
        blob(cv, ctrl, SUIT, w=6.0, seed=seed + 200, boil=1.3, n=7, shade=jshade)
        vy = -262 + 6 * (br - 1) * 100
        blob(cv, [(hip - 24, -394), (hip + 24, -394), (hip, vy)], SHIRT, w=4.0, seed=seed + 210, boil=0.8, n=3)
        for side in (-1, 1):                                      # lapels with yellow piping
            lap = [(hip + side * 24, -394), (hip + side * 62, -390), (hip + side * 54, -352), (hip + side * 38, -330), (hip + side * 4, vy + 4)]
            blob(cv, lap, LAPEL, w=4.0, seed=seed + 220 + side, boil=0.9, n=4)
            line(cv, [(hip + side * 58, -384), (hip + side * 50, -350), (hip + side * 34, -326), (hip + side * 8, vy - 6)], 3.6, PIPING,
                 seed=seed + 226 + side, boil=0.6, n=5, taper=(0.1, 0.1))
        blob(cv, ell(hip, vy + 14, 7, 7, n=7), PAL["gold"], w=3.0, seed=seed + 230, boil=0.4)
        blob(cv, ell(hip, vy + 70, 6, 6, n=7), PAL["gold"], w=3.0, seed=seed + 231, boil=0.4)
        line(cv, [(hip + 70, -254), (hip + 92, -256)], 3.0, seed=seed + 232, boil=0.5, n=2)       # pocket
        # bowtie
        bty = -386
        for side in (-1, 1):
            blob(cv, [(hip + side * 6, bty), (hip + side * 44, bty - 20), (hip + side * 48, bty + 2), (hip + side * 42, bty + 20)],
                 PIPING, w=4.0, seed=seed + 240 + side, boil=0.7, n=3)
        blob(cv, ell(hip, bty, 10, 10, n=7), PAL["orange"], w=3.5, seed=seed + 244, boil=0.5)
        if P.get("mic"):
            blob(cv, ell(hip + 46, -352, 8, 10, n=7), (40, 40, 50), w=3.0, seed=seed + 246, boil=0.4)
        # head
        cv.save()
        cv.translate(hx, hy)
        cv.rotate(P["head_tilt"])
        sq = P["squash"]
        cv.scale(HEAD_S * (1 + (1 - sq) * 0.6), HEAD_S * sq)
        _tv_head(cv, P, seed + 300)
        cv.restore()
        # arms + gloves
        hands = {}
        for side, pre in ((-1, "aL"), (1, "aR")):
            sx, sy = side * 74 + hip, -370
            wx, wy, fdir = _host_arm(cv, sx, sy, P[pre + "_sh"], P[pre + "_el"], seed + 400 + side * 20)
            hands[pre] = (wx, wy, fdir + P[pre + "_hand"])
        if P["prop"] is not None and callable(P["prop"]):
            P["prop"](cv, hands)
        for side, pre in ((-1, "aL"), (1, "aR")):
            wx, wy, ang = hands[pre]
            _hand(cv, wx, wy, ang, P[pre + "_pose"], 1 if side < 0 else -1, seed + 500 + side * 30, rgb=GLOVE, cuff=GLOVE)
        cv.restore()
        cv.restore()
        return hands
    finally:
        core.INKMUL = old


# ---------------------------------------------------------------- extras
def ai_blob(cv, x, y, s, phase=0.0, seed=5000, rgb=None, look=(0.0, 0.0), mouth=0.0):
    """A friendly gooey AI: a wobbling gel drop with one big eye and a little antenna."""
    rgb = rgb or PAL["acid"]
    pts = []
    for k in range(12):
        a = k / 12 * 2 * math.pi
        r = 1 + 0.07 * math.sin(a * 3 + phase * 2.3) + 0.05 * math.sin(a * 5 - phase * 3.1)
        yk = 1.0 if math.sin(a) < 0 else 0.82
        pts.append((x + 110 * s * r * math.cos(a), y - 90 * s + 110 * s * r * yk * math.sin(a)))
    blob(cv, pts, rgb, w=6, seed=seed, boil=1.2, n=6,
         shade=lambda c: c.drawPath(poly_path(ell(x + 50 * s, y - 40 * s, 90 * s, 80 * s, n=12)), paint(mix(rgb, INK, 0.25))))
    line(cv, [(x, y - 196 * s), (x + 10 * s, y - 240 * s)], 4, seed=seed + 1, boil=0.6, n=3)
    dots(cv, [(x + 10 * s, y - 244 * s)], 9 * s, PAL["magenta"])
    ex, ey = x + look[0] * 14 * s, y - 110 * s + look[1] * 10 * s
    blob(cv, ell(x, y - 110 * s, 44 * s, 46 * s, n=10), PAL["white"], w=5, seed=seed + 2, boil=0.8)
    dots(cv, [(ex, ey)], 22 * s, PAL["teal"])
    dots(cv, [(ex, ey)], 11 * s, INK)
    dots(cv, [(ex - 7 * s, ey - 8 * s)], 4 * s, PAL["white"])
    if mouth > 0.05:
        blob(cv, ell(x, y - 40 * s, 22 * s, 8 * s + 16 * s * mouth, n=8), PAL["mouth"], w=4, seed=seed + 3, boil=0.6)
    else:
        line(cv, [(x - 20 * s, y - 44 * s), (x, y - 36 * s), (x + 20 * s, y - 44 * s)], 4, seed=seed + 4, boil=0.6, n=3)


def alien(cv, x, y, s, yawn=0.0, blink=0.0, press=0.0, seed=5500, chew=0.0, look=(0.0, 0.0), rgb=None):
    """A bored grey-green alien at the controls (big head, black almond eyes, a robe). y = bottom."""
    rgb = rgb or (150, 220, 120)
    blob(cv, [(x - 150 * s, y), (x - 120 * s, y - 230 * s), (x + 120 * s, y - 230 * s), (x + 150 * s, y)], PAL["lilac"], w=6, seed=seed, boil=1.0, n=4,
         shade=lambda c: c.drawRect(skia.Rect.MakeLTRB(x + 40 * s, y - 260 * s, x + 200 * s, y), paint(mix(PAL["lilac"], INK, 0.2))))
    line(cv, [(x, y - 230 * s), (x, y)], 4, seed=seed + 1, boil=0.6, n=3)
    hx, hy = x, y - 400 * s
    head = [(hx, hy - 170 * s), (hx + 130 * s, hy - 110 * s), (hx + 140 * s, hy - 10 * s), (hx + 70 * s, hy + 120 * s), (hx, hy + 150 * s),
            (hx - 70 * s, hy + 120 * s), (hx - 140 * s, hy - 10 * s), (hx - 130 * s, hy - 110 * s)]
    blob(cv, head, rgb, w=6.5, seed=seed + 2, boil=1.2, n=6,
         shade=lambda c: c.drawPath(poly_path(ell(hx + 70 * s, hy, 90 * s, 160 * s, n=12)), paint(mix(rgb, INK, 0.2))))
    for side in (-1, 1):
        ex, ey = hx + side * 62 * s, hy - 4 * s
        eye = [(ex - side * 50 * s, ey + 14 * s), (ex, ey - 26 * s), (ex + side * 52 * s, ey - 22 * s), (ex + side * 30 * s, ey + 24 * s)]
        if blink > 0.8:
            line(cv, [(ex - 40 * s, ey + 4 * s), (ex + 40 * s, ey + 4 * s)], 6, seed=seed + 5 + side, boil=0.6, n=2)
        else:
            blob(cv, eye, (14, 10, 22), w=4, seed=seed + 5 + side, boil=0.8, n=4)
            dots(cv, [(ex + look[0] * 14 * s - 8 * s, ey - 6 * s + look[1] * 6 * s)], 7 * s, PAL["white"])
    mo = max(yawn, chew * abs(math.sin(core.D * 0.7)))
    if mo > 0.05:
        blob(cv, ell(hx, hy + 90 * s, 22 * s, 8 * s + 34 * s * mo, n=8), PAL["mouth"], w=4, seed=seed + 9, boil=0.6)
    else:
        line(cv, [(hx - 18 * s, hy + 92 * s), (hx + 18 * s, hy + 90 * s)], 4, seed=seed + 9, boil=0.6, n=2)
    for side in (-1, 1):
        hx2 = x + side * 120 * s
        hy2 = y - 120 * s + press * 30 * s * (1 if side > 0 else 0)
        tube(cv, [(x + side * 110 * s, y - 210 * s), (x + side * 170 * s, y - 160 * s), (hx2, hy2)], 22 * s, rgb, w=4, seed=seed + 20 + side)
        _hand(cv, hx2, hy2, 90 + side * 10, "point" if side > 0 else "open", 1 if side < 0 else -1, seed + 30 + side, rgb=rgb)


def agent(cv, x, y, s, phase=0.0, rgb=None, seed=5800, look=0.0):
    """A tiny sim person on a walk cycle (bean body, ball head, two dot eyes). y = feet."""
    rgb = rgb or PAL["orange"]
    st = math.sin(phase * 2 * math.pi)
    bob = abs(math.cos(phase * 2 * math.pi)) * 4 * s
    for side in (-1, 1):
        fx = x + side * 8 * s + st * side * 12 * s
        line(cv, [(x + side * 7 * s, y - 34 * s - bob), (fx, y)], 6 * s + 1.5, INK, seed=seed + side, boil=0.6, n=2, taper=(0, 0))
    blob(cv, [(x - 18 * s, y - 34 * s - bob), (x - 16 * s, y - 80 * s - bob), (x + 16 * s, y - 80 * s - bob), (x + 18 * s, y - 34 * s - bob)], rgb,
         w=3.5, seed=seed + 3, boil=0.8, n=3)
    hy = y - 104 * s - bob
    blob(cv, ell(x, hy, 22 * s, 22 * s, n=8), PAL["peach"], w=3.5, seed=seed + 4, boil=0.7)
    dots(cv, [(x - 7 * s + look * 4 * s, hy - 2 * s), (x + 7 * s + look * 4 * s, hy - 2 * s)], 2.8 * s + 0.5, INK)
    for side in (-1, 1):
        line(cv, [(x + side * 16 * s, y - 74 * s - bob), (x + side * 26 * s - st * side * 8 * s, y - 46 * s - bob)], 5 * s + 1.2, INK,
             seed=seed + 6 + side, boil=0.6, n=2, taper=(0, 0))


def cosmic_hand(cv, x, y, s, ang=0.0, seed=6000, pose="hold", sleeve=None):
    """A giant hand reaching in (from a starry sleeve if `sleeve` colour is given). (x, y) = wrist, ang = direction."""
    cv.save()
    cv.translate(x, y)
    cv.scale(s * 3.2, s * 3.2)
    old = core.INKMUL
    core.INKMUL = old / max(s * 3.2, 0.2) ** 0.6
    if sleeve is not None:
        r = math.radians(ang + 180)
        d = np.array([math.cos(r), math.sin(r)])
        n = np.array([-d[1], d[0]])
        pts = [n * 26 + d * 4, n * 34 + d * 260, -n * 34 + d * 260, -n * 26 + d * 4]
        blob(cv, pts, sleeve, w=5, seed=seed + 1, boil=1.0, n=3,
             shade=lambda c: [dots(c, [tuple(d * (40 + 40 * k) + n * (12 * math.sin(k * 2.1)))], 2.2, PAL["yellow"]) for k in range(5)])
        line(cv, [n * 30 + d * 10, -n * 30 + d * 10], 4, seed=seed + 2, boil=0.6, n=2)
    _hand(cv, 0, 0, ang, pose, 1, seed + 5, rgb=PAL["cream"])
    core.INKMUL = old
    cv.restore()


def gauge(cv, x, y, s, value, seed=7000, face=True):
    """Probability meter with a face. value 0..1 sweeps the needle."""
    blob(cv, [(x - 150 * s, y), (x - 150 * s, y - 60 * s), (x, y - 160 * s), (x + 150 * s, y - 60 * s), (x + 150 * s, y)], PAL["cream"], w=6,
         seed=seed, boil=1.0, n=5)
    for k, col in enumerate((PAL["red"], PAL["orange"], PAL["yellow"], PAL["acid"])):
        a0 = math.pi + k * math.pi / 4
        pts = [(x + 120 * s * math.cos(a0 + u * math.pi / 4), y - 10 * s + 120 * s * math.sin(a0 + u * math.pi / 4)) for u in np.linspace(0, 1, 6)]
        brush(cv, np.array(pts), 18 * s, col, taper=(0.02, 0.02), seed=seed + k)
    a = math.pi + float(np.clip(value, 0, 1)) * math.pi
    line(cv, [(x, y - 10 * s), (x + 104 * s * math.cos(a), y - 10 * s + 104 * s * math.sin(a))], 7, PAL["magenta"], seed=seed + 9, boil=0.5, n=2,
         taper=(0, 0.6))
    dots(cv, [(x, y - 10 * s)], 12 * s, INK)
    if face:
        for side in (-1, 1):
            dots(cv, [(x + side * 36 * s, y - 56 * s)], 7 * s, INK)
        line(cv, [(x - 20 * s, y - 34 * s), (x, y - 26 * s), (x + 20 * s, y - 34 * s)], 4, seed=seed + 12, boil=0.6, n=3)


def melting_clock(cv, x, y, s, phase=0.0, seed=8000):
    """A Dali clock drooping over an invisible edge: yellow face, drip, hands spinning."""
    sag = 0.5 + 0.5 * math.sin(phase)
    pts = [(x - 80 * s, y - 40 * s), (x - 20 * s, y - 70 * s), (x + 60 * s, y - 60 * s), (x + 86 * s, y - 10 * s), (x + 70 * s, y + 40 * s),
           (x + 40 * s, y + 70 * s + 40 * s * sag), (x + 20 * s, y + 130 * s + 50 * s * sag), (x, y + 70 * s), (x - 60 * s, y + 46 * s), (x - 90 * s, y + 10 * s)]
    blob(cv, pts, PAL["yellow"], w=6, seed=seed, boil=1.1, n=6,
         shade=lambda c: c.drawPath(poly_path(ell(x + 40 * s, y + 40 * s, 60 * s, 70 * s, n=10)), paint(PAL["gold"])))
    blob(cv, ell(x - 4 * s, y + 2 * s, 56 * s, 50 * s, n=12), PAL["white"], w=4.5, seed=seed + 1, boil=0.9)
    for k in range(12):
        a = k / 12 * 2 * math.pi
        dots(cv, [(x - 4 * s + 44 * s * math.cos(a), y + 2 * s + 40 * s * math.sin(a))], 2.6 * s + 0.6, INK)
    for L, sp in ((28, 1.0), (40, 12.0)):
        a = phase * sp
        line(cv, [(x - 4 * s, y + 2 * s), (x - 4 * s + L * s * math.sin(a), y + 2 * s - L * s * math.cos(a))], 4.5 if L < 30 else 3.5,
             seed=seed + 3 + L, boil=0.4, n=2, taper=(0, 0.3))
    dots(cv, [(x - 4 * s, y + 2 * s)], 5 * s, PAL["red"])
