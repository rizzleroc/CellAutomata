"""A 4K seamless beauty loop: a crystalline journey — dendritic trees / frost
ferns, 6- and 12-fold snowflakes, and odd soliton crystals — folded from live
reaction-diffusion. Perfectly seamless via a wrap-crossfade of the final frames
back to frame 0. Streamed at 2160x2160.

  python3 tools/beauty_loop.py --out media/beauty_loop_4k.mp4
"""
from __future__ import annotations
import argparse, os
import numpy as np
from PIL import Image
import imageio_ffmpeg
from cellauto.engine import Engine
from cellauto.rules import REGISTRY

RULE = "abiogenesis-stage1-grayscott"


def lut(stops):
    g = np.linspace(0, 1, 256); xs = np.array([s[0] for s in stops])
    cols = np.array([s[1] for s in stops], float)
    return np.stack([np.interp(g, xs, cols[:, c]) for c in range(3)], 1).astype(np.uint8)


PAL = {
    "pine":  lut([(0, (2, 8, 6)), (.3, (8, 60, 38)), (.55, (40, 150, 96)), (.8, (150, 225, 160)), (1, (235, 255, 235))]),
    "frost": lut([(0, (2, 6, 16)), (.3, (16, 70, 140)), (.6, (90, 180, 245)), (.82, (185, 230, 255)), (1, (245, 252, 255))]),
    "ice":   lut([(0, (3, 5, 14)), (.25, (8, 34, 90)), (.5, (16, 110, 190)), (.75, (110, 220, 245)), (1, (230, 250, 255))]),
    "amethyst": lut([(0, (6, 2, 14)), (.3, (60, 18, 110)), (.6, (150, 70, 210)), (.82, (210, 150, 245)), (1, (245, 235, 255))]),
    "gold":  lut([(0, (4, 3, 1)), (.25, (70, 40, 6)), (.5, (180, 120, 20)), (.75, (245, 200, 70)), (1, (255, 250, 215))]),
}

# (engine key, symmetry order, palette) — the loop's phases
PHASES = [("tree", 6, "pine"), ("flake", 6, "frost"), ("flake2", 12, "ice"), ("oddity", 5, "amethyst")]
ENGINES = {
    "tree":   dict(kw=dict(F=0.0545, k=0.062), warm=540, scatter=False),
    "flake":  dict(kw=dict(F=0.026, k=0.055), warm=440, scatter=False),
    "flake2": dict(kw=dict(preset="labyrinth"), warm=460, scatter=False),
    "oddity": dict(kw=dict(F=0.018, k=0.050), warm=520, scatter=True),
}


def make_engine(spec, grid):
    eng = Engine(width=grid, height=grid, rule=REGISTRY[RULE](**spec["kw"]), seed=1)
    if spec["scatter"]:
        rng = np.random.default_rng(5); u = np.ones((grid, grid), np.float32); v = np.zeros((grid, grid), np.float32); r = 5
        for _ in range(grid // 9):
            cy = int(rng.integers(r, grid - r)); cx = int(rng.integers(r, grid - r))
            u[cy - r:cy + r, cx - r:cx + r] = 0.5; v[cy - r:cy + r, cx - r:cx + r] = 0.25
        v += rng.uniform(0, 0.02, (grid, grid)).astype(np.float32)
        eng.state.u = u; eng.state.v = np.clip(v, 0, 1)
    for _ in range(spec["warm"]):
        eng.step()
    return eng


class Kal:
    def __init__(self, K, G):
        yy, xx = np.mgrid[0:K, 0:K]; c = K / 2.0
        self.R = np.hypot(xx - c, yy - c).astype(np.float32)
        self.TH = np.arctan2(yy - c, xx - c).astype(np.float32)
        self.mask = np.clip((0.985 - self.R / (K / 2.0)) / 0.05, 0, 1).astype(np.float32)
        self.scale = G / float(K); self.G = G

    def fold(self, V, n, phase, zoom):
        wedge = 2 * np.pi / n
        a = np.mod(self.TH + phase, wedge); a = np.minimum(a, wedge - a)
        rr = self.R * self.scale * zoom; G = self.G
        sx = np.clip(G / 2 + rr * np.cos(a), 0, G - 1.001)
        sy = np.clip(G / 2 + rr * np.sin(a), 0, G - 1.001)
        x0 = sx.astype(np.int32); y0 = sy.astype(np.int32); fx = sx - x0; fy = sy - y0
        f = (V[y0, x0] * (1 - fx) * (1 - fy) + V[y0, x0 + 1] * fx * (1 - fy)
             + V[y0 + 1, x0] * (1 - fx) * fy + V[y0 + 1, x0 + 1] * fx * fy)
        return f * self.mask


def colorize(field, pal, gamma=0.72):
    pos = field[field > 0.02]
    hi = np.percentile(pos, 99.5) if pos.size else 1.0
    f = np.clip(field / (hi + 1e-6), 0, 1) ** gamma
    return PAL[pal][(f * 255).astype(np.uint8)].astype(np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--K", type=int, default=2160)
    ap.add_argument("--foldK", type=int, default=1100, help="kaleidoscope render res, upscaled to K")
    ap.add_argument("--grid", type=int, default=220)
    ap.add_argument("--dur", type=float, default=22)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--out", default="media/beauty_loop_4k.mp4")
    a = ap.parse_args()

    print("warming engines ...")
    engs = {k: make_engine(s, a.grid) for k, s in ENGINES.items()}
    kal = Kal(a.foldK, a.grid)
    N = int(a.dur * a.fps)
    seg = N / len(PHASES)
    xf = int(1.2 * a.fps)
    L = int(1.6 * a.fps)   # wrap-crossfade length

    def fld(key, n, rot, zoom):
        v = np.asarray(engs[key].state.v, np.float32)
        v = v / (v.max() + 1e-6)
        return kal.fold(v, n, rot, zoom)

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    wr = imageio_ffmpeg.write_frames(a.out, (a.K, a.K), fps=a.fps, codec="libx264",
        pix_fmt_in="rgb24", pix_fmt_out="yuv420p", macro_block_size=2,
        output_params=["-crf", "17", "-preset", "medium"])
    wr.send(None)
    frame0 = None
    for fi in range(N):
        rot = 0.018 * fi
        zoom = 1.0 + 0.04 * np.sin(2 * np.pi * fi / N)
        pi = min(int(fi / seg), len(PHASES) - 1)
        local = fi - pi * seg
        # advance active engines
        engs[PHASES[pi][0]].step()
        w = 0.0; pj = pi
        if local > seg - xf and pi < len(PHASES) - 1:
            pj = pi + 1; w = (local - (seg - xf)) / xf
            engs[PHASES[pj][0]].step()
        k1, n1, p1 = PHASES[pi]
        rgb = colorize(fld(k1, n1, rot, zoom), p1)
        if w > 0:
            k2, n2, p2 = PHASES[pj]
            rgb = (1 - w) * rgb + w * colorize(fld(k2, n2, rot, zoom), p2)
        img = np.asarray(Image.fromarray(rgb.astype(np.uint8)).resize((a.K, a.K), Image.BICUBIC), np.uint8)
        if fi == 0:
            frame0 = img.copy()
        if fi >= N - L:                      # wrap-crossfade back to frame 0
            ww = (fi - (N - L) + 1) / L
            img = ((1 - ww) * img.astype(np.float32) + ww * frame0.astype(np.float32)).astype(np.uint8)
        wr.send(np.ascontiguousarray(img).tobytes())
        if fi % 60 == 0:
            print(f"  frame {fi}/{N} (phase {PHASES[pi][0]})", flush=True)
    wr.close()
    print(f"DONE -> {a.out} ({os.path.getsize(a.out)/1e6:.1f} MB, {a.dur:.0f}s, {a.K}x{a.K} seamless)")


if __name__ == "__main__":
    main()
