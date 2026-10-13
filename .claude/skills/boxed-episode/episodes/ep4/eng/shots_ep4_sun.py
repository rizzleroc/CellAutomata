"""BOXED ep4 'THE CAVE' -- owner `sun`: T030_adjust (his eyes adjust: shadows -> reflections -> the real things ->
moon and stars -> one morning) and T031_sun (the sun rises: the show's ringed planet, 'Oh. Hey, Gary.', '...Whoa.',
seasons and years, the colour of everything, and the chain sun -> light -> cave -> fire -> shadows).

Gary here is drawn by `_gary` (an extended copy of shots_ep2.eyeball_creature in local units, scaled with ink
compensation) because these shots need a gaze direction, squint lids, tears, an iris reflection and new arm poses.
"""
from contextlib import contextmanager
from .shots_ep4_base import *
from .zee import _mouth as _zmouth, _hand

GS = 4400                                                         # Gary's seed (same as the base gary())


# ===================================================================== small utilities
def _k(t, a, b):
    """0..1 smoothstep of t between a and b."""
    if b <= a:
        return 1.0 if t >= a else 0.0
    return ease((t - a) / (b - a))


def _lin(cv, p0, p1, cols, pos=None, rect=None, a=255, blend=None):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(*p0), skia.Point(*p1)], [core.C(c, a) for c in cols], pos))
    if blend is not None:
        p.setBlendMode(blend)
    cv.drawRect(rect or R(-600, -600, W + 600, H + 600), p)


def _glow(cv, x, y, r, rgb, a, mid=0.35, blend=None, mida=0.35):
    if r < 1 or a <= 0:
        return
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(float(x), float(y)), float(r),
                                               [core.C(rgb, int(min(255, a))), core.C(rgb, int(min(255, a * mida))), core.C(rgb, 0)], [0.0, mid, 1.0]))
    if blend is not None:
        p.setBlendMode(blend)
    cv.drawCircle(float(x), float(y), float(r), p)


def _wash(cv, rgb, a, blend=None):
    if a > 0:
        p = paint(rgb, int(min(255, a)))
        if blend is not None:
            p = skia.Paint(AntiAlias=True, Color=core.C(rgb, int(min(255, a))))
            p.setBlendMode(blend)
        cv.drawRect(R(-600, -600, W + 600, H + 600), p)


def _rays(cv, x, y, r0, r1, n, rot_deg, rgb, a, width=0.5, blend=None, wob=0.0, t=0.0, a_end=0):
    """n tapered wedges from radius r0 to r1 that fade out with distance (one path, one radial shader)."""
    if a <= 0:
        return
    path = skia.Path()
    for k in range(n):
        a0 = math.radians(rot_deg) + k * 2 * math.pi / n
        half = math.pi / n * width * (1 + wob * math.sin(t * 1.7 + k * 2.3))
        path.moveTo(x + r0 * math.cos(a0 - half * 0.25), y + r0 * math.sin(a0 - half * 0.25))
        path.lineTo(x + r1 * math.cos(a0 - half), y + r1 * math.sin(a0 - half))
        path.lineTo(x + r1 * math.cos(a0 + half), y + r1 * math.sin(a0 + half))
        path.lineTo(x + r0 * math.cos(a0 + half * 0.25), y + r0 * math.sin(a0 + half * 0.25))
        path.close()
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(float(x), float(y)), float(r1), [core.C(rgb, int(a)), core.C(rgb, int(a)), core.C(rgb, a_end)],
                                               [0.0, max(0.01, r0 / r1), 1.0]))
    if blend is not None:
        p.setBlendMode(blend)
    cv.drawPath(path, p)


@contextmanager
def _tint(cv, rgb, k, bounds=None):
    """Everything drawn inside is pulled toward colour rgb by k (0..1) -- night, silhouettes, warm light."""
    if k <= 0.003:
        yield
        return
    m = [1 - k, 0, 0, 0, k * rgb[0] / 255.0, 0, 1 - k, 0, 0, k * rgb[1] / 255.0, 0, 0, 1 - k, 0, k * rgb[2] / 255.0, 0, 0, 0, 1, 0]
    cv.saveLayer(bounds, skia.Paint(ColorFilter=skia.ColorFilters.Matrix(m)))
    try:
        yield
    finally:
        cv.restore()


@contextmanager
def _xf(cv, x, y, s, rot_deg=0.0):
    """Local frame at (x, y) scaled by s (pen weight compensated like sets.Cam)."""
    cv.save()
    cv.translate(x, y)
    if rot_deg:
        cv.rotate(rot_deg)
    cv.scale(s, s)
    old = core.INKMUL
    core.INKMUL = old / max(s, 0.05) ** 0.5
    try:
        yield
    finally:
        core.INKMUL = old
        cv.restore()


@contextmanager
def _cam(cv, cx, cy, z, rot_deg=0.0):
    """World camera: world point (cx, cy) lands at the frame centre, zoom z."""
    cv.save()
    cv.translate(W / 2, H / 2)
    if rot_deg:
        cv.rotate(rot_deg)
    cv.scale(z, z)
    cv.translate(-cx, -cy)
    old = core.INKMUL
    core.INKMUL = old / max(z, 0.05) ** 0.5
    try:
        yield
    finally:
        core.INKMUL = old
        cv.restore()


def _label(cv, text, x, y, t, t0, size=96, fill=None, seed=0, font="shrik", shadow_rgb=None, fills=None, dur=0.35, a=255):
    """A hand-painted word that springs in (scale pop about its centre)."""
    if t < t0:
        return
    k = pop(t, t0, dur)
    cv.save()
    cv.translate(x, y - size * 0.35)
    cv.rotate(-4 + 8 * float(hsh(seed)) + 3 * math.sin(t * 2.1 + seed))
    cv.scale(k, k)
    paint_text(cv, text, 0, size * 0.35, font=font, size=size, fill=fill or P_["yellow"], fills=fills, ink_w=6 if size > 70 else 4.5, shadow=(7, 7),
               shadow_rgb=shadow_rgb or INK, seed=seed, wobble=1.6, a=a)
    cv.restore()


def _sparkles(cv, t, box, n, seed, cols=None, r=(6, 16), a=255):
    x0, y0, x1, y1 = box
    cols = cols or [P_["white"], P_["yellow"], P_["cream"]]
    for k in range(n):
        ph = (t * (0.6 + 0.5 * float(hsh(seed + k * 1.3))) + float(hsh(seed + k * 2.9))) % 1.0
        if ph > 0.8:
            continue
        sx = x0 + (x1 - x0) * float(hsh(seed + k * 7.7))
        sy = y0 + (y1 - y0) * float(hsh(seed + k * 4.3))
        rr = (r[0] + (r[1] - r[0]) * float(hsh(seed + k * 3.1))) * math.sin(ph / 0.8 * math.pi)
        if rr > 1.5:
            sparkle(cv, sx, sy, rr, cols[k % len(cols)], w=2.0, seed=seed + k, a=a)


# ===================================================================== GARY (extended)
def _lid_pts(yb, lid, Rw=150.0):
    """Upper lid: at 0 the resting beret-like cap, closing to a U-shaped lid line below the iris at 1."""
    phi = math.radians(7.7 - 26.0 * lid)
    yc = yb - 124 + 190 * lid
    rr = Rw + 3
    xs, ys = rr * math.cos(phi), yb - rr * math.sin(phi)
    pts = []
    for k in range(7):
        a = (math.pi - phi) - (math.pi - 2 * phi) * k / 6
        pts.append((rr * math.cos(a), yb - rr * math.sin(a)))
    ym = yc + (ys - yc) * (0.42 - 0.3 * lid)
    pts += [(xs * 0.6, ym), (0.0, yc), (-xs * 0.6, ym)]
    return pts


def _low_pts(yb, low, Rw=150.0):
    psi = math.radians(14 + 10 * low)
    yc = yb + Rw - 150 * low
    rr = Rw + 3
    xs, ys = rr * math.cos(psi), yb + rr * math.sin(psi)
    pts = []
    for k in range(7):
        a = psi + (math.pi - 2 * psi) * k / 6
        pts.append((rr * math.cos(a), yb + rr * math.sin(a)))
    ym = yc + (ys - yc) * 0.42
    pts += [(-xs * 0.55, ym), (0.0, yc), (xs * 0.55, ym)]
    return pts


ARMS = {   # pose: (elbow, hand, hand angle, hand pose) for the screen-LEFT arm (local units); the right arm mirrors x
    "hang": ((-150, 250), (-140, 330), 100, "open"),
    "rest": ((-175, 255), (-205, 352), 115, "flat"),
    "up": ((-235, 40), (-240, -150), -100, "spread"),
    "clasp": ((-170, 300), (-34, 252), -15, "open"),
    "cheek": ((-230, 250), (-158, 92), -62, "open"),
    "pillow": ((-235, 10), (-118, -112), -25, "open"),
    "reach": ((-235, 110), (-330, -20), -140, "open"),
    "point": ((-235, 120), (-350, 40), -165, "point"),
    "shield": ((-262, 20), (-128, -86), -12, "flat"),
    "fist": ((-210, 150), (-200, 30), -95, "fist"),
}


def _garm(cv, side, pose, t, seed, wave_k=1.0):
    sh = (side * 104.0, 190.0)
    if pose == "wave":
        hx, hy = side * (205 + 16 * math.sin(t * 8)), -100.0
        el = (side * 200.0, 140.0)
        ang = -90 + side * 14 * math.sin(t * 8) if side < 0 else -90 + 14 * math.sin(t * 8)
        pz = "open"
    else:
        (ex, ey), (hx, hy), ang, pz = ARMS.get(pose, ARMS["hang"])
        el = (side * -ex, ey) if side > 0 else (ex, ey)
        hx = -hx if side > 0 else hx
        if side > 0:
            ang = 180 - ang
    tube(cv, [sh, el, (hx, hy)], 22, P_["cream"], w=4.5, seed=seed, boil=0.8, n=8)
    cv.save()
    cv.translate(hx, hy)
    hs = 1.7 if pose == "shield" else 1.15
    cv.scale(hs, hs)
    _hand(cv, 0, 0, ang, pz, 1 if side < 0 else -1, seed + 2, rgb=P_["white"])
    cv.restore()


def _gary(cv, x, y, s, t, look=(0.0, 0.0), lid=0.0, low=0.0, pupil=None, loud=0.0, mouth=None, arms=("hang", "hang"), tears=0.0,
          refl=None, light=None, view="front", seed=GS, bob=1.0, body=True, shine=0.0, squint_lines=0.0, rot=0.0, tear_rate=0.55):
    """Gary the eyeball (x, y = centre of his eye, scale s). look = gaze (-1..1, x right / y down) with a foreshortened
    iris; lid / low = upper / lower lid (0 open .. 1 shut); pupil = pupil radius / iris radius; loud = talking;
    mouth None|'smile'|'o'|'grin'|'flat'|'wobble'|'squint'; arms = (left pose, right pose) from ARMS or 'wave';
    tears 0..1 (wet iris + rolling drops); refl(cv, ex, ey, rx, ry) paints a reflection into the iris; light = (rgb, ang, k)
    a coloured rim light from screen angle ang; view 'front'|'back'."""
    with _xf(cv, x, y, s, rot):
        b = 6 * math.sin(t * 3.1) * bob
        arms = arms or ("hang", "hang")
        if body:
            for side, pose in ((-1, arms[0]), (1, arms[1])):           # arms that go behind the head
                if pose == "pillow":
                    _garm(cv, side, pose, t, seed + 50 + 14 * (side > 0))
            blob(cv, [(-128, 360), (-110, 170), (-55, 112), (55, 112), (110, 170), (128, 360)], P_["cream"], w=5, seed=seed, boil=1.0, n=6,
                 shade=lambda c: ([c.drawRect(R(-140, 232 + k * 46, 140, 250 + k * 46), paint(P_["orange"])) for k in range(3)],
                                  c.drawRect(R(60, 100, 160, 380), paint(P_["cream_sh"], 120))))
            if view == "front":
                paint_text(cv, "G", 0, 300, font="shrik", size=76, fill=P_["red"], ink_w=4, shadow=None, seed=seed + 30, streaks=False)
        Rw = 150.0
        yb = b

        def white_shade(c):
            for k, a in enumerate(np.linspace(0, 6.0, 8)):
                line(c, [(Rw * math.cos(a), yb + Rw * math.sin(a)), (100 * math.cos(a + 0.25), yb + 100 * math.sin(a + 0.25))], 3.5, P_["red"],
                     seed=seed + 10 + k, boil=0.8, n=3)
            cres = skia.Op(_circ(0, yb, Rw + 2), _circ(-22, yb - 26, Rw + 4), skia.PathOp.kDifference_PathOp)
            if cres is not None:
                c.drawPath(cres, paint((236, 214, 214), 150))
            if light is not None:
                rgb, ang, kk = light
                ar = math.radians(ang)
                rim = skia.Op(_circ(0, yb, Rw + 2), _circ(-math.cos(ar) * 34, yb - math.sin(ar) * 34, Rw + 2), skia.PathOp.kDifference_PathOp)
                if rim is not None:
                    c.drawPath(rim, paint(rgb, int(230 * kk)))
                sh2 = skia.Op(_circ(0, yb, Rw + 2), _circ(math.cos(ar) * 60, yb + math.sin(ar) * 60, Rw + 2), skia.PathOp.kDifference_PathOp)
                if sh2 is not None:
                    c.drawPath(sh2, paint(P_["violet"], int(70 * kk)))
        blob(cv, ell(0, yb, Rw, Rw, n=14), P_["white"], w=6, seed=seed + 4, boil=1.2, shade=white_shade)
        if view == "front":
            ir = 66.0
            ox, oy = -4 + look[0] * 78, -22 + look[1] * (64 if look[1] < 0 else 92)
            ex, ey = ox, yb + oy
            dd = math.hypot(ox, oy) / Rw
            sq = math.sqrt(max(0.2, 1 - dd * dd))
            ang = math.degrees(math.atan2(oy, ox)) if dd > 0.02 else 0.0
            pr = (pupil if pupil is not None else 0.42 + 0.22 * min(1.0, loud))
            cv.save()
            cv.clipPath(_circ(0, yb, Rw - 1), doAntiAlias=True)
            blob(cv, ell(ex, ey, ir * sq, ir, n=11, rot=ang), P_["teal"], w=4.5, seed=seed + 5, boil=0.8,
                 shade=lambda c: c.drawPath(poly_path(cr_closed(ell(ex + 10 * sq, ey + 12, ir * 0.8 * sq, ir * 0.75, n=8, rot=ang), 4)), paint(P_["tealdk"])))
            cv.save()
            cv.clipPath(poly_path(cr_closed(ell(ex, ey, ir * sq, ir, n=11, rot=ang), 4)), doAntiAlias=True)
            for k in range(10):                                         # iris fibres
                a = k * 0.628 + 0.2
                cv.drawLine(ex + math.cos(a) * ir * pr * 1.1 * sq, ey + math.sin(a) * ir * pr * 1.1, ex + math.cos(a) * ir * 0.92 * sq,
                            ey + math.sin(a) * ir * 0.92, paint(mix(P_["teal"], P_["mint"], 0.5), 140, stroke=3))
            blob(cv, ell(ex, ey, ir * pr * sq, ir * pr, n=9, rot=ang), INK, w=0, seed=seed + 6, boil=0.5, misreg=(0, 0))
            dots(cv, [(ex - ir * pr * 0.45 - 6, ey - ir * pr * 0.5 - 6)], ir * pr * 0.28 + 3, P_["white"])
            dots(cv, [(ex + ir * 0.42 * sq, ey + ir * 0.4)], 4.5, P_["white"], a=200)
            if refl is not None:
                refl(cv, ex, ey, ir * sq, ir)
            if shine > 0:
                for k in range(3):
                    sparkle(cv, ex + (-30 + 34 * k) * sq, ey - 26 + 18 * (k % 2), (9 + 5 * (k == 1)) * shine, P_["white"], w=2.0, seed=seed + 70 + k)
            cv.restore()
            if tears > 0:                                               # the wet meniscus along the lower iris
                arc = [(ex + ir * sq * math.cos(a), ey + ir * 0.92 * math.sin(a) + 6) for a in np.linspace(0.25, math.pi - 0.25, 9)]
                brush(cv, cr_open(np.array(arc), 4), 10, (150, 230, 255), taper=(0.3, 0.3), seed=seed + 80, a=int(210 * min(1, tears)))
                brush(cv, cr_open(np.array(arc[2:6]) + np.array([0, -3]), 4), 3.5, P_["white"], taper=(0.3, 0.3), seed=seed + 81, a=int(230 * min(1, tears)))
            cv.restore()
            if lid > 0.97:
                blob(cv, _lid_pts(yb, 1.0), P_["violet"], w=5, seed=seed + 7, boil=1.0, n=5)
                line(cv, [(-120, yb + 84), (0, yb + 100), (120, yb + 84)], 5, seed=seed + 8, boil=0.7, n=5)
            else:
                blob(cv, _lid_pts(yb, lid), P_["violet"], w=5, seed=seed + 7, boil=1.0, n=5)
            if low > 0.02:
                blob(cv, _low_pts(yb, low), P_["violet"], w=4.5, seed=seed + 9, boil=0.9, n=5)
            if squint_lines > 0.05:
                for side in (-1, 1):
                    for k in range(3):
                        a0 = math.radians(-25 + 25 * k)
                        r0, r1 = 160, 160 + 34 * squint_lines
                        line(cv, [(side * r0 * math.cos(a0), yb + r0 * math.sin(a0) - 30), (side * r1 * math.cos(a0), yb + r1 * math.sin(a0) - 30)], 4.5,
                             seed=seed + 90 + k + 3 * (side > 0), boil=0.6, n=2, taper=(0.2, 0.4))
            mo = min(1.0, loud * 1.5)
            mx, my = 6 + look[0] * 26, yb + 92 + max(-10.0, look[1] * 26)
            if lid > 0.5 or look[1] > 0.6:
                my += 8
            md = mouth
            if md is None:
                md = "talk" if mo > 0.08 else "smile"
            if md == "talk" and mo > 0.08:
                mh = 5 + 30 * mo
                blob(cv, ell(mx, my + mh * 0.3, 34, mh, n=10), P_["mouth"], w=4.5, seed=seed + 40, boil=0.7,
                     shade=lambda c: blob(c, ell(mx + 4, my + mh * 1.1, 22, mh * 0.6, n=8), P_["tongue"], w=0, seed=seed + 41, boil=0.5, misreg=(0, 0)))
            elif md == "o":
                ro = 12 + 10 * max(mo, 0.3)
                blob(cv, ell(mx, my + 6, ro * 0.85, ro, n=9), P_["mouth"], w=4.5, seed=seed + 43, boil=0.6)
            elif md == "grin":
                blob(cv, [(mx - 44, my - 6), (mx + 44, my - 6), (mx + 30, my + 26), (mx, my + 38), (mx - 30, my + 26)], P_["mouth"], w=4.5, seed=seed + 44, boil=0.7,
                     n=5, shade=lambda c: (c.drawRect(R(mx - 50, my - 12, mx + 50, my + 4), paint(P_["white"])),
                                          c.drawPath(poly_path(cr_closed(ell(mx + 4, my + 32, 22, 12, n=8), 3)), paint(P_["tongue"]))))
            elif md == "flat":
                line(cv, [(mx - 26, my), (mx + 26, my + 1)], 4.5, seed=seed + 45, boil=0.6, n=3, taper=(0.3, 0.3))
            elif md == "wobble":
                line(cv, [(mx - 30, my + 2), (mx - 15, my - 3), (mx, my + 3), (mx + 15, my - 3), (mx + 30, my + 2)], 4.5, seed=seed + 46, boil=0.8, n=4,
                     taper=(0.3, 0.3))
            elif md == "squint":
                line(cv, [(mx - 34, my + 4), (mx - 12, my - 2), (mx + 12, my + 5), (mx + 34, my - 1)], 5, seed=seed + 47, boil=0.8, n=4, taper=(0.3, 0.3))
            else:
                line(cv, [(mx - 30, my - 4), (mx, my + 8), (mx + 30, my - 4)], 4.5, seed=seed + 42, boil=0.6, n=6, taper=(0.3, 0.3))
            if tears > 0:                                               # rolling tears
                for i in range(3):
                    ph = (t * tear_rate + i * 0.37 + float(hsh(seed + i)) * 0.2) % 1.0
                    side = -1 if i % 2 == 0 else 1
                    sx, sy = ex + side * ir * sq * 0.72, ey + ir * 0.62
                    u = ph ** 1.4
                    tx = sx + side * (16 * u + 30 * u * u)
                    ty = sy + 210 * u
                    rr = 9 + 5 * math.sin(ph * math.pi)
                    al = int(255 * min(1.0, tears) * min(1.0, (1 - ph) * 4))
                    blob(cv, [(tx, ty - rr * 2.2), (tx + rr, ty), (tx, ty + rr), (tx - rr, ty)], (160, 230, 255), w=3, seed=seed + 85 + i, boil=0.5, n=4, a=al)
                    dots(cv, [(tx - rr * 0.35, ty - rr * 0.1)], rr * 0.28, P_["white"], a=al)
        else:
            blob(cv, _lid_pts(yb, 0.42), P_["violet"], w=5, seed=seed + 7, boil=1.0, n=5)
        if body:
            for side, pose in ((-1, arms[0]), (1, arms[1])):
                if pose and pose != "pillow":
                    _garm(cv, side, pose, t, seed + 50 + 14 * (side > 0))


def _circ(x, y, r):
    p = skia.Path()
    p.addCircle(float(x), float(y), float(r))
    return p


# ===================================================================== THE SUN (the show's ringed planet)
SUN_BASE = P_["gold"]                                              # matches the sun-planet of the return / out / main-unit shots
SUN_BANDS = [(-0.55, 0.2, P_["yellow"]), (-0.12, 0.16, P_["orange"]), (0.3, 0.22, P_["cream"])]


def _sun_face(cv, x, y, r, t, lids=(0.45, 0.45), look=(0.0, 0.0), brow=0.0, vis="X", mo=0.0, smile=0.4, seed=0, lid_rgb=None, wk=1.0):
    ex, er, ey = r * 0.3, r * 0.2, y - r * 0.12
    iw = max(3.0, r * 0.024)
    c = lid_rgb or mix(P_["orange"], INK, 0.12)
    for side, lv in ((-1, lids[0]), (1, lids[1])):
        cx = x + side * ex
        blob(cv, ell(cx, ey, er, er * 1.08, n=12), P_["white"], w=max(3.0, r * 0.022), seed=seed + 40 + side, boil=0.7)
        pr = er * 0.42
        px, py = cx + look[0] * er * 0.42, ey + look[1] * er * 0.4
        dots(cv, [(px, py)], pr, INK)
        dots(cv, [(px - pr * 0.35, py - pr * 0.4)], pr * 0.3, P_["white"])
        lv = min(1.0, lv)
        if lv > 0.02:
            ly = ey - er * 1.08 + 2 * er * 1.08 * lv + (er * 0.2 if lv > 0.96 else 0)
            lid = [(cx - er * 1.12, ey - er * 1.25), (cx + er * 1.12, ey - er * 1.25), (cx + er * 1.12, ly - er * 0.05), (cx + er * 0.5, ly + er * 0.14),
                   (cx - er * 0.5, ly + er * 0.14), (cx - er * 1.12, ly - er * 0.05)]
            cv.save()
            cv.clipPath(poly_path(cr_closed(ell(cx, ey, er + 1.5, er * 1.08 + 1.5, n=12), 4)), doAntiAlias=True)
            blob(cv, lid, c, w=0, seed=seed + 50 + side, boil=0.4, n=4, misreg=(0, 0))
            cv.restore()
            if lv > 0.96:                                           # shut: a sleepy lash curve
                line(cv, [(cx - er * 1.02, ey + er * 0.1), (cx, ey + er * 0.42), (cx + er * 1.02, ey + er * 0.1)], iw * 1.15, seed=seed + 52 + side, boil=0.5, n=5)
                for k in range(3):
                    bx = cx + side * er * (0.55 + 0.2 * k)
                    line(cv, [(bx, ey + er * (0.3 - 0.06 * k)), (bx + side * er * 0.16, ey + er * (0.56 - 0.05 * k))], iw * 0.6, seed=seed + 56 + k + side,
                         boil=0.4, n=2, taper=(0.2, 0.4))
            else:
                line(cv, [(cx - er * 1.02, ly - er * 0.02), (cx, ly + er * 0.16), (cx + er * 1.02, ly - er * 0.02)], iw, seed=seed + 52 + side, boil=0.5, n=5)
        by = ey - er * 1.45 - 3 - brow * er * 0.55
        line(cv, [(cx - er * 0.8, by + side * brow * er * 0.1), (cx, by - er * 0.17), (cx + er * 0.8, by - side * brow * er * 0.1)], max(2.5, r * 0.02),
             seed=seed + 54 + side, boil=0.5, n=4, taper=(0.3, 0.3))
    my = y + r * 0.27
    if vis not in ("X", "M") and mo > 0.05:
        k = r / 158.0
        with _xf(cv, x, my - r * 0.02, k):
            core.INKMUL = core.INKMUL * (iw / (5.0 * k ** 0.5))
            _zmouth(cv, vis, mo, smile, seed + 60, wk=wk)
    else:
        sw = r * 0.26
        line(cv, [(x - sw, my - smile * r * 0.06), (x, my + smile * r * 0.13), (x + sw, my - smile * r * 0.06)], iw, seed=seed + 60, boil=0.6, n=6,
             taper=(0.25, 0.25))
    for side in (-1, 1):
        dots(cv, [(x + side * r * 0.56, y + r * 0.16)], r * 0.08, P_["hotpink"], a=150)


def _sun_body(cv, x, y, r, t, seed=5100, ring_tilt=-16, ring=True, glow=1.0, bands=None):
    """The ringed planet as the sun: planet disc + ring, with a hot inner glow (face drawn separately)."""
    rg = dict(rx=1.75, ry=0.33, rgb=P_["teal"], rgb2=P_["cream"], tilt=ring_tilt) if ring else None
    w.planet(cv, x, y, r, SUN_BASE, bands=bands or SUN_BANDS, ring=None, face=None, seed=seed, crater=False, shade_rgb=mix(P_["gold"], P_["red"], 0.3))
    for k, (ca, cr_, cs) in enumerate(((-128, 0.8, 0.09), (-52, 0.84, 0.07), (152, 0.78, 0.06), (38, 0.83, 0.08), (-95, 0.62, 0.05))):
        a = math.radians(ca)
        cx_, cy_ = x + r * cr_ * math.cos(a), y + r * cr_ * math.sin(a)
        blob(cv, ell(cx_, cy_, r * cs, r * cs * 0.8, n=8), mix(SUN_BASE, INK, 0.2), w=max(2.0, r * 0.014), seed=seed + 10 + k, boil=0.5)
    if glow > 0:
        cv.save()
        cv.clipPath(_circ(x, y, r * 1.01), doAntiAlias=True)
        _glow(cv, x - r * 0.15, y - r * 0.2, r * 1.25, (255, 250, 200), int(150 * glow), mid=0.4, blend=skia.BlendMode.kScreen)
        cv.restore()
    return rg


def _sun(cv, x, y, r, t, lids=(0.45, 0.45), look=(0.0, 0.3), brow=0.0, vis="X", mo=0.0, smile=0.4, seed=5100, ring_tilt=-16, glow=1.0, ring=True, wk=1.0,
         ry=0.36, ring_dy=0.24):
    """The sun = the show's ringed planet with its sleepy face (ring seated a little low so the talking mouth stays clear)."""
    rg = dict(rx=1.75, ry=ry, rgb=P_["teal"], rgb2=P_["cream"], tilt=ring_tilt) if ring else None
    _glow(cv, x, y, r * 1.45, (255, 255, 225), int(255 * glow), mid=0.7, mida=0.75)
    if rg:
        w._ring(cv, x, y + r * ring_dy, r, rg, seed + 300, "back")
    _sun_body(cv, x, y, r, t, seed=seed, glow=glow)
    _sun_face(cv, x, y, r, t, lids=lids, look=look, brow=brow, vis=vis, mo=mo, smile=smile, seed=seed + 100, wk=wk)
    if rg:
        w._ring(cv, x, y + r * ring_dy, r, rg, seed + 300, "front")


def _corona(cv, x, y, r, t, k=1.0, rot=0.0, cols=None):
    """The sun's huge corona: soft bloom, two counter-rotating ray fans, and halo rings rippling outward."""
    if k <= 0:
        return
    _glow(cv, x, y, r * 4.2, (255, 170, 60), int(120 * k), mid=0.3)
    _glow(cv, x, y, r * 2.3, (255, 236, 160), int(200 * k), mid=0.45)
    _rays(cv, x, y, r * 0.9, r * 5.5, 18, rot + t * 3.0, (255, 214, 60), int(120 * k), width=0.55, wob=0.25, t=t)
    _rays(cv, x, y, r * 0.95, r * 3.6, 26, -rot * 0.7 - t * 4.5 + 7, (255, 250, 220), int(90 * k), width=0.3, wob=0.4, t=t * 1.3)
    for j in range(4):                                             # rippling halo rings
        ph = (t * 0.35 + j / 4.0) % 1.0
        rr = r * (1.25 + 1.6 * ph)
        a = int(170 * k * (1 - ph) ** 1.3)
        if a > 6:
            cv.drawPath(poly_path(cr_closed(jit(ell(x, y, rr, rr, n=20), 2.0, 5300 + j), 3)), paint((cols or [P_["yellow"], P_["hotpink"], P_["cream"], P_["orange"]])[j], a, stroke=5 + 5 * (1 - ph)))


def _flare(cv, sx, sy, k, t):
    """Psychedelic lens flare: coloured discs along the line from the light through the frame centre."""
    if k <= 0.01:
        return
    dx, dy = W / 2 - sx, H / 2 - sy
    for j, (u, rr, col) in enumerate(((0.55, 60, P_["teal"]), (0.85, 30, P_["hotpink"]), (1.15, 110, P_["violet"]), (1.4, 46, P_["acid"]),
                                      (1.75, 150, P_["orange"]), (2.05, 26, P_["cream"]))):
        px, py = sx + dx * u, sy + dy * u
        _glow(cv, px, py, rr * (1 + 0.06 * math.sin(t * 3 + j)), col, int(90 * k), mid=0.75, mida=0.8, blend=skia.BlendMode.kScreen)
        cv.drawPath(poly_path(ell(px, py, rr, rr, n=6, phase=0.3)), paint(col, int(38 * k), stroke=3))


# ===================================================================== LANDSCAPE PARTS
def _curve(x0, x1, base, amp, freq, phase, n=44, amp2=0.0, freq2=2.7):
    xs = np.linspace(x0, x1, n)
    ys = base - amp * (0.5 + 0.5 * np.sin(xs / W * 2 * math.pi * freq + phase)) - amp2 * np.sin(xs / W * 2 * math.pi * freq2 + phase * 1.7)
    return xs, ys


def _band_hill(cv, xs, ys, cols, stripe=30, seed=0, ink=5.0, bottom=1500, rim=None, rim_a=0, dots_rgb=None, tilt=0.0):
    """A rolling hill filled with stripes that follow its crest (the show's rainbow hills)."""
    top = list(zip(xs, ys))
    cv.drawPath(poly_path(top + [(xs[-1], bottom), (xs[0], bottom)]), paint(cols[0]))
    nb = len(cols)
    for k in range(1, 9):
        off = k * stripe * (1 + 0.15 * k)
        y2 = ys + off + tilt * (xs - xs.mean()) * 0.02 * k
        cv.drawPath(poly_path(list(zip(xs, y2)) + [(xs[-1], bottom), (xs[0], bottom)]), paint(cols[k % nb]))
    if dots_rgb is not None:
        cv.save()
        cv.clipPath(poly_path(top + [(xs[-1], bottom), (xs[0], bottom)]), doAntiAlias=True)
        stipple(cv, dots_rgb, (xs[0], float(ys.min()), xs[-1], float(ys.max()) + 260), spacing=17, r=2.0, seed=seed + 5,
                fn=lambda X, Y: np.clip(np.sin(X * 0.011 + seed) * 0.5 + 0.5, 0.15, 1) * 0.7)
        cv.restore()
    if rim is not None and rim_a > 0:
        brush(cv, np.stack([xs, ys + 7], 1), 9, rim, taper=(0.02, 0.02), seed=seed + 9, a=int(rim_a))
    line(cv, np.stack([xs, ys], 1)[::2], ink, seed=seed + 3, boil=1.2, n=6, taper=(0.02, 0.02))


def _ptree(cv, x, y, s, t, season="psy", grow=1.0, seed=0, face=False, sway=1.0, look=0.0, blink=None):
    """A psychedelic lollipop tree (x, y = trunk base). season psy|spring|summer|autumn|winter."""
    if grow <= 0.01:
        return
    gs = pop(grow, 0.0, 1.0) if grow < 1 else 1.0
    with _xf(cv, x, y, s):
        cv.scale(1.0 + 0.12 * (1 - gs) * math.sin(grow * 9), gs)
        sw = math.sin(t * 0.9 + seed) * 10 * sway
        h = 300.0
        trunk_c = {"winter": (120, 80, 150)}.get(season, P_["violet"])
        trunk = [(-30, 0), (-20, -h * 0.45), (-14 + sw * 0.4, -h * 0.85), (14 + sw * 0.4, -h * 0.85), (20, -h * 0.45), (32, 0)]
        blob(cv, trunk, trunk_c, w=5, seed=seed, boil=0.9, n=5,
             shade=lambda c: ([line(c, [(-40, -20 - k * 52), (0, -36 - k * 52), (40, -50 - k * 52)], 7, mix(trunk_c, P_["magenta"], 0.6), seed=seed + 1 + k,
                                    boil=0.6, n=3, taper=(0, 0)) for k in range(6)],
                              c.drawRect(R(8, -h, 50, 10), paint(mix(trunk_c, INK, 0.25), 150))))
        for side in (-1, 1):
            line(cv, [(side * 6 + sw * 0.3, -h * 0.62), (side * 60 + sw * 0.6, -h * 0.8), (side * 96 + sw, -h * 0.98)], 12, trunk_c, seed=seed + 8 + side, boil=0.7, n=4,
                 taper=(0, 0.6))
            line(cv, [(side * 6 + sw * 0.3, -h * 0.62), (side * 60 + sw * 0.6, -h * 0.8), (side * 96 + sw, -h * 0.98)], 3.5, seed=seed + 9 + side, boil=0.7, n=4,
                 taper=(0, 0.6))
        cx, cy = sw, -h - 40
        if season == "winter":
            for k in range(5):
                a = math.radians(-150 + k * 30)
                tip = (cx + 150 * math.cos(a), cy + 30 + 120 * math.sin(a))
                line(cv, [(sw * 0.5, -h * 0.8), ((sw * 0.5 + tip[0]) / 2, (-h * 0.8 + tip[1]) / 2 - 10), tip], 9, trunk_c, seed=seed + 20 + k, boil=0.6, n=4, taper=(0, 0.8))
                blob(cv, ell(tip[0], tip[1] - 6, 26, 12, n=8), P_["white"], w=3.5, seed=seed + 30 + k, boil=0.5)
            return
        pal = {"psy": [P_["magenta"], P_["orange"], P_["hotpink"], P_["yellow"], P_["violet"]],
               "spring": [P_["acid"], P_["mint"], P_["acid_dk"], P_["hotpink"], P_["acid"]],
               "summer": [P_["acid_dk"], P_["teal"], P_["acid"], P_["tealdk"], P_["acid_dk"]],
               "autumn": [P_["orange"], P_["red"], P_["gold"], (230, 70, 30), P_["yellow"]]}[season]
        lobes = [(-95, 10, 92), (95, 14, 90), (0, -70, 110), (-40, 50, 80), (48, 46, 84)]
        for k, (lx, ly, lr) in enumerate(lobes):
            col = pal[k % len(pal)]
            px, py = cx + lx + 4 * math.sin(t * 1.3 + k), cy + ly + 3 * math.cos(t * 1.1 + k)

            def sh(c, px=px, py=py, lr=lr, col=col, k=k):
                c.drawPath(poly_path(cr_closed(ell(px + lr * 0.3, py + lr * 0.35, lr * 0.9, lr * 0.8, n=10), 3)), paint(mix(col, INK, 0.22)))
                sp = [(px + (lr * 0.08 + lr * 0.11 * u) * math.cos(u * 2.1 + t * 0.8 + k), py + (lr * 0.08 + lr * 0.11 * u) * math.sin(u * 2.1 + t * 0.8 + k))
                      for u in np.linspace(0, 6.2, 22)]
                brush(c, np.array(sp), 5, mix(col, P_["white"], 0.45), taper=(0.1, 0.3), seed=seed + 60 + k, a=200)
            blob(cv, ell(px, py, lr, lr * 0.92, n=11), col, w=5, seed=seed + 40 + k, boil=1.0, shade=sh)
        if season == "spring":
            for k in range(14):
                a = k * 2.4
                rr = 40 + 110 * float(hsh(seed + k))
                bx, by = cx + rr * math.cos(a) * 1.2, cy + rr * math.sin(a) * 0.75
                blob(cv, ell(bx, by, 13, 12, n=6), P_["hotpink"], w=3, seed=seed + 100 + k, boil=0.5)
                dots(cv, [(bx, by)], 4, P_["white"])
        elif season == "summer":
            for k in range(7):
                a = k * 2.4 + 0.5
                rr = 40 + 100 * float(hsh(seed + k * 3))
                blob(cv, ell(cx + rr * math.cos(a) * 1.2, cy + rr * math.sin(a) * 0.75, 14, 14, n=7), P_["orange"], w=3, seed=seed + 120 + k, boil=0.5)
        elif season == "psy":
            for k in range(6):
                a = k * 1.9 + 0.3
                rr = 50 + 90 * float(hsh(seed + k * 5))
                sparkle(cv, cx + rr * math.cos(a) * 1.2, cy + rr * math.sin(a) * 0.7, 12, P_["cream"], w=2.5, seed=seed + 140 + k)
        if face:
            fy = -h * 0.42
            bl = blink if blink is not None else (1.0 if (t * 0.5 + seed) % 3.7 < 0.15 else 0.0)
            for side in (-1, 1):
                ex = side * 15 + look * 6
                if bl > 0.5:
                    line(cv, [(ex - 9, fy), (ex + 9, fy)], 4, seed=seed + 150 + side, boil=0.4, n=2)
                else:
                    blob(cv, ell(ex, fy, 11, 13, n=8), P_["white"], w=3.5, seed=seed + 150 + side, boil=0.5)
                    dots(cv, [(ex + look * 4, fy + 2)], 5.5, INK)
            line(cv, [(-12, fy + 26), (0, fy + 34), (12, fy + 26)], 4, seed=seed + 155, boil=0.5, n=3)


def _flower(cv, x, y, s, t, petal=None, petal2=None, seed=0, grow=1.0, sing=0.0, look=0.0, stem=120.0, n=7, face=True, sleep=0.0):
    """A flower with a little face (x, y = stem base). sing 0..1 opens its mouth; sleep 0..1 closes eyes/droops."""
    if grow <= 0.01:
        return
    k = pop(grow, 0.0, 1.0) if grow < 1 else 1.0
    petal = petal or P_["hotpink"]
    petal2 = petal2 or mix(petal, P_["white"], 0.3)
    with _xf(cv, x, y, s * max(0.05, k)):
        sw = math.sin(t * 1.7 + seed) * 10 + sleep * 18
        hx, hy = sw, -stem + sleep * 16
        line(cv, [(0, 0), (sw * 0.3, -stem * 0.5), (hx, hy)], 9, P_["acid_dk"], seed=seed, boil=0.6, n=4, taper=(0, 0))
        line(cv, [(0, 0), (sw * 0.3, -stem * 0.5), (hx, hy)], 3, seed=seed + 1, boil=0.6, n=4, taper=(0, 0))
        blob(cv, [(sw * 0.15, -stem * 0.35), (34, -stem * 0.55), (52, -stem * 0.42), (26, -stem * 0.3)], P_["acid"], w=3.5, seed=seed + 2, boil=0.6, n=3)
        rot0 = t * 20 + seed * 37
        for j in range(n):
            a = math.radians(rot0 + j * 360 / n)
            pc = (hx + 40 * math.cos(a), hy + 40 * math.sin(a))
            blob(cv, ell(pc[0], pc[1], 30, 17, n=8, rot=math.degrees(a)), petal if j % 2 == 0 else petal2, w=3.5, seed=seed + 10 + j, boil=0.7)
        blob(cv, ell(hx, hy, 30, 30, n=10), P_["yellow"], w=4, seed=seed + 30, boil=0.7,
             shade=lambda c: c.drawPath(poly_path(cr_closed(ell(hx + 8, hy + 10, 26, 22, n=8), 3)), paint(P_["gold"])))
        if face:
            bl = 1.0 if sleep > 0.5 or (t * 0.7 + seed * 0.13) % 2.9 < 0.12 else 0.0
            for side in (-1, 1):
                ex = hx + side * 10 + look * 4
                if bl:
                    line(cv, [(ex - 6, hy - 5), (ex, hy - 2), (ex + 6, hy - 5)], 3, seed=seed + 40 + side, boil=0.4, n=3)
                else:
                    dots(cv, [(ex, hy - 5)], 4.2, INK)
                    dots(cv, [(ex - 1.2, hy - 6.5)], 1.3, P_["white"])
            if sing > 0.05:
                blob(cv, ell(hx + look * 3, hy + 10, 7, 4 + 8 * sing, n=8), P_["mouth"], w=2.8, seed=seed + 45, boil=0.4)
            else:
                line(cv, [(hx - 8, hy + 7), (hx, hy + 12), (hx + 8, hy + 7)], 3, seed=seed + 46, boil=0.4, n=3)
            dots(cv, [(hx - 18, hy + 4), (hx + 18, hy + 4)], 4.5, P_["hotpink"], a=160)


def _person(cv, x, y, s, t, body=None, head=None, seed=0, wave=0.0, kind=0, look=0.0, grow=1.0, hop=0.0):
    """A friendly little 'real' person/creature: rubber-hose limbs, oversized head, huge graphic eyes. y = feet."""
    if grow <= 0.01:
        return
    k = pop(grow, 0.0, 1.0) if grow < 1 else 1.0
    body = body or P_["orange"]
    head = head or P_["peach"]
    with _xf(cv, x, y - hop, s):
        cv.scale(1.0 + 0.25 * (1 - k), max(0.05, k))
        bob = abs(math.sin(t * 3.0 + seed)) * 5
        for side in (-1, 1):
            tube(cv, [(side * 16, -70 - bob), (side * 22, -36), (side * 20, 0)], 13, mix(body, INK, 0.25), w=3.5, seed=seed + side, boil=0.6)
            blob(cv, ell(side * 26, 2, 20, 9, n=8), P_["red"] if kind % 2 else P_["teal"], w=3, seed=seed + 4 + side, boil=0.4)
        blob(cv, [(-40, -60 - bob), (-34, -150 - bob), (0, -166 - bob), (34, -150 - bob), (40, -60 - bob), (0, -50 - bob)], body, w=4.5, seed=seed + 8, boil=0.8,
             n=4, shade=lambda c: [c.drawRect(R(-50, -120 - bob + j * 26, 50, -110 - bob + j * 26), paint(mix(body, P_["white"], 0.35))) for j in range(3)])
        for side in (-1, 1):
            if side > 0 and wave > 0:
                wv = math.sin(t * 9 + seed) * 22 * wave
                pts = [(30, -140 - bob), (74, -190 - bob), (82 + wv, -246 - bob)]
            else:
                pts = [(side * 30, -140 - bob), (side * 56, -110 - bob), (side * 60, -76 - bob)]
            tube(cv, pts, 12, body, w=3.5, seed=seed + 12 + side, boil=0.7)
            dots(cv, [pts[-1]], 10, P_["white"])
        hy = -250 - bob
        hr = 82
        blob(cv, ell(0, hy, hr, hr * 0.94, n=12), head, w=5, seed=seed + 20, boil=0.9,
             shade=lambda c: c.drawPath(poly_path(cr_closed(ell(24, hy + 24, hr * 0.85, hr * 0.8, n=10), 3)), paint(mix(head, INK, 0.15))))
        if kind == 0:                                                # antennae
            for side in (-1, 1):
                line(cv, [(side * 26, hy - 70), (side * 40, hy - 120), (side * 52, hy - 138)], 4, seed=seed + 30 + side, boil=0.6, n=3)
                dots(cv, [(side * 52, hy - 140)], 9, P_["acid"])
        elif kind == 1:                                              # pom-pom hat
            blob(cv, [(-70, hy - 50), (0, hy - 110), (70, hy - 50)], P_["teal"], w=4, seed=seed + 32, boil=0.6, n=3)
            blob(cv, ell(0, hy - 112, 18, 18, n=8), P_["yellow"], w=3.5, seed=seed + 33, boil=0.5)
        elif kind == 2:                                              # a tuft of hair
            blob(cv, [(-40, hy - 70), (-10, hy - 120), (6, hy - 84), (30, hy - 124), (46, hy - 70)], P_["magenta"], w=4, seed=seed + 34, boil=0.6, n=4)
        else:                                                        # little horns
            for side in (-1, 1):
                blob(cv, [(side * 34, hy - 66), (side * 58, hy - 120), (side * 64, hy - 60)], P_["cream"], w=3.5, seed=seed + 35 + side, boil=0.5, n=3)
        bl = 1.0 if (t * 0.6 + seed * 0.21) % 3.3 < 0.12 else 0.0
        for side in (-1, 1):
            ex = side * 30 + look * 8
            if bl:
                line(cv, [(ex - 18, hy - 6), (ex, hy), (ex + 18, hy - 6)], 4, seed=seed + 40 + side, boil=0.4, n=3)
            else:
                blob(cv, ell(ex, hy - 8, 22, 26, n=9), P_["white"], w=4, seed=seed + 40 + side, boil=0.5)
                dots(cv, [(ex + look * 8, hy - 4)], 11, INK)
                dots(cv, [(ex + look * 8 - 4, hy - 9)], 3.5, P_["white"])
        line(cv, [(-24, hy + 34), (0, hy + 48), (24, hy + 34)], 4.5, seed=seed + 45, boil=0.5, n=4)
        dots(cv, [(-52, hy + 22), (52, hy + 22)], 9, P_["hotpink"], a=150)


# ===================================================================== T030_adjust
def _cloud(cv, x, y, s, seed=0, rgb=None, a=255, face=False, t=0.0):
    rgb = rgb or P_["white"]
    pts = []
    for k in range(12):
        ang = k / 12 * 2 * math.pi
        bump = 1.0 + 0.16 * math.sin(ang * 5 + seed)
        pts.append((x + 120 * s * bump * math.cos(ang), y + 52 * s * bump * math.sin(ang) - (14 * s if math.sin(ang) < 0 else 0)))
    blob(cv, pts, rgb, w=4.5, seed=seed, boil=1.0, n=5, a=a,
         shade=lambda c: c.drawPath(poly_path(cr_closed(ell(x + 20 * s, y + 30 * s, 120 * s, 34 * s, n=10), 3)), paint(mix(rgb, P_["lilac"], 0.35), a)))
    if face:
        for side in (-1, 1):
            line(cv, [(x + side * 26 * s - 9 * s, y - 4 * s), (x + side * 26 * s, y + 2 * s), (x + side * 26 * s + 9 * s, y - 4 * s)], 3.5, seed=seed + 5 + side,
                 boil=0.5, n=3, a=a)
        line(cv, [(x - 10 * s, y + 14 * s), (x, y + 20 * s), (x + 10 * s, y + 14 * s)], 3.5, seed=seed + 8, boil=0.5, n=3, a=a)


def _meadow_bg(cv, t, glare=1.0, seed=6100, horizon=760):
    """Bright summer meadow (for the white-out close-up): pale sky, glare top-right, soft hills, flowers."""
    _lin(cv, (0, 0), (0, horizon), [(120, 210, 255), (190, 238, 255), (255, 240, 214)])
    cv.save()
    cv.translate(760, horizon + 300)
    for k, col in enumerate((P_["hotpink"], P_["orange"], P_["yellow"], P_["acid"], P_["teal"], P_["violet"])):
        rr = 980 - k * 34
        cv.drawPath(poly_path(cr_open(ell(0, 0, rr, rr * 0.8, n=24)[12:], 4), closed=False), paint(col, 120, stroke=34))
    cv.restore()
    for k in range(4):
        cx = (200 + k * 520 + t * (14 + 6 * k)) % (W + 500) - 250
        _cloud(cv, cx, 150 + 120 * (k % 2) + 18 * math.sin(t * 0.7 + k), 0.9 + 0.3 * (k % 3), seed=seed + 40 + k * 3, face=(k == 1), t=t)
    _glow(cv, 1780, -60, 1200, (255, 255, 236), int(255 * glare), mid=0.3)
    _rays(cv, 1780, -60, 120, 1900, 14, 98 + t * 2, (255, 255, 230), int(70 * glare), width=0.4, wob=0.3, t=t)
    xs, ys = _curve(-200, W + 200, horizon - 10, 70, 1.2, 0.8 + seed)
    _band_hill(cv, xs, ys, [(120, 230, 170), (150, 240, 120), (110, 210, 150)], stripe=26, seed=seed + 1, ink=4)
    xs, ys = _curve(-200, W + 200, horizon + 120, 90, 0.9, 2.1 + seed)
    _band_hill(cv, xs, ys, [P_["acid"], (140, 230, 40), P_["acid_dk"]], stripe=34, seed=seed + 2, ink=5)
    for k in range(7):
        fx = 90 + k * 290 + 40 * math.sin(k * 2.3)
        _flower(cv, fx, horizon + 260 + 30 * (k % 2), 0.9, t, petal=[P_["hotpink"], P_["orange"], P_["violet"], P_["teal"]][k % 4], seed=seed + 20 + k * 7)


def _streaks(cv, x, y, t, a, seed=0):
    """Anamorphic light streaks + glints through a blinding light source at x, y."""
    if a <= 0:
        return
    for k in range(3):
        hh = 10 + 8 * k
        p = skia.Paint(AntiAlias=True)
        p.setShader(skia.GradientShader.MakeLinear([skia.Point(x - 1400, y), skia.Point(x + 1400, y)],
                                                   [core.C(P_["white"], 0), core.C((255, 250, 225), int(a * (0.9 - 0.25 * k))), core.C(P_["white"], 0)]))
        yy = y + (k - 1) * 46 + 6 * math.sin(t * 2 + k)
        cv.drawPath(poly_path(cr_closed(ell(x, yy, 1400, hh, n=12), 3)), p)
    _sparkles(cv, t, (x - 900, y - 300, x + 300, y + 500), 9, seed + 7, r=(14, 34), a=int(min(255, a * 1.2)))


def _floaters(cv, t, a, seed=6200):
    """Eye floaters: translucent squiggles drifting across a blown-out view."""
    if a <= 0:
        return
    for k in range(7):
        x0 = (float(hsh(seed + k)) * W + t * (20 + 16 * k)) % (W + 400) - 200
        y0 = 160 + float(hsh(seed + k * 3.3)) * 760 + 40 * math.sin(t * 0.6 + k)
        pts = [(x0 + j * 26, y0 + 18 * math.sin(j * 0.9 + t * 1.3 + k)) for j in range(9)]
        brush(cv, cr_open(np.array(pts), 6), 7 + 4 * (k % 3), (190, 170, 220), taper=(0.3, 0.3), seed=seed + 10 + k, a=int(a * 0.55))
        dots(cv, [(pts[2][0], pts[2][1] - 30)], 10 + 4 * (k % 2), (200, 180, 230), a=int(a * 0.35))


STEPS = (2.8, 3.72, 3.92, 4.48)                                    # "adjust" "step" "by" "step"


def _adjust_whiteout(cv, t, T):
    """0..5.65: blinding white resolves step by step into Gary squinting in the meadow; his pupil clicks smaller."""
    n = sum(1 for s0 in STEPS if t >= s0)
    lastk = 1.0
    if n:
        lastk = _k(t, STEPS[n - 1], STEPS[n - 1] + 0.14)
    levels = [0.0, 0.3, 0.52, 0.72, 0.9]
    exp = levels[max(0, n - 1)] + (levels[n] - levels[max(0, n - 1)]) * lastk if n else 0.0
    exp = max(exp, 0.12 * _k(t, 0.0, 2.6))
    late = _k(t, 4.9, 5.6)
    z = 1.0 + 0.03 * t
    with _cam(cv, 960, 560, z):
        _meadow_bg(cv, t, glare=1.0)
        lid = 0.82 - 0.62 * exp
        low = 0.0
        pup = 0.86 - 0.5 * exp
        look = (0.12 * math.sin(t * 0.9), -0.05 + 0.75 * late)
        _gary(cv, 960, 470, 1.85, t, look=look, lid=lid + 0.1 * late, low=low, pupil=pup, mouth="squint" if exp < 0.7 else ("smile" if late > 0.4 else "flat"),
              arms=("hang" if late < 0.5 else "rest", "shield" if late < 0.5 else "rest"), squint_lines=max(0.0, 1 - exp * 1.4),
              light=(P_["yellow"], -40, 0.5), tears=max(0.0, 0.7 - exp))
    # the click of each step: a ring pulse round the eye
    if n:
        ph = (t - STEPS[n - 1]) / 0.35
        if 0 <= ph < 1:
            rr = 300 + 260 * ph
            cv.drawPath(poly_path(cr_closed(ell(960, 440, rr, rr, n=20), 3)), paint(P_["white"], int(200 * (1 - ph)), stroke=14 * (1 - ph) + 2))
    white = 255 * (1 - exp) ** 1.15
    if t < STEPS[0]:
        white = 236 - 26 * _k(t, 0.0, STEPS[0]) + 6 * math.sin(t * 9)
    _floaters(cv, t, 200 * (1 - exp) * (1 - late))
    _glow(cv, 1700, 40, 900, P_["white"], int(min(255, 120 + white * 0.5)), mid=0.4)
    _wash(cv, (255, 253, 244), white)
    _streaks(cv, 1640, 120, t, 230 * (1 - 0.7 * exp) * (1 - late), seed=6400)


SHADOW_RGB = (58, 22, 108)


E1, E2 = (0.14, 0.42), (1.42, 0.07)                                  # shadow axes: width -> depth, height -> to the right


@contextmanager
def _proj(cv, bx, by, e1=E1, e2=E2):
    """Ground-plane shadow projection: local x -> e1, local height (-y) -> e2 (light low from the left)."""
    cv.save()
    cv.concat(skia.Matrix.MakeAll(e1[0], -e2[0], bx, e1[1], -e2[1], by, 0, 0, 1))
    try:
        yield
    finally:
        cv.restore()


def _shadow_fill(cv, path, a=215, blur=9.0, rgb=None):
    rgb = rgb or SHADOW_RGB
    halo = skia.Paint(AntiAlias=True, Color=core.C(rgb, int(a * 0.5)))
    halo.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    cv.drawPath(path, halo)
    cv.drawPath(path, paint(rgb, a))


def _gary_shadow(cv, bx, by, s, t, wave=0.0, a=215):
    with _proj(cv, bx, by):
        cv.scale(s, s)
        body = poly_path(cr_closed(jit([(-128, 0), (-110, -190), (-55, -248), (55, -248), (110, -190), (128, 0)], 1.0, 7710), 5))
        body.addCircle(0, -360 + 6 * math.sin(t * 3.1), 150)
        _shadow_fill(cv, body, a=a)
        for side in (-1, 1):
            if side < 0 and wave > 0:
                hx, hy = -205 - 16 * math.sin(t * 8) * wave, -380 - 60 * wave
                pts = [(-104, -170), (-215, -230 - 40 * wave), (hx, hy)]
            else:
                pts = [(side * 104, -170), (side * 160, -110), (side * 175, -20)]
            cv.drawPath(open_path_pts(cr_open(np.array(pts, float), 6).tolist()), paint(SHADOW_RGB, a, stroke=34))
            cv.drawCircle(pts[-1][0], pts[-1][1], 30, paint(SHADOW_RGB, a))


def _tree_shadow(cv, bx, by, s, t, a=215):
    with _proj(cv, bx, by):
        cv.scale(s, s)
        sw = math.sin(t * 0.9) * 10
        p = poly_path(cr_closed([(-30, 0), (-18, -150), (-14 + sw * 0.4, -255), (14 + sw * 0.4, -255), (18, -150), (32, 0)], 4))
        for lx, ly, lr in [(-95, 10, 92), (95, 14, 90), (0, -70, 110), (-40, 50, 80), (48, 46, 84)]:
            p.addCircle(sw + lx, -340 + ly, lr)
        p.setFillType(skia.PathFillType.kWinding)
        _shadow_fill(cv, p, a=a, blur=12)


def _bunny_shadow(cv, bx, by, s, t, hop, a=215, face=-1):
    """Shadow of a hopping bunny: drawn upright-ish (its own profile), sliding along the lawn."""
    cv.save()
    cv.translate(bx, by - hop * 0.25)
    cv.skew(-0.35, 0)
    cv.scale(s * face, s * 0.62)
    P = np.array(SHAPES["bunny"], float)
    _shadow_fill(cv, poly_path(cr_closed(jit(P, 1.2, 7720), 4)), a=a, blur=7)
    cv.restore()


def _lawn(cv, t, seed=6500, glare=1.0):
    """High-angle sunny lawn: wavy mown psychedelic stripes, stipple, tufts, daisies, mushrooms."""
    w.field(cv, (150, 236, 40))
    cols = [(176, 246, 70), (120, 220, 30), (196, 250, 110), (100, 206, 60), (150, 240, 160), (110, 226, 120), (220, 250, 120)]
    for k in range(-2, 16):
        y0 = -120 + k * 92
        xs = np.linspace(-300, W + 300, 30)
        top = y0 + 22 * np.sin(xs / 260.0 + k * 0.7 + t * 0.3)
        bot = y0 + 92 + 22 * np.sin(xs / 260.0 + (k + 1) * 0.7 + t * 0.3)
        cv.drawPath(poly_path(list(zip(xs, top)) + list(zip(xs[::-1], bot[::-1]))), paint(cols[k % len(cols)]))
    stipple(cv, (90, 180, 20), (0, 160, W, H), spacing=19, r=2.2, seed=seed, fn=lambda X, Y: 0.4 + 0.6 * np.clip((Y - 160) / 900, 0, 1))
    for k in range(26):                                            # grass tufts
        gx = (float(hsh(seed + k * 3.1)) * 2100 - 90)
        gy = 240 + float(hsh(seed + k * 5.7)) * 840
        for j in range(3):
            line(cv, [(gx + j * 9 - 9, gy), (gx + j * 12 - 12 + 4 * math.sin(t * 2 + k), gy - 26 - 8 * (j == 1))], 4, (60, 150, 20), seed=seed + 20 + k * 3 + j,
                 boil=0.6, n=2, taper=(0, 0.7))
    for k in range(12):                                            # little daisies
        fx = float(hsh(seed + k * 9.1)) * 1900 + 10
        fy = 300 + float(hsh(seed + k * 2.3)) * 760
        for j in range(5):
            a = j * 1.2566 + k
            dots(cv, [(fx + 9 * math.cos(a), fy + 6 * math.sin(a))], 6, [P_["white"], P_["hotpink"], P_["yellow"]][k % 3])
        dots(cv, [(fx, fy)], 5, P_["orange"])
    for k, (mx, my, ms) in enumerate(((1700, 1010, 0.42), (1780, 1040, 0.3), (130, 1000, 0.36))):
        w.mushroom(cv, mx, my, ms, cap=[P_["red"], P_["magenta"], P_["orange"]][k], seed=seed + 300 + k)
    if glare > 0:
        p = skia.Paint(AntiAlias=True)
        p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, -40), skia.Point(0, 470)], [core.C((255, 255, 242), int(255 * glare)),
                                                                                             core.C((255, 252, 220), int(170 * glare)), core.C((255, 250, 220), 0)],
                                                   [0.0, 0.4, 1.0]))
        cv.drawRect(R(-600, -600, W + 600, 480), p)
        p2 = skia.Paint(AntiAlias=True)
        p2.setShader(skia.GradientShader.MakeLinear([skia.Point(-60, 0), skia.Point(520, 0)], [core.C((255, 255, 240), int(230 * glare)), core.C((255, 255, 240), 0)]))
        cv.drawRect(R(-600, -600, 540, H + 600), p2)


def _adjust_shadows(cv, t, T):
    """5.65..8.2: 'First, he can only look at shadows.' -- safe dark shadows on the bright grass; a bunny shadow hops by."""
    lt = t - 5.65
    z = 1.0 + 0.03 * lt
    with _cam(cv, 960, 560, z):
        _lawn(cv, t)
        _tree_shadow(cv, 760, 300, 0.95, t)
        hop_x = 2150 - (lt - 0.45) * 760
        bh = 0.0
        if lt > 0.45 and hop_x > -300:
            ph = (lt * 2.4) % 1.0
            bh = 150 * math.sin(ph * math.pi)
            _bunny_shadow(cv, hop_x, 650, 1.0, t, hop=bh, face=-1)
        wave = _k(lt, 1.55, 1.85) * (1 - _k(lt, 2.3, 2.5))
        _gary_shadow(cv, 560, 880, 0.95, t, wave=wave)
        _ptree(cv, 760, 300, 0.72, t, season="summer", seed=6600)
        cv.drawPath(poly_path(cr_closed(ell(560, 884, 140, 26, n=10), 3)), paint(SHADOW_RGB, 140))
        bx = hop_x if lt > 0.45 else 2100
        follow = float(np.clip((bx - 560) / 1100.0, -1, 1))
        look = (0.3 + 0.55 * follow, 0.75 - 0.25 * max(0.0, follow)) if 0.6 < lt and bx < 1900 else (0.45, 0.95)
        joy = _k(lt, 0.9, 1.3)
        _gary(cv, 560, 538, 0.95, t, look=look, lid=0.2 - 0.12 * joy, rot=4, mouth="grin" if joy > 0.5 else "smile", arms=("wave" if wave > 0.3 else "rest", "rest"),
              light=(P_["yellow"], 200, 0.7), shine=0.7 * joy)
    _glow(cv, -140, 160, 900, (255, 255, 236), 230, mid=0.3)


_OFF = {}


def _offscreen(key, wd, ht):
    sf = _OFF.get(key)
    if sf is None:
        sf = skia.Surface(int(wd), int(ht))
        _OFF[key] = sf
    return sf


def _pond_path(seed=6700):
    pts = []
    for k in range(18):
        a = k / 18 * 2 * math.pi
        rr = 1.0 + 0.05 * math.sin(a * 3 + 1.3) + 0.03 * math.sin(a * 7)
        pts.append((960 + 1010 * rr * math.cos(a), 560 + 600 * rr * math.sin(a)))
    return pts


def _reflection(c, t, wave, seed=6800):
    """What the pond mirrors, seen from above (drawn in full-frame coords): zenith sky, clouds, the trees round the
    rim leaning in, a sun glint, and Gary's own face looking back up."""
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(960, 520), 1100, [core.C((40, 120, 255)), core.C((90, 190, 255)), core.C((190, 236, 255)),
                                                                           core.C((255, 220, 240))], [0.0, 0.35, 0.75, 1.0]))
    c.drawRect(R(-100, -100, W + 100, H + 100), p)
    for k in range(5):
        a = k * 1.25 + t * 0.05
        _cloud(c, 960 + 470 * math.cos(a) * 1.3, 470 + 250 * math.sin(a), 0.7, seed=seed + k * 3, rgb=(250, 250, 255))
    for k, col in enumerate((P_["violet"], P_["teal"], P_["acid"], P_["yellow"], P_["orange"], P_["hotpink"])):
        rr = 300 + k * 22                                           # a 'glory': rainbow rings round his reflected head
        c.drawPath(poly_path(ell(960, 600, rr, rr, n=40)), paint(col, 110, stroke=22))
    for k, (ang, rr, sc, season) in enumerate(((198, 0.97, 0.8, "psy"), (232, 0.99, 0.7, "summer"), (268, 0.97, 0.85, "psy"), (304, 0.99, 0.7, "autumn"),
                                               (340, 0.97, 0.8, "spring"), (160, 1.0, 0.62, "summer"), (20, 1.0, 0.62, "psy"))):
        a = math.radians(ang)
        bx, by = 960 + 1060 * rr * math.cos(a), 560 + 640 * rr * math.sin(a)
        c.save()
        c.translate(bx, by)
        c.rotate(ang + 90 + 180)
        _ptree(c, 0, 0, sc, t, season=season, seed=seed + 40 + k * 9, sway=0.6)
        c.restore()
    _glow(c, 1290, 330, 260, (255, 255, 230), 210)
    sparkle(c, 1290, 330, 52, P_["white"], w=3, seed=seed + 90)
    _gary(c, 960, 650, 1.32, t, look=(0.0, -0.15), lid=0.05, mouth="grin" if wave > 0.2 else "smile", arms=("rest", "wave" if wave > 0.2 else "rest"),
          shine=0.5, seed=GS)


def _adjust_pond(cv, t, T):
    """8.2..10.5: 'Then reflections in the water.' -- POV down into the pond: the sky, trees and his own eye rippling."""
    lt = t - 8.2
    wave = _k(lt, 0.9, 1.1)
    z = 1.0 + 0.02 * lt
    pond = poly_path(cr_closed(_pond_path(), 4))
    sf = _offscreen("refl", 960, 540)
    c2 = sf.getCanvas()
    c2.save()
    c2.scale(0.5, 0.5)
    old = core.INKMUL
    core.INKMUL = old * 1.4
    _reflection(c2, t, wave)
    core.INKMUL = old
    c2.restore()
    img = sf.makeImageSnapshot()
    drops = ((0.15, 930, 560), (1.25, 1180, 760), (1.75, 700, 420))
    with _cam(cv, 960, 540, z):
        _lawn(cv, t, glare=0.0)
        cv.save()
        cv.clipPath(pond, doAntiAlias=True)
        samp = skia.SamplingOptions(skia.FilterMode.kLinear)
        amp_t = 3.0 + sum(14.0 * math.exp(-(lt - d0) * 2.2) for d0, _, _ in drops if lt > d0)
        stp = 6
        for yy in range(0, H, stp):
            dx = amp_t * math.sin(yy * 0.045 + t * 7.0) + 2.0 * math.sin(yy * 0.13 - t * 5)
            cv.drawImageRect(img, skia.Rect(0, yy / 2, 960, (yy + stp) / 2), skia.Rect(dx - 4, yy, W + dx + 4, yy + stp), samp, None,
                             skia.Canvas.kFast_SrcRectConstraint)
        _glow(cv, 960, 560, 1200, (10, 60, 120), 150, mid=0.55, mida=0.15)
        _wash(cv, (0, 140, 170), 38)
        for d0, rx_, ry_ in drops:                                  # ripple rings
            if lt > d0:
                for j in range(3):
                    ph = (lt - d0) * 0.9 - j * 0.18
                    if 0 < ph < 1.2:
                        rr = 30 + 520 * ph
                        cv.drawPath(poly_path(cr_closed(ell(rx_, ry_, rr, rr * 0.62, n=18), 3)), paint(P_["white"], int(150 * max(0, 1 - ph / 1.2)), stroke=5))
        for k in range(26):                                         # glints dancing on the surface
            gx = 120 + float(hsh(6900 + k)) * 1680
            gy = 100 + float(hsh(6950 + k)) * 900
            ph = (t * 1.3 + float(hsh(7000 + k))) % 1.0
            if ph < 0.5:
                L = 16 + 30 * math.sin(ph * 2 * math.pi)
                line(cv, [(gx - L, gy), (gx + L, gy + 1)], 4, P_["white"], seed=7050 + k, boil=0.4, n=2, taper=(0.4, 0.4), a=200)
        cv.restore()
        brush(cv, cr_closed(jit(_pond_path(), 1.0, 6710), 4), 7, closed=True, seed=6711)
        # things floating ON the water (not mirrored)
        for k, (px, py, pr, ang) in enumerate(((330, 830, 90, 20), (1560, 300, 80, 200), (1660, 820, 105, 120), (420, 260, 70, 300), (1250, 960, 60, 60))):
            px += 10 * math.sin(t * 0.6 + k)
            pts = [(px + pr * math.cos(math.radians(ang + a)), py + pr * 0.7 * math.sin(math.radians(ang + a))) for a in range(20, 340, 32)] + [(px, py)]
            blob(cv, pts, [P_["acid_dk"], (40, 170, 90), P_["acid_dk"], (60, 190, 110), (40, 170, 90)][k], w=4.5, seed=7100 + k, boil=0.8, n=4,
                 shade=lambda c, px=px, py=py, pr=pr: [c.drawLine(px, py, px + pr * math.cos(a), py + pr * 0.7 * math.sin(a), paint(P_["acid"], 160, stroke=3))
                                                     for a in np.linspace(0.5, 5.8, 6)])
        _flower(cv, 1660, 850, 1.1, t, petal=P_["hotpink"], petal2=P_["white"], seed=7150, stem=10, face=True, sing=0.3 * wave)
        fx, fy = 330, 820                                               # a frog on a lily pad
        blob(cv, ell(fx, fy, 62, 46, n=10), P_["acid"], w=4.5, seed=7160, boil=0.8,
             shade=lambda c: c.drawPath(poly_path(cr_closed(ell(fx + 14, fy + 18, 50, 30, n=8), 3)), paint(P_["acid_dk"])))
        for side in (-1, 1):
            blob(cv, ell(fx + side * 30, fy - 40, 22, 22, n=8), P_["acid"], w=4, seed=7162 + side, boil=0.6)
            bl = (t * 0.8) % 2.3 < 0.12
            if bl:
                line(cv, [(fx + side * 30 - 12, fy - 40), (fx + side * 30 + 12, fy - 40)], 4, seed=7165 + side, boil=0.4, n=2)
            else:
                dots(cv, [(fx + side * 30, fy - 40)], 13, P_["white"])
                dots(cv, [(fx + side * 30 + 3, fy - 38)], 7, INK)
        line(cv, [(fx - 30, fy - 4), (fx, fy + 6), (fx + 30, fy - 4)], 4, seed=7168, boil=0.5, n=3)
        sx = 1320 + 160 * math.sin(t * 0.9)                             # a water strider
        sy = 560 + 60 * math.cos(t * 0.7)
        for j in range(3):
            for side in (-1, 1):
                line(cv, [(sx, sy), (sx + side * 40, sy - 20 + j * 20), (sx + side * 70, sy - 34 + j * 34)], 2.5, seed=7170 + j * 2 + (side > 0), boil=0.5, n=3,
                     taper=(0, 0.6))
                dots(cv, [(sx + side * 70, sy - 34 + j * 34)], 4, P_["white"], a=180)
        blob(cv, ell(sx, sy, 18, 7, n=8), (60, 40, 70), w=3, seed=7180, boil=0.4)
        for k in range(10):                                             # reeds round the rim
            rx = [40, 110, 1820, 1880, 60, 1850, 160, 1760, 1900, 20][k]
            ry = [140, 80, 120, 200, 980, 960, 1050, 1040, 1030, 900][k]
            ht = 160 + 60 * float(hsh(7200 + k))
            sw = 10 * math.sin(t * 1.2 + k)
            line(cv, [(rx, ry), (rx + sw * 0.5, ry - ht * 0.5), (rx + sw, ry - ht)], 7, P_["acid_dk"], seed=7210 + k, boil=0.6, n=3, taper=(0, 0.5))
            if k % 2 == 0:
                blob(cv, ell(rx + sw, ry - ht - 10, 9, 26, n=8), (130, 70, 50), w=3.5, seed=7230 + k, boil=0.4)
    _glow(cv, 1400, -100, 700, (255, 255, 236), 120)


def _day_sky(cv, t, seed=6900, horizon=640, glare=(80, -60), clouds=True, bright=1.0, grad=True):
    if grad:
        _lin(cv, (0, -100), (0, horizon), [(70, 160, 255), (140, 214, 255), (210, 244, 255), (255, 236, 205)], pos=[0.0, 0.4, 0.75, 1.0])
    gx, gy = glare
    _rays(cv, gx, gy, 80, 2300, 16, 20 + t * 2.5, (255, 255, 235), int(80 * bright), width=0.45, wob=0.3, t=t)
    _glow(cv, gx, gy, 900, (255, 255, 236), int(240 * bright), mid=0.3)
    if clouds:
        for k in range(4):
            cx = (300 + k * 560 + t * (16 + 5 * k)) % (W + 600) - 300
            _cloud(cv, cx, 120 + 90 * (k % 2) + 14 * math.sin(t * 0.6 + k), 0.75 + 0.25 * (k % 3), seed=seed + 40 + k * 3, face=(k == 2), t=t)


def _butterflies(cv, t, box, n=6, seed=7800):
    """Little flapping butterflies wandering about (two pairs of wings + body)."""
    x0, y0, x1, y1 = box
    cols = [P_["hotpink"], P_["yellow"], P_["teal"], P_["orange"], P_["lilac"], P_["acid"]]
    for k in range(n):
        ph = t * (0.25 + 0.06 * k) + k * 1.7
        bx = x0 + (x1 - x0) * (0.5 + 0.45 * math.sin(ph + float(hsh(seed + k)) * 6))
        by = y0 + (y1 - y0) * (0.5 + 0.4 * math.sin(ph * 1.7 + k))
        fl = abs(math.sin(t * 11 + k * 2.1))
        col = cols[k % len(cols)]
        q = 1.8
        for side in (-1, 1):
            blob(cv, ell(bx + side * 13 * q * (0.3 + 0.7 * fl), by - 8 * q, 13 * q * (0.3 + 0.7 * fl), 12 * q, n=7), col, w=3, seed=seed + 10 + k * 2 + (side > 0),
                 boil=0.4)
            blob(cv, ell(bx + side * 9 * q * (0.3 + 0.7 * fl), by + 7 * q, 8 * q * (0.3 + 0.7 * fl), 8 * q, n=6), mix(col, P_["white"], 0.3), w=2.6,
                 seed=seed + 30 + k * 2 + (side > 0), boil=0.4)
        line(cv, [(bx, by - 12 * q), (bx, by + 12 * q)], 5, seed=seed + 50 + k, boil=0.3, n=2, taper=(0.2, 0.2))
        for side in (-1, 1):
            line(cv, [(bx, by - 12 * q), (bx + side * 8, by - 22 * q)], 2.5, seed=seed + 60 + k + (side > 0), boil=0.3, n=2, taper=(0.1, 0.5))


def _day_hills(cv, t, seed=6950, horizon=640):
    xs0, ys0 = _curve(-300, W + 300, horizon - 70, 60, 1.6, seed * 0.07 + 0.9, amp2=20)     # far lilac range + the pyramid eye
    _band_hill(cv, xs0, ys0, [P_["lilac"], (220, 180, 255), P_["hotpink"]], stripe=14, seed=seed + 7, ink=3.5)
    w.pyramid(cv, 1520, float(np.interp(1520, xs0, ys0)) + 30, 0.32, look=(-0.6, 0.2), seed=seed + 9, rays=True)
    xs, ys = _curve(-300, W + 300, horizon, 90, 1.1, seed * 0.1, amp2=30)
    _band_hill(cv, xs, ys, [P_["teal"], (60, 200, 230), P_["mint"]], stripe=20, seed=seed + 1, ink=4)
    for k in range(5):
        px = 120 + k * 420 + 60 * math.sin(k)
        py = float(np.interp(px, xs, ys))
        w.mushroom(cv, px, py + 6, 0.22, cap=[P_["red"], P_["magenta"], P_["orange"]][k % 3], seed=seed + 50 + k, face=False)
    xs, ys = _curve(-300, W + 300, horizon + 110, 80, 0.8, seed * 0.13 + 1.7, amp2=24)
    _band_hill(cv, xs, ys, [P_["yellow"], P_["orange"], (255, 200, 60)], stripe=26, seed=seed + 2, ink=4.5)
    xs, ys = _curve(-300, W + 300, horizon + 230, 70, 1.3, seed * 0.17 + 3.1, amp2=20)
    _band_hill(cv, xs, ys, [P_["acid"], (140, 230, 40), P_["acid_dk"], (120, 220, 60)], stripe=30, seed=seed + 3, ink=5,
               dots_rgb=(90, 170, 20))


def _real_things(cv, t, T):
    """10.5..16.44: 'Then the real things themselves. Trees. Flowers. People.'"""
    lt = t - 10.5
    cx = 960 + 70 * _k(t, 10.5, 16.4)
    z = 1.0 + 0.035 * _k(t, 10.5, 16.4)
    t_tree, t_flow, t_ppl = 13.0, 14.12, 15.46
    with _cam(cv, cx, 540, z):
        _day_sky(cv, t, glare=(60, -80))
        _day_hills(cv, t)
        # trees
        _ptree(cv, 820, 700, 0.55, t, season="spring", grow=_k(t, t_tree + 0.3, t_tree + 0.55) if t < t_tree + 0.6 else 1.0, seed=7300)
        _ptree(cv, 1660, 690, 0.72, t, season="autumn", grow=_k(t, t_tree + 0.16, t_tree + 0.45) if t < t_tree + 0.5 else 1.0, seed=7310)
        gt = (t - t_tree) / 0.5
        _ptree(cv, 1200, 800, 1.3, t, season="psy", grow=min(1.0, max(0.0, gt)), seed=7320, face=True, look=-0.6)
        # people
        for k, (px, py, ps, body, head, kind) in enumerate(((1420, 850, 0.74, P_["blue"], P_["peach"], 0), (1600, 870, 0.66, P_["magenta"], P_["mint"], 1),
                                                            (1790, 850, 0.76, P_["orange"], P_["lilac"], 2), (960, 860, 0.62, P_["teal"], P_["yellow"], 3))):
            g = (t - (t_ppl + k * 0.09)) / 0.45
            if g > 0:
                hop = 30 * max(0.0, math.sin((t - t_ppl - k * 0.09) * 9)) if g < 1.4 else 0.0
                _person(cv, px, py, ps, t, body=body, head=head, seed=7400 + k * 17, wave=_k(t, t_ppl + 0.3 + k * 0.1, t_ppl + 0.5 + k * 0.1), kind=kind,
                        look=-0.8, grow=min(1.0, g), hop=hop)
        # Gary on the bank, lifting his eye from the water to the world
        up = _k(t, 10.6, 11.6)
        lk_x = 0.25 + 0.5 * up
        lk_y = 0.85 - 1.05 * up
        if t > t_tree:
            lk_x, lk_y = 0.8, -0.35
        if t > t_flow:
            lk_x, lk_y = 0.75, 0.25
        if t > t_ppl:
            lk_x, lk_y = 0.9, 0.0
        wow = _k(t, t_tree, t_tree + 0.3)
        wave = _k(t, t_ppl + 0.5, t_ppl + 0.7)
        # the pond in the corner
        pond = [(-200, 930), (150, 905), (420, 960), (470, 1080), (380, 1200), (-200, 1200)]
        blob(cv, pond, (70, 170, 230), w=6, seed=7500, boil=1.0, n=5,
             shade=lambda c: ([c.drawLine(20 + k * 80, 1000 + (k % 3) * 22, 80 + k * 80, 1000 + (k % 3) * 22, paint(P_["white"], 150, stroke=4)) for k in range(5)],
                              _glow(c, 150, 1020, 360, (20, 80, 160), 120)))
        blob(cv, ell(330, 1030, 50, 24, n=9), P_["acid_dk"], w=4, seed=7510, boil=0.6)
        cv.drawPath(poly_path(cr_closed(ell(540, 884, 130, 22, n=10), 3)), paint((60, 120, 20), 110))
        _gary(cv, 540, 590, 0.82, t, look=(lk_x, lk_y), lid=0.25 - 0.25 * up, mouth="o" if 0.2 < wow < 1 and t < t_tree + 0.8 else ("grin" if wave > 0.3 else "smile"),
              arms=("rest", "wave" if wave > 0.3 else "rest"), shine=wow, light=(P_["yellow"], 200, 0.5))
        # flowers pop in the foreground
        for k, (fx, fy, fs, col) in enumerate(((720, 1040, 1.2, P_["hotpink"]), (890, 1075, 0.95, P_["orange"]), (1100, 1045, 1.25, P_["violet"]),
                                              (1300, 1080, 1.0, P_["red"]), (1510, 1050, 1.2, P_["teal"]), (1700, 1080, 0.95, P_["magenta"]),
                                              (1880, 1045, 1.15, P_["yellow"]))):
            g = (t - (t_flow + k * 0.06)) / 0.4
            if g > 0:
                _flower(cv, fx, fy, fs, t, petal=col, seed=7600 + k * 11, grow=min(1.0, g), sing=0.5 + 0.5 * math.sin(t * 6 + k) if t > t_flow + 0.5 else 0.0,
                        look=-0.7)
        _butterflies(cv, t, (700, 380, 1800, 760))
    _label(cv, "TREES.", 780, 250, t, t_tree, size=108, fill=P_["acid"], seed=7700)
    _label(cv, "FLOWERS.", 1250, 150, t, t_flow, size=108, fill=P_["hotpink"], seed=7710)
    _label(cv, "PEOPLE.", 1640, 320, t, t_ppl, size=108, fill=P_["orange"], seed=7720)
    _wash(cv, (255, 253, 240), 150 * (1 - _k(t, 10.5, 12.2)))


# ---------------------------------------------------------------- night / dawn / sunrise landscape (shared with T031)
def _mixc(a, b, k):
    return mix(a, b, float(np.clip(k, 0, 1)))


def _lightc(rgb, night, dawn):
    """Relight a day colour: pull toward deep indigo (night) and toward a dark magenta (pre-dawn backlight)."""
    c = _mixc(rgb, (26, 12, 66), night * 0.78)
    return _mixc(c, (92, 24, 92), dawn * 0.55)


def _night_sky(cv, t, a=1.0, star_k=1.0, seed=8000, stars2=0.0, horizon=820, grad=True):
    if grad:
        _lin(cv, (0, -200), (0, horizon), [(10, 4, 30), (30, 12, 84), (72, 26, 140), (150, 46, 150)], pos=[0.0, 0.42, 0.78, 1.0], a=int(255 * a))
    for k, (nx, ny, nr, col, na) in enumerate(((420, 300, 520, P_["magenta"], 60), (1300, 220, 600, P_["blue"], 70), (1650, 520, 420, P_["teal"], 40),
                                               (800, 560, 480, P_["violet"], 80), (150, 620, 380, P_["hotpink"], 40))):
        br = 0.85 + 0.15 * math.sin(t * 0.7 + k * 1.9)
        _glow(cv, nx + 20 * math.sin(t * 0.1 + k), ny, nr * br, col, int(na * a * br), mid=0.5, mida=0.45)
    cv.save()                                                       # the milky way: a diagonal glow band thick with stars
    cv.translate(980, 420)
    cv.rotate(-24)
    pm = skia.Paint(AntiAlias=True)
    pm.setShader(skia.GradientShader.MakeLinear([skia.Point(0, -170), skia.Point(0, 170)], [core.C(P_["lilac"], 0), core.C((230, 200, 255), int(70 * a)),
                                                                                          core.C(P_["lilac"], 0)]))
    cv.drawRect(R(-1400, -170, 1400, 170), pm)
    if star_k > 0:
        i = np.arange(420, dtype=np.float64)
        X = -1300 + hsh(seed + i * 1.7) * 2600
        Y = (hsh(seed + i * 2.3) - 0.5) * 2 * 120 * (0.3 + 0.7 * hsh(seed + i * 3.1))
        tw = 0.5 + 0.5 * np.abs(np.sin(core.D * 0.2 + i))
        dots(cv, np.stack([X, Y], 1), 1.6, (255, 250, 230), a=int(200 * a * star_k * float(tw.mean())))
    cv.restore()
    if star_k > 0:
        with _tint(cv, (10, 4, 30), 1 - min(1.0, a * star_k)):
            w.stars(cv, seed + 1, (-100, -100, W + 100, horizon - 60), n=320, big=10)
    if stars2 > 0:                                                   # the second wave: bright stars popping on
        for k in range(26):
            sx = 60 + float(hsh(seed + 50 + k * 1.3)) * 1800
            sy = 40 + float(hsh(seed + 60 + k * 2.1)) * (horizon - 260)
            kk = pop(stars2 * 1.6 - k * 0.025, 0.0, 0.35)
            if kk > 0.01:
                _glow(cv, sx, sy, 34 * kk, (255, 250, 220), int(120 * a))
                sparkle(cv, sx, sy, (9 + 9 * float(hsh(seed + k))) * kk, [P_["white"], P_["yellow"], P_["mint"], P_["hotpink"]][k % 4], w=2.0, seed=seed + 70 + k,
                        a=int(255 * a))


BUNNY_STARS = SHAPES["bunny"]


def _constellation(cv, x, y, s, k, t, a=255, seed=8100):
    """The bunny constellation: its stars, then the lines drawing themselves star to star (k 0..1)."""
    P = [(x + px * s, y + py * s) for px, py in BUNNY_STARS]
    n = len(P)
    m = k * n
    pts = []
    for j in range(n + 1):
        if j <= m:
            pts.append(P[j % n])
        else:
            if j - 1 < m:
                f = m - (j - 1)
                a0, b0 = P[(j - 1) % n], P[j % n]
                pts.append((a0[0] + (b0[0] - a0[0]) * f, a0[1] + (b0[1] - a0[1]) * f))
            break
    if len(pts) > 1:
        cv.drawPath(open_path_pts(pts), paint((200, 240, 255), int(a * 0.85), stroke=4))
        cv.drawPath(open_path_pts(pts), paint((200, 240, 255), int(a * 0.25), stroke=12))
    for j, (px, py) in enumerate(P):
        if j > m + 1:
            continue
        r = 6 + 4 * (j % 3 == 0) + 2 * math.sin(t * 4 + j)
        _glow(cv, px, py, r * 4, (220, 240, 255), int(a * 0.5))
        sparkle(cv, px, py, r * 1.6, P_["white"], w=1.8, seed=seed + j, a=a)


def _far_hills(cv, t, night, dawn, rim=None, rim_a=0, seed=8200, horizon=820):
    """Three rainbow hill ranges toward the horizon (relit for night/dawn) + mist bands between them."""
    xs, ys = _curve(-300, W + 300, horizon, 70, 1.05, 1.2, amp2=22)
    _band_hill(cv, xs, ys, [_lightc(c, night, dawn) for c in (P_["violet"], P_["lilac"], P_["hotpink"])], stripe=16, seed=seed + 1, ink=4, rim=rim,
               rim_a=rim_a)
    mist = _lightc((255, 220, 240), night, dawn)
    xs2, ys2 = _curve(-300, W + 300, horizon + 60, 30, 1.7, 2.4)
    cv.drawPath(poly_path(list(zip(xs2, ys2)) + list(zip(xs2[::-1], ys2[::-1] + 70))), paint(mist, 70))
    xs, ys = _curve(-300, W + 300, horizon + 90, 80, 0.85, 2.9, amp2=26)
    _band_hill(cv, xs, ys, [_lightc(c, night, dawn) for c in (P_["magenta"], P_["orange"], P_["yellow"], P_["orange"])], stripe=22, seed=seed + 2, ink=4.5,
               rim=rim, rim_a=rim_a * 0.8)
    return xs, ys


def _front_hill(cv, t, night, dawn, seed=8300, glow_k=0.0):
    """The foreground hillock (left) Gary lies / sits on: acid stripes, flowers, glowing mushrooms, fireflies at night."""
    xs = np.linspace(-300, 1400, 34)
    ys = 900 + 160 * ((xs - 380) / 900.0) ** 2 + 18 * np.sin(xs / 140.0)
    _band_hill(cv, xs, ys, [_lightc(c, night, dawn) for c in (P_["acid"], P_["teal"], P_["acid_dk"], (140, 230, 40))], stripe=26, seed=seed + 1, ink=5.5)
    xs2 = np.linspace(1100, W + 300, 20)
    ys2 = 980 + 60 * np.sin(xs2 / 230.0 + 1.0)
    _band_hill(cv, xs2, ys2, [_lightc(c, night, dawn) for c in (P_["teal"], P_["acid"], P_["tealdk"])], stripe=24, seed=seed + 2, ink=5)
    for k, (fx, fy) in enumerate(((80, 1000), (190, 1030), (760, 990), (880, 1040), (1500, 1050), (1720, 1030))):
        _flower(cv, fx, fy, 0.75, t, petal=_lightc([P_["hotpink"], P_["orange"], P_["violet"], P_["red"], P_["yellow"], P_["magenta"]][k], night * 0.6, dawn),
                seed=seed + 20 + k * 9, sleep=night * (1 - glow_k))
    for k, (mx, my) in enumerate(((30, 930), (1010, 1010), (1840, 1000))):
        glow_mushroom(cv, mx, my, 1.0, t, seed=seed + 60 + k)
    if night > 0.2:                                                  # fireflies
        for k in range(14):
            ph = t * (0.3 + 0.05 * k) + k
            fx = (float(hsh(seed + k * 3.3)) * 2000 + 40 * math.sin(ph)) % 1920
            fy = 700 + float(hsh(seed + k * 5.1)) * 330 + 26 * math.sin(ph * 1.3)
            bl = 0.5 + 0.5 * math.sin(t * 3 + k * 2.1)
            _glow(cv, fx, fy, 26, P_["acid"], int(120 * night * bl))
            dots(cv, [(fx, fy)], 3.5, (230, 255, 160), a=int(255 * night * bl))


def _sky_wheel(cv, t, th, day_fn, night_fn, C=(960, 1900)):
    """The sky as a giant dial: rotating th 0 -> 180 degrees swaps the day half for the night half (dusk on the seam)."""
    for which in ("day", "night"):
        ang = th if which == "day" else th - 180
        if (which == "day" and th >= 179.5) or (which == "night" and th <= 0.5):
            continue
        cv.save()
        cv.rotate(ang, C[0], C[1])
        cv.clipRect(R(C[0] - 5000, C[1] - 5000, C[0] + 5000, C[1]), doAntiAlias=True)
        g = skia.Paint(AntiAlias=True)
        if which == "day":
            cols, pos = [(255, 236, 205), (255, 236, 205), (190, 236, 255), (110, 190, 255), (60, 140, 250)], [0.0, 0.36, 0.5, 0.72, 1.0]
        else:
            cols, pos = [(150, 46, 150), (150, 46, 150), (72, 26, 140), (30, 12, 84), (10, 4, 30)], [0.0, 0.36, 0.48, 0.7, 1.0]
        g.setShader(skia.GradientShader.MakeRadial(skia.Point(*C), 2600, [core.C(c) for c in cols], pos))
        cv.drawRect(R(C[0] - 2700, C[1] - 2700, C[0] + 2700, C[1] + 10), g)
        (day_fn if which == "day" else night_fn)(cv)
        p = skia.Paint(AntiAlias=True)
        col = (255, 130, 40) if which == "day" else (255, 60, 150)
        p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, C[1] - 420), skia.Point(0, C[1])], [core.C(col, 0), core.C(col, 230)]))
        cv.drawRect(R(C[0] - 5000, C[1] - 420, C[0] + 5000, C[1]), p)
        cv.restore()
    if 0.5 < th < 179.5:
        cv.save()
        cv.rotate(th, C[0], C[1])
        line(cv, [(C[0] - 4000, C[1]), (C[0], C[1]), (C[0] + 4000, C[1])], 7, P_["yellow"], seed=8400, boil=1.0, n=3, taper=(0, 0))
        for k in range(10):
            sparkle(cv, C[0] - 2400 + k * 300 + 40 * math.sin(t * 3 + k), C[1] - 10, 16, P_["cream"], w=2, seed=8410 + k)
        cv.restore()


T_MOON, T_STARS, T_FINALLY, T_MORNING, T_SUNITSELF = 18.05, 19.32, 20.6, 21.73, 23.06


def _night_and_morning(cv, t, T):
    """16.44..25.71: 'At night, he looks up at the moon and the stars. And finally, one morning... he can look at the sun itself.'"""
    th = 180 * _k(t, 16.5, 17.45)
    night = th / 180.0
    dawn = _k(t, T_FINALLY, T_SUNITSELF + 1.6)
    night_l = night * (1 - 0.75 * dawn)
    gx, gy = 1180, 830                                               # where the morning glow (and tomorrow's sun) comes up
    zc = _k(t, T_FINALLY, 25.7)
    up = _k(t, 16.6, T_FINALLY + 0.4) * (1 - zc)                    # drift up into the stars while he stargazes
    cam_x, cam_y, z = 960 + 120 * zc + 30 * up, 540 + 60 * zc - 22 * up, 1.0 + 0.12 * zc + 0.035 * up
    star_fade = 1 - _k(t, T_FINALLY + 0.6, T_SUNITSELF + 1.2)
    with _cam(cv, cam_x, cam_y, z):
        def day_fn(c):
            _day_sky(c, t, glare=(1500, -60), horizon=820, grad=th < 0.5)

        def night_fn(c):
            _night_sky(c, t, a=1.0, star_k=star_fade, stars2=_k(t, T_STARS, T_STARS + 1.0) * star_fade, grad=th > 179.5)

        _sky_wheel(cv, t, th, day_fn, night_fn)
        if dawn > 0:                                                 # the dawn creeping up from the horizon
            p = skia.Paint(AntiAlias=True)
            p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, -100), skia.Point(0, 860)],
                                                       [core.C((60, 20, 130), int(160 * dawn)), core.C(P_["magenta"], int(150 * dawn)),
                                                        core.C(P_["orange"], int(230 * dawn)), core.C(P_["yellow"], int(255 * dawn))], [0.0, 0.5, 0.82, 1.0]))
            cv.drawRect(R(-600, -600, W + 600, 900), p)
            _glow(cv, gx, gy, 300 + 900 * dawn, (255, 200, 90), int(255 * dawn), mid=0.3)
            _glow(cv, gx, gy, 120 + 400 * dawn, (255, 250, 210), int(255 * dawn ** 1.5), mid=0.4)
            rk = _k(t, T_SUNITSELF - 0.2, T_SUNITSELF + 1.5)
            if rk > 0:
                _rays(cv, gx, gy + 40, 60, 2200 * rk + 200, 22, 180 + 5 * math.sin(t * 0.4), (255, 214, 90), int(120 * rk), width=0.42, wob=0.35, t=t)
                _rays(cv, gx, gy + 40, 60, 1500 * rk + 200, 11, 188 + 3 * math.sin(t * 0.6), (255, 250, 210), int(110 * rk), width=0.18, wob=0.5, t=t * 1.3)
            ek = _k(t, T_SUNITSELF + 0.6, 25.7)
            if ek > 0:                                               # the very rim of the light about to break the horizon
                _glow(cv, gx, gy + 20, 260 + 160 * ek, (255, 255, 235), int(255 * ek), mid=0.25, mida=0.6)
                cv.drawPath(poly_path(cr_closed(ell(gx, gy + 34, 210 + 60 * ek, 40 + 24 * ek, n=14), 3)), paint((255, 255, 240), int(240 * ek)))
            _dawn_birds(cv, t - T_MORNING)
        # the moon rising on "moon", sinking away at dawn
        mk = _k(t, T_MOON - 0.45, T_MOON + 0.35)
        sk_ = _k(t, T_MORNING - 0.4, T_SUNITSELF + 2.2)
        if mk > 0 and night > 0.5 and sk_ < 0.99:
            my = 980 - 760 * mk + 380 * sk_
            mx = 470 - 30 * mk - 760 * sk_
            kk = 1.0 + 0.12 * math.sin(max(0.0, min(1.0, (t - T_MOON) / 0.35)) * math.pi)
            _glow(cv, mx, my, 330 * kk, (230, 240, 255), int(120 * (1 - dawn)), mid=0.35)
            with _tint(cv, (255, 170, 200), 0.5 * sk_):
                w.skull_moon(cv, mx, my, 92 * kk, seed=8600)
        if night > 0.6:
            ck = _k(t, T_STARS + 0.15, T_STARS + 1.1)
            if ck > 0:
                _constellation(cv, 1420, 330, 1.9, ck, t, a=int(255 * star_fade))
            sk = (t - (T_STARS + 0.85)) / 0.6                        # a shooting star
            if 0 < sk < 1:
                sx, sy = 1700 - 900 * sk, 120 + 300 * sk
                brush(cv, np.array([(sx + 260, sy - 86), (sx + 130, sy - 43), (sx, sy)]), 7, P_["cream"], taper=(0.9, 0.05), seed=8650, a=int(255 * (1 - sk)))
                sparkle(cv, sx, sy, 16, P_["white"], seed=8651)
        rim = _mixc((200, 170, 255), (255, 200, 80), dawn)
        _far_hills(cv, t, night_l, dawn * (1 - night_l * 0.5), rim=rim, rim_a=230 * max(night_l * 0.6, dawn))
        _front_hill(cv, t, night_l, dawn * 0.7)
        # Gary: lying stargazing -> sits up on "And finally" -> watches the glow
        sit = _k(t, T_FINALLY + 0.25, T_FINALLY + 0.85)
        rot = -88 * (1 - sit)
        if t < 17.6:
            lk = (0.85, 0.0)
        elif t < T_STARS:
            lk = (0.8, -0.45)                                        # (local) -> up-left: the moon
        elif t < T_FINALLY + 0.3:
            lk = (0.75, 0.55)                                        # (local) -> up-right: the stars
        else:
            lk = (0.85, -0.05 - 0.1 * (1 - sit))
        if sit > 0.5:
            lk = (0.9, 0.1 - 0.15 * dawn)
        gx0, gy0 = 470 + 40 * sit, 885 - 90 * sit
        light = None
        if night_l > 0.3:
            light = ((200, 190, 255), -110, 0.55 * night_l)
        if dawn > 0.05:
            light = ((255, 190, 90), -10, min(1.0, dawn * 1.2))
        with _tint(cv, (40, 20, 90), 0.42 * night_l):
            _gary(cv, gx0, gy0, 0.72, t, look=lk, lid=0.12 - 0.12 * dawn, rot=rot, arms=("pillow", "pillow") if sit < 0.5 else ("rest", "rest"),
                  mouth="o" if T_SUNITSELF < t else ("smile" if t < T_FINALLY else "flat"), shine=0.8 * _k(t, T_STARS, T_STARS + 0.3) * (1 - sit) + dawn,
                  light=light)
    _flare(cv, *_cam_pt(gx, gy, cam_x, cam_y, z), _k(t, T_SUNITSELF, 25.4) * 0.9, t)
    _wash(cv, (255, 170, 60), 46 * _k(t, T_SUNITSELF + 0.8, 25.7), blend=skia.BlendMode.kScreen)


def _dawn_birds(cv, tt):
    """Five birds crossing the dawn; tt = seconds since 'one morning' (continues across the cut into T031)."""
    for k in range(5):
        bt = tt - k * 0.25
        if bt > 0:
            bx = 1900 - bt * (260 + 30 * k)
            if bx < -200:
                continue
            by = 420 + 60 * k + 20 * math.sin(bt * 3 + k)
            fl = math.sin(bt * 12 + k)
            line(cv, [(bx - 26, by - 10 * fl), (bx - 10, by), (bx, by + 4), (bx + 10, by), (bx + 26, by - 10 * fl)], 4.5, (60, 20, 70), seed=8500 + k,
                 boil=0.5, n=3)


T030_DUR = 25.715


def _cam_pt(x, y, cx, cy, z):
    return W / 2 + (x - cx) * z, H / 2 + (y - cy) * z


def T030_adjust(cv, t, T, A):
    if t < 5.65:
        _adjust_whiteout(cv, t, T)
    elif t < 8.2:
        _adjust_shadows(cv, t, T)
    elif t < 10.5:
        _adjust_pond(cv, t, T)
    elif t < 16.44:
        _real_things(cv, t, T)
    else:
        _night_and_morning(cv, t, T)


# ===================================================================== T031_sun
SUN_X, SUN_Y, SUN_R = 1180, 430, 250                                # world position of the risen sun (same world as T030's dawn)


def _sunrise_sky(cv, t, sx, sy, k, seed=9000):
    """Sky for the sunrise: violet zenith -> magenta -> orange -> gold horizon; sunburst wedges; long lit clouds."""
    top = _mixc((40, 14, 100), (110, 40, 200), k)
    _lin(cv, (0, -300), (0, 860), [top, P_["magenta"], (255, 120, 40), (255, 210, 80)], pos=[0.0, 0.45, 0.75, 1.0])
    path = skia.Path()
    n = 30
    for j in range(n):
        a0 = math.radians(t * 3.0) + j * 2 * math.pi / n
        a1 = a0 + math.pi / n
        path.moveTo(sx, sy)
        path.lineTo(sx + 3000 * math.cos(a0), sy + 3000 * math.sin(a0))
        path.lineTo(sx + 3000 * math.cos(a1), sy + 3000 * math.sin(a1))
        path.close()
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(sx, sy), 2000, [core.C((255, 240, 150), int(120 * k)), core.C((255, 180, 90), int(70 * k)),
                                                                          core.C((255, 120, 200), int(26 * k))], [0.0, 0.4, 1.0]))
    cv.drawPath(path, p)
    for j, (cx, cy, cw, col) in enumerate(((330, 260, 1.4, P_["hotpink"]), (1650, 190, 1.2, P_["magenta"]), (700, 520, 1.0, P_["orange"]), (1820, 600, 0.9, P_["hotpink"]),
                                           (120, 640, 0.8, P_["orange"]))):
        cx2 = cx + 18 * math.sin(t * 0.3 + j)
        pts = [(cx2 - 240 * cw, cy + 16), (cx2 - 190 * cw, cy - 8), (cx2 - 130 * cw, cy - 30), (cx2 - 70 * cw, cy - 18), (cx2 - 10 * cw, cy - 44),
               (cx2 + 60 * cw, cy - 26), (cx2 + 130 * cw, cy - 38), (cx2 + 200 * cw, cy - 10), (cx2 + 250 * cw, cy + 14), (cx2, cy + 24)]
        blob(cv, pts, _mixc(col, (255, 230, 170), 0.15), w=3.5, seed=seed + 20 + j, boil=0.9, n=4,
             shade=lambda c, cx2=cx2, cy=cy, cw=cw: c.drawRect(R(cx2 - 270 * cw, cy + 4, cx2 + 270 * cw, cy + 40), paint((255, 206, 100))))


def _land_sunrise(cv, t, sun_y, sun_k, look_sun=True, gary=True, seed=9100, lids=(1.0, 1.0), look=(0.0, 0.3), vis="X", mo=0.0, brow=0.0, wk=1.0,
                  smile=0.4, ring_tilt=-16, gary_kw=None):
    """The sunrise world (camera applied by the caller): sky, corona, the ringed planet-sun coming up behind the hills,
    rainbow ranges lighting up, the hillock with Gary watching."""
    _sunrise_sky(cv, t, SUN_X, sun_y, sun_k)
    carry = 1 - _k(t, 0.0, 2.6)                                    # T030's dawn rays + horizon rim, handed over to the corona
    if carry > 0:
        _rays(cv, SUN_X, 870, 60, 2400, 22, 180 + 5 * math.sin(t * 0.4), (255, 214, 90), int(120 * carry), width=0.42, wob=0.35, t=t)
        _rays(cv, SUN_X, 870, 60, 1700, 11, 188 + 3 * math.sin(t * 0.6), (255, 250, 210), int(110 * carry), width=0.18, wob=0.5, t=t * 1.3)
        _glow(cv, SUN_X, 850, 420, (255, 255, 235), int(255 * carry), mid=0.25, mida=0.6)
    _dawn_birds(cv, t + T030_DUR - T_MORNING)
    _corona(cv, SUN_X, sun_y, SUN_R, t, k=max(sun_k, 0.5))
    _sun(cv, SUN_X, sun_y, SUN_R, t, lids=lids, look=look, brow=brow, vis=vis, mo=mo, smile=smile, seed=5100, ring_tilt=ring_tilt, wk=wk)
    dawn = 1 - sun_k
    rim = (255, 230, 120)
    _far_hills(cv, t, 0.0, dawn * 0.8, rim=rim, rim_a=230)
    _front_hill(cv, t, 0.0, dawn * 0.5)
    if gary:
        kw = dict(look=(0.75, -0.35), lid=0.0, mouth="o", arms=("rest", "rest"), light=((255, 200, 90), -20, 1.0), shine=0.8)
        kw.update(gary_kw or {})
        _gary(cv, 510, 795, 0.72, t, **kw)


def _sun_rise(cv, t, T):
    """0..5.71 SUNRISE: the planet rises over the rainbow hills, enormous corona; its sleepy eyes open."""
    rise = _k(t, 0.3, 4.0)
    sun_y = 1020 - (1020 - SUN_Y) * rise
    sun_k = 0.15 + 0.85 * _k(t, 0.0, 3.8)
    zc = _k(t, 0.0, 5.0)
    cam_x, cam_y, z = 1080 - 20 * zc, 600 - 150 * zc, 1.12 - 0.14 * zc
    yawn = _k(t, 3.3, 3.8) * (1 - _k(t, 4.4, 4.9))
    lids = 1.0 - 0.55 * _k(t, 4.5, 5.3)
    if 3.3 < t < 4.9:
        lids = 1.0
    look = (0.0, 0.3) if t < 5.25 else (-0.7, 0.55)
    with _cam(cv, cam_x, cam_y, z):
        _land_sunrise(cv, t, sun_y, sun_k, lids=(lids, lids), look=look, vis="O" if yawn > 0.05 else "X", mo=yawn, wk=1.5, brow=0.5 * yawn,
                      gary_kw=dict(look=(0.8, -0.2 - 0.5 * rise)))
    _flare(cv, *_cam_pt(SUN_X, sun_y, cam_x, cam_y, z), 0.8 * sun_k, t)
    _wash(cv, (255, 200, 120), 60 * (1 - _k(t, 0.0, 1.2)), blend=skia.BlendMode.kScreen)


def _ray_hand(cv, x, y, r, t, k, ang0=-28.0, seed=9200):
    """A sunbeam that curls out of the sun like an arm and waves a little glove of light."""
    if k <= 0.01:
        return
    a = math.radians(ang0)
    base = (x + r * 0.98 * math.cos(a), y + r * 0.98 * math.sin(a))
    wv = math.sin(t * 9.0) * 16 * k
    L = r * 1.25 * k
    mid = (base[0] + L * 0.6, base[1] - L * 0.05)
    tip = (base[0] + L * 0.85, base[1] - L * 0.62)
    tube(cv, [base, mid, tip], 46 * k, (255, 220, 90), w=5, seed=seed, boil=0.9, n=8)
    _glow(cv, tip[0], tip[1], 160 * k, (255, 240, 160), int(160 * k))
    cv.save()
    cv.translate(*tip)
    cv.scale(2.4 * k, 2.4 * k)
    old = core.INKMUL
    core.INKMUL = old / (2.4 * k) ** 0.5
    _hand(cv, 0, 0, -80 + wv, "spread", 1, seed + 3, rgb=(255, 238, 150))
    core.INKMUL = old
    cv.restore()


def _back_gary(cv, x, y, s, t, seed=GS, rim=1.0):
    """Gary seen from behind (over-the-shoulder), backlit by the sunrise."""
    with _tint(cv, (110, 36, 130), 0.42):
        _gary(cv, x, y, s, t, view="back", arms=("rest", "rest"), seed=seed)
    with _xf(cv, x, y, s):
        b = 6 * math.sin(t * 3.1)
        rimp = skia.Op(_circ(0, b, 152), _circ(-30, b + 22, 152), skia.PathOp.kDifference_PathOp)
        if rimp is not None:
            cv.drawPath(rimp, paint((255, 220, 120), int(230 * rim)))


def _sun_hey(cv, t, T):
    """5.71..7.8 P01 'Oh. Hey, Gary.' -- over Gary's shoulder: the sun-planet notices him, talks, winks, waves a sunbeam."""
    lt = t - 5.71
    vis, mo = vis_at("P01", T)
    oh = _k(t, 5.75, 6.0) * (1 - _k(t, 6.5, 6.8))
    wink = _k(t, 7.05, 7.2) * (1 - _k(t, 7.55, 7.75))
    lids = (0.35 - 0.2 * oh + 0.65 * wink, 0.35 - 0.2 * oh)
    z = 1.2 + 0.05 * lt
    cx, cy = SUN_X + 20, SUN_Y + 70
    with _cam(cv, cx, cy, z):
        _sunrise_sky(cv, t, SUN_X, SUN_Y, 1.0)
        _corona(cv, SUN_X, SUN_Y, SUN_R, t, k=1.0)
        _ray_hand(cv, SUN_X, SUN_Y, SUN_R, t, _k(t, 6.55, 6.9), ang0=8)
        _sun(cv, SUN_X, SUN_Y, SUN_R, t, lids=lids, look=(-0.75, 0.6), brow=0.8 * oh + 0.3, vis=vis, mo=mo, smile=0.55, ring_tilt=-16 + 3 * math.sin(t * 2.0))
        _far_hills(cv, t, 0.0, 0.0, rim=(255, 230, 120), rim_a=230)
    _back_gary(cv, 300, 880, 1.3, t)
    _flare(cv, *_cam_pt(SUN_X, SUN_Y, cx, cy, z), 0.5, t)


def _iris_sun(cv, ex, ey, rx, ry, t, k=1.0):
    """The sun-planet reflected in Gary's iris (top-right of the cornea): a tiny, complete ringed planet + glints."""
    sx, sy = ex + rx * 0.32, ey - ry * 0.34
    rr = ry * 0.2 * k
    _glow(cv, sx, sy, rr * 4.0, (255, 230, 150), 210)
    _rays(cv, sx, sy, rr * 1.1, rr * 3.4, 14, t * 6, (255, 250, 210), 120, width=0.4)
    with _xf(cv, sx, sy, rr / 120.0):
        core.INKMUL *= 0.8
        _sun(cv, 0, 0, 120, t, lids=(0.35, 0.35), look=(-0.3, 0.5), smile=0.7, glow=0.8)
    sparkle(cv, sx + rr * 1.5, sy - rr * 1.3, rr * 0.8, P_["white"], w=1.5, seed=9302)


def _gary_whoa(cv, t, T):
    """7.8..12.25 G05 '...Whoa.' -- Gary close-up: tears of joy, the sun in his eye; 'And he understands' pushes into it."""
    loud = loud_at("G05", T)
    push = _k(t, 10.35, 12.1) ** 1.8
    s = 2.25
    gx, gy = 960, 455
    b = 6 * math.sin(t * 3.1) * s
    ex = gx + (-4 + 0.15 * 78) * s
    ey = gy + b + (-22 - 0.35 * 64) * s
    irx, iry = 66 * s, 66 * s
    fx, fy = ex + irx * 0.32, ey - iry * 0.34                        # the reflected sun: the push-in target
    z = 1.0 + 0.07 * _k(t, 7.8, 10.4) + 6.5 * push
    cx = 960 + (fx - 960) * min(1.0, push * 1.4)
    cy = 540 + (fy - 540) * min(1.0, push * 1.4)
    with _cam(cv, cx, cy, z):
        _lin(cv, (0, 0), (0, H), [(255, 120, 60), (255, 60, 150), (130, 40, 200)])
        w.sunburst(cv, 1700, -100, 2800, 34, [(255, 96, 140), (255, 140, 60)], rot_deg=t * 4.0, seed=9390)
        _wash(cv, (255, 90, 120), 90)
        for j in range(5):                                            # light ripples rolling out of the sun (top right)
            ph = (t * 0.4 + j / 5.0) % 1.0
            rr = 300 + 2000 * ph
            cv.drawPath(poly_path(ell(1700, -100, rr, rr, n=48)), paint([P_["yellow"], P_["cream"], P_["hotpink"], P_["orange"], P_["mint"]][j],
                                                                       int(150 * (1 - ph)), stroke=18 * (1 - ph) + 4))
        _rays(cv, 1700, -100, 100, 2600, 26, 100 + t * 4, (255, 220, 120), 150, width=0.5, wob=0.3, t=t)
        _glow(cv, 1700, -100, 1400, (255, 240, 180), 230, mid=0.3)
        _sparkles(cv, t, (0, 0, W, H), 22, 9400, r=(10, 26))
        for k in range(9):                                            # bokeh discs
            bx = float(hsh(9450 + k)) * W
            by = float(hsh(9460 + k)) * H
            _glow(cv, bx + 20 * math.sin(t * 0.4 + k), by, 70 + 50 * float(hsh(9470 + k)), [P_["yellow"], P_["hotpink"], P_["cream"]][k % 3], 90, mid=0.8, mida=0.9)
        tears = _k(t, 8.4, 9.2)
        arms = ("cheek", "cheek") if t > 8.6 else ("rest", "rest")
        _gary(cv, gx, gy, s, t, look=(0.15, -0.35), lid=0.0, pupil=0.3 + 0.1 * min(1.0, loud), loud=loud, mouth="o" if loud > 0.05 or 8.0 < t < 9.2 else "wobble",
              arms=arms, tears=tears, refl=lambda c, ex_, ey_, rx_, ry_: _iris_sun(c, ex_, ey_, rx_, ry_, t), light=((255, 210, 110), -40, 1.0),
              shine=0.0, tear_rate=0.45)
    fl = _k(t, 11.8, 12.25)
    if fl > 0:
        _glow(cv, 960, 540, 300 + 1800 * fl, (255, 252, 230), int(255 * fl), mid=0.5, mida=0.9)
        _wash(cv, (255, 250, 225), 255 * fl ** 2)


SEASONS = ("spring", "summer", "autumn", "winter")
SEAS_PAL = {   # sky top, sky horizon, hill, hill stripe, hill dots, far hills
    "spring": ((110, 200, 255), (255, 214, 236), (150, 236, 60), (190, 250, 120), (255, 150, 200), (120, 230, 170)),
    "summer": ((40, 140, 255), (255, 236, 150), (60, 200, 80), (120, 230, 60), (255, 214, 0), (40, 190, 160)),
    "autumn": ((120, 60, 200), (255, 150, 60), (230, 110, 30), (200, 60, 40), (255, 190, 40), (170, 60, 110)),
    "winter": ((120, 130, 230), (220, 225, 255), (240, 244, 255), (205, 210, 250), (170, 180, 240), (190, 190, 240)),
}
T_SEAS0, T_FAST = 12.25, 13.95


def _season_phase(t):
    if t < T_SEAS0:
        return 0.0
    if t < T_FAST:
        return (t - T_SEAS0) / 0.425
    ph, tt, dt = 4.0, T_FAST, 1 / 48.0
    while tt < t:
        h = min(dt, t - tt)
        ph += h * (2.35 + 2.65 * _k(tt, T_FAST, 14.7))
        tt += h
    return ph


def _seasons(cv, t, T):
    """12.25..15.06 'The sun makes the seasons and the years.' -- the sun arcs over a little world; spring, summer,
    autumn, winter flip by, then the years fly (trails, a rolling year counter, the tree growing)."""
    ph = _season_phase(t)
    i = int(math.floor(ph)) % 4
    f = ph - math.floor(ph)
    fast = _k(t, T_FAST, 14.4)
    bl = (1 - fast) * _k(f, 0.86, 1.0) + fast * ease(f)
    A_, B_ = SEAS_PAL[SEASONS[i]], SEAS_PAL[SEASONS[(i + 1) % 4]]
    pal = [_mixc(a, b, bl) for a, b in zip(A_, B_)]
    dom = SEASONS[i] if bl < 0.5 else SEASONS[(i + 1) % 4]
    years = int(ph // 4)
    z = 1.0 + 0.04 * _k(t, T_SEAS0, 15.06)
    with _cam(cv, 960, 560, z):
        _lin(cv, (0, -100), (0, 760), [pal[0], _mixc(pal[0], pal[1], 0.5), pal[1]])
        # the sun's path: trail(s) then the sun
        acx, acy, arx, ary = 960, 820, 900, 700

        def arc_pt(u):
            a = math.pi + u * math.pi
            return acx + arx * math.cos(a), acy + ary * math.sin(a)
        tr = [arc_pt(u) for u in np.linspace(0, 1, 40)]
        cv.drawPath(open_path_pts(tr), paint(P_["white"], int(40 + 120 * fast), stroke=10 + 30 * fast))
        if fast > 0.05:
            for j, col in enumerate((P_["hotpink"], P_["yellow"], P_["teal"])):
                trj = [(x, y + (j - 1) * 26) for x, y in tr]
                cv.drawPath(open_path_pts(trj), paint(col, int(110 * fast), stroke=12))
        _glow(cv, *arc_pt(f), 380, (255, 240, 170), 230, mid=0.3)
        _rays(cv, *arc_pt(f), 130, 520, 16, t * 40, (255, 240, 160), 120, width=0.45)
        if fast > 0.3:
            for gj in (0.1, 0.2):
                gx, gy = arc_pt(max(0.0, f - gj))
                _glow(cv, gx, gy, 140, (255, 220, 120), int(150 * fast * (1 - gj * 3)))
        sx, sy = arc_pt(f)
        with _xf(cv, sx, sy, 0.42):
            _sun(cv, 0, 0, 250, t, lids=(0.3, 0.3), look=(0.45 * math.cos(math.pi * f), 0.6), smile=0.8, ring_tilt=-16 + 30 * (f - 0.5))
        # far hills + the little round world
        w.floaters(cv, 9480, (-100, 40, W + 100, 600), n=12, t=t)
        xs0, ys0 = _curve(-300, W + 300, 720, 60, 1.7, 2.2, amp2=18)
        _band_hill(cv, xs0, ys0, [_mixc(pal[5], P_["hotpink"], 0.45), _mixc(pal[5], P_["violet"], 0.35), _mixc(pal[5], P_["yellow"], 0.4)], stripe=14,
                   seed=9490, ink=3.5)
        xs, ys = _curve(-300, W + 300, 780, 70, 1.2, 0.7, amp2=20)
        _band_hill(cv, xs, ys, [pal[5], _mixc(pal[5], P_["white"], 0.25), _mixc(pal[5], INK, 0.12)], stripe=18, seed=9500, ink=4)
        dome = ell(960, 2150, 1500, 1500, n=60)
        blob(cv, dome, pal[2], w=6, seed=9510, boil=1.2, n=3,
             shade=lambda c: ([c.drawPath(poly_path(ell(960, 2150, 1500 - k * 46, 1500 - k * 46, n=60)), paint(pal[3] if k % 2 else pal[2])) for k in range(1, 12)],
                              stipple(c, pal[4], (0, 640, W, H), spacing=22, r=3.2, seed=9511, fn=lambda X, Y: np.clip(np.sin(X * 0.02) * 0.5 + 0.6, 0.2, 1))))
        grow = 1.0 + 0.06 * min(years, 4)
        _ptree(cv, 560, 700, 0.7 * grow, t, season=dom, seed=9530, face=True, look=0.6 * math.cos(math.pi * f))
        lx = -math.cos(math.pi * f) * 0.9
        _gary(cv, 1230, 545, 0.4, t, look=(lx, -0.6), lid=0.0, mouth="grin" if fast > 0.3 else "smile", arms=("rest", "up" if fast > 0.5 else "rest"), shine=0.6)
        # particles
        for k in range(26):
            ph2 = (t * (0.18 + 0.05 * (k % 5)) + float(hsh(9600 + k))) % 1.0
            px = float(hsh(9610 + k)) * 2100 - 90 + 60 * math.sin(t * 1.5 + k)
            if dom == "spring":
                py = 80 + ph2 * 900
                blob(cv, ell(px, py, 9, 6, n=6, rot=t * 90 + k * 40), P_["hotpink"], w=2, seed=9620 + k, boil=0.4)
            elif dom == "summer":
                if k < 12:
                    sparkle(cv, px, 200 + float(hsh(9630 + k)) * 600, 8 + 6 * math.sin(t * 5 + k), P_["yellow"], w=2, seed=9640 + k)
            elif dom == "autumn":
                py = 80 + ph2 * 950
                blob(cv, [(px, py - 12), (px + 9, py), (px, py + 12), (px - 9, py)], [P_["orange"], P_["red"], P_["gold"]][k % 3], w=2.2, seed=9650 + k, boil=0.4,
                     n=3)
            else:
                py = 60 + ph2 * 980
                dots(cv, [(px, py)], 5 + 2 * (k % 3), P_["white"])
    # words: the season names flip with the sun, then the years roll
    if t < T_FAST + 0.05:
        nm = {"spring": ("SPRING", P_["acid"]), "summer": ("SUMMER", P_["yellow"]), "autumn": ("AUTUMN", P_["orange"]), "winter": ("WINTER", P_["cream"])}[SEASONS[i]]
        _label(cv, nm[0], 960, 985, t, T_SEAS0 + i * 0.425 + 0.02, size=110, fill=nm[1], seed=9700 + i, dur=0.25)
    if t > T_FAST:
        yrs = int(1 + (math.exp(3.6 * max(0.0, t - T_FAST)) - 1) * 9)
        paint_text(cv, "YEAR", 820, 1000, font="shrik", size=86, fill=P_["cream"], ink_w=5.5, shadow=(6, 6), seed=9710)
        _label(cv, f"{yrs:,}", 1120, 1012, t, T_FAST, size=130, fill=P_["yellow"], seed=9711 + yrs % 7, dur=0.18)
    _wash(cv, (255, 250, 225), 230 * (1 - _k(t, T_SEAS0, T_SEAS0 + 0.22)))


GREY_CF = skia.ColorFilters.Matrix([0.26, 0.5, 0.1, 0, 0.02, 0.26, 0.5, 0.1, 0, 0.02, 0.26, 0.5, 0.12, 0, 0.05, 0, 0, 0, 1, 0])
T_WAVE0, T_WAVE1 = 15.6, 17.15


def _colour_world(cv, t, wave_r, wx, wy, seed=9800):
    """The real world of T030 (trees, flowers, people, Gary), lit by the sun up in the top-left corner."""
    _day_sky(cv, t, glare=(wx, wy), horizon=640, bright=0.6)
    _day_hills(cv, t)
    _ptree(cv, 1250, 800, 1.2, t, season="psy", seed=7320, face=True, look=-0.6)
    _ptree(cv, 1700, 700, 0.7, t, season="autumn", seed=7310)
    _ptree(cv, 840, 700, 0.55, t, season="spring", seed=7300)
    for k, (px, py, ps, body, head, kind) in enumerate(((1460, 870, 0.74, P_["blue"], P_["peach"], 0), (1630, 890, 0.66, P_["magenta"], P_["mint"], 1),
                                                        (1810, 870, 0.76, P_["orange"], P_["lilac"], 2), (1000, 880, 0.62, P_["teal"], P_["yellow"], 3))):
        hit = wave_r - math.hypot(px - wx, py - 250 - wy)
        hop = 40 * math.sin(min(1.0, max(0.0, hit / 260.0)) * math.pi)
        _person(cv, px, py, ps, t, body=body, head=head, seed=7400 + k * 17, wave=1.0 if hit > 0 else 0.0, kind=kind, look=-0.8, hop=hop)
    hitg = wave_r - math.hypot(560 - wx, 590 - wy)
    _gary(cv, 560, 590, 0.82, t, look=(-0.55, -0.5) if hitg > 0 else (0.0, 0.2), lid=0.0 if hitg > 0 else 0.35, mouth="grin" if hitg > 0 else "flat",
          arms=("up", "up") if hitg > 0 else ("rest", "rest"), shine=1.0 if hitg > 0 else 0.0)
    for k, (fx, fy, fs, col) in enumerate(((720, 1040, 1.2, P_["hotpink"]), (890, 1075, 0.95, P_["orange"]), (1100, 1045, 1.25, P_["violet"]),
                                          (1300, 1080, 1.0, P_["red"]), (1510, 1050, 1.2, P_["teal"]), (1700, 1080, 0.95, P_["magenta"]),
                                          (1880, 1045, 1.15, P_["yellow"]), (300, 1050, 1.1, P_["orange"]), (120, 1020, 0.9, P_["hotpink"]))):
        hit = wave_r - math.hypot(fx - wx, fy - 120 - wy)
        _flower(cv, fx, fy, fs, t, petal=col, seed=7600 + k * 11, sing=0.8 if hit > 0 else 0.0, sleep=0.0 if hit > 0 else 0.9, look=-0.7)


def _colour_wave(cv, t, T):
    """15.06..17.5 'It's what lets you see anything at all.' -- a grey, sightless world; the sun opens its eyes and a wave
    of colour rolls out from it, flooding everything with neon."""
    wx, wy = 300, 210
    wave_r = 0.0 if t < T_WAVE0 else 240 + 2400 * _k(t, T_WAVE0, T_WAVE1) ** 1.25
    _colour_world(cv, t, wave_r, wx, wy)
    wake = _k(t, 15.25, 15.6)
    _corona(cv, wx, wy, 130, t, k=0.35 + 0.65 * wake)
    img = cv.getSurface().makeImageSnapshot()
    outside = skia.Path()
    outside.addRect(R(-10, -10, W + 10, H + 10))
    if wave_r > 1:
        outside.addCircle(wx, wy, wave_r)
        outside.setFillType(skia.PathFillType.kEvenOdd)
    cv.save()
    cv.resetMatrix()
    cv.clipPath(outside, doAntiAlias=True)
    pg = skia.Paint(ColorFilter=GREY_CF)
    cv.drawImage(img, 0, 0, skia.SamplingOptions(), pg)
    _wash(cv, (20, 16, 30), 70)
    cv.restore()
    with _tint(cv, (150, 150, 160), 0.75 * (1 - wake)):
        _sun(cv, wx, wy, 130, t, lids=(1.0 - 0.7 * wake, 1.0 - 0.7 * wake), look=(0.6, 0.5), smile=0.3 + 0.5 * wake, glow=wake)
    if 1 < wave_r < 2600:                                             # the wave front: a rainbow ring with sparkles
        for j, col in enumerate((P_["violet"], P_["teal"], P_["acid"], P_["yellow"], P_["orange"], P_["magenta"])):
            cv.drawPath(poly_path(ell(wx, wy, max(1.0, wave_r - j * 16), max(1.0, wave_r - j * 16), n=72)), paint(col, 220, stroke=16))
        brush(cv, ell(wx, wy, wave_r + 9, wave_r + 9, n=72), 5, closed=True, seed=9900)
        for k in range(16):
            a = k * 0.39 + t * 0.6
            sparkle(cv, wx + (wave_r + 6) * math.cos(a), wy + (wave_r + 6) * math.sin(a), 16 + 6 * math.sin(t * 6 + k), P_["white"], w=2.5, seed=9910 + k)
    _label(cv, "LIGHT!", 1500, 260, t, T_WAVE0 + 0.5, size=120, fill=P_["yellow"], seed=9920, fills=[P_["yellow"], P_["orange"], P_["hotpink"], P_["acid"], P_["teal"]])


# ---------------------------------------------------------------- the chain: sun -> light -> cave mouth -> fire -> puppets -> shadows
CH_SUN = (2900, -720)
CH_PATH = [(2900, -720), (2420, -330), (1930, 110), (1760, 330), (1590, 560), (1530, 700), (1380, 600), (1150, 470), (700, 430), (260, 420)]
CH_NODES = [(0.0, "THE SUN", (2900, -1010), P_["yellow"]), (0.2, "LIGHT", (2690, -330), P_["cream"]), (0.52, "FIRE", (1700, 560), P_["orange"]),
            (0.66, "PUPPETS", (1150, 300), P_["mint"]), (0.98, "SHADOWS", (300, 150), P_["hotpink"])]
HILL_TOP = [(-700, -330), (0, -380), (600, -420), (1100, -420), (1500, -330), (1780, -160), (1960, 20)]
CAVE_CLIP = HILL_TOP + [(2010, 150), (2050, 1700), (-700, 1700)]


def _poly_len(P):
    P = np.asarray(P, float)
    d = np.hypot(*np.diff(P, axis=0).T)
    return np.concatenate([[0.0], np.cumsum(d)])


def _partial(P, frac):
    P = np.asarray(P, float)
    L = _poly_len(P)
    tgt = frac * L[-1]
    out = [P[0]]
    for i in range(1, len(P)):
        if L[i] <= tgt:
            out.append(P[i])
        else:
            u = (tgt - L[i - 1]) / max(1e-6, L[i] - L[i - 1])
            out.append(P[i - 1] + (P[i] - P[i - 1]) * u)
            break
    return np.array(out)


def _chain_path(cv, frac, t):
    """The glowing dotted causal chain, drawn progressively, with a bright head and arrowheads at the nodes."""
    if frac <= 0:
        return
    C = cr_open(np.array(CH_PATH, float), 12)
    Pp = _partial(C, frac)
    if len(Pp) < 2:
        return
    path = open_path_pts(Pp.tolist())
    cv.drawPath(path, paint((255, 230, 120), 70, stroke=34))
    p = paint((255, 246, 200), 255, stroke=12)
    dash = skia.Paint(p)
    dash.setPathEffect(skia.DashPathEffect.Make([4.0, 30.0], -t * 120))
    cv.drawPath(path, dash)
    hx, hy = Pp[-1]
    _glow(cv, hx, hy, 120, (255, 250, 210), 230)
    sparkle(cv, hx, hy, 30, P_["white"], w=3, seed=9950)


def _bunny_pos(t):
    return 170 + 6 * math.sin(t * 2), 430 - abs(math.sin(t * 4.2)) * 40


def _chain_world(cv, t, frac, view, seed=9960):
    """The cutaway world (world coords): sky + the sun outside, the hill with the cave inside, the meadow, Gary.
    view = visible world rect (x0, y0, x1, y1); anything entirely outside it is skipped."""
    vx0, vy0, vx1, vy1 = view

    def vis(x0, y0, x1, y1):
        return not (x1 < vx0 or x0 > vx1 or y1 < vy0 or y0 > vy1)
    _lin(cv, (0, -1700), (0, 250), [(70, 110, 255), (150, 200, 255), (255, 230, 190)], rect=R(-3000, -3000, 6000, 600))
    sx_, sy_ = CH_SUN
    if vis(-800, -1800, 4400, 260):
        _rays(cv, *CH_SUN, 200, 4200, 24, t * 3, (255, 240, 160), 110, width=0.5, wob=0.3, t=t)
    for k, (qx, qy) in enumerate(((300, -950), (1150, -800), (1950, -1020), (3750, -860), (4400, -1000))):
        if vis(qx - 260, qy - 140, qx + 260, qy + 120):
            _cloud(cv, qx + 30 * math.sin(t * 0.4 + k), qy, 1.6, seed=seed + k * 3, face=(k == 1), t=t)
    if vis(sx_ - 1000, sy_ - 1000, sx_ + 1000, sy_ + 1000):
        _corona(cv, *CH_SUN, 230, t, k=1.0)
        _sun(cv, *CH_SUN, 230, t, lids=(0.3, 0.3), look=(-0.7, 0.6), smile=0.7)
    if vis(-800, -460, 4300, 300):
        xs = np.linspace(-800, 4200, 60)                               # distant rainbow ranges outside
        for j, (base, amp, cols) in enumerate(((-300, 120, (P_["violet"], P_["lilac"], P_["hotpink"])), (-120, 110, (P_["magenta"], P_["orange"], P_["yellow"])))):
            ys = base - amp * (0.5 + 0.5 * np.sin(xs / 700.0 + j * 1.7))
            _band_hill(cv, xs, ys, list(cols), stripe=26, seed=seed + 20 + j, ink=5)
    earth = HILL_TOP + [(2010, 150), (2300, 160), (2800, 140), (3400, 170), (4300, 150), (4300, 1800), (-700, 1800)]

    def strata(c):
        for k in range(9):                                          # violet strata bands + sparse grain (cheap for a huge slab)
            yy = -260 + k * 230
            if not vis(-800, yy - 60, 4400, yy + 130):
                continue
            xs_ = np.linspace(-800, 4400, 14)
            ys_ = yy + 40 * np.sin(xs_ / 520.0 + k * 1.3)
            c.drawPath(poly_path(list(zip(xs_, ys_)) + list(zip(xs_[::-1], ys_[::-1] + 70))), paint(mix(CV_ROCK, CV_ROCK2, 0.45 if k % 2 else 0.0)))
            line(c, np.stack([xs_, ys_], 1)[::2], 3.5, mix(CV_ROCK, INK, 0.35), seed=seed + 31 + k, boil=0.8, n=4, taper=(0.05, 0.05), a=170)
        bx0, by0, bx1, by1 = max(-700, vx0 - 50), max(-420, vy0 - 50), min(4300, vx1 + 50), min(1800, vy1 + 50)
        if bx1 > bx0 and by1 > by0:
            stipple(c, mix(CV_ROCK, INK, 0.45), (bx0 - bx0 % 46, by0 - by0 % 40, bx1, by1), spacing=46, r=3.2, seed=seed + 33)
    if vis(-700, -430, 4300, 1800):
        blob(cv, earth, CV_ROCK, w=6, seed=seed + 30, boil=1.1, n=4, shade=strata)
    for k, (qx, qy) in enumerate(((2350, 520), (2900, 880), (3500, 600), (3900, 1050), (2600, 1250))):      # the cutaway's buried treasures
        if vis(qx - 150, qy - 200, qx + 150, qy + 60):
            crystal(cv, qx, qy, 1.2, t, seed=seed + 100 + k)
    for k in range(3):
        if vis(2200 + k * 520, 250, 2700 + k * 520, 750):
            w.worm(cv, 2500 + k * 520, 380 + 300 * (k % 2), 0.9, t * 1.5 + k, seed=seed + 120 + k)
    for k, rx in enumerate((2620, 3300)):                          # roots under the meadow trees
        if vis(rx - 200, 160, rx + 200, 520):
            for j in range(3):
                line(cv, [(rx, 170), (rx + (j - 1) * 60, 300), (rx + (j - 1) * 140, 420 + 40 * j)], 9, (150, 90, 150), seed=seed + 130 + k * 3 + j, boil=0.8, n=4,
                     taper=(0, 0.8))
    if vis(-700, -430, 2060, 1700):
        cv.save()
        cv.clipPath(poly_path(cr_closed(np.array(CAVE_CLIP, float), 3)), doAntiAlias=True)
        bx, by = _bunny_pos(t)
        sh = [("bunny", bx, by, 1.15), ("horse", 330 - (t * 60) % 700, 470, 0.9)]
        cave_side(cv, T=317.3 + t, cam=dict(x=0, y=0, z=1.0), wall_shadows=sh)
        gk = _k(t, 21.75, 22.4)
        if gk > 0:                                                      # even the shadow is made by the light: a golden rim
            cv.save()
            cv.translate(bx, by)
            cv.scale(1.15 * 1.1, 1.15 * 1.1)
            P = np.array(SHAPES["bunny"], float)
            pth = poly_path(cr_closed(P, 4))
            gp = skia.Paint(AntiAlias=True, Color=core.C((255, 220, 90), int(170 * gk)))
            gp.setStyle(skia.Paint.kStroke_Style)
            gp.setStrokeWidth(16)
            gp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 8))
            cv.drawPath(pth, gp)
            cv.drawPath(pth, paint((255, 240, 160), int(255 * gk), stroke=4))
            cv.restore()
            for k in range(5):
                a = t * 1.5 + k * 1.26
                sparkle(cv, bx + 120 * math.cos(a), by - 40 + 130 * math.sin(a), 12 * gk, P_["yellow"], w=2, seed=9990 + k)
        cv.restore()
    if vis(-700, -500, 2000, 100):
        top = np.array(HILL_TOP + [(1975, 60)], float)                  # grass along the hill
        grass = cr_open(top, 8)
        cv.drawPath(open_path_pts(grass.tolist()), paint(P_["acid_dk"], stroke=70))
        cv.drawPath(open_path_pts((grass + np.array([0, -14])).tolist()), paint(P_["acid"], stroke=40))
        brush(cv, grass + np.array([0, -36]), 6, taper=(0.02, 0.05), seed=seed + 40)
    if vis(1950, 80, 4300, 230):
        mead = cr_open(np.array([(2000, 160), (2300, 160), (2800, 140), (3400, 170), (4300, 150)], float), 8)
        cv.drawPath(open_path_pts(mead.tolist()), paint(P_["acid_dk"], stroke=70))
        cv.drawPath(open_path_pts((mead + np.array([0, -14])).tolist()), paint(P_["acid"], stroke=40))
        brush(cv, mead + np.array([0, -36]), 6, taper=(0.05, 0.02), seed=seed + 41)
    for (tx, ty, ts, season, sd, face) in ((700, -440, 1.1, "psy", 50, True), (1250, -440, 0.8, "summer", 51, False), (3300, 150, 1.0, "spring", 52, False),
                                           (2620, 150, 0.7, "autumn", 53, False)):
        if vis(tx - 260 * ts, ty - 520 * ts, tx + 260 * ts, ty + 10):
            _ptree(cv, tx, ty, ts, t, season=season, seed=seed + sd, face=face, look=0.8)
    for k, fx in enumerate((150, 380, 1000, 1500, 2600, 2900, 3600, 3900)):
        fy = float(np.interp(fx, [p_[0] for p_ in HILL_TOP], [p_[1] for p_ in HILL_TOP])) - 26 if fx < 1960 else 128
        if vis(fx - 80, fy - 200, fx + 80, fy + 10):
            _flower(cv, fx, fy, 1.1, t, petal=[P_["hotpink"], P_["orange"], P_["violet"], P_["teal"]][k % 4], seed=seed + 60 + k * 7, sing=0.4)
    if vis(2050, -300, 2550, 160):
        _gary(cv, 2300, -82, 0.62, t, look=(0.55, -0.7), lid=0.0, mouth="grin", arms=("rest", "up"), shine=0.8, light=((255, 220, 120), -50, 0.9))


def _cam_spline(keys, t):
    """Smooth (Catmull-Rom, eased at both ends) camera through timed keys (t, x, y, z)."""
    ts = [k[0] for k in keys]
    if t <= ts[0]:
        return keys[0][1:]
    if t >= ts[-1]:
        return keys[-1][1:]
    u = _k(t, ts[0], ts[-1])
    tt = ts[0] + u * (ts[-1] - ts[0])
    j = max(0, min(len(ts) - 2, int(np.searchsorted(ts, tt) - 1)))
    f = (tt - ts[j]) / (ts[j + 1] - ts[j])
    P = [np.array(k[1:], float) for k in keys]
    p0, p1, p2, p3 = P[max(0, j - 1)], P[j], P[j + 1], P[min(len(P) - 1, j + 2)]
    out = 0.5 * ((2 * p1) + (-p0 + p2) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f * f + (-p0 + 3 * p1 - 3 * p2 + p3) * f ** 3)
    return tuple(out)


def _chain(cv, t, T):
    """17.5..23.19 'In a way, it was behind everything he ever saw. Even the shadows.' -- a dreamy diagram move from the
    sun, down its light into the cave mouth, to the fire, the puppets and finally the shadows on the wall."""
    keys = [(17.55, 2900, -720, 1.45), (19.0, 2150, -170, 0.52), (20.2, 1500, 300, 0.7), (21.1, 1000, 470, 0.95), (22.1, 390, 470, 1.22), (23.2, 360, 470, 1.32)]
    cx, cy, z = _cam_spline(keys, t)
    frac = _k(t, 18.6, 21.9) ** 1.1
    view = (cx - W / 2 / z, cy - H / 2 / z, cx + W / 2 / z, cy + H / 2 / z)
    with _cam(cv, cx, cy, z):
        _chain_world(cv, t, frac, view)
        _chain_path(cv, frac, t)
    for k, (f0, text, (lx, ly), col) in enumerate(CH_NODES):
        t0 = 17.75 if k == 0 else 18.6 + (21.9 - 18.6) * f0 ** (1 / 1.1)
        sx, sy = _cam_pt(lx, ly, cx, cy, z)
        if -200 < sx < W + 200 and -100 < sy < H + 200:
            _label(cv, text, float(np.clip(sx, 220, W - 220)), float(np.clip(sy, 120, H - 60)), t, t0, size=86 if k < 4 else 120, fill=col, seed=9980 + k)
    _wash(cv, (255, 250, 225), 200 * (1 - _k(t, 17.5, 17.85)))


def T031_sun(cv, t, T, A):
    if t < 5.71:
        _sun_rise(cv, t, T)
    elif t < 7.8:
        _sun_hey(cv, t, T)
    elif t < T_SEAS0:
        _gary_whoa(cv, t, T)
    elif t < 15.06:
        _seasons(cv, t, T)
    elif t < 17.5:
        _colour_wave(cv, t, T)
    else:
        _chain(cv, t, T)
