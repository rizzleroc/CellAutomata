"""BOXED ep4 'THE CAVE' -- the main unit: cold open in the dark, the title, every talk-show beat, the host's meltdown,
the outdoor sign-off, the endcard and the post-credits stinger."""
from .shots_ep4_base import *          # noqa: F401,F403
from .shots_ep4_base import (P_, R, PAL, INK, W, H, paint, poly_path, cr_closed, cr_open, ell, blob, line, brush, dots, hsh, mix,
                             jit, rot, stipple, sparkle, rect_pts, tube, core, w, sets, paint_text, draw_zee, draw_host, Hh, G,
                             ease, pop, lerp, CAM_HOST, CAM_ZEE, CAM_WIDE, CAM_TWO, HOST_POS, GUEST_POS, studio, caption,
                             loud_at, vis_at, spk_loud, gary, LINES, SLOTS, darkness, vignette, firelight, shadow_shape,
                             audience_rows, cave_wall_view, sun_rays, prisoner, chain)
import math
import numpy as np
import skia
from .cast import HEAD_Y, HEAD_S, PHOS, head_anchor

PHOS_GLOW = (150, 255, 210)


def L0(lid):
    return LINES[lid]["t0"]


def L1(lid):
    return LINES[lid]["t1"]


# ------------------------------------------------------------------ camera / lighting helpers
def cam_lerp(a, b, u):
    u = ease(u)
    return dict(x=lerp(a["x"], b["x"], u), y=lerp(a["y"], b["y"], u), z=lerp(a["z"], b["z"], u))


def shake(cam, amt, T, seed=0):
    if amt <= 0:
        return cam
    c = dict(cam)
    c["x"] += amt * (hsh(core.D * 1.3 + seed) - 0.5) * 2
    c["y"] += amt * (hsh(core.D * 2.7 + seed + 9) - 0.5) * 2
    return c


def host_screen(A, cam, extra=None):
    """Screen-space centre of the host's CRT for a camera (uses the acting channels)."""
    P = dict(A["HOST"]); P.update(HOST_POS); P.update(extra or {})
    lx, ly = head_anchor(P)
    X, Y = P["x"] + lx * P["s"], P["y"] + ly * P["s"]
    return sets.Cam(None, cam).to_screen(X, Y, 1.0)


def zee_eyes(A, cam, extra=None):
    P = dict(A["GUEST"]); P.update(GUEST_POS); P.update(extra or {})
    X, Y = P["x"], P["y"] + (-536 + P.get("head_dy", 0.0)) * P["s"]
    return sets.Cam(None, cam).to_screen(X, Y, 1.0)


def light_mask(cv, lights, ambient=14, T=0.0):
    """Multiply the frame by a lightmap: dark ambient + additive radial pools. lights: (x, y, r, k, rgb)."""
    s = skia.Surface.MakeRaster(skia.ImageInfo.Make(W, H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType))
    c = s.getCanvas()
    c.clear(skia.ColorSetARGB(255, ambient, ambient, int(ambient * 1.3)))
    for (x, y, r, k, rgb) in lights:
        fl = 1.0 + 0.04 * math.sin(T * 13.0 + x * 0.01)
        p = skia.Paint(AntiAlias=True)
        p.setBlendMode(skia.BlendMode.kPlus)
        c1 = tuple(int(min(255, v * k * fl)) for v in rgb)
        p.setShader(skia.GradientShader.MakeRadial(skia.Point(x, y), max(1.0, r), [core.C(c1), core.C(tuple(int(v * 0.45) for v in c1)), core.C((0, 0, 0))],
                                                   [0.0, 0.42, 1.0]))
        c.drawCircle(x, y, r, p)
    img = s.makeImageSnapshot()
    mp = skia.Paint()
    mp.setBlendMode(skia.BlendMode.kMultiply)
    cv.drawImage(img, 0, 0, skia.SamplingOptions(), mp)


def glow(cv, x, y, r, rgb, a=90):
    p = skia.Paint(AntiAlias=True)
    p.setBlendMode(skia.BlendMode.kScreen)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(x, y), max(1.0, r), [core.C(rgb, a), core.C(rgb, 0)]))
    cv.drawCircle(x, y, r, p)


# ------------------------------------------------------------------ the dark stage (cold open)
def dark_stage(cv, T, cam, host, guest, bunny=0.0, bunny_hop=0.0, seed=7):
    """The BOXED stage with the cosmic backdrop switched off: a bare studio flat, the island, desk, couch, performers.
    bunny 0..1: a giant hand-shadow bunny on the flat behind the host (follows his hands)."""
    C = sets.Cam(cv, cam)
    with C.layer(0.6):
        w.field(cv, (58, 46, 84))
        for k in range(9):                                         # flat panels + seams
            x = -300 + k * 300
            line(cv, [(x, -200), (x + 4, 900)], 4, (40, 30, 62), seed=seed + k, boil=0.6, n=2, taper=(0, 0))
        stipple(cv, (44, 34, 68), (-300, -200, 2300, 900), spacing=18, r=2.0, seed=seed + 3)
        for k in range(6):                                         # dead light rigs hanging
            x = 100 + k * 340
            line(cv, [(x, -200), (x, 40)], 3, (30, 24, 44), seed=seed + 20 + k, boil=0.5, n=2, taper=(0, 0))
            blob(cv, [(x - 34, 40), (x + 34, 40), (x + 26, 96), (x - 26, 96)], (40, 34, 56), w=4, seed=seed + 30 + k, boil=0.6, n=3)
        if bunny > 0.01:
            hx, hy = 1040, 340
            sc = 1.9 * ease(bunny)
            spot = skia.Paint(AntiAlias=True)
            spot.setShader(skia.GradientShader.MakeRadial(skia.Point(hx, hy + 20), 420, [core.C((215, 240, 255), int(190 * min(1, bunny * 1.5))),
                                                                                       core.C((150, 200, 230), int(90 * min(1, bunny * 1.5))), core.C((90, 120, 160), 0)],
                                                          [0.0, 0.55, 1.0]))
            cv.drawCircle(hx, hy + 20, 420, spot)
            yy = hy - 30 * abs(math.sin(bunny_hop * math.pi * 2)) * bunny
            shadow_shape(cv, "hand_bunny", hx + 40 * math.sin(bunny_hop * 1.3), yy, sc, T, rgb=(14, 8, 24), a=int(235 * min(1, bunny * 1.6)), seed=seed + 50)
        paint_text(cv, "BOXED", 960, 190, font="shrik", size=150, fill=(70, 60, 90), ink_w=5, shadow=None, seed=seed + 310, wobble=1.0, streaks=False)
    with C.layer(0.85):
        w.island(cv, 960, 905, 820, 120, seed=seed + 200, top=P_["violet"], depth=240, strata=[P_["orange"], P_["red"], P_["maroon"], P_["night"]])
        w.rug(cv, 960, 905, 640, 92, seed=seed + 210)
    with C.layer(1.0):
        w.couch(cv, 1350, 905, 0.82, seed=seed + 400, rgb=P_["orange"], rgb2=P_["red"], part="back")
        w.lamp(cv, 1760, 905, 1.0, seed=seed + 410)
        w.plant(cv, 190, 905, 0.95, seed=seed + 420, phase=T * 0.3)
        if host is not None:
            draw_host(cv, host)
        sets.desk(cv, 640, 912, 1.0, seed=seed + 430)
        sets.mug(cv, 858, 744, 1.0, T, seed=seed + 440)
        if guest is not None:
            draw_zee(cv, guest)
        w.couch(cv, 1350, 905, 0.82, seed=seed + 400, rgb=P_["orange"], rgb2=P_["red"], part="front")
        sets.side_table(cv, 1690, 912, 1.0, seed=seed + 450)
        sets.lava(cv, 1690, 812, 1.0, T, seed=seed + 460)


def dark_lights(cv, A, cam, T, zee_k=0.25, extra=()):
    hx, hy = host_screen(A, cam)
    z = cam["z"]
    zx, zy = zee_eyes(A, cam)
    lights = [(hx, hy, 430 * z, 1.05, (210, 255, 235)), (hx, hy + 200 * z, 760 * z, 0.32, (150, 230, 255))]
    if zee_k > 0:
        lights.append((zx, zy, 260 * z, zee_k, (190, 170, 255)))
    lights += list(extra)
    light_mask(cv, lights, ambient=5, T=T)
    glow(cv, hx, hy, 230 * z, PHOS_GLOW, a=80)


# ------------------------------------------------------------------ audience close-ups
def audience_cu(cv, T, gx=960, gy=560, gs=1.0, spot=0.0, dark=0.0, seed=8800, gary_kw=None, rows=True):
    """Gary sitting among the eyeball audience; optional spotlight cone on him; dark 0..1 = house lights off."""
    w.field(cv, (30, 14, 52))
    sunb = [(40, 18, 70), (30, 14, 52)]
    w.sunburst(cv, 960, -200, 2400, 22, sunb, rot_deg=T * 2, seed=seed)
    cols = [(40, 20, 70), (54, 26, 90), (70, 30, 110)]
    if rows:
        for row in range(3):
            y = 380 + row * 230
            for k in range(9):
                x = -60 + k * 250 + (125 if row % 2 else 0)
                if abs(x - gx) < 210 and abs(y - gy) < 300:
                    continue
                r = 90 + row * 14
                bob = 4 * math.sin(T * 2 + k * 1.3 + row)
                blob(cv, ell(x, y + bob, r, r * 1.05, n=10), cols[(k + row) % 3], w=5, seed=seed + k * 7 + row * 100, boil=1.0)
                look = (gx - x) / 900.0
                dots(cv, [(x + look * 30, y + bob - 8)], 24, (200, 255, 230) if (k + row) % 2 else (255, 200, 240))
                dots(cv, [(x + look * 30, y + bob - 8)], 11, INK)
    if spot > 0:
        p = skia.Paint(AntiAlias=True)
        p.setShader(skia.GradientShader.MakeLinear([skia.Point(gx, -100), skia.Point(gx, gy + 300)], [core.C(P_["cream"], int(150 * spot)), core.C(P_["yellow"], int(60 * spot))]))
        cv.drawPath(poly_path([(gx - 70, -100), (gx + 70, -100), (gx + 330 * gs, gy + 420 * gs), (gx - 330 * gs, gy + 420 * gs)]), p)
        cv.drawPath(poly_path(cr_closed(ell(gx, gy + 400 * gs, 330 * gs, 70 * gs, n=16), 4)), paint(P_["yellow"], int(70 * spot)))
    gary(cv, gx, gy, gs, T, seed=seed + 900, **(gary_kw or {}))
    if dark > 0:
        darkness(cv, int(235 * dark))


# ------------------------------------------------------------------ sunny outdoor set (tag)
def sunny_set(cv, T, cam, host=None, guest=None, gary_xy=None, seed=77):
    C = sets.Cam(cv, cam)
    with C.layer(0.15):
        g = skia.Paint(AntiAlias=True)
        g.setShader(skia.GradientShader.MakeLinear([skia.Point(0, -200), skia.Point(0, 900)],
                                                   [core.C(P_["hotpink"]), core.C(P_["peach"]), core.C(P_["yellow"])], [0.0, 0.55, 1.0]))
        cv.drawRect(R(-400, -400, 2400, 1400), g)
        w.sunburst(cv, 1460, 260, 2400, 26, [mix(P_["yellow"], P_["white"], 0.4), mix(P_["peach"], P_["yellow"], 0.3)], rot_deg=T * 3, seed=seed)
        firelight(cv, 1460, 260, 700, T, a=120, rgb=P_["yellow"], seed=seed + 1)
        for k in range(5):                                         # clouds drift behind the sun
            cx = (200 + k * 420 + T * 14) % 2300 - 200
            cy = 120 + k * 46 + (90 if abs(cx - 1460) < 330 else 0)
            blob(cv, [(cx - 120, cy + 40), (cx - 60, cy - 10), (cx + 30, cy), (cx + 120, cy + 45)], P_["white"], w=4, seed=seed + 10 + k, boil=0.9, n=4)
        w.planet(cv, 1460, 260, 210, P_["yellow"], bands=[(-0.5, 0.2, P_["orange"]), (0.1, 0.18, P_["gold"]), (0.4, 0.2, P_["orange"])],
                 ring=dict(rx=1.75, ry=0.33, rgb=P_["teal"], rgb2=P_["cream"], tilt=-16),
                 face=dict(look=(-0.5, 0.25), smile=0.9, lids=0.25, lid_rgb=P_["gold"]), seed=seed + 2, crater=False)
    with C.layer(0.45):
        w.hills(cv, 760, 110, [P_["acid"], P_["teal"], P_["yellow"], P_["orange"], P_["magenta"]], seed=seed + 20, freq=1.4, spacing=26)
        for k in range(10):
            fx = 80 + k * 190
            w.mushroom(cv, fx, 860 + 20 * math.sin(k), 0.35 + 0.1 * (k % 3), seed=seed + 30 + k) if k % 3 == 0 else None
    with C.layer(0.85):
        w.island(cv, 960, 905, 820, 120, seed=seed + 200, top=P_["acid"], depth=240, strata=[P_["yellow"], P_["orange"], P_["red"], P_["maroon"]])
        w.rug(cv, 960, 905, 640, 92, seed=seed + 210)
        for k in range(16):                                        # flowers on the turf
            fx = 260 + k * 92 + 20 * math.sin(k * 3.1)
            fy = 905 + 70 * math.sin(k * 1.9) * 0.6
            for j in range(5):
                a = j / 5 * 2 * math.pi + T * 0.5
                dots(cv, [(fx + 9 * math.cos(a), fy - 30 + 9 * math.sin(a))], 7, [P_["hotpink"], P_["white"], P_["yellow"]][k % 3])
            dots(cv, [(fx, fy - 30)], 5, P_["orange"])
    with C.layer(1.0):
        w.couch(cv, 1350, 905, 0.82, seed=seed + 400, rgb=P_["orange"], rgb2=P_["red"], part="back")
        if host is not None:
            draw_host(cv, host)
        sets.desk(cv, 640, 912, 1.0, seed=seed + 430)
        sets.mug(cv, 858, 744, 1.0, T, seed=seed + 440)
        if guest is not None:
            draw_zee(cv, guest)
        w.couch(cv, 1350, 905, 0.82, seed=seed + 400, rgb=P_["orange"], rgb2=P_["red"], part="front")
        if gary_xy is not None:
            gx, gy, gs = gary_xy
            gary(cv, gx, gy, gs, T, seed=seed + 900)
            shades(cv, gx - 4 * gs, gy - 22 * gs, gs)


def shades(cv, x, y, s):
    """Tiny cool sunglasses for Gary's single eye."""
    blob(cv, [(x - 110 * s, y - 40 * s), (x + 110 * s, y - 40 * s), (x + 96 * s, y + 40 * s), (x + 20 * s, y + 52 * s), (x - 20 * s, y + 52 * s), (x - 96 * s, y + 40 * s)],
         (20, 10, 30), w=5, seed=991, boil=0.6, n=3, shade=lambda c: c.drawPath(poly_path([(x - 80 * s, y - 30 * s), (x - 30 * s, y - 30 * s), (x - 70 * s, y + 10 * s)]),
                                                                            paint(P_["white"], 120)))
    for side in (-1, 1):
        line(cv, [(x + side * 108 * s, y - 34 * s), (x + side * 150 * s, y - 50 * s)], 6, (20, 10, 30), seed=992 + side, boil=0.4, n=2, taper=(0, 0))


# ===================================================================== COLD OPEN
def T001_dark_open(cv, t, T, A):
    cam = cam_lerp(dict(x=40, y=40, z=1.25), dict(x=-60, y=10, z=1.38), t / 10.65)
    h, g = Hh(A, t), G(A, t)
    h["smile"] = 0.2
    dark_stage(cv, T, cam, h, g)
    on = min(1.0, max(0.0, (T - 1.2) / 0.5))                      # the CRT glow flickers on
    fl = on * (0.75 + 0.25 * (hsh(core.D * 1.7) > 0.25)) if T < 2.0 else 1.0
    zk = 0.08 + 0.32 * ease((T - L0("C02") + 0.4) / 0.6)
    hx, hy = host_screen(A, cam)
    if fl < 0.05:
        darkness(cv, 255)
        return
    dark_lights(cv, A, cam, T, zee_k=zk * fl)
    if fl < 1.0:
        darkness(cv, int(255 * (1 - fl)))
    for k in range(14):                                            # dust motes in the CRT light
        ph = (T * 0.05 + hsh(k * 3.3)) % 1.0
        mx = hx - 300 + 600 * hsh(k * 5.1) + 40 * math.sin(T * 0.6 + k)
        my = hy - 260 + 520 * ph
        dots(cv, [(mx, my)], 1.6 + 1.6 * hsh(k), PHOS_GLOW, a=int(140 * fl * (1 - abs(ph - 0.5) * 2)))


def T002_bunny(cv, t, T, A):
    t_bunny = L0("C03") + (L1("C03") - L0("C03")) * 0.78
    if T < L0("C05") - 0.1:
        cam = cam_lerp(dict(x=-60, y=10, z=1.38), dict(x=-200, y=-150, z=1.12), (T - L0("C03")) / 5.0)
    elif T < L0("C06") - 0.2:
        cam = dict(x=-230, y=-60, z=1.55)
    else:
        cam = None
    bunny = ease((T - t_bunny) / 0.6)
    hop = T * 1.6
    if cam is not None:
        h, g = Hh(A, t), G(A, t)
        dark_stage(cv, T, cam, h, g, bunny=bunny, bunny_hop=hop)
        hx, hy = host_screen(A, cam)
        bx, by = sets.Cam(None, cam).to_screen(1040, 360, 0.6)
        dark_lights(cv, A, cam, T, zee_k=0.22, extra=[(bx, by + 20, 520 * cam["z"], 0.75 * max(0.25, bunny), (190, 240, 230))])
        for k in range(8):                                         # the audience in the dark, in front of the stage
            ax = 80 + k * 250
            blob(cv, ell(ax, 1095 + 10 * (k % 2), 120, 110, n=10), (10, 6, 16), w=4, seed=8870 + k, boil=0.8)
        if L0("C04") - 0.2 < T < L0("C05"):                        # Gary's glowing eye out in the dark
            k = ease((T - L0("C04") + 0.2) / 0.3)
            ex, ey = 1580, 1040
            blob(cv, ell(ex, ey, 46, 48, n=10), (20, 12, 30), w=4, seed=8890, boil=0.8)
            dots(cv, [(ex - 4, ey - 6)], 26 * k, (230, 255, 240))
            dots(cv, [(ex - 4, ey - 6)], 12 * k, INK)
            dots(cv, [(ex - 12, ey - 14)], 5 * k, P_["white"])
            glow(cv, ex, ey, 120, (200, 255, 230), a=int(60 * k))
            if T > L0("C04") + 0.2:
                caption(cv, "OOOOH!", ex - 40, ey - 80, T, L0("C04") + 0.2, size=64, fill=P_["cream"], font="bangers", seed=2021)
    else:                                                          # C06: Gary close-up in the dark, awestruck
        audience_cu(cv, T, gx=1000, gy=520, gs=1.15, spot=0.0, dark=0.0, seed=8800)
        darkness(cv, 150)
        glow(cv, 990, 500, 420, PHOS_GLOW, a=90)
        for k in range(5):
            sparkle(cv, 1000 + 230 * math.cos(k * 1.3 + T), 470 + 160 * math.sin(k * 2.1 + T), 12 + 4 * math.sin(T * 6 + k), P_["cream"], seed=2030 + k)


def T003_roll_titles(cv, t, T, A):
    cam = cam_lerp(dict(x=390, y=40, z=1.75), dict(x=390, y=40, z=1.9), t / 3.8)
    h, g = Hh(A, t), G(A, t)
    dark_stage(cv, T, cam, h, g)
    zx, zy = zee_eyes(A, cam)
    light_mask(cv, [(zx, zy, 900, 0.75, (200, 180, 255)), (zx - 900, zy, 700, 0.5, (210, 255, 235))], ambient=14, T=T)
    glow(cv, zx, zy, 380, (200, 170, 255), a=50)
    if t > 3.5:                                                    # flash out to the titles
        cv.drawRect(R(0, 0, W, H), paint(P_["white"], int(255 * min(1, (t - 3.5) / 0.25))))


# ===================================================================== TITLE
def T004_title(cv, t, T, A):
    cam = dict(x=0, y=0, z=1.0 + 0.012 * t)
    kinds = [("hand_bunny", 0.0), ("horse", 0.33), ("person", 0.66)]
    sh = []
    for kind, off in kinds:
        ph = (t * 0.09 + off) % 1.0
        sh.append((kind, 2100 - ph * 2300, 760, 1.6))
    cave_wall_view(cv, T, cam=cam, shadows=sh, prisoners=7, heads_y=1060)
    C = sets.Cam(cv, cam)
    with C.layer(0.9):
        w.halo(cv, 960, 470, [430, 350, 270], [P_["magenta"], P_["violet"], P_["orange"]], seed=1500)
        paint_text(cv, "BOXED", 960, 540, font="shrik", size=280, fill=P_["yellow"], ink_w=9, shadow=(14, 14), shadow_rgb=P_["magenta"], seed=1510,
                   wobble=2.6, reveal=float(np.clip(t / 0.9, 0, 1)), stagger=0.12, drips=1.3)
        if t > 1.1:
            paint_text(cv, "EPISODE FOUR", 960, 650, font="londrina", size=60, fill=P_["cream"], ink_w=4, shadow=(5, 5), seed=1520,
                       reveal=float(np.clip((t - 1.1) / 0.5, 0, 1)), stagger=0.05)
        if t > 1.6:
            paint_text(cv, "THE CAVE", 960, 790, font="shrik", size=150, fills=[P_["orange"], P_["hotpink"], P_["teal"], P_["acid"]], ink_w=7,
                       shadow=(9, 9), shadow_rgb=INK, seed=1530, reveal=float(np.clip((t - 1.6) / 0.8, 0, 1)), stagger=0.06, drips=1.0)
    for k in range(8):
        sparkle(cv, 960 + 520 * math.cos(k / 8 * 6.28 + t * 0.6), 520 + 300 * math.sin(k / 8 * 6.28 + t * 0.6), 14 + 5 * math.sin(t * 5 + k), P_["yellow"], seed=1540 + k)
    vignette(cv, a=150)
    if t < 0.25:
        cv.drawRect(R(0, 0, W, H), paint(P_["white"], int(255 * (1 - t / 0.25))))


# ===================================================================== INTRO
def T005_lights_up(cv, t, T, A):
    if t < 2.0:                                                    # three light banks clunk on
        banks = sum(1 for tb in (0.35, 0.95, 1.5) if t >= tb)
        if banks == 0:
            cam = dict(x=0, y=30, z=1.02)
            dark_stage(cv, T, cam, Hh(A, t), G(A, t))
            darkness(cv, 225)
            return
        studio(cv, T, A, dict(x=0, y=30, z=1.02), t)
        audience_rows(cv, T)
        fl = 1.0 if hsh(core.D * 3.1) > 0.3 else 0.7
        darkness(cv, int([0, 170, 90, 0][banks] * fl))
        return
    u = (t - 2.0) / (49.53 - 38.92)
    cam = cam_lerp(dict(x=0, y=30, z=1.02), dict(x=-140, y=0, z=1.25), u)
    studio(cv, T, A, cam, t)
    audience_rows(cv, T)
    tag_t = t - 2.6
    if 0 < tag_t < 5.0:
        from .shots_a import tag
        tag(cv, "THE HOST", "still a television", 90, 160, tag_t, 0.0, 5.0, P_["magenta"], "left", seed=1600)


def T006_host_recap(cv, t, T, A):
    cam = dict(x=-430, y=CAM_HOST["y"] - 10, z=1.65)
    studio(cv, T, A, cam, t)
    lt = T - L0("H02")
    beats = [(0.6, "HACKED IT", P_["acid"], "EP.1"), (2.4, "DID THE MATH", P_["teal"], "EP.2"), (4.4, "A DREAM?", P_["hotpink"], "EP.3")]
    rew = ease((lt - 5.6) / 1.0)
    for k, (tb, label, col, ep) in enumerate(beats):
        if lt < tb:
            continue
        k_in = pop(lt, tb, 0.35)
        x, y = 300 + 170 * (k % 2), 240 + k * 270
        cv.save(); cv.translate(x, y); cv.rotate(-6 + 6 * k + rew * 360 * (1 if k % 2 else -1)); cv.scale(k_in * (1 - rew * 0.9), k_in * (1 - rew * 0.9))
        w.tv(cv, 0, 0, 0.72, seed=1700 + k, body=[P_["orange"], P_["teal"], P_["magenta"]][k],
             screen=lambda c, r, k=k, col=col: _recap_screen(c, r, k, col, T))
        paint_text(cv, label, 0, 118, font="bangers", size=44, fill=col, ink_w=3.5, shadow=(4, 4), seed=1710 + k)
        paint_text(cv, ep, -96, -60, font="marker", size=26, fill=P_["cream"], ink_w=0, shadow=(2, 2), seed=1720 + k, streaks=False)
        cv.restore()
    if lt > 5.6:                                                   # rewinding 2400 years
        yr = int(lerp(2026, -375, ease((lt - 5.8) / 2.8)))
        txt = f"{yr} AD" if yr > 0 else f"{-yr} BC"
        caption(cv, "<< REWIND <<", 430, 380, lt, 5.7, size=64, fill=P_["cream"], font="bangers", seed=1730)
        paint_text(cv, txt, 430, 560, font="shrik", size=120, fill=P_["yellow"], ink_w=7, shadow=(9, 9), shadow_rgb=P_["magenta"], seed=1740 + (core.D % 3),
                   wobble=2.0)
        for k in range(6):
            yy = (lt * 900 + k * 180) % 1080
            cv.drawRect(R(60, yy, 820, yy + 6), paint(P_["white"], 60))


def _recap_screen(c, r, k, col, T):
    cx, cy, wd, ht = r
    c.drawRect(R(cx - wd, cy - ht, cx + wd, cy + ht), paint((10, 20, 30)))
    if k == 0:
        for j in range(5):
            paint_text(c, "".join("01"[int(hsh(j * 7 + i + core.D * 0.2) * 2)] for i in range(12)), cx, cy - ht / 2 + 22 + j * 18, font="marker", size=16,
                       fill=P_["acid"], ink_w=0, shadow=None, seed=j, streaks=False)
    elif k == 1:
        paint_text(c, "1 : 1,000,000,000", cx, cy + 8, font="bangers", size=26, fill=P_["teal"], ink_w=0, shadow=None, seed=3, streaks=False)
    else:
        for j in range(3):
            ph = (T * 0.5 + j / 3) % 1.0
            paint_text(c, "z", cx - 20 + j * 18, cy + 20 - ph * 50, font="bangers", size=20 + 14 * ph, fill=P_["hotpink"], ink_w=0, shadow=None, seed=j, streaks=False,
                       a=int(255 * (1 - ph)))


def T007_welcome(cv, t, T, A):
    if T < SLOTS["APPLAUSE"]["t0"] - 0.6:
        cam = cam_lerp(dict(x=40, y=40, z=1.25), dict(x=180, y=30, z=1.45), t / 5.0)
        studio(cv, T, A, cam, t)
        if T > L1("H03") - 1.6:                                   # spotlight swings onto Zee
            k = ease((T - (L1("H03") - 1.6)) / 0.5)
            zx, zy = zee_eyes(A, cam)
            p = skia.Paint(AntiAlias=True)
            p.setBlendMode(skia.BlendMode.kScreen)
            p.setShader(skia.GradientShader.MakeLinear([skia.Point(zx, -100), skia.Point(zx, zy + 500)], [core.C(P_["cream"], int(140 * k)), core.C(P_["yellow"], int(40 * k))]))
            cv.drawPath(poly_path([(zx - 60, -100), (zx + 60, -100), (zx + 360, zy + 520), (zx - 360, zy + 520)]), p)
    else:
        lt = T - (SLOTS["APPLAUSE"]["t0"] - 0.6)
        cam = cam_lerp(dict(x=0, y=30, z=1.02), dict(x=0, y=40, z=1.08), lt / 3.0)
        studio(cv, T, A, cam, t)
        audience_rows(cv, T, raise_k=0.0)
        for k in range(14):                                        # cheering: little hands + hearts pop out of the audience
            ph = (lt * 1.6 + k / 14) % 1.0
            x = 60 + k * 140
            y = 1040 - 120 * ph
            if k % 3 == 0:
                hp = [(x, y + 18), (x - 20, y), (x - 14, y - 14), (x, y - 6), (x + 14, y - 14), (x + 20, y)]
                blob(cv, hp, [P_["hotpink"], P_["red"], P_["magenta"]][k % 3], w=3, seed=1800 + k, boil=0.6, n=3, a=int(255 * (1 - ph)))
            else:
                sparkle(cv, x, y - 30, 12 * (1 - ph) + 4, P_["yellow"], seed=1820 + k, a=int(255 * (1 - ph)))


def T008_zee_bunny(cv, t, T, A):
    if T < L0("G00") - 0.15:
        cam = cam_lerp(CAM_ZEE, dict(x=CAM_ZEE["x"], y=CAM_ZEE["y"] - 10, z=2.0), t / 6.0)
        studio(cv, T, A, cam, t)
        tag_t = t - 0.4
        if 0 < tag_t < 4.5:
            from .shots_a import tag
            tag(cv, "ZEE", "guest · simulant", 1830, 950, tag_t, 0.0, 4.5, P_["teal"], "right", seed=1900)
    else:
        lt = T - (L0("G00") - 0.15)
        audience_cu(cv, T, gx=920, gy=470, gs=1.0, spot=0.6, seed=8800)
        x, y = 1160, 640 + 4 * math.sin(T * 2)                    # the framed bunny photo
        cv.save(); cv.translate(x, y); cv.rotate(-8 + 2 * math.sin(T * 1.3))
        blob(cv, rect_pts([(-90, -110), (90, -110), (90, 110), (-90, 110)], 3), P_["gold"], w=5, seed=1910, boil=0.8, n=3)
        cv.drawRect(R(-70, -90, 70, 90), paint(P_["cream"]))
        shadow_shape(cv, "hand_bunny", 0, 0, 0.62, T, rgb=(30, 16, 40), a=240, seed=1911, wobble=0.3)
        paint_text(cv, "RIP", 0, 84, font="marker", size=26, fill=P_["red"], ink_w=0, shadow=None, seed=1912, streaks=False)
        cv.restore()
        for k in range(2):                                         # tears
            ph = (lt * 1.4 + k * 0.5) % 1.0
            blob(cv, [(900 + k * 50, 480 + ph * 200), (912 + k * 50, 500 + ph * 200), (900 + k * 50, 512 + ph * 200), (888 + k * 50, 500 + ph * 200)], P_["mint"], w=3,
                 seed=1920 + k, boil=0.5, n=3, a=int(255 * (1 - ph)))


def T009_host_plato(cv, t, T, A):
    cam = cam_lerp(CAM_HOST, dict(x=CAM_HOST["x"] - 20, y=CAM_HOST["y"] - 20, z=1.95), t / 3.6)
    studio(cv, T, A, cam, t)


def T010_zee_allegory(cv, t, T, A):
    cam = cam_lerp(CAM_ZEE, dict(x=CAM_ZEE["x"], y=CAM_ZEE["y"] - 20, z=2.1), t / 10.2)
    lt = T - L0("Z02")
    dark_t = L1("Z02") - 2.2
    studio(cv, T, A, cam, t)
    if lt > 0.3:
        paint_text(cv, "THE ALLEGORY", 400, 250, font="shrik", size=86, fill=P_["yellow"], ink_w=6, shadow=(8, 8), shadow_rgb=P_["magenta"], seed=2000,
                   reveal=float(np.clip((lt - 0.3) / 0.5, 0, 1)), stagger=0.05)
        paint_text(cv, "OF THE CAVE", 400, 350, font="shrik", size=86, fills=[P_["orange"], P_["hotpink"], P_["teal"]], ink_w=6, shadow=(8, 8), seed=2001,
                   reveal=float(np.clip((lt - 0.7) / 0.5, 0, 1)), stagger=0.05)
    if lt > 3.1:
        caption(cv, "PLATO · THE REPUBLIC · c. 375 BC", 400, 440, lt, 3.1, size=40, fill=P_["cream"], font="londrina", seed=2002, dur=0.6)
    if T > dark_t:                                                # 'and it starts... in the dark' - lights die
        k = ease((T - dark_t) / 1.2)
        zx, zy = zee_eyes(A, cam)
        light_mask(cv, [(zx, zy, lerp(2400, 520, k), 1.0, (255, 255, 255))], ambient=int(lerp(255, 8, k)), T=T)


# ===================================================================== PART 1 talk beats
def T013_host_yikes(cv, t, T, A):
    cam = cam_lerp(dict(x=CAM_HOST["x"], y=CAM_HOST["y"], z=1.8), dict(x=CAM_HOST["x"], y=CAM_HOST["y"] - 10, z=1.9), t / 3.4)
    studio(cv, T, A, cam, t)


def T015_host_puppets(cv, t, T, A):
    cam = dict(x=CAM_HOST["x"] + 30, y=CAM_HOST["y"], z=1.75)
    studio(cv, T, A, cam, t)
    shadow_shape(cv, "hand_bunny", 1300, 380, 1.1, T, rgb=(40, 20, 60), a=int(120 * ease(t / 0.5)), seed=2100)


def T017_strange(cv, t, T, A):
    cam = cam_lerp(dict(x=40, y=40, z=1.3), dict(x=0, y=30, z=1.45), t / 3.5)
    studio(cv, T, A, cam, t)


def T018_like_ourselves(cv, t, T, A):
    if T < L0("H08") - 0.25:                                       # 'Like ourselves.' - dramatic ECU, firelight on her face
        cam = cam_lerp(dict(x=CAM_ZEE["x"], y=CAM_ZEE["y"] - 40, z=2.6), dict(x=CAM_ZEE["x"], y=CAM_ZEE["y"] - 40, z=2.75), t / 1.9)
        studio(cv, T, A, cam, t)
        zx, zy = zee_eyes(A, cam)
        light_mask(cv, [(zx - 200, zy + 300, 900, 1.0, (255, 170, 90)), (zx + 400, zy - 300, 700, 0.35, (150, 120, 255))], ambient=30, T=T)
    elif T < L0("Z10") - 0.15:
        cam = dict(x=CAM_HOST["x"], y=CAM_HOST["y"] - 30, z=2.2)
        studio(cv, T, A, cam, t)
    else:
        lt = T - (L0("Z10") - 0.15)
        cam = cam_lerp(CAM_ZEE, dict(x=CAM_ZEE["x"] + 60, y=CAM_ZEE["y"], z=1.95), lt / 4.8)
        studio(cv, T, A, cam, t)
        if lt > 0.6:                                               # the quote plaque
            k = pop(lt, 0.6, 0.4)
            cv.save(); cv.translate(470, 330); cv.rotate(-4); cv.scale(k, k)
            blob(cv, rect_pts([(-380, -150), (380, -150), (380, 150), (-380, 150)], 3), P_["cream"], w=6, seed=2200, boil=1.0, n=3,
                 shade=lambda c: stipple(c, P_["cream_sh"], (-380, -150, 380, 150), spacing=12, r=1.6, seed=2201))
            paint_text(cv, "“LIKE OURSELVES.”", 0, -10, font="shrik", size=78, fill=P_["red"], ink_w=5, shadow=(6, 6), shadow_rgb=P_["maroon"], seed=2202)
            paint_text(cv, "— PLATO, REPUBLIC VII", 0, 90, font="londrina", size=44, fill=P_["night"], ink_w=0, shadow=None, seed=2203, streaks=False)
            cv.restore()


def T019_classic_plato(cv, t, T, A):
    cam = cam_lerp(dict(x=CAM_HOST["x"], y=CAM_HOST["y"], z=1.75), dict(x=CAM_HOST["x"] - 30, y=CAM_HOST["y"], z=1.85), t / 3.9)
    studio(cv, T, A, cam, t)
    hx, hy = host_screen(A, cam)
    for k in range(3):                                             # nervous sweat drops off the TV
        ph = (t * 1.1 + k * 0.33) % 1.0
        x = hx + 300 + 30 * k
        y = hy - 120 + ph * 160
        blob(cv, [(x, y - 22), (x + 12, y + 4), (x, y + 14), (x - 12, y + 4)], P_["mint"], w=3.5, seed=2300 + k, boil=0.6, n=4, a=int(255 * (1 - ph)))


def T021_gameshow_idea(cv, t, T, A):
    lt = T - L0("H10")
    z = 1.75 + (0.35 * ease((lt - 3.0) / 0.4) if lt > 3.0 else 0.0)
    cam = dict(x=CAM_HOST["x"], y=CAM_HOST["y"], z=z)
    studio(cv, T, A, cam, t)
    if lt > 3.0:                                                   # 'GAME SHOW' - marquee bulbs explode around the frame
        k = ease((lt - 3.0) / 0.3)
        n = 28
        for i in range(n):
            u = i / n
            if u < 0.25:
                x, y = 40 + u / 0.25 * 1840, 40
            elif u < 0.5:
                x, y = 1880, 40 + (u - 0.25) / 0.25 * 1000
            elif u < 0.75:
                x, y = 1880 - (u - 0.5) / 0.25 * 1840, 1040
            else:
                x, y = 40, 1040 - (u - 0.75) / 0.25 * 1000
            on = (i + int(lt * 14)) % 3 == 0
            dots(cv, [(x, y)], 16 * k, P_["yellow"] if on else P_["orange"])
            if on:
                glow(cv, x, y, 50, P_["yellow"], a=int(120 * k))
        caption(cv, "GAME SHOW?!", 1420, 300, lt, 3.05, size=110, fill=P_["yellow"], font="shrik", seed=2400, shadow_rgb=P_["magenta"], dur=0.35)


# ===================================================================== PART 2 talk beats
def T024_volunteer(cv, t, T, A):
    if T < SLOTS["SPOTLIGHT"]["t0"]:
        cam = cam_lerp(dict(x=40, y=40, z=1.3), dict(x=-80, y=20, z=1.5), t / 2.0)
        studio(cv, T, A, cam, t)
    else:
        lt = T - SLOTS["SPOTLIGHT"]["t0"]
        sweep = 1.0 - ease(lt / 0.9)
        gx = 960 + sweep * 700 * math.sin(lt * 9)
        audience_cu(cv, T, gx=960, gy=520, gs=1.0, spot=0.0, dark=0.0, seed=8800)
        light_mask(cv, [(gx, 600, 560, 1.05, (255, 240, 210))], ambient=55, T=T)
        p = skia.Paint(AntiAlias=True)
        p.setBlendMode(skia.BlendMode.kScreen)
        p.setShader(skia.GradientShader.MakeLinear([skia.Point(gx, -100), skia.Point(gx, 980)], [core.C(P_["cream"], 200), core.C(P_["yellow"], 80)]))
        cv.drawPath(poly_path([(gx - 60, -100), (gx + 60, -100), (gx + 340, 1000), (gx - 340, 1000)]), p)
        if lt > 0.95:
            caption(cv, "!!", 1180, 330, lt, 0.95, size=120, fill=P_["yellow"], font="bangers", seed=2500, dur=0.2)


def T025_gary_eager(cv, t, T, A):
    audience_cu(cv, T, gx=960, gy=500, gs=1.12, spot=1.0, seed=8800, gary_kw=dict(wave=min(1.0, t / 0.4)))
    darkness(cv, 60)
    if T > L0("G01") + 2.6:
        thought = pop(T, L0("G01") + 2.6, 0.35)
        cv.save(); cv.translate(1430, 300); cv.scale(thought, thought)
        from .shots_ep4_base import thought_bubble
        thought_bubble(cv, 0, 0, 200, 130, seed=2600)
        for k in range(3):
            shadow_shape(cv, "bunny", -110 + k * 110, 0 + 10 * math.sin(T * 6 + k), 0.45, T, rgb=(40, 20, 60), seed=2601 + k)
        cv.restore()


def T028_relatable(cv, t, T, A):
    cam = cam_lerp(dict(x=CAM_HOST["x"], y=CAM_HOST["y"] - 30, z=1.9), dict(x=CAM_HOST["x"], y=CAM_HOST["y"] - 40, z=2.15), t / 2.4)
    studio(cv, T, A, cam, t)


def T032_not_quite(cv, t, T, A):
    if T < L0("Z20") - 0.2:
        cam = cam_lerp(dict(x=40, y=40, z=1.3), dict(x=-60, y=20, z=1.45), t / 3.6)
        studio(cv, T, A, cam, t, host=dict(face="heart"))
    elif T < L0("H14") - 0.1:                                      # 'Not quite.' crash zoom
        lt = T - (L0("Z20") - 0.2)
        z = 1.9 + 0.8 * ease(lt / 0.25)
        cam = dict(x=CAM_ZEE["x"], y=CAM_ZEE["y"] - 40, z=z)
        studio(cv, T, A, cam, t)
        cv.drawRect(R(0, 0, W, H), paint(P_["red"], 40))
        vignette(cv, a=220, inner=0.3)
    else:
        cam = shake(dict(x=CAM_HOST["x"], y=CAM_HOST["y"], z=1.9), 14, T)
        studio(cv, T, A, cam, t)


def T034_bumper(cv, t, T, A):
    w.field(cv, P_["night"])
    w.sunburst(cv, 960, 540, 2400, 24, [P_["violet"], P_["night"]], rot_deg=t * 40, seed=3400)
    w.halo(cv, 960, 540, [420, 330, 240], [P_["magenta"], P_["orange"], P_["yellow"]], seed=3401)
    paint_text(cv, "BOXED", 960, 610, font="shrik", size=240, fill=P_["yellow"], ink_w=8, shadow=(12, 12), shadow_rgb=P_["magenta"], seed=3402,
               reveal=float(np.clip(t / 0.5, 0, 1)), stagger=0.08, drips=1.0)
    bx = -300 + (t / 4.0) * 2500                                   # the bunny hops across
    by = 990 - 110 * abs(math.sin(t * 4.0))
    shadow_shape(cv, "hand_bunny", bx, by, 0.8, T, rgb=(20, 10, 30), a=240, seed=3403)
    caption(cv, "THE CAVE · PART 2", 960, 760, t, 0.6, size=56, fill=P_["cream"], seed=3404)


def T035_back(cv, t, T, A):
    cam = cam_lerp(dict(x=0, y=30, z=1.1), dict(x=CAM_HOST["x"] + 60, y=CAM_HOST["y"], z=1.6), t / 2.0)
    studio(cv, T, A, cam, t)


def T039_tough_crowd(cv, t, T, A):
    cam = dict(x=CAM_HOST["x"], y=CAM_HOST["y"] - 10, z=1.85)
    studio(cv, T, A, cam, t)


def T041_host_kill(cv, t, T, A):
    cam = shake(dict(x=CAM_HOST["x"], y=CAM_HOST["y"], z=1.8 + 0.2 * ease(t / 0.2)), 16 * (1 - ease(t / 2.5)), T)
    studio(cv, T, A, cam, t)
    cv.drawRect(R(0, 0, W, H), paint(P_["red"], int(70 * (1 - ease(t / 1.0)))))


def T043_cave_fought(cv, t, T, A):
    cam = cam_lerp(dict(x=40, y=40, z=1.3), dict(x=60, y=40, z=1.42), t / 5.4)
    studio(cv, T, A, cam, t)
    hx, hy = host_screen(A, cam)
    zx, zy = zee_eyes(A, cam)
    light_mask(cv, [(hx, hy, 900, 0.9, (220, 255, 240)), (zx, zy, 800, 0.85, (255, 210, 190)), (960, 300, 1400, 0.35, (255, 255, 255))], ambient=50, T=T)


# ===================================================================== PART 4: the realisation + meltdown
def T045_flat_rectangle(cv, t, T, A):
    if T < L0("Z27") - 0.1:
        lt = T - L0("H22")
        z = 1.8 + 1.4 * ease(lt / 3.5)
        cam = dict(x=CAM_HOST["x"] - 30, y=CAM_HOST["y"] - 80 - 40 * ease(lt / 3.5), z=z)
        studio(cv, T, A, cam, t)
        vignette(cv, a=int(120 + 80 * ease(lt / 3.5)), inner=0.35)
    else:
        cam = dict(x=CAM_ZEE["x"], y=CAM_ZEE["y"] - 10, z=2.0)
        studio(cv, T, A, cam, t)


def T046_meltdown(cv, t, T, A):
    if T < L0("Z28") - 0.15:                                       # H23 panic
        lt = T - L0("H23")
        cam = shake(dict(x=CAM_HOST["x"] + 40, y=CAM_HOST["y"] + 10, z=1.6), 10 + 8 * math.sin(lt * 3), T, seed=5)
        h = Hh(A, t)
        studio_bg = int(lt * 6) % 2 == 0 and lt > 2.2 and lt < 4.6
        if lt > 2.2 and lt < 4.6:                                  # 'I'm the WALL!' - the world flashes into a cave wall
            cave_wall_view(cv, T, cam=dict(x=0, y=0, z=1.05), shadows=[("person", 960, 480, 2.6)], prisoners=0)
            C = sets.Cam(cv, cam)
            with C.layer(1.0):
                draw_host(cv, h)
                sets.desk(cv, 640, 912, 1.0, seed=437)
        else:
            sets.talkshow(cv, T, cam, host=h, guest=G(A, t))
        if lt > 5.0:                                               # 'AM I THE PUPPETS?!' - marionette strings from above
            C = sets.Cam(cv, cam)
            with C.layer(1.0):
                hands = []
                for side, pre in ((-1, "aL"), (1, "aR")):
                    from .zee import arm_points
                    sx, sy = side * 74, -370
                    (ex, ey), (wx, wy), _ = arm_points(sx, sy, h[pre + "_sh"], h[pre + "_el"], 100, 96)
                    hands.append((h["x"] + wx * h["s"], h["y"] + wy * h["s"]))
                hx, hy = host_screen(A, dict(x=0, y=0, z=1.0))
                for (x, y) in hands + [(640, 930 - 700 * 0.78)]:
                    line(cv, [(x, y), (x + 10 * math.sin(T * 3), -300)], 2.4, P_["cream"], seed=4600 + int(x), boil=0.3, n=2, taper=(0, 0))
                blob(cv, rect_pts([(420, -60), (860, -60), (860, -20), (420, -20)], 3), (120, 70, 40), w=4, seed=4610, boil=0.6, n=3)
        cv.drawRect(R(0, 0, W, H), paint(P_["magenta"], int(40 * (0.5 + 0.5 * math.sin(lt * 18)))))
    elif T < L0("H24") - 0.15:                                     # Z28 deadpan
        lt = T - (L0("Z28") - 0.15)
        cam = dict(x=CAM_ZEE["x"], y=CAM_ZEE["y"] - 10, z=1.95)
        studio(cv, T, A, cam, t)
        icons = [(1.1, "FIRE", P_["orange"]), (2.3, "WALL", P_["peach"]), (3.3, "SHADOWS", P_["violet"])]
        for k, (tb, label, col) in enumerate(icons):
            if lt < tb:
                continue
            kk = pop(lt, tb, 0.3)
            x, y = 300, 200 + k * 290
            cv.save(); cv.translate(x, y); cv.scale(kk, kk)
            blob(cv, ell(0, 0, 82, 82, n=12), col, w=5, seed=4700 + k, boil=0.9)
            if k == 0:
                from .shots_ep4_base import cave_fire
                cave_fire(cv, 0, 40, 0.3, T, seed=4710, logs=False)
            elif k == 1:
                for j in range(3):
                    line(cv, [(-60, -30 + j * 30), (60, -30 + j * 30)], 4, mix(col, INK, 0.4), seed=4720 + j, boil=0.5, n=2)
            else:
                shadow_shape(cv, "person", 0, 0, 0.6, T, rgb=(30, 12, 50), seed=4730)
            paint_text(cv, label, 0, 136, font="bangers", size=46, fill=P_["cream"], ink_w=3.5, shadow=(4, 4), seed=4740 + k)
            cv.restore()
        if lt > 4.6:
            caption(cv, "A VERY EFFICIENT CAVE", 640, 1010, lt, 4.6, size=60, fill=P_["yellow"], font="bangers", seed=4750)
    else:                                                          # H24 wail: the set cracks into rock
        lt = T - (L0("H24") - 0.15)
        cam = shake(dict(x=CAM_HOST["x"], y=CAM_HOST["y"], z=1.7 - 0.25 * ease(lt / 3.5)), 12, T, seed=9)
        studio(cv, T, A, cam, t)
        crack = ease(lt / 1.2)
        for k in range(8):
            a = k / 8 * 2 * math.pi + 0.3
            pts = [(960, 540)]
            for j in range(5):
                rr = (j + 1) * 230 * crack
                pts.append((960 + rr * math.cos(a + 0.2 * math.sin(j * 3 + k)), 540 + rr * math.sin(a + 0.2 * math.sin(j * 2 + k))))
            line(cv, pts, 7, INK, seed=4800 + k, boil=0.8, n=5, taper=(0.05, 0.6))
        cv.drawRect(R(0, 0, W, H), paint((80, 30, 120), int(90 * crack)))


def cartoon_door(cv, x, y, s, open_amt=0.2, seed=0, rgb=None, sign=True):
    """A chunky cartoon door standing at (x, y = bottom centre): arched frame, light blasting out of the gap, knob, EXIT sign."""
    rgb = rgb or P_["orange"]
    wd, ht = 170 * s, 320 * s
    frame = [(x - wd / 2 - 22 * s, y), (x - wd / 2 - 22 * s, y - ht), (x - wd / 2, y - ht - 40 * s), (x, y - ht - 58 * s), (x + wd / 2, y - ht - 40 * s),
             (x + wd / 2 + 22 * s, y - ht), (x + wd / 2 + 22 * s, y)]
    blob(cv, frame, P_["maroon"], w=6, seed=seed, boil=0.8, n=4)
    opening = [(x - wd / 2, y), (x - wd / 2, y - ht), (x, y - ht - 34 * s), (x + wd / 2, y - ht), (x + wd / 2, y)]
    cv.drawPath(poly_path(cr_closed(opening, 4)), paint(P_["yellow"]))
    glow(cv, x, y - ht * 0.5, 260 * s, P_["yellow"], a=110)
    ox = x - wd / 2 + wd * (1 - open_amt * 0.75)
    panel = [(x - wd / 2, y), (x - wd / 2, y - ht), (ox, y - ht - 22 * s * open_amt - 10 * s), (ox, y + 10 * s * open_amt)]
    blob(cv, panel, rgb, w=5, seed=seed + 1, boil=0.7, n=3,
         shade=lambda c: [c.drawRect(R(x - wd / 2 + 14 * s, y - ht + 30 * s + k * 120 * s, ox - 14 * s, y - ht + 120 * s + k * 120 * s), paint(mix(rgb, INK, 0.2))) for k in range(2)])
    dots(cv, [(x - wd / 2 + (ox - (x - wd / 2)) * 0.82, y - ht * 0.48)], 9 * s, P_["gold"])
    if sign:
        blob(cv, rect_pts([(x - 70 * s, y - ht - 120 * s), (x + 70 * s, y - ht - 120 * s), (x + 70 * s, y - ht - 72 * s), (x - 70 * s, y - ht - 72 * s)], 3),
             P_["red"], w=4, seed=seed + 2, boil=0.6, n=3)
        paint_text(cv, "EXIT?", x, y - ht - 80 * s, font="bangers", size=40 * s, fill=P_["cream"], ink_w=0, shadow=None, seed=seed + 3, streaks=False)


def T048_door(cv, t, T, A):
    cam = dict(x=CAM_HOST["x"] + 40, y=CAM_HOST["y"] - 20, z=1.55)
    studio(cv, T, A, cam, t)
    lt = T - L0("H25")
    if lt > 2.9:                                                   # 'Show me a door!' - doors slam in
        for k, (x, y, sc) in enumerate(((1520, 1060, 1.1), (230, 1060, 1.0), (1790, 700, 0.62), (130, 560, 0.5))):
            tb = 3.0 + k * 0.28
            if lt < tb:
                continue
            kk = pop(lt, tb, 0.3)
            cv.save(); cv.translate(x, y); cv.scale(1.0 / max(0.2, kk) ** 0.3 * kk, kk * (1.0 + 0.15 * math.sin((lt - tb) * 20) * math.exp(-(lt - tb) * 4)))
            cartoon_door(cv, 0, 0, sc, open_amt=0.15 + 0.1 * math.sin(T * 3 + k), seed=4900 + k * 5, rgb=[P_["orange"], P_["teal"], P_["hotpink"], P_["acid"]][k])
            cv.restore()


# ===================================================================== PART 5 talk beats
def T050_thats_it(cv, t, T, A):
    if T < L0("Z33") - 0.15:
        cam = dict(x=CAM_HOST["x"] + 20, y=CAM_HOST["y"], z=1.75)
        studio(cv, T, A, cam, t)
    elif T < L0("H27") - 0.15:
        lt = T - (L0("Z33") - 0.15)
        cam = cam_lerp(CAM_ZEE, dict(x=CAM_ZEE["x"], y=CAM_ZEE["y"] - 20, z=2.15), lt / 9.5)
        studio(cv, T, A, cam, t)
        if lt > 6.2:                                               # 'what's casting this shadow?' - a mystery light from behind camera
            k = ease((lt - 6.2) / 1.0)
            zx, zy = zee_eyes(A, cam)
            light_mask(cv, [(zx + 200, zy - 100, 1300, 1.0, (255, 240, 200))], ambient=int(lerp(255, 120, k)), T=T)
            shadow_shape(cv, "person", 1500, 520, 2.4, T, rgb=(30, 10, 50), a=int(90 * k), seed=5000)
            caption(cv, "?", 1650, 360, lt, 6.6, size=160, fill=P_["yellow"], font="shrik", seed=5001)
    else:
        cam = cam_lerp(dict(x=40, y=40, z=1.3), dict(x=-80, y=20, z=1.45), (T - L0("H27")) / 2.0)
        studio(cv, T, A, cam, t)


# ===================================================================== TAG + ENDCARD + STINGER
def T053_tag(cv, t, T, A):
    if T < L0("G08") - 0.15:
        cam = dict(x=40, y=40, z=1.3)
        sunny_set(cv, T, cam, host=Hh(A, t), guest=G(A, t), gary_xy=(1730, 840, 0.4))
    elif T < L0("H30") - 0.15:                                     # Gary in shades
        lt = T - (L0("G08") - 0.15)
        cam = dict(x=40, y=40, z=1.0)
        C = sets.Cam(cv, cam)
        sunny_set(cv, T, dict(x=300, y=-60, z=1.6), host=None, guest=None)
        gary(cv, 960, 480, 1.05, T, seed=8800 + 900)
        shades(cv, 956, 457, 1.05)
        for k in range(6):
            sparkle(cv, 960 + 330 * math.cos(k + T), 440 + 220 * math.sin(k * 1.7 + T), 14, P_["yellow"], seed=5300 + k)
        if lt > 2.0:
            caption(cv, "10/10", 1480, 860, lt, 2.0, size=130, fill=P_["acid"], font="shrik", seed=5310, shadow_rgb=P_["magenta"])
    elif T < L0("Z35") - 0.1:
        lt = T - (L0("H30") - 0.15)
        cam = cam_lerp(dict(x=CAM_HOST["x"] + 80, y=CAM_HOST["y"], z=1.55), dict(x=CAM_HOST["x"] + 40, y=CAM_HOST["y"] - 20, z=1.7), lt / 8.0)
        sunny_set(cv, T, cam, host=Hh(A, t), guest=G(A, t))
    elif T < L0("H31") - 0.05:
        cam = dict(x=CAM_ZEE["x"], y=CAM_ZEE["y"] - 10, z=1.95)
        sunny_set(cv, T, cam, host=Hh(A, t), guest=G(A, t))
    else:
        lt = T - (L0("H31") - 0.05)
        cam = cam_lerp(dict(x=40, y=40, z=1.3), dict(x=0, y=30, z=1.05), lt / 1.4)
        sunny_set(cv, T, cam, host=Hh(A, t), guest=G(A, t), gary_xy=(1730, 840, 0.4))
        for k in range(16):
            ph = (lt * 0.8 + k / 16) % 1.0
            sparkle(cv, 100 + k * 115, 1000 - 900 * ph, 10 + 8 * (1 - ph), [P_["yellow"], P_["hotpink"], P_["teal"]][k % 3], seed=5400 + k)


def T054_endcard(cv, t, T, A):
    w.field(cv, P_["hotpink"])
    w.sunburst(cv, 960, 1300, 2600, 30, [P_["magenta"], P_["hotpink"]], rot_deg=t * 4, seed=5500)
    w.halo(cv, 960, 300, [250, 190, 130], [P_["violet"], P_["orange"], P_["yellow"]], seed=5501)
    paint_text(cv, "BOXED", 960, 350, font="shrik", size=200, fill=P_["yellow"], ink_w=8, shadow=(12, 12), shadow_rgb=P_["magenta"], seed=5502,
               reveal=float(np.clip(t / 0.6, 0, 1)), stagger=0.08, drips=1.0)
    paint_text(cv, "EPISODE 4 · THE CAVE", 960, 440, font="londrina", size=56, fill=P_["cream"], ink_w=4, shadow=(5, 5), seed=5503,
               reveal=float(np.clip((t - 0.4) / 0.6, 0, 1)), stagger=0.03)
    credits = ["Adapted from Plato's Republic, Book VII (c. 375 BC) — the Allegory of the Cave",
               "Quoted lines after Benjamin Jowett's translation (1871)",
               "Original characters · voices, music & sound generated with ElevenLabs"]
    for k, c in enumerate(credits):
        if t > 1.0 + k * 0.3:
            paint_text(cv, c, 960, 540 + k * 50, font="marker", size=30, fill=P_["night"], ink_w=0, shadow=None, seed=5510 + k, streaks=False, wobble=0.5)
    if t > 2.2:
        paint_text(cv, "STAY BOXED.", 960, 770, font="shrik", size=110, fill=P_["acid"], ink_w=7, shadow=(9, 9), shadow_rgb=P_["night"], seed=5520,
                   reveal=float(np.clip((t - 2.2) / 0.6, 0, 1)), stagger=0.06)
        paint_text(cv, "(and turn around)", 960, 840, font="caveat", size=48, fill=P_["night"], ink_w=0, shadow=None, seed=5521, streaks=False,
                   reveal=float(np.clip((t - 3.0) / 0.6, 0, 1)))
    from .zee import DEFAULTS as ZD
    zp = dict(ZD); zp.update(x=330, y=1180, s=0.62, legs=True, smile=0.8, aR_sh=-60 - 14 * math.sin(t * 8), aR_el=-40, aR_pose="open", px=0.3, py=0.1,
                         antL=(4 * math.sin(t * 3), 3 * math.sin(t * 4)), antR=(4 * math.sin(t * 3 + 1), 3 * math.sin(t * 4 + 1)))
    draw_zee(cv, zp)
    draw_host(cv, dict(x=1610, y=1150, s=0.6, legs=True, aL_sh=-120 - 14 * math.sin(t * 8), aL_el=40, aL_pose="open", smile=0.7, px=-0.3))
    gary(cv, 1830, 860, 0.36, T, seed=8800 + 900, wave=1.0)
    shades(cv, 1829, 852, 0.36)


def T055_stinger(cv, t, T, A):
    lt = t
    z = 1.0
    sh = [("bunny", 960, 470, 0.0)]
    cave_wall_view(cv, T, cam=dict(x=0, y=0, z=1.0), shadows=[], prisoners=7, heads_y=1030)
    k_logo = 1.0 - ease((lt - 0.2) / 2.0) * 0.0
    paint_text(cv, "BOXED", 960, 420, font="shrik", size=210, fill=(110, 26, 60), ink_w=0, shadow=None, seed=5600, streaks=False, wobble=1.5, a=220)
    if T > L0("G09") - 0.1:                                        # the bunny comes back
        kk = ease((T - (L0("G09") - 0.1)) / 0.7)
        bx = lerp(2200, 1420, kk)
        by = 620 - 120 * abs(math.sin((T - L0("G09")) * 4.0)) * kk
        shadow_shape(cv, "hand_bunny", bx, by, 1.5, T, rgb=CV_SHADOW_DARK, a=235, seed=5610)
    vignette(cv, a=200, inner=0.4)


CV_SHADOW_DARK = (90, 16, 52)
