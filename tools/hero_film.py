"""hero_film.py — "Catalytic Silence", the cellauto flagship hero film (v2).

A landscape (1920x1080) cinematic cut for the website overture + social,
built from three visual registers:

  1. THE SEARCH  — the everything-wall of all 17 rules / thousands of sims,
                   conveying the scale of the hunt for the best configs.
  2. SEM         — live specimens rendered as a real instrument view:
                   the v-field as a heightfield, normal-mapped + Blinn-Phong
                   relit into a monochrome / warm-sepia micrograph, wrapped in
                   "LIVE SEM FEED" chrome (per docs/PRD_SEM_VISUALIZATION.md).
                   NOT a viridis heat-map.
  3. PAINTINGS   — the photoreal stage plates (docs/generated/*.png), the V1
                   art layer; light-studio cut-outs are keyed onto obsidian.

All titling is Pillow (the bundled imageio-ffmpeg has no drawtext); ffmpeg
does Ken-Burns, xfade and the ambient drone bed.

    python tools/hero_film.py --test     # fast, low-res pipeline check
    python tools/hero_film.py            # full render -> media/hero/
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from cellauto.engine import Engine                       # noqa: E402
from cellauto.rules import REGISTRY                       # noqa: E402
import imageio_ffmpeg                                     # noqa: E402

FF = imageio_ffmpeg.get_ffmpeg_exe()

# ── Canvas + palette ────────────────────────────────────────────────────────
W, H = 1920, 1080
FPS = 30
OBSIDIAN = (8, 11, 18)
BONE = (230, 224, 208)
BONE_DIM = (150, 150, 142)
TEAL = (57, 212, 200)
REC = (214, 78, 70)

GEN = REPO / "docs" / "generated"

F_SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
F_ITAL = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
F_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


NARRATION = (
    "We searched. Seventeen rules, six thousand primordial soups, six hundred "
    "configurations of a reaction-diffusion equation — every one scored for how "
    "alive it looked, and the most alive were kept. This is what the instrument "
    "found. Before life, there was soup, seeded from the real yields of the 1953 "
    "Miller-Urey experiment. Then four numbers begin to divide, like protocells. "
    "Membranes close around the chemistry. Bounded chemistry begins to compete, "
    "and to copy. From primordial soup to the last universal common ancestor — "
    "this is cellauto, watching chemistry remember how to become."
)


# ── SEM heightfield relighting (per relit.py / SEM PRD) ──────────────────────
def lut(stops):
    g = np.linspace(0, 1, 256)
    xs = np.array([s[0] for s in stops])
    cols = np.array([s[1] for s in stops], float)
    return np.stack([np.interp(g, xs, cols[:, c]) for c in range(3)], 1).astype(np.float32) / 255.0


# warm-sepia "instrument" ramp — obsidian substrate -> bone highlight
SEM_LUT = lut([(0.0, (6, 6, 7)), (.28, (54, 45, 34)), (.55, (128, 108, 80)),
               (.80, (200, 180, 146)), (1.0, (242, 233, 214))])


def relight(h, albedo, az, el=0.55, bump=3.0, shin=22.0, ambient=0.18, ks=0.85):
    """Treat h (0..1) as a heightfield: normals from its gradient, Blinn-Phong
    shade with a light at azimuth `az`. Returns float 0..1 RGB."""
    gy, gx = np.gradient(h.astype(np.float32))
    nx, ny, nz = -gx * bump, -gy * bump, np.ones_like(h, np.float32)
    inv = 1.0 / np.sqrt(nx * nx + ny * ny + nz * nz)
    nx, ny, nz = nx * inv, ny * inv, nz * inv
    lx, ly, lz = np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)
    diff = np.clip(nx * lx + ny * ly + nz * lz, 0, 1)
    hx, hy, hz = lx, ly, lz + 1.0
    hn = 1.0 / np.sqrt(hx * hx + hy * hy + hz * hz)
    spec = np.clip(nx * (hx * hn) + ny * (hy * hn) + nz * (hz * hn), 0, 1) ** shin
    lit = albedo * (ambient + (1 - ambient) * diff[..., None]) + ks * spec[..., None]
    return np.clip(lit, 0, 1)


def sem_specimen(height, az, vmax, bump=3.0, shin=22, ks=0.85, gamma=0.85, grain=4.0):
    hn = np.clip(height.astype(np.float32) / vmax, 0, 1) ** gamma
    alb = SEM_LUT[(hn * 255).astype(np.uint8)]
    lit = relight(hn, alb, az, bump=bump, shin=shin, ks=ks)
    arr = lit * 255.0
    if grain:
        arr += np.random.normal(0, grain, arr.shape)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


# ── Specimen square on obsidian ──────────────────────────────────────────────
SPEC = 850
SX, SY = (W - SPEC) // 2, 30


def on_obsidian(specimen: Image.Image) -> Image.Image:
    canvas = Image.new("RGB", (W, H), OBSIDIAN)
    canvas.paste(specimen.resize((SPEC, SPEC), Image.LANCZOS), (SX, SY))
    return canvas


def key_onto_obsidian(path, tol=46, lthr=196, feather=2.0):
    """Drop a light-studio background to obsidian (cut-out painting plates)."""
    a = np.asarray(Image.open(path).convert("RGB"), np.float32)
    cps = np.concatenate([a[:20, :20].reshape(-1, 3), a[:20, -20:].reshape(-1, 3),
                          a[-20:, :20].reshape(-1, 3), a[-20:, -20:].reshape(-1, 3)])
    corner = np.median(cps, 0)
    if corner.mean() < 120:                       # already dark -> nothing to key
        return Image.fromarray(a.astype(np.uint8), "RGB")
    d = np.sqrt(((a - corner) ** 2).sum(2))
    bg = (d < tol) & (a.mean(2) > lthr)
    alpha = np.asarray(Image.fromarray(np.where(bg, 0, 255).astype(np.uint8))
                       .filter(ImageFilter.GaussianBlur(feather)), np.float32)[:, :, None] / 255.0
    out = a * alpha + np.array(OBSIDIAN, np.float32) * (1 - alpha)
    return Image.fromarray(out.astype(np.uint8), "RGB")


def frame_plate(plate, mode: str) -> Image.Image:
    """'cover' fills the frame (+edge vignette); 'painting' keys a cut-out plate
    onto obsidian and fits it into the vitrine box."""
    canvas = Image.new("RGB", (W, H), OBSIDIAN)
    if mode == "cover":
        im = Image.open(plate).convert("RGBA")
        s = max(W / im.width, H / im.height)
        im2 = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
        im2 = im2.crop(((im2.width - W) // 2, (im2.height - H) // 2,
                        (im2.width - W) // 2 + W, (im2.height - H) // 2 + H))
        base = canvas.convert("RGBA")
        base.alpha_composite(im2)
        arr = np.asarray(base.convert("RGB"), np.float32)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        vig = np.clip(1.0 - 0.92 * np.clip((r - 0.50) / 0.50, 0, 1) ** 1.6, 0.0, 1.0)
        arr = arr * vig[:, :, None] + np.array(OBSIDIAN, np.float32) * (1 - vig)[:, :, None]
        return Image.fromarray(arr.astype(np.uint8), "RGB")
    else:  # painting (keyed cut-out, fit into vitrine box)
        im = key_onto_obsidian(plate)
        s = min((SPEC + 120) / im.width, (SPEC + 120) / im.height)
        im2 = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
        canvas.paste(im2, ((W - im2.width) // 2, (H - im2.height) // 2 - 30))
        return canvas


# ── Text helpers ─────────────────────────────────────────────────────────────
def text_tracked(d, xy, s, fnt, fill, tracking=0, anchor="l"):
    widths = [d.textlength(ch, font=fnt) for ch in s]
    total = sum(widths) + tracking * (len(s) - 1)
    x, y = xy
    if anchor == "c":
        x -= total / 2
    elif anchor == "r":
        x -= total
    for ch, wch in zip(s, widths):
        d.text((x, y), ch, font=fnt, fill=fill)
        x += wch + tracking


def caption_overlay(path, eyebrow, title, descriptor, citation, ticks=True, sem=False):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    top = 760
    for y in range(top, H):
        a = int(150 * (y - top) / (H - top))
        d.line([(0, y), (W, y)], fill=(6, 9, 14, a))
    if ticks:
        col = (BONE if sem else TEAL) + (160,)
        gap, leg, sw = 26, 56, 2
        for cx, cy, dx, dy in [(SX, SY, 1, 1), (SX + SPEC, SY, -1, 1),
                               (SX, SY + SPEC, 1, -1), (SX + SPEC, SY + SPEC, -1, -1)]:
            d.line([(cx - dx * gap, cy - dy * gap), (cx - dx * gap + dx * leg, cy - dy * gap)], fill=col, width=sw)
            d.line([(cx - dx * gap, cy - dy * gap), (cx - dx * gap, cy - dy * gap + dy * leg)], fill=col, width=sw)
    if sem:
        # LIVE SEM FEED instrument chrome
        fm = font(F_MONO, 22)
        d.ellipse([(SX - 26, 4), (SX - 10, 20)], fill=REC + (255,))
        text_tracked(d, (SX + 2, 2), "REC   LIVE  SEM  FEED", fm, BONE + (235,), tracking=3)
        text_tracked(d, (SX + SPEC + 26, 2), "00:00:14:08", fm, BONE_DIM + (255,), tracking=2, anchor="r")
        # scale bar under the specimen, left
        sb_y = SY + SPEC + 16
        d.line([(SX, sb_y), (SX + 160, sb_y)], fill=BONE + (235,), width=2)
        d.line([(SX, sb_y - 6), (SX, sb_y + 6)], fill=BONE + (235,), width=2)
        d.line([(SX + 160, sb_y - 6), (SX + 160, sb_y + 6)], fill=BONE + (235,), width=2)
        d.text((SX + 172, sb_y - 14), "2 µm", font=fm, fill=BONE + (235,))
        text_tracked(d, (SX + SPEC, sb_y - 14), "HV 5.00 kV   WD 9.8 mm   MAG 12000×   SE2",
                     fm, BONE_DIM + (255,), tracking=1, anchor="r")
    # lower-third title block
    bx, by = 150, 892
    text_tracked(d, (bx, by), eyebrow, font(F_MONO, 22), BONE_DIM + (255,), tracking=6)
    d.line([(bx, by + 36), (bx + 360, by + 36)], fill=(BONE if sem else TEAL) + (160,), width=1)
    text_tracked(d, (bx, by + 52), title, font(F_SERIF, 60), BONE + (255,), tracking=2)
    d.text((bx + 2, by + 130), descriptor, font=font(F_ITAL, 34), fill=BONE + (230,))
    text_tracked(d, (W - 150, by + 8), citation, font(F_MONO, 22), BONE_DIM + (255,), tracking=4, anchor="r")
    img.save(path)


def title_card(path, eyebrow, big, sub, footer=None):
    img = Image.new("RGB", (W, H), OBSIDIAN)
    d = ImageDraw.Draw(img, "RGBA")
    m, leg = 70, 34
    for cx, cy, dx, dy in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line([(cx, cy), (cx + dx * leg, cy)], fill=BONE_DIM + (120,), width=1)
        d.line([(cx, cy), (cx, cy + dy * leg)], fill=BONE_DIM + (120,), width=1)
    text_tracked(d, (W / 2, 360), eyebrow, font(F_MONO, 24), BONE_DIM, tracking=8, anchor="c")
    text_tracked(d, (W / 2, 430), big, font(F_SERIF, 150), BONE, tracking=10, anchor="c")
    d.line([(W / 2 - 240, 620), (W / 2 + 240, 620)], fill=TEAL + (170,), width=1)
    f_sub = font(F_ITAL, 40)
    d.text((W / 2 - d.textlength(sub, font=f_sub) / 2, 660), sub, font=f_sub, fill=BONE)
    if footer:
        text_tracked(d, (W / 2, H - 130), footer, font(F_MONO, 24), BONE_DIM, tracking=6, anchor="c")
    img.save(path)


# ── ffmpeg helpers ───────────────────────────────────────────────────────────
def run(args):
    p = subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", *args],
                       capture_output=True, text=True)
    if p.returncode != 0:
        sys.stderr.write("FFMPEG FAIL\n" + p.stderr[-1500:] + "\n")
        raise RuntimeError("ffmpeg failed")


def fade_str(dur, fin, fout):
    s = ""
    if fin:
        s += ",fade=t=in:st=0:d=0.6:color=#08070c"
    if fout:
        s += f",fade=t=out:st={dur - 0.7:.2f}:d=0.7:color=#08070c"
    return s


def enc(clip, crf, preset):
    return ["-r", str(FPS), "-c:v", "libx264", "-crf", str(crf), "-preset", preset,
            "-pix_fmt", "yuv420p", clip]


# ── Beats ────────────────────────────────────────────────────────────────────
def scatter_seed(eng, grid):
    rng = np.random.default_rng(7)
    u, v = np.asarray(eng.state.u), np.asarray(eng.state.v)
    u[:], v[:] = 1.0, 0.0
    rad = max(2, grid // 80)
    for _ in range(max(60, grid * grid // 900)):
        cx, cy = int(rng.integers(rad, grid - rad)), int(rng.integers(rad, grid - rad))
        u[cy - rad:cy + rad, cx - rad:cx + rad] = 0.5
        v[cy - rad:cy + rad, cx - rad:cx + rad] = 0.25
    v += (rng.random((grid, grid)) - 0.5) * 0.02
    np.clip(v, 0.0, 1.0, out=v)
    eng.state.u[:], eng.state.v[:] = u, v


def frame_sem_gs(eng, az):
    return sem_specimen(np.asarray(eng.state.v, np.float32), az, vmax=0.42,
                        bump=3.4, shin=26, ks=0.95)


def frame_sem_lum(vmax=0.85, bump=2.6, shin=18, ks=0.7):
    def fn(eng, az):
        rgb = np.asarray(eng.rule.render_rgb(eng.state), np.float32)
        lum = (0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]) / 255.0
        return sem_specimen(lum, az, vmax=vmax, bump=bump, shin=shin, ks=ks)
    return fn


def sim_beat(tmp, idx, dur, cap, rule_name, cfg, seed, warmup, framefn,
             crf, preset, fin, fout, grid=240, steps_per=6, scatter=False):
    print(f"[beat {idx}] SEM sim {rule_name} grid={grid} frames={int(dur * FPS)}", flush=True)
    rule = REGISTRY[rule_name](**cfg)
    eng = Engine(width=grid, height=grid, rule=rule, seed=seed)
    if scatter:
        scatter_seed(eng, grid)
    for _ in range(warmup):
        eng.step()
    fdir = Path(tmp) / f"sim_{idx:02d}"
    fdir.mkdir(parents=True, exist_ok=True)
    n = int(dur * FPS)
    frozen = False
    for fi in range(n):
        if not frozen:
            t0 = time.time()
            for _ in range(steps_per):
                eng.step()
            if time.time() - t0 > 1.5:
                frozen = True
                sys.stderr.write(f"[beat {idx}] sim froze at frame {fi}\n")
        az = 2 * np.pi * fi / n + 0.6                  # orbiting instrument light
        on_obsidian(framefn(eng, az)).save(fdir / f"f_{fi:05d}.png")
    capp = Path(tmp) / f"cap_{idx:02d}.png"
    caption_overlay(capp, *cap, sem=True)
    clip = str(Path(tmp) / f"clip_{idx:02d}.mp4")
    fc = (f"[0:v]fps={FPS},format=rgba[a];[a][1:v]overlay=0:0"
          f"{fade_str(dur, fin, fout)},format=yuv420p[v]")
    run(["-framerate", str(FPS), "-i", str(fdir / "f_%05d.png"),
         "-loop", "1", "-t", str(dur), "-i", str(capp),
         "-filter_complex", fc, "-map", "[v]", "-t", str(dur), *enc(clip, crf, preset)])
    return clip


def plate_beat(tmp, idx, dur, plate, cap, mode, crf, preset, fin, fout, ticks=True):
    print(f"[beat {idx}] painting {Path(plate).name} ({mode})", flush=True)
    basep = Path(tmp) / f"base_{idx:02d}.png"
    frame_plate(plate, mode).save(basep)
    capp = Path(tmp) / f"cap_{idx:02d}.png"
    caption_overlay(capp, *cap, ticks=ticks)
    clip = str(Path(tmp) / f"clip_{idx:02d}.mp4")
    n = int(dur * FPS)
    zrate, zmax = (0.0009, 1.11) if mode == "cover" else (0.0006, 1.07)
    fc = (f"[0:v]fps={FPS},scale={W}:{H},setsar=1,"
          f"zoompan=z='min(1.0+{zrate}*on,{zmax})':d={n}:s={W}x{H}:fps={FPS}:"
          f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'[z];"
          f"[z]format=rgba[zz];[zz][1:v]overlay=0:0{fade_str(dur, fin, fout)},format=yuv420p[v]")
    run(["-loop", "1", "-t", str(dur), "-i", str(basep),
         "-loop", "1", "-t", str(dur), "-i", str(capp),
         "-filter_complex", fc, "-map", "[v]", "-t", str(dur), *enc(clip, crf, preset)])
    return clip


def video_beat(tmp, idx, dur, src, cap, crf, preset, fin, fout, ss=2.0):
    print(f"[beat {idx}] search footage {Path(src).name}", flush=True)
    capp = Path(tmp) / f"cap_{idx:02d}.png"
    caption_overlay(capp, *cap, ticks=False)
    clip = str(Path(tmp) / f"clip_{idx:02d}.mp4")
    n = int(dur * FPS)
    fc = (f"[0:v]fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
          f"eq=brightness=-0.10:saturation=0.72,setsar=1,"
          f"zoompan=z='min(1.0+0.0006*on,1.08)':d={n}:s={W}x{H}:fps={FPS}:"
          f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'[z];"
          f"[z]format=rgba[zz];[zz][1:v]overlay=0:0{fade_str(dur, fin, fout)},format=yuv420p[v]")
    run(["-ss", str(ss), "-t", str(dur), "-i", str(src),
         "-loop", "1", "-t", str(dur), "-i", str(capp),
         "-filter_complex", fc, "-map", "[v]", "-t", str(dur), *enc(clip, crf, preset)])
    return clip


def title_beat(tmp, idx, dur, card_args, crf, preset, fin, fout):
    print(f"[beat {idx}] title", flush=True)
    cardp = Path(tmp) / f"title_{idx:02d}.png"
    title_card(cardp, *card_args)
    clip = str(Path(tmp) / f"clip_{idx:02d}.mp4")
    fc = (f"[0:v]fps={FPS},scale={W}:{H},"
          f"zoompan=z='min(1.0+0.0004*on,1.05)':d={int(dur*FPS)}:s={W}x{H}:fps={FPS}:"
          f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'{fade_str(dur, fin, fout)},format=yuv420p[v]")
    run(["-loop", "1", "-t", str(dur), "-i", str(cardp),
         "-filter_complex", fc, "-map", "[v]", "-t", str(dur), *enc(clip, crf, preset)])
    return clip


# ── Assemble: xfade chain + ambient drone bed ────────────────────────────────
def assemble(clips, durs, out, crf, preset):
    T = 0.6
    tmp = tempfile.mkdtemp(prefix="herojoin_")
    inputs = []
    for c in clips:
        inputs += ["-i", c]
    parts, prev, cum = [], "[0:v]", durs[0]
    for i in range(1, len(clips)):
        off = cum - T
        lab = f"[x{i}]"
        parts.append(f"{prev}[{i}:v]xfade=transition=fade:duration={T}:offset={off:.3f}{lab}")
        prev = lab
        cum += durs[i] - T
    total = cum
    silent = os.path.join(tmp, "silent.mp4")
    run([*inputs, "-filter_complex", ";".join(parts), "-map", prev,
         *enc(silent, crf, preset), "-movflags", "+faststart"])
    af = (f"[1:a][2:a]amix=inputs=2[m];[m][3:a]amix=inputs=2,"
          f"volume=0.13,lowpass=f=380,tremolo=f=0.15:d=0.25,"
          f"afade=t=in:st=0:d=2.0,afade=t=out:st={total-2.2:.2f}:d=2.2[a]")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    run(["-i", silent,
         "-f", "lavfi", "-t", str(total), "-i", "sine=frequency=73.42:sample_rate=44100",
         "-f", "lavfi", "-t", str(total), "-i", "sine=frequency=110:sample_rate=44100",
         "-f", "lavfi", "-t", str(total), "-i", "sine=frequency=146.83:sample_rate=44100",
         "-filter_complex", af, "-map", "0:v", "-map", "[a]",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest",
         "-movflags", "+faststart", out])
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--out", default=str(REPO / "media" / "hero" / "cellauto_hero.mp4"))
    args = ap.parse_args()

    test = args.test
    crf = 30 if test else 21
    preset = "veryfast" if test else "medium"
    grid = 120 if test else 240
    f = 0.45 if test else 1.0

    tmp = tempfile.mkdtemp(prefix="herobeats_")
    clips, durs = [], []

    def add(clip, d):
        clips.append(clip)
        durs.append(d)

    # 0 — title
    d = 6 * f
    add(title_beat(tmp, 0, d,
                   ("P L A T E   I   ·   C A T A L Y T I C   S I L E N C E   ·   M M X X V I",
                    "cellauto", "an origin-of-life instrument"),
                   crf, preset, True, False), d)
    # 1 — THE SEARCH (scale)
    d = 9 * f
    add(video_beat(tmp, 1, d, REPO / "media" / "grand" / "everything_wall.mp4",
                   ("T H E   S E A R C H", "Seventeen Rules, Six Thousand Soups",
                    "Every configuration scored for life; the most alive were kept.",
                    "658 CONFIGURATIONS · GRID 140"),
                   crf, preset, False, False, ss=1.0), d)
    # 2 — primordial soup (painting)
    d = 9 * f
    add(plate_beat(tmp, 2, d, GEN / "stage0_soup.png",
                   ("S T A G E   0   ·   P R I M O R D I A L   S O U P", "Primordial Soup",
                    "Monomers condense in a reducing ocean.", "MILLER · UREY  1953"),
                   "cover", crf, preset, False, False, ticks=False), d)
    # 3 — the first division (SEM hero)
    d = 15 * f
    add(sim_beat(tmp, 3, d,
                 ("S T A G E   1   ·   R E A C T I O N – D I F F U S I O N", "The First Division",
                  "Four numbers, splitting like protocells.", "TURING 1952 · PEARSON 1993"),
                 "abiogenesis-stage1-grayscott", {"preset": "spots"}, seed=7,
                 warmup=80 if not test else 30, framefn=frame_sem_gs,
                 crf=crf, preset=preset, fin=False, fout=False, grid=grid, scatter=True), d)
    # 4 — vesicles (painting, keyed)
    d = 9 * f
    add(plate_beat(tmp, 4, d, GEN / "stage3_vesicles.png",
                   ("S T A G E   3   ·   V E S I C L E S", "The First Membranes",
                    "A bilayer closes around the chemistry.", "HELFRICH  1973"),
                   "painting", crf, preset, False, False), d)
    # 5 — selection (SEM)
    d = 10 * f
    add(sim_beat(tmp, 5, d,
                 ("S T A G E   4   ·   S E L E C T I O N", "Chemistry That Competes",
                  "Bounded chemistry begins to copy, and to win.", "EIGEN · SCHUSTER  1977"),
                 "abiogenesis-stage4-selection", {}, seed=4,
                 warmup=30 if not test else 15, framefn=frame_sem_lum(0.82, bump=2.4, shin=16, ks=0.6),
                 crf=crf, preset=preset, fin=False, fout=False, grid=min(grid, 150), steps_per=2), d)
    # 6 — the arc (painting, panorama)
    d = 10 * f
    add(plate_beat(tmp, 6, d, GEN / "pipeline_poster.png",
                   ("T W E L V E   S T A G E S   ·   O N E   A P P A R A T U S", "Chemistry Into Life",
                    "Primordial soup to the last universal common ancestor.", "CELLAUTO · MMXXVI"),
                   "cover", crf, preset, False, False, ticks=False), d)
    # 7 — closing title
    d = 7 * f
    add(title_beat(tmp, 7, d,
                   ("T W E L V E   O B S E R V A T I O N S   ·   O N E   E V E N T", "cellauto",
                    "chemistry remembers how to become.",
                    "G I T H U B . C O M / R I Z Z L E R O C / C E L L A U T O M A T A"),
                   crf, preset, False, True), d)

    total = assemble(clips, durs, args.out, crf, preset)
    size = os.path.getsize(args.out) / 1e6
    print(f"\nHERO FILM -> {args.out}")
    print(f"  duration ~{total:.1f}s   size {size:.1f} MB   {W}x{H}@{FPS}   beats={len(clips)}")


if __name__ == "__main__":
    main()
