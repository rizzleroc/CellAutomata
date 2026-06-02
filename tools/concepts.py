"""GENESIS concepts — realize the whip/Kimi brainstorm as relit 3D videos.
Reuses relit.py's normal-map lighting so reaction-diffusion reads as living
matter. Themed, titled segments + a deep-time DAY counter for "The 9th Day",
ambient bed, concatenated into a reel (+ individual clips).

  python3 tools/concepts.py
"""
from __future__ import annotations
import os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
import relit as R
import beauty_ultra as BU
from cellauto.engine import Engine
from cellauto.rules import REGISTRY

RULE = R.RULE
FF = imageio_ffmpeg.get_ffmpeg_exe()
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SIZE, FPS = 1080, 30

SEGS = [
    dict(name="THE 9TH DAY", sub="from lifeless soup, self-replicators emerge",
         kw=dict(preset="mitosis"), seed="central", grid=150, warm=0,
         pal="copper", bump=3.4, shin=22, ks=1.0, dur=13, day=True),
    dict(name="NEURAL GARDEN", sub="cells wiring themselves into synaptic channels",
         kw=dict(preset="labyrinth"), seed="scatter", grid=240, warm=300,
         pal="jade", bump=2.8, shin=18, ks=0.8, dur=11),
    dict(name="CRYSTAL BRAIN", sub="crystalline cognition — order out of corrosion",
         kw=dict(F=0.026, k=0.055), seed="scatter", grid=240, warm=300,
         pal="ice", bump=3.0, shin=42, ks=1.1, dur=11),
    dict(name="LUCA'S METABOLISM", sub="the last universal ancestor's metabolic web",
         kw=dict(F=0.0545, k=0.062), seed="scatter", grid=240, warm=300,
         pal="gold", bump=3.0, shin=24, ks=1.0, dur=11),
]


def fmt_day(d):
    d = float(d)
    if d >= 1e9: return f"{d/1e9:.1f}B"
    if d >= 1e6: return f"{d/1e6:.1f}M"
    if d >= 1e3: return f"{int(d):,}"
    return str(int(d))


def make_engine(seg):
    grid = seg["grid"]
    eng = Engine(width=grid, height=grid, rule=REGISTRY[RULE](**seg["kw"]), seed=1)
    if seg["seed"] == "scatter":
        rng = np.random.default_rng(7)
        u = np.ones((grid, grid), np.float32); v = np.zeros((grid, grid), np.float32); r = 5
        for _ in range(grid // 11):
            cy = int(rng.integers(r, grid - r)); cx = int(rng.integers(r, grid - r))
            u[cy - r:cy + r, cx - r:cx + r] = 0.5; v[cy - r:cy + r, cx - r:cx + r] = 0.25
        v += rng.uniform(0, 0.02, (grid, grid)).astype(np.float32)
        eng.state.u = u; eng.state.v = np.clip(v, 0, 1)
    for _ in range(seg["warm"]):
        eng.step()
    return eng


def seg_writer(path):
    wr = imageio_ffmpeg.write_frames(path, (SIZE, SIZE), fps=FPS, codec="libx264",
        pix_fmt_in="rgb24", pix_fmt_out="yuv420p", macro_block_size=2,
        output_params=["-crf", "17", "-preset", "medium"]); wr.send(None); return wr


def render_seg(seg, path):
    eng = make_engine(seg)
    n = seg["dur"] * FPS; wr = seg_writer(path)
    tf = ImageFont.truetype(FB, 46); sf = ImageFont.truetype(FR, 24); dayf = ImageFont.truetype(FB, 70)
    for fi in range(n):
        eng.step()
        v = np.asarray(eng.state.v, np.float32)
        alb = R.colorize(v, seg["pal"])
        az = 2 * np.pi * fi / n + 0.6
        lit = R.relight(v, alb, az, bump=seg["bump"], shininess=seg["shin"], ks=seg["ks"])
        img = Image.fromarray(lit).resize((SIZE, SIZE), Image.BICUBIC).convert("RGB")
        d = ImageDraw.Draw(img)
        d.rectangle([0, SIZE - 92, SIZE, SIZE], fill=(5, 7, 11))
        d.text((32, SIZE - 82), seg["name"], font=tf, fill=(244, 248, 252))
        d.text((34, SIZE - 34), seg["sub"], font=sf, fill=(175, 192, 208))
        if seg.get("day"):
            day = 10 ** (1 + 5.6 * (fi / n))
            txt = f"DAY {fmt_day(day)}"
            d.text((SIZE / 2 - d.textlength(txt, font=dayf) / 2, 30), txt, font=dayf, fill=(245, 240, 220))
        af = min(1.0, (fi + 1) / 12, (n - fi) / 12)
        fr = np.asarray(img, np.uint8)
        if af < 0.999:
            fr = (fr.astype(np.float32) * af).astype(np.uint8)
        wr.send(np.ascontiguousarray(fr).tobytes())
    wr.close()
    print(f"  {seg['name']}")


def main():
    os.makedirs("media", exist_ok=True)
    tmp = "/tmp/concepts"; os.makedirs(tmp, exist_ok=True)
    print("rendering concept segments ...")
    parts = []
    for seg in SEGS:
        slug = seg["name"].split()[0].lower() if seg["name"][0] != "T" else seg["name"].replace(" ", "_").replace("'", "").lower()
        p = f"{tmp}/{seg['name'].replace(' ', '_').replace(chr(39), '')}.mp4"
        render_seg(seg, p); parts.append(p)
        # keep "The 9th Day" + "Neural Garden" as standalone heroes
        if seg["name"] in ("THE 9TH DAY", "NEURAL GARDEN"):
            import shutil; shutil.copy(p, f"media/concept_{seg['name'].split()[-1].lower()}.mp4")
    total = sum(s["dur"] for s in SEGS)
    lst = f"{tmp}/list.txt"
    open(lst, "w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in parts))
    silent = f"{tmp}/silent.mp4"
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", lst, "-c", "copy", silent], check=True)
    bed = f"{tmp}/bed.wav"; BU.ambient(total, bed)
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", silent, "-i", bed,
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "176k", "-shortest",
                    "-movflags", "+faststart", "media/concepts_reel.mp4"], check=True)
    print(f"DONE -> media/concepts_reel.mp4 ({os.path.getsize('media/concepts_reel.mp4')/1e6:.1f} MB, {total}s) + concept heroes")


if __name__ == "__main__":
    main()
