"""Render the v4.1 "Day in the Life of a Cell" narrative-channel art bundle.

Every panel is REAL output: each of the twelve extended-pipeline stages is run
headlessly through the actual simulator, composed by the grounded SEM renderer
(``cellauto.renderer_sem.SemRenderer``), then narrated by Channel B
(``cellauto.channel.NarrativeChannel``) — the anthropomorphized story layer
(protagonist + time-of-day grade + narration ribbon + STORY tag). So the bundle
is also an end-to-end smoke test of the whole Channel-A → Channel-B path at
hi-res.

Outputs (docs/generated/narrative/):
    beat_00_soup.png … beat_11_luca.png    — one composed frame per day beat
    day_in_the_life.png                     — 4×3 contact-sheet poster

Run:
    python tools/render_narrative_art.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from cellauto.channel import NarrativeChannel  # noqa: E402
from cellauto.engine import Engine  # noqa: E402
from cellauto.narrative import DAY_IN_THE_LIFE  # noqa: E402
from cellauto.renderer_sem import SemRenderer, _load_mono_font  # noqa: E402
from cellauto.rules.abiogenesis import (  # noqa: E402
    AbiogenesisStage0Soup,
    AbiogenesisStage1GrayScott,
    AbiogenesisStage2RAF,
    AbiogenesisStage3Vesicles,
    AbiogenesisStage4Selection,
)
from cellauto.rules.abiogenesis.stage_chirality import (  # noqa: E402
    AbiogenesisStageHomochirality,
)
from cellauto.rules.abiogenesis.stage_coacervate import (  # noqa: E402
    AbiogenesisStageCoacervate,
)
from cellauto.rules.abiogenesis.stage_code import AbiogenesisStageGeneticCode  # noqa: E402
from cellauto.rules.abiogenesis.stage_luca import AbiogenesisStageLUCA  # noqa: E402
from cellauto.rules.abiogenesis.stage_minerals import AbiogenesisStageMinerals  # noqa: E402
from cellauto.rules.abiogenesis.stage_rna import AbiogenesisStageRNAWorld  # noqa: E402
from cellauto.rules.abiogenesis.stage_vents import AbiogenesisStageVents  # noqa: E402

OUT_DIR = REPO_ROOT / "docs" / "generated" / "narrative"

# Extended-pipeline order (matches narrative.DAY_IN_THE_LIFE indices 0..11):
# (slug, rule_cls, grid, steps, seed).
STAGES = [
    ("soup", AbiogenesisStage0Soup, 90, 16, 3),
    ("vent", AbiogenesisStageVents, 80, 60, 5),
    ("reaction_diffusion", AbiogenesisStage1GrayScott, 80, 400, 7),
    ("minerals", AbiogenesisStageMinerals, 80, 60, 4),
    ("raf", AbiogenesisStage2RAF, 80, 22, 7),
    ("chirality", AbiogenesisStageHomochirality, 80, 120, 6),
    ("rna_world", AbiogenesisStageRNAWorld, 80, 80, 8),
    ("genetic_code", AbiogenesisStageGeneticCode, 60, 60, 9),
    ("coacervate", AbiogenesisStageCoacervate, 80, 200, 4),
    ("vesicles", AbiogenesisStage3Vesicles, 96, 40, 9),
    ("selection", AbiogenesisStage4Selection, 80, 60, 4),
    ("luca", AbiogenesisStageLUCA, 60, 80, 11),
]

PANEL = 900  # hi-res compose edge per beat — proves Channel B is resolution-free.


def specimen_rgb(rule_cls, grid: int, steps: int, seed: int) -> np.ndarray:
    """Run a rule headlessly and return its (grid, grid, 3) uint8 render output."""
    rule = rule_cls()
    eng = Engine(width=grid, height=grid, rule=rule, seed=seed)
    for _ in range(steps):
        eng.step()
    if getattr(rule, "renderer_kind", "discrete") == "field":
        return np.asarray(rule.render_rgb(eng.state), dtype=np.uint8)
    rgb = np.zeros((grid, grid, 3), dtype=np.uint8)
    for y in range(grid):
        for x in range(grid):
            color, _ = rule.render_cell(eng.state, x, y)
            rgb[y, x] = (int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16))
    return rgb


def render_beat(idx: int, slug: str, rule_cls, grid: int, steps: int, seed: int) -> Image.Image:
    """Compose one day beat: SEM micrograph (Channel A) + story overlay (Channel B)."""
    beat = DAY_IN_THE_LIFE[idx]
    palette = "cool-mono" if beat.time_of_day == "night" else "warm-sepia"

    renderer = SemRenderer(canvas=None, canvas_size=600, palette=palette)
    renderer.width, renderer.height = grid, grid
    renderer.stage_label = f"Stage {idx} — {slug.replace('_', ' ')}"

    state_rgb = specimen_rgb(rule_cls, grid, steps, seed)
    sem = renderer.compose_at(state_rgb, PANEL)  # Channel A, hi-res

    channel = NarrativeChannel(size=PANEL, palette=palette, enabled=True)
    channel.set_stage(idx, len(STAGES))
    channel._phase = (idx / len(STAGES)) % 1.0  # vary the pose/reveal per beat
    composed = channel.compose(sem)  # Channel B overlay

    print(f"  [{idx:2d}] {beat.clock}  {beat.title}  ({beat.mood}, {beat.time_of_day})")
    return Image.fromarray(composed, "RGB")


def contact_sheet(panels: list[Image.Image]) -> Image.Image:
    """Tile the twelve beats into a 4×3 poster with a title bar."""
    cols, rows = 4, 3
    cell = 460
    gap = 20
    pad = 48
    title_h = 150
    W = pad * 2 + cols * cell + (cols - 1) * gap
    H = title_h + pad * 2 + rows * cell + (rows - 1) * gap
    sheet = Image.new("RGB", (W, H), (14, 12, 10))

    from PIL import ImageDraw

    draw = ImageDraw.Draw(sheet)
    title_font = _load_mono_font(54)
    sub_font = _load_mono_font(24)
    if title_font is not None:
        draw.text((pad, 44), "A DAY IN THE LIFE OF A CELL", font=title_font, fill=(236, 224, 208))
    if sub_font is not None:
        draw.text(
            (pad, 110),
            "cellauto v4.1 · Channel B narrative over grounded SEM · twelve beats, dawn to rebirth",
            font=sub_font,
            fill=(150, 140, 128),
        )

    for i, panel in enumerate(panels):
        r, c = divmod(i, cols)
        x = pad + c * (cell + gap)
        y = title_h + pad + r * (cell + gap)
        sheet.paste(panel.resize((cell, cell), Image.LANCZOS), (x, y))
    return sheet


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 60)
    print("cellauto v4.1 — Day in the Life narrative art bundle")
    print("=" * 60)
    panels: list[Image.Image] = []
    for idx, (slug, rule_cls, grid, steps, seed) in enumerate(STAGES):
        panel = render_beat(idx, slug, rule_cls, grid, steps, seed)
        panels.append(panel)
        panel.save(OUT_DIR / f"beat_{idx:02d}_{slug}.png", optimize=True)
    sheet = contact_sheet(panels)
    sheet_path = OUT_DIR / "day_in_the_life.png"
    sheet.save(sheet_path, optimize=True)
    print(f"\nContact sheet -> {sheet_path}")
    print("Done.")


if __name__ == "__main__":
    main()
