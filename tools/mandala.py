"""Sacred geometry from cellular automata: evolve Gray-Scott reaction-diffusion
from a centred seed, then fold the field with n-fold dihedral symmetry
(kaleidoscope) to produce mandalas / rose-windows / flower-of-life forms.

Generates a gallery grid of many mandalas (varying symmetry order, source
regime, palette), high-res hero stills, and blooming-mandala animations.

  python3 tools/mandala.py
"""
from __future__ import annotations
import os, numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
from cellauto.engine import Engine
from cellauto.rules import REGISTRY

RULE = "abiogenesis-stage1-grayscott"
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def lut(stops):
    g = np.linspace(0, 1, 256); xs = np.array([s[0] for s in stops])
    cols = np.array([s[1] for s in stops], float)
    return np.stack([np.interp(g, xs, cols[:, c]) for c in range(3)], 1).astype(np.uint8)


PALS = {
    "gold":     lut([(0, (2, 2, 8)), (.25, (40, 12, 90)), (.5, (150, 40, 140)), (.7, (240, 110, 90)), (.85, (250, 190, 90)), (1, (255, 250, 210))]),
    "ice":      lut([(0, (3, 5, 14)), (.25, (8, 34, 90)), (.5, (16, 110, 190)), (.75, (70, 210, 232)), (1, (210, 250, 255))]),
    "emerald":  lut([(0, (2, 8, 6)), (.3, (10, 60, 40)), (.55, (24, 150, 96)), (.8, (120, 222, 130)), (1, (236, 255, 220))]),
    "amethyst": lut([(0, (6, 2, 14)), (.3, (60, 18, 110)), (.6, (140, 60, 200)), (.82, (210, 140, 240)), (1, (245, 230, 255))]),
    "ember":    lut([(0, (4, 2, 2)), (.22, (70, 12, 8)), (.5, (175, 35, 12)), (.75, (245, 120, 25)), (1, (255, 240, 175))]),
    "rose":     lut([(0, (10, 3, 8)), (.3, (90, 20, 50)), (.6, (210, 60, 110)), (.82, (245, 150, 180)), (1, (255, 235, 240))]),
}


def colorize(a, pal, gamma=0.8):
    vmax = float(a.max()) + 1e-6
    return PALS[pal][(np.clip(a / vmax, 0, 1) ** gamma * 255).astype(np.uint8)]


def evolve(kw, grid, steps, seed=1):
    rule = REGISTRY[RULE](**kw)
    eng = Engine(width=grid, height=grid, rule=rule, seed=seed)
    for _ in range(steps):
        eng.step()
    return np.asarray(eng.state.v, np.float32)


def _rot(v, ang):
    if ang == 0:
        return v
    return np.asarray(Image.fromarray(v).rotate(ang, resample=Image.BILINEAR), np.float32)


def mandala(v, n, mirror=True):
    """n-fold dihedral fold via max of rotated (and mirrored) copies."""
    acc = v.copy()
    for j in range(1, n):
        acc = np.maximum(acc, _rot(v, 360.0 * j / n))
    if mirror:
        m = np.ascontiguousarray(v[:, ::-1])
        for j in range(n):
            acc = np.maximum(acc, _rot(m, 360.0 * j / n))
    return acc


def radial_mask(a, frac=0.97):
    g = a.shape[0]
    yy, xx = np.mgrid[0:g, 0:g]
    r = np.sqrt((xx - g / 2) ** 2 + (yy - g / 2) ** 2) / (g / 2)
    return a * np.clip((frac - r) / 0.10, 0, 1)


# regime textures (centred-seed Gray-Scott) → distinct mandala motifs
REGIMES = {
    "coral":      dict(F=0.0545, k=0.062),
    "labyrinth":  dict(preset="labyrinth"),
    "spots":      dict(preset="mitosis"),
    "maze":       dict(F=0.026, k=0.055),
    "stripes":    dict(F=0.030, k=0.057),
    "chaos":      dict(F=0.018, k=0.050),
    "turbulence": dict(F=0.022, k=0.051),
    "solitons":   dict(F=0.062, k=0.0609),
}
REG_STEPS = {"coral": 520, "labyrinth": 460, "spots": 360, "maze": 460,
             "stripes": 460, "chaos": 520, "turbulence": 520, "solitons": 460}
NS = [5, 6, 7, 8, 9, 10, 12, 16]
PAL_LIST = list(PALS)


def gallery(out="media/sacred_geometry_gallery.png", cols=6, rows=6, tile=296, grid=168):
    fields = {name: evolve(kw, grid, REG_STEPS[name]) for name, kw in REGIMES.items()}
    reg_names = list(REGIMES)
    gap, top = 8, 78
    W = cols * tile + (cols + 1) * gap
    H = top + rows * tile + (rows + 1) * gap
    img = Image.new("RGB", (W, H), (8, 9, 14))
    d = ImageDraw.Draw(img)
    d.text((gap + 6, 22), f"SACRED GEOMETRY FROM CELLULAR AUTOMATA  ·  {cols*rows} mandalas",
           font=ImageFont.truetype(FB, 34), fill=(238, 244, 250))
    lf = ImageFont.truetype(FB, 18)
    count = 0
    for i in range(cols * rows):
        reg = reg_names[(i * 3) % len(reg_names)]      # spread regimes
        n = NS[(i * 5) % len(NS)]
        pal = PAL_LIST[(i * 7) % len(PAL_LIST)]
        a = radial_mask(mandala(fields[reg], n))
        til = Image.fromarray(colorize(a, pal)).resize((tile, tile), Image.BICUBIC)
        x = gap + (i % cols) * (tile + gap)
        y = top + gap + (i // cols) * (tile + gap)
        img.paste(til, (x, y))
        d.text((x + 8, y + tile - 26), f"{n}-fold · {reg}", font=lf, fill=(235, 240, 248))
        count += 1
    img.save(out)
    print(f"gallery -> {out}  ({count} mandalas, {W}x{H})")
    return count


def heroes(grid=240):
    picks = [("spots", 12, "gold"), ("labyrinth", 8, "ice"),
             ("chaos", 6, "amethyst"), ("coral", 16, "ember")]
    for reg, n, pal in picks:
        v = evolve(REGIMES[reg], grid, REG_STEPS[reg])
        a = radial_mask(mandala(v, n))
        Image.fromarray(colorize(a, pal)).resize((1080, 1080), Image.BICUBIC).save(
            f"media/mandala_{n}fold_{reg}.png")
        print(f"  hero {n}-fold {reg} ({pal})")


def bloom(reg, n, pal, dur=15, fps=30, grid=190, size=1080, out=None):
    out = out or f"media/mandala_bloom_{n}fold_{reg}.mp4"
    rule = REGISTRY[RULE](**REGIMES[reg])
    eng = Engine(width=grid, height=grid, rule=rule, seed=1)
    N = dur * fps
    wr = imageio_ffmpeg.write_frames(out, (size, size), fps=fps, codec="libx264",
        pix_fmt_in="rgb24", pix_fmt_out="yuv420p", macro_block_size=2,
        output_params=["-crf", "18", "-preset", "medium"])
    wr.send(None)
    tf = ImageFont.truetype(FB, 30)
    for fi in range(N):
        eng.step()
        v = np.asarray(eng.state.v, np.float32)
        a = radial_mask(mandala(v, n))
        img = Image.fromarray(colorize(a, pal)).resize((size, size), Image.BICUBIC).convert("RGB")
        d = ImageDraw.Draw(img)
        d.text((26, 22), f"{n}-FOLD MANDALA  ·  {reg}  ·  gen {fi}", font=tf, fill=(238, 244, 250))
        af = min(1.0, (fi + 1) / 12, (N - fi) / 12)
        fr = np.asarray(img, np.uint8)
        if af < 0.999:
            fr = (fr.astype(np.float32) * af).astype(np.uint8)
        wr.send(np.ascontiguousarray(fr).tobytes())
    wr.close()
    print(f"  bloom -> {out} ({dur}s)")


def main():
    os.makedirs("media", exist_ok=True)
    n = gallery()
    print("heroes:"); heroes()
    print("blooms:")
    bloom("spots", 12, "gold")
    bloom("chaos", 8, "ice")
    print(f"DONE — {n} mandalas in the gallery + 4 hero stills + 2 blooming animations")


if __name__ == "__main__":
    main()
