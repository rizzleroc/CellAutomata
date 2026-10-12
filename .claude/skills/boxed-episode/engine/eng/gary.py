"""Gary, full body: the standard Gary for any shot that needs more than the seated audience pose.

`draw_gary(cv, x, fy, s, T, **pose)` draws the classic design of `shots_ep2.eyeball_creature` (same proportions,
colours, red veins, teal iris, violet lid, cream sweater with orange stripes and the red "G", white four-finger
hands; the default seed 4400 matches the audience Gary) and adds everything Ep4's shot authors had to build for
themselves (promoted from the Ep4 escape module, with the other authors' extras folded in):

- legs: cream rubber-hose legs and red sneakers (the series standard), sitting (stand=0) .. standing (stand=1),
  walking (step = phase in radians), dangling or dragged feet (feet=[(X, Y), (X, Y)])
- turning: yaw 0 front, +90 facing screen-right, -90 screen-left, 180 back view; hyaw turns only the eye
- posable rubber-hose arms with natural-elbow IK; hands in s-units relative to the eye centre (or world coords)
- expressions: look, lid (breathing by default), squint, shut, crinkle, pupil size or 'pin' / 'spiral' / 'x' /
  'heart' / 'dollar', shock lines, mouths ('auto' talk, smile, frown, flat, wobbly, grin, scream, pout, o),
  gushing tears, sweat, veins, tiny sunglasses (shades=0 in place .. 1 slid down so he peeks over them)
- cel lighting (light=dict(dir, a, rgb)), bleach (washed out by glare), an optional iron collar (Ep4 prisoners)

Placement: (x, fy) is the floor point under him. Seated, his eye centre sits 360*s above fy (standing raises it
by 108*s). To place him by the eye like `eyeball_creature(cv, x, y, ...)`, pass fy = y + 360 * s.
Lip sync: pass loud (0..1); an episode base module's `gary_full()` feeds `spk_loud("AUD", T)`.
Returns anchors: dict(eye=(X, Y), r=eye radius, iris=(X, Y), hip=(X, Y), shL=(X, Y), shR=(X, Y)).
"""
import math

import numpy as np
import skia

from . import core
from .core import (PAL, INK, paint, poly_path, cr_closed, cr_open, ell, blob, line, brush, dots, hsh, mix, jit, rot,
                   rect_pts, tube, stipple)
from .letters import paint_text
from .zee import _hand

P_ = PAL
TEAR = (160, 228, 255)
IRON = (140, 140, 172)
IRON_DK = (86, 84, 120)
BRASS = (255, 196, 40)
BRASS_DK = (214, 120, 20)
SHADES = (20, 10, 30)


def R(x0, y0, x1, y1):
    return skia.Rect.MakeLTRB(float(x0), float(y0), float(x1), float(y1))


def _cl(v, a=0.0, b=1.0):
    return float(min(b, max(a, v)))


def _lerp(a, b, u):
    return a + (b - a) * u


def _bl(c, k):
    """Wash a colour toward white (k 0..1) for the overexposed look."""
    return mix(c, P_["white"], k) if k > 0 else c


def _ink_scale(s):
    return min(4.0, max(0.55, s)) ** 0.5


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


def _shades(cv, x, y, s, fx=1.0, seed=991, inkc=INK):
    """Tiny cool sunglasses for his single eye (the Ep4 tag/endcard look); (x, y) = iris centre, fx = turn squash."""
    def X(dx):
        return x + dx * s * fx
    blob(cv, [(X(-110), y - 40 * s), (X(110), y - 40 * s), (X(96), y + 40 * s), (X(20), y + 52 * s), (X(-20), y + 52 * s), (X(-96), y + 40 * s)],
         SHADES, w=5, ink=inkc, seed=seed, boil=0.6, n=3,
         shade=lambda c: c.drawPath(poly_path([(X(-80), y - 30 * s), (X(-30), y - 30 * s), (X(-70), y + 10 * s)]), paint(P_["white"], 120)))
    for side in (-1, 1):
        line(cv, [(X(side * 108), y - 34 * s), (X(side * 150), y - 50 * s)], 6, SHADES, seed=seed + 1 + side, boil=0.4, n=2, taper=(0, 0))


def draw_gary(cv, x, fy, s, T, seed=4400, yaw=0.0, look=(0.0, 0.0), lid=None, tilt=0.0, squint=0.0, shut=0.0, crinkle=0.0,
              pupil=None, iris=1.0, mouth="auto", mo=None, loud=None, tears=0.0, tear_dir=1.0, tear_up=0.0, sweat=0.0, veins=0.0,
              stand=0.0, lean=0.0, knees=0.0, step=None, feet=None, arms=None, collar=False, light=None, bleach=0.0,
              bob=1.0, glint=True, shock=0.0, shades=None, eye_scale=1.0, hyaw=None, arms_only=False, arms_off=False):
    """Draw Gary. (x, fy) = floor point under him; s = scale (eye radius 150*s, sweater 360*s tall, legs 108*s at stand=1).
      yaw     0 front, +90 facing screen-right, -90 facing screen-left, 180 back view; hyaw = eye-only turn
      look    iris offset (-1..1); lid 0 (wide) .. 1 (half shut) [default: breathing 0.25..0.45]; tilt = lid slant
      squint  lower-lid crease 0..1; shut 0..1 = lid closed; crinkle = squeezed-shut wrinkles
      pupil   radius as a fraction of the iris (0.07 pinned .. 0.8 dilated) or 'pin' | 'spiral' | 'x' | 'heart' |
              'dollar'; iris = iris scale; shock = startle lines in the iris
      mouth   'auto' (talk from loud) | 'smile' | 'frown' | 'flat' | 'wobbly' | 'grin' | 'scream' | 'pout' | 'o'; mo = openness
      arms    dict(L=..., R=...), each dict(hand=(hx, hy[, hz]) in s-units relative to the eye centre (front-view
              coords; default hanging at (+-140, 330)), or world=(X, Y) screen coords; pose ('open', 'fist', 'point',
              'flat', ... as zee._hand), ang, mirror, bend (+1/-1 elbow side), behind, elbow=(ex, ey), reach)
      stand   0 sitting on the floor .. 1 standing on little legs; lean = upper-body tilt (deg); knees = wobble
      step    walk phase (radians) or None; feet = [(X, Y), (X, Y)] world positions (dangling / dragged)
      tears   0..1 gushing tears (tear_dir flips the arcs, tear_up turns them into geysers); sweat 0..1; veins 0..1
      shades  None = no sunglasses; 0 = on the eye .. 1 = slid down so he peeks over them
      light   dict(dir=(dx, dy) toward the light, a=0..1, rgb) -- cel crescent + warm glaze
      bleach  0..1 washes his colours toward white (overexposed world); collar = True | dict(open=0..1, lock=bool)
      arms_only / arms_off draw only / skip the front arms (for props held between body and arm)."""
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
    kind = pupil if isinstance(pupil, str) else None
    L0 = 0.0 if loud is None else loud
    if kind == "pin":
        pf = 0.07
    elif kind is None:
        pf = pupil if pupil is not None else (0.42 + 0.22 * min(1.0, L0))
    else:
        pf = 0.42
    fx = max(0.06, ca)
    if ca > -0.05:
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
        pr = ir * pf
        if kind == "spiral":                               # dizzy
            ang0 = T * 7.0
            pts = [(ex + (u * ir * 0.12) * fx * math.cos(ang0 + u), ey + (u * ir * 0.12) * math.sin(ang0 + u)) for u in np.linspace(0.3, 7.2, 40)]
            line(cv, pts, 5.5 * min(1.0, s * 1.2) + 1.5, inkc, seed=seed + 6, boil=0.4, n=3, taper=(0.1, 0.1))
        elif kind == "x":                                  # knocked out
            for d in (-1, 1):
                line(cv, [(ex - ir * 0.45 * fx, ey - d * ir * 0.45), (ex + ir * 0.45 * fx, ey + d * ir * 0.45)], 9 * s + 2, inkc,
                     seed=seed + 6 + d, boil=0.5, n=2, taper=(0.1, 0.1))
        elif kind == "heart":                              # smitten (beats)
            hr = ir * 0.62 * (1 + 0.08 * math.sin(T * 14))
            hp = [(ex, ey + hr), (ex - hr * 1.15 * fx, ey - hr * 0.1), (ex - hr * 0.62 * fx, ey - hr * 0.95), (ex, ey - hr * 0.45),
                  (ex + hr * 0.62 * fx, ey - hr * 0.95), (ex + hr * 1.15 * fx, ey - hr * 0.1)]
            blob(cv, hp, _bl(P_["magenta"], bk), w=3.5, ink=inkc, seed=seed + 7, boil=0.6, n=4)
        elif kind == "dollar":                             # greed
            cv.save(); cv.translate(ex, ey); cv.scale(fx, 1.0)
            paint_text(cv, "$", 0, ir * 0.42, font="bangers", size=ir * 1.25, fill=_bl(P_["yellow"], bk), ink_w=3.5, outline_rgb=inkc, shadow=None,
                       seed=seed + 7, streaks=False)
            cv.restore()
        else:
            blob(cv, ell(ex, ey, pr * fx, pr, n=9), inkc, w=0, seed=seed + 6, boil=0.5 if pr > 6 else 0.2, misreg=(0, 0))
        if glint:
            if kind in (None, "pin"):
                small = pf <= 0.2
                gr = ir * 0.13 if small else max(2.5 * s, pr * 0.28)
                dots(cv, [(ex - (pr * 0.45 + (gr if small else 0)) * fx, ey - max(pr * 0.5, ir * 0.25))], gr, P_["white"])
            else:
                dots(cv, [(ex - ir * 0.32 * fx, ey - ir * 0.36)], max(2.0, ir * 0.14), P_["white"])
        cv.restore()

    # lid (bowl cap; front window lowers to close)
    if lid is None:
        lid = 0.25 + 0.2 * math.sin(T * 0.7)
    h_front = -150 * s + 105 * s * max(0.0, lid)
    h_side = -20 * s - 90 * s * _cl((0.25 - lid) / 0.45)
    if shut > 0:
        h_front = _lerp(h_front, 64 * s, shut)
        h_side = _lerp(h_side, 22 * s, shut)
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

    # sunglasses (on the iris; slide down toward the mouth as shades -> 1)
    if shades is not None and ca > 0.2:
        _shades(cv, ex, ey + _cl(float(shades)) * 70 * s, s * iris, fx=fx, seed=seed + 140, inkc=inkc)

    # mouth (on the white, under the iris)
    mb = math.radians(hyaw + 10 * look[0])
    cm, sm = math.cos(mb), math.sin(mb)
    if cm > 0.12:
        fxm = max(0.15, cm)
        mx, my = 6 * s * cm + 118 * s * sm, ecy + 92 * s
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
    return dict(eye=to_world(ecx, ecy), r=rr, iris=to_world(ex, ey), hip=(x, hip_y), shL=to_world(*sh_pts["L"]), shR=to_world(*sh_pts["R"]))
