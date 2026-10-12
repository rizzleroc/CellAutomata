#!/usr/bin/env python3
"""'FREE ED SHEERAN' -- 60 s animated cover, 1080x1920 @ 24 fps.

Act 1  (0-9 s)    a real 3D jewel case (front art + spine) floats in a spotlight on a dark stage and turns to camera.
Act 2  (9-52.5 s) we push through the plastic into the art, rebuilt as a 2.5D multiplane stack: crowd flashes and
                  stadium beams, the title drips, the suits jab, the signs pump, the glass shimmers, the flag waves,
                  the pedal sparks, the CANCELLED ticket slams, then the fishbowl cracks and shatters.
Act 3  (52.5-60)  pull back out to the case, its cover now cracked, and fade.
   python3 anim.py --stills 3 12 20 ...     -> stills/still_<t>.png
   python3 anim.py                           -> out/video.mp4 (4 workers)
"""
import json, math, os, subprocess, sys, time
import numpy as np
import skia
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
FF = "/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
W, H, FPS, DUR = 1080, 1920, 24, 60.0
SAMP = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)
T_SWITCH_IN, T_SWITCH_OUT = 9.0, 52.5
T_SLAM, T_CRACK0, T_SHATTER = 42.5, 44.6, 50.0
ART = 2880.0
BOWL_C, BOWL_R = (1372.0, 1584.0), (860.0, 756.0)
RIM_C, RIM_R = (1372.0, 816.0), (484.0, 104.0)


# ------------------------------------------------------------------ small utils
def clamp(x, a=0.0, b=1.0):
    return a if x < a else (b if x > b else x)


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_in(x):
    x = clamp(x)
    return x * x * x


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def hsh(x):
    v = math.sin(x * 12.9898 + 78.233) * 43758.5453
    return v - math.floor(v)


def col(r, g, b, a=255):
    return skia.ColorSetARGB(int(clamp(a, 0, 255)), int(r), int(g), int(b))


def paint(c, blend=None, aa=True, stroke=None, cap=None):
    p = skia.Paint(AntiAlias=aa, Color=c)
    if blend is not None:
        p.setBlendMode(blend)
    if stroke is not None:
        p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke)
        p.setStrokeCap(cap or skia.Paint.kRound_Cap); p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


def radial(cv, x, y, r, c0, c1=None, blend=skia.BlendMode.kPlus):
    c1 = c1 if c1 is not None else (c0 & 0x00FFFFFF)
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(x, y), max(r, 0.5), [c0, c1]))
    if blend is not None:
        p.setBlendMode(blend)
    cv.drawCircle(x, y, r, p)


def poly(pts):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    p.close()
    return p


def ellipse_path(c, r):
    p = skia.Path()
    p.addOval(skia.Rect.MakeLTRB(c[0] - r[0], c[1] - r[1], c[0] + r[0], c[1] + r[1]))
    return p


def to_img(rgba, mip=True):
    im = skia.Image.fromarray(np.ascontiguousarray(rgba), colorType=skia.kRGBA_8888_ColorType)
    return im.withDefaultMipmaps() if mip else im


# ------------------------------------------------------------------ assets
class Assets:
    def __init__(self):
        L = os.path.join(HERE, "layers")
        self.offs = json.load(open(os.path.join(L, "offsets.json")))
        self.layers = {}
        for n in ("title", "suits", "sign1", "sign2", "flag", "ticket_cancel", "bowl"):
            a = np.asarray(Image.open(os.path.join(L, f"{n}.png")).convert("RGBA"))
            self.layers[n] = (to_img(a), a.shape[1], a.shape[0])
        bg = np.asarray(Image.open(os.path.join(L, "bg.png")).convert("RGBA"))
        self.bg = to_img(bg)
        art = np.asarray(Image.open(os.path.join(HERE, "art.png")).convert("RGB"))
        self.art_rgb = art
        tl = self.layers["title"]
        ta = np.asarray(Image.open(os.path.join(L, "title.png")).convert("RGBA")).astype(np.float32)
        red = np.clip((ta[..., 0] - (ta[..., 1] + ta[..., 2]) / 2 - 40) / 60, 0, 1) * (ta[..., 3] / 255)
        small = Image.fromarray((red * 255).astype(np.uint8)).resize((ta.shape[1] // 8, ta.shape[0] // 8), Image.BILINEAR)
        from PIL import ImageFilter
        glow = np.asarray(small.filter(ImageFilter.GaussianBlur(5)), np.float32) / 255.0
        g = np.zeros(glow.shape + (4,), np.uint8)
        g[..., 0] = 255; g[..., 1] = 40; g[..., 2] = 30; g[..., 3] = np.clip(glow * 255 * 1.6, 0, 255).astype(np.uint8)
        self.title_glow = (to_img(g), g.shape[1], g.shape[0], ta.shape[1], ta.shape[0])
        self.front = to_img(self.make_front(art))
        sp = np.asarray(Image.open(os.path.join(HERE, "spine.png")).convert("RGBA"))
        self.spine = to_img(sp)
        self.cracks = Cracks()
        self._front_cracked = None

    @staticmethod
    def make_front(art, cracked=None):
        """Front face texture at 20 px/mm: 142x125 mm -> 2840x2500 (hinge strip + 120 mm art + plastic lip)."""
        fw, fh = 2840, 2500
        f = np.zeros((fh, fw, 4), np.float32)
        f[..., :3] = (206, 209, 216); f[..., 3] = 255
        xs = np.arange(440, dtype=np.float32)
        hinge = 200 + 25 * np.sin(xs / 440 * math.pi) - 18 * (np.abs(xs - 70) < 5) - 22 * (np.abs(xs - 120) < 4) - 16 * (np.abs(xs - 330) < 4) \
            - 26 * (np.abs(xs - 400) < 6) + 30 * (np.abs(xs - 92) < 3)
        f[:, :440, :3] = hinge[None, :, None] * np.array([1.0, 1.01, 1.04])[None, None, :]
        src = cracked if cracked is not None else art
        a = np.asarray(Image.fromarray(src).resize((2400, 2400), Image.LANCZOS), np.float32)
        f[50:2450, 440:2840, :3] = a
        f[:, 436:444, :3] *= 0.55
        return np.clip(f, 0, 255).astype(np.uint8)

    def front_cracked(self):
        if self._front_cracked is None:
            surf = skia.Surface.MakeRaster(skia.ImageInfo.Make(2880, 2880, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType))
            c = surf.getCanvas()
            c.drawImage(to_img(np.dstack([self.art_rgb, np.full(self.art_rgb.shape[:2], 255, np.uint8)]), mip=False), 0, 0)
            self.cracks.draw(c, 1.0, scale=1.0)
            arr = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)[:, :, :3]
            self._front_cracked = to_img(self.make_front(self.art_rgb, cracked=arr))
        return self._front_cracked


# ------------------------------------------------------------------ the crack network (art coords)
class Cracks:
    def __init__(self, seed=5):
        rng = np.random.default_rng(seed)
        self.I = np.array([1915.0, 1080.0])                      # impact: upper-right glass, clear of the face
        segs = []                                                 # (x0, y0, x1, y1, birth_distance, width)

        def inside(p):
            return ((p[0] - BOWL_C[0]) / (BOWL_R[0] - 25)) ** 2 + ((p[1] - BOWL_C[1]) / (BOWL_R[1] - 25)) ** 2 < 1.0

        rays = []
        n = 15
        for k in range(n):
            ang = k / n * 2 * math.pi + rng.uniform(-0.18, 0.18)
            p = self.I.copy(); d = 0.0; pts = [(p.copy(), 0.0)]
            wd = rng.uniform(5.5, 8.5)
            while inside(p) and d < 2600:
                step = rng.uniform(40, 95)
                ang += rng.normal(0, 0.22)
                q = p + step * np.array([math.cos(ang), math.sin(ang)])
                segs.append((p[0], p[1], q[0], q[1], d, wd))
                d += step; p = q; pts.append((p.copy(), d))
                wd = max(2.2, wd * 0.96)
                if rng.random() < 0.13:                           # side branch
                    ba = ang + rng.choice([-1, 1]) * rng.uniform(0.5, 1.1)
                    bp = p.copy(); bd = d; bw = wd * 0.6
                    for _ in range(int(rng.integers(2, 6))):
                        st = rng.uniform(30, 70); ba += rng.normal(0, 0.3)
                        bq = bp + st * np.array([math.cos(ba), math.sin(ba)])
                        if not inside(bq):
                            break
                        segs.append((bp[0], bp[1], bq[0], bq[1], bd, bw)); bd += st; bp = bq; bw = max(1.6, bw * 0.85)
            rays.append(pts)
        for rad in (110, 240, 400, 600):                          # concentric spider-web rings
            for k in range(n):
                a_, b_ = rays[k], rays[(k + 1) % n]
                pa = min(a_, key=lambda z: abs(z[1] - rad + rng.uniform(-20, 20)))
                pb = min(b_, key=lambda z: abs(z[1] - rad + rng.uniform(-20, 20)))
                if pa[1] < rad * 0.6 or pb[1] < rad * 0.6 or rng.random() < 0.25:
                    continue
                mid = (pa[0] + pb[0]) / 2 + rng.normal(0, 12, 2)
                for (u0, u1) in ((pa[0], mid), (mid, pb[0])):
                    if inside(u0) and inside(u1):
                        segs.append((u0[0], u0[1], u1[0], u1[1], rad * 1.15, 2.6))
        self.segs = np.array(segs, np.float64)
        self.maxd = self.segs[:, 4].max() + 100

    def draw(self, cv, grow, scale=1.0, alpha=1.0):
        """grow 0..1 -> fraction of the network revealed (by distance from the impact point)."""
        if grow <= 0:
            return
        lim = grow * self.maxd
        cv.save()
        cv.clipPath(ellipse_path(BOWL_C, BOWL_R), skia.ClipOp.kIntersect, True)
        S = self.segs
        vis = S[S[:, 4] < lim]
        for layer, (rgb, a, wmul, dx) in enumerate((((0, 0, 0), 120, 1.9, 3.0), ((255, 255, 255), 50, 3.2, 0.0), ((235, 248, 255), 235, 1.0, 0.0))):
            for x0, y0, x1, y1, d, wd in vis:
                f = clamp((lim - d) / 120.0)
                ex, ey = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
                cv.drawLine(x0 + dx, y0 + dx, ex + dx, ey + dx, paint(col(*rgb, a * alpha), stroke=wd * wmul * scale))
        radial(cv, self.I[0], self.I[1], 120 * min(1, grow * 4), col(255, 255, 255, 170 * alpha))
        cv.restore()


# ------------------------------------------------------------------ the 3D jewel case
CASE_W, CASE_H, CASE_D = 142.0, 125.0, 10.4
FOCAL = 2400.0


def rot(yaw, pitch, roll):
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cr, sr = math.cos(roll), math.sin(roll)
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
    Rz = np.array([[cr, -sr, 0], [sr, cr, 0], [0, 0, 1]])
    return Ry @ Rx @ Rz


def project(P, cam):
    c = np.array([CASE_W / 2, CASE_H / 2, CASE_D / 2])
    X = (np.asarray(P, float) - c) @ rot(cam["yaw"], cam["pitch"], cam["roll"]).T
    X = X + np.array([cam["ox"], cam["oy"], cam["dist"]])
    return np.stack([W / 2 + FOCAL * X[:, 0] / X[:, 2], H / 2 + cam.get("sy", 0) + FOCAL * X[:, 1] / X[:, 2]], 1), X[:, 2]


def face_matrix(tex_w, tex_h, q):
    m = skia.Matrix()
    m.setPolyToPoly([skia.Point(0, 0), skia.Point(tex_w, 0), skia.Point(tex_w, tex_h), skia.Point(0, tex_h)], [skia.Point(*p) for p in q])
    return m


def draw_case(cv, A, cam, cracked=False, glare=0.0):
    Wc, Hc, Dc = CASE_W, CASE_H, CASE_D
    faces = [
        ("back", [(Wc, 0, Dc), (0, 0, Dc), (0, Hc, Dc), (Wc, Hc, Dc)]),
        ("left", [(0, 0, Dc), (0, 0, 0), (0, Hc, 0), (0, Hc, Dc)]),
        ("right", [(Wc, 0, 0), (Wc, 0, Dc), (Wc, Hc, Dc), (Wc, Hc, 0)]),
        ("top", [(0, 0, Dc), (Wc, 0, Dc), (Wc, 0, 0), (0, 0, 0)]),
        ("bottom", [(0, Hc, 0), (Wc, Hc, 0), (Wc, Hc, Dc), (0, Hc, Dc)]),
        ("front", [(0, 0, 0), (Wc, 0, 0), (Wc, Hc, 0), (0, Hc, 0)]),
    ]
    vis = []
    for name, P in faces:
        q, z = project(P, cam)
        area = sum(q[i][0] * q[(i + 1) % 4][1] - q[(i + 1) % 4][0] * q[i][1] for i in range(4))
        if area > 0:
            vis.append((z.mean(), name, q))
    vis.sort(key=lambda v: -v[0])
    for _, name, q in vis:
        if name == "front":
            tex = A.front_cracked() if cracked else A.front
            cv.save(); cv.concat(face_matrix(2840, 2500, q))
            cv.drawImage(tex, 0, 0, SAMP)
            p = skia.Paint(AntiAlias=True)                       # glossy plastic sheen that slides as the case turns
            gx = 2840 * (0.5 - cam["yaw"] * 2.2) + glare
            p.setShader(skia.GradientShader.MakeLinear([skia.Point(gx - 900, 0), skia.Point(gx + 900, 2500)],
                                                        [col(255, 255, 255, 0), col(255, 255, 255, 58), col(255, 255, 255, 0)], [0.35, 0.5, 0.65]))
            p.setBlendMode(skia.BlendMode.kScreen)
            cv.drawRect(skia.Rect.MakeWH(2840, 2500), p)
            cv.drawRect(skia.Rect.MakeLTRB(6, 6, 2834, 2494), paint(col(255, 255, 255, 90), stroke=10))
            cv.restore()
        elif name == "left":
            cv.save(); cv.concat(face_matrix(250, 3000, q))
            cv.drawImage(A.spine, 0, 0, SAMP)
            cv.drawRect(skia.Rect.MakeWH(250, 3000), paint(col(0, 0, 0, 40)))
            cv.restore()
        else:
            shade = {"right": 150, "top": 205, "bottom": 120, "back": 60}[name]
            cv.drawPath(poly(q), paint(col(shade, shade + 4, shade + 10, 235)))
            cv.drawPath(poly(q), paint(col(255, 255, 255, 70), stroke=2))


def case_cam(t):
    """Act 1 / Act 3 camera for the jewel case."""
    if t < T_SWITCH_IN:
        u = ease(clamp((t - 0.6) / (T_SWITCH_IN - 0.6)))
        yaw = math.radians(38 * (1 - u) ** 1.4 + 2.5 * math.sin(t * 0.9) * (1 - u))
        pitch = math.radians(-7 * (1 - u) + 1.0 * math.sin(t * 0.7) * (1 - u))
        roll = math.radians(-3 * (1 - u))
        dist = 272 + 380 * (1 - ease(clamp((t - 0.6) / (T_SWITCH_IN - 0.6)))) ** 1.6
        ox = -11.0 * ease(clamp((t - 5.0) / 4.0))
        oy = 6 * math.sin(t * 1.3) * (1 - u)
        return dict(yaw=yaw, pitch=pitch, roll=roll, dist=dist, ox=ox, oy=oy)
    u = ease(clamp((t - T_SWITCH_OUT) / 5.5))
    yaw = math.radians(-24 * u)
    pitch = math.radians(5 * u)
    dist = 272 + 420 * u
    ox = -11.0 * (1 - u)
    oy = -4 * u + 3 * math.sin(t * 1.2) * u
    return dict(yaw=yaw, pitch=pitch, roll=0.0, dist=dist, ox=ox, oy=oy)


# ------------------------------------------------------------------ stage (acts 1 and 3)
def stage(cv, t, light):
    p = skia.Paint()
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(W / 2, H * 0.42), H * 0.8, [col(34, 24, 46), col(8, 6, 14), col(0, 0, 0)], [0, 0.55, 1]))
    cv.drawRect(skia.Rect.MakeWH(W, H), p)
    for k in range(16):                                           # far stadium bokeh
        x = hsh(k * 3.1) * W; y = 120 + hsh(k * 7.7) * 700
        c = [(255, 60, 60), (255, 230, 200), (120, 160, 255)][k % 3]
        tw = 0.6 + 0.4 * math.sin(t * (1.2 + hsh(k)) + k)
        radial(cv, x, y, 30 + 50 * hsh(k * 1.9), col(*c, 60 * tw * light))
    if light > 0:                                                 # the spotlight cone
        q = skia.Paint(AntiAlias=True)
        q.setShader(skia.GradientShader.MakeLinear([skia.Point(0, -100), skia.Point(0, H * 0.95)],
                                                    [col(255, 236, 210, 95 * light), col(255, 236, 210, 0)]))
        q.setBlendMode(skia.BlendMode.kPlus)
        cv.drawPath(poly([(W / 2 - 90, -100), (W / 2 + 90, -100), (W / 2 + 640, H * 0.95), (W / 2 - 640, H * 0.95)]), q)
        radial(cv, W / 2, H * 0.84, 520, col(255, 220, 190, 70 * light))
    for k in range(70):                                           # haze motes in the beam
        u = (hsh(k * 2.3) + t * (0.012 + 0.02 * hsh(k * 5.1))) % 1.0
        x = W / 2 + (hsh(k * 9.7) - 0.5) * 900 * (0.3 + u) + 30 * math.sin(t * 0.5 + k)
        y = H * (0.05 + 0.85 * ((hsh(k * 4.4) + t * 0.01) % 1.0))
        radial(cv, x, y, 2 + 5 * hsh(k * 6.6), col(255, 240, 220, 120 * light * (0.4 + 0.6 * hsh(k * 8.8))))
    heads(cv, t, light)


def heads(cv, t, light):
    """A front row of crowd silhouettes along the bottom, with camera flashes."""
    for k in range(12):
        x = -40 + k * 100 + 30 * hsh(k * 2.2)
        y = H - 40 + 14 * math.sin(t * 2.2 + k * 1.7)
        r = 70 + 18 * hsh(k * 3.3)
        cv.drawCircle(x, y - r * 0.6, r * 0.55, paint(col(6, 4, 10)))
        cv.drawRect(skia.Rect.MakeLTRB(x - r * 0.9, y - r * 0.15, x + r * 0.9, H + 20), paint(col(6, 4, 10)))
        if light > 0 and (t * 3 + hsh(k * 9.1) * 7) % 7 < 0.12:
            radial(cv, x + 20, y - r, 70, col(255, 255, 255, 170))


# ------------------------------------------------------------------ act 2 camera
KEYS = [
    (9.0, 1440, 1440, 0.375), (11.4, 1372, 1450, 0.74), (13.0, 1330, 1380, 0.78),
    (15.0, 790, 650, 0.98), (18.6, 1880, 610, 0.98),
    (21.2, 520, 1240, 1.02), (24.6, 590, 1300, 1.10),
    (26.8, 2380, 1180, 0.98), (30.6, 2430, 1260, 1.06),
    (33.2, 1320, 1290, 1.12), (37.6, 1350, 1330, 1.24),
    (39.6, 640, 2370, 1.06), (41.7, 2230, 2400, 1.00), (43.6, 2290, 2370, 1.04),
    (45.2, 1372, 1470, 0.76), (49.8, 1372, 1440, 0.84), (50.6, 1380, 1440, 0.90),
    (51.9, 1440, 1440, 0.52), (52.5, 1440, 1440, 0.375),
]


def act2_cam(t):
    ks = KEYS
    if t <= ks[0][0]:
        return ks[0][1:]
    if t >= ks[-1][0]:
        return ks[-1][1:]
    i = max(j for j in range(len(ks) - 1) if ks[j][0] <= t)
    t0, t1 = ks[i][0], ks[i + 1][0]
    u = (t - t0) / (t1 - t0)

    def val(k, d):
        return math.log(ks[k][3]) if d == 2 else ks[k][1 + d]

    out = []
    for d in range(3):
        p0, p1 = val(i, d), val(i + 1, d)
        m0 = (val(min(i + 1, len(ks) - 1), d) - val(max(i - 1, 0), d)) / (ks[min(i + 1, len(ks) - 1)][0] - ks[max(i - 1, 0)][0]) * (t1 - t0) * 0.5
        m1 = (val(min(i + 2, len(ks) - 1), d) - val(i, d)) / (ks[min(i + 2, len(ks) - 1)][0] - ks[i][0]) * (t1 - t0) * 0.5
        if i == 0:
            m0 = 0.0
        if i + 1 == len(ks) - 1:
            m1 = 0.0
        h00, h10, h01, h11 = 2 * u ** 3 - 3 * u ** 2 + 1, u ** 3 - 2 * u ** 2 + u, -2 * u ** 3 + 3 * u ** 2, u ** 3 - u ** 2
        out.append(h00 * p0 + h10 * m0 + h01 * p1 + h11 * m1)
    return out[0], out[1], math.exp(out[2])


PARALLAX = {"bg": 0.0, "title": 0.10, "sign1": 0.14, "sign2": 0.17, "bowl": 0.20, "flag": 0.20, "suits": 0.26, "ticket_cancel": 0.0}


def layer_xform(cv, cam, p, shake=(0.0, 0.0)):
    cx, cy, z = cam
    zl = z * (z / 0.375) ** (p * 0.10)
    clx = cx + (cx - 1440) * p * 0.12
    cly = cy + (cy - 1440) * p * 0.12
    cv.translate(W / 2 + shake[0], H / 2 + shake[1])
    cv.scale(zl, zl)
    cv.translate(-clx, -cly)
    return zl


def jab(t):
    v = 0.0
    if 19.0 < t < 26.0:
        tb = 19.3 + round((t - 19.3) / 0.62) * 0.62
        v = math.exp(-((t - tb) / 0.07) ** 2)
    else:
        tb = round(t / 2.48) * 2.48
        v = 0.5 * math.exp(-((t - tb) / 0.09) ** 2)
    return v


def pump(t, ph):
    on = 1.0 if 25.5 < t < 32.0 else 0.45
    x = math.sin(2 * math.pi * (t * 1.6 + ph))
    return on * max(0.0, x) ** 1.5


def slam_scale(t):
    """CANCELLED ticket: lifts toward camera, then slams down at T_SLAM."""
    if t < T_SLAM - 0.75 or t > T_SLAM + 0.6:
        return 1.0, 0.0
    if t < T_SLAM - 0.13:
        u = ease((t - (T_SLAM - 0.75)) / 0.62)
        return 1.0 + 0.42 * u, -9 * u
    if t < T_SLAM:
        u = ease_in((t - (T_SLAM - 0.13)) / 0.13)
        return 1.42 - 0.47 * u, -9 * (1 - u)
    u = (t - T_SLAM) / 0.6
    return 0.95 + 0.05 * (1 - math.exp(-u * 6) * math.cos(u * 18)), 0.0


def shake_at(t):
    a = 0.0
    if T_SLAM <= t < T_SLAM + 0.5:
        a += 26 * math.exp(-(t - T_SLAM) * 9)
    if T_CRACK0 <= t < T_SHATTER:
        a += 3 + 6 * ((t - T_CRACK0) / (T_SHATTER - T_CRACK0)) ** 2
    if T_SHATTER <= t < T_SHATTER + 1.2:
        a += 46 * math.exp(-(t - T_SHATTER) * 4)
    if a <= 0:
        return (0.0, 0.0)
    return ((hsh(t * 97.1) - 0.5) * 2 * a, (hsh(t * 51.7 + 3) - 0.5) * 2 * a)


def draw_layer(cv, A, name, extra=None):
    img, w_, h_ = A.layers[name]
    ox, oy = A.offs[name]
    cv.save()
    if extra is not None:
        extra(cv)
    cv.drawImage(img, ox, oy, SAMP)
    cv.restore()


def draw_flag(cv, A, t):
    img, w_, h_ = A.layers["flag"]
    ox, oy = A.offs["flag"]
    n = 40
    for i in range(n):
        u0, u1 = i / n, (i + 1) / n
        u = (u0 + u1) / 2
        amp = 22 * u ** 1.2
        dy = amp * math.sin(2 * math.pi * (t * 1.1 - u * 1.3))
        dx = -6 * u * (1 + math.sin(2 * math.pi * (t * 1.1 - u * 1.3 + 0.25))) * 0.5
        src = skia.Rect.MakeLTRB(u0 * w_, 0, u1 * w_ + 1.2, h_)
        dst = skia.Rect.MakeLTRB(ox + u0 * w_ + dx, oy + dy, ox + u1 * w_ + 1.2 + dx, oy + h_ + dy)
        cv.drawImageRect(img, src, dst, SAMP)


def title_extras(cv, A, t):
    """Fresh red paint keeps dripping off the letters; the title throbs with a red glow."""
    gimg, gw, gh, tw, th = A.title_glow
    a = 0.35 + 0.25 * math.sin(t * 2.6) + (0.4 if 13.5 < t < 19 else 0.0) * (0.5 + 0.5 * math.sin(t * 8))
    p = skia.Paint(); p.setAlphaf(clamp(a * 0.8)); p.setBlendMode(skia.BlendMode.kPlus)
    cv.drawImageRect(gimg, skia.Rect.MakeWH(gw, gh), skia.Rect.MakeWH(tw, th), SAMP, p)
    drips = [(178, 520, 9.0, 260), (395, 470, 10.5, 170), (868, 552, 12.0, 220), (1290, 486, 11.2, 190), (1652, 512, 13.8, 240), (2238, 560, 14.5, 260)]
    for k, (x, y0, t0, L) in enumerate(drips):
        if t < t0:
            continue
        u = ease_out((t - t0) / 5.5)
        ln = L * u
        wd = 22 - 4 * (k % 2)
        path = skia.Path()
        path.moveTo(x - wd / 2, y0); path.lineTo(x + wd / 2, y0)
        path.cubicTo(x + wd * 0.4, y0 + ln * 0.5, x + wd * 0.3, y0 + ln * 0.8, x + wd * 0.45, y0 + ln)
        path.lineTo(x - wd * 0.45, y0 + ln)
        path.cubicTo(x - wd * 0.3, y0 + ln * 0.8, x - wd * 0.4, y0 + ln * 0.5, x - wd / 2, y0)
        cv.drawPath(path, paint(col(150, 14, 20)))
        cv.drawCircle(x, y0 + ln, wd * 0.62, paint(col(150, 14, 20)))
        cv.drawLine(x - wd * 0.15, y0 + 6, x - wd * 0.12, y0 + ln - 6, paint(col(255, 120, 110, 110), stroke=3))
        cv.drawCircle(x - wd * 0.18, y0 + ln - wd * 0.15, wd * 0.18, paint(col(255, 170, 160, 150)))
        cyc = (t - t0 - 4.0) % 3.7                                # a drop detaches and falls
        if t - t0 > 4.0 and cyc < 0.9:
            fy = y0 + ln + 30 + 900 * cyc ** 2
            cv.drawCircle(x, fy, wd * 0.45, paint(col(150, 14, 20)))


def crowd_flashes(cv, t, rate):
    """Photographers in the stands: deterministic flash events."""
    n = int(rate * 1.2)
    for k in range(n):
        period = 1.2
        ph = hsh(k * 13.7)
        tk = math.floor((t + ph * period) / period)
        local = (t + ph * period) - tk * period
        if local > 0.16:
            continue
        sd = k * 31.3 + tk * 7.77
        x = 60 + hsh(sd) * 2760; y = 600 + hsh(sd + 1.1) * 1250
        if ((x - BOWL_C[0]) / BOWL_R[0]) ** 2 + ((y - BOWL_C[1]) / BOWL_R[1]) ** 2 < 1.0:
            continue
        a = 1.0 - local / 0.16
        r = 26 + 26 * hsh(sd + 2.2)
        radial(cv, x, y, r * 3.2, col(255, 255, 255, 230 * a))
        cv.drawLine(x - r * 2.6, y, x + r * 2.6, y, paint(col(255, 255, 255, 200 * a), stroke=4, blend=skia.BlendMode.kPlus))
        cv.drawLine(x, y - r * 1.8, x, y + r * 1.8, paint(col(255, 255, 255, 170 * a), stroke=3, blend=skia.BlendMode.kPlus))


def beams(cv, t, a):
    for k, (sx, sy, base, sweep, sp) in enumerate(((2620, 470, 112, 16, 0.31), (300, 520, 66, 14, 0.27), (1500, 300, 92, 22, 0.21))):
        ang = math.radians(base + sweep * math.sin(t * sp * 2 * math.pi * 0.5 + k))
        spread = math.radians(9)
        L = 2600
        p1 = (sx + L * math.cos(ang - spread), sy + L * math.sin(ang - spread))
        p2 = (sx + L * math.cos(ang + spread), sy + L * math.sin(ang + spread))
        q = skia.Paint(AntiAlias=True)
        q.setShader(skia.GradientShader.MakeRadial(skia.Point(sx, sy), L, [col(255, 238, 215, 70 * a), col(255, 238, 215, 0)]))
        q.setBlendMode(skia.BlendMode.kPlus)
        cv.drawPath(poly([(sx, sy), p1, p2]), q)
        radial(cv, sx, sy, 90, col(255, 245, 230, 200 * a))


def stadium_twinkle(cv, t):
    for k in range(14):
        x = 2440 + hsh(k * 1.7) * 420; y = 500 + hsh(k * 2.9) * 90
        tw = max(0.0, math.sin(t * (2 + 3 * hsh(k)) + k * 2.1)) ** 3
        radial(cv, x, y, 40 + 30 * tw, col(255, 250, 235, 200 * tw))


def glass_fx(cv, t, boost=0.0):
    cv.save()
    cv.clipPath(ellipse_path(BOWL_C, BOWL_R), skia.ClipOp.kIntersect, True)
    period = 5.5
    u = ((t - 9.5) % period) / 2.2
    if u < 1.0:
        x = BOWL_C[0] - 1300 + 2600 * ease(u)
        p = skia.Paint(AntiAlias=True)
        p.setShader(skia.GradientShader.MakeLinear([skia.Point(x - 260, BOWL_C[1] - 500), skia.Point(x + 260, BOWL_C[1] + 300)],
                                                    [col(255, 255, 255, 0), col(255, 255, 255, 105 + 60 * boost), col(255, 255, 255, 0)]))
        p.setBlendMode(skia.BlendMode.kScreen)
        cv.drawRect(skia.Rect.MakeLTRB(BOWL_C[0] - BOWL_R[0], BOWL_C[1] - BOWL_R[1], BOWL_C[0] + BOWL_R[0], BOWL_C[1] + BOWL_R[1]), p)
    cv.restore()
    a = t * 0.9                                                    # a glint that runs round the rim
    gx, gy = RIM_C[0] + RIM_R[0] * math.cos(a), RIM_C[1] + RIM_R[1] * math.sin(a)
    tw = 0.6 + 0.4 * math.sin(t * 5)
    radial(cv, gx, gy, 70, col(255, 255, 255, 220 * tw))
    cv.drawLine(gx - 110, gy, gx + 110, gy, paint(col(255, 255, 255, 170 * tw), stroke=4, blend=skia.BlendMode.kPlus))
    cv.drawLine(gx, gy - 80, gx, gy + 80, paint(col(255, 255, 255, 150 * tw), stroke=3, blend=skia.BlendMode.kPlus))


def pedal_sparks(cv, t, a):
    cx, cy = 520.0, 2410.0
    k = int(t * 12)
    if hsh(k * 3.3) < 0.55:
        for j in range(2):
            sd = k * 7.1 + j * 3.3
            p0 = np.array([cx + (hsh(sd) - 0.5) * 180, cy + (hsh(sd + 1) - 0.5) * 90])
            p1 = p0 + np.array([(hsh(sd + 2) - 0.5) * 260, (hsh(sd + 3) - 0.6) * 200])
            pts = [p0]
            for i in range(1, 8):
                f = i / 8
                q = p0 + (p1 - p0) * f + np.array([(hsh(sd + i * 1.7) - 0.5) * 50, (hsh(sd + i * 2.3) - 0.5) * 50])
                pts.append(q)
            pts.append(p1)
            path = skia.Path(); path.moveTo(*pts[0])
            for q in pts[1:]:
                path.lineTo(*q)
            cv.drawPath(path, paint(col(120, 200, 255, 120 * a), stroke=16, blend=skia.BlendMode.kPlus))
            cv.drawPath(path, paint(col(230, 245, 255, 255 * a), stroke=4, blend=skia.BlendMode.kPlus))
            radial(cv, p0[0], p0[1], 60, col(160, 220, 255, 200 * a))
    for i in range(18):                                            # sparks: little ballistic embers
        life = 0.9
        ph = hsh(i * 5.3)
        u = ((t + ph * life) % life) / life
        sd = math.floor((t + ph * life) / life) * 3.1 + i
        vx, vy = (hsh(sd) - 0.5) * 900, -300 - 500 * hsh(sd + 1)
        x = cx + vx * u * life; y = cy + vy * u * life + 1400 * (u * life) ** 2
        radial(cv, x, y, 14 * (1 - u) + 4, col(255, 200, 90, 255 * (1 - u) * a))


def floor_glints(cv, t):
    for k, (x, y) in enumerate(((452, 1968), (2300, 2052), (2560, 2180), (1200, 2688), (2272, 2740), (920, 2440), (1720, 2010))):
        tw = max(0.0, math.sin(t * (1.5 + hsh(k)) * 2 + k * 1.9)) ** 6
        if tw > 0.02:
            radial(cv, x, y, 40, col(255, 255, 255, 230 * tw))
            cv.drawLine(x - 70 * tw, y, x + 70 * tw, y, paint(col(255, 255, 255, 220 * tw), stroke=3, blend=skia.BlendMode.kPlus))
            cv.drawLine(x, y - 50 * tw, x, y + 50 * tw, paint(col(255, 255, 255, 200 * tw), stroke=3, blend=skia.BlendMode.kPlus))


def slam_fx(cv, t):
    if not (T_SLAM <= t < T_SLAM + 1.0):
        return
    u = (t - T_SLAM) / 1.0
    cx, cy = 2390.0, 2380.0
    radial(cv, cx, cy, 300 + 600 * u, col(255, 40, 40, 150 * (1 - u)))
    for k in range(26):                                            # dust puff
        ang = hsh(k * 2.7) * 2 * math.pi
        sp = 300 + 700 * hsh(k * 4.1)
        x = cx + math.cos(ang) * sp * ease_out(u) * 1.2
        y = cy + math.sin(ang) * sp * ease_out(u) * 0.45 - 120 * u
        radial(cv, x, y, 50 + 90 * u, col(190, 170, 150, 120 * (1 - u)), blend=None)


def dust(cv, t, a=1.0):
    for k in range(90):
        z = 0.3 + 0.7 * hsh(k * 1.3)
        x = (hsh(k * 2.1) * W + t * 12 * z + 40 * math.sin(t * 0.3 + k)) % (W + 80) - 40
        y = (hsh(k * 3.7) * H - t * 18 * z) % (H + 80) - 40
        r = 1.5 + 6 * z ** 2
        radial(cv, x, y, r * 2.2, col(255, 236, 210, 110 * a * (0.3 + 0.7 * hsh(k * 5.9))))


class Shards:
    def __init__(self, seed=9):
        rng = np.random.default_rng(seed)
        self.items = []
        for k in range(80):
            ang = rng.uniform(0, 2 * math.pi)
            r0 = math.sqrt(rng.uniform(0, 1))
            x0 = BOWL_C[0] + math.cos(ang) * BOWL_R[0] * r0 * 0.9
            y0 = BOWL_C[1] + math.sin(ang) * BOWL_R[1] * r0 * 0.9
            sz = rng.uniform(40, 200)
            pts = [(math.cos(a) * sz * rng.uniform(0.5, 1.0), math.sin(a) * sz * rng.uniform(0.5, 1.0))
                   for a in sorted(rng.uniform(0, 2 * math.pi, int(rng.integers(3, 6))))]
            v = (math.cos(ang) * rng.uniform(600, 2400), math.sin(ang) * rng.uniform(600, 2400) - 300)
            self.items.append((x0, y0, pts, v, rng.uniform(-6, 6), rng.uniform(0.6, 2.4)))

    def draw(self, cv, t):
        u = t - T_SHATTER
        if u < 0 or u > 1.9:
            return
        for x0, y0, pts, v, spin, grow in self.items:
            s = 1 + grow * u * 1.6
            x = x0 + v[0] * u; y = y0 + v[1] * u + 900 * u * u
            a = clamp(1 - u / 1.9)
            cv.save(); cv.translate(x, y); cv.rotate(math.degrees(spin * u)); cv.scale(s, s)
            path = poly(pts)
            cv.drawPath(path, paint(col(200, 232, 255, 70 * a)))
            cv.drawPath(path, paint(col(255, 255, 255, 230 * a), stroke=3.5))
            cv.drawLine(pts[0][0] * 0.6, pts[0][1] * 0.6, pts[1][0] * 0.2, pts[1][1] * 0.2, paint(col(255, 255, 255, 200 * a), stroke=5))
            cv.restore()


SHARDS = Shards()


def cover_world(cv, A, t):
    cx, cy, z = act2_cam(t)
    sh = shake_at(t)
    if z < 0.72:                                                   # outside the art: the stage + the case surround
        stage(cv, t, 1.0)
        cv.save(); layer_xform(cv, (cx, cy, z), 0.0, sh)
        cv.translate(-528, -60); cv.scale(1.2, 1.2)
        cv.drawImage(A.front_cracked() if t > T_SHATTER else A.front, 0, 0, SAMP)
        cv.restore()
    cam = (cx, cy, z)
    cv.save(); layer_xform(cv, cam, 0.0, sh)
    cv.clipRect(skia.Rect.MakeWH(ART, ART))
    cv.drawImage(A.bg, 0, 0, SAMP)
    rate = 7 + (12 if 25 < t < 32 else 0) + (16 * clamp((t - T_CRACK0) / 4) if t > T_CRACK0 else 0)
    crowd_flashes(cv, t, rate)
    beams(cv, t, 0.8 if t < T_CRACK0 else 0.8 + 0.4 * math.sin(t * 20) ** 2)
    stadium_twinkle(cv, t)
    cv.restore()

    def L(name, fn=None, p=None):
        cv.save(); layer_xform(cv, cam, PARALLAX[name] if p is None else p, sh)
        cv.clipRect(skia.Rect.MakeWH(ART, ART))
        if fn is None:
            draw_layer(cv, A, name)
        else:
            fn()
        cv.restore()

    def title():
        draw_layer(cv, A, "title", lambda c: c.translate(0, 5 * math.sin(t * 1.4)))
        title_extras(cv, A, t)
    L("title", title)

    def bowl():
        bs = (hsh(t * 33) - 0.5) * 6 * clamp((t - T_CRACK0) / 5) if T_CRACK0 < t < T_SHATTER else 0
        draw_layer(cv, A, "bowl", lambda c: c.translate(bs, 0))
        glass_fx(cv, t, boost=1.0 if 31 < t < 38 else 0.0)
        if t > T_CRACK0:
            g = 1.0 if t > T_SHATTER else ease_in(clamp((t - T_CRACK0) / (T_SHATTER - T_CRACK0 - 0.1))) ** 0.6
            A.cracks.draw(cv, g, scale=1.0)
    L("bowl", bowl)
    L("flag", lambda: draw_flag(cv, A, t))

    def sign(name, pivot, ph):
        def f():
            v = pump(t, ph)
            draw_layer(cv, A, name, lambda c: (c.translate(0, -34 * v), c.rotate(2.2 * math.sin(2 * math.pi * (t * 0.8 + ph)), pivot[0], pivot[1])))
        return f
    L("sign1", sign("sign1", (2430, 1250), 0.0))
    L("sign2", sign("sign2", (2500, 1935), 0.37))

    def suits():
        j = jab(t)
        s = 1 + 0.022 * j + 0.005 * math.sin(t * 1.3)
        draw_layer(cv, A, "suits", lambda c: (c.translate(16 * j, 0), c.scale(s, s)))
        if 19 < t < 26.5:
            radial(cv, 420, 1100, 520, col(255, 30, 30, 70 + 60 * j))
    L("suits", suits)

    def floor():
        sc, ang = slam_scale(t)
        draw_layer(cv, A, "ticket_cancel", lambda c: (c.translate(2390, 2380), c.rotate(ang), c.scale(sc, sc), c.translate(-2390, -2380)))
        pedal_sparks(cv, t, 1.0 if 38 < t < 44 else 0.55)
        floor_glints(cv, t)
        slam_fx(cv, t)
    L("ticket_cancel", floor)
    cv.save(); layer_xform(cv, cam, 0.3, sh)
    SHARDS.draw(cv, t)
    cv.restore()
    dust(cv, t, 0.8)


# ------------------------------------------------------------------ frame assembly + post
VIGN = None
RNG_GRAIN = np.random.default_rng(3)


def post(a, t):
    global VIGN
    if VIGN is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2)
        VIGN = np.clip(1.15 - 0.55 * d ** 2, 0.25, 1.0)[..., None]
    out = a.astype(np.float32) * VIGN
    ca = 0.0
    if T_SLAM <= t < T_SLAM + 0.3:
        ca = 8 * (1 - (t - T_SLAM) / 0.3)
    if T_SHATTER <= t < T_SHATTER + 0.8:
        ca = max(ca, 18 * (1 - (t - T_SHATTER) / 0.8))
    if ca > 0.5:
        k = int(ca)
        out[:, :, 0] = np.roll(out[:, :, 0], k, axis=1)
        out[:, :, 2] = np.roll(out[:, :, 2], -k, axis=1)
    g = RNG_GRAIN.normal(0, 5.5, (H // 2, W // 2, 1)).astype(np.float32).repeat(2, 0).repeat(2, 1)
    out += g
    fl = 0.0
    if T_SHATTER <= t < T_SHATTER + 0.6:
        fl = math.exp(-(t - T_SHATTER) * 7)
    if abs(t - (T_SWITCH_IN - 0.25)) < 0.25:
        fl = max(fl, 0.65 * (1 - abs(t - (T_SWITCH_IN - 0.25)) / 0.25))
    if 0.95 <= t < 1.3:
        fl = max(fl, 0.35 * (1 - (t - 0.95) / 0.35))
    if fl > 0:
        out = out * (1 - fl) + 255 * fl
    if t < 1.0:
        out *= ease(t / 1.0) * 0.0 + (0.0 if t < 0.95 else 1.0)
    if t > DUR - 2.0:
        out *= clamp((DUR - t) / 2.0)
    return np.clip(out, 0, 255).astype(np.uint8)


def frame(A, t):
    surf = skia.Surface.MakeRaster(skia.ImageInfo.Make(W, H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType))
    cv = surf.getCanvas()
    cv.clear(col(0, 0, 0))
    if T_SWITCH_IN <= t < T_SWITCH_OUT:
        cover_world(cv, A, t)
    else:
        light = 1.0 if t >= 0.95 else 0.0
        stage(cv, t, light)
        cam = case_cam(t)
        q, _ = project([(0, 125, 0), (142, 125, 0), (142, 125, 10.4), (0, 125, 10.4)], cam)
        fy = q[:, 1].max()
        sh = skia.Paint(AntiAlias=True)
        sh.setShader(skia.GradientShader.MakeRadial(skia.Point(W / 2, fy + 30), 420, [col(0, 0, 0, 200), col(0, 0, 0, 0)]))
        cv.save(); cv.scale(1, 0.18); cv.drawCircle(W / 2, (fy + 30) / 0.18, 420, sh); cv.restore()
        rec = skia.PictureRecorder()
        rc = rec.beginRecording(skia.Rect.MakeWH(W, H))
        draw_case(rc, A, cam, cracked=t >= T_SWITCH_OUT, glare=(t - 4.0) * 260 if t < T_SWITCH_IN else 0.0)
        pic = rec.finishRecordingAsPicture()
        cv.save()                                                  # floor reflection
        cv.translate(0, 2 * fy + 20); cv.scale(1, -1)
        lp = skia.Paint(); lp.setAlphaf(0.22)
        cv.saveLayer(None, lp)
        cv.drawPicture(pic)
        mp = skia.Paint()
        mp.setShader(skia.GradientShader.MakeLinear([skia.Point(0, fy), skia.Point(0, fy - 380)], [col(0, 0, 0, 255), col(0, 0, 0, 0)]))
        mp.setBlendMode(skia.BlendMode.kDstIn)
        cv.drawRect(skia.Rect.MakeWH(W, H), mp)
        cv.restore(); cv.restore()
        cv.drawPicture(pic)
        if t >= T_SWITCH_OUT:                                      # the title on the case keeps glowing red
            radial(cv, W / 2, H * 0.34, 520, col(255, 30, 30, 40 + 20 * math.sin(t * 3)))
        dust(cv, t, 0.6 * light)
    a = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)[:, :, :3]
    return post(a, t)


# ------------------------------------------------------------------ drivers
def render_range(a, b, path):
    A = Assets()
    p = subprocess.Popen([FF, "-y", "-v", "error", "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", f"{W}x{H}", "-framerate", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-crf", "15", "-preset", "medium", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    t0 = time.time()
    for f in range(a, b):
        p.stdin.write(np.ascontiguousarray(frame(A, f / FPS)).tobytes())
        if (f - a) % 48 == 0:
            print(f"[{a}-{b}] f={f} {(time.time() - t0) / max(1, f - a + 1):.2f}s/frame", flush=True)
    p.stdin.close(); p.wait()


def main_full(nw=4):
    out = os.path.join(HERE, "out"); os.makedirs(out, exist_ok=True)
    n = int(DUR * FPS)
    cuts = [round(n * k / nw) for k in range(nw + 1)]
    env = dict(os.environ)
    procs, segs = [], []
    for k in range(nw):
        seg = os.path.join(out, f"seg{k}.mp4"); segs.append(seg)
        procs.append(subprocess.Popen([sys.executable, __file__, "--range", str(cuts[k]), str(cuts[k + 1]), seg], env=env))
    codes = [p.wait() for p in procs]
    if any(codes):
        raise SystemExit(f"worker failed {codes}")
    with open(os.path.join(out, "segs.txt"), "w") as f:
        for s in segs:
            f.write(f"file '{s}'\n")
    subprocess.run([FF, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(out, "segs.txt"), "-c", "copy", os.path.join(out, "video.mp4")], check=True)
    print("VIDEO ->", os.path.join(out, "video.mp4"))


def stills(times):
    A = Assets()
    od = os.path.join(HERE, "stills"); os.makedirs(od, exist_ok=True)
    for tt in times:
        t0 = time.time()
        Image.fromarray(frame(A, float(tt))).save(os.path.join(od, f"still_{float(tt):05.2f}.png"))
        print(f"still {tt} ({time.time() - t0:.2f}s)", flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--range":
        render_range(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
    elif len(sys.argv) > 1 and sys.argv[1] == "--stills":
        stills(sys.argv[2:])
    else:
        main_full()
