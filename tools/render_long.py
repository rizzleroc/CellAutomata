"""Render a LONG, smooth Conway clip: one generation per frame so the change is
continuous, not a fast-forward. Heat-trail rendering (gliders streak like
comets). Use for a single champion seed.

  python3 tools/render_long.py --seed 5650 --grid 90 --soup 22 --dens 0.44 \
      --dur 24 --note "3,957-generation methuselah" --out media/long_5650.mp4
"""
from __future__ import annotations
import argparse, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from monkeys import step, soup

FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def lut(stops):
    g = np.linspace(0, 1, 256); xs = np.array([s[0] for s in stops])
    cols = np.array([s[1] for s in stops], float)
    return np.stack([np.interp(g, xs, cols[:, c]) for c in range(3)], 1).astype(np.uint8)


ICE = lut([(0, (3, 5, 14)), (.25, (8, 34, 90)), (.5, (16, 110, 190)),
           (.75, (70, 210, 232)), (1, (210, 250, 255))])


def render(heat, alive, size):
    rgb = ICE[(np.clip(heat, 0, 1) * 255).astype(np.uint8)]
    rgb[alive] = (255, 255, 255)
    return Image.fromarray(rgb).resize((size, size), Image.BICUBIC)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--grid", type=int, default=90)
    ap.add_argument("--soup", type=int, default=22)
    ap.add_argument("--dens", type=float, default=0.44)
    ap.add_argument("--dur", type=float, default=24)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--start", type=int, default=0, help="skip this many gens before recording")
    ap.add_argument("--decay", type=float, default=0.80)
    ap.add_argument("--size", type=int, default=1080)
    ap.add_argument("--note", default="")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    g = soup(a.seed, a.grid, a.soup, a.dens)
    heat = np.zeros((a.grid, a.grid), np.float32)
    for _ in range(a.start):
        heat = np.maximum(heat * a.decay, g.astype(np.float32)); g = step(g)
    N = int(a.dur * a.fps)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    wr = imageio_ffmpeg.write_frames(a.out, (a.size, a.size), fps=a.fps, codec="libx264",
        pix_fmt_in="rgb24", pix_fmt_out="yuv420p", macro_block_size=2,
        output_params=["-crf", "18", "-preset", "medium"])
    wr.send(None)
    big = ImageFont.truetype(FB, 52); small = ImageFont.truetype(FR, 24)
    for fi in range(N):
        gen = a.start + fi
        heat = np.maximum(heat * a.decay, g.astype(np.float32))
        pop = int(g.sum())
        img = render(heat, g, a.size).convert("RGB")
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, a.size, 92], fill=(6, 8, 13))
        d.text((28, 16), f"GENERATION {gen:,}", font=big, fill=(245, 250, 255))
        tw = d.textlength(f"{pop:,} live cells", font=small)
        d.text((a.size - tw - 28, 34), f"{pop:,} live cells", font=small, fill=(120, 210, 235))
        if a.note:
            d.rectangle([0, a.size - 58, a.size, a.size], fill=(6, 8, 13))
            d.text((28, a.size - 50), a.note, font=small, fill=(150, 214, 92))
        af = min(1.0, (fi + 1) / 12, (N - fi) / 12)
        fr = np.asarray(img, np.uint8)
        if af < 0.999:
            fr = (fr.astype(np.float32) * af).astype(np.uint8)
        wr.send(np.ascontiguousarray(fr).tobytes())
        g = step(g)
    wr.close()
    print(f"DONE -> {a.out} ({os.path.getsize(a.out)/1e6:.1f} MB, {a.dur}s, {N} gens)")


if __name__ == "__main__":
    main()
