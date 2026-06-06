"""GRAND SEARCH — a universal, rule-agnostic discovery search across ALL 17
rules in the REGISTRY, run at a LARGER grid for a bigger picture, then render
the champions BIG (full field, zoomed out).

Instead of only sweeping Gray-Scott F/k, this scores on the *rendered RGB*
(luminance + chroma) so the same complexity metric works for discrete soups,
Conway, Wolfram space-time diagrams, diverging vent/chirality maps and every
field rule. We keep the best-per-rule plus a global top, so every visualization
gets representation — then render each champion at a large grid.

  python3 tools/grand_search.py --worker 0/16     # one search shard
  python3 tools/grand_search.py --render          # curate + render BIG
  python3 tools/grand_search.py --curate          # just rebuild grand_top.json
"""
from __future__ import annotations
import argparse, glob, json, math, os, subprocess, sys, time, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_progress_video as MP            # ambient_bed
from cellauto.engine import Engine
from cellauto.rules import REGISTRY

FF = imageio_ffmpeg.get_ffmpeg_exe()
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
OUT = "discovery/grand"
TOP = "discovery/grand_top.json"
SEARCH_GRID = 140          # "more cells" — bigger picture than the old 80
GS = "abiogenesis-stage1-grayscott"

# crisp = nearest-neighbour upscale (discrete grids); else bicubic (fields)
CRISP = {"wolfram1d", "conway", "abiogenesis-stage0-soup", "natural-selection"}

# Human label for each rule (for the wall + heroes)
LABELS = {
    "wolfram1d": ("Elementary CA", "Wolfram 1D space-time"),
    "conway": ("Game of Life", "Conway B3/S23"),
    "abiogenesis-stage0-soup": ("Primordial Soup", "Miller-Urey molecules"),
    "natural-selection": ("Natural Selection", "competing species"),
    "abiogenesis-stage1-grayscott": ("Reaction-Diffusion", "Gray-Scott / Turing"),
    "abiogenesis-stage2-raf": ("Autocatalytic Sets", "Kauffman RAF"),
    "abiogenesis-stage3-vesicles": ("Vesicles", "fatty-acid membranes"),
    "abiogenesis-stage4-selection": ("Protocell Selection", "Eigen-Schuster hypercycle"),
    "abiogenesis-rna-world": ("RNA World", "Eigen quasispecies"),
    "abiogenesis-homochirality": ("Homochirality", "Frank symmetry breaking"),
    "abiogenesis-hydrothermal-vent": ("Hydrothermal Vent", "Lane-Martin proton gradient"),
    "abiogenesis-coacervate": ("Coacervates", "Cahn-Hilliard phase separation"),
    "abiogenesis-mineral-catalysis": ("Mineral Catalysis", "Ferris clay polymerization"),
    "abiogenesis-genetic-code": ("Genetic Code", "Woese code coevolution"),
    "abiogenesis-luca": ("LUCA", "ancestral core genome"),
    "abiogenesis-pipeline": ("The Pipeline", "soup -> LUCA, 5 stages"),
    "abiogenesis-pipeline-extended": ("Extended Pipeline", "12 stages"),
}

# Per-rule grid for the BIG render (slow rules capped to keep runtime sane).
RENDER_GRID = {
    "wolfram1d": 420, "conway": 380,
    "abiogenesis-stage0-soup": 300, "natural-selection": 300,
    "abiogenesis-stage1-grayscott": 360, "abiogenesis-stage3-vesicles": 320,
    "abiogenesis-homochirality": 320, "abiogenesis-hydrothermal-vent": 320,
    "abiogenesis-mineral-catalysis": 320, "abiogenesis-stage2-raf": 300,
    "abiogenesis-stage4-selection": 300, "abiogenesis-coacervate": 240,
    "abiogenesis-rna-world": 220, "abiogenesis-genetic-code": 240,
    "abiogenesis-luca": 240, "abiogenesis-pipeline": 300,
    "abiogenesis-pipeline-extended": 300,
}


# ----------------------------------------------------------------------------
# seeding
# ----------------------------------------------------------------------------
def scatter_gs(eng, grid, seed):
    """Scatter-seed a Gray-Scott field so the WHOLE frame comes alive."""
    rng = np.random.default_rng(seed)
    u = np.ones((grid, grid), np.float32); v = np.zeros((grid, grid), np.float32); r = max(3, grid // 28)
    for _ in range(grid // 11):
        cy = int(rng.integers(r, grid - r)); cx = int(rng.integers(r, grid - r))
        u[cy - r:cy + r, cx - r:cx + r] = 0.5; v[cy - r:cy + r, cx - r:cx + r] = 0.25
    v += rng.uniform(0, 0.02, (grid, grid)).astype(np.float32)
    eng.state.u = u; eng.state.v = np.clip(v, 0, 1)


def build_engine(rule, cfg, grid, seed):
    eng = Engine(width=grid, height=grid, rule=REGISTRY[rule](**cfg), seed=seed)
    # scatter-seed plain Gray-Scott (mitosis thrives from its central seed)
    if rule == GS and cfg.get("preset") != "mitosis" and hasattr(eng.state, "u"):
        scatter_gs(eng, grid, seed)
    return eng


# ----------------------------------------------------------------------------
# universal complexity score (on the rendered RGB)
# ----------------------------------------------------------------------------
def _entropy(f):
    h, _ = np.histogram(f, bins=24, range=(0.0, 1.0)); p = h / (h.sum() + 1e-12); p = p[p > 0]
    return float(-(p * np.log2(p)).sum() / np.log2(24))


def _frame_metrics(rgb):
    """rgb uint8 HxWx3 -> (luminance, entropy, edge, struct, chroma, coverage)."""
    f = rgb.astype(np.float32) / 255.0
    lum = 0.299 * f[..., 0] + 0.587 * f[..., 1] + 0.114 * f[..., 2]
    gx, gy = np.gradient(lum)
    edge = float(np.sqrt(gx * gx + gy * gy).mean())
    struct = float(lum.std())
    chroma = float(f.std(axis=2).mean())          # per-pixel spread across channels
    cover = float(((lum > 0.06) & (lum < 0.97)).mean())
    return lum, _entropy(lum), edge, struct, chroma, cover


def score_candidate(rule, cfg, seed, grid=SEARCH_GRID, warm=46, steps=210, sample=10):
    eng = build_engine(rule, cfg, grid, seed)
    for _ in range(warm):
        eng.step()
    rl = eng.rule
    ents, edges, structs, chromas, covers, motions = [], [], [], [], [], []
    prev = None; dead_run = 0
    for st in range(1, steps + 1):
        eng.step()
        if st % sample and st != steps:
            continue
        rgb = np.asarray(rl.render_rgb(eng.state), np.uint8)
        lum, ent, edge, struct, chroma, cover = _frame_metrics(rgb)
        ents.append(ent); edges.append(edge); structs.append(struct)
        chromas.append(chroma); covers.append(cover)
        motions.append(float(np.abs(lum - prev).mean()) if prev is not None else 0.0)
        prev = lum
        # early-exit a truly dead frozen run
        if struct < 8e-3 and motions[-1] < 6e-5:
            dead_run += 1
            if dead_run >= 3:
                break
        else:
            dead_run = 0
    n = len(structs)
    if n < 3:
        return None
    i0 = n // 2                                    # "sustained" = second half
    ent_m = float(np.mean(ents[i0:])); edge_m = float(np.mean(edges[i0:]))
    str_m = float(np.mean(structs[i0:])); chr_m = float(np.mean(chromas[i0:]))
    cov_m = float(np.mean(covers[i0:])); mot_m = float(np.mean(motions[i0:]))
    alive = float(np.mean([1.0 if (s > 6e-3 and m > 8e-5) else 0.0
                           for s, m in zip(structs, motions)]))
    cls = ("dead" if (str_m < 6e-3 and mot_m < 8e-5)
           else "static" if mot_m < 3e-4
           else "living" if mot_m < 6e-3 else "chaotic")
    # normalised, soft-capped components
    edge_n = min(edge_m / 0.060, 1.0)
    str_n = min(str_m / 0.220, 1.0)
    chr_n = min(chr_m / 0.180, 1.0)
    mot_n = 1.0 - math.exp(-mot_m / 0.004)
    cov_f = 0.45 + 0.55 * min(cov_m / 0.55, 1.0)   # reward a filled frame
    complexity = (0.28 * ent_m + 0.24 * edge_n + 0.20 * str_n
                  + 0.12 * chr_n + 0.16 * mot_n) * (0.35 + 0.65 * alive) * cov_f
    if cls == "dead":
        complexity *= 0.03
    elif cls == "static":
        complexity *= 0.55
    return {"rule": rule, "cfg": cfg, "seed": seed, "cls": cls,
            "score": round(complexity, 4), "ent": round(ent_m, 4),
            "edge": round(edge_m, 5), "struct": round(str_m, 4),
            "chroma": round(chr_m, 4), "cover": round(cov_m, 3),
            "motion": round(mot_m, 5), "alive": round(alive, 3)}


# ----------------------------------------------------------------------------
# candidate space across ALL rules
# ----------------------------------------------------------------------------
def candidates():
    C = []

    def add(rule, cfg, seeds, tag=None):
        for s in seeds:
            C.append({"rule": rule, "cfg": dict(cfg), "seed": int(s)})

    # --- Wolfram 1D: curated interesting elementary rules, 2 seeds each
    wrules = [18, 22, 26, 28, 30, 41, 45, 54, 57, 60, 62, 73, 75, 82, 86, 89, 90,
              99, 101, 105, 106, 109, 110, 120, 124, 126, 129, 135, 137, 146, 147,
              150, 151, 153, 161, 165, 169, 182, 183, 193, 195, 225]
    for r in wrules:
        add("wolfram1d", {"rule_number": r}, [1, 2])
    # --- Conway: density sweep x seeds
    for d in [0.10, 0.18, 0.25, 0.30, 0.38, 0.45, 0.55]:
        add("conway", {"initial_density": d}, [1, 2, 3])
    # --- Soup / natural selection
    for ls in [12, 25, 40, 60]:
        add("abiogenesis-stage0-soup", {"amoeba_lifespan": ls}, [1, 2])
    add("natural-selection", {}, [1, 2, 3])
    # --- Gray-Scott: F/k grid + seeds (scatter), plus presets
    Fs = [0.014, 0.018, 0.022, 0.026, 0.030, 0.034, 0.038, 0.042, 0.054, 0.062, 0.078]
    Ks = [0.045, 0.050, 0.055, 0.058, 0.061, 0.063, 0.065, 0.068]
    for F in Fs:
        for k in Ks:
            add(GS, {"F": F, "k": k}, [1, 2])
    for preset in ["spots", "stripes", "mitosis", "waves", "labyrinth"]:
        add(GS, {"preset": preset}, [1, 2])
    # --- RAF autocatalytic sets
    for ns in [6, 8, 12]:
        for nr in [12, 16, 24]:
            for ff in [0.3, 0.5]:
                add("abiogenesis-stage2-raf",
                    {"n_species": ns, "n_reactions": nr, "food_fraction": ff}, [1, 2])
    # --- Vesicles
    for cmc in [0.2, 0.3, 0.4]:
        for kb in [0.015, 0.025, 0.04]:
            for (F, k) in [(0.04, 0.06), (0.03, 0.057), (0.025, 0.055)]:
                add("abiogenesis-stage3-vesicles",
                    {"cmc_threshold": cmc, "kappa_bend": kb, "F": F, "k": k}, [1, 2])
    # --- Protocell selection
    for ns in [3, 4, 6]:
        for mr in [0.005, 0.02, 0.05]:
            for dyn in ["hypercycle", "proxy"]:
                add("abiogenesis-stage4-selection",
                    {"n_species": ns, "mutation_rate": mr, "dynamics": dyn}, [1, 2])
    # --- RNA world (error catastrophe sweep)
    for er in [0.005, 0.01, 0.02, 0.04, 0.06, 0.10]:
        for sup in [5, 10, 20]:
            add("abiogenesis-rna-world", {"error_rate": er, "superiority": sup}, [1, 2])
    # --- Homochirality
    for ka in [0.5, 1.0, 2.0]:
        for kc in [1.0, 2.0, 3.0]:
            for nz in [0.01, 0.03]:
                add("abiogenesis-homochirality",
                    {"k_auto": ka, "k_cross": kc, "noise": nz}, [1, 2])
    # --- Hydrothermal vent
    for va in [0.03, 0.05, 0.08]:
        for ks in [3, 6, 10]:
            for dec in [0.02, 0.04, 0.08]:
                add("abiogenesis-hydrothermal-vent",
                    {"vent_alkalinity": va, "k_synth": ks, "decay": dec}, [1])
    # --- Coacervates
    for kp in [0.2, 0.3, 0.5]:
        for mc in [-0.5, -0.4, -0.2, 0.0]:
            for nz in [0.2, 0.3]:
                add("abiogenesis-coacervate",
                    {"kappa": kp, "mean_composition": mc, "noise": nz}, [1])
    # --- Mineral catalysis
    for kc in [0.15, 0.25, 0.4]:
        for cp in [4, 9, 16]:
            for fd in [0.05, 0.08, 0.12]:
                add("abiogenesis-mineral-catalysis",
                    {"k_clay": kc, "clay_patches": cp, "feed": fd}, [1])
    # --- Genetic code
    for sm in [0.02, 0.04, 0.08]:
        for cm in [0.005, 0.01, 0.02]:
            for sf in [0.2, 0.35]:
                add("abiogenesis-genetic-code",
                    {"strand_mutation": sm, "code_mutation": cm, "seed_fraction": sf}, [1, 2])
    # --- LUCA
    for mr in [0.004, 0.008, 0.02]:
        for cp in [0.5, 0.7, 0.9]:
            for sf in [0.3, 0.4]:
                add("abiogenesis-luca",
                    {"mutation_rate": mr, "core_prevalence": cp, "seed_fraction": sf}, [1, 2])
    # --- Pipelines
    for sd in [40, 70]:
        add("abiogenesis-pipeline", {"stage_duration": sd}, [1, 2])
        add("abiogenesis-pipeline-extended", {"stage_duration": sd}, [1, 2])
    return C


# ----------------------------------------------------------------------------
# search worker
# ----------------------------------------------------------------------------
def worker(shard, nshards):
    allc = candidates()
    # interleave by index so slow rules spread evenly across shards
    mine = [c for i, c in enumerate(allc) if i % nshards == shard]
    os.makedirs(OUT, exist_ok=True)
    out = f"{OUT}/g_{shard:02d}.jsonl"
    t0, kept = time.time(), 0
    with open(out, "w") as fh:
        for j, c in enumerate(mine):
            try:
                rec = score_candidate(c["rule"], c["cfg"], c["seed"])
            except Exception as e:  # noqa: BLE001
                rec = {"rule": c["rule"], "cfg": c["cfg"], "seed": c["seed"],
                       "cls": "error", "score": 0.0, "err": f"{type(e).__name__}: {e}"}
            if rec:
                fh.write(json.dumps(rec) + "\n"); kept += 1
            if (j + 1) % 15 == 0:
                fh.flush()
                print(f"shard {shard}: {j+1}/{len(mine)} ({time.time()-t0:.0f}s)", flush=True)
    print(f"DONE shard {shard}: {kept} recs -> {out} "
          f"({time.time()-t0:.0f}s) [space={len(allc)}, mine={len(mine)}]", flush=True)


# ----------------------------------------------------------------------------
# curate
# ----------------------------------------------------------------------------
def load_all():
    rs = []
    for fp in glob.glob(f"{OUT}/g_*.jsonl"):
        for ln in open(fp):
            ln = ln.strip()
            if ln:
                try:
                    rs.append(json.loads(ln))
                except json.JSONDecodeError:
                    pass
    return rs


def curate():
    rs = load_all()
    good = [r for r in rs if r.get("cls") in ("living", "chaotic", "static")]
    good.sort(key=lambda r: -r.get("score", 0))
    # best per rule
    best_per_rule = {}
    for r in good:
        best_per_rule.setdefault(r["rule"], r)
    per_rule = sorted(best_per_rule.values(), key=lambda r: -r["score"])
    # global top, deduped by rule so the reel is diverse (max 2 per rule)
    seen = {}; global_top = []
    for r in good:
        c = seen.get(r["rule"], 0)
        if c < 2:
            global_top.append(r); seen[r["rule"]] = c + 1
        if len(global_top) >= 24:
            break
    out = {"searched": len(rs), "alive": len(good),
           "per_rule": per_rule, "global_top": global_top}
    os.makedirs(os.path.dirname(TOP), exist_ok=True)
    json.dump(out, open(TOP, "w"), indent=2)
    print(f"searched={len(rs)} alive={len(good)} rules_covered={len(per_rule)}")
    for r in per_rule:
        nm = LABELS.get(r["rule"], (r["rule"], ""))[0]
        print(f"  {r['score']:.3f} {r['cls']:7} {nm:22} {r['rule']}  cfg={r['cfg']}")
    return out


# ----------------------------------------------------------------------------
# BIG rendering
# ----------------------------------------------------------------------------
def _fade(arr, fi, n, k=10):
    a = min(1.0, (fi + 1) / k, (n - fi) / k)
    return arr if a >= 0.999 else (arr.astype(np.float32) * a).astype(np.uint8)


def render_hero(rec, out, size=1080, dur=11, fps=30):
    rule = rec["rule"]; cfg = rec["cfg"]; grid = RENDER_GRID.get(rule, 300)
    crisp = rule in CRISP
    eng = build_engine(rule, cfg, grid, rec["seed"]); rl = eng.rule
    # warmup so we open on a mature pattern
    warm = grid if rule == "wolfram1d" else 90 if rule == "conway" else 60
    for _ in range(warm):
        eng.step()
    N = dur * fps
    wr = imageio_ffmpeg.write_frames(out, (size, size), fps=fps, codec="libx264",
        pix_fmt_in="rgb24", pix_fmt_out="yuv420p", macro_block_size=2,
        output_params=["-crf", "21", "-preset", "medium"])
    wr.send(None)
    name, sub = LABELS.get(rule, (rule, ""))
    cfg_str = ", ".join(f"{k}={v}" for k, v in cfg.items()) or "defaults"
    lf = ImageFont.truetype(FB, 40); sf = ImageFont.truetype(FR, 24); tf = ImageFont.truetype(FR, 22)
    for fi in range(N):
        eng.step()
        rgb = np.asarray(rl.render_rgb(eng.state), np.uint8)
        img = Image.fromarray(rgb).resize((size, size),
            Image.NEAREST if crisp else Image.BICUBIC).convert("RGB")
        d = ImageDraw.Draw(img)
        d.rectangle([0, size - 104, size, size], fill=(6, 8, 12))
        d.text((30, size - 96), name, font=lf, fill=(244, 248, 252))
        d.text((32, size - 48), sub, font=sf, fill=(170, 196, 212))
        d.text((size - tf.getlength(cfg_str) - 26, size - 44), cfg_str, font=tf, fill=(150, 170, 190))
        d.text((30, 26), f"score {rec['score']:.2f} · {rec['cls']}", font=tf, fill=(150, 200, 200))
        wr.send(np.ascontiguousarray(_fade(np.asarray(img, np.uint8), fi, N)).tobytes())
    wr.close()
    print(f"  hero -> {out}  ({os.path.getsize(out)/1e6:.1f} MB)")


def render_wall(per_rule, out, dur=15, fps=30, cell=300, cols=4):
    tiles = per_rule[:16]
    rows = math.ceil(len(tiles) / cols)
    W, H = cols * cell, rows * cell
    engs = []
    for r in tiles:
        g = min(RENDER_GRID.get(r["rule"], 300), 220)   # smaller per-tile
        e = build_engine(r["rule"], r["cfg"], g, r["seed"])
        warm = g if r["rule"] == "wolfram1d" else 55
        for _ in range(warm):
            e.step()
        engs.append((e, r["rule"] in CRISP, r))
    N = dur * fps
    wr = imageio_ffmpeg.write_frames(out, (W, H), fps=fps, codec="libx264",
        pix_fmt_in="rgb24", pix_fmt_out="yuv420p", macro_block_size=2,
        output_params=["-crf", "22", "-preset", "medium"])
    wr.send(None)
    nf = ImageFont.truetype(FB, 20)
    for fi in range(N):
        canvas = Image.new("RGB", (W, H), (5, 7, 11))
        for i, (e, crisp, r) in enumerate(engs):
            e.step()
            rgb = np.asarray(e.rule.render_rgb(e.state), np.uint8)
            til = Image.fromarray(rgb).resize((cell, cell),
                Image.NEAREST if crisp else Image.BICUBIC).convert("RGB")
            d = ImageDraw.Draw(til)
            d.rectangle([0, cell - 30, cell, cell], fill=(0, 0, 0))
            d.text((8, cell - 26), LABELS.get(r["rule"], (r["rule"], ""))[0], font=nf, fill=(235, 240, 248))
            canvas.paste(til, ((i % cols) * cell, (i // cols) * cell))
        wr.send(np.ascontiguousarray(_fade(np.asarray(canvas, np.uint8), fi, N)).tobytes())
    wr.close()
    print(f"  wall -> {out}  ({os.path.getsize(out)/1e6:.1f} MB)")


def add_bed(silent, final):
    import imageio_ffmpeg as iio
    # duration via ffprobe-ish: count is unknown, just make a long bed and -shortest
    bed_path = "/tmp/grand_bed.wav"; sr = 22050
    bed = MP.ambient_bed(sr * 240, sr)            # up to 4 min, -shortest trims
    mix = np.clip(bed * 0.15 * 32767, -32768, 32767).astype(np.int16)
    with wave.open(bed_path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(mix.tobytes())
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", silent, "-i", bed_path,
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "150k", "-shortest",
                    "-movflags", "+faststart", final], check=True)


def _hero_name(i, rule):
    nm = rule.replace("abiogenesis-", "").replace("stage", "s")
    return f"media/grand/hero_{i:02d}_{nm}.mp4"


def render_one_hero(idx):
    """Render per_rule[idx] champion BIG (parallelisable)."""
    per_rule = json.load(open(TOP))["per_rule"]
    if idx >= len(per_rule):
        print(f"no hero {idx} (only {len(per_rule)})"); return
    r = per_rule[idx]
    os.makedirs("media/grand", exist_ok=True)
    render_hero(r, _hero_name(idx, r["rule"]))


def render_wall_cmd():
    per_rule = json.load(open(TOP))["per_rule"]
    os.makedirs("media/grand", exist_ok=True)
    wall_silent = "/tmp/grand_wall.mp4"
    render_wall(per_rule, wall_silent)
    add_bed(wall_silent, "media/grand/everything_wall.mp4")
    print(f"DONE wall -> media/grand/everything_wall.mp4 "
          f"({os.path.getsize('media/grand/everything_wall.mp4')/1e6:.1f} MB)")


def assemble():
    """Concat the rendered heroes into a reel (trim each), add bed, make a GIF."""
    heroes = sorted(glob.glob("media/grand/hero_*.mp4"))
    if not heroes:
        print("no heroes to assemble"); return
    # trim each hero to a 7s reel clip so the reel stays watchable
    clips = []
    for h in heroes:
        c = f"/tmp/reel_{os.path.basename(h)}"
        subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", h,
                        "-t", "7", "-c", "copy", c], check=True)
        clips.append(os.path.abspath(c))
    lst = "/tmp/grand_reel.txt"
    open(lst, "w").write("".join(f"file '{c}'\n" for c in clips))
    reel_silent = "/tmp/grand_reel_silent.mp4"
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", lst, "-c", "copy", reel_silent], check=True)
    add_bed(reel_silent, "media/grand/grand_reel.mp4")
    # GIF from the top-scoring hero (first in sorted per_rule order = hero_00)
    top_hero = heroes[0]
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", top_hero,
                    "-vf", "fps=12,scale=460:-1:flags=lanczos,palettegen=max_colors=96:stats_mode=diff",
                    "/tmp/grand_pal.png"], check=True)
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", top_hero,
                    "-i", "/tmp/grand_pal.png",
                    "-lavfi", "fps=12,scale=460:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=4",
                    "-loop", "0", "media/grand/grand_hero.gif"], check=True)
    print(f"DONE reel ({os.path.getsize('media/grand/grand_reel.mp4')/1e6:.1f} MB) + gif "
          f"from {len(heroes)} heroes")


def render():
    """Sequential fallback: wall + all heroes + reel + gif."""
    data = curate()
    render_wall_cmd()
    for i in range(len(data["per_rule"])):
        render_one_hero(i)
    assemble()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--worker", default="")
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--curate", action="store_true")
    ap.add_argument("--wall", action="store_true")
    ap.add_argument("--hero", type=int, default=-1)
    ap.add_argument("--assemble", action="store_true")
    a = ap.parse_args()
    if a.render:
        render()
    elif a.curate:
        curate()
    elif a.wall:
        render_wall_cmd()
    elif a.hero >= 0:
        render_one_hero(a.hero)
    elif a.assemble:
        assemble()
    elif a.worker:
        sh, ns = (int(x) for x in a.worker.split("/")); worker(sh, ns)
    else:
        ap.error("need --worker i/N, --curate, --wall, --hero N, --assemble, or --render")


if __name__ == "__main__":
    main()
