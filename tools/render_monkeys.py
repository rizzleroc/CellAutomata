"""Render the monkey-search hall of fame: the freak random soups that refused
to die. Re-runs each champion (measuring its TRUE lifespan with a high cap),
then renders a hero timelapse + a 3x2 montage with heat-trail rendering so
gliders streak like comets. Plus stills + a champions manifest."""
from __future__ import annotations
import glob, json, os, numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from monkeys import step, soup  # exact app rule (B3/S23, toroidal)

FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def lut(stops):
    g = np.linspace(0, 1, 256); xs = np.array([s[0] for s in stops])
    cols = np.array([s[1] for s in stops], float)
    return np.stack([np.interp(g, xs, cols[:, c]) for c in range(3)], 1).astype(np.uint8)


ICE = lut([(0, (3, 5, 14)), (.25, (8, 34, 90)), (.5, (16, 110, 190)),
           (.75, (70, 210, 232)), (1, (210, 250, 255))])


def render(heat, alive, size):
    rgb = ICE[(np.clip(heat, 0, 1) * 255).astype(np.uint8)]
    rgb[alive] = (255, 255, 255)              # live cells pop white over trails
    return Image.fromarray(rgb).resize((size, size), Image.BICUBIC)


def champions(n=6):
    rs = []
    for fp in glob.glob("discovery/monkeys/m_*.jsonl"):
        for l in open(fp):
            l = l.strip()
            if l:
                rs.append(json.loads(l))
    total = len(rs)
    rs.sort(key=lambda r: ((2 if r["fate"] == "perpetual" else 0) * 10_000_000
                           + r["longevity"] * 1000 + r["peak"]), reverse=True)
    return rs[:n], total


def true_life(r, cap=40000):
    g = soup(r["seed"], r["G"], r["S"], r["dens"]); seen = {}; peak = int(g.sum())
    for gen in range(cap + 1):
        pop = int(g.sum())
        if pop == 0:
            return gen, "extinct", peak
        peak = max(peak, pop)
        h = hash(g.tobytes())
        if h in seen:
            return seen[h], f"period-{gen-seen[h]}", peak
        seen[h] = gen; g = step(g)
    return cap, "perpetual", peak


def replay(r, show_gens, n_frames, decay=0.80):
    g = soup(r["seed"], r["G"], r["S"], r["dens"])
    heat = np.zeros((r["G"], r["G"]), np.float32)
    caps = set(int(x) for x in np.linspace(0, show_gens, n_frames))
    frames = []
    for gen in range(show_gens + 1):
        heat = np.maximum(heat * decay, g.astype(np.float32))
        if gen in caps:
            frames.append((heat.copy(), g.copy()))
        g = step(g)
    return frames


def main():
    champs, total = champions(6)
    print(f"{total} soups searched; top 6 champions:")
    for r in champs:
        tl, fate, peak = true_life(r)
        r["true_life"], r["true_fate"], r["true_peak"] = tl, fate, peak
        print(f"  seed={r['seed']:5} init={r['init_cells']:3} cells -> "
              f"lifespan {tl:,}{'+' if fate=='perpetual' else ''} gens, fate={fate}, peak={peak}")

    SHOW, NF, FPS = 3000, 450, 30
    reels = [replay(r, SHOW, NF) for r in champs]
    os.makedirs("media", exist_ok=True)
    big = ImageFont.truetype(FB, 54); med = ImageFont.truetype(FB, 30)
    small = ImageFont.truetype(FR, 22); tiny = ImageFont.truetype(FR, 19)

    # ---- hero: champion #0 fullscreen ----
    r0 = champs[0]
    wr = imageio_ffmpeg.write_frames("media/monkey_champion.mp4", (1080, 1080), fps=FPS,
        codec="libx264", pix_fmt_in="rgb24", pix_fmt_out="yuv420p", macro_block_size=2,
        output_params=["-crf", "18", "-preset", "medium"])
    wr.send(None)
    for fi, (heat, alive) in enumerate(reels[0]):
        gen = int(fi / (NF - 1) * SHOW)
        img = render(heat, alive, 1080).convert("RGB")
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, 1080, 96], fill=(6, 8, 13))
        d.text((30, 16), f"GENERATION {gen:,}", font=big, fill=(245, 250, 255))
        d.rectangle([0, 1080 - 70, 1080, 1080], fill=(6, 8, 13))
        life = f"{r0['true_life']:,}{'+' if r0['true_fate']=='perpetual' else ''}"
        d.text((30, 1080 - 60),
               f"{r0['init_cells']}-cell random soup  ·  lifespan {life} gens  ·  peak {r0['true_peak']} cells  ·  seed {r0['seed']}",
               font=small, fill=(150, 214, 92))
        a = min(1.0, (fi + 1) / 10, (NF - fi) / 10)
        fr = np.asarray(img, np.uint8)
        if a < 0.999:
            fr = (fr.astype(np.float32) * a).astype(np.uint8)
        wr.send(np.ascontiguousarray(fr).tobytes())
    wr.close()
    print("hero -> media/monkey_champion.mp4")

    # ---- montage 3x2 ----
    P, COLS, ROWS, TOP = 360, 3, 2, 70
    W, H = P * COLS, TOP + P * ROWS
    wr = imageio_ffmpeg.write_frames("media/monkeys_hall.mp4", (W, H), fps=FPS,
        codec="libx264", pix_fmt_in="rgb24", pix_fmt_out="yuv420p", macro_block_size=2,
        output_params=["-crf", "19", "-preset", "medium"])
    wr.send(None)
    for fi in range(NF):
        gen = int(fi / (NF - 1) * SHOW)
        canvas = Image.new("RGB", (W, H), (6, 8, 13))
        for ci, (r, reel) in enumerate(zip(champs, reels)):
            heat, alive = reel[fi]
            x, y = (ci % COLS) * P, TOP + (ci // COLS) * P
            canvas.paste(render(heat, alive, P), (x, y))
            d = ImageDraw.Draw(canvas)
            d.rectangle([x, y + P - 30, x + P, y + P], fill=(4, 6, 10))
            life = f"{r['true_life']:,}{'+' if r['true_fate']=='perpetual' else ''}"
            d.text((x + 8, y + P - 27), f"seed {r['seed']} · {life} gens · peak {r['true_peak']}",
                   font=tiny, fill=(120, 210, 235))
        d = ImageDraw.Draw(canvas)
        d.text((20, 16), f"MONKEYS AT KEYBOARDS — GENERATION {gen:,}", font=med, fill=(244, 249, 253))
        a = min(1.0, (fi + 1) / 10, (NF - fi) / 10)
        fr = np.asarray(canvas, np.uint8)
        if a < 0.999:
            fr = (fr.astype(np.float32) * a).astype(np.uint8)
        wr.send(np.ascontiguousarray(fr).tobytes())
    wr.close()
    print("montage -> media/monkeys_hall.mp4")

    # ---- stills (peak-ish frame = last) + manifest ----
    for i, (r, reel) in enumerate(zip(champs[:4], reels[:4])):
        heat, alive = reel[-1]
        render(heat, alive, 720).save(f"media/monkey_{i}_seed{r['seed']}.png")
    json.dump({"soups_searched": total,
               "champions": [{k: r[k] for k in ("seed", "G", "S", "dens", "init_cells",
                                                "true_life", "true_fate", "true_peak", "growth")}
                             for r in champs]},
              open("discovery/monkeys_champions.json", "w"), indent=2)
    print("DONE")


if __name__ == "__main__":
    main()
