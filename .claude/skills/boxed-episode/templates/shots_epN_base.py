"""BOXED episode base module (TEMPLATE, from Ep4 'THE CAVE') -- shared helpers for every shot module of the episode.
Copy to eng/shots_<EPN>_base.py, set EPN, keep the generic helpers, and replace THE CAVE KIT with this episode's world kit.
Original Ep4 docstring: (shots_ep4 / _cave / _game / _escape / _sun / _ad /
_return / _out).

Shot functions are named T###_slug (see ep4/timeline.json["shots"]) with signature fn(cv, t, T, A):
  cv  skia canvas 1920x1080      t  seconds since the shot started      T  episode time (s)
  A   acting channels for this drawing: A["HOST"], A["GUEST"] (dicts for draw_host / draw_zee)

GARY: gary(cv, x, y_eye, s, T) = the seated audience Gary (eyeball_creature); gary_full(cv, x, floor_y, s, T, **pose)
  = the standard full-body Gary (eng/gary.py: legs, walk, turns, posable arms, every expression), lip-synced.

THE CAVE KIT (use it so every cave shot in the episode matches):
  cave_side(cv, T, ...)        the classic cross-section: shadow wall (left) | chained prisoners | low puppet wall +
                               carriers | fire | the steep path up to the sunlit cave mouth (top right)
  cave_wall_view(cv, T, ...)   the prisoners' POV: the huge firelit wall with shadows, prisoners' heads in silhouette
  rock_mass, cave_fire, firelight, chain, prisoner, carrier, shadow_shape, statue (+ cave colours CV_*)
"""
import json
import math
import os
import numpy as np
import skia
from .core import (PAL, INK, W, H, paint, poly_path, cr_closed, cr_open, ell, blob, line, brush, dots, hsh, mix, jit, rot,
                   stipple, sparkle, rect_pts, tube)
from . import core
from . import world as w
from . import sets
from .letters import paint_text, measure, wrap_lines
from .zee import draw_zee, _hand
from .cast import draw_host, agent, alien, ai_blob, cosmic_hand, melting_clock, gauge
from .shots_a import ease, pop, lerp, Hh, G, CAM_HOST, CAM_ZEE, tag, guest_prop, host_prop, HOST_POS, GUEST_POS, ribbon_wipe
from .shots_ep2 import eyeball_creature, audience_rows, glow_square, pixel_text, social_glyph
from .gary import draw_gary

P_ = PAL
EPN = "ep5"   # <- this episode's folder under $B
EP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), EPN)
TL = json.load(open(os.path.join(EP, "timeline.json")))
LINES = {l["id"]: l for l in TL["lines"]}
SLOTS = {s["id"]: s for s in TL["slots"]}
SHOTS = {s["id"]: s for s in TL["shots"]}
CAM_WIDE = dict(x=0, y=30, z=1.02)
CAM_TWO = dict(x=40, y=40, z=1.3)
_LIPS = None

# cave colours: violet-indigo rock, hot firelight, a warm wall, maroon shadows
CV_ROCK = (52, 22, 96)
CV_ROCK2 = (78, 34, 140)
CV_ROCK_DK = (24, 10, 48)
CV_WALL = (255, 170, 96)
CV_WALL2 = (255, 120, 70)
CV_SHADOW = (96, 20, 60)
CV_FIRE = [P_["yellow"], P_["orange"], P_["red"], P_["magenta"]]


def R(x0, y0, x1, y1):
    return skia.Rect.MakeLTRB(float(x0), float(y0), float(x1), float(y1))


def _lips():
    global _LIPS
    if _LIPS is None:
        _LIPS = json.load(open(os.path.join(EP, "lipsync.json")))
    return _LIPS


def loud_at(lid, T):
    """Loudness 0..~1.4 of dialogue line `lid` at episode time T (0 outside the line) -- drive mouths/pulses with it."""
    L = _lips()[lid]
    fi = int((T - L["t0"]) * 24)
    return float(L["loud"][fi]) if 0 <= fi < L["n"] else 0.0


def vis_at(lid, T):
    """(viseme, openness) for line `lid` at time T -- for mouths of characters without an acting track (Gary, planet)."""
    L = _lips()[lid]
    fi = int((T - L["t0"]) * 24)
    if 0 <= fi < L["n"]:
        return L["vis"][fi], float(L["open"][fi])
    return "X", 0.0


def line_at(T):
    for l in TL["lines"]:
        if l["t0"] <= T < l["t1"]:
            return l
    return None


def spk_loud(spk, T):
    """Loudness of whatever line speaker `spk` ('AUD' = Gary, 'PLANET', 'ANN', 'HOST', 'GUEST') is saying at time T."""
    l = line_at(T)
    if l is None or l["spk"] != spk:
        return 0.0
    return loud_at(l["id"], T)


def gary(cv, x, y, s, T, seed=4400, mic=False, wave=0.0, loud=None):
    """Gary the eyeball (y = centre of his eye; his sweater hangs ~360*s below). Mouth follows his AUD lines."""
    eyeball_creature(cv, x, y, s, T, spk_loud("AUD", T) if loud is None else loud, seed=seed, mic=mic, wave=wave)


def gary_full(cv, x, fy, s, T, **pose):
    """Gary with legs, arms, turns and the full expression set (eng.gary.draw_gary): fy = the floor under him
    (seated his eye sits 360*s above it). Mouth follows his AUD lines unless loud=/mouth= is given. Use this, not a
    home-made copy, whenever he stands, walks, turns, gestures or emotes beyond the seated audience pose."""
    pose.setdefault("loud", spk_loud("AUD", T))
    return draw_gary(cv, x, fy, s, T, **pose)


def studio(cv, T, A, cam, t=0.0, host=None, guest=None, sign=1.0):
    """The BOXED talk-show set with both performers driven by the acting track. host/guest: dict overrides."""
    h = Hh(A, t, **(host or {}))
    g = G(A, t, **(guest or {}))
    sets.talkshow(cv, T, cam, host=h, guest=g, sign=sign)
    return h, g


def caption(cv, text, x, y, t, t0, size=84, fill=None, font="londrina", seed=0, shadow_rgb=None, align="center", dur=0.5, fills=None):
    """Hand-painted pop-in text that reveals over `dur` seconds starting at shot-time t0."""
    if t < t0:
        return
    paint_text(cv, text, x, y, font=font, size=size, fill=fill or P_["yellow"], fills=fills, ink_w=5.5 if size > 60 else 4, shadow=(6, 6),
               shadow_rgb=shadow_rgb or INK, seed=seed, reveal=float(np.clip((t - t0) / dur, 0, 1)), stagger=0.03, align=align)


def thought_bubble(cv, x, y, rx, ry, seed=0, a=255, fill=None):
    """A wobbly cloud bubble centred at x,y with the little trailing puffs going down-left. Returns the cloud path for clipping."""
    pts = []
    n = 14
    for k in range(n):
        ang = k / n * 2 * math.pi
        bump = 1.0 + 0.12 * math.sin(ang * 5 + seed)
        pts.append((x + rx * bump * math.cos(ang), y + ry * bump * math.sin(ang)))
    blob(cv, pts, fill or P_["white"], w=6, seed=seed, boil=1.2, n=6, a=a)
    for k, (dx, dy, r) in enumerate(((-rx * 0.75, ry * 1.05, 26), (-rx * 0.95, ry * 1.45, 16))):
        blob(cv, ell(x + dx, y + dy, r, r * 0.8, n=8), fill or P_["white"], w=4.5, seed=seed + 5 + k, boil=0.8, a=a)
    return poly_path(cr_closed(jit(pts, 0.0, seed), 6))


def vignette(cv, a=170, rgb=(0, 0, 0), inner=0.45):
    """Darken the frame edges (drawn on top)."""
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), W * 0.75, [core.C(rgb, 0), core.C(rgb, 0), core.C(rgb, a)], [0.0, inner, 1.0]))
    cv.drawRect(R(0, 0, W, H), p)


def darkness(cv, a):
    """Full-frame black overlay with alpha a (0..255) -- lights going out."""
    if a > 0:
        cv.drawRect(R(-10, -10, W + 10, H + 10), paint((6, 2, 12), int(min(255, a))))


# ===================================================================== THE CAVE KIT
def firelight(cv, x, y, r, T, a=150, rgb=None, seed=0):
    """Flickering radial glow (additive-looking warm light pool)."""
    rgb = rgb or P_["orange"]
    fl = 0.86 + 0.1 * math.sin(T * 11.0 + seed) + 0.06 * math.sin(T * 23.0 + seed * 2.1) + 0.05 * float(hsh(core.D * 0.31 + seed))
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(x, y), max(1.0, r * fl), [core.C(rgb, int(a * fl)), core.C(rgb, int(a * 0.35 * fl)), core.C(rgb, 0)],
                                               [0.0, 0.45, 1.0]))
    cv.drawCircle(x, y, r * fl, p)


def cave_fire(cv, x, y, s, T, seed=4100, logs=True, intensity=1.0):
    """A cartoon campfire (base at x, y): crossed logs, four nested tongues of flame that lick and boil, sparks."""
    if logs:
        for k, ang in enumerate((-18, 18, -4)):
            cv.save(); cv.translate(x, y - 12 * s); cv.rotate(ang)
            blob(cv, rect_pts([(-110 * s, -16 * s), (110 * s, -16 * s), (110 * s, 16 * s), (-110 * s, 16 * s)], 3), (120, 56, 40), w=4.5, seed=seed + k, boil=0.8, n=3,
                 shade=lambda c: c.drawRect(R(-120 * s, 2 * s, 120 * s, 20 * s), paint((80, 30, 30))))
            cv.restore()
    for li, col in enumerate(CV_FIRE[::-1]):
        k = 1.0 - li * 0.2
        hgt = (230 + 30 * math.sin(T * 3.1 + li)) * s * k * intensity
        wid = 120 * s * k
        pts = [(x - wid, y - 6 * s)]
        n = 7
        for j in range(n):
            u = (j + 0.5) / n
            px = x - wid + 2 * wid * u
            lick = math.sin(T * (6.0 + j) + j * 1.7 + li) * 0.5 + 0.5
            ph = hgt * (0.45 + 0.55 * math.sin(math.pi * u)) * (0.75 + 0.35 * lick)
            pts.append((px + 14 * s * math.sin(T * 5 + j + li), y - ph))
            if j < n - 1:
                pts.append((px + wid / n, y - ph * 0.55))
        pts.append((x + wid, y - 6 * s))
        blob(cv, pts, col, w=4.0 if li == 0 else 2.6, seed=seed + 10 + li, boil=1.6, n=4, a=255)
    for k in range(9):                                             # sparks rising
        ph = (T * (0.5 + 0.13 * k) + k * 0.37) % 1.0
        sx = x + (hsh(seed + k * 3.1) - 0.5) * 200 * s + 30 * s * math.sin(T * 2 + k)
        sy = y - 140 * s - ph * 420 * s
        dots(cv, [(sx, sy)], (4.5 - 3 * ph) * s + 0.8, P_["yellow"] if k % 2 else P_["orange"], a=int(255 * (1 - ph)))


def rock_mass(cv, pts, seed=4200, rgb=None, rim=None, rim_side=1, a=255, ink=5.5):
    """An irregular cave rock surface (polygon pts) with strata lines, mottling and an optional coloured firelight rim."""
    rgb = rgb or CV_ROCK
    P = np.asarray(pts, float)
    x0, y0 = P.min(0); x1, y1 = P.max(0)

    def sh(c):
        for k in range(7):                                         # strata
            yy = y0 + (y1 - y0) * (k + 0.5) / 7
            pts2 = [(x0 - 40, yy + 18 * math.sin(k * 1.9 + seed)), ((x0 + x1) / 2, yy - 14 * math.sin(k + seed)), (x1 + 40, yy + 10 * math.sin(k * 2.7))]
            line(c, pts2, 3.0, mix(rgb, INK, 0.35), seed=seed + 20 + k, boil=0.8, n=6, taper=(0.1, 0.1), a=170)
        stipple(c, mix(rgb, INK, 0.45), (x0, y0, x1, y1), spacing=15, r=2.0, seed=seed + 3,
                fn=lambda X, Y: np.clip(0.3 + 0.7 * np.sin(X * 0.013 + Y * 0.02 + seed) ** 2, 0, 1) * 0.8)
        if rim is not None:
            cx = x1 if rim_side > 0 else x0
            c.drawPath(poly_path(cr_closed([(cx - rim_side * 70, y0 - 50), (cx + rim_side * 60, y0 - 50), (cx + rim_side * 60, y1 + 50), (cx - rim_side * 40, y1 + 50)], 3)),
                       paint(rim, 130))
    blob(cv, P, rgb, w=ink, seed=seed, boil=1.1, n=5, shade=sh, a=a)


def chain(cv, p0, p1, seed=4300, link=16.0, rgb=None, sag=18.0, w=3.0):
    """A sagging iron chain of interlocking oval links from p0 to p1."""
    rgb = rgb or (150, 150, 175)
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = p1 - p0
    L = float(np.hypot(*d)) or 1.0
    n = max(2, int(L / link))
    for k in range(n):
        u = (k + 0.5) / n
        p = p0 + d * u + np.array([0.0, sag * math.sin(math.pi * u)])
        ang = math.degrees(math.atan2(d[1], d[0])) + (90 if k % 2 else 0) * 0 + (0 if k % 2 == 0 else 0)
        rx, ry = link * 0.62, (link * 0.36 if k % 2 == 0 else link * 0.14)
        Pt = ell(p[0], p[1], rx, ry, n=10, rot=ang)
        cv.drawPath(poly_path(cr_closed(jit(Pt, 0.4, seed + k), 3)), paint(INK, stroke=w + 3.5))
        cv.drawPath(poly_path(cr_closed(jit(Pt, 0.4, seed + k), 3)), paint(rgb, stroke=w))


def prisoner(cv, x, y, s, T, seed=4500, view="side", face=1, look=(0.0, 0.0), rgb=None, eye_rgb=None, chained=True, glow=0.0,
             blink=None, mouth=0.0, anchor=None):
    """A chained prisoner: a squat eyeball creature sitting on the cave floor (x, y = floor point under the body).
    view 'side' (facing `face` = -1 left / +1 right), 'back' (seen from behind, staring at the wall) or 'front'.
    Iron collar on the neck with a chain to an anchor ring in the floor; ankle shackles."""
    rgb = rgb or [(64, 30, 110), (90, 40, 150), (46, 20, 86), (110, 50, 120)][int(hsh(seed) * 4)]
    eye_rgb = eye_rgb or [(200, 255, 230), (255, 200, 240), (255, 240, 170), (190, 220, 255)][int(hsh(seed + 1) * 4)]
    bob = 2.5 * math.sin(T * 1.7 + seed) * s
    r = 70 * s
    cx, cy = x, y - r * 1.15 + bob
    body = [(x - r * 1.05, y), (x - r * 1.1, cy), (x - r * 0.7, cy - r * 0.95), (x, cy - r * 1.12), (x + r * 0.7, cy - r * 0.95), (x + r * 1.1, cy), (x + r * 1.05, y)]
    blob(cv, body, rgb, w=5.0 * min(1.0, s * 1.4) + 1.5, seed=seed, boil=1.0, n=5,
         shade=lambda c: c.drawPath(poly_path(cr_closed(ell(cx + face * r * 0.45, cy + r * 0.3, r * 0.9, r * 1.1, n=10), 3)), paint(mix(rgb, INK, 0.3))))
    if glow > 0:
        firelight(cv, cx - face * r * 0.4, cy - r * 0.2, r * 1.6, T, a=int(90 * glow), seed=seed)
    if view == "back":
        line(cv, [(cx - r * 0.5, cy - r * 0.5), (cx, cy - r * 0.62), (cx + r * 0.5, cy - r * 0.5)], 3, mix(rgb, P_["white"], 0.25), seed=seed + 3, boil=0.6, n=4)
    else:
        bl = blink if blink is not None else (1.0 if (T * 0.4 + hsh(seed) * 3) % 3.1 < 0.12 else 0.0)
        ex = cx + (face * r * 0.32 if view == "side" else 0.0)
        ey = cy - r * 0.18
        er = r * (0.5 if view == "front" else 0.42)
        if bl > 0.5:
            line(cv, [(ex - er, ey), (ex, ey + er * 0.3), (ex + er, ey)], 4, seed=seed + 5, boil=0.6, n=4)
        else:
            blob(cv, ell(ex, ey, er, er * 1.05, n=10), P_["white"], w=4, seed=seed + 5, boil=0.7)
            ix = ex + (face * er * 0.35 if view == "side" else 0) + look[0] * er * 0.4
            iy = ey + look[1] * er * 0.4
            dots(cv, [(ix, iy)], er * 0.55, eye_rgb)
            dots(cv, [(ix, iy)], er * 0.28, INK)
            dots(cv, [(ix - er * 0.15, iy - er * 0.2)], er * 0.1 + 0.8, P_["white"])
        if mouth > 0.05:
            blob(cv, ell(ex, ey + er * 1.45, er * 0.45, er * 0.18 + er * 0.5 * mouth, n=8), P_["mouth"], w=3, seed=seed + 6, boil=0.6)
    if chained:
        ny = cy + r * 0.42                                          # collar
        blob(cv, ell(cx, ny, r * 0.82, r * 0.2, n=10), (120, 120, 150), w=3.5, seed=seed + 8, boil=0.6,
             shade=lambda c: c.drawRect(R(cx - r, ny, cx + r, ny + r * 0.3), paint((80, 80, 110))))
        ax, ay = anchor if anchor is not None else (x - face * r * 1.5, y + 4 * s)
        chain(cv, (cx - face * r * 0.6, ny + r * 0.1), (ax, ay), seed=seed + 9, link=max(8.0, 15 * s), sag=10 * s, w=max(1.6, 2.6 * s))
        blob(cv, ell(ax, ay, 12 * s + 2, 5 * s + 2, n=8), (120, 120, 150), w=3, seed=seed + 10, boil=0.4)
        for side in (-1, 1):                                       # ankle shackles at the base
            blob(cv, ell(x + side * r * 0.6, y - 6 * s, r * 0.25, r * 0.1, n=8), (120, 120, 150), w=3, seed=seed + 12 + side, boil=0.4)


def carrier(cv, x, y, s, T, holding="horse", seed=4600, phase=0.0, rgb=None, face=1):
    """A hooded puppet-carrier walking along behind the low wall (x, y = feet), holding a statue up on a pole.
    holding: one of shadow_shape kinds ('bunny', 'horse', 'tree', 'person', 'bird', 'fish', 'jug', 'star')."""
    rgb = rgb or (36, 16, 60)
    step = math.sin((T + phase) * 4.2)
    bob = abs(math.cos((T + phase) * 4.2)) * 6 * s
    for side in (-1, 1):
        line(cv, [(x + side * 14 * s, y - 120 * s - bob), (x + side * 18 * s + step * side * 22 * s, y)], 16 * s + 2, rgb, seed=seed + side, boil=0.7, n=3, taper=(0, 0))
    robe = [(x - 60 * s, y - 60 * s - bob), (x - 46 * s, y - 230 * s - bob), (x, y - 300 * s - bob), (x + 46 * s, y - 230 * s - bob), (x + 60 * s, y - 60 * s - bob)]
    blob(cv, robe, rgb, w=4.5, seed=seed + 3, boil=1.0, n=5)
    hx, hy = x + face * 6 * s, y - 280 * s - bob
    blob(cv, ell(hx, hy, 42 * s, 48 * s, n=10), rgb, w=4.5, seed=seed + 4, boil=0.9)        # hood
    for side in (-1, 1):
        dots(cv, [(hx + face * 10 * s + side * 12 * s, hy + 4 * s)], 4.5 * s + 1, P_["yellow"])
    px, py = x + face * 40 * s, y - 210 * s - bob                                               # pole up to the statue
    top = (px + face * 10 * s, y - 470 * s - bob)
    line(cv, [(px, py + 80 * s), top], 7 * s + 1.5, (110, 70, 40), seed=seed + 6, boil=0.5, n=2, taper=(0, 0))
    tube(cv, [(x + face * 30 * s, y - 220 * s - bob), (px, py)], 14 * s, rgb, w=3.5, seed=seed + 7, boil=0.6)
    statue(cv, holding, top[0], top[1] - 60 * s, 0.9 * s, T, seed=seed + 8)


def statue(cv, kind, x, y, s, T, seed=4700, rgb=None):
    """A carved, painted puppet statue (the real object whose shadow the prisoners see). Centre x, y."""
    rgb = rgb or [P_["cream"], P_["peach"], P_["lilac"], P_["mint"]][int(hsh(seed) * 4)]
    pts = SHAPES.get(kind, SHAPES["star"])
    P = np.array([(x + px * s, y + py * s) for px, py in pts])
    blob(cv, P, rgb, w=4.0, seed=seed, boil=0.8, n=4,
         shade=lambda c: stipple(c, mix(rgb, INK, 0.35), (P[:, 0].min(), P[:, 1].min(), P[:, 0].max(), P[:, 1].max()), spacing=9, r=1.4, seed=seed + 1,
                                 fn=lambda X, Y: np.clip((X - x) / (60 * s + 1) + 0.2, 0, 1) * 0.8))


def shadow_shape(cv, kind, x, y, s, T, rgb=None, a=230, seed=4800, wobble=1.0, outline=False):
    """A soft-edged flat SHADOW silhouette of a puppet (bunny, horse, tree, person, bird, fish, jug, star, hand_bunny)
    centred at x, y -- what the prisoners see on the wall. Drawn twice (blurred halo + body) for a firelit penumbra."""
    rgb = rgb or CV_SHADOW
    pts = SHAPES.get(kind, SHAPES["star"])
    fl = 1.0 + 0.03 * math.sin(T * 9 + seed) * wobble
    P = np.array([(x + px * s * fl, y + py * s * fl) for px, py in pts])
    halo = skia.Paint(AntiAlias=True, Color=core.C(rgb, int(a * 0.45)))
    halo.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10 * s + 2))
    path = poly_path(cr_closed(jit(P, 1.2 * wobble, seed), 4))
    cv.drawPath(path, halo)
    cv.drawPath(path, paint(rgb, a))
    if outline:
        brush(cv, cr_closed(jit(P, 1.2 * wobble, seed), 4), 3.5, closed=True, seed=seed + 1)


# silhouettes, unit scale ~ +-100 px (y down)
SHAPES = {
    "bunny": [(-70, 60), (-80, 10), (-60, -30), (-20, -40), (-10, -110), (6, -150), (22, -110), (18, -50), (34, -120), (52, -150), (60, -100),
              (44, -40), (70, -20), (90, 10), (80, 40), (50, 60), (0, 70)],
    "horse": [(-110, 50), (-100, -10), (-60, -30), (20, -30), (50, -70), (60, -110), (80, -120), (110, -90), (100, -70), (80, -60), (70, -20),
              (80, 50), (66, 50), (56, 10), (-40, 10), (-60, 50), (-74, 50), (-80, 14), (-96, 20), (-96, 50)],
    "tree": [(-14, 90), (-12, 20), (-80, 30), (-100, -10), (-80, -60), (-40, -100), (0, -116), (44, -100), (84, -60), (100, -10), (80, 30), (12, 20), (14, 90)],
    "person": [(-40, 100), (-36, 20), (-56, 30), (-60, -10), (-34, -40), (-24, -60), (-30, -90), (0, -112), (30, -90), (24, -60), (34, -40), (60, -10),
               (56, 30), (36, 20), (40, 100), (6, 100), (0, 50), (-6, 100)],
    "bird": [(-100, -10), (-50, -40), (-10, -20), (10, -60), (40, -90), (30, -30), (70, -30), (100, -10), (60, 0), (20, 20), (-20, 30), (-60, 10)],
    "fish": [(-100, 0), (-60, -40), (0, -50), (50, -30), (80, -60), (90, 0), (80, 60), (50, 30), (0, 50), (-60, 40)],
    "jug": [(-30, -100), (30, -100), (24, -70), (60, -30), (64, 40), (40, 90), (-40, 90), (-64, 40), (-60, -30), (-24, -70)],
    "star": [(0, -100), (24, -30), (95, -30), (38, 12), (60, 85), (0, 40), (-60, 85), (-38, 12), (-95, -30), (-24, -30)],
    "hand_bunny": [(-60, 100), (-70, 40), (-50, 0), (-40, -60), (-46, -140), (-30, -150), (-16, -70), (-6, -70), (6, -150), (22, -146),
                   (16, -60), (40, -20), (60, 20), (50, 60), (30, 70), (20, 100)],
}


def crystal(cv, x, y, s, T, seed=4900, rgb=None):
    """A glowing crystal cluster growing from the rock (base at x, y)."""
    rgb = rgb or [P_["teal"], P_["acid"], P_["hotpink"], P_["lilac"]][int(hsh(seed) * 4)]
    firelight(cv, x, y - 30 * s, 110 * s, T, a=70, rgb=rgb, seed=seed)
    for k in range(4):
        ang = -60 + k * 38 + 8 * math.sin(seed + k)
        L = (60 + 50 * hsh(seed + k * 3)) * s
        wd = (14 + 8 * hsh(seed + k * 5)) * s
        r = math.radians(ang - 90)
        tip = (x + L * math.cos(r), y + L * math.sin(r))
        n = (-math.sin(r), math.cos(r))
        pts = [(x + n[0] * wd, y + n[1] * wd), (tip[0] + n[0] * wd * 0.5, tip[1] + n[1] * wd * 0.5), tip, (tip[0] - n[0] * wd * 0.5, tip[1] - n[1] * wd * 0.5),
               (x - n[0] * wd, y - n[1] * wd)]
        blob(cv, pts, rgb, w=3.0, seed=seed + 10 + k, boil=0.5, n=2,
             shade=lambda c, pts=pts: c.drawPath(poly_path([pts[0], pts[1], pts[2], ((pts[0][0] + pts[4][0]) / 2, (pts[0][1] + pts[4][1]) / 2)]), paint(P_["white"], 90)))


def glow_mushroom(cv, x, y, s, T, seed=4950, rgb=None):
    """A little bioluminescent mushroom (base x, y)."""
    rgb = rgb or [P_["acid"], P_["teal"], P_["hotpink"]][int(hsh(seed) * 3)]
    pulse = 0.75 + 0.25 * math.sin(T * 2.2 + seed)
    firelight(cv, x, y - 40 * s, 80 * s, T, a=int(90 * pulse), rgb=rgb, seed=seed)
    line(cv, [(x, y), (x + 4 * s, y - 24 * s), (x, y - 40 * s)], 9 * s + 1.5, P_["cream"], seed=seed + 1, boil=0.6, n=3, taper=(0, 0))
    blob(cv, [(x - 34 * s, y - 36 * s), (x - 26 * s, y - 62 * s), (x, y - 72 * s), (x + 26 * s, y - 62 * s), (x + 34 * s, y - 36 * s)], rgb, w=3.0, seed=seed + 2, boil=0.6, n=4,
         shade=lambda c: dots(c, [(x - 12 * s, y - 56 * s), (x + 10 * s, y - 60 * s), (x + 2 * s, y - 46 * s)], 4 * s + 0.6, P_["white"], a=200))


def handprint(cv, x, y, s, rgb=None, a=110, seed=4980, ang=0.0):
    """An ancient sprayed handprint (stencil) on the cave wall."""
    rgb = rgb or P_["maroon"]
    cv.save(); cv.translate(x, y); cv.rotate(ang); cv.scale(s, s)
    halo = skia.Paint(AntiAlias=True, Color=core.C(rgb, a))
    halo.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 7))
    cv.drawPath(poly_path(cr_closed(ell(0, 18, 34, 38, n=10), 3)), halo)
    for k, (ax, L) in enumerate(((-40, 46), (-14, 62), (8, 66), (28, 58), (52, 40))):
        r = math.radians(ax - 90 if k < 4 else 10 - 90)
        p0 = (math.cos(r) * 14 + (k - 2) * 12 * 0.0, -10)
        pts = [(-8 + (k - 2) * 15 if k < 4 else 30, 0), ((k - 2) * 16 if k < 4 else 58, -L * 0.8 if k < 4 else -L * 0.4)]
        cv.drawPath(open_path_pts(pts), _halo_stroke(rgb, a, 16))
    cv.restore()


def _halo_stroke(rgb, a, wdt):
    p = skia.Paint(AntiAlias=True, Color=core.C(rgb, a))
    p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(wdt); p.setStrokeCap(skia.Paint.kRound_Cap)
    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 5))
    return p


def open_path_pts(pts):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    return p


def sun_rays(cv, x, y, r, T, n=14, a=60, rgb=None, ang0=110, span=80):
    """Shafts of daylight fanning in from a point (e.g. the cave mouth)."""
    rgb = rgb or P_["yellow"]
    for k in range(n):
        u = (k + 0.5) / n
        aa = math.radians(ang0 + span * (u - 0.5) + 2 * math.sin(T * 0.5 + k))
        wd = math.radians(span / n * (0.35 + 0.25 * math.sin(T * 0.9 + k * 1.7)))
        p = [(x, y), (x + r * math.cos(aa - wd), y + r * math.sin(aa - wd)), (x + r * math.cos(aa + wd), y + r * math.sin(aa + wd))]
        sh = skia.Paint(AntiAlias=True)
        sh.setShader(skia.GradientShader.MakeRadial(skia.Point(x, y), r, [core.C(rgb, a), core.C(rgb, 0)]))
        cv.drawPath(poly_path(p), sh)


def wall_surface(cv, poly, T, seed=4010, cx=None, cy=None, glow=1.0):
    """The firelit wall the shadows fall on: hot orange-yellow gradient, cracks, stipple grain, faded handprints."""
    P = np.asarray(poly, float)
    x0, y0 = P.min(0); x1, y1 = P.max(0)
    cx = (x0 + x1) / 2 if cx is None else cx
    cy = (y0 + y1) * 0.6 if cy is None else cy
    path = poly_path(cr_closed(jit(P, 0.8, seed), 4))
    g = skia.Paint(AntiAlias=True)
    fl = 0.93 + 0.05 * math.sin(T * 9.0 + seed) + 0.03 * math.sin(T * 17.0)
    g.setShader(skia.GradientShader.MakeRadial(skia.Point(cx, cy), max(x1 - x0, y1 - y0) * 0.75 * fl,
                                               [core.C(mix(P_["yellow"], CV_WALL, 0.35)), core.C(CV_WALL), core.C(CV_WALL2), core.C(mix(CV_WALL2, P_["red"], 0.6))],
                                               [0.0, 0.35 * glow, 0.7, 1.0]))
    cv.drawPath(path, g)
    cv.save()
    cv.clipPath(path, doAntiAlias=True)
    stipple(cv, mix(CV_WALL2, P_["red"], 0.5), (x0, y0, x1, y1), spacing=15, r=2.1, seed=seed + 2,
            fn=lambda X, Y: np.clip(np.hypot(X - cx, Y - cy) / (max(x1 - x0, y1 - y0) * 0.6), 0, 1) * 0.9)
    for k in range(9):                                             # cracks
        sx = x0 + (x1 - x0) * hsh(seed + k * 2.3)
        sy = y0 + (y1 - y0) * hsh(seed + k * 4.1)
        pts = [(sx, sy)]
        for j in range(4):
            pts.append((pts[-1][0] + 30 * (hsh(seed + k * 7 + j) - 0.5) * 2, pts[-1][1] + 40 + 30 * hsh(seed + k * 5 + j)))
        line(cv, pts, 2.6, mix(CV_WALL2, P_["maroon"], 0.6), seed=seed + 20 + k, boil=0.6, n=4, taper=(0.3, 0.5), a=160)
    for k in range(5):                                             # ancient handprints
        handprint(cv, x0 + (x1 - x0) * (0.1 + 0.8 * hsh(seed + 40 + k)), y0 + (y1 - y0) * (0.15 + 0.3 * hsh(seed + 50 + k)), 0.7 + 0.4 * hsh(seed + 60 + k),
                  rgb=[P_["maroon"], P_["red"], P_["violet"]][k % 3], a=70, seed=seed + 70 + k, ang=-20 + 40 * hsh(seed + 80 + k))
    cv.restore()
    brush(cv, cr_closed(jit(P, 0.8, seed), 4), 6.0, closed=True, seed=seed + 3)


def cave_side(cv, T, cam=None, fire=1.0, seed=4000, carriers=True, prisoners=6, shadows=True, mouth_light=1.0, wall_shadows=None):
    """THE CLASSIC CROSS-SECTION (camera-aware; parallax layers). Layout at cam z=1 (world coords):
         wall (x<330)  |  prisoners x 420..900 facing LEFT  |  low wall x 960..1340, carriers behind it  |  fire x 1520
         steep path rising from x 1250 up to the cave mouth top-right (x 1700..1920, y 0..260), daylight beyond.
    wall_shadows: optional list of (kind, x, y, s) to cast on the wall (default: the carriers' statues, projected)."""
    C = sets.Cam(cv, cam or dict(x=0, y=0, z=1.0))
    kinds = ["horse", "bunny", "tree", "person", "bird", "jug"]
    with C.layer(0.2):                                             # deep back wall of the cavern
        w.field(cv, CV_ROCK_DK)
        rock_mass(cv, [(-300, 80), (700, 40), (1400, 90), (2300, 30), (2300, 1000), (-300, 1000)], seed=seed + 11, rgb=(36, 14, 70), ink=4)
        for k in range(7):
            crystal(cv, 80 + k * 300 + 60 * math.sin(k * 1.7), 640 + 90 * math.sin(k * 2.9), 0.7, T, seed=seed + 120 + k)
        firelight(cv, 1500, 700, 1300, T, a=int(90 * fire), seed=seed)
    with C.layer(0.5):                                             # far rock + the cave mouth with daylight
        if mouth_light > 0:
            g = skia.Paint(AntiAlias=True)
            g.setShader(skia.GradientShader.MakeRadial(skia.Point(1840, 90), 560, [core.C(P_["white"], int(255 * mouth_light)), core.C(P_["yellow"], int(210 * mouth_light)),
                                                                                    core.C(P_["orange"], 0)], [0.0, 0.35, 1.0]))
            cv.drawRect(R(1300, -200, 2300, 760), g)
            sun_rays(cv, 1860, 60, 1300, T, n=12, a=int(70 * mouth_light), ang0=145, span=55)
        rock_mass(cv, [(-200, -200), (2300, -200), (2300, -60), (1960, 20), (1700, 260), (1500, 180), (1200, 120), (800, 160), (300, 120), (-200, 200)],
                  seed=seed + 1, rgb=CV_ROCK, rim=P_["magenta"], rim_side=1)
        for row, (yb, sc, col) in enumerate(((112, 1.0, CV_ROCK2), (150, 0.7, mix(CV_ROCK2, P_["magenta"], 0.25)))):
            for k in range(11):                                    # two rows of stalactites
                sx = 60 + k * 165 + 50 * math.sin(k * 2.3 + row) + row * 80
                if sx > 1650:
                    continue
                sl = (60 + 80 * hsh(seed + k + row * 20)) * sc
                y0s = yb + 18 * math.sin(k + row)
                blob(cv, [(sx - 28 * sc, y0s), (sx + 28 * sc, y0s), (sx + 5 * sc, y0s + sl + 40 * sc), (sx - 2 * sc, y0s + sl + 46 * sc)], col, w=4,
                     seed=seed + 30 + k + row * 20, boil=0.8, n=3,
                     shade=lambda c, sx=sx, y0s=y0s, sl=sl, sc=sc: c.drawPath(poly_path([(sx + 6 * sc, y0s), (sx + 28 * sc, y0s), (sx + 5 * sc, y0s + sl + 40 * sc)]),
                                                                          paint(mix(col, INK, 0.3))))
                ph = ((T * 0.35 + hsh(seed + k * 7 + row)) % 1.0)
                if (k + row) % 3 == 0:                             # a water drop forming and falling
                    dy = 0 if ph < 0.7 else (ph - 0.7) / 0.3 * 600
                    dots(cv, [(sx + 1, y0s + sl + 50 * sc + dy)], 5, P_["mint"], a=int(255 * (1 - max(0, ph - 0.7) / 0.3)))
    with C.layer(0.85):
        wall = [(-200, 120), (330, 140), (360, 420), (330, 760), (290, 1000), (-200, 1000)]
        wall_surface(cv, wall, T, seed=seed + 2, cx=150, cy=520)
        if shadows:
            sh_list = wall_shadows
            if sh_list is None:
                sh_list = []
                for k in range(3):
                    ph = (T * 0.07 + k / 3.0) % 1.0
                    sh_list.append((kinds[(int(T * 0.07 + k / 3.0) * 3 + k) % len(kinds)], 330 - ph * 520, 420 + 40 * math.sin(k), 1.0))
            cv.save()
            cv.clipPath(poly_path(cr_closed(wall, 4)), doAntiAlias=True)
            for kind, sx, sy, ss in sh_list:
                shadow_shape(cv, kind, sx, sy, 1.1 * ss, T, seed=seed + 40 + int(sx))
            cv.restore()
        rock_mass(cv, [(-200, 860), (700, 830), (1300, 860), (1700, 820), (2300, 840), (2300, 1300), (-200, 1300)], seed=seed + 3, rgb=CV_ROCK2,
                  rim=P_["orange"], rim_side=1)
        for k in range(14):                                        # pebbles
            px = 60 + k * 140 + 50 * math.sin(k * 3.1)
            blob(cv, ell(px, 960 + 60 * hsh(seed + k * 9), 16 + 10 * hsh(seed + k), 9 + 5 * hsh(seed + k * 2), n=8), mix(CV_ROCK2, P_["lilac"], 0.25), w=3,
                 seed=seed + 200 + k, boil=0.5)
        path = [(1250, 860), (1420, 640), (1560, 470), (1700, 300), (1820, 160), (2000, 120), (2000, 260), (1880, 330), (1700, 520), (1560, 700), (1440, 880)]
        blob(cv, path, mix(CV_ROCK2, P_["orange"], 0.3), w=5, seed=seed + 4, boil=1.0, n=4,
             shade=lambda c: [blob(c, ell(1330 + k * 66, 820 - k * 82, 30, 12, n=8, rot=-50), mix(CV_ROCK2, P_["orange"], 0.5), w=3, seed=seed + 50 + k, boil=0.5)
                              for k in range(10)])
        for k, (mx, my) in enumerate(((60, 900), (370, 930), (930, 905), (1180, 935))):
            glow_mushroom(cv, mx, my, 0.8, T, seed=seed + 300 + k)
    with C.layer(1.0):
        firelight(cv, 1520, 760, 560, T, a=int(150 * fire), rgb=P_["orange"], seed=seed + 7)
        if fire > 0.01:
            cave_fire(cv, 1520, 850, 0.9, T, seed=seed + 8, intensity=fire)
        if carriers:
            for k in range(3):
                ph = (T * 0.07 + k / 3.0) % 1.0
                cx = 1380 - ph * 520
                carrier(cv, cx, 860, 0.62, T, holding=kinds[(int(T * 0.07 + k / 3.0) * 3 + k) % len(kinds)], seed=seed + 60 + k * 10, phase=k * 0.7, face=-1)
        blob(cv, rect_pts([(960, 700), (1340, 700), (1350, 870), (950, 870)], 3), mix(CV_ROCK2, P_["maroon"], 0.3), w=6, seed=seed + 9, boil=0.9, n=3,
             shade=lambda c: ([c.drawLine(960 + k * 48, 700, 958 + k * 48, 870, paint(mix(CV_ROCK2, INK, 0.4), stroke=3)) for k in range(9)],
                              c.drawRect(R(950, 700, 1350, 724), paint(mix(CV_ROCK2, P_["orange"], 0.45)))))
        for k in range(prisoners):
            px = 420 + k * 95
            prisoner(cv, px, 900 + (k % 2) * 30, 0.62 + 0.04 * (k % 2), T, seed=seed + 100 + k * 13, view="side", face=-1, look=(-1, 0),
                     anchor=(px + 70, 912 + (k % 2) * 30), glow=0.5)


def cave_wall_view(cv, T, cam=None, fire=1.0, seed=4000, shadows=None, prisoners=7, heads_y=1010, wall_tint=None):
    """THE PRISONERS' POV: the immense firelit wall fills the frame; flickering light from behind the camera; the prisoners'
    heads and collars in silhouette along the bottom, chained together. shadows: list of (kind, x, y, s) (default: a slow parade)."""
    C = sets.Cam(cv, cam or dict(x=0, y=0, z=1.0))
    with C.layer(0.6):
        w.field(cv, CV_ROCK_DK)
        wall_surface(cv, [(-220, -220), (2140, -220), (2140, 1300), (-220, 1300)], T, seed=seed + 1, cx=960, cy=820)
        rock_mass(cv, [(-300, -300), (2300, -300), (2300, -20), (1600, 60), (900, 30), (300, 80), (-300, 40)], seed=seed + 5, rgb=CV_ROCK, rim=P_["orange"])
        sl = shadows
        if sl is None:
            kinds = ["horse", "bunny", "tree", "person", "bird", "fish", "jug"]
            sl = []
            for k in range(3):
                ph = (T * 0.06 + k / 3.0) % 1.0
                sl.append((kinds[(int(T * 0.06 + k / 3.0) * 3 + k) % len(kinds)], 2100 - ph * 2300, 470 + 50 * math.sin(k * 2.1), 2.2))
        for kind, sx, sy, ss in sl:
            shadow_shape(cv, kind, sx, sy, ss, T, seed=seed + 20 + int(sx))
    with C.layer(1.0):
        pts = []
        for k in range(prisoners):
            px = 120 + k * (1680 / max(1, prisoners - 1))
            r = 110 + 12 * (k % 2)
            yy = heads_y + 18 * (k % 2) + 3 * math.sin(T * 1.6 + k)
            pts.append((px, yy, r))
        for k in range(len(pts) - 1):                               # chained to each other
            chain(cv, (pts[k][0] + pts[k][2] * 0.7, pts[k][1] + pts[k][2] * 0.6), (pts[k + 1][0] - pts[k + 1][2] * 0.7, pts[k + 1][1] + pts[k + 1][2] * 0.6),
                  seed=seed + 100 + k, link=20, sag=26, w=3.5)
        for k, (px, yy, r) in enumerate(pts):
            blob(cv, ell(px, yy, r, r * 1.05, n=12), (24, 10, 40), w=5, seed=seed + 60 + k, boil=1.0,
                 shade=lambda c, px=px, yy=yy, r=r: c.drawPath(poly_path(cr_closed(ell(px, yy - r * 0.95, r * 0.9, r * 0.3, n=10), 3)), paint(P_["orange"], 70)))
            blob(cv, ell(px, yy + r * 0.55, r * 0.8, r * 0.2, n=10), (110, 110, 140), w=3.5, seed=seed + 80 + k, boil=0.6)
            line(cv, [(px - r * 0.5, yy - r * 0.66), (px, yy - r * 0.78), (px + r * 0.5, yy - r * 0.66)], 4, P_["yellow"], seed=seed + 90 + k, boil=0.6, n=4, a=190)
