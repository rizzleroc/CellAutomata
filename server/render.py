"""Headless hi-res SEM render — the paywalled compute.

Builds a ``cellauto`` rule from a validated request, runs the engine for N
steps, then shades the field through the tested, tkinter-free
``SemRenderer.compose_at`` and returns PNG bytes. This is the same engine +
renderer the desktop app uses; the win here is that it runs headless on the
server and decouples render resolution from grid resolution (standing
requirement #64).

All inputs are untrusted (#42 / SEC-008): the rule must be a known field rule,
every param is range-checked against its ``ParamSpec``, and grid/steps/size are
hard-capped — both individually and via a combined work budget — before any
engine step runs.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Any

from cellauto.engine import Engine
from cellauto.renderer_sem import PALETTE_COOL_MONO, PALETTE_WARM_SEPIA, SemRenderer
from cellauto.rules import REGISTRY
from server import catalog, config

_PALETTES = {PALETTE_WARM_SEPIA, PALETTE_COOL_MONO}


class RenderError(Exception):
    """A 400-class validation failure with a human-readable message."""


@dataclass(frozen=True)
class RenderRequest:
    rule: str
    preset: str | None
    params: dict[str, Any]
    seed: int | None
    grid: int
    steps: int
    size: int
    palette: str


def _as_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RenderError(f"{field} must be a number")
    return int(value)


def parse_request(body: dict) -> RenderRequest:
    if not isinstance(body, dict):
        raise RenderError("request body must be a JSON object")
    rule = str(body.get("rule", "")).strip()
    if not catalog.is_field_rule(rule):
        raise RenderError(f"unknown or unsupported rule: {rule!r}")

    s = config.settings
    grid = _as_int(body.get("grid", 200), "grid")
    steps = _as_int(body.get("steps", 400), "steps")
    size = _as_int(body.get("size", 2048), "size")
    palette = str(body.get("palette", PALETTE_WARM_SEPIA)).strip()
    if palette not in _PALETTES:
        raise RenderError(f"palette must be one of {sorted(_PALETTES)}")

    if not (16 <= grid <= s.max_render_grid):
        raise RenderError(f"grid must be in [16, {s.max_render_grid}]")
    if not (1 <= steps <= s.max_render_steps):
        raise RenderError(f"steps must be in [1, {s.max_render_steps}]")
    if not (64 <= size <= s.max_render_size):
        raise RenderError(f"size must be in [64, {s.max_render_size}]")
    if grid * grid * steps > s.max_render_work:
        raise RenderError(
            f"requested work (grid²·steps = {grid * grid * steps:,}) exceeds the "
            f"budget {s.max_render_work:,} — reduce grid or steps"
        )

    seed_raw = body.get("seed", None)
    seed = None if seed_raw is None else _as_int(seed_raw, "seed")

    entry = catalog.rule_entry(rule)
    assert entry is not None  # is_field_rule guaranteed it

    preset = body.get("preset", None)
    if preset is not None:
        preset = str(preset).strip()
        if not entry.presets:
            raise RenderError(f"rule {rule!r} has no regimes/presets")
        if preset not in entry.presets:
            raise RenderError(f"preset must be one of {list(entry.presets)}")

    raw_params = body.get("params", {}) or {}
    if not isinstance(raw_params, dict):
        raise RenderError("params must be an object")
    specs = entry.param_specs()
    params: dict[str, Any] = {}
    for key, value in raw_params.items():
        spec = specs.get(key)
        if spec is None:
            raise RenderError(f"unknown param {key!r} for rule {rule!r}")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise RenderError(f"param {key!r} must be a number")
        if not (spec.lo <= value <= spec.hi):
            raise RenderError(f"param {key!r} must be in [{spec.lo}, {spec.hi}]")
        params[key] = int(round(value)) if spec.integer else float(value)

    return RenderRequest(
        rule=rule,
        preset=preset,
        params=params,
        seed=seed,
        grid=grid,
        steps=steps,
        size=size,
        palette=palette,
    )


def _build_rule(req: RenderRequest):
    kwargs: dict[str, Any] = dict(req.params)
    if req.preset is not None:
        kwargs["preset"] = req.preset
    cls = REGISTRY[req.rule]
    try:
        return cls(**kwargs)
    except TypeError as exc:
        # A ParamSpec/field mismatch — treat as a bad request rather than a 500.
        raise RenderError(f"cannot configure {req.rule!r}: {exc}") from exc


def render_png(body: dict) -> bytes:
    """Validate ``body``, run the sim, and return a PNG micrograph as bytes.

    Raises ``RenderError`` (→ HTTP 400) for any invalid input.
    """
    req = parse_request(body)
    rule = _build_rule(req)

    engine_kwargs: dict[str, Any] = {"width": req.grid, "height": req.grid, "rule": rule}
    if req.seed is not None:
        engine_kwargs["seed"] = req.seed
    engine = Engine(**engine_kwargs)
    for _ in range(req.steps):
        engine.step()

    rgb = engine.rule.render_rgb(engine.state)

    renderer = SemRenderer(canvas=None, canvas_size=req.size, palette=req.palette)
    renderer.width = req.grid
    renderer.height = req.grid
    entry = catalog.rule_entry(req.rule)
    renderer.set_stage_label(entry.label if entry else req.rule)
    frame = renderer.compose_at(rgb, req.size)  # (size, size, 3) uint8

    from PIL import Image

    buf = BytesIO()
    Image.fromarray(frame, mode="RGB").save(buf, format="PNG")
    return buf.getvalue()
