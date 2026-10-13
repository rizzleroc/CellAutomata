"""BOXED ep4 'THE CAVE' -- owner 'cave': the descent into the cave and the whole set-up of the allegory.

  T011_cave_in        fall down a crystal shaft -> the immense cavern opens up -> painted title THE CAVE (+ echo)
  T012_cave_reveal    Z03-Z04: crane down the huge cavern to the chained row; baby-prisoner inset; ankle/collar
                      inserts; one prisoner strains to turn his head; their eye; whip to the prisoners' POV
  T014_fire_wall      Z05-Z06: reverse angle - the fire behind them, the low wall (a puppet-show screen, with a tiny
                      proscenium gag), carriers with statues popping up on 'animals / people / trees'; then the
                      cross-section: firelight carries the statues' shapes onto the wall
  T016_only_shadows   Z07-Z08: the endless shadow parade; NOPE-stamped cards (fire / puppets / each other); only
                      shadows; carriers chatting, echo rings bounce off the wall; the shadows 'talk'
  T020_shadowplay     SHADOWPLAY + Z11: the shadow show as their whole world; REALITY; name labels; study
                      scribbles; the quickest guesser gets a medal + laurels while the others clap in chains

Everything is built from the shared CAVE KIT in shots_ep4_base (same layout, colours, prisoners, carriers, statues,
shadows, fire); the helpers below only enrich it (agate rock, glow-worm curtains, crystals, spores, foreground
silhouettes) and add the reverse angle, the grand cavern, the shaft, close-ups and the graphic beats.
"""
from .shots_ep4_base import *          # noqa: F401,F403
from .zee import _hand

# ===================================================================== small helpers


def kin(t, t0, d=0.4):
    """Eased 0..1 ramp starting at t0 over d seconds."""
    return ease((t - t0) / d)


def win(t, t0, t1, a=0.25, b=0.25):
    """Eased window: 0 -> 1 over [t0, t0+a], 1 -> 0 over [t1-b, t1]."""
    return ease((t - t0) / a) * (1.0 - ease((t - (t1 - b)) / b))


def seg(t, keys):
    """Piecewise eased interpolation through keys [(t, value-or-tuple), ...]."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (ta, va), (tb, vb) in zip(keys[:-1], keys[1:]):
        if t <= tb:
            u = ease((t - ta) / max(1e-6, tb - ta))
            if isinstance(va, (tuple, list)):
                return tuple(a + (b - a) * u for a, b in zip(va, vb))
            return va + (vb - va) * u
    return keys[-1][1]


def camk(t, keys):
    """Camera dict from keyframes [(t, (x, y, z)), ...] with a tiny hand-held drift."""
    x, y, z = seg(t, keys)
    return dict(x=x + 6 * math.sin(t * 0.7) + 3 * math.sin(t * 1.9), y=y + 4 * math.sin(t * 0.53 + 1), z=z)


def glow(cv, x, y, r, rgb, a=50, n=4, sy=1.0, seed=0, T=0.0, flick=0.0):
    """Cel-style glow: n nested translucent wobbly discs (cheap, flat, poster-like)."""
    fl = 1.0 + flick * (0.05 * math.sin(T * 11 + seed) + 0.03 * math.sin(T * 23 + seed * 1.7))
    for k in range(n):
        f = (1.0 - k / n) * fl
        P = ell(x, y, r * f, r * f * sy, n=16, phase=seed + k)
        cv.drawPath(poly_path(cr_closed(jit(P, r * 0.012, seed + k), 3)), paint(rgb, a))


def soft(cv, x, y, r, rgb, a=120, sy=1.0):
    """Soft radial light pool (gradient) -- use sparingly, it is fill-rate heavy."""
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(x, y), max(1.0, r), [core.C(rgb, a), core.C(rgb, int(a * 0.3)), core.C(rgb, 0)], [0.0, 0.5, 1.0]))
    if sy != 1.0:
        cv.save(); cv.translate(x, y); cv.scale(1.0, sy); cv.translate(-x, -y)
        cv.drawCircle(x, y, r, p)
        cv.restore()
    else:
        cv.drawCircle(x, y, r, p)


def spores(cv, T, box, n=40, seed=0, cols=None, size=1.0, a=230, rise=18.0, drift=24.0):
    """Drifting glowing motes (embers / spores) inside box."""
    x0, y0, x1, y1 = box
    cols = cols or [P_["yellow"], P_["orange"], P_["cream"]]
    i = np.arange(n, dtype=np.float64)
    X = x0 + hsh(seed + i * 3.17) * (x1 - x0) + drift * np.sin(T * 0.55 + i * 1.3)
    Y = y0 + np.mod(hsh(seed + i * 5.71) * (y1 - y0) - T * rise * (0.5 + hsh(seed + i * 2.3)), (y1 - y0))
    tw = np.sin(T * (2.0 + 2.0 * hsh(seed + i)) + i) > -0.2
    for ci, c in enumerate(cols):
        for big in (0, 1):
            m = ((i % len(cols)) == ci) & tw & ((i % 2) == big)
            if not m.any():
                continue
            P = np.stack([X[m], Y[m]], 1)
            r = size * (1.6 + 1.6 * big)
            dots(cv, P, r * 3.0, c, a=int(a * 0.16))
            dots(cv, P, r, c, a=a)


def glowworms(cv, T, x0, x1, ytop, n=24, seed=0, L0=60, L1=260, rgb=None, a=210):
    """A curtain of glow-worm threads hanging from a cave ceiling, beaded with light."""
    rgb = rgb or P_["teal"]
    path = skia.Path()
    beads, tips = [], []
    for k in range(n):
        x = x0 + (x1 - x0) * float(hsh(seed + k * 1.71))
        L = L0 + (L1 - L0) * float(hsh(seed + k * 2.93)) ** 1.5
        sw = 6 * math.sin(T * 0.9 + k * 1.3)
        y0 = ytop + 30 * float(hsh(seed + k * 4.1))
        path.moveTo(x, y0)
        path.quadTo(x + sw * 0.3, y0 + L * 0.5, x + sw, y0 + L)
        nb = 3 + int(4 * hsh(seed + k * 5.3))
        for j in range(nb):
            u = (j + 1) / (nb + 1)
            beads.append((x + sw * u * u, y0 + L * u))
        tips.append((x + sw, y0 + L))
    cv.drawPath(path, paint(mix(rgb, P_["white"], 0.2), int(a * 0.5), stroke=1.6))
    dots(cv, beads, 2.4, mix(rgb, P_["white"], 0.45), a=a)
    dots(cv, tips, 10, rgb, a=int(a * 0.22))
    dots(cv, tips, 4, P_["mint"], a=a)


_PICS = {}


def stip(cv, rgb, box, spacing=15, r=2.0, seed=0, fn=None, a=255, key=None):
    """core.stipple, recorded once into a skia.Picture and replayed (stipple never boils)."""
    k = (key, tuple(int(v) for v in rgb), tuple(int(round(v)) for v in box), spacing, r, seed, a)
    pic = _PICS.get(k)
    if pic is None:
        if len(_PICS) > 400:
            _PICS.clear()
        x0, y0, x1, y1 = box
        rec = skia.PictureRecorder()
        c = rec.beginRecording(skia.Rect.MakeLTRB(x0 - 20, y0 - 20, x1 + 20, y1 + 20))
        stipple(c, rgb, box, spacing, r, seed, a, fn)
        pic = rec.finishRecordingAsPicture()
        _PICS[k] = pic
    cv.drawPicture(pic)


def rock(cv, pts, seed=4200, rgb=None, rim=None, rim_side=1, a=255, ink=5.5, strata=7, sp=15, agate=None):
    """kit rock_mass with a cached stipple and optional psychedelic agate banding agate=(cx, cy, r0, n, rgb2)."""
    rgb = rgb or CV_ROCK
    P = np.asarray(pts, float)
    x0, y0 = P.min(0)
    x1, y1 = P.max(0)

    def sh(c):
        if agate is not None:
            ax, ay, r0, na, rgb2 = agate
            for k in range(na):
                rr = r0 * (1.0 - k / (na + 0.5))
                col = rgb2 if k % 2 == 0 else rgb
                c.drawPath(poly_path(cr_closed(jit(ell(ax, ay, rr * 1.35, rr, n=14, phase=k * 0.7), rr * 0.02, seed + 60 + k), 3)), paint(col, 120 if k % 2 == 0 else 255))
        for k in range(strata):
            yy = y0 + (y1 - y0) * (k + 0.5) / strata
            pts2 = [(x0 - 40, yy + 18 * math.sin(k * 1.9 + seed)), ((x0 + x1) / 2, yy - 14 * math.sin(k + seed)), (x1 + 40, yy + 10 * math.sin(k * 2.7))]
            line(c, pts2, 3.0, mix(rgb, INK, 0.35), seed=seed + 20 + k, boil=0.8, n=6, taper=(0.1, 0.1), a=170)
        stip(c, mix(rgb, INK, 0.45), (x0, y0, x1, y1), sp, 2.0, seed + 3,
             fn=lambda X, Y: np.clip(0.3 + 0.7 * np.sin(X * 0.013 + Y * 0.02 + seed) ** 2, 0, 1) * 0.8, key="rock")
        if rim is not None:
            cx = x1 if rim_side > 0 else x0
            c.drawPath(poly_path(cr_closed([(cx - rim_side * 70, y0 - 50), (cx + rim_side * 60, y0 - 50), (cx + rim_side * 60, y1 + 50),
                                            (cx - rim_side * 40, y1 + 50)], 3)), paint(rim, 130))
    blob(cv, P, rgb, w=ink, seed=seed, boil=1.1, n=5, shade=sh, a=a)


def stalac(cv, x, y, L, wd, rgb, seed=0, T=0.0, drip=True, ink=4.0):
    """A ringed stalactite hanging from y (tip at y+L) with a highlight, a dark side and a forming water drop."""
    pts = [(x - wd, y - 12), (x + wd, y - 12), (x + wd * 0.55, y + L * 0.45), (x + wd * 0.12, y + L * 0.93), (x, y + L), (x - wd * 0.14, y + L * 0.9),
           (x - wd * 0.5, y + L * 0.42)]
    dk = mix(rgb, INK, 0.32)
    hi = mix(rgb, P_["white"], 0.3)

    def sh(c):
        c.drawPath(poly_path([(x + wd * 0.18, y - 30), (x + wd * 1.2, y - 30), (x + wd * 0.2, y + L * 1.05)]), paint(dk))
        c.drawPath(poly_path([(x - wd * 0.62, y - 10), (x - wd * 0.36, y - 10), (x - wd * 0.08, y + L * 0.72), (x - wd * 0.2, y + L * 0.74)]), paint(hi, 150))
        for k in range(3):
            yy = y + L * (0.18 + 0.2 * k)
            c.drawLine(x - wd, yy, x + wd, yy + 6, paint(dk, 200, stroke=2.4))
    blob(cv, pts, rgb, w=ink, seed=seed, boil=0.8, n=4, shade=sh)
    if drip:
        ph = (T * 0.33 + float(hsh(seed * 1.3))) % 1.0
        dy = 0.0 if ph < 0.72 else (ph - 0.72) / 0.28 * 520
        rr = 3 + 4 * min(1.0, ph / 0.72)
        dots(cv, [(x, y + L + rr + dy)], rr, P_["mint"], a=int(255 * (1 - max(0.0, ph - 0.72) / 0.28)))


def stalag(cv, x, y, L, wd, rgb, seed=0, ink=4.5, rim=None):
    """A stalagmite growing up from y (tip at y-L)."""
    pts = [(x - wd, y + 10), (x - wd * 0.6, y - L * 0.45), (x - wd * 0.12, y - L * 0.93), (x, y - L), (x + wd * 0.18, y - L * 0.9), (x + wd * 0.55, y - L * 0.4),
           (x + wd, y + 10)]
    dk = mix(rgb, INK, 0.3)

    def sh(c):
        c.drawPath(poly_path([(x + wd * 0.1, y + 20), (x + wd * 1.2, y + 20), (x + wd * 0.1, y - L * 1.05)]), paint(dk))
        if rim is not None:
            c.drawPath(poly_path([(x - wd * 1.1, y + 20), (x - wd * 0.62, y + 20), (x - wd * 0.05, y - L * 1.02), (x - wd * 0.3, y - L * 0.9)]), paint(rim, 170))
        for k in range(3):
            yy = y - L * (0.15 + 0.2 * k)
            c.drawLine(x - wd, yy, x + wd, yy - 5, paint(dk, 200, stroke=2.4))
    blob(cv, pts, rgb, w=ink, seed=seed, boil=0.8, n=4, shade=sh)


def crys(cv, x, y, s, T, seed=4900, rgb=None, n=5, glow_a=55, ang0=0.0):
    """Crystal cluster (kit style) with a cheap cel glow; ang0 tilts the whole cluster."""
    rgb = rgb or [P_["teal"], P_["acid"], P_["hotpink"], P_["lilac"]][int(hsh(seed) * 4)]
    pulse = 0.8 + 0.2 * math.sin(T * 2.3 + seed)
    glow(cv, x, y - 30 * s, 120 * s * pulse, rgb, a=int(glow_a * 0.6), n=3, seed=seed)
    for k in range(n):
        ang = ang0 - 64 + k * (128 / max(1, n - 1)) + 8 * math.sin(seed + k)
        L = (55 + 60 * float(hsh(seed + k * 3))) * s * (1.25 if k == n // 2 else 1.0)
        wd = (12 + 9 * float(hsh(seed + k * 5))) * s
        r = math.radians(ang - 90)
        tip = (x + L * math.cos(r), y + L * math.sin(r))
        nn = (-math.sin(r), math.cos(r))
        pts = [(x + nn[0] * wd, y + nn[1] * wd), (tip[0] + nn[0] * wd * 0.5, tip[1] + nn[1] * wd * 0.5), tip, (tip[0] - nn[0] * wd * 0.5, tip[1] - nn[1] * wd * 0.5),
               (x - nn[0] * wd, y - nn[1] * wd)]
        blob(cv, pts, rgb, w=3.0, seed=seed + 10 + k, boil=0.5, n=2,
             shade=lambda c, pts=pts: (c.drawPath(poly_path([pts[0], pts[1], pts[2], ((pts[0][0] + pts[4][0]) / 2, (pts[0][1] + pts[4][1]) / 2)]), paint(P_["white"], 95)),
                                      c.drawPath(poly_path([pts[4], pts[3], pts[2], ((pts[0][0] + pts[4][0]) / 2, (pts[0][1] + pts[4][1]) / 2)]), paint(mix(rgb, INK, 0.25), 120))))
    if hsh(seed + 7) > 0.4:
        sparkle(cv, x + 20 * s * math.sin(seed), y - 70 * s, 9 * s + 3, P_["white"], w=1.6, seed=seed + 30, a=int(255 * pulse))


def speed_lines(cv, cx, cy, n, r0, r1, seed=0, rgb=None, a=120, w=3.0, jitter=1.0):
    """Radial speed lines (fresh every drawing)."""
    rgb = rgb or P_["cream"]
    path = skia.Path()
    for k in range(n):
        ang = 2 * math.pi * float(hsh(seed + k * 1.37 + core.D * 0.71))
        ra = r0 + (r1 - r0) * 0.5 * float(hsh(seed + k * 2.11 + core.D * 0.37)) * jitter
        rb = ra + (r1 - r0) * (0.25 + 0.5 * float(hsh(seed + k * 3.7 + core.D * 0.13)))
        path.moveTo(cx + ra * math.cos(ang), cy + ra * math.sin(ang))
        path.lineTo(cx + rb * math.cos(ang), cy + rb * math.sin(ang))
    cv.drawPath(path, paint(rgb, a, stroke=w))


def hlines(cv, n, seed=0, rgb=None, a=110, w=3.0, box=(0, 0, W, H), vertical=False):
    """Straight streak lines across a box (whip pans / falls)."""
    rgb = rgb or P_["cream"]
    x0, y0, x1, y1 = box
    path = skia.Path()
    for k in range(n):
        u = float(hsh(seed + k * 1.9 + core.D * 0.53))
        L = (0.2 + 0.6 * float(hsh(seed + k * 2.7 + core.D * 0.29)))
        s0 = float(hsh(seed + k * 4.3 + core.D * 0.17)) * (1 - L)
        if vertical:
            x = x0 + u * (x1 - x0)
            path.moveTo(x, y0 + s0 * (y1 - y0)); path.lineTo(x, y0 + (s0 + L) * (y1 - y0))
        else:
            y = y0 + u * (y1 - y0)
            path.moveTo(x0 + s0 * (x1 - x0), y); path.lineTo(x0 + (s0 + L) * (x1 - x0), y)
    cv.drawPath(path, paint(rgb, a, stroke=w))


def flash(cv, a, rgb=None):
    if a > 0:
        cv.drawRect(R(-50, -50, W + 50, H + 50), paint(rgb or P_["white"], int(np.clip(a, 0, 1) * 255)))


def dim(cv, a, rgb=(10, 4, 30)):
    if a > 0:
        cv.drawRect(R(-50, -50, W + 50, H + 50), paint(rgb, int(np.clip(a, 0, 1) * 255)))


def sfx(cv, text, x, y, size, t, t0, fill=None, seed=0, ang=-8, dur=0.25, hold=0.9, shadow_rgb=None, font="bangers"):
    """Comic sound-effect lettering that slams in at t0 and fades after `hold` seconds."""
    if t < t0 or t > t0 + hold + 0.25:
        return
    k = pop(t, t0, dur)
    a = 255 * (1.0 - ease((t - t0 - hold) / 0.25))
    cv.save(); cv.translate(x, y); cv.rotate(ang + 3 * math.sin(t * 20) * (1 - kin(t, t0, 0.4))); cv.scale(k, k)
    paint_text(cv, text, 0, size * 0.35, font=font, size=size, fill=fill or P_["yellow"], ink_w=6, shadow=(7, 7), shadow_rgb=shadow_rgb or P_["magenta"],
               seed=seed, a=int(a))
    cv.restore()


# ===================================================================== kit-matched characters (extended)
def pris(cv, x, y, s, T, seed=4500, view="side", face=1.0, look=(0.0, 0.0), rgb=None, eye_rgb=None, chained=True, glow_k=0.0,
         blink=None, mouth=0.0, anchor=None, sag=None, rim=None, eye_k=1.0, sparkle_k=0.0, veins=0.0, arms=None, squash=(1.0, 1.0),
         collar=True, shackles=True, refl=None, ink_k=1.0, feet=False, detail=False, shake=0.0, rim_dir=(0.0, -1.0), refl_top=None, mouth_low=False):
    """The kit prisoner (same body/eye/collar/chain design) plus: continuous `face` (head turn), eye size `eye_k`,
    amazed sparkles, straining red veins, a taut chain (`sag`), a fire rim light, optional stubby `arms`
    dict(l=(hx, hy), r=(hx, hy), cuffs=True) in body-local units of r, and a reflection `refl(c, ex, ey, er)` in the eye."""
    rgb = rgb or [(64, 30, 110), (90, 40, 150), (46, 20, 86), (110, 50, 120)][int(hsh(seed) * 4)]
    eye_rgb = eye_rgb or [(200, 255, 230), (255, 200, 240), (255, 240, 170), (190, 220, 255)][int(hsh(seed + 1) * 4)]
    bob = 2.5 * math.sin(T * 1.7 + seed) * s
    r = 70 * s
    sx, sy = squash
    cx, cy = x, y - r * 1.15 * sy + bob
    body = [(x - r * 1.05 * sx, y), (x - r * 1.1 * sx, cy), (x - r * 0.7 * sx, cy - r * 0.95 * sy), (x, cy - r * 1.12 * sy), (x + r * 0.7 * sx, cy - r * 0.95 * sy),
            (x + r * 1.1 * sx, cy), (x + r * 1.05 * sx, y)]
    fs = max(-1.0, min(1.0, face))
    if shake > 0:
        x += shake * 7 * s * math.sin(T * 90.0)
        cx = x
        body = [(px_ + shake * 7 * s * math.sin(T * 90.0), py_) for px_, py_ in body]
    if arms is not None and arms.get("behind"):
        _arms(cv, cx, cy, r, s, arms, seed, rgb)

    def sh(c):
        if rim is not None:                                        # crescent rim light on the side facing the light
            dx, dy = rim_dir
            c.drawRect(R(x - r * 2, cy - r * 2, x + r * 2, y + r), paint(rim))
            c.drawPath(poly_path(cr_closed([(px_ - dx * r * 0.13, py_ - dy * r * 0.13) for px_, py_ in body], 5)), paint(rgb))
        c.drawPath(poly_path(cr_closed(ell(cx + fs * r * 0.45, cy + r * 0.3, r * 0.9, r * 1.1, n=10), 3)), paint(mix(rgb, INK, 0.3)))
    blob(cv, body, rgb, w=(5.0 * min(1.0, s * 1.4) + 1.5) * ink_k, seed=seed, boil=1.0, n=5, shade=sh)
    if glow_k > 0:
        firelight(cv, cx - fs * r * 0.4, cy - r * 0.2, r * 1.6, T, a=int(90 * glow_k), seed=seed)
    ex = ey = er = 0.0
    if view == "back":
        line(cv, [(cx - r * 0.5, cy - r * 0.5), (cx, cy - r * 0.62), (cx + r * 0.5, cy - r * 0.5)], 3, mix(rgb, P_["white"], 0.25), seed=seed + 3, boil=0.6, n=4)
    else:
        bl = blink if blink is not None else (1.0 if (T * 0.4 + hsh(seed) * 3) % 3.1 < 0.12 else 0.0)
        ex = cx + (fs * r * 0.32 if view == "side" else 0.0)
        ey = cy - r * 0.18 * sy
        er = r * (0.5 if view == "front" else 0.42) * eye_k
        if bl > 0.5:
            line(cv, [(ex - er, ey), (ex, ey + er * 0.3), (ex + er, ey)], 4 * ink_k, seed=seed + 5, boil=0.6, n=4)
        else:
            def esh(c):
                if veins > 0:
                    for k in range(6):
                        a0 = k * 1.047 + 0.4
                        p0 = (ex + er * 1.02 * math.cos(a0), ey + er * 1.02 * math.sin(a0))
                        p1 = (ex + er * 0.55 * math.cos(a0 + 0.25), ey + er * 0.55 * math.sin(a0 + 0.25))
                        line(c, [p0, ((p0[0] + p1[0]) / 2 + 3, (p0[1] + p1[1]) / 2 - 2), p1], 2.2 + 1.5 * s, P_["red"], seed=seed + 40 + k, boil=0.7, n=3, a=int(255 * veins))
                if refl is not None:
                    refl(c, ex, ey, er)
            blob(cv, ell(ex, ey, er, er * 1.05, n=10), P_["white"], w=4 * ink_k, seed=seed + 5, boil=0.7, shade=esh)
            ix = ex + (fs * er * 0.35 if view == "side" else 0) + look[0] * er * 0.4
            iy = ey + look[1] * er * 0.4
            dots(cv, [(ix, iy)], er * 0.55, eye_rgb)
            dots(cv, [(ix, iy)], er * 0.28 * (1.0 - 0.25 * sparkle_k), INK)
            dots(cv, [(ix - er * 0.15, iy - er * 0.2)], er * 0.1 + 0.8, P_["white"])
            if refl_top is not None:
                cv.save(); cv.clipPath(poly_path(cr_closed(ell(ex, ey, er, er * 1.05, n=10), 3)), doAntiAlias=True)
                refl_top(cv, ex, ey, er)
                cv.restore()
            if sparkle_k > 0:
                dots(cv, [(ix + er * 0.18, iy + er * 0.12)], er * 0.06 + 0.6, P_["white"])
                for k in range(3):
                    aa = -2.3 + k * 0.9 + 0.2 * math.sin(T * 6 + k)
                    sparkle(cv, ex + er * 1.5 * math.cos(aa), ey + er * 1.5 * math.sin(aa), (5 + 4 * s) * sparkle_k * (0.8 + 0.3 * math.sin(T * 9 + k)),
                            P_["yellow"] if k != 1 else P_["white"], w=1.8, seed=seed + 70 + k)
        if mouth > 0.05 and not mouth_low:
            blob(cv, ell(ex, ey + er * 1.45, er * 0.45, er * 0.18 + er * 0.5 * mouth, n=8), P_["mouth"], w=3, seed=seed + 6, boil=0.6)
    if chained and collar:
        ny = cy + r * 0.42 * sy
        blob(cv, ell(cx, ny, r * 0.82 * sx, r * 0.2, n=10), (120, 120, 150), w=3.5 * ink_k, seed=seed + 8, boil=0.6,
             shade=lambda c: (c.drawRect(R(cx - r, ny, cx + r, ny + r * 0.3), paint((80, 80, 110))),
                              c.drawRect(R(cx - r, ny - r * 0.2, cx + r, ny - r * 0.1), paint((180, 180, 205)))))
        ax, ay = anchor if anchor is not None else (x - fs * r * 1.5, y + 4 * s)
        chain(cv, (cx - fs * r * 0.6, ny + r * 0.1), (ax, ay), seed=seed + 9, link=max(8.0, 15 * s), sag=(10 * s if sag is None else sag), w=max(1.6, 2.6 * s))
        blob(cv, ell(ax, ay, 12 * s + 2, 5 * s + 2, n=8), (120, 120, 150), w=3, seed=seed + 10, boil=0.4)
    if mouth_low and mouth > 0.05 and view != "back":              # mouth under the collar (amazed / cheering)
        mx_, my_ = ex, cy + r * 0.74 * sy
        mh = r * (0.06 + 0.16 * mouth)
        blob(cv, ell(mx_, my_ + mh * 0.3, r * 0.22, mh, n=10), P_["mouth"], w=3.5 * ink_k, seed=seed + 6, boil=0.6,
             shade=lambda c: blob(c, ell(mx_ + r * 0.03, my_ + mh * 1.0, r * 0.14, mh * 0.5, n=8), P_["tongue"], w=0, seed=seed + 7, boil=0.4, misreg=(0, 0)))
    if feet:                                                       # stubby feet poking out at the front
        for j, (fx, fy) in enumerate(((x + fs * r * 1.1, y + r * 0.05), (x + fs * r * 0.62, y + r * 0.1))):
            blob(cv, ell(fx, fy - r * 0.02, r * 0.34, r * 0.17, n=10), mix(rgb, P_["lilac"], 0.35), w=4 * ink_k, seed=seed + 20 + j, boil=0.8,
                 shade=lambda c, fx=fx, fy=fy: c.drawPath(poly_path(cr_closed(ell(fx + r * 0.05, fy + r * 0.08, r * 0.34, r * 0.08, n=8), 3)), paint(mix(rgb, INK, 0.2))))
            for q in range(3):
                dots(cv, [(fx + fs * r * (0.22 + 0.0 * q), fy - r * 0.08 + q * r * 0.07)], r * 0.025 + 1, mix(rgb, INK, 0.4))
    if chained and detail:                                         # rivets + a padlock on the collar
        ny = cy + r * 0.42 * sy
        dots(cv, [(cx + r * 0.82 * sx * math.cos(a_), ny + r * 0.2 * math.sin(a_) - r * 0.02) for a_ in np.linspace(0.35, 2.8, 7)], r * 0.035 + 1, (200, 200, 225))
        lx, ly = cx + fs * r * 0.25, ny + r * 0.24
        tube(cv, [(lx - r * 0.07, ly), (lx - r * 0.07, ly - r * 0.1), (lx + r * 0.07, ly - r * 0.1), (lx + r * 0.07, ly)], r * 0.035, (190, 190, 205), w=3, seed=seed + 14,
             boil=0.4, n=4)
        blob(cv, rect_pts([(lx - r * 0.12, ly), (lx + r * 0.12, ly), (lx + r * 0.12, ly + r * 0.17), (lx - r * 0.12, ly + r * 0.17)], 3), P_["gold"], w=3.5, seed=seed + 15,
             boil=0.5, n=3, shade=lambda c: c.drawRect(R(lx + r * 0.04, ly, lx + r * 0.2, ly + r * 0.2), paint(mix(P_["gold"], INK, 0.25))))
        dots(cv, [(lx, ly + r * 0.08)], r * 0.025 + 1, INK)
    if chained and shackles:
        if feet:
            pts_ = []
            for j, (fx, fy) in enumerate(((x + fs * r * 1.1, y + r * 0.05), (x + fs * r * 0.62, y + r * 0.1))):
                blob(cv, ell(fx - fs * r * 0.1, fy - r * 0.02, r * 0.08, r * 0.2, n=10), (130, 130, 160), w=3.5 * ink_k, seed=seed + 24 + j, boil=0.5,
                     shade=lambda c, fx=fx, fy=fy: (c.drawRect(R(fx - r * 0.06, fy - r * 0.3, fx + r * 0.2, fy + r * 0.1), paint((90, 90, 120))),
                                                    c.drawRect(R(fx - r * 0.2, fy - r * 0.24, fx - r * 0.1, fy + r * 0.1), paint((200, 200, 225)))))
                pts_.append((fx - fs * r * 0.1, fy + r * 0.1))
            chain(cv, pts_[0], pts_[1], seed=seed + 26, link=max(8.0, 13 * s), sag=8 * s, w=max(1.6, 2.4 * s))
            ax_, ay_ = anchor if anchor is not None else (x - fs * r * 1.5, y + 4 * s)
            chain(cv, pts_[1], (ax_ - fs * r * 0.2, ay_ + r * 0.02), seed=seed + 27, link=max(8.0, 13 * s), sag=6 * s, w=max(1.6, 2.4 * s))
        else:
            for side in (-1, 1):
                blob(cv, ell(x + side * r * 0.6, y - 6 * s, r * 0.25, r * 0.1, n=8), (120, 120, 150), w=3, seed=seed + 12 + side, boil=0.4)
    if arms is not None and not arms.get("behind"):
        _arms(cv, cx, cy, r, s, arms, seed, rgb)
    return dict(cx=cx, cy=cy, r=r, ex=ex, ey=ey, er=er)


def _arms(cv, cx, cy, r, s, arms, seed, rgb):
    """Stubby rubber-hose arms with white mitten hands and iron cuffs (+ a short chain between the wrists)."""
    hands = []
    for side, key in ((-1, "l"), (1, "r")):
        hx, hy = arms[key]
        sh = (cx + side * r * 0.95, cy + r * 0.15)
        hp = (cx + hx * r, cy + hy * r)
        el = ((sh[0] + hp[0]) / 2 + side * r * 0.25, (sh[1] + hp[1]) / 2 + r * 0.12)
        tube(cv, [sh, el, hp], r * 0.2, rgb, w=3.5, seed=seed + 80 + side, boil=0.8, n=6)
        hands.append(hp)
    if arms.get("cuffs", True) and len(hands) == 2:
        chain(cv, hands[0], hands[1], seed=seed + 90, link=max(7.0, r * 0.16), sag=r * 0.12, w=max(1.4, r * 0.03))
    for k, (hp, side) in enumerate(zip(hands, (-1, 1))):
        cv.save(); cv.translate(hp[0], hp[1]); sc = r / 70.0 * 0.95; cv.scale(sc, sc)
        ang = arms.get("ang", (-90, -90))[k]
        _hand(cv, 0, 0, ang, arms.get("pose", "open"), side, seed + 95 + k, rgb=P_["white"])
        if arms.get("cuffs", True):
            blob(cv, ell(-math.cos(math.radians(ang)) * 6, -math.sin(math.radians(ang)) * 6, 20, 20, n=8), (130, 130, 160), w=3.5, seed=seed + 98 + k, boil=0.5,
                 shade=lambda c: c.drawRect(R(-30, 4, 30, 30), paint((85, 85, 115))))
        cv.restore()


def statue2(cv, kind, x, y, s, T, seed=4700, rgb=None, back=0.0, rim=None):
    """kit statue + optional backlight (darken the face toward the viewer) and a hot rim."""
    statue(cv, kind, x, y, s, T, seed=seed, rgb=rgb)
    if back > 0 or rim is not None:
        pts = SHAPES.get(kind, SHAPES["star"])
        P = np.array([(x + px * s, y + py * s) for px, py in pts])
        path = poly_path(cr_closed(jit(P, 0.6, seed + 917), 4))
        if back > 0:
            cv.drawPath(path, paint((40, 14, 60), int(170 * back)))
        if rim is not None:
            cv.save(); cv.clipPath(path, doAntiAlias=True)
            cv.drawPath(path, paint(rim, 210, stroke=10 * s + 3))
            cv.restore()
        brush(cv, cr_closed(jit(P, 0.8, seed), 4), 4.0, closed=True, seed=seed + 3)


def carrier2(cv, x, y, s, T, holding="horse", seed=4600, phase=0.0, rgb=None, face=1, raise_k=1.0, walk=True, talk=0.0, statue_k=1.0,
             back=0.0, rim=None, srgb=None, bob_amp=1.0):
    """kit carrier with: the statue pole raised by raise_k (0 hidden low .. 1 up), statue pop scale statue_k, a talking
    glowing mouth under the hood (talk 0..1) and the walk cycle switchable (walk=False stands)."""
    rgb = rgb or (36, 16, 60)
    tt = (T + phase) if walk else phase
    step = math.sin(tt * 4.2) if walk else 0.0
    bob = abs(math.cos(tt * 4.2)) * 6 * s * bob_amp if walk else 0.0
    for side in (-1, 1):
        line(cv, [(x + side * 14 * s, y - 120 * s - bob), (x + side * 18 * s + step * side * 22 * s, y)], 16 * s + 2, rgb, seed=seed + side, boil=0.7, n=3, taper=(0, 0))
    robe = [(x - 60 * s, y - 60 * s - bob), (x - 46 * s, y - 230 * s - bob), (x, y - 300 * s - bob), (x + 46 * s, y - 230 * s - bob), (x + 60 * s, y - 60 * s - bob)]
    blob(cv, robe, rgb, w=4.5, seed=seed + 3, boil=1.0, n=5,
         shade=(lambda c: c.drawPath(poly_path(cr_closed(ell(x - face * 40 * s, y - 200 * s - bob, 40 * s, 150 * s, n=10), 3)), paint(rim, 120))) if rim else None)
    hx, hy = x + face * 6 * s, y - 280 * s - bob
    blob(cv, ell(hx, hy, 42 * s, 48 * s, n=10), rgb, w=4.5, seed=seed + 4, boil=0.9,
         shade=(lambda c: c.drawPath(poly_path(cr_closed(ell(hx - face * 30 * s, hy - 20 * s, 26 * s, 40 * s, n=10), 3)), paint(rim, 130))) if rim else None)
    blob(cv, ell(hx + face * 12 * s, hy + 6 * s, 26 * s, 30 * s, n=10), (12, 4, 20), w=0, seed=seed + 5, boil=0.6, misreg=(0, 0))
    for side in (-1, 1):
        dots(cv, [(hx + face * 12 * s + side * 11 * s, hy + 1 * s)], 4.5 * s + 1, P_["yellow"])
    if talk > 0.05:
        blob(cv, ell(hx + face * 13 * s, hy + 18 * s, 8 * s, (2 + 9 * talk) * s, n=8), P_["orange"], w=2, seed=seed + 7, boil=0.5)
    lift = (1.0 - raise_k) * 230 * s
    px, py = x + face * 40 * s, y - 210 * s - bob + lift * 0.3
    top = (px + face * 10 * s, y - 470 * s - bob + lift)
    if statue_k > 0.01:
        line(cv, [(px, py + 80 * s), top], 7 * s + 1.5, (110, 70, 40), seed=seed + 6, boil=0.5, n=2, taper=(0, 0))
    tube(cv, [(x + face * 30 * s, y - 220 * s - bob), (px, py)], 14 * s, rgb, w=3.5, seed=seed + 7, boil=0.6)
    if statue_k > 0.01:
        statue2(cv, holding, top[0], top[1] - 60 * s * statue_k, 0.9 * s * statue_k, T, seed=seed + 8, back=back, rim=rim, rgb=srgb)
    return top


# custom shadow silhouettes for animated shadow play (unit ~ +-100, y down, facing right)
SH2 = {
    "bird_up": [(-104, -2), (-70, -10), (-36, -14), (-40, -62), (-14, -116), (2, -60), (22, -18), (56, -22), (78, -34), (100, -26), (118, -16), (96, -8), (74, 6),
                (40, 16), (0, 20), (-40, 16), (-104, 14)],
    "bird_dn": [(-104, -2), (-70, -10), (-30, -12), (22, -18), (56, -22), (78, -34), (100, -26), (118, -16), (96, -8), (74, 6), (40, 16), (18, 26), (6, 70),
                (-16, 118), (-30, 66), (-34, 18), (-104, 14)],
    "horse_a": [(-110, 40), (-100, -10), (-60, -30), (20, -30), (50, -70), (60, -110), (80, -120), (110, -90), (100, -70), (80, -60), (70, -20),
                (96, 30), (84, 40), (56, 10), (-40, 10), (-80, 46), (-94, 40), (-74, 6), (-96, 16), (-104, 40)],
    "horse_b": [(-110, 50), (-100, -10), (-60, -30), (20, -30), (50, -70), (60, -110), (80, -120), (110, -90), (100, -70), (80, -60), (70, -20),
                (66, 56), (52, 56), (50, 10), (-40, 10), (-46, 56), (-60, 56), (-70, 14), (-96, 20), (-98, 56)],
    "bunny_s": [(-80, 50), (-90, 10), (-66, -24), (-20, -32), (-14, -120), (4, -160), (22, -120), (18, -44), (40, -126), (60, -156), (66, -104),
                (46, -36), (76, -16), (98, 14), (86, 42), (54, 56), (0, 62)],
}


def shadow2(cv, pts, x, y, s, T, rgb=None, a=230, seed=4800, flip=1, sy=1.0, ang=0.0, blur=True):
    """kit shadow_shape for any point list; flip=-1 mirrors (faces left), sy squash/stretch, ang tilt (deg)."""
    rgb = rgb or CV_SHADOW
    fl = 1.0 + 0.03 * math.sin(T * 9 + seed)
    P = np.array([(px * flip, py * sy) for px, py in (SHAPES[pts] if isinstance(pts, str) and pts in SHAPES else SH2[pts] if isinstance(pts, str) else pts)], float)
    if ang:
        P = rot(P, ang)
    P = P * s * fl + np.array([x, y])
    path = poly_path(cr_closed(jit(P, 1.2, seed), 4))
    if blur:
        halo = skia.Paint(AntiAlias=True, Color=core.C(rgb, int(a * 0.45)))
        halo.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10 * s + 2))
        cv.drawPath(path, halo)
    cv.drawPath(path, paint(rgb, a))
    return P


# ===================================================================== THE CROSS-SECTION (kit layout, enriched)
KINDS = ["horse", "bunny", "tree", "person", "bird", "jug"]


def side_world(cv, T, cam=None, fire=1.0, seed=4000, carriers=None, prisoners=None, wall_shadows=None, mouth_light=1.0, hooks=None,
               fg=True, low_wall=None, decor=1):
    """kit cave_side() layout (wall x<330 | prisoners 420..900 facing left | low wall 960..1340 + carriers | fire 1520 | path to
    the mouth top-right), enriched: agate back rock, glow-worm curtains, more crystals, spores, foreground silhouettes.
    carriers / prisoners: None = kit default parade/row, [] = none, or lists of dicts (see code). hooks: {'back','wall','mid',
    'front','top'} callables(cv) run inside the matching camera layers."""
    hooks = hooks or {}
    C = sets.Cam(cv, cam or dict(x=0, y=0, z=1.0))
    with C.layer(0.2):                                             # deep back wall of the cavern
        w.field(cv, CV_ROCK_DK)
        glow(cv, 1500, 690, 1250, (70, 24, 110), a=60, n=4, seed=seed + 1)
        rock(cv, [(-400, 80), (700, 40), (1400, 90), (2400, 30), (2400, 1100), (-400, 1100)], seed=seed + 11, rgb=(36, 14, 70), ink=4,
             agate=(1500, 640, 900, 6, (58, 22, 104)))
        glowworms(cv, T, -300, 2300, 30, n=34, seed=seed + 15, L0=50, L1=240, rgb=P_["teal"], a=170)
        for k in range(7):
            crys(cv, 80 + k * 300 + 60 * math.sin(k * 1.7), 640 + 90 * math.sin(k * 2.9), 0.7, T, seed=seed + 120 + k)
        if "back" in hooks:
            hooks["back"](cv)
    with C.layer(0.5):                                             # far rock + the cave mouth with daylight
        if mouth_light > 0:
            g = skia.Paint(AntiAlias=True)
            g.setShader(skia.GradientShader.MakeRadial(skia.Point(1840, 90), 560, [core.C(P_["white"], int(255 * mouth_light)), core.C(P_["yellow"], int(210 * mouth_light)),
                                                                                    core.C(P_["orange"], 0)], [0.0, 0.35, 1.0]))
            cv.drawRect(R(1300, -200, 2300, 760), g)
            sun_rays(cv, 1860, 60, 1300, T, n=9, a=int(70 * mouth_light), ang0=145, span=55)
        rock(cv, [(-300, -300), (2400, -300), (2400, -60), (1960, 20), (1700, 260), (1500, 180), (1200, 120), (800, 160), (300, 120), (-300, 200)],
             seed=seed + 1, rgb=CV_ROCK, rim=P_["magenta"], rim_side=1)
        glowworms(cv, T, 100, 1500, 120, n=16, seed=seed + 25, L0=60, L1=200, rgb=P_["acid"], a=200)
        for row, (yb, sc, col) in enumerate(((112, 1.0, CV_ROCK2), (150, 0.7, mix(CV_ROCK2, P_["magenta"], 0.25)))):
            for k in range(11):                                    # two rows of stalactites
                sx = 60 + k * 165 + 50 * math.sin(k * 2.3 + row) + row * 80
                if sx > 1650:
                    continue
                sl = (60 + 80 * float(hsh(seed + k + row * 20))) * sc
                y0s = yb + 18 * math.sin(k + row)
                stalac(cv, sx, y0s, sl + 46 * sc, 28 * sc, col, seed=seed + 30 + k + row * 20, T=T, drip=(k + row) % 3 == 0)
        if decor:
            for k in range(3):
                crys(cv, 420 + k * 430, 150 + 20 * k, 0.55, T, seed=seed + 140 + k, ang0=180)
        if "top" in hooks:
            hooks["top"](cv)
    with C.layer(0.85):
        wall = [(-200, 120), (330, 140), (360, 420), (330, 760), (290, 1000), (-200, 1000)]
        wall_surface(cv, wall, T, seed=seed + 2, cx=150, cy=520)
        sh_list = wall_shadows
        if sh_list is None:
            sh_list = []
            for k in range(3):
                ph = (T * 0.07 + k / 3.0) % 1.0
                sh_list.append((KINDS[(int(T * 0.07 + k / 3.0) * 3 + k) % len(KINDS)], 330 - ph * 520, 420 + 40 * math.sin(k), 1.0))
        if sh_list or "wall" in hooks:
            cv.save()
            cv.clipPath(poly_path(cr_closed(wall, 4)), doAntiAlias=True)
            for item in sh_list:
                kind, sx, sy, ss = item[:4]
                aa = item[4] if len(item) > 4 else 230
                if callable(kind):
                    kind(cv, sx, sy, ss)
                else:
                    shadow_shape(cv, kind, sx, sy, 1.1 * ss, T, seed=seed + 40 + int(sx), a=int(aa))
            if "wall" in hooks:
                hooks["wall"](cv)
            cv.restore()
        rock(cv, [(-300, 860), (700, 830), (1300, 860), (1700, 820), (2400, 840), (2400, 1400), (-300, 1400)], seed=seed + 3, rgb=CV_ROCK2,
             rim=P_["orange"], rim_side=1)
        for k in range(16):                                        # pebbles
            px = -40 + k * 140 + 50 * math.sin(k * 3.1)
            blob(cv, ell(px, 960 + 60 * float(hsh(seed + k * 9)), 16 + 10 * float(hsh(seed + k)), 9 + 5 * float(hsh(seed + k * 2)), n=8), mix(CV_ROCK2, P_["lilac"], 0.25),
                 w=3, seed=seed + 200 + k, boil=0.5)
        path = [(1250, 860), (1420, 640), (1560, 470), (1700, 300), (1820, 160), (2000, 120), (2000, 260), (1880, 330), (1700, 520), (1560, 700), (1440, 880)]
        blob(cv, path, mix(CV_ROCK2, P_["orange"], 0.3), w=5, seed=seed + 4, boil=1.0, n=4,
             shade=lambda c: [blob(c, ell(1330 + k * 66, 820 - k * 82, 30, 12, n=8, rot=-50), mix(CV_ROCK2, P_["orange"], 0.5), w=3, seed=seed + 50 + k, boil=0.5)
                              for k in range(10)])
        for k, (mx, my) in enumerate(((60, 900), (370, 930), (930, 905), (1180, 935), (1700, 900))):
            glow_mushroom(cv, mx, my, 0.8, T, seed=seed + 300 + k)
        if decor:
            for k, (cx_, cy_) in enumerate(((-120, 880), (1980, 860))):
                crys(cv, cx_, cy_, 0.9, T, seed=seed + 330 + k)
        if "mid" in hooks:
            hooks["mid"](cv)
    with C.layer(1.0):
        glow(cv, 1520, 770, 560, P_["orange"], a=int(20 * fire), n=3, sy=0.75, seed=seed + 7, T=T, flick=1.0)
        firelight(cv, 1520, 760, 420, T, a=int(130 * fire), rgb=P_["orange"], seed=seed + 7)
        if fire > 0.01:
            cave_fire(cv, 1520, 850, 0.9, T, seed=seed + 8, intensity=fire)
        if carriers is None:
            for k in range(3):
                ph = (T * 0.07 + k / 3.0) % 1.0
                carrier(cv, 1380 - ph * 520, 860, 0.62, T, holding=KINDS[(int(T * 0.07 + k / 3.0) * 3 + k) % len(KINDS)], seed=seed + 60 + k * 10, phase=k * 0.7, face=-1)
        else:
            for k, cd in enumerate(carriers):
                carrier2(cv, cd["x"], cd.get("y", 860), cd.get("s", 0.62), T, holding=cd.get("kind", "horse"), seed=cd.get("seed", seed + 60 + k * 10),
                         phase=cd.get("phase", k * 0.7), face=cd.get("face", -1), raise_k=cd.get("raise", 1.0), walk=cd.get("walk", True),
                         talk=cd.get("talk", 0.0), statue_k=cd.get("statue_k", 1.0))
        lw = low_wall or {}
        lk = lw.get("k", 1.0)
        if lk > 0.01:
            top = 870 - 170 * lk
            blob(cv, rect_pts([(960, top), (1340, top), (1350, 870), (950, 870)], 3), mix(CV_ROCK2, P_["maroon"], 0.3), w=6, seed=seed + 9, boil=0.9, n=3,
                 shade=lambda c: ([c.drawLine(960 + k * 48, top, 958 + k * 48, 870, paint(mix(CV_ROCK2, INK, 0.4), stroke=3)) for k in range(9)],
                                  c.drawRect(R(950, top, 1350, top + 24), paint(mix(CV_ROCK2, P_["orange"], 0.45)))))
            if "wall_fx" in lw:
                lw["wall_fx"](cv, top)
        if prisoners is None:
            prisoners = [dict() for _ in range(6)]
        for k, pd in enumerate(prisoners):
            px = pd.get("x", 420 + k * 95)
            py = pd.get("y", 900 + (k % 2) * 30)
            pris(cv, px, py, pd.get("s", 0.62 + 0.04 * (k % 2)), T, seed=pd.get("seed", seed + 100 + k * 13), view="side", face=pd.get("face", -1),
                 look=pd.get("look", (-1, 0)), anchor=pd.get("anchor", (px + 70, py + 12)), glow_k=pd.get("glow", 0.5), mouth=pd.get("mouth", 0.0),
                 eye_k=pd.get("eye_k", 1.0), sparkle_k=pd.get("sparkle", 0.0), blink=pd.get("blink"), sag=pd.get("sag"), veins=pd.get("veins", 0.0),
                 squash=pd.get("squash", (1.0, 1.0)), rim=pd.get("rim"))
        if "front" in hooks:
            hooks["front"](cv)
    if fg:
        with C.layer(1.3):
            stalag(cv, -170, 1190, 420, 110, (30, 12, 56), seed=seed + 500, rim=P_["magenta"])
            stalag(cv, -40, 1210, 230, 70, (40, 16, 70), seed=seed + 501, rim=P_["magenta"])
            stalag(cv, 2110, 1200, 380, 110, (30, 12, 56), seed=seed + 503, rim=P_["orange"])
            stalac(cv, -120, -90, 300, 90, (30, 12, 56), seed=seed + 505, T=T)
            stalac(cv, 2060, -110, 260, 80, (30, 12, 56), seed=seed + 506, T=T)
    spores(cv, T, (0, 0, W, H), n=26, seed=seed + 600, size=1.0, a=200, rise=22)


# ===================================================================== THE PRISONERS' POV (kit cave_wall_view, enriched)
def pov_heads(cv, T, n=7, heads_y=1010, seed=4000, cheer=0.0, x0=120, x1=1800, r0=110, bounce=0.0, arms_up=0.0):
    """Row of prisoners' heads seen from behind (silhouettes) with collars, rim light and the chain between them.
    cheer 0..1 adds waving stubby arms; bounce adds a hop."""
    pts = []
    for k in range(n):
        px = x0 + k * ((x1 - x0) / max(1, n - 1))
        r = r0 + 12 * (k % 2)
        hop = bounce * abs(math.sin(T * 7.0 + k * 1.9)) * 34
        yy = heads_y + 18 * (k % 2) + 3 * math.sin(T * 1.6 + k) - hop
        pts.append((px, yy, r))
    for k in range(len(pts) - 1):                                   # chained to each other
        chain(cv, (pts[k][0] + pts[k][2] * 0.7, pts[k][1] + pts[k][2] * 0.6), (pts[k + 1][0] - pts[k + 1][2] * 0.7, pts[k + 1][1] + pts[k + 1][2] * 0.6),
              seed=seed + 100 + k, link=20, sag=26, w=3.5)
    for k, (px, yy, r) in enumerate(pts):
        if cheer > 0.01:                                            # stubby arms waving above the head, white mitts, iron cuffs
            for side in (-1, 1):
                ph = T * 8.0 + k * 1.3 + (0 if side < 0 else 1.6)
                up = arms_up if arms_up > 0 else cheer
                hx = px + side * r * (0.95 + 0.22 * math.sin(ph))
                hy = yy - r * (0.45 + 0.85 * up) - 16 * math.sin(ph) * cheer
                tube(cv, [(px + side * r * 0.72, yy - r * 0.05), (px + side * r * 1.08, yy - r * 0.35), (hx, hy + r * 0.12)], r * 0.24, (40, 18, 66), w=4,
                     seed=seed + 300 + k * 2 + side, boil=0.8, n=5)
                cv.save(); cv.translate(hx, hy); sc = r / 110.0 * 1.25; cv.scale(sc, sc)
                _hand(cv, 0, 0, -90 + side * 12 + 10 * math.sin(ph), "spread", side, seed + 340 + k * 2 + side, rgb=P_["cream"])
                blob(cv, ell(0, 22, 22, 9, n=8), (130, 130, 160), w=3.5, seed=seed + 360 + k * 2 + side, boil=0.4)
                cv.restore()
        blob(cv, ell(px, yy, r, r * 1.05, n=12), (24, 10, 40), w=5, seed=seed + 60 + k, boil=1.0,
             shade=lambda c, px=px, yy=yy, r=r: (c.drawPath(poly_path(cr_closed(ell(px, yy - r * 0.95, r * 0.95, r * 0.34, n=10), 3)), paint(P_["orange"], 90)),
                                                c.drawPath(poly_path(cr_closed(ell(px - r * 0.2, yy - r * 1.02, r * 0.6, r * 0.14, n=10), 3)), paint(P_["yellow"], 120))))
        blob(cv, ell(px, yy + r * 0.55, r * 0.8, r * 0.2, n=10), (110, 110, 140), w=3.5, seed=seed + 80 + k, boil=0.6,
             shade=lambda c, px=px, yy=yy, r=r: c.drawRect(R(px - r, yy + r * 0.38, px + r, yy + r * 0.5), paint((170, 170, 200))))
        line(cv, [(px - r * 0.5, yy - r * 0.66), (px, yy - r * 0.78), (px + r * 0.5, yy - r * 0.66)], 4, P_["yellow"], seed=seed + 90 + k, boil=0.6, n=4, a=190)
    return pts


def pov_wall(cv, T, cam=None, seed=4000, shadows=None, heads=7, heads_y=1010, hooks=None, cheer=0.0, bounce=0.0, spore_n=34, head_shadows=True,
             frame=True, wall_glow=1.0):
    """THE PRISONERS' POV: the immense firelit wall, the parade of shadows, the prisoners' own head-shadows along its foot,
    rock frame with stalactites and crystals, dust in the firelight, and the row of heads in silhouette (layer 1.0).
    shadows: list of (kind|pts|callable, x, y, s[, flip, sy, ang, a]) in wall-layer coords (default: the kit parade)."""
    hooks = hooks or {}
    C = sets.Cam(cv, cam or dict(x=0, y=0, z=1.0))
    with C.layer(0.6):
        w.field(cv, CV_ROCK_DK)
        wall_surface(cv, [(-300, -240), (2220, -240), (2220, 1340), (-300, 1340)], T, seed=seed + 1, cx=960, cy=820, glow=wall_glow)
        for k in range(4):                                         # cave paintings: spirals + an ancient eye
            gx, gy = [(250, 260), (1660, 290), (1080, 210), (1420, 700)][k]
            col = [P_["maroon"], P_["violet"], P_["red"], P_["maroon"]][k]
            if k == 2:
                blob(cv, [(gx - 60, gy), (gx, gy - 28), (gx + 60, gy), (gx, gy + 28)], None, w=4, ink=P_["maroon"], seed=seed + 400, boil=0.8, n=5)
                dots(cv, [(gx, gy)], 13, P_["maroon"], a=150)
            else:
                sp = [(gx + (6 + u * 7) * math.cos(u * 0.9), gy + (6 + u * 7) * math.sin(u * 0.9)) for u in range(12)]
                line(cv, sp, 5, col, seed=seed + 410 + k, boil=0.8, n=4, taper=(0.1, 0.5), a=120)
        sl = shadows
        if sl is None:
            kinds = ["horse", "bunny", "tree", "person", "bird", "fish", "jug"]
            sl = []
            for k in range(3):
                ph = (T * 0.06 + k / 3.0) % 1.0
                sl.append((kinds[(int(T * 0.06 + k / 3.0) * 3 + k) % len(kinds)], 2100 - ph * 2300, 470 + 50 * math.sin(k * 2.1), 2.2))
        if head_shadows:                                           # their own heads' shadows at the foot of the wall
            for k in range(heads):
                hx = 120 + k * (1680 / max(1, heads - 1))
                cv.drawPath(poly_path(cr_closed(jit(ell(hx, 1010 - 6 * (k % 2), 190, 175, n=12), 2.0, seed + 470 + k), 3)), paint(CV_SHADOW, 140))
        for item in sl:
            kind, sx, sy, ss = item[:4]
            flip = item[4] if len(item) > 4 else 1
            ssy = item[5] if len(item) > 5 else 1.0
            ang = item[6] if len(item) > 6 else 0.0
            aa = item[7] if len(item) > 7 else 230
            if callable(kind):
                kind(cv, sx, sy, ss)
            elif kind in SHAPES and flip == 1 and ssy == 1.0 and ang == 0.0:
                shadow_shape(cv, kind, sx, sy, ss, T, seed=seed + 20 + int(sx), a=int(aa))
            else:
                shadow2(cv, kind, sx, sy, ss, T, seed=seed + 20 + int(sx), flip=flip, sy=ssy, ang=ang, a=int(aa))
        if "wall" in hooks:
            hooks["wall"](cv)
        if frame:
            rock(cv, [(-500, -500), (2500, -500), (2500, -40), (1700, 40), (1200, 10), (900, 34), (300, 70), (-500, 30)], seed=seed + 5, rgb=CV_ROCK,
                 rim=P_["orange"], strata=5)
            for k in range(13):
                sx = -160 + k * 185 + 40 * math.sin(k * 2.7)
                y0 = 40 + 30 * math.sin(k * 1.3) - (25 if 800 < sx < 1300 else 0)
                stalac(cv, sx, y0, 70 + 110 * float(hsh(seed + k * 3.3)), 24 + 12 * float(hsh(seed + k * 5.1)),
                       [CV_ROCK2, mix(CV_ROCK2, P_["magenta"], 0.25)][k % 2], seed=seed + 430 + k, T=T, drip=k % 3 == 1)
            rock(cv, [(-500, -100), (10, -60), (70, 300), (-10, 760), (50, 1400), (-500, 1400)], seed=seed + 6, rgb=CV_ROCK2, rim=P_["orange"], strata=6)
            rock(cv, [(2420, -100), (1910, -60), (1850, 360), (1930, 800), (1870, 1400), (2420, 1400)], seed=seed + 7, rgb=CV_ROCK2, rim=P_["magenta"],
                 rim_side=-1, strata=6)
            crys(cv, 40, 640, 1.2, T, seed=seed + 450, ang0=50)
            crys(cv, 1880, 520, 1.1, T, seed=seed + 451, ang0=-50)
            crys(cv, 1900, 980, 1.3, T, seed=seed + 452, ang0=-40)
            glow_mushroom(cv, 60, 330, 1.2, T, seed=seed + 453)
            glow_mushroom(cv, 1870, 260, 1.1, T, seed=seed + 454)
        spores(cv, T, (-200, 0, 2100, 1100), n=spore_n, seed=seed + 500, size=1.3, a=170, rise=10, drift=40)
    with C.layer(1.0):
        pts = pov_heads(cv, T, n=heads, heads_y=heads_y, seed=seed, cheer=cheer, bounce=bounce) if heads > 0 else []
        if "front" in hooks:
            hooks["front"](cv)
    return pts


def big_fire(cv, x, y, s, T, intensity=1.0, seed=4150):
    """The kit campfire, made glorious: halo rings, the four kit tongues, a white-hot core, detached wisps, embers."""
    glow(cv, x, y - 150 * s, 320 * s * (0.8 + 0.2 * intensity), P_["orange"], a=int(24 * intensity), n=4, seed=seed, T=T, flick=1.0)
    cave_fire(cv, x, y, s, T, seed=seed + 1, intensity=intensity)
    for li, (col, kh, kw) in enumerate(((P_["orange"], 1.02, 0.55), (P_["yellow"], 0.82, 0.34))):   # tall hot centre tongues
        H = (235 + 30 * math.sin(T * 3.7 + li)) * s * kh * intensity
        Wd = 120 * s * kw
        pts = [(x - Wd, y - 6 * s)]
        for j in range(5):
            u = (j + 0.5) / 5
            px = x - Wd + 2 * Wd * u
            lick = 0.5 + 0.5 * math.sin(T * (7.0 + j) + j * 1.3 + li)
            ph = H * (0.35 + 0.65 * math.sin(math.pi * u) ** 1.5) * (0.8 + 0.3 * lick)
            pts.append((px + 10 * s * math.sin(T * 6 + j + li), y - ph))
            if j < 4:
                pts.append((px + Wd / 5, y - ph * 0.6))
        pts.append((x + Wd, y - 6 * s))
        blob(cv, pts, col, w=2.6, seed=seed + 30 + li, boil=1.6, n=4)
    hgt = (115 + 25 * math.sin(T * 4.3)) * s * intensity
    core_pts = [(x - 32 * s, y - 8 * s), (x - 24 * s, y - hgt * 0.45), (x - 8 * s + 6 * s * math.sin(T * 7), y - hgt * 0.8), (x + 3 * s, y - hgt),
                (x + 12 * s, y - hgt * 0.7), (x + 26 * s, y - hgt * 0.4), (x + 34 * s, y - 8 * s)]
    blob(cv, core_pts, P_["cream"], w=0, seed=seed + 2, boil=1.6, n=4, a=215, misreg=(0, 0))
    for k in range(4):                                             # wisps breaking off and rising
        ph = (T * (0.9 + 0.2 * k) + k * 0.27) % 1.0
        wx = x + (k - 1.5) * 50 * s + 20 * s * math.sin(T * 3 + k)
        wy = y - (180 + 260 * ph) * s * (0.6 + 0.4 * intensity)
        ws = (1.0 - ph) * s
        if ws > 0.05:
            blob(cv, [(wx, wy - 46 * ws), (wx + 18 * ws, wy), (wx, wy + 22 * ws), (wx - 18 * ws, wy)], [P_["yellow"], P_["orange"], P_["hotpink"]][k % 3], w=2.5,
                 seed=seed + 10 + k, boil=0.8, n=4, a=int(255 * (1 - ph)))
    spores(cv, T, (x - 260 * s, y - 700 * s, x + 260 * s, y - 120 * s), n=18, seed=seed + 20, cols=[P_["yellow"], P_["orange"]], size=1.2 * s, a=230, rise=160, drift=30)


# ===================================================================== THE REVERSE ANGLE (from the wall, looking at the fire)
def rev_view(cv, T, cam=None, seed=4300, carriers=None, prisoners=None, fire=1.0, hooks=None, wall_fx=None, n_pris=6, fg=True, wall_k=1.0):
    """Looking from the shadow wall toward the fire: the prisoners face us (front view, backlit, chained), behind them
    the low wall (a puppet-show screen), the carriers behind it holding statues up against the fire, the fire, and far
    back the steep path to the sunlit cave mouth.  carriers: list of dicts (x, kind, face, raise, statue_k, walk, talk,
    phase, s); prisoners: list of dicts overriding pris() channels per seat."""
    hooks = hooks or {}
    C = sets.Cam(cv, cam or dict(x=0, y=0, z=1.0))
    with C.layer(0.15):
        w.field(cv, CV_ROCK_DK)
        g = skia.Paint(AntiAlias=True)
        g.setShader(skia.GradientShader.MakeRadial(skia.Point(1480, 40), 640, [core.C(P_["white"]), core.C(P_["yellow"], 210), core.C(P_["orange"], 0)],
                                                   [0.0, 0.3, 1.0]))
        cv.drawRect(R(700, -300, 2300, 700), g)
        rock(cv, [(-400, -300), (2400, -300), (2400, 1100), (-400, 1100)], seed=seed + 1, rgb=(40, 16, 76), ink=4, agate=(960, 640, 1000, 5, (52, 20, 94)))
        cave_mouth(cv, 1500, 60, 0.9, T, seed=seed + 4)
        for k in range(6):                                         # the steep switchback path up to the mouth
            y0_, y1_ = 700 - k * 100, 700 - (k + 1) * 100
            x0_, x1_ = (980, 1300) if k % 2 == 0 else (1300, 1040)
            if k == 5:
                x1_ = 1440
            line(cv, [(x0_, y0_), (x1_, y1_ + 10)], 22, mix(CV_ROCK2, P_["orange"], 0.4), seed=seed + 2 + k, boil=0.7, n=2, taper=(0, 0))
            for q in range(4):
                u_ = (q + 0.5) / 4
                px_, py_ = x0_ + (x1_ - x0_) * u_, y0_ + (y1_ + 10 - y0_) * u_
                cv.drawLine(px_ - 8, py_ - 9, px_ + 8, py_ + 9, paint(mix(CV_ROCK2, INK, 0.4), stroke=3))
        glowworms(cv, T, -300, 2300, -40, n=40, seed=seed + 3, L0=60, L1=300, rgb=P_["teal"], a=170)
        for k in range(9):
            sx = -100 + k * 260 + 50 * math.sin(k * 1.7)
            if 1250 < sx < 1750:
                continue
            stalac(cv, sx, -30 + 20 * math.sin(k), 120 + 120 * float(hsh(seed + k)), 40, [CV_ROCK2, mix(CV_ROCK2, P_["magenta"], 0.25)][k % 2], seed=seed + 10 + k, T=T)
        for k in range(6):
            crys(cv, 100 + k * 340 + 40 * math.sin(k * 2.2), 560 + 60 * math.sin(k * 1.4), 0.7, T, seed=seed + 30 + k)
    with C.layer(0.4):                                             # the fire and its light
        glow(cv, 960, 560, 900, P_["magenta"], a=int(22 * fire), n=3, sy=0.7, seed=seed + 40, T=T, flick=1.0)
        rays = skia.Path()
        for k in range(16):
            a0 = math.radians(T * 6 + k * 22.5)
            rays.moveTo(960, 560)
            rays.lineTo(960 + 1500 * math.cos(a0), 560 + 1500 * math.sin(a0))
            rays.lineTo(960 + 1500 * math.cos(a0 + 0.12), 560 + 1500 * math.sin(a0 + 0.12))
            rays.close()
        cv.drawPath(rays, paint(P_["orange"], int(24 * fire)))
        rock(cv, [(-400, 640), (600, 610), (1300, 630), (2400, 600), (2400, 1300), (-400, 1300)], seed=seed + 42, rgb=(60, 24, 104), strata=4, rim=None)
        glow(cv, 960, 700, 640, P_["orange"], a=int(30 * fire), n=4, sy=0.45, seed=seed + 43, T=T, flick=1.0)
        firelight(cv, 960, 560, 520, T, a=int(150 * fire), seed=seed + 44)
        if fire > 0.01:
            big_fire(cv, 960, 660, 1.45 * (0.6 + 0.4 * min(1.2, fire)), T, intensity=fire, seed=seed + 45)
        if "fire" in hooks:
            hooks["fire"](cv)
    with C.layer(0.6):                                             # carriers behind the low wall
        for k, cd in enumerate(carriers or []):
            cs = cd.get("s", 0.8)
            top = carrier2(cv, cd["x"], cd.get("y", 790), cs, T, holding=cd.get("kind", "horse"), seed=cd.get("seed", seed + 60 + k * 10),
                           phase=cd.get("phase", k * 0.7), face=cd.get("face", 1), raise_k=cd.get("raise", 1.0), walk=cd.get("walk", True), talk=cd.get("talk", 0.0),
                           statue_k=cd.get("statue_k", 1.35), back=0.0, rim=P_["orange"])
            sk = cd.get("statue_k", 1.35)
            if "veil" in cd:
                veil(cv, top[0], top[1] - 60 * cs * sk, cs * sk, cd["veil"], seed=seed + 70 + k * 3, T=T)
            if cd.get("burst", 0) > 0:
                burst(cv, top[0], top[1] - 60 * cs * sk, 150 * cs * sk, cd["burst"], seed=seed + 80 + k)
        if "carriers" in hooks:
            hooks["carriers"](cv)
    with C.layer(0.62):                                            # the low wall = the puppet screen
        top = 840 - 190 * wall_k
        blk = mix(CV_ROCK2, P_["maroon"], 0.35)

        def wsh(c):
            for k in range(26):
                xx = -380 + k * 110
                c.drawLine(xx, top + 30, xx - 4, 820, paint(mix(blk, INK, 0.45), stroke=3))
            for j in range(3):
                c.drawLine(-400, top + 60 + j * 46, 2400, top + 62 + j * 46, paint(mix(blk, INK, 0.4), stroke=2.5))
            c.drawRect(R(-400, top - 20, 2400, top + 26), paint(mix(blk, P_["orange"], 0.55)))
            c.drawRect(R(-400, top - 20, 2400, top + 6), paint(mix(P_["orange"], P_["yellow"], 0.4)))
            stip(c, mix(blk, INK, 0.5), (-400, top, 2400, 840), 16, 2.0, seed + 50, key="revwall")
        if wall_k > 0.01:
            blob(cv, rect_pts([(-420, top), (2420, top - 8), (2420, 850), (-420, 850)], 6), blk, w=6, seed=seed + 51, boil=1.0, n=3, shade=wsh)
        if wall_fx is not None:
            wall_fx(cv, top)
    with C.layer(1.0):                                             # the prisoners, facing us
        pl = prisoners if prisoners is not None else [dict() for _ in range(n_pris)]
        n = len(pl)
        xs = [190 + k * (1540 / max(1, n - 1)) for k in range(n)]
        for k, pd in enumerate(pl):
            px = pd.get("x", xs[k])
            py = pd.get("y", 1065 + 14 * (k % 2))
            pris(cv, px, py, pd.get("s", 1.15), T, seed=pd.get("seed", seed + 100 + k * 13), view="front", face=pd.get("face", 1.0), look=pd.get("look", (0.0, 0.1)),
                 anchor=pd.get("anchor", (px + 150, py + 6)), rim=pd.get("rim", P_["orange"]), mouth=pd.get("mouth", 0.0), eye_k=pd.get("eye_k", 1.0),
                 sparkle_k=pd.get("sparkle", 0.0), blink=pd.get("blink"), arms=pd.get("arms"), refl=pd.get("refl"), squash=pd.get("squash", (1.0, 1.0)),
                 refl_top=pd.get("refl_top"), mouth_low=True)
        if "front" in hooks:
            hooks["front"](cv)
    if fg:
        with C.layer(1.25):
            stalag(cv, -140, 1200, 380, 120, (26, 10, 48), seed=seed + 90, rim=P_["orange"])
            stalag(cv, 2080, 1210, 340, 110, (26, 10, 48), seed=seed + 91, rim=P_["magenta"])
    spores(cv, T, (0, 0, W, H), n=30, seed=seed + 95, size=1.1, a=200, rise=30)


# ===================================================================== THE GRAND CAVERN (establishing) + the shaft
def mini_tableau(cv, T, x, y, s, seed=5200):
    """The whole allegory set-up in miniature, far below (x, y = foot of the shadow wall; s = scale vs the cross-section)."""
    old = core.INKMUL
    core.INKMUL = old * 0.6
    cv.save(); cv.translate(x, y); cv.scale(s, s); cv.translate(-330, -900)
    wall = [(-40, 200), (330, 220), (360, 470), (330, 760), (300, 930), (-40, 930)]
    wall_surface(cv, wall, T, seed=seed + 1, cx=150, cy=560)
    cv.save(); cv.clipPath(poly_path(cr_closed(wall, 4)), doAntiAlias=True)
    for k in range(3):
        ph = (T * 0.07 + k / 3.0) % 1.0
        shadow_shape(cv, KINDS[(int(T * 0.07 + k / 3.0) * 3 + k) % len(KINDS)], 330 - ph * 420, 470 + 40 * math.sin(k), 1.0, T, seed=seed + 5 + k)
    cv.restore()
    cv.drawPath(poly_path(cr_closed([(-160, 905), (700, 880), (1500, 895), (2050, 880), (2050, 1000), (-160, 1000)], 4)), paint(mix((62, 26, 108), P_["orange"], 0.12)))
    glow(cv, 1520, 790, 520, P_["orange"], a=40, n=4, sy=0.7, seed=seed + 3, T=T, flick=1.0)
    cave_fire(cv, 1520, 880, 0.9, T, seed=seed + 4)
    for k in range(3):
        ph = (T * 0.07 + k / 3.0) % 1.0
        carrier(cv, 1380 - ph * 420, 890, 0.62, T, holding=KINDS[(int(T * 0.07 + k / 3.0) * 3 + k) % len(KINDS)], seed=seed + 20 + k * 7, phase=k * 0.7, face=-1)
    blob(cv, rect_pts([(960, 730), (1340, 730), (1350, 900), (950, 900)], 3), mix(CV_ROCK2, P_["maroon"], 0.3), w=6, seed=seed + 9, boil=0.8, n=3,
         shade=lambda c: c.drawRect(R(950, 730, 1350, 754), paint(mix(CV_ROCK2, P_["orange"], 0.45))))
    for k in range(6):
        px = 430 + k * 95
        pris(cv, px, 930 + (k % 2) * 24, 0.62, T, seed=seed + 40 + k * 13, view="side", face=-1, look=(-1, 0), anchor=(px + 70, 942 + (k % 2) * 24))
    cv.restore()
    core.INKMUL = old


def cave_mouth(cv, x, y, s, T, seed=5050):
    """An irregular opening in the rock with the blinding outside world beyond (sky, green hills, a sun-glare)."""
    mouth = [(x - 110 * s, y - 70 * s), (x - 20 * s, y - 120 * s), (x + 90 * s, y - 100 * s), (x + 140 * s, y), (x + 120 * s, y + 120 * s), (x + 20 * s, y + 150 * s),
             (x - 90 * s, y + 130 * s), (x - 150 * s, y + 30 * s)]
    mp = poly_path(cr_closed(jit(mouth, 1.0, seed), 4))
    cv.save(); cv.clipPath(mp, doAntiAlias=True)
    cv.drawRect(R(x - 200 * s, y - 200 * s, x + 200 * s, y + 200 * s), paint((170, 225, 255)))
    blob(cv, [(x - 220 * s, y + 100 * s), (x - 60 * s, y + 66 * s), (x + 60 * s, y + 86 * s), (x + 220 * s, y + 56 * s), (x + 220 * s, y + 220 * s), (x - 220 * s, y + 220 * s)],
         P_["mint"], w=3, seed=seed + 1, boil=0.6, n=4)
    soft(cv, x + 10 * s, y - 10 * s, 200 * s, P_["white"], a=255)
    soft(cv, x + 10 * s, y - 10 * s, 110 * s, P_["white"], a=255)
    cv.restore()
    brush(cv, cr_closed(jit(mouth, 1.0, seed), 4), 6, closed=True, seed=seed + 2)
    for k in range(5):                                             # teeth of rock on the lip
        tx = x - 90 * s + k * 50 * s
        ty = y - 110 * s + 20 * s * math.sin(k * 1.7)
        blob(cv, [(tx - 16 * s, ty - 10 * s), (tx + 16 * s, ty - 10 * s), (tx + 2 * s, ty + (40 + 30 * (k % 2)) * s)], (46, 18, 84), w=3.5, seed=seed + 5 + k, boil=0.6, n=2)
    sun_rays(cv, x, y, 1300 * s, T, n=8, a=55, ang0=150, span=55)


def wing(cv, side, x_edge, y_top, y_bot, rgb, rim, seed, T, crys_y=None, mush_y=None, depth=1.0):
    """A theatre-wing of cave rock on one side of the frame (side -1 left / +1 right): bulging inner edge, neon rim,
    strata, crystals and glowing mushrooms."""
    xo = x_edge
    far = x_edge + side * 1400
    pts = [(far, y_top - 400), (xo + side * 60, y_top - 400), (xo - side * 40, y_top), (xo + side * 70, y_top + (y_bot - y_top) * 0.3), (xo - side * 90, y_top + (y_bot - y_top) * 0.55),
           (xo + side * 20, y_top + (y_bot - y_top) * 0.8), (xo - side * 60, y_bot), (far, y_bot + 400)]
    rock(cv, pts, seed=seed, rgb=rgb, rim=rim, rim_side=-side, ink=5.5 * depth ** 0.3, strata=8,
         agate=(xo + side * 260, (y_top + y_bot) / 2, 340, 4, mix(rgb, P_["violet"], 0.35)))
    if crys_y is not None:
        crys(cv, xo - side * 30, crys_y, 1.1, T, seed=seed + 7, ang0=-side * 70)
    if mush_y is not None:
        for k in range(3):
            glow_mushroom(cv, xo - side * (40 + k * 70), mush_y + 10 * (k % 2), 1.2 - 0.2 * k, T, seed=seed + 9 + k)


def grand(cv, T, cam=None, seed=5000):
    """THE IMMENSE CAVERN, high up (multiplane): glow-worm 'night sky' on the vault, the hole we fell through with shafts
    of light, the blinding mouth in the far wall, the floor far below with the tiny lit tableau (layer 0.45, prisoners
    around x=960, y=505), rock wings and stalactite bands parting in front as the camera cranes down and pushes in."""
    C = sets.Cam(cv, cam or dict(x=0, y=0, z=1.0))
    with C.layer(0.1):
        w.field(cv, CV_ROCK_DK)
        glow(cv, 960, 700, 1400, (84, 28, 128), a=46, n=5, sy=0.55, seed=seed + 1)
        w.stars(cv, seed + 2, (-600, -1000, 2500, 520), n=520, colors=[P_["teal"], P_["mint"], P_["acid"], P_["hotpink"], P_["cream"]], big=16, rmax=2.8)
        for k, (cx, wd) in enumerate(((380, 80), (1450, 110))):     # far columns, lost in the dark
            pts = [(cx - wd * 1.5, -1400), (cx + wd * 1.5, -1400), (cx + wd * 0.5, -300), (cx + wd * 0.6, 300), (cx + wd * 1.5, 640), (cx - wd * 1.5, 640),
                   (cx - wd * 0.6, 300), (cx - wd * 0.5, -300)]
            blob(cv, pts, (34, 14, 66), w=3, seed=seed + 5 + k, boil=0.8, n=4,
                 shade=lambda c, cx=cx, wd=wd: c.drawRect(R(cx - wd * 2, -1500, cx - wd * 0.2, 800), paint((50, 20, 92))))
        pts = [(-700, 1400)] + [(-700 + j * 170, 460 - 110 * float(hsh(seed + j * 3.1)) - 50 * math.sin(j * 0.8)) for j in range(22)] + [(3000, 1400)]
        blob(cv, pts, (42, 16, 80), w=3.5, seed=seed + 9, boil=0.8, n=3)
    with C.layer(0.25):
        rays = skia.Path()                                         # shafts from the ceiling hole we fell through
        for k in range(9):
            a0 = math.radians(64 + k * 6.5 + 1.5 * math.sin(T * 0.4 + k))
            rays.moveTo(900, -420); rays.lineTo(900 + 2600 * math.cos(a0), -420 + 2600 * math.sin(a0))
            rays.lineTo(900 + 2600 * math.cos(a0 + 0.05), -420 + 2600 * math.sin(a0 + 0.05)); rays.close()
        cv.drawPath(rays, paint(P_["yellow"], 16))
        glow(cv, 900, -420, 300, P_["yellow"], a=55, n=4, sy=0.35, seed=seed + 12)
        blob(cv, ell(900, -420, 170, 46, n=12), P_["white"], w=5, seed=seed + 13, boil=1.0)
        rock(cv, [(1360, -1200), (2800, -1200), (2800, 700), (1500, 700), (1440, 420), (1520, 120), (1400, -300)], seed=seed + 14, rgb=(44, 18, 82), rim=P_["orange"],
             rim_side=-1, strata=8)
        cave_mouth(cv, 1720, 200, 1.0, T, seed=seed + 15)
        stalac(cv, 1180, -1400, 1080, 80, mix(CV_ROCK2, P_["magenta"], 0.2), seed=seed + 38, T=T, ink=4.5)
        glowworms(cv, T, 200, 1500, -760, n=46, seed=seed + 40, L0=160, L1=560, rgb=P_["teal"], a=170)
    with C.layer(0.45):                                            # the cavern floor far below with the tableau
        blob(cv, [(-700, 540), (200, 505), (900, 525), (1500, 500), (2700, 520), (2700, 1500), (-700, 1500)], (62, 26, 108), w=4.5, seed=seed + 50, boil=0.8, n=4,
             shade=lambda c: (c.drawRect(R(-700, 505, 2700, 532), paint(mix((62, 26, 108), P_["orange"], 0.35))),
                              stip(c, (44, 18, 80), (-700, 520, 2700, 1500), 14, 2.0, seed + 51, key="gfloor")))
        glow(cv, 1190, 540, 520, P_["orange"], a=26, n=4, sy=0.35, seed=seed + 52, T=T, flick=1.0)
        for k in range(16):                                        # stalagmites + crystals across the floor
            fx = -400 + k * 190 + 60 * math.sin(k * 2.7)
            if 640 < fx < 1560:
                continue
            fy = 560 + 120 * float(hsh(seed + k * 1.9))
            if k % 3 == 0:
                crys(cv, fx, fy, 0.6, T, seed=seed + 140 + k)
            else:
                stalag(cv, fx, fy, 70 + 150 * float(hsh(seed + k * 2.3)), 24 + 12 * float(hsh(seed + k)), [(70, 28, 120), (88, 36, 146)][k % 2], seed=seed + 160 + k,
                       ink=3.5, rim=P_["magenta"] if k % 2 else P_["orange"])
        mini_tableau(cv, T, 870, 520, 0.27, seed=seed + 60)
        for k in range(2):                                         # mist
            yy = 480 + k * 50 + 10 * math.sin(T * 0.5 + k)
            cv.drawPath(poly_path(cr_closed([(-700, yy), (500, yy - 30), (1300, yy + 10), (2700, yy - 20), (2700, yy + 50), (1300, yy + 70), (500, yy + 40), (-700, yy + 60)], 4)),
                        paint(P_["lilac"], 16))
    with C.layer(0.6):
        wing(cv, -1, 330, -500, 900, (50, 20, 92), P_["magenta"], seed + 200, T, crys_y=240, mush_y=860)
        wing(cv, 1, 1640, -400, 900, (46, 18, 86), P_["orange"], seed + 220, T, crys_y=380, mush_y=880)
        for k in range(6):                                         # stalactite band
            sx = 260 + k * 290 + 50 * math.sin(k * 2.1)
            stalac(cv, sx, -760, 300 + 220 * float(hsh(seed + k * 3.3)), 56 + 20 * float(hsh(seed + k)), [CV_ROCK2, mix(CV_ROCK2, P_["magenta"], 0.3)][k % 2],
                   seed=seed + 70 + k, T=T, ink=5)
        blob(cv, [(-400, -1300), (2400, -1300), (2400, -720), (1500, -760), (900, -700), (300, -780), (-400, -700)], (40, 16, 74), w=5, seed=seed + 69, boil=1.0, n=4)
        glowworms(cv, T, 300, 1700, -740, n=26, seed=seed + 80, L0=180, L1=460, rgb=P_["acid"], a=200)
        w.eye_bat(cv, 1180 + 260 * math.sin(T * 0.45), -260 + 50 * math.sin(T * 1.1), 0.8, T * 2.2, seed=seed + 90)
    with C.layer(0.85):
        wing(cv, -1, 60, -700, 1100, (38, 14, 70), P_["teal"], seed + 240, T, crys_y=420, mush_y=1060)
        wing(cv, 1, 1880, -600, 1100, (36, 14, 68), P_["magenta"], seed + 260, T, crys_y=520, mush_y=1070)
        w.eye_bat(cv, 520 + 160 * math.sin(T * 0.37 + 2), -380 + 40 * math.sin(T * 0.9), 0.75, T * 2.5, seed=seed + 91)
    with C.layer(1.1):
        stalac(cv, -60, -1100, 900, 230, (30, 10, 56), seed=seed + 100, T=T, ink=6)
        stalac(cv, 210, -1100, 640, 120, (38, 14, 70), seed=seed + 104, T=T, ink=5)
        stalac(cv, 1990, -1100, 860, 220, (30, 10, 56), seed=seed + 101, T=T, ink=6)
        crys(cv, 90, -420, 1.3, T, seed=seed + 102, ang0=160)
        rock(cv, [(-700, 760), (40, 690), (380, 740), (640, 900), (700, 1600), (-700, 1600)], seed=seed + 103, rgb=(30, 10, 56), rim=P_["magenta"], strata=4)
        for k in range(4):
            glow_mushroom(cv, 0 + k * 120, 720 + 18 * (k % 2), 1.6 - 0.15 * k, T, seed=seed + 110 + k)
        crys(cv, 1980, 900, 1.6, T, seed=seed + 115, ang0=-30)
    spores(cv, T, (0, 0, W, H), n=40, seed=seed + 120, cols=[P_["mint"], P_["teal"], P_["yellow"]], size=1.2, a=200, rise=14, drift=30)


def shaft(cv, t, T, seed=5300):
    """Falling down a narrow crystal shaft (looking down): banded rock rings rush outward, crystals and spikes streak
    past, speed lines, the light of the cavern growing at the bottom like a sun. Returns the light-disc radius."""
    zc = 1.2 * t + 1.9 * t * t
    zend = 1.2 * 1.55 + 1.9 * 1.55 ** 2 + 0.55
    cx = 960 + 30 * math.sin(t * 7.0)
    cy = 560 + 22 * math.cos(t * 5.0)
    roll = -40 * t - 12 * t * t
    w.field(cv, (8, 3, 18))
    R0 = 520.0
    dl = max(0.05, zend - zc)
    rl = min(R0 / dl * 0.9, 820.0)
    cv.save(); cv.translate(cx, cy); cv.rotate(roll)
    w.sunburst(cv, 0, 0, max(rl * 2.2, 2400 if rl >= 819 else 0), 20, [P_["orange"], P_["magenta"]], rot_deg=t * 90, seed=seed)
    for k in range(4, 0, -1):                                      # the light at the bottom
        cv.drawCircle(0, 0, rl * (0.55 + 0.22 * k), paint([P_["magenta"], P_["orange"], P_["yellow"], P_["cream"]][4 - k], 255))
    cv.drawCircle(0, 0, rl * 0.55, paint(P_["white"]))
    ring_cols = [(84, 30, 140), (40, 14, 74), (120, 36, 150), (30, 10, 58), (70, 24, 120), (50, 18, 92)]
    k0 = int(math.floor(zc / 0.42))
    rings = []
    for k in range(k0 + 1, k0 + 30):
        zk = k * 0.42
        if zk >= zend:
            break
        dz = zk - zc
        if dz <= 0.08:
            continue
        rings.append((k, dz))
    for k, dz in sorted(rings, key=lambda q: -q[1]):
        rr = R0 / dz
        if rr > 4200:
            continue
        nP = 22
        ang = np.linspace(0, 2 * math.pi, nP, endpoint=False) + k * 0.7
        mod = 1 + 0.15 * np.sin(3 * ang + k * 1.3) + 0.08 * np.sin(5 * ang + k * 2.1) + 0.06 * (hsh(k * 7.1 + np.arange(nP) * 1.3) - 0.5)
        P = np.stack([rr * mod * np.cos(ang), rr * mod * np.sin(ang)], 1)
        inner = cr_closed(jit(P, rr * 0.006, seed + k), 4)
        fog = float(np.clip(1.0 - dz / 10.0, 0, 1))
        base = ring_cols[k % len(ring_cols)]
        col = mix(mix(base, P_["magenta"], 0.5 * (1 - fog) ** 2), (14, 5, 28), 0.5 * fog ** 3)
        path = skia.Path()
        path.addRect(R(-6000, -6000, 6000, 6000))
        path.addPoly([skia.Point(float(a), float(b)) for a, b in inner], True)
        path.setFillType(skia.PathFillType.kEvenOdd)
        cv.drawPath(path, paint(col))
        band = inner * 1.07                                         # strata band just behind the lip
        brush(cv, band, max(2.0, min(22.0, rr * 0.03)), mix(col, INK, 0.35), closed=True, seed=seed + 20 + k, a=200)
        rim = P_["orange"] if k % 3 == 0 else (P_["magenta"] if k % 3 == 1 else P_["teal"])
        brush(cv, inner * 1.018, max(2.5, min(30.0, rr * 0.04)), mix(rim, col, 0.25), closed=True, seed=seed + 30 + k, a=int(230 * (1 - 0.5 * fog)))
        brush(cv, inner, max(2.5, min(16.0, rr * 0.013)), INK, closed=True, seed=seed + 40 + k)
        for j in range(3):                                         # crystals / spikes pointing inward
            a0 = k * 2.3 + j * 2.1
            mm = 1 + 0.15 * math.sin(3 * a0 + k * 1.3) + 0.08 * math.sin(5 * a0 + k * 2.1)
            bx, by = rr * mm * math.cos(a0) * 1.01, rr * mm * math.sin(a0) * 1.01
            L = rr * (0.3 if j == 0 else 0.17)
            tipx, tipy = bx - L * math.cos(a0), by - L * math.sin(a0)
            nx, ny = -math.sin(a0) * rr * (0.07 if j == 0 else 0.05), math.cos(a0) * rr * (0.07 if j == 0 else 0.05)
            ccol = [P_["teal"], P_["hotpink"], P_["acid"], P_["lilac"]][(k + j) % 4] if j != 2 else mix(col, P_["lilac"], 0.35)
            if j == 0 and rr < 3000:
                glow(cv, (bx + tipx) / 2, (by + tipy) / 2, rr * 0.2, ccol, a=45, n=2, seed=seed + k)
            blob(cv, [(bx + nx, by + ny), (tipx, tipy), (bx - nx, by - ny)], ccol, w=max(2.5, min(9.0, rr * 0.011)), seed=seed + 60 + k * 3 + j, boil=0.6, n=3,
                 shade=lambda c, bx=bx, by=by, tipx=tipx, tipy=tipy, nx=nx, ny=ny: c.drawPath(poly_path([(bx, by), (tipx, tipy), (bx + nx, by + ny)]), paint(P_["white"], 100)))
    cv.restore()
    speed_lines(cv, cx, cy, 70, 260, 1300, seed=seed + 90, rgb=P_["cream"], a=120, w=3.0)
    speed_lines(cv, cx, cy, 30, 420, 1300, seed=seed + 91, rgb=P_["teal"], a=150, w=4.5)
    return rl


def title_card(cv, t, t0, x=960, y=500, size=270, seed=5400, a=1.0, out=0.0):
    """THE CAVE: shrik, orange/yellow letters, magenta shadow, drips, with echo copies rippling outward behind it."""
    if t < t0 or a <= 0.01:
        return
    rv = float(np.clip((t - t0) / 0.45, 0, 1))
    cx, cy = x, y - size * 0.34
    for i in range(3):                                             # the echo: copies ripple outward and fade, again and again
        ph = ((t - t0 - 0.2) / 0.9 + i / 3.0)
        if ph < 0:
            continue
        ph = ph % 1.0
        sc = 1.0 + 0.3 * ph + out * 0.5
        al = int(200 * (1 - ph) ** 1.5 * min(1.0, (t - t0 - 0.2) * 3) * a)
        if al < 8:
            continue
        cv.save(); cv.translate(cx, cy); cv.scale(sc, sc); cv.translate(-cx, -cy)
        paint_text(cv, "THE CAVE", x, y, font="shrik", size=size, fill=[P_["magenta"], P_["violet"], P_["teal"]][i], ink_w=0, shadow=None, seed=seed + 10 + i,
                   wobble=3.0, streaks=False, a=al, step=9.0)
        cv.restore()
    sc = 1.0 + 0.04 * math.sin(t * 3.0) + out * 0.25
    cv.save(); cv.translate(cx, cy); cv.scale(sc, sc); cv.translate(-cx, -cy)
    paint_text(cv, "THE CAVE", x, y, font="shrik", size=size, fills=[P_["orange"], P_["yellow"]], ink_w=8, shadow=(12, 12), shadow_rgb=P_["magenta"], seed=seed,
               wobble=2.6, reveal=rv, stagger=0.09, drips=1.3, a=int(255 * a))
    cv.restore()


# ===================================================================== T011  CAVE_IN
GRAND_KEYS_011 = [(1.62, (40, -1000, 0.92)), (2.5, (16, -700, 0.98)), (3.27, (0, -600, 1.0))]


def T011_cave_in(cv, t, T, A):
    if t < 1.62:                                                   # the fall down the shaft
        rl = shaft(cv, t, T)
        darkness(cv, 255 * (1 - kin(t, 0.0, 0.3)) * 0.85)
        if t > 1.45:
            flash(cv, kin(t, 1.45, 0.17) * 0.3, P_["white"])
        return
    cam = camk(t, GRAND_KEYS_011)
    cam["rot"] = 9.0 * (1 - kin(t, 1.62, 1.2))
    grand(cv, T, cam)
    if t < 2.3:                                                    # still falling: vertical streaks
        hlines(cv, 40, seed=5500, rgb=P_["cream"], a=int(130 * (1 - kin(t, 1.62, 0.65))), w=3.5, vertical=True)
    flash(cv, 0.6 * (1 - kin(t, 1.62, 0.35)), P_["white"])
    title_card(cv, t, 1.95)
    vignette(cv, a=130)


# ===================================================================== close-ups (T012)
CU_X = (330, 960, 1590)          # three prisoners of the row, big (s=2.4), floor at y=1000, facing the wall (left)
CU_S = 2.4
CU_Y = 1000


def cu_world(cv, T, cam, seed=5600, pl=None, hooks=None):
    """Close-up set: three prisoners at s=2.4 on the floor, warm wall-light from the left, dark bokeh cave behind."""
    hooks = hooks or {}
    C = sets.Cam(cv, cam)
    with C.layer(0.35):
        w.field(cv, (30, 12, 58))
        glow(cv, -200, 600, 1300, P_["orange"], a=34, n=5, sy=0.9, seed=seed + 1, T=T, flick=1.0)
        rock(cv, [(-600, -400), (2600, -400), (2600, 300), (1700, 360), (900, 300), (200, 380), (-600, 320)], seed=seed + 2, rgb=(42, 16, 78), strata=4, rim=P_["magenta"])
        for k in range(9):                                         # bokeh crystals
            bx = -200 + k * 300 + 80 * math.sin(k * 2.3)
            by = 420 + 260 * float(hsh(seed + k * 1.7))
            col = [P_["teal"], P_["hotpink"], P_["acid"], P_["lilac"]][k % 4]
            rr = 50 + 50 * float(hsh(seed + k * 2.9))
            dots(cv, [(bx, by)], rr, col, a=40)
            dots(cv, [(bx, by)], rr * 0.55, col, a=50)
        glowworms(cv, T, -400, 2400, 250, n=30, seed=seed + 3, L0=60, L1=220, rgb=P_["teal"], a=170)
    with C.layer(0.7):
        soft(cv, -350, 760, 1250, P_["orange"], a=150)
        crys(cv, -40, 980, 1.6, T, seed=seed + 4, ang0=40)
        crys(cv, 2020, 990, 1.5, T, seed=seed + 5, ang0=-40)
    with C.layer(1.0):
        blob(cv, [(-500, 990), (800, 975), (1800, 990), (2600, 980), (2600, 1700), (-500, 1700)], CV_ROCK2, w=6, seed=seed + 6, boil=1.0, n=4,
             shade=lambda c: (c.drawRect(R(-500, 975, 2600, 1000), paint(mix(CV_ROCK2, P_["orange"], 0.4))),
                              stip(c, mix(CV_ROCK2, INK, 0.35), (-500, 990, 2600, 1700), 16, 2.6, seed + 7, key="cufloor")))
        for k in range(10):
            px = -300 + k * 290 + 60 * math.sin(k * 2.2)
            blob(cv, ell(px, 1090 + 70 * float(hsh(seed + k)), 40 + 20 * float(hsh(seed + k * 3)), 18 + 8 * float(hsh(seed + k * 5)), n=8), mix(CV_ROCK2, P_["lilac"], 0.25),
                 w=4, seed=seed + 20 + k, boil=0.6)
        for k, x in enumerate(CU_X):
            pd = (pl or [{}, {}, {}])[k]
            if pd is None:
                continue
            pris(cv, x, CU_Y, CU_S, T, seed=pd.get("seed", 4100 + k * 13), view="side", face=pd.get("face", -1.0), look=pd.get("look", (-1, 0)),
                 anchor=pd.get("anchor", (x + 330, CU_Y + 18)), glow_k=0.0, sag=pd.get("sag"), veins=pd.get("veins", 0.0), squash=pd.get("squash", (1.0, 1.0)),
                 rim=P_["orange"], feet=True, detail=True, eye_k=pd.get("eye_k", 1.0), blink=pd.get("blink"), mouth=pd.get("mouth", 0.0), shake=pd.get("shake", 0.0),
                 sparkle_k=pd.get("sparkle", 0.0), rim_dir=(-1.0, -0.25))
        if "front" in hooks:
            hooks["front"](cv)
    spores(cv, T, (0, 0, W, H), n=24, seed=seed + 30, size=1.6, a=190, rise=16)


def baby_pris(cv, x, y, s, T, seed=5700, bonnet=None, look=-1.0, paci=True, bonnet_on=1.0, bon_fly=0.0):
    """A baby prisoner: rounder, huge sparkly eye, frilly bonnet, pacifier, a tiny collar on a tiny ball-and-chain."""
    rgb = [(64, 30, 110), (90, 40, 150), (46, 20, 86), (110, 50, 120)][int(hsh(seed) * 4)]
    bonnet = bonnet or [P_["hotpink"], (150, 210, 255), P_["mint"], P_["peach"]][int(hsh(seed + 2) * 4)]
    r = 70 * s
    bob = 3 * math.sin(T * 2.4 + seed) * s
    cx, cy = x, y - r * 0.95 + bob
    blob(cv, ell(cx, cy, r * 0.98, r * 0.92, n=12), rgb, w=4.5, seed=seed, boil=0.9,
         shade=lambda c: c.drawPath(poly_path(cr_closed(ell(cx + r * 0.35, cy + r * 0.25, r * 0.8, r * 0.8, n=10), 3)), paint(mix(rgb, INK, 0.28))))
    for k in range(2):                                             # cheeks
        dots(cv, [(cx - r * 0.55, cy + r * 0.32)], r * 0.13, P_["hotpink"], a=150)
    ex, ey = cx - r * 0.3, cy - r * 0.05
    er = r * 0.5
    blob(cv, ell(ex, ey, er, er * 1.06, n=10), P_["white"], w=4, seed=seed + 3, boil=0.6)
    ix, iy = ex + look * er * 0.32, ey + er * 0.05
    dots(cv, [(ix, iy)], er * 0.62, [(200, 255, 230), (255, 200, 240), (255, 240, 170), (190, 220, 255)][int(hsh(seed + 1) * 4)])
    dots(cv, [(ix, iy)], er * 0.33, INK)
    dots(cv, [(ix - er * 0.18, iy - er * 0.22)], er * 0.14, P_["white"])
    dots(cv, [(ix + er * 0.16, iy + er * 0.14)], er * 0.07, P_["white"])
    if paci:
        px_, py_ = cx - r * 0.82, cy + r * 0.42
        blob(cv, ell(px_, py_, r * 0.1, r * 0.2, n=8), P_["cream"], w=3, seed=seed + 4, boil=0.5)
        cv.drawCircle(px_ - r * 0.14, py_, r * 0.1, paint(INK, stroke=4.5))
        cv.drawCircle(px_ - r * 0.14, py_, r * 0.1, paint(P_["hotpink"], stroke=2.5))
    ny = cy + r * 0.62                                             # tiny collar + ball and chain
    blob(cv, ell(cx, ny, r * 0.72, r * 0.12, n=10), (140, 140, 170), w=3, seed=seed + 5, boil=0.5)
    bx, by = cx + r * 1.6, y - r * 0.18
    chain(cv, (cx + r * 0.6, ny + r * 0.05), (bx - r * 0.2, by), seed=seed + 6, link=max(6.0, 10 * s), sag=8 * s, w=max(1.4, 2.0 * s))
    blob(cv, ell(bx, by, r * 0.24, r * 0.24, n=9), (70, 70, 95), w=3.5, seed=seed + 7, boil=0.5,
         shade=lambda c: dots(c, [(bx - r * 0.08, by - r * 0.08)], r * 0.06, (170, 170, 200)))
    if bonnet_on > 0.01:                                           # the frilly bonnet (can fly off)
        cv.save()
        if bon_fly > 0:
            cv.translate(cx + r * 0.6 * bon_fly, cy - r * 2.6 * bon_fly); cv.rotate(260 * bon_fly); cv.translate(-cx, -cy)
        bpts = [(cx - r * 0.55, cy - r * 0.78), (cx - r * 0.05, cy - r * 1.06), (cx + r * 0.6, cy - r * 0.86), (cx + r * 1.06, cy - r * 0.2), (cx + r * 0.9, cy + r * 0.45),
                (cx + r * 0.62, cy + r * 0.2), (cx + r * 0.58, cy - r * 0.3), (cx + r * 0.2, cy - r * 0.62), (cx - r * 0.4, cy - r * 0.6)]
        frill = []
        for k in range(7):
            u = k / 6
            frill.append((cx - r * 0.5 + u * r * 1.3 + r * 0.1 * math.sin(u * 3), cy - r * 0.72 + u * u * r * 1.0))
        for k, (fx, fy) in enumerate(frill):
            blob(cv, ell(fx, fy, r * 0.13, r * 0.13, n=8), P_["white"], w=2.5, seed=seed + 30 + k, boil=0.5)
        blob(cv, bpts, bonnet, w=4, seed=seed + 8, boil=0.7, n=4,
             shade=lambda c: [c.drawLine(cx - r * 0.2 + k * r * 0.3, cy - r * 1.1, cx + r * 0.3 + k * r * 0.25, cy + r * 0.4, paint(mix(bonnet, P_["white"], 0.4), stroke=3)) for k in range(4)])
        if bon_fly <= 0:
            for side in (-1, 1):                                   # the bow under the 'chin'
                blob(cv, [(cx + r * 0.75, cy + r * 0.5), (cx + r * 0.75 + side * r * 0.3, cy + r * 0.38), (cx + r * 0.75 + side * r * 0.3, cy + r * 0.66)], bonnet, w=3,
                     seed=seed + 40 + side, boil=0.5, n=3)
        cv.restore()


def baby_inset(cv, T, t, t0, t1, cx=1250, cy=460, R0=360, seed=5800):
    """'since they were children': a round memory vignette - babies in bonnets watching a tiny shadow, then POOF, all
    grown up (one keeps his bonnet)."""
    k = pop(t, t0, 0.4) * (1.0 - ease((t - (t1 - 0.3)) / 0.3))
    if k <= 0.01:
        return
    lt = t - t0
    grow_t = 1.35                                                  # babies -> adults
    gk = float(np.clip((lt - grow_t) / 0.3, 0, 1))
    cv.save(); cv.translate(cx, cy); cv.scale(k, k); cv.translate(-cx, -cy)
    for j, (dx, dy, rr) in enumerate(((-R0 * 0.78, R0 * 0.86, 34), (-R0 * 1.0, R0 * 1.12, 22), (-R0 * 1.13, R0 * 1.3, 13))):
        blob(cv, ell(cx + dx, cy + dy, rr, rr * 0.85, n=8), P_["cream"], w=4.5, seed=seed + 1 + j, boil=0.8)
    scal = []
    for j in range(24):
        a_ = j / 24 * 2 * math.pi
        rad = R0 * (1.0 + 0.045 * math.sin(a_ * 8 + t * 2))
        scal.append((cx + rad * math.cos(a_), cy + rad * math.sin(a_)))
    blob(cv, [(x_ + (x_ - cx) * 0.06, y_ + (y_ - cy) * 0.06) for x_, y_ in scal], P_["magenta"], w=6, seed=seed + 5, boil=1.0, n=4)
    clip = poly_path(cr_closed(jit(scal, 0.8, seed + 6), 4))
    cv.save(); cv.clipPath(clip, doAntiAlias=True)
    grown = gk >= 0.5
    cv.drawRect(R(cx - R0 - 20, cy - R0 - 20, cx + R0 + 20, cy + R0 + 20), paint((255, 196, 220) if not grown else (150, 64, 150)))
    soft(cv, cx - R0 * 0.6, cy + R0 * 0.1, R0 * 1.3, P_["orange"] if grown else P_["yellow"], a=190 if grown else 150)
    for j in range(10):
        sparkle(cv, cx - R0 + (j * 197) % (2 * R0), cy - R0 * 0.85 + (j * 131) % int(R0 * 0.9), 7 + 4 * (j % 3), P_["white"] if not grown else P_["yellow"], w=1.5,
                seed=seed + 10 + j, a=200)
    wx0 = cx - R0 * 0.95                                           # their little wall with a little shadow on it
    wall_surface(cv, [(wx0 - 60, cy - R0), (wx0 + 120, cy - R0), (wx0 + 140, cy + R0 * 0.2), (wx0 + 120, cy + R0), (wx0 - 60, cy + R0)], T, seed=seed + 12,
                 cx=wx0 + 40, cy=cy - 40)
    shadow_shape(cv, "bunny" if not grown else "horse", wx0 + 60 + 10 * math.sin(T * 2), cy - R0 * 0.2, 0.55, T, seed=seed + 13)
    fy = cy + R0 * 0.48
    cv.drawRect(R(cx - R0 - 20, fy, cx + R0 + 20, cy + R0 + 20), paint((150, 80, 170) if not grown else (120, 70, 180)))
    brush(cv, cr_open([(cx - R0, fy), (cx, fy - 6), (cx + R0, fy)], 6), 5, seed=seed + 14)
    if not grown:                                                  # the mobile over the cot
        mx, my = cx + R0 * 0.15, cy - R0 * 0.62
        line(cv, [(mx, cy - R0), (mx, my)], 3, seed=seed + 15, boil=0.4, n=2)
        line(cv, [(mx - 170, my + 10), (mx, my - 6), (mx + 170, my + 10)], 4, (200, 150, 90), seed=seed + 16, boil=0.5, n=4)
        for j, kind in enumerate(("bunny", "star", "horse")):
            hx = mx - 160 + j * 160
            sw = 10 * math.sin(T * 1.6 + j)
            line(cv, [(hx, my + 8), (hx + sw, my + 60)], 2, seed=seed + 17 + j, boil=0.4, n=2)
            shadow_shape(cv, kind, hx + sw, my + 100, 0.32, T, rgb=[P_["violet"], P_["gold"], P_["teal"]][j], a=255, seed=seed + 20 + j, outline=True)
    n = 4
    for j in range(n):
        bx = cx - R0 * 0.4 + j * R0 * 0.42
        if not grown:
            baby_pris(cv, bx, fy + 22, 1.12, T, seed=seed + 40 + j * 7, look=-1.0)
        else:
            ak = pop(lt, grow_t + 0.15, 0.35)
            keep = j == 2
            sc = 0.75 + 0.3 * ak
            pris(cv, bx + 10, fy + 26, sc, T, seed=seed + 60 + j * 13, view="side", face=-1, look=(-1, 0), anchor=(bx + 80, fy + 34), glow_k=0.0, rim=P_["orange"],
                 rim_dir=(-1.0, -0.2), rgb=[(110, 50, 170), (130, 60, 190), (96, 44, 160), (140, 60, 150)][j])
            if keep:
                cv.save(); cv.translate(bx + 10, fy + 26 - 70 * sc * 1.4); cv.scale(sc * 0.9, sc * 0.9); cv.translate(-(bx + 10), -(fy + 26 - 70 * sc * 1.4))
                bpx, bpy = bx + 10, fy + 26 - 70 * sc * 1.4
                bp = [(bpx - 40, bpy - 50), (bpx + 10, bpy - 74), (bpx + 60, bpy - 56), (bpx + 80, bpy - 10), (bpx + 50, bpy - 20), (bpx + 20, bpy - 46), (bpx - 30, bpy - 40)]
                blob(cv, bp, P_["mint"], w=3.5, seed=seed + 90, boil=0.6, n=4)
                for q in range(5):
                    blob(cv, ell(bpx - 36 + q * 18, bpy - 44 - 6 * math.sin(q), 8, 8, n=7), P_["white"], w=2, seed=seed + 91 + q, boil=0.4)
                cv.restore()
        if 0.0 < gk < 1.0 or (grown and lt < grow_t + 0.6):        # POOF + flying bonnets
            u = float(np.clip((lt - grow_t) / 0.6, 0, 1))
            for q in range(7):
                a_ = q / 7 * 2 * math.pi + j
                rr = 40 + 70 * u
                blob(cv, ell(bx + rr * math.cos(a_), fy - 70 + rr * 0.7 * math.sin(a_), 30 * (1 - u) + 8, 26 * (1 - u) + 7, n=8), P_["white"], w=3, seed=seed + 100 + j * 9 + q,
                     boil=0.8, a=int(255 * (1 - u)))
            if j != 2:
                bpx, bpy = bx + 40 * u * (1 if j % 2 else -1), fy - 120 - 260 * u
                cv.save(); cv.translate(bpx, bpy); cv.rotate(300 * u * (1 if j % 2 else -1))
                blob(cv, [(-40, -10), (0, -36), (44, -16), (54, 20), (30, 8), (0, -10), (-30, 0)], [P_["hotpink"], (150, 210, 255), P_["mint"], P_["peach"]][j % 4], w=3.5,
                     seed=seed + 120 + j, boil=0.6, n=4)
                cv.restore()
    cv.restore()
    brush(cv, cr_closed(jit(scal, 0.8, seed + 6), 4), 7, closed=True, seed=seed + 7)
    lab = "THEN" if not grown else "NOW"
    blob(cv, rect_pts([(cx - 120, cy + R0 - 34), (cx + 120, cy + R0 - 44), (cx + 132, cy + R0 + 30), (cx - 128, cy + R0 + 38)], 3), P_["yellow"], w=5, seed=seed + 8, boil=0.8, n=3)
    paint_text(cv, lab, cx, cy + R0 + 20, font="bangers", size=58, fill=P_["magenta"], ink_w=4, shadow=(3, 3), seed=seed + 9)
    cv.restore()


def big_eye(cv, T, cx, cy, R0, seed=5900, look=(-1.0, 0.0), refl_t=0.0, blink=0.0, body=(90, 40, 150), eye_rgb=(200, 255, 230)):
    """Extreme close-up of a prisoner's eye: purple skin lit by the wall, wet sclera, a psychedelic ringed iris, the firelit
    wall reflected across it with the shadow parade crossing, sparkling highlights."""
    w.field(cv, body)
    soft(cv, cx - R0 * 2.4, cy - R0 * 0.2, R0 * 3.2, P_["orange"], a=150)
    stip(cv, mix(body, INK, 0.32), (0, 0, W, H), 20, 3.0, seed + 1, fn=lambda X, Y: np.clip(np.hypot(X - cx, Y - cy) / 1100.0, 0.25, 1.0), key="eyeskin")
    for k in range(6):                                             # skin bumps
        bx = cx + R0 * (1.6 + 0.5 * math.cos(k * 2.1)) * math.cos(k * 1.05 + 0.4)
        by = cy + R0 * (1.4 + 0.4 * math.sin(k * 1.7)) * math.sin(k * 1.05 + 0.4)
        blob(cv, ell(bx, by, 26 + 12 * (k % 3), 20 + 8 * (k % 2), n=8), mix(body, INK, 0.2), w=3, seed=seed + 30 + k, boil=0.6)
    blob(cv, ell(cx + R0 * 0.06, cy + R0 * 0.08, R0 * 1.26, R0 * 1.28, n=16), mix(body, INK, 0.4), w=5, seed=seed + 2, boil=1.0,
         shade=lambda c: c.drawPath(poly_path(cr_closed(ell(cx - R0 * 0.5, cy - R0 * 0.2, R0 * 0.7, R0 * 1.1, n=12), 3)), paint(mix(body, P_["orange"], 0.35), 160)))
    ix, iy = cx + look[0] * R0 * 0.36, cy + look[1] * R0 * 0.3
    iR = R0 * 0.58

    def sh(c):
        c.drawPath(poly_path(cr_closed(ell(cx + R0 * 0.32, cy + R0 * 0.38, R0 * 1.0, R0 * 0.9, n=12), 3)), paint((222, 214, 238)))
        for k in range(6):                                          # faint veins at the edge
            a0 = 0.2 + k * 0.45
            p0 = (cx + R0 * math.cos(a0), cy + R0 * math.sin(a0))
            line(c, [p0, (cx + R0 * 0.8 * math.cos(a0 + 0.1), cy + R0 * 0.8 * math.sin(a0 + 0.1)), (cx + R0 * 0.7 * math.cos(a0 + 0.05), cy + R0 * 0.7 * math.sin(a0 + 0.05))],
                 3, P_["red"], seed=seed + 10 + k, boil=0.8, n=3, a=110)
        for k, col in enumerate((mix(eye_rgb, P_["teal"], 0.6), eye_rgb, mix(eye_rgb, P_["acid"], 0.35), mix(eye_rgb, P_["white"], 0.4))):
            c.drawCircle(ix, iy, iR * (1.0 - 0.14 * k), paint(col))
        for k in range(36):                                         # iris striations
            a0 = k / 36 * 2 * math.pi
            c.drawLine(ix + iR * 0.48 * math.cos(a0), iy + iR * 0.48 * math.sin(a0), ix + iR * 0.97 * math.cos(a0 + 0.06), iy + iR * 0.97 * math.sin(a0 + 0.06),
                       paint(mix(eye_rgb, P_["tealdk"], 0.55), 190, stroke=3.0))
        c.drawCircle(ix, iy, iR, paint(mix(eye_rgb, INK, 0.6), stroke=7))
        c.drawCircle(ix, iy, iR * 0.46, paint(INK))
        wall = [(cx - R0 * 0.95, cy - R0 * 0.7), (cx + R0 * 0.2, cy - R0 * 0.86), (cx + R0 * 0.26, cy - R0 * 0.42), (cx - R0 * 0.9, cy - R0 * 0.28)]
        c.save(); c.clipPath(poly_path(cr_closed(wall, 4)), doAntiAlias=True)
        c.drawRect(R(cx - R0 * 1.2, cy - R0 * 1.0, cx + R0 * 0.5, cy + R0 * 0.2), paint(P_["peach"], 150))
        for j in range(2):                                          # the parade, reflected
            kind = ["horse", "bunny", "bird", "person"][(int(refl_t / 1.8) + j) % 4]
            u = ((refl_t / 1.8) + j * 0.5) % 1.0
            shadow_shape(c, kind, cx + R0 * (0.5 - u * 1.7), cy - R0 * 0.58, R0 * 0.0018, T, a=215, seed=seed + 20 + j)
        c.restore()
        c.drawPath(poly_path(cr_closed(wall, 4)), paint(P_["white"], 110, stroke=4))
        c.drawCircle(ix + iR * 0.42, iy + iR * 0.4, iR * 0.12, paint(P_["white"], 230))
        c.drawCircle(ix + iR * 0.2, iy + iR * 0.58, iR * 0.06, paint(P_["white"], 200))
    blob(cv, ell(cx, cy, R0, R0 * 1.04, n=16), P_["white"], w=10, seed=seed + 3, boil=1.0, shade=sh)
    if blink > 0.01:
        lid = [(cx - R0 * 1.3, cy - R0 * 1.4), (cx + R0 * 1.3, cy - R0 * 1.4), (cx + R0 * 1.3, cy - R0 * 1.04 + 2.1 * R0 * blink), (cx, cy - R0 * 0.9 + 2.3 * R0 * blink),
               (cx - R0 * 1.3, cy - R0 * 1.04 + 2.1 * R0 * blink)]
        cv.save(); cv.clipPath(poly_path(cr_closed(ell(cx, cy, R0 + 6, R0 * 1.04 + 6, n=16), 3)), doAntiAlias=True)
        blob(cv, lid, body, w=8, seed=seed + 4, boil=0.8, n=4)
        cv.restore()
    sparkle(cv, cx + R0 * 0.78, cy - R0 * 0.86, 30, P_["white"], w=3, seed=seed + 5)
    sparkle(cv, cx - R0 * 0.9, cy + R0 * 0.9, 18, P_["yellow"], w=2.5, seed=seed + 6)
    spores(cv, T, (0, 0, W, H), n=30, seed=seed + 7, size=2.0, a=200, rise=20, drift=40)


def whip(cv, u, draw_a, draw_b, dist=1500):
    """Whip pan between two scenes: u 0..1; A leaves to the left, B enters from the right, with smear + streaks."""
    p = skia.Paint()
    p.setImageFilter(skia.ImageFilters.Blur(30 + 50 * math.sin(math.pi * u), 0))
    cv.saveLayer(None, p)
    if u < 0.5:
        cv.save(); cv.translate(-dist * ease(u * 2) * 0.6, 0); draw_a(); cv.restore()
    else:
        cv.save(); cv.translate(dist * (1 - ease((u - 0.5) * 2)) * 0.6, 0); draw_b(); cv.restore()
    cv.restore()
    hlines(cv, 46, seed=5990, rgb=P_["cream"], a=int(150 * math.sin(math.pi * u)), w=4.0)


# ===================================================================== T012  CAVE REVEAL (Z03-Z04)
def T012_cave_reveal(cv, t, T, A):
    if t >= 10.55:
        return _t012_b(cv, t, T, A)
    if t < 4.75:                                                   # crane down the immense cavern
        cam = camk(t, [(0.0, (0, -600, 1.0)), (4.6, (0, -155, 2.6)), (5.0, (0, -110, 2.9))])
        grand(cv, T, cam)
        title_card(cv, t + 3.265, 1.95, a=1.0 - kin(t, 0.15, 0.55), out=kin(t, 0.0, 0.7))
        vignette(cv, a=120)
    else:                                                          # the cross-section: push in on the chained row
        cam = camk(t, [(4.75, (40, 60, 1.06)), (7.6, (-300, 250, 1.75)), (10.6, (-320, 262, 1.9))])
        side_world(cv, T, cam, fg=t < 6.5)
        if t > 7.6:
            dim(cv, 0.45 * win(t, 7.6, 10.6, 0.3, 0.3))
        baby_inset(cv, T, t, 7.8, 10.55)
        vignette(cv, a=120)
    if 4.4 < t < 5.1:                                              # a foreground rock wipes past the lens
        u = (t - 4.4) / 0.7
        y0 = 1150 - 2600 * u
        pts = [(-100, y0), (300, y0 - 80), (700, y0 - 20), (1100, y0 - 110), (1500, y0 - 40), (2020, y0 - 90), (2020, y0 + 1500), (1500, y0 + 1600), (900, y0 + 1520),
               (300, y0 + 1620), (-100, y0 + 1540)]
        rock(cv, pts, seed=6000, rgb=(44, 16, 80), rim=P_["magenta"], strata=10, agate=(960, y0 + 760, 1000, 7, (84, 30, 140)))
        brush(cv, cr_open([(x_, y_ + 26) for x_, y_ in pts[:6]], 8), 22, P_["orange"], seed=6003, a=200)
        for k in range(5):
            vy = y0 + 200 + k * 260
            line(cv, [(-100, vy), (500, vy - 40 + 30 * math.sin(k)), (1200, vy + 20), (2020, vy - 30)], 7, [P_["teal"], P_["hotpink"], P_["acid"]][k % 3], seed=6030 + k,
                 boil=1.0, n=5, taper=(0.05, 0.05), a=200)
        for k in range(4):
            crys(cv, 200 + k * 500, y0 - 20, 1.6, T, seed=6010 + k)
            crys(cv, 450 + k * 480, y0 + 520 + 160 * (k % 2), 1.5, T, seed=6015 + k)
            crys(cv, 250 + k * 520, y0 + 1050 + 120 * (k % 2), 1.4, T, seed=6040 + k)
            glow_mushroom(cv, 700 + k * 420, y0 + 820, 1.6, T, seed=6050 + k)
        hlines(cv, 30, seed=6020, a=120, w=4, vertical=True)


def _strain(t):
    """The straining prisoner's channels during Z04 'so they can't even turn their heads' (shot time t)."""
    face, sq, veins, shake, sag, mouth = -1.0, (1.0, 1.0), 0.0, 0.0, None, 0.0
    if 12.7 <= t < 13.3:                                           # try to turn...
        u = ease((t - 12.7) / 0.6)
        face = -1.0 + 1.35 * u
        sq = (1.0 + 0.06 * u, 1.0 - 0.05 * u)
        veins, shake, sag, mouth = u, 0.5 * u, 22 * (1 - u), 0.25 * u
    elif 13.3 <= t < 13.55:                                        # CLANK: the collar stops it, snaps back
        u = (t - 13.3) / 0.25
        face = 0.35 - 1.1 * ease(u) + 0.15 * math.sin(u * 9) * (1 - u)
        sq = (0.94, 1.08)
        veins, shake, sag, mouth = 1.0, 1.0, 0.0, 0.6
    elif 13.55 <= t < 14.05:                                       # one more go, harder
        u = math.sin(math.pi * (t - 13.55) / 0.5)
        face = -0.75 + 0.85 * u
        sq = (1.0 + 0.08 * u, 1.0 - 0.06 * u)
        veins, shake, sag, mouth = 1.0, 0.8 * u + 0.2, 4.0, 0.3 + 0.4 * u
    elif 14.05 <= t < 14.7:                                        # ...gives up (deflates), eye back to the wall
        u = ease((t - 14.05) / 0.5)
        face = -0.75 - 0.25 * u
        sq = (1.0 + 0.08 * math.sin(math.pi * u), 1.0 - 0.1 * math.sin(math.pi * u))
        veins, shake, sag, mouth = 1.0 - u, 0.0, 18 * u + 4, 0.0
    return dict(face=face, squash=sq, veins=veins, shake=shake, sag=sag, mouth=mouth, look=(-1.0 if face < -0.5 else 1.0, -0.2 * veins))


def _t012_b(cv, t, T, A):
    """T012 second half: Z04 close-ups -> the eye -> whip to the prisoners' POV."""
    if t < 11.55:                                                  # 'Their legs...' ankles + shackles
        cam = dict(x=-120 + 50 * (t - 10.55), y=468, z=3.9 + 0.2 * (t - 10.55), rot=-5.0)
        jig = math.exp(-max(0.0, t - 10.75) * 5) * (1 if t > 10.75 else 0)
        cu_world(cv, T, cam, pl=[{}, dict(shake=jig * 0.6), {}])
        sfx(cv, "CLINK!", 1420, 300, 130, t, 10.75, fill=P_["cream"], seed=6100, ang=-10, hold=0.6)
        vignette(cv, a=140)
        return
    if t < 12.45:                                                  # '...and necks are chained' collar + padlock
        cam = dict(x=-20 - 20 * (t - 11.55), y=300, z=2.05 + 0.06 * (t - 11.55), rot=4.0)
        jig = math.exp(-max(0.0, t - 11.75) * 5) * (1 if t > 11.75 else 0)
        cu_world(cv, T, cam, pl=[{}, dict(shake=jig * 0.5), {}])
        sfx(cv, "CLANK!", 1420, 300, 130, t, 11.75, fill=P_["yellow"], seed=6110, ang=8, hold=0.55)
        vignette(cv, a=140)
        return
    if t < 14.7:                                                   # 'so they can't even turn their heads'
        st = _strain(t)
        cam = dict(x=0 + 6 * math.sin(t), y=230, z=1.42 + 0.03 * (t - 12.45))
        if 13.3 <= t < 13.6:
            cam["x"] += 14 * math.sin(t * 70) * (1 - (t - 13.3) / 0.3)
            cam["y"] += 9 * math.cos(t * 60) * (1 - (t - 13.3) / 0.3)
        mid = dict(face=st["face"], squash=st["squash"], veins=st["veins"], shake=st["shake"], sag=st["sag"], mouth=st["mouth"], look=st["look"])

        def fx(c):
            x, y = CU_X[1], CU_Y - 70 * CU_S * 1.3
            if 12.75 < t < 13.35 or 13.6 < t < 14.0:              # 'turn!' motion arc over the head
                kk = min(1.0, (t - (12.75 if t < 13.4 else 13.6)) / 0.3)
                arc = [(x - 120 + 240 * u, y - 250 - 60 * math.sin(math.pi * u)) for u in np.linspace(0, kk, 8)]
                if len(arc) > 2:
                    brush(c, cr_open(arc, 6), 12, P_["cream"], taper=(0.1, 0.0), seed=6125)
                    ex_, ey_ = arc[-1]
                    blob(c, [(ex_ + 30, ey_ + 4), (ex_ - 6, ey_ - 26), (ex_ - 4, ey_ + 30)], P_["cream"], w=4, seed=6126, boil=0.6, n=3)
            if 13.3 <= t < 13.7:                                   # CLANK impact star at the collar's chain
                kk = (t - 13.3) / 0.4
                ix_, iy_ = x + 60, CU_Y - 70 * CU_S * 1.15 + 70 * CU_S * 0.5
                star = []
                for j in range(16):
                    rr = (90 if j % 2 == 0 else 40) * (0.6 + 0.6 * kk)
                    a_ = j / 16 * 2 * math.pi + 0.2
                    star.append((ix_ + rr * math.cos(a_), iy_ + rr * math.sin(a_)))
                blob(c, star, P_["yellow"], w=5, seed=6127, boil=1.0, n=2, a=int(255 * (1 - kk ** 2)))
            if st["veins"] > 0.05:                                 # strain marks + sweat
                for k in range(7):
                    a_ = -2.6 + k * 0.33
                    r0, r1 = 230, 270 + 25 * math.sin(t * 30 + k)
                    line(c, [(x + r0 * math.cos(a_), y + r0 * math.sin(a_)), (x + r1 * math.cos(a_), y + r1 * math.sin(a_))], 6, seed=6120 + k, boil=1.0, n=2,
                         a=int(255 * st["veins"]))
                for k in range(3):
                    u = (t * 1.8 + k / 3) % 1.0
                    sx_, sy_ = x - 150 + k * 150 + 60 * u * (1 if k else -1), y - 120 + u * 160
                    blob(c, [(sx_, sy_ - 26), (sx_ + 14, sy_ + 2), (sx_, sy_ + 16), (sx_ - 14, sy_ + 2)], P_["mint"], w=3.5, seed=6130 + k, boil=0.6, n=4,
                         a=int(255 * (1 - u) * st["veins"]))
        cu_world(cv, T, cam, pl=[dict(look=(-1, 0)), mid, dict(look=(-1, 0))], hooks=dict(front=fx))
        sfx(cv, "NNNGH!", 520, 250, 100, t, 12.85, fill=P_["hotpink"], seed=6140, ang=-6, hold=0.45)
        sfx(cv, "CLANK!", 1420, 270, 140, t, 13.3, fill=P_["yellow"], seed=6141, ang=7, hold=0.5)
        if t > 14.05:
            caption(cv, "*sigh*", 1380, 300, t, 14.15, size=96, fill=P_["cream"], font="marker", seed=6142)
        vignette(cv, a=140)
        return

    def ecu():
        R0 = 380 + 50 * ease((t - 14.7) / 1.8)
        bl = 1.0 - abs((t - 15.85) / 0.12) if abs(t - 15.85) < 0.12 else 0.0
        big_eye(cv, T, 1060, 545, R0, look=(-1.0, -0.12), refl_t=t - 14.7, blink=bl)

    def pov():
        cam = dict(x=0, y=10 - 20 * ease((t - 16.6) / 2.7), z=1.0 + 0.06 * ease((t - 16.6) / 2.7))
        pov_wall(cv, T, cam, shadows=[("horse", 1450 - 120 * (t - 16.5), 430, 2.4), ("bunny", 500 - 90 * (t - 16.5), 470, 2.2)])
    if t < 16.5:                                                   # 'All they can ever see...'
        ecu()
        vignette(cv, a=150)
        return
    if t < 16.85:
        whip(cv, (t - 16.5) / 0.35, ecu, pov)
        return
    pov()                                                          # '...is the wall in front of them.'
    vignette(cv, a=110)


# ===================================================================== T014 helpers
def veil(cv, x, y, s, k_off, seed=0, T=0.0):
    """A lilac cloth draped over a statue on its pole; k_off 0 covering .. 1 whisked away (flies up-right, spins, fades)."""
    if k_off >= 1.0:
        return
    u = ease(k_off)
    cv.save()
    cv.translate(x + 260 * s * u, y - 420 * s * u); cv.rotate(160 * u); cv.scale(1 + 0.3 * u, 1 + 0.3 * u)
    sw = 6 * math.sin(T * 3 + seed)
    pts = [(-8 * s, -120 * s), (40 * s, -96 * s), (78 * s, -10 * s), (96 * s + sw, 84 * s), (40 * s, 70 * s), (0, 92 * s), (-44 * s, 70 * s), (-96 * s + sw, 84 * s),
           (-78 * s, -10 * s), (-46 * s, -96 * s)]
    blob(cv, pts, P_["lilac"], w=4.5, seed=seed, boil=0.9, n=4, a=int(255 * (1 - u)),
         shade=lambda c: [line(c, [(fx * s, -60 * s), (fx * 1.3 * s, 80 * s)], 3, mix(P_["lilac"], P_["violet"], 0.5), seed=seed + 3 + q, boil=0.6, n=2, a=200)
                          for q, fx in enumerate((-40, -10, 25, 55))])
    cv.restore()


def burst(cv, x, y, r, k, seed=0):
    """Pop sparkles + rays around a revealed object (k: 0..1 life)."""
    if k <= 0 or k >= 1:
        return
    for j in range(8):
        a_ = j / 8 * 2 * math.pi + seed
        rr = r * (0.6 + 0.9 * k)
        sparkle(cv, x + rr * math.cos(a_), y + rr * math.sin(a_), (18 + 10 * (j % 2)) * (1 - k * 0.6), [P_["yellow"], P_["white"], P_["hotpink"]][j % 3], w=2.5,
                seed=seed + j, a=int(255 * (1 - k)))
    for j in range(12):
        a_ = j / 12 * 2 * math.pi
        line(cv, [(x + r * 0.5 * math.cos(a_), y + r * 0.5 * math.sin(a_)), (x + r * (0.8 + 0.6 * k) * math.cos(a_), y + r * (0.8 + 0.6 * k) * math.sin(a_))], 5,
             P_["yellow"], seed=seed + 20 + j, boil=0.6, n=2, a=int(230 * (1 - k)))


def proscenium(cv, top, k, T, seed=6300, x0=150, x1=1770, y_bar=230):
    """The puppet-show gag: red velvet drapes rise on the low wall's ends, a scalloped gold valance drops in, footlights
    blink along the wall top and a star marquee pops up."""
    if k <= 0.01:
        return
    kd = pop(k, 0.0, 0.45)
    kv = pop(k, 0.25, 0.45)
    ks = pop(k, 0.5, 0.4)
    red, red_dk, gold = (200, 20, 60), (130, 8, 40), P_["gold"]
    for side, xe in ((-1, x0), (1, x1)):                           # drapes
        hgt = (top - y_bar) * kd
        if hgt < 5:
            continue
        yb = top
        xin = xe - side * 170
        pts = [(xe + side * 30, yb - hgt - 20), (xin, yb - hgt - 20), (xin + side * 40, yb - hgt * 0.55), (xin - side * 30, yb - hgt * 0.38), (xe - side * 30, yb),
               (xe + side * 40, yb)]
        blob(cv, pts, red, w=5, seed=seed + side, boil=0.9, n=4,
             shade=lambda c, xe=xe, xin=xin, hgt=hgt, side=side: [c.drawLine(xe - side * (20 + q * 36), yb - hgt, xe - side * (14 + q * 22), yb, paint(red_dk, stroke=9))
                                                                  for q in range(4)])
        tx, ty = xin + side * 10, yb - hgt * 0.42                  # tie-back + tassel
        blob(cv, ell(tx, ty, 26, 14, n=8), gold, w=3.5, seed=seed + 5 + side, boil=0.5)
        line(cv, [(tx, ty), (tx + side * 8, ty + 40)], 6, gold, seed=seed + 7 + side, boil=0.5, n=2, taper=(0, 0))
        blob(cv, [(tx + side * 8 - 12, ty + 40), (tx + side * 8 + 12, ty + 40), (tx + side * 8 + 16, ty + 80), (tx + side * 8 - 16, ty + 80)], gold, w=3, seed=seed + 9 + side,
             boil=0.5, n=3)
    if kv > 0.01:                                                   # valance with scallops + fringe
        yv = y_bar - 140 * (1 - kv)
        cv.save(); cv.translate(0, 0)
        blob(cv, rect_pts([(x0 - 40, yv - 70), (x1 + 40, yv - 70), (x1 + 40, yv + 10), (x0 - 40, yv + 10)], 4), red, w=5, seed=seed + 11, boil=0.8, n=3)
        nsc = 9
        for q in range(nsc):
            sx0 = x0 - 40 + (x1 - x0 + 80) * q / nsc
            sx1 = x0 - 40 + (x1 - x0 + 80) * (q + 1) / nsc
            blob(cv, [(sx0, yv), (sx1, yv), ((sx0 + sx1) / 2, yv + 46)], red_dk, w=4, seed=seed + 20 + q, boil=0.7, n=4)
            dots(cv, [((sx0 + sx1) / 2, yv + 50)], 9, gold)
        brush(cv, cr_open([(x0 - 40, yv - 44), ((x0 + x1) / 2, yv - 50), (x1 + 40, yv - 44)], 8), 9, gold, seed=seed + 30)
        cv.restore()
    if ks > 0.01:                                                   # footlights + star marquee
        for q in range(14):
            bx = x0 + 40 + q * (x1 - x0 - 80) / 13
            on = (int(T * 6) + q) % 3 != 0
            dots(cv, [(bx, top - 6)], 16 if on else 11, P_["yellow"] if on else P_["orange"], a=int(255 * ks) if on else int(180 * ks))
            if on:
                dots(cv, [(bx, top - 6)], 30, P_["yellow"], a=int(50 * ks))
        sx, sy = (x0 + x1) / 2, y_bar - 90
        cv.save(); cv.translate(sx, sy); cv.scale(ks, ks); cv.rotate(4 * math.sin(T * 2))
        star = [(0, -110), (30, -36), (112, -36), (46, 12), (70, 92), (0, 46), (-70, 92), (-46, 12), (-112, -36), (-30, -36)]
        blob(cv, star, P_["yellow"], w=6, seed=seed + 40, boil=0.8, n=3)
        paint_text(cv, "SHOW!", 0, 22, font="bangers", size=56, fill=P_["magenta"], ink_w=3.5, shadow=None, seed=seed + 41, streaks=False)
        cv.restore()


def dust(cv, x0, x1, y, k, seed=0, n=10):
    """Billowing dust puffs along a line (k: 0..1 life)."""
    if k <= 0 or k >= 1:
        return
    col = mix(P_["lilac"], P_["cream"], 0.35)
    for j in range(n):
        px = x0 + (x1 - x0) * (j + 0.5) / n + 30 * math.sin(j * 2.3)
        for q in range(4):
            rr = (22 + 30 * k) * (1.0 - 0.15 * q)
            ox = (q - 1.5) * rr * 0.9 + 14 * math.sin(j + q)
            oy = -rr * 0.5 - 50 * k * (0.5 + 0.3 * q) - 10 * (q % 2)
            blob(cv, ell(px + ox, y + oy, rr, rr * 0.85, n=8), col, w=2.5, seed=seed + j * 5 + q, boil=1.0, a=int(230 * (1 - k) ** 0.8))


def beam(cv, fire_xy, st_a, st_b, sh_a, sh_b, k, rgb=None, a=46):
    """Projection rays (screen space): a cone from the fire to the statue (st_a..st_b), then fanning from the statue to
    its shadow on the wall (sh_a..sh_b). k 0..1 = how far the light has travelled."""
    if k <= 0.01:
        return
    rgb = rgb or P_["yellow"]
    p = skia.Paint(AntiAlias=True, Color=core.C(rgb, a))
    p.setBlendMode(skia.BlendMode.kScreen)
    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6))
    k1 = min(1.0, k / 0.4)
    fx, fy = fire_xy
    pa = (fx + (st_a[0] - fx) * k1, fy + (st_a[1] - fy) * k1)
    pb = (fx + (st_b[0] - fx) * k1, fy + (st_b[1] - fy) * k1)
    cv.drawPath(poly_path([(fx, fy), pa, pb]), p)
    if k > 0.4:
        k2 = (k - 0.4) / 0.6
        qa = (st_a[0] + (sh_a[0] - st_a[0]) * k2, st_a[1] + (sh_a[1] - st_a[1]) * k2)
        qb = (st_b[0] + (sh_b[0] - st_b[0]) * k2, st_b[1] + (sh_b[1] - st_b[1]) * k2)
        cv.drawPath(poly_path([st_a, qa, qb, st_b]), p)
        ln = paint(P_["white"], 120, stroke=2.0, blend=skia.BlendMode.kScreen)
        cv.drawLine(st_a[0], st_a[1], qa[0], qa[1], ln)
        cv.drawLine(st_b[0], st_b[1], qb[0], qb[1], ln)
    ln = paint(P_["white"], 110, stroke=2.0, blend=skia.BlendMode.kScreen)
    cv.drawLine(fx, fy, pa[0], pa[1], ln)
    cv.drawLine(fx, fy, pb[0], pb[1], ln)


# ===================================================================== T014  FIRE + LOW WALL + CARRIERS (Z05-Z06)
def _t014_carriers(t):
    """Reverse-view carriers: veiled statues walked in on 'people walk behind that wall carrying objects', then unveiled
    on 'animals' (13.85) / 'people' (14.93) / 'trees' (15.97)."""
    out = []
    spec = [(-350, 520, 9.6, 1, "horse", 13.85), (2250, 1400, 9.9, -1, "tree", 15.97), (2400, 960, 10.9, -1, "person", 14.93)]
    for k, (xa, xb, t0, face, kind, tu) in enumerate(spec):
        if t < t0:
            continue
        u = float(np.clip((t - t0) / 2.6, 0, 1))
        x = xa + (xb - xa) * (1 - (1 - u) ** 2)
        walking = u < 1.0
        raise_k = 0.62 + 0.38 * pop(t, tu - 0.15, 0.35)
        d = dict(x=x, kind=kind, face=face, walk=walking, phase=k * 0.9 if walking else k * 0.9 + 0.4)
        d["raise"] = raise_k
        d["veil"] = float(np.clip((t - tu) / 0.45, 0, 1))
        d["burst"] = float(np.clip((t - tu - 0.1) / 0.7, 0, 1)) if t > tu + 0.1 else 0.0
        d["talk"] = 0.0
        out.append(d)
    return out


def T014_fire_wall(cv, t, T, A):
    if t < 17.25:
        # crane up from the prisoners' faces to the fire behind them; the low wall rises; curtains; carriers + statues
        cam = camk(t, [(0.0, (0, 300, 1.72)), (0.35, (0, 290, 1.7)), (2.1, (0, -10, 1.02)), (4.9, (0, 20, 1.08)), (6.6, (0, 0, 1.0)), (9.4, (0, -30, 1.08)),
                       (13.2, (0, -60, 1.12)), (17.25, (0, -80, 1.2))])
        fire = 0.55 + 0.75 * pop(t, 1.1, 0.5) - 0.3 * kin(t, 1.8, 1.0)
        wall_k = pop(t, 5.1, 0.5)
        pk = float(np.clip((t - 7.25) / 1.4, 0, 1)) if t > 7.25 else 0.0

        def wfx(c, top):
            dust(c, -200, 2100, 850, (t - 5.1) / 0.9, seed=6400, n=12)
            proscenium(c, top, pk, T)
        pl = [dict(look=(0.0, 0.25), blink=None) for _ in range(6)]
        rev_view(cv, T, cam, carriers=_t014_carriers(t), prisoners=pl, fire=fire, wall_k=wall_k, wall_fx=wfx)
        sfx(cv, "FWOOSH!", 1460, 300, 120, t, 1.12, fill=P_["yellow"], seed=6410, ang=-8, hold=0.7)
        sfx(cv, "RUMBLE", 420, 880, 90, t, 5.1, fill=P_["lilac"], seed=6411, ang=4, hold=0.6, shadow_rgb=P_["violet"])
        vignette(cv, a=130)
        return
    # the cross-section: light from the fire passes the statues and throws their shadows big onto the wall
    lt = t - 17.25
    cam = camk(t, [(17.25, (60, 30, 1.06)), (18.7, (-60, 20, 1.08)), (20.4, (-640, -20, 1.42))])
    kinds = [("horse", 930, (10, 300, 1.25)), ("person", 1070, (205, 440, 1.15)), ("tree", 1210, (40, 620, 1.2))]
    carriers = [dict(x=x - 14 * lt, kind=k_, face=-1, walk=True, phase=j * 0.8) for j, (k_, x, _) in enumerate(kinds)]
    gk = [float(np.clip((lt - 0.75 - 0.2 * j) / 0.6, 0, 1)) for j in range(3)]
    shadows = []
    for j, (k_, x, (sx_, sy_, ss_)) in enumerate(kinds):
        shadows.append((k_, sx_, sy_, ss_ * (0.5 + 0.5 * pop(gk[j], 0.0, 1.0)), int(235 * min(1.0, gk[j] * 1.8))))
    side_world(cv, T, cam, carriers=carriers, wall_shadows=shadows, fg=False)
    C = sets.Cam(cv, cam)
    fxy = C.to_screen(1520, 700, 1.0)
    for j, (k_, x, (sx_, sy_, ss_)) in enumerate(kinds):
        bk = float(np.clip((lt - 0.1 - 0.2 * j) / 1.0, 0, 1))
        stx, sty = x - 14 * lt - 40 * 0.62, 860 - 470 * 0.62 - 60 * 0.62
        st_a = C.to_screen(stx, sty - 62, 1.0)
        st_b = C.to_screen(stx, sty + 62, 1.0)
        sh_a = C.to_screen(sx_ + 40, sy_ - 130 * ss_, 0.85)
        sh_b = C.to_screen(sx_ + 40, sy_ + 120 * ss_, 0.85)
        beam(cv, fxy, st_a, st_b, sh_a, sh_b, ease(bk), rgb=P_["yellow"], a=50)
    vignette(cv, a=120)


# ===================================================================== T016 helpers
PARADE = ["horse_a", "bunny", "bird_up", "person", "fish", "tree", "jug", "star"]


def parade(T, n=6, speed=110.0, spacing=470.0, y0=470, s=2.0, x_right=2350, kinds=None, phase=0.0):
    """An endless right-to-left conveyor of shadows (POV wall-layer coords) with walk-bob, galloping/flapping variants."""
    kinds = kinds or PARADE
    out = []
    span = spacing * n
    for k in range(n):
        u = (T * speed + k * spacing + phase) % span
        x = x_right - u
        idx = int((T * speed + k * spacing + phase) // span) * n + k
        kind = kinds[idx % len(kinds)]
        bob = abs(math.sin(T * 5.0 + k * 1.7)) * 16
        yy = y0 + 70 * math.sin(k * 2.3) - bob
        if kind.startswith("horse"):
            kind = "horse_a" if int(T * 6 + k) % 2 else "horse_b"
        if kind.startswith("bird"):
            kind = "bird_up" if int(T * 5 + k) % 2 else "bird_dn"
            yy -= 180
        out.append((kind, x, yy, s * (0.9 + 0.2 * math.sin(k * 1.9)), -1 if kind in ("bird_up", "bird_dn", "horse_a", "horse_b") else 1))
    return out


def polaroid(cv, x, y, w_, h_, ang, k, art, label, seed=0, T=0.0):
    """A taped polaroid card that pops in (k), art(c, cx, cy, ww, hh) drawn in its window, a hand-written label."""
    if k <= 0.01:
        return
    cv.save(); cv.translate(x, y); cv.rotate(ang); cv.scale(k, k)
    blob(cv, rect_pts([(-w_ / 2 + 10, -h_ / 2 + 14), (w_ / 2 + 10, -h_ / 2 + 14), (w_ / 2 + 10, h_ / 2 + 14), (-w_ / 2 + 10, h_ / 2 + 14)], 3), INK, w=0, seed=seed + 1,
         boil=0.6, n=3, a=110, misreg=(0, 0))
    blob(cv, rect_pts([(-w_ / 2, -h_ / 2), (w_ / 2, -h_ / 2), (w_ / 2, h_ / 2), (-w_ / 2, h_ / 2)], 3), P_["cream"], w=5, seed=seed + 2, boil=0.8, n=3)
    wx0, wy0, wx1, wy1 = -w_ / 2 + 22, -h_ / 2 + 22, w_ / 2 - 22, h_ / 2 - 90
    cv.drawRect(R(wx0, wy0, wx1, wy1), paint((40, 16, 70)))
    cv.save(); cv.clipRect(R(wx0, wy0, wx1, wy1), doAntiAlias=True)
    art(cv, (wx0 + wx1) / 2, (wy0 + wy1) / 2, wx1 - wx0, wy1 - wy0)
    cv.restore()
    brush(cv, np.array([(wx0, wy0), (wx1, wy0), (wx1, wy1), (wx0, wy1)]), 4, closed=True, seed=seed + 3)
    blob(cv, rect_pts([(-60, -h_ / 2 - 22), (60, -h_ / 2 - 30), (64, -h_ / 2 + 14), (-56, -h_ / 2 + 20)], 3), P_["yellow"], w=0, seed=seed + 4, boil=0.6, n=3, a=170,
         misreg=(0, 0))
    paint_text(cv, label, 0, h_ / 2 - 30, font="marker", size=40, fill=INK, ink_w=0, shadow=None, seed=seed + 5, wobble=1.0, streaks=False)
    cv.restore()


def nope(cv, x, y, sz, k, ang=-12.0, seed=0, text="NOPE"):
    """A hand-painted red rubber-stamp NOPE that slams down (k = seconds since the slam / its pop phase)."""
    if k <= 0:
        return
    sc = 1.0 + 1.3 * (1.0 - ease(min(1.0, k / 0.18)))
    a = int(255 * min(1.0, k / 0.08))
    cv.save(); cv.translate(x, y); cv.rotate(ang + 4 * math.sin(seed)); cv.scale(sc, sc)
    wd = measure(text, "bangers", sz) + sz * 0.55
    ht = sz * 1.08
    red = (226, 24, 44)
    blob(cv, rect_pts([(-wd / 2, -ht / 2), (wd / 2, -ht / 2), (wd / 2, ht / 2), (-wd / 2, ht / 2)], 4), None, w=sz * 0.09, ink=red, seed=seed, boil=1.4, n=3, a=a)
    blob(cv, rect_pts([(-wd / 2 + sz * 0.12, -ht / 2 + sz * 0.12), (wd / 2 - sz * 0.12, -ht / 2 + sz * 0.12), (wd / 2 - sz * 0.12, ht / 2 - sz * 0.12),
                       (-wd / 2 + sz * 0.12, ht / 2 - sz * 0.12)], 4), None, w=sz * 0.035, ink=red, seed=seed + 1, boil=1.2, n=3, a=a)
    paint_text(cv, text, 0, sz * 0.36, font="bangers", size=sz, fill=red, ink_w=sz * 0.03, outline_rgb=P_["maroon"], shadow=None, seed=seed + 2, streaks=False,
               wobble=3.0, a=a)
    i = np.arange(40, dtype=float)                                  # distressed ink: paper specks through the paint
    dots(cv, np.stack([(hsh(seed + i * 1.3) - 0.5) * wd, (hsh(seed + i * 2.7) - 0.5) * ht], 1), sz * 0.025, P_["cream"], a=int(a * 0.8))
    if k < 0.7:
        for j in range(9):                                          # splatter on impact
            a_ = j * 0.7 + seed
            rr = wd * (0.55 + 0.25 * float(hsh(seed + j)))
            dots(cv, [(rr * math.cos(a_), rr * 0.6 * math.sin(a_))], sz * (0.03 + 0.03 * float(hsh(seed + j * 3))), red, a=int(a * (1 - k / 0.7)))
    cv.restore()


def bubble(cv, x, y, text, tail, k, seed=0, size=64, font="bangers", fill=None, txt_rgb=None, w_=None):
    """Comic speech bubble centred at x,y with its tail pointing to `tail` (pops with k 0..1)."""
    if k <= 0.01:
        return
    tw = (w_ or measure(text, font, size)) + size * 0.9
    th = size * 1.55
    cv.save(); cv.translate(x, y); cv.scale(k, k)
    tx, ty = tail[0] - x, tail[1] - y
    ang = math.atan2(ty, tx)
    nx, ny = -math.sin(ang), math.cos(ang)
    base = (math.cos(ang) * tw * 0.3, math.sin(ang) * th * 0.3)
    blob(cv, [(base[0] + nx * 26, base[1] + ny * 26), (tx / k if k > 0 else tx, ty / k if k > 0 else ty), (base[0] - nx * 26, base[1] - ny * 26)], fill or P_["white"], w=5,
         seed=seed, boil=0.8, n=3)
    blob(cv, ell(0, 0, tw / 2, th / 2, n=14), fill or P_["white"], w=5.5, seed=seed + 1, boil=1.0)
    blob(cv, [(base[0] + nx * 22, base[1] + ny * 22), (base[0] * 1.6, base[1] * 1.6), (base[0] - nx * 22, base[1] - ny * 22)], fill or P_["white"], w=0, seed=seed + 2,
         boil=0.6, n=3, misreg=(0, 0))
    paint_text(cv, text, 0, size * 0.36, font=font, size=size, fill=txt_rgb or P_["magenta"], ink_w=3.5, shadow=None, seed=seed + 3, streaks=False,
               reveal=min(1.0, k * 1.2), stagger=0.05)
    cv.restore()


def echo_rings(cv, cx, cy, t, t0, n=4, period=0.32, speed=900, ang=180, span=90, rgb=None, w_=6, maxr=1100, seed=0):
    """Sound-wave arcs travelling out from (cx, cy) in direction ang (deg), spawned every `period` after t0."""
    if t < t0:
        return
    rgb = rgb or P_["cream"]
    for k in range(n):
        tk = t - t0 - k * period
        if tk < 0:
            continue
        r = tk * speed
        if r > maxr or r < 10:
            continue
        a = int(230 * (1 - r / maxr))
        a0, a1 = math.radians(ang - span / 2), math.radians(ang + span / 2)
        pts = [(cx + r * math.cos(a0 + (a1 - a0) * u), cy + r * math.sin(a0 + (a1 - a0) * u)) for u in np.linspace(0, 1, 12)]
        line(cv, pts, w_ + 2, INK, seed=seed + k, boil=1.0, n=4, taper=(0.3, 0.3), a=int(a * 0.6))
        line(cv, pts, w_, rgb, seed=seed + k, boil=1.0, n=4, taper=(0.3, 0.3), a=a)


def marquee(cv, x, y, k, T, seed=6560):
    """A wooden board hanging on two chains from the ceiling: NOW PLAYING / FOREVER (k = drop-in)."""
    if k <= 0.01:
        return
    yy = y - 260 * (1 - k)
    sw = 3 * math.sin(T * 1.3)
    cv.save(); cv.translate(x, yy); cv.rotate(sw)
    for side in (-1, 1):
        chain(cv, (side * 190, -330), (side * 170, -80), seed=seed + side, link=16, sag=4, w=3)
    blob(cv, rect_pts([(-250, -90), (250, -96), (256, 96), (-246, 100)], 3), (170, 30, 120), w=6, seed=seed + 3, boil=0.8, n=3,
         shade=lambda c: [c.drawLine(-250, -50 + q * 46, 250, -52 + q * 46, paint((120, 16, 90), stroke=3)) for q in range(4)])
    for q in range(12):
        bx = -230 + q * 42
        on = (int(T * 8) + q) % 2 == 0
        dots(cv, [(bx, -76), (bx, 82)], 7 if on else 5, P_["yellow"] if on else P_["orange"])
    paint_text(cv, "NOW PLAYING", 0, -22, font="bangers", size=50, fill=P_["cream"], ink_w=3.5, shadow=(3, 3), seed=seed + 5, streaks=False)
    paint_text(cv, "FOREVER", 0, 60, font="shrik", size=62, fills=[P_["yellow"], P_["orange"]], ink_w=4, shadow=(4, 4), shadow_rgb=P_["magenta"], seed=seed + 6)
    cv.restore()


# ===================================================================== T016  ONLY SHADOWS (Z07-Z08)
def _card_fire(c, cx, cy, ww, hh, T):
    glow(c, cx, cy + 20, 160, P_["orange"], a=50, n=3, seed=6500)
    big_fire(c, cx, cy + 110, 0.55, T, seed=6501)


def _card_puppet(c, cx, cy, ww, hh, T):
    glow(c, cx, cy, 170, P_["violet"], a=60, n=3, seed=6510)
    line(c, [(cx + 4, cy + 200), (cx, cy + 10)], 9, (110, 70, 40), seed=6511, boil=0.5, n=2, taper=(0, 0))
    statue2(c, "horse", cx, cy - 40, 1.25, T, seed=6512, rgb=P_["peach"])
    blob(c, ell(cx - 90, cy + 150, 46, 52, n=10), (36, 16, 60), w=4, seed=6513, boil=0.8)
    dots(c, [(cx - 102, cy + 150), (cx - 80, cy + 150)], 5, P_["yellow"])


def _card_each(c, cx, cy, ww, hh, T):
    c.drawRect(R(cx - ww, cy - hh, cx + ww, cy + hh), paint((70, 30, 110)))
    pris(c, cx - 75, cy + 120, 0.75, T, seed=6520, view="side", face=1, look=(1, 0), anchor=(cx - 120, cy + 126), sparkle_k=0.6)
    pris(c, cx + 75, cy + 120, 0.75, T, seed=6533, view="side", face=-1, look=(-1, 0), anchor=(cx + 120, cy + 126), sparkle_k=0.6)
    k = 0.85 + 0.15 * math.sin(T * 6)
    blob(c, [(cx, cy - 20 + 30 * k), (cx - 30 * k, cy - 50), (cx - 18 * k, cy - 70 * k), (cx, cy - 58), (cx + 18 * k, cy - 70 * k), (cx + 30 * k, cy - 50)], P_["hotpink"],
         w=3.5, seed=6540, boil=0.6, n=4)


def T016_only_shadows(cv, t, T, A):
    if t < 10.45:
        # the prisoners' POV: the endless parade; NOPE cards; 'only shadows' wide
        if t < 8.9:
            cam = dict(x=10 * math.sin(t * 0.4), y=-10 + 4 * math.sin(t * 0.5), z=1.02 + 0.03 * t / 8.9)
        else:
            u = ease((t - 8.9) / 1.2)
            cam = dict(x=0, y=-10 + 30 * u, z=1.05 - 0.13 * u)
        sl = parade(T, n=6, speed=120.0, spacing=470.0, y0=520, s=2.0)

        def wall_fx(c):
            if t > 8.8:                                            # 'only shadows': a halo of firelight blooms on the wall
                kk = ease((t - 8.8) / 1.0)
                for j in range(9):
                    a0 = math.radians(-90 + (j - 4) * 15 + 3 * math.sin(T * 0.7 + j))
                    pth = poly_path([(960, 1350), (960 + 2200 * math.cos(a0 - 0.04), 1350 + 2200 * math.sin(a0 - 0.04)),
                                     (960 + 2200 * math.cos(a0 + 0.04), 1350 + 2200 * math.sin(a0 + 0.04))])
                    c.drawPath(pth, paint(P_["yellow"], int(38 * kk), blend=skia.BlendMode.kScreen))
                for j in range(14):
                    sparkle(c, 100 + (j * 211) % 1700, 140 + (j * 137) % 560, (8 + 5 * (j % 3)) * kk, [P_["white"], P_["yellow"], P_["cream"]][j % 3], w=1.6, seed=6600 + j,
                            a=int(220 * kk))
        def front_board(c):
            marquee(c, 960, 250, pop(t, 0.15, 0.5) * (1 - ease((t - 4.0) / 0.4)), T)
        pov_wall(cv, T, cam, shadows=sl, hooks=dict(wall=wall_fx), heads=7)
        if t < 4.4:
            C_ = sets.Cam(cv, cam)
            with C_.layer(0.6):
                front_board(cv)
        cards = [(4.4, 4.85, 430, 470, -8, _card_fire, "THE FIRE"), (5.6, 6.0, 960, 430, 4, _card_puppet, "THE PUPPETS"),
                 (7.12, 7.62, 1490, 470, -5, _card_each, "EACH OTHER")]
        if 4.3 < t < 9.4:
            dim(cv, 0.42 * win(t, 4.3, 9.4, 0.25, 0.5))
            for j, (t0, ts, x, y, ang, art, lab) in enumerate(cards):
                if t < t0:
                    continue
                k = pop(t, t0, 0.35)
                fly = ease((t - 8.75 - j * 0.06) / 0.45) if t > 8.75 else 0.0
                xx = x + (x - 960) * 1.6 * fly
                yy = y + 700 * fly * fly - 120 * fly
                aa = ang + (j - 1) * 50 * fly
                polaroid(cv, xx, yy, 380, 450, aa, k, lambda c, cx, cy, ww, hh, art=art: art(c, cx, cy, ww, hh, T), lab, seed=6700 + j * 10, T=T)
                if t >= ts:
                    cv.save(); cv.translate(xx, yy); cv.rotate(aa)
                    nope(cv, 0, -50, 140, t - ts, ang=-14 + 9 * j, seed=6750 + j * 7)
                    cv.restore()
        vignette(cv, a=120)
        return
    if t < 12.15:                                                  # 'when the carriers talk' - two carriers chatting backstage
        lt = t - 10.45
        cam = dict(x=-300 + 12 * lt, y=-20, z=2.0 + 0.05 * lt)
        tk1 = abs(math.sin(t * 13.0)) if (int(t * 2.2) % 2 == 0) else 0.08
        tk2 = abs(math.sin(t * 11.0 + 1)) if (int(t * 2.2) % 2 == 1) else 0.08
        carriers = [dict(x=560, kind="horse", face=1, walk=False, phase=0.3, talk=tk1, statue_k=1.1, s=1.0),
                    dict(x=790, kind="bunny", face=-1, walk=False, phase=1.1, talk=tk2, statue_k=1.1, s=1.0)]

        def chat(c):
            for j, (bx, by, txt, tl, t0) in enumerate(((330, 380, "...so then I says...", (560, 525), 10.55), (1010, 360, "NO WAY!", (790, 525), 11.15))):
                if t > t0:
                    bubble(c, bx, by, txt, tl, pop(t, t0, 0.3), seed=6800 + j * 5, size=30 if j == 0 else 40, font="marker" if j == 0 else "bangers",
                           txt_rgb=INK if j == 0 else P_["magenta"])
        rev_view(cv, T, cam, carriers=carriers, hooks=dict(carriers=chat), n_pris=6)
        vignette(cv, a=130)
        return
    if t < 14.45:                                                  # 'their voices echo off the wall'
        lt = t - 12.15
        cam = dict(x=-60 - 30 * lt, y=40, z=1.06 + 0.02 * lt)
        tk = abs(math.sin(t * 12.0))
        carriers = [dict(x=1080, kind="horse", face=1, walk=False, phase=0.3, talk=tk), dict(x=1270, kind="bunny", face=-1, walk=False, phase=1.1, talk=1 - tk)]
        side_world(cv, T, cam, carriers=carriers, fg=False)
        C = sets.Cam(cv, cam)
        mx, my = C.to_screen(1175, 680, 1.0)
        wx, wy = C.to_screen(300, 470, 0.85)
        d = math.hypot(mx - wx, my - wy)
        echo_rings(cv, mx, my, lt, 0.05, n=6, period=0.26, speed=1000, ang=math.degrees(math.atan2(wy - my, wx - mx)), span=64, maxr=d, seed=6900, w_=11)
        echo_rings(cv, wx, wy, lt, 0.05 + d / 1000, n=6, period=0.26, speed=760, ang=12, span=80, rgb=P_["yellow"], maxr=760, seed=6920, w_=11)
        if lt > 0.05 + d / 1000:                                   # the wall 'rings' where the echo hits
            kk = min(1.0, (lt - 0.05 - d / 1000) / 0.3)
            for j in range(3):
                rr = (40 + 60 * j) * kk + 8 * math.sin(t * 20 + j)
                cv.drawCircle(wx, wy, rr, paint(P_["yellow"], int(150 * (1 - j / 3)), stroke=6))
        caption(cv, "ECHO... echo... echo...", 960, 150, lt, 0.9, size=66, fill=P_["cream"], font="marker", seed=6940, dur=0.9)
        vignette(cv, a=120)
        return
    # 'So the prisoners believe the shadows are talking': wall + prisoners, bubbles out of the shadows, amazement
    lt = t - 14.45
    cam = dict(x=-560 + 8 * math.sin(t * 0.6), y=110, z=1.5 + 0.03 * lt)
    amaze = ease((lt - 0.75) / 0.4)
    pl = []
    for k in range(6):
        pl.append(dict(look=(-1, -0.2), eye_k=1.0 + 0.3 * amaze, sparkle=amaze, mouth=0.6 * amaze * (0.8 + 0.2 * math.sin(t * 5 + k)), blink=0.0 if amaze > 0 else None))
    hs, bs = 1.15, 1.05
    shadows = [("horse", -60, 560, hs), ("bunny", 230, 590, bs)]

    def wall_hook(c):
        echo_rings(c, 300, 470, lt, 0.0, n=6, period=0.45, speed=420, ang=0, span=70, rgb=P_["yellow"], maxr=420, seed=6950, w_=7)
    side_world(cv, T, cam, wall_shadows=shadows, prisoners=pl, fg=False, hooks=dict(wall=wall_hook))
    C = sets.Cam(cv, cam)
    hx, hy = C.to_screen(-60 + 108 * 1.1 * hs, 560 - 100 * 1.1 * hs, 0.85)
    bx_, by_ = C.to_screen(230 + 88 * 1.1 * bs, 590 - 30 * 1.1 * bs, 0.85)
    bubble(cv, hx + 330, hy - 110, "NEIGH?", (hx + 10, hy - 10), pop(lt, 0.35, 0.35), seed=6960, size=84)
    bubble(cv, bx_ + 330, by_ - 220, "HI, GUYS!", (bx_ + 10, by_ - 10), pop(lt, 1.6, 0.35), seed=6970, size=70, txt_rgb=P_["blue"])
    for k in range(6):                                             # little '!' over the amazed prisoners
        px, py = C.to_screen(420 + k * 95, 900 + (k % 2) * 30 - 128, 1.0)
        if amaze > 0.05:
            paint_text(cv, "!", px + 10, py - 12 * amaze - 4 * math.sin(t * 9 + k), font="bangers", size=64 * amaze, fill=P_["yellow"], ink_w=3.5, shadow=(3, 3),
                       seed=6980 + k, streaks=False)
    vignette(cv, a=120)


# ===================================================================== T020 helpers
def name_tag(cv, text, x, y, k, tx, ty, seed=0, col=None, size=46, ang=-6.0):
    """A hand-lettered paper name tag pinned to a shadow by a string (pops with k)."""
    if k <= 0.01:
        return
    col = col or P_["cream"]
    line(cv, [(x, y + size * 0.4), ((x + tx) / 2, (y + ty) / 2 + 20), (tx, ty)], 3, INK, seed=seed, boil=0.8, n=4, a=int(255 * min(1, k)))
    dots(cv, [(tx, ty)], 7, P_["red"])
    cv.save(); cv.translate(x, y); cv.rotate(ang + 6 * math.sin(seed + 0.0)); cv.scale(k, k)
    tw = measure(text, "marker", size) + 50
    blob(cv, rect_pts([(-tw / 2, -size * 0.75), (tw / 2, -size * 0.8), (tw / 2 + 6, size * 0.6), (-tw / 2 - 4, size * 0.66)], 3), col, w=4.5, seed=seed + 1, boil=0.8, n=3)
    dots(cv, [(-tw / 2 + 18, -size * 0.1)], 7, INK)
    paint_text(cv, text, 8, size * 0.32, font="marker", size=size, fill=P_["magenta"], ink_w=0, shadow=None, seed=seed + 2, wobble=1.0, streaks=False)
    cv.restore()


def chalk(cv, pts, k, w_=5.0, seed=0, rgb=None, closed=False):
    """A chalk scribble drawn on progressively (k 0..1 of its length)."""
    if k <= 0.01:
        return
    P = cr_open(np.asarray(pts, float), 6)
    n = max(2, int(len(P) * min(1.0, k)))
    brush(cv, P[:n], w_, rgb or P_["white"], taper=(0.05, 0.1), var=0.5, seed=seed, a=225)


def chalk_text(cv, text, x, y, k, size=44, seed=0, ang=0.0):
    if k <= 0.01:
        return
    cv.save(); cv.translate(x, y); cv.rotate(ang)
    paint_text(cv, text, 0, 0, font="caveat", size=size, fill=P_["white"], ink_w=0, shadow=None, seed=seed, wobble=1.5, streaks=False, reveal=min(1.0, k),
               stagger=0.05, a=230)
    cv.restore()


def medal(cv, x, y, s, ang=0.0, seed=0, ribbon=1.0):
    """A gold medal on a short red/blue ribbon (x, y = centre of the disc)."""
    cv.save(); cv.translate(x, y); cv.rotate(ang)
    L = 80 * s * ribbon
    for side, col in ((-1, P_["red"]), (1, P_["blue"])):
        blob(cv, [(side * 6 * s, -24 * s), (side * 46 * s, -24 * s - L), (side * 18 * s, -30 * s - L), (side * -8 * s, -34 * s)], col, w=3.5, seed=seed + side, boil=0.6, n=3)
    blob(cv, ell(0, 0, 50 * s, 50 * s, n=14), P_["gold"], w=4.5, seed=seed + 3, boil=0.7,
         shade=lambda c: (c.drawCircle(-12 * s, -14 * s, 24 * s, paint(P_["yellow"])), c.drawCircle(16 * s, 18 * s, 26 * s, paint(mix(P_["gold"], P_["orange"], 0.5), 160))))
    star = [(0, -30 * s), (8 * s, -10 * s), (29 * s, -10 * s), (12 * s, 4 * s), (19 * s, 25 * s), (0, 12 * s), (-19 * s, 25 * s), (-12 * s, 4 * s), (-29 * s, -10 * s),
            (-8 * s, -10 * s)]
    blob(cv, star, P_["yellow"], w=2.5, seed=seed + 4, boil=0.5, n=2)
    sparkle(cv, 30 * s, -34 * s, 16 * s + 4, P_["white"], w=2, seed=seed + 5)
    cv.restore()


def laurel(cv, x, y, rr, seed=0, k=1.0):
    """A laurel wreath sitting on top of a head like a crown (x, y = centre of the arc, rr = half-width)."""
    if k <= 0.01:
        return
    cv.save(); cv.translate(x, y); cv.scale(k, k)
    for side in (-1, 1):
        for j in range(6):
            a_ = math.radians(90 - side * (12 + j * 15))
            px, py = rr * math.cos(a_), -rr * 0.42 * math.sin(a_)
            la = -side * (20 + j * 15)
            leaf = rot(np.array([(0, -20), (10, 0), (0, 20), (-10, 0)], float), la + 90) + np.array([px, py])
            blob(cv, leaf, [P_["acid"], P_["acid_dk"]][j % 2], w=3, seed=seed + j * 2 + side, boil=0.5, n=3)
    for q in range(3):
        sparkle(cv, -rr * 0.8 + q * rr * 0.8, -rr * 0.7 - 8 * math.sin(q * 2 + seed), 12, P_["yellow"], w=2, seed=seed + 50 + q)
    cv.restore()


def scroll_banner(cv, text, x, y, wdt, k, seed=0, size=120, font="shrik", fills=None):
    """A cream ribbon scroll with folded ends carrying painted text; slams in with k."""
    if k <= 0.01:
        return
    cv.save(); cv.translate(x, y); cv.scale(k, k); cv.rotate(-2 + 2 * math.sin(seed))
    h2 = size * 0.62
    for side in (-1, 1):
        blob(cv, [(side * wdt / 2 * 0.86, -h2 * 0.6), (side * (wdt / 2 + 90), -h2 * 0.8), (side * (wdt / 2 + 50), 0), (side * (wdt / 2 + 90), h2 * 0.9),
                  (side * wdt / 2 * 0.86, h2 * 0.75)], P_["cream_sh"], w=5, seed=seed + side, boil=0.8, n=3)
    blob(cv, [(-wdt / 2, -h2), (0, -h2 - 16), (wdt / 2, -h2), (wdt / 2, h2), (0, h2 - 14), (-wdt / 2, h2)], P_["cream"], w=6, seed=seed + 3, boil=0.9, n=4)
    paint_text(cv, text, 0, size * 0.36, font=font, size=size, fills=fills or [P_["orange"], P_["yellow"]], ink_w=6, shadow=(7, 7), shadow_rgb=P_["magenta"],
               seed=seed + 4, wobble=2.0, drips=0.8)
    cv.restore()


def clap_arms(t, k=0, rate=13.0, up=False):
    """Arms dict for pris(): chained hands clapping in front (or waving overhead when up=True)."""
    if up:
        ph = t * 9.0 + k
        return dict(l=(-1.25 + 0.15 * math.sin(ph), -1.0 - 0.2 * math.sin(ph * 1.3)), r=(1.25 + 0.15 * math.sin(ph + 1.5), -1.0 - 0.2 * math.sin(ph * 1.3 + 1)),
                    ang=(-110, -70), pose="spread", cuffs=True)
    op = 0.5 + 0.5 * math.sin(t * rate + k * 1.7)
    return dict(l=(-0.2 - 0.45 * op, 0.84), r=(0.2 + 0.45 * op, 0.84), ang=(-10, -170), pose="flat", cuffs=True)


# ===================================================================== T020  SHADOWPLAY + Z11
def _show(t):
    """The lively shadow show (POV wall coords): a hopping bunny, a flapping bird, a galloping horse, a hand-bunny cameo."""
    sl = []
    ph = t * 2.1
    hop = abs(math.sin(math.pi * ph))
    sl.append(("bunny_s", 1750 - 330 * t, 690 - hop * 240, 2.0, -1, 0.84 + 0.3 * hop))
    sl.append(("bird_up" if int(t * 10) % 2 else "bird_dn", -150 + 640 * t, 300 + 50 * math.sin(t * 2.5), 1.6, 1))
    if t > 1.0:
        sl.append(("horse_a" if int(t * 8) % 2 else "horse_b", 2350 - 560 * (t - 1.0), 760 - abs(math.sin(t * 8)) * 26, 2.1, -1))
    if t > 2.3:
        u = ease((t - 2.3) / 0.5)
        sl.append(("hand_bunny", 260, 1180 - 330 * u, 1.9, 1, 1.0, 6 * math.sin(t * 9)))
    return sl


def T020_shadowplay(cv, t, T, A):
    if t < 3.6:                                                    # SHADOWPLAY: the show + cheering heads (their POV)
        pulse = 0.5 + 0.5 * math.sin(t * 2 * math.pi * 2.0)
        cam = dict(x=10 * math.sin(t * 0.8), y=-6, z=1.02 + 0.015 * pulse)
        pov_wall(cv, T, cam, shadows=_show(t), cheer=1.0, bounce=0.7, heads=7)
        for j, (t0, x, y, txt) in enumerate(((0.5, 420, 600, "YAY!"), (1.3, 1480, 560, "WOO!"), (2.2, 960, 620, "BUNNY!!"), (2.9, 1660, 600, "YAY!"))):
            sfx(cv, txt, x, y, 64, t, t0, fill=[P_["yellow"], P_["hotpink"], P_["acid"], P_["yellow"]][j], seed=7000 + j, ang=-8 + 6 * j, hold=0.55)
        vignette(cv, a=110)
        return
    if t < 7.06:                                                   # their faces: pure joy (reverse angle)
        lt = t - 3.6
        cam = dict(x=8 * math.sin(t), y=210 - 40 * ease(lt / 3.4), z=1.42 - 0.08 * ease(lt / 3.4))
        refl = lambda c, ex, ey, er: shadow_shape(c, "bunny", ex + er * (0.35 - 0.7 * ((t * 0.6) % 1.0)), ey - er * 0.3, er * 0.004, T, a=200, seed=7050)
        pl = [dict(arms=clap_arms(t, k, up=True), mouth=0.55 + 0.25 * math.sin(t * 7 + k), sparkle=1.0, eye_k=1.15, look=(0.0, -0.15), refl_top=refl,
                   squash=(1.0 + 0.04 * math.sin(t * 14 + k), 1.0 - 0.04 * math.sin(t * 14 + k))) for k in range(6)]
        carriers = [dict(x=470, kind="bunny", face=1, walk=True, phase=0.0, statue_k=1.25), dict(x=960, kind="horse", face=-1, walk=True, phase=0.6, statue_k=1.25),
                    dict(x=1450, kind="bird", face=-1, walk=True, phase=1.2, statue_k=1.25)]
        for k, cd in enumerate(carriers):
            cd["raise"] = 0.82 + 0.18 * math.sin(t * 7 + k * 2)

        def conf(c):
            for j in range(26):
                x = (j * 97 + 40 * math.sin(t * 2 + j)) % 1900 + 10
                y = 700 + ((j * 53 + t * (120 + 40 * (j % 3))) % 420)
                sparkle(c, x, y, 7 + 4 * (j % 3), [P_["yellow"], P_["hotpink"], P_["mint"], P_["white"]][j % 4], w=1.5, seed=7060 + j)
        rev_view(cv, T, cam, carriers=carriers, prisoners=pl, fire=1.15, hooks=dict(front=conf))
        C = sets.Cam(cv, cam)
        for j, (t0, k, txt) in enumerate(((4.25, 1, "WOOO!"), (5.35, 4, "AGAIN!"))):
            px, py = C.to_screen(190 + k * 308, 1065 - 160, 1.0)
            bubble(cv, px + (160 if k < 3 else -160), py - 210, txt, (px, py - 60), pop(t, t0, 0.3) * (1 - ease((t - t0 - 1.2) / 0.3)), seed=7080 + j, size=58)
        vignette(cv, a=120)
        return
    if t < 13.15:                                                  # their reality: REALITY / names / study
        lt = t - 7.06
        cam = dict(x=6 * math.sin(t * 0.5), y=0, z=1.0 + 0.04 * ease(lt / 6.0))
        hop = abs(math.sin(math.pi * t * 1.6))
        bun = (420, 640 - hop * 90)
        hor = (1060, 720 - abs(math.sin(t * 7)) * 14)
        bird = (1580, 430 + 30 * math.sin(t * 2.2))
        sl = [("bunny_s", bun[0], bun[1], 1.9, 1, 0.9 + 0.2 * hop), ("horse_a" if int(t * 6) % 2 else "horse_b", hor[0], hor[1], 2.0, -1),
              ("bird_up" if int(t * 8) % 2 else "bird_dn", bird[0], bird[1], 1.5, -1)]

        def study(c):
            scroll_banner(c, "REALITY", 960, 255, 740, pop(t, 8.95, 0.4), seed=7100, size=118)
            if t > 8.95:
                for j in range(6):
                    sparkle(c, 960 + 520 * math.cos(j * 1.05 + t), 255 + 120 * math.sin(j * 1.05 + t), 14 * pop(t, 8.95, 0.4), P_["yellow"], seed=7110 + j)
            name_tag(c, "MR. HOPS", 285, 470, pop(t, 10.62, 0.3), bun[0] - 90, bun[1] - 20, seed=7120, ang=-8)
            name_tag(c, "BARRY THE HORSE", 1250, 520, pop(t, 10.85, 0.3), hor[0] + 60, hor[1] - 70, seed=7130, ang=5)
            name_tag(c, "SHEILA", 1660, 610, pop(t, 11.08, 0.3), bird[0] + 30, bird[1] + 20, seed=7140, ang=-4)
            ks = float(np.clip((t - 11.9) / 0.9, 0, 1))
            if ks > 0:                                             # study scribbles
                chalk(c, [(bun[0] - 60, bun[1] - 300), (bun[0] - 20, bun[1] - 300)], ks * 3, seed=7150)
                chalk(c, [(bun[0] - 40, bun[1] - 300), (bun[0] - 40, bun[1] - 90)], ks * 2.2, seed=7151)
                chalk(c, [(bun[0] - 60, bun[1] - 90), (bun[0] - 20, bun[1] - 90)], ks * 3 - 0.6, seed=7163)
                chalk_text(c, "EARS: 2", bun[0] - 200, bun[1] - 190, ks * 2, size=50, seed=7152, ang=-6)
                arc = [(bun[0] - 220 + 440 * u, bun[1] + 60 - 260 * math.sin(math.pi * u)) for u in np.linspace(0, 1, 9)]
                for j, (ax_, ay_) in enumerate(arc):
                    if j / 8 < ks * 1.3:
                        dots(c, [(ax_, ay_)], 5, P_["white"], a=220)
                chalk_text(c, "HOP?!", bun[0] + 210, bun[1] - 120, ks * 1.6, size=50, seed=7153, ang=8)
                chalk(c, [(hor[0] - 300, hor[1] - 220), (hor[0] - 160, hor[1] - 260), (hor[0] - 120, hor[1] - 160), (hor[0] - 260, hor[1] - 120), (hor[0] - 300, hor[1] - 220)],
                      ks * 1.4, seed=7154)
                chalk_text(c, "LEGS = 4??", hor[0] + 300, hor[1] - 10, ks * 1.5, size=50, seed=7155, ang=-3)
                chalk_text(c, "BUNNY", 640, 850, ks * 2.0, size=46, seed=7156)
                chalk(c, [(745, 835), (835, 835)], ks * 2.0 - 0.3, seed=7157)
                chalk(c, [(815, 820), (838, 835), (815, 850)], ks * 2.0 - 0.4, seed=7158)
                chalk_text(c, "HORSE", 935, 850, ks * 2.0 - 0.5, size=46, seed=7159)
                chalk(c, [(1040, 835), (1130, 835)], ks * 2.0 - 0.7, seed=7160)
                chalk(c, [(1110, 820), (1133, 835), (1110, 850)], ks * 2.0 - 0.8, seed=7161)
                chalk_text(c, "???", 1190, 855, ks * 2.0 - 0.9, size=56, seed=7162)
        pov_wall(cv, T, cam, shadows=sl, hooks=dict(wall=study), heads=7)
        vignette(cv, a=110)
        return
    # 'They even hand out honors to whoever's quickest at guessing which shadow comes next'
    lt = t - 13.15
    cam = dict(x=6 * math.sin(t * 0.6), y=190, z=1.42 + 0.06 * ease(lt / 5.0))
    xs = [380, 670, 960, 1250, 1540]
    won = t >= 15.2
    clap = t >= 15.4
    pl = []
    for k, x in enumerate(xs):
        d = dict(x=x, y=1065 + 10 * (k % 2), s=1.15)
        if k == 2:                                                 # the quickest guesser
            d["mouth"] = 0.8 * (abs(math.sin(t * 12)) if 13.5 < t < 14.3 else 0.0) + (0.6 if won else 0.0)
            d["sparkle"] = 1.0 if won else 0.0
            d["eye_k"] = 1.15 if won else 1.0
            d["look"] = (0.0, -0.2)
            if won:
                d["arms"] = clap_arms(t, 0, up=True)
        else:
            d["look"] = ((1.0 if k < 2 else -1.0) if 13.6 < t < 15.2 else 0.0, 0.1)
            d["eye_k"] = 1.0 + 0.2 * ease((t - 14.5) / 0.3)
            if clap:
                d["arms"] = clap_arms(t, k)
                d["mouth"] = 0.35 + 0.2 * math.sin(t * 9 + k)
        if t > 14.4:
            d["refl_top"] = lambda c, ex, ey, er: shadow_shape(c, "horse", ex - er * 0.15, ey - er * 0.32, er * 0.0032, T, a=210, seed=7200)
        pl.append(d)
    raise_h = pop(t, 14.15, 0.35)
    carriers = [dict(x=700, kind="horse", face=1, walk=False, phase=0.4, statue_k=1.25 * max(0.01, raise_h))]
    carriers[0]["raise"] = 0.5 + 0.5 * raise_h

    def honours(c):
        gx, gy, r = 960, 1065, 70 * 1.15
        cy_ = gy - 1.15 * r
        if t > 15.0:                                               # medal drops in on its ribbon
            u = float(np.clip((t - 15.0) / 0.3, 0, 1))
            my = -300 + (cy_ + r * 0.8 + 300) * (u * u) - (math.sin(min(1.0, max(0.0, (t - 15.3) / 0.35)) * math.pi) * 22 if t > 15.3 else 0)
            medal(c, gx + 22 + 5 * math.sin(t * 5), my, 0.62, ang=6 * math.sin(t * 4), seed=7210, ribbon=0.55)
        laurel(c, gx, cy_ - r * 1.08, r * 0.95, seed=7220, k=pop(t, 15.55, 0.35))
        if clap:
            for k, x in enumerate(xs):
                if k == 2:
                    continue
                if math.sin(t * 13.0 + k * 1.7) < -0.85:           # clap impact marks (at the hands, below the eye)
                    hy = 1065 + 10 * (k % 2) - 1.15 * 70 * 1.15 + 0.84 * 70 * 1.15
                    for j in range(5):
                        a_ = math.pi / 2 + (j - 2) * 0.5
                        c.drawLine(x + 34 * math.cos(a_), hy + 34 * math.sin(a_), x + 62 * math.cos(a_), hy + 62 * math.sin(a_), paint(P_["yellow"], 230, stroke=5))
            for j in range(30):                                    # confetti
                x = (j * 89 + 30 * math.sin(t * 2 + j)) % 1900 + 10
                y = 560 + ((j * 47 + (t - 15.4) * (220 + 60 * (j % 3))) % 620)
                ang = t * 6 + j
                dx, dy = 12 * math.cos(ang), 6 * math.sin(ang * 1.3)
                c.drawPath(poly_path([(x - dx, y - dy), (x + dy, y - dx), (x + dx, y + dy), (x - dy, y + dx)]),
                           paint([P_["magenta"], P_["yellow"], P_["teal"], P_["acid"], P_["orange"]][j % 5]))
    rev_view(cv, T, cam, carriers=carriers, prisoners=pl, fire=1.0, hooks=dict(front=honours))
    C = sets.Cam(cv, cam)
    gx_s, gy_s = C.to_screen(960, 1065 - 70 * 1.15 * 1.4, 1.0)
    bubble(cv, gx_s + 300, gy_s - 260, "HORSE!", (gx_s + 30, gy_s - 40), pop(t, 13.5, 0.3) * (1 - ease((t - 14.9) / 0.25)), seed=7230, size=80)
    for k, x in enumerate(xs):
        if k != 2 and 13.9 < t < 15.0:
            px, py = C.to_screen(x, 1065 - 70 * 1.15 * 2.6, 1.0)
            paint_text(cv, "?", px, py, font="bangers", size=70 * pop(t, 13.9 + 0.08 * k, 0.3), fill=P_["cream"], ink_w=3.5, shadow=(3, 3), seed=7240 + k)
    sfx(cv, "DING!", 1520, 300, 120, t, 15.2, fill=P_["yellow"], seed=7250, ang=8, hold=0.7)
    scroll_banner(cv, "QUICKEST GUESSER!", 960, 160, 900, pop(t, 15.9, 0.4), seed=7260, size=74, font="bangers", fills=[P_["magenta"], P_["blue"]])
    vignette(cv, a=120)
