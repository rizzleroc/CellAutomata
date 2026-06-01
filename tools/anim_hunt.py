"""Animation hunt — deep & wide search for the best animated mandalas.

Wide: ~42 reaction-diffusion sources across the F/k complexity band + presets,
both centre- and scatter-seeded. For each, measure TEMPORAL motion (sustained
frame-to-frame change) and sweep the compound+octave kaleidoscope recipes,
scoring the folded mandala for COMPLEXITY. Animation score = complexity x motion.
Render mode turns the champions into seamless animated loops + a best-of reel.

  python3 tools/anim_hunt.py --worker 0     # 1 of 16 search workers
  python3 tools/anim_hunt.py --contact      # contact sheet of all previews
  python3 tools/anim_hunt.py --render       # render champion loops + reel + gif
"""
from __future__ import annotations
import argparse, glob, json, math, os, subprocess, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mandala_x as MX
import imageio_ffmpeg
from cellauto.engine import Engine
from cellauto.rules import REGISTRY

RULE = MX.RULE
OUT = "discovery/animhunt"
FF = imageio_ffmpeg.get_ffmpeg_exe()
GRID = 240

FK = [(0.014, 0.045), (0.018, 0.050), (0.022, 0.051), (0.026, 0.055), (0.030, 0.057),
      (0.0264, 0.0579), (0.0186, 0.0502), (0.034, 0.0618), (0.0367, 0.0649), (0.039, 0.058),
      (0.045, 0.063), (0.0545, 0.062), (0.058, 0.063), (0.062, 0.0609), (0.070, 0.061), (0.016, 0.0448)]
PRESETS = ["mitosis", "labyrinth", "waves", "stripes", "spots"]
SOURCES = []
for F, k in FK:
    for s in (1, 7):
        SOURCES.append((f"F{F:.3f}k{k:.3f}", dict(F=F, k=k), s, s == 7))
for p in PRESETS:
    for s in (1, 7):
        SOURCES.append((p, dict(preset=p), s, s == 7))


def scatter_seed(eng, grid, seed):
    rng = np.random.default_rng(seed); u = np.ones((grid, grid), np.float32); v = np.zeros((grid, grid), np.float32); r = 5
    for _ in range(grid // 9):
        cy = int(rng.integers(r, grid - r)); cx = int(rng.integers(r, grid - r))
        u[cy - r:cy + r, cx - r:cx + r] = 0.5; v[cy - r:cy + r, cx - r:cx + r] = 0.25
    v += rng.uniform(0, 0.02, (grid, grid)).astype(np.float32)
    eng.state.u = u; eng.state.v = np.clip(v, 0, 1)


def evolve_measure(kw, seed, scatter, warm=520):
    eng = Engine(width=GRID, height=GRID, rule=REGISTRY[RULE](**kw), seed=seed)
    if scatter:
        scatter_seed(eng, GRID, seed)
    prev = None; acts = []
    for s in range(1, warm + 1):
        eng.step()
        if s > warm - 26:
            v = np.asarray(eng.state.v, np.float32)
            if prev is not None:
                acts.append(float(np.abs(v - prev).mean()))
            prev = v
    v = np.asarray(eng.state.v, np.float32)
    return v / (v.max() + 1e-9), (float(np.mean(acts)) if acts else 0.0)


def compound_anim(kal, V, n1, n2, octs, rot, zoom):
    A = kal.fold(V, n1, rot, zoom)
    B = kal.fold(V, n2, rot + np.pi / max(n2, 1) * 0.5, zoom * 1.003)
    Mf = np.maximum(A, 0.82 * B)
    g = math.gcd(n1, n2)
    for oi in range(octs):
        Mf = np.maximum(Mf, (0.6 - 0.13 * oi) * MX.warp(Mf, 2.0 + 1.4 * oi, rot + 2 * np.pi / g * (oi + 1)))
    Mf = Mf * kal.mask
    return Mf / (Mf.max() + 1e-6)


def worker(idx):
    os.makedirs(OUT, exist_ok=True)
    pals = list(MX.PAL)
    for gi in range(idx, len(SOURCES), 16):
        name, kw, seed, scatter = SOURCES[gi]
        V, act = evolve_measure(kw, seed, scatter)
        np.savez_compressed(f"{OUT}/src_{gi:03d}.npz", V=V.astype(np.float16))
        kal = MX.Kal(400, GRID)
        best = None
        for n1 in (6, 8, 10, 12, 16):
            for n2 in (3, 5, 6):
                for octs in (0, 1, 2):
                    cx = MX.score(MX.compound(kal, V, n1, n2, octs))
                    if best is None or cx > best[3]:
                        best = (n1, n2, octs, cx)
        motion = min(act / 0.009, 1.5)
        combined = best[3] * (0.4 + 0.6 * motion)
        rec = {"gi": gi, "name": name, "kw": kw, "seed": seed, "scatter": scatter,
               "n1": best[0], "n2": best[1], "octs": best[2],
               "complexity": round(best[3], 4), "activity": round(act, 5),
               "motion": round(motion, 3), "combined": round(combined, 4)}
        json.dump(rec, open(f"{OUT}/best_{gi:03d}.json", "w"))
        k2 = MX.Kal(420, GRID)
        img = MX.colorize(MX.compound(k2, V, best[0], best[1], best[2]), pals[gi % len(pals)])
        Image.fromarray(img.astype(np.uint8)).resize((360, 360), Image.BICUBIC).save(f"{OUT}/prev_{gi:03d}.jpg", quality=85)
        print(f"[{idx}] {name} s{seed}{'sc' if scatter else ''}: {best[0]}x{best[1]} o{best[2]} "
              f"cx={best[3]:.3f} mot={motion:.2f} comb={combined:.3f}", flush=True)


def load_bests():
    return sorted([json.load(open(f)) for f in glob.glob(f"{OUT}/best_*.json")],
                  key=lambda b: -b["combined"])


def contact(out="discovery/animhunt_contact.jpg"):
    bests = load_bests()
    cols = 7; tile = 220; rows = (len(bests) + cols - 1) // cols
    img = Image.new("RGB", (cols * tile, rows * tile + 30), (10, 12, 16))
    from PIL import ImageDraw, ImageFont
    d = ImageDraw.Draw(img); f = ImageFont.truetype(MX.__dict__.get("FB", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf") if False else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
    for i, b in enumerate(bests):
        p = f"{OUT}/prev_{b['gi']:03d}.jpg"
        if not os.path.exists(p):
            continue
        t = Image.open(p).resize((tile - 6, tile - 6))
        x = (i % cols) * tile; y = (i // cols) * tile + 28
        img.paste(t, (x + 3, y + 3))
        d.text((x + 5, y + 4), f"#{i+1} {b['name'][:11]} {b['n1']}x{b['n2']}", font=f, fill=(240, 245, 250))
        d.text((x + 5, y + tile - 16), f"c{b['combined']:.2f} m{b['motion']:.1f}", font=f, fill=(150, 210, 235))
    img.save(out, quality=88)
    print(f"contact -> {out} ({len(bests)} candidates)")
    print("TOP 8:")
    for b in bests[:8]:
        print(f"  {b['name']:14} s{b['seed']} {b['n1']}x{b['n2']} o{b['octs']} cx={b['complexity']} mot={b['motion']} comb={b['combined']}")


def render_loop(b, pal, out, K=640, OUTRES=1080, dur=10, fps=30):
    eng = Engine(width=GRID, height=GRID, rule=REGISTRY[RULE](**b["kw"]), seed=b["seed"])
    if b["scatter"]:
        scatter_seed(eng, GRID, b["seed"])
    for _ in range(520):                       # warm to the intricate state the search scored
        eng.step()
    v = np.asarray(eng.state.v, np.float32); v /= (v.max() + 1e-9)   # FREEZE (avoids fill-in drift)
    kal = MX.Kal(K, GRID)
    N = dur * fps
    wr = imageio_ffmpeg.write_frames(out, (OUTRES, OUTRES), fps=fps, codec="libx264",
        pix_fmt_in="rgb24", pix_fmt_out="yuv420p", macro_block_size=2,
        output_params=["-crf", "18", "-preset", "medium"])
    wr.send(None)
    for fi in range(N):
        rot = 2 * np.pi * fi / N               # full turn -> perfectly seamless
        zoom = 1.0 + 0.05 * np.sin(2 * np.pi * fi / N)
        rgb = MX.colorize(compound_anim(kal, v, b["n1"], b["n2"], b["octs"], rot, zoom), pal)
        img = np.asarray(Image.fromarray(rgb.astype(np.uint8)).resize((OUTRES, OUTRES), Image.BICUBIC), np.uint8)
        wr.send(np.ascontiguousarray(img).tobytes())
    wr.close()
    print(f"  loop -> {out}")


def render():
    bests = load_bests()
    seen, top = set(), []
    for b in bests:
        if b["name"] in seen:
            continue
        seen.add(b["name"]); top.append(b)
        if len(top) >= 6:
            break
    os.makedirs("media", exist_ok=True)
    pals = ["nebula", "ice", "fire", "amethyst", "aqua", "emerald"]
    clips = []
    for i, b in enumerate(top):
        out = f"media/anim_{i}_{b['name'].replace('.','')}.mp4"
        print(f"#{i} {b['name']} {b['n1']}x{b['n2']} o{b['octs']} comb={b['combined']}")
        render_loop(b, pals[i % len(pals)], out)
        clips.append(os.path.abspath(out))
    lst = "/tmp/anim_reel.txt"
    open(lst, "w").write("".join(f"file '{c}'\n" for c in clips))
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", lst, "-c", "copy", "-movflags", "+faststart", "media/best_animations_reel.mp4"], check=True)
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", clips[0],
                    "-vf", "fps=12,scale=440:-1:flags=lanczos,palettegen=max_colors=64:stats_mode=diff", "/tmp/ah_pal.png"], check=True)
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", clips[0], "-i", "/tmp/ah_pal.png",
                    "-lavfi", "fps=12,scale=440:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=4",
                    "-loop", "0", "media/best_animation.gif"], check=True)
    json.dump({"champions": top}, open("discovery/animhunt_top.json", "w"), indent=2)
    print(f"DONE — {len(top)} loops + reel + GIF")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--worker", type=int, default=-1)
    ap.add_argument("--contact", action="store_true")
    ap.add_argument("--render", action="store_true")
    a = ap.parse_args()
    if a.contact:
        contact()
    elif a.render:
        render()
    elif a.worker >= 0:
        worker(a.worker)
    else:
        ap.error("need --worker N | --contact | --render")


if __name__ == "__main__":
    main()
