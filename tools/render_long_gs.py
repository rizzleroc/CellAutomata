"""Render a LONG Gray-Scott clip: one PDE generation per frame, scattered
ignition so it fills edge-to-edge, for sustained reaction-diffusion change.

  python3 tools/render_long_gs.py --F 0.0198 --k 0.0495 --pal ocean --dur 22 \
      --title "WAVE STORM" --out media/long_wavestorm.mp4
"""
from __future__ import annotations
import argparse, os, numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
from cellauto.engine import Engine
from cellauto.rules import REGISTRY

RULE = "abiogenesis-stage1-grayscott"
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def lut(stops):
    g = np.linspace(0, 1, 256); xs = np.array([s[0] for s in stops])
    cols = np.array([s[1] for s in stops], float)
    return np.stack([np.interp(g, xs, cols[:, c]) for c in range(3)], 1).astype(np.uint8)


PAL = {
    "ember": lut([(0, (4, 2, 2)), (.22, (70, 12, 8)), (.5, (175, 35, 12)), (.75, (245, 120, 25)), (1, (255, 240, 175))]),
    "ocean": lut([(0, (2, 4, 18)), (.3, (6, 42, 84)), (.55, (10, 125, 155)), (.8, (44, 214, 194)), (1, (228, 255, 238))]),
    "magma": lut([(0, (0, 0, 4)), (.25, (60, 15, 92)), (.5, (152, 30, 112)), (.75, (242, 92, 80)), (.9, (252, 162, 92)), (1, (252, 253, 191))]),
    "aurora": lut([(0, (3, 6, 14)), (.3, (12, 60, 70)), (.55, (24, 150, 120)), (.78, (120, 222, 96)), (1, (236, 255, 190))]),
}


def colorize(v, pal, vmax=0.42, gamma=0.82):
    return PAL[pal][(np.clip(v / vmax, 0, 1) ** gamma * 255).astype(np.uint8)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--F", type=float, required=True)
    ap.add_argument("--k", type=float, required=True)
    ap.add_argument("--pal", default="ocean")
    ap.add_argument("--dur", type=float, default=22)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--grid", type=int, default=210)
    ap.add_argument("--size", type=int, default=1080)
    ap.add_argument("--title", default="")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    rule = REGISTRY[RULE](F=a.F, k=a.k)
    eng = Engine(width=a.grid, height=a.grid, rule=rule, seed=1)
    rng = np.random.default_rng(11)
    u = np.ones((a.grid, a.grid), np.float32); v = np.zeros((a.grid, a.grid), np.float32)
    r = 5
    for _ in range(26):
        cy = int(rng.integers(r, a.grid - r)); cx = int(rng.integers(r, a.grid - r))
        u[cy - r:cy + r, cx - r:cx + r] = 0.5; v[cy - r:cy + r, cx - r:cx + r] = 0.25
    v += rng.uniform(0, 0.02, (a.grid, a.grid)).astype(np.float32)
    eng.state.u = u; eng.state.v = np.clip(v, 0, 1)

    N = int(a.dur * a.fps)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    wr = imageio_ffmpeg.write_frames(a.out, (a.size, a.size), fps=a.fps, codec="libx264",
        pix_fmt_in="rgb24", pix_fmt_out="yuv420p", macro_block_size=2,
        output_params=["-crf", "18", "-preset", "medium"])
    wr.send(None)
    tf = ImageFont.truetype(FB, 46); sf = ImageFont.truetype(FR, 24)
    for fi in range(N):
        eng.step()
        img = Image.fromarray(colorize(np.asarray(eng.state.v, np.float32), a.pal)
                              ).resize((a.size, a.size), Image.BICUBIC).convert("RGB")
        d = ImageDraw.Draw(img)
        if a.title:
            for yy in range(120):
                d.line([(0, a.size - 120 + yy), (a.size, a.size - 120 + yy)],
                       fill=(0, 0, 0, 0)) if False else None
            d.rectangle([0, a.size - 92, a.size, a.size], fill=(6, 8, 13))
            d.text((28, a.size - 82), a.title, font=tf, fill=(244, 249, 253))
            d.text((30, a.size - 34),
                   f"Gray-Scott  F={a.F:.4f}  k={a.k:.4f}   ·   REAL ENGINE OUTPUT   ·   gen {fi}",
                   font=sf, fill=(170, 190, 208))
        af = min(1.0, (fi + 1) / 12, (N - fi) / 12)
        fr = np.asarray(img, np.uint8)
        if af < 0.999:
            fr = (fr.astype(np.float32) * af).astype(np.uint8)
        wr.send(np.ascontiguousarray(fr).tobytes())
    wr.close()
    print(f"DONE -> {a.out} ({os.path.getsize(a.out)/1e6:.1f} MB, {a.dur}s, {N} gens)")


if __name__ == "__main__":
    main()
