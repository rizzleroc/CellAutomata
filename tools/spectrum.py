"""THE FULL SPECTRUM — a grand tour video of every visualization in CellAutomata.
Each rule rendered with its OWN native render_rgb (discrete soup/Conway/Wolfram,
diverging vent & chirality maps, viridis fields), plus the discovery search and
the art pipeline. Labelled segments + ambient bed.

  python3 tools/spectrum.py
"""
from __future__ import annotations
import os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_progress_video as MP            # ambient_bed
import relit as R                           # relit art segment
import mandala_x as MX                      # mandala art segment
from cellauto.engine import Engine
from cellauto.rules import REGISTRY

FF = imageio_ffmpeg.get_ffmpeg_exe()
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SIZE, FPS, SR = 1080, 30, 22050
GS = "abiogenesis-stage1-grayscott"

# (kind, rule/spec, cfg, warm, crisp, name, sub)
TOUR = [
    ("title", None, None, 0, False, "THE FULL SPECTRUM", "every visualization in CellAutomata"),
    ("rule", "abiogenesis-stage0-soup", {}, 55, False, "Primordial Soup", "Miller–Urey · discrete molecular cells"),
    ("gs",   GS, dict(preset="mitosis"), 300, False, "Reaction–Diffusion", "Gray-Scott · Turing patterns"),
    ("rule", "abiogenesis-stage2-raf", {}, 45, False, "Autocatalytic Sets", "Kauffman RAF · self-sustaining chemistry"),
    ("rule", "abiogenesis-mineral-catalysis", {}, 60, False, "Mineral Catalysis", "Ferris clay · surface polymerization"),
    ("rule", "abiogenesis-hydrothermal-vent", {}, 70, False, "Hydrothermal Vent", "Lane–Martin · the proton gradient"),
    ("rule", "abiogenesis-homochirality", {}, 80, False, "Homochirality", "Frank · L vs R symmetry breaking"),
    ("rule", "abiogenesis-rna-world", dict(error_rate=0.02), 60, False, "RNA World", "Eigen quasispecies"),
    ("rule", "abiogenesis-genetic-code", {}, 90, False, "Genetic Code", "Woese · code coevolution"),
    ("rule", "abiogenesis-coacervate", {}, 90, False, "Coacervates", "Cahn–Hilliard · phase separation"),
    ("rule", "abiogenesis-stage3-vesicles", {}, 80, False, "Vesicles", "fatty-acid membranes"),
    ("rule", "abiogenesis-stage4-selection", {}, 95, False, "Protocell Selection", "Eigen–Schuster hypercycle"),
    ("rule", "abiogenesis-luca", {}, 130, False, "LUCA", "comparative genomics · Weiss 2016"),
    ("rule", "conway", {}, 40, True, "Game of Life", "Conway · B3/S23"),
    ("rule", "wolfram1d", dict(rule_number=110), 0, True, "Elementary CA", "Wolfram · Rule 110, Turing-complete"),
    ("rule", "abiogenesis-pipeline-extended", {}, 30, False, "The Pipeline", "soup → LUCA, 12 stages"),
    ("grid", None, None, 0, False, "Discovery Search", "scoring thousands of sims"),
    ("relit", None, None, 0, False, "Generative Art", "3D relighting + kaleidoscope"),
    ("title", None, None, 0, False, "CellAutomata", "one sandbox · the whole spectrum"),
]
SEG = 4.5  # seconds per tour stop


def bg():
    top = np.array([7, 11, 18], np.float32); bot = np.array([15, 26, 42], np.float32)
    ramp = np.linspace(0, 1, SIZE, np.float32)[:, None]
    return np.repeat((top * (1 - ramp) + bot * ramp)[:, None, :], SIZE, 1).astype(np.uint8)
BG = bg()


def make_engine(rule, cfg, grid, scatter=False, seed=1):
    eng = Engine(width=grid, height=grid, rule=REGISTRY[rule](**cfg), seed=seed)
    if scatter and hasattr(eng.state, "u"):
        rng = np.random.default_rng(seed); u = np.ones((grid, grid), np.float32); v = np.zeros((grid, grid), np.float32); r = 5
        for _ in range(grid // 11):
            cy = int(rng.integers(r, grid - r)); cx = int(rng.integers(r, grid - r))
            u[cy - r:cy + r, cx - r:cx + r] = 0.5; v[cy - r:cy + r, cx - r:cx + r] = 0.25
        v += rng.uniform(0, 0.02, (grid, grid)).astype(np.float32); eng.state.u = u; eng.state.v = np.clip(v, 0, 1)
    return eng


def label(img, idx, total, name, sub):
    d = ImageDraw.Draw(img)
    d.text((30, 26), f"CellAutomata · the full spectrum   {idx}/{total}", font=ImageFont.truetype(FB, 24), fill=(150, 200, 200))
    d.rectangle([0, SIZE - 96, SIZE, SIZE], fill=(5, 7, 11))
    d.text((32, SIZE - 84), name, font=ImageFont.truetype(FB, 46), fill=(244, 248, 252))
    d.text((34, SIZE - 34), sub, font=ImageFont.truetype(FR, 25), fill=(172, 190, 208))


def fade(arr, fi, n, k=9):
    a = min(1.0, (fi + 1) / k, (n - fi) / k)
    return arr if a >= 0.999 else (arr.astype(np.float32) * a).astype(np.uint8)


def main():
    os.makedirs("media", exist_ok=True)
    n_stops = sum(1 for s in TOUR if s[0] != "title")
    silent = "/tmp/spectrum_silent.mp4"
    wr = imageio_ffmpeg.write_frames(silent, (SIZE, SIZE), fps=FPS, codec="libx264", pix_fmt_in="rgb24",
        pix_fmt_out="yuv420p", macro_block_size=2, output_params=["-crf", "19", "-preset", "medium"])
    wr.send(None)
    grid_engs = None
    idx = 0
    for kind, rule, cfg, warm, crisp, name, sub in TOUR:
        N = int((3.0 if kind == "title" else SEG) * FPS)
        if kind == "title":
            img = Image.fromarray(BG.copy()); d = ImageDraw.Draw(img)
            tf = ImageFont.truetype(FB, 74); sf = ImageFont.truetype(FR, 34)
            d.text((SIZE / 2 - d.textlength(name, font=tf) / 2, 430), name, font=tf, fill=(238, 244, 250))
            d.text((SIZE / 2 - d.textlength(sub, font=sf) / 2, 540), sub, font=sf, fill=(150, 190, 205))
            arr = np.asarray(img, np.uint8)
            for fi in range(N):
                wr.send(np.ascontiguousarray(fade(arr.copy(), fi, N, 12)).tobytes())
            continue
        idx += 1
        if kind == "rule":
            scatter = rule == GS
            eng = make_engine(rule, cfg, 130 if crisp else 170, scatter=scatter)
            rl = REGISTRY[rule](**cfg)
            for _ in range(warm):
                eng.step()
            for fi in range(N):
                eng.step()
                rgb = np.asarray(rl.render_rgb(eng.state), np.uint8)
                img = Image.fromarray(rgb).resize((SIZE, SIZE), Image.NEAREST if crisp else Image.BICUBIC).convert("RGB")
                label(img, idx, n_stops, name, sub)
                wr.send(np.ascontiguousarray(fade(np.asarray(img, np.uint8), fi, N)).tobytes())
        elif kind == "gs":
            eng = make_engine(GS, cfg, 200, scatter=True); rl = REGISTRY[GS](**cfg)
            for _ in range(warm):
                eng.step()
            for fi in range(N):
                eng.step()
                rgb = np.asarray(rl.render_rgb(eng.state), np.uint8)
                img = Image.fromarray(rgb).resize((SIZE, SIZE), Image.BICUBIC).convert("RGB")
                label(img, idx, n_stops, name, sub)
                wr.send(np.ascontiguousarray(fade(np.asarray(img, np.uint8), fi, N)).tobytes())
        elif kind == "grid":
            regs = [dict(F=0.026, k=0.055), dict(F=0.0545, k=0.062), dict(F=0.018, k=0.05),
                    dict(preset="labyrinth"), dict(F=0.030, k=0.057), dict(F=0.0264, k=0.0579),
                    dict(F=0.07, k=0.061), dict(F=0.0186, k=0.0502), dict(preset="mitosis")]
            engs = [make_engine(GS, c, 90, scatter=True, seed=i + 1) for i, c in enumerate(regs)]
            for _ in range(150):
                for e in engs:
                    e.step()
            for fi in range(N):
                canvas = Image.new("RGB", (SIZE, SIZE), (6, 8, 12))
                for i, e in enumerate(engs):
                    e.step(); v = np.asarray(e.state.v, np.float32)
                    til = Image.fromarray(MX.colorize(v, ["nebula", "ice", "fire", "amethyst", "aqua", "emerald", "gold", "rose", "ember"][i]).astype(np.uint8))
                    canvas.paste(til.resize((SIZE // 3, SIZE // 3), Image.BICUBIC), ((i % 3) * SIZE // 3, (i // 3) * SIZE // 3))
                label(canvas, idx, n_stops, name, sub)
                wr.send(np.ascontiguousarray(fade(np.asarray(canvas, np.uint8), fi, N)).tobytes())
        elif kind == "relit":
            eng = make_engine(GS, dict(F=0.026, k=0.055), 220, scatter=True)
            for _ in range(320):
                eng.step()
            for fi in range(N):
                eng.step(); v = np.asarray(eng.state.v, np.float32)
                alb = R.colorize(v, "gold"); lit = R.relight(v, alb, az=2 * np.pi * fi / N + 0.6, bump=3.4, shininess=26, ks=1.05)
                img = Image.fromarray(lit).resize((SIZE, SIZE), Image.BICUBIC).convert("RGB")
                label(img, idx, n_stops, name, sub)
                wr.send(np.ascontiguousarray(fade(np.asarray(img, np.uint8), fi, N)).tobytes())
        print(f"  stop {idx}/{n_stops}: {name}", flush=True)
    wr.close()
    total_s = sum((3.0 if s[0] == "title" else SEG) for s in TOUR)
    bed_path = "/tmp/spectrum_bed.wav"
    bed = MP.ambient_bed(int(total_s * SR), SR)
    mix = np.clip(bed * 0.16 * 32767, -32768, 32767).astype(np.int16)
    with wave.open(bed_path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(mix.tobytes())
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", silent, "-i", bed_path,
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest",
                    "-movflags", "+faststart", "media/full_spectrum.mp4"], check=True)
    print(f"DONE -> media/full_spectrum.mp4 ({os.path.getsize('media/full_spectrum.mp4')/1e6:.1f} MB, {total_s:.0f}s)")


if __name__ == "__main__":
    main()
