"""Render the cellauto v3.4 release poster — a single A3 PNG in the
"Catalytic Silence" aesthetic. Pure type on obsidian, 12 specimen cards on a
strict grid. See docs/generated/catalytic_silence_v3_4.md for the philosophy.

Usage:
    python tools/render_release_poster.py

Output:
    docs/generated/release_poster_v3_4.png   (3300 x 4677 px, 300 DPI)
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ── Canvas dimensions (A3 portrait at 300 DPI) ───────────────────────────────
WIDTH = 3300
HEIGHT = 4677

# ── Catalytic Silence palette ────────────────────────────────────────────────
BG = (10, 14, 22)          # #0a0e16 — obsidian
BONE = (230, 224, 208)     # #e6e0d0 — warm bone
BONE_DIM = (140, 138, 130) # #8c8a82 — quiet bone
HAIRLINE = (31, 79, 76)    # #1f4f4c — desaturated teal
ACCENT = (57, 212, 200)    # #39d4c8 — used VERY sparingly
INK_DEEP = (60, 58, 54)    # softer-than-bone-dim for the deepest microcaps

# Outer margin (≈ 0.93" at 300 DPI).
MARGIN = 280

# ── Font paths (bundled with the canvas-design skill) ────────────────────────
SKILL_FONTS = Path(
    "C:\\Users\\guru8\\AppData\\Roaming\\Claude\\local-agent-mode-sessions"
    "\\skills-plugin\\b8479bcb-49c5-490c-9c54-5a5f7d6d20f5"
    "\\23339d37-fc49-4612-b536-c30b630a3402\\skills\\canvas-design\\canvas-fonts"
)


def load_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    """Resolve a font name to a Pillow FreeType font. Falls back to the
    default bitmap font (rare — we ship the named ones)."""
    candidates = [
        SKILL_FONTS / name,
        SKILL_FONTS / f"{name}.ttf",
        Path("C:/Windows/Fonts") / f"{name}.ttf",
    ]
    for p in candidates:
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def main() -> Path:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    # ── Fonts ────────────────────────────────────────────────────────────────
    f_display_title = load_font("Italiana-Regular.ttf", 320)
    f_display_subtitle = load_font("CrimsonPro-Italic.ttf", 72)
    f_eyebrow = load_font("IBMPlexMono-Regular.ttf", 28)
    f_section = load_font("IBMPlexMono-Bold.ttf", 26)
    f_card_number = load_font("Italiana-Regular.ttf", 156)
    f_card_title = load_font("IBMPlexMono-Bold.ttf", 30)
    f_card_principle = load_font("CrimsonPro-Italic.ttf", 32)
    f_card_citation = load_font("IBMPlexMono-Regular.ttf", 22)
    f_footer = load_font("IBMPlexMono-Regular.ttf", 24)
    f_footer_italic = load_font("CrimsonPro-Italic.ttf", 32)

    # ── Helpers ──────────────────────────────────────────────────────────────
    def text_w(text: str, font: ImageFont.FreeTypeFont) -> int:
        l, _, r, _ = draw.textbbox((0, 0), text, font=font)
        return r - l

    def text_h(text: str, font: ImageFont.FreeTypeFont) -> int:
        _, t, _, b = draw.textbbox((0, 0), text, font=font)
        return b - t

    def centered(y: int, text: str, font: ImageFont.FreeTypeFont, color) -> int:
        w = text_w(text, font)
        draw.text(((WIDTH - w) // 2, y), text, font=font, fill=color)
        return text_h(text, font)

    def wrap_text(
        text: str,
        font: ImageFont.FreeTypeFont,
        max_w: int,
    ) -> list[str]:
        words = text.split()
        lines: list[str] = []
        cur = ""
        for w in words:
            trial = cur + (" " if cur else "") + w
            if text_w(trial, font) <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    # ── Header ───────────────────────────────────────────────────────────────
    y = MARGIN
    eyebrow_text = "PLATE  XII   ·   CELLAUTO   ·   MMXXVI"
    eyebrow_h = centered(y, eyebrow_text, f_eyebrow, BONE_DIM)
    y += eyebrow_h + 28

    title_text = "cellauto"
    title_h = centered(y, title_text, f_display_title, BONE)
    y += title_h + 18

    subtitle_text = "twelve observations on the coalescence of chemistry into life"
    sub_h = centered(y, subtitle_text, f_display_subtitle, BONE)
    y += sub_h + 70

    # Top hairline (full width, accent teal).
    draw.line([(MARGIN, y), (WIDTH - MARGIN, y)], fill=ACCENT, width=2)
    y += 60

    # ── Specimen grid (4 rows × 3 cols) ──────────────────────────────────────
    # ASCII-safe forms: the bundled Italiana / CrimsonPro / IBMPlexMono fonts
    # do not all carry Greek glyphs or "⇒". The principles use "yields" /
    # "1/L" instead, so nothing renders as tofu.
    cards: list[tuple[str, str, str, str]] = [
        ("0",  "PRIMORDIAL SOUP",      "Dissolved monomers mix and condense in a reducing ocean.",      "Oparin 1924  ·  Miller 1953"),
        ("1",  "ALKALINE VENT",        "A pH gradient does the thermodynamic work.",                    "Lane & Martin 2012"),
        ("2",  "REACTION–DIFFUSION",   "Pattern formation from a four-parameter PDE.",                  "Turing 1952  ·  Pearson 1993"),
        ("3",  "MINERAL CATALYSIS",    "Polymerisation localised to montmorillonite clay.",             "Ferris 1996"),
        ("4",  "AUTOCATALYTIC SETS",   "A closed, food-generated, reflexively-autocatalytic loop.",     "Kauffman 1986  ·  Hordijk & Steel 2004"),
        ("5",  "HOMOCHIRALITY",        "Autocatalysis with mutual antagonism breaks mirror symmetry.",  "Frank 1953  ·  Soai 1995"),
        ("6",  "RNA WORLD",            "A spatial quasispecies; error catastrophe at the 1/L threshold.","Gilbert 1986  ·  Eigen 1971"),
        ("7",  "GENETIC CODE",         "Selection on the code itself drives convergence.",              "Vetsigian–Woese–Goldenfeld 2006"),
        ("8",  "COACERVATES",          "Liquid–liquid phase separation; membraneless droplets.",        "Oparin 1924  ·  Banani 2017"),
        ("9",  "VESICLE FORMATION",    "Amphiphiles self-assemble above the CMC.",                      "Hanczyc & Szostak 2003"),
        ("10", "PROTOCELL SELECTION",  "Bounded chemistry with heritable variation yields Darwin.",     "Eigen & Schuster 1977"),
        ("11", "LUCA DISTILLATION",    "The core genome shared by every surviving lineage.",            "Weiss et al. 2016"),
    ]

    grid_top = y
    grid_w = WIDTH - 2 * MARGIN
    cols = 3
    rows = 4
    col_w = grid_w // cols
    # Reserve footer space — measure now to size the grid.
    footer_height = 260
    grid_bottom = HEIGHT - MARGIN - footer_height
    grid_h = grid_bottom - grid_top
    row_h = grid_h // rows

    inner_pad_x = 80
    inner_pad_top = 80
    inner_pad_bottom = 96

    # Hairline border between cells (drawn under content).
    for r in range(rows + 1):
        yy = grid_top + r * row_h
        draw.line([(MARGIN, yy), (WIDTH - MARGIN, yy)], fill=HAIRLINE, width=1)
    for c in range(cols + 1):
        xx = MARGIN + c * col_w
        draw.line([(xx, grid_top), (xx, grid_bottom)], fill=HAIRLINE, width=1)

    # Draw each card. Layout per card (top → bottom, single column):
    #   1. STAGE  N            (eyebrow, monospace, tracked, dim)
    #   2. Big serif number    (Italiana, left-aligned, optical baseline)
    #   3. CARD TITLE          (monospace bold caps, hairline underneath)
    #   4. Italic principle    (wrapped, serif italic)
    #   5. Citation            (monospace, dim) anchored to the card bottom
    for idx, (num, title, principle, citation) in enumerate(cards):
        r = idx // cols
        c = idx % cols
        cx0 = MARGIN + c * col_w
        cy0 = grid_top + r * row_h
        text_left = cx0 + inner_pad_x
        text_right = cx0 + col_w - inner_pad_x
        max_text_w = text_right - text_left

        # 1. Tiny eyebrow above the number.
        eyebrow_card = f"STAGE  {num}"
        draw.text((text_left, cy0 + inner_pad_top), eyebrow_card, font=f_card_citation, fill=BONE_DIM)

        # 2. Big serif numeral on its own row (left-aligned, no inline collision).
        num_y = cy0 + inner_pad_top + 50
        draw.text((text_left, num_y), num, font=f_card_number, fill=BONE)
        num_h = text_h("0", f_card_number)

        # 3. Title on a new row below the numeral, hairline beneath.
        title_y = num_y + num_h + 16
        draw.text((text_left, title_y), title, font=f_card_title, fill=BONE)
        underline_y = title_y + text_h(title, f_card_title) + 16
        draw.line(
            [(text_left, underline_y), (text_right, underline_y)],
            fill=HAIRLINE, width=1,
        )

        # 4. Italic principle (wrapped).
        principle_lines = wrap_text(principle, f_card_principle, max_text_w)
        py = underline_y + 40
        line_height = text_h("Mg", f_card_principle) + 14
        for line in principle_lines:
            draw.text((text_left, py), line, font=f_card_principle, fill=BONE)
            py += line_height

        # 5. Citation pinned to the card bottom.
        cit_y = cy0 + row_h - inner_pad_bottom + 8
        draw.text((text_left, cit_y), citation, font=f_card_citation, fill=BONE_DIM)

    # ── Footer ───────────────────────────────────────────────────────────────
    footer_y = grid_bottom + 70
    # Hairline above footer.
    draw.line(
        [(MARGIN, grid_bottom + 30), (WIDTH - MARGIN, grid_bottom + 30)],
        fill=ACCENT, width=2,
    )
    line1 = "12  RULES   ·   120  TESTS   ·   MIT  LICENSE"
    centered(footer_y, line1, f_footer, BONE_DIM)
    line2 = "github.com/rizzleroc/CellAutomata"
    centered(footer_y + 80, line2, f_footer_italic, BONE)

    out = Path("docs/generated/release_poster_v3_4.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG", dpi=(300, 300))
    return out


if __name__ == "__main__":
    p = main()
    print(f"Wrote {p}  ({p.stat().st_size} bytes)")
