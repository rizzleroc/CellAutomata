#!/usr/bin/env python3
"""Build a vertical (1080x1920) "progress" sizzle video for cellauto.

Text is rendered with Pillow (the bundled ffmpeg has no drawtext/freetype);
ffmpeg handles compositing, Ken-Burns motion, crossfades and H.264 encoding.
Real simulation footage comes from `cellauto export` GIFs in exports/.
"""
from __future__ import annotations
import os
import subprocess
import sys
import tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FF = imageio_ffmpeg.get_ffmpeg_exe()
W, H = 1080, 1920
FPS = 30
T = 0.5  # crossfade seconds
TMP = tempfile.mkdtemp(prefix="cavid_")
OUT_DIR = os.path.join(ROOT, "marketing", "social", "assets")
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "cellauto_progress.mp4")

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_M = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
ACCENT = (94, 214, 184)   # viridis-ish teal


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(draw, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_centered(draw, lines, fnt, y, fill, line_gap=12, shadow=True):
    for ln in lines:
        w = draw.textlength(ln, font=fnt)
        x = (W - w) / 2
        if shadow:
            draw.text((x + 3, y + 3), ln, font=fnt, fill=(0, 0, 0, 180))
        draw.text((x, y), ln, font=fnt, fill=fill)
        y += fnt.size + line_gap
    return y


def caption_png(path, title, subtitle=None):
    """Transparent 1080x1920 with a bottom scrim + caption."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # soft scrim: vertical gradient black, alpha ramps from 0 -> 190
    scrim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(scrim)
    top = 1380
    for y in range(top, H):
        a = int(200 * (y - top) / (H - top))
        sd.line([(0, y), (W, y)], fill=(6, 10, 14, a))
    img = Image.alpha_composite(img, scrim)
    d = ImageDraw.Draw(img)
    tf = font(FONT_B, 64)
    tlines = wrap(d, title, tf, W - 160)
    # accent rule
    sub_h = 0
    if subtitle:
        sf = font(FONT, 40)
        slines = wrap(d, subtitle, sf, W - 200)
        sub_h = len(slines) * (sf.size + 8)
    block_h = len(tlines) * (tf.size + 12) + sub_h + 40
    y = H - 220 - block_h
    d.rectangle([(W / 2 - 60, y - 28), (W / 2 + 60, y - 18)], fill=ACCENT + (255,))
    y = draw_centered(d, tlines, tf, y, (255, 255, 255, 255))
    if subtitle:
        y += 14
        draw_centered(d, slines, sf, y, (200, 224, 218, 235))
    img.save(path)


def cover_blur(plate, darken=150, blur=22):
    im = Image.open(plate).convert("RGB")
    # cover-resize to WxH
    scale = max(W / im.width, H / im.height)
    im = im.resize((int(im.width * scale) + 1, int(im.height * scale) + 1))
    x = (im.width - W) // 2
    y = (im.height - H) // 2
    im = im.crop((x, y, x + W, y + H)).filter(ImageFilter.GaussianBlur(blur))
    ov = Image.new("RGBA", (W, H), (4, 8, 12, darken))
    return Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")


def card_png(path, plate, big, smalls=None, mono=None, logo=None, big_size=104):
    bg = cover_blur(plate, darken=170, blur=26).convert("RGBA")
    d = ImageDraw.Draw(bg)
    cy = H // 2 - 220
    if logo and os.path.exists(logo):
        lg = Image.open(logo).convert("RGBA").resize((300, 300))
        bg.alpha_composite(lg, ((W - 300) // 2, cy - 320))
    bf = font(FONT_B, big_size)
    blines = wrap(d, big, bf, W - 140)
    # accent rule above
    d.rectangle([(W / 2 - 70, cy - 26), (W / 2 + 70, cy - 14)], fill=ACCENT + (255,))
    y = draw_centered(d, blines, bf, cy, (255, 255, 255, 255))
    y += 28
    if smalls:
        sf = font(FONT, 46)
        for s in smalls:
            y = draw_centered(d, [s], sf, y, (210, 230, 224, 240), line_gap=18)
            y += 8
    if mono:
        y += 24
        mf = font(FONT_M, 40)
        w = d.textlength(mono, font=mf)
        d.rounded_rectangle([(W / 2 - w / 2 - 34, y - 16), (W / 2 + w / 2 + 34, y + mf.size + 18)],
                            radius=18, fill=(10, 16, 20, 220), outline=ACCENT + (255,), width=3)
        d.text(((W - w) / 2, y), mono, font=mf, fill=ACCENT + (255,))
    bg.convert("RGB").save(path)


def run(args):
    p = subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", *args],
                       capture_output=True, text=True)
    if p.returncode != 0:
        sys.stderr.write("FFMPEG FAILED:\n" + " ".join(args)[:800] + "\n" + p.stderr[-1500:] + "\n")
        raise SystemExit(1)


# ---- scene definitions -------------------------------------------------
G = lambda n: os.path.join(ROOT, "exports", n)
D = lambda n: os.path.join(ROOT, "docs", n)

scenes = [
    dict(kind="card", dur=3.2, plate=D("genesis.png"), big="cellauto",
         smalls=["the origin of life, simulated"], logo=D("icon.png"), big_size=128),
    dict(kind="image", dur=3.6, src=D("hero.png"),
         title="A four-parameter equation", sub="that divides like a living cell"),
    dict(kind="video", dur=4.2, src=G("grayscott_mitosis.gif"), ss=1.0,
         title="Stage 1 · Gray–Scott", sub="real reaction–diffusion, running live"),
    dict(kind="image", dur=3.6, src=D("pipeline.png"),
         title="12 coupled stages", sub="primordial soup → LUCA"),
    dict(kind="video", dur=3.2, src=G("vent.gif"), ss=0.6,
         title="Hydrothermal vent", sub="live PMF & ΔG · Lane–Martin"),
    dict(kind="video", dur=3.2, src=G("homochirality.gif"), ss=0.6,
         title="Homochirality", sub="Frank 1953 symmetry breaking"),
    dict(kind="video", dur=3.2, src=G("rna_world.gif"), ss=0.6,
         title="RNA world", sub="Eigen error catastrophe"),
    dict(kind="video", dur=3.2, src=G("coacervate.gif"), ss=0.6,
         title="Coacervates", sub="Cahn–Hilliard phase separation"),
    dict(kind="image", dur=3.8, src=D("genesis.png"),
         title="Every panel is real simulator output", sub=None),
    dict(kind="card", dur=3.4, plate=D("prima-materia.png"), big="v3.6.0",
         smalls=["12-stage coupled pipeline", "141 tests passing · MIT"], big_size=120),
    dict(kind="card", dur=3.4, plate=D("hero.png"), big="Try it yourself",
         mono="github.com/rizzleroc/CellAutomata", smalls=["open source · Python"]),
]

clip_paths, durs = [], []
for i, s in enumerate(scenes):
    clip = os.path.join(TMP, f"clip_{i:02d}.mp4")
    dur = s["dur"]
    fin = (i == 0)
    fout = (i == len(scenes) - 1)
    fade = ""
    if fin:
        fade += f",fade=t=in:st=0:d=0.5"
    if fout:
        fade += f",fade=t=out:st={dur-0.6:.2f}:d=0.6"

    if s["kind"] == "card":
        cp = os.path.join(TMP, f"card_{i:02d}.png")
        card_png(cp, s["plate"], s["big"], s.get("smalls"), s.get("mono"),
                 s.get("logo"), s.get("big_size", 104))
        vf = (f"fps={FPS},scale={W}:{H},setsar=1,"
              f"zoompan=z='min(1.0+0.00035*on,1.07)':x='iw/2-(iw/zoom/2)':"
              f"y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS}{fade},format=yuv420p")
        run(["-loop", "1", "-t", f"{dur}", "-i", cp,
             "-filter_complex", f"[0:v]{vf}[v]", "-map", "[v]",
             "-r", f"{FPS}", "-c:v", "libx264", "-crf", "20", "-preset", "medium",
             "-pix_fmt", "yuv420p", clip])

    elif s["kind"] == "image":
        cap = os.path.join(TMP, f"cap_{i:02d}.png")
        caption_png(cap, s["title"], s.get("sub"))
        fc = (
            f"[0:v]fps={FPS},split=2[a][b];"
            f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"boxblur=22:2,eq=brightness=-0.20:saturation=1.05[bg];"
            f"[b]scale=960:1420:force_original_aspect_ratio=decrease[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2-70[c];"
            f"[c]zoompan=z='min(1.0+0.0005*on,1.09)':x='iw/2-(iw/zoom/2)':"
            f"y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS}[z];"
            f"[z][1:v]overlay=0:0{fade},format=yuv420p[v]"
        )
        run(["-loop", "1", "-t", f"{dur}", "-i", s["src"],
             "-loop", "1", "-t", f"{dur}", "-i", cap,
             "-filter_complex", fc, "-map", "[v]",
             "-r", f"{FPS}", "-c:v", "libx264", "-crf", "20", "-preset", "medium",
             "-pix_fmt", "yuv420p", clip])

    else:  # video
        cap = os.path.join(TMP, f"cap_{i:02d}.png")
        caption_png(cap, s["title"], s.get("sub"))
        fc = (
            f"[0:v]fps={FPS},split=2[a][b];"
            f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"boxblur=24:2,eq=brightness=-0.22:saturation=1.05[bg];"
            f"[b]scale=980:980:force_original_aspect_ratio=decrease[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2-70[c];"
            f"[c][1:v]overlay=0:0{fade},format=yuv420p[v]"
        )
        run(["-ss", f"{s['ss']}", "-t", f"{dur}", "-i", s["src"],
             "-loop", "1", "-t", f"{dur}", "-i", cap,
             "-filter_complex", fc, "-map", "[v]",
             "-r", f"{FPS}", "-c:v", "libx264", "-crf", "20", "-preset", "medium",
             "-pix_fmt", "yuv420p", clip])

    clip_paths.append(clip)
    durs.append(dur)
    print(f"  scene {i:02d} [{s['kind']:5}] {dur:.1f}s -> ok")

# ---- crossfade chain ---------------------------------------------------
inputs = []
for c in clip_paths:
    inputs += ["-i", c]
parts, prev, cum = [], "[0:v]", durs[0]
for i in range(1, len(clip_paths)):
    off = cum - T
    lab = f"[x{i}]"
    parts.append(f"{prev}[{i}:v]xfade=transition=fade:duration={T}:offset={off:.3f}{lab}")
    prev = lab
    cum += durs[i] - T
total = cum
vfilter = ";".join(parts)
silent = os.path.join(TMP, "silent.mp4")
run([*inputs, "-filter_complex", vfilter, "-map", prev,
     "-r", f"{FPS}", "-c:v", "libx264", "-crf", "19", "-preset", "medium",
     "-pix_fmt", "yuv420p", "-movflags", "+faststart", silent])
print(f"  montage assembled: {total:.1f}s")

# ---- ambient audio bed -------------------------------------------------
afilter = (
    f"[1:a][2:a]amix=inputs=2:duration=longest,volume=0.11,lowpass=f=520,"
    f"afade=t=in:st=0:d=1.6,afade=t=out:st={total-1.8:.2f}:d=1.8[a]"
)
run(["-i", silent,
     "-f", "lavfi", "-t", f"{total}", "-i", "sine=frequency=98:sample_rate=44100",
     "-f", "lavfi", "-t", f"{total}", "-i", "sine=frequency=146.83:sample_rate=44100",
     "-filter_complex", afilter, "-map", "0:v", "-map", "[a]",
     "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest",
     "-movflags", "+faststart", OUT])

print(f"DONE -> {OUT}")
