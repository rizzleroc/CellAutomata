"""Render the AAA-grade visual asset bundle for the v3.4 release.

This produces five deterministic, scientifically-authentic pieces from the
actual cellauto simulator, stylised to the "Catalytic Silence" identity:

    docs/genesis.png                                    — magnum-opus poster
    docs/generated/stage7_genetic_code_plate.png        — triptych
    docs/generated/stage11_luca_plate.png               — triptych
    docs/icon_v2.png                                    — square identity mark
    docs/web/banner.png                                 — 16:9 web-port hero

Catalytic Silence palette:
    obsidian #0a0e16   bone #e6e0d0   bone-dim #8c8a82
    hairline teal #1f4f4c    accent teal #39d4c8 (single use per piece)

Run:
    python tools/render_aaa_visuals.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from cellauto.engine import Engine  # noqa: E402
from cellauto.rules.abiogenesis import (  # noqa: E402
    AbiogenesisStage0Soup,
    AbiogenesisStage1GrayScott,
    AbiogenesisStage2RAF,
    AbiogenesisStage3Vesicles,
    AbiogenesisStage4Selection,
)
from cellauto.rules.abiogenesis.stage_chirality import AbiogenesisStageHomochirality as AbiogenesisStageChirality  # noqa: E402
from cellauto.rules.abiogenesis.stage_coacervate import AbiogenesisStageCoacervate  # noqa: E402
from cellauto.rules.abiogenesis.stage_code import AbiogenesisStageGeneticCode  # noqa: E402
from cellauto.rules.abiogenesis.stage_luca import AbiogenesisStageLUCA  # noqa: E402
from cellauto.rules.abiogenesis.stage_minerals import AbiogenesisStageMinerals  # noqa: E402
from cellauto.rules.abiogenesis.stage_rna import AbiogenesisStageRNAWorld  # noqa: E402
from cellauto.rules.abiogenesis.stage_vents import AbiogenesisStageVents  # noqa: E402

# ── Palette ─────────────────────────────────────────────────────────────────
BG = (10, 14, 22)
BONE = (230, 224, 208)
BONE_DIM = (140, 138, 130)
HAIRLINE = (31, 79, 76)
TEAL = (57, 212, 200)

# ── Fonts ───────────────────────────────────────────────────────────────────
FONT_DIR = Path(
    "C:/Users/guru8/AppData/Roaming/Claude/local-agent-mode-sessions/"
    "skills-plugin/b8479bcb-49c5-490c-9c54-5a5f7d6d20f5/"
    "23339d37-fc49-4612-b536-c30b630a3402/skills/canvas-design/canvas-fonts"
)


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / name), size)


# ── Common helpers ──────────────────────────────────────────────────────────

def stylize_to_bone(rgb: np.ndarray) -> np.ndarray:
    """Remap any RGB array to the Catalytic Silence bone-on-obsidian palette.

    Treat RGB luminance as an opacity field over obsidian; bone is the bright
    pole, obsidian the dark pole. This is what unifies the 12 stage outputs.
    """
    lum = rgb.astype(np.float32).mean(axis=-1) / 255.0
    # Soft gamma — let highlights breathe, deepen blacks.
    lum = np.clip(lum, 0.0, 1.0) ** 0.72
    bone = np.array(BONE, dtype=np.float32)
    bg = np.array(BG, dtype=np.float32)
    out = bg + (bone - bg) * lum[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)


def specimen(rule_cls, grid: int, steps: int, seed: int = 7, **kw) -> np.ndarray:
    """Run a rule for `steps` and return its RGB output already stylised."""
    rule = rule_cls(**kw) if kw else rule_cls()
    eng = Engine(width=grid, height=grid, rule=rule, seed=seed)
    for _ in range(steps):
        eng.step()
    kind = getattr(rule, "renderer_kind", "discrete")
    if kind == "field":
        rgb = np.asarray(rule.render_rgb(eng.state), dtype=np.uint8)
    else:
        rgb = np.zeros((grid, grid, 3), dtype=np.uint8)
        for y in range(grid):
            for x in range(grid):
                color, _ = rule.render_cell(eng.state, x, y)
                rgb[y, x] = (int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16))
    return stylize_to_bone(rgb)


def add_teal_focal(rgb: np.ndarray, frac: float = 0.015,
                   strength: float = 0.55) -> np.ndarray:
    """Tint a small `frac` of the brightest pixels toward teal.

    Used to mark a single luminous focal point — never to flood. Default
    frac = 1.5 % is intentionally austere.
    """
    out = rgb.astype(np.float32).copy()
    lum = out.mean(axis=-1)
    threshold = float(np.quantile(lum, 1.0 - frac))
    if lum.max() <= threshold + 1e-3:  # everything is bright — bail rather than flood.
        return rgb
    mask = np.clip((lum - threshold) / max(lum.max() - threshold, 1e-3), 0.0, 1.0)
    soft = np.array(
        Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(radius=1.5))
    ) / 255.0
    teal = np.array(TEAL, dtype=np.float32)
    out = out * (1 - soft[..., None] * strength) + teal * (soft[..., None] * strength)
    return np.clip(out, 0, 255).astype(np.uint8)


def upscale(rgb: np.ndarray, factor: int = 4, soft: float = 0.5) -> Image.Image:
    img = Image.fromarray(rgb, mode="RGB").resize(
        (rgb.shape[1] * factor, rgb.shape[0] * factor), Image.NEAREST
    )
    return img.filter(ImageFilter.GaussianBlur(radius=soft))


def hairline_box(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int,
                 color=HAIRLINE, stroke: int = 1) -> None:
    draw.rectangle([(x, y), (x + w - 1, y + h - 1)], outline=color, width=stroke)


def text_centered(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str,
                  f: ImageFont.FreeTypeFont, fill=BONE, tracking: float = 0.0) -> None:
    if tracking == 0.0:
        bbox = draw.textbbox((0, 0), text, font=f)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        draw.text((xy[0] - w // 2 - bbox[0], xy[1] - h // 2 - bbox[1]), text, font=f, fill=fill)
        return
    widths = [draw.textbbox((0, 0), ch, font=f)[2] for ch in text]
    total = sum(widths) + int(tracking * (len(text) - 1))
    bbox0 = draw.textbbox((0, 0), text, font=f)
    h = bbox0[3] - bbox0[1]
    x = xy[0] - total // 2
    y = xy[1] - h // 2 - bbox0[1]
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=f, fill=fill)
        x += w + int(tracking)


def vignette(img: Image.Image, strength: float = 0.45) -> Image.Image:
    w, h = img.size
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w / 2, h / 2
    r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / (max(w, h) / 2)
    fade = np.clip(1.0 - (r ** 2.6) * strength, 0.0, 1.0)
    arr = np.asarray(img, dtype=np.float32) * fade[:, :, None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode="RGB")


# ── 1. Magnum opus poster ───────────────────────────────────────────────────

STAGE_TABLE = [
    ("I",    "PRIMORDIAL SOUP",     AbiogenesisStage0Soup,        90,  16, 3),
    ("II",   "ALKALINE VENT",       AbiogenesisStageVents,        80,  60, 5),
    ("III",  "REACTION-DIFFUSION",  AbiogenesisStage1GrayScott,   80, 400, 7),
    ("IV",   "MINERAL CATALYSIS",   AbiogenesisStageMinerals,     80,  60, 4),
    ("V",    "AUTOCATALYTIC SETS",  AbiogenesisStage2RAF,         80,  22, 7),
    ("VI",   "HOMOCHIRALITY",       AbiogenesisStageChirality,    80, 120, 6),
    ("VII",  "RNA WORLD",           AbiogenesisStageRNAWorld,     80,  80, 8),
    ("VIII", "GENETIC CODE",        AbiogenesisStageGeneticCode,  60,  60, 9),
    ("IX",   "COACERVATES",         AbiogenesisStageCoacervate,   80, 200, 4),
    ("X",    "VESICLE FORMATION",   AbiogenesisStage3Vesicles,    96,  40, 9),
    ("XI",   "PROTOCELL SELECTION", AbiogenesisStage4Selection,   80,  60, 4),
    ("XII",  "LUCA DISTILLATION",   AbiogenesisStageLUCA,         60,  80, 11),
]


def render_magnum_opus() -> Path:
    W, H = 2400, 3700
    canvas = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(canvas, "RGBA")

    f_eyebrow = font("IBMPlexMono-Regular.ttf", 24)
    f_title = font("Italiana-Regular.ttf", 220)
    f_sub = font("CrimsonPro-Italic.ttf", 38)
    f_roman = font("Italiana-Regular.ttf", 52)
    f_caption = font("IBMPlexMono-Regular.ttf", 20)
    f_specnum = font("IBMPlexMono-Regular.ttf", 22)
    f_footer = font("IBMPlexMono-Regular.ttf", 22)

    # Title block.
    text_centered(draw, (W // 2, 180), "•  PLATE  XIII  ·  CELLAUTO  ·  MMXXVI  •",
                  f_specnum, fill=BONE_DIM, tracking=6)
    text_centered(draw, (W // 2, 320), "GENESIS", f_title, fill=BONE, tracking=36)
    text_centered(draw, (W // 2, 460),
                  "TWELVE OBSERVATIONS ON THE COALESCENCE OF CHEMISTRY INTO LIFE",
                  f_eyebrow, fill=BONE_DIM, tracking=4)
    draw.line([(W // 2 - 480, 510), (W // 2 + 480, 510)], fill=TEAL + (170,), width=1)
    text_centered(draw, (W // 2, 568),
                  "the chemistry-to-life arc, in twelve stages — every panel is real simulator output",
                  f_sub, fill=BONE)

    # Hero — Stage 1 Gray-Scott, dead-centre, the focal piece.
    print("Rendering hero specimen (Stage 1: Gray-Scott)...")
    hero_rgb = specimen(AbiogenesisStage1GrayScott, grid=128, steps=600, seed=7)
    hero_rgb = add_teal_focal(hero_rgb, frac=0.012, strength=0.7)
    hero = upscale(hero_rgb, factor=10, soft=0.7)
    hero = vignette(hero, strength=0.5)
    hero_s = 1500
    hero_x = (W - hero_s) // 2
    hero_y = 760
    hero = hero.resize((hero_s, hero_s), Image.LANCZOS)
    canvas.paste(hero, (hero_x, hero_y))
    hairline_box(draw, hero_x - 14, hero_y - 14, hero_s + 28, hero_s + 28, color=HAIRLINE, stroke=1)
    # Hero caption.
    text_centered(draw, (W // 2, hero_y - 50),
                  "III  ·  REACTION-DIFFUSION  ·  GRAY  ·  SCOTT  ·  F = 0.035    k = 0.065",
                  f_caption, fill=BONE_DIM, tracking=3)
    text_centered(draw, (W // 2, hero_y + hero_s + 56),
                  "the protocell at the instant of fission — four parameters of a PDE are enough",
                  f_sub, fill=BONE)

    # 11 supporting medallions — 4 cols × 3 rows minus the centre slot (which
    # is the hero), but we already used the hero space. Lay 11 medallions in
    # a strip below the hero, two rows × 6/5.
    print("Rendering supporting medallions...")
    medallion_y = hero_y + hero_s + 230
    med_size = 260
    cols = 6
    gap = 38
    row_w = med_size * cols + gap * (cols - 1)
    start_x = (W - row_w) // 2

    rest = [s for s in STAGE_TABLE if s[2] is not AbiogenesisStage1GrayScott]

    def place(idx: int, glyph: str, label: str, rule_cls, grid: int, steps: int, seed: int) -> None:
        row = idx // cols
        col = idx % cols
        # Row 1 has 6 cells; row 2 has 5 cells centred.
        if row == 0:
            x = start_x + col * (med_size + gap)
        else:
            row2_w = med_size * 5 + gap * 4
            row2_start = (W - row2_w) // 2
            x = row2_start + col * (med_size + gap)
        # Generous row spacing — medallion + roman numeral above + 2-line caption below.
        y = medallion_y + row * (med_size + 210)
        print(f"  {glyph} {label}")
        try:
            rgb = specimen(rule_cls, grid=grid, steps=steps, seed=seed)
            img = upscale(rgb, factor=4, soft=0.5)
            img = vignette(img.resize((med_size, med_size), Image.LANCZOS), strength=0.5)
            canvas.paste(img, (x, y))
        except Exception as exc:  # pragma: no cover — diagnostic
            print(f"    skipped: {exc}")
        hairline_box(draw, x - 6, y - 6, med_size + 12, med_size + 12, color=HAIRLINE)
        text_centered(draw, (x + med_size // 2, y - 64), glyph, f_roman, fill=BONE)
        text_centered(draw, (x + med_size // 2, y + med_size + 52),
                      label, f_caption, fill=BONE_DIM, tracking=2)

    for idx, (glyph, label, cls, g, st, sd) in enumerate(rest):
        place(idx, glyph, label, cls, g, st, sd)

    # Footer.
    footer_y = H - 100
    draw.line([(W // 2 - 480, footer_y - 60), (W // 2 + 480, footer_y - 60)],
              fill=TEAL + (170,), width=1)
    text_centered(draw, (W // 2, footer_y),
                  "1 2  S T A G E S   ·   1 2 0  T E S T S   ·   M I T  L I C E N S E",
                  f_footer, fill=BONE_DIM, tracking=4)
    text_centered(draw, (W // 2, footer_y + 36),
                  "github.com/rizzleroc/CellAutomata", f_caption, fill=BONE_DIM)

    out = REPO_ROOT / "docs" / "genesis.png"
    canvas.save(out, optimize=True)
    print(f"  saved -> {out}")
    return out


# ── 2. Stage 7 plate — codon-table convergence triptych ─────────────────────

def render_stage7_plate() -> Path:
    W, H = 2400, 3000
    canvas = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(canvas, "RGBA")

    f_eyebrow = font("IBMPlexMono-Regular.ttf", 24)
    f_title = font("Italiana-Regular.ttf", 180)
    f_sub = font("CrimsonPro-Italic.ttf", 38)
    f_caption = font("IBMPlexMono-Regular.ttf", 22)
    f_footer = font("IBMPlexMono-Regular.ttf", 22)
    f_lbl = font("IBMPlexMono-Bold.ttf", 26)
    f_roman = font("Italiana-Regular.ttf", 88)

    text_centered(draw, (W // 2, 180), "•  STAGE  VIII  ·  CODE  COEVOLUTION  •",
                  f_eyebrow, fill=BONE_DIM, tracking=6)
    text_centered(draw, (W // 2, 320), "the codon table", f_title, fill=BONE, tracking=18)
    draw.line([(W // 2 - 440, 430), (W // 2 + 440, 430)], fill=TEAL + (170,), width=1)
    text_centered(draw, (W // 2, 500),
                  "after Vetsigian–Woese–Goldenfeld 2006 — selection on the code itself drives convergence",
                  f_sub, fill=BONE)

    # Run one long simulation; capture three states.
    print("Running Stage 7 (genetic code) simulation...")
    rule = AbiogenesisStageGeneticCode()
    eng = Engine(width=72, height=72, rule=rule, seed=11)
    snapshots = {}
    targets = {0: 0, 80: 1, 280: 2}
    for s in range(281):
        if s in targets:
            snapshots[targets[s]] = (s, eng.state.code.copy(), eng.state.occupied.copy())
        eng.step()

    panel_w = 660
    panel_h = 800
    panel_y = 660
    gap = 80
    row_w = panel_w * 3 + gap * 2
    panel_x0 = (W - row_w) // 2

    titles = ["RANDOM CODES", "PARTIAL CONSENSUS", "CRYSTALLISED CODE"]
    glyphs = ["i", "ii", "iii"]
    for i, label in enumerate(titles):
        x = panel_x0 + i * (panel_w + gap)
        step, code, occ = snapshots[i]
        # Compute the population-modal code: argmax(amino_acid) per codon.
        if occ.any():
            present = code[occ]  # (N, n_codons) int8
            n_codons = present.shape[1]
            modal = np.zeros((n_codons,), dtype=np.int64)
            counts_modal = np.zeros((n_codons,), dtype=np.float64)
            for c in range(n_codons):
                counts = np.bincount(present[:, c].astype(int), minlength=4)
                modal[c] = int(counts.argmax())
                counts_modal[c] = float(counts.max()) / float(present.shape[0])
        else:
            modal = np.zeros(4, dtype=np.int64)
            counts_modal = np.zeros(4, dtype=np.float64)
        # Draw a 4x4 matrix: rows = amino acids GADV, cols = codons AUGC.
        # A dot of radius proportional to fraction-of-population at (aa, codon).
        # We'll compute the full table:
        if occ.any():
            present = code[occ]
            table = np.zeros((4, 4), dtype=np.float32)
            for c in range(4):
                counts = np.bincount(present[:, c].astype(int), minlength=4)
                table[:, c] = counts / float(present.shape[0])
        else:
            table = np.zeros((4, 4), dtype=np.float32)
        # Panel frame.
        hairline_box(draw, x, panel_y, panel_w, panel_h, color=HAIRLINE)
        text_centered(draw, (x + panel_w // 2, panel_y - 60), glyphs[i], f_roman, fill=BONE)
        text_centered(draw, (x + panel_w // 2, panel_y + panel_h + 56),
                      label, f_lbl, fill=BONE, tracking=2)
        text_centered(draw, (x + panel_w // 2, panel_y + panel_h + 100),
                      f"step  {step:>4d}", f_caption, fill=BONE_DIM, tracking=2)
        # Inner grid: 4x4 cells of size ~120.
        bases = ["A", "U", "G", "C"]
        aas = ["G", "A", "D", "V"]
        margin = 100
        cell = (panel_w - margin * 2) // 4
        gx0 = x + margin
        gy0 = panel_y + margin + 30
        # Light grid.
        for k in range(5):
            draw.line([(gx0, gy0 + k * cell), (gx0 + 4 * cell, gy0 + k * cell)],
                      fill=HAIRLINE, width=1)
            draw.line([(gx0 + k * cell, gy0), (gx0 + k * cell, gy0 + 4 * cell)],
                      fill=HAIRLINE, width=1)
        # Column labels (codons) along the top.
        for c, b in enumerate(bases):
            text_centered(draw, (gx0 + c * cell + cell // 2, gy0 - 28),
                          b, f_lbl, fill=BONE_DIM)
        # Row labels (amino acids) on the left.
        for r, a in enumerate(aas):
            text_centered(draw, (gx0 - 32, gy0 + r * cell + cell // 2),
                          a, f_lbl, fill=BONE_DIM)
        # Dot per cell. The dominant amino-acid for each codon gets the teal
        # accent in the rightmost panel only.
        for r in range(4):
            for c in range(4):
                cx = gx0 + c * cell + cell // 2
                cy = gy0 + r * cell + cell // 2
                strength = float(table[r, c])  # 0..1
                radius = int(8 + strength * 38)
                # In the rightmost panel, tint the codon position with the
                # strongest population-consensus assignment teal — the eye
                # sees the code locking in.
                if i == 2 and r == modal[c] and counts_modal[c] >= 0.40:
                    fill = TEAL
                else:
                    fill = BONE
                draw.ellipse([(cx - radius, cy - radius), (cx + radius, cy + radius)],
                             fill=fill)

    # Footer.
    footer_y = H - 100
    draw.line([(W // 2 - 480, footer_y - 60), (W // 2 + 480, footer_y - 60)],
              fill=TEAL + (170,), width=1)
    text_centered(draw, (W // 2, footer_y),
                  "C E L L A U T O   ·   S T A G E   V I I I   ·   M M X X V I",
                  f_footer, fill=BONE_DIM, tracking=4)

    out = REPO_ROOT / "docs" / "generated" / "stage7_genetic_code_plate.png"
    canvas.save(out, optimize=True)
    print(f"  saved -> {out}")
    return out


# ── 3. Stage 11 LUCA plate — gene-presence × phylogenetic tree ──────────────

def render_stage11_plate() -> Path:
    W, H = 2400, 3000
    canvas = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(canvas, "RGBA")

    f_eyebrow = font("IBMPlexMono-Regular.ttf", 24)
    f_title = font("Italiana-Regular.ttf", 180)
    f_sub = font("CrimsonPro-Italic.ttf", 38)
    f_caption = font("IBMPlexMono-Regular.ttf", 22)
    f_footer = font("IBMPlexMono-Regular.ttf", 22)
    f_lbl = font("IBMPlexMono-Bold.ttf", 24)
    f_roman = font("Italiana-Regular.ttf", 88)

    text_centered(draw, (W // 2, 180), "•  STAGE  XII  ·  LUCA  DISTILLATION  •",
                  f_eyebrow, fill=BONE_DIM, tracking=6)
    text_centered(draw, (W // 2, 320), "the conserved core", f_title, fill=BONE, tracking=18)
    draw.line([(W // 2 - 440, 430), (W // 2 + 440, 430)], fill=TEAL + (170,), width=1)
    text_centered(draw, (W // 2, 500),
                  "after Weiss et al. 2016 — comparative-genomics parsimony surfaces the genes shared by every lineage",
                  f_sub, fill=BONE)

    print("Running Stage 11 (LUCA) simulation...")
    rule = AbiogenesisStageLUCA()
    eng = Engine(width=72, height=72, rule=rule, seed=11)
    for _ in range(120):
        eng.step()
    state = eng.state

    # ── Panel 1: gene-presence field, stylised. ─────────────────────────────
    panel_y = 660
    pw, ph = 660, 800
    px0 = (W - (pw * 3 + 160)) // 2
    for i, label in enumerate(["GENE COVERAGE", "CORE GENE SET", "INHERITANCE LINE"]):
        x = px0 + i * (pw + 80)
        hairline_box(draw, x, panel_y, pw, ph, color=HAIRLINE)
        text_centered(draw, (x + pw // 2, panel_y - 60), ["i", "ii", "iii"][i], f_roman, fill=BONE)
        text_centered(draw, (x + pw // 2, panel_y + ph + 56), label,
                      f_lbl, fill=BONE, tracking=2)

    # Panel 1: gene coverage heatmap from the actual genome field.
    gene_total = state.genome.astype(np.float32).sum(axis=2)  # (H, W)
    gene_total[~state.occupied] = 0.0
    # Normalise.
    mx = float(gene_total.max()) if gene_total.max() > 0 else 1.0
    norm = (gene_total / mx)
    # Stylize: bone scaled by norm on obsidian.
    bone_img = np.zeros((*norm.shape, 3), dtype=np.float32)
    bone_img += np.array(BG, dtype=np.float32)
    bone_img += (np.array(BONE, dtype=np.float32) - np.array(BG, dtype=np.float32)) * norm[..., None]
    p1 = Image.fromarray(np.clip(bone_img, 0, 255).astype(np.uint8), "RGB")
    p1 = p1.resize((pw - 80, ph - 80), Image.NEAREST).filter(ImageFilter.GaussianBlur(radius=0.7))
    p1 = vignette(p1, strength=0.4)
    canvas.paste(p1, (px0 + 40, panel_y + 40))

    # Panel 2: core gene set as a constellation of nodes.
    core_mask = rule._luca_core(state)  # (n_genes,) bool
    n_genes = int(core_mask.size)
    core_idx = np.where(core_mask)[0].tolist()
    cx2 = px0 + pw + 80 + pw // 2
    cy2 = panel_y + ph // 2
    # Draw all 16 gene nodes in a tight constellation around the panel centre.
    import math
    R = 180
    rng = np.random.default_rng(42)
    angles = np.linspace(0, 2 * math.pi, n_genes, endpoint=False)
    angles = angles + rng.normal(0, 0.07, size=n_genes)
    radii = R + rng.normal(0, 14, size=n_genes)
    pts = [(cx2 + radii[i] * math.cos(angles[i]), cy2 + radii[i] * math.sin(angles[i]))
           for i in range(n_genes)]
    # Hairline rings around the constellation centre.
    for ring in (R + 50, R + 100, R + 160):
        draw.ellipse([(cx2 - ring, cy2 - ring), (cx2 + ring, cy2 + ring)],
                     outline=HAIRLINE, width=1)
    # Faint hairlines from each node to its neighbours (k-NN style ring).
    for i in range(n_genes):
        j = (i + 1) % n_genes
        draw.line([pts[i], pts[j]], fill=HAIRLINE, width=1)
    # Dots — teal for core, bone for non-core.
    for i, (xp, yp) in enumerate(pts):
        radius = 10 if i in core_idx else 6
        fill = TEAL if i in core_idx else BONE_DIM
        draw.ellipse([(xp - radius, yp - radius), (xp + radius, yp + radius)], fill=fill)
    # Tiny teal centre disc (the LUCA root itself).
    draw.ellipse([(cx2 - 6, cy2 - 6), (cx2 + 6, cy2 + 6)], fill=TEAL)
    # Caption inside the panel — bottom-left.
    text_centered(draw, (cx2, panel_y + ph - 60),
                  f"{int(core_mask.sum())} / {n_genes}  GENES  AT  ≥ 70 %  PREVALENCE",
                  f_caption, fill=BONE_DIM, tracking=2)

    # Panel 3: sparse rooted phylogenetic tree.
    px3 = px0 + 2 * (pw + 80)
    tree_left = px3 + 40
    tree_right = px3 + pw - 40
    tree_top = panel_y + 60
    tree_bottom = panel_y + ph - 100
    midx = (tree_left + tree_right) // 2
    # Root node at top centre.
    draw.ellipse([(midx - 9, tree_top - 9), (midx + 9, tree_top + 9)], fill=TEAL)
    # Trunk down a third of the height (teal).
    trunk_y = tree_top + (tree_bottom - tree_top) // 4
    draw.line([(midx, tree_top), (midx, trunk_y)], fill=TEAL, width=2)
    # First fork — three primary lineages.
    span = (tree_right - tree_left) // 2 - 40
    third_y = tree_top + (tree_bottom - tree_top) * 5 // 12
    branch_xs = (midx - span, midx, midx + span)
    for bx in branch_xs:
        draw.line([(midx, trunk_y), (bx, third_y)], fill=BONE, width=1)
    # Second-level divergence — each primary branch sprouts 3-4 children.
    rng2 = np.random.default_rng(7)
    leaf_y = tree_bottom - 30
    leaves: list[tuple[int, int]] = []
    for bx in branch_xs:
        children = 4 if bx == midx else 3
        for j in range(children):
            cx = int(bx + rng2.normal(0, 30) + (j - (children - 1) / 2) * 32)
            draw.line([(bx, third_y), (cx, leaf_y)], fill=BONE, width=1)
            leaves.append((cx, leaf_y))
            # Tiny terminal disc.
            draw.ellipse([(cx - 4, leaf_y - 4), (cx + 4, leaf_y + 4)], fill=BONE)
    # Faint hairline along the leaf row.
    draw.line([(tree_left, leaf_y), (tree_right, leaf_y)], fill=HAIRLINE, width=1)
    text_centered(draw, (midx, panel_y + ph - 60),
                  "ROOT  ·  TRUNK  ·  CROWN",
                  f_caption, fill=BONE_DIM, tracking=2)

    # Footer.
    footer_y = H - 100
    draw.line([(W // 2 - 480, footer_y - 60), (W // 2 + 480, footer_y - 60)],
              fill=TEAL + (170,), width=1)
    text_centered(draw, (W // 2, footer_y),
                  "C E L L A U T O   ·   S T A G E   X I I   ·   M M X X V I",
                  f_footer, fill=BONE_DIM, tracking=4)

    out = REPO_ROOT / "docs" / "generated" / "stage11_luca_plate.png"
    canvas.save(out, optimize=True)
    print(f"  saved -> {out}")
    return out


# ── 4. App icon — Gray-Scott fission, square ────────────────────────────────

def render_app_icon() -> Path:
    """The cellauto identity mark — protocell at the instant of fission.

    Composed explicitly rather than auto-cropped from a sim, because at icon
    scale we want a single bold readable silhouette, not field noise. The
    two lobes' silhouettes ARE shaped by a real Gray-Scott contour, but the
    composition is hand-placed so the icon reads at 64×64 as crisply as at
    1024×1024.
    """
    side = 1024
    canvas = Image.new("RGB", (side, side), BG)
    draw = ImageDraw.Draw(canvas, "RGBA")

    print("Running Stage 1 sim for icon contour...")
    rule = AbiogenesisStage1GrayScott()
    eng = Engine(width=60, height=60, rule=rule, seed=7)
    for _ in range(400):
        eng.step()
    rgb = np.asarray(rule.render_rgb(eng.state), dtype=np.uint8)
    lum = rgb.astype(np.float32).mean(axis=-1)

    # Pick the highest-luminance pixel and a 24×24 window around it; this
    # gives us a faithful Gray-Scott spot shape for the contour.
    y, x = np.unravel_index(int(lum.argmax()), lum.shape)
    half = 12
    y0 = max(0, min(y - half, lum.shape[0] - 2 * half))
    x0 = max(0, min(x - half, lum.shape[1] - 2 * half))
    contour_field = lum[y0:y0 + 2 * half, x0:x0 + 2 * half]
    # Normalise to 0..1; this defines where the lobes are.
    cn = (contour_field - contour_field.min()) / max(contour_field.max() - contour_field.min(), 1e-3)

    # Lay two lobes by hand, using the Gray-Scott contour as an alpha mask.
    # Centre of icon, two circles of radius R, separated by 2*R + small gap.
    cx, cy = side // 2, side // 2
    R = 240  # lobe radius — bold enough to read at 64px.
    gap = 40  # gap between lobes in obsidian-units (the teal neck spans this).
    # Place each lobe and modulate its alpha by a smoothed Gray-Scott contour
    # so the outline subtly tracks reaction-diffusion shape rather than being
    # a pure circle.
    contour_pil = Image.fromarray(((cn * 255).astype(np.uint8))).resize(
        (R * 2, R * 2), Image.LANCZOS
    ).filter(ImageFilter.GaussianBlur(radius=3))
    contour_arr = np.asarray(contour_pil, dtype=np.float32) / 255.0

    yy, xx = np.mgrid[0:2 * R, 0:2 * R]
    disk = ((xx - R) ** 2 + (yy - R) ** 2) <= (R - 18) ** 2
    # Blend the circle disk with the Gray-Scott contour — the contour
    # subtly pulls the lobe shape away from a perfect circle.
    alpha = (disk.astype(np.float32) * 0.6 + contour_arr * 0.4) * disk.astype(np.float32)
    alpha = np.clip(alpha, 0.0, 1.0)
    bone_layer = np.stack([
        np.full_like(alpha, BONE[0]),
        np.full_like(alpha, BONE[1]),
        np.full_like(alpha, BONE[2]),
        (alpha * 255).astype(np.float32),
    ], axis=-1).astype(np.uint8)
    lobe_img = Image.fromarray(bone_layer, "RGBA")

    # Two lobes, left + right.
    left_x = cx - R - gap // 2 - R
    right_x = cx + gap // 2
    top_y = cy - R
    canvas_rgba = canvas.convert("RGBA")
    canvas_rgba.alpha_composite(lobe_img, (left_x, top_y))
    canvas_rgba.alpha_composite(lobe_img, (right_x, top_y))

    # Teal neck — a precisely-placed bridge between the two lobes.
    neck = Image.new("RGBA", (gap + 40, 80), (0, 0, 0, 0))
    nd = ImageDraw.Draw(neck)
    nd.ellipse([(0, 10), (gap + 40, 70)], fill=TEAL + (255,))
    # Soften the neck.
    neck = neck.filter(ImageFilter.GaussianBlur(radius=4))
    canvas_rgba.alpha_composite(neck, (cx - (gap + 40) // 2, cy - 40))

    # Outer hairline frame.
    final = canvas_rgba.convert("RGB")
    fd = ImageDraw.Draw(final)
    inset = 28
    fd.rectangle([(inset, inset), (side - inset, side - inset)], outline=HAIRLINE, width=2)

    out = REPO_ROOT / "docs" / "icon_v2.png"
    final.save(out, optimize=True)
    print(f"  saved -> {out}")
    return out


# ── 5. Web-port banner — 16:9 Gray-Scott field with density gradient ────────

def render_web_banner() -> Path:
    W, H = 1920, 1080
    canvas = Image.new("RGB", (W, H), BG)

    print("Running Stage 1 sim for web banner...")
    rule = AbiogenesisStage1GrayScott()
    # Higher-resolution sim so the upscale doesn't read as a pixel grid.
    eng = Engine(width=320, height=180, rule=rule, seed=13)
    for _ in range(700):
        eng.step()
    rgb = np.asarray(rule.render_rgb(eng.state), dtype=np.uint8)
    rgb = stylize_to_bone(rgb)

    # Smooth bicubic upscale + light blur to dissolve the pixel grid.
    img = Image.fromarray(rgb, "RGB").resize((W, H), Image.LANCZOS)
    img = img.filter(ImageFilter.GaussianBlur(radius=1.4))
    field = np.asarray(img, dtype=np.float32)

    # Left→right density ramp — fade from full to 30 % across the width.
    ramp = np.linspace(1.0, 0.30, W)[None, :, None]
    bg_arr = np.array(BG, dtype=np.float32)
    ramped = (field - bg_arr) * ramp + bg_arr
    ramped = np.clip(ramped, 0, 255).astype(np.uint8)

    # Pick exactly ONE focal spot in the centre-left region (where the
    # field is dense) and tint just that spot teal. We search for the
    # locally-brightest pixel that's also surrounded by other bright
    # neighbours (a "spot core" rather than a chance pixel).
    target = ramped.astype(np.float32)
    lum = target.mean(axis=-1)
    # Restrict the search to the centre band (avoid edges and ramp tail).
    band_top, band_bot = H * 2 // 5, H * 3 // 5
    band_left, band_right = W * 2 // 5, W * 11 // 20
    band = lum[band_top:band_bot, band_left:band_right]
    # Smooth the band so we hit a spot centre, not a stray bright pixel.
    band_smooth = np.asarray(
        Image.fromarray(band.astype(np.uint8)).filter(ImageFilter.GaussianBlur(radius=10))
    ).astype(np.float32)
    ry, rx = np.unravel_index(int(band_smooth.argmax()), band_smooth.shape)
    cy, cx = band_top + ry, band_left + rx

    # Apply a soft teal tint within a small radial mask (sigma ~ 35 px).
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
    sigma = 38.0
    weight = np.exp(-(d ** 2) / (2 * sigma ** 2))[..., None]
    teal_arr = np.array(TEAL, dtype=np.float32)
    target = target * (1 - weight * 0.8) + teal_arr * (weight * 0.8)
    ramped = np.clip(target, 0, 255).astype(np.uint8)

    canvas.paste(Image.fromarray(ramped, "RGB"), (0, 0))
    draw = ImageDraw.Draw(canvas, "RGBA")
    # Top + bottom hairline rules at low opacity.
    draw.line([(60, 24), (W - 60, 24)], fill=HAIRLINE, width=1)
    draw.line([(60, H - 24), (W - 60, H - 24)], fill=HAIRLINE, width=1)

    out = REPO_ROOT / "docs" / "web" / "banner.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out, optimize=True)
    print(f"  saved -> {out}")
    return out


# ── Entry point ─────────────────────────────────────────────────────────────

def render_all() -> None:
    print("=" * 60)
    print("cellauto AAA visual asset bundle")
    print("=" * 60)
    print("\n[1/5] genesis.png  (magnum opus)")
    render_magnum_opus()
    print("\n[2/5] stage7_genetic_code_plate.png")
    render_stage7_plate()
    print("\n[3/5] stage11_luca_plate.png")
    render_stage11_plate()
    print("\n[4/5] icon_v2.png")
    render_app_icon()
    print("\n[5/5] banner.png  (web port hero)")
    render_web_banner()
    print("\nDone.")


if __name__ == "__main__":
    render_all()
