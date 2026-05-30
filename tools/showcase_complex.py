"""Longer reel of INCREDIBLE complex reactions — fullscreen, high-res, one sim
step per frame for hypnotic motion. Spatiotemporal chaos, spiral waves, worm
turbulence, soliton gas. Streamed straight from the engine to a silent MP4."""
from __future__ import annotations
import os, numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
from cellauto.engine import Engine
from cellauto.rules import REGISTRY

RULE = "abiogenesis-stage1-grayscott"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONTR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def lut(stops):
    g = np.linspace(0, 1, 256)
    xs = np.array([s[0] for s in stops]); cols = np.array([s[1] for s in stops], float)
    return np.stack([np.interp(g, xs, cols[:, c]) for c in range(3)], 1).astype(np.uint8)


PAL = {
    "ember": lut([(0, (4, 2, 2)), (.22, (70, 12, 8)), (.5, (175, 35, 12)),
                  (.75, (245, 120, 25)), (1, (255, 240, 175))]),
    "ocean": lut([(0, (2, 4, 18)), (.3, (6, 42, 84)), (.55, (10, 125, 155)),
                  (.8, (44, 214, 194)), (1, (228, 255, 238))]),
    "magma": lut([(0, (0, 0, 4)), (.25, (60, 15, 92)), (.5, (152, 30, 112)),
                  (.75, (242, 92, 80)), (.9, (252, 162, 92)), (1, (252, 253, 191))]),
    "aurora": lut([(0, (3, 6, 14)), (.3, (12, 60, 70)), (.55, (24, 150, 120)),
                   (.78, (120, 222, 96)), (1, (236, 255, 190))]),
}


def colorize(v, pal, vmax=0.42, gamma=0.82):
    idx = (np.clip(v / vmax, 0, 1) ** gamma * 255).astype(np.uint8)
    return PAL[pal][idx]


SEGS = [
    dict(name="SPATIOTEMPORAL CHAOS", sub="F=0.0162  k=0.0448", kw=dict(F=0.0162, k=0.0448), pal="ember",   secs=15),
    dict(name="SPIRAL WAVES",         sub="F=0.0118  k=0.0500", kw=dict(F=0.0118, k=0.0500), pal="ocean",   secs=15),
    dict(name="WORM TURBULENCE",      sub="F=0.0186  k=0.0502", kw=dict(F=0.0186, k=0.0502), pal="magma",   secs=14),
    dict(name="PULSING CHAOS",        sub="F=0.0260  k=0.0540", kw=dict(F=0.026,  k=0.054),  pal="aurora",  secs=14),
]
SIZE, FPS, GRID = 1080, 30, 220


def overlay(name, sub):
    ov = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for i in range(150):  # bottom vignette
        a = int(150 * (i / 150) ** 1.6)
        d.line([(0, SIZE - 150 + i), (SIZE, SIZE - 150 + i)], fill=(0, 0, 0, a))
    d.text((40, SIZE - 96), name, font=ImageFont.truetype(FONT, 46), fill=(244, 248, 252))
    d.text((42, SIZE - 44), sub + "   ·   REAL ENGINE OUTPUT", font=ImageFont.truetype(FONTR, 26),
           fill=(180, 198, 214))
    return ov


def main(out="media/complex_reactions.mp4"):
    os.makedirs("media", exist_ok=True)
    wr = imageio_ffmpeg.write_frames(out, (SIZE, SIZE), fps=FPS, codec="libx264",
        pix_fmt_in="rgb24", pix_fmt_out="yuv420p", macro_block_size=8,
        output_params=["-crf", "18", "-preset", "medium"])
    wr.send(None)
    for si, s in enumerate(SEGS):
        n = s["secs"] * FPS
        rule = REGISTRY[RULE](**s["kw"])
        eng = Engine(width=GRID, height=GRID, rule=rule, seed=1)
        # scatter ~20 ignition patches (like multiple central seeds) so complex
        # reactions erupt and fill edge-to-edge while staying self-sustaining.
        rng = np.random.default_rng(1234 + si)
        u = np.ones((GRID, GRID), np.float32)
        v = np.zeros((GRID, GRID), np.float32)
        r = 5
        for _ in range(20):
            cy = int(rng.integers(r, GRID - r)); cx = int(rng.integers(r, GRID - r))
            u[cy - r:cy + r, cx - r:cx + r] = 0.5
            v[cy - r:cy + r, cx - r:cx + r] = 0.25
        v += rng.uniform(0.0, 0.02, (GRID, GRID)).astype(np.float32)
        np.clip(v, 0.0, 1.0, out=v)
        eng.state.u = u
        eng.state.v = v
        ov = overlay(s["name"], s["sub"])
        last = None
        for j in range(n):
            eng.step()
            img = Image.fromarray(colorize(np.asarray(eng.state.v, np.float32), s["pal"])
                                  ).resize((SIZE, SIZE), Image.BICUBIC)
            img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
            a = min(1.0, (j + 1) / 12, (n - j) / 12)
            fr = np.asarray(img, np.uint8)
            if a < 0.999:
                fr = (fr.astype(np.float32) * a).astype(np.uint8)
            wr.send(np.ascontiguousarray(fr).tobytes())
            last = np.asarray(eng.state.v, np.float32)
        Image.fromarray(colorize(last, s["pal"])).resize((900, 900), Image.BICUBIC).save(
            f"media/cx_{si}_{s['name'].split()[0].lower()}.png")
        print(f"segment {si} {s['name']} done ({n} frames)")
    wr.close()
    print(f"DONE -> {out} ({os.path.getsize(out)/1e6:.1f} MB, {sum(s['secs'] for s in SEGS)}s, {SIZE}x{SIZE})")


if __name__ == "__main__":
    main()
