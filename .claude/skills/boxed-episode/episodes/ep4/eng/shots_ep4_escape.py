"""BOXED ep4 'THE CAVE' -- owner `escape`: the freed prisoner (Gary) is unchained, turned to the fire, shown the puppets
and dragged up into the sun.

  T023_set_free        Z12: a big key turns in Gary's collar padlock, the chains fall, he wobbles up and turns around.
  T026_fire_hurts      Z13 + G02: the fire blinds him -- pinned pupil, white glare -- 'MY EVERYTHING!'
  T027_puppets_reveal  Z14 + G03: a carrier points at the statues (dotted arrows to their shadows); Gary sulks and hugs
                       the bunny shadow: 'Put me back.'
  T029_dragged         Z15 + ASCENT + G04: two carriers drag him up the steep path, a climbing montage, a white-out,
                       'TOO MUCH OUTSIDE!'

Gary is drawn with `gary_x`, an extended, turnable re-drawing of eyeball_creature (same proportions / colours /
sweater / lid) that adds a 3-D yaw (back view -> profile -> front), legs, two posable arms, the iron collar, and
expressions: lid / squint / squeeze-shut, pinned or dilated pupil, scream / pout / skeptical mouths, tears, sweat.
"""
from .shots_ep4_base import *          # noqa: F401,F403
from .shots_ep4_base import (P_, R, PAL, INK, W, H, paint, poly_path, cr_closed, cr_open, ell, blob, line, brush, dots, hsh, mix,
                             jit, rot, sparkle, rect_pts, tube, stipple, core, w, sets, paint_text, _hand, ease, pop, lerp,
                             loud_at, vis_at, spk_loud, firelight, cave_fire, rock_mass, chain, prisoner, carrier, statue,
                             shadow_shape, SHAPES, crystal, glow_mushroom, handprint, sun_rays, wall_surface, vignette,
                             CV_ROCK, CV_ROCK2, CV_ROCK_DK, CV_WALL, CV_WALL2, CV_SHADOW, CV_FIRE)
import math
import numpy as np
import skia

TEAR = (160, 228, 255)
TEAR_DK = (70, 150, 235)
IRON = (140, 140, 172)
IRON_DK = (86, 84, 120)
HOOD = (40, 18, 66)
HOOD_HI = (92, 48, 140)
BRASS = (255, 196, 40)
BRASS_DK = (214, 120, 20)


def _cl(v, a=0.0, b=1.0):
    return float(min(b, max(a, v)))


def _seg(t, a, b):
    """0 before a, 1 after b, smooth in between."""
    return ease((t - a) / max(1e-6, b - a))


def _bl(c, k):
    return mix(c, P_["white"], k) if k > 0 else c


def _shake(cv, amp, seed=0, rot_amp=0.0):
    """Per-drawing camera shake (call first; scales up a touch so no edges show)."""
    if amp <= 0:
        return
    dx = (float(hsh(core.D * 1.37 + seed)) - 0.5) * 2 * amp
    dy = (float(hsh(core.D * 2.11 + seed + 5)) - 0.5) * 2 * amp
    sc = 1 + 2.2 * amp / W
    cv.translate(W / 2 + dx, H / 2 + dy)
    if rot_amp:
        cv.rotate((float(hsh(core.D * 0.77 + seed + 9)) - 0.5) * 2 * rot_amp)
    cv.scale(sc, sc)
    cv.translate(-W / 2, -H / 2)


def _ink_scale(s):
    return min(4.0, max(0.55, s)) ** 0.5


# ===================================================================== GARY, extended
def _lid_poly(cx, cy, s, yaw, h_side, h_front, tilt, N=25):
    """Visible violet lid region (screen polygon) and its lower edge (the crease), for a bowl-shaped lid on Gary's
    eyeball turned by `yaw` degrees. Heights are relative to the eye centre (negative = up)."""
    Rr = 150.0 * s
    th = math.radians(yaw)
    edge = []
    for b in np.linspace(-math.pi / 2, math.pi / 2, N):
        phi = b - th
        phi = (phi + math.pi) % (2 * math.pi) - math.pi
        wf = math.cos(phi) ** 2 if abs(phi) < math.pi / 2 else 0.0
        h = h_side + (h_front - h_side) * wf + tilt * s * math.sin(phi) * (abs(math.cos(phi)) if abs(phi) < math.pi / 2 else 0.0)
        h = min(max(h, -Rr * 0.995), Rr * 0.995)
        rh = math.sqrt(max(0.0, Rr * Rr - h * h))
        edge.append((cx + rh * math.sin(b), cy + h))
    a_r = math.atan2(edge[-1][1] - cy, edge[-1][0] - cx)
    a_l = math.atan2(edge[0][1] - cy, edge[0][0] - cx)
    if a_l > 0:
        a_l -= 2 * math.pi
    if a_r < a_l:
        a_r += 2 * math.pi
    top = []
    for a in np.linspace(a_r, a_l, 16)[1:-1]:
        rr = Rr * (1.025 + 0.012 * math.sin(a * 3))
        top.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return edge, edge + top


def _arm_pts(sh, hand, bend=1.0, seg=78.0):
    """Rubber-hose arm: shoulder -> elbow -> wrist; the elbow sits where two segments of length `seg` meet (IK),
    pushed to the `bend` side (+1 / -1); a slight hose curve is kept even when the arm is fully stretched."""
    sx, sy = sh
    hx, hy = hand
    mx, my = (sx + hx) / 2, (sy + hy) / 2
    dx, dy = hx - sx, hy - sy
    L = math.hypot(dx, dy) + 1e-6
    nx, ny = -dy / L, dx / L
    off = math.sqrt(max(0.0, seg * seg - (L / 2) ** 2)) + 0.06 * L
    return [(sx, sy), (mx + nx * off * bend, my + ny * off * bend), (hx, hy)]


def gary_x(cv, x, fy, s, T, seed=4400, yaw=0.0, look=(0.0, 0.0), lid=None, tilt=0.0, squint=0.0, shut=0.0, crinkle=0.0,
           pupil=None, iris=1.0, mouth="auto", mo=None, loud=None, tears=0.0, tear_dir=1.0, tear_up=0.0, sweat=0.0, veins=0.0,
           stand=0.0, lean=0.0, knees=0.0, step=None, feet=None, arms=None, collar=False, light=None, bleach=0.0,
           bob=1.0, glint=True, shock=0.0, eye_scale=1.0, hyaw=None, arms_only=False, arms_off=False):
    """Gary (on-model re-drawing of eyeball_creature, extended). (x, fy) = floor point under him; s = scale
    (eye radius 150*s, sweater 360*s tall, legs 118*s when stand=1).
      yaw     0 front, +90 facing screen-right, -90 facing screen-left, 180 back view
      look    iris offset (-1..1); lid 0 (wide) .. 1 (half shut) [default: breathing 0.25..0.45]; tilt = lid slant
      squint  lower-lid crease 0..1; shut 0..1 = lid closed; crinkle = squeezed-shut wrinkles
      pupil   radius as a fraction of the iris (0.07 pinned .. 0.8 dilated); iris = iris scale
      mouth   'auto' (talk/smile) | 'smile' | 'frown' | 'flat' | 'wobbly' | 'scream' | 'pout' | 'o' | 'grin'; mo = openness
      arms    dict(L=..., R=...) each dict(hand=(hx, hy[, hz]) in s-units relative to the eye centre (front-view coords),
              or world=(X, Y) screen coords; pose, ang, mirror, bend, behind)
      stand   0 sitting on the floor .. 1 standing on little legs; lean = upper-body tilt (deg); knees = wobble
      step    walk phase (radians) or None; feet = [(X, Y), (X, Y)] world positions (dangling / dragged)
      light   dict(dir=(dx, dy) toward the light, a=0..1, rgb) -- cel crescent + warm glaze
      bleach  0..1 washes his colours toward white (overexposed world)"""
    old_ink = core.INKMUL
    core.INKMUL = old_ink * _ink_scale(s)
    th = math.radians(yaw)
    cth, sth = math.cos(th), math.sin(th)
    hyaw = yaw if hyaw is None else hyaw
    hth = math.radians(hyaw)
    face = math.cos(hth) > 0.0
    bk = bleach
    inkc = mix(INK, (200, 170, 150), bk * 0.75) if bk > 0 else INK
    cream, orange, white, violet = _bl(P_["cream"], bk), _bl(P_["orange"], bk), _bl(P_["white"], bk * 0.5), _bl(P_["violet"], bk)
    red = _bl(P_["red"], bk)
    LL = 108.0 * s
    hip_y = fy - LL * stand
    eb = 6 * math.sin(T * 3.1) * s * bob
    ecx, ecy = 0.0, -360.0 * s + eb                 # eye centre in body coords (hip at the origin)
    rr = 150.0 * s * eye_scale

    def to_world(px, py):
        a = math.radians(lean)
        return x + px * math.cos(a) - py * math.sin(a), hip_y + px * math.sin(a) + py * math.cos(a)

    def to_local(X, Y):
        a = math.radians(-lean)
        dx, dy = X - x, Y - hip_y
        return dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a)

    # ---------------------------------------------------------------- legs (world space, behind the sweater)
    leg_draw = []
    if (stand > 0.02 or feet is not None) and not arms_only:
        for side in (-1, 1):
            hx_l, hy_l = side * 50 * s * abs(cth) + side * 14 * s * (1 - abs(cth)), -14 * s
            hipw = to_world(hx_l, hy_l)
            if feet is not None:
                fx, fyy = feet[0 if side < 0 else 1]
            else:
                fx = x + side * 46 * s * abs(cth) + side * 16 * s * (1 - abs(cth))
                fyy = fy
                if step is not None:
                    ph = step + (0 if side < 0 else math.pi)
                    fx += sth * 34 * s * math.sin(ph) + (0 if abs(sth) > 0.3 else side * 6 * s * math.sin(ph))
                    fyy -= 20 * s * max(0.0, math.cos(ph))
            kx = (hipw[0] + fx) / 2 + side * knees * 34 * s + sth * 10 * s
            ky = (hipw[1] + fyy) / 2 - 4 * s
            leg_draw.append((side, hipw, (kx, ky), (fx, fyy)))
        for side, hipw, kn, ft in leg_draw:
            tube(cv, [hipw, kn, (ft[0], ft[1] - 14 * s)], 25 * s, cream, w=4.5, ink=inkc, seed=seed + 70 + side, boil=0.8, n=6)
            fdir = sth if abs(sth) > 0.25 else 0.0
            shoe = [(ft[0] - 30 * s + fdir * 4 * s, ft[1]), (ft[0] - 28 * s + fdir * 10 * s, ft[1] - 22 * s), (ft[0] + fdir * 14 * s, ft[1] - 27 * s),
                    (ft[0] + 30 * s + fdir * 22 * s, ft[1] - 16 * s), (ft[0] + 33 * s + fdir * 22 * s, ft[1])]
            blob(cv, shoe, red, w=4.0, ink=inkc, seed=seed + 74 + side, boil=0.6,
                 shade=lambda c, ft=ft: c.drawRect(R(ft[0] - 40 * s, ft[1] - 4 * s, ft[0] + 40 * s, ft[1] + 10 * s), paint(_bl(P_["white"], bk))))

    cv.save()
    cv.translate(x, hip_y)
    cv.rotate(lean)

    # ---------------------------------------------------------------- arms (split into behind / in front)
    sh_pts = {}
    arm_specs = []
    arms = arms or {}
    for side, key in ((-1, "L"), (1, "R")):
        spec = dict(hand=(side * 140, 330, 0.0), pose="open", ang=None, bend=-side * 1.0)
        spec.update(arms.get(key, {}) or {})
        sx0 = side * 104.0 * s
        shx, shz = sx0 * cth, -sx0 * sth
        shp = (shx, -170.0 * s)
        if "world" in spec and spec["world"] is not None:
            hp = to_local(*spec["world"])
            hz = shz
        else:
            hx, hy = spec["hand"][0] * s, spec["hand"][1] * s - 360.0 * s
            hz0 = (spec["hand"][2] if len(spec["hand"]) > 2 else 0.0) * s
            hp = (hx * cth + hz0 * sth, hy)
            hz = -hx * sth + hz0 * cth
        behind = spec.get("behind")
        if behind is None:
            behind = (shz + hz) * 0.5 < -30 * s
        arm_specs.append((side, spec, shp, hp, behind))
        sh_pts[key] = shp

    def draw_arm(side, spec, shp, hp):
        if spec.get("elbow") is not None:
            el = (spec["elbow"][0] * s, spec["elbow"][1] * s - 360.0 * s)
            pts = [shp, el, hp]
        else:
            pts = _arm_pts(shp, hp, bend=spec.get("bend", -side) * (1 if cth >= 0 else -1), seg=78.0 * s * spec.get("reach", 1.0))
        tube(cv, pts, 22 * s, cream, w=4.5, ink=inkc, seed=seed + 50 + side, boil=0.8, n=8)
        ang = spec.get("ang")
        if ang is None:
            ang = math.degrees(math.atan2(pts[2][1] - pts[1][1], pts[2][0] - pts[1][0]))
        mir = spec.get("mirror", 1 if side < 0 else -1)
        cv.save(); cv.translate(*hp); cv.scale(s * 1.15, s * 1.15)
        _hand(cv, 0, 0, ang, spec.get("pose", "open"), mir, seed + 52 + side * 7, rgb=white)
        cv.restore()

    if arms_only:
        for side, spec, shp, hp, behind in arm_specs:
            if not behind:
                draw_arm(side, spec, shp, hp)
        cv.restore()
        core.INKMUL = old_ink
        return None
    for side, spec, shp, hp, behind in arm_specs:
        if behind and not arms_off:
            draw_arm(side, spec, shp, hp)

    # ---------------------------------------------------------------- sweater
    sw = [(-128 * s, 0), (-110 * s, -190 * s), (-55 * s, -248 * s), (55 * s, -248 * s), (110 * s, -190 * s), (128 * s, 0)]
    L_ = light

    def sw_shade(c):
        for k in range(3):
            c.drawRect(R(-140 * s, (-128 + k * 46) * s, 140 * s, (-110 + k * 46) * s), paint(orange))
        if L_:
            _cel(c, 0, -124 * s, 150 * s, L_, bk)
    blob(cv, sw, cream, w=5, ink=inkc, seed=seed, boil=1.0, n=6, shade=sw_shade)
    if cth > 0.15:
        gx = 112 * s * sth
        cv.save(); cv.translate(gx, -60 * s); cv.scale(max(0.08, cth), 1.0)
        paint_text(cv, "G", 0, 0, font="shrik", size=76 * s, fill=red, ink_w=4, outline_rgb=inkc, shadow=None, seed=seed + 30, streaks=False)
        cv.restore()

    # ---------------------------------------------------------------- eyeball
    nv = 8 + int(10 * veins)

    def eye_shade(c):
        for k, a in enumerate(np.linspace(0, 6.0, nv)):
            l1 = 150 * s
            l2 = (100 - 40 * veins * (k % 2)) * s
            pts = [(ecx + l1 * math.cos(a), ecy + l1 * math.sin(a)), (ecx + l2 * math.cos(a + 0.25), ecy + l2 * math.sin(a + 0.25))]
            if veins > 0 and k % 2 == 0:
                pts.append((ecx + (l2 - 26 * s) * math.cos(a + 0.05), ecy + (l2 - 26 * s) * math.sin(a + 0.05)))
            line(c, pts, 3.5 + 1.5 * veins, red, seed=seed + 10 + k, boil=0.8, n=3)
        if L_:
            _cel(c, ecx, ecy, rr, L_, bk)
    blob(cv, ell(ecx, ecy, rr, rr, n=14), white, w=6, ink=inkc, seed=seed + 4, boil=1.2, shade=eye_shade)
    eye_clip = poly_path(cr_closed(ell(ecx, ecy, rr - 2, rr - 2, n=18), 4))

    # iris + pupil (projected on the sphere; hidden from behind)
    ir = 66 * s * iris
    ia = hth + math.radians(28 * look[0])
    ca, sa = math.cos(ia), math.sin(ia)
    ex = -4 * s * ca + 136 * s * sa
    ey = ecy - 22 * s + look[1] * 30 * s
    if ca > -0.05:
        fx = max(0.06, ca)
        cv.save(); cv.clipPath(eye_clip, doAntiAlias=True)
        if squint > 0:
            cut = ey + ir * (1.0 - 1.15 * squint)
            cv.clipRect(R(-400 * s, -900 * s, 400 * s, cut))
        blob(cv, ell(ex, ey, ir * fx, ir, n=11), _bl(P_["teal"], bk), w=4.5, ink=inkc, seed=seed + 5, boil=0.8,
             shade=lambda c: c.drawPath(poly_path(cr_closed(ell(ex + 10 * s * fx, ey + 12 * s, ir * 0.8 * fx, ir * 0.75, n=8), 4)), paint(_bl(P_["tealdk"], bk))))
        if shock > 0:
            for k in range(10):
                a = k * 0.628 + 0.3
                line(cv, [(ex + ir * 0.5 * fx * math.cos(a), ey + ir * 0.5 * math.sin(a)), (ex + ir * 0.92 * fx * math.cos(a), ey + ir * 0.92 * math.sin(a))],
                     2.4, _bl(P_["mint"], bk), seed=seed + 90 + k, boil=0.5, n=2, taper=(0.1, 0.5), a=int(220 * shock))
        L0 = 0.0 if loud is None else loud
        pr = ir * (pupil if pupil is not None else (0.42 + 0.22 * min(1.0, L0)))
        blob(cv, ell(ex, ey, pr * fx, pr, n=9), inkc, w=0, seed=seed + 6, boil=0.5 if pr > 6 else 0.2, misreg=(0, 0))
        if glint:
            gr = max(2.5 * s, pr * 0.28) if pupil is None or pupil > 0.2 else ir * 0.13
            dots(cv, [(ex - (pr * 0.45 + (gr if pupil is not None and pupil <= 0.2 else 0)) * fx, ey - max(pr * 0.5, ir * 0.25))], gr, P_["white"])
        cv.restore()

    # lid (bowl cap; front window lowers to close)
    if lid is None:
        lid = 0.25 + 0.2 * math.sin(T * 0.7)
    h_front = -150 * s + 105 * s * max(0.0, lid)
    h_side = -20 * s - 90 * s * _cl((0.25 - lid) / 0.45)
    if shut > 0:
        h_front = lerp(h_front, 64 * s, shut)
        h_side = lerp(h_side, 22 * s, shut)
    edge, lid_poly = _lid_poly(ecx, ecy, s * eye_scale, hyaw, h_side, h_front, tilt)
    blob(cv, lid_poly, violet, w=5, ink=inkc, seed=seed + 7, boil=1.0, n=3,
         shade=(lambda c: _cel(c, ecx, ecy, rr, L_, bk)) if L_ else None)
    if shut > 0.6 and face:                             # crease (and squeeze wrinkles)
        brush(cv, cr_open(jit(edge[2:-2], 0.8, seed + 8), 4), 6.5 * min(1.0, shut), inkc, taper=(0.15, 0.15), seed=seed + 8)
        if crinkle > 0:
            for k in range(3):
                off = (22 + 20 * k) * s
                sub = [(px, py - off * (1 - 0.6 * abs(px - ecx) / rr)) for px, py in edge[5:-5]]
                line(cv, sub[::2], 4.0 - k * 0.8, mix(violet, INK, 0.55), seed=seed + 120 + k, boil=1.2, n=4, taper=(0.3, 0.3), a=int(255 * crinkle))
            for side in (-1, 1):
                bx, by = ecx + side * rr * 0.96, ecy + h_side + 6 * s
                for k in range(3):
                    a = math.radians(side * (20 + k * 25)) + (0 if side > 0 else math.pi)
                    line(cv, [(bx + 14 * s * math.cos(a), by + 14 * s * math.sin(a)), (bx + 46 * s * math.cos(a), by + 46 * s * math.sin(a))], 4.0, inkc,
                         seed=seed + 130 + k + side * 5, boil=0.8, n=2, taper=(0.2, 0.4), a=int(255 * crinkle))
    if squint > 0.05 and face and ca > 0.1:              # lower-lid crease under the iris
        cut = ey + ir * (1.0 - 1.15 * squint)
        hw = ir * 1.35 * max(0.3, ca)
        line(cv, [(ex - hw, cut + 10 * s), (ex, cut - 3 * s), (ex + hw, cut + 10 * s)], 4.5, inkc, seed=seed + 9, boil=0.7, n=5, taper=(0.3, 0.3))

    # mouth (on the white, under the iris)
    mb = math.radians(hyaw + 10 * look[0])
    cm, sm = math.cos(mb), math.sin(mb)
    if cm > 0.12:
        fxm = max(0.15, cm)
        mx, my = 6 * s * cm + 118 * s * sm, ecy + 92 * s
        L0 = 0.0 if loud is None else loud
        md = mouth
        if md == "auto":
            md = "talk"
        if md == "talk":
            m_o = min(1.0, L0 * 1.5) if mo is None else mo
            if m_o > 0.08:
                mh = (5 + 30 * m_o) * s
                blob(cv, ell(mx, my + mh * 0.3, 34 * s * fxm, mh, n=10), _bl(P_["mouth"], bk), w=4.5, ink=inkc, seed=seed + 40, boil=0.7,
                     shade=lambda c: blob(c, ell(mx + 4 * s, my + mh * 1.1, 22 * s * fxm, mh * 0.6, n=8), _bl(P_["tongue"], bk), w=0, seed=seed + 41, boil=0.5, misreg=(0, 0)))
            else:
                line(cv, [(mx - 30 * s * fxm, my - 4 * s), (mx, my + 8 * s), (mx + 30 * s * fxm, my - 4 * s)], 4.5, inkc, seed=seed + 42, boil=0.6, n=6, taper=(0.3, 0.3))
        elif md in ("smile", "frown", "flat", "wobbly", "grin"):
            cu = {"smile": 1.0, "frown": -1.0, "flat": 0.1, "wobbly": 0.0, "grin": 1.4}[md]
            if md == "wobbly":
                pts = [(mx + (u - 0.5) * 66 * s * fxm, my + (6 * s if j % 2 else -4 * s)) for j, u in enumerate(np.linspace(0, 1, 7))]
            elif md == "flat":
                pts = [(mx - 30 * s * fxm, my + 2 * s), (mx + 4 * s, my + 1 * s), (mx + 30 * s * fxm, my - 7 * s)]
            else:
                pts = [(mx - 32 * s * fxm, my - 6 * s * cu), (mx, my + 10 * s * cu), (mx + 32 * s * fxm, my - 6 * s * cu)]
            if md == "grin":
                blob(cv, [pts[0], (mx, my + 34 * s), pts[2], (mx, my + 4 * s)], _bl(P_["mouth"], bk), w=4.5, ink=inkc, seed=seed + 44, boil=0.6, n=5)
            else:
                line(cv, pts, 5.0, inkc, seed=seed + 43, boil=0.6, n=6, taper=(0.3, 0.3))
        elif md == "scream":
            m_o = (0.7 + 0.3 * min(1.0, L0 * 1.3)) if mo is None else mo
            mh = (14 + 40 * m_o) * s
            mw = (30 + 14 * m_o) * s * fxm
            cy0 = my + mh * 0.25

            def sc_sh(c):
                blob(c, ell(mx + 3 * s, cy0 + mh * 0.75, mw * 0.7, mh * 0.45, n=8), _bl(P_["tongue"], bk), w=0, seed=seed + 46, boil=0.6, misreg=(0, 0))
                c.drawRect(R(mx - mw, cy0 - mh, mx + mw, cy0 - mh * 0.72), paint(_bl(P_["white"], bk * 0.5)))
                dots(c, [(mx, cy0 - mh * 0.35)], 6 * s, _bl(P_["maroon"], bk))
            blob(cv, ell(mx, cy0, mw, mh, n=12), _bl(P_["mouth"], bk), w=5, ink=inkc, seed=seed + 45, boil=1.0, shade=sc_sh)
        elif md == "pout":
            m_o = (0.0 if mo is None else mo) + min(0.7, L0 * 1.2)
            px_ = mx - 2 * s
            lip = ell(px_, my + 12 * s + 4 * s * m_o, 22 * s * fxm, (10 + 4 * m_o) * s, n=10)
            if m_o > 0.12:
                blob(cv, ell(px_, my + 4 * s, 14 * s * fxm, (4 + 10 * m_o) * s, n=8), _bl(P_["mouth"], bk), w=3.5, ink=inkc, seed=seed + 46, boil=0.6)
            blob(cv, lip, _bl(P_["tongue"], bk), w=4.5, ink=inkc, seed=seed + 47, boil=0.6,
                 shade=lambda c: dots(c, [(px_ - 8 * s * fxm, my + 9 * s)], 4 * s, P_["white"], a=200))
            line(cv, [(px_ - 38 * s * fxm, my + 12 * s), (px_ - 16 * s * fxm, my - 2 * s), (px_ + 16 * s * fxm, my - 2 * s), (px_ + 38 * s * fxm, my + 12 * s)], 5.5,
                 inkc, seed=seed + 48, boil=0.6, n=5, taper=(0.3, 0.3))
        elif md == "o":
            m_o = 0.5 if mo is None else mo
            blob(cv, ell(mx, my + 6 * s, (12 + 10 * m_o) * s * fxm, (12 + 16 * m_o) * s, n=9), _bl(P_["mouth"], bk), w=4.5, ink=inkc, seed=seed + 39, boil=0.7)

    # collar (iron band at the neck) -- dict(open=0..1, lock=bool) lets the halves spring apart
    if collar:
        co = collar if isinstance(collar, dict) else {}
        op = co.get("open", 0.0)
        cyc = -214 * s
        if op <= 0.0:
            P = [(-104 * s, cyc - 4 * s), (-60 * s, cyc - 20 * s), (0, cyc - 24 * s), (60 * s, cyc - 20 * s), (104 * s, cyc - 4 * s),
                 (104 * s, cyc + 14 * s), (60 * s, cyc + 26 * s), (0, cyc + 30 * s), (-60 * s, cyc + 26 * s), (-104 * s, cyc + 14 * s)]
            blob(cv, P, IRON, w=4.5, ink=inkc, seed=seed + 60, boil=0.7, n=4,
                 shade=lambda c: (c.drawPath(poly_path([(-110 * s, cyc + 10 * s), (0, cyc + 18 * s), (110 * s, cyc + 10 * s), (110 * s, cyc + 40 * s), (-110 * s, cyc + 40 * s)]),
                                             paint(IRON_DK)),
                                  dots(c, [(k * 34 * s, cyc + 2 * s + abs(k) * -3 * s) for k in (-2, -1, 1, 2)], 4.5 * s, IRON_DK)))
            if co.get("lock", False) and face:
                _padlock(cv, 0, cyc + 30 * s, 0.42 * s, seed + 64, inkc=inkc)
        else:
            for side in (-1, 1):
                ang = side * 38 * op
                dx = side * 70 * s * op
                cv.save(); cv.translate(dx, cyc + 40 * s * op * op); cv.rotate(ang)
                P = [(side * 4 * s, -20 * s), (side * 60 * s, -18 * s), (side * 102 * s, -6 * s), (side * 104 * s, 12 * s), (side * 60 * s, 24 * s), (side * 4 * s, 24 * s)]
                blob(cv, P, IRON, w=4.5, ink=inkc, seed=seed + 60 + side, boil=0.7, n=4,
                     shade=lambda c, side=side: (c.drawRect(R(-110 * s, 8 * s, 110 * s, 30 * s), paint(IRON_DK)),
                                                 dots(c, [(side * 30 * s, 2 * s), (side * 76 * s, 2 * s)], 4.5 * s, IRON_DK)))
                cv.restore()

    # arms in front
    for side, spec, shp, hp, behind in arm_specs:
        if not behind and not arms_off:
            draw_arm(side, spec, shp, hp)
    cv.restore()

    # ---------------------------------------------------------------- tears / sweat (world space)
    if tears > 0 and face:
        for side in (-1, 1):
            if side * sth < -0.6:
                continue
            bx, by = to_world(ecx + side * rr * 0.93 * max(0.35, abs(cth)) + 30 * s * sth, ecy + h_side + 14 * s)
            _tear_spray(cv, bx, by, side, s, T, tears, seed + 200 + side * 17, tear_dir, tear_up)
    if sweat > 0:
        for k in range(4):
            u = (T * 1.7 + k * 0.25) % 1.0
            side = -1 if k % 2 else 1
            a = math.radians(-90 + side * (35 + 18 * k))
            d = (150 + 120 * u) * s
            px, py = to_world(ecx + d * math.cos(a), ecy + d * math.sin(a) + 160 * s * u * u)
            _drop(cv, px, py, 15 * s * (1 - 0.3 * u), math.degrees(a) + 90, P_["mint"], seed + 230 + k, a=int(255 * sweat * (1 - u ** 3)))
    core.INKMUL = old_ink
    return dict(eye=to_world(ecx, ecy), r=rr, hip=(x, hip_y), shL=to_world(*sh_pts["L"]), shR=to_world(*sh_pts["R"]))


def _cel(c, cx, cy, r, L, bk=0.0):
    """Cel lighting inside a clipped shape: a dark crescent away from the light, a warm glaze toward it."""
    dx, dy = L.get("dir", (1.0, 0.0))
    n = math.hypot(dx, dy) + 1e-6
    dx, dy = dx / n, dy / n
    a = L.get("a", 1.0)
    shad = L.get("shadow", (40, 10, 70))
    full = skia.Path(); full.addCircle(cx, cy, r * 1.15)
    cut = skia.Path(); cut.addCircle(cx + dx * r * 0.42, cy + dy * r * 0.42, r * 1.12)
    cres = skia.Op(full, cut, skia.PathOp.kDifference_PathOp)
    if cres is not None:
        c.drawPath(cres, paint(shad, int(110 * a * (1 - bk))))
    g = skia.Paint(AntiAlias=True)
    rgb = L.get("rgb", P_["orange"])
    g.setShader(skia.GradientShader.MakeRadial(skia.Point(cx + dx * r, cy + dy * r), r * 1.6, [core.C(rgb, int(150 * a)), core.C(rgb, 0)]))
    c.drawRect(R(cx - r * 2, cy - r * 2, cx + r * 2, cy + r * 2), g)


def _drop(cv, x, y, r, ang, rgb, seed, a=255):
    """A teardrop (point toward `ang` degrees)."""
    if a <= 4 or r < 0.8:
        return
    P = [(0, -r * 1.7), (r * 0.75, -r * 0.2), (r * 0.9, r * 0.45), (0, r), (-r * 0.9, r * 0.45), (-r * 0.75, -r * 0.2)]
    P = rot(P, ang) + np.array([x, y])
    blob(cv, P, rgb, w=3.0, seed=seed, boil=0.5, n=4, a=a,
         shade=lambda c: dots(c, [(x - r * 0.3, y - r * 0.2)], r * 0.25, P_["white"], a=a))


def _tear_spray(cv, bx, by, side, s, T, k, seed, dirk=1.0, up=0.0):
    """Comic crying: a gushing arc of tears from an eye corner plus flung droplets. up > 0 turns it into a geyser."""
    v0 = (420 + 160 * k) * s
    g = 1300 * s
    vx0 = side * v0 * 0.75 * dirk * (1 - 0.55 * up)
    vy0 = -v0 * (0.55 + 0.9 * up)
    pts = []
    for u in np.linspace(0, 0.55 + 0.35 * up, 10):
        pts.append((bx + vx0 * u + 6 * s * math.sin(T * 30 + u * 9), by + vy0 * u + 0.5 * g * u * u))
    tube(cv, pts, (16 + 10 * k) * s, TEAR, w=3.5, seed=seed, boil=0.9, n=4)
    line(cv, pts[1:6], 4 * s + 1, P_["white"], seed=seed + 1, boil=0.6, n=3, taper=(0.3, 0.3), a=170)
    for j in range(9 + int(5 * up)):
        u = (T * 1.9 + j / 9.0) % 1.0
        sp = 0.75 + 0.5 * float(hsh(seed + j))
        tt = u * (0.75 + 0.5 * up)
        px = bx + vx0 * sp * 1.05 * tt
        py = by + vy0 * sp * 1.05 * tt + 0.5 * g * tt * tt
        vx, vy = vx0 * sp, vy0 * sp + g * tt
        _drop(cv, px, py, (9 + 6 * float(hsh(seed + 30 + j))) * s * (1 - 0.4 * u), math.degrees(math.atan2(vy, vx)) + 90 + 180, TEAR, seed + 40 + j,
              a=int(255 * min(1.0, k * 1.5) * (1 - u ** 4)))


def _padlock(cv, x, y, s, seed=0, open_k=0.0, inkc=None, shackle_rgb=None, keyhole=True):
    """A brass padlock hanging from (x, y) (top of the shackle). open_k 0..1 pops the shackle's right leg out and swings it."""
    inkc = inkc or INK
    bw, bh = 120 * s, 104 * s
    top = y + 70 * s
    sk = shackle_rgb or IRON
    lift = 34 * s * open_k
    cv.save()
    if open_k > 0:
        cv.translate(x - 50 * s, top - lift); cv.rotate(-55 * open_k); cv.translate(-(x - 50 * s), -(top - lift))
        cv.translate(0, -lift)
    tube(cv, [(x - 50 * s, top + 6 * s), (x - 50 * s, y + 28 * s), (x, y), (x + 50 * s, y + 28 * s), (x + 50 * s, top + 6 * s)], 20 * s + 2, sk, w=4.5,
         ink=inkc, seed=seed, boil=0.6, n=5)
    cv.restore()

    def sh(c):
        c.drawRect(R(x + bw * 0.28, top - 10, x + bw + 10, top + bh + 10), paint(BRASS_DK))
        stipple(c, BRASS_DK, (x - bw, top, x + bw, top + bh), spacing=11 * s + 3, r=1.8 * s + 0.6, seed=seed + 3,
                fn=lambda X, Y: np.clip((X - x) / bw + 0.3, 0, 1))
        c.drawPath(poly_path(cr_closed(ell(x - bw * 0.45, top + bh * 0.22, bw * 0.28, bh * 0.1, n=8, rot=-12), 3)), paint(P_["white"], 150))
    blob(cv, rect_pts([(x - bw, top), (x + bw, top), (x + bw * 0.96, top + bh), (x - bw * 0.96, top + bh)], 3), BRASS, w=5.5, ink=inkc, seed=seed + 2,
         boil=0.8, n=3, shade=sh)
    if keyhole:
        dots(cv, [(x, top + bh * 0.42)], 15 * s + 1, inkc)
        blob(cv, [(x - 9 * s, top + bh * 0.45), (x + 9 * s, top + bh * 0.45), (x + 14 * s, top + bh * 0.8), (x - 14 * s, top + bh * 0.8)], inkc, w=0, seed=seed + 4,
             boil=0.4, n=2, misreg=(0, 0))
    return (x, top + bh * 0.42)


# ===================================================================== FX
def clank_star(cv, x, y, r, seed=0, rgb=None, n=9, a=255, rot_deg=0.0):
    """Comic impact burst (jagged star) with a white core."""
    rgb = rgb or P_["yellow"]
    pts = []
    for k in range(n * 2):
        ang = math.radians(rot_deg) + k * math.pi / n
        rad = r * (1.0 if k % 2 == 0 else 0.45 + 0.1 * float(hsh(seed + k)))
        pts.append((x + rad * math.cos(ang), y + rad * math.sin(ang)))
    blob(cv, pts, rgb, w=4.5, seed=seed, boil=1.0, n=2, a=a,
         shade=lambda c: c.drawPath(poly_path(cr_closed(ell(x, y, r * 0.32, r * 0.32, n=8), 3)), paint(P_["white"], a)))


def motion_lines(cv, x, y, ang, n=4, L=80, gap=26, seed=0, rgb=None, wdt=5.0, a=255):
    """A bundle of parallel speed lines trailing behind (x, y) along direction `ang` (deg, direction of travel)."""
    rgb = rgb or INK
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    for k in range(n):
        o = (k - (n - 1) / 2) * gap
        sx, sy = x - sa * o, y + ca * o
        LL = L * (0.6 + 0.6 * float(hsh(seed + k)))
        line(cv, [(sx - ca * LL * 0.2, sy - sa * LL * 0.2), (sx - ca * LL, sy - sa * LL)], wdt, rgb, seed=seed + k, boil=0.8, n=2, taper=(0.1, 0.9), a=a)


def burst_lines(cv, x, y, r0, r1, n=16, seed=0, rgb=None, wdt=6.0, a=255, rot_deg=0.0, jag=0.0):
    """Radiating comic emphasis / scream lines around a point."""
    rgb = rgb or INK
    for k in range(n):
        ang = math.radians(rot_deg + k * 360.0 / n + 9 * float(hsh(seed + k)))
        q0 = r0 * (0.9 + 0.2 * float(hsh(seed + k * 3 + core.D * 0.1)))
        q1 = r1 * (0.8 + 0.35 * float(hsh(seed + k * 5 + core.D * 0.13)))
        pts = [(x + q0 * math.cos(ang), y + q0 * math.sin(ang)), (x + q1 * math.cos(ang), y + q1 * math.sin(ang))]
        if jag > 0:
            m = ((pts[0][0] + pts[1][0]) / 2 + jag * math.cos(ang + 1.57), (pts[0][1] + pts[1][1]) / 2 + jag * math.sin(ang + 1.57))
            pts = [pts[0], m, pts[1]]
        line(cv, pts, wdt, rgb, seed=seed + 40 + k, boil=0.8, n=2, taper=(0.15, 0.6), a=a)


def dust_puff(cv, x, y, s, u, seed=0, rgb=None, a=255):
    """A cartoon dust cloud: puffs grow and fade as u goes 0 -> 1."""
    if u <= 0 or u >= 1:
        return
    rgb = rgb or (210, 170, 220)
    for k in range(5):
        ang = math.radians(-160 + k * 35)
        d = (16 + 40 * u) * s
        r = (14 + 22 * u) * s * (0.7 + 0.5 * float(hsh(seed + k)))
        blob(cv, ell(x + d * math.cos(ang), y + d * math.sin(ang) * 0.55 - 10 * s * u, r, r * 0.85, n=8), rgb, w=3.0, seed=seed + k, boil=0.8,
             a=int(a * (1 - u) ** 0.8))


def glare(cv, x, y, r, a=200, rgb=None, blend=True):
    """Additive white/yellow light bloom."""
    rgb = rgb or P_["white"]
    if a <= 0:
        return
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(x, y), max(1.0, r), [core.C(rgb, int(a)), core.C(rgb, int(a * 0.45)), core.C(rgb, 0)], [0.0, 0.4, 1.0]))
    if blend:
        p.setBlendMode(skia.BlendMode.kScreen)
    cv.drawRect(R(x - r, y - r, x + r, y + r), p)


def light_rays(cv, x, y, r, T, n=16, a=90, rgb=None, rot_deg=0.0, width=0.5, spin=6.0, blend=True):
    """Wedge rays radiating from (x, y) (gradient alpha), slowly rotating."""
    rgb = rgb or P_["yellow"]
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(x, y), max(1.0, r), [core.C(rgb, int(a)), core.C(rgb, int(a * 0.5)), core.C(rgb, 0)], [0.0, 0.5, 1.0]))
    if blend:
        p.setBlendMode(skia.BlendMode.kScreen)
    path = skia.Path()
    for k in range(n):
        a0 = math.radians(rot_deg + T * spin + k * 360.0 / n)
        wd = math.radians(360.0 / n * width * (0.75 + 0.5 * float(hsh(k * 3.3))))
        path.moveTo(x, y)
        path.lineTo(x + r * math.cos(a0 - wd / 2), y + r * math.sin(a0 - wd / 2))
        path.lineTo(x + r * math.cos(a0 + wd / 2), y + r * math.sin(a0 + wd / 2))
        path.close()
    cv.drawPath(path, p)


def rays_fast(cv, x, y, r, T, n=14, a=60, rgb=None, ang0=110, span=80):
    """Same geometry as the kit's sun_rays (shafts fanning from a point) but batched into a single path + shader."""
    rgb = rgb or P_["yellow"]
    path = skia.Path()
    for k in range(n):
        u = (k + 0.5) / n
        aa = math.radians(ang0 + span * (u - 0.5) + 2 * math.sin(T * 0.5 + k))
        wd = math.radians(span / n * (0.35 + 0.25 * math.sin(T * 0.9 + k * 1.7)))
        path.moveTo(x, y)
        path.lineTo(x + r * math.cos(aa - wd), y + r * math.sin(aa - wd))
        path.lineTo(x + r * math.cos(aa + wd), y + r * math.sin(aa + wd))
        path.close()
    sh = skia.Paint(AntiAlias=True)
    sh.setShader(skia.GradientShader.MakeRadial(skia.Point(x, y), r, [core.C(rgb, a), core.C(rgb, 0)]))
    cv.drawPath(path, sh)


def wash(cv, rgb, a, blend=None):
    """Full-frame colour wash (optionally screen / multiply)."""
    if a <= 0:
        return
    p = skia.Paint(AntiAlias=False, Color=core.C(rgb, int(min(255, a))))
    if blend == "screen":
        p.setBlendMode(skia.BlendMode.kScreen)
    elif blend == "multiply":
        p.setBlendMode(skia.BlendMode.kMultiply)
    elif blend == "plus":
        p.setBlendMode(skia.BlendMode.kPlus)
    cv.drawRect(R(-200, -200, W + 200, H + 200), p)


def heart(cv, x, y, r, seed=0, rgb=None, a=255):
    rgb = rgb or P_["hotpink"]
    P = [(x, y + r), (x - r * 1.05, y - r * 0.05), (x - r * 0.95, y - r * 0.75), (x - r * 0.45, y - r * 0.95), (x, y - r * 0.5),
         (x + r * 0.45, y - r * 0.95), (x + r * 0.95, y - r * 0.75), (x + r * 1.05, y - r * 0.05)]
    blob(cv, P, rgb, w=3.5, seed=seed, boil=0.7, n=4, a=a,
         shade=lambda c: dots(c, [(x - r * 0.45, y - r * 0.45)], r * 0.18, P_["white"], a=a))


def sfx(cv, text, x, y, size, t, t0, seed=0, fill=None, fills=None, font="bangers", rot_deg=0.0, dur=0.25, hold=9.0, shadow_rgb=None):
    """Comic sound-effect lettering that pops in at t0 (springy), jitters, and fades after `hold` seconds."""
    if t < t0 or t > t0 + hold + 0.3:
        return
    k = pop(t, t0, dur)
    fade = 1.0 - _seg(t, t0 + hold, t0 + hold + 0.3)
    if k <= 0.01 or fade <= 0.01:
        return
    cv.save(); cv.translate(x, y); cv.rotate(rot_deg + 3 * math.sin(core.D * 1.3 + seed)); cv.scale(k, k)
    paint_text(cv, text, 0, size * 0.35, font=font, size=size, fill=fill or P_["yellow"], fills=fills, ink_w=6.5 if size > 90 else 5, shadow=(7, 7),
               shadow_rgb=shadow_rgb or INK, seed=seed, wobble=2.5, a=int(255 * fade))
    cv.restore()


# ===================================================================== shared cave pieces
def stalactites(cv, y0, x0, x1, seed=0, n=12, sc=1.0, rgb=None, drip=True, T=0.0):
    rgb = rgb or CV_ROCK2
    for k in range(n):
        sx = x0 + (x1 - x0) * (k + 0.5) / n + 40 * math.sin(k * 2.3 + seed)
        sl = (70 + 110 * float(hsh(seed + k))) * sc
        wd = (26 + 14 * float(hsh(seed + k * 3))) * sc
        yy = y0 + 16 * math.sin(k * 1.7 + seed)
        P = [(sx - wd, yy - 30), (sx + wd, yy - 30), (sx + wd * 0.3, yy + sl * 0.7), (sx + 3, yy + sl), (sx - wd * 0.2, yy + sl * 0.7)]
        blob(cv, P, rgb, w=4, seed=seed + 30 + k, boil=0.8, n=3,
             shade=lambda c, sx=sx, yy=yy, sl=sl, wd=wd: (c.drawPath(poly_path([(sx + wd * 0.2, yy - 30), (sx + wd, yy - 30), (sx + 3, yy + sl)]), paint(mix(rgb, INK, 0.3))),
                                                        c.drawPath(poly_path([(sx - wd * 0.7, yy - 30), (sx - wd * 0.4, yy - 30), (sx - 2, yy + sl * 0.8)]), paint(P_["hotpink"], 90))))
        if drip and k % 3 == 0:
            ph = (T * 0.4 + float(hsh(seed + k * 7))) % 1.0
            dy = 0 if ph < 0.7 else (ph - 0.7) / 0.3 * 500
            dots(cv, [(sx + 3, yy + sl + 8 + dy)], 5.5 * sc, P_["mint"], a=int(255 * (1 - max(0, ph - 0.7) / 0.3)))


def floor_band(cv, y, T, seed=0, rgb=None, rim=None, x0=-300, x1=2300, pebbles=12, mush=()):
    rgb = rgb or CV_ROCK2
    rock_mass(cv, [(x0, y + 10), ((x0 + x1) * 0.3, y - 14), ((x0 + x1) * 0.62, y + 12), (x1, y - 8), (x1, y + 700), (x0, y + 700)], seed=seed, rgb=rgb,
              rim=rim, rim_side=1)
    for k in range(pebbles):
        px = x0 + 120 + k * (x1 - x0 - 240) / max(1, pebbles - 1) + 40 * math.sin(k * 3.1 + seed)
        py = y + 40 + 90 * float(hsh(seed + k * 9))
        blob(cv, ell(px, py, 18 + 12 * float(hsh(seed + k)), 9 + 5 * float(hsh(seed + k * 2)), n=8), mix(rgb, P_["lilac"], 0.3), w=3, seed=seed + 200 + k, boil=0.5)
    for k, (mx, my, ms) in enumerate(mush):
        glow_mushroom(cv, mx, my, ms, T, seed=seed + 300 + k)


def hooded(cv, x, fy, s, T, seed=4600, face=1, hands=None, walk=None, lean=0.0, rim=None, rim_side=None, glaze=None, eyes=True,
           hand_rgb=None, robe=None):
    """A hooded puppet-carrier with free arms. hands = [dict(world=(X, Y), pose, ang, mirror), ...] (0-2 hands); walk = phase or None.
    rim = rim-light colour on the `rim_side` edge; glaze = (rgb, a) warm wash over the front."""
    robe = robe or HOOD
    hand_rgb = hand_rgb or (150, 120, 190)
    rim_side = rim_side if rim_side is not None else face
    old = core.INKMUL
    core.INKMUL = old * _ink_scale(s)
    bob = (abs(math.cos(walk)) * 7 * s) if walk is not None else 2 * s * math.sin(T * 2 + seed)
    cv.save(); cv.translate(x, fy); cv.rotate(lean); cv.translate(-x, -fy)
    for side in (-1, 1):                                                # legs / feet under the hem
        st = math.sin(walk + (0 if side < 0 else math.pi)) if walk is not None else 0.0
        fx = x + side * 18 * s + st * 26 * s * face
        line(cv, [(x + side * 14 * s, fy - 80 * s - bob), (fx, fy - 6 * s)], 15 * s + 2, mix(robe, INK, 0.3), seed=seed + side, boil=0.6, n=2, taper=(0, 0))
        blob(cv, ell(fx + face * 8 * s, fy - 5 * s, 18 * s, 8 * s, n=8), INK, w=0, seed=seed + 2 + side, boil=0.4, misreg=(0, 0))
    top = fy - 300 * s - bob
    robe_pts = [(x - 66 * s, fy - 50 * s - bob), (x - 52 * s, fy - 170 * s - bob), (x - 40 * s, top + 60 * s), (x, top + 20 * s), (x + 40 * s, top + 60 * s),
                (x + 52 * s, fy - 170 * s - bob), (x + 66 * s, fy - 50 * s - bob), (x + 20 * s, fy - 40 * s - bob), (x - 20 * s, fy - 44 * s - bob)]

    def rshade(c):
        for k in range(3):
            xx = x - 30 * s + k * 30 * s
            line(c, [(xx, top + 90 * s), (xx + 6 * s * (k - 1), fy - 50 * s)], 3.0, mix(robe, INK, 0.45), seed=seed + 10 + k, boil=0.6, n=3, taper=(0.2, 0.2), a=200)
        if glaze:
            gr = skia.Paint(AntiAlias=True)
            gr.setShader(skia.GradientShader.MakeLinear([skia.Point(x, fy), skia.Point(x, top)], [core.C(glaze[0], int(glaze[1])), core.C(glaze[0], 0)]))
            c.drawRect(R(x - 90 * s, top - 40 * s, x + 90 * s, fy + 10), gr)
        if rim:
            ex = x + rim_side * 66 * s
            c.drawPath(poly_path([(ex - rim_side * 22 * s, top), (ex + rim_side * 40 * s, top), (ex + rim_side * 40 * s, fy + 10), (ex - rim_side * 16 * s, fy + 10)]), paint(rim, 210))
    blob(cv, robe_pts, robe, w=4.5, seed=seed + 3, boil=1.0, n=4, shade=rshade)
    hx, hy = x + face * 6 * s, top + 8 * s                                # hood
    hood = [(hx - 46 * s, hy + 34 * s), (hx - 44 * s, hy - 20 * s), (hx - 10 * s, hy - 58 * s), (hx + face * 30 * s, hy - 52 * s), (hx + 48 * s, hy - 12 * s),
            (hx + 46 * s, hy + 34 * s)]

    def hshade(c):
        if rim:
            c.drawPath(poly_path(cr_closed(ell(hx + rim_side * 44 * s, hy - 8 * s, 16 * s, 50 * s, n=8), 3)), paint(rim, 210))
        if glaze:
            c.drawRect(R(hx - 60 * s, hy - 70 * s, hx + 60 * s, hy + 40 * s), paint(glaze[0], int(glaze[1] * 0.4)))
    blob(cv, hood, robe, w=4.5, seed=seed + 4, boil=0.9, n=4, shade=hshade)
    blob(cv, ell(hx + face * 8 * s, hy + 4 * s, 28 * s, 30 * s, n=10), (8, 2, 16), w=0, seed=seed + 5, boil=0.6, misreg=(0, 0))
    if eyes:
        blink = (T * 0.5 + float(hsh(seed)) * 4) % 3.7 < 0.1
        for side in (-1, 1):
            ex, ey = hx + face * 12 * s + side * 11 * s, hy + 2 * s
            if blink:
                line(cv, [(ex - 5 * s, ey), (ex + 5 * s, ey)], 2.5, P_["yellow"], seed=seed + 6 + side, boil=0.3, n=2, taper=(0, 0))
            else:
                dots(cv, [(ex, ey)], 5.5 * s + 1, P_["yellow"])
                dots(cv, [(ex, ey)], 9 * s + 1, P_["yellow"], a=60)
    for k, hd in enumerate(hands or []):                                 # arms
        side = hd.get("side", face if k == 0 else -face)
        shx, shy = x + side * 34 * s, top + 92 * s
        wx, wy = hd["world"]
        el = _arm_pts((shx, shy), (wx, wy), bend=hd.get("bend", -side), seg=95 * s * hd.get("reach", 1.0))
        tube(cv, el, 26 * s, robe, w=4.0, seed=seed + 20 + k, boil=0.8, n=6)
        blob(cv, ell(el[0][0], el[0][1] + 4 * s, 20 * s, 16 * s, n=8), robe, w=0, seed=seed + 24 + k, boil=0.5, misreg=(0, 0))
        ang = hd.get("ang")
        if ang is None:
            ang = math.degrees(math.atan2(wy - el[1][1], wx - el[1][0]))
        cv.save(); cv.translate(wx, wy); cv.scale(s * 1.25, s * 1.25)
        _hand(cv, 0, 0, ang, hd.get("pose", "open"), hd.get("mirror", 1 if side < 0 else -1), seed + 26 + k * 5, rgb=hand_rgb, cuff=robe)
        cv.restore()
    cv.restore()
    core.INKMUL = old
    return (hx, hy)


def big_key(cv, tip, s, turn=0.0, seed=0, ang=0.0, inkc=None):
    """A giant ornate golden key lying along +x from its tip (the bit end at `tip`), bow at the far end.
    turn 0..1 rotates it a quarter turn about its shaft (the bow foreshortens)."""
    inkc = inkc or INK
    x, y = tip
    cv.save(); cv.translate(x, y); cv.rotate(ang)
    fq = max(0.08, abs(math.cos(turn * math.pi / 2)))
    Ls = 250 * s
    blob(cv, rect_pts([(-6 * s, -11 * s * fq - 4), (Ls, -13 * s * fq - 4), (Ls, 13 * s * fq + 4), (-6 * s, 11 * s * fq + 4)], 3), BRASS, w=4.5, ink=inkc,
         seed=seed, boil=0.6, n=3, shade=lambda c: c.drawRect(R(-10 * s, 4 * s * fq, Ls + 10, 20 * s), paint(BRASS_DK)))
    for k in range(3):                                                   # decorative collars on the shaft
        cx = Ls * (0.55 + 0.16 * k)
        blob(cv, ell(cx, 0, 9 * s, 19 * s * fq + 3, n=8), BRASS, w=3.5, ink=inkc, seed=seed + 3 + k, boil=0.5,
             shade=lambda c, cx=cx: c.drawRect(R(cx, -30 * s, cx + 12 * s, 30 * s), paint(BRASS_DK)))
    bx = Ls + 92 * s                                                      # bow: a ring with an eye-shaped window
    bow = ell(bx, 0, 96 * s, 88 * s * fq + 2, n=16)

    def bsh(c):
        c.drawPath(poly_path(cr_closed(ell(bx + 26 * s, 20 * s * fq, 80 * s, 60 * s * fq + 1, n=10), 3)), paint(BRASS_DK))
        stipple(c, BRASS_DK, (bx - 100 * s, -90 * s, bx + 100 * s, 90 * s), spacing=10 * s + 2, r=1.6 * s + 0.5, seed=seed + 7,
                fn=lambda X, Y: np.clip((X - bx) / (100 * s) + 0.4, 0, 1))
        c.drawPath(poly_path(cr_closed(ell(bx - 40 * s, -40 * s * fq, 26 * s, 12 * s * fq + 1, n=8, rot=-30), 3)), paint(P_["white"], 170))
    blob(cv, bow, BRASS, w=5.5, ink=inkc, seed=seed + 8, boil=0.8, shade=bsh)
    if fq > 0.25:
        eye = [(bx - 58 * s, 0), (bx - 20 * s, -36 * s * fq), (bx + 20 * s, -36 * s * fq), (bx + 58 * s, 0), (bx + 20 * s, 36 * s * fq), (bx - 20 * s, 36 * s * fq)]
        blob(cv, eye, P_["magenta"], w=4.0, ink=inkc, seed=seed + 9, boil=0.6, n=5,
             shade=lambda c: (c.drawCircle(bx, 0, 22 * s * fq + 1, paint(P_["teal"])), c.drawCircle(bx, 0, 10 * s * fq + 0.5, paint(INK))))
    cv.restore()


# ===================================================================== T023  SET FREE
def motes(cv, T, box, n=40, seed=0, rgb=None, a=200, rise=60.0, r=3.0):
    """Floating embers / dust motes drifting up through the light."""
    x0, y0, x1, y1 = box
    cols = rgb or [P_["yellow"], P_["orange"], P_["cream"], P_["hotpink"]]
    for k in range(n):
        u = float(hsh(seed + k * 1.3))
        v = float(hsh(seed + k * 2.7))
        x = x0 + u * (x1 - x0) + 30 * math.sin(T * 0.8 + k)
        y = y1 - ((v * (y1 - y0) + T * rise * (0.5 + float(hsh(seed + k * 4.1)))) % (y1 - y0))
        tw = 0.5 + 0.5 * math.sin(T * 5 + k * 1.7)
        dots(cv, [(x, y)], r * (0.6 + 0.8 * float(hsh(seed + k * 5.5))), cols[k % len(cols)], a=int(a * tw))


def _wall_pov(cv, T, C, seed=5100, shadows=(), heads=(), floor_y=800, wall_p=0.55, floor_p=0.8, head_a=90):
    """The prisoners' wall seen from behind them (camera at the fire): ceiling + stalactites, the huge hot wall with
    shadows, the floor in front of it. heads = [(x, s)] prisoner positions whose head-shadows fall on the wall."""
    with C.layer(wall_p):
        w.field(cv, CV_ROCK_DK)
        wall = [(-420, -60), (2340, -60), (2340, floor_y + 60), (-420, floor_y + 60)]
        wall_surface(cv, wall, T, seed=seed, cx=960, cy=floor_y - 260, glow=1.0)
        cv.save(); cv.clipPath(poly_path(wall), doAntiAlias=True)
        for kind, sx, sy, ss in shadows:
            shadow_shape(cv, kind, sx, sy, ss, T, seed=seed + 20 + int(sx * 0.1))
        hp = skia.Paint(AntiAlias=True, Color=core.C(CV_SHADOW, head_a))
        hp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 18))
        for hx, hs in heads:                                            # the prisoners' own soft head-shadows
            cv.drawPath(poly_path(cr_closed(ell(hx, floor_y - 40 * hs, 70 * hs, 66 * hs, n=10), 3)), hp)
        cv.restore()
        rock_mass(cv, [(-500, -400), (2400, -400), (2400, 30), (1700, 80), (1100, 40), (500, 90), (-500, 40)], seed=seed + 5, rgb=CV_ROCK, rim=P_["orange"])
        stalactites(cv, 120, -300, 2200, seed=seed + 8, n=9, sc=0.75, rgb=mix(CV_ROCK2, P_["magenta"], 0.3), T=T)
        stalactites(cv, 60, -260, 2240, seed=seed + 7, n=11, sc=1.15, T=T)
        for k in range(5):
            crystal(cv, -100 + k * 520 + 60 * math.sin(k), 50 + 20 * math.sin(k * 2.1), 0.9, T, seed=seed + 60 + k)
    with C.layer(floor_p):
        floor_band(cv, floor_y, T, seed=seed + 9, rgb=CV_ROCK2, rim=P_["orange"], pebbles=10,
                   mush=((80, floor_y + 70, 0.9), (1840, floor_y + 60, 0.9), (620, floor_y + 150, 0.7), (1320, floor_y + 160, 0.7)))


def _fire_glow(cv, T, a=1.0, y=1350, r=1400, seed=5150, x=960):
    """Warm firelight spilling up from behind the camera (screen-blended)."""
    fl = 0.9 + 0.08 * math.sin(T * 9.0 + seed) + 0.05 * math.sin(T * 21.0)
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(x, y), r * fl, [core.C(P_["orange"], int(170 * a)), core.C(P_["red"], int(70 * a)), core.C(P_["red"], 0)],
                                               [0.0, 0.5, 1.0]))
    p.setBlendMode(skia.BlendMode.kScreen)
    cv.drawRect(R(-100, -100, W + 100, H + 100), p)


def _halo_rings(cv, x, y, t, a=1.0, seed=0, r0=120):
    """Psychedelic 'chosen one' rings rippling out from a point."""
    cols = [P_["magenta"], P_["yellow"], P_["teal"], P_["acid"], P_["hotpink"]]
    for k in range(6):
        ph = (t * 0.55 + k / 6.0) % 1.0
        r = r0 + ph * 520
        al = int(220 * a * (1 - ph) ** 1.5)
        if al < 6:
            continue
        P = ell(x, y, r, r * 0.92, n=16)
        P = P + np.stack([np.cos(np.arange(16) * 2.1 + k + t * 3), np.sin(np.arange(16) * 1.7 + k)], 1) * 7
        brush(cv, cr_closed(jit(P, 1.0, seed + k), 4), 9.0 * (1 - ph) + 2, cols[k % 5], closed=True, seed=seed + k, a=al)


def _prisoner_row(cv, T, xs, fy, s, seed=5300, view="back", glow=0.6, face=None):
    for k, px in enumerate(xs):
        f = face if face is not None else (1 if k % 2 else -1)
        prisoner(cv, px, fy + 12 * (k % 2), s, T, seed=seed + k * 13, view=view, face=f, anchor=(px + 40 * s, fy + 40 * s + 12 * (k % 2)), glow=glow)


def _fg_rocks(cv, T, seed=5180, rim=None, left=True, right=True, y=1080):
    rim = rim or P_["orange"]
    if left:
        rock_mass(cv, [(-200, y - 150), (60, y - 230), (230, y - 180), (330, y - 60), (360, y + 200), (-200, y + 200)], seed=seed, rgb=CV_ROCK_DK, rim=rim, rim_side=1, ink=6)
        glow_mushroom(cv, 150, y - 200, 1.1, T, seed=seed + 1)
    if right:
        rock_mass(cv, [(1560, y + 200), (1600, y - 90), (1720, y - 200), (1900, y - 250), (2120, y - 170), (2120, y + 200)], seed=seed + 2, rgb=CV_ROCK_DK, rim=rim,
                  rim_side=-1, ink=6)
        crystal(cv, 1800, y - 230, 1.1, T, seed=seed + 3, rgb=P_["teal"])


def T023_set_free(cv, t, T, A):
    if t < 3.8:
        _t023_wide(cv, t, T)
    elif t < 6.05:
        _t023_key(cv, t, T)
    else:
        _t023_stand(cv, t, T)


def _t023_wide(cv, t, T):
    k = ease(t / 3.8)
    gfy, gs = 1010, 0.8
    C = sets.Cam(cv, dict(x=0, y=lerp(-30, 120, k), z=lerp(1.0, 1.22, k)))
    sh = [("bunny", 470 - t * 40, 330, 1.9), ("horse", 1500 - t * 55, 280, 1.7), ("tree", 2350 - t * 50, 320, 1.6)]
    xs = [150, 420, 690, 1230, 1500, 1770]
    _wall_pov(cv, T, C, seed=5100, shadows=sh, heads=[(x, 1.2) for x in xs] + [(960, 1.6)], floor_y=700)
    spot = _seg(t, 1.0, 1.7)
    with C.layer(0.9):
        motes(cv, T, (-100, 100, 2000, 1000), n=36, seed=5170, a=200)
    _fire_glow(cv, T, a=0.9)
    with C.layer(1.0):
        for j, px in enumerate(xs):
            prisoner(cv, px, 1000 + 14 * (j % 2), 1.45 + 0.1 * (j % 3 == 1), T, seed=5300 + j * 13, view="back", anchor=(px + 60, 1050 + 14 * (j % 2)), glow=0.4)
        g = gary_x(cv, 960, gfy, gs, T, seed=4400, yaw=180, collar=True, light=dict(dir=(0, 1), a=0.7, rgb=P_["orange"]))
        cy = g["hip"][1] - 214 * gs
        chain(cv, (962, cy + 60), (1040, 1062), seed=5401, link=14, sag=16, w=3.0)
        _padlock(cv, 960, cy + 4, 0.36, seed=5402)
        blob(cv, ell(1040, 1064, 18, 8, n=8), IRON, w=3, seed=5403, boil=0.4)
    with C.layer(1.3):
        _fg_rocks(cv, T, seed=5180)
    if spot > 0:                                                     # 'one prisoner': everything else dims, rings ripple out
        gx, gy = C.to_screen(960, gfy - 360 * gs, 1.0)
        p = skia.Paint(AntiAlias=True)
        p.setShader(skia.GradientShader.MakeRadial(skia.Point(gx, gy + 60), 700, [core.C((20, 6, 44), 0), core.C((20, 6, 44), int(90 * spot)),
                                                                                 core.C((20, 6, 44), int(165 * spot))], [0.0, 0.42, 1.0]))
        cv.drawRect(R(-50, -50, W + 50, H + 50), p)
        _halo_rings(cv, gx, gy, t, a=spot, seed=5420, r0=170)
        if t > 2.45:
            for j in range(9):
                ang = j * 0.698 + t * 0.8
                rr = 230 + 30 * math.sin(t * 3 + j)
                sparkle(cv, gx + rr * math.cos(ang), gy + 40 + rr * 0.85 * math.sin(ang), 18 * pop(t, 2.45 + j * 0.05, 0.3), [P_["yellow"], P_["white"], P_["mint"]][j % 3],
                        seed=5430 + j)
    vignette(cv, a=150)


def _t023_key(cv, t, T):
    lt = t - 3.8
    shake = 0.0
    if 5.62 < t < 5.95:
        shake = 14 * (1 - (t - 5.62) / 0.33)
    cv.save()
    _shake(cv, shake, seed=5500)
    C = sets.Cam(cv, dict(x=0, y=0, z=1.0 + 0.02 * lt))
    with C.layer(0.5):
        w.field(cv, CV_ROCK_DK)
        wall_surface(cv, [(-300, -300), (2220, -300), (2220, 1400), (-300, 1400)], T, seed=5510, cx=960, cy=300)
        shadow_shape(cv, "bunny", 300, 330, 2.2, T, seed=5511)
        shadow_shape(cv, "horse", 1690, 260, 2.0, T, seed=5512)
        motes(cv, T, (-100, -100, 2000, 1100), n=30, seed=5513, a=180)
    with C.layer(0.8):
        prisoner(cv, 120, 1180, 3.1, T, seed=5520, view="back", chained=False, glow=0.5)
        prisoner(cv, 1820, 1200, 3.1, T, seed=5521, view="back", chained=False, glow=0.5)
    s = 2.3
    op = _seg(t, 5.18, 5.5)
    fall = max(0.0, t - 5.32)
    with C.layer(1.0):
        gx, gfy = 960, 1040
        g = gary_x(cv, gx, gfy, s, T, seed=4400, yaw=180, collar=dict(open=op), bob=0.3, veins=0.5, light=dict(dir=(0, 1), a=0.6, rgb=P_["orange"]))
        cy = g["hip"][1] - 214 * s
        top = cy + 34
        lk = _seg(t, 5.05, 5.22)
        ldy = 0.5 * 2600 * fall * fall
        lrot = 70 * fall
        cv.save(); cv.translate(gx, top + ldy); cv.rotate(lrot); cv.translate(-gx, -top)
        chain(cv, (gx + 4, top + 40), (gx + 60, 1250), seed=5530, link=26, sag=30, w=4.5)
        kh = _padlock(cv, gx, top, 1.25, seed=5531, open_k=lk)
        cv.restore()
        # the key, held by a hooded hand coming in from the right
        kin = _seg(t, 3.8, 4.45)
        push = 40 * (1 - _seg(t, 4.45, 4.62))
        out = _seg(t, 5.25, 5.75)
        turn = _seg(t, 4.72, 5.05)
        ks = 1.45
        kx = kh[0] + (1 - kin) * 1100 + push + out * 1100
        ky = kh[1]
        bx = kx + 342 * ks
        hx, hy = bx + 112 * ks, ky - 4
        tube(cv, [(2200, ky + 330), (1900, ky + 170), (hx + 70, ky + 40)], 84, HOOD, w=5, seed=5540, boil=0.8, n=6)
        blob(cv, ell(hx + 90, ky + 40, 54, 62, n=10), HOOD, w=5, seed=5541, boil=0.7,
             shade=lambda c: c.drawRect(R(hx + 40, ky - 40, hx + 160, ky), paint(P_["orange"], 120)))
        big_key(cv, (kx, ky), ks, turn=turn, seed=5542)
        cv.save(); cv.translate(hx, hy); cv.scale(2.3, 2.3)
        _hand(cv, 0, 0, 185 - 30 * turn, "pinch", 1, 5543, rgb=(150, 120, 190), cuff=HOOD)
        cv.restore()
        if 4.72 < t < 5.25:                                            # turning arc
            a0 = -80 - 140 * turn
            arc = [(bx + 175 * math.cos(math.radians(a)), ky + 175 * math.sin(math.radians(a))) for a in np.linspace(a0, a0 + 130, 9)]
            line(cv, arc, 8, P_["yellow"], seed=5545, boil=0.8, n=4, taper=(0.1, 0.1))
            e = arc[-1]
            blob(cv, [e, (e[0] - 34, e[1] - 30), (e[0] + 30, e[1] - 34)], P_["yellow"], w=3.5, seed=5546, boil=0.5, n=2)
        if t > 5.05:
            burst_lines(cv, kh[0], kh[1], 80, 190, n=12, seed=5547, rgb=P_["yellow"], wdt=8, a=int(255 * (1 - _seg(t, 5.2, 5.5))))
        if op > 0:                                                     # collar halves springing apart
            for side in (-1, 1):
                motion_lines(cv, gx + side * (300 + 80 * op), cy - 10, 180 if side < 0 else 0, n=3, L=150, gap=30, seed=5550 + side, wdt=6,
                             a=int(255 * (1 - _seg(t, 5.55, 5.8))))
        if t > 5.62:
            for j in range(4):
                clank_star(cv, 560 + j * 300, 1010 - 40 * (j % 2), 64 * pop(t, 5.62 + j * 0.05, 0.25) * (1 - _seg(t, 5.9, 6.05)), seed=5560 + j,
                           rgb=[P_["yellow"], P_["white"], P_["acid"], P_["yellow"]][j], rot_deg=j * 20)
    cv.restore()
    sfx(cv, "CLICK!", 1450, 330, 140, t, 5.05, seed=5570, fills=[P_["yellow"], P_["white"]], rot_deg=-8, hold=0.55)
    sfx(cv, "CLANK!", 540, 820, 160, t, 5.62, seed=5571, fills=[P_["acid"], P_["yellow"]], rot_deg=6, hold=0.5)
    vignette(cv, a=140)


def _t023_stand(cv, t, T):
    s = 1.0
    gx, gfy = 880, 1040
    up = _seg(t, 6.25, 6.85)
    crouch = math.sin(math.pi * _cl((t - 6.12) / 0.3)) * (1 - up)
    wt = t - 6.85
    wob = math.exp(-1.25 * wt) if wt > 0 else 0.0
    lean = 13 * math.sin(2 * math.pi * 1.9 * wt) * wob if wt > 0 else 0.0
    knees = 0.75 * math.sin(2 * math.pi * 2.6 * wt) * wob if wt > 0 else 0.0
    turn = ease((t - 8.05) / 1.1)
    yaw = 180 * (1 - turn)
    wide = _seg(t, 9.1, 9.42)
    eye_y = gfy - 360 * s - 108 * s * up
    push = ease((t - 7.95) / 1.69)
    C = sets.Cam(cv, dict(x=lerp(0, gx - 960, push), y=lerp(-30, eye_y - 540 + 70, push), z=lerp(1.0, 1.6, push)))
    _wall_pov(cv, T, C, seed=5600, shadows=[("bunny", 420 - t * 30, 300, 1.9), ("tree", 1560 - t * 30, 280, 1.8)],
              heads=[(330, 1.5), (880, 1.9)], floor_y=690)
    with C.layer(0.9):
        motes(cv, T, (-100, 100, 2000, 1000), n=30, seed=5605, a=200)
    lk = _cl(turn * 1.3 - 0.3)
    _fire_glow(cv, T, a=0.8 + 0.5 * lk)
    if lk > 0:
        ex0, ey0 = C.to_screen(gx, eye_y, 1.0)
        light_rays(cv, ex0, 1350, 1600, T, n=14, a=int(80 * lk), rgb=P_["yellow"], rot_deg=-90 - 35, width=0.45, spin=0)
        glare(cv, ex0, ey0, 640, a=int(90 * lk + 60 * wide), rgb=P_["yellow"])
    with C.layer(1.0):
        prisoner(cv, 330, 1035, 1.75, T, seed=5610, view="back", anchor=(400, 1080), glow=0.5)
        # the broken collar + chain on the floor
        for side in (-1, 1):
            blob(cv, ell(gx + side * 170, 1048, 80, 18, n=10, rot=side * 8), IRON, w=4, seed=5612 + side, boil=0.6,
                 shade=lambda c, side=side: c.drawRect(R(gx + side * 170 - 90, 1050, gx + side * 170 + 90, 1080), paint(IRON_DK)))
        chain(cv, (gx - 80, 1066), (gx + 330, 1074), seed=5614, link=15, sag=6, w=3.0)
        # the carrier who frees him: lifts him under the arm, then signals 'turn around'
        help_ = 1 - _seg(t, 6.95, 7.35)
        twirl = _seg(t, 7.65, 7.9) * (1 - _seg(t, 8.55, 8.85))
        cs = 1.75
        chx, chy = 1390 + 30 * (1 - help_), 1050
        ctop = chy - 300 * cs
        rest = (chx - 40, ctop + 290)
        if help_ > 0.01:
            hand = (lerp(1260, gx + 120 * s, help_), lerp(ctop + 260, eye_y + 200 * s + 30 * (1 - up), help_))
            hd = dict(world=hand, pose="flat", ang=200)
        else:
            ang = t * 10
            tw = (chx - 230 + 26 * math.cos(ang), ctop + 190 + 26 * math.sin(ang))
            hd = dict(world=(lerp(rest[0], tw[0], twirl), lerp(rest[1], tw[1], twirl)), pose="point" if twirl > 0.2 else "open",
                      ang=lerp(100, 190, twirl))
        hooded(cv, chx, chy, cs, T, seed=5620, face=-1, hands=[hd], glaze=(P_["hotpink"], 80), rim=P_["orange"], rim_side=-1)
        armk = (1 - turn)
        if wt > 0:
            fl = math.sin(2 * math.pi * 2.0 * wt)
            aL = dict(hand=(lerp(-140, -250, wob * armk), lerp(330, 90 + 50 * fl, wob * armk)), pose="spread" if wob > 0.3 else "open")
            aR = dict(hand=(lerp(140, 250, wob * armk), lerp(330, 70 - 50 * fl, wob * armk)), pose="spread" if wob > 0.3 else "open")
        else:
            aL, aR = dict(), dict()
        light = dict(dir=(0.15, 1.0), a=0.5 + 0.5 * lk, rgb=P_["orange"])
        g = gary_x(cv, gx, gfy + 6 * crouch, s, T, seed=4400, yaw=yaw, stand=up, lean=lean, knees=knees + 0.35 * crouch, arms=dict(L=aL, R=aR),
                   light=light, lid=lerp(0.35, -0.3, wide), iris=lerp(1.0, 0.86, wide), pupil=lerp(0.42, 0.13, wide), shock=wide,
                   mouth="o" if wide > 0.3 else "smile", mo=0.3 + 0.4 * wide, sweat=0.8 * wob if wt > 0 else 0.0)
        if twirl > 0.05:                                               # circular 'turn around' arrow over Gary
            ecx, ecy = gx, eye_y - 40
            a0 = t * 2.6
            arc = [(ecx + 230 * math.cos(a), ecy + 70 * math.sin(a)) for a in np.linspace(a0, a0 + 4.6 * twirl, 14)]
            line(cv, arc, 10, P_["yellow"], seed=5625, boil=0.8, n=4, taper=(0.05, 0.05), a=int(255 * twirl))
            e, e2 = arc[-1], arc[-2]
            d = math.atan2(e[1] - e2[1], e[0] - e2[0])
            tip = (e[0] + 34 * math.cos(d), e[1] + 34 * math.sin(d))
            blob(cv, [tip, (e[0] + 26 * math.cos(d + 1.9), e[1] + 26 * math.sin(d + 1.9)), (e[0] + 26 * math.cos(d - 1.9), e[1] + 26 * math.sin(d - 1.9))],
                 P_["yellow"], w=4, seed=5626, boil=0.5, n=2, a=int(255 * twirl))
        if 0.05 < wob < 0.95 and wt > 0:                                   # wobble lines
            for side in (-1, 1):
                for j in range(2):
                    cxl, cyl = gx + side * (165 + 34 * j), gfy - 100 - 90 * j
                    arc = [(cxl + side * 22 * math.cos(a), cyl + 44 * math.sin(a)) for a in np.linspace(-1.2, 1.2, 5)]
                    line(cv, arc, 5, INK, seed=5630 + j + side * 3, boil=1.0, n=3, taper=(0.2, 0.2), a=int(255 * min(1.0, wob * 1.4)))
    if lk > 0:
        ex, ey = C.to_screen(g["eye"][0], g["eye"][1], 1.0)
        rr = g["r"] * C.zoom(1.0)
        sparkle(cv, ex - rr * 0.42, ey - rr * 0.45, 26 * lk + 20 * wide, P_["white"], seed=5641)
        if wide > 0:
            burst_lines(cv, ex, ey, rr * 1.12, rr * 1.12 + 170, n=18, seed=5640, rgb=P_["yellow"], wdt=8, a=int(240 * wide))
    vignette(cv, a=140)


# ===================================================================== T026  THE FIRE HURTS
def flame_tongue(cv, x, y, h, wd, bend, rgb, seed, w_=4.0, boil=1.4, a=255):
    """One licking tongue of flame (base centre x, y; height h; half-width wd; tip offset bend)."""
    P = [(x - wd, y), (x - wd * 0.85, y - h * 0.3), (x - wd * 0.35 + bend * 0.35, y - h * 0.66), (x + bend, y - h), (x + wd * 0.3 + bend * 0.55, y - h * 0.6),
         (x + wd * 0.8 + bend * 0.15, y - h * 0.28), (x + wd, y)]
    blob(cv, P, rgb, w=w_, seed=seed, boil=boil, n=5, a=a)


def big_fire(cv, x, y, s, T, seed=6100, a_glow=1.0):
    """The huge neon campfire: layered licking tongues (magenta -> red -> orange -> yellow -> white core), embers, heat waves."""
    firelight(cv, x, y - 250 * s, 900 * s, T, a=int(150 * a_glow), rgb=P_["orange"], seed=seed)
    firelight(cv, x, y - 200 * s, 480 * s, T, a=int(160 * a_glow), rgb=P_["yellow"], seed=seed + 1)
    layers = ((P_["magenta"], 7, 1.0, 190), (P_["red"], 6, 0.82, 160), (P_["orange"], 5, 0.66, 130), (P_["yellow"], 4, 0.48, 96), (P_["white"], 2, 0.3, 60))
    for li, (col, n, hk, half) in enumerate(layers):
        for j in range(n):
            u = (j + 0.5) / n
            ph = T * (4.2 + 0.6 * j + li) + j * 2.3 + li
            lick = 0.5 + 0.5 * math.sin(ph)
            fx = x + (u - 0.5) * 2 * half * s
            hh = (220 + 300 * math.sin(math.pi * (0.15 + 0.7 * u))) * s * hk * (0.72 + 0.42 * lick)
            ww = (half * 2 / n) * s * 0.95 + 18 * s
            bend = 40 * s * math.sin(ph * 0.7 + 1.0) * (1.2 - hk)
            flame_tongue(cv, fx, y + 6 * s, hh, ww, bend, col, seed + li * 20 + j, w_=4.5 if li == 0 else 3.0, boil=1.6)
    for k, ang in enumerate((-16, 16, -3)):                             # logs on top of the base
        cv.save(); cv.translate(x, y + 4 * s); cv.rotate(ang)
        blob(cv, rect_pts([(-200 * s, -20 * s), (200 * s, -20 * s), (200 * s, 20 * s), (-200 * s, 20 * s)], 3), (150, 60, 120), w=4.5, seed=seed + 90 + k, boil=0.8, n=3,
             shade=lambda c: (c.drawRect(R(-210 * s, 4 * s, 210 * s, 26 * s), paint((90, 30, 80))), c.drawRect(R(-210 * s, -24 * s, 210 * s, -12 * s), paint(P_["orange"], 160))))
        cv.restore()
    for k in range(5):                                                  # heat waves
        yy = y - 560 * s - k * 60 * s - (T * 80 * s) % (60 * s)
        xs = np.linspace(x - 200 * s, x + 200 * s, 9)
        line(cv, [(xx, yy + 12 * s * math.sin(xx * 0.03 + T * 6 + k)) for xx in xs], 3.0, P_["yellow"], seed=seed + 10 + k, boil=0.8, n=3, taper=(0.3, 0.3),
             a=int(120 * (1 - k / 5)))
    for k in range(18):                                                 # embers
        ph = (T * (0.45 + 0.1 * (k % 4)) + k * 0.173) % 1.0
        ex = x + (float(hsh(seed + k * 3.1)) - 0.5) * 420 * s + 50 * s * math.sin(T * 2 + k)
        ey = y - 200 * s - ph * 760 * s
        dots(cv, [(ex, ey)], (6 - 4 * ph) * s + 1, [P_["yellow"], P_["orange"], P_["white"], P_["hotpink"]][k % 4], a=int(255 * (1 - ph)))


def _low_wall(cv, x0, x1, ytop, ybot, seed=6150, rgb=None, rim=None, lit_top=None):
    rgb = rgb or mix(CV_ROCK2, P_["maroon"], 0.35)

    def sh(c):
        for k in range(int((x1 - x0) / 70)):
            xx = x0 + 35 + k * 70
            c.drawLine(xx, ytop + 26, xx - 2, ybot, paint(mix(rgb, INK, 0.4), stroke=3))
        c.drawLine(x0, (ytop + ybot) / 2 + 10, x1, (ytop + ybot) / 2 + 6, paint(mix(rgb, INK, 0.4), stroke=3))
        if lit_top:
            c.drawRect(R(x0 - 20, ytop - 10, x1 + 20, ytop + 22), paint(lit_top))
        if rim:
            c.drawRect(R(x0 - 20, ybot - 26, x1 + 20, ybot + 10), paint(rim, 120))
    blob(cv, rect_pts([(x0, ytop), (x1, ytop - 6), (x1 + 10, ybot), (x0 - 10, ybot)], 4), rgb, w=6, seed=seed, boil=0.9, n=3, shade=sh)


def _silhouette_puppets(cv, T, items, ytop, seed=6200, rgb=None, rim=None, phase=0.0):
    """Carriers' hoods + statues on poles rising above the low wall, back-lit into silhouettes with a hot rim."""
    rgb = rgb or (34, 12, 54)
    rim = rim or P_["orange"]
    for k, (kind, x, s) in enumerate(items):
        bob = 4 * math.sin(T * 4.2 + k * 1.3)
        hx, hy = x - 60 * s, ytop - 20 * s + bob
        blob(cv, ell(hx, hy, 46 * s, 56 * s, n=10), rgb, w=4.5, seed=seed + k * 7, boil=0.9,
             shade=lambda c, hx=hx, hy=hy, s=s: c.drawPath(poly_path(cr_closed(ell(hx - 30 * s, hy - 10 * s, 16 * s, 50 * s, n=8), 3)), paint(rim, 200)))
        line(cv, [(x, ytop + 40), (x + 4 * s, ytop - 200 * s + bob)], 9 * s + 2, (70, 40, 30), seed=seed + k * 7 + 1, boil=0.5, n=2, taper=(0, 0))
        sx, sy = x + 6 * s, ytop - 270 * s + bob
        P = np.array([(sx + px * s * 0.9, sy + py * s * 0.9) for px, py in SHAPES[kind]])
        blob(cv, P, rgb, w=4.5, seed=seed + k * 7 + 2, boil=0.8, n=4)
        brush(cv, cr_closed(jit(P + np.array([-4.0, -3.0]), 0.6, seed + k), 4), 4.0, rim, closed=True, seed=seed + k * 7 + 3, a=200)


def _pain_marks(cv, x, y, r, T, seed=0, a=255, n=5):
    """Comic 'ouch' marks: little zig-zag lightning ticks around a point."""
    for k in range(n):
        ang = math.radians(-150 + k * (120 / max(1, n - 1)) + 6 * math.sin(core.D * 0.9 + k))
        x0, y0 = x + r * math.cos(ang), y + r * math.sin(ang)
        d = 90
        pts = [(x0, y0), (x0 + d * 0.5 * math.cos(ang) - 12 * math.sin(ang), y0 + d * 0.5 * math.sin(ang) + 12 * math.cos(ang)),
               (x0 + d * 0.6 * math.cos(ang) + 12 * math.sin(ang), y0 + d * 0.6 * math.sin(ang) - 12 * math.cos(ang)), (x0 + d * math.cos(ang), y0 + d * math.sin(ang))]
        brush(cv, np.array(pts), 16.0, INK, taper=(0.1, 0.5), seed=seed + k + 20, a=a)
        brush(cv, np.array(pts), 9.0, P_["yellow"], taper=(0.1, 0.5), seed=seed + k, a=a)


def _gary_shadow(cv, x, y, s, a=150, blur=16):
    """Gary's own big soft shadow (eye + sweater silhouette) thrown on a wall."""
    p = skia.Paint(AntiAlias=True, Color=core.C(CV_SHADOW, a))
    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    path = poly_path(cr_closed(ell(x, y, 150 * s, 150 * s, n=12), 3))
    path.addPath(poly_path(cr_closed([(x - 128 * s, y + 360 * s), (x - 110 * s, y + 170 * s), (x - 55 * s, y + 112 * s), (x + 55 * s, y + 112 * s),
                                      (x + 110 * s, y + 170 * s), (x + 128 * s, y + 360 * s)], 4)))
    cv.drawPath(path, p)


def _hot_bg(cv, T, k=1.0, seed=6300, wall=True):
    """The prisoners' wall behind Gary, now blasted by the fire in front of him (camera at the fire)."""
    w.field(cv, CV_ROCK_DK)
    if wall:
        wall_surface(cv, [(-300, -300), (2220, -300), (2220, 1400), (-300, 1400)], T, seed=seed, cx=960, cy=560, glow=1.0)
    rock_mass(cv, [(-400, -400), (2400, -400), (2400, -20), (1500, 40), (700, 10), (-400, 50)], seed=seed + 3, rgb=CV_ROCK, rim=P_["orange"])
    stalactites(cv, 30, -200, 2150, seed=seed + 4, n=10, sc=0.9, T=T)


def T026_fire_hurts(cv, t, T, A):
    if t < 1.62:
        _t026_reveal(cv, t, T)
    elif t < 3.15:
        _t026_hurts(cv, t, T)
    elif t < 5.95:
        _t026_dark(cv, t, T)
    elif t < 8.12:
        _t026_blind(cv, t, T)
    else:
        _t026_agony(cv, t, T)


def _t026_reveal(cv, t, T):
    k = ease(t / 1.62)
    C = sets.Cam(cv, dict(x=lerp(-20, 60, k), y=lerp(10, -10, k), z=lerp(1.0, 1.1, k)))
    with C.layer(0.3):
        w.field(cv, CV_ROCK_DK)
        rock_mass(cv, [(-60, -60), (1990, -60), (1990, 1140), (-60, 1140)], seed=6010, rgb=(46, 16, 84), ink=4)
        glare(cv, 1150, 560, 1100, a=200, rgb=P_["orange"])
        for j in range(6):
            crystal(cv, -60 + j * 420 + 40 * math.sin(j), 640 + 60 * math.sin(j * 2.3), 0.9, T, seed=6020 + j)
        rock_mass(cv, [(-500, -400), (2500, -400), (2500, 60), (1600, 130), (900, 90), (200, 150), (-500, 110)], seed=6011, rgb=CV_ROCK, rim=P_["hotpink"])
        stalactites(cv, 120, -300, 2300, seed=6012, n=12, sc=1.2, rgb=mix(CV_ROCK2, P_["orange"], 0.25), T=T)
    with C.layer(0.6):
        big_fire(cv, 1150, 780, 2.05, T, seed=6100)
        light_rays(cv, 1150, 480, 1600, T, n=18, a=60, rgb=P_["yellow"], spin=5)
    with C.layer(0.75):
        _silhouette_puppets(cv, T, [("horse", 470 + t * 30, 1.0), ("bunny", 860 + t * 30, 1.0), ("tree", 1520 + t * 30, 1.05), ("bird", 1880 + t * 30, 0.95)], 740)
        _low_wall(cv, -300, 2300, 740, 900, seed=6150, rgb=(46, 16, 70), rim=P_["orange"], lit_top=P_["orange"])
    with C.layer(1.0):
        floor_band(cv, 900, T, seed=6160, rgb=(40, 14, 70), rim=P_["orange"], pebbles=8, mush=((300, 980, 0.9), (1650, 990, 0.9)))
        motes(cv, T, (0, 200, 1920, 1000), n=40, seed=6170, a=220, rise=120)
    with C.layer(1.2):                                               # Gary, from behind, dwarfed by the blaze
        gary_x(cv, 420, 1330, 1.3, T, seed=4400, yaw=196, stand=1.0, light=dict(dir=(1.0, -0.7), a=1.0, rgb=P_["yellow"], shadow=(30, 8, 60)),
               arms=dict(L=dict(hand=(-150, 300)), R=dict(hand=(150, 300))))
    vignette(cv, a=120)


def _gary_front_hot(cv, t, T, s, ex, ey, glow=1.0, **kw):
    """Gary facing the fire (which is behind the camera), with his big shadow on the wall behind him."""
    fy = ey + 360 * s + 108 * s
    _gary_shadow(cv, ex + 30, ey - 40, s * 1.25, a=150)
    return gary_x(cv, ex, fy, s, T, seed=4400, stand=1.0, light=dict(dir=(0.1, 1.0), a=glow, rgb=P_["yellow"]), **kw)


def _t026_hurts(cv, t, T):
    lt = t - 1.62
    sh = 5 * _seg(t, 1.7, 1.9) * (1 - _seg(t, 2.6, 3.1))
    cv.save(); _shake(cv, sh, seed=6400)
    C = sets.Cam(cv, dict(x=0, y=0, z=1.0 + 0.03 * lt))
    with C.layer(0.6):
        _hot_bg(cv, T, seed=6300)
        _prisoner_row(cv, T, [260, 1660], 1080, 1.9, seed=6310, view="side", glow=0.0)
    _fire_glow(cv, T, a=1.2, y=1250)
    with C.layer(1.0):
        wince = _seg(t, 1.72, 1.95)
        g = _gary_front_hot(cv, t, T, 1.55, 960, 470, glow=1.0, lid=lerp(0.35, 0.85, wince), tilt=-14 * wince, squint=0.55 * wince,
                            pupil=lerp(0.42, 0.16, wince), veins=0.6 * wince, mouth="wobbly" if wince > 0.5 else "o", mo=0.4, sweat=wince,
                            arms=dict(L=dict(hand=(-210, 160), pose="spread"), R=dict(hand=(210, 150), pose="spread")))
        if wince > 0.1:
            _pain_marks(cv, 960, 440, 330, T, seed=6420, a=int(255 * wince), n=7)
    light_rays(cv, 960, 1300, 1700, T, n=16, a=60, rgb=P_["yellow"], rot_deg=-160, width=0.4, spin=0)
    cv.restore()
    vignette(cv, a=110, rgb=(60, 10, 30))


def _three_garys(cv, T, t, seed=6500):
    """'His whole life in the dark': baby, kid and grown-up Gary in a row, chained, staring at a dim wall."""
    for k, (x, s, fy) in enumerate(((560, 0.36, 900), (930, 0.52, 920), (1420, 0.74, 945))):
        g = gary_x(cv, x, fy, s, T + k * 0.7, seed=4400 + k * 31, yaw=-62, pupil=0.78, iris=1.08, lid=0.3, mouth="smile",
                   arms=dict(L=dict(hand=(-60, 340, 120)), R=dict(hand=(60, 340, 120))), light=dict(dir=(-1.0, -0.2), a=0.7, rgb=P_["orange"], shadow=(10, 4, 30)))
        cyc = g["hip"][1] - 214 * s
        chain(cv, (x + 40 * s, cyc + 10 * s), (x + 150 * s, fy + 10), seed=seed + k, link=max(8, 14 * s), sag=10 * s, w=2.4)
        blob(cv, ell(x, cyc, 96 * s, 22 * s, n=10), IRON, w=3.5, seed=seed + 10 + k, boil=0.5)
        if k == 0:                                                      # baby: a pacifier
            mx, my = g["eye"][0] - 70 * s, g["eye"][1] + 95 * s
            blob(cv, ell(mx, my, 30 * s, 22 * s, n=8), P_["hotpink"], w=3, seed=seed + 20, boil=0.5)
            blob(cv, ell(mx - 20 * s, my, 12 * s, 14 * s, n=8), P_["yellow"], w=2.5, seed=seed + 21, boil=0.4)
            sparkle(cv, g["eye"][0] - 10, g["eye"][1] - 90 * s - 30, 10, P_["mint"], seed=seed + 22)


def _tally(cv, x, y, n, seed=0, rgb=None, a=220, sc=1.0):
    """Prison tally marks scratched into the wall: groups of four strokes crossed by a fifth; n strokes in all."""
    rgb = rgb or P_["lilac"]
    g = 0
    while n > 0:
        gx = x + (g % 6) * 92 * sc
        gy = y + (g // 6) * 96 * sc
        k = min(5, n)
        for j in range(min(4, k)):
            xx = gx + j * 16 * sc
            line(cv, [(xx, gy), (xx + 3 * sc, gy + 60 * sc)], 5.5 * sc, rgb, seed=seed + g * 7 + j, boil=0.8, n=2, taper=(0.15, 0.3), a=a)
        if k == 5:
            line(cv, [(gx - 10 * sc, gy + 46 * sc), (gx + 66 * sc, gy + 12 * sc)], 5.5 * sc, rgb, seed=seed + g * 7 + 5, boil=0.8, n=2, taper=(0.15, 0.3), a=a)
        n -= k
        g += 1


def _t026_dark(cv, t, T):
    lt = t - 3.15
    C = sets.Cam(cv, dict(x=lerp(-160, 160, ease(lt / 2.8)), y=0, z=1.12))
    with C.layer(0.5):
        w.field(cv, (16, 6, 36))
        p = skia.Paint(AntiAlias=True)
        p.setShader(skia.GradientShader.MakeRadial(skia.Point(220, 420), 1100, [core.C((150, 50, 80)), core.C((56, 18, 70)), core.C((16, 6, 36))], [0.0, 0.5, 1.0]))
        cv.drawRect(R(-400, -400, 2400, 1500), p)
        shadow_shape(cv, "bunny", 180, 420, 2.0, T, rgb=(40, 8, 40), a=210, seed=6510)
        _tally(cv, 640, 120, int(4 + 60 * _cl(lt / 2.6)), seed=6512, rgb=mix(P_["lilac"], P_["hotpink"], 0.3), a=170, sc=0.9)
        w.stars(cv, 6511, (-300, -100, 2300, 500), n=60, big=0, rmax=1.6)
        for k in range(4):
            glow_mushroom(cv, 120 + k * 560, 905, 0.9, T, seed=6515 + k)
    with C.layer(0.8):
        rock_mass(cv, [(-500, 900), (600, 880), (1400, 905), (2400, 890), (2400, 1400), (-500, 1400)], seed=6520, rgb=(34, 14, 64), rim=(110, 40, 110))
    with C.layer(1.0):
        _three_garys(cv, T, t, seed=6500)
    wash(cv, (175, 150, 235), 255, blend="multiply")
    with C.layer(1.0):
        th = math.radians(-62)
        for k, (x, s, fy) in enumerate(((560, 0.36, 900), (930, 0.52, 920), (1420, 0.74, 945))):
            ex = x + (-4 * math.cos(th) + 136 * math.sin(th)) * s
            ey = fy - 360 * s - 22 * s + 6 * math.sin((T + k * 0.7) * 3.1) * s
            dots(cv, [(ex - 14 * s, ey - 22 * s)], 10 * s + 1.5, P_["white"])
            sparkle(cv, ex - 40 * s, ey - 60 * s, 8 + 14 * s, P_["mint"], seed=6540 + k, w=1.5)
        motes(cv, T, (-200, 100, 2100, 950), n=26, seed=6545, a=160, rise=25, rgb=[P_["mint"], P_["lilac"], P_["teal"]], r=2.6)
    caption(cv, "...IN THE DARK", 1430, 220, lt, 0.3, size=86, fill=P_["lilac"], font="londrina", seed=6530, shadow_rgb=(10, 4, 26), dur=0.6)
    vignette(cv, a=150, rgb=(4, 0, 12))


def _t026_blind(cv, t, T):
    lt = t - 5.95
    bloom = _seg(t, 6.0, 6.6)
    blind = _seg(t, 6.83, 7.1)
    white = _seg(t, 6.9, 8.05)
    squeeze = _seg(t, 7.55, 8.05)
    sh = 7 * blind
    cv.save(); _shake(cv, sh, seed=6600)
    C = sets.Cam(cv, dict(x=0, y=-40, z=1.05 + 0.25 * ease(lt / 2.17)))
    with C.layer(0.6):
        _hot_bg(cv, T, seed=6610)
    _fire_glow(cv, T, a=1.0 + 0.6 * bloom, y=1250)
    with C.layer(1.0):
        g = _gary_front_hot(cv, t, T, 1.55, 960, 470, glow=1.0, lid=lerp(lerp(0.35, -0.3, blind), 0.9, squeeze), pupil=lerp(lerp(0.5, 0.42, bloom), 0.06, blind),
                            iris=lerp(1.0, 0.82, blind), shock=blind, veins=blind, mouth="o" if squeeze < 0.5 else "scream", mo=lerp(0.3, 0.9, blind),
                            shut=squeeze * 0.6, tilt=0, arms=dict(L=dict(hand=(lerp(-140, -240, blind), lerp(330, 40, blind)), pose="spread"),
                                                                    R=dict(hand=(lerp(140, 240, blind), lerp(330, 30, blind)), pose="spread")))
    ex, ey = C.to_screen(g["eye"][0], g["eye"][1], 1.0)
    rr = g["r"] * C.zoom(1.0)
    light_rays(cv, 960, 1500, 2600, T, n=20, a=int(40 + 130 * bloom), rgb=P_["white"], rot_deg=-90 - 60, width=0.5, spin=0)
    glare(cv, 960, 1250, 1200, a=int(150 * bloom + 80 * white), rgb=P_["yellow"])
    lens_flare(cv, 960, 1300, T, a=bloom, seed=6625)
    if blind > 0:
        px, py = ex - 4 * 1.55 * C.zoom(1.0), ey - 22 * 1.55 * C.zoom(1.0)
        sparkle(cv, px + 70, py - 70, 34 * pop(t, 6.83, 0.3), P_["white"], seed=6620)
        burst_lines(cv, ex, ey, rr * 1.1, rr * 1.1 + 200, n=20, seed=6621, rgb=P_["yellow"], wdt=9, a=int(230 * blind * (1 - white)))
        sfx(cv, "PING!", ex + rr + 150, ey - rr * 0.75, 90, t, 6.86, seed=6622, fills=[P_["white"], P_["yellow"]], rot_deg=12, hold=0.7)
    cv.restore()
    wash(cv, P_["white"], int(200 * white ** 1.5), blend="screen")


def lens_flare(cv, sx, sy, T, a=1.0, seed=0, n=7):
    """Psychedelic lens flare: rainbow discs + hexagons strung along the line from the light through frame centre."""
    dx, dy = W / 2 - sx, H / 2 - sy
    cols = [P_["magenta"], P_["teal"], P_["yellow"], P_["violet"], P_["acid"], P_["hotpink"], P_["blue"]]
    for k in range(n):
        u = 0.35 + k * 0.32 + 0.05 * math.sin(T * 0.7 + k)
        px, py = sx + dx * u, sy + dy * u
        r = (40 + 90 * float(hsh(seed + k))) * (1.0 + 0.1 * math.sin(T * 2 + k))
        p = skia.Paint(AntiAlias=True)
        col = cols[k % len(cols)]
        if k % 2:
            p.setShader(skia.GradientShader.MakeRadial(skia.Point(px, py), r, [core.C(col, int(40 * a)), core.C(col, int(110 * a)), core.C(col, 0)], [0.0, 0.85, 1.0]))
            p.setBlendMode(skia.BlendMode.kScreen)
            cv.drawCircle(px, py, r, p)
        else:
            hexp = [(px + r * math.cos(math.radians(60 * j + 15 * k)), py + r * math.sin(math.radians(60 * j + 15 * k))) for j in range(6)]
            p.setColor(core.C(col, int(70 * a)))
            p.setBlendMode(skia.BlendMode.kScreen)
            cv.drawPath(poly_path(hexp), p)
            cv.drawPath(poly_path(hexp), paint(mix(col, P_["white"], 0.4), int(120 * a), stroke=3))


def _bleached_cave(cv, T, k=1.0, seed=6700, fire_x=2050, fire_y=640, puppets=True):
    """The cave as Gary sees it now: everything blown out -- white-hot at the fire, then yellow, orange and hot pink
    at the edges; pale lilac rock in thin peach ink; rotating rays; rainbow lens flares."""
    g = skia.Paint(AntiAlias=True)
    g.setShader(skia.GradientShader.MakeRadial(skia.Point(fire_x, fire_y), 2300, [core.C(P_["white"]), core.C(mix(P_["yellow"], P_["white"], 0.45)),
                                                                                 core.C(mix(P_["orange"], P_["white"], 0.25)), core.C(mix(P_["hotpink"], P_["white"], 0.2)),
                                                                                 core.C(mix(P_["magenta"], P_["white"], 0.25))], [0.0, 0.25, 0.5, 0.75, 1.0]))
    cv.drawRect(R(-400, -400, 2400, 1500), g)
    w.sunburst(cv, fire_x, fire_y, 2600, 26, [mix(P_["yellow"], P_["white"], 0.55), mix(P_["yellow"], P_["white"], 0.3)], rot_deg=T * 6, seed=seed)
    pale = mix(P_["lilac"], P_["white"], 0.45)
    pk = mix(INK, P_["hotpink"], 0.55)
    blob(cv, [(-400, -400), (2400, -400), (2400, 40), (1500, 100), (800, 60), (-400, 110)], pale, w=4, ink=pk, seed=seed, boil=1.0, n=4,
         shade=lambda c: c.drawRect(R(-400, 0, 2400, 120), paint(mix(P_["hotpink"], P_["white"], 0.5))))
    for k2 in range(10):
        sx = -100 + k2 * 230
        L = 120 + 90 * float(hsh(seed + k2))
        blob(cv, [(sx - 34, 60), (sx + 34, 60), (sx + 4, L), (sx - 4, L)], pale, w=3.5, ink=pk, seed=seed + 10 + k2, boil=0.8, n=3)
    blob(cv, [(-400, 900), (800, 880), (2400, 900), (2400, 1500), (-400, 1500)], mix(P_["hotpink"], P_["white"], 0.62), w=4, ink=pk, seed=seed + 30, boil=1.0, n=4,
         shade=lambda c: [c.drawLine(-400 + j * 260, 900, -700 + j * 300, 1500, paint(mix(P_["hotpink"], P_["white"], 0.4), stroke=6)) for j in range(12)])
    light_rays(cv, fire_x, fire_y, 2700, T, n=22, a=120, rgb=P_["white"], spin=7)
    glare(cv, fire_x, fire_y, 900, a=255, rgb=P_["white"])
    lens_flare(cv, fire_x, fire_y, T, a=1.0, seed=seed + 50)


def _t026_agony(cv, t, T):
    loud = loud_at("G02", T)
    if t < 9.05:                                                     # 'AAAH!' -- extreme close-up
        cv.save(); _shake(cv, 16 + 10 * loud, seed=6800, rot_amp=1.2)
        _bleached_cave(cv, T, seed=6810, fire_x=960, fire_y=1300)
        s = 3.3
        gary_x(cv, 960, 430 + 360 * s, s, T, seed=4400, shut=1.0, crinkle=1.0, mouth="scream", loud=loud, tears=1.0, veins=1.0, bob=0.5,
               light=dict(dir=(0, 1), a=0.6, rgb=P_["yellow"]))
        burst_lines(cv, 960, 520, 640, 1100, n=22, seed=6820, rgb=INK, wdt=11, jag=14)
        cv.restore()
        sfx(cv, "AAAH!", 250, 190, 140, t, 8.15, seed=6830, fills=[P_["red"], P_["magenta"], P_["orange"]], font="shrik", rot_deg=-14, dur=0.2, hold=5)
        sfx(cv, "AAAH!", 1690, 820, 120, t, 8.35, seed=6831, fills=[P_["orange"], P_["yellow"], P_["red"]], font="shrik", rot_deg=12, dur=0.2, hold=5)
        return
    lt = t - 9.05
    shake = 5 + 9 * loud
    cv.save(); _shake(cv, shake, seed=6840, rot_amp=0.6)
    push = ease((t - 9.05) / 6.6)
    C = sets.Cam(cv, dict(x=lerp(-60, -100, push), y=lerp(0, -40, push), z=lerp(1.0, 1.28, push)))
    with C.layer(0.4):
        _bleached_cave(cv, T, seed=6850, fire_x=2150, fire_y=600)
    with C.layer(0.8):
        _silhouette_puppets(cv, T, [("horse", 1480, 0.8), ("tree", 1780, 0.85)], 780, rgb=mix(P_["lilac"], P_["white"], 0.35), rim=P_["white"], seed=6860)
        _low_wall(cv, 1270, 2400, 780, 900, seed=6870, rgb=mix(P_["lilac"], P_["white"], 0.4))
    s = 1.15
    gx = 840 + 40 * math.sin(lt * 2.3)
    fy = 1010
    if t < 10.6:                                                      # 'MY EVERYTHING!' -- tiny hands can't cover the giant eye
        k = _seg(t, 9.05, 9.3)
        kw = dict(yaw=lerp(30, 12, k), lean=-8 + 6 * math.sin(lt * 7), shut=1.0, crinkle=1.0, mouth="scream", tears=1.0, veins=1.0,
                  arms=dict(L=dict(hand=(-60, 20, 160), pose="spread", ang=-60), R=dict(hand=(70, 0, 160), pose="spread", ang=-120)),
                  step=lt * 9, knees=0.4 * math.sin(lt * 9))
    elif t < 12.7:                                                    # 'Zee, I'm one big eye!' -- pointing at all of himself
        lt2 = t - 10.6
        k = _seg(t, 10.6, 10.9)
        pt = _seg(t, 11.3, 11.55)
        wv = math.sin(lt2 * 8)
        kw = dict(yaw=lerp(12, -22, k) * (1 - pt), lean=4 * wv, shut=0.86, crinkle=0.6, mouth="scream", tears=0.8, veins=1.0, knees=0.2 * wv,
                  arms=dict(L=dict(hand=(lerp(-250, -175, pt), lerp(160, 20, pt) + 14 * wv), pose="point" if pt > 0.5 else "spread", ang=lerp(-140, -20, pt)),
                            R=dict(hand=(lerp(250, 180, pt), lerp(150, 10, pt) - 14 * wv), pose="point" if pt > 0.5 else "spread", ang=lerp(-40, 200, pt))))
    else:                                                             # 'This is the worst possible thing!' -- collapse and wail
        lt3 = t - 12.7
        drop = _seg(t, 12.7, 13.05)
        kick = math.sin(lt3 * 14)
        kw = dict(yaw=0, lean=-6 * math.sin(lt3 * 5), shut=1.0, crinkle=1.0, mouth="scream", tears=1.0, tear_up=1.0, veins=1.0, stand=1 - drop,
                  arms=dict(L=dict(hand=(-220 - 30 * kick, -150 + 60 * kick), pose="spread"), R=dict(hand=(220 + 30 * kick, -160 - 60 * kick), pose="spread")))
        fy = 1010 - 30 * drop
    kw.setdefault("stand", 1.0)
    with C.layer(1.0):
        gary_x(cv, gx, fy, s, T, seed=4400, loud=loud, light=dict(dir=(1, -0.2), a=0.9, rgb=P_["white"]), bleach=0.12, **kw)
        ey = fy - 360 * s - 108 * s * kw["stand"]
        if t < 10.6:
            motion_lines(cv, gx + 280, ey + 40, 180, n=4, L=140, gap=40, seed=6880, wdt=6)
        burst_lines(cv, gx, ey, 250, 380, n=12, seed=6890, rgb=INK, wdt=9, a=230)
    cv.restore()
    if 11.4 < t < 12.75:                                              # the label gag
        k = pop(t, 11.45, 0.3) * (1 - _seg(t, 12.55, 12.75))
        cv.save(); cv.translate(1480, 250); cv.rotate(-6 + 2 * math.sin(core.D)); cv.scale(k, k)
        paint_text(cv, "100% EYE", 0, 30, font="shrik", size=104, fills=[P_["magenta"], P_["violet"], P_["blue"]], ink_w=6, shadow=(7, 7), seed=6895)
        line(cv, [(-150, 70), (-300, 170), (-420, 230)], 9, INK, seed=6896, boil=0.8, n=4, taper=(0.1, 0.1))
        blob(cv, [(-445, 240), (-400, 200), (-392, 256)], INK, w=0, seed=6897, boil=0.4, n=2, misreg=(0, 0))
        cv.restore()


# ===================================================================== T027  THE PUPPETS
def dotted_arrow(cv, p0, p1, bulge, u, seed=0, rgb=None, gap=34, r=8.0, a=255, head=True, ctrl=None):
    """A dotted arc from p0 to p1 (quadratic bow `bulge` px), revealed up to fraction u, with an arrowhead at the tip."""
    if u <= 0:
        return
    rgb = rgb or P_["yellow"]
    (x0, y0), (x1, y1) = p0, p1
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) + 1e-6
    cx, cy = mx - dy / L * bulge, my + dx / L * bulge
    if ctrl is not None:
        cx, cy = ctrl
    n = max(4, int(L / gap))
    m = int(n * min(1.0, u))
    pts = []
    for k in range(m + 1):
        q = k / n
        x = (1 - q) ** 2 * x0 + 2 * (1 - q) * q * cx + q * q * x1
        y = (1 - q) ** 2 * y0 + 2 * (1 - q) * q * cy + q * q * y1
        pts.append((x, y))
    if len(pts) > 1:
        dots(cv, pts[:-1], r + 3.5, INK, a=a)
        dots(cv, pts[:-1], r, rgb, a=a)
    if head and len(pts) > 1:
        ex, ey = pts[-1]
        px, py = pts[-2]
        d = math.atan2(ey - py, ex - px)
        tip = (ex + 26 * math.cos(d), ey + 26 * math.sin(d))
        blob(cv, [tip, (ex + 26 * math.cos(d + 2.3), ey + 26 * math.sin(d + 2.3)), (ex + 26 * math.cos(d - 2.3), ey + 26 * math.sin(d - 2.3))], rgb, w=4,
             seed=seed, boil=0.5, n=2, a=a)


def _statue_glow(cv, kind, x, y, s, T, seed, rgb, glow=0.0):
    if glow > 0:
        glare(cv, x, y, 190 * s, a=int(150 * glow), rgb=P_["yellow"])
    statue(cv, kind, x, y, s, T, seed=seed, rgb=rgb)
    blob(cv, ell(x, y + 110 * s, 60 * s, 14 * s, n=8), mix(CV_ROCK2, P_["orange"], 0.4), w=3.5, seed=seed + 40, boil=0.5)


def T027_puppets_reveal(cv, t, T, A):
    if t < 7.4:
        _t027_wide(cv, t, T)
    elif t < 9.27:
        _t027_doubt(cv, t, T)
    else:
        _t027_sulk(cv, t, T)


STATUES = [("horse", 1270, 585, 0.95, 5711, P_["peach"]), ("bunny", 1490, 575, 1.0, 5712, P_["cream"]), ("tree", 1715, 560, 0.95, 5713, P_["mint"])]
WALL_SH = [("horse", 200, 300, 1.25), ("bunny", 380, 560, 1.35), ("tree", 170, 770, 1.15)]


def _t027_wide(cv, t, T):
    k = ease(t / 7.4)
    C = sets.Cam(cv, dict(x=lerp(60, 0, k), y=lerp(10, -20, k), z=lerp(1.08, 1.0, k)))
    with C.layer(0.4):
        w.field(cv, CV_ROCK_DK)
        rock_mass(cv, [(-60, -60), (1990, -60), (1990, 1140), (-60, 1140)], seed=5701, rgb=(44, 16, 80), ink=4)
        glare(cv, 2000, 650, 1100, a=200, rgb=P_["orange"])
        for j in range(5):
            crystal(cv, 700 + j * 300, 640 + 50 * math.sin(j * 2.3), 0.85, T, seed=5702 + j)
    with C.layer(0.7):
        big_fire(cv, 2010, 770, 1.15, T, seed=5705)
    with C.layer(0.85):
        wall = [(-300, 60), (560, 90), (640, 420), (600, 780), (540, 960), (-300, 960)]
        wall_surface(cv, wall, T, seed=5706, cx=250, cy=560)
        pulse = _seg(t, 4.0, 4.4) * (1 - _seg(t, 5.9, 6.4))
        cv.save(); cv.clipPath(poly_path(cr_closed(wall, 4)), doAntiAlias=True)
        for j, (kind, sx, sy, ss) in enumerate(WALL_SH):
            if pulse > 0:
                glare(cv, sx, sy, 230 * ss, a=int(120 * pulse * (0.7 + 0.3 * math.sin(T * 8 + j))), rgb=P_["yellow"])
            shadow_shape(cv, kind, sx, sy, ss, T, seed=5720 + j)
        cv.restore()
        rock_mass(cv, [(560, 60), (700, 40), (760, 300), (720, 620), (690, 980), (560, 980), (610, 700), (640, 400)], seed=5716, rgb=CV_ROCK2, rim=P_["orange"], rim_side=1)
        rock_mass(cv, [(-500, -400), (2500, -400), (2500, 30), (1700, 90), (1000, 60), (400, 110), (-500, 70)], seed=5707, rgb=CV_ROCK, rim=P_["orange"])
        stalactites(cv, 80, -200, 2300, seed=5708, n=12, sc=1.0, T=T)
    with C.layer(1.0):
        floor_band(cv, 880, T, seed=5709, rgb=CV_ROCK2, rim=P_["orange"], pebbles=10, mush=((660, 960, 0.9), (1020, 1000, 0.8)))
        glow_k = _seg(t, 6.15, 6.5) * (1 - _seg(t, 7.1, 7.4))
        for kind, sx, sy, ss, sd, col in STATUES:
            _statue_glow(cv, kind, sx, sy, ss, T, sd, col, glow=glow_k * (0.8 + 0.2 * math.sin(T * 9)))
        _low_wall(cv, 1130, 2300, 700, 900, seed=5714, rgb=mix(CV_ROCK2, P_["maroon"], 0.3), lit_top=mix(CV_ROCK2, P_["orange"], 0.5))
        # the carrier presents the statues
        pt = _seg(t, 0.45, 1.25)
        cs, chx, chy = 1.45, 1060, 960
        ctop = chy - 300 * cs
        hand = (lerp(chx + 40, chx + 230, pt), lerp(ctop + 330, ctop + 160, pt))
        hooded(cv, chx, chy, cs, T, seed=5715, face=-1, hands=[dict(world=hand, pose="point" if pt > 0.6 else "open", ang=lerp(80, -18, pt), side=1, bend=1)],
               glaze=(P_["hotpink"], 70), rim=P_["orange"], rim_side=1)
        # Gary: squinting, still teary, eyes on the carrier -> the statues -> following the arrows to the wall -> back
        ph = [(0.0, 40, 0.5), (1.3, 55, 0.7), (4.2, 50, 0.6), (4.8, -35, -0.6), (6.3, -45, -0.7), (6.9, 40, 0.5)]
        yaw, lk = ph[0][1], ph[0][2]
        for (t0, y0, l0), (t1, y1, l1) in zip(ph[:-1], ph[1:]):
            if t >= t1 - 0.4:
                yaw = lerp(y0, y1, _seg(t, t1 - 0.4, t1))
                lk = lerp(l0, l1, _seg(t, t1 - 0.4, t1))
        gary_x(cv, 790, 975, 0.82, T, seed=4400, yaw=yaw, look=(lk * 0.3, -0.25), stand=1.0, lid=0.75, squint=0.35, veins=0.5, pupil=0.3,
               mouth="flat" if t > 6.9 else "o", mo=0.25, light=dict(dir=(1, -0.3), a=0.8, rgb=P_["orange"]),
               arms=dict(L=dict(hand=(-150, 310)), R=dict(hand=(150, 310))))
        # dotted arrows statue -> shadow
        cols = [P_["yellow"], P_["teal"], P_["hotpink"]]
        for j, ((kind, sx, sy, ss, sd, col), (_, wx, wy, ws)) in enumerate(zip(STATUES, WALL_SH)):
            u = _seg(t, 4.0 + j * 0.55, 5.15 + j * 0.55)
            ctrl = [(820, -60), (900, 40), (640, -170)][j]
            dotted_arrow(cv, (sx - 20, sy - 110), (wx + 90 + 20 * j, wy - 40), 0, u, seed=5730 + j, rgb=cols[j], ctrl=ctrl)
    with C.layer(1.25):
        _fg_rocks(cv, T, seed=5740, left=False)
    vignette(cv, a=130)


def _t027_doubt(cv, t, T):
    lt = t - 7.4
    C = sets.Cam(cv, dict(x=0, y=0, z=1.0 + 0.04 * lt))
    with C.layer(0.5):
        w.field(cv, CV_ROCK_DK)
        rock_mass(cv, [(-60, -60), (1990, -60), (1990, 1140), (-60, 1140)], seed=5751, rgb=(44, 16, 80), ink=4)
        glare(cv, 1900, 650, 1000, a=190, rgb=P_["orange"])
        big_fire(cv, 1950, 800, 0.9, T, seed=5752)
        for j, (kind, sx, sy, ss, sd, col) in enumerate(STATUES):
            _statue_glow(cv, kind, 1150 + j * 260, 560 - 10 * j, 1.15, T, sd, col)
        _low_wall(cv, 950, 2300, 700, 900, seed=5753, rgb=mix(CV_ROCK2, P_["maroon"], 0.3), lit_top=mix(CV_ROCK2, P_["orange"], 0.5))
        rock_mass(cv, [(-500, -400), (2500, -400), (2500, 20), (1500, 70), (600, 40), (-500, 80)], seed=5754, rgb=CV_ROCK, rim=P_["orange"])
        stalactites(cv, 60, -200, 2300, seed=5755, n=11, sc=1.0, T=T)
    with C.layer(1.0):
        sk = _seg(t, 7.6, 8.1)
        tilt_ = lerp(0, 34, sk)
        g = gary_x(cv, 640, 470 + 360 * 1.55 + 108 * 1.55, 1.55, T, seed=4400, yaw=18, look=(lerp(0.2, 0.75, sk), 0.05), stand=1.0, lid=lerp(0.6, 0.95, sk),
                   tilt=tilt_, squint=lerp(0.3, 0.6, sk), pupil=lerp(0.32, 0.22, sk), veins=0.4, mouth="flat", light=dict(dir=(1, -0.2), a=0.8, rgb=P_["orange"]),
                   arms=dict(L=dict(hand=(lerp(-150, 30, sk), lerp(310, 190, sk), 90), pose="fist", ang=lerp(100, -70, sk)),
                             R=dict(hand=(lerp(150, 70, sk), lerp(310, 250, sk), 60), pose="open", ang=lerp(80, 170, sk))))
        if t > 8.25:                                                   # '...' thought dots
            for j in range(3):
                kk = pop(t, 8.25 + j * 0.18, 0.25)
                if kk > 0:
                    blob(cv, ell(990 + j * 62, 210 - j * 26, 22 * kk, 22 * kk, n=8), P_["white"], w=4, seed=5760 + j, boil=0.6)
    vignette(cv, a=130)


def plush_shadow(cv, x, y, s, T, ang=0.0, flop=0.0, seed=5800, a=245):
    """The bunny SHADOW peeled off the wall and held like a floppy plush toy: a soft-edged flat maroon silhouette."""
    cv.save(); cv.translate(x, y); cv.rotate(ang)
    cv.scale(1.0 - 0.18 * flop, 1.0 + 0.06 * flop)
    if flop:
        cv.skew(0.25 * flop * math.sin(T * 4.0), 0)
    shadow_shape(cv, "bunny", 0, 0, s, T, rgb=CV_SHADOW, a=a, seed=seed, wobble=1.5)
    cv.restore()


def _t027_sulk(cv, t, T):
    loud = loud_at("G03", T)
    pz = ease((t - 10.9) / 1.4)
    C = sets.Cam(cv, dict(x=lerp(0, 60, pz), y=lerp(0, -10, pz), z=lerp(1.0, 1.32, pz) + 0.01 * (t - 9.27)))
    bx, by, bs = 1000, 470, 2.0
    gx0, gfy0, s0 = 860, 1065, 1.05
    walk = _seg(t, 10.95, 11.55)
    back = _seg(t, 11.95, 12.25)                                    # steps back toward camera with his prize
    gx = lerp(lerp(gx0, bx + 30, walk), bx + 10, back)
    gfy = lerp(lerp(gfy0, 800, walk), 880, back)
    s = lerp(lerp(s0, 0.62, walk), 0.74, back)
    peel = _seg(t, 11.5, 11.85)
    held = t >= 11.85
    with C.layer(0.6):
        w.field(cv, CV_ROCK_DK)
        wall_surface(cv, [(-300, -100), (2220, -100), (2220, 860), (-300, 860)], T, seed=5770, cx=1000, cy=480)
        shadow_shape(cv, "horse", 300, 360, 1.7, T, seed=5771)
        shadow_shape(cv, "tree", 1700, 330, 1.6, T, seed=5772)
        if peel > 0:                                                  # the pale imprint left on the wall
            shadow_shape(cv, "bunny", bx, by, bs, T, rgb=mix(CV_WALL, P_["white"], 0.45), a=int(150 * peel), seed=5774, wobble=0.5)
        if not held:
            cv.save(); cv.translate(bx - 80 * bs, by); cv.scale(1 - 0.55 * peel, 1 - 0.1 * peel); cv.skew(-0.5 * peel, 0); cv.translate(-(bx - 80 * bs), -by)
            cv.translate(160 * peel, -40 * peel)
            shadow_shape(cv, "bunny", bx, by, bs, T, seed=5773)
            cv.restore()
        _gary_shadow(cv, gx + 40 * (1 - walk), gfy - 600 * s - 200 * (1 - walk), s * (1.6 - 0.5 * walk), a=int(90 + 50 * walk), blur=int(26 - 14 * walk))
        rock_mass(cv, [(-500, -400), (2500, -400), (2500, 20), (1700, 70), (1000, 40), (400, 80), (-500, 50)], seed=5775, rgb=CV_ROCK, rim=P_["orange"])
        stalactites(cv, 60, -200, 2300, seed=5776, n=12, sc=1.0, T=T)
        floor_band(cv, 800, T, seed=5777, rgb=CV_ROCK2, rim=P_["orange"], pebbles=10, mush=((120, 880, 0.9), (1800, 870, 0.9)))
    _fire_glow(cv, T, a=0.8)
    with C.layer(1.0):
        for j, px in enumerate((150, 1760)):
            prisoner(cv, px, 1060, 1.9, T, seed=5780 + j * 13, view="back", anchor=(px + 70, 1100), glow=0.4)
        cross = _seg(t, 9.27, 9.5)
        turn = _seg(t, 10.6, 11.0)
        shake = math.sin((t - 9.85) * 26) * 26 * (_seg(t, 9.85, 9.95) * (1 - _seg(t, 10.25, 10.4)))
        kw = dict(lid=0.72, tilt=-24, mouth="pout")
        ey_w = gfy - (360 + 108) * s
        plush = None
        if held:                                                      # cuddling the shadow like a teddy bear
            yaw = lerp(180, 360, _seg(t, 11.85, 12.15))
            rock_ = math.sin(T * 4.0)
            putback = _seg(t, 12.25, 12.4)
            kw = dict(lid=lerp(0.6, 0.7, putback), tilt=-26 * putback, shut=lerp(1.0, 0.0, putback), mouth="pout" if putback > 0.3 else "grin",
                      look=(0.0, 0.15), tears=0.2 * putback)
            arms = dict(L=dict(hand=(95, 300, 110), pose="flat", ang=-30), R=dict(hand=(-100, 345, 120), pose="flat", ang=210))
            lean = 6 * rock_
            plush = (gx + 70 * s + 14 * rock_, ey_w + 345 * s, 1.75 * s, 16 + 8 * rock_)
        elif walk >= 1.0:                                             # reaching up to peel it off the wall
            yaw = 180
            arms = dict(L=dict(world=(lerp(gx + 140 * s, bx + 120, _seg(t, 11.4, 11.55)), lerp(ey_w + 200 * s, by - 20, _seg(t, 11.4, 11.55))), pose="pinch",
                               behind=True),
                        R=dict(world=(lerp(gx - 140 * s, bx + 60 + 140 * peel, _seg(t, 11.4, 11.55)), lerp(ey_w + 200 * s, by - 130 + 60 * peel, _seg(t, 11.4, 11.55))),
                               pose="pinch", behind=True))
            lean = -5 * peel
        elif turn > 0:
            yaw = lerp(0, 180, turn)
            arms = dict()
            lean = 0.0
        else:
            yaw = lerp(0, -28, _seg(t, 9.3, 9.45)) * (1 - _seg(t, 9.75, 9.9)) + shake
            arms = dict(L=dict(hand=(lerp(-150, 100, cross), lerp(310, 205, cross), lerp(0, 90, cross)), pose="fist", ang=lerp(100, -25, cross)),
                        R=dict(hand=(lerp(150, -100, cross), lerp(310, 258, cross), lerp(0, 110, cross)), pose="fist", ang=lerp(80, 205, cross)))
            lean = 0.0
        if plush is not None and _seg(t, 11.85, 12.15) < 0.5:          # still facing the wall: the shadow is in front of him
            plush_shadow(cv, plush[0], plush[1] - 30, plush[2], T, ang=plush[3], flop=1.0)
        gary_x(cv, gx, gfy, s, T, seed=4400, yaw=yaw, stand=1.0, step=(t * 11 if 0.02 < walk < 0.98 or 0.02 < back < 0.98 else None), loud=loud, mo=0.0,
               arms=arms, arms_off=plush is not None and _seg(t, 11.85, 12.15) >= 0.5, light=dict(dir=(0, 1), a=0.6, rgb=P_["orange"]), lean=lean, **kw)
        if plush is not None and _seg(t, 11.85, 12.15) >= 0.5:         # facing us: hugging it to his chest
            plush_shadow(cv, plush[0], plush[1], plush[2], T, ang=plush[3], flop=0.6)
            gary_x(cv, gx, gfy, s, T, seed=4400, yaw=yaw, stand=1.0, loud=loud, mo=0.0, arms=arms, light=dict(dir=(0, 1), a=0.6, rgb=P_["orange"]),
                   lean=lean, arms_only=True, **kw)
        if peel > 0.2 and not held:
            sfx(cv, "SHLUPP!", bx + 330, by - 250, 84, t, 11.6, seed=5796, fills=[P_["acid"], P_["yellow"]], rot_deg=-10, hold=0.6)
        if held:
            hk = _seg(t, 11.9, 12.1)
            for j in range(5):
                u = (T * 0.6 + j * 0.2) % 1.0
                heart(cv, gx - 150 + 75 * j + 30 * math.sin(T * 2 + j), ey_w - 120 - u * 260, (16 + 10 * (j % 2)) * hk, seed=5790 + j,
                      rgb=[P_["hotpink"], P_["magenta"], P_["red"]][j % 3], a=int(255 * hk * (1 - u)))
        if 9.3 < t < 10.5:
            sfx(cv, "HMPH!", gx + 330, gfy - 720, 96, t, 9.32, seed=5795, fills=[P_["lilac"], P_["white"]], rot_deg=8, hold=0.9)
    vignette(cv, a=130)


# ===================================================================== T029  DRAGGED UP INTO THE SUN
SLOPE = 0.62


def _py(x):
    """Surface height of the long steep path (world coords)."""
    return 900 - SLOPE * x + 14 * math.sin(x * 0.011) + 8 * math.sin(x * 0.037)


def _drag_trio(cv, T, X, s, seed=6900, look_back=1.0, light=None, bleach=0.0, gary_kw=None, floor=None, d=1, sil=0.0, hood_rim=None):
    """Two hooded carriers hauling Gary along a floor (default: up the long slope `_py`) by his arms: the leader ahead
    pulling, the other behind shoving. X = Gary's world x; d = +1 travelling right, -1 travelling left.
    sil > 0 darkens everyone toward a back-lit silhouette."""
    floor = floor or _py
    walk = T * 7.5
    lx = X + d * 240 * s
    rx = X - d * 330 * s
    lf, rf = floor(lx), floor(rx)
    gy_floor = floor(X)
    hip_lift = 30 * s
    eye_y = gy_floor - (360 + 108) * s - hip_lift
    gripL = (X - d * 125 * s, eye_y + 215 * s)
    gripR = (X + d * 150 * s, eye_y + 160 * s)
    gk = dict(gary_kw or {})
    feet = [(X - d * 95 * s + 10 * s * math.sin(walk), gy_floor + 8 * s), (X - d * 30 * s - 10 * s * math.sin(walk + 1), gy_floor + 6 * s)]
    rim = hood_rim or (light.get("rgb", P_["yellow"]) if light else P_["orange"])
    robe = mix(HOOD, (8, 2, 18), sil)
    hood_kw = dict(glaze=None if sil > 0.5 else (P_["hotpink"], 70), rim=rim, rim_side=d, robe=robe, hand_rgb=mix((150, 120, 190), (30, 14, 50), sil))
    hooded(cv, rx, rf, 1.55 * s, T, seed=seed + 1, face=d, walk=walk + 1.3, lean=d * 10, hands=[dict(world=gripL, pose="hold", ang=90 - d * 80, side=d, bend=-d)],
           **hood_kw)
    L_ = dict(light) if light else None
    g = gary_x(cv, X, gy_floor - hip_lift + 108 * s, s, T, seed=seed + 50 if seed != 6900 else 4400, stand=1.0, lean=-d * 22 + 4 * math.sin(walk * 0.5), feet=feet,
               arms=dict(L=dict(world=gripL if d > 0 else gripR, pose="open", behind=d > 0), R=dict(world=gripR if d > 0 else gripL, pose="open", behind=d < 0)),
               light=L_, bleach=bleach, yaw=gk.pop("yaw", d * 35), hyaw=gk.pop("hyaw", -d * 40 * look_back), **gk)
    if sil > 0:
        rr = g["r"]
        ex, ey = g["eye"]
        p = skia.Paint(AntiAlias=True, Color=core.C((20, 6, 34), int(200 * sil)))
        cv.drawPath(poly_path(cr_closed(ell(ex, ey, rr * 1.02, rr * 1.02, n=14), 4)), p)
        cv.drawPath(poly_path(cr_closed([(X - 130 * s, gy_floor - hip_lift), (X - 112 * s, ey + 170 * s), (X - 55 * s, ey + 112 * s), (X + 55 * s, ey + 112 * s),
                                         (X + 112 * s, ey + 170 * s), (X + 130 * s, gy_floor - hip_lift)], 4)), p)
        brush(cv, cr_closed(ell(ex, ey, rr, rr, n=14), 4)[18:44], 5.0, rim, taper=(0.3, 0.3), seed=seed + 9, a=int(230 * sil))
    hooded(cv, lx, lf, 1.55 * s, T, seed=seed + 2, face=d, walk=walk, lean=d * 16, hands=[dict(world=gripR, pose="hold", ang=90 + d * 110, side=-d, bend=d)],
           **hood_kw)
    return g, feet


def _slope_world(cv, T, C, lk, seed=7000, x_rng=(-1200, 4200)):
    """The long steep rocky path out of the cave (camera-aware). lk 0..1 = how much daylight reaches this far."""
    dark = (30, 12, 58)
    hot = mix(P_["magenta"], P_["orange"], lk)
    with C.layer(0.35):
        w.field(cv, mix(dark, (90, 30, 110), lk))
        g = skia.Paint(AntiAlias=True)
        g.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 1400), skia.Point(2600, -1600)],
                                                   [core.C(mix(dark, P_["violet"], 0.3)), core.C(mix(P_["violet"], hot, 0.5)), core.C(mix(hot, P_["yellow"], 0.6 * lk))],
                                                   [0.0, 0.6, 1.0]))
        cv.drawRect(R(-3000, -3000, 5000, 3000), g)
        for k in range(-8, 14):                                          # strata bands parallel to the slope
            off = k * 150
            xs = np.linspace(-2500, 4500, 18)
            ys = 600 + off - SLOPE * 0.6 * xs + 30 * np.sin(xs * 0.004 + k)
            col = [mix(CV_ROCK, hot, 0.15 + 0.3 * lk), mix(CV_ROCK2, hot, 0.25 + 0.3 * lk), mix(P_["violet"], hot, 0.2 + 0.4 * lk)][k % 3]
            pts = list(zip(xs, ys)) + list(zip(xs[::-1], ys[::-1] + 120))
            cv.drawPath(poly_path(pts), paint(col, 120))
            brush(cv, np.stack([xs, ys], 1), 3.0, mix(INK, hot, 0.3), taper=(0.02, 0.02), seed=seed + k, a=130)
        for k in range(12):
            cxp = -400 + k * 430 + 260 * float(hsh(seed + k * 7.7))
            crystal(cv, cxp, 520 - SLOPE * 0.6 * cxp + 220 * (float(hsh(seed + k * 3.3)) - 0.5), 0.8 + 0.7 * float(hsh(seed + k)), T, seed=seed + 40 + k)
    with C.layer(0.6):
        for k in range(18):                                              # hanging rocks + stalactites far above the path
            hx = -800 + k * 300 + 200 * float(hsh(seed + k * 5.1))
            hy = 120 - SLOPE * 0.75 * hx + 160 * (float(hsh(seed + k * 2.9)) - 0.5)
            sl = 80 + 220 * float(hsh(seed + k))
            blob(cv, [(hx - 50, hy - 300), (hx + 50, hy - 300), (hx + 14, hy + sl), (hx - 6, hy + sl + 10)], mix(CV_ROCK2, hot, 0.25 * lk), w=4,
                 seed=seed + 60 + k, boil=0.8, n=3, shade=lambda c, hx=hx, hy=hy: c.drawPath(poly_path([(hx + 10, hy - 300), (hx + 50, hy - 300), (hx + 14, hy + 200)]),
                                                                                          paint(mix(CV_ROCK2, INK, 0.3))))
    with C.layer(1.0):
        x0, x1 = x_rng
        xs = np.linspace(x0, x1, 44)
        top = [(x, _py(x)) for x in xs]
        cliff = top + [(x1, _py(x0) + 260), (x0, _py(x0) + 260)]
        rock_mass(cv, cliff, seed=seed + 80, rgb=mix(CV_ROCK, hot, 0.2 * lk), rim=None, ink=5)
        cv.drawPath(poly_path(top + [(x, _py(x) + 34) for x in xs[::-1]]), paint(mix(CV_ROCK2, P_["orange"], 0.35 + 0.3 * lk)))
        brush(cv, np.array(top), 6.0, INK, taper=(0.01, 0.01), seed=seed + 81)
        for k in range(1, 7):                                            # strata in the cliff face, parallel to the path
            sub = [(x, _py(x) + 70 * k + 26 * math.sin(x * 0.006 + k)) for x in xs[::3]]
            line(cv, sub, 4.0, mix(CV_ROCK, INK, 0.4), seed=seed + 90 + k, boil=0.8, n=4, taper=(0.02, 0.02), a=170)
        k0 = int(x0 // 260)
        for k in range(k0, k0 + int((x1 - x0) / 260) + 2):              # glowing pockets + crystal veins in the cliff
            vx = k * 260 + 120 * float(hsh(seed + k * 1.9))
            vy = _py(vx) + 160 + 260 * float(hsh(seed + k * 4.3))
            if k % 3 == 0:
                crystal(cv, vx, vy, 0.9 + 0.5 * float(hsh(seed + k)), T, seed=seed + 400 + k % 50)
            elif k % 3 == 1:
                glare(cv, vx, vy, 90, a=110, rgb=[P_["magenta"], P_["teal"], P_["acid"]][k % 3], blend=False)
                dots(cv, [(vx + 18 * math.cos(j * 2.1), vy + 14 * math.sin(j * 2.1)) for j in range(3)], 6, [P_["hotpink"], P_["mint"], P_["acid"]][k % 3])
        k0 = int(x0 // 120)
        for k in range(k0, k0 + int((x1 - x0) / 120)):                   # steps / stones on the path (world-anchored)
            sx = k * 120 + 50 * float(hsh(seed + k * 1.3))
            blob(cv, ell(sx, _py(sx) + 18, 30 + 10 * float(hsh(seed + k)), 10, n=8, rot=-30), mix(CV_ROCK2, P_["lilac"], 0.3 + 0.2 * lk), w=3,
                 seed=seed + 100 + k, boil=0.5)
        k0 = int(x0 // 420)
        for k in range(k0, k0 + int((x1 - x0) / 420) + 1):               # boulders + mushrooms on the path edge (world-anchored)
            bx = k * 420 + 160 * float(hsh(seed + k * 2.2))
            if k % 2 == 0:
                rock_mass(cv, [(bx - 90, _py(bx - 90) + 10), (bx - 60, _py(bx) - 90), (bx + 30, _py(bx) - 120), (bx + 100, _py(bx + 100) - 40),
                               (bx + 100, _py(bx + 100) + 20)], seed=seed + 200 + k, rgb=mix(CV_ROCK2, hot, 0.2), rim=P_["orange"], ink=4.5)
            else:
                glow_mushroom(cv, bx, _py(bx) + 6, 1.1, T, seed=seed + 300 + k)


def _drag_shot(cv, t, T):
    """1.95 .. 10.29: the long haul up the slope; the cave mouth's light grows ahead."""
    lt = t - 1.95
    X = 300 + 300 * lt
    lk = _cl(lt / 8.34) ** 1.3
    s = 0.62
    gx, gyf = X, _py(X)
    C = sets.Cam(cv, dict(x=gx - 960 + 140, y=gyf - 540 - 200, z=1.12))
    _slope_world(cv, T, C, lk, seed=7000, x_rng=(X - 950, X + 1200))
    with C.layer(0.55):                                                   # the mouth far up ahead (grows brighter)
        mx_, my_ = 0.55 * (gx - 960 + 140) + 1720, 0.55 * (gyf - 540 - 200) + 80
        glare(cv, mx_, my_, 700 + 500 * lk, a=int(120 + 135 * lk), rgb=P_["white"], blend=False)
        if lk > 0.2:
            rays_fast(cv, mx_, my_, 2400, T, n=14, a=int(90 * lk), rgb=P_["yellow"], ang0=150, span=60)
    with C.layer(1.0):
        light = dict(dir=(1, -0.8), a=0.4 + 0.6 * lk, rgb=mix(P_["orange"], P_["yellow"], lk))
        g, feet = _drag_trio(cv, T, X, s, seed=6900, look_back=1.0, light=light,
                             gary_kw=dict(mouth="wobbly" if lt < 4 else "pout", lid=0.7, tilt=20, look=(-0.7, 0.2), sweat=0.6))
        for j, (fx, fy) in enumerate(feet):                               # scraping heels: dust puffs + scrape lines + pebbles
            for k in range(3):
                u = ((T * 2.6 + k / 3.0 + j * 0.17) % 1.0)
                dust_puff(cv, fx - 40 - u * 120, fy + 6 + u * 70, 0.9, u, seed=6950 + j * 10 + k, rgb=mix((210, 170, 220), P_["yellow"], lk * 0.5))
            line(cv, [(fx - 30, fy + 4), (fx - 150, fy + 4 + 150 * SLOPE)], 4, INK, seed=6960 + j, boil=1.0, n=2, taper=(0.1, 0.9), a=200)
        for k in range(4):
            u = (T * 1.3 + k * 0.25) % 1.0
            px = X - 120 - u * 500
            dots(cv, [(px, _py(px) - 10 + 20 * abs(math.sin(u * 12)))], 7, mix(CV_ROCK2, P_["lilac"], 0.4), a=int(255 * (1 - u)))
    with C.layer(1.3):                                                    # foreground rocks sliding past
        for k in range(3):
            fx = (k * 1300 + 600) - ((X * 0.3) % 1300)
            fxw = fx + (gx - 960 + 140)
            rock_mass(cv, [(fxw - 260, 1500), (fxw - 200, 1080 + 0.0), (fxw - 40, 990), (fxw + 160, 1040), (fxw + 260, 1500)], seed=7100 + k,
                      rgb=(26, 10, 46), rim=mix(P_["orange"], P_["yellow"], lk), rim_side=1, ink=6)
    motes(cv, T, (0, 0, 1920, 1080), n=30, seed=7110, a=int(120 + 120 * lk), rise=40)
    hx, hy = C.to_screen(feet[0][0], feet[0][1], 1.0)
    sfx(cv, "SKRRRTCH!", hx - 120, hy + 120, 66, t, 3.05, seed=7120, fills=[P_["lilac"], P_["cream"]], rot_deg=-28, hold=1.3)
    sfx(cv, "SKRRTCH!", hx - 160, hy + 130, 56, t, 6.2, seed=7121, fills=[P_["peach"], P_["cream"]], rot_deg=-30, hold=1.0)
    if t > 8.6:                                                           # 'into the sunlight': the light sweeps down the path
        k = _seg(t, 8.6, 10.2)
        light_rays(cv, 1900, -200, 2600, T, n=16, a=int(120 * k), rgb=P_["yellow"], rot_deg=95, width=0.45, spin=3)
        glare(cv, 1700, 100, 1200, a=int(160 * k), rgb=P_["yellow"])
    vignette(cv, a=int(170 - 90 * lk))


def _grab_shot(cv, t, T):
    """0 .. 1.95: 'But they don't put him back.' -- hands grab him and he's hauled off his feet; the shadow plush falls."""
    C = sets.Cam(cv, dict(x=60, y=-10, z=1.32 - 0.05 * t))
    bx, by = 1000, 470
    with C.layer(0.6):
        w.field(cv, CV_ROCK_DK)
        wall_surface(cv, [(-300, -100), (2220, -100), (2220, 860), (-300, 860)], T, seed=5770, cx=1000, cy=480)
        shadow_shape(cv, "horse", 300, 360, 1.7, T, seed=5771)
        shadow_shape(cv, "tree", 1700, 330, 1.6, T, seed=5772)
        shadow_shape(cv, "bunny", bx, by, 2.0, T, rgb=mix(CV_WALL, P_["white"], 0.45), a=150, seed=5774, wobble=0.5)
        rock_mass(cv, [(-500, -400), (2500, -400), (2500, 20), (1700, 70), (1000, 40), (400, 80), (-500, 50)], seed=5775, rgb=CV_ROCK, rim=P_["orange"])
        stalactites(cv, 60, -200, 2300, seed=5776, n=12, sc=1.0, T=T)
        floor_band(cv, 800, T, seed=5777, rgb=CV_ROCK2, rim=P_["orange"], pebbles=10, mush=((120, 880, 0.9), (1800, 870, 0.9)))
    _fire_glow(cv, T, a=0.8)
    grab = _seg(t, 0.45, 0.75)
    lift = _seg(t, 0.85, 1.35)
    s = 0.74
    gx, gfy0 = 1010, 880
    with C.layer(1.0):
        drop = _seg(t, 0.75, 1.3)                                        # the plush slips out of his arms and flops on the floor
        if drop >= 1:
            cv.save(); cv.translate(gx + 190, gfy0 - 18); cv.scale(1.0, 0.35)
            shadow_shape(cv, "bunny", 0, 0, 1.3, T, rgb=CV_SHADOW, a=240, seed=5800)
            cv.restore()
        gfy = gfy0 - 120 * lift
        ey = gfy - (360 + 108) * s
        gl = (gx - 230 * s - 40 * (1 - grab), ey + 190 * s)
        gr = (gx + 230 * s + 40 * (1 - grab), ey + 170 * s)
        kick = math.sin(t * 22) * lift
        feet = [(gx - 40 * s + 30 * s * kick, gfy + 10 * s - 30 * s * abs(kick)), (gx + 40 * s - 30 * s * kick, gfy + 10 * s - 30 * s * abs(-kick))] if lift > 0 else None
        if grab > 0:
            for side, (hx, hy) in ((-1, gl), (1, gr)):
                hooded(cv, gx + side * 470, 1090, 1.9, T, seed=6800 + side, face=-side, hands=[dict(world=(hx, hy), pose="hold", ang=0 if side < 0 else 180, side=-side,
                                                                                                    bend=side)], glaze=(P_["hotpink"], 70), rim=P_["orange"], rim_side=side)
        held = grab <= 0.5
        arms = dict(L=dict(world=gl, pose="spread"), R=dict(world=gr, pose="spread")) if not held else dict(L=dict(hand=(95, 300, 110), pose="flat", ang=-30),
                                                                                                        R=dict(hand=(-100, 345, 120), pose="flat", ang=210))
        gkw = dict(seed=4400, stand=1.0, feet=feet, lid=lerp(0.6, -0.2, grab), pupil=lerp(0.42, 0.2, grab), shock=grab, mouth="o" if grab > 0.3 else "pout",
                   mo=0.6, light=dict(dir=(0, 1), a=0.6, rgb=P_["orange"]), sweat=grab, look=(0.4 * drop, 0.5 * drop))
        rock_ = math.sin(T * 4.0)
        ey_w = gfy - (360 + 108) * s
        if held:                                                       # still cuddling the shadow (continuity from T027)
            gary_x(cv, gx, gfy, s, T, arms=arms, arms_off=True, **gkw)
            plush_shadow(cv, gx + 70 * s + 14 * rock_, ey_w + 345 * s, 1.75 * s, T, ang=16 + 8 * rock_, flop=0.6)
            gary_x(cv, gx, gfy, s, T, arms=arms, arms_only=True, **gkw)
        else:
            gary_x(cv, gx, gfy, s, T, arms=arms, **gkw)
            if drop < 1:
                plush_shadow(cv, gx + 70 * s + 140 * drop, ey_w + 345 * s + 230 * drop * drop, 1.75 * s, T, ang=16 + 70 * drop, flop=1.0)
        if grab > 0:
            sfx(cv, "GRAB!", gx, ey - 230, 100, t, 0.5, seed=6810, fills=[P_["yellow"], P_["acid"]], rot_deg=-6, hold=0.6)
        if 0.05 < lift < 0.95:
            for side in (-1, 1):
                motion_lines(cv, gx + side * 120, gfy - 20, -90, n=3, L=110, gap=34, seed=6820 + side, wdt=5)
    vignette(cv, a=130)


def T029_dragged(cv, t, T, A):
    if t < 1.95:
        _grab_shot(cv, t, T)
    elif t < 10.29:
        _drag_shot(cv, t, T)
    elif t < 19.70:
        _ascent(cv, t, T)
    else:
        _too_much(cv, t, T)


def _ledge(cv, p0, p1, thick, seed, top_rgb, body_rgb, rim=None):
    """A rocky ramp/ledge from p0 to p1 (top surface) with a thick underside."""
    (x0, y0), (x1, y1) = p0, p1
    pts = [(x0, y0), ((x0 + x1) / 2, (y0 + y1) / 2 - 6), (x1, y1), (x1 + 20, y1 + thick * 0.6), ((x0 + x1) / 2, (y0 + y1) / 2 + thick), (x0 - 20, y0 + thick * 0.7)]
    blob(cv, pts, body_rgb, w=5, seed=seed, boil=1.0, n=4,
         shade=lambda c: (c.drawPath(poly_path([(x0 - 30, y0 - 10), (x1 + 30, y1 - 10), (x1 + 30, y1 + 22), (x0 - 30, y0 + 22)]), paint(top_rgb)),
                          c.drawPath(poly_path([(x0, y0 + thick * 0.5), (x1, y1 + thick * 0.4), (x1, y1 + thick), (x0, y0 + thick)]), paint(mix(body_rgb, INK, 0.3), 160))))
    if rim:
        brush(cv, np.array([(x0, y0 - 2), (x1, y1 - 2)]), 4.0, rim, taper=(0.1, 0.1), seed=seed + 1, a=200)


def _asc_switchback(cv, t, T, lt):
    """Wide: a towering cavern, the path zig-zagging up its wall; three tiny climbers; light pouring down from above."""
    C = sets.Cam(cv, dict(x=0, y=lerp(260, -60, ease(lt / 1.86)), z=1.0))
    with C.layer(0.5):
        w.field(cv, (34, 12, 70))
        g = skia.Paint(AntiAlias=True)
        g.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 1500), skia.Point(0, -500)], [core.C((30, 10, 60)), core.C(P_["violet"]), core.C(P_["hotpink"])]))
        cv.drawRect(R(-400, -800, 2400, 1900), g)
        glare(cv, 1500, -350, 900, a=230, rgb=P_["white"], blend=False)
        rays_fast(cv, 1500, -350, 2200, T, n=12, a=70, rgb=P_["yellow"], ang0=110, span=70)
        for k in range(9):
            crystal(cv, 120 + k * 230 + 60 * math.sin(k * 2.1), 1300 - k * 170 + 80 * math.sin(k), 1.2, T, seed=7300 + k)
    with C.layer(1.0):
        rock_mass(cv, [(-400, -700), (300, -700), (200, 300), (260, 1400), (-400, 1900)], seed=7310, rgb=CV_ROCK, rim=P_["magenta"], rim_side=1)
        rock_mass(cv, [(2400, -700), (1650, -700), (1760, 300), (1700, 1400), (2400, 1900)], seed=7311, rgb=CV_ROCK, rim=P_["orange"], rim_side=-1)
        ramps = [((260, 1350), (1700, 1100)), ((1700, 1100), (260, 820)), ((260, 820), (1700, 540)), ((1700, 540), (260, 260)), ((260, 260), (1700, -40)),
                 ((1700, -40), (300, -330))]
        for k, (p0, p1) in enumerate(ramps):
            _ledge(cv, p0, p1, 70, 7320 + k, mix(CV_ROCK2, P_["orange"], 0.3 + 0.1 * k), mix(CV_ROCK2, P_["violet"], 0.3), rim=P_["yellow"] if k > 2 else None)
        for k in range(7):
            glow_mushroom(cv, 300 + k * 210, 1340 - k * 35 - (k % 2) * 290, 0.9, T, seed=7330 + k)
        (p0, p1) = ramps[2]
        u = 0.25 + 0.35 * (lt / 1.86)
        X = lerp(p0[0], p1[0], u)
        fl = lambda xx: p0[1] + (p1[1] - p0[1]) * (xx - p0[0]) / (p1[0] - p0[0]) - 4
        _drag_trio(cv, T, X, 0.26, seed=7340, d=-1, look_back=0.5, light=dict(dir=(1, -1), a=0.8, rgb=P_["yellow"]), floor=fl,
                   gary_kw=dict(mouth="o", mo=0.4, lid=0.4, look=(0.3, -0.6)))
    motes(cv, T, (0, 0, 1920, 1080), n=40, seed=7350, a=200, rise=50)
    vignette(cv, a=150)


def _asc_crystals(cv, t, T, lt):
    """Medium: past giant glowing crystals, the walls swirling with colour; Gary goggles at the light show."""
    C = sets.Cam(cv, dict(x=lerp(-200, 260, lt / 1.85), y=0, z=1.05))
    with C.layer(0.3):
        w.field(cv, P_["night"])
        for k, col in enumerate((P_["violet"], P_["magenta"], P_["teal"], P_["blue"], P_["hotpink"], P_["acid"])):
            w.wavy_band(cv, -60 + k * 170, 1400, mix(col, P_["night"], 0.25), amp=60, freq=1.1 + 0.3 * k, seed=7400 + k + int(T * 2) % 2 * 0)
        w.stars(cv, 7410, (-300, -100, 2300, 900), n=120, big=8)
        rock_mass(cv, [(-600, -600), (2600, -600), (2600, 40), (1800, 120), (1100, 60), (400, 140), (-600, 90)], seed=7415, rgb=CV_ROCK, rim=P_["teal"])
        stalactites(cv, 110, -400, 2500, seed=7416, n=14, sc=1.2, rgb=mix(CV_ROCK2, P_["magenta"], 0.3), T=T)
    with C.layer(0.6):
        for k in range(6):
            crystal(cv, -200 + k * 480, 1040, 3.2 + 0.6 * math.sin(k), T, seed=7420 + k,
                    rgb=[P_["teal"], P_["magenta"], P_["acid"], P_["lilac"], P_["hotpink"], P_["teal"]][k])
    with C.layer(1.0):
        fl = lambda xx: 900 - 0.18 * (xx - 700)
        xs = np.linspace(-800, 2900, 30)
        rock_mass(cv, [(x, fl(x)) for x in xs] + [(2900, 1600), (-800, 1600)], seed=7430, rgb=mix(CV_ROCK2, P_["magenta"], 0.2), rim=None, ink=5)
        cv.drawPath(poly_path([(x, fl(x)) for x in xs] + [(x, fl(x) + 26) for x in xs[::-1]]), paint(mix(CV_ROCK2, P_["teal"], 0.45)))
        X = 520 + 330 * lt
        _drag_trio(cv, T, X, 0.55, seed=7440, light=dict(dir=(0.4, -1), a=0.9, rgb=P_["teal"]), floor=fl, look_back=-0.4,
                   gary_kw=dict(mouth="o", mo=0.6, lid=-0.1, pupil=0.75, look=(0.2, -0.7), shock=0.6), hood_rim=P_["teal"])
    with C.layer(1.35):
        for k in range(3):
            crystal(cv, 200 + k * 900, 1150, 2.6, T, seed=7450 + k, rgb=[P_["magenta"], P_["acid"], P_["teal"]][k])
    for k in range(10):
        sparkle(cv, (k * 211 + T * 40) % 1920, 150 + 80 * math.sin(k * 1.9 + T), 10 + 8 * (k % 3), [P_["white"], P_["mint"], P_["yellow"]][k % 3], seed=7460 + k)
    vignette(cv, a=140)


def _asc_steps(cv, t, T, lt):
    """Steep carved steps; the rock now glows orange / pink / yellow; shafts of light; climbers half silhouetted."""
    C = sets.Cam(cv, dict(x=lerp(-120, 260, lt / 1.85), y=lerp(160, -120, lt / 1.85), z=1.08))
    with C.layer(0.35):
        w.field(cv, P_["orange"])
        for k, col in enumerate((P_["red"], P_["orange"], P_["hotpink"], P_["yellow"], P_["gold"], P_["peach"], P_["yellow"])):
            w.wavy_band(cv, -150 + k * 160, 1600, col, amp=50, freq=1.3 + 0.2 * k, seed=7500 + k)
        rock_mass(cv, [(-600, -700), (2600, -700), (2600, -60), (1900, -10), (1300, -80), (600, 30), (-600, -20)], seed=7505, rgb=mix(CV_ROCK2, P_["red"], 0.3),
                  rim=P_["yellow"])
        stalactites(cv, -40, -400, 2500, seed=7506, n=13, sc=1.1, rgb=mix(CV_ROCK2, P_["hotpink"], 0.4), T=T)
        light_rays(cv, 1700, -300, 2400, T, n=14, a=110, rgb=P_["white"], rot_deg=100, width=0.45, spin=2)
    with C.layer(1.0):
        fl = lambda xx: 1000 - 0.7 * (xx - 500)
        steps = []
        for k in range(-6, 22):
            x0 = 500 + k * 90
            steps += [(x0, fl(x0)), (x0, fl(x0 + 90))]
        steps = steps + [(steps[-1][0] + 400, steps[-1][1]), (steps[-1][0] + 400, 2400), (steps[0][0] - 400, 2400)]
        blob(cv, steps, mix(P_["maroon"], P_["magenta"], 0.3), w=5, seed=7510, boil=0.8, n=2,
             shade=lambda c: ([c.drawLine(500 + k * 90, fl(500 + k * 90 + 90), 500 + k * 90 + 90, fl(500 + k * 90 + 90), paint(P_["yellow"], stroke=6)) for k in range(-6, 22)],
                              stipple(c, mix(P_["maroon"], INK, 0.3), (-200, -600, 2600, 2400), spacing=16, r=2.2, seed=7511,
                                      fn=lambda X, Y: np.clip((Y - fl(X)) / 500.0, 0, 1) * 0.9)))
        for k in range(6):
            glow_mushroom(cv, 300 + k * 330, fl(300 + k * 330) + 40, 1.2, T, seed=7520 + k)
        X = 640 + 300 * lt
        _drag_trio(cv, T, X, 0.5, seed=7530, light=dict(dir=(1, -1), a=1.0, rgb=P_["yellow"]), floor=lambda xx: fl(xx) + 6, look_back=0.2, sil=0.45,
                   gary_kw=dict(mouth="o", mo=0.5, lid=0.5, squint=0.4, look=(0.5, -0.5)))
    glare(cv, 1800, -100, 1100, a=200, rgb=P_["white"])
    motes(cv, T, (0, 0, 1920, 1080), n=40, seed=7540, a=220, rise=60, rgb=[P_["white"], P_["yellow"], P_["cream"]])
    vignette(cv, a=110, rgb=(90, 20, 40))


def _cave_mouth(cv, cx, cy, rx, ry, T, k=1.0, seed=7600):
    """The jagged opening onto daylight, blazing white-yellow, with stalactite teeth silhouetted against it and sun rays."""
    pts = []
    n = 26
    for j in range(n):
        a = j / n * 2 * math.pi
        rr = 1.0 + 0.16 * (float(hsh(seed + j * 1.7)) - 0.5) + 0.08 * math.sin(a * 3 + seed)
        if math.sin(a) < -0.2:                                          # the roof: deeper notches
            rr *= 0.86 + 0.22 * float(hsh(seed + j * 3.1))
        pts.append((cx + rx * rr * math.cos(a), cy + ry * rr * math.sin(a)))
    P = rect_pts(pts, 2)
    g = skia.Paint(AntiAlias=True)
    g.setShader(skia.GradientShader.MakeRadial(skia.Point(cx, cy), max(rx, ry) * 1.1, [core.C(P_["white"]), core.C(mix(P_["yellow"], P_["white"], 0.5)),
                                                                                    core.C(P_["yellow"])], [0.0, 0.6, 1.0]))
    path = poly_path(cr_closed(jit(P, 1.2, seed), 2))
    cv.drawPath(path, g)
    cv.save(); cv.clipPath(path, doAntiAlias=True)
    for j in range(5):                                                   # bleached hint of the world outside
        hx = cx - rx * 0.9 + j * rx * 0.45
        blob(cv, ell(hx, cy + ry * 0.62, rx * 0.24, ry * 0.13, n=8), mix(P_["acid"], P_["white"], 0.75), w=0, seed=seed + 10 + j, boil=0.6, misreg=(0, 0))
    for j in range(7):                                                   # stalactite teeth hanging into the light
        tx = cx - rx * 0.8 + j * rx * 0.27 + 20 * math.sin(j * 2.3 + seed)
        tl = ry * (0.25 + 0.3 * float(hsh(seed + 30 + j)))
        ty = cy - ry * 1.2
        blob(cv, [(tx - 26, ty), (tx + 26, ty), (tx + 4, ty + ry * 0.35 + tl), (tx - 3, ty + ry * 0.35 + tl + 6)], mix(CV_ROCK, P_["magenta"], 0.35), w=4,
             seed=seed + 40 + j, boil=0.8, n=3)
    cv.restore()
    brush(cv, cr_closed(jit(P, 1.2, seed), 2), 7.0, closed=True, seed=seed + 1)
    rays_fast(cv, cx, cy, 2600, T, n=16, a=int(110 * k), rgb=P_["yellow"], ang0=90, span=150)
    rays_fast(cv, cx, cy, 2200, T * 1.3, n=10, a=int(70 * k), rgb=P_["white"], ang0=90, span=120)


def _backlit_floor(cv, T, xs, y_top, seed=7800, rgb=None, light_rgb=None, n_peb=14):
    """Floor dressing for back-lit shots: long shadows from the figures at `xs` fanning toward camera, light streaks, pebbles."""
    rgb = rgb or (40, 10, 50)
    light_rgb = light_rgb or P_["yellow"]
    for k in range(7):                                                   # light streaks between the shadows
        x0 = 300 + k * 230
        cv.drawPath(poly_path([(x0 - 20, y_top), (x0 + 20, y_top), (x0 * 2.2 - 1050 + 160, 1500), (x0 * 2.2 - 1050 - 60, 1500)]), paint(light_rgb, 50))
    for x in xs:
        p = skia.Paint(AntiAlias=True)
        p.setShader(skia.GradientShader.MakeLinear([skia.Point(x, y_top), skia.Point(x, 1300)], [core.C(rgb, 220), core.C(rgb, 60)]))
        x2 = 960 + (x - 960) * 2.6
        cv.drawPath(poly_path([(x - 28, y_top), (x + 28, y_top), (x2 + 140, 1400), (x2 - 140, 1400)]), p)
    for k in range(n_peb):
        px = 80 + k * 1800 / n_peb + 60 * float(hsh(seed + k))
        py = y_top + 40 + 300 * float(hsh(seed + k * 3.3)) ** 1.5
        blob(cv, ell(px, py, 14 + 16 * (py - y_top) / 300, 7 + 6 * (py - y_top) / 300, n=8), mix(CV_ROCK2, P_["orange"], 0.4), w=3, seed=seed + 20 + k,
             boil=0.5, shade=lambda c, px=px, py=py: c.drawRect(R(px - 40, py - 30, px + 40, py - 4), paint(light_rgb, 120)))
    for k, mx in enumerate((150, 1780)):
        glow_mushroom(cv, mx, y_top + 160, 1.3, T, seed=seed + 50 + k)


def _asc_rays(cv, t, T, lt):
    """Looking up the last slope at the huge mouth: sun rays blast in; the climbers are silhouettes against the glare."""
    z = lerp(1.0, 1.22, ease(lt / 1.95))
    C = sets.Cam(cv, dict(x=0, y=-40, z=z))
    with C.layer(0.6):
        w.field(cv, (60, 20, 90))
        rock_mass(cv, [(-80, -80), (2000, -80), (2000, 1160), (-80, 1160)], seed=7610, rgb=mix(CV_ROCK, P_["magenta"], 0.35), ink=4)
        _cave_mouth(cv, 980, 300, 470, 300, T, seed=7611)
        rock_mass(cv, [(-500, 900), (500, 700), (900, 600), (1100, 600), (1500, 720), (2400, 900), (2400, 1500), (-500, 1500)], seed=7612,
                  rgb=mix(CV_ROCK2, P_["orange"], 0.4), rim=P_["yellow"], ink=5)
        stalactites(cv, -10, -200, 2200, seed=7613, n=11, sc=1.3, rgb=mix(CV_ROCK2, P_["hotpink"], 0.4), T=T)
    with C.layer(1.0):
        fl = lambda xx: 1050 - 0.42 * (xx - 300)
        X = 560 + 120 * lt
        _drag_trio(cv, T, X, 0.42, seed=7620, light=dict(dir=(0.5, -1), a=1.0, rgb=P_["white"]), floor=fl, look_back=-0.3, sil=0.85, hood_rim=P_["yellow"],
                   gary_kw=dict(mouth="o", mo=0.4, lid=0.6, squint=0.6))
    motes(cv, T, (200, 0, 1700, 1080), n=60, seed=7630, a=230, rise=30, rgb=[P_["white"], P_["yellow"], P_["cream"]])
    glare(cv, 980 + 0 * z, 300, 900, a=150, rgb=P_["white"])
    vignette(cv, a=130, rgb=(60, 10, 40))


def _asc_whiteout(cv, t, T, lt):
    """At the threshold: the opening swallows the frame; a WHITE-OUT flash."""
    z = lerp(1.25, 2.6, ease(lt / 1.9) ** 1.6)
    C = sets.Cam(cv, dict(x=0, y=-60 * ease(lt / 1.9), z=z))
    with C.layer(1.0):
        w.field(cv, (60, 20, 90))
        rock_mass(cv, [(-80, -80), (2000, -80), (2000, 1160), (-80, 1160)], seed=7710, rgb=mix(CV_ROCK, P_["magenta"], 0.4), ink=4)
        _cave_mouth(cv, 960, 420, 560, 380, T, seed=7711, k=1.2)
        fl = lambda xx: 740 + 0.02 * (xx - 900)
        X = 840 + 60 * lt
        _drag_trio(cv, T, X, 0.3, seed=7720, light=dict(dir=(0, -1), a=1.0, rgb=P_["white"]), floor=fl, look_back=0.0, sil=1.0, hood_rim=P_["white"],
                   gary_kw=dict(mouth="o", mo=0.5))
        rock_mass(cv, [(-500, 760), (600, 730), (1300, 740), (2400, 760), (2400, 1500), (-500, 1500)], seed=7712, rgb=mix(CV_ROCK2, P_["orange"], 0.5),
                  rim=P_["yellow"], ink=5)
        _backlit_floor(cv, T, [X - 0.3 * 330, X, X + 0.3 * 240], 750, seed=7713)
    fl_k = _seg(t, 18.75, 19.3)
    if fl_k > 0:
        r = 60 + 1500 * fl_k ** 1.5
        glare(cv, 960, 480, r * 1.5, a=255, rgb=P_["white"], blend=False)
        cv.drawCircle(960, 480, r, paint(P_["white"]))
        burst_lines(cv, 960, 480, r * 0.6, r * 1.6, n=28, seed=7730, rgb=P_["yellow"], wdt=14, a=int(200 * (1 - fl_k * 0.5)))
    if t > 19.3:
        wash(cv, P_["white"], 255)
        light_rays(cv, 960, 480, 1600, T, n=24, a=50, rgb=P_["yellow"], spin=20, blend=False)
        for j in range(6):
            sparkle(cv, 960 + 520 * math.cos(j * 1.05 + T), 480 + 300 * math.sin(j * 1.05 + T), 20, P_["yellow"], seed=7740 + j, w=2.0)


def _ascent(cv, t, T):
    if t < 12.15:
        _asc_switchback(cv, t, T, t - 10.29)
    elif t < 14.0:
        _asc_crystals(cv, t, T, t - 12.15)
    elif t < 15.85:
        _asc_steps(cv, t, T, t - 14.0)
    elif t < 17.8:
        _asc_rays(cv, t, T, t - 15.85)
    else:
        _asc_whiteout(cv, t, T, t - 17.8)


def _bleached_world(cv, T, seed=7800):
    """Outside, as a cave-dweller sees it: blown-out white-yellow, a white sun-glare, ghostly pale trees and hills."""
    g = skia.Paint(AntiAlias=True)
    g.setShader(skia.GradientShader.MakeRadial(skia.Point(1500, 120), 2200, [core.C(P_["white"]), core.C(mix(P_["yellow"], P_["white"], 0.7)),
                                                                            core.C(mix(P_["yellow"], P_["white"], 0.45))], [0.0, 0.45, 1.0]))
    cv.drawRect(R(-300, -300, 2300, 1500), g)
    w.sunburst(cv, 1500, 120, 2600, 30, [mix(P_["yellow"], P_["white"], 0.78), mix(P_["yellow"], P_["white"], 0.6)], rot_deg=T * 8, seed=seed)
    pk = mix(INK, P_["yellow"], 0.62)
    for k, (hy, col) in enumerate(((760, mix(P_["acid"], P_["white"], 0.78)), (830, mix(P_["teal"], P_["white"], 0.8)), (900, mix(P_["acid"], P_["white"], 0.7)))):
        xs = np.linspace(-200, 2200, 30)
        ys = hy - 40 * np.sin(xs * 0.003 + k * 1.7)
        cv.drawPath(poly_path(list(zip(xs, ys)) + [(2200, 1500), (-200, 1500)]), paint(col))
        brush(cv, np.stack([xs, ys], 1), 3.5, pk, taper=(0.02, 0.02), seed=seed + k, a=150)
    for k in range(9):                                                   # bleached tiny tree silhouettes
        tx = 80 + k * 225 + 40 * math.sin(k * 2.3)
        ty = 770 - 40 * math.sin(tx * 0.003) + 20 * (k % 3)
        sc = 0.55 + 0.25 * float(hsh(seed + k))
        line(cv, [(tx, ty), (tx + 3, ty - 70 * sc)], 10 * sc + 2, mix(P_["peach"], P_["white"], 0.5), seed=seed + 20 + k, boil=0.5, n=2, taper=(0, 0), a=200)
        blob(cv, ell(tx + 3, ty - 110 * sc, 60 * sc, 52 * sc, n=10), mix(P_["acid"], P_["white"], 0.7), w=3, ink=pk, seed=seed + 30 + k, boil=0.8, a=210)
    light_rays(cv, 1500, 120, 2600, T, n=20, a=120, rgb=P_["white"], spin=9)
    glare(cv, 1500, 120, 1000, a=255, rgb=P_["white"])
    lens_flare(cv, 1500, 120, T, a=0.8, seed=seed + 50)


def _too_much(cv, t, T):
    """'TOO MUCH! TOO MUCH OUTSIDE!' -- Gary in the blown-out daylight: eye clenched, flailing, running on the spot."""
    loud = loud_at("G04", T)
    lt = t - 19.7
    cv.save(); _shake(cv, 8 + 10 * loud, seed=7900, rot_amp=0.8)
    _bleached_world(cv, T, seed=7800)
    C = sets.Cam(cv, dict(x=0, y=0, z=1.0 + 0.06 * lt))
    with C.layer(1.0):
        for side in (-1, 1):                                             # the carriers, bleached to ghosts
            hooded(cv, 960 + side * 560, 1020, 1.25, T, seed=7910 + side, face=-side, robe=mix(P_["lilac"], P_["white"], 0.45), hand_rgb=mix(P_["hotpink"], P_["white"], 0.55),
                   eyes=True, hands=[dict(world=(960 + side * 470, 600), pose="flat", ang=-90, side=-side)])
        fl = math.sin(lt * 15)
        s = 1.05
        gary_x(cv, 960, 1010, s, T, seed=4400, stand=1.0, step=lt * 16, shut=1.0, crinkle=1.0, mouth="scream", loud=loud, sweat=1.0, veins=1.0, bleach=0.3,
               lean=6 * math.sin(lt * 9), light=dict(dir=(1, -1), a=0.8, rgb=P_["white"]),
               arms=dict(L=dict(hand=(-230 - 40 * fl, -160 + 80 * fl), pose="spread"), R=dict(hand=(230 - 40 * fl, -170 - 80 * fl), pose="spread")))
        ey = 1010 - 468 * s
        burst_lines(cv, 960, ey, 270, 420, n=14, seed=7920, rgb=INK, wdt=9, a=230)
    cv.restore()
    sfx(cv, "TOO MUCH!", 560, 200, 140, t, 19.8, seed=7930, fills=[P_["orange"], P_["red"], P_["magenta"]], font="shrik", rot_deg=-8, dur=0.2, hold=9)
    sfx(cv, "OUTSIDE!!", 1540, 480, 120, t, 21.15, seed=7931, fills=[P_["magenta"], P_["violet"], P_["blue"]], font="shrik", rot_deg=7, dur=0.2, hold=9)
