"""BOXED sets: the parallax camera, the shared cosmic sky and the floating talk-show stage.

Cam(cv, cam).layer(p) — cam = dict(x, y, z[, rot]): (x, y) is the world offset (at parallax 1) of the point the camera
centres, z the zoom. A layer with parallax p moves by p*(x, y) and zooms by 1 + (z-1)*p, and compensates the pen
weight (core.INKMUL ~ zoom^-0.5) so zoomed layers keep a hand-inked line rather than ballooning.
"""
import math
from contextlib import contextmanager
import numpy as np
import skia
from .core import (PAL, INK, W, H, paint, blob, line, brush, ell, dots, stipple, mix, poly_path, cr_closed, cr_open,
                   rect_pts, jit, hsh)
from . import core
from . import world as w
from .letters import paint_text

P_ = PAL


class Cam:
    def __init__(self, cv, cam):
        cam = cam or {}
        self.cv = cv
        self.x = float(cam.get("x", 0.0))
        self.y = float(cam.get("y", 0.0))
        self.z = float(cam.get("z", 1.0))
        self.rot = float(cam.get("rot", 0.0))

    def zoom(self, p):
        return 1.0 + (self.z - 1.0) * p

    def to_screen(self, X, Y, p=1.0):
        zf = self.zoom(p)
        return W / 2 + zf * (X - W / 2 - self.x * p), H / 2 + zf * (Y - H / 2 - self.y * p)

    @contextmanager
    def layer(self, p):
        cv = self.cv
        zf = self.zoom(p)
        cv.save()
        cv.translate(W / 2, H / 2)
        if self.rot:
            cv.rotate(self.rot * p)
        cv.scale(zf, zf)
        cv.translate(-W / 2 - self.x * p, -H / 2 - self.y * p)
        old = core.INKMUL
        core.INKMUL = old / max(zf, 0.05) ** 0.5
        try:
            yield self
        finally:
            core.INKMUL = old
            cv.restore()


def cosmos(cv, t, cam, palette="dusk", seed=1, planet_xy=(1560, 210), extras=True):
    """The shared psychedelic sky: wavy colour bands, a sunburst, a ringed planet with a face, a skull moon,
    a cosmic ribbon, star speckle and drifting creatures."""
    C = Cam(cv, cam)
    pals = {
        "dusk": [P_["night"], P_["violet"], P_["magenta"], P_["orange"], P_["yellow"]],
        "deep": [P_["void"], P_["deepblue"], P_["violet"], P_["blue"], P_["teal"]],
        "acid": [P_["maroon"], P_["red"], P_["orange"], P_["acid"], P_["yellow"]],
    }
    bands = pals[palette]
    with C.layer(0.15):
        w.field(cv, bands[0])
        w.sunburst(cv, 960, 1250, 2200, 28, [mix(bands[0], bands[1], 0.55), bands[0]], rot_deg=t * 2.5, seed=seed)
        for k, c in enumerate(bands[1:]):
            w.wavy_band(cv, 640 + k * 120, 900, c, amp=26 + k * 6, freq=1.4 + k * 0.35, seed=seed + k * 3)
        w.stars(cv, seed + 10, (-200, -200, W + 200, 760), n=260, big=12)
        w.floaters(cv, seed + 15, (-100, 0, W + 100, 640), n=16, t=t)
    with C.layer(0.3):
        w.skull_moon(cv, 250 + 10 * math.sin(t * 0.3), 170, 82, seed=seed + 20)
        px, py = planet_xy
        w.planet(cv, px, py, 260, P_["orange"], bands=[(-0.55, 0.22, P_["red"]), (-0.1, 0.18, P_["yellow"]), (0.32, 0.24, P_["magenta"])],
                 ring=dict(rx=1.75, ry=0.33, rgb=P_["teal"], rgb2=P_["cream"], tilt=-16),
                 face=dict(look=(-0.6 + 0.5 * math.sin(t * 0.35), 0.3 + 0.2 * math.sin(t * 0.21)), smile=0.4 + 0.1 * math.sin(t * 0.5),
                           lids=0.45 if (t % 5.3) > 0.18 else 0.98, lid_rgb=P_["orange"]),
                 seed=seed + 30)
        w.planet(cv, 760, 120, 46, P_["acid"], bands=[(-0.2, 0.3, P_["teal"])], seed=seed + 40, crater=False)
    with C.layer(0.45):
        w.ribbon(cv, [(-200, 980), (300, 760), (760, 820), (1180, 560), (1600, 640), (2150, 380)], 150,
                 [P_["magenta"], P_["orange"], P_["yellow"], P_["night"], P_["teal"]], flow=t * 0.9, seed=seed + 50, starband=3)
        if extras:
            w.eye_bat(cv, 520 + 60 * math.sin(t * 0.5), 300 + 26 * math.sin(t * 1.3), 0.9, t * 1.6, seed=seed + 60)
            w.jelly(cv, 1180 + 30 * math.sin(t * 0.4), 260 + 20 * math.sin(t * 0.7), 0.8, t * 0.8, seed=seed + 70)
    with C.layer(0.6):
        w.hills(cv, 930, 120, [P_["teal"], P_["acid"], P_["yellow"], P_["orange"], P_["red"]], seed=seed + 80, freq=1.6, spacing=24)
        w.pyramid(cv, 1700, 780, 0.55, look=(-0.5, 0.2), seed=seed + 90, rays=True)
        w.wizard(cv, 170, 860, 0.5, seed=seed + 100, phase=t * 0.5)
        w.mushroom(cv, 1460, 900, 0.55, seed=seed + 110)
        w.eyeball_walker(cv, 360 + (t * 40) % 300, 860, 0.5, t * 1.4, seed=seed + 120)


def talkshow(cv, t, cam, host=None, guest=None, sign=1.0, seed=7):
    """The floating talk-show stage: host behind a curved desk (left), guest on the couch (right)."""
    from .zee import draw_zee
    from .cast import draw_host
    cosmos(cv, t, cam, "dusk", seed)
    C = Cam(cv, cam)
    with C.layer(0.85):
        w.island(cv, 960, 905, 820, 120, seed=seed + 200, top=P_["violet"], depth=240,
                 strata=[P_["orange"], P_["red"], P_["maroon"], P_["night"]])
        w.rug(cv, 960, 905, 640, 92, seed=seed + 210)
        if sign > 0:
            for k in range(7):
                a = int(70 * sign)
                blob(cv, ell(960, 140, 300 + k * 6, 92 + k * 6, n=12), P_["hotpink"], w=0, seed=seed + 300 + k, boil=2, misreg=(0, 0), a=max(0, a - k * 9))
            paint_text(cv, "BOXED", 960, 186, font="shrik", size=150, fill=P_["yellow"], ink_w=7, shadow=(9, 9), shadow_rgb=P_["magenta"],
                       seed=seed + 310, wobble=2.0, reveal=sign, drips=1)
    with C.layer(1.0):
        w.couch(cv, 1350, 905, 0.82, seed=seed + 400, rgb=P_["orange"], rgb2=P_["red"], part="back")
        w.lamp(cv, 1760, 905, 1.0, seed=seed + 410)
        w.plant(cv, 190, 905, 0.95, seed=seed + 420, phase=t * 0.3)
        if host is not None:
            draw_host(cv, host)
        desk(cv, 640, 912, 1.0, seed=seed + 430)
        mug(cv, 858, 744, 1.0, t, seed=seed + 440)
        if guest is not None:
            draw_zee(cv, guest)
        w.couch(cv, 1350, 905, 0.82, seed=seed + 400, rgb=P_["orange"], rgb2=P_["red"], part="front")
        side_table(cv, 1690, 912, 1.0, seed=seed + 450)
        lava(cv, 1690, 812, 1.0, t, seed=seed + 460)


def desk(cv, x, y, s=1.0, seed=0, top_rgb=None, body_rgb=None):
    """The curved host desk: orange panelled pill with a red end, an eye emblem, and a long yellow plank top.
    (x, y) = bottom centre on the stage floor; the plank top sits at y - 168*s."""
    top_rgb = top_rgb or P_["yellow"]
    body_rgb = body_rgb or P_["orange"]
    hw, ht = 360 * s, 168 * s
    body = [(x - hw, y - ht + 8 * s), (x - hw * 0.5, y - ht + 4 * s), (x + hw * 0.5, y - ht + 4 * s), (x + hw, y - ht + 8 * s),
            (x + hw + 18 * s, y - ht * 0.5), (x + hw - 10 * s, y - 6 * s), (x + hw * 0.5, y), (x - hw * 0.5, y), (x - hw + 10 * s, y - 6 * s),
            (x - hw - 18 * s, y - ht * 0.5)]

    def sh(c):
        c.drawPath(poly_path([(x + hw * 0.62, y - ht - 20 * s), (x + hw + 40 * s, y - ht - 20 * s), (x + hw + 40 * s, y + 10 * s), (x + hw * 0.58, y + 10 * s)]),
                   paint(P_["red"]))
        for k in range(9):
            xx = x - hw * 0.86 + k * hw * 0.215
            c.drawLine(xx, y - ht + 16 * s, xx + 3 * s, y - 10 * s, paint(mix(body_rgb, P_["red"], 0.75), stroke=3.2 * s + 0.8))
        stipple(c, mix(body_rgb, P_["red"], 0.6), (x - hw - 20 * s, y - ht, x + hw + 20 * s, y), spacing=13 * s + 2, r=1.5 * s + 0.4, seed=seed + 3,
                fn=lambda X, Y: np.clip((Y - (y - ht * 0.6)) / (ht * 0.6), 0, 1) * 0.8)
    blob(cv, body, body_rgb, w=6.5, seed=seed, boil=1.1, n=5, shade=sh)
    ex, ey = x - 10 * s, y - ht * 0.5                                       # eye emblem
    eye = [(ex - 74 * s, ey), (ex - 30 * s, ey - 30 * s), (ex + 30 * s, ey - 30 * s), (ex + 74 * s, ey), (ex + 30 * s, ey + 30 * s), (ex - 30 * s, ey + 30 * s)]
    blob(cv, eye, P_["yellow"], w=5, seed=seed + 5, boil=0.9, n=5)
    look = math.sin(core.D * 0.05) * 14 * s
    dots(cv, [(ex + look, ey)], 22 * s, INK)
    dots(cv, [(ex + look - 7 * s, ey - 7 * s)], 6 * s, P_["white"])
    top = [(x - hw - 160 * s, y - ht + 2 * s), (x - hw * 0.6, y - ht - 16 * s), (x + hw * 0.6, y - ht - 16 * s), (x + hw + 170 * s, y - ht + 2 * s),
           (x + hw * 0.6, y - ht + 12 * s), (x - hw * 0.6, y - ht + 12 * s)]
    blob(cv, top, top_rgb, w=5.5, seed=seed + 7, boil=1.0, n=6,
         shade=lambda c: c.drawRect(skia.Rect.MakeLTRB(x - hw - 200 * s, y - ht + 3 * s, x + hw + 200 * s, y - ht + 20 * s), paint(P_["gold"])))


def mug(cv, x, y, s, t, seed=0):
    """Teal mug with a loop handle and curling steam. (x, y) = base centre."""
    m = [(x - 34 * s, y - 70 * s), (x + 34 * s, y - 70 * s), (x + 30 * s, y - 6 * s), (x + 18 * s, y), (x - 18 * s, y), (x - 30 * s, y - 6 * s)]
    blob(cv, ell(x + 40 * s, y - 38 * s, 20 * s, 18 * s, n=10), None, w=6.5, seed=seed + 1, boil=0.6)
    blob(cv, m, P_["teal"], w=5.5, seed=seed, boil=0.8, n=4,
         shade=lambda c: c.drawRect(skia.Rect.MakeLTRB(x + 12 * s, y - 80 * s, x + 50 * s, y + 4 * s), paint(P_["tealdk"])))
    for k in range(3):
        ph = t * 1.4 + k * 2.1
        xs = x - 14 * s + k * 14 * s
        pts = [(xs + 6 * s * math.sin(ph + u * 2.2), y - 84 * s - u * 26 * s) for u in range(5)]
        line(cv, pts, 2.6, P_["white"], seed=seed + 4 + k, boil=0.6, n=5, taper=(0.4, 0.6), a=150)


def side_table(cv, x, y, s=1.0, seed=0):
    """Teal stippled drum table. (x, y) = bottom centre; the top sits at y - 100*s."""
    hw = 74 * s
    body = [(x - hw, y - 100 * s), (x + hw, y - 100 * s), (x + hw - 6 * s, y - 4 * s), (x - hw + 6 * s, y - 4 * s)]
    blob(cv, rect_pts(body, 3), P_["teal"], w=5.5, seed=seed, boil=0.9, n=3,
         shade=lambda c: (stipple(c, P_["tealdk"], (x - hw, y - 100 * s, x + hw, y), spacing=10 * s + 1, r=2.2 * s + 0.4, seed=seed + 1),
                          c.drawRect(skia.Rect.MakeLTRB(x + hw * 0.45, y - 110 * s, x + hw + 10 * s, y + 4 * s), paint(P_["tealdk"], 150))))
    blob(cv, ell(x, y - 100 * s, hw + 8 * s, 18 * s, n=12), mix(P_["teal"], P_["white"], 0.15), w=5.5, seed=seed + 2, boil=0.8)


def lava(cv, x, y, s, t, seed=0):
    """Lava lamp: yellow base cone, a tapered pink glass with orange blobs rising, a pointed yellow cap. (x, y) = base."""
    base = [(x - 44 * s, y), (x - 26 * s, y - 50 * s), (x + 26 * s, y - 50 * s), (x + 44 * s, y)]
    blob(cv, base, P_["yellow"], w=5, seed=seed, boil=0.7, n=3,
         shade=lambda c: c.drawRect(skia.Rect.MakeLTRB(x + 8 * s, y - 60 * s, x + 50 * s, y + 4 * s), paint(P_["gold"])))
    glass = [(x - 26 * s, y - 50 * s), (x - 42 * s, y - 150 * s), (x - 30 * s, y - 250 * s), (x - 16 * s, y - 286 * s), (x + 16 * s, y - 286 * s),
             (x + 30 * s, y - 250 * s), (x + 42 * s, y - 150 * s), (x + 26 * s, y - 50 * s)]

    def blobs(c):
        glow = skia.Paint(AntiAlias=True)
        glow.setShader(skia.GradientShader.MakeLinear([skia.Point(x, y - 290 * s), skia.Point(x, y - 50 * s)],
                                                      [core.C(P_["magenta"]), core.C(P_["hotpink"])]))
        c.drawRect(skia.Rect.MakeLTRB(x - 60 * s, y - 300 * s, x + 60 * s, y), glow)
        for k in range(4):
            ph = (t * (0.05 + 0.02 * k) + k * 0.27) % 1.0
            by = y - 70 * s - ph * 200 * s
            bx = x + 10 * s * math.sin(t * 0.7 + k * 2)
            r = (16 + 6 * math.sin(t + k)) * s * (1 - 0.35 * ph)
            c.drawPath(poly_path(cr_closed(ell(bx, by, r, r * 1.25, n=8), 4)), paint(P_["orange"]))
        c.drawRect(skia.Rect.MakeLTRB(x - 30 * s, y - 70 * s, x + 30 * s, y - 52 * s), paint(P_["orange"]))
        c.drawPath(poly_path(cr_closed([(x - 24 * s, y - 250 * s), (x - 14 * s, y - 270 * s), (x - 30 * s, y - 160 * s)], 3)), paint(P_["white"], 60))
    blob(cv, glass, P_["hotpink"], w=5.5, seed=seed + 2, boil=0.9, n=5, shade=blobs)
    cap = [(x - 16 * s, y - 284 * s), (x, y - 336 * s), (x + 16 * s, y - 284 * s)]
    blob(cv, cap, P_["yellow"], w=5, seed=seed + 4, boil=0.6, n=4)
