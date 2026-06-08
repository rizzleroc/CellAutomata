"""needle.py — find the needle in the haystack.

Every discovery hunt cached its evolved reaction-diffusion source fields
(discovery/{animhunt,mandalax}/src_*.npz, 240px + 360px). This re-folds ALL of
them through a richer compound-kaleidoscope sweep than any single hunt tried
(more fold orders, more octaves), scores each by the mandala complexity metric,
ranks globally, and lays the winners on one contact sheet so the truly perfect
visualizations can be picked by eye — then rendered at 2160 in curated palettes.

    python tools/needle.py --sweep     # score every source, render the contact sheet
    python tools/needle.py --render "id1,id2,..."   # final 2160 stills of the picks
"""
from __future__ import annotations
import argparse, glob, json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mandala_x as MX                      # Kal, compound, score, colorize, PAL
import relit as R                           # metallic relight (gold/jade/ice/amethyst/copper)
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FM = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
RANK = "discovery/needle_rank.json"
DEEP_RANK = "discovery/needle_deep_rank.json"
FPS = 30
# per-metal relight character (bump, shininess, ks)
METAL = {"gold": (4.2, 26, 1.10), "copper": (4.0, 22, 1.00), "jade": (3.6, 18, 0.78),
         "ice": (4.4, 46, 1.22), "amethyst": (4.2, 30, 1.05)}

# richer than any single hunt swept
N1 = (6, 8, 10, 12, 16, 24)
N2 = (3, 5, 6)
OCTS = (1, 2, 3)
PAL_CYCLE = ["nebula", "ice", "fire", "emerald", "amethyst", "aqua", "rose", "ember", "gold"]

# --deep: finer fresh sources in the winning regimes + a far wider symmetry space
DEEP_N1 = (8, 10, 12, 16, 20, 24, 28, 32, 40, 48)
DEEP_N2 = (3, 5, 6, 7)
DEEP_OCTS = (1, 2, 3, 4)
DEEP_REGIMES = {
    "plasma": dict(F=0.0264, k=0.0579), "coral": dict(F=0.0545, k=0.062),
    "maze": dict(F=0.026, k=0.055), "worm": dict(F=0.0186, k=0.0502),
    "turbulence": dict(F=0.022, k=0.051),
}
DEEP_SEEDS = (1, 7, 11, 17)
DEEP_GRID = 460
DEEP_STEPS = 720
DEEP_SRC = "discovery/needle_src"


def sources():
    out = []
    for grp in ("mandalax", "animhunt", os.path.basename(DEEP_SRC)):
        d0 = DEEP_SRC if grp == os.path.basename(DEEP_SRC) else f"discovery/{grp}"
        for f in sorted(glob.glob(f"{d0}/*.npz")):
            d = np.load(f)
            if "V" not in d:
                continue
            V = np.asarray(d["V"], np.float32)
            V = V / (V.max() + 1e-6)
            base = os.path.basename(f).replace("src_", "").replace(".npz", "")
            sid = f"{grp[:4]}_{base}"
            reg = str(d["regime"]) if "regime" in d else "gs"
            out.append(dict(id=sid, path=f, grid=V.shape[0], V=V, regime=reg))
    return out


def best_params(src, K=360, n1s=N1, n2s=N2, octss=OCTS):
    kal = MX.Kal(K, src["grid"])
    best = None
    for n1 in n1s:
        for n2 in n2s:
            if n2 >= n1:
                continue
            for octs in octss:
                sc = MX.score(MX.compound(kal, src["V"], n1, n2, octs))
                if best is None or sc > best[0]:
                    best = (sc, n1, n2, octs)
    return best


def evolve_new():
    """Fresh, finer reaction-diffusion sources in the regimes the first sweep
    rewarded — bigger grid = finer lace at large fold radius."""
    os.makedirs(DEEP_SRC, exist_ok=True)
    made = 0
    for reg, kw in DEEP_REGIMES.items():
        for seed in DEEP_SEEDS:
            out = f"{DEEP_SRC}/src_{reg}{seed}.npz"
            if os.path.exists(out):
                continue
            V = MX.evolve_scatter(kw, DEEP_GRID, DEEP_STEPS, seed)
            np.savez_compressed(out, V=V.astype(np.float16), regime=reg, grid=DEEP_GRID, seed=seed)
            made += 1
            print(f"  evolved {reg} s{seed} @{DEEP_GRID}")
    print(f"new sources: {made} (cache {DEEP_SRC})")


def render_tile(src, n1, n2, octs, pal, K):
    rgb = MX.colorize(MX.compound(MX.Kal(K, src["grid"]), src["V"], n1, n2, octs), pal)
    return Image.fromarray(rgb)


def sweep():
    srcs = sources()
    print(f"scoring {len(srcs)} sources x {len(N1)*len(N2)*len(OCTS)} symmetries ...")
    ranked = []
    for i, s in enumerate(srcs):
        sc, n1, n2, octs = best_params(s)
        ranked.append(dict(id=s["id"], regime=s["regime"], grid=s["grid"],
                           n1=n1, n2=n2, octs=octs, score=round(float(sc), 4)))
        if i % 10 == 0:
            print(f"  {i}/{len(srcs)}")
    ranked.sort(key=lambda r: -r["score"])
    json.dump({"ranked": ranked}, open(RANK, "w"), indent=2)
    by = {s["id"]: s for s in srcs}

    top = ranked[:48]
    cols, cell = 8, 320
    rows = (len(top) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell, rows * cell), (6, 7, 11))
    d = ImageDraw.Draw(sheet)
    fb, fm = ImageFont.truetype(FB, 22), ImageFont.truetype(FM, 17)
    for i, r in enumerate(top):
        pal = PAL_CYCLE[i % len(PAL_CYCLE)]
        tile = render_tile(by[r["id"]], r["n1"], r["n2"], r["octs"], pal, K=300).resize((cell - 8, cell - 8), Image.LANCZOS)
        x, y = (i % cols) * cell + 4, (i // cols) * cell + 4
        sheet.paste(tile, (x, y))
        d.text((x + 6, y + 4), f"#{i+1}", font=fb, fill=(245, 240, 220))
        d.text((x + 6, y + cell - 30), f"{r['id']} {r['n1']}x{r['n2']}o{r['octs']}", font=fm, fill=(180, 235, 230))
        d.text((x + cell - 78, y + 4), f"{r['score']:.3f}", font=fm, fill=(245, 220, 150))
    sheet.save("/tmp/needle_sheet.png")
    print(f"\nTOP 12:")
    for i, r in enumerate(top[:12]):
        print(f"  #{i+1:2d} {r['id']:10s} {r['regime']:10s} {r['n1']}x{r['n2']} o{r['octs']}  score={r['score']}")
    print("\ncontact sheet -> /tmp/needle_sheet.png   ranking -> " + RANK)


def render(ids):
    ranked = {r["id"]: r for r in json.load(open(RANK))["ranked"]}
    by = {s["id"]: s for s in sources()}
    os.makedirs("media/needles", exist_ok=True)
    fallback = ["nebula", "fire", "ice", "amethyst", "emerald", "aqua", "rose", "ember"]
    paths = []
    for i, spec in enumerate(ids):
        sid, _, pal = spec.partition(":")          # "id" or "id:palette"
        pal = pal or fallback[i % len(fallback)]
        r = ranked[sid]
        img = render_tile(by[sid], r["n1"], r["n2"], r["octs"], pal, K=2160)
        out = f"media/needles/needle_{i:02d}_{sid}_{pal}.jpg"
        img.save(out, quality=94)
        paths.append(out)
        print(f"  #{i} {sid} {r['n1']}x{r['n2']}o{r['octs']} {pal} score={r['score']} -> {out}")
    print(f"DONE — {len(ids)} needles @2160 -> media/needles/")
    return paths


def deep():
    """Dig deeper: evolve finer fresh sources in the winning regimes, then sweep
    a far wider symmetry space (fold to 48, four octaves) over EVERY source."""
    evolve_new()
    srcs = sources()
    combos = sum(1 for n1 in DEEP_N1 for n2 in DEEP_N2 for o in DEEP_OCTS if n2 < n1)
    print(f"deep sweep: {len(srcs)} sources x {combos} symmetries ...")
    ranked = []
    for i, s in enumerate(srcs):
        sc, n1, n2, octs = best_params(s, K=400, n1s=DEEP_N1, n2s=DEEP_N2, octss=DEEP_OCTS)
        ranked.append(dict(id=s["id"], regime=s["regime"], grid=s["grid"],
                           n1=n1, n2=n2, octs=octs, score=round(float(sc), 4)))
        if i % 10 == 0:
            print(f"  {i}/{len(srcs)}")
    ranked.sort(key=lambda r: -r["score"])
    json.dump({"ranked": ranked}, open(DEEP_RANK, "w"), indent=2)
    by = {s["id"]: s for s in srcs}
    top = ranked[:48]
    cols, cell = 8, 320
    rows = (len(top) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell, rows * cell), (6, 7, 11))
    d = ImageDraw.Draw(sheet)
    fb, fm = ImageFont.truetype(FB, 22), ImageFont.truetype(FM, 16)
    for i, r in enumerate(top):
        pal = PAL_CYCLE[i % len(PAL_CYCLE)]
        tile = render_tile(by[r["id"]], r["n1"], r["n2"], r["octs"], pal, K=300).resize((cell - 8, cell - 8), Image.LANCZOS)
        x, y = (i % cols) * cell + 4, (i // cols) * cell + 4
        sheet.paste(tile, (x, y))
        d.text((x + 6, y + 4), f"#{i+1}", font=fb, fill=(245, 240, 220))
        d.text((x + 6, y + cell - 28), f"{r['id']} {r['n1']}x{r['n2']}o{r['octs']}", font=fm, fill=(180, 235, 230))
        d.text((x + cell - 74, y + 4), f"{r['score']:.3f}", font=fm, fill=(245, 220, 150))
    sheet.save("/tmp/needle_deep_sheet.png")
    print("\nDEEP TOP 12:")
    for i, r in enumerate(top[:12]):
        print(f"  #{i+1:2d} {r['id']:14s} {r['regime']:10s} {r['n1']}x{r['n2']} o{r['octs']}  score={r['score']}")
    print(f"\nprev ceiling 0.114 -> deep best {top[0]['score']}")
    print("contact sheet -> /tmp/needle_deep_sheet.png   ranking -> " + DEEP_RANK)


# ── relit spinning medallion videos ──────────────────────────────────────────
def _writer(path, size):
    wr = imageio_ffmpeg.write_frames(path, (size, size), fps=FPS, codec="libx264",
        pix_fmt_in="rgb24", pix_fmt_out="yuv420p", macro_block_size=2,
        output_params=["-crf", "16", "-preset", "medium"])
    wr.send(None)
    return wr


def _rank_lookup():
    d = {}
    for f in (DEEP_RANK, RANK):
        if os.path.exists(f):
            for r in json.load(open(f))["ranked"]:
                d.setdefault(r["id"], r)
    return d


def video_one(src, r, pal, out, dur=8, size=1080, K=1160):
    """Carve the mandala as a heightfield, spin it a seamless 360° under a fixed
    light → a relit metal medallion."""
    bump, shin, ks = METAL.get(pal, METAL["gold"])
    M = MX.compound(MX.Kal(K, src["grid"]), src["V"], r["n1"], r["n2"], r["octs"]).astype(np.float32)
    Mimg = Image.fromarray(M)                       # 'F' for sub-pixel rotation
    N = int(dur * FPS)
    wr = _writer(out, size)
    lf = ImageFont.truetype(FB, 30)
    for fi in range(N):
        p = fi / N
        Mr = np.asarray(Mimg.rotate(360.0 * p, resample=Image.BILINEAR), np.float32)
        zoom = 1.0 + 0.045 * np.sin(2 * np.pi * p)  # gentle breathing
        alb = R.colorize(Mr, pal, vmax=1.0)
        lit = R.relight(Mr, alb, az=0.7, el=0.5, bump=bump, shininess=shin, ks=ks)
        img = Image.fromarray(lit)
        if abs(zoom - 1.0) > 1e-3:
            c = K / 2.0; half = (K / zoom) / 2.0
            img = img.crop((c - half, c - half, c + half, c + half))
        img = img.resize((size, size), Image.BICUBIC).convert("RGB")
        d = ImageDraw.Draw(img)
        d.text((34, size - 54), f"{src['id']}  {r['n1']}×{r['n2']}  ·  {pal}", font=lf, fill=(236, 230, 214))
        af = min(1.0, (fi + 1) / 12.0, (N - fi) / 12.0)
        fr = np.asarray(img, np.uint8)
        if af < 0.999:
            fr = (fr.astype(np.float32) * af).astype(np.uint8)
        wr.send(np.ascontiguousarray(fr).tobytes())
    wr.close()
    print(f"  {src['id']} {r['n1']}x{r['n2']}o{r['octs']} {pal} -> {out}")


def video(specs, dur=8, size=1080, reel=True):
    ranks = _rank_lookup()
    by = {s["id"]: s for s in sources()}
    os.makedirs("media/needles", exist_ok=True)
    parts = []
    for sid_pal in specs:
        sid, _, pal = sid_pal.partition(":")
        pal = pal if pal in METAL else "gold"
        if sid not in by or sid not in ranks:
            print(f"  !! skip {sid} (no source/rank)")
            continue
        out = f"media/needles/spin_{sid}_{pal}.mp4"
        video_one(by[sid], ranks[sid], pal, out, dur=dur, size=size)
        parts.append(out)
    if reel and len(parts) > 1:
        _reel(parts, "media/needles/needle_reel.mp4", dur * len(parts))
    print(f"DONE — {len(parts)} medallion videos -> media/needles/")


def _reel(parts, out, total):
    tmp = "/tmp/needlereel"
    os.makedirs(tmp, exist_ok=True)
    lst = f"{tmp}/list.txt"
    open(lst, "w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in parts))
    silent = f"{tmp}/silent.mp4"
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", lst, "-c", "copy", silent], check=True)
    af = (f"[1:a][2:a]amix=inputs=2,volume=0.16,lowpass=f=420,"
          f"afade=t=in:st=0:d=1.5,afade=t=out:st={total-2:.1f}:d=2[a]")
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", silent,
                    "-f", "lavfi", "-t", str(total), "-i", "sine=frequency=98:sample_rate=44100",
                    "-f", "lavfi", "-t", str(total), "-i", "sine=frequency=146.83:sample_rate=44100",
                    "-filter_complex", af, "-map", "0:v", "-map", "[a]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest",
                    "-movflags", "+faststart", out], check=True)
    print(f"  reel -> {out} ({os.path.getsize(out)/1e6:.1f} MB)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--deep", action="store_true")
    ap.add_argument("--render", type=str, default="")
    ap.add_argument("--video", type=str, default="")
    ap.add_argument("--dur", type=float, default=8.0)
    a = ap.parse_args()
    if a.sweep:
        sweep()
    elif a.deep:
        deep()
    elif a.render:
        render([x.strip() for x in a.render.split(",") if x.strip()])
    elif a.video:
        video([x.strip() for x in a.video.split(",") if x.strip()], dur=a.dur)
    else:
        ap.error("need --sweep | --deep | --render ids | --video id:pal,...")


if __name__ == "__main__":
    main()
