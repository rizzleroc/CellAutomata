"""BOXED ep4 'THE CAVE' -- owner 'out': the payoff.

T049_education  Zee: education isn't a funnel crammed into an empty head (red X) or eyes painted onto a blank face
                (red X) -- the power to see is already inside (a little eye of light in the chest); the luminous soul
                turns all the way around, away from the shadows, toward the light, and colour blooms out of the light
                (POST hook: a violet duotone everywhere the bloom has not reached yet).
T051_turn       the host's TV head swivels 180 deg (the back of the set: vents, power cord, PROPERTY OF THE CAVE
                sticker); the studio rumbles and the cosmic backdrop cracks and slides apart like stone doors onto a
                cave mouth and a blazing sunrise; god rays, dust motes, everyone lit gold.
T052_outside    the funk-gospel finale (108 BPM): the host, Zee, Gary in tiny sunglasses and the unchained eyeball
                audience parade up out of the cave into a psychedelic sunrise; flowers bloom where they pass; the
                ringed sun-planet grins; it ends on a hilltop group tableau with the sun behind them.
"""
from .shots_ep4_base import *                      # noqa: F401,F403
from contextlib import contextmanager
from .zee import _hand
from .acting import ik
from . import cast as _cast
from . import zee as _zee

SCREEN_B = skia.BlendMode.kScreen
PLUS_B = skia.BlendMode.kPlus
ATOP_B = skia.BlendMode.kSrcATop


# ===================================================================== small shared helpers
@contextmanager
def at(cv, x, y, s=1.0, rot=0.0, sx=None):
    """Local drawing frame at (x, y), scaled by s (sx overrides the x scale, e.g. to mirror); pen weight compensated."""
    old = core.INKMUL
    cv.save()
    cv.translate(x, y)
    if rot:
        cv.rotate(rot)
    cv.scale(s if sx is None else sx, s)
    core.INKMUL = old / max(abs(s), 0.05) ** 0.5
    try:
        yield
    finally:
        core.INKMUL = old
        cv.restore()


def radial(cv, x, y, r, cols, stops=None, blend=None, rect=None):
    """Radial gradient disc (cols = list of (rgb, a)); optional blend mode; rect fills a rect instead of the disc."""
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(float(x), float(y)), max(1.0, float(r)), [core.C(c, a) for c, a in cols], stops))
    if blend is not None:
        p.setBlendMode(blend)
    if rect is not None:
        cv.drawRect(R(*rect), p)
    else:
        cv.drawCircle(float(x), float(y), float(r), p)


def glow_stroke(cv, path, rgb, wdt, blur, a=255, blend=None):
    p = skia.Paint(AntiAlias=True, Color=core.C(rgb, a))
    p.setStyle(skia.Paint.kStroke_Style)
    p.setStrokeWidth(float(wdt))
    p.setStrokeCap(skia.Paint.kRound_Cap)
    p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, float(blur)))
    if blend is not None:
        p.setBlendMode(blend)
    cv.drawPath(path, p)


def glow_fill(cv, path, rgb, blur, a=255, blend=None):
    p = skia.Paint(AntiAlias=True, Color=core.C(rgb, a))
    if blur > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, float(blur)))
    if blend is not None:
        p.setBlendMode(blend)
    cv.drawPath(path, p)


def quad(cv, pts, rgb, a=255):
    cv.drawPath(poly_path(pts), paint(rgb, a))


def ease_io(u):
    u = min(max(float(u), 0.0), 1.0)
    return u * u * u * (u * (u * 6 - 15) + 10)


def seg(t, t0, t1):
    """0..1 linear progress of t through [t0, t1] (clamped)."""
    return float(np.clip((t - t0) / max(1e-6, t1 - t0), 0.0, 1.0))


def shake(amp, seed=0):
    return ((float(hsh(core.D * 1.37 + seed)) - 0.5) * 2 * amp, (float(hsh(core.D * 2.11 + seed + 7)) - 0.5) * 2 * amp)


def arm_ik(S, Tg, l1, l2, side):
    sh, el, _ = ik(S, Tg, l1, l2, side)
    return sh, el


def limb(cv, S, Tg, l1, l2, side, width, rgb, seed, w=4.5):
    """A two-bone rubber-hose arm/leg from S toward target Tg; returns (wrist, forearm direction deg)."""
    sh, el = arm_ik(S, Tg, l1, l2, side)
    (ex, ey), (wx, wy), fdir = _zee.arm_points(S[0], S[1], sh, el, l1, l2)
    tube(cv, [S, (ex, ey), (wx, wy)], width, rgb, w=w, seed=seed, boil=0.9, n=8)
    return (wx, wy), fdir


def book(cv, x, y, wd, ht, ang, rgb, seed=0, title=True):
    """A chunky hardback book centred at x, y (rotated ang degrees)."""
    cv.save()
    cv.translate(x, y)
    cv.rotate(ang)
    blob(cv, rect_pts([(-wd / 2 + 6, -ht / 2 + 6), (wd / 2 + 6, -ht / 2 + 6), (wd / 2 + 6, ht / 2 + 6), (-wd / 2 + 6, ht / 2 + 6)], 2), P_["cream"], w=3.5,
         seed=seed + 1, boil=0.6, n=3, shade=lambda c: [c.drawLine(-wd / 2, -ht / 2 + 9 + k * 5, wd / 2 + 8, -ht / 2 + 9 + k * 5, paint(P_["cream_sh"], stroke=1.6))
                                                        for k in range(int(ht / 5))])
    blob(cv, rect_pts([(-wd / 2, -ht / 2), (wd / 2, -ht / 2), (wd / 2, ht / 2), (-wd / 2, ht / 2)], 2), rgb, w=4.0, seed=seed, boil=0.7, n=3,
         shade=lambda c: (c.drawRect(R(-wd / 2, -ht / 2, -wd / 2 + wd * 0.16, ht / 2), paint(mix(rgb, INK, 0.3))),
                          c.drawRect(R(-wd / 2 + wd * 0.3, -ht * 0.18, wd / 2 - wd * 0.12, ht * 0.02), paint(mix(rgb, P_["yellow"], 0.6))) if title else None))
    cv.restore()


BOOK_COLS = [P_["red"], P_["blue"], P_["magenta"], P_["teal"], P_["orange"], P_["acid_dk"], P_["violet"]]


def paint_stroke(cv, C, wd, rgb, seed, u=1.0, ink=True, dry=True, under=None):
    """A loaded-brush paint stroke along the dense centreline C (first fraction u shown): ink edge, flat paint, bristle
    streaks (lighter + darker) that run dry toward the tail, a split dry-brush tail and a pooled blob where it landed.
    under(cv, 'ink'|'paint') is called between the ink and paint passes (for drips that must join the outline)."""
    m = max(3, int(len(C) * u))
    C = C[:m]
    tail = 0.25 if u >= 1 else 0.04
    if ink:
        brush(cv, C, wd + 10, INK, taper=(0.06, tail), var=0.18, seed=seed, minw=0.5)
        cv.drawCircle(float(C[0][0]), float(C[0][1]), wd * 0.5 + 5, paint(INK))
    if under is not None:
        under(cv, "ink")
    brush(cv, C, wd, rgb, taper=(0.06, tail), var=0.18, seed=seed, minw=0.5)
    cv.drawCircle(float(C[0][0]), float(C[0][1]), wd * 0.5, paint(rgb))
    if under is not None:
        under(cv, "paint")
    N = core._normals(C, False)
    n = len(C)
    for j in range(9):
        off = -0.38 + 0.095 * j + 0.03 * float(hsh(seed + j))
        light = j % 3 != 2
        col = mix(rgb, P_["white"], 0.25 + 0.25 * float(hsh(seed + 30 + j))) if light else mix(rgb, INK, 0.35)
        i0 = int(n * 0.04 * float(hsh(seed + 50 + j)))
        i1 = int(n * (0.72 + 0.28 * float(hsh(seed + 70 + j)))) if (dry and u >= 1) else n
        if i1 - i0 > 3:
            brush(cv, C[i0:i1] + N[i0:i1] * (off * wd), wd * (0.035 + 0.05 * float(hsh(seed + 90 + j))), col, taper=(0.2, 0.5), var=0.5,
                  seed=seed + 5 + j, a=190 if light else 150)
    if u >= 1 and dry:                                              # dry-brush split at the tail
        d = C[-1] - C[-4]
        d = d / (np.hypot(*d) + 1e-6)
        nn = np.array([-d[1], d[0]])
        for j in range(4):
            o = (-0.3 + 0.2 * j) * wd
            p0 = C[-6] + nn * o
            p1 = C[-1] + d * wd * (0.3 + 0.4 * float(hsh(seed + 110 + j))) + nn * o * 1.3
            line(cv, [p0, p1], wd * 0.12, rgb, seed=seed + 120 + j, boil=0.5, n=2, taper=(0.0, 0.8))
    return C


def red_x(cv, cx, cy, size, k, seed=0):
    """A big hand-painted red X: stroke 1 paints on over k 0..0.42, stroke 2 over 0.5..0.92, then drips run."""
    if k <= 0:
        return
    strokes = [[(-0.5, -0.42), (-0.16, -0.12), (0.18, 0.17), (0.5, 0.44)], [(0.46, -0.46), (0.14, -0.13), (-0.18, 0.15), (-0.48, 0.45)]]
    wd = size * 0.12
    for j, ctrl in enumerate(strokes):
        u = float(np.clip((k - j * 0.5) / 0.42, 0, 1))
        if u <= 0:
            continue
        P = np.array([(cx + px * size, cy + py * size) for px, py in ctrl])
        Cp = cr_open(jit(P, size * 0.005, seed + j * 7), 22)
        drips = []
        if u >= 1.0:                                                  # drips run from the lower edge
            dk = float(np.clip((k - j * 0.5 - 0.42) / 0.9, 0, 1))
            Nn = core._normals(Cp, False)
            for d in range(5):
                f = 0.15 + 0.17 * d + 0.05 * float(hsh(seed + d + j * 10))
                i = int(f * (len(Cp) - 1))
                nrm = Nn[i] if Nn[i][1] > 0 else -Nn[i]
                px, py = Cp[i] + nrm * wd * 0.3
                L = size * (0.05 + 0.14 * float(hsh(seed + d * 3 + j))) * (0.25 + 0.75 * dk)
                dw = wd * (0.1 + 0.06 * float(hsh(seed + d * 5 + j)))
                dp = skia.Path()
                dp.moveTo(px - dw * 1.4, py - dw * 2.5)
                dp.cubicTo(px - dw * 0.8, py + L * 0.4, px - dw * 0.5, py + L * 0.8, px - dw * 0.55, py + L)
                dp.lineTo(px + dw * 0.55, py + L)
                dp.cubicTo(px + dw * 0.5, py + L * 0.8, px + dw * 0.8, py + L * 0.4, px + dw * 1.4, py - dw * 2.5)
                dp.close()
                dp.addCircle(px, py + L, dw * 0.9)
                drips.append((dp, px, py + L, dw))

        def under(c, phase, drips=drips):
            for dp, px, py, dw in drips:
                if phase == "ink":
                    c.drawPath(dp, paint(INK, stroke=10))
                else:
                    c.drawPath(dp, paint(P_["red"]))
                    c.drawCircle(px - dw * 0.3, py - dw * 0.2, dw * 0.3, paint(mix(P_["red"], P_["white"], 0.45), 200))
        paint_stroke(cv, Cp, wd, P_["red"], seed + j * 20, u=u, under=under)
        if u >= 1.0:
            for d in range(9):
                a = float(hsh(seed + 40 + d + j * 20)) * 6.283
                rr = wd * (0.8 + 1.6 * float(hsh(seed + 60 + d + j)))
                ex, ey = Cp[-1] if d % 2 else Cp[0]
                r_ = 3 + 9 * float(hsh(seed + 80 + d + j))
                dots(cv, [(ex + rr * math.cos(a), ey + rr * math.sin(a))], r_ + 2.5, INK)
                dots(cv, [(ex + rr * math.cos(a), ey + rr * math.sin(a))], r_, P_["red"])


def iris_wipe(cv, cx, cy, r):
    """Classic cartoon iris: black everywhere outside a circle of radius r (wobbly ink ring)."""
    p = skia.Path()
    p.addRect(R(-50, -50, W + 50, H + 50))
    if r > 1:
        q = poly_path(cr_closed(jit(ell(cx, cy, r, r, n=24), 2.0, 9000), 3))
        p = skia.Op(p, q, skia.PathOp.kDifference_PathOp) or p
    cv.drawPath(p, paint((8, 4, 16)))
    if r > 1:
        brush(cv, cr_closed(jit(ell(cx, cy, r, r, n=24), 2.0, 9000), 3), 9, closed=True, seed=9001)


# ===================================================================== T049: the lesson
T49_CUT1 = 1.30          # Zee CU -> classroom
T49_X1 = 5.30            # first red X
T49_PAN = (5.72, 6.02)   # whip-pan classroom -> doctor
T49_X2 = 7.50            # second red X
T49_IRIS = (7.92, 8.18)  # iris out on the patient's chest
SOUL_T0 = 8.18           # darkness: the little light inside
TURN = (11.55, 14.35)    # 'Learning is turning the whole soul around'
AWAY = (14.85, 16.25)    # 'away from the shadows'
TOWARD = (16.75, 17.75)  # 'toward the light'
BLOOM = (12.4, 17.7)


def _wallpaper(cv, box, base, cols, t, seed, step=150, amp=26, wdt=40):
    x0, y0, x1, y1 = box
    cv.drawRect(R(x0, y0, x1, y1), paint(base))
    for k in range(int((x1 - x0) / step) + 2):
        xs = x0 + k * step
        pts = np.array([(xs + amp * math.sin(y * 0.011 + k * 1.3 + t * 0.6), y) for y in np.linspace(y0 - 20, y1 + 20, 14)])
        brush(cv, cr_open(pts, 6), wdt, cols[k % len(cols)], taper=(0.01, 0.01), var=0.12, seed=seed + k)
        dots(cv, [(xs + step / 2 + amp * 0.6 * math.sin(y * 0.02 + k), y) for y in np.arange(y0 + 30, y1, 70)], 5, cols[(k + 1) % len(cols)], a=200)


def _checker_floor(cv, y0, cols, seed, vx=960, n=9, rows=6, y1=H + 40, tile=210):
    """A perspective checkerboard floor from the line y0 down past the frame (columns converge on a vanishing point)."""
    vy = y0 - 700
    cv.drawRect(R(-60, y0, W + 60, y1), paint(cols[0]))
    ys = [y0 + (y1 - y0) * ((k / rows) ** 1.6) for k in range(rows + 1)]

    def X(xb, yy):
        return vx + (xb - vx) * (yy - vy) / (y1 - vy)
    for r in range(rows):
        for c in range(-n, n + 1):
            if (r + c) % 2:
                continue
            xb0 = vx + (c - 0.5) * tile
            xb1 = xb0 + tile
            quad(cv, [(X(xb0, ys[r]), ys[r]), (X(xb1, ys[r]), ys[r]), (X(xb1, ys[r + 1]), ys[r + 1]), (X(xb0, ys[r + 1]), ys[r + 1])], cols[1])
    line(cv, [(-60, y0), (W + 60, y0)], 5, seed=seed, boil=0.8, n=2, taper=(0, 0))


def _classroom_bg(cv, T, t):
    _wallpaper(cv, (-80, -80, W + 80, 940), P_["orange"], [P_["magenta"], P_["yellow"], P_["hotpink"]], T, 7100)
    radial(cv, 900, 300, 1100, [(P_["yellow"], 120), (P_["yellow"], 0)])
    # the chalkboard
    bx0, by0, bx1, by1 = 70, 60, 1850, 640
    blob(cv, rect_pts([(bx0 - 30, by0 - 30), (bx1 + 30, by0 - 30), (bx1 + 30, by1 + 34), (bx0 - 30, by1 + 34)], 3), (176, 70, 40), w=6, seed=7110, boil=1.0, n=3,
         shade=lambda c: [c.drawLine(bx0 - 40, by0 - 18 + k * 9, bx1 + 40, by0 - 18 + k * 9, paint((150, 52, 30), stroke=2)) for k in range(3)])
    board = (14, 84, 78)
    blob(cv, rect_pts([(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)], 3), board, w=5, seed=7111, boil=0.9, n=3,
         shade=lambda c: (radial(c, 700, 300, 900, [(mix(board, P_["teal"], 0.25), 255), (board, 255)]),
                          [line(c, [(bx0 + 60 + k * 230, by0 + 40 + 30 * math.sin(k)), (bx0 + 200 + k * 230, by0 + 120 + 40 * math.cos(k * 1.7))], 30,
                                mix(board, P_["white"], 0.12), seed=7112 + k, boil=0.6, n=3, a=120) for k in range(8)]))
    chalk = (236, 246, 232)
    cht = lambda s, x, y, sz, sd, f="marker", rot_jit=5.0, a=215: paint_text(cv, s, x, y, font=f, size=sz, fill=chalk, ink_w=0, shadow=None, seed=sd,
                                                                            wobble=1.0, streaks=False, a=a, rot_jit=rot_jit)
    cht("2+2=5", 1520, 170, 64, 7120)
    cht("A  B  C", 1500, 290, 58, 7121)
    cht("?!", 380, 520, 80, 7122)
    brush(cv, cr_closed(jit(ell(1260, 480, 46, 46, n=10), 1.5, 7131), 4), 3.5, chalk, closed=True, seed=7132, a=200)
    brush(cv, cr_closed(jit(ell(1260, 480, 92, 22, n=12, rot=-12), 1.5, 7133), 4), 3.0, chalk, closed=True, seed=7134, a=170)
    brush(cv, cr_closed(jit([(150, 300), (205, 270), (260, 300), (205, 330)], 1.2, 7135), 6), 3.5, chalk, closed=True, seed=7136, a=200)
    dots(cv, [(205, 300)], 11, chalk, a=200)
    line(cv, [(1650, 400), (1650, 470), (1625, 520)], 3.5, chalk, seed=7137, boil=1, n=3, a=200)
    line(cv, [(1650, 470), (1675, 520)], 3.5, chalk, seed=7138, boil=1, n=2, a=200)
    line(cv, [(1615, 430), (1685, 430)], 3.5, chalk, seed=7139, boil=1, n=2, a=200)
    brush(cv, cr_closed(jit(ell(1650, 380, 20, 20, n=8), 1.2, 7140), 4), 3.5, chalk, closed=True, seed=7141, a=200)
    # EDUCATION (chalked in on the word)
    r = seg(t, 2.45, 3.25)
    if r > 0:
        paint_text(cv, "EDUCATION", 420, 205, font="marker", size=104, fill=chalk, ink_w=0, shadow=None, seed=7150, wobble=1.0, streaks=False,
                   reveal=r, stagger=0.07, a=235)
        if r >= 1:
            line(cv, [(150, 235), (420, 245), (700, 232)], 6, chalk, seed=7151, boil=1.0, n=4, taper=(0.1, 0.3), a=210)
    # Dali clock dripping off the top-right corner of the board frame
    melting_clock(cv, 1835, 95, 0.9, phase=T * 1.3, seed=7160)
    # a ringed-planet globe on a little stand, far left
    line(cv, [(150, 905), (150, 780)], 8, (120, 70, 40), seed=7170, boil=0.5, n=2, taper=(0, 0))
    blob(cv, ell(150, 910, 60, 14, n=10), (150, 90, 50), w=4, seed=7171, boil=0.6)
    w.planet(cv, 150, 735, 62, P_["teal"], bands=[(-0.4, 0.25, P_["acid"]), (0.15, 0.25, P_["blue"])], ring=dict(rx=1.6, ry=0.3, rgb=P_["magenta"], rgb2=P_["yellow"], tilt=-20),
             seed=7172, crater=False)
    _checker_floor(cv, 920, [P_["violet"], P_["magenta"]], 7180)


def _teacher(cv, x, y, s, T, hand_w, shove, seed=7200):
    """The old-timey schoolmaster (feet at x, y; faces left): frock coat, waistcoat, walrus moustache, pince-nez,
    mortarboard. hand_w = world target of his front (book) hand; shove 0..1 = how hard he is ramming it in."""
    bob = -10 * shove
    lean = -6 - 6 * shove
    with at(cv, x, y, s):
        loc = ((hand_w[0] - x) / s, (hand_w[1] - y) / s)
        coat, coat_sh = (58, 22, 112), (36, 12, 74)
        for side, lx in ((-1, -26), (1, 22)):                          # striped legs + pointy shoes
            tube(cv, [(lx, -250), (lx - 4, -120), (lx - 2, -18)], 26, (140, 130, 176), w=4.5, seed=seed + side, boil=0.8, n=5)
            for k in range(6):
                yy = -230 + k * 36
                line(cv, [(lx - 12, yy), (lx + 12, yy + 3)], 3, (80, 70, 120), seed=seed + 5 + k + side * 9, boil=0.4, n=2, taper=(0, 0), a=200)
            blob(cv, [(lx + 16, -4), (lx - 54, -6), (lx - 70, -16), (lx - 44, -28), (lx + 18, -28)], (30, 22, 44), w=4.5, seed=seed + 20 + side, boil=0.6, n=4)
        cv.save()
        cv.rotate(lean, 0, -250)
        cv.translate(0, bob)
        body = [(-36, -575), (-82, -548), (-100, -470), (-96, -350), (-78, -232), (-20, -224), (92, -150), (104, -250), (96, -360), (84, -470), (74, -548), (36, -580)]
        blob(cv, body, coat, w=6, seed=seed + 30, boil=1.1, n=6,
             shade=lambda c: (c.drawPath(poly_path(cr_closed([(30, -580), (110, -540), (120, -150), (50, -200), (60, -400)], 4)), paint(coat_sh)),
                              stipple(c, coat_sh, (-110, -590, 120, -140), spacing=13, r=1.6, seed=seed + 31, fn=lambda X, Y: np.clip((X + 10) / 90, 0, 1) * 0.8)))
        blob(cv, [(-58, -540), (-24, -548), (-30, -330), (-74, -340)], P_["gold"], w=4, seed=seed + 32, boil=0.8, n=3,
             shade=lambda c: [dots(c, [(-46, -500 + k * 40)], 5, P_["orange"]) for k in range(4)])
        line(cv, [(-70, -420), (-40, -398), (-20, -410)], 3.5, P_["yellow"], seed=seed + 33, boil=0.6, n=4, taper=(0, 0))
        for side in (-1, 1):                                            # lapels
            line(cv, [(-30 + side * 26, -560), (-50 + side * 12, -470), (-58 + side * 4, -380)], 4, mix(coat, P_["white"], 0.25), seed=seed + 34 + side, boil=0.7, n=4)
        blob(cv, [(-70, -578), (-6, -596), (20, -570), (-40, -556)], P_["white"], w=4, seed=seed + 36, boil=0.6, n=3)                 # wing collar
        for side in (-1, 1):                                            # floppy red bowtie
            blob(cv, [(-34, -566), (-34 + side * 50, -594), (-30 + side * 56, -560), (-34 + side * 44, -540)], P_["red"], w=4, seed=seed + 37 + side, boil=0.8, n=3)
        blob(cv, ell(-34, -566, 12, 12, n=7), P_["red"], w=3.5, seed=seed + 40, boil=0.5)
        # back arm: hugging a stack of books against his chest
        stack_y = -470
        for k in range(4):
            book(cv, -70 + 6 * math.sin(k * 2.1), stack_y + k * 30 - 60, 124, 30, -4 + 5 * math.sin(k * 1.7), BOOK_COLS[(k + 2) % len(BOOK_COLS)], seed=seed + 50 + k * 4, title=False)
        tube(cv, [(54, -530), (60, -420), (-10, -392)], 30, coat, w=4.5, seed=seed + 60, boil=0.8, n=6)
        _hand(cv, -24, -390, 175, "hold", -1, seed + 62, rgb=P_["white"], cuff=P_["white"])
        # head (3/4 facing left)
        hx, hy = -24, -690
        tilt = -8 - 6 * shove
        cv.save()
        cv.rotate(tilt, hx, hy + 80)
        blob(cv, ell(hx, hy, 82, 98, n=14), P_["peach"], w=5.5, seed=seed + 70, boil=1.0,
             shade=lambda c: (c.drawPath(poly_path(cr_closed(ell(hx + 46, hy + 30, 70, 90, n=10), 3)), paint(mix(P_["peach"], P_["orange"], 0.45), 150)),
                              c.drawPath(poly_path(cr_closed(ell(hx - 30, hy - 62, 26, 13, n=8, rot=-20), 3)), paint(P_["white"], 120))))
        blob(cv, ell(hx + 70, hy + 6, 18, 26, n=8), P_["peach"], w=4, seed=seed + 71, boil=0.7)                      # ear
        for k, (dx, dy, rr) in enumerate(((72, -40, 24), (84, -8, 22), (64, -66, 18), (90, 24, 16))):              # white side hair
            blob(cv, ell(hx + dx, hy + dy, rr, rr * 0.9, n=8), P_["white"], w=3.5, seed=seed + 72 + k, boil=0.9)
        for side, (ex, er) in enumerate(((-56, 24), (-6, 19))):         # pince-nez + beady eyes + bushy brows
            blob(cv, ell(hx + ex, hy - 10, er, er * 1.05, n=10), mix(P_["mint"], P_["white"], 0.5), w=4, seed=seed + 80 + side, boil=0.6, a=200)
            dots(cv, [(hx + ex - 6, hy - 8)], 6, INK)
            dots(cv, [(hx + ex - 8, hy - 11)], 2, P_["white"])
            line(cv, [(hx + ex - er - 6, hy - er - 18), (hx + ex, hy - er - 26 + side * 2), (hx + ex + er + 4, hy - er - 12)], 9, P_["white"], seed=seed + 84 + side,
                 boil=0.8, n=4, taper=(0.3, 0.2))
            line(cv, [(hx + ex - er - 6, hy - er - 18), (hx + ex, hy - er - 26 + side * 2), (hx + ex + er + 4, hy - er - 12)], 3, seed=seed + 86 + side,
                 boil=0.8, n=4, taper=(0.3, 0.2))
        line(cv, [(hx - 34, hy - 12), (hx - 26, hy - 16)], 3.5, seed=seed + 88, boil=0.4, n=2)
        blob(cv, ell(hx - 92, hy + 22, 32, 27, n=10), P_["red"], w=4.5, seed=seed + 89, boil=0.8,
             shade=lambda c: dots(c, [(hx - 100, hy + 12)], 6, P_["white"], a=170))
        must = [(hx - 150, hy + 74), (hx - 134, hy + 44), (hx - 96, hy + 40), (hx - 60, hy + 50), (hx - 20, hy + 40), (hx + 18, hy + 50), (hx + 34, hy + 78),
                (hx + 10, hy + 70), (hx - 20, hy + 90), (hx - 70, hy + 78), (hx - 116, hy + 92)]
        blob(cv, must, P_["white"], w=4.5, seed=seed + 90, boil=1.0, n=5,
             shade=lambda c: [line(c, [(hx - 120 + k * 26, hy + 52), (hx - 128 + k * 26, hy + 82)], 2.2, (200, 196, 210), seed=seed + 91 + k, boil=0.5, n=2) for k in range(6)])
        # mortarboard with a swinging tassel
        blob(cv, [(hx - 66, hy - 70), (hx - 52, hy - 104), (hx + 40, hy - 108), (hx + 62, hy - 72)], (30, 20, 50), w=4.5, seed=seed + 100, boil=0.7, n=4)
        board = [(hx - 140, hy - 112), (hx - 14, hy - 142), (hx + 110, hy - 114), (hx - 16, hy - 90)]
        blob(cv, board, (40, 26, 66), w=5, seed=seed + 101, boil=0.8, n=2, shade=lambda c: quad(c, [(hx - 16, hy - 90), (hx + 110, hy - 114), (hx + 120, hy - 100), (hx - 16, hy - 76)], (20, 12, 34)))
        sw = 14 * math.sin(T * 7.0) + 20 * shove
        line(cv, [(hx - 14, hy - 118), (hx - 70, hy - 110), (hx - 92 + sw * 0.3, hy - 60), (hx - 96 + sw, hy - 18)], 4, P_["yellow"], seed=seed + 102, boil=0.6, n=5, taper=(0, 0))
        blob(cv, [(hx - 106 + sw, hy - 26), (hx - 86 + sw, hy - 26), (hx - 82 + sw, hy + 6), (hx - 110 + sw, hy + 6)], P_["yellow"], w=3.5, seed=seed + 103, boil=0.6, n=3)
        dots(cv, [(hx - 14, hy - 118)], 7, P_["yellow"])
        cv.restore()
        # front arm: shoving a book into the funnel
        cv.restore()
        la = math.radians(lean)
        S = (-60 * math.cos(la) - (-280 + bob) * math.sin(la), -250 + (-60) * math.sin(la) + (-280 + bob) * math.cos(la))
        (wx, wy), fdir = limb(cv, S, loc, 150, 150, -1, 30, coat, seed + 110)
        _hand(cv, wx, wy, fdir, "hold", 1, seed + 114, rgb=P_["white"], cuff=P_["white"])


def _funnel(cv, mx, my, rx, ry, sx, sy, srx, seed, stuffed):
    """A huge tin funnel: mouth ellipse (mx, my, rx, ry), spout down to (sx, sy). stuffed 0..1 = books jammed in the mouth."""
    tin, tin_sh, tin_hi = (176, 188, 214), (120, 128, 166), (240, 246, 255)
    blob(cv, ell(mx, my, rx, ry, n=20), (40, 34, 60), w=5, seed=seed, boil=0.8)                        # mouth interior
    cv.save()
    cv.clipPath(poly_path(cr_closed(ell(mx, my, rx - 6, ry - 3, n=20), 3)), doAntiAlias=True)
    for k in range(int(3 + 7 * stuffed)):                                                                   # jam of books
        bx = mx - rx * 0.6 + (k * 97 % int(rx * 1.2))
        book(cv, bx, my - 6 - 10 * math.sin(k * 1.9), 90, 26, -30 + 60 * float(hsh(seed + k)), BOOK_COLS[k % len(BOOK_COLS)], seed=seed + 10 + k * 3, title=False)
    cv.restore()
    cone = [(mx - rx, my), (sx - srx, sy - 50), (sx - srx, sy + 70), (sx + srx, sy + 70), (sx + srx, sy - 50), (mx + rx, my)]
    def sh(c):
        quad(c, [(mx + rx * 0.35, my), (mx + rx + 20, my), (sx + srx + 10, sy + 80), (sx + srx * 0.3, sy + 80)], tin_sh)
        line(c, [(mx - rx * 0.55, my + 10), (sx - srx * 0.5, sy - 40), (sx - srx * 0.5, sy + 60)], 14, tin_hi, seed=seed + 41, boil=0.6, n=4, taper=(0.1, 0.3), a=210)
        for k in range(1, 4):
            u = k / 4
            yy = my + (sy - 50 - my) * u
            hw = rx + (srx - rx) * u
            c.drawPath(poly_path(cr_open([(mx - hw - 10, yy), (mx, yy + ry * (1 - u) * 0.8), (mx + hw + 10, yy)], 6), closed=False), paint(tin_sh, stroke=3))
    blob(cv, cone, tin, w=5.5, seed=seed + 40, boil=0.9, n=4, shade=sh)
    rim = cr_closed(jit(ell(mx, my, rx, ry, n=20), 0.8, seed + 50), 3)                                      # front rim band
    front = rim[(rim[:, 1] >= my - 2)]
    if len(front) > 2:
        front = front[np.argsort(front[:, 0])]
        brush(cv, front, 16, tin_hi, taper=(0.05, 0.05), seed=seed + 51)
    brush(cv, rim, 5.5, closed=True, seed=seed + 52)


def _kid_head(cv, x, y, s, T, mode="normal", bulge=0.0, spin=0.0, seed=7300, look=(0.0, 0.0), lid_open=1.0, mouth=0.4, blank_glow=0.0):
    """The student (round lilac head, centre x, y). mode: 'funnel' (skull lid flipped open, dazed spiral eyes),
    'blank' (no face at all), 'normal'."""
    skin, skin_sh = P_["lilac"], mix(P_["lilac"], P_["violet"], 0.55)
    sx_, sy_ = 1 + 0.07 * bulge, 1 - 0.045 * bulge
    with at(cv, x, y, s, sx=s * sx_):
        cv.scale(1.0, sy_)
        r = 130
        for side in (-1, 1):                                                   # ears
            blob(cv, ell(side * 126, 6, 24, 30, n=8), skin, w=4.5, seed=seed + 1 + side, boil=0.7,
                 shade=lambda c, side=side: c.drawPath(poly_path(cr_closed(ell(side * 128, 8, 10, 15, n=7), 3)), paint(skin_sh)))
        if mode == "funnel":
            cut = -72
            hw = math.sqrt(r * r - cut * cut)
            head = np.array([(r * math.cos(a), r * math.sin(a)) for a in np.linspace(-math.asin(-cut / r) + 0, math.pi + math.asin(-cut / r), 14)])
            head = np.vstack([head, [(-hw * 0.5, cut + 2), (hw * 0.5, cut + 2)]])
            blob(cv, head, skin, w=6, seed=seed + 5, boil=1.0, n=5,
                 shade=lambda c: c.drawPath(poly_path(cr_closed(ell(40, 50, 120, 110, n=12), 3)), paint(skin_sh, 120)))
            # the open skull: dark hole + the lid flipped back on its hinge
            blob(cv, ell(0, cut, hw - 4, 24, n=14), (34, 14, 50), w=4.5, seed=seed + 6, boil=0.7)
            cap = [(r * math.cos(a), r * math.sin(a)) for a in np.linspace(math.pi + math.asin(-cut / r), 2 * math.pi - math.asin(-cut / r), 9)]
            cv.save()
            cv.rotate(104 * lid_open + 6 * math.sin(T * 9), hw, cut)
            blob(cv, cap + [(hw * 0.4, cut + 6), (-hw * 0.4, cut + 6)], skin, w=5.5, seed=seed + 7, boil=0.9, n=4,
                 shade=lambda c: c.drawPath(poly_path(cr_closed(ell(0, cut - 4, hw, 16, n=10), 3)), paint(P_["hotpink"], 200)))
            cv.restore()
        else:
            blob(cv, ell(0, 0, r, r * 0.98, n=16), skin, w=6, seed=seed + 5, boil=1.0,
                 shade=lambda c: (c.drawPath(poly_path(cr_closed(ell(40, 50, 120, 110, n=12), 3)), paint(skin_sh, 120)),
                                  c.drawPath(poly_path(cr_closed(ell(-50, -70, 34, 16, n=8, rot=-25), 3)), paint(P_["white"], 110))))
        for side in (-1, 1):                                                    # blush
            cv.drawPath(poly_path(ell(side * 78, 52, 24, 13, n=12)), paint(P_["hotpink"], 140))
        if mode == "blank":
            return
        for side in (-1, 1):
            ex, ey = side * 50, -4
            blob(cv, ell(ex, ey, 36, 40, n=10), P_["white"], w=5, seed=seed + 20 + side, boil=0.8)
            if mode == "funnel":
                pts = [(ex + (2 + u * 2.3) * math.cos(u * side + spin * 6), ey + (2 + u * 2.3) * math.sin(u * side + spin * 6)) for u in np.linspace(0, 13, 36)]
                brush(cv, np.array(pts), 4.5, INK, seed=seed + 24 + side, taper=(0.1, 0.1))
            else:
                dots(cv, [(ex + look[0] * 12, ey + look[1] * 12)], 13, INK)
                dots(cv, [(ex + look[0] * 12 - 4, ey + look[1] * 12 - 5)], 4, P_["white"])
        if mouth > 0.1:
            blob(cv, ell(0, 70, 22, 10 + 22 * mouth, n=10), P_["mouth"], w=4.5, seed=seed + 30, boil=0.7,
                 shade=lambda c: c.drawPath(poly_path(ell(4, 70 + 16 * mouth, 14, 9, n=8)), paint(P_["tongue"])))
        else:
            line(cv, [(-22, 66), (0, 76), (22, 66)], 5, seed=seed + 31, boil=0.6, n=3)


def _kid_lip(cv, x, y, s, bulge, seed=7300):
    """The front lip of the open skull, drawn over the funnel spout so it sits INSIDE the head."""
    sx_, sy_ = 1 + 0.07 * bulge, 1 - 0.045 * bulge
    with at(cv, x, y, s, sx=s * sx_):
        cv.scale(1.0, sy_)
        cut, hw = -72, math.sqrt(130 * 130 - 72 * 72)
        P = ell(0, cut, hw - 4, 24, n=24)
        front = P[P[:, 1] >= cut - 1]
        front = front[np.argsort(front[:, 0])]
        brush(cv, front + np.array([0.0, 6.0]), 13, P_["lilac"], taper=(0.05, 0.05), seed=seed + 8)
        brush(cv, front + np.array([0.0, 12.0]), 4.5, INK, taper=(0.1, 0.1), seed=seed + 9)


def _kid_arms(cv, x, y, s, T, seed=7370, gown=False, tremble=0.0, grip_y=None):
    """The student's arms (head centre x, y): gripping the desk edge (grip_y) or resting on the knees."""
    col = (190, 222, 255) if gown else P_["teal"]
    tr = math.sin(T * 40) * 3 * tremble
    with at(cv, x + tr, y, s):
        for k, side in enumerate((-1, 1)):
            sh = (side * 112, 186)
            if grip_y is not None:
                hand = (side * 150, grip_y - y + 4 * math.sin(T * 30 + k) * tremble)
                el = (side * 172, (sh[1] + hand[1]) / 2 + 10)
            else:
                hand = (side * 70, 300)
                el = (side * 150, 260)
            tube(cv, [sh, el, hand], 30, col, w=4.5, seed=seed + k, boil=0.8, n=6)
            _hand(cv, hand[0], hand[1], 90 - side * 20 if grip_y is not None else 60 + side * 40, "hold" if grip_y is not None else "flat",
                  1 if side < 0 else -1, seed + 5 + k * 9, rgb=P_["lilac"])


def _kid_body(cv, x, y, s, T, seed=7350, gown=False, tremble=0.0):
    """Torso of the student below a head at x, y (sitting)."""
    tr = (math.sin(T * 40) * 3 * tremble, 0)
    with at(cv, x + tr[0], y, s):
        col = (190, 222, 255) if gown else P_["teal"]
        body = [(-60, 120), (-118, 170), (-132, 330), (132, 330), (118, 170), (60, 120)]
        def sh(c):
            if gown:
                for k in range(30):
                    dots(c, [(-110 + (k * 53) % 220, 140 + (k * 37) % 190)], 4, P_["blue"], a=160)
            else:
                for k in range(4):
                    c.drawRect(R(-140, 170 + k * 40, 140, 186 + k * 40), paint(P_["yellow"]))
            c.drawPath(poly_path([(40, 110), (150, 110), (150, 340), (70, 340)]), paint(mix(col, INK, 0.25), 140))
        blob(cv, body, col, w=5.5, seed=seed, boil=1.0, n=5, shade=sh)
        blob(cv, ell(0, 122, 46, 16, n=10), P_["lilac"], w=4.5, seed=seed + 1, boil=0.6)


def _school_desk(cv, x, y, seed=7400, T=0.0):
    """The kid's little desk (top plank at y)."""
    blob(cv, rect_pts([(x - 250, y + 10), (x + 250, y + 10), (x + 230, y + 170), (x - 230, y + 170)], 3), P_["red"], w=6, seed=seed, boil=0.9, n=3,
         shade=lambda c: (c.drawRect(R(x + 130, y, x + 260, y + 180), paint(mix(P_["red"], INK, 0.25))),
                          c.drawRect(R(x - 200, y + 50, x + 200, y + 56), paint(P_["maroon"])), c.drawRect(R(x - 200, y + 110, x + 200, y + 116), paint(P_["maroon"]))))
    blob(cv, rect_pts([(x - 280, y - 22), (x + 280, y - 22), (x + 290, y + 14), (x - 290, y + 14)], 3), P_["orange"], w=6, seed=seed + 1, boil=0.9, n=3,
         shade=lambda c: c.drawRect(R(x - 300, y, x + 300, y + 16), paint(P_["gold"])))
    # apple with a worm peeking out
    ax, ay = x + 170, y - 46
    blob(cv, [(ax - 30, ay - 10), (ax - 10, ay - 26), (ax, ay - 20), (ax + 12, ay - 26), (ax + 32, ay - 10), (ax + 28, ay + 18), (ax, ay + 24), (ax - 28, ay + 18)],
         P_["red"], w=4.5, seed=seed + 5, boil=0.7, n=4, shade=lambda c: dots(c, [(ax - 12, ay - 10)], 6, P_["white"], a=170))
    line(cv, [(ax, ay - 22), (ax + 4, ay - 40)], 4, (110, 70, 30), seed=seed + 6, boil=0.4, n=2)
    blob(cv, [(ax + 4, ay - 36), (ax + 26, ay - 50), (ax + 18, ay - 32)], P_["acid"], w=3, seed=seed + 7, boil=0.4, n=3)
    wy_ = ay - 4 + 4 * math.sin(T * 5)
    blob(cv, ell(ax + 30, wy_, 10, 10, n=8), P_["hotpink"], w=3, seed=seed + 8, boil=0.5)
    dots(cv, [(ax + 33, wy_ - 2)], 2.5, INK)
    # ink well + quill
    blob(cv, rect_pts([(x - 200, y - 50), (x - 160, y - 50), (x - 156, y - 18), (x - 204, y - 18)], 2), P_["blue"], w=4, seed=seed + 9, boil=0.5, n=3)
    line(cv, [(x - 182, y - 46), (x - 150, y - 120)], 4, seed=seed + 10, boil=0.5, n=2)
    blob(cv, [(x - 160, y - 100), (x - 130, y - 150), (x - 142, y - 96)], P_["white"], w=3, seed=seed + 11, boil=0.6, n=3)


def _steam(cv, x, y, side, k, seed):
    """A burst of steam puffs out of an ear (k = 0..1 age of the burst)."""
    if k <= 0 or k >= 1:
        return
    for j in range(3):
        u = k - j * 0.12
        if u <= 0:
            continue
        px, py = x + side * (30 + 150 * u), y - 30 * u - 60 * u * u
        r = 14 + 34 * u
        blob(cv, ell(px, py, r, r * 0.86, n=9), P_["white"], w=4, seed=seed + j, boil=1.0, a=int(255 * (1 - u) ** 0.6))


def _classroom(cv, t, T):
    """Shot B: the funnel. World = screen (light camera drift)."""
    z = 1.0 + 0.035 * seg(t, T49_CUT1, T49_PAN[0])
    jolt = shake(14 * math.exp(-max(0.0, t - T49_X1 - 0.1) * 7), 3) if t > T49_X1 + 0.1 else (0.0, 0.0)
    cam = dict(x=20 * seg(t, T49_CUT1, T49_PAN[0]) + jolt[0], y=-10 * seg(t, T49_CUT1, T49_PAN[0]) + jolt[1], z=z)
    C = sets.Cam(cv, cam)
    MX, MY, KX, KY = 840, 238, 840, 560
    I0, IV = 1.45, 0.47                                    # stuffing cycle start, interval
    n_ins = int(max(0.0, (t - I0) / IV)) if t > I0 else 0
    u = ((t - I0) / IV) % 1.0 if t > I0 else 0.0
    if t > T49_X1 + 0.3:                                   # after the X: everybody freezes mid-shove
        u = 0.62
    shove = math.sin(math.pi * seg(u, 0.4, 0.7)) if 0.4 < u < 0.7 else 0.0
    stack, rel = (1338, 372), (MX + 60, MY - 90)
    if u < 0.45:
        hand = (lerp(stack[0], rel[0], ease(u / 0.45)), lerp(stack[1], rel[1], ease(u / 0.45)) - 60 * math.sin(math.pi * u / 0.45))
    elif u < 0.62:
        k = (u - 0.45) / 0.17
        hand = (lerp(rel[0], MX + 30, k), lerp(rel[1], MY - 10, k))
    else:
        k = (u - 0.62) / 0.38
        hand = (lerp(MX + 30, stack[0], ease(k)), lerp(MY - 10, stack[1], ease(k)) - 40 * math.sin(math.pi * k))
    # last insertion time -> bulge, steam
    t_last = I0 + (n_ins - 1) * IV + 0.62 * IV if n_ins > 0 else -9
    if u >= 0.62 and t <= T49_X1 + 0.3:
        t_last = I0 + n_ins * IV + 0.62 * IV
    age = t - t_last
    bulge = math.exp(-age / 0.16) * math.cos(age * 30) if 0 <= age < 0.7 else 0.0
    grow = 0.035 * min(n_ins, 8) / 8
    with C.layer(1.0):
        _classroom_bg(cv, T, t)
        for k, (bw, bh, col) in enumerate(((330, 52, P_["blue"]), (300, 46, P_["magenta"]))):
            book(cv, 1400 + 8 * k, 905 - k * 50, bw, bh, -1.5 + 3 * k, col, seed=7500 + k * 5)
        _school_desk(cv, KX, 790, T=T)
        _kid_body(cv, KX, KY, 1.0, T, tremble=min(1.0, n_ins / 5))
        _kid_arms(cv, KX, KY, 1.0, T, tremble=min(1.0, n_ins / 5), grip_y=772)
        _kid_head(cv, KX, KY, 1.0 + grow, T, mode="funnel", bulge=bulge, spin=T * 0.8, mouth=0.5 + 0.4 * abs(math.sin(T * 3)))
        for side in (-1, 1):
            _steam(cv, KX + side * 150, KY + 10, side, age / 0.7, 7600 + side * 10)
        _funnel(cv, MX, MY, 210, 50, KX, KY - 72 * (1.0 + grow) - 62, 34, 7700, min(1.0, n_ins / 7))
        _kid_lip(cv, KX, KY, 1.0 + grow, bulge)
        # the item in flight / in hand
        kinds = ["book", "A", "book", "2+2", "book", "π", "book", "?", "book", "B", "book"]
        item = kinds[n_ins % len(kinds)]
        if u < 0.62:
            ix, iy, ang, sc = hand[0] - 10, hand[1] - 30, -20 + 40 * u, 1.0
        else:
            k = (u - 0.62) / 0.22
            ix, iy, ang, sc = MX + 20, MY - 10 + 30 * k, 10, max(0.0, 1 - k)
        if sc > 0.02 and t <= T49_X1 + 0.3:
            if item == "book":
                book(cv, ix, iy, 120 * sc, 34 * sc, ang, BOOK_COLS[n_ins % len(BOOK_COLS)], seed=7800 + n_ins)
            else:
                cv.save(); cv.translate(ix, iy); cv.rotate(ang * 0.5)
                paint_text(cv, item, 0, 30 * sc, font="bangers", size=96 * sc + 1, fill=[P_["yellow"], P_["hotpink"], P_["acid"], P_["teal"]][n_ins % 4],
                           ink_w=4.5, shadow=(4, 4), seed=7810 + n_ins, streaks=False)
                cv.restore()
        _teacher(cv, 1420, 856, 0.98, T, hand, shove)
        # dazed stars orbiting the kid's head
        if n_ins >= 3:
            for k in range(3):
                a = T * 4.5 + k * 2.09
                sparkle(cv, KX + 190 * math.cos(a), KY - 120 + 40 * math.sin(a), 18 + 4 * math.sin(T * 9 + k), [P_["yellow"], P_["white"], P_["acid"]][k], seed=7900 + k)
        # sweat drops flying
        for k in range(2):
            ph = (T * 1.7 + k * 0.5) % 1.0
            dx = (1 if k else -1) * (100 + 80 * ph)
            blob(cv, [(KX + dx, KY - 110 - 40 * ph + 80 * ph * ph - 18), (KX + dx + 10, KY - 110 - 40 * ph + 80 * ph * ph + 6), (KX + dx, KY - 110 - 40 * ph + 80 * ph * ph + 14),
                      (KX + dx - 10, KY - 110 - 40 * ph + 80 * ph * ph + 6)], P_["mint"], w=3, seed=7950 + k, boil=0.5, n=4, a=int(255 * (1 - ph)))
    return C


def _doctor_bg(cv, T):
    _wallpaper(cv, (-80, -80, W + 80, 940), P_["mint"], [mix(P_["teal"], P_["mint"], 0.3), P_["hotpink"], mix(P_["lilac"], P_["mint"], 0.3)], T + 3, 8100, step=170, amp=18, wdt=26)
    radial(cv, 980, 380, 900, [(P_["white"], 120), (P_["white"], 0)])
    pts = [(x, 640 + 26 * (1 if (k % 2) else -1)) for k, x in enumerate(range(-80, W + 120, 60))]          # zigzag dado rail
    band = np.array(pts + [(W + 120, 700), (-80, 700)], float)
    quad(cv, band, P_["magenta"])
    brush(cv, np.array(pts, float), 5, taper=(0.01, 0.01), seed=8101)
    cv.drawRect(R(-80, 700, W + 80, 940), paint(mix(P_["teal"], P_["mint"], 0.35)))
    line(cv, [(-80, 700), (W + 80, 700)], 5, seed=8102, boil=0.6, n=2, taper=(0, 0))
    # the eye chart
    cx0, cy0, cx1, cy1 = 120, 90, 470, 590
    blob(cv, rect_pts([(cx0, cy0), (cx1, cy0), (cx1, cy1), (cx0, cy1)], 3), P_["white"], w=6, seed=8110, boil=0.9, n=3,
         shade=lambda c: c.drawRect(R(cx0, cy1 - 40, cx1, cy1), paint(P_["red"])))
    rows = [("E", 120), ("F P", 74), ("T O Z", 54), ("L P E D", 40), ("P E C F D", 30), ("PLATO WAS HERE", 20)]
    yy = cy0 + 30
    for k, (txt, sz) in enumerate(rows):
        yy += sz * 0.95 + 14
        paint_text(cv, txt, (cx0 + cx1) / 2, yy, font="londrina", size=sz, fill=INK, ink_w=0, shadow=None, seed=8120 + k, wobble=0.6, streaks=False,
                   spacing=sz * 0.25, rot_jit=2.0)
    # diploma with an eye seal
    blob(cv, rect_pts([(1500, 110), (1790, 110), (1790, 330), (1500, 330)], 3), P_["gold"], w=6, seed=8130, boil=0.8, n=3)
    blob(cv, rect_pts([(1522, 130), (1768, 130), (1768, 310), (1522, 310)], 3), P_["cream"], w=4, seed=8131, boil=0.7, n=3)
    paint_text(cv, "DIPLOMA", 1645, 190, font="shrik", size=40, fill=P_["maroon"], ink_w=0, shadow=None, seed=8132, streaks=False)
    for k in range(3):
        line(cv, [(1550, 220 + k * 18), (1740, 220 + k * 18)], 2.5, mix(INK, P_["cream"], 0.4), seed=8133 + k, boil=0.5, n=2, taper=(0.1, 0.1))
    blob(cv, ell(1720, 290, 28, 28, n=10), P_["red"], w=3.5, seed=8136, boil=0.6)
    w.eye_glyph(cv, 1720, 290, 0.32, seed=8137)
    # cabinet with an eyeball in a jar
    blob(cv, rect_pts([(1560, 420), (1830, 420), (1830, 930), (1560, 930)], 3), P_["violet"], w=6, seed=8140, boil=0.9, n=3,
         shade=lambda c: (c.drawRect(R(1580, 450, 1810, 640), paint(mix(P_["violet"], P_["lilac"], 0.5))), c.drawLine(1695, 660, 1695, 920, paint(INK, stroke=4))))
    blob(cv, rect_pts([(1620, 480), (1720, 480), (1720, 620), (1620, 620)], 3), mix(P_["mint"], P_["acid"], 0.4), w=4.5, seed=8141, boil=0.8, n=3, a=230)
    bob = 6 * math.sin(T * 1.8)
    blob(cv, ell(1670, 560 + bob, 32, 32, n=10), P_["white"], w=4, seed=8142, boil=0.7)
    dots(cv, [(1678, 562 + bob)], 13, P_["blue"])
    dots(cv, [(1680, 562 + bob)], 6, INK)
    blob(cv, rect_pts([(1612, 466), (1728, 466), (1728, 486), (1612, 486)], 2), P_["gold"], w=4, seed=8143, boil=0.6, n=3)
    _checker_floor(cv, 930, [P_["white"], P_["teal"]], 8150)
    # exam lamp pouring a cone of light
    quad(cv, [(900, 150), (1060, 150), (1250, 940), (640, 940)], P_["yellow"], 50)
    line(cv, [(980, -40), (980, 70)], 8, (90, 90, 110), seed=8160, boil=0.4, n=2, taper=(0, 0))
    blob(cv, [(880, 160), (920, 80), (1040, 80), (1080, 160)], (200, 205, 225), w=5, seed=8161, boil=0.7, n=3)
    blob(cv, ell(980, 162, 100, 18, n=12), P_["yellow"], w=4.5, seed=8162, boil=0.6)


def _doctor(cv, x, y, s, T, tip_w, seed=8200):
    """The doctor (feet x, y; faces left): lab coat, head mirror, stethoscope, tongue out; palette in the back hand and a
    long paintbrush whose tip is at the world point tip_w."""
    with at(cv, x, y, s):
        tip = ((tip_w[0] - x) / s, (tip_w[1] - y) / s)
        for side, lx in ((-1, -40), (1, 36)):
            tube(cv, [(lx, -170), (lx - 2, -90), (lx, -20)], 34, (40, 40, 70), w=4.5, seed=seed + side, boil=0.7, n=4)
            blob(cv, [(lx + 22, -2), (lx - 50, -4), (lx - 58, -18), (lx - 36, -32), (lx + 24, -32)], (30, 22, 44), w=4.5, seed=seed + 4 + side, boil=0.6, n=4)
        coat = [(-50, -540), (-120, -500), (-150, -380), (-150, -200), (-132, -128), (132, -128), (150, -200), (150, -380), (120, -500), (50, -540)]
        blob(cv, coat, P_["white"], w=6, seed=seed + 10, boil=1.0, n=6,
             shade=lambda c: (c.drawPath(poly_path(cr_closed([(40, -540), (170, -480), (170, -110), (60, -110), (80, -330)], 4)), paint((200, 222, 250))),
                              stipple(c, (180, 200, 240), (-160, -550, 170, -110), spacing=12, r=1.5, seed=seed + 11, fn=lambda X, Y: np.clip((X - 0) / 120, 0, 1) * 0.8),
                              c.drawLine(-6, -520, -10, -130, paint(INK, stroke=3.5))))
        for k in range(3):
            dots(cv, [(-20, -470 + k * 90)], 7, (180, 190, 220))
        blob(cv, rect_pts([(-120, -330), (-60, -330), (-60, -260), (-120, -260)], 2), P_["white"], w=4, seed=seed + 12, boil=0.6, n=3)
        line(cv, [(-104, -350), (-104, -300)], 6, P_["red"], seed=seed + 13, boil=0.4, n=2, taper=(0, 0))
        line(cv, [(-88, -356), (-88, -300)], 6, P_["blue"], seed=seed + 14, boil=0.4, n=2, taper=(0, 0))
        for side in (-1, 1):
            line(cv, [(side * 48, -538), (side * 70, -470), (side * 30, -380)], 4.5, seed=seed + 15 + side, boil=0.7, n=4)
        # stethoscope
        line(cv, [(-40, -530), (-70, -460), (-50, -390), (-20, -370)], 7, (60, 60, 80), seed=seed + 20, boil=0.6, n=5, taper=(0, 0))
        line(cv, [(40, -530), (50, -470), (10, -400), (-20, -370)], 7, (60, 60, 80), seed=seed + 21, boil=0.6, n=5, taper=(0, 0))
        blob(cv, ell(-20, -360, 20, 20, n=9), (200, 205, 225), w=4, seed=seed + 22, boil=0.5, shade=lambda c: dots(c, [(-26, -366)], 5, P_["white"]))
        # back arm + palette
        (wx, wy), fd = limb(cv, (90, -500), (150, -360), 110, 110, 1, 30, P_["white"], seed + 30)
        pal = [(wx - 30, wy - 70), (wx + 90, wy - 90), (wx + 140, wy - 30), (wx + 100, wy + 30), (wx - 10, wy + 30), (wx - 50, wy - 10)]
        blob(cv, pal, (226, 186, 130), w=4.5, seed=seed + 32, boil=0.8, n=5,
             shade=lambda c: [blob(c, ell(wx + 20 + 34 * math.cos(k * 1.1), wy - 30 + 26 * math.sin(k * 1.1), 13, 11, n=7), col, w=2.5, seed=seed + 33 + k, boil=0.5)
                              for k, col in enumerate((P_["magenta"], P_["teal"], P_["yellow"], P_["blue"], P_["white"]))])
        _hand(cv, wx, wy, fd, "hold", -1, seed + 40, rgb=(170, 235, 170))
        # head
        hx, hy = -10, -650
        skin = (170, 235, 170)
        blob(cv, ell(hx, hy, 112, 108, n=16), skin, w=6, seed=seed + 50, boil=1.0,
             shade=lambda c: c.drawPath(poly_path(cr_closed(ell(hx + 50, hy + 40, 100, 90, n=12), 3)), paint(mix(skin, P_["tealdk"], 0.35), 140)))
        blob(cv, ell(hx + 104, hy + 10, 20, 28, n=8), skin, w=4.5, seed=seed + 51, boil=0.6)
        for k in range(3):
            line(cv, [(hx - 20 + k * 22, hy - 104), (hx - 30 + k * 26, hy - 140 - 10 * (k % 2))], 3.5, seed=seed + 52 + k, boil=0.8, n=3)
        line(cv, [(hx - 110, hy - 40), (hx - 30, hy - 72), (hx + 60, hy - 76), (hx + 110, hy - 40)], 9, (60, 60, 80), seed=seed + 55, boil=0.6, n=5, taper=(0, 0))
        blob(cv, ell(hx - 66, hy - 62, 38, 38, n=12), (220, 225, 240), w=4.5, seed=seed + 56, boil=0.6,
             shade=lambda c: (radial(c, hx - 78, hy - 74, 30, [(P_["white"], 255), ((220, 225, 240), 0)]),))
        dots(cv, [(hx - 66, hy - 62)], 8, (60, 60, 80))
        for k, ex in enumerate((-70, -20)):                                   # glasses, eyes on the work, bushy brows
            blob(cv, ell(hx + ex, hy, 22, 20, n=10), mix(P_["mint"], P_["white"], 0.6), w=4, seed=seed + 60 + k, boil=0.6, a=200)
            dots(cv, [(hx + ex - 8, hy + 6)], 6, INK)
            line(cv, [(hx + ex - 26, hy - 30 + k * 4), (hx + ex + 22, hy - 26 - k * 6)], 10, P_["white"], seed=seed + 62 + k, boil=0.8, n=3, taper=(0.2, 0.2))
            line(cv, [(hx + ex - 26, hy - 30 + k * 4), (hx + ex + 22, hy - 26 - k * 6)], 3, seed=seed + 64 + k, boil=0.8, n=3, taper=(0.2, 0.2))
        line(cv, [(hx - 48, hy), (hx - 42, hy)], 3, seed=seed + 66, boil=0.3, n=2)
        blob(cv, [(hx - 50, hy + 10), (hx - 112, hy + 46), (hx - 106, hy + 60), (hx - 46, hy + 46)], mix(skin, P_["orange"], 0.35), w=4.5, seed=seed + 67, boil=0.7, n=4)
        line(cv, [(hx - 80, hy + 74), (hx - 50, hy + 82), (hx - 20, hy + 74)], 4.5, seed=seed + 68, boil=0.6, n=3)
        tg = 4 * math.sin(T * 6)
        blob(cv, [(hx - 30, hy + 76), (hx - 10 + tg, hy + 100), (hx - 26 + tg, hy + 108), (hx - 40, hy + 82)], P_["tongue"], w=3.5, seed=seed + 69, boil=0.6, n=4)
        # front arm + the brush (held near its end, bristles at tip)
        bd = np.array([-1.0, 0.25]) / math.hypot(1.0, 0.25)
        grip = (tip[0] - bd[0] * 210, tip[1] - bd[1] * 210)
        (wx, wy), fd = limb(cv, (-100, -500), grip, 140, 140, -1, 30, P_["white"], seed + 80)
        line(cv, [np.array(grip) - bd * 60, (tip[0] - bd[0] * 34, tip[1] - bd[1] * 34)], 9, (140, 80, 40), seed=seed + 82, boil=0.4, n=2, taper=(0, 0))
        line(cv, [(tip[0] - bd[0] * 40, tip[1] - bd[1] * 40), (tip[0] - bd[0] * 22, tip[1] - bd[1] * 22)], 11, (200, 205, 225), seed=seed + 83, boil=0.3, n=2, taper=(0, 0))
        blob(cv, [(tip[0] - bd[0] * 24 - bd[1] * 7, tip[1] - bd[1] * 24 + bd[0] * 7), (tip[0], tip[1]), (tip[0] - bd[0] * 24 + bd[1] * 7, tip[1] - bd[1] * 24 - bd[0] * 7)],
             P_["blue"], w=3, seed=seed + 84, boil=0.4, n=3)
        _hand(cv, wx, wy, math.degrees(math.atan2(bd[1], bd[0])), "pinch", 1, seed + 86, rgb=skin)


def _painted_eye(cv, x, y, sz, k, drip, seed, look=(0.3, 0.0)):
    """A crude painted-on cartoon eye (k 0..1 = how much of it is painted so far; drip 0..1 = runs of wet paint)."""
    if k <= 0:
        return
    a0 = -math.pi / 2
    n = 26
    m = max(2, int(n * min(1.0, k / 0.6)))
    pts = [(x + sz * math.cos(a0 + 2 * math.pi * j / (n - 1)) * (1 + 0.08 * math.sin(j * 1.7 + seed)), y + sz * 1.12 * math.sin(a0 + 2 * math.pi * j / (n - 1))) for j in range(m)]
    if k > 0.6:
        f = (k - 0.6) / 0.4
        blob(cv, pts, P_["white"], w=0, seed=seed, boil=0.8, n=3, a=int(255 * min(1, f * 2)))
        if f > 0.4:
            dots(cv, [(x + look[0] * sz * 0.4, y + look[1] * sz * 0.4)], sz * 0.5, P_["blue"])
            dots(cv, [(x + look[0] * sz * 0.4, y + look[1] * sz * 0.4)], sz * 0.24, INK)
    brush(cv, cr_open(jit(np.array(pts), 1.2, seed + 1), 3), 7, INK, taper=(0.05, 0.3), seed=seed + 2)
    if k >= 1:                                                         # lashes, painted with gusto
        for j in range(4):
            a = -math.pi * (0.25 + 0.17 * j)
            line(cv, [(x + sz * math.cos(a), y + sz * 1.1 * math.sin(a)), (x + sz * 1.45 * math.cos(a), y + sz * 1.55 * math.sin(a))], 5, seed=seed + 10 + j, boil=0.6, n=2)
    if drip > 0:
        for j in range(3):
            dx = x + sz * (-0.5 + 0.5 * j)
            L = sz * (0.5 + 1.2 * float(hsh(seed + j))) * drip
            col = [P_["blue"], P_["white"], INK][j]
            line(cv, [(dx, y + sz * 0.8), (dx + 2, y + sz * 0.8 + L)], 7, col, seed=seed + 20 + j, boil=0.5, n=2, taper=(0, 0))
            dots(cv, [(dx + 2, y + sz * 0.8 + L)], 6, col)


def _doctor_office(cv, t, T):
    """Shot C: painting eyes onto a blank face."""
    jolt = shake(14 * math.exp(-max(0.0, t - T49_X2 - 0.1) * 7), 5) if t > T49_X2 + 0.1 else (0.0, 0.0)
    cam = dict(x=jolt[0] + 30 * seg(t, T49_PAN[1], T49_IRIS[0]), y=jolt[1], z=1.0 + 0.04 * seg(t, T49_PAN[1], T49_IRIS[0]))
    C = sets.Cam(cv, cam)
    KX, KY = 800, 440
    with C.layer(1.0):
        _doctor_bg(cv, T)
        blob(cv, ell(KX, 760, 120, 24, n=12), P_["red"], w=5, seed=8300, boil=0.7)                          # stool
        for side in (-1, 1):
            line(cv, [(KX + side * 70, 770), (KX + side * 110, 930)], 9, (200, 205, 225), seed=8301 + side, boil=0.4, n=2, taper=(0, 0))
        for side in (-1, 1):                                                                                 # dangling legs
            sw = 14 * math.sin(T * 4 + side)
            tube(cv, [(KX + side * 40, 740), (KX + side * 46 + sw, 830), (KX + side * 44 + sw, 880)], 26, P_["lilac"], w=4.5, seed=8303 + side, boil=0.7, n=4)
            blob(cv, ell(KX + side * 46 + sw, 890, 30, 14, n=8), P_["acid"], w=4, seed=8306 + side, boil=0.6)
        _kid_body(cv, KX, KY, 1.0, T, gown=True)
        _kid_arms(cv, KX, KY, 1.0, T, gown=True)
        _kid_head(cv, KX, KY, 1.0, T, mode="blank")
        # painted eyes: the left one is done (and dripping), the right one is being painted now
        k2 = seg(t, 6.15, 7.3)
        _painted_eye(cv, KX - 52, KY - 6, 34, 1.0, 0.35 + 0.65 * seg(t, 6.0, 8.0), 8310, look=(0.5, 0.3))
        _painted_eye(cv, KX + 52, KY - 2, 31, k2, 0.0 if k2 < 1 else seg(t, 7.3, 8.2), 8320, look=(-0.4, 0.5))
        if k2 < 0.6:
            a = -math.pi / 2 + 2 * math.pi * min(1.0, k2 / 0.6)
            tip = (KX + 52 + 31 * math.cos(a), KY - 2 + 31 * 1.12 * math.sin(a))
        elif k2 < 1.0:
            a = (k2 - 0.6) / 0.4 * 18
            tip = (KX + 52 + 14 * math.cos(a), KY - 2 + 14 * math.sin(a))
        else:
            tip = (KX + 120 + 30 * seg(t, 7.3, 7.6), KY + 20)
        _doctor(cv, 1310, 930, 1.0, T, tip)
        if t > 6.3:                                                                                          # sweat on the blank face
            ph = (T * 1.3) % 1.0
            blob(cv, [(KX + 110, KY - 60 + 40 * ph - 20), (KX + 122, KY - 60 + 40 * ph + 4), (KX + 110, KY - 60 + 40 * ph + 14), (KX + 98, KY - 60 + 40 * ph + 4)],
                 P_["mint"], w=3, seed=8330, boil=0.5, n=4)
    return C


# ---------------------------------------------------------------- the soul
SOUL_X, SOUL_Y = 880, 600          # chest of the luminous figure (world)
LIGHT_XY = (1720, 430)            # the blazing opening it turns toward (world, parallax 0.8)
OPENING = [(1470, 900), (1452, 640), (1482, 420), (1556, 250), (1680, 168), (1830, 186), (1960, 250), (2050, 300), (2050, 900)]


def _soul_state(lt):
    """Shared timing for the soul segment (drawing + POST): camera, turn, bloom, ..."""
    d = seg(lt, SOUL_T0 + 0.05, 11.3)
    z = lerp(2.5, 1.0, ease_io(d))
    cx, cy = lerp(SOUL_X - 960, 0.0, ease_io(d)), lerp(SOUL_Y - 20 - 540, 0.0, ease_io(d))
    away = ease_io(seg(lt, *AWAY))
    toward = ease_io(seg(lt, *TOWARD))
    turn = ease_io(seg(lt, *TURN)) - 0.17 * toward
    bloom = ease_io(seg(lt, *BLOOM)) ** 1.2
    eye_open = ease(seg(lt, 9.75, 10.15))
    glow = 0.35 + 0.65 * ease(seg(lt, SOUL_T0 + 0.1, 9.0))
    x = SOUL_X + 110 * away + 90 * toward
    return dict(cam=dict(x=cx + 40 * toward, y=cy, z=z + 0.04 * toward), turn=turn, away=away, toward=toward, bloom=bloom, eye_open=eye_open,
                glow=glow, x=x)


def _rot_y(p, al):
    """Rotate a body-local 3D point (x right, y down, z toward camera) about the vertical axis; facing angle al
    (-90 deg = facing screen-left). Returns projected (x, y) and depth z."""
    x, y, z = p
    s_, c_ = math.sin(al), math.cos(al)
    return x * c_ + z * s_, y, -x * s_ + z * c_


def _soul_outline(turn, T, arms_up=0.0, seed=8500):
    """The figure's silhouette (head + ghostly body with a wispy tail) and feature anchors, in local coords
    (origin = chest). turn 0 = facing screen-left (profile), 0.5 = facing camera, 1 = facing screen-right."""
    al = math.radians(-90 + 180 * turn)
    sa, ca = math.sin(al), math.cos(al)
    sway = 14 * math.sin(T * 1.6)
    lean = 10 * sa
    body = [(-46 + lean * 0.6, -86), (-80 + lean * 0.4, -52), (-88, 20), (-74, 90), (-44, 150), (-14 + sway * 0.6, 205), (16 + sway * 1.2, 250),
            (34 + sway, 206), (52, 146), (76, 90), (88, 20), (80 + lean * 0.4, -52), (46 + lean * 0.6, -86)]
    head_c = (lean * 1.2, -170)
    hr = 96
    bp = poly_path(cr_closed(jit(body, 1.6, seed), 8))
    hp = poly_path(cr_closed(jit(ell(head_c[0], head_c[1], hr, hr * 0.98, n=14), 1.4, seed + 1), 6))
    sil = skia.Op(bp, hp, skia.PathOp.kUnion_PathOp) or bp
    arms = []
    for k, side in enumerate((-1, 1)):
        sh = _rot_y((side * 74, -50, 0), al)
        rest = (side * 122, 46, 118)
        up = (side * 215, -196, 40)
        rx_, ry_, rz_ = [rest[i] + (up[i] - rest[i]) * arms_up for i in range(3)]
        hd = _rot_y((rx_, ry_ + 8 * math.sin(T * 2.2 + k), rz_), al)
        el = _rot_y(((side * 74 + rx_) / 2 + side * 26, (-50 + ry_) / 2 + 10 * (1 - arms_up), rz_ * 0.5), al)
        arms.append(((sh[0] + lean * 0.4, sh[1]), (el[0] + lean * 0.3, el[1]), (hd[0] + lean * 0.3, hd[1]), (sh[2] + hd[2]) / 2))
    eyes = []
    for k, side in enumerate((-1, 1)):
        lon = al + side * math.radians(30)
        if math.cos(lon) > 0.08:
            eyes.append((head_c[0] + hr * 0.88 * math.sin(lon), head_c[1] - 6, math.cos(lon)))
    mouth = (head_c[0] + hr * 0.8 * sa, head_c[1] + 44, ca)
    chest = (70 * sa * 0.9, -6, max(0.25, ca + 0.35 * abs(sa)))
    return sil, arms, eyes, mouth, chest, head_c


def _soul_arm(cv, arm, c_out, c_in, glow, seed, front, colour=0.0):
    sh, el, hd, depth = arm
    ap = poly_path(cr_open(jit([sh, el, hd], 1.0, seed), 8), closed=False)
    glow_stroke(cv, ap, c_out, 54, 14, int((150 if front else 90) * glow))
    if colour > 0.02:
        glow_stroke(cv, ap, P_["vdark"], 40, 0, int(200 * colour))
    glow_stroke(cv, ap, mix(c_in, c_out, 0.3), 34, 0, int((170 if front else 110) * glow))
    glow_stroke(cv, ap, P_["white"], 3.4, 0, 235 if front else 150)
    radial(cv, hd[0], hd[1], 46, [(P_["white"], 250 if front else 160), (c_out, 140), (c_out, 0)], stops=[0.0, 0.5, 1.0])
    hp = cr_closed(jit(ell(hd[0], hd[1], 22, 22, n=8), 0.8, seed + 3), 4)
    cv.drawPath(poly_path(hp), paint(mix(c_in, P_["white"], 0.5), 230 if front else 150))
    brush(cv, hp, 3.0, P_["vdark"] if colour > 0.3 else P_["white"], closed=True, seed=seed + 4)


def _soul(cv, x, y, s, T, turn, glow=1.0, eye_open=1.0, colour=0.0, arms_up=0.0, seed=8500):
    """The luminous soul: translucent body, blurred glowing outline + crisp core, drifting inner sparks, glowing eyes,
    and the little eye of light in its chest."""
    sil, arms, eyes, mouth, chest, head_c = _soul_outline(turn, T, arms_up, seed)
    c_out = mix((110, 236, 255), P_["gold"], colour)
    c_in = mix((220, 255, 250), P_["white"], colour)
    with at(cv, x, y, s):
        for k, arm in enumerate(arms):                         # the far arm, behind the body
            if arm[3] < 0:
                _soul_arm(cv, arm, c_out, c_in, glow, seed + 9 + k * 5, False, colour)
        glow_fill(cv, sil, c_out, 40, int(110 * glow))
        glow_fill(cv, sil, c_in, 0, int(80 + 50 * glow))
        cv.save()
        cv.clipPath(sil, doAntiAlias=True)
        radial(cv, chest[0], chest[1] - 40, 260, [(c_out, int(90 * glow)), (c_out, 0)])
        if colour > 0.01:                                       # iridescent sheen once the colour arrives
            p = skia.Paint(AntiAlias=True)
            p.setShader(skia.GradientShader.MakeLinear([skia.Point(-120, -280), skia.Point(120, 260)],
                                                       [core.C(P_["hotpink"], int(150 * colour)), core.C(P_["yellow"], int(140 * colour)),
                                                        core.C(P_["teal"], int(150 * colour)), core.C(P_["violet"], int(140 * colour))], None))
            cv.drawRect(R(-200, -300, 200, 300), p)
        for k in range(16):                                     # sparks rising inside
            ph = (T * (0.18 + 0.05 * (k % 4)) + float(hsh(seed + k))) % 1.0
            px = -70 + 140 * float(hsh(seed + k * 3)) + 12 * math.sin(T * 2 + k)
            py = 230 - ph * 500
            dots(cv, [(px, py)], 2.5 + 3 * float(hsh(seed + k * 7)), P_["white"], a=int(220 * math.sin(math.pi * ph)))
        cv.restore()
        glow_stroke(cv, sil, c_out, 30, 14, int(220 * glow))
        if colour > 0.02:                                       # a deep rim so it still reads against the blaze
            glow_stroke(cv, sil, P_["vdark"], 12, 0, int(220 * colour))
        glow_stroke(cv, sil, c_in, 9, 2.5, int(235 * glow))
        glow_stroke(cv, sil, P_["white"], 3.4, 0, 255)
        for k, arm in enumerate(arms):                         # the near arm
            if arm[3] >= 0:
                _soul_arm(cv, arm, c_out, c_in, glow, seed + 9 + k * 5, True, colour)
        for ex, ey, f in eyes:                                  # soft glowing eyes
            radial(cv, ex, ey, 34, [(c_out, int(220 * glow)), (c_out, 0)])
            cv.drawPath(poly_path(cr_closed(jit(ell(ex, ey, 15 * f + 2, 21, n=10), 0.8, seed + 20), 4)), paint(P_["white"]))
            dots(cv, [(ex + 3 * (1 if turn > 0.5 else -1) * (1 - f), ey + 2)], 6.5 * f + 2, (40, 60, 120))
        mx, my, mf = mouth
        if mf > 0.15:
            line(cv, [(mx - 22 * mf, my - 4), (mx, my + 9 + 6 * colour), (mx + 22 * mf, my - 4)], 4.5, P_["white"], seed=seed + 30, boil=0.6, n=3, a=235)
        cx, cy, cf = chest                                      # the little eye of light already inside
        pul = 0.85 + 0.15 * math.sin(T * 5.0)
        radial(cv, cx, cy, 130 * pul * (0.6 + 0.4 * glow), [(P_["yellow"], int(220 * glow)), (P_["gold"], int(100 * glow)), (P_["gold"], 0)], stops=[0.0, 0.4, 1.0])
        for k in range(10):                                     # tiny rays
            a = k / 10 * 2 * math.pi + T * 0.6
            r0, r1 = 28, 48 + 16 * math.sin(T * 4 + k)
            line(cv, [(cx + r0 * math.cos(a), cy + r0 * math.sin(a)), (cx + r1 * math.cos(a), cy + r1 * math.sin(a))], 3.2, P_["yellow"], seed=seed + 40 + k, boil=0.4, n=2,
                 taper=(0.1, 0.6), a=int(230 * glow))
        ew, eh = 26 * cf + 6, 16
        oy = eh * eye_open
        if eye_open > 0.08:
            ep = [(cx - ew, cy), (cx - ew * 0.4, cy - oy), (cx + ew * 0.4, cy - oy), (cx + ew, cy), (cx + ew * 0.4, cy + oy * 0.9), (cx - ew * 0.4, cy + oy * 0.9)]
            P = cr_closed(jit(ep, 0.5, seed + 50), 5)
            cv.drawPath(poly_path(P), paint(P_["white"]))
            cv.save(); cv.clipPath(poly_path(P), doAntiAlias=True)
            lk = 6 * math.sin(T * 1.3) + 5 * (turn - 0.5) * 2
            dots(cv, [(cx + lk, cy)], 11, P_["teal"])
            dots(cv, [(cx + lk, cy)], 5, INK)
            dots(cv, [(cx + lk - 3, cy - 3)], 2.2, P_["white"])
            cv.restore()
            brush(cv, P, 3.0, (120, 60, 20), closed=True, seed=seed + 51)
        else:
            line(cv, [(cx - ew, cy), (cx, cy + 4), (cx + ew, cy)], 4, P_["white"], seed=seed + 52, boil=0.5, n=3)


def _sun_disc(cv, x, y, r, T, a=1.0, seed=8590):
    radial(cv, x, y, r * 4.0, [(P_["white"], int(255 * a)), (P_["yellow"], int(230 * a)), (P_["orange"], int(120 * a)), (P_["orange"], 0)], stops=[0.0, 0.22, 0.55, 1.0])
    for k in range(18):
        ang = k / 18 * 2 * math.pi + T * 0.25
        L = r * (1.6 + 0.35 * math.sin(T * 3 + k * 1.7))
        line(cv, [(x + r * 1.08 * math.cos(ang), y + r * 1.08 * math.sin(ang)), (x + L * math.cos(ang), y + L * math.sin(ang))], 7, P_["white"], seed=seed + k, boil=0.6, n=2,
             taper=(0.1, 0.7), a=int(220 * a))
    cv.drawCircle(x, y, r, paint(P_["white"], int(255 * a)))
    brush(cv, cr_closed(jit(ell(x, y, r, r, n=14), 1.2, seed + 30), 4), 5, P_["yellow"], closed=True, seed=seed + 31, a=int(255 * a))


def _soul_cave(cv, T, C, st, lt):
    """The cave around the soul: the shadow wall (left), floor, rock, and the blazing opening (right)."""
    turn, away, toward, bloom = st["turn"], st["away"], st["toward"], st["bloom"]
    light = 0.55 + 0.2 * turn + 0.25 * toward
    with C.layer(0.5):
        w.field(cv, CV_ROCK_DK)
        rock_mass(cv, [(-300, -300), (2300, -300), (2300, 1300), (-300, 1300)], seed=8601, rgb=(40, 16, 80), ink=0)
        for k in range(6):
            crystal(cv, 160 + k * 300, 860 + 30 * math.sin(k * 2.3), 0.8, T, seed=8610 + k)
    with C.layer(0.8):
        lx, ly = LIGHT_XY
        radial(cv, lx, ly, 1100 + 500 * toward, [(P_["yellow"], int(150 * light)), (P_["orange"], int(80 * light)), (P_["magenta"], 0)], stops=[0.0, 0.4, 1.0],
               rect=(-400, -400, W + 400, H + 400))
        op = poly_path(cr_closed(jit(OPENING, 1.5, 8615), 5))
        cv.save()
        cv.clipPath(op, doAntiAlias=True)
        radial(cv, lx, ly, 700, [(P_["white"], 255), (P_["yellow"], 255), (P_["orange"], 255), (P_["magenta"], 255)], stops=[0.0, 0.25, 0.6, 1.0], rect=(1300, 0, 2200, 1000))
        w.hills(cv, 760, 70, [mix(P_["acid"], P_["yellow"], 0.4), mix(P_["teal"], P_["white"], 0.3), P_["acid"]], seed=8616, freq=3.0, spacing=26)
        _sun_disc(cv, lx, ly - 30, 82 + 10 * toward, T, a=1.0)
        cv.restore()
        rk = skia.Path()
        rk.addRect(R(1300, -300, 2300, 1300))
        rk = skia.Op(rk, op, skia.PathOp.kDifference_PathOp) or rk
        p_ = paint(CV_ROCK)
        cv.drawPath(rk, p_)
        cv.save()
        cv.clipPath(rk, doAntiAlias=True)
        stipple(cv, mix(CV_ROCK, INK, 0.45), (1300, -300, 2300, 1300), spacing=15, r=2.0, seed=8617,
                fn=lambda X, Y: np.clip(0.3 + 0.7 * np.sin(X * 0.013 + Y * 0.02) ** 2, 0, 1) * 0.8)
        glow_stroke(cv, op, P_["gold"], 60, 18, int(200 * light))
        cv.restore()
        brush(cv, cr_closed(jit(OPENING, 1.5, 8615), 5), 6, closed=True, seed=8618)
    with C.layer(1.0):
        wall = [(-200, 60), (440, 90), (500, 400), (470, 760), (430, 900), (-200, 900)]
        wall_surface(cv, wall, T, seed=8630, cx=200, cy=480, glow=0.6 + 0.3 * light)
        cv.save()
        cv.clipPath(poly_path(cr_closed(wall, 4)), doAntiAlias=True)
        fade = 1.0 - 0.85 * away
        for k, (kind, sx, sy, ss) in enumerate((("bunny", 110, 250, 1.1), ("horse", 300, 660, 0.95))):
            shadow_shape(cv, kind, sx + 14 * math.sin(T * 0.7 + k), sy, ss * (1 - 0.4 * away), T, a=int(210 * fade), seed=8640 + k)
        sil = _soul_outline(turn, T, 0.0, seed=8500)[0]
        sc = 1.05 * (1 - 0.25 * away)
        m = skia.Matrix()
        m.setScale(sc, sc)
        m.postTranslate(270 - 50 * away, 430)
        sp = skia.Path(sil)
        sp.transform(m)
        glow_fill(cv, sp, CV_SHADOW, 12, int(190 * fade))
        cv.drawPath(sp, paint(CV_SHADOW, int(215 * fade)))
        cv.restore()
        rock_mass(cv, [(-300, 860), (600, 840), (1200, 870), (1500, 880), (2300, 860), (2300, 1300), (-300, 1300)], seed=8650, rgb=CV_ROCK2, rim=P_["gold"], rim_side=1)
        for k in range(12):
            px = 40 + k * 165 + 40 * math.sin(k * 3.1)
            blob(cv, ell(px, 930 + 50 * float(hsh(8660 + k * 9)), 16 + 10 * float(hsh(8661 + k)), 9, n=8), mix(CV_ROCK2, P_["lilac"], 0.25), w=3, seed=8670 + k, boil=0.5)
        rock_mass(cv, [(-300, -300), (2300, -300), (2300, 30), (1500, 70), (900, 40), (300, 90), (-300, 60)], seed=8680, rgb=CV_ROCK, rim=P_["magenta"], rim_side=1)
        for k in range(9):                                     # stalactites
            sx = 120 + k * 190 + 40 * math.sin(k * 2.3)
            if sx > 1400:
                continue
            sl = 70 + 70 * float(hsh(8690 + k))
            blob(cv, [(sx - 26, 60), (sx + 26, 60), (sx + 4, 60 + sl), (sx - 2, 64 + sl)], CV_ROCK2, w=4, seed=8700 + k, boil=0.8, n=3)
        for k in range(6):
            glow_mushroom(cv, 560 + k * 150 + 30 * math.sin(k * 2.2), 890 + 20 * math.sin(k * 1.7), 0.7, T, seed=8710 + k)


def _soul_bloom_layer(cv, T, C, st, lt):
    """Everything that arrives with the colour: god rays from the opening, flowers, a ribbon, sparkles."""
    bloom, toward = st["bloom"], st["toward"]
    with C.layer(0.8):
        lx, ly = LIGHT_XY
        n = 16
        for k in range(n):                                     # god rays raking across the cave toward the wall
            u = (k + 0.5) / n
            aa = math.radians(180 + 50 * (u - 0.5) + 2.5 * math.sin(T * 0.5 + k))
            wd = math.radians(1.5 + 1.3 * math.sin(T * 0.8 + k * 1.7))
            r = 2300
            p = [(lx, ly), (lx + r * math.cos(aa - wd), ly + r * math.sin(aa - wd)), (lx + r * math.cos(aa + wd), ly + r * math.sin(aa + wd))]
            sh = skia.Paint(AntiAlias=True)
            sh.setShader(skia.GradientShader.MakeRadial(skia.Point(lx, ly), r, [core.C(P_["yellow"], int(60 + 110 * toward + 40 * bloom)), core.C(P_["yellow"], 0)], None))
            sh.setBlendMode(SCREEN_B)
            cv.drawPath(poly_path(p), sh)
    with C.layer(1.0):
        if bloom > 0.3:
            ctrl = [(1660, 400), (1420, 170), (1080, 250), (760, 130), (420, 230), (60, 150), (-300, 240)]
            dense = cr_open(np.array(ctrl, float), 10)
            m = max(3, int(len(dense) * min(1.0, (bloom - 0.3) * 2.2)))
            w.ribbon(cv, dense[:m], 40 + 50 * bloom, [P_["magenta"], P_["orange"], P_["yellow"], P_["acid"], P_["teal"]], flow=T * 1.2, seed=8800, ink=4)
        for k in range(15):                                    # flowers popping up from the floor, nearest the light first
            fx = 1460 - k * 100 + 30 * math.sin(k * 2.7)
            fy = 880 + 26 * math.sin(k * 1.9)
            kk = pop(bloom * 2700 - math.hypot(fx - LIGHT_XY[0], fy - LIGHT_XY[1]), 160, 260)
            if kk <= 0.01:
                continue
            _flower(cv, fx, fy, (0.55 + 0.35 * float(hsh(8810 + k))) * kk, T, seed=8820 + k * 7, kind=k % 3)
        for k in range(18):
            if bloom < 0.2:
                break
            a = float(hsh(8900 + k)) * 6.283 + T * 0.3
            rr = 180 + 520 * float(hsh(8901 + k))
            sparkle(cv, 1300 + rr * math.cos(a) * 1.3, 420 + rr * math.sin(a) * 0.6, 8 + 10 * float(hsh(8902 + k)), [P_["yellow"], P_["white"], P_["hotpink"], P_["acid"]][k % 4],
                    seed=8903 + k, a=int(255 * min(1.0, (bloom - 0.2) * 2)))


def _flower(cv, x, y, s, T, seed=0, kind=0):
    """A psychedelic flower (base x, y): wobbly stem with two leaves, petals, and a face or an eye in the middle."""
    if s <= 0.01:
        return
    sw = 8 * math.sin(T * 2.4 + seed)
    top = (x + sw * s * 2, y - 150 * s)
    line(cv, [(x, y), (x + sw * s, y - 70 * s), top], 9 * s + 2, P_["acid_dk"], seed=seed, boil=0.7, n=4, taper=(0, 0))
    for side in (-1, 1):
        blob(cv, [(x + sw * s * 0.8, y - 60 * s), (x + side * 50 * s, y - 90 * s), (x + side * 70 * s, y - 70 * s), (x + side * 30 * s, y - 50 * s)], P_["acid"], w=3 * min(1, s * 2) + 1,
             seed=seed + 2 + side, boil=0.6, n=3)
    cols = [(P_["hotpink"], P_["yellow"]), (P_["orange"], P_["magenta"]), (P_["teal"], P_["yellow"]), (P_["violet"], P_["acid"])][(seed // 7) % 4]
    npet = 7 if kind != 1 else 5
    spin = T * 0.5 + seed
    for k in range(npet):
        a = k / npet * 2 * math.pi + spin
        px, py = top[0] + 44 * s * math.cos(a), top[1] + 44 * s * math.sin(a)
        blob(cv, ell(px, py, 34 * s, 20 * s, n=7, rot=math.degrees(a)), cols[0], w=3.5 * min(1, s * 1.6) + 1, seed=seed + 10 + k, boil=0.6, n=4)
    blob(cv, ell(top[0], top[1], 30 * s, 30 * s, n=9), cols[1], w=4 * min(1, s * 1.6) + 1, seed=seed + 20, boil=0.6, n=5)
    if kind == 2:
        dots(cv, [top], 15 * s, P_["white"])
        dots(cv, [(top[0] + 3 * s, top[1])], 8 * s, INK)
    else:
        for side in (-1, 1):
            dots(cv, [(top[0] + side * 10 * s, top[1] - 4 * s)], 4 * s + 0.8, INK)
        line(cv, [(top[0] - 11 * s, top[1] + 8 * s), (top[0], top[1] + 15 * s), (top[0] + 11 * s, top[1] + 8 * s)], 2.5 * min(1, s * 2) + 0.8, seed=seed + 30, boil=0.4, n=3)


def _soul_scene(cv, t, T):
    st = _soul_state(t)
    C = sets.Cam(cv, st["cam"])
    _soul_cave(cv, T, C, st, t)
    _soul_bloom_layer(cv, T, C, st, t)
    with C.layer(1.0):
        y = SOUL_Y - 12 * math.sin(T * 1.4) - 40 * st["toward"]
        tw = st["toward"]
        if tw > 0.01:                                          # a rainbow aura blossoms behind it
            cols = [P_["magenta"], P_["orange"], P_["yellow"], P_["acid"], P_["teal"], P_["violet"]]
            for k in range(6):
                r = (420 - k * 52) * (0.4 + 0.6 * tw) + 8 * math.sin(T * 3 + k)
                p = poly_path(cr_closed(jit(ell(st["x"] + 20, y - 60, r, r * 1.08, n=20, phase=k * 0.4), 2.5, 8950 + k), 4))
                glow_fill(cv, p, cols[k], 18, int(70 * tw))
            ox, oy = st["x"] + 20, y - 60
            for k in range(14):                                # a slowly turning rainbow sunburst
                a1 = k / 14 * 2 * math.pi + T * 0.35
                a2 = a1 + 2 * math.pi / 28
                rr = 900 * tw
                pp = skia.Paint(AntiAlias=True)
                pp.setShader(skia.GradientShader.MakeRadial(skia.Point(ox, oy), rr, [core.C(cols[k % 6], int(150 * tw)), core.C(cols[k % 6], 0)], None))
                pp.setBlendMode(SCREEN_B)
                cv.drawPath(poly_path([(ox, oy), (ox + rr * math.cos(a1), oy + rr * math.sin(a1)), (ox + rr * math.cos(a2), oy + rr * math.sin(a2))]), pp)
        _soul(cv, st["x"], y, 1.0, T, st["turn"], glow=st["glow"] * (1 + 0.3 * st["toward"]), eye_open=st["eye_open"],
              colour=st["bloom"] * 0.8, arms_up=st["toward"])
    if t < SOUL_T0 + 0.35:                                     # fade up from the iris black
        darkness(cv, 255 * (1 - seg(t, SOUL_T0, SOUL_T0 + 0.35)))


def T049_education(cv, t, T, A):
    if t < T49_CUT1:                                           # Zee: 'Here's the best part.'
        z = 1.9 + 0.08 * t
        studio(cv, T, A, dict(x=CAM_ZEE["x"] + 10 * t, y=CAM_ZEE["y"] + 6, z=z), t)
        return
    if t < T49_PAN[0]:
        _classroom(cv, t, T)
        red_x(cv, 900, 520, 820, seg(t, T49_X1, T49_X1 + 0.7) * 2.0 if t > T49_X1 else 0, seed=9100)
        return
    if t < T49_PAN[1]:                                         # whip pan (classroom out left, doctor in from right)
        u = ease_io(seg(t, *T49_PAN))
        off = -W * u
        cv.save(); cv.translate(off, 0)
        cv.clipRect(R(0, 0, W, H))
        _classroom(cv, t, T)
        red_x(cv, 900, 520, 820, 2.0, seed=9100)
        cv.restore()
        cv.save(); cv.translate(off + W, 0)
        cv.clipRect(R(0, 0, W, H))
        _doctor_office(cv, t, T)
        cv.restore()
        for k in range(26):                                    # speed streaks
            yy = (k * 97) % H
            L = 300 + 500 * float(hsh(9200 + k))
            xx = (float(hsh(9210 + k)) * (W + L)) - L
            line(cv, [(xx, yy), (xx + L, yy)], 6 + 10 * float(hsh(9220 + k)), P_["white"], seed=9230 + k, boil=0.4, n=2, taper=(0.4, 0.4), a=170)
        return
    if t < SOUL_T0:
        _doctor_office(cv, t, T)
        red_x(cv, 860, 520, 800, seg(t, T49_X2, T49_X2 + 0.7) * 2.0 if t > T49_X2 else 0, seed=9300)
        if t > T49_IRIS[0]:
            r = lerp(1300, 0, ease(seg(t, *T49_IRIS)))
            iris_wipe(cv, 800, 640, r)
        return
    _soul_scene(cv, t, T)


_DUO_LUT = None


def _duo(img, f):
    """Violet tritone where f == 0, the true colour where f == 1."""
    global _DUO_LUT
    if _DUO_LUT is None:
        L = np.linspace(0, 1, 256)
        Ls = L * L * (3 - 2 * L)                          # S-curve for punch
        k0, k1, k2 = np.array([12, 4, 34.0]), np.array([92, 52, 190.0]), np.array([226, 214, 255.0])
        lut = np.where(Ls[:, None] < 0.5, k0 + (k1 - k0) * (Ls[:, None] / 0.5), k1 + (k2 - k1) * ((Ls[:, None] - 0.5) / 0.5))
        _DUO_LUT = lut.astype(np.float32)
    a = img.astype(np.float32)
    L = (a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114).astype(np.uint8)
    duo = _DUO_LUT[L]
    out = duo + (a - duo) * f[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)


_GRID4 = None


def _grid4():
    global _GRID4
    if _GRID4 is None:
        ys, xs = np.mgrid[0:H:4, 0:W:4]
        _GRID4 = (xs.astype(np.float32) + 2, ys.astype(np.float32) + 2)
    return _GRID4


def _post_049(img, lt, dur, T):
    if lt < SOUL_T0:
        return img
    st = _soul_state(lt)
    C = sets.Cam(None, st["cam"])
    xs, ys = _grid4()
    zf = C.zoom(1.0)
    # the soul keeps its own colour (an aura around the whole figure)
    cx, cy = C.to_screen(st["x"], SOUL_Y - 50, 1.0)
    d = np.hypot((xs - cx) / (240 * zf), (ys - cy) / (360 * zf))
    f = np.clip((1.0 - d) / 0.35, 0, 1)
    if st["bloom"] > 0:                                    # the bloom spreading out of the light
        lx, ly = C.to_screen(*LIGHT_XY, 0.8)
        rb = 2700 * st["bloom"]
        f = np.maximum(f, np.clip((rb - np.hypot(xs - lx, ys - ly)) / 420.0, 0, 1))
    lx, ly = C.to_screen(*LIGHT_XY, 0.8)                   # and the light itself is always golden
    f = np.maximum(f, np.clip((420 * C.zoom(0.8) - np.hypot(xs - lx, ys - ly)) / 200.0, 0, 1))
    if f.min() >= 0.999:
        return img
    F = np.repeat(np.repeat(f, 4, 0), 4, 1)[:H, :W]
    return _duo(img, F)


POST = {"T049_education": _post_049}


# ===================================================================== T051: the turn
TV_A, TV_B = 172.0, 118.0          # half-width / half-depth of the host's CRT case (head-local units)


def _tv_front(cv, P, seed, light=0.0):
    """The front of the host's TV (case + screen + phosphor face): _tv_head without the antennae."""
    case = [(-166, -116), (166, -116), (176, -40), (172, 96), (150, 118), (-150, 118), (-172, 96), (-176, -40)]

    def sh(c):
        c.drawPath(poly_path([(110, -130), (190, -130), (190, 130), (96, 130)]), paint(_cast.CASE_SH))
        stipple(c, _cast.CASE_SH, (-180, -130, 190, 130), spacing=12, r=1.8, seed=seed, fn=lambda X, Y: np.clip((X - 40) / 90, 0, 1))
    blob(cv, case, _cast.CASE, w=6.5, seed=seed, boil=1.2, n=5, shade=sh)
    for k in range(2):
        kx, ky = 142, -54 + k * 64
        blob(cv, ell(kx, ky, 15, 15, n=8), P_["orange"], w=4, seed=seed + 70 + k, boil=0.6)
        line(cv, [(kx, ky), (kx + 9 * math.cos(core.D * 0.3 + k), ky + 9 * math.sin(core.D * 0.3 + k))], 3.5, seed=seed + 72 + k, boil=0.3, n=2)
    for k in range(4):
        line(cv, [(122 + k * 9, 70), (122 + k * 9, 100)], 3.0, seed=seed + 80 + k, boil=0.5, n=2, taper=(0, 0))
    scr = [(-140, -96), (96, -96), (104, -10), (96, 92), (-140, 92), (-150, -2)]
    Ps = cr_closed(jit(scr, 0.9, seed + 5), 6)
    spath = poly_path(Ps)
    cv.drawPath(spath, paint(_cast.SCREEN))
    cv.save()
    cv.clipPath(spath, doAntiAlias=True)
    cv.drawPath(poly_path(cr_closed(ell(-22, -2, 116, 86, n=12), 4)), paint((26, 60, 80)))
    if light > 0.01:
        radial(cv, 60, -80, 260, [(P_["gold"], int(110 * light)), (P_["gold"], 0)])
    cv.save()
    cv.translate(-22, -4)
    _cast._screen_face(cv, P, seed + 200, 236.0, 168.0)
    cv.restore()
    for k in range(-100, 100, 7):
        cv.drawRect(R(-160, k, 110, k + 2.4), paint((0, 0, 0), 70))
    roll = (core.D * 11) % 260 - 130
    cv.drawRect(R(-160, roll, 110, roll + 18), paint(_cast.PHOS, 22))
    cv.drawPath(poly_path(cr_closed([(-120, -84), (-60, -90), (-110, -40)], 3)), paint((255, 255, 255), 38))
    cv.restore()
    brush(cv, Ps, 6.0, closed=True, seed=seed + 6)


def _tv_side(cv, x0, x1, seed):
    """The case's side panel between x0 and x1 (vents + a little brand plate)."""
    if x1 - x0 < 2:
        return
    pts = rect_pts([(x0, -112), (x1, -112), (x1, 114), (x0, 114)], 3)

    def sh(c):
        c.drawRect(R(x0 - 5, -120, x0 + (x1 - x0) * 0.22, 120), paint(mix(_cast.CASE_SH, INK, 0.25)))
        for k in range(6):
            yy = -70 + k * 22
            c.drawLine(x0 + (x1 - x0) * 0.32, yy, x0 + (x1 - x0) * 0.78, yy, paint(INK, stroke=max(1.5, 4.0 * min(1.0, (x1 - x0) / 120))))
    blob(cv, pts, _cast.CASE_SH, w=6, seed=seed, boil=1.0, n=3, shade=sh)


def _tv_back(cv, P, seed, light=0.0):
    """The BACK of the host's TV: the case rim, the bulging rear housing full of vents, a serial plate and a sticker
    reading PROPERTY OF THE CAVE."""
    case = [(-166, -116), (166, -116), (176, -40), (172, 96), (150, 118), (-150, 118), (-172, 96), (-176, -40)]
    blob(cv, case, _cast.CASE, w=6.5, seed=seed, boil=1.2, n=5,
         shade=lambda c: (c.drawPath(poly_path([(-190, -130), (-110, -130), (-96, 130), (-190, 130)]), paint(_cast.CASE_SH)),
                          stipple(c, _cast.CASE_SH, (-180, -130, 190, 130), spacing=12, r=1.8, seed=seed, fn=lambda X, Y: np.clip((-X - 40) / 90, 0, 1))))
    hous = [(-128, -92), (128, -92), (140, -40), (134, 88), (-134, 88), (-140, -40)]

    def hs(c):
        c.drawRect(R(-150, 30, 150, 100), paint(mix(_cast.CASE_SH, INK, 0.2)))
        for row in range(5):                                        # vent slots
            for col in range(7):
                vx, vy = -102 + col * 34, -70 + row * 22
                c.drawPath(poly_path(cr_closed(ell(vx, vy, 12, 4.2, n=8), 3)), paint((14, 30, 40)))
        if light > 0.01:
            radial(c, 40, -60, 200, [(P_["gold"], int(120 * light)), (P_["gold"], 0)])
    blob(cv, hous, mix(_cast.CASE, _cast.CASE_SH, 0.55), w=5.5, seed=seed + 3, boil=1.0, n=4, shade=hs)
    blob(cv, rect_pts([(-120, 50), (-50, 50), (-50, 76), (-120, 76)], 2), (190, 196, 210), w=3.5, seed=seed + 4, boil=0.6, n=3)      # serial plate
    for k in range(3):
        line(cv, [(-114, 57 + k * 7), (-60, 57 + k * 7)], 1.6, (90, 90, 110), seed=seed + 5 + k, boil=0.3, n=2, taper=(0, 0))
    cv.save()                                                         # the sticker
    cv.translate(46, 2)
    cv.rotate(-7)
    blob(cv, rect_pts([(-94, -44), (94, -44), (94, 44), (-94, 44)], 3), P_["cream"], w=4.5, seed=seed + 10, boil=0.8, n=3,
         shade=lambda c: (c.drawRect(R(-100, -50, 100, -30), paint(P_["red"])), c.drawRect(R(-100, 34, 100, 50), paint(P_["red"]))))
    paint_text(cv, "PROPERTY OF", 0, 2, font="londrina", size=27, fill=INK, ink_w=0, shadow=None, seed=seed + 11, wobble=0.5, streaks=False, rot_jit=2.0)
    paint_text(cv, "THE CAVE", 0, 30, font="bangers", size=30, fill=P_["red"], ink_w=0, shadow=None, seed=seed + 12, wobble=0.5, streaks=False, rot_jit=2.0,
               spacing=2.0)
    line(cv, [(70, -44), (94, -20)], 3, P_["cream_sh"], seed=seed + 13, boil=0.3, n=2, taper=(0, 0))     # a peeling corner
    cv.restore()


def _tv_turn_head(cv, P, seed, phi, light=0.0, cord_sw=0.0):
    """The host's TV head rotated phi degrees about the neck (0 = facing us, 90 = edge-on, 180 = back to us)."""
    ph = math.radians(phi)
    sphi, cphi = math.sin(ph), math.cos(ph)
    for side, key in ((-1, "antL"), (1, "antR")):                     # antennae ride on the top centre
        dx, dy = P[key]
        base = np.array([side * 20.0 * cphi, -126.0])
        tip = np.array([(side * 112 + dx) * cphi + 26 * sphi * side * 0.3, -276 + dy])
        line(cv, [base, (base + tip) / 2 + np.array([dx * 0.2, 0]), tip], 6.0, (200, 200, 220), seed=seed + 60 + side, boil=0.9, n=6, taper=(0, 0))
        blob(cv, ell(tip[0], tip[1], 11, 11, n=7), P_["orange"], w=4, seed=seed + 62 + side, boil=0.6)
    blob(cv, ell(0, -126, max(8.0, 34 * abs(cphi) + 16 * sphi), 16, n=8), _cast.CASE_SH, w=5, seed=seed + 64, boil=0.8)
    if phi > 92:                                                      # the power cord dangling off the back
        cx0 = -TV_B * sphi + 70 * abs(cphi)
        sw = cord_sw
        cord = [(cx0, 80), (cx0 + 30 + sw * 0.3, 190), (cx0 + 10 + sw, 300), (cx0 + 26 + sw * 1.4, 380)]
        line(cv, cord, 13, INK, seed=seed + 90, boil=0.8, n=8, taper=(0, 0))
        line(cv, cord, 7, (60, 56, 80), seed=seed + 90, boil=0.8, n=8, taper=(0, 0))
        px, py = cord[-1]
        blob(cv, rect_pts([(px - 16, py), (px + 16, py), (px + 14, py + 34), (px - 14, py + 34)], 2), (40, 36, 52), w=4, seed=seed + 91, boil=0.5, n=3)
        for side in (-1, 1):
            line(cv, [(px + side * 7, py + 34), (px + side * 7, py + 54)], 5, (210, 200, 160), seed=seed + 92 + side, boil=0.3, n=2, taper=(0, 0))
    if 0.5 < phi < 179.5:                                             # the side panel (left side, turned toward us)
        _tv_side(cv, -TV_A * cphi - TV_B * sphi, -TV_A * cphi + TV_B * sphi, seed + 30)
    if phi < 89.5:
        cv.save()
        cv.translate(TV_B * sphi, 0)
        cv.scale(max(0.02, cphi), 1.0)
        _tv_front(cv, P, seed, light)
        cv.restore()
    elif phi > 90.5:
        cv.save()
        cv.translate(-TV_B * sphi, 0)
        cv.scale(max(0.02, -cphi), 1.0)
        _tv_back(cv, P, seed + 400, light)
        cv.restore()


def _host_turn(cv, P0, phi, light=0.0, cord_sw=0.0, seed=3000):
    """cast.draw_host with the TV head swivelled by phi degrees (copied from cast.draw_host; everything else identical)."""
    P = dict(_cast.HOST_DEFAULTS)
    P.update(P0)
    s = float(P["s"])
    old = core.INKMUL
    core.INKMUL = old / max(s, 0.15) ** 0.5
    try:
        cv.save()
        cv.translate(P["x"], P["y"])
        cv.scale(s, s)
        hip = P["hip"]
        if P["legs"]:
            _cast._host_legs(cv, P, seed)
        cv.save()
        cv.rotate(P["lean"], hip, -186)
        br = 1 + 0.012 * math.sin(P["breath"] * 2 * math.pi)
        tilt = math.radians(P["head_tilt"])
        hx, hy = hip, _cast.HEAD_Y + P["head_dy"]
        bx, by = hx - math.sin(tilt) * 110 * _cast.HEAD_S, hy + math.cos(tilt) * 110 * _cast.HEAD_S
        neck = [(hip, -370), (hip + (bx - hip) * 0.4 + 6, (by - 370) * 0.5 - 185), (bx, by)]
        line(cv, neck, 34, INK, seed=seed + 150, boil=0.8, n=6, taper=(0, 0), var=0.05)
        cv.save(); cv.translate(1.2, 0.8)
        line(cv, neck, 24, _cast.NECK, seed=seed + 150, boil=0.8, n=6, taper=(0, 0), var=0.05)
        cv.restore()
        ctrl = np.array([(-28, -398), (-80, -394), (-102, -372), (-100, -300), (-92, -220), (-98, -150), (-40, -140),
                         (40, -140), (98, -150), (92, -220), (100, -300), (102, -372), (80, -394), (28, -398)], float)
        ctrl[:, 0] = ctrl[:, 0] * br + hip
        ctrl[:, 1] = -150 + (ctrl[:, 1] + 150) * br

        def jshade(c):
            c.drawPath(poly_path(cr_closed([(44 + hip, -392), (120 + hip, -380), (120 + hip, -130), (52 + hip, -130), (64 + hip, -260)], 5)), paint(_cast.SUIT_SH))
            stipple(c, _cast.SUIT_SH, (-110 + hip, -400, 110 + hip, -130), spacing=13, r=1.6, seed=seed + 9, fn=lambda X, Y: np.clip(((X - hip) - 10) / 70, 0, 1) * 0.8)
        blob(cv, ctrl, _cast.SUIT, w=6.0, seed=seed + 200, boil=1.3, n=7, shade=jshade)
        vy = -262 + 6 * (br - 1) * 100
        blob(cv, [(hip - 24, -394), (hip + 24, -394), (hip, vy)], _cast.SHIRT, w=4.0, seed=seed + 210, boil=0.8, n=3)
        for side in (-1, 1):
            lap = [(hip + side * 24, -394), (hip + side * 62, -390), (hip + side * 54, -352), (hip + side * 38, -330), (hip + side * 4, vy + 4)]
            blob(cv, lap, _cast.LAPEL, w=4.0, seed=seed + 220 + side, boil=0.9, n=4)
            line(cv, [(hip + side * 58, -384), (hip + side * 50, -350), (hip + side * 34, -326), (hip + side * 8, vy - 6)], 3.6, _cast.PIPING,
                 seed=seed + 226 + side, boil=0.6, n=5, taper=(0.1, 0.1))
        blob(cv, ell(hip, vy + 14, 7, 7, n=7), P_["gold"], w=3.0, seed=seed + 230, boil=0.4)
        blob(cv, ell(hip, vy + 70, 6, 6, n=7), P_["gold"], w=3.0, seed=seed + 231, boil=0.4)
        line(cv, [(hip + 70, -254), (hip + 92, -256)], 3.0, seed=seed + 232, boil=0.5, n=2)
        bty = -386
        for side in (-1, 1):
            blob(cv, [(hip + side * 6, bty), (hip + side * 44, bty - 20), (hip + side * 48, bty + 2), (hip + side * 42, bty + 20)], _cast.PIPING, w=4.0,
                 seed=seed + 240 + side, boil=0.7, n=3)
        blob(cv, ell(hip, bty, 10, 10, n=7), P_["orange"], w=3.5, seed=seed + 244, boil=0.5)
        cv.save()
        cv.translate(hx, hy)
        cv.rotate(P["head_tilt"])
        sq = P["squash"]
        cv.scale(_cast.HEAD_S * (1 + (1 - sq) * 0.6), _cast.HEAD_S * sq)
        _tv_turn_head(cv, P, seed + 300, phi, light, cord_sw)
        cv.restore()
        hands = {}
        for side, pre in ((-1, "aL"), (1, "aR")):
            sx, sy = side * 74 + hip, -370
            wx, wy, fdir = _cast._host_arm(cv, sx, sy, P[pre + "_sh"], P[pre + "_el"], seed + 400 + side * 20)
            hands[pre] = (wx, wy, fdir + P[pre + "_hand"])
        for side, pre in ((-1, "aL"), (1, "aR")):
            wx, wy, ang = hands[pre]
            _hand(cv, wx, wy, ang, P[pre + "_pose"], 1 if side < 0 else -1, seed + 500 + side * 30, rgb=_cast.GLOVE, cuff=_cast.GLOVE)
        cv.restore()
        cv.restore()
        return hands
    finally:
        core.INKMUL = old


SEAM = [(960 + 34 * math.sin(k * 2.39) + 22 * math.sin(k * 5.1), -520 + k * 2100 / 15) for k in range(16)]
SUN_W = (960, 600)                 # where the sun sits behind the set (parallax 0.22)


def _beyond(cv, T, cam, light=1.0, seed=7300):
    """What was behind the backdrop all along: a cave mouth opening onto a blazing psychedelic sunrise."""
    C = sets.Cam(cv, cam)
    sx, sy = SUN_W
    with C.layer(0.22):
        w.field(cv, P_["violet"])
        radial(cv, sx, sy, 1500, [(P_["white"], 255), (P_["yellow"], 255), (P_["orange"], 255), (P_["magenta"], 255), (P_["violet"], 255)],
               stops=[0.0, 0.1, 0.28, 0.55, 1.0], rect=(-600, -600, W + 600, H + 600))
        for k in range(16):                                         # turning sunburst
            a1 = k / 16 * 2 * math.pi + T * 0.12
            a2 = a1 + math.pi / 16
            pp = skia.Paint(AntiAlias=True)
            pp.setShader(skia.GradientShader.MakeRadial(skia.Point(sx, sy), 1400, [core.C(P_["white"], 120), core.C(P_["yellow"], 0)], None))
            pp.setBlendMode(SCREEN_B)
            cv.drawPath(poly_path([(sx, sy), (sx + 1600 * math.cos(a1), sy + 1600 * math.sin(a1)), (sx + 1600 * math.cos(a2), sy + 1600 * math.sin(a2))]), pp)
        rg = dict(rx=1.85, ry=0.3, rgb=mix(P_["gold"], P_["white"], 0.4), rgb2=P_["white"], tilt=-12)
        w._ring(cv, sx, sy, 150, rg, seed + 1, "back")
        cv.drawCircle(sx, sy, 150, paint(P_["white"]))
        brush(cv, cr_closed(jit(ell(sx, sy, 150, 150, n=16), 1.2, seed + 2), 4), 6, P_["yellow"], closed=True, seed=seed + 3)
        w._ring(cv, sx, sy, 150, rg, seed + 1, "front")
        radial(cv, sx, sy, 420, [(P_["white"], 200), (P_["white"], 0)])
        for k, (yy, col) in enumerate(((760, mix(P_["magenta"], P_["orange"], 0.4)), (820, P_["magenta"]), (880, mix(P_["violet"], P_["magenta"], 0.4)))):
            w.wavy_band(cv, yy, 900, col, amp=34 - k * 6, freq=1.2 + k * 0.5, seed=seed + 10 + k)
    with C.layer(0.32):                                             # the rock of the cave mouth around the light
        arch = [(260, 1300), (300, 760), (420, 420), (640, 190), (960, 110), (1280, 190), (1500, 420), (1620, 760), (1660, 1300)]
        ap = poly_path(cr_closed(jit(arch, 1.5, seed + 20), 6))
        rk = skia.Path()
        rk.addRect(R(-700, -700, W + 700, H + 700))
        rk = skia.Op(rk, ap, skia.PathOp.kDifference_PathOp) or rk
        cv.drawPath(rk, paint(CV_ROCK))
        cv.save()
        cv.clipPath(rk, doAntiAlias=True)
        stipple(cv, mix(CV_ROCK, INK, 0.45), (-200, -200, W + 200, H + 200), spacing=16, r=2.2, seed=seed + 21,
                fn=lambda X, Y: np.clip(0.3 + 0.7 * np.sin(X * 0.011 + Y * 0.017) ** 2, 0, 1) * 0.8)
        for k in range(9):
            yy = -100 + k * 150
            line(cv, [(-300, yy + 30 * math.sin(k)), (500, yy - 20), (1400, yy + 26 * math.cos(k)), (2300, yy)], 3, mix(CV_ROCK, INK, 0.35), seed=seed + 22 + k, boil=0.8, n=6, a=160)
        glow_stroke(cv, ap, P_["gold"], 90, 30, int(230 * light))
        glow_stroke(cv, ap, P_["yellow"], 26, 6, int(220 * light))
        cv.restore()
        brush(cv, cr_closed(jit(arch, 1.5, seed + 20), 6), 7, closed=True, seed=seed + 23)
        for k in range(5):                                          # stalactite teeth on the arch
            u = 0.25 + 0.125 * k
            px = lerp(640, 1280, u)
            py = 150 + 60 * abs(u - 0.5) * 2
            blob(cv, [(px - 34, py - 30), (px + 34, py - 30), (px + 6, py + 70 + 30 * float(hsh(seed + 30 + k))), (px - 4, py + 76)], CV_ROCK2, w=4.5,
                 seed=seed + 31 + k, boil=0.8, n=3, shade=lambda c, px=px, py=py: glow_stroke(c, open_path_pts([(px + 30, py - 30), (px + 4, py + 90)]), P_["gold"], 10, 3, 200))


def _seam_screen(C):
    return np.array([C.to_screen(x, y, 0.3) for x, y in SEAM])


def _backdrop(cv, T, cam, opn=0.0, crack=0.0, light=0.0, seed=7):
    """The cosmic sky backdrop as two stone slabs: a glowing crack runs down the seam, then they grind apart."""
    C = sets.Cam(cv, cam)
    sm = _seam_screen(C)
    zf = C.zoom(0.3)
    dpx = opn * 780 * zf
    if opn > 0.0005:
        _beyond(cv, T, cam, light)
    for side in (-1, 1):
        far = -900 if side < 0 else W + 900
        poly = np.vstack([[(far, sm[0][1])], sm, [(far, sm[-1][1])]])
        cv.save()
        cv.translate(side * dpx, 0)
        cv.clipPath(poly_path(poly), doAntiAlias=True)
        sets.cosmos(cv, T, cam, "dusk", seed)
        if opn > 0.0005:                                            # the raw stone edge of the slab, rim-lit by the sunrise
            bw = 80 * zf
            band = np.vstack([sm, (sm + np.array([side * bw, 0.0]))[::-1]])
            cv.drawPath(poly_path(band), paint(CV_ROCK2))
            stipple(cv, mix(CV_ROCK2, INK, 0.4), (sm[:, 0].min() - bw - 20, -200, sm[:, 0].max() + bw + 20, H + 200), spacing=13, r=2.0, seed=seed + 40 + side)
            for k in range(0, len(sm) - 1, 2):
                p0 = sm[k] + np.array([side * bw * 0.15, 0])
                line(cv, [p0, p0 + np.array([side * bw * 0.8, 24])], 3, mix(CV_ROCK2, INK, 0.45), seed=seed + 50 + k + side, boil=0.6, n=2, a=180)
            glow_stroke(cv, open_path_pts(sm), P_["gold"], 46 * zf, 14, int(230 * light))
            brush(cv, sm + np.array([side * bw, 0.0]), 4, seed=seed + 60 + side, taper=(0.01, 0.01), a=200)
        brush(cv, sm, 7, seed=seed + 62 + side, taper=(0.01, 0.01))
        cv.restore()
    if 0.0 < opn < 0.999:                                           # grinding stone: dust puffs where the slabs drag
        for side in (-1, 1):
            for k in range(7):
                ph = (opn * 3.0 + k / 7.0) % 1.0
                i = int(len(sm) * (0.25 + 0.55 * float(hsh(seed + 200 + k + side * 9))))
                bx, by = sm[i] + np.array([side * dpx, 0.0])
                r = (20 + 70 * ph) * zf
                blob(cv, ell(bx + side * (10 + 60 * ph) * zf, by - 30 * ph * zf, r, r * 0.8, n=9), mix(P_["lilac"], P_["cream"], 0.5), w=3,
                     seed=seed + 220 + k + side * 13, boil=1.0, a=int(200 * (1 - ph) * min(1.0, opn * 8)))
    if crack > 0 and opn < 0.06:                                    # the crack of light, spreading from the middle
        mid = len(sm) // 2
        reach = int(math.ceil(crack * mid)) + 1
        part = sm[max(0, mid - reach):min(len(sm), mid + reach)]
        if len(part) > 1:
            pth = open_path_pts(part)
            glow_stroke(cv, pth, P_["gold"], 70 * crack + 20, 24, int(200 * crack), blend=SCREEN_B)
            glow_stroke(cv, pth, P_["yellow"], 18 + 10 * crack, 4, 255)
            glow_stroke(cv, pth, P_["white"], 6 + 4 * crack, 0, 255)
            for k in range(len(part) - 1):                          # branch cracks + leaking rays
                p = part[k]
                side = 1 if k % 2 else -1
                q = p + np.array([side * (40 + 50 * float(hsh(seed + 70 + k))), 30 + 40 * float(hsh(seed + 80 + k))])
                glow_stroke(cv, open_path_pts([p, (p + q) / 2 + np.array([0, -12]), q]), P_["yellow"], 6, 2, int(230 * crack))
            for k in range(10):
                p = part[int(k * (len(part) - 1) / 9)]
                side = 1 if k % 2 else -1
                ang = math.radians(side * (10 + 25 * float(hsh(seed + 90 + k))))
                L = 400 + 300 * crack
                q0 = p
                q1 = p + np.array([side * L * math.cos(ang), L * math.sin(ang) * 0.4 - 30])
                q2 = p + np.array([side * L * math.cos(ang), L * math.sin(ang) * 0.4 + 30])
                pp = skia.Paint(AntiAlias=True)
                pp.setShader(skia.GradientShader.MakeRadial(skia.Point(*p), L, [core.C(P_["yellow"], int(130 * crack)), core.C(P_["yellow"], 0)], None))
                pp.setBlendMode(SCREEN_B)
                cv.drawPath(poly_path([q0, q1, q2]), pp)


def _flood(cv, T, cam, light, seed=7400):
    """Gold daylight pouring out of the opening over the whole studio: a screen-blend glow, god rays, dust motes."""
    if light <= 0.01:
        return
    C = sets.Cam(cv, cam)
    sx, sy = C.to_screen(*SUN_W, 0.22)
    radial(cv, sx, sy, 1900, [(P_["gold"], int(128 * light)), (P_["orange"], int(60 * light)), (P_["orange"], 0)], stops=[0.0, 0.45, 1.0],
           blend=SCREEN_B, rect=(-50, -50, W + 50, H + 50))
    n = 15
    for k in range(n):
        u = (k + 0.5) / n
        aa = math.radians(90 + 150 * (u - 0.5) + 3 * math.sin(T * 0.4 + k * 1.3))
        wd = math.radians(1.6 + 1.6 * math.sin(T * 0.7 + k * 2.1))
        r = 2600
        p = [(sx, sy), (sx + r * math.cos(aa - wd), sy + r * math.sin(aa - wd)), (sx + r * math.cos(aa + wd), sy + r * math.sin(aa + wd))]
        pp = skia.Paint(AntiAlias=True)
        pp.setShader(skia.GradientShader.MakeRadial(skia.Point(sx, sy), r, [core.C(P_["yellow"], int(82 * light)), core.C(P_["yellow"], 0)], None))
        pp.setBlendMode(SCREEN_B)
        cv.drawPath(poly_path(p), pp)
    for k in range(46):                                              # dust motes turning in the light
        ph = (T * (0.04 + 0.03 * float(hsh(seed + k))) + float(hsh(seed + 10 + k))) % 1.0
        x = float(hsh(seed + 20 + k)) * W + 40 * math.sin(T * 0.6 + k)
        y = H - ph * (H + 100) + 30 * math.sin(T * 0.9 + k * 1.7)
        tw = 0.5 + 0.5 * math.sin(T * 3 + k * 2.3)
        dots(cv, [(x, y)], 1.6 + 3.2 * float(hsh(seed + 30 + k)), P_["white"], a=int(230 * light * tw))


def _audience_watch(cv, T, light, gaze=(960, 300), seed=7500, cam=None):
    """The studio audience in front of the stage, staring up at the light (eyes catching the gold)."""
    cols = [P_["night"], (40, 20, 70), (54, 26, 90)]
    for row in range(2):
        y = 1080 + 40 - row * 70
        for k in range(14):
            x = -40 + k * 150 + (75 if row else 0)
            r = 64 - row * 6
            bob = 4 * math.sin(T * 2 + k * 1.3 + row)
            blob(cv, ell(x, y + bob, r, r * 1.05, n=10), cols[(k + row) % 3], w=5, seed=seed + k * 7 + row * 100, boil=1.0,
                 shade=lambda c, x=x, y=y, r=r: radial(c, x, y - r, r * 1.3, [(P_["gold"], int(150 * light)), (P_["gold"], 0)]))
            dx, dy = gaze[0] - x, gaze[1] - y
            dd = math.hypot(dx, dy) + 1e-6
            ex, ey = x + 14 * dx / dd, y + bob - 10 + 10 * dy / dd
            dots(cv, [(ex, ey)], 18, mix((200, 255, 230) if (k + row) % 2 else (255, 200, 240), P_["yellow"], 0.4 * light))
            dots(cv, [(ex + 3 * dx / dd, ey + 3 * dy / dd)], 8, INK)
            dots(cv, [(ex - 4, ey - 5)], 3.5, P_["white"])


def _studio_open(cv, T, A, cam, t, phi=0.0, opn=0.0, crack=0.0, light=0.0, rumble=0.0, host=None, guest=None, cord_sw=0.0, seed=7):
    """sets.talkshow, rebuilt so the backdrop can split open and the host's head can swivel."""
    h = Hh(A, t, **(host or {}))
    g = G(A, t, **(guest or {}))
    _backdrop(cv, T, cam, opn, crack, light, seed)
    C = sets.Cam(cv, cam)
    with C.layer(0.85):
        w.island(cv, 960, 905, 820, 120, seed=seed + 200, top=P_["violet"], depth=240, strata=[P_["orange"], P_["red"], P_["maroon"], P_["night"]])
        w.rug(cv, 960, 905, 640, 92, seed=seed + 210)
        sw = rumble * 5 * math.sin(T * 13) + rumble * 3 * math.sin(T * 21)
        cv.save()
        cv.rotate(sw, 960, -60)
        for k in range(7):
            blob(cv, ell(960, 140, 300 + k * 6, 92 + k * 6, n=12), P_["hotpink"], w=0, seed=seed + 300 + k, boil=2, misreg=(0, 0), a=max(0, 70 - k * 9))
        paint_text(cv, "BOXED", 960, 186, font="shrik", size=150, fill=P_["yellow"], ink_w=7, shadow=(9, 9), shadow_rgb=P_["magenta"], seed=seed + 310, wobble=2.0, drips=1)
        cv.restore()
    with C.layer(1.0):
        w.couch(cv, 1350, 905, 0.82, seed=seed + 400, rgb=P_["orange"], rgb2=P_["red"], part="back")
        w.lamp(cv, 1760, 905, 1.0, seed=seed + 410)
        w.plant(cv, 190, 905, 0.95, seed=seed + 420, phase=T * 0.3)
        _host_turn(cv, h, phi, light, cord_sw)
        sets.desk(cv, 640, 912, 1.0, seed=seed + 430)
        sets.mug(cv, 858, 744, 1.0, T, seed=seed + 440)
        draw_zee(cv, g)
        w.couch(cv, 1350, 905, 0.82, seed=seed + 400, rgb=P_["orange"], rgb2=P_["red"], part="front")
        sets.side_table(cv, 1690, 912, 1.0, seed=seed + 450)
        sets.lava(cv, 1690, 812, 1.0, T, seed=seed + 460)
    return h, g


def _debris(cv, t, t0, amt, seed=7600):
    """Pebbles and dust shaken loose from above during the rumble."""
    if t < t0 or amt <= 0:
        return
    for k in range(16):
        st = t0 + float(hsh(seed + k)) * 2.2
        if t < st:
            continue
        u = t - st
        x = 120 + float(hsh(seed + 10 + k)) * 1680
        y = -30 + 0.5 * 2400 * u * u
        if y > H + 40:
            continue
        r = 5 + 9 * float(hsh(seed + 20 + k))
        blob(cv, ell(x, y, r, r * 0.8, n=7, rot=u * 400), mix(CV_ROCK2, P_["lilac"], 0.3), w=3, seed=seed + 30 + k, boil=0.6)
        dots(cv, [(x + 6 * math.sin(k), y - 30)], 3, P_["cream"], a=int(150 * amt))


def T051_turn(cv, t, T, A):
    # beats (shot time): breath 0.2-1.3 | head 0->180 1.3-4.0 | rumble 3.0+ | crack 3.6 | doors 4.15-5.6
    # 'Whoa.' 5.44 | head back to Zee 6.05-6.55 | 'Has that always been there?' 6.65-8.03 | cut to Zee 8.1 | 'Always.' 8.43
    crack = seg(t, 3.55, 4.15)
    opn = ease_io(seg(t, 4.15, 5.7)) ** 1.1
    light = 0.25 * crack + 0.75 * ease(seg(t, 4.15, 5.3))
    rumble = seg(t, 2.9, 3.6) * (1 - seg(t, 5.6, 6.6))
    if t < 4.0:
        phi = 180 * ease_io(seg(t, 1.3, 4.0)) + 3 * math.sin(t * 9) * seg(t, 1.3, 1.6) * (1 - seg(t, 3.7, 4.0))
    elif t < 6.05:
        phi = 180.0
    else:
        phi = lerp(180, 46, ease_io(seg(t, 6.05, 6.6))) + 2 * math.sin(t * 2.0)
    br = math.sin(math.pi * seg(t, 0.15, 1.35))
    host = dict(head_dy=-16 * br, breath=0.25 * br, lean=-2.0 * br - 3.0 * seg(t, 5.4, 6.0) * (1 - seg(t, 6.0, 6.6)))
    if 0.35 < t < 1.15:
        host.update(blinkL=1.0, blinkR=1.0)
    elif t < 4.0:
        host.update(pupil=1.0 + 0.25 * seg(t, 1.2, 1.6), brow_ang=0.4, smile=0.1)
    if t > 6.3:
        host.update(px=0.6, py=-0.1, pupil=1.3)
    cord_sw = 22 * math.sin(t * 3.1) * seg(t, 3.0, 4.2)
    if t >= 8.1:                                                      # Zee, smiling: 'Always.'
        u = t - 8.1
        cam = dict(x=CAM_ZEE["x"] + 8 * u, y=CAM_ZEE["y"] - 10, z=1.95 + 0.025 * u)
        _studio_open(cv, T, A, cam, t, phi=46, opn=1.0, crack=1.0, light=1.0, host=dict(host), guest=dict(px=-0.35, py=-0.1), cord_sw=0.0)
        _flood(cv, T, cam, 0.9)
        return
    pull = ease_io(seg(t, 2.8, 4.4))
    push = ease_io(seg(t, 5.6, 8.1))
    z = lerp(1.85 + 0.1 * seg(t, 0.0, 2.8), 1.03, pull) + 0.27 * push
    x = lerp(-330, 0, pull) + lerp(0, -40, push)
    y = lerp(-40, 30, pull) + 26 * push
    jx, jy = shake(13 * rumble, 77)
    cam = dict(x=x + jx, y=y + jy, z=z)
    gaze_up = seg(t, 4.2, 5.0)
    guest = dict(px=lerp(-0.75, -0.15, gaze_up), py=lerp(0.0, -0.55, gaze_up), smile=0.4 + 0.35 * gaze_up)
    _studio_open(cv, T, A, cam, t, phi=phi, opn=opn, crack=crack, light=light, rumble=rumble, host=host, guest=guest, cord_sw=cord_sw)
    _debris(cv, t, 3.0, rumble)
    if z < 1.5:
        _audience_watch(cv, T, light)
    _flood(cv, T, cam, light)


# ===================================================================== T052: outside (the finale)
BPM52 = 108.0
BEAT52 = 596.293                   # first downbeat of ep4_M_OUTSIDE (108 BPM; music4 places the cue at OUTSIDE t0 - 0.05, beat 1 is 0.011 s in)
SHOE_H = (30, 22, 44)


def beat52(T):
    """Finale beat clock: (beat index, phase 0..1)."""
    b = (T - BEAT52) * BPM52 / 60.0
    return int(math.floor(b)), b - math.floor(b)


_BOUNCE = [1.0]                    # global bounce gain (ramps in with the music)


def hop_of(ph):
    """0 on the beat (feet down), 1 mid-beat (up in the air)."""
    return _BOUNCE[0] * math.sin(math.pi * ph) ** 0.85


def contact_of(ph):
    """1 right on the beat (squash), fading over the first ~15% of the beat."""
    return max(0.0, 1.0 - ph / 0.16) if ph < 0.5 else max(0.0, (ph - 0.93) / 0.07)


def _step_legs(cv, hips, feet_x, lift, l1, l2, width, rgb, seed, flare=0.0, shoe_rgb=SHOE_H, sole=None, shoe_len=1.0):
    """Two rubber-hose legs from hips to feet that step: lift = (left_lift, right_lift) in local px."""
    for k, side in enumerate((-1, 1)):
        hx, hy = hips[k]
        fx, fy = feet_x[k], -lift[k]
        (wx, wy), fdir = limb(cv, (hx, hy), (fx, fy - 22), l1, l2, -side, width, rgb, seed + k * 5)
        if flare > 0:                                                  # bell-bottom flare
            blob(cv, [(wx - width * 0.45, wy - 50), (wx + width * 0.45, wy - 50), (wx + width * 0.5 + flare, wy + 6), (wx - width * 0.5 - flare, wy + 6)], rgb, w=4.5,
                 seed=seed + 20 + k, boil=0.8, n=4)
        L = 1.0 * shoe_len
        shoe = [(wx - side * 26 * L, wy - 6), (wx + side * 30 * L, wy - 8), (wx + side * 54 * L, wy + 10), (wx + side * 48 * L, wy + 24), (wx - side * 32 * L, wy + 24)]
        blob(cv, shoe, shoe_rgb, w=4.5, seed=seed + 30 + k, boil=0.8, n=5,
             shade=(lambda c, wx=wx, wy=wy: c.drawRect(R(wx - 80, wy + 14, wx + 80, wy + 30), paint(sole))) if sole else None)


def _host_dance(cv, A, x, y, s, T, move="roof", heart=False, seed=3000, travel=0.0, extra=None):
    """The host dancing on the finale beat: stepping legs, bouncing, arm moves; heart eyes optional."""
    b, ph = beat52(T)
    hop, con = hop_of(ph), contact_of(ph)
    P = dict(A["HOST"])
    up = -26 * s * hop
    sx_, sy_ = 1 + 0.035 * con, 1 - 0.045 * con
    act = b % 2
    lift = (34 * hop if act == 0 else 0.0, 34 * hop if act == 1 else 0.0)
    sw = math.sin(math.pi * (b + ph))                                   # sways left/right one beat each way
    P.update(x=0.0, y=0.0, s=1.0, legs=False, lean=6 * sw, head_tilt=-7 * sw, smile=0.95, vis="E", mo=0.55 + 0.25 * hop, pupil=1.15,
             browL=0.4, browR=0.4, blinkL=0.0, blinkR=0.0, face="heart" if heart else "normal", glitch=0.0, px=0.0, py=-0.1)
    arms = _host_moves(move, b, ph, hop)
    P.update(arms)
    if extra:
        P.update(extra)
    cv.save()
    cv.translate(x, y + up)
    cv.scale(s * sx_, s * sy_)
    old = core.INKMUL
    core.INKMUL = old / max(s, 0.15) ** 0.5
    _step_legs(cv, ((-34 + travel * 0, -176), (34, -176)), (-44 + 8 * sw, 44 + 8 * sw), lift, 96, 96, 46, _cast.TROU, seed + 600)
    core.INKMUL = old
    cv.restore()
    cv.save()
    cv.translate(x, y + up)
    cv.scale(sx_, sy_)
    cv.translate(-x, -(y + up))
    P.update(x=x, y=y + up, s=s)
    draw_host(cv, P)
    cv.restore()


def _arms_from(targets, SH, LL, hand_abs):
    out = {}
    for side, key in ((-1, "L"), (1, "R")):
        wx, wy, pose = targets[key]
        sh, el, _ = ik(SH[side], (wx, wy), *LL, side)
        out["a" + key + "_sh"] = sh
        out["a" + key + "_el"] = el
        out["a" + key + "_pose"] = pose
        out["a" + key + "_hand"] = hand_abs[key] - (sh + el)
    return out


def _host_moves(move, b, ph, hop):
    from .acting import SH_HOST, L_HOST
    if move == "roof":                                                  # raise the roof, pumping on the beat
        k = 40 * hop
        t = dict(L=(-250, -520 - k, "flat"), R=(250, -520 - k, "flat"))
        ha = dict(L=250, R=290)
    elif move == "wave":
        k = 40 * math.sin(math.pi * (b + ph))
        t = dict(L=(-96, -252, "flat"), R=(250 + k, -560, "open"))
        ha = dict(L=150, R=280 + k * 0.4)
    elif move == "point":                                               # disco point, up-right / down-left
        if b % 2 == 0:
            t = dict(L=(-90, -300, "fist"), R=(260, -600, "point"))
            ha = dict(L=150, R=300)
        else:
            t = dict(L=(-200, -230, "point"), R=(96, -330, "fist"))
            ha = dict(L=150, R=200)
    elif move == "clap":
        t = dict(L=(-18 - 130 * hop, -330, "flat"), R=(18 + 130 * hop, -330, "flat"))
        ha = dict(L=330, R=210)
    else:                                                               # 'tada'
        t = dict(L=(-280, -560, "spread"), R=(280, -560, "spread"))
        ha = dict(L=235, R=305)
    return _arms_from(t, SH_HOST, L_HOST, ha)


def _zee_moves(move, b, ph, hop):
    from .acting import SH_GUEST, L_GUEST
    if move == "big":
        k = 30 * hop
        t = dict(L=(-250, -450 - k, "spread"), R=(250, -450 - k, "spread"))
        ha = dict(L=235, R=305)
    elif move == "wave":
        k = 36 * math.sin(math.pi * (b + ph))
        t = dict(L=(-250 + k, -470, "open"), R=(250 + k, -470, "open"))
        ha = dict(L=250 + k * 0.4, R=290 + k * 0.4)
    elif move == "clap":
        t = dict(L=(-16 - 120 * hop, -300, "flat"), R=(16 + 120 * hop, -300, "flat"))
        ha = dict(L=330, R=210)
    elif move == "point":
        if b % 2 == 0:
            t = dict(L=(-250, -500, "point"), R=(80, -260, "fist"))
            ha = dict(L=240, R=30)
        else:
            t = dict(L=(-80, -260, "fist"), R=(250, -500, "point"))
            ha = dict(L=150, R=300)
    else:
        t = dict(L=(-260, -470, "spread"), R=(260, -470, "spread"))
        ha = dict(L=235, R=305)
    return _arms_from(t, SH_GUEST, L_GUEST, ha)


def _zee_dance(cv, A, x, y, s, T, move="big", seed=300, extra=None):
    b, ph = beat52(T)
    hop, con = hop_of(ph), contact_of(ph)
    P = dict(A["GUEST"])
    up = -28 * s * hop
    sx_, sy_ = 1 + 0.04 * con, 1 - 0.05 * con
    act = (b + 1) % 2
    lift = (36 * hop if act == 0 else 0.0, 36 * hop if act == 1 else 0.0)
    sw = math.sin(math.pi * (b + ph))
    P.update(x=0.0, y=0.0, s=1.0, legs=False, lean=-6 * sw, head_tilt=8 * sw, smile=0.9, vis="E", mo=0.5 + 0.3 * hop, lid=0.4, blinkL=0.0, blinkR=0.0,
             browL=0.35, browR=0.35, px=0.0, py=-0.15, blush=1.5, head_turn=0.0, sweat=0.0, antL=(-14 * sw, 10 * hop), antR=(-14 * sw, -10 * hop))
    P.update(_zee_moves(move, b, ph, hop))
    if extra:
        P.update(extra)
    cv.save()
    cv.translate(x, y + up)
    cv.scale(s * sx_, s * sy_)
    old = core.INKMUL
    core.INKMUL = old / max(s, 0.15) ** 0.5
    _step_legs(cv, ((-30, -196), (30, -196)), (-46 - 8 * sw, 46 - 8 * sw), lift, 100, 100, 50, _zee.PANTS, seed + 700, flare=26, shoe_rgb=_zee.SHOE,
               sole=P_["white"])
    core.INKMUL = old
    cv.restore()
    cv.save()
    cv.translate(x, y + up)
    cv.scale(sx_, sy_)
    cv.translate(-x, -(y + up))
    P.update(x=x, y=y + up, s=s)
    draw_zee(cv, P)
    cv.restore()


def _sunglasses(cv, cx, cy, s, seed, tip=0.0):
    """Gary's tiny sunglasses: two little dark lenses perched on his giant iris (tip slides them down the eye)."""
    cy = cy + tip
    for side in (-1, 1):
        lx = cx + side * 33 * s
        lens = ell(lx, cy, 29 * s, 22 * s, n=10)
        P = blob(cv, lens, (36, 16, 60), w=4.5, seed=seed + side, boil=0.6,
                 shade=lambda c, lx=lx: (radial(c, lx - 8 * s, cy - 10 * s, 30 * s, [(P_["magenta"], 200), (P_["violet"], 0)]),
                                          c.drawPath(poly_path([(lx - 14 * s, cy - 16 * s), (lx - 4 * s, cy - 18 * s), (lx - 18 * s, cy + 2 * s)]), paint(P_["white"], 210))))
    line(cv, [(cx - 6 * s, cy - 6 * s), (cx, cy - 10 * s), (cx + 6 * s, cy - 6 * s)], 5, seed=seed + 3, boil=0.4, n=3)
    for side in (-1, 1):
        line(cv, [(cx + side * 60 * s, cy - 6 * s), (cx + side * 108 * s, cy - 12 * s - tip * 0.3), (cx + side * 146 * s, cy + 2 * s - tip * 0.5)], 4, seed=seed + 5 + side, boil=0.5, n=4)


def _gary_dance(cv, x, y, s, T, seed=4400, tip=0.0, squint=0.0, loud=0.0, wave_arm=True):
    """Gary in the parade: legs + sneakers under the sweater, bouncing, both hands up, tiny sunglasses.
    tip lowers the shades down his eye; squint (0..1) = peeking at the sun: pupil shrinks to a pinprick, lid squints."""
    b, ph = beat52(T)
    hop, con = hop_of(ph), contact_of(ph)
    yy = y - 30 * s * hop
    act = b % 2
    for k, side in enumerate((-1, 1)):                                   # legs
        lift = 40 * s * hop if act == k else 0.0
        hx, hy = x + side * 50 * s, yy + 340 * s
        fx, fy = x + side * 62 * s, y + 470 * s - lift
        tube(cv, [(hx, hy), (hx + side * 14 * s, (hy + fy) / 2), (fx, fy)], 34 * s, P_["cream"], w=4.5, seed=seed + 100 + k, boil=0.7, n=5)
        blob(cv, [(fx - side * 26 * s, fy - 8 * s), (fx + side * 34 * s, fy - 10 * s), (fx + side * 60 * s, fy + 8 * s), (fx + side * 52 * s, fy + 22 * s), (fx - side * 30 * s, fy + 22 * s)],
             P_["red"], w=4.5, seed=seed + 110 + k, boil=0.7, n=5, shade=lambda c, fx=fx, fy=fy: c.drawRect(R(fx - 80 * s, fy + 12 * s, fx + 80 * s, fy + 30 * s), paint(P_["white"])))
    eyeball_creature(cv, x, yy, s, T, loud, seed=seed, mic=False, wave=1.0)
    bob = 6 * math.sin(T * 3.1) * s
    if wave_arm:                                                         # the other hand up too
        hx = x + 205 * s + 16 * s * math.sin(T * 8)
        hy = yy - 40 * s - 30 * s * hop
        tube(cv, [(x + 104 * s, yy + 190 * s), (x + 200 * s, yy + 140 * s), (hx, hy)], 22 * s, P_["cream"], w=4.5, seed=seed + 120, boil=0.8, n=8)
        cv.save(); cv.translate(hx, hy); cv.scale(s * 1.15, s * 1.15)
        _hand(cv, 0, 0, -90 - 14 * math.sin(T * 8), "open", -1, seed + 122, rgb=P_["white"])
        cv.restore()
    ex, ey = x - 4 * s, yy + bob - 22 * s
    if squint > 0.02:                                                    # peeking straight at the sun: OW
        ir = 66 * s
        blob(cv, ell(ex, ey, ir, ir, n=11), P_["teal"], w=4.5, seed=seed + 5, boil=0.8,
             shade=lambda c: c.drawPath(poly_path(cr_closed(ell(ex + 10 * s, ey + 12 * s, ir * 0.8, ir * 0.75, n=8), 4)), paint(P_["tealdk"])))
        pr = ir * (0.42 - 0.32 * squint)
        dots(cv, [(ex, ey)], pr, INK)
        dots(cv, [(ex - pr * 0.4, ey - pr * 0.5)], max(1.5, pr * 0.3), P_["white"])
        r = 150 * s
        cy = yy + bob
        top = cy - r * 1.04
        ly = top + 1.1 * r * squint
        cv.save()
        cv.clipPath(poly_path(cr_closed(ell(x, cy, r + 3, r + 3, n=16), 4)), doAntiAlias=True)
        blob(cv, [(x - r - 30, top - 40), (x + r + 30, top - 40), (x + r + 30, ly + 10 * s), (x, ly - 22 * s), (x - r - 30, ly + 10 * s)], P_["violet"], w=0, seed=seed + 130,
             boil=0.5, n=4, misreg=(0, 0))
        cv.restore()
        line(cv, [(x - r * 0.97, ly + 8 * s), (x - r * 0.4, ly - 16 * s), (x + r * 0.4, ly - 16 * s), (x + r * 0.97, ly + 8 * s)], 6, seed=seed + 131, boil=0.6, n=6)
        for k in range(3):                                               # squint lines + a tear
            line(cv, [(x + r * 1.02, cy - r * 0.3 + k * 26 * s), (x + r * 1.25, cy - r * 0.42 + k * 34 * s)], 5, seed=seed + 133 + k, boil=0.5, n=2, a=int(255 * squint))
            line(cv, [(x - r * 1.02, cy - r * 0.3 + k * 26 * s), (x - r * 1.25, cy - r * 0.42 + k * 34 * s)], 5, seed=seed + 136 + k, boil=0.5, n=2, a=int(255 * squint))
        tph = (T * 1.8) % 1.0
        blob(cv, [(x + r * 0.7, cy + r * 0.2 + 70 * s * tph - 18 * s), (x + r * 0.7 + 11 * s, cy + r * 0.2 + 70 * s * tph + 6 * s), (x + r * 0.7, cy + r * 0.2 + 70 * s * tph + 16 * s),
              (x + r * 0.7 - 11 * s, cy + r * 0.2 + 70 * s * tph + 6 * s)], P_["mint"], w=3.5, seed=seed + 140, boil=0.5, n=4, a=int(255 * squint))
    _sunglasses(cv, ex, ey, s, seed + 140, tip=tip)


MARCH_COLS = [(118, 62, 210), (150, 64, 178), (92, 44, 170), (170, 72, 150), (104, 70, 220), (136, 40, 140)]
IRIS_COLS = [P_["mint"], P_["hotpink"], P_["yellow"], (150, 200, 255), P_["acid"], P_["orange"]]


def _marcher(cv, x, y, s, T, seed=0, look=(0.3, -0.4), arms="up", light=(1.0, -1.0), phase_off=0):
    """An unchained eyeball audience member, dancing (x, y = feet): a squat dome body with one huge happy eye, a big
    grin, little stepping legs, arms up, an iron collar with a broken chain swinging, and a broken ankle shackle."""
    b, ph = beat52(T)
    b += phase_off
    hop, con = hop_of(ph), contact_of(ph)
    col = MARCH_COLS[int(hsh(seed) * len(MARCH_COLS)) % len(MARCH_COLS)]
    iris = IRIS_COLS[int(hsh(seed + 1) * len(IRIS_COLS)) % len(IRIS_COLS)]
    shoe = [P_["red"], P_["teal"], P_["yellow"], P_["acid"]][int(hsh(seed + 2) * 4) % 4]
    with at(cv, x, y, s):
        up = -26 * hop
        act = b % 2
        for k, side in enumerate((-1, 1)):
            lift = 26 * hop if act == k else 0.0
            fx = side * 30 + 6 * math.sin(math.pi * (b + ph)) * side
            tube(cv, [(side * 26, -44 + up), (side * 32, -22 + up * 0.5 - lift * 0.5), (fx, -6 - lift)], 20, mix(col, INK, 0.25), w=4, seed=seed + 10 + k, boil=0.7, n=4)
            blob(cv, ell(fx + side * 8, -2 - lift, 22, 11, n=8), shoe, w=4, seed=seed + 12 + k, boil=0.6)
            if k == 0:                                                   # broken ankle shackle + chain stub
                blob(cv, ell(fx, -14 - lift, 16, 7, n=8), (150, 150, 180), w=3, seed=seed + 14, boil=0.4)
                chain(cv, (fx - 10, -10 - lift), (fx - 46, 0), seed=seed + 15, link=12, sag=4, w=2.2)
        cv.save()
        cv.translate(0, up)
        cv.scale(1 + 0.05 * con, 1 - 0.06 * con)
        r = 70
        body = [(-r, -36), (-r * 1.08, -110), (-r * 0.74, -176), (0, -198), (r * 0.74, -176), (r * 1.08, -110), (r, -36), (0, -28)]
        lx, ly = light

        def sh(c):
            c.drawPath(poly_path(cr_closed(ell(-lx * 40, 10, 90, 140, n=10), 3)), paint(mix(col, INK, 0.3)))
            c.drawPath(poly_path(cr_closed(ell(lx * 70, -150, 40, 70, n=10, rot=lx * 20), 3)), paint(mix(col, P_["gold"], 0.55), 200))
        blob(cv, body, col, w=5, seed=seed + 20, boil=1.0, n=5, shade=sh)
        for k, side in enumerate((-1, 1)):                                # arms
            if arms == "up":
                hx, hy = side * (r + 46 + 10 * math.sin(T * 6 + k)), -196 - 22 * hop
            elif arms == "wave":
                hx, hy = side * (r + 40), -150 - 40 * (hop if k == act else 0.2)
            else:
                hx, hy = side * (r + 30), -60
            tube(cv, [(side * r * 0.92, -110), (side * (r + 30), -140), (hx, hy)], 16, col, w=4, seed=seed + 30 + k, boil=0.8, n=5)
            blob(cv, ell(hx, hy, 15, 15, n=8), P_["white"], w=3.5, seed=seed + 32 + k, boil=0.6)
        ey = -124
        blob(cv, ell(0, ey, 46, 46, n=12), P_["white"], w=4.5, seed=seed + 40, boil=0.8)
        ix, iy = look[0] * 14, ey + look[1] * 14
        dots(cv, [(ix, iy)], 24, iris)
        dots(cv, [(ix, iy)], 11, INK)
        dots(cv, [(ix - 7, iy - 8)], 5, P_["white"])
        blob(cv, [(-52, ey + 18), (-24, ey + 34), (24, ey + 34), (52, ey + 18), (52, ey + 60), (-52, ey + 60)], col, w=0, seed=seed + 41, boil=0.5, n=3, misreg=(0, 0))
        line(cv, [(-40, ey + 22), (0, ey + 36), (40, ey + 22)], 4, seed=seed + 42, boil=0.5, n=3)      # happy lower lid
        mo = 0.6 + 0.4 * hop
        blob(cv, [(-26, -76), (26, -76), (20, -76 + 22 * mo), (0, -72 + 30 * mo), (-20, -76 + 22 * mo)], P_["mouth"], w=4, seed=seed + 43, boil=0.6, n=4,
             shade=lambda c: c.drawPath(poly_path(ell(2, -70 + 24 * mo, 12, 8, n=8)), paint(P_["tongue"])))
        blob(cv, ell(0, -46, r * 0.92, 13, n=12), (150, 150, 180), w=3.5, seed=seed + 50, boil=0.5,
             shade=lambda c: c.drawRect(R(-r, -46, r, -30), paint((100, 100, 130))))
        sw = 26 * math.sin(math.pi * (b + ph)) * (1 if seed % 2 else -1)       # the broken chain swinging off the collar
        p0 = (18, -38)
        p1 = (18 + sw * 0.6, 10 + 10 * hop)
        chain(cv, p0, p1, seed=seed + 51, link=13, sag=6, w=2.4)
        brush(cv, cr_open([(p1[0] - 7, p1[1] + 2), (p1[0] - 2, p1[1] + 12), (p1[0] + 7, p1[1] + 10)], 4), 3.0, (150, 150, 180), seed=seed + 52)
        cv.restore()


def _sun_planet(cv, x, y, r, T, grin=1.0, look=(0.0, 0.35), seed=9600, glow=1.0, wink=0.0):
    """The show's ringed planet as the rising sun: glowing gold, ring behind, big happy eyes and an open grin."""
    radial(cv, x, y, r * 3.4, [(P_["white"], int(230 * glow)), (P_["yellow"], int(170 * glow)), (P_["orange"], int(60 * glow)), (P_["orange"], 0)],
           stops=[0.0, 0.3, 0.6, 1.0])
    ring = dict(rx=1.85, ry=0.34, rgb=P_["teal"], rgb2=P_["cream"], tilt=-12)
    w._ring(cv, x, y, r, ring, seed + 300, "back")
    w._ring(cv, x, y, r, ring, seed + 300, "front")
    lids = 0.1 + 0.88 * wink
    w.planet(cv, x, y, r, P_["gold"], bands=[(-0.62, 0.2, P_["yellow"]), (-0.16, 0.16, P_["orange"]), (0.38, 0.22, P_["yellow"])],
             face=dict(look=look, smile=1.0, lids=lids, lid_rgb=P_["orange"]), seed=seed, crater=False, shade_rgb=mix(P_["gold"], P_["red"], 0.3))
    g = max(0.0, grin)
    top = [(x - 0.4 * r, y + 0.13 * r), (x - 0.2 * r, y + 0.19 * r), (x, y + 0.21 * r), (x + 0.2 * r, y + 0.19 * r), (x + 0.4 * r, y + 0.13 * r)]
    bot = [(x + 0.3 * r, y + 0.13 * r + 0.2 * r * g), (x, y + 0.2 * r + 0.3 * r * g), (x - 0.3 * r, y + 0.13 * r + 0.2 * r * g)]
    P = top + bot

    def sh(c):
        c.drawRect(R(x - r, y + 0.1 * r, x + r, y + 0.27 * r), paint(P_["white"]))
        c.drawPath(poly_path(ell(x + 0.05 * r, y + 0.2 * r + 0.3 * r * g, 0.2 * r, 0.11 * r * (0.5 + g), n=12)), paint(P_["tongue"]))
    blob(cv, P, P_["mouth"], w=max(4.0, r * 0.03), seed=seed + 20, boil=1.0, n=5, shade=sh)
    for side in (-1, 1):
        line(cv, [(x + side * 0.42 * r, y + 0.08 * r), (x + side * 0.47 * r, y + 0.16 * r)], max(3.0, r * 0.022), seed=seed + 25 + side, boil=0.5, n=2)


def _band(cv, y, height, rgb, amp, freq, seed, x0=-400, x1=W + 400, ink=4.0):
    xs = np.linspace(x0, x1, int((x1 - x0) / 40) + 2)
    ys = y + amp * np.sin(xs / W * math.pi * 2 * freq + seed * 1.7) + amp * 0.35 * np.sin(xs / W * math.pi * 6 * freq + seed)
    pts = list(zip(xs, ys)) + [(x1, y + height), (x0, y + height)]
    cv.drawPath(poly_path(pts), paint(rgb))
    brush(cv, np.stack([xs, ys], 1), ink, taper=(0.01, 0.01), seed=seed + 11, a=210)


def _sky52(cv, T, C, sun, r, p=0.05, seed=9500, stars=0.0, grin=1.0, look=(0.0, 0.35), glow=1.0, wink=0.0):
    with C.layer(p):
        sx, sy = sun
        w.field(cv, P_["night"])
        radial(cv, sx, sy, 2300, [(P_["white"], 255), (P_["yellow"], 255), (P_["orange"], 255), (P_["hotpink"], 255), (P_["violet"], 255), (P_["night"], 255)],
               stops=[0.0, 0.08, 0.22, 0.42, 0.68, 1.0], rect=(-1200, -900, W + 2600, H + 900))
        for k in range(22):                                          # the slowly turning sunburst
            a1 = k / 22 * 2 * math.pi + T * 0.09
            a2 = a1 + math.pi / 22
            pp = skia.Paint(AntiAlias=True)
            pp.setShader(skia.GradientShader.MakeRadial(skia.Point(sx, sy), 2400, [core.C(P_["white"] if k % 2 else P_["yellow"], 95), core.C(P_["yellow"], 0)], None))
            pp.setBlendMode(SCREEN_B)
            cv.drawPath(poly_path([(sx, sy), (sx + 2600 * math.cos(a1), sy + 2600 * math.sin(a1)), (sx + 2600 * math.cos(a2), sy + 2600 * math.sin(a2))]), pp)
        if stars > 0:
            w.stars(cv, seed + 1, (-300, -300, 900, 420), n=110, big=6)
        _sun_planet(cv, sx, sy, r, T, grin=grin, look=look, seed=seed + 10, glow=glow, wink=wink)


def _confetti52(cv, t, seed=9700, n=60, a=1.0, bursts=()):
    """Falling confetti + twinkling sparkles (screen space). bursts = [(x, y, age, dir)] confetti cannons firing
    up and inward from (x, y)."""
    cols = [P_["magenta"], P_["yellow"], P_["teal"], P_["acid"], P_["orange"], P_["hotpink"], P_["white"]]
    for k in range(n):
        x = float(hsh(seed + k)) * (W + 100) - 50 + 50 * math.sin(t * 1.7 + k)
        y = ((float(hsh(seed + 100 + k)) * H + t * (130 + 110 * float(hsh(seed + 200 + k)))) % (H + 80)) - 40
        ang = t * (4 + 3 * float(hsh(seed + 300 + k))) + k
        dx, dy = 13 * math.cos(ang), 6 * math.sin(ang * 1.3)
        cv.drawPath(poly_path([(x - dx, y - dy), (x + dy, y - dx), (x + dx, y + dy), (x - dy, y + dx)]), paint(cols[k % len(cols)], int(255 * a)))
    for k in range(int(n / 4)):
        x = float(hsh(seed + 400 + k)) * W
        y = float(hsh(seed + 500 + k)) * H * 0.85
        tw = 0.5 + 0.5 * math.sin(t * 5 + k * 1.9)
        if tw > 0.35:
            sparkle(cv, x, y, 9 + 12 * tw, [P_["yellow"], P_["white"], P_["hotpink"], P_["acid"]][k % 4], w=2.5, seed=seed + 600 + k, a=int(255 * a))
    for j, (bx, by, age, dr) in enumerate(bursts):
        if 0 <= age < 2.2:
            for k in range(56):
                ang = math.radians(-90 + dr * (8 + 40 * float(hsh(seed + 700 + k + j * 50))))
                sp = 1500 + 900 * float(hsh(seed + 800 + k + j * 50))
                drag = (1 - math.exp(-age * 2.2)) / 2.2
                px = bx + math.cos(ang) * sp * drag + 30 * math.sin(age * 6 + k)
                py = by + math.sin(ang) * sp * drag + 240 * age * age
                al = int(255 * max(0.0, 1 - age / 2.2))
                if k % 3 == 0:
                    sparkle(cv, px, py, 20, cols[k % len(cols)], w=2.5, seed=seed + 900 + k, a=al)
                else:
                    dx, dy = 19 * math.cos(age * 9 + k), 9 * math.sin(age * 11 + k)
                    cv.drawPath(poly_path([(px - dx, py - dy), (px + dy, py - dx), (px + dx, py + dy), (px - dy, py + dx)]), paint(cols[k % len(cols)], al))


def _bloom_flower(cv, x, y, s, T, born, t, seed, kind=0):
    """A flower that pops open when something passes (born = time it started to bloom)."""
    k = pop(t, born, 0.32)
    if k <= 0.01:
        line(cv, [(x, y), (x + 2, y - 26 * s)], 7 * s + 2, P_["acid_dk"], seed=seed, boil=0.5, n=2, taper=(0, 0))
        blob(cv, ell(x + 2, y - 30 * s, 10 * s + 2, 14 * s + 2, n=8), P_["acid"], w=3, seed=seed + 1, boil=0.5)
        return
    _flower(cv, x, y, s * k, T, seed=seed, kind=kind)


def _darkened(cv, bbox, amt, fn):
    """Draw fn() darkened by amt (0..1) on its own pixels (the cave's shadow on the marchers still inside)."""
    if amt <= 0.01:
        fn()
        return
    cv.saveLayer(R(*bbox), None)
    fn()
    cv.drawRect(R(*bbox), paint((14, 6, 34), int(255 * min(1.0, amt)), blend=ATOP_B))
    cv.restore()


# --------------------------------------------------------------- the cast list (emerge order)
CAST52 = ["host", "zee", "gary"] + [f"eye{k}" for k in range(13)]


def _draw_member(cv, A, who, x, y, s, T, move=None, t=0.0, extra=None):
    """Draw one parade member with its feet at (x, y); s = parade scale (1 = full-size host)."""
    if who == "host":
        _host_dance(cv, A, x, y, s * 0.9, T, move=move or "roof", heart=(int((T - BEAT52) / 2.222) % 3 == 1), extra=extra)
    elif who == "zee":
        _zee_dance(cv, A, x, y, s * 0.9, T, move=move or "big", extra=extra)
    elif who == "gary":
        gs = s * 0.74
        ex_ = extra or {}
        _gary_dance(cv, x, y - 470 * gs, gs, T, tip=ex_.get("tip", 0.0), squint=ex_.get("squint", 0.0), loud=ex_.get("loud", 0.0))
    else:
        k = int(who[3:])
        _marcher(cv, x, y, s * 1.45, T, seed=4900 + k * 37, look=(0.4 * math.sin(k * 1.7), -0.5), arms=["up", "wave", "up"][k % 3], phase_off=k % 2)


def _member_height(who, s):
    return {"host": 900, "zee": 820, "gary": 740}.get(who, 300) * s


# --------------------------------------------------------------- scene A: out of the cave mouth
PATH_A = [(445, 846), (560, 884), (760, 940), (1000, 978), (1300, 984), (1650, 966), (2150, 950)]
_PATH_A_D = None


def _path_a(u):
    global _PATH_A_D
    if _PATH_A_D is None:
        _PATH_A_D = cr_open(np.array(PATH_A, float), 24)
    i = min(len(_PATH_A_D) - 1, max(0, int(u * (len(_PATH_A_D) - 1))))
    x, y = _PATH_A_D[i]
    s = 0.24 + 0.4 * min(1.0, u / 0.55) ** 0.9
    return float(x), float(y), s


def _scene_a(cv, t, T, A):
    cam = dict(x=40 * seg(t, 0, 6.7), y=-10 * seg(t, 0, 6.7), z=1.0 + 0.05 * seg(t, 0, 6.7))
    C = sets.Cam(cv, cam)
    sun = (1500, 330 - 40 * seg(t, 0, 6.7))
    _sky52(cv, T, C, sun, 150, p=0.08, stars=1.0, grin=0.6 + 0.4 * seg(t, 1.0, 3.0), look=(-0.6, 0.45))
    with C.layer(0.18):
        w.ribbon(cv, [(-300, 520), (300, 230), (900, 90), (1500, 60), (2300, 160)], 120, [P_["magenta"], P_["orange"], P_["yellow"], P_["acid"], P_["teal"]],
                 flow=T * 0.9, seed=9800, starband=None, ink=5)
    with C.layer(0.32):
        for k, (yy, col) in enumerate(((660, P_["teal"]), (700, P_["acid"]), (740, P_["yellow"]), (780, P_["orange"]))):
            _band(cv, yy, 600, col, 22 + k * 5, 1.3 + k * 0.4, 9810 + k)
        w.pyramid(cv, 1780, 700, 0.42, look=(-0.6, 0.0), seed=9820, rays=True)
        w.mushroom(cv, 1240, 760, 0.5, seed=9821)
    with C.layer(1.0):
        hill = [(-260, 1200), (-260, 300), (60, 170), (360, 110), (640, 190), (860, 370), (1010, 560), (1120, 720), (1180, 860), (1210, 1200)]
        mouth = [(262, 862), (270, 700), (322, 566), (440, 508), (566, 552), (628, 690), (636, 862)]

        def hs(c):
            c.drawPath(poly_path(cr_closed([(700, 150), (1300, 300), (1300, 1200), (900, 1200), (960, 600)], 4)), paint(mix(CV_ROCK2, P_["gold"], 0.35)))
            stipple(c, mix(CV_ROCK, INK, 0.4), (-260, 100, 1220, 1200), spacing=15, r=2.1, seed=9831, fn=lambda X, Y: np.clip(0.3 + 0.7 * np.sin(X * 0.012 + Y * 0.02) ** 2, 0, 1) * 0.8)
            for k in range(6):
                yy = 260 + k * 110
                line(c, [(-260, yy + 20 * math.sin(k)), (400, yy - 18), (1100, yy + 30 + 10 * math.cos(k))], 3, mix(CV_ROCK2, INK, 0.4), seed=9832 + k, boil=0.8, n=5, a=170)
            glow_stroke(c, poly_path(cr_closed(hill, 5)), P_["gold"], 70, 22, 220)
        blob(cv, hill, CV_ROCK2, w=6, seed=9830, boil=1.1, n=5, shade=hs)
        blob(cv, mouth, (16, 6, 36), w=6, seed=9840, boil=1.0, n=5,
             shade=lambda c: radial(c, 450, 760, 260, [(P_["hotpink"], 70), (P_["hotpink"], 0)]))
        line(cv, [(118, 905), (122, 712)], 14, (150, 90, 50), seed=9842, boil=0.5, n=2, taper=(0, 0))          # signpost: OUTSIDE ->
        cv.save()
        cv.translate(126, 716)
        cv.rotate(-6 + 2 * math.sin(T * 1.3))
        blob(cv, [(-84, -34), (62, -40), (104, -4), (64, 32), (-82, 28)], (226, 170, 100), w=5, seed=9843, boil=0.8, n=3,
             shade=lambda c: [c.drawLine(-86, -20 + k * 16, 100, -22 + k * 16, paint((196, 136, 76), stroke=2.5)) for k in range(4)])
        paint_text(cv, "OUTSIDE", 4, 13, font="londrina", size=34, fill=P_["red"], ink_w=0, shadow=None, seed=9844, streaks=False, rot_jit=3.0)
        cv.restore()
        for k, (cx_, cy_) in enumerate(((150, 420), (720, 330), (930, 600), (40, 640), (820, 700))):
            crystal(cv, cx_, cy_, 0.7, T, seed=9850 + k)
        for k, (mx_, my_) in enumerate(((210, 880), (700, 860), (960, 820), (60, 560))):
            glow_mushroom(cv, mx_, my_, 0.9, T, seed=9860 + k)
        grass = [(-200, 1200), (-200, 900), (300, 870), (700, 880), (1100, 900), (1500, 880), (2200, 900), (2200, 1200)]
        blob(cv, grass, P_["acid"], w=6, seed=9870, boil=1.0, n=4,
             shade=lambda c: [c.drawPath(poly_path(cr_open([(-200, 940 + k * 46), (500, 930 + k * 50), (1200, 950 + k * 44), (2200, 940 + k * 48)], 6), closed=False),
                                         paint([P_["teal"], P_["yellow"], P_["acid_dk"]][k % 3], stroke=12)) for k in range(5)])
        road = cr_open(np.array(PATH_A, float), 10)
        rw = np.interp(np.arange(len(road)), [0, len(road) - 1], [70, 230])
        N = core._normals(road, False)
        poly = np.vstack([road + N * (rw[:, None] / 2), (road - N * (rw[:, None] / 2))[::-1]])
        cv.drawPath(poly_path(poly), paint(P_["peach"]))
        brush(cv, road + N * (rw[:, None] / 2), 4.5, taper=(0.02, 0.02), seed=9871)
        brush(cv, road - N * (rw[:, None] / 2), 4.5, taper=(0.02, 0.02), seed=9872)
        for k in range(16):
            u = (k + 0.5) / 16
            i = int(u * (len(road) - 1))
            px, py = road[i] + N[i] * rw[i] * 0.3 * math.sin(k * 2.3)
            blob(cv, ell(px, py, 6 + 10 * u, 4 + 5 * u, n=7), P_["cream_sh"], w=2.5, seed=9873 + k, boil=0.5)
        # who is where
        ms = []
        for i, who in enumerate(CAST52):
            u = (t - (0.05 + i * 0.5556)) * 0.162
            if u < -0.01:
                continue
            ms.append((u, who))
        lead = max(u for u, _ in ms) if ms else 0.0
        hx = _path_a(lead)[0] if ms else 0
        for k in range(14):                                           # flowers along the path bloom as the host passes
            u = 0.12 + k * 0.065
            px, py, ss = _path_a(u)
            side = 1 if k % 2 else -1
            fx, fy = px - 30, py - (50 + 40 * ss)
            born = 0.05 + (u / 0.162) + 0.15
            if side < 0:
                _bloom_flower(cv, fx, fy, 0.3 + 0.4 * ss, T, born, t, seed=9880 + k * 7, kind=k % 3)
        for u, who in sorted(ms):
            x, y, ss = _path_a(max(0.0, u))
            dark = 1.0 - seg(u, 0.02, 0.13)
            hh = _member_height(who, ss)
            _darkened(cv, (x - hh, y - hh * 1.3, x + hh, y + 60), dark * 0.92, lambda x=x, y=y, ss=ss, who=who: _draw_member(cv, A, who, x, y, ss, T))
        for k in range(14):
            u = 0.12 + k * 0.065
            px, py, ss = _path_a(u)
            side = 1 if k % 2 else -1
            if side > 0:
                born = 0.05 + (u / 0.162) + 0.15
                _bloom_flower(cv, px + 60, py + 95 + 70 * ss, 0.32 + 0.38 * ss, T, born, t, seed=9880 + k * 7, kind=k % 3)
    _flood_soft(cv, T, C.to_screen(*sun, 0.08), 0.6)
    _confetti52(cv, t, seed=9700, n=int(10 + 30 * seg(t, 2.0, 6.0)), a=seg(t, 1.5, 3.0))


def _flood_soft(cv, T, sun_scr, a, seed=9750):
    sx, sy = sun_scr
    radial(cv, sx, sy, 1700, [(P_["gold"], int(110 * a)), (P_["orange"], int(40 * a)), (P_["orange"], 0)], stops=[0.0, 0.4, 1.0], blend=SCREEN_B,
           rect=(-50, -50, W + 50, H + 50))
    for k in range(10):
        u = (k + 0.5) / 10
        aa = math.radians(150 + 70 * (u - 0.5) + 3 * math.sin(T * 0.4 + k * 1.3))
        wd = math.radians(1.6 + 1.4 * math.sin(T * 0.7 + k * 2.1))
        r = 2600
        p = [(sx, sy), (sx + r * math.cos(aa - wd), sy + r * math.sin(aa - wd)), (sx + r * math.cos(aa + wd), sy + r * math.sin(aa + wd))]
        pp = skia.Paint(AntiAlias=True)
        pp.setShader(skia.GradientShader.MakeRadial(skia.Point(sx, sy), r, [core.C(P_["yellow"], int(70 * a)), core.C(P_["yellow"], 0)], None))
        pp.setBlendMode(SCREEN_B)
        cv.drawPath(poly_path(p), pp)


T52_B, T52_C = 6.678, 15.567       # cuts on bar lines


def T052_outside(cv, t, T, A):
    _BOUNCE[0] = 0.45 + 0.55 * seg(t, 0.0, 3.5)
    if t < T52_B:
        _scene_a(cv, t, T, A)
    elif t < T52_C:
        _scene_b(cv, t, T, A)
    else:
        _scene_c(cv, t, T, A)
    _BOUNCE[0] = 1.0


def _road_y(X):
    return 930 + 16 * math.sin(X * 0.0031) + 8 * math.sin(X * 0.0011 + 1.0)


B_GAPS = {"host": 0, "zee": 330, "gary": 650}
for _k in range(13):
    B_GAPS[f"eye{_k}"] = 880 + _k * 168
B_SPEED = 165.0


def _scene_b(cv, t, T, A):
    """The parade on the road over the rolling hills: a tracking shot (Gary lowers his tiny sunglasses and winks)."""
    tb = t - T52_B
    track = B_SPEED * tb
    lead = track + 1460
    gx = lead - B_GAPS["gary"]
    zin = ease_io(seg(t, 10.7, 11.3)) * (1 - ease_io(seg(t, 13.45, 14.05)))
    z = 1.0 + 0.9 * zin + 0.006 * contact_of(beat52(T)[1])
    gy = _road_y(gx) - 470 * 0.6 * 0.74 + 40
    cam = dict(x=lerp(track, gx - 960, zin), y=lerp(0.0, gy - 540, zin), z=z)
    C = sets.Cam(cv, cam)
    _sky52(cv, T, C, (1480, 300), 135, p=0.05, look=(-0.5, 0.5))
    vis0, vis1 = cam["x"] - 900, cam["x"] + W + 900
    with C.layer(0.16):
        x0 = cam["x"] * 0.16 - 400
        w.ribbon(cv, [(x0, 240), (x0 + 700, 80), (x0 + 1400, 130), (x0 + 2100, 40), (x0 + 2900, 110)], 96,
                 [P_["magenta"], P_["orange"], P_["yellow"], P_["acid"], P_["teal"]], flow=T * 1.1, seed=9900, ink=5)
    with C.layer(0.3):
        x0, x1 = cam["x"] * 0.3 - 500, cam["x"] * 0.3 + W + 500
        for k, (yy, col) in enumerate(((600, P_["teal"]), (640, mix(P_["teal"], P_["acid"], 0.5)), (680, P_["yellow"]), (720, P_["orange"]))):
            _band(cv, yy, 700, col, 24 + k * 6, 1.1 + k * 0.4, 9910 + k, x0=x0, x1=x1)
    with C.layer(0.56):
        base = cam["x"] * 0.56
        k0 = int((base - 800) // 560)
        for k in range(k0, k0 + 6):
            hx = k * 560 + 180 * math.sin(k * 1.7)
            hh = 230 + 80 * float(hsh(9920 + k))
            cols = [[P_["acid"], P_["yellow"], P_["teal"]], [P_["hotpink"], P_["orange"], P_["yellow"]], [P_["teal"], P_["mint"], P_["acid"]]][k % 3]
            dome = [(hx - 420, 900), (hx - 300, 900 - hh * 0.7), (hx, 900 - hh), (hx + 300, 900 - hh * 0.7), (hx + 420, 900)]
            blob(cv, dome + [(hx + 420, 1200), (hx - 420, 1200)], cols[0], w=5, seed=9921 + k, boil=1.0, n=5,
                 shade=lambda c, hx=hx, hh=hh, cols=cols: [c.drawPath(poly_path(cr_open([(hx - 500, 900 - hh * (0.62 - j * 0.16) + 40), (hx, 900 - hh * (0.95 - j * 0.16)),
                                                                                          (hx + 500, 900 - hh * (0.62 - j * 0.16) + 40)], 8), closed=False),
                                                                     paint(cols[1 + j % 2], stroke=26)) for j in range(4)])
            kind = k % 4
            if kind == 0:
                w.mushroom(cv, hx + 120, 900 - hh * 0.84, 0.55, seed=9930 + k)
            elif kind == 1:
                w.pyramid(cv, hx - 60, 900 - hh * 0.9, 0.36, look=(0.4, 0.2), seed=9931 + k, rays=False)
            elif kind == 2:
                w.wizard(cv, hx + 80, 900 - hh * 0.88, 0.55, seed=9932 + k, phase=T * 2.2)
            else:
                w.eyeball_walker(cv, hx - 40 + 30 * math.sin(T), 900 - hh * 0.93, 0.6, T * 3.2, seed=9933 + k)
    with C.layer(1.0):
        x0, x1 = vis0, vis1
        xs = np.arange(x0, x1 + 80, 80.0)
        top = np.array([(x, _road_y(x) - 140 - 18 * math.sin(x * 0.004)) for x in xs])
        meadow = np.vstack([top, [(x1 + 80, 1400), (x0, 1400)]])
        cv.drawPath(poly_path(meadow), paint(P_["acid"]))
        for j in range(4):
            yy = np.array([(x, _road_y(x) - 100 + j * 70 + 10 * math.sin(x * 0.006 + j)) for x in xs])
            brush(cv, yy, 14, [P_["teal"], P_["yellow"], P_["acid_dk"], P_["mint"]][j], taper=(0.01, 0.01), seed=9940 + j, a=200)
        brush(cv, top, 5, taper=(0.01, 0.01), seed=9944)
        ra = np.array([(x, _road_y(x) - 46) for x in xs])
        rb = np.array([(x, _road_y(x) + 52) for x in xs])
        cv.drawPath(poly_path(np.vstack([ra, rb[::-1]])), paint(P_["peach"]))
        brush(cv, ra, 4.5, taper=(0.01, 0.01), seed=9945)
        brush(cv, rb, 4.5, taper=(0.01, 0.01), seed=9946)
        for X in np.arange((x0 // 90) * 90, x1, 90.0):
            blob(cv, ell(X + 30 * math.sin(X), _road_y(X) + 10 + 24 * math.sin(X * 0.37), 8, 5, n=7), P_["cream_sh"], w=2.5, seed=int(X) % 997 + 9950, boil=0.5)
        fl = []
        zf_ = C.zoom(1.0)
        fx0 = cam["x"] + W / 2 - (W / 2) / zf_ - 160
        fx1 = cam["x"] + W / 2 + (W / 2) / zf_ + 160
        for X in np.arange((fx0 // 130) * 130, fx1, 130.0):
            born = T52_B + (X - 1460) / B_SPEED + 0.05
            fl.append((X, born))
        for X, born in fl:                                            # behind the road
            _bloom_flower(cv, X + 40 * math.sin(X * 0.7), _road_y(X) - 66, 0.55 + 0.25 * float(hsh(X * 0.01)), T, born, t, seed=int(X) % 991 + 9960, kind=int(X / 130) % 3)
        order = sorted(B_GAPS.items(), key=lambda kv: -kv[1])
        for who, gap in order:
            X = lead - gap
            if X < x0 - 300 or X > x1 + 300:
                continue
            ex = {}
            if who == "gary":
                down = ease(seg(t, 11.5, 11.8)) * (1 - ease(seg(t, 12.55, 12.75)))
                ex = dict(tip=78 * 0.444 * down, squint=ease(seg(t, 11.75, 11.95)) * (1 - ease(seg(t, 12.5, 12.65))),
                          loud=0.55 * seg(t, 12.75, 12.85) * (1 - seg(t, 13.3, 13.5)))
            mv = ["roof", "point", "wave", "clap"][int((T - BEAT52) / 2.2222) % 4] if who in ("host", "zee") else None
            if who == "zee" and mv == "roof":
                mv = "big"
            _draw_member(cv, A, who, X, _road_y(X), 0.6, T, move=mv, extra=ex)
        for X, born in fl:                                            # in front of the road (sparse, low)
            if int(X / 130) % 2 == 0:
                _bloom_flower(cv, X + 65 + 30 * math.cos(X), _road_y(X) + 150, 0.5 + 0.2 * float(hsh(X * 0.013)), T, born + 0.12, t, seed=int(X) % 983 + 9970,
                              kind=int(X / 130 + 1) % 3)
        if 12.75 < t < 13.6:                                          # shades back on: cool again (ting!)
            k = pop(t, 12.78, 0.22) * (1 - seg(t, 13.3, 13.6))
            gyy = _road_y(gx) - 470 * 0.444 + 6 * math.sin(T * 3.1) * 0.444
            sparkle(cv, gx + 40, gyy - 40, 40 * k + 1, P_["white"], w=3, seed=9980)
            sparkle(cv, gx + 95, gyy - 75, 20 * k + 1, P_["yellow"], w=3, seed=9981)
    with C.layer(1.35):
        base = cam["x"] * 1.35
        for k in range(int((base - 400) // 640), int((base + W + 400) // 640) + 1):
            fx = k * 640 + 160 * math.sin(k * 2.1)
            _flower(cv, fx, 1200, 0.8 + 0.25 * float(hsh(k + 9990)), T, seed=9991 + (k % 50) * 7, kind=k % 3)
    _flood_soft(cv, T, (1480, 250), 0.45)
    _confetti52(cv, t, seed=9720, n=48, a=1.0)


C_SPOTS = [  # who, feet x, feet y, scale, entry dx, entry dy
    ("host", 640, 812, 0.6, -560, 30), ("zee", 1280, 812, 0.6, 560, 30), ("gary", 960, 975, 0.6, 0, 460),
    ("eye0", 430, 846, 0.5, -700, 30), ("eye1", 1490, 846, 0.5, 700, 30), ("eye2", 255, 880, 0.54, -700, 40), ("eye3", 1665, 880, 0.54, 700, 40),
    ("eye4", 95, 925, 0.58, -600, 50), ("eye5", 1825, 925, 0.58, 600, 50), ("eye6", 360, 985, 0.62, -800, 50), ("eye7", 1560, 985, 0.62, 800, 50),
    ("eye8", 170, 1035, 0.64, -700, 50), ("eye9", 1750, 1035, 0.64, 700, 50), ("eye10", 560, 960, 0.56, -820, 40), ("eye11", 1360, 960, 0.56, 820, 40),
]
T52_TADA = 22.234                  # beat 40: the big group jump
def _scene_c(cv, t, T, A):
    """The hilltop tableau under the grinning sun: crane down from the sun as everybody arrives, then the TA-DA."""
    pull = ease_io(seg(t, T52_C, T52_C + 3.6))
    b, ph = beat52(T)
    z = lerp(1.2, 1.0, pull) + 0.03 * seg(t, 19.5, 25.6) + 0.007 * contact_of(ph)
    cam = dict(x=0.0, y=lerp(-55.0, 12.0, pull), z=z)
    C = sets.Cam(cv, cam)
    tada = seg(t, T52_TADA - 0.1, T52_TADA + 0.15) * (1 - seg(t, 24.6, 25.0))
    _sky52(cv, T, C, (960, 405), 272, p=0.08, grin=0.85 + 0.25 * tada, look=(0.25 * math.sin(T * 0.9), 0.55), glow=1.0 + 0.3 * tada)
    with C.layer(0.2):
        w.ribbon(cv, [(-300, 900), (200, 380), (700, 90), (1240, 80), (1700, 330), (2200, 860)], 120, [P_["magenta"], P_["orange"], P_["yellow"], P_["acid"], P_["teal"]],
                 flow=T * 1.0, seed=9800, ink=5)
    with C.layer(0.38):
        for k, (yy, col) in enumerate(((690, P_["teal"]), (725, P_["acid"]), (760, P_["yellow"]))):
            _band(cv, yy, 700, col, 20 + k * 6, 1.4 + k * 0.5, 9840 + k)
    with C.layer(1.0):
        hill = [(-320, 1300), (-320, 1000), (100, 900), (480, 812), (960, 776), (1440, 812), (1820, 900), (2240, 1000), (2240, 1300)]

        def hs(c):
            for j in range(7):
                dy = j * 62
                pts = [(-400, 1000 + dy), (100, 900 + dy * 1.05), (480, 822 + dy * 1.1), (960, 790 + dy * 1.12), (1440, 822 + dy * 1.1), (1820, 900 + dy * 1.05), (2300, 1000 + dy)]
                c.drawPath(poly_path(cr_open(pts, 8), closed=False), paint([P_["teal"], P_["yellow"], P_["hotpink"], P_["orange"], P_["mint"], P_["yellow"], P_["teal"]][j], stroke=22))
        blob(cv, hill, P_["acid"], w=6, seed=9850, boil=1.0, n=5, shade=hs)
        for k in range(16):                                          # the crest bursts into flowers, from the middle outward
            fx = 960 + (k // 2 + 0.6) * 108 * (1 if k % 2 else -1) + 24 * math.sin(k * 2.3)
            fy = 800 + abs(fx - 960) ** 1.35 * 0.02 + 14 * float(hsh(9860 + k))
            born = T52_C + 0.3 + abs(fx - 960) / 700.0
            _bloom_flower(cv, fx, fy, 0.34 + 0.16 * float(hsh(9870 + k)), T, born, t, seed=9875 + k * 7, kind=k % 3)
        jump = 70 * math.sin(math.pi * seg(t, T52_TADA - 0.05, T52_TADA + 0.5))
        for who, fx, fy, ss, ex_, ey_ in sorted(C_SPOTS, key=lambda q: q[2]):
            idx = CAST52.index(who)
            arrive = ease_io(seg(t, T52_C + 0.1 * (idx % 5), T52_C + 2.4 + 0.12 * (idx % 5)))
            if who == "gary":
                arrive = ease_io(seg(t, T52_C + 1.6, T52_C + 2.3))
            x = fx + ex_ * (1 - arrive)
            y = fy + ey_ * (1 - arrive) - jump * (1.2 if who == "gary" else 1.0)
            mv = None
            if who in ("host", "zee"):
                mv = "tada" if tada > 0.5 else (["roof", "clap", "point", "wave"][int((T - BEAT52) / 2.2222) % 4])
                if who == "zee" and mv == "roof":
                    mv = "big"
            _draw_member(cv, A, who, x, y, ss, T, move=mv, extra=dict(loud=0.5 * tada) if who == "gary" else None)
        for k in range(6):                                           # a few big blooms in the bottom corners
            fx = [40, 230, 120, 1880, 1690, 1800][k]
            fy = [1110, 1150, 1210, 1110, 1150, 1210][k]
            _bloom_flower(cv, fx, fy, 0.75, T, T52_C + 1.0 + 0.15 * k, t, seed=9990 + k * 7, kind=k % 3)
        rise = ease(seg(t, T52_TADA - 1.6, T52_TADA - 0.9))
        for side in (-1, 1) if rise > 0 else ():                    # confetti cannons pop up in the corners
            cx_ = 960 + side * 890
            kick = math.exp(-max(0.0, t - T52_TADA) * 6) if t > T52_TADA else 0.0
            cv.save()
            cv.translate(cx_, 1080 + 230 * (1 - rise) + 30 * kick)
            cv.scale(0.8, 0.8)
            cv.rotate(side * -28 + side * 6 * kick)
            blob(cv, rect_pts([(-40, -10), (40, -10), (32, -170), (-32, -170)], 3), P_["magenta"], w=5, seed=9995 + side, boil=0.8, n=3,
                 shade=lambda c: [c.drawRect(R(-50, -60 - j * 44, 50, -48 - j * 44), paint(P_["yellow"])) for j in range(3)])
            blob(cv, ell(0, -170, 36, 12, n=10), (40, 20, 60), w=4, seed=9997 + side, boil=0.6)
            cv.restore()
    _flood_soft(cv, T, C.to_screen(960, 405, 0.08), 0.55 + 0.3 * tada)
    _confetti52(cv, t, seed=9740, n=70, a=1.0, bursts=[(90, 950, t - T52_TADA, 1), (1830, 950, t - T52_TADA, -1)])
