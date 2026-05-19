"""CLI entry: `python -m cellauto <subcommand>` (or just `cellauto` after install).

Subcommands:
    gui       launch the Tk sandbox
    simulate  headless: run N steps and print final population (and optionally save)
    export    headless: run N steps and write a GIF
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from cellauto.engine import Engine
from cellauto.export import export_gif
from cellauto.rules import REGISTRY


def _make_engine(args: argparse.Namespace) -> Engine:
    if args.load:
        return Engine.load(args.load, REGISTRY)
    if args.rule not in REGISTRY:
        raise SystemExit(f"unknown rule '{args.rule}'. Available: {', '.join(REGISTRY)}")
    rule = REGISTRY[args.rule]()
    kwargs = {"width": args.grid, "height": args.grid, "rule": rule}
    if args.seed is not None:
        kwargs["seed"] = args.seed
    return Engine(**kwargs)


def cmd_gui(args: argparse.Namespace) -> None:
    from cellauto.app import run
    run(rule_name=args.rule, grid_size=args.grid, seed=args.seed)


def cmd_simulate(args: argparse.Namespace) -> None:
    engine = _make_engine(args)
    for _ in range(args.steps):
        engine.step()
    out = {
        "rule": engine.rule.name,
        "seed": engine.seed,
        "step_count": engine.step_count,
        "population": dict(engine.population()),
    }
    print(json.dumps(out, indent=2))
    if args.save:
        engine.save(args.save)


def cmd_export(args: argparse.Namespace) -> None:
    engine = _make_engine(args)
    frames: list[dict] = []
    for _ in range(args.steps):
        rule = engine.rule
        cells = [[rule.render_cell(engine.grid.cells[y][x]) for x in range(engine.grid.width)]
                 for y in range(engine.grid.height)]
        frames.append({"width": engine.grid.width, "height": engine.grid.height,
                       "cells": cells, "canvas_size": args.canvas})
        engine.step()
    out = Path(args.out)
    export_gif(frames, out, fps=args.fps)
    print(f"wrote {out} ({len(frames)} frames @ {args.fps} fps)")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cellauto", description="Pluggable cellular automata sandbox.")
    p.add_argument("--log-level", default="INFO", help="DEBUG, INFO, WARNING, ERROR")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--rule", default="natural-selection", choices=list(REGISTRY))
        sp.add_argument("--grid", type=int, default=60, help="grid edge size (square)")
        sp.add_argument("--seed", type=int, default=None, help="RNG seed for reproducibility")
        sp.add_argument("--load", default=None, help="load a snapshot.json instead of starting fresh")

    sp_gui = sub.add_parser("gui", help="launch the Tk sandbox")
    add_common(sp_gui)
    sp_gui.set_defaults(func=cmd_gui)

    sp_sim = sub.add_parser("simulate", help="run N steps headlessly and print stats")
    add_common(sp_sim)
    sp_sim.add_argument("--steps", type=int, default=100)
    sp_sim.add_argument("--save", default=None, help="optional path to save final snapshot.json")
    sp_sim.set_defaults(func=cmd_simulate)

    sp_exp = sub.add_parser("export", help="run N steps and write an animated GIF")
    add_common(sp_exp)
    sp_exp.add_argument("--steps", type=int, default=60)
    sp_exp.add_argument("--fps", type=int, default=8)
    sp_exp.add_argument("--canvas", type=int, default=600, help="output GIF size in px")
    sp_exp.add_argument("--out", default="exports/run.gif")
    sp_exp.set_defaults(func=cmd_export)

    return p


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper()),
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    args.func(args)


if __name__ == "__main__":
    main(sys.argv[1:])
