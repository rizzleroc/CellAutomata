"""The Reliquary — a 5-day release calendar of 25 story-driven vertical videos.

A narrative arc from chaos to order, one chapter per day, five episodes each:

  Day 1  GENESIS      pattern born from noise              (evolution loops)
  Day 2  THE LAWS     each reaction-diffusion law a being  (evolution loops)
  Day 3  SYMMETRY     folding chaos into mandalas          (kaleidoscope loops)
  Day 4  THE RELICS   mandalas cast as carved medallions   (relit spins)
  Day 5  THE RELIQUARY the whole journey, then the vault   (transformation arcs)

Each episode is 9:16 (1080x1920): a title card, the animated specimen, timed
caption beats that tell its story, and a per-day ambient drone.

  python3 tools/schedule.py --one d1e1     # smoke-test one episode
  python3 tools/schedule.py --all          # render all 25 + poster + sizzle + calendar
"""
from __future__ import annotations
import argparse, glob, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mandala_x as MX
import relit as R
import needle as NE
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
OUT = "media/schedule"
W, H = 1080, 1920
DISC = 960
DX, DY = (W - DISC) // 2, 320          # disc occupies y 320..1280
FPS = 30
BG = (8, 9, 14)
GOLD = (214, 188, 120)
INK = (236, 232, 222)
DIM = (150, 156, 168)
METAL = NE.METAL                        # bump/shininess/ks per metal
# per-day ambient drone (root, fifth) Hz — descends then resolves
DRONE = {1: (73.42, 110.0), 2: (82.41, 123.47), 3: (98.0, 146.83),
         4: (110.0, 164.81), 5: (73.42, 110.0)}

# circular disc alpha (soft edge) for petri-dish framing of raw evolution
_yy, _xx = np.mgrid[0:DISC, 0:DISC]
_rr = np.hypot(_xx - DISC / 2, _yy - DISC / 2) / (DISC / 2)
DISC_A = np.clip((0.985 - _rr) / 0.04, 0, 1).astype(np.float32)


def _font(sz, bold=True):
    return ImageFont.truetype(FB if bold else FR, sz)


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


def _spaced(s):
    return "  ".join(s.upper())


def _text(canvas, xy, s, font, fill, a=1.0, anchor="mm", spacing=10):
    """Alpha-aware centered text on an RGBA canvas."""
    if a <= 0.01:
        return
    ov = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    col = (fill[0], fill[1], fill[2], int(255 * min(1.0, a)))
    if "\n" in s:
        d.multiline_text(xy, s, font=font, fill=col, anchor=anchor, align="center", spacing=spacing)
    else:
        d.text(xy, s, font=font, fill=col, anchor=anchor)
    canvas.alpha_composite(ov)


# ── engines: each returns N disc frames (DISC x DISC x3 uint8) ────────────────
def _col(v, pal, hi, gamma=0.82):
    f = np.clip(v / (hi + 1e-6), 0, 1) ** gamma
    return MX.PAL[pal][(f * 255).astype(np.uint8)]


def frames_evolve(kw, grid, seed, N, pal, steps=720):
    eng = MX.Engine(width=grid, height=grid, rule=MX.REGISTRY[MX.RULE](**kw), seed=seed)
    rng = np.random.default_rng(seed)
    u = np.ones((grid, grid), np.float32); v = np.zeros((grid, grid), np.float32); r = 5
    for _ in range(grid // 8):
        cy = int(rng.integers(r, grid - r)); cx = int(rng.integers(r, grid - r))
        u[cy - r:cy + r, cx - r:cx + r] = 0.5; v[cy - r:cy + r, cx - r:cx + r] = 0.25
    v += rng.uniform(0, 0.02, (grid, grid)).astype(np.float32)
    eng.state.u = u; eng.state.v = np.clip(v, 0, 1)
    caps = [int(round((i / (N - 1)) ** 1.25 * steps)) for i in range(N)]  # ease-in emergence
    snaps, cur = [], 0
    for cap in caps:
        while cur < cap:
            eng.step(); cur += 1
        snaps.append(np.asarray(eng.state.v, np.float32).copy())
    hi = float(np.percentile(snaps[-1][snaps[-1] > 0.02], 99.5)) if (snaps[-1] > 0.02).any() else 1.0
    out = []
    for s in snaps:
        rgb = _col(s, pal, hi)
        a = (DISC_A if grid == DISC else np.asarray(Image.fromarray((DISC_A * 255).astype(np.uint8)).resize((DISC, DISC))).astype(np.float32) / 255)
        im = Image.fromarray(rgb).resize((DISC, DISC), Image.BICUBIC)
        arr = (np.asarray(im, np.float32) * a[..., None]).astype(np.uint8)
        out.append(arr)
    return out


def frames_kal(V, n1, n2, octs, N, pal, K=DISC):
    kal = MX.Kal(K, V.shape[0])
    big = Image.fromarray(MX.colorize(MX.compound(kal, V, n1, n2, octs), pal))
    out = []
    for fi in range(N):
        p = fi / N
        im = big.rotate(360.0 * p, resample=Image.BICUBIC)
        z = 1.0 + 0.05 * math.sin(2 * math.pi * p); c = K / 2.0; half = (K / z) / 2.0
        im = im.crop((c - half, c - half, c + half, c + half)).resize((DISC, DISC), Image.BICUBIC)
        out.append(np.asarray(im.convert("RGB"), np.uint8))
    return out


def frames_relit(V, n1, n2, octs, N, metal, K=1040):
    bump, shin, ks = METAL.get(metal, METAL["gold"])
    M = MX.compound(MX.Kal(K, V.shape[0]), V, n1, n2, octs).astype(np.float32)
    Mimg = Image.fromarray(M)
    out = []
    for fi in range(N):
        p = fi / N
        Mr = np.asarray(Mimg.rotate(360.0 * p, resample=Image.BILINEAR), np.float32)
        alb = R.colorize(Mr, metal, vmax=1.0)
        lit = R.relight(Mr, alb, az=0.7, el=0.5, bump=bump, shininess=shin, ks=ks)
        im = Image.fromarray(lit)
        z = 1.0 + 0.045 * math.sin(2 * math.pi * p); c = K / 2.0; half = (K / z) / 2.0
        im = im.crop((c - half, c - half, c + half, c + half)).resize((DISC, DISC), Image.BICUBIC)
        out.append(np.asarray(im.convert("RGB"), np.uint8))
    return out


def frames_arc(V, n1, n2, octs, N, pal, metal):
    """Transformation: a flat colored mandala dissolves into a relit medallion."""
    k = frames_kal(V, n1, n2, octs, N, pal)
    r = frames_relit(V, n1, n2, octs, N, metal)
    t0, t1 = int(0.42 * N), int(0.58 * N)
    out = []
    for fi in range(N):
        if fi <= t0:
            out.append(k[fi])
        elif fi >= t1:
            out.append(r[fi])
        else:
            w = (fi - t0) / (t1 - t0)
            out.append((k[fi].astype(np.float32) * (1 - w) + r[fi].astype(np.float32) * w).astype(np.uint8))
    return out


def frames_finale(V, kw, seed, N, pal, metal):
    """The journey in one breath: noise -> growth -> mandala -> medallion."""
    a, b, c = int(0.26 * N), int(0.52 * N), N
    ev = frames_evolve(kw, 240, seed, a, pal, steps=560)
    ka = frames_kal(V, 40, 7, 2, b - a, pal)
    re = frames_relit(V, 40, 7, 2, c - b, metal)
    return ev + ka + re


# ── episode schedule ──────────────────────────────────────────────────────────
_SRC_CACHE = {}


def _src(sid):
    if not _SRC_CACHE:
        _SRC_CACHE.update({s["id"]: s["V"] for s in NE.sources()})
    return _SRC_CACHE[sid]


SCHEDULE = [
    # ── DAY 1 · GENESIS ── pattern born from noise (evolution) ──
    dict(id="d1e1", day=1, chapter="GENESIS", title="First Light",
         logline="Out of uniform nothing, the first instability.", eng="evolve",
         kw=dict(F=0.0545, k=0.062), seed=1, pal="nebula", dur=10,
         beats=[(0.05, "A flat field. Perfectly still."), (0.4, "Then — a flaw. A seed that will not settle."),
                (0.75, "From one defect, a world begins.")]),
    dict(id="d1e2", day=1, chapter="GENESIS", title="The Seeding",
         logline="Scattered sparks compete for the medium.", eng="evolve",
         kw=dict(F=0.0264, k=0.0579), seed=7, pal="fire", dur=10,
         beats=[(0.05, "Dozens of seeds, cast at random."), (0.45, "Each devours the substrate around it."),
                (0.78, "The strongest geometries survive.")]),
    dict(id="d1e3", day=1, chapter="GENESIS", title="First Contact",
         logline="Where two fronts meet, structure is decided.", eng="evolve",
         kw=dict(F=0.0186, k=0.0502), seed=3, pal="aqua", dur=10,
         beats=[(0.05, "Growing fronts race outward."), (0.45, "They collide — and negotiate."),
                (0.78, "Borders freeze into filigree.")]),
    dict(id="d1e4", day=1, chapter="GENESIS", title="Replication",
         logline="The pattern learns to copy itself.", eng="evolve",
         kw=dict(F=0.026, k=0.055), seed=1, pal="emerald", dur=10,
         beats=[(0.05, "A corridor splits in two."), (0.45, "Two becomes four. Four, a labyrinth."),
                (0.78, "Information, endlessly xeroxed.")]),
    dict(id="d1e5", day=1, chapter="GENESIS", title="The Living Skin",
         logline="A surface that never stops moving.", eng="evolve",
         kw=dict(F=0.022, k=0.051), seed=7, pal="ember", dur=10,
         beats=[(0.05, "No final state — only flux."), (0.45, "Turbulence, held just shy of chaos."),
                (0.78, "Alive, in the only sense that matters.")]),
    # ── DAY 2 · THE LAWS ── each regime a character ──
    dict(id="d2e1", day=2, chapter="THE LAWS", title="Chaos",
         logline="Law I — feed 0.018, kill 0.050.", eng="evolve",
         kw=dict(F=0.018, k=0.050), seed=1, pal="nebula", dur=9,
         beats=[(0.06, "The oldest law. The least patient."), (0.5, "It builds only to tear down."),
                (0.8, "Order here is always temporary.")]),
    dict(id="d2e2", day=2, chapter="THE LAWS", title="The Labyrinth",
         logline="Law II — the maze that solves itself.", eng="evolve",
         kw=dict(preset="labyrinth"), seed=1, pal="ice", dur=9,
         beats=[(0.06, "Every wall an exact width apart."), (0.5, "No planner. No blueprint."),
                (0.8, "The rule alone draws the maze.")]),
    dict(id="d2e3", day=2, chapter="THE LAWS", title="The Coral",
         logline="Law III — feed 0.0545, kill 0.062.", eng="evolve",
         kw=dict(F=0.0545, k=0.062), seed=7, pal="fire", dur=9,
         beats=[(0.06, "Branch, branch, and branch again."), (0.5, "It grows toward what it lacks."),
                (0.8, "A reef with no ocean.")]),
    dict(id="d2e4", day=2, chapter="THE LAWS", title="The Plasma",
         logline="Law IV — feed 0.0264, kill 0.0579.", eng="evolve",
         kw=dict(F=0.0264, k=0.0579), seed=7, pal="amethyst", dur=9,
         beats=[(0.06, "Dense. Granular. Restless."), (0.5, "A thousand cells, none at rest."),
                (0.8, "The richest law we found.")]),
    dict(id="d2e5", day=2, chapter="THE LAWS", title="The Worm",
         logline="Law V — feed 0.0186, kill 0.0502.", eng="evolve",
         kw=dict(F=0.0186, k=0.0502), seed=3, pal="aqua", dur=9,
         beats=[(0.06, "Long solitons that crawl."), (0.5, "They avoid themselves, and each other."),
                (0.8, "Life, rehearsed in chemistry.")]),
    # ── DAY 3 · SYMMETRY ── folding chaos into mandalas (kaleidoscope) ──
    dict(id="d3e1", day=3, chapter="SYMMETRY", title="Two Mirrors",
         logline="The simplest fold. Chaos, halved and matched.", eng="kal",
         sid="mand_14", n1=6, n2=3, octs=1, pal="nebula", dur=10,
         beats=[(0.06, "Take one chaotic field."), (0.45, "Fold it across a handful of mirrors."),
                (0.78, "Noise discovers it was a mandala.")]),
    dict(id="d3e2", day=3, chapter="SYMMETRY", title="The Bloom",
         logline="Eight petals from a reef of static.", eng="kal",
         sid="mand_06", n1=8, n2=5, octs=2, pal="fire", dur=10,
         beats=[(0.06, "Two fold-orders interfere."), (0.45, "Their beat-pattern becomes petals."),
                (0.78, "A flower no garden could grow.")]),
    dict(id="d3e3", day=3, chapter="SYMMETRY", title="Twelvefold Gate",
         logline="Where the octaves nest, depth appears.", eng="kal",
         sid="mand_13", n1=12, n2=6, octs=1, pal="aqua", dur=10,
         beats=[(0.06, "Twelve gates around one center."), (0.45, "Each ring echoes the last, smaller."),
                (0.78, "A mandala inside a mandala.")]),
    dict(id="d3e4", day=3, chapter="SYMMETRY", title="The Rose Window",
         logline="Twenty-four arcs of woven coral.", eng="kal",
         sid="need_coral7", n1=24, n2=6, octs=1, pal="emerald", dur=10,
         beats=[(0.06, "The coral law, folded high."), (0.45, "Stone lace, like a cathedral's glass."),
                (0.78, "Built by a rule, not a mason.")]),
    dict(id="d3e5", day=3, chapter="SYMMETRY", title="Infinite Regress",
         logline="Forty mirrors, and the eye falls in.", eng="kal",
         sid="need_plasma11", n1=40, n2=7, octs=2, pal="amethyst", dur=10,
         beats=[(0.06, "The deepest fold we dared."), (0.45, "Detail all the way down."),
                (0.78, "The center keeps its secret.")]),
    # ── DAY 4 · THE RELICS ── mandalas cast as carved medallions (relit) ──
    dict(id="d4e1", day=4, chapter="THE RELICS", title="Cast in Frost",
         logline="The labyrinth, struck in cold silver.", eng="relit",
         sid="need_maze7", metal="ice", dur=10,
         beats=[(0.06, "Read the pattern as a height."), (0.45, "Light it from a single sun."),
                (0.78, "Flat math, made tactile.")]),
    dict(id="d4e2", day=4, chapter="THE RELICS", title="The Jade Disc",
         logline="Coral relief carved into green stone.", eng="relit",
         sid="need_coral7", metal="jade", dur=10,
         beats=[(0.06, "Every ridge throws a shadow."), (0.45, "Every hollow holds the dark."),
                (0.78, "An heirloom that never existed.")]),
    dict(id="d4e3", day=4, chapter="THE RELICS", title="The Gold Coin",
         logline="The deepest needle, stamped in gold.", eng="relit",
         sid="need_plasma7", metal="gold", dur=11,
         beats=[(0.06, "Forty-eight-fold. Our richest find."), (0.45, "A thousand beads of raised gold."),
                (0.8, "The prize of the whole search.")]),
    dict(id="d4e4", day=4, chapter="THE RELICS", title="Amethyst Seal",
         logline="A gemstone pressed from plasma.", eng="relit",
         sid="need_plasma11", metal="amethyst", dur=10,
         beats=[(0.06, "Granular fire, set in violet."), (0.45, "It turns, and the highlights run."),
                (0.78, "Pressed once, kept forever.")]),
    dict(id="d4e5", day=4, chapter="THE RELICS", title="Copper Relic",
         logline="The coral law, aged into bronze.", eng="relit",
         sid="need_coral1", metal="copper", dur=10,
         beats=[(0.06, "Warm metal, old as the rule."), (0.45, "Patina of pure computation."),
                (0.78, "Dug from a haystack of noise.")]),
    # ── DAY 5 · THE RELIQUARY ── the journey, then the vault (arcs + finale) ──
    dict(id="d5e1", day=5, chapter="THE RELIQUARY", title="From Chaos, Form",
         logline="A field becomes a relic, before your eyes.", eng="arc",
         sid="need_coral7", n1=40, n2=7, octs=1, pal="emerald", metal="jade", dur=11,
         beats=[(0.06, "The flat mandala, spinning."), (0.5, "Now watch it gain a third dimension."),
                (0.82, "Pattern, cast into metal.")]),
    dict(id="d5e2", day=5, chapter="THE RELIQUARY", title="The Frozen Maze",
         logline="Labyrinth to silver, in one turn.", eng="arc",
         sid="need_maze1", n1=48, n2=7, octs=1, pal="ice", metal="ice", dur=11,
         beats=[(0.06, "Forty-eight corridors, mirrored."), (0.5, "The light finds every wall."),
                (0.82, "A maze you could hold.")]),
    dict(id="d5e3", day=5, chapter="THE RELIQUARY", title="The Gilding",
         logline="Plasma, transmuted to gold leaf.", eng="arc",
         sid="need_plasma17", n1=40, n2=7, octs=1, pal="fire", metal="gold", dur=11,
         beats=[(0.06, "Colour first. Then carving."), (0.5, "The same field, two materials."),
                (0.82, "Both true. Both the rule.")]),
    dict(id="d5e4", day=5, chapter="THE RELIQUARY", title="The Verdigris",
         logline="Coral aged from pigment into bronze.", eng="arc",
         sid="need_coral11", n1=28, n2=7, octs=1, pal="aqua", metal="copper", dur=11,
         beats=[(0.06, "A reef, drawn in light."), (0.5, "A reef, struck in metal."),
                (0.82, "One specimen. Two lives.")]),
    dict(id="d5e5", day=5, chapter="THE RELIQUARY", title="The Vault",
         logline="Noise, to law, to mandala, to relic — the whole journey.", eng="finale",
         sid="need_plasma7", kw=dict(F=0.0264, k=0.0579), seed=7, pal="nebula", metal="gold", dur=13,
         beats=[(0.04, "It began as a flaw in nothing."), (0.32, "A law gave it shape."),
                (0.58, "Symmetry gave it grace."), (0.82, "And we kept it. The Reliquary.")]),
]


def _beat_at(beats, p):
    """Active caption + alpha for visual-progress fraction p in [0,1]."""
    cur = None
    for i, (s, _) in enumerate(beats):
        e = beats[i + 1][0] if i + 1 < len(beats) else 1.01
        if s <= p < e:
            cur = (i, s, e); break
    if cur is None:
        return "", 0.0
    i, s, e = cur
    fade = 0.06
    a = min((p - s) / fade, (e - p) / fade, 1.0)
    return beats[i][1], max(0.0, a)


# ── compositor ────────────────────────────────────────────────────────────────
def _title_frames(ep, n):
    fch, fti, flo, fnum = _font(40), _font(96), _font(40, False), _font(34, False)
    out = []
    for fi in range(n):
        p = fi / max(n - 1, 1)
        a = min(p / 0.18, (1 - p) / 0.18, 1.0)
        cv = Image.new("RGBA", (W, H), (*BG, 255))
        _text(cv, (W // 2, 560), _spaced(f"Day {ep['day']}  ·  {ep['chapter']}"), fch, GOLD, a * 0.92)
        tlines = _wrap(ImageDraw.Draw(cv), ep["title"], fti, W - 160)
        _text(cv, (W // 2, 760), "\n".join(tlines), fti, INK, a, spacing=14)
        cv2 = ImageDraw.Draw(cv)
        cv2.line([(W // 2 - 120, 900), (W // 2 + 120, 900)], fill=(*GOLD, int(180 * a)), width=2)
        llines = _wrap(ImageDraw.Draw(cv), ep["logline"], flo, W - 200)
        _text(cv, (W // 2, 1010), "\n".join(llines), flo, DIM, a, spacing=12)
        idx = [e["id"] for e in SCHEDULE].index(ep["id"]) + 1
        _text(cv, (W // 2, 1230), f"{idx:02d} / 25", fnum, GOLD, a * 0.8)
        _text(cv, (W // 2, 1740), _spaced("CellAutomata"), _font(28), DIM, a * 0.7)
        out.append(np.asarray(cv.convert("RGB"), np.uint8))
    return out


def _compose(ep, disc_frames):
    fchap, ftit, fcap, fsig = _font(30), _font(46), _font(44, False), _font(24)
    nv = len(disc_frames)
    end_s = 1 - (1.9 / (nv / FPS))           # end-card window
    out = []
    for fi, disc in enumerate(disc_frames):
        p = fi / max(nv - 1, 1)
        cv = Image.new("RGBA", (W, H), (*BG, 255))
        cv.paste(Image.fromarray(disc), (DX, DY))
        gin = min(p / 0.05, 1.0)             # fade in from title cut
        _text(cv, (W // 2, 168), _spaced(ep["chapter"]), fchap, GOLD, 0.75 * gin)
        _text(cv, (W // 2, 232), ep["title"], ftit, INK, 0.9 * gin)
        txt, ba = _beat_at(ep["beats"], p)
        if txt:
            lines = _wrap(ImageDraw.Draw(cv), txt, fcap, W - 150)
            _text(cv, (W // 2, 1470), "\n".join(lines), fcap, INK, ba * gin, spacing=12)
        if p >= end_s:
            ea = min((p - end_s) / 0.12, 1.0)
            _text(cv, (W // 2, 1660), _spaced(f"Day {ep['day']} of 5"), _font(26), GOLD, ea * 0.85)
            _text(cv, (W // 2, 1720), _spaced("CellAutomata"), fsig, DIM, ea * 0.7)
        frame = np.asarray(cv.convert("RGB"), np.uint8)
        if gin < 1.0:                        # global fade-in over the cut
            frame = (frame.astype(np.float32) * (0.25 + 0.75 * gin)).astype(np.uint8)
        out.append(frame)
    return out


def _disc_frames(ep, nv):
    e = ep["eng"]
    if e == "evolve":
        return frames_evolve(ep["kw"], 240, ep["seed"], nv, ep["pal"])
    if e == "kal":
        return frames_kal(_src(ep["sid"]), ep["n1"], ep["n2"], ep["octs"], nv, ep["pal"])
    if e == "relit":
        r = NE._rank_lookup()[ep["sid"]]
        return frames_relit(_src(ep["sid"]), r["n1"], r["n2"], r["octs"], nv, ep["metal"])
    if e == "arc":
        return frames_arc(_src(ep["sid"]), ep["n1"], ep["n2"], ep["octs"], nv, ep["pal"], ep["metal"])
    if e == "finale":
        return frames_finale(_src(ep["sid"]), ep["kw"], ep["seed"], nv, ep["pal"], ep["metal"])
    raise ValueError(e)


def _writer(path):
    wr = imageio_ffmpeg.write_frames(path, (W, H), fps=FPS, codec="libx264",
        pix_fmt_in="rgb24", pix_fmt_out="yuv420p", macro_block_size=8,
        output_params=["-crf", "20", "-preset", "medium"])
    wr.send(None)
    return wr


def _mux(silent, out, dur, day):
    base, fifth = DRONE[day]
    af = (f"[1:a][2:a]amix=inputs=2,volume=0.13,lowpass=f=480,"
          f"afade=t=in:st=0:d=1.4,afade=t=out:st={dur-1.8:.1f}:d=1.8[a]")
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", silent,
                    "-f", "lavfi", "-t", f"{dur}", "-i", f"sine=frequency={base}:sample_rate=44100",
                    "-f", "lavfi", "-t", f"{dur}", "-i", f"sine=frequency={fifth}:sample_rate=44100",
                    "-filter_complex", af, "-map", "0:v", "-map", "[a]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "144k", "-shortest",
                    "-movflags", "+faststart", out], check=True)


def render_one(ep):
    d = f"{OUT}/day{ep['day']}"
    os.makedirs(d, exist_ok=True)
    nt = int(2.4 * FPS)
    nv = int((ep["dur"] - 2.4) * FPS)
    disc = _disc_frames(ep, nv)
    frames = _title_frames(ep, nt) + _compose(ep, disc)
    silent = f"/tmp/{ep['id']}_silent.mp4"
    out = f"{d}/{ep['id']}_{ep['title'].lower().replace(' ', '_').replace(',', '')}.mp4"
    wr = _writer(silent)
    for fr in frames:
        wr.send(np.ascontiguousarray(fr).tobytes())
    wr.close()
    _mux(silent, out, ep["dur"], ep["day"])
    Image.fromarray(disc[len(disc) // 2]).resize((360, 360)).save(f"/tmp/thumb_{ep['id']}.png")
    print(f"  {ep['id']} {ep['chapter'][:10]:10s} {ep['title']:20s} {ep['eng']:6s} -> {os.path.basename(out)}")
    return out


def poster():
    cols, rows, cell, pad = 5, 5, 360, 16
    cw, ch = cell + 40, cell + 96
    P = Image.new("RGB", (cols * cw + pad, rows * ch + pad + 120), BG)
    d = ImageDraw.Draw(P)
    _t = lambda xy, s, f, c, an="mm": d.text(xy, s, font=f, fill=c, anchor=an)
    _t((P.width // 2, 64), "THE RELIQUARY", _font(60), GOLD)
    _t((P.width // 2, 112), "  ".join("A FIVE-DAY RELEASE IN 25 STORIES".split()), _font(22, False), DIM)
    for i, ep in enumerate(SCHEDULE):
        r, c = i // cols, i % cols
        x, y = pad + c * cw, 140 + r * ch
        th = f"/tmp/thumb_{ep['id']}.png"
        if os.path.exists(th):
            P.paste(Image.open(th).resize((cell, cell)), (x + 20, y + 8))
        d.text((x + 20, y + cell + 18), f"D{ep['day']}·{ep['title']}", font=_font(22), fill=INK)
        d.text((x + 20, y + cell + 50), ep["chapter"], font=_font(16, False), fill=GOLD)
    P.save(f"{OUT}/_poster.jpg", quality=90)
    print(f"poster -> {OUT}/_poster.jpg")


def sizzle(paths):
    tmp = "/tmp/sizzle"; os.makedirs(tmp, exist_ok=True)
    segs = []
    for i, p in enumerate(paths):
        s = f"{tmp}/s{i:02d}.mp4"
        subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-ss", "3.0", "-t", "2.3",
                        "-i", p, "-an", "-c:v", "libx264", "-crf", "20", "-preset", "fast",
                        "-vf", "fps=30,setpts=PTS-STARTPTS", s], check=True)
        segs.append(s)
    lst = f"{tmp}/list.txt"; open(lst, "w").write("".join(f"file '{s}'\n" for s in segs))
    total = len(segs) * 2.3
    sv = f"{tmp}/sv.mp4"
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", lst, "-c", "copy", sv], check=True)
    out = f"{OUT}/_week_sizzle.mp4"
    af = (f"[1:a][2:a]amix=inputs=2,volume=0.14,lowpass=f=500,"
          f"afade=t=in:st=0:d=1.5,afade=t=out:st={total-2:.1f}:d=2[a]")
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", sv,
                    "-f", "lavfi", "-t", f"{total}", "-i", "sine=frequency=82.41:sample_rate=44100",
                    "-f", "lavfi", "-t", f"{total}", "-i", "sine=frequency=123.47:sample_rate=44100",
                    "-filter_complex", af, "-map", "0:v", "-map", "[a]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "144k", "-shortest",
                    "-movflags", "+faststart", out], check=True)
    print(f"sizzle -> {out} ({os.path.getsize(out)/1e6:.1f} MB)")


def calendar():
    L = ["# The Reliquary — 5-Day Release Calendar",
         "", "25 story-driven vertical (9:16) videos. One chapter per day, five episodes each,",
         "tracing an arc from chaos to order. Render with `python3 tools/schedule.py --all`.",
         "", "| Day | # | Episode | Engine | Story |", "|---|---|---|---|---|"]
    for i, e in enumerate(SCHEDULE):
        L.append(f"| {e['day']} · {e['chapter']} | {i+1:02d} | **{e['title']}** | {e['eng']} | {e['logline']} |")
    L += ["", "## Posting cadence", ""]
    days = {1: "GENESIS — pattern born from noise", 2: "THE LAWS — each rule a character",
            3: "SYMMETRY — folding chaos into mandalas", 4: "THE RELICS — mandalas cast as medallions",
            5: "THE RELIQUARY — the whole journey, then the vault"}
    for dnum, desc in days.items():
        eps = [e for e in SCHEDULE if e["day"] == dnum]
        L.append(f"- **Day {dnum}: {desc}** — " + ", ".join(e["title"] for e in eps))
    open(f"{OUT}/CALENDAR.md", "w").write("\n".join(L) + "\n")
    print(f"calendar -> {OUT}/CALENDAR.md")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--one", type=str, default="")
    ap.add_argument("--day", type=int, default=0)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--assemble", action="store_true", help="poster+sizzle+calendar from existing mp4s")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    if a.one:
        render_one(next(e for e in SCHEDULE if e["id"] == a.one))
    elif a.day:
        for e in [e for e in SCHEDULE if e["day"] == a.day]:
            render_one(e)
    elif a.all or a.assemble:
        paths = []
        if a.all:
            for e in SCHEDULE:
                paths.append(render_one(e))
        else:
            paths = sorted(glob.glob(f"{OUT}/day*/*.mp4"))
        poster(); calendar()
        if paths:
            sizzle(paths)
        print(f"\nDONE — {len(SCHEDULE)} episodes in {OUT}/")
    else:
        ap.error("need --one ID | --day N | --all | --assemble")


if __name__ == "__main__":
    main()
