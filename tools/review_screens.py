"""Deterministic headless screenshot harness for the v4.1 application review.

Drives the REAL engine for each registered rule and writes a representative
canvas frame to docs/review/screenshots/. Field stages are rendered both in
the v3.6 viridis path (rule.render_rgb) and the v4.0 SEM path
(SemRenderer.compose, which is canvas-free and Tk-free). Discrete rules are
rendered via the shared export frame helper.

Every pixel traces to a real engine value — this is the same render_rgb /
render_cell output the GUI canvas shows, captured headlessly because this CI
container has no tkinter/display. Emits a JSON manifest (final population
stats per rule) to stdout so the review can cite real numbers.

Run:  python3 tools/review_screens.py
"""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

import numpy as np
from PIL import Image

import cellauto.renderer_sem as semmod
from cellauto import export
from cellauto.engine import Engine
from cellauto.rules import REGISTRY

OUT = Path("docs/review/screenshots")
OUT.mkdir(parents=True, exist_ok=True)
CANVAS = 600
SEED = 7

WARM = getattr(semmod, "PALETTE_WARM_SEPIA", "warm-sepia")
SEM_OK = getattr(semmod, "sem_is_available", lambda: True)()

# (steps, grid, rule_kwargs, nice stage label for the SEM badge)
PLAN: dict[str, tuple[int, int, dict, str]] = {
    # discrete
    "abiogenesis-stage0-soup": (60, 60, {}, "Stage 0 — soup"),
    "natural-selection": (60, 60, {}, "Stage 0 — soup (legacy alias)"),
    "conway": (120, 80, {}, "Conway — Life"),
    "wolfram1d": (118, 120, {"rule_number": 110}, "Wolfram — Rule 110"),
    # field
    "abiogenesis-stage1-grayscott": (1500, 110, {}, "Stage I — Gray-Scott"),
    "abiogenesis-stage2-raf": (400, 100, {}, "Stage V — RAF / Kauffman"),
    "abiogenesis-stage3-vesicles": (600, 100, {}, "Stage X — vesicles"),
    "abiogenesis-stage4-selection": (500, 100, {}, "Stage XI — protocell selection"),
    "abiogenesis-hydrothermal-vent": (400, 100, {}, "Stage II — alkaline vent"),
    "abiogenesis-mineral-catalysis": (500, 100, {}, "Stage IV — mineral catalysis"),
    "abiogenesis-homochirality": (600, 100, {}, "Stage VI — homochirality"),
    "abiogenesis-rna-world": (350, 100, {}, "Stage VII — RNA world"),
    "abiogenesis-coacervate": (800, 100, {}, "Stage IX — coacervates"),
    "abiogenesis-genetic-code": (350, 100, {}, "Stage VIII — genetic code"),
    "abiogenesis-luca": (350, 100, {}, "Stage XII — LUCA"),
    "abiogenesis-pipeline": (500, 100, {}, "Pipeline — 5-stage"),
    "abiogenesis-pipeline-extended": (700, 100, {}, "Pipeline — extended"),
}


def save_field(rgb: np.ndarray, path: Path) -> None:
    Image.fromarray(np.asarray(rgb, dtype=np.uint8), "RGB").resize(
        (CANVAS, CANVAS), Image.Resampling.NEAREST
    ).save(path)


def save_sem(rgb: np.ndarray, label: str, path: Path) -> bool:
    try:
        r = semmod.SemRenderer(canvas=None, canvas_size=CANVAS, palette=WARM, stage_label=label)
        out = r.compose(np.asarray(rgb, dtype=np.uint8))
        Image.fromarray(np.asarray(out, dtype=np.uint8), "RGB").save(path)
        return True
    except Exception as exc:  # SEM failures are themselves findings — record them
        print(f"    SEM FAILED for {label}: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return False


def save_discrete(rule, state, w: int, h: int, path: Path) -> None:
    cells = [[rule.render_cell(state, x, y) for x in range(w)] for y in range(h)]
    frame = {"kind": "discrete", "width": w, "height": h, "cells": cells, "canvas_size": CANVAS}
    export._frame_to_image(frame).save(path)


def main() -> int:
    manifest: list[dict] = []
    for name, (steps, grid, kwargs, label) in PLAN.items():
        rec: dict = {"rule": name, "steps": steps, "grid": grid}
        try:
            rule = REGISTRY[name](**kwargs)
            eng = Engine(width=grid, height=grid, rule=rule, seed=SEED)
            kind = getattr(rule, "renderer_kind", "discrete")
            for _ in range(steps):
                eng.step()
            try:
                rec["population"] = {k: (int(v) if isinstance(v, (int, np.integer)) else v)
                                     for k, v in dict(eng.population()).items()}
            except Exception as exc:
                rec["population_error"] = f"{exc.__class__.__name__}: {exc}"
            rec["kind"] = kind
            if kind == "field":
                rgb = rule.render_rgb(eng.state)
                rec["render_rgb_shape"] = list(np.asarray(rgb).shape)
                vp = OUT / f"{name}.png"
                save_field(rgb, vp)
                rec["viridis"] = str(vp)
                if SEM_OK:
                    sp = OUT / f"{name}_sem.png"
                    if save_sem(rgb, label, sp):
                        rec["sem"] = str(sp)
            else:
                vp = OUT / f"{name}.png"
                save_discrete(rule, eng.state, eng.grid.width, eng.grid.height, vp)
                rec["render"] = str(vp)
            print(f"OK  {name:36s} kind={kind:8s} steps={steps} -> {OUT/name}.png")
        except Exception as exc:
            rec["error"] = f"{exc.__class__.__name__}: {exc}"
            rec["traceback"] = traceback.format_exc().splitlines()[-4:]
            print(f"ERR {name:36s} {exc.__class__.__name__}: {exc}", file=sys.stderr)
        manifest.append(rec)

    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print("\n=== MANIFEST (final populations) ===")
    print(json.dumps(manifest, indent=2))
    n_ok = sum(1 for r in manifest if "error" not in r)
    n_sem = sum(1 for r in manifest if "sem" in r)
    print(f"\nrendered {n_ok}/{len(manifest)} rules; {n_sem} SEM frames; SEM_available={SEM_OK}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
