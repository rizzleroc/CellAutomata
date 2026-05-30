"""Showcase reel — pure, high-res Gray-Scott visuals straight from the engine.
No narration, no clutter: a 2x2 wall of emergent life in four palettes, plus
crisp stills. Silent MP4 via the bundled ffmpeg."""
from __future__ import annotations
import os, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
from cellauto.engine import Engine
from cellauto.rules import REGISTRY

RULE = "abiogenesis-stage1-grayscott"
FF = imageio_ffmpeg.get_ffmpeg_exe()
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def lut(stops):
    g = np.linspace(0, 1, 256)
    xs = np.array([s[0] for s in stops]); cols = np.array([s[1] for s in stops], float)
    return np.stack([np.interp(g, xs, cols[:, c]) for c in range(3)], 1).astype(np.uint8)


PAL = {
    "magma": lut([(0, (0, 0, 4)), (.25, (60, 15, 90)), (.5, (150, 30, 110)),
                  (.75, (240, 90, 80)), (.9, (252, 160, 90)), (1, (252, 253, 191))]),
    "ocean": lut([(0, (2, 4, 18)), (.3, (6, 40, 80)), (.55, (10, 120, 150)),
                  (.8, (40, 210, 190)), (1, (225, 255, 235))]),
    "ember": lut([(0, (4, 2, 2)), (.25, (70, 12, 8)), (.5, (170, 35, 12)),
                  (.75, (245, 120, 25)), (1, (255, 238, 170))]),
    "viridis": lut([(0, (68, 1, 84)), (.25, (59, 82, 139)), (.5, (33, 145, 140)),
                    (.75, (94, 201, 98)), (1, (253, 231, 37))]),
}


def colorize(v, pal, vmax=0.42, gamma=0.85):
    idx = (np.clip(v / vmax, 0, 1) ** gamma * 255).astype(np.uint8)
    return PAL[pal][idx]


def render_v_pool(kw, grid, dev, n_out, seed=1):
    rule = REGISTRY[RULE](**kw)
    eng = Engine(width=grid, height=grid, rule=rule, seed=seed)
    grab = set(int(round(x)) for x in np.linspace(1, dev, n_out))
    pool = []
    for step in range(1, dev + 1):
        eng.step()
        if step in grab:
            pool.append(np.asarray(eng.state.v, np.float32).copy())
    while len(pool) < n_out:
        pool.append(pool[-1])
    return pool[:n_out]


PANELS = [
    dict(name="CORAL GROWTH",  kw=dict(F=0.0545, k=0.062),     dev=780, pal="ember"),
    dict(name="LABYRINTH",     kw=dict(preset="labyrinth"),     dev=440, pal="ocean"),
    dict(name="MITOSIS",       kw=dict(preset="mitosis"),       dev=380, pal="magma"),
    dict(name="SOLITONS",      kw=dict(F=0.062, k=0.0609),      dev=560, pal="viridis"),
]


def main():
    SIZE, DUR, FPS, GRID = 540, 15, 30, 200
    N = DUR * FPS
    print("rendering panels ...")
    pools = []
    for p in PANELS:
        pools.append(render_v_pool(p["kw"], GRID, p["dev"], N))
        print(" ", p["name"], "done")

    # crisp stills (final developed frame, upscaled)
    os.makedirs("media", exist_ok=True)
    for p, pool in zip(PANELS, pools):
        rgb = colorize(pool[-1], p["pal"])
        Image.fromarray(rgb).resize((760, 760), Image.BICUBIC).save(
            f"media/still_{p['name'].split()[0].lower()}.png")

    fnt = ImageFont.truetype(FONT, 22)
    out = "media/showcase.mp4"
    wr = imageio_ffmpeg.write_frames(out, (SIZE * 2, SIZE * 2), fps=FPS,
        codec="libx264", pix_fmt_in="rgb24", pix_fmt_out="yuv420p",
        macro_block_size=8, output_params=["-crf", "18", "-preset", "medium"])
    wr.send(None)
    pos = [(0, 0), (SIZE, 0), (0, SIZE), (SIZE, SIZE)]
    print("compositing montage ...")
    for i in range(N):
        canvas = Image.new("RGB", (SIZE * 2, SIZE * 2), (8, 10, 14))
        for p, pool, (x, y) in zip(PANELS, pools, pos):
            tile = Image.fromarray(colorize(pool[i], p["pal"])).resize(
                (SIZE, SIZE), Image.BICUBIC)
            canvas.paste(tile, (x, y))
        d = ImageDraw.Draw(canvas)
        d.line([(SIZE, 0), (SIZE, SIZE * 2)], fill=(8, 10, 14), width=4)
        d.line([(0, SIZE), (SIZE * 2, SIZE)], fill=(8, 10, 14), width=4)
        for p, (x, y) in zip(PANELS, pos):
            d.text((x + 18, y + SIZE - 36), p["name"], font=fnt, fill=(235, 240, 248))
        wr.send(np.ascontiguousarray(np.asarray(canvas, np.uint8)).tobytes())
    wr.close()
    print(f"DONE -> {out} ({os.path.getsize(out)/1e6:.1f} MB, {DUR}s, {SIZE*2}x{SIZE*2})")


if __name__ == "__main__":
    main()
