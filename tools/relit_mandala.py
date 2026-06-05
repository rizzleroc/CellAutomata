"""Relit mandalas — fold the compound kaleidoscope, then treat it as a carved
heightfield and Blinn-Phong relight it: a 3D gold / jade / amethyst / ice
medallion spinning under a fixed light. Seamless full-360 loop. Reuses relit.py
(relighting) + mandala_x (compound fold).

  python3 tools/relit_mandala.py
"""
from __future__ import annotations
import os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
import relit as R
import mandala_x as MX
import beauty_ultra as BU

FF = imageio_ffmpeg.get_ffmpeg_exe()
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SIZE, FPS = 1080, 30

MATS = [
    dict(name="GOLD MEDALLION", kw=dict(F=0.018, k=0.050), n1=12, n2=6, octs=1, pal="gold",   bump=4.2, shin=26, ks=1.1, warm=440),
    dict(name="JADE ROSETTE",   kw=dict(F=0.026, k=0.055), n1=8,  n2=6, octs=1, pal="jade",   bump=3.6, shin=18, ks=0.75, warm=420),
    dict(name="AMETHYST SIGIL", kw=dict(preset="labyrinth"), n1=16, n2=6, octs=2, pal="amethyst", bump=4.2, shin=30, ks=1.05, warm=440),
    dict(name="ICE CRYSTAL",    kw=dict(F=0.0545, k=0.062), n1=12, n2=6, octs=1, pal="ice",    bump=4.4, shin=46, ks=1.2, warm=520),
]


def writer(path):
    wr = imageio_ffmpeg.write_frames(path, (SIZE, SIZE), fps=FPS, codec="libx264",
        pix_fmt_in="rgb24", pix_fmt_out="yuv420p", macro_block_size=2,
        output_params=["-crf", "17", "-preset", "medium"]); wr.send(None); return wr


def build_field(m, K=760):
    eng = R.evolve_scatter(m["kw"], 240)
    for _ in range(m["warm"]):
        eng.step()
    v = np.asarray(eng.state.v, np.float32); v /= v.max() + 1e-9
    return MX.compound(MX.Kal(K, 240), v, m["n1"], m["n2"], m["octs"]).astype(np.float32)   # 0..1, KxK


def render_loop(m, out, dur=10):
    M = build_field(m)
    Mimg = Image.fromarray(M)                 # 'F' float image for rotation
    N = dur * FPS; wr = writer(out)
    lf = ImageFont.truetype(FB, 38)
    for fi in range(N):
        Mr = np.asarray(Mimg.rotate(360.0 * fi / N, resample=Image.BILINEAR), np.float32)   # spin (seamless)
        alb = R.colorize(Mr, m["pal"])
        lit = R.relight(Mr, alb, az=0.7, el=0.5, bump=m["bump"], shininess=m["shin"], ks=m["ks"])
        img = Image.fromarray(lit).resize((SIZE, SIZE), Image.BICUBIC).convert("RGB")
        d = ImageDraw.Draw(img); d.text((34, SIZE - 60), m["name"], font=lf, fill=(238, 244, 250))
        af = min(1.0, (fi + 1) / 12, (N - fi) / 12)
        fr = np.asarray(img, np.uint8)
        if af < 0.999:
            fr = (fr.astype(np.float32) * af).astype(np.uint8)
        wr.send(np.ascontiguousarray(fr).tobytes())
    wr.close()
    print(f"  {m['name']} -> {out}")


def main():
    os.makedirs("media", exist_ok=True)
    tmp = "/tmp/relmand"; os.makedirs(tmp, exist_ok=True)
    print("rendering relit mandalas ...")
    parts = []
    for m in MATS:
        p = f"{tmp}/{m['name'].split()[0].lower()}.mp4"; render_loop(m, p); parts.append(p)
    import shutil; shutil.copy(parts[0], "media/relit_mandala_gold.mp4")
    # reel + ambient bed
    total = len(MATS) * 10
    lst = f"{tmp}/list.txt"; open(lst, "w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in parts))
    silent = f"{tmp}/silent.mp4"
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", lst, "-c", "copy", silent], check=True)
    bed = f"{tmp}/bed.wav"; BU.ambient(total, bed)
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", silent, "-i", bed,
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "176k", "-shortest",
                    "-movflags", "+faststart", "media/relit_mandala_reel.mp4"], check=True)
    # lean seamless GIF of the gold medallion
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", parts[0],
                    "-vf", "fps=14,scale=460:-1:flags=lanczos,palettegen=max_colors=80:stats_mode=diff", "/tmp/rm_pal.png"], check=True)
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", parts[0], "-i", "/tmp/rm_pal.png",
                    "-lavfi", "fps=14,scale=460:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=4",
                    "-loop", "0", "media/relit_mandala.gif"], check=True)
    print(f"DONE -> media/relit_mandala_reel.mp4 + relit_mandala_gold.mp4 + relit_mandala.gif")


if __name__ == "__main__":
    main()
