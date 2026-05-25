"""Render `docs/prima-materia.png` — a Catalytic Silence plate.

This is a one-off art generator. It runs the actual cellauto simulations
(Stage 0 – 4) to produce five specimen images, then composes them with
typography from the canvas-design font pack into a museum-quality
observational plate.

Run from anywhere:

    python docs/design/render_prima_materia.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from cellauto.engine import Engine                                            # noqa: E402
from cellauto.rules.abiogenesis import (                                      # noqa: E402
    AbiogenesisStage0Soup,
    AbiogenesisStage1GrayScott,
    AbiogenesisStage2RAF,
    AbiogenesisStage3Vesicles,
    AbiogenesisStage4Selection,
)

# ── Canvas + palette ────────────────────────────────────────────────────────
W, H = 2400, 3200
BG = (10, 14, 22)            # obsidian
TEXT = (230, 224, 208)       # bone
TEXT_DIM = (140, 138, 130)
TEAL = (57, 212, 200)
MAGENTA = (212, 57, 164)

# ── Fonts (canvas-design pack) ──────────────────────────────────────────────
# Load the bundled fonts from the repo so this script runs on any
# machine, not just the author's. The TTFs are shipped at
# cellauto/assets/fonts/. docs/design/ → ../../cellauto/assets/fonts/.
FONT_DIR = Path(__file__).resolve().parents[2] / "cellauto" / "assets" / "fonts"


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / name), size)


# ── Specimen rendering helpers ──────────────────────────────────────────────

def discrete_to_rgb(rule, state, grid: int) -> np.ndarray:
    arr = np.zeros((grid, grid, 3), dtype=np.uint8)
    for y in range(grid):
        for x in range(grid):
            color, _shape = rule.render_cell(state, x, y)
            arr[y, x] = (int(color[1:3], 16),
                         int(color[3:5], 16),
                         int(color[5:7], 16))
    return arr


def _raf_render_stretched(state, n_species: int) -> np.ndarray:
    """Custom RAF render: contrast-stretch the density field so the
    autocatalytic hotspot reads against the food-supply background.
    The default render_rgb normalises by max only, which saturates the
    whole field at yellow once the wave reaches it."""
    from cellauto.renderer import cmap_viridis
    density = state.concentrations.sum(axis=2)
    lo, hi = float(density.min()), float(density.max())
    stretched = (density - lo) / max(hi - lo, 1e-9)
    return cmap_viridis(stretched)


def specimen(rule_cls, grid: int, steps: int, seed: int = 7,
             pixel_block: int = 4) -> Image.Image:
    """Run a rule for `steps` steps; return a square RGB image."""
    rule = rule_cls()
    eng = Engine(width=grid, height=grid, rule=rule, seed=seed)
    for _ in range(steps):
        eng.step()
    kind = getattr(rule, "renderer_kind", "discrete")
    # Stage 2 (RAF) wants a custom contrast-stretched render so the
    # hotspot is visible against the food-supply background.
    if rule_cls.__name__ == "AbiogenesisStage2RAF":
        rgb = np.asarray(_raf_render_stretched(eng.state, rule.n_species),
                         dtype=np.uint8)
    elif kind == "field":
        rgb = np.asarray(rule.render_rgb(eng.state), dtype=np.uint8)
    else:
        rgb = discrete_to_rgb(rule, eng.state, grid)
    img = Image.fromarray(rgb, mode="RGB")
    # Stage 0 (the discrete soup) is the only specimen with a fully
    # saturated 16-colour palette and reads loud against the four others.
    # A gentle blend toward the obsidian ground keeps the chromatic
    # diversity but lowers its overall key to match the plate.
    if rule_cls.__name__ == "AbiogenesisStage0Soup":
        bg = Image.new("RGB", img.size, BG)
        img = Image.blend(img, bg, 0.18)
    # Crisp pixel-art upscale, then a faint Gaussian softens edges so the
    # specimen reads as a photographic plate rather than a screenshot.
    img = img.resize((grid * pixel_block, grid * pixel_block), Image.NEAREST)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.6))
    return img


def vignette(img: Image.Image, strength: float = 0.55) -> Image.Image:
    """Soft radial darken — makes the specimen feel like a microscope plate."""
    w, h = img.size
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w / 2, h / 2
    r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / (max(w, h) / 2)
    fade = np.clip(1.0 - (r ** 2.6) * strength, 0.0, 1.0)
    arr = (np.asarray(img, dtype=np.float32) * fade[:, :, None]).astype(np.uint8)
    return Image.fromarray(arr, mode="RGB")


def paste_specimen(canvas: Image.Image, img: Image.Image,
                   x: int, y: int, size: int) -> None:
    sized = img.resize((size, size), Image.LANCZOS)
    sized = vignette(sized, strength=0.5)
    canvas.paste(sized, (x, y))


def draw_corner_ticks(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int,
                      gap: int = 36, leg: int = 70, stroke: int = 2,
                      color=TEAL) -> None:
    """Four corner brackets, offset outside the specimen by `gap`."""
    # Top-left
    draw.line([(x - gap, y - gap), (x - gap + leg, y - gap)], fill=color, width=stroke)
    draw.line([(x - gap, y - gap), (x - gap, y - gap + leg)], fill=color, width=stroke)
    # Top-right
    draw.line([(x + w + gap, y - gap), (x + w + gap - leg, y - gap)], fill=color, width=stroke)
    draw.line([(x + w + gap, y - gap), (x + w + gap, y - gap + leg)], fill=color, width=stroke)
    # Bottom-left
    draw.line([(x - gap, y + h + gap), (x - gap + leg, y + h + gap)], fill=color, width=stroke)
    draw.line([(x - gap, y + h + gap), (x - gap, y + h + gap - leg)], fill=color, width=stroke)
    # Bottom-right
    draw.line([(x + w + gap, y + h + gap), (x + w + gap - leg, y + h + gap)],
              fill=color, width=stroke)
    draw.line([(x + w + gap, y + h + gap), (x + w + gap, y + h + gap - leg)],
              fill=color, width=stroke)


def text_centered(draw: ImageDraw.ImageDraw, xy_center: tuple[int, int],
                  text: str, font_: ImageFont.FreeTypeFont,
                  fill=TEXT, tracking: float = 0.0) -> None:
    if tracking == 0.0:
        bbox = draw.textbbox((0, 0), text, font=font_)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        draw.text((xy_center[0] - w // 2 - bbox[0],
                   xy_center[1] - h // 2 - bbox[1]), text, font=font_, fill=fill)
        return
    # Manual letter-spacing.
    widths = [draw.textbbox((0, 0), ch, font=font_)[2] for ch in text]
    total = sum(widths) + int(tracking * (len(text) - 1))
    bbox0 = draw.textbbox((0, 0), text, font=font_)
    ascent = -bbox0[1]
    h = bbox0[3] - bbox0[1]
    x = xy_center[0] - total // 2
    y = xy_center[1] - h // 2 - bbox0[1]
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=font_, fill=fill)
        x += w + int(tracking)


def text_left(draw: ImageDraw.ImageDraw, xy: tuple[int, int],
              text: str, font_: ImageFont.FreeTypeFont,
              fill=TEXT, tracking: float = 0.0) -> None:
    if tracking == 0.0:
        draw.text(xy, text, font=font_, fill=fill)
        return
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font_, fill=fill)
        x += draw.textbbox((0, 0), ch, font=font_)[2] + int(tracking)


def text_right(draw: ImageDraw.ImageDraw, xy_right: tuple[int, int],
               text: str, font_: ImageFont.FreeTypeFont,
               fill=TEXT, tracking: float = 0.0) -> None:
    if tracking == 0.0:
        bbox = draw.textbbox((0, 0), text, font=font_)
        w = bbox[2] - bbox[0]
        draw.text((xy_right[0] - w - bbox[0], xy_right[1]),
                  text, font=font_, fill=fill)
        return
    widths = [draw.textbbox((0, 0), ch, font=font_)[2] for ch in text]
    total = sum(widths) + int(tracking * (len(text) - 1))
    x = xy_right[0] - total
    y = xy_right[1]
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=font_, fill=fill)
        x += w + int(tracking)


# ── Compose ────────────────────────────────────────────────────────────────

def draw_canvas_registration(draw: ImageDraw.ImageDraw,
                             margin: int = 80, leg: int = 40,
                             stroke: int = 1) -> None:
    """Tiny L-brackets at the four canvas corners — registration marks."""
    color = TEXT_DIM
    # Top-left
    draw.line([(margin, margin), (margin + leg, margin)], fill=color, width=stroke)
    draw.line([(margin, margin), (margin, margin + leg)], fill=color, width=stroke)
    # Top-right
    draw.line([(W - margin, margin), (W - margin - leg, margin)],
              fill=color, width=stroke)
    draw.line([(W - margin, margin), (W - margin, margin + leg)],
              fill=color, width=stroke)
    # Bottom-left
    draw.line([(margin, H - margin), (margin + leg, H - margin)],
              fill=color, width=stroke)
    draw.line([(margin, H - margin), (margin, H - margin - leg)],
              fill=color, width=stroke)
    # Bottom-right
    draw.line([(W - margin, H - margin), (W - margin - leg, H - margin)],
              fill=color, width=stroke)
    draw.line([(W - margin, H - margin), (W - margin, H - margin - leg)],
              fill=color, width=stroke)


def render() -> Path:
    canvas = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(canvas, "RGBA")
    draw_canvas_registration(draw)

    # Fonts.  This font pack lacks serif Greek glyphs; we use Roman numerals
    # in the title face (Italiana) so the catalogue numbering reads as one
    # voice with the title block.
    f_title = font("Italiana-Regular.ttf", 220)
    f_roman_hero = font("Italiana-Regular.ttf", 110)
    f_roman_sub = font("Italiana-Regular.ttf", 72)
    f_eyebrow = font("IBMPlexMono-Regular.ttf", 24)
    f_sub_it = font("CrimsonPro-Italic.ttf", 34)
    f_year = font("IBMPlexMono-Regular.ttf", 22)
    f_name = font("IBMPlexMono-Bold.ttf", 22)
    f_param = font("IBMPlexMono-Regular.ttf", 18)
    f_caption_it = font("CrimsonPro-Italic.ttf", 30)
    f_footer = font("IBMPlexMono-Regular.ttf", 20)
    f_specnum = font("IBMPlexMono-Regular.ttf", 18)

    # ── Title block ─────────────────────────────────────────────────────────
    # Tiny apparatus mark above the title.
    text_centered(draw, (W // 2, 168), "•  PLATE  XII  •",
                  f_specnum, fill=TEXT_DIM, tracking=6)
    text_centered(draw, (W // 2, 260), "PRIMA MATERIA",
                  f_title, fill=TEXT, tracking=32)
    text_centered(draw, (W // 2, 400),
                  "FIVE OBSERVATIONS ON THE COALESCENCE OF CHEMISTRY INTO PATTERN",
                  f_eyebrow, fill=TEXT_DIM, tracking=4)

    # Hairline rule under the title.
    rule_y = 450
    draw.line([(W // 2 - 360, rule_y), (W // 2 + 360, rule_y)],
              fill=TEAL + (170,), width=1)

    text_centered(draw, (W // 2, 510),
                  "from the Annals of Catalytic Silence", f_sub_it, fill=TEXT)

    # ── Hero specimen — Stage 1, Gray-Scott ─────────────────────────────────
    # Probe results showed grid=128 / steps=600 / seed=7 yields ~12% active
    # cells: a healthy spread of self-replicating spots.
    print("Rendering hero specimen (Stage 1: Gray-Scott)...")
    hero = specimen(AbiogenesisStage1GrayScott, grid=128, steps=600, seed=7,
                    pixel_block=6)
    hero_x, hero_y, hero_s = (W - 1400) // 2, 720, 1400
    # Roman numeral I, large, sitting above the specimen as the chapter mark.
    text_centered(draw, (W // 2, hero_y - 90), "I", f_roman_hero, fill=TEXT)
    paste_specimen(canvas, hero, hero_x, hero_y, hero_s)
    draw_corner_ticks(draw, hero_x, hero_y, hero_s, hero_s,
                      gap=36, leg=80, stroke=2, color=TEAL)
    # Corner annotations: discipline mark on left, citation date on right.
    text_left(draw, (hero_x - 36, hero_y - 60),
              "REACTION  ·  DIFFUSION", f_specnum, fill=TEXT_DIM, tracking=4)
    text_right(draw, (hero_x + hero_s + 36, hero_y - 60),
               "MCMLXXXV", f_specnum, fill=TEXT_DIM, tracking=4)
    # Caption row immediately under the hero.
    text_left(draw, (hero_x - 36, hero_y + hero_s + 56),
              "GRAY  ·  SCOTT", f_name, fill=TEXT, tracking=3)
    text_right(draw, (hero_x + hero_s + 36, hero_y + hero_s + 58),
               "F = 0.035    k = 0.065", f_param, fill=TEXT_DIM, tracking=2)

    # ── Sub-row: Stages 0, 2, 3, 4 ──────────────────────────────────────────
    print("Rendering supporting specimens...")
    sub_size = 410
    gap = 80
    row_w = sub_size * 4 + gap * 3
    sub_x0 = (W - row_w) // 2
    sub_y = hero_y + hero_s + 250

    # Note on parameters: each specimen wants to be caught at the
    # *moment of pattern* rather than at saturation.  RAF in particular
    # saturates to a single colour after ~60 steps — pulled back to ~22.
    subs = [
        (AbiogenesisStage0Soup,        90,  16, 3, "II",  "MCMXXIV",   "OPARIN  ·  HALDANE",  "discrete cellular ensemble"),
        (AbiogenesisStage2RAF,         80,  10, 7, "III", "MCMLXXXVI", "KAUFFMAN",            "autocatalytic closure"),
        (AbiogenesisStage3Vesicles,    96,  40, 9, "IV",  "MCMLXXIII", "HELFRICH",            "bilayer self-assembly"),
        (AbiogenesisStage4Selection,   80,  60, 4, "V",   "MCMLXXVII", "EIGEN  ·  SCHUSTER",  "hypercycle selection"),
    ]

    for i, (cls, grid, steps, seed, glyph, year, name, sub) in enumerate(subs):
        print(f"  [{i + 1}/4] {name}")
        img = specimen(cls, grid=grid, steps=steps, seed=seed, pixel_block=4)
        sx = sub_x0 + i * (sub_size + gap)
        paste_specimen(canvas, img, sx, sub_y, sub_size)
        draw_corner_ticks(draw, sx, sub_y, sub_size, sub_size,
                          gap=18, leg=44, stroke=2, color=TEAL)
        # Roman numeral above the specimen, centered — same voice as the title.
        text_centered(draw, (sx + sub_size // 2, sub_y - 78), glyph,
                      f_roman_sub, fill=TEXT)
        # Year as tiny mono under the numeral.
        text_centered(draw, (sx + sub_size // 2, sub_y - 26), year,
                      f_year, fill=TEXT_DIM, tracking=2)
        # Name + descriptor under the specimen.
        text_centered(draw, (sx + sub_size // 2, sub_y + sub_size + 50),
                      name, f_name, fill=TEXT, tracking=2)
        text_centered(draw, (sx + sub_size // 2, sub_y + sub_size + 90),
                      sub, f_param, fill=TEXT_DIM, tracking=1)

    # ── Bottom block ────────────────────────────────────────────────────────
    bottom_y = sub_y + sub_size + 200

    # Hairline rule, narrower than the title rule.
    draw.line([(W // 2 - 480, bottom_y), (W // 2 + 480, bottom_y)],
              fill=TEAL + (170,), width=1)

    f_caption_big = font("CrimsonPro-Italic.ttf", 34)
    text_centered(
        draw, (W // 2, bottom_y + 56),
        "Five plates, one event — chemistry remembers how to become.",
        f_caption_big, fill=TEXT,
    )

    # Footer line — index marks and series. PLATE moved to the top header so
    # only the institutional mark + series live here.
    footer_y = H - 80
    text_left(draw, (160, footer_y), "FOLIO  V",
              f_footer, fill=TEXT_DIM, tracking=4)
    text_centered(draw, (W // 2, footer_y),
                  "ANNALS  OF  CATALYTIC  SILENCE",
                  f_footer, fill=TEXT_DIM, tracking=6)
    text_right(draw, (W - 160, footer_y), "SERIES  MMXXVI",
               f_footer, fill=TEXT_DIM, tracking=4)

    # Save.
    out = REPO_ROOT / "docs" / "prima-materia.png"
    canvas.save(out, optimize=True)
    print(f"\nSaved -> {out}")
    return out


if __name__ == "__main__":
    render()
