"""High-resolution, high-complexity mandalas. Evolve a scatter-seeded
reaction-diffusion field at a large grid (busy, intricate texture everywhere),
then fold with a polar kaleidoscope directly at 4K-class output resolution.

  python3 tools/mandala_hires.py
"""
from __future__ import annotations
import os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mandala as M
from cellauto.engine import Engine
from cellauto.rules import REGISTRY

RULE = M.RULE


def evolve_scatter(kw, grid, steps, seed=1):
    rule = REGISTRY[RULE](**kw)
    eng = Engine(width=grid, height=grid, rule=rule, seed=seed)
    rng = np.random.default_rng(seed)
    u = np.ones((grid, grid), np.float32); v = np.zeros((grid, grid), np.float32)
    r = 5
    for _ in range(grid // 8):
        cy = int(rng.integers(r, grid - r)); cx = int(rng.integers(r, grid - r))
        u[cy - r:cy + r, cx - r:cx + r] = 0.5; v[cy - r:cy + r, cx - r:cx + r] = 0.25
    v += rng.uniform(0, 0.02, (grid, grid)).astype(np.float32)
    eng.state.u = u; eng.state.v = np.clip(v, 0, 1)
    for _ in range(steps):
        eng.step()
    v = np.asarray(eng.state.v, np.float32)
    return v / (v.max() + 1e-6)


class Kal:
    def __init__(self, OUT, G):
        self.OUT, self.G = OUT, G
        yy, xx = np.mgrid[0:OUT, 0:OUT]
        c = OUT / 2.0
        self.R = np.hypot(xx - c, yy - c).astype(np.float32)
        self.TH = np.arctan2(yy - c, xx - c).astype(np.float32)
        r = self.R / (OUT / 2.0)
        self.mask = np.clip((0.99 - r) / 0.05, 0, 1).astype(np.float32)
        self.scale = G / float(OUT)

    def fold(self, V, n, phase=0.0, zoom=0.98):
        wedge = 2 * np.pi / n
        a = np.mod(self.TH + phase, wedge)
        a = np.minimum(a, wedge - a)
        rr = self.R * self.scale * zoom
        G = self.G
        sx = np.clip(G / 2 + rr * np.cos(a), 0, G - 1.001)
        sy = np.clip(G / 2 + rr * np.sin(a), 0, G - 1.001)
        x0 = sx.astype(np.int32); y0 = sy.astype(np.int32)
        fx = sx - x0; fy = sy - y0
        f = (V[y0, x0] * (1 - fx) * (1 - fy) + V[y0, x0 + 1] * fx * (1 - fy)
             + V[y0 + 1, x0] * (1 - fx) * fy + V[y0 + 1, x0 + 1] * fx * fy)
        return f * self.mask


def colorize(field, pal, gamma=0.72):
    hi = np.percentile(field[field > 0.01], 99.5) if (field > 0.01).any() else 1.0
    f = np.clip(field / (hi + 1e-6), 0, 1) ** gamma
    return M.PALS[pal][(f * 255).astype(np.uint8)]


def main():
    os.makedirs("media", exist_ok=True)
    SRC = {
        "chaos": dict(F=0.018, k=0.050), "labyrinth": dict(preset="labyrinth"),
        "coral": dict(F=0.0545, k=0.062), "maze": dict(F=0.026, k=0.055),
    }
    print("evolving high-grid sources (scatter-seeded) ...")
    fields = {}
    for nm, kw in SRC.items():
        fields[nm] = evolve_scatter(kw, 400, 650)
        print(f"  {nm} (grid 400)")

    heroes = [
        ("chaos", 8, "amethyst"), ("chaos", 12, "gold"),
        ("labyrinth", 6, "ice"), ("labyrinth", 16, "rose"),
        ("coral", 10, "ember"), ("maze", 14, "emerald"),
    ]
    kal = Kal(2160, 400)
    for nm, n, pal in heroes:
        img = colorize(kal.fold(fields[nm], n), pal)
        Image.fromarray(img).save(f"media/hires_{n}fold_{nm}.jpg", quality=92)
        print(f"  hero 2160 {n}-fold {nm} ({pal})")

    print("showpiece (3456, grid 460) ...")
    big = evolve_scatter(SRC["chaos"], 460, 700, seed=3)
    kal2 = Kal(3456, 460)
    Image.fromarray(colorize(kal2.fold(big, 12), "gold")).save(
        "media/hires_showpiece_12fold.jpg", quality=94)
    print("DONE — 6 heroes @2160 + 1 showpiece @3456")


if __name__ == "__main__":
    main()
