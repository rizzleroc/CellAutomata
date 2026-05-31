"""Shared helpers for building vertical (1080x1920) cellauto reels.

Text is rendered with Pillow (the bundled imageio-ffmpeg has no drawtext);
ffmpeg handles compositing, Ken-Burns motion, xfade crossfades, H.264/AAC.
"""
from __future__ import annotations
import os
import subprocess
import sys
import tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
W, H = 1080, 1920
FPS = 30
T = 0.5  # crossfade seconds
ACCENT = (94, 214, 184)

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_M = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


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
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    scrim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(scrim)
    top = 1380
    for y in range(top, H):
        a = int(205 * (y - top) / (H - top))
        sd.line([(0, y), (W, y)], fill=(6, 10, 14, a))
    img = Image.alpha_composite(img, scrim)
    d = ImageDraw.Draw(img)
    tf = font(FONT_B, 64)
    tlines = wrap(d, title, tf, W - 160)
    sub_h = 0
    slines = []
    if subtitle:
        sf = font(FONT, 40)
        slines = wrap(d, subtitle, sf, W - 200)
        sub_h = len(slines) * (sf.size + 8)
    block_h = len(tlines) * (tf.size + 12) + sub_h + 40
    y = H - 230 - block_h
    d.rectangle([(W / 2 - 60, y - 28), (W / 2 + 60, y - 18)], fill=ACCENT + (255,))
    y = draw_centered(d, tlines, tf, y, (255, 255, 255, 255))
    if subtitle:
        y += 14
        draw_centered(d, slines, font(FONT, 40), y, (200, 224, 218, 235))
    img.save(path)


def cover_blur(plate, darken=160, blur=24):
    im = Image.open(plate).convert("RGB")
    scale = max(W / im.width, H / im.height)
    im = im.resize((int(im.width * scale) + 1, int(im.height * scale) + 1))
    x = (im.width - W) // 2
    y = (im.height - H) // 2
    im = im.crop((x, y, x + W, y + H)).filter(ImageFilter.GaussianBlur(blur))
    ov = Image.new("RGBA", (W, H), (4, 8, 12, darken))
    return Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")


def card_png(path, plate, big, smalls=None, mono=None, logo=None, big_size=104):
    bg = cover_blur(plate, darken=172, blur=26).convert("RGBA")
    d = ImageDraw.Draw(bg)
    cy = H // 2 - 200
    if logo and os.path.exists(logo):
        lg = Image.open(logo).convert("RGBA").resize((300, 300))
        bg.alpha_composite(lg, ((W - 300) // 2, cy - 330))
    bf = font(FONT_B, big_size)
    blines = wrap(d, big, bf, W - 130)
    d.rectangle([(W / 2 - 70, cy - 26), (W / 2 + 70, cy - 14)], fill=ACCENT + (255,))
    y = draw_centered(d, blines, bf, cy, (255, 255, 255, 255))
    y += 28
    if smalls:
        sf = font(FONT, 46)
        for s in smalls:
            y = draw_centered(d, [s], sf, y, (210, 230, 224, 240), line_gap=16)
            y += 6
    if mono:
        y += 26
        mf = font(FONT_M, 38)
        w = d.textlength(mono, font=mf)
        d.rounded_rectangle([(W / 2 - w / 2 - 34, y - 16), (W / 2 + w / 2 + 34, y + mf.size + 18)],
                            radius=18, fill=(10, 16, 20, 225), outline=ACCENT + (255,), width=3)
        d.text(((W - w) / 2, y), mono, font=mf, fill=ACCENT + (255,))
    bg.convert("RGB").save(path)


def run(args):
    p = subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", *args],
                       capture_output=True, text=True)
    if p.returncode != 0:
        sys.stderr.write("FFMPEG FAIL:\n" + " ".join(str(a) for a in args)[:600]
                         + "\n" + p.stderr[-1200:] + "\n")
        raise RuntimeError("ffmpeg failed")


def _scene_clip(scene, idx, tmp, fade_in, fade_out, preset, crf, threads):
    dur = scene["dur"]
    clip = os.path.join(tmp, f"clip_{idx:02d}.mp4")
    fade = ""
    if fade_in:
        fade += ",fade=t=in:st=0:d=0.5"
    if fade_out:
        fade += f",fade=t=out:st={dur-0.6:.2f}:d=0.6"
    enc = ["-r", str(FPS), "-c:v", "libx264", "-crf", str(crf), "-preset", preset,
           "-threads", str(threads), "-pix_fmt", "yuv420p", clip]

    if scene["kind"] == "card":
        cp = os.path.join(tmp, f"card_{idx:02d}.png")
        card_png(cp, scene["plate"], scene["big"], scene.get("smalls"),
                 scene.get("mono"), scene.get("logo"), scene.get("big_size", 104))
        vf = (f"fps={FPS},scale={W}:{H},setsar=1,"
              f"zoompan=z='min(1.0+0.00035*on,1.07)':x='iw/2-(iw/zoom/2)':"
              f"y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS}{fade},format=yuv420p")
        run(["-loop", "1", "-t", str(dur), "-i", cp,
             "-filter_complex", f"[0:v]{vf}[v]", "-map", "[v]", *enc])

    elif scene["kind"] == "image":
        cap = os.path.join(tmp, f"cap_{idx:02d}.png")
        caption_png(cap, scene["title"], scene.get("sub"))
        fc = (f"[0:v]fps={FPS},split=2[a][b];"
              f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
              f"boxblur=22:2,eq=brightness=-0.20:saturation=1.05[bg];"
              f"[b]scale=960:1420:force_original_aspect_ratio=decrease[fg];"
              f"[bg][fg]overlay=(W-w)/2:(H-h)/2-70[c];"
              f"[c]zoompan=z='min(1.0+0.0005*on,1.09)':x='iw/2-(iw/zoom/2)':"
              f"y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS}[z];"
              f"[z][1:v]overlay=0:0{fade},format=yuv420p[v]")
        run(["-loop", "1", "-t", str(dur), "-i", scene["src"],
             "-loop", "1", "-t", str(dur), "-i", cap,
             "-filter_complex", fc, "-map", "[v]", *enc])

    else:  # video
        cap = os.path.join(tmp, f"cap_{idx:02d}.png")
        caption_png(cap, scene["title"], scene.get("sub"))
        fc = (f"[0:v]fps={FPS},split=2[a][b];"
              f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
              f"boxblur=24:2,eq=brightness=-0.22:saturation=1.05[bg];"
              f"[b]scale=980:980:force_original_aspect_ratio=decrease[fg];"
              f"[bg][fg]overlay=(W-w)/2:(H-h)/2-70[c];"
              f"[c][1:v]overlay=0:0{fade},format=yuv420p[v]")
        run(["-ss", str(scene.get("ss", 0.5)), "-t", str(dur), "-i", scene["src"],
             "-loop", "1", "-t", str(dur), "-i", cap,
             "-filter_complex", fc, "-map", "[v]", *enc])
    return clip, dur


def build_reel(scenes, out_path, preset="veryfast", crf=25, threads=2, audio=True):
    tmp = tempfile.mkdtemp(prefix="reel_")
    clips, durs = [], []
    n = len(scenes)
    for i, sc in enumerate(scenes):
        clip, dur = _scene_clip(sc, i, tmp, i == 0, i == n - 1, preset, crf, threads)
        clips.append(clip)
        durs.append(dur)
    # crossfade chain
    inputs = []
    for c in clips:
        inputs += ["-i", c]
    parts, prev, cum = [], "[0:v]", durs[0]
    for i in range(1, n):
        off = cum - T
        lab = f"[x{i}]"
        parts.append(f"{prev}[{i}:v]xfade=transition=fade:duration={T}:offset={off:.3f}{lab}")
        prev = lab
        cum += durs[i] - T
    total = cum
    silent = os.path.join(tmp, "silent.mp4")
    run([*inputs, "-filter_complex", ";".join(parts), "-map", prev,
         "-r", str(FPS), "-c:v", "libx264", "-crf", str(crf), "-preset", preset,
         "-threads", str(threads), "-pix_fmt", "yuv420p", "-movflags", "+faststart", silent])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    if not audio:
        os.replace(silent, out_path)
        return out_path, total
    af = (f"[1:a][2:a]amix=inputs=2:duration=longest,volume=0.11,lowpass=f=520,"
          f"afade=t=in:st=0:d=1.4,afade=t=out:st={total-1.6:.2f}:d=1.6[a]")
    run(["-i", silent,
         "-f", "lavfi", "-t", str(total), "-i", "sine=frequency=98:sample_rate=44100",
         "-f", "lavfi", "-t", str(total), "-i", "sine=frequency=146.83:sample_rate=44100",
         "-filter_complex", af, "-map", "0:v", "-map", "[a]",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest",
         "-movflags", "+faststart", out_path])
    return out_path, total
