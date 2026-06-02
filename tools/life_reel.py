"""LIFE — a field guide to emergent organisms. Raw living dynamics (not folded
mandalas): self-replicating protocells dividing, colonies branching, excitable
waves, neural tissue, and Conway artificial life — rendered smooth (1 gen/frame)
in fluorescence-microscopy palettes with field-guide labels + an ambient bed.

  python3 tools/life_reel.py
"""
from __future__ import annotations
import os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beauty_ultra as BU          # reuse ambient() bed
from monkeys import step as life_step, soup as life_soup
from cellauto.engine import Engine
from cellauto.rules import REGISTRY

RULE = "abiogenesis-stage1-grayscott"
FF = imageio_ffmpeg.get_ffmpeg_exe()
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SIZE, FPS = 1080, 30


def lut(stops):
    g = np.linspace(0, 1, 256); xs = np.array([s[0] for s in stops])
    cols = np.array([s[1] for s in stops], float)
    return np.stack([np.interp(g, xs, cols[:, c]) for c in range(3)], 1).astype(np.uint8)


PAL = {
    "cyto":     lut([(0, (2, 8, 12)), (.3, (6, 60, 80)), (.6, (20, 165, 175)), (.82, (120, 230, 220)), (1, (236, 255, 250))]),
    "membrane": lut([(0, (8, 2, 12)), (.3, (70, 10, 60)), (.6, (185, 30, 120)), (.82, (242, 120, 190)), (1, (255, 226, 245))]),
    "chloro":   lut([(0, (2, 10, 4)), (.3, (10, 70, 30)), (.6, (44, 165, 72)), (.82, (145, 228, 112)), (1, (236, 255, 220))]),
    "amber":    lut([(0, (4, 3, 1)), (.3, (70, 40, 6)), (.6, (192, 120, 20)), (.82, (245, 205, 82)), (1, (255, 250, 220))]),
}


def colorize(field, pal, vmax=0.4, gamma=0.8):
    return PAL[pal][(np.clip(field / vmax, 0, 1) ** gamma * 255).astype(np.uint8)]


def seg_writer(path):
    wr = imageio_ffmpeg.write_frames(path, (SIZE, SIZE), fps=FPS, codec="libx264",
        pix_fmt_in="rgb24", pix_fmt_out="yuv420p", macro_block_size=2,
        output_params=["-crf", "18", "-preset", "medium"])
    wr.send(None); return wr


def label(img, name, sub):
    d = ImageDraw.Draw(img)
    d.rectangle([0, SIZE - 96, SIZE, SIZE], fill=(4, 6, 10))
    d.text((34, SIZE - 84), name, font=ImageFont.truetype(FB, 46), fill=(240, 246, 252))
    d.text((36, SIZE - 32), sub, font=ImageFont.truetype(FR, 24), fill=(165, 185, 205))


def fade(arr, fi, n, k=12):
    a = min(1.0, (fi + 1) / k, (n - fi) / k)
    return arr if a >= 0.999 else (arr.astype(np.float32) * a).astype(np.uint8)


GS = [
    dict(name="PRIMORDIAL SOUP", sub="Gray-Scott · order self-organising from a scatter of seeds",
         kw=dict(F=0.030, k=0.057), seed="scatter", pal="cyto", dur=10),
    dict(name="CELL DIVISION", sub="self-replicating protocells — they grow, then divide (mitosis)",
         kw=dict(preset="mitosis"), seed="central", grid=150, pal="membrane", dur=13),
    dict(name="COLONY", sub="Gray-Scott coral · organisms branching to fill the dish",
         kw=dict(F=0.0545, k=0.062), seed="scatter", pal="chloro", dur=11),
    dict(name="EXCITABLE WAVES", sub="wave turbulence — like an excitable living medium",
         kw=dict(F=0.018, k=0.050), seed="scatter", pal="cyto", dur=10),
    dict(name="NEURAL TISSUE", sub="Gray-Scott labyrinth · self-wiring channels",
         kw=dict(preset="labyrinth"), seed="scatter", pal="membrane", dur=10),
]


def render_gs(spec, path):
    grid = spec.get("grid", 220)
    eng = Engine(width=grid, height=grid, rule=REGISTRY[RULE](**spec["kw"]), seed=1)
    if spec.get("seed", "scatter") == "scatter":
        rng = np.random.default_rng(7)
        u = np.ones((grid, grid), np.float32); v = np.zeros((grid, grid), np.float32); r = 5
        for _ in range(grid // 11):
            cy = int(rng.integers(r, grid - r)); cx = int(rng.integers(r, grid - r))
            u[cy - r:cy + r, cx - r:cx + r] = 0.5; v[cy - r:cy + r, cx - r:cx + r] = 0.25
        v += rng.uniform(0, 0.02, (grid, grid)).astype(np.float32)
        eng.state.u = u; eng.state.v = np.clip(v, 0, 1)
    # else: keep the rule's default central-patch seed (mitosis thrives from it)
    n = int(spec["dur"] * FPS); wr = seg_writer(path)
    for fi in range(n):
        eng.step()
        v = np.asarray(eng.state.v, np.float32)
        img = Image.fromarray(colorize(v, spec["pal"])).resize((SIZE, SIZE), Image.BICUBIC).convert("RGB")
        label(img, spec["name"], spec["sub"])
        wr.send(np.ascontiguousarray(fade(np.asarray(img, np.uint8), fi, n)).tobytes())
    wr.close()
    print(f"  {spec['name']}")


def render_conway(path, dur=12):
    grid = 130
    g = life_soup(917, grid, 36, 0.40)        # a known long-lived colony
    heat = np.zeros((grid, grid), np.float32)
    ICE = PAL["cyto"]
    n = int(dur * FPS); wr = seg_writer(path)
    for fi in range(n):
        heat = np.maximum(heat * 0.80, g.astype(np.float32))
        rgb = ICE[(np.clip(heat, 0, 1) * 255).astype(np.uint8)]
        rgb[g] = (255, 255, 255)
        img = Image.fromarray(rgb).resize((SIZE, SIZE), Image.BICUBIC).convert("RGB")
        label(img, "ARTIFICIAL LIFE", "Conway's Game of Life · a colony of gliders & oscillators")
        wr.send(np.ascontiguousarray(fade(np.asarray(img, np.uint8), fi, n)).tobytes())
        g = life_step(g)
    wr.close()
    print("  ARTIFICIAL LIFE")


def title_card(path, dur=3.5):
    n = int(dur * FPS); wr = seg_writer(path)
    base = Image.new("RGB", (SIZE, SIZE), (6, 9, 14))
    d = ImageDraw.Draw(base)
    t1 = "LIFE"; f1 = ImageFont.truetype(FB, 120); f2 = ImageFont.truetype(FR, 34)
    d.text((SIZE/2 - d.textlength(t1, font=f1)/2, SIZE/2 - 110), t1, font=f1, fill=(238, 246, 252))
    s = "emergent organisms from simple rules"
    d.text((SIZE/2 - d.textlength(s, font=f2)/2, SIZE/2 + 30), s, font=f2, fill=(150, 200, 210))
    arr = np.asarray(base, np.uint8)
    for fi in range(n):
        wr.send(np.ascontiguousarray(fade(arr.copy(), fi, n, 16)).tobytes())
    wr.close()


def main():
    os.makedirs("media", exist_ok=True)
    tmp = "/tmp/life"; os.makedirs(tmp, exist_ok=True)
    parts = []
    title_card(f"{tmp}/00_title.mp4"); parts.append(f"{tmp}/00_title.mp4")
    print("rendering life segments ...")
    for i, spec in enumerate(GS, 1):
        p = f"{tmp}/{i:02d}_{spec['pal']}.mp4"; render_gs(spec, p); parts.append(p)
    cp = f"{tmp}/zz_conway.mp4"; render_conway(cp); parts.append(cp)
    # standalone hero mitosis clip
    render_gs(dict(name="CELL DIVISION", sub="self-replicating protocells dividing — Gray-Scott mitosis",
                   kw=dict(preset="mitosis"), seed="central", grid=150, pal="membrane", dur=16), "media/life_mitosis.mp4")

    total = 3.5 + sum(s["dur"] for s in GS) + 12
    lst = "/tmp/life_concat.txt"
    open(lst, "w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in parts))
    silent = f"{tmp}/silent.mp4"
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", lst, "-c", "copy", silent], check=True)
    bed = f"{tmp}/bed.wav"; BU.ambient(total, bed)
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", silent, "-i", bed,
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "176k", "-shortest",
                    "-movflags", "+faststart", "media/life_reel.mp4"], check=True)
    print(f"DONE -> media/life_reel.mp4 ({os.path.getsize('media/life_reel.mp4')/1e6:.1f} MB, ~{total:.0f}s)"
          f" + media/life_mitosis.mp4")


if __name__ == "__main__":
    main()
