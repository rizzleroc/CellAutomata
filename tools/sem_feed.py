"""LIVE SEM FEED — the origin of life, run backward.

Animates the repo's real SEM-style simulation stills (docs/generated/stage*.png)
into a single vertical 9:16 "instrument feed" that plays the 12-stage abiogenesis
pipeline in REVERSE — LUCA dissolving back through the genetic code, protocells,
vesicles, autocatalytic sets, Gray-Scott reaction-diffusion, down to the formless
primordial soup. Each stage is held with a slow microscope push-in and a reticle /
scale-bar / "LIVE SEM FEED" badge overlay, then erodes into the previous stage via
a reaction-diffusion dissolve. A descending drone underscores the un-making.

  python3 tools/sem_feed.py            # render media/sem/live_sem_feed_reverse.mp4
"""
from __future__ import annotations
import math, os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
SRC = "docs/generated"
OUT = "media/sem"
W, H = 1080, 1920
FPS = 30
BG = (10, 13, 20)
TEAL = (57, 212, 200)
CREAM = (231, 224, 205)
DIM = (122, 132, 148)
WIN = (20, 360, 1040, 585)        # x, y, w, h  (16:9 instrument window)
HOLD_S, DISS_S = 4.2, 1.4         # per-stage hold + dissolve-to-prior duration


def _font(sz, serif=False, bold=True):
    cands = ([
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
    ] if serif else []) + [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]
    for c in cands:
        if os.path.exists(c):
            return ImageFont.truetype(c, sz)
    return ImageFont.load_default()


def _spaced(s):
    return " ".join(s.upper())


def _text(cv, xy, s, font, fill, a=1.0, anchor="mm", align="center", spacing=8):
    if a <= 0.01:
        return
    ov = Image.new("RGBA", cv.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    col = (*fill, int(255 * min(1.0, a)))
    if "\n" in s:
        d.multiline_text(xy, s, font=font, fill=col, anchor=anchor, align=align, spacing=spacing)
    else:
        d.text(xy, s, font=font, fill=col, anchor=anchor)
    cv.alpha_composite(ov)


def _wrap(draw, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= maxw:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


# ── reverse-chronology journey (only the stages we have stills for) ───────────
STAGES = [
    dict(n=11, key="stage11_luca_plate", name="LUCA",
         cite="the last universal common ancestor", desc="One cell. Ancestor of everything that lives.",
         story="The last common ancestor of all life. Run the clock back."),
    dict(n=7, key="stage7_genetic_code_plate", name="The Genetic Code",
         cite="codon → amino-acid mapping", desc="The 4×4×4 table that turns sequence into substance.",
         story="Unwrite the code — the mapping of triplet to amino acid dissolves."),
    dict(n=4, key="stage4_selection", name="Protocell Selection",
         cite="differential replication", desc="Compartments that copy faster outlast the rest.",
         story="Protocells forget their winners. Selection runs in reverse."),
    dict(n=3, key="stage3_vesicles", name="Vesicles",
         cite="Helfrich membrane curvature", desc="The first inside, sealed by a lipid bilayer.",
         story="Membranes unseal. The first 'inside' becomes outside again."),
    dict(n=2, key="stage2_autocatalytic", name="Autocatalytic Sets",
         cite="Kauffman RAF networks", desc="Reaction loops that collectively make themselves.",
         story="The self-sustaining loops break their own catalysis."),
    dict(n=1, key="stage1_reaction_diffusion", name="Gray–Scott",
         cite="Turing 1952 · reaction-diffusion", desc="Pure chemistry: an activator racing an inhibitor.",
         story="Down to reaction and diffusion. Spots and stripes — nothing alive."),
    dict(n=0, key="stage0_soup", name="Primordial Soup",
         cite="prebiotic chemistry", desc="A warm, structureless broth of molecules.",
         story="And finally — a warm, formless soup. Before the first pattern."),
]


def _knockout_bg(im):
    """Some SEM stills were saved on a light transparency-checkerboard. The grid
    is purely achromatic (R=G=B) while every subject is warm sepia/amber, so we
    key the bright low-saturation background to instrument black, feathered."""
    arr = np.asarray(im, np.float32)
    corners = np.concatenate([arr[:30, :30], arr[:30, -30:], arr[-30:, :30], arr[-30:, -30:]]).reshape(-1, 3)
    if corners.mean() <= 100:
        return im                                   # already on a dark background
    lum = arr @ np.array([0.299, 0.587, 0.114], np.float32)
    sat = arr.max(2) - arr.min(2)
    bg = ((sat < 16) & (lum > 145)).astype(np.float32)
    bgm = np.asarray(Image.fromarray((bg * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.2)), np.float32) / 255
    keep = (1 - bgm)[..., None]
    out = arr * keep + np.array(BG, np.float32) * (1 - keep)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def _cover(path, w, h, up=1.18):
    im = _knockout_bg(Image.open(path).convert("RGB"))
    tw, th = int(w * up), int(h * up)
    s = max(tw / im.width, th / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x = (im.width - tw) // 2; y = (im.height - th) // 2
    return im.crop((x, y, x + tw, y + th))


def _noise(w, h, seed):
    rng = np.random.default_rng(seed)
    f = np.zeros((h, w), np.float32)
    for oct in range(4):
        gw, gh = 4 << oct, 4 << oct
        g = rng.random((gh, gw)).astype(np.float32)
        f += np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255 * (0.5 ** oct)
    f -= f.min(); f /= (f.max() + 1e-6)
    return f


_VIG = None
def _window_fx(arr):
    """Vignette + reticle on a window-sized RGB float array (in place-ish)."""
    global _VIG
    h, w = arr.shape[:2]
    if _VIG is None or _VIG.shape[:2] != (h, w):
        yy, xx = np.mgrid[0:h, 0:w]
        r = np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2))
        _VIG = np.clip(1.0 - 0.45 * np.clip(r - 0.5, 0, 1) ** 1.5, 0, 1).astype(np.float32)[..., None]
    return arr * _VIG


def _ken(img, p):
    """Slow push-in crop of a cover image at progress p in [0,1] -> WIN-sized RGB."""
    _, _, w, h = WIN
    z = 1.0 + 0.10 * p
    cw, ch = int(w / z * (img.width / (w * 1.18))), int(h / z * (img.height / (h * 1.18)))
    # simpler: crop centered region scaling with zoom, then resize to window
    cw = int(img.width / (1.18) / z); ch = int(img.height / (1.18) / z)
    cx = img.width // 2 + int(0.04 * img.width * (p - 0.5))
    cy = img.height // 2
    box = (cx - cw // 2, cy - ch // 2, cx + cw // 2, cy + ch // 2)
    return img.crop(box).resize((w, h), Image.LANCZOS)


def _overlay(cv, st, t_in, badge_a, dissolve=False):
    d = ImageDraw.Draw(cv)
    x, y, w, h = WIN
    # window border + corner ticks
    d.rectangle([x - 1, y - 1, x + w, y + h], outline=(*TEAL, int(120 * badge_a)), width=1)
    rl = 26
    for (cx, cy) in [(x, y), (x + w, y), (x, y + h), (x + w, y + h)]:
        d.line([(cx - rl, cy), (cx + rl, cy)], fill=(*TEAL, 150), width=1)
        d.line([(cx, cy - rl), (cx, cy + rl)], fill=(*TEAL, 150), width=1)
    # reticle crosshair + quadrant ticks
    ccx, ccy = x + w // 2, y + h // 2
    d.line([(ccx, y + 10), (ccx, y + h - 10)], fill=(*TEAL, 70), width=1)
    d.line([(x + 10, ccy), (x + w - 10, ccy)], fill=(*TEAL, 70), width=1)
    for fx in (0.25, 0.75):
        d.line([(x + int(w * fx), ccy - 8), (x + int(w * fx), ccy + 8)], fill=(*TEAL, 110), width=1)
        d.line([(ccx - 8, y + int(h * fx)), (ccx + 8, y + int(h * fx))], fill=(*TEAL, 110), width=1)
    # top badge (pulsing)
    _text(cv, (W // 2, 150), f"▶  {_spaced('LIVE SEM FEED')}   ·   STAGE {st['n']:02d}",
          _font(30), TEAL, badge_a)
    _text(cv, (W // 2, 250), st["name"], _font(74, serif=True), CREAM, 1.0)
    _text(cv, (W // 2, 312), st["cite"], _font(30, serif=True, bold=False), DIM, 0.9)
    # scale bar under window
    sb_y = y + h + 40; sb_x = x + 8
    d.line([(sb_x, sb_y), (sb_x + 150, sb_y)], fill=(*CREAM, 200), width=2)
    d.line([(sb_x, sb_y - 6), (sb_x, sb_y + 6)], fill=(*CREAM, 200), width=2)
    d.line([(sb_x + 150, sb_y - 6), (sb_x + 150, sb_y + 6)], fill=(*CREAM, 200), width=2)
    _text(cv, (sb_x + 75, sb_y + 26), "1 µm", _font(24), DIM, 0.9)
    _text(cv, (x + w - 8, sb_y + 13), _spaced("plate · mmxxvi"), _font(20), DIM, 0.6, anchor="rm")
    # wall label
    dd = ImageDraw.Draw(cv)
    desc = "\n".join(_wrap(dd, st["desc"], _font(34, serif=True, bold=False), W - 160))
    _text(cv, (W // 2, 1120), desc, _font(34, serif=True, bold=False), CREAM, 0.92, spacing=10)
    # marginalia ticker (slides up slightly as it fades in)
    ta = min(t_in / 0.6, 1.0)
    story = "\n".join(_wrap(dd, st["story"], _font(30), W - 150))
    _text(cv, (W // 2, 1400), story, _font(30), CREAM if not dissolve else DIM, ta, spacing=10)
    # bottom apparatus
    _text(cv, (W // 2, 1840), _spaced("cellautomata  ·  live sem feed"), _font(22), DIM, 0.55)


def render():
    os.makedirs(OUT, exist_ok=True)
    imgs = [_cover(f"{SRC}/{s['key']}.png", WIN[2], WIN[3]) for s in STAGES]
    mask = _noise(WIN[2], WIN[3], 7)
    silent = f"/tmp/sem_feed_silent.mp4"
    wr = imageio_ffmpeg.write_frames(silent, (W, H), fps=FPS, codec="libx264",
        pix_fmt_in="rgb24", pix_fmt_out="yuv420p", macro_block_size=8,
        output_params=["-crf", "19", "-preset", "medium"])
    wr.send(None)
    nhold, ndiss = int(HOLD_S * FPS), int(DISS_S * FPS)
    total_intro = 1.0

    def compose(window_rgb, st, t_in, badge_a, fade=1.0, dissolve=False):
        cv = Image.new("RGBA", (W, H), (*BG, 255))
        win = Image.fromarray(np.clip(_window_fx(window_rgb.astype(np.float32)), 0, 255).astype(np.uint8))
        cv.paste(win, (WIN[0], WIN[1]))
        _overlay(cv, st, t_in, badge_a)
        fr = np.asarray(cv.convert("RGB"), np.uint8)
        if fade < 1.0:
            fr = (fr.astype(np.float32) * fade).astype(np.uint8)
        return fr

    for si, st in enumerate(STAGES):
        # hold (ken-burns push-in)
        for fi in range(nhold):
            p = fi / nhold
            badge_a = 0.55 + 0.45 * (0.5 + 0.5 * math.sin(2 * math.pi * (fi / FPS) / 2.2))
            win = np.asarray(_ken(imgs[si], p), np.float32)
            fade = min((si * 0 + fi) / (0.6 * FPS), 1.0) if si == 0 and fi < 0.6 * FPS else 1.0
            fade = min(fi / (0.5 * FPS), 1.0) if si == 0 else 1.0
            wr.send(np.ascontiguousarray(compose(win, st, fi / FPS, badge_a, fade)).tobytes())
        # dissolve into prior stage (reverse-morphogenesis), except after the last (soup)
        if si < len(STAGES) - 1:
            nxt = imgs[si + 1]
            a_end = np.asarray(_ken(imgs[si], 1.0), np.float32)
            for fi in range(ndiss):
                p = fi / ndiss
                thr = p * 1.25 - 0.12
                dsm = np.clip((mask - thr) / 0.10, 0, 1)[..., None]   # 1=keep A, 0=show B
                b = np.asarray(_ken(nxt, 0.0), np.float32)
                win = a_end * dsm + b * (1 - dsm)
                # teal dissolve front
                front = np.abs(mask - thr) < 0.02
                win[front] = win[front] * 0.4 + np.array(TEAL, np.float32) * 0.6
                badge_a = 0.5
                wr.send(np.ascontiguousarray(compose(win, st, 1.0, badge_a, dissolve=True)).tobytes())
        else:
            # settle on soup, fade to black
            for fi in range(int(1.6 * FPS)):
                p = fi / (1.6 * FPS)
                win = np.asarray(_ken(imgs[si], min(1.0, 0.0 + p)), np.float32)
                wr.send(np.ascontiguousarray(compose(win, st, 1.0, 0.5, fade=1.0 - 0.85 * p)).tobytes())
    wr.close()

    dur = (len(STAGES) * HOLD_S) + (len(STAGES) - 1) * DISS_S + 1.6
    out = f"{OUT}/live_sem_feed_reverse.mp4"
    af = (f"[1:a][2:a]amix=inputs=2,volume=0.13,lowpass=f=420,"
          f"afade=t=in:st=0:d=2,afade=t=out:st={dur-2.2:.1f}:d=2.2[a]")
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", silent,
                    "-f", "lavfi", "-t", f"{dur}", "-i", "sine=frequency=61.74:sample_rate=44100",
                    "-f", "lavfi", "-t", f"{dur}", "-i", "sine=frequency=92.50:sample_rate=44100",
                    "-filter_complex", af, "-map", "0:v", "-map", "[a]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "144k", "-shortest",
                    "-movflags", "+faststart", out], check=True)
    print(f"-> {out}  ({os.path.getsize(out)/1e6:.1f} MB, {dur:.0f}s, {len(STAGES)} stages reversed)")


if __name__ == "__main__":
    render()
