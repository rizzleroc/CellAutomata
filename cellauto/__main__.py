"""CLI entry: `python -m cellauto <subcommand>`.

Subcommands:
    gui       launch the Tk sandbox
    web       launch the browser sandbox (Flask server)
    simulate  headless: run N steps, print final population (and optionally save)
    export    headless: run N steps and write an animated GIF

Common flags: --rule, --grid, --seed, --load. --rule-config accepts repeated
key=value pairs to set rule-specific parameters (e.g. rule_number=110 for
Wolfram, amoeba_lifespan=10 for stage 0). --stage N is a convenience for
abiogenesis-pipeline (sets starting_stage).
"""

from __future__ import annotations

import argparse
import json
import logging
import sys

from cellauto.engine import Engine
from cellauto.export import export_gif
from cellauto.rules import REGISTRY


def _parse_value(s: str):
    """Parse a CLI key=value's value into the most natural Python type."""
    if s.lower() in ("true", "false"):
        return s.lower() == "true"
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def _rule_kwargs(args: argparse.Namespace) -> dict:
    kwargs = {}
    for entry in args.rule_config or []:
        if "=" not in entry:
            raise SystemExit(f"--rule-config expects key=value, got: {entry!r}")
        k, v = entry.split("=", 1)
        kwargs[k.strip()] = _parse_value(v.strip())
    if args.stage is not None and args.rule.startswith("abiogenesis-pipeline"):
        kwargs.setdefault("starting_stage", args.stage)
    return kwargs


def _make_engine(args: argparse.Namespace) -> Engine:
    if args.load:
        return Engine.load(args.load, REGISTRY)
    if args.rule not in REGISTRY:
        raise SystemExit(f"unknown rule '{args.rule}'. Available: {', '.join(REGISTRY)}")
    rule_cls = REGISTRY[args.rule]
    rule = rule_cls(**_rule_kwargs(args))
    kwargs = {"width": args.grid, "height": args.grid, "rule": rule}
    if args.seed is not None:
        kwargs["seed"] = args.seed
    return Engine(**kwargs)


def cmd_gui(args: argparse.Namespace) -> None:
    from cellauto.app import run

    # GUI ignores --rule-config / --stage at construction time but the rule
    # picker can switch to any rule once running. (P1 followup: pass kwargs.)
    if args.load:
        # Easiest path: launch GUI and immediately load snapshot. The GUI's
        # File>Open does this anyway, but for scripted launches we wire it.
        from tkinter import Tk

        from cellauto.app import App

        root = Tk()
        app = App(root, rule_name=args.rule, grid_size=args.grid, seed=args.seed)
        app._stop()
        app.engine = Engine.load(args.load, REGISTRY)
        app.rule_var.set(app.engine.rule.name)
        app._init_renderer()
        app._render()
        app._update_status()
        root.mainloop()
        return
    run(rule_name=args.rule, grid_size=args.grid, seed=args.seed)


def cmd_web(args: argparse.Namespace) -> None:
    from cellauto.web import run

    run(host=args.host, port=args.port, debug=args.debug)


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
    from pathlib import Path

    frames: list[dict] = []
    for _ in range(args.steps):
        kind = getattr(engine.rule, "renderer_kind", "discrete")
        if kind == "field":
            rgb = engine.rule.render_rgb(engine.state)
            frames.append({"kind": "field", "rgb": rgb.tolist(), "canvas_size": args.canvas})
        else:
            w, h = engine.grid.width, engine.grid.height
            cells = [[engine.rule.render_cell(engine.state, x, y) for x in range(w)] for y in range(h)]
            frames.append(
                {"kind": "discrete", "width": w, "height": h, "cells": cells, "canvas_size": args.canvas}
            )
        engine.step()
    out = Path(args.out)
    export_gif(frames, out, fps=args.fps)
    print(f"wrote {out} ({len(frames)} frames @ {args.fps} fps)")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cellauto", description="Pluggable cellular automata + abiogenesis sandbox."
    )
    p.add_argument("--log-level", default="INFO", help="DEBUG, INFO, WARNING, ERROR")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--rule", default="abiogenesis-pipeline", choices=list(REGISTRY))
        sp.add_argument("--grid", type=int, default=60, help="grid edge size (square)")
        sp.add_argument("--seed", type=int, default=None, help="RNG seed")
        sp.add_argument("--load", default=None, help="load snapshot.json instead of new")
        sp.add_argument(
            "--rule-config",
            action="append",
            default=[],
            metavar="key=value",
            help="repeatable rule-specific parameter, e.g. rule_number=110",
        )
        sp.add_argument(
            "--stage",
            type=int,
            default=None,
            help="for abiogenesis-pipeline: starting stage 0-4; "
            "for abiogenesis-pipeline-extended: starting stage 0-11",
        )

    sp_gui = sub.add_parser("gui", help="launch the Tk sandbox")
    add_common(sp_gui)
    sp_gui.set_defaults(func=cmd_gui)

    sp_web = sub.add_parser("web", help="launch the browser sandbox (Flask)")
    sp_web.add_argument("--host", default="127.0.0.1", help="bind address (use 0.0.0.0 for LAN)")
    sp_web.add_argument("--port", type=int, default=8765, help="bind port")
    sp_web.add_argument("--debug", action="store_true", help="Flask debug mode")
    sp_web.set_defaults(func=cmd_web)

    sp_sim = sub.add_parser("simulate", help="run N steps headlessly")
    add_common(sp_sim)
    sp_sim.add_argument("--steps", type=int, default=100)
    sp_sim.add_argument("--save", default=None, help="optional snapshot.json path")
    sp_sim.set_defaults(func=cmd_simulate)

    sp_exp = sub.add_parser("export", help="run N steps and write animated GIF")
    add_common(sp_exp)
    sp_exp.add_argument("--steps", type=int, default=60)
    sp_exp.add_argument("--fps", type=int, default=8)
    sp_exp.add_argument("--canvas", type=int, default=600, help="output GIF size px")
    sp_exp.add_argument("--out", default="exports/run.gif")
    sp_exp.set_defaults(func=cmd_export)
    return p


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    args.func(args)


if __name__ == "__main__":
    main(sys.argv[1:])
