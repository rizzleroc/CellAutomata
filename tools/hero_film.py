"""hero_film.py — "Catalytic Silence", the cellauto flagship hero film.

A landscape (1920x1080) cinematic cut for the website overture + social.
It intercuts a LIVE, on-palette Gray-Scott hero beat (the signature
"four-parameter PDE that divides") with the photoreal specimen plates,
wrapped in the Catalytic Silence museum aesthetic: obsidian ground, a
teal -> bone -> magenta specimen ramp, a hairline lower-third, corner
registration ticks, and a low ambient drone.

Design notes
------------
- The bundled imageio-ffmpeg has NO drawtext (no freetype build) -> ALL
  text is rendered with Pillow and overlaid as full-frame RGBA PNGs.
- The live sim is recoloured away from viridis into the brand ramp and
  given an SEM-grade pass (bloom + vignette + film grain).
- Narration is authored in NARRATION below and timed to the beats; this
  container cannot reach huggingface to run VibeVoice, so the film ships
  with the ambient bed and the script is wired for one-step muxing via
  marketing/social/voiceover/add_voiceover.py once a WAV exists.

Usage
-----
    python tools/hero_film.py --test      # fast, low-res pipeline check
    python tools/hero_film.py             # full render -> media/hero/
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from cellauto.engine import Engine                       # noqa: E402
from cellauto.rules import REGISTRY                       # noqa: E402
import imageio_ffmpeg                                     # noqa: E402

FF = imageio_ffmpeg.get_ffmpeg_exe()

# ── Canvas + Catalytic Silence palette ──────────────────────────────────────
W, H = 1920, 1080
FPS = 30
OBSIDIAN = (8, 11, 18)
BONE = (230, 224, 208)
BONE_DIM = (150, 150, 142)
TEAL = (57, 212, 200)
MAGENTA = (212, 57, 164)

GEN = REPO / "docs" / "generated"

# Fonts available on this box (closest Catalytic Silence voices).
F_SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"          # title
F_ITAL = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"  # caption
F_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"        # apparatus


def font(path, size):
    return ImageFont.truetype(path, size)


# ── Narration (authored; timed to beats; for VibeVoice mux later) ────────────
NARRATION = (
    "What you're watching is cell division, with no biology at all. "
    "Just four numbers in a reaction-diffusion equation, splitting like living "
    "protocells. Before life, there was soup, seeded from the real yields of the "
    "1953 Miller-Urey experiment. Then the first membranes close around it. "
    "Chemistry begins to compete, and to copy. Twelve stages, one apparatus, "
    "from primordial soup to the last universal common ancestor. "
    "This is cellauto, watching chemistry remember how to become."
)


# ── Brand colormap: obsidian -> teal -> bone -> magenta ─────────────────────
def build_lut() -> np.ndarray:
    stops = [
        (0.00, (8, 11, 18)),
        (0.16, (12, 28, 36)),
        (0.38, (24, 120, 118)),
        (0.60, (57, 212, 200)),
        (0.80, (150, 224, 210)),
        (0.92, (230, 224, 208)),
        (1.00, (224, 90, 170)),
    ]
    lut = np.zeros((256, 3), np.float32)
    for i in range(256):
        t = i / 255.0
        for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
            if t0 <= t <= t1:
                f = (t - t0) / max(t1 - t0, 1e-9)
                lut[i] = np.array(c0) * (1 - f) + np.array(c1) * f
                break
    return lut


LUT = build_lut()


def colormap(field: np.ndarray, scale: float, gamma: float = 0.85) -> np.ndarray:
    t = np.clip(field / scale, 0.0, 1.0) ** gamma
    idx = np.clip((t * 255).astype(np.int32), 0, 255)
    return LUT[idx].astype(np.uint8)


# ── SEM-grade post: bloom + vignette + grain ────────────────────────────────
def sem_post(rgb: np.ndarray, grain: float = 6.0, bloom: float = 0.55) -> Image.Image:
    img = Image.fromarray(rgb, "RGB")
    # bloom: blur the bright areas and screen them back
    lum = np.asarray(img.convert("L"), np.float32) / 255.0
    mask = np.clip((lum - 0.55) / 0.45, 0, 1)[:, :, None]
    glow = Image.fromarray((rgb * mask).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(7))
    base = np.asarray(img, np.float32)
    gl = np.asarray(glow, np.float32)
    screen = 255.0 - (255.0 - base) * (255.0 - gl * bloom) / 255.0
    out = screen
    # vignette
    h, w = out.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    out *= np.clip(1.0 - 0.42 * (r ** 2.4), 0.25, 1.0)[:, :, None]
    # grain
    if grain:
        out += np.random.normal(0, grain, out.shape)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")


# ── Specimen square centered on an obsidian frame ───────────────────────────
SPEC = 850                                    # specimen square side (vitrine)
SX, SY = (W - SPEC) // 2, 30                   # centered, top margin -> clean caption band


def on_obsidian(specimen: Image.Image) -> Image.Image:
    canvas = Image.new("RGB", (W, H), OBSIDIAN)
    canvas.paste(specimen.resize((SPEC, SPEC), Image.LANCZOS), (SX, SY))
    return canvas


def frame_plate(plate, mode: str) -> Image.Image:
    """Flatten a (possibly transparent) plate onto obsidian, framed for the beat.
    'cover' fills the frame; 'specimen' fits the cutout into the vitrine box."""
    im = Image.open(plate).convert("RGBA")
    canvas = Image.new("RGB", (W, H), OBSIDIAN)
    if mode == "cover":
        s = max(W / im.width, H / im.height)
        im2 = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
        x = (im2.width - W) // 2
        y = (im2.height - H) // 2
        im2 = im2.crop((x, y, x + W, y + H))
        base = canvas.convert("RGBA")
        base.alpha_composite(im2)
        arr = np.asarray(base.convert("RGB"), np.float32)
        # strong edge vignette -> blends any light "paper" border into obsidian
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        vig = np.clip(1.0 - 0.92 * np.clip((r - 0.50) / 0.50, 0, 1) ** 1.6, 0.0, 1.0)
        arr = arr * vig[:, :, None] + np.array(OBSIDIAN, np.float32) * (1 - vig)[:, :, None]
        canvas = Image.blend(Image.fromarray(arr.astype(np.uint8), "RGB"),
                             Image.new("RGB", (W, H), OBSIDIAN), 0.08)
    else:  # specimen
        s = min(SPEC / im.width, SPEC / im.height)
        im2 = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
        base = canvas.convert("RGBA")
        base.alpha_composite(im2, (SX + (SPEC - im2.width) // 2, SY + (SPEC - im2.height) // 2))
        canvas = base.convert("RGB")
    return canvas


# ── Letter-spaced text helpers ──────────────────────────────────────────────
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


# ── Caption overlay (corner ticks + hairline lower-third) ───────────────────
def caption_overlay(path, eyebrow, title, descriptor, citation, ticks=True):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # scrim for legibility over footage
    top = 760
    for y in range(top, H):
        a = int(150 * (y - top) / (H - top))
        d.line([(0, y), (W, y)], fill=(6, 9, 14, a))
    if ticks:
        col, gap, leg, sw = TEAL + (150,), 26, 56, 2
        for cx, cy, dx, dy in [(SX, SY, 1, 1), (SX + SPEC, SY, -1, 1),
                               (SX, SY + SPEC, 1, -1), (SX + SPEC, SY + SPEC, -1, -1)]:
            d.line([(cx - dx * gap, cy - dy * gap),
                    (cx - dx * gap + dx * leg, cy - dy * gap)], fill=col, width=sw)
            d.line([(cx - dx * gap, cy - dy * gap),
                    (cx - dx * gap, cy - dy * gap + dy * leg)], fill=col, width=sw)
    # lower-third block
    f_eye = font(F_MONO, 22)
    f_ttl = font(F_SERIF, 60)
    f_des = font(F_ITAL, 34)
    f_cit = font(F_MONO, 22)
    bx, by = 150, 884
    text_tracked(d, (bx, by), eyebrow, f_eye, BONE_DIM + (255,), tracking=6)
    d.line([(bx, by + 36), (bx + 360, by + 36)], fill=TEAL + (160,), width=1)
    text_tracked(d, (bx, by + 52), title, f_ttl, BONE + (255,), tracking=2)
    d.text((bx + 2, by + 128), descriptor, font=f_des, fill=BONE + (230,))
    text_tracked(d, (W - 150, by + 8), citation, f_cit, BONE_DIM + (255,),
                 tracking=4, anchor="r")
    img.save(path)


# ── Title cards ─────────────────────────────────────────────────────────────
def title_card(path, eyebrow, big, sub, footer=None):
    img = Image.new("RGB", (W, H), OBSIDIAN)
    d = ImageDraw.Draw(img, "RGBA")
    # faint canvas registration marks
    m, leg = 70, 34
    for cx, cy, dx, dy in [(m, m, 1, 1), (W - m, m, -1, 1),
                           (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        d.line([(cx, cy), (cx + dx * leg, cy)], fill=BONE_DIM + (120,), width=1)
        d.line([(cx, cy), (cx, cy + dy * leg)], fill=BONE_DIM + (120,), width=1)
    text_tracked(d, (W / 2, 360), eyebrow, font(F_MONO, 24), BONE_DIM, tracking=8, anchor="c")
    text_tracked(d, (W / 2, 430), big, font(F_SERIF, 150), BONE, tracking=10, anchor="c")
    d.line([(W / 2 - 240, 620), (W / 2 + 240, 620)], fill=TEAL + (170,), width=1)
    f_sub = font(F_ITAL, 40)
    sw = d.textlength(sub, font=f_sub)
    d.text((W / 2 - sw / 2, 660), sub, font=f_sub, fill=BONE)
    if footer:
        text_tracked(d, (W / 2, H - 130), footer, font(F_MONO, 24), BONE_DIM, tracking=6, anchor="c")
    img.save(path)


# ── ffmpeg helpers ──────────────────────────────────────────────────────────
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
    return ["-r", str(FPS), "-c:v", "libx264", "-crf", str(crf),
            "-preset", preset, "-pix_fmt", "yuv420p", clip]


# ── Beats ───────────────────────────────────────────────────────────────────
def scatter_seed(eng, grid):
    """Fill a Gray-Scott field with dividing spots (a lone central seed barely
    covers the frame in a sane step budget — see CONTINUE.md)."""
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


def frame_gs(eng):
    """Hero Gray-Scott: raw v field through the brand ramp (restrained magenta)."""
    v = np.asarray(eng.state.v, np.float32)
    return sem_post(colormap(v, 0.40, gamma=0.8), grain=5.0)


def frame_lum(scale=0.80, gamma=0.95):
    """Any rule via the universal render_rgb path -> luminance -> brand ramp."""
    def fn(eng):
        rgb = np.asarray(eng.rule.render_rgb(eng.state), np.float32)
        lum = (0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]) / 255.0
        return sem_post(colormap(lum, scale, gamma), grain=5.0)
    return fn


def sim_beat(tmp, idx, dur, cap, rule_name, cfg, seed, warmup, framefn,
             crf, preset, fin, fout, grid=280, steps_per=6, scatter=False):
    """Render a live sim beat: step the rule, recolour each frame through the
    brand ramp + SEM post, frame the specimen on obsidian, overlay the caption."""
    rule = REGISTRY[rule_name](**cfg)
    eng = Engine(width=grid, height=grid, rule=rule, seed=seed)
    if scatter:
        scatter_seed(eng, grid)
    for _ in range(warmup):
        eng.step()
    fdir = Path(tmp) / f"sim_{idx:02d}"
    fdir.mkdir(parents=True, exist_ok=True)
    for fi in range(int(dur * FPS)):
        for _ in range(steps_per):
            eng.step()
        on_obsidian(framefn(eng)).save(fdir / f"f_{fi:05d}.png")
    capp = Path(tmp) / f"cap_{idx:02d}.png"
    caption_overlay(capp, *cap)
    clip = str(Path(tmp) / f"clip_{idx:02d}.mp4")
    fc = (f"[0:v]fps={FPS},format=rgba[a];[a][1:v]overlay=0:0"
          f"{fade_str(dur, fin, fout)},format=yuv420p[v]")
    run(["-framerate", str(FPS), "-i", str(fdir / "f_%05d.png"),
         "-loop", "1", "-t", str(dur), "-i", str(capp),
         "-filter_complex", fc, "-map", "[v]", "-t", str(dur),
         *enc(clip, crf, preset)])
    return clip


def plate_beat(tmp, idx, dur, plate, cap, mode, crf, preset, fin, fout, ticks=True):
    """mode='cover' (fill + slow pan) or 'specimen' (cutout fit + slow zoom).
    The plate is flattened onto obsidian in PIL first so transparency always
    resolves to the brand ground (ffmpeg alpha-over-color was unreliable)."""
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
          f"[z]format=rgba[zz];[zz][1:v]overlay=0:0"
          f"{fade_str(dur, fin, fout)},format=yuv420p[v]")
    run(["-loop", "1", "-t", str(dur), "-i", str(basep),
         "-loop", "1", "-t", str(dur), "-i", str(capp),
         "-filter_complex", fc, "-map", "[v]", "-t", str(dur),
         *enc(clip, crf, preset)])
    return clip


def title_beat(tmp, idx, dur, card_args, crf, preset, fin, fout):
    cardp = Path(tmp) / f"title_{idx:02d}.png"
    title_card(cardp, *card_args)
    clip = str(Path(tmp) / f"clip_{idx:02d}.mp4")
    fc = (f"[0:v]fps={FPS},scale={W}:{H},"
          f"zoompan=z='min(1.0+0.0004*on,1.05)':d={int(dur*FPS)}:s={W}x{H}:fps={FPS}:"
          f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
          f"{fade_str(dur, fin, fout)},format=yuv420p[v]")
    run(["-loop", "1", "-t", str(dur), "-i", str(cardp),
         "-filter_complex", fc, "-map", "[v]", "-t", str(dur),
         *enc(clip, crf, preset)])
    return clip


# ── Assemble: xfade chain + ambient drone bed ───────────────────────────────
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
    # ambient drone: D1 + A1 + D2 sines, low-passed, slow tremolo
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
    grid = 120 if test else 280
    f = 0.45 if test else 1.0      # duration scale for the test pass

    tmp = tempfile.mkdtemp(prefix="herobeats_")
    clips, durs = [], []

    def add(clip, d):
        clips.append(clip)
        durs.append(d)

    n = 7  # beats
    # 0 — opening title
    d0 = 6 * f
    add(title_beat(tmp, 0, d0,
                   ("P L A T E   I   ·   C A T A L Y T I C   S I L E N C E   ·   M M X X V I",
                    "cellauto", "an origin-of-life instrument"),
                   crf, preset, True, False), d0)
    # 1 — primordial soup (cover plate)
    d1 = 10 * f
    add(plate_beat(tmp, 1, d1, GEN / "stage0_soup.png",
                   ("S T A G E   0   ·   P R I M O R D I A L   S O U P", "Primordial Soup",
                    "Monomers condense in a reducing ocean.", "MILLER · UREY  1953"),
                   "cover", crf, preset, False, False, ticks=False), d1)
    # 2 — the first division (LIVE Gray-Scott hero)
    d2 = 16 * f
    add(sim_beat(tmp, 2, d2,
                 ("S T A G E   1   ·   R E A C T I O N – D I F F U S I O N", "The First Division",
                  "Four numbers, splitting like protocells.", "TURING 1952 · PEARSON 1993"),
                 "abiogenesis-stage1-grayscott", {"preset": "spots"}, seed=7,
                 warmup=80 if not test else 30, framefn=frame_gs,
                 crf=crf, preset=preset, fin=False, fout=False, grid=grid, scatter=True), d2)
    # 3 — vesicles (LIVE, brand ramp)
    d3 = 10 * f
    add(sim_beat(tmp, 3, d3,
                 ("S T A G E   3   ·   V E S I C L E S", "The First Membranes",
                  "A bilayer closes around the chemistry.", "HELFRICH  1973"),
                 "abiogenesis-stage3-vesicles", {}, seed=9,
                 warmup=60 if not test else 20, framefn=frame_lum(0.78, 0.92),
                 crf=crf, preset=preset, fin=False, fout=False, grid=grid, steps_per=4), d3)
    # 4 — protocell selection (LIVE, brand ramp)
    d4 = 10 * f
    add(sim_beat(tmp, 4, d4,
                 ("S T A G E   4   ·   S E L E C T I O N", "Chemistry That Competes",
                  "Bounded chemistry begins to copy, and to win.", "EIGEN · SCHUSTER  1977"),
                 "abiogenesis-stage4-selection", {}, seed=4,
                 warmup=40 if not test else 15, framefn=frame_lum(0.80, 0.95),
                 crf=crf, preset=preset, fin=False, fout=False, grid=grid, steps_per=4), d4)
    # 5 — the whole arc (pipeline panorama, cover pan)
    d5 = 11 * f
    add(plate_beat(tmp, 5, d5, GEN / "pipeline_poster.png",
                   ("T W E L V E   S T A G E S   ·   O N E   A P P A R A T U S", "Chemistry Into Life",
                    "Primordial soup to the last universal common ancestor.", "CELLAUTO · MMXXVI"),
                   "cover", crf, preset, False, False, ticks=False), d5)
    # 6 — closing title
    d6 = 7 * f
    add(title_beat(tmp, 6, d6,
                   ("T W E L V E   O B S E R V A T I O N S   ·   O N E   E V E N T", "cellauto",
                    "chemistry remembers how to become.",
                    "G I T H U B . C O M / R I Z Z L E R O C / C E L L A U T O M A T A"),
                   crf, preset, False, True), d6)

    assert len(clips) == n
    total = assemble(clips, durs, args.out, crf, preset)
    size = os.path.getsize(args.out) / 1e6
    print(f"\nHERO FILM -> {args.out}")
    print(f"  duration ~{total:.1f}s   size {size:.1f} MB   {W}x{H}@{FPS}")
    print(f"  narration script ({len(NARRATION.split())} words) wired for VibeVoice mux.")


if __name__ == "__main__":
    main()
