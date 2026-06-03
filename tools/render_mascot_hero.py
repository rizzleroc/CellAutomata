"""Bake the amoeba hero/identity art from the shared colony geometry.

Writes the committed hero asset (``docs/amoeba_hero.png``) and a dark-ground
"colony proof" montage (``v32-colony-proof.png``, gitignored) that shows the
same amoeba scaling down to the small cells the default grid produces — a
no-display visual check of the living-colony design.

    python tools/render_mascot_hero.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))  # run `python tools/render_mascot_hero.py` from anywhere

from cellauto.mascot_image import render_amoeba  # noqa: E402
OBSIDIAN = (10, 14, 22, 255)  # #0a0e16 — Catalytic-Silence ground


def main() -> None:
    # 1) The hero: a single polished, transparent amoeba for README / About.
    hero = render_amoeba(768, happy=True, frame=8, supersample=4)
    hero_path = _ROOT / "docs" / "amoeba_hero.png"
    hero.save(hero_path)
    print(f"wrote {hero_path.relative_to(_ROOT)}  ({hero.size[0]}x{hero.size[1]})")

    # 2) Colony proof: the hero beside a row of shrinking amoebas (varied seeds),
    #    on obsidian, to prove faces stay legible down to default-grid sizes.
    pad = 28
    sizes = [96, 64, 40, 24, 16, 12]
    strip_w = sum(sizes) + pad * (len(sizes) + 1)
    canvas = Image.new("RGBA", (max(768, strip_w), 768 + 200), OBSIDIAN)
    canvas.alpha_composite(render_amoeba(640, frame=8, supersample=4), (max(768, strip_w) // 2 - 320, 24))
    x = pad
    base_y = 768 + (200 - max(sizes)) // 2
    for i, sz in enumerate(sizes):
        cell = render_amoeba(sz, frame=4 + i * 7, seed=0xCE11 + i * 9173, supersample=4)
        canvas.alpha_composite(cell, (x, base_y + (max(sizes) - sz)))
        x += sz + pad
    proof_path = _ROOT / "v32-colony-proof.png"
    canvas.convert("RGB").save(proof_path)
    print(f"wrote {proof_path.relative_to(_ROOT)}  (colony legibility proof)")


if __name__ == "__main__":
    main()
