"""Relit reaction-diffusion — treat the v field as a heightfield, compute surface
normals from its gradient, and Blinn-Phong shade with an orbiting light. Flat
Gray-Scott becomes 3D molten/glassy/organic relief. Cheap numpy, big payoff.

  python3 tools/relit.py
"""
from __future__ import annotations
import os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
from cellauto.engine import Engine
from cellauto.rules import REGISTRY

RULE = "abiogenesis-stage1-grayscott"
FF = imageio_ffmpeg.get_ffmpeg_exe()
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def lut(stops):
    g = np.linspace(0, 1, 256); xs = np.array([s[0] for s in stops])
    cols = np.array([s[1] for s in stops], float)
    return np.stack([np.interp(g, xs, cols[:, c]) for c in range(3)], 1).astype(np.float32) / 255.0


PAL = {
    "gold":   lut([(0, (20, 12, 2)), (.4, (120, 70, 12)), (.7, (210, 150, 35)), (.9, (245, 205, 90)), (1, (255, 245, 200))]),
    "copper": lut([(0, (16, 6, 4)), (.4, (110, 40, 24)), (.7, (200, 95, 55)), (.9, (240, 160, 110)), (1, (255, 225, 195))]),
    "jade":   lut([(0, (4, 16, 10)), (.4, (16, 80, 50)), (.7, (40, 165, 100)), (.9, (130, 220, 150)), (1, (225, 255, 230))]),
    "ice":    lut([(0, (6, 12, 22)), (.4, (24, 70, 130)), (.7, (70, 150, 220)), (.9, (150, 210, 245)), (1, (235, 248, 255))]),
    "amethyst": lut([(0, (14, 6, 22)), (.4, (70, 28, 120)), (.7, (140, 70, 200)), (.9, (200, 150, 240)), (1, (245, 235, 255))]),
}


def colorize(v, pal, vmax=0.42, gamma=0.85):
    idx = (np.clip(v / vmax, 0, 1) ** gamma * 255).astype(np.uint8)
    return PAL[pal][idx]                       # H x W x 3 float (0..1)


def relight(v, albedo, az, el=0.55, bump=3.0, shininess=26.0, ambient=0.16, ks=0.95):
    gy, gx = np.gradient(v.astype(np.float32))
    nx = -gx * bump; ny = -gy * bump; nz = np.ones_like(v, np.float32)
    inv = 1.0 / np.sqrt(nx * nx + ny * ny + nz * nz)
    nx *= inv; ny *= inv; nz *= inv
    lx = np.cos(el) * np.cos(az); ly = np.cos(el) * np.sin(az); lz = np.sin(el)
    diff = np.clip(nx * lx + ny * ly + nz * lz, 0, 1)
    hx, hy, hz = lx, ly, lz + 1.0
    hn = 1.0 / np.sqrt(hx * hx + hy * hy + hz * hz)
    spec = np.clip(nx * (hx * hn) + ny * (hy * hn) + nz * (hz * hn), 0, 1) ** shininess
    lit = albedo * (ambient + (1 - ambient) * diff[..., None]) + ks * spec[..., None]
    return (np.clip(lit, 0, 1) * 255).astype(np.uint8)


def evolve_scatter(kw, grid, seed=1):
    eng = Engine(width=grid, height=grid, rule=REGISTRY[RULE](**kw), seed=seed)
    rng = np.random.default_rng(seed)
    u = np.ones((grid, grid), np.float32); v = np.zeros((grid, grid), np.float32); r = 5
    for _ in range(grid // 11):
        cy = int(rng.integers(r, grid - r)); cx = int(rng.integers(r, grid - r))
        u[cy - r:cy + r, cx - r:cx + r] = 0.5; v[cy - r:cy + r, cx - r:cx + r] = 0.25
    v += rng.uniform(0, 0.02, (grid, grid)).astype(np.float32)
    eng.state.u = u; eng.state.v = np.clip(v, 0, 1)
    return eng


MATERIALS = [
    dict(name="MOLTEN GOLD", kw=dict(F=0.026, k=0.055), pal="gold", bump=3.2, shin=24, ks=1.05),
    dict(name="LIVING JADE", kw=dict(F=0.0545, k=0.062), pal="jade", bump=2.6, shin=16, ks=0.7),
    dict(name="OBSIDIAN ICE", kw=dict(preset="labyrinth"), pal="ice", bump=2.9, shin=40, ks=1.1),
    dict(name="PLASMA CHROME", kw=dict(F=0.018, k=0.050), pal="amethyst", bump=3.0, shin=30, ks=1.0),
]
SIZE, FPS, GRID = 1080, 30, 240


def writer(path):
    wr = imageio_ffmpeg.write_frames(path, (SIZE, SIZE), fps=FPS, codec="libx264",
        pix_fmt_in="rgb24", pix_fmt_out="yuv420p", macro_block_size=2,
        output_params=["-crf", "17", "-preset", "medium"]); wr.send(None); return wr


def label(img, name, sub):
    d = ImageDraw.Draw(img)
    d.text((30, 26), name, font=ImageFont.truetype(FB, 44), fill=(245, 248, 252))
    d.text((32, 80), sub, font=ImageFont.truetype(FR, 23), fill=(180, 195, 210))


def render_material(m, out, dur=11, warm=320):
    eng = evolve_scatter(m["kw"], GRID)
    for _ in range(warm):
        eng.step()
    n = dur * FPS; wr = writer(out)
    for fi in range(n):
        eng.step()
        v = np.asarray(eng.state.v, np.float32)
        alb = colorize(v, m["pal"])
        az = 2 * np.pi * fi / n + 0.6           # orbiting light
        lit = relight(v, alb, az, bump=m["bump"], shininess=m["shin"], ks=m["ks"])
        img = Image.fromarray(lit).resize((SIZE, SIZE), Image.BICUBIC).convert("RGB")
        label(img, m["name"], "reaction-diffusion as a lit 3D surface (normal-mapped)")
        af = min(1.0, (fi + 1) / 12, (n - fi) / 12)
        fr = np.asarray(img, np.uint8)
        if af < 0.999:
            fr = (fr.astype(np.float32) * af).astype(np.uint8)
        wr.send(np.ascontiguousarray(fr).tobytes())
    wr.close()
    print(f"  {m['name']} -> {out}")


def render_compare(out, dur=9):
    m = MATERIALS[0]
    eng = evolve_scatter(m["kw"], GRID)
    for _ in range(320):
        eng.step()
    n = dur * FPS; wr = writer(out)
    for fi in range(n):
        eng.step()
        v = np.asarray(eng.state.v, np.float32)
        alb = colorize(v, m["pal"])
        flat = (np.clip(alb, 0, 1) * 255).astype(np.uint8)
        lit = relight(v, alb, 2 * np.pi * fi / n + 0.6, bump=m["bump"], shininess=m["shin"], ks=m["ks"])
        full = Image.fromarray(flat).resize((SIZE, SIZE), Image.BICUBIC).convert("RGB")
        litimg = Image.fromarray(lit).resize((SIZE, SIZE), Image.BICUBIC)
        full.paste(litimg.crop((SIZE // 2, 0, SIZE, SIZE)), (SIZE // 2, 0))
        d = ImageDraw.Draw(full)
        d.line([(SIZE // 2, 0), (SIZE // 2, SIZE)], fill=(245, 248, 252), width=3)
        d.text((40, SIZE - 56), "FLAT", font=ImageFont.truetype(FB, 36), fill=(220, 225, 232))
        d.text((SIZE // 2 + 40, SIZE - 56), "RELIT", font=ImageFont.truetype(FB, 36), fill=(245, 235, 200))
        af = min(1.0, (fi + 1) / 12, (n - fi) / 12)
        fr = np.asarray(full, np.uint8)
        if af < 0.999:
            fr = (fr.astype(np.float32) * af).astype(np.uint8)
        wr.send(np.ascontiguousarray(fr).tobytes())
    wr.close()
    print(f"  FLAT|RELIT compare -> {out}")


def main():
    os.makedirs("media", exist_ok=True)
    tmp = "/tmp/relit"; os.makedirs(tmp, exist_ok=True)
    print("rendering relit materials ...")
    parts = []
    for m in MATERIALS:
        p = f"{tmp}/{m['name'].split()[0].lower()}.mp4"
        render_material(m, p); parts.append(p)
    render_compare("media/relit_compare.mp4")
    # also keep the gold hero standalone
    import shutil; shutil.copy(parts[0], "media/relit_molten_gold.mp4")
    lst = f"{tmp}/list.txt"
    open(lst, "w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in parts))
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", lst, "-c", "copy", "-movflags", "+faststart", "media/relit_reel.mp4"], check=True)
    print(f"DONE -> media/relit_reel.mp4 + relit_compare.mp4 + relit_molten_gold.mp4")


if __name__ == "__main__":
    main()
