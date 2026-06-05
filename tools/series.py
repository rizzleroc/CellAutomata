"""CellAutomata explainer SERIES renderer (data-driven).

Each PART (see tools/series_scripts.py) is a list of scenes. Scene kinds:
  - title    : part number + title + subtitle card
  - engine   : footage from ANY rule via REGISTRY[rule].render_rgb (grayscott,
               abiogenesis stages, conway, wolfram1d, natural-selection, ...)
  - relit    : Gray-Scott v-field, 3D normal-map relit (molten/jewel look)
  - mandala  : compound kaleidoscope fold (spinning)
  - grid     : 3x3 of evolving sims (the discovery search)
  - command  : a "TRY IT" card — real `cellauto export ...` line + tunable knobs

Every scene carries vo (narration) + cap (on-screen caption). Per-part: espeak
voice-over + ambient bed, muxed. Renders media/series/partNN_<slug>.mp4.

  python3 tools/series.py            # render all parts
  python3 tools/series.py --part 2   # render one part
"""
from __future__ import annotations
import argparse, os, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
import relit as R
import mandala_x as MX
import make_progress_video as MP          # tts(), read_int16(), ambient_bed()
from cellauto.engine import Engine
from cellauto.rules import REGISTRY

FF = imageio_ffmpeg.get_ffmpeg_exe()
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FM = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
SIZE, FPS, SR = 1080, 30, 22050
ACCENT = (96, 210, 200)

# microscopy/field palettes for the generic engine renderer when a rule's own
# render is dull; default uses the rule's render_rgb.
MICRO = {
    "cyto": R.lut([(0, (2, 8, 12)), (.3, (6, 60, 80)), (.6, (20, 165, 175)), (.82, (120, 230, 220)), (1, (236, 255, 250))]),
    "amber": R.lut([(0, (4, 3, 1)), (.3, (70, 40, 6)), (.6, (192, 120, 20)), (.82, (245, 205, 82)), (1, (255, 250, 220))]),
}


def _bg():
    top = np.array([7, 11, 18], np.float32); bot = np.array([15, 26, 42], np.float32)
    ramp = np.linspace(0, 1, SIZE, np.float32)[:, None]
    return np.repeat((top * (1 - ramp) + bot * ramp)[:, None, :], SIZE, 1).astype(np.uint8)
BG = _bg()


def watermark(d, part):
    d.text((34, 28), f"CellAutomata · Part {part}", font=ImageFont.truetype(FB, 26), fill=(150, 200, 200))


def caption(d, cap):
    d.rectangle([0, SIZE - 88, SIZE, SIZE], fill=(5, 7, 11))
    d.text((34, SIZE - 74), cap, font=ImageFont.truetype(FB, 40), fill=(244, 248, 252))


def fade(arr, fi, n, k=10):
    a = min(1.0, (fi + 1) / k, (n - fi) / k)
    return arr if a >= 0.999 else (arr.astype(np.float32) * a).astype(np.uint8)


def make_engine(rule, cfg, grid, seed, mode):
    eng = Engine(width=grid, height=grid, rule=REGISTRY[rule](**cfg), seed=seed)
    if mode == "scatter":
        rng = np.random.default_rng(seed); u = np.ones((grid, grid), np.float32); v = np.zeros((grid, grid), np.float32); r = 5
        for _ in range(grid // 11):
            cy = int(rng.integers(r, grid - r)); cx = int(rng.integers(r, grid - r))
            u[cy - r:cy + r, cx - r:cx + r] = 0.5; v[cy - r:cy + r, cx - r:cx + r] = 0.25
        v += rng.uniform(0, 0.02, (grid, grid)).astype(np.float32)
        if hasattr(eng.state, "u"):
            eng.state.u = u; eng.state.v = np.clip(v, 0, 1)
    return eng


# ----- scene renderers (each yields frames via send(img_pil, fi, n)) -----
def sc_title(s, n, send, part):
    img = Image.fromarray(BG.copy()); d = ImageDraw.Draw(img)
    d.text((SIZE / 2 - d.textlength(f"PART {part}", font=ImageFont.truetype(FB, 40)) / 2, 300),
           f"PART {part}", font=ImageFont.truetype(FB, 40), fill=ACCENT)
    tf = ImageFont.truetype(FB, 76)
    for i, line in enumerate(_wrap(d, s["title"], tf, SIZE - 200)):
        d.text((SIZE / 2 - d.textlength(line, font=tf) / 2, 380 + i * 90), line, font=tf, fill=(238, 244, 250))
    sf = ImageFont.truetype(FR, 34)
    for i, line in enumerate(_wrap(d, s.get("sub", ""), sf, SIZE - 260)):
        d.text((SIZE / 2 - d.textlength(line, font=sf) / 2, 600 + i * 46), line, font=sf, fill=(150, 175, 195))
    arr = np.asarray(img, np.uint8)
    for fi in range(n):
        send(Image.fromarray(fade(arr.copy(), fi, n, 14)), fi, n)


def _wrap(d, text, fnt, maxw):
    out, line = [], ""
    for w in text.split():
        t = (line + " " + w).strip()
        if d.textlength(t, font=fnt) <= maxw:
            line = t
        else:
            out.append(line); line = w
    if line:
        out.append(line)
    return out or [""]


_RULECACHE = {}


def _rule_for(s):
    key = (s["rule"], tuple(sorted(s.get("cfg", {}).items())))
    rule = _RULECACHE.get(key)
    if rule is None:
        rule = REGISTRY[s["rule"]](**s.get("cfg", {})); _RULECACHE[key] = rule
    return rule


def sc_engine(s, n, send, part):
    grid = s.get("grid", 200)
    eng = make_engine(s["rule"], s.get("cfg", {}), grid, s.get("seed", 1), s.get("mode", "central"))
    rule = _rule_for(s)
    for _ in range(s.get("warm", 0)):
        eng.step()
    for fi in range(n):
        eng.step()
        rgb = np.asarray(rule.render_rgb(eng.state), np.uint8)
        img = Image.fromarray(rgb).resize((SIZE, SIZE), Image.NEAREST if s.get("crisp") else Image.BICUBIC).convert("RGB")
        d = ImageDraw.Draw(img); watermark(d, part); caption(d, s["cap"])
        send(Image.fromarray(fade(np.asarray(img, np.uint8), fi, n)), fi, n)


def sc_relit(s, n, send, part):
    grid = s.get("grid", 220)
    eng = make_engine("abiogenesis-stage1-grayscott", s.get("cfg", {}), grid, s.get("seed", 1), s.get("mode", "scatter"))
    for _ in range(s.get("warm", 320)):
        eng.step()
    for fi in range(n):
        eng.step()
        v = np.asarray(eng.state.v, np.float32)
        alb = R.colorize(v, s.get("pal", "gold"))
        lit = R.relight(v, alb, az=2 * np.pi * fi / n + 0.6, bump=s.get("bump", 3.2), shininess=s.get("shin", 26), ks=s.get("ks", 1.0))
        img = Image.fromarray(lit).resize((SIZE, SIZE), Image.BICUBIC).convert("RGB")
        d = ImageDraw.Draw(img); watermark(d, part); caption(d, s["cap"])
        send(Image.fromarray(fade(np.asarray(img, np.uint8), fi, n)), fi, n)


def sc_mandala(s, n, send, part):
    eng = make_engine("abiogenesis-stage1-grayscott", s.get("cfg", {}), 220, s.get("seed", 1), "scatter")
    for _ in range(s.get("warm", 420)):
        eng.step()
    v = np.asarray(eng.state.v, np.float32); v /= v.max() + 1e-9
    M = MX.compound(MX.Kal(640, 220), v, s.get("n1", 12), s.get("n2", 6), s.get("octs", 1))
    base = Image.fromarray(MX.colorize(M, s.get("pal", "nebula")).astype(np.uint8)).resize((SIZE, SIZE), Image.BICUBIC)
    for fi in range(n):
        img = base.rotate(360.0 * fi / n, resample=Image.BICUBIC, expand=False).convert("RGB")
        d = ImageDraw.Draw(img); watermark(d, part); caption(d, s["cap"])
        send(Image.fromarray(fade(np.asarray(img, np.uint8), fi, n)), fi, n)


GRID_RULES = [("abiogenesis-stage1-grayscott", dict(F=0.026, k=0.055)), ("abiogenesis-stage1-grayscott", dict(F=0.0545, k=0.062)),
              ("abiogenesis-stage1-grayscott", dict(F=0.018, k=0.05)), ("abiogenesis-stage1-grayscott", dict(preset="labyrinth")),
              ("abiogenesis-stage1-grayscott", dict(F=0.030, k=0.057)), ("abiogenesis-stage1-grayscott", dict(F=0.0264, k=0.0579)),
              ("abiogenesis-stage1-grayscott", dict(F=0.022, k=0.051)), ("abiogenesis-stage1-grayscott", dict(F=0.0186, k=0.0502)),
              ("abiogenesis-stage1-grayscott", dict(preset="mitosis"))]


def sc_grid(s, n, send, part):
    engs = [make_engine(r, c, 90, i + 1, "scatter") for i, (r, c) in enumerate(GRID_RULES)]
    for _ in range(200):
        for e in engs:
            e.step()
    for fi in range(n):
        canvas = Image.new("RGB", (SIZE, SIZE), (6, 8, 12))
        for i, e in enumerate(engs):
            e.step(); v = np.asarray(e.state.v, np.float32)
            tile = Image.fromarray((MICRO["cyto"][(np.clip(v / .42, 0, 1) ** .8 * 255).astype(np.uint8)] * 255).astype(np.uint8))
            canvas.paste(tile.resize((SIZE // 3, SIZE // 3), Image.BICUBIC), ((i % 3) * SIZE // 3, (i // 3) * SIZE // 3))
        d = ImageDraw.Draw(canvas); watermark(d, part); caption(d, s["cap"])
        send(Image.fromarray(fade(np.asarray(canvas, np.uint8), fi, n)), fi, n)


def sc_command(s, n, send, part):
    img = Image.fromarray(BG.copy()); d = ImageDraw.Draw(img)
    watermark(d, part)
    d.text((50, 130), "TRY IT YOURSELF", font=ImageFont.truetype(FB, 44), fill=ACCENT)
    # command box
    d.rounded_rectangle([50, 210, SIZE - 50, 360], radius=16, fill=(10, 14, 20), outline=(40, 70, 86), width=2)
    mf = ImageFont.truetype(FM, 24)
    for i, line in enumerate(s["cmd"]):
        d.text((74, 234 + i * 34), line, font=mf, fill=(180, 240, 220))
    # tunables
    d.text((50, 400), "Knobs you can tune:", font=ImageFont.truetype(FB, 32), fill=(238, 244, 250))
    kf = ImageFont.truetype(FR, 27)
    for i, (k, desc) in enumerate(s["knobs"]):
        y = 452 + i * 50
        d.text((66, y), f"• {k}", font=ImageFont.truetype(FB, 27), fill=(150, 210, 235))
        d.text((66 + d.textlength(f"• {k}", font=ImageFont.truetype(FB, 27)) + 14, y), desc, font=kf, fill=(176, 192, 208))
    caption(d, s["cap"])
    arr = np.asarray(img, np.uint8)
    for fi in range(n):
        send(Image.fromarray(fade(arr.copy(), fi, n, 12)), fi, n)


SCENE = {"title": sc_title, "engine": sc_engine, "relit": sc_relit, "mandala": sc_mandala, "grid": sc_grid, "command": sc_command}


def render_part(part_no, part, outdir):
    tmp = f"/tmp/series_p{part_no}"; os.makedirs(tmp, exist_ok=True)
    # TTS + timing
    audio, counts = [], []
    lead, tail = 0.3, 0.7
    for i, sc in enumerate(part["scenes"]):
        wav = f"{tmp}/vo_{i}.wav"; MP.tts(sc["vo"], wav)
        sp, _ = MP.read_int16(wav)
        seg = np.concatenate([np.zeros(int(lead * SR), np.int32), sp, np.zeros(int(tail * SR), np.int32)])
        dur = max(len(seg) / SR, 3.5 if sc["kind"] == "title" else 4.0)
        nf = int(round(dur * FPS)); pad = nf / FPS * SR - len(seg)
        if pad > 0:
            seg = np.concatenate([seg, np.zeros(int(pad), np.int32)])
        audio.append(seg); counts.append(nf)
    speech = np.concatenate(audio); bed = MP.ambient_bed(len(speech), SR)
    mix = np.clip(speech.astype(np.float64) * 0.95 + bed * 0.12 * 32767, -32768, 32767).astype(np.int16)
    narr = f"{tmp}/narr.wav"
    with wave.open(narr, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(mix.tobytes())
    silent = f"{tmp}/silent.mp4"
    wr = imageio_ffmpeg.write_frames(silent, (SIZE, SIZE), fps=FPS, codec="libx264", pix_fmt_in="rgb24",
        pix_fmt_out="yuv420p", macro_block_size=2, output_params=["-crf", "19", "-preset", "medium"])
    wr.send(None)

    def send(img, fi, n):
        wr.send(np.ascontiguousarray(np.asarray(img.convert("RGB"), np.uint8)).tobytes())

    for i, sc in enumerate(part["scenes"]):
        SCENE[sc["kind"]](sc, counts[i], send, part_no)
        print(f"  part {part_no} scene {i+1}/{len(part['scenes'])} ({sc['kind']})", flush=True)
    wr.close()
    os.makedirs(outdir, exist_ok=True)
    out = f"{outdir}/part{part_no:02d}_{part['slug']}.mp4"
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", silent, "-i", narr,
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "176k", "-shortest",
                    "-movflags", "+faststart", out], check=True)
    print(f"PART {part_no} -> {out} ({os.path.getsize(out)/1e6:.1f} MB)")
    return out


def main():
    import series_scripts
    ap = argparse.ArgumentParser(); ap.add_argument("--part", type=int, default=0); a = ap.parse_args()
    outdir = "media/series"
    parts = series_scripts.PARTS
    items = [(a.part, parts[a.part - 1])] if a.part else list(enumerate(parts, 1))
    for no, p in items:
        render_part(no, p, outdir)


if __name__ == "__main__":
    main()
