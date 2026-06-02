"""CellAutomata explainer video — 8 scenes, our real footage + espeak voice-over
+ on-screen captions + ambient bed. Reuses relit.py (3D relighting), mandala_x
(kaleidoscope fold), and make_progress_video (TTS + bed helpers).

  python3 tools/explainer.py --out media/explainer.mp4
"""
from __future__ import annotations
import argparse, os, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
import relit as R
import mandala_x as MX
import make_progress_video as MP            # tts(), read_int16(), ambient_bed()
from cellauto.engine import Engine
from cellauto.rules import REGISTRY

RULE = R.RULE
FF = imageio_ffmpeg.get_ffmpeg_exe()
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SIZE, FPS, SR = 1080, 30, 22050

# script (authored to match the whip prompt format)
SCENES = [
    dict(kind="rd", relit=True, kw=dict(preset="mitosis"), seed="central", grid=150, pal="copper",
         cap="Life from simple rules",
         vo="What if life didn't need a miracle — just a few simple rules?"),
    dict(kind="rd", relit=False, kw=dict(F=0.030, k=0.057), seed="scatter", grid=220, pal="cyto",
         cap="Two chemicals, one rule",
         vo="CellAutomata starts with two reacting chemicals and one equation."),
    dict(kind="rd", relit=False, kw=dict(preset="mitosis"), seed="central", grid=150, pal="membrane",
         cap="Self-replicating cells",
         vo="Those rules make spots that grow, then split — cells dividing, with no D N A at all."),
    dict(kind="grid", cap="Thousands of universes searched",
         vo="We search thousands of these tiny universes in parallel, hunting the most alive."),
    dict(kind="rd", relit=True, kw=dict(F=0.018, k=0.050), seed="scatter", grid=220, pal="amethyst",
         cap="Complexity from chemistry",
         vo="The winners boil, branch, and swim — real complexity, from pure chemistry."),
    dict(kind="mandala", kw=dict(F=0.026, k=0.055), n1=12, n2=6, pal="nebula",
         cap="Folded into sacred geometry",
         vo="Fold them into symmetry, and they become mandalas and snowflakes."),
    dict(kind="rd", relit=True, kw=dict(F=0.026, k=0.055), seed="scatter", grid=220, pal="gold",
         cap="Rendered in 4K",
         vo="Light them as three D surfaces, and flat math turns to molten metal."),
    dict(kind="rd", relit=True, kw=dict(preset="mitosis"), seed="central", grid=150, pal="copper",
         cap="Open source · reproduce any seed",
         vo="Every world here is deterministic — reproduce any of them from a single seed. CellAutomata."),
]

CYTO = {"cyto": R.lut([(0, (2, 8, 12)), (.3, (6, 60, 80)), (.6, (20, 165, 175)), (.82, (120, 230, 220)), (1, (236, 255, 250))]),
        "membrane": R.lut([(0, (8, 2, 12)), (.3, (70, 10, 60)), (.6, (185, 30, 120)), (.82, (242, 120, 190)), (1, (255, 226, 245))])}


def colorize_micro(v, pal, vmax=0.4, gamma=0.8):
    return (CYTO[pal][(np.clip(v / vmax, 0, 1) ** gamma * 255).astype(np.uint8)] * 255).astype(np.uint8)


def make_engine(kw, seed, grid, warm):
    eng = Engine(width=grid, height=grid, rule=REGISTRY[RULE](**kw), seed=1)
    if seed == "scatter":
        rng = np.random.default_rng(7); u = np.ones((grid, grid), np.float32); v = np.zeros((grid, grid), np.float32); r = 5
        for _ in range(grid // 11):
            cy = int(rng.integers(r, grid - r)); cx = int(rng.integers(r, grid - r))
            u[cy - r:cy + r, cx - r:cx + r] = 0.5; v[cy - r:cy + r, cx - r:cx + r] = 0.25
        v += rng.uniform(0, 0.02, (grid, grid)).astype(np.float32); eng.state.u = u; eng.state.v = np.clip(v, 0, 1)
    for _ in range(warm):
        eng.step()
    return eng


GRID_REGIMES = [dict(F=0.026, k=0.055), dict(F=0.0545, k=0.062), dict(F=0.018, k=0.05),
                dict(preset="labyrinth"), dict(F=0.030, k=0.057), dict(F=0.0264, k=0.0579),
                dict(F=0.022, k=0.051), dict(F=0.0186, k=0.0502), dict(preset="mitosis")]


def overlay(img, cap):
    d = ImageDraw.Draw(img)
    d.text((34, 30), "CellAutomata", font=ImageFont.truetype(FB, 30), fill=(235, 240, 248))
    d.rectangle([0, SIZE - 86, SIZE, SIZE], fill=(5, 7, 11))
    d.text((34, SIZE - 70), cap, font=ImageFont.truetype(FB, 40), fill=(245, 248, 252))


def scene_frames(scene, n, send):
    cap = scene["cap"]
    if scene["kind"] == "grid":
        engs = [make_engine(GRID_REGIMES[i], "scatter", 90, 200) for i in range(9)]
        for fi in range(n):
            canvas = Image.new("RGB", (SIZE, SIZE), (6, 8, 12))
            for i, e in enumerate(engs):
                e.step(); v = np.asarray(e.state.v, np.float32)
                tile = Image.fromarray((R.PAL["amethyst"][(np.clip(v / .42, 0, 1) ** .8 * 255).astype(np.uint8)] * 255).astype(np.uint8))
                canvas.paste(tile.resize((SIZE // 3, SIZE // 3), Image.BICUBIC), ((i % 3) * SIZE // 3, (i // 3) * SIZE // 3))
            overlay(canvas, cap); send(canvas, fi, n)
    elif scene["kind"] == "mandala":
        eng = make_engine(scene["kw"], "scatter", 220, 420)
        v = np.asarray(eng.state.v, np.float32); v /= v.max() + 1e-9        # FREEZE (avoid fill-in)
        M = MX.compound(MX.Kal(640, 220), v, scene["n1"], scene["n2"], 1)
        base = Image.fromarray(MX.colorize(M, scene["pal"]).astype(np.uint8)).resize((SIZE, SIZE), Image.BICUBIC)
        for fi in range(n):
            img = base.rotate(360.0 * fi / n, resample=Image.BICUBIC, expand=False).convert("RGB")
            overlay(img, cap); send(img, fi, n)
    else:
        eng = make_engine(scene["kw"], scene["seed"], scene["grid"], 0 if scene["seed"] == "central" else 300)
        for fi in range(n):
            eng.step(); v = np.asarray(eng.state.v, np.float32)
            if scene["relit"]:
                alb = R.colorize(v, scene["pal"]); lit = R.relight(v, alb, 2 * np.pi * fi / n + 0.6)
            else:
                lit = colorize_micro(v, scene["pal"])
            img = Image.fromarray(lit).resize((SIZE, SIZE), Image.BICUBIC).convert("RGB")
            overlay(img, cap); send(img, fi, n)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="media/explainer.mp4"); a = ap.parse_args()
    os.makedirs("media", exist_ok=True); tmp = "/tmp/explainer"; os.makedirs(tmp, exist_ok=True)
    # TTS + timing
    print("voice-over ..."); audio_parts, counts = [], []
    lead, tail = 0.3, 0.7
    for i, s in enumerate(SCENES):
        wav = f"{tmp}/vo_{i}.wav"; MP.tts(s["vo"], wav)
        sp, _sr = MP.read_int16(wav)
        seg = np.concatenate([np.zeros(int(lead * SR), np.int32), sp, np.zeros(int(tail * SR), np.int32)])
        dur = max(len(seg) / SR, 4.0); nf = int(round(dur * FPS))
        pad = nf / FPS * SR - len(seg)
        if pad > 0:
            seg = np.concatenate([seg, np.zeros(int(pad), np.int32)])
        audio_parts.append(seg); counts.append(nf)
        print(f"  scene {i+1}: {dur:.1f}s")
    speech = np.concatenate(audio_parts); bed = MP.ambient_bed(len(speech), SR)
    mix = np.clip(speech.astype(np.float64) * 0.95 + bed * 0.12 * 32767, -32768, 32767).astype(np.int16)
    narr = f"{tmp}/narr.wav"
    with wave.open(narr, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(mix.tobytes())
    # video
    silent = f"{tmp}/silent.mp4"
    wr = imageio_ffmpeg.write_frames(silent, (SIZE, SIZE), fps=FPS, codec="libx264", pix_fmt_in="rgb24",
        pix_fmt_out="yuv420p", macro_block_size=2, output_params=["-crf", "18", "-preset", "medium"])
    wr.send(None)

    def send(img, fi, n):
        af = min(1.0, (fi + 1) / 10, (n - fi) / 10)
        fr = np.asarray(img, np.uint8)
        if af < 0.999:
            fr = (fr.astype(np.float32) * af).astype(np.uint8)
        wr.send(np.ascontiguousarray(fr).tobytes())

    print("rendering scenes ...")
    for i, s in enumerate(SCENES):
        scene_frames(s, counts[i], send); print(f"  scene {i+1} done")
    wr.close()
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", silent, "-i", narr,
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "176k", "-shortest",
                    "-movflags", "+faststart", a.out], check=True)
    print(f"DONE -> {a.out} ({os.path.getsize(a.out)/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
