"""Render a narrated progress video (MP4 + voice-over) that proves what the
CellAutomata discovery engine does — using REAL simulation footage from the
Gray-Scott rule, not stock b-roll.

Pipeline (fully local, no network):
  1. espeak-ng  -> per-segment voice-over WAV (offline TTS)
  2. cellauto Engine.render_rgb -> real reaction-diffusion frames (viridis)
  3. Pillow -> title cards + lower-third labels + fades
  4. imageio-ffmpeg's bundled ffmpeg -> H.264 video, then mux AAC audio

Run:  python3 tools/make_progress_video.py --out progress.mp4
"""
from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import imageio_ffmpeg
from cellauto.engine import Engine
from cellauto.rules import REGISTRY
from cellauto.rules.abiogenesis import stage1_grayscott as gs

W, H, FPS = 1280, 720, 30
RULE = "abiogenesis-stage1-grayscott"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
ACCENT = (86, 222, 196)      # teal
ACCENT2 = (150, 214, 92)     # viridis green
BG_TOP, BG_BOT = (7, 11, 18), (16, 28, 44)
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def font(sz, bold=True):
    return ImageFont.truetype(FONT_B if bold else FONT_R, sz)


# ---------------------------------------------------------------- backgrounds
def _gradient_bg():
    top = np.array(BG_TOP, np.float32)
    bot = np.array(BG_BOT, np.float32)
    ramp = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    col = (top[None, :] * (1 - ramp) + bot[None, :] * ramp)  # H x 3
    bg = np.repeat(col[:, None, :], W, axis=1)
    # soft centre glow
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt(((xx - W / 2) / (W * 0.7)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2)
    glow = np.clip(1 - d, 0, 1)[..., None] ** 2 * np.array([10, 26, 30], np.float32)
    return np.clip(bg + glow, 0, 255).astype(np.uint8)


_BG = _gradient_bg()


def _wrap(draw, text, fnt, max_w):
    out = []
    for para in text.split("\n"):
        words, line = para.split(" "), ""
        for w in words:
            t = (line + " " + w).strip()
            if draw.textlength(t, font=fnt) <= max_w:
                line = t
            else:
                out.append(line)
                line = w
        out.append(line)
    return out


def card_image(kicker, title, subtitle, foot):
    img = Image.fromarray(_BG.copy())
    d = ImageDraw.Draw(img)
    cx = W // 2
    # measure block height to vertically centre
    tfont = font(84, True)
    title_lines = _wrap(d, title, tfont, W - 240)
    blocks = []
    if kicker:
        blocks.append(("kicker", kicker))
    for ln in title_lines:
        blocks.append(("title", ln))
    if subtitle:
        blocks.append(("sub", subtitle))
    heights = {"kicker": 46, "title": 100, "sub": 60}
    total = sum(heights[k] for k, _ in blocks)
    y = (H - total) // 2 - 10
    for kind, txt in blocks:
        if kind == "kicker":
            f = font(30, True)
            spaced = "   ".join(txt.upper())
            w = d.textlength(spaced, font=f)
            d.text((cx - w / 2, y), spaced, font=f, fill=ACCENT)
            y += heights[kind]
        elif kind == "title":
            f = tfont
            w = d.textlength(txt, font=f)
            d.text((cx - w / 2, y), txt, font=f, fill=(238, 244, 250))
            y += heights[kind]
        else:
            f = font(34, False)
            for ln in _wrap(d, txt, f, W - 320):
                w = d.textlength(ln, font=f)
                d.text((cx - w / 2, y), ln, font=f, fill=(150, 170, 190))
                y += 44
    # accent rule under title
    d.line([(cx - 70, y + 6), (cx + 70, y + 6)], fill=ACCENT2, width=3)
    if foot:
        f = font(24, False)
        w = d.textlength(foot, font=f)
        d.text((cx - w / 2, H - 70), foot, font=f, fill=(110, 128, 146))
    return np.asarray(img, np.uint8)


# ---------------------------------------------------------------- simulations
def render_pool(kw, grid, dev, seed, pool_n=170):
    rule = REGISTRY[RULE](**kw)
    eng = Engine(width=grid, height=grid, rule=rule, seed=seed)
    grab = set(int(round(x)) for x in np.linspace(1, dev, pool_n))
    pool = []
    for step in range(1, dev + 1):
        eng.step()
        if step in grab:
            pool.append(np.asarray(rule.render_rgb(eng.state), np.uint8))
    return pool


def sim_overlay(name, sub, tag):
    """Static RGBA overlay (lower-third band + labels) drawn once per clip."""
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    # lower-third gradient band
    band_h = 168
    for i in range(band_h):
        a = int(200 * (i / band_h) ** 1.4)
        d.line([(0, H - band_h + i), (W, H - band_h + i)], fill=(4, 7, 12, a))
    d.line([(80, H - band_h + 6), (W - 80, H - band_h + 6)], fill=(*ACCENT, 90), width=2)
    d.text((84, H - 132), name, font=font(50, True), fill=(240, 246, 252))
    d.text((86, H - 64), sub, font=font(27, False), fill=(168, 186, 204))
    # classification pill (top-left)
    pf = font(24, True)
    pw = d.textlength(tag, font=pf)
    d.rounded_rectangle([84, 70, 84 + pw + 36, 116], radius=22, fill=(*ACCENT2, 235))
    d.text((84 + 18, 78), tag, font=pf, fill=(8, 16, 10))
    d.text((84, 132), "REAL ENGINE OUTPUT", font=font(20, True), fill=(120, 200, 188))
    return ov


def sim_frame(pool, p, overlay):
    idx = int(round(p * (len(pool) - 1)))
    sq = Image.fromarray(pool[idx]).resize((720, 720), Image.BICUBIC)
    img = Image.fromarray(_BG.copy())
    img.paste(sq, ((W - 720) // 2, (H - 720) // 2))
    # thin frame around specimen
    d = ImageDraw.Draw(img)
    x0, y0 = (W - 720) // 2, (H - 720) // 2
    d.rectangle([x0 - 1, y0 - 1, x0 + 720, y0 + 720], outline=(40, 70, 86), width=2)
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    return np.asarray(img, np.uint8)


def fade(frame, a):
    if a >= 0.999:
        return frame
    return (frame.astype(np.float32) * a).astype(np.uint8)


# ---------------------------------------------------------------- audio (TTS)
def tts(text, path):
    subprocess.run(["espeak-ng", "-v", "en-us", "-s", "150", "-p", "44",
                    "-g", "8", "-w", path, text], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def read_int16(path):
    w = wave.open(path, "rb")
    sr, ch, n = w.getframerate(), w.getnchannels(), w.getnframes()
    a = np.frombuffer(w.readframes(n), np.int16).astype(np.int32)
    w.close()
    if ch == 2:
        a = a.reshape(-1, 2).mean(1).astype(np.int32)
    return a, sr


def ambient_bed(n, sr):
    t = np.arange(n) / sr
    bed = (0.55 * np.sin(2 * np.pi * 98 * t)
           + 0.40 * np.sin(2 * np.pi * 147 * t)
           + 0.28 * np.sin(2 * np.pi * 196.5 * t))
    lfo = 0.6 + 0.4 * np.sin(2 * np.pi * 0.05 * t)
    bed *= lfo
    bed /= (np.max(np.abs(bed)) + 1e-9)
    # fade in/out 1.5s
    f = min(int(1.5 * sr), n // 2)
    env = np.ones(n)
    env[:f] = np.linspace(0, 1, f)
    env[-f:] = np.linspace(1, 0, f)
    return bed * env


# ---------------------------------------------------------------- the script
def segments():
    def gk(name):
        F, k = gs.GRAY_SCOTT_PRESETS[name]
        return float(F), float(k)

    mF, mk = gk("mitosis")
    lF, lk = gk("labyrinth")
    return [
        dict(type="card", kicker="PROGRESS REPORT", title="CellAutomata",
             subtitle="Abiogenesis Discovery Engine",
             foot="reaction-diffusion life search",
             vo="Cellular Automata. An engine that searches for the origins of "
                "life, one simulation at a time. Here is our progress."),
        dict(type="card", kicker="THE HARNESS",
             title="We taught a search\nto look for life", subtitle="",
             foot="Gray-Scott reaction-diffusion",
             vo="We built a discovery harness around the Gray Scott reaction "
                "diffusion model. It sweeps thousands of parameter combinations, "
                "and scores every run for life like, emergent structure."),
        dict(type="sim", name="Self-Replicating Spots",
             sub=f"Gray-Scott  F={mF:.4f}  k={mk:.4f}  ·  preset “mitosis”",
             tag="LIVING", kw=dict(preset="mitosis"), grid=132, dev=360, seed=1,
             vo="This is mitosis. From a single seed, spots grow, and then "
                "divide. Self replication, emerging from pure chemistry."),
        dict(type="sim", name="Coral Growth",
             sub="Gray-Scott  F=0.0545  k=0.0620  ·  stabilises near generation 720",
             tag="STABLE", kw=dict(F=0.0545, k=0.062), grid=132, dev=780, seed=1,
             vo="Tune the feed and kill rates, and the system grows like coral. "
                "Branching, accreting, and finally settling into a stable, living "
                "structure."),
        dict(type="sim", name="Labyrinth",
             sub=f"Gray-Scott  F={lF:.4f}  k={lk:.4f}  ·  self-organising channels",
             tag="LIVING", kw=dict(preset="labyrinth"), grid=132, dev=420, seed=1,
             vo="Shift the parameters again, and labyrinthine channels self "
                "organise across the entire field."),
        dict(type="sim", name="Solitons  ·  U-Skate",
             sub="Gray-Scott  F=0.0620  k=0.0609  ·  self-propelled pulses",
             tag="LIVING", kw=dict(F=0.062, k=0.0609), grid=132, dev=560, seed=1,
             vo="And here, solitons. Self propelled pulses that glide and "
                "persist, never fully settling."),
        dict(type="card", kicker="THE SWEEP",
             title="5,376 simulations\n16 parallel workers", subtitle="",
             foot="classified · scored · timed — we detect when life stabilises",
             vo="To find the best of these, we launched sixteen parallel workers, "
                "sweeping over five thousand simulations. Each one is classified, "
                "scored, and timed. We detect the exact generation where life "
                "stabilises."),
        dict(type="card", kicker="THE PAYOFF", title="The PLUS\nReplay Library",
             subtitle="", foot="every find deterministic — one command replays it, pixel for pixel",
             vo="The winners are curated into the PLUS replay library. Every find "
                "is fully deterministic. A single command replays it, pixel for "
                "pixel."),
        dict(type="card", kicker="", title="CellAutomata",
             subtitle="Life, discovered by search.", foot="",
             vo="Cellular Automata. Life, discovered by search."),
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="progress.mp4")
    ap.add_argument("--lead", type=float, default=0.35)
    ap.add_argument("--tail", type=float, default=0.75)
    ap.add_argument("--min-card", type=float, default=3.2)
    args = ap.parse_args()

    segs = segments()
    tmp = tempfile.mkdtemp(prefix="pv_")
    sr = 22050

    # ---- 1. TTS + timing ----
    audio_parts, frame_counts = [], []
    print("· generating voice-over (espeak-ng) ...")
    for i, s in enumerate(segs):
        wav = os.path.join(tmp, f"vo_{i}.wav")
        tts(s["vo"], wav)
        speech, sr = read_int16(wav)
        seg = np.concatenate([np.zeros(int(args.lead * sr), np.int32), speech,
                              np.zeros(int(args.tail * sr), np.int32)])
        dur = len(seg) / sr
        if s["type"] == "card":
            dur = max(dur, args.min_card)
        nframes = int(round(dur * FPS))
        pad = nframes / FPS * sr - len(seg)
        if pad > 0:
            seg = np.concatenate([seg, np.zeros(int(pad), np.int32)])
        audio_parts.append(seg)
        frame_counts.append(nframes)
        print(f"  [{i}] {s['type']:4} {dur:5.1f}s / {nframes} frames")

    # ---- 2. master narration + ambient bed ----
    speech = np.concatenate(audio_parts)
    bed = ambient_bed(len(speech), sr)
    mix = speech.astype(np.float64) + bed * 0.11 * 32767
    mix = np.clip(mix, -32768, 32767).astype(np.int16)
    narr = os.path.join(tmp, "narration.wav")
    with wave.open(narr, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(mix.tobytes())
    total_s = len(mix) / sr
    print(f"· narration: {total_s:.1f}s")

    # ---- 3. stream video frames ----
    silent = os.path.join(tmp, "silent.mp4")
    writer = imageio_ffmpeg.write_frames(
        silent, (W, H), fps=FPS, codec="libx264", pix_fmt_in="rgb24",
        pix_fmt_out="yuv420p", macro_block_size=8,
        output_params=["-crf", "20", "-preset", "medium"])
    writer.send(None)
    FADE = 9
    for i, s in enumerate(segs):
        n = frame_counts[i]
        if s["type"] == "card":
            base = card_image(s["kicker"], s["title"], s["subtitle"], s["foot"])
            for j in range(n):
                a = min(1.0, (j + 1) / FADE, (n - j) / FADE)
                writer.send(np.ascontiguousarray(fade(base, a)).tobytes())
        else:
            pool = render_pool(s["kw"], s["grid"], s["dev"], s["seed"])
            ov = sim_overlay(s["name"], s["sub"], s["tag"])
            for j in range(n):
                p = j / max(1, n - 1)
                fr = sim_frame(pool, p, ov)
                a = min(1.0, (j + 1) / FADE, (n - j) / FADE)
                writer.send(np.ascontiguousarray(fade(fr, a)).tobytes())
        print(f"· segment {i} rendered ({n} frames)")
    writer.close()

    # ---- 4. mux ----
    subprocess.run([FFMPEG, "-y", "-i", silent, "-i", narr, "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", args.out], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sz = os.path.getsize(args.out)
    print(f"\nDONE -> {args.out}  ({sz/1e6:.1f} MB, {total_s:.1f}s, {W}x{H}@{FPS})")


if __name__ == "__main__":
    main()
