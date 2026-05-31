"""Beauty loop — ULTRA. The furthest version: true 4K (3840), ~48s, 8 crystal
phases (compound symmetry up to 24-fold + self-similar octave nesting) on busy
reaction-diffusion sources, slow rotation + breathing zoom, a seamless ambient
bed, and a perfect wrap-loop. Folds at foldK then upscales to 4K for speed.

  python3 tools/beauty_ultra.py --out media/beauty_ultra_4k.mp4
"""
from __future__ import annotations
import argparse, os, subprocess, wave
import numpy as np
from PIL import Image
import imageio_ffmpeg
from cellauto.engine import Engine
from cellauto.rules import REGISTRY

RULE = "abiogenesis-stage1-grayscott"
FF = imageio_ffmpeg.get_ffmpeg_exe()


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
    "ember": lut([(0, (4, 2, 2)), (.22, (70, 12, 8)), (.5, (175, 35, 12)), (.75, (245, 120, 25)), (1, (255, 240, 175))]),
    "aqua":  lut([(0, (1, 6, 12)), (.3, (6, 60, 80)), (.55, (10, 150, 150)), (.78, (90, 230, 200)), (1, (225, 255, 240))]),
}

# (engine key, symmetry n, octaves, palette)
PHASES = [
    ("coral", 6, 1, "pine"), ("maze", 12, 0, "frost"), ("labyrinth", 8, 1, "ice"),
    ("plasma", 18, 0, "amethyst"), ("soliton", 5, 1, "gold"), ("chaos", 24, 0, "frost"),
    ("worm", 7, 1, "ember"), ("stripes", 12, 0, "aqua"),
]
ENGINES = {
    "coral":     dict(kw=dict(F=0.0545, k=0.062), warm=460, scatter=False),
    "maze":      dict(kw=dict(F=0.026, k=0.055), warm=420, scatter=False),
    "labyrinth": dict(kw=dict(preset="labyrinth"), warm=440, scatter=False),
    "plasma":    dict(kw=dict(F=0.0264, k=0.0579), warm=460, scatter=True),
    "soliton":   dict(kw=dict(F=0.062, k=0.0609), warm=520, scatter=True),
    "chaos":     dict(kw=dict(F=0.018, k=0.050), warm=480, scatter=True),
    "worm":      dict(kw=dict(F=0.0186, k=0.0502), warm=460, scatter=True),
    "stripes":   dict(kw=dict(F=0.030, k=0.057), warm=440, scatter=False),
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
        self.scale = G / float(K); self.G = G; self.c = c

    def fold(self, V, n, phase, zoom):
        wedge = 2 * np.pi / n
        a = np.mod(self.TH + phase, wedge); a = np.minimum(a, wedge - a)
        rr = self.R * self.scale * zoom; G = self.G
        sx = np.clip(G / 2 + rr * np.cos(a), 0, G - 1.001)
        sy = np.clip(G / 2 + rr * np.sin(a), 0, G - 1.001)
        x0 = sx.astype(np.int32); y0 = sy.astype(np.int32); fx = sx - x0; fy = sy - y0
        return (V[y0, x0] * (1 - fx) * (1 - fy) + V[y0, x0 + 1] * fx * (1 - fy)
                + V[y0 + 1, x0] * (1 - fx) * fy + V[y0 + 1, x0 + 1] * fx * fy)

    def warp(self, M, scale, rot):
        K = M.shape[0]
        dx = np.arange(K) - self.c
        ca, sa = np.cos(rot), np.sin(rot)
        X = dx[None, :]; Y = dx[:, None]
        sx = self.c + (X * ca - Y * sa) * scale; sy = self.c + (X * sa + Y * ca) * scale
        inb = (sx >= 0) & (sx < K - 1) & (sy >= 0) & (sy < K - 1)
        sx = np.clip(sx, 0, K - 1.001); sy = np.clip(sy, 0, K - 1.001)
        x0 = sx.astype(np.int32); y0 = sy.astype(np.int32); fx = sx - x0; fy = sy - y0
        out = (M[y0, x0] * (1 - fx) * (1 - fy) + M[y0, x0 + 1] * fx * (1 - fy)
               + M[y0 + 1, x0] * (1 - fx) * fy + M[y0 + 1, x0 + 1] * fx * fy)
        return out * inb

    def phase_field(self, V, n, octs, rot, zoom):
        M = self.fold(V, n, rot, zoom)
        for oi in range(octs):
            M = np.maximum(M, (0.55 - 0.12 * oi) * self.warp(M, 2.0 + 1.3 * oi, rot * 1.3 + 0.6))
        return M * self.mask


def colorize(field, pal, gamma=0.72):
    pos = field[field > 0.02]
    hi = np.percentile(pos, 99.5) if pos.size else 1.0
    f = np.clip(field / (hi + 1e-6), 0, 1) ** gamma
    return PAL[pal][(f * 255).astype(np.uint8)].astype(np.float32)


def ambient(dur, path, sr=22050):
    n = int(dur * sr); t = np.arange(n) / sr
    bed = np.zeros(n)
    base = [55.0, 82.41, 110.0, 164.81, 220.0, 329.63]
    amps = [0.55, 0.32, 0.5, 0.3, 0.26, 0.16]
    for i, (f, amp) in enumerate(zip(base, amps)):
        f = round(f * dur) / dur                       # integer cycles -> seamless
        lfo = 0.6 + 0.4 * np.sin(2 * np.pi * (i + 1) * t / dur)
        bed += amp * lfo * np.sin(2 * np.pi * f * t)
    bed /= (np.max(np.abs(bed)) + 1e-9)
    mix = np.clip(bed * 0.5 * 32767, -32768, 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(mix.tobytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--K", type=int, default=3840)
    ap.add_argument("--foldK", type=int, default=1024)
    ap.add_argument("--grid", type=int, default=260)
    ap.add_argument("--dur", type=float, default=48)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--out", default="media/beauty_ultra_4k.mp4")
    a = ap.parse_args()

    print("warming engines ...")
    engs = {k: make_engine(s, a.grid) for k, s in ENGINES.items()}
    kal = Kal(a.foldK, a.grid)
    N = int(a.dur * a.fps); seg = N / len(PHASES)
    xf = int(1.3 * a.fps); L = int(1.8 * a.fps)

    def fld(key, n, octs, rot, zoom):
        v = np.asarray(engs[key].state.v, np.float32); v = v / (v.max() + 1e-6)
        return kal.phase_field(v, n, octs, rot, zoom)

    silent = "/tmp/_beauty_silent.mp4"
    wr = imageio_ffmpeg.write_frames(silent, (a.K, a.K), fps=a.fps, codec="libx264",
        pix_fmt_in="rgb24", pix_fmt_out="yuv420p", macro_block_size=2,
        output_params=["-crf", "16", "-preset", "medium"])
    wr.send(None)
    frame0 = None
    for fi in range(N):
        rot = 0.016 * fi
        zoom = 1.0 + 0.045 * np.sin(2 * np.pi * fi / N)
        pi = min(int(fi / seg), len(PHASES) - 1); local = fi - pi * seg
        engs[PHASES[pi][0]].step()
        w = 0.0; pj = pi
        if local > seg - xf and pi < len(PHASES) - 1:
            pj = pi + 1; w = (local - (seg - xf)) / xf; engs[PHASES[pj][0]].step()
        k1, n1, o1, p1 = PHASES[pi]
        rgb = colorize(fld(k1, n1, o1, rot, zoom), p1)
        if w > 0:
            k2, n2, o2, p2 = PHASES[pj]
            rgb = (1 - w) * rgb + w * colorize(fld(k2, n2, o2, rot, zoom), p2)
        img = np.asarray(Image.fromarray(rgb.astype(np.uint8)).resize((a.K, a.K), Image.BICUBIC), np.uint8)
        if fi == 0:
            frame0 = img.copy()
        if fi >= N - L:
            ww = (fi - (N - L) + 1) / L
            img = ((1 - ww) * img.astype(np.float32) + ww * frame0.astype(np.float32)).astype(np.uint8)
        wr.send(np.ascontiguousarray(img).tobytes())
        if fi % 60 == 0:
            print(f"  frame {fi}/{N} ({PHASES[pi][0]} {PHASES[pi][1]}-fold)", flush=True)
    wr.close()

    print("ambient bed + mux ...")
    bed = "/tmp/_beauty_bed.wav"; ambient(a.dur, bed)
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", silent, "-i", bed,
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", a.out], check=True)
    print(f"DONE -> {a.out} ({os.path.getsize(a.out)/1e6:.1f} MB, {a.dur:.0f}s, {a.K}x{a.K})")


if __name__ == "__main__":
    main()
