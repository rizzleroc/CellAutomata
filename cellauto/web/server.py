"""Flask server exposing the cellauto Engine over HTTP.

API surface (all JSON unless noted):
    GET    /                                  index page (the SPA)
    GET    /api/health                        liveness probe
    GET    /api/rules                         list available rules + tutorial copy
    GET    /api/rules/<name>/params           param spec for a rule (slider metadata)
    GET    /api/rules/<name>/presets          named presets (Gray-Scott regimes etc.)
    POST   /api/sessions                      body: {rule, grid, seed?, config?} → {session_id, ...}
    GET    /api/sessions/<sid>                current state (step_count, fps, population, stage info)
    POST   /api/sessions/<sid>/step           body: {n: int} → state after stepping
    POST   /api/sessions/<sid>/reset          body: {rule?, grid?, seed?, config?}
    DELETE /api/sessions/<sid>
    GET    /api/sessions/<sid>/params         live param values for the current rule (or inner stage)
    POST   /api/sessions/<sid>/params         body: {key: value, ...} → reapplies live (rebuilds if reinit)
    POST   /api/sessions/<sid>/preset         body: {name: preset_name} (Gray-Scott)
    POST   /api/sessions/<sid>/promote        manual pipeline stage promotion
    POST   /api/sessions/<sid>/stage          body: {stage: int} jump to stage N (pipeline)
    POST   /api/sessions/<sid>/auto_promote   body: {enabled: bool, duration?: int}
    GET    /api/sessions/<sid>/snapshot.json  download a snapshot file
    POST   /api/sessions/<sid>/load           body: snapshot dict → replace engine
    GET    /api/sessions/<sid>/frame.png      rendered RGB PNG; ?download=1 forces attachment
    POST   /api/sessions/<sid>/gif            body: {steps, fps, canvas?} → image/gif bytes

Sessions live in-memory keyed by UUID. The server is meant for local /
single-user use — there is no auth, no quota, and no persistence beyond
process lifetime.
"""

from __future__ import annotations

import io
import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from cellauto.engine import Engine
from cellauto.rules import REGISTRY
from cellauto.rules.params import PARAM_SPECS, PEARSON_PRESET_RULES
from cellauto.tutorial import tutorial_for

log = logging.getLogger(__name__)

# Hard caps so a bad client can't OOM the server.
MAX_GRID = 240
MAX_STEPS_PER_REQUEST = 50
MAX_GIF_STEPS = 240
MAX_SESSIONS = 64
MAX_SNAPSHOT_BYTES = 50 * 1024 * 1024  # 50 MB; large pipelines + 200² grids can get fat

# Named scientific presets surfaced to the UI. Right now only Gray-Scott
# has them, but the dispatch is keyed by rule name so adding more is just
# a registry entry.
PRESET_REGISTRY: dict[str, dict[str, dict[str, float]]] = {}


def _gray_scott_presets() -> dict[str, dict[str, float]]:
    from cellauto.rules.abiogenesis.science import GRAY_SCOTT_PRESETS

    return {name: {"F": F, "k": k} for name, (F, k) in GRAY_SCOTT_PRESETS.items()}


def _build_preset_registry() -> dict[str, dict[str, dict[str, float]]]:
    out: dict[str, dict[str, dict[str, float]]] = {}
    for rule in PEARSON_PRESET_RULES:
        out[rule] = _gray_scott_presets()
    return out


PRESET_REGISTRY = _build_preset_registry()


def _parse_value(s: Any) -> Any:
    """Coerce stringly-typed JSON config values to int/float/bool when natural.

    The Tk GUI's rule picker passes raw types; HTML form inputs send strings.
    This mirrors ``cellauto.__main__._parse_value``.
    """
    if not isinstance(s, str):
        return s
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


def _make_engine(rule_name: str, grid: int, seed: int | None, config: dict | None) -> Engine:
    if rule_name not in REGISTRY:
        raise ValueError(f"unknown rule '{rule_name}'")
    if not (4 <= grid <= MAX_GRID):
        raise ValueError(f"grid must be 4..{MAX_GRID}, got {grid}")
    rule_cls = REGISTRY[rule_name]
    kwargs = {k: _parse_value(v) for k, v in (config or {}).items()}
    rule = rule_cls(**kwargs) if kwargs else rule_cls()
    eng_kwargs: dict[str, Any] = {"width": grid, "height": grid, "rule": rule}
    if seed is not None:
        eng_kwargs["seed"] = int(seed)
    return Engine(**eng_kwargs)


def _render_png(engine: Engine) -> bytes:
    """Render the current state to a PNG.

    Every rule implements ``render_rgb`` returning (H, W, 3) uint8 — see
    the Rule protocol. We hand that to PIL and ship the result. No scaling
    is done server-side; the client uses ``image-rendering: pixelated`` so
    the upscaled canvas stays crisp.
    """
    from PIL import Image

    rgb = engine.rule.render_rgb(engine.state)
    arr = np.asarray(rgb, dtype=np.uint8)
    if arr.ndim != 3 or arr.shape[2] != 3:
        raise RuntimeError(f"rule '{engine.rule.name}' produced bad rgb shape {arr.shape}")
    img = Image.fromarray(arr, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=False)
    return buf.getvalue()


def _active_rule(engine: Engine) -> Any:
    """Return the rule whose parameters are 'currently active'.

    For pipeline rules this is the inner rule of the active stage so the
    UI shows the sliders that actually affect what the user is looking at.
    """
    state = engine.state
    inner = getattr(state, "inner_rule", None)
    return inner if inner is not None else engine.rule


def _stage_info(engine: Engine) -> dict | None:
    """If this engine runs a pipeline rule, return display metadata for the
    current stage; otherwise None."""
    state = engine.state
    rule = engine.rule
    if not hasattr(rule, "stage_info_for") or not hasattr(state, "current_stage"):
        return None
    info = rule.stage_info_for(state.current_stage)
    total = len(getattr(rule, "stage_classes", ()))
    # Surface every stage's title so the frontend can label the full stage
    # dropdown ("0 — Primordial soup" / "1 — Reaction-diffusion" / …) rather
    # than only the currently-selected one.
    stages = []
    for i in range(total):
        si = rule.stage_info_for(i)
        stages.append({"index": i, "title": si.title})
    return {
        "index": info.index,
        "title": info.title,
        "principle": info.principle,
        "detail": info.detail,
        "citation": info.citation,
        "legend": info.legend,
        "current_stage": state.current_stage,
        "total_stages": total,
        "stages": stages,
        "auto_promote": bool(getattr(rule, "auto_promote", False)),
        "stage_duration": int(getattr(rule, "stage_duration", 0)),
    }


def _state_summary(engine: Engine) -> dict:
    out: dict[str, Any] = {
        "rule": engine.rule.name,
        "grid": engine.width,
        "seed": engine.seed,
        "step_count": engine.step_count,
        "fps": round(engine.fps(), 1),
        "population": dict(engine.population()),
    }
    info = _stage_info(engine)
    if info is not None:
        out["stage_info"] = info
    return out


def _param_payload(engine: Engine) -> dict:
    """Build the param-control payload for the rule whose knobs the user
    should see (the active stage of a pipeline, or the rule itself).

    Some rules (Gray-Scott) default ``F``/``k`` to ``None`` and resolve
    them from a named preset at step time. If we returned ``None`` to the
    client the slider would render at midpoint and lie about what the sim
    is actually running. Fall back to the preset's value so the slider
    starts where the chemistry actually is.
    """
    active = _active_rule(engine)
    specs = PARAM_SPECS.get(active.name, [])
    preset_bank = PRESET_REGISTRY.get(active.name, {})
    preset_name = getattr(active, "preset", None) if preset_bank else None
    preset_values = preset_bank.get(preset_name, {}) if preset_name else {}
    params = []
    for spec in specs:
        value = getattr(active, spec.attr, None)
        if value is None and spec.attr in preset_values:
            value = preset_values[spec.attr]
        params.append(
            {
                "attr": spec.attr,
                "label": spec.label,
                "lo": spec.lo,
                "hi": spec.hi,
                "step": spec.step,
                "integer": spec.integer,
                "reinit": spec.reinit,
                "value": value,
            }
        )
    return {
        "rule": active.name,
        "params": params,
        "presets": sorted(preset_bank.keys()),
        "active_preset": preset_name,
    }


def _apply_params(engine: Engine, updates: dict[str, Any]) -> tuple[list[str], bool]:
    """Apply parameter changes to the active rule.

    Returns (applied_keys, did_reinit). ``reinit`` params (n_species etc.)
    rebuild the inner state from scratch so structural changes take effect;
    live params are just attribute writes.
    """
    active = _active_rule(engine)
    specs_by_attr = {s.attr: s for s in PARAM_SPECS.get(active.name, [])}
    applied: list[str] = []
    needs_reinit = False
    for key, raw in updates.items():
        spec = specs_by_attr.get(key)
        if spec is None:
            continue
        value: Any = int(raw) if spec.integer else float(raw)
        # Clamp to spec range so a malicious / buggy client can't push
        # the rule outside the science-valid envelope.
        value = max(spec.lo, min(spec.hi, value))
        if spec.integer:
            value = int(value)
        setattr(active, spec.attr, value)
        applied.append(spec.attr)
        if spec.reinit:
            needs_reinit = True
    if needs_reinit:
        # Rebuild the active rule's state in place. For pipeline rules this
        # is the inner stage's state; for standalone rules it's engine.state.
        pip_state = getattr(engine.state, "inner_state", None)
        if pip_state is not None:
            engine.state.inner_state = active.init_state(engine.width, engine.height)
        else:
            engine.state = engine.rule.init_state(engine.width, engine.height)
        # Zero the step counter so the UI's "step: N" stays consistent with
        # the fresh state. Wolfram 1D is especially obvious about this — its
        # canvas is an accumulated history, so without the reset the stats
        # say "step: 5" but the canvas shows only the seed pixel.
        engine.step_count = 0
        engine._step_durations.clear()
    return applied, needs_reinit


def _capture_frame(engine: Engine, canvas: int) -> dict:
    """Snapshot the current state in the format export_gif expects.

    Mirrors the shape used by ``cellauto export`` (see __main__.cmd_export).
    """
    rule = engine.rule
    kind = getattr(rule, "renderer_kind", "discrete")
    if kind == "field":
        rgb = rule.render_rgb(engine.state)
        return {"kind": "field", "rgb": np.asarray(rgb, dtype=np.uint8).tolist(), "canvas_size": canvas}
    w = engine.grid.width
    h = engine.grid.height
    cells = [[rule.render_cell(engine.state, x, y) for x in range(w)] for y in range(h)]
    return {"kind": "discrete", "width": w, "height": h, "cells": cells, "canvas_size": canvas}


@dataclass
class _Session:
    engine: Engine
    last_touched: float = field(default_factory=time.time)
    # Per-session lock so /step, /gif, /params, etc. don't mutate the
    # same Engine concurrently. Werkzeug's threaded dev server and
    # gunicorn (with threads > 1) can both interleave requests for the
    # same session — without this the GIF render races the play loop on
    # shared NumPy buffers and the step counter desyncs.
    lock: threading.Lock = field(default_factory=threading.Lock)


class _SessionStore:
    """Thread-safe dict of in-memory sessions with simple LRU eviction.

    Werkzeug's dev server is multi-threaded by default; without a lock we
    race on the engine state during concurrent /step + /frame.png hits
    from the same browser tab.
    """

    def __init__(self, capacity: int = MAX_SESSIONS) -> None:
        self.capacity = capacity
        self._sessions: dict[str, _Session] = {}
        self._lock = threading.Lock()

    def create(self, engine: Engine) -> str:
        sid = uuid.uuid4().hex
        with self._lock:
            if len(self._sessions) >= self.capacity:
                # Evict the least-recently-touched session.
                oldest = min(self._sessions.items(), key=lambda kv: kv[1].last_touched)[0]
                del self._sessions[oldest]
            self._sessions[sid] = _Session(engine=engine)
        return sid

    def get(self, sid: str) -> _Session | None:
        with self._lock:
            s = self._sessions.get(sid)
            if s is not None:
                s.last_touched = time.time()
            return s

    def delete(self, sid: str) -> bool:
        with self._lock:
            return self._sessions.pop(sid, None) is not None

    def replace_engine(self, sid: str, engine: Engine) -> _Session | None:
        with self._lock:
            s = self._sessions.get(sid)
            if s is None:
                return None
            s.engine = engine
            s.last_touched = time.time()
            return s


def build_app() -> Any:
    """Construct the Flask app. Imported lazily so the core package keeps
    working when Flask isn't installed."""
    try:
        from flask import Flask, abort, jsonify, request, send_from_directory
    except ImportError as e:
        raise SystemExit(
            'The web server needs Flask. Install with:\n    pip install -e ".[web]"\nor: pip install flask'
        ) from e

    from pathlib import Path

    static_dir = Path(__file__).parent / "static"
    app = Flask(__name__, static_folder=str(static_dir), static_url_path="/static")
    app.config["MAX_CONTENT_LENGTH"] = MAX_SNAPSHOT_BYTES
    store = _SessionStore()

    def _require(sid: str) -> _Session:
        """Fetch a session or 404. Extracted so mypy can see the non-None
        return path; ``flask.abort`` is typed as ``NoReturn`` upstream but
        CI runs mypy with ``--ignore-missing-imports`` so the assert keeps
        the narrowing explicit."""
        s = store.get(sid)
        if s is None:
            abort(404)
        assert s is not None
        return s

    @app.get("/")
    def index() -> Any:
        return send_from_directory(str(static_dir), "index.html")

    @app.get("/api/health")
    def health() -> Any:
        # Cheap liveness probe for Railway / load balancers. Doesn't touch
        # the session store so an unhealthy store still gets restarted.
        return jsonify({"status": "ok", "rules": len(REGISTRY)})

    @app.get("/api/rules")
    def list_rules() -> Any:
        return jsonify({"rules": [{"name": name, "tutorial": list(tutorial_for(name))} for name in REGISTRY]})

    @app.get("/api/rules/<name>/params")
    def rule_params(name: str) -> Any:
        if name not in REGISTRY:
            abort(404)
        specs = PARAM_SPECS.get(name, [])
        return jsonify(
            {
                "rule": name,
                "params": [
                    {
                        "attr": s.attr,
                        "label": s.label,
                        "lo": s.lo,
                        "hi": s.hi,
                        "step": s.step,
                        "integer": s.integer,
                        "reinit": s.reinit,
                    }
                    for s in specs
                ],
                "presets": sorted(PRESET_REGISTRY.get(name, {}).keys()),
            }
        )

    @app.get("/api/rules/<name>/presets")
    def rule_presets(name: str) -> Any:
        if name not in REGISTRY:
            abort(404)
        return jsonify({"rule": name, "presets": PRESET_REGISTRY.get(name, {})})

    @app.post("/api/sessions")
    def create_session() -> Any:
        data = request.get_json(silent=True) or {}
        try:
            engine = _make_engine(
                rule_name=data.get("rule", "abiogenesis-pipeline"),
                grid=int(data.get("grid", 80)),
                seed=data.get("seed"),
                config=data.get("config"),
            )
        except (ValueError, TypeError) as e:
            return jsonify({"error": str(e)}), 400
        sid = store.create(engine)
        return jsonify({"session_id": sid, **_state_summary(engine)})

    @app.get("/api/sessions/<sid>")
    def get_session(sid: str) -> Any:
        s = _require(sid)
        with s.lock:
            return jsonify(_state_summary(s.engine))

    @app.post("/api/sessions/<sid>/step")
    def step_session(sid: str) -> Any:
        s = _require(sid)
        data = request.get_json(silent=True) or {}
        n = int(data.get("n", 1))
        if not (1 <= n <= MAX_STEPS_PER_REQUEST):
            return jsonify({"error": f"n must be 1..{MAX_STEPS_PER_REQUEST}"}), 400
        with s.lock:
            for _ in range(n):
                s.engine.step()
            return jsonify(_state_summary(s.engine))

    @app.post("/api/sessions/<sid>/reset")
    def reset_session(sid: str) -> Any:
        s = _require(sid)
        data = request.get_json(silent=True) or {}
        try:
            engine = _make_engine(
                rule_name=data.get("rule", s.engine.rule.name),
                grid=int(data.get("grid", s.engine.width)),
                seed=data.get("seed"),
                config=data.get("config"),
            )
        except (ValueError, TypeError) as e:
            return jsonify({"error": str(e)}), 400
        with s.lock:
            store.replace_engine(sid, engine)
        return jsonify(_state_summary(engine))

    @app.delete("/api/sessions/<sid>")
    def delete_session(sid: str) -> Any:
        if not store.delete(sid):
            abort(404)
        return ("", 204)

    @app.get("/api/sessions/<sid>/params")
    def session_params(sid: str) -> Any:
        s = _require(sid)
        with s.lock:
            return jsonify(_param_payload(s.engine))

    @app.post("/api/sessions/<sid>/params")
    def session_set_params(sid: str) -> Any:
        s = _require(sid)
        data = request.get_json(silent=True) or {}
        with s.lock:
            try:
                applied, reinit = _apply_params(s.engine, data)
            except (TypeError, ValueError) as e:
                return jsonify({"error": str(e)}), 400
            return jsonify({"applied": applied, "reinit": reinit, **_state_summary(s.engine)})

    @app.post("/api/sessions/<sid>/preset")
    def session_set_preset(sid: str) -> Any:
        s = _require(sid)
        data = request.get_json(silent=True) or {}
        name = data.get("name", "")
        with s.lock:
            active = _active_rule(s.engine)
            bank = PRESET_REGISTRY.get(active.name, {})
            if name not in bank:
                return jsonify({"error": f"unknown preset '{name}' for rule {active.name}"}), 400
            _apply_params(s.engine, bank[name])
            # Some rules (Gray-Scott) also track which preset is active for
            # their serialised config; set it if the attr exists.
            if hasattr(active, "preset"):
                active.preset = name
            return jsonify({"preset": name, **_state_summary(s.engine)})

    @app.post("/api/sessions/<sid>/promote")
    def session_promote(sid: str) -> Any:
        s = _require(sid)
        rule = s.engine.rule
        if not hasattr(rule, "promote"):
            return jsonify({"error": f"rule {rule.name} is not a pipeline"}), 400
        with s.lock:
            rule.promote(s.engine.state)
            return jsonify(_state_summary(s.engine))

    @app.post("/api/sessions/<sid>/stage")
    def session_set_stage(sid: str) -> Any:
        s = _require(sid)
        rule = s.engine.rule
        if not hasattr(rule, "set_stage"):
            return jsonify({"error": f"rule {rule.name} is not a pipeline"}), 400
        data = request.get_json(silent=True) or {}
        try:
            n = int(data.get("stage", 0))
        except (TypeError, ValueError):
            return jsonify({"error": "stage must be an integer"}), 400
        with s.lock:
            rule.set_stage(s.engine.state, n)
            return jsonify(_state_summary(s.engine))

    @app.post("/api/sessions/<sid>/auto_promote")
    def session_auto_promote(sid: str) -> Any:
        s = _require(sid)
        rule: Any = s.engine.rule
        if not hasattr(rule, "auto_promote"):
            return jsonify({"error": f"rule {rule.name} is not a pipeline"}), 400
        data = request.get_json(silent=True) or {}
        with s.lock:
            if "enabled" in data:
                rule.auto_promote = bool(data["enabled"])
            if "duration" in data:
                try:
                    rule.stage_duration = max(1, int(data["duration"]))
                except (TypeError, ValueError):
                    return jsonify({"error": "duration must be an integer"}), 400
            return jsonify(_state_summary(s.engine))

    @app.get("/api/sessions/<sid>/snapshot.json")
    def session_snapshot(sid: str) -> Any:
        import json

        s = _require(sid)
        with s.lock:
            body = json.dumps(s.engine.to_dict(), indent=2).encode("utf-8")
            filename = f"cellauto-{s.engine.rule.name}-step{s.engine.step_count}.json"
        resp = app.response_class(body, mimetype="application/json")
        resp.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        return resp

    @app.post("/api/sessions/<sid>/load")
    def session_load(sid: str) -> Any:
        s = _require(sid)
        data = request.get_json(silent=True) or {}
        try:
            rule_name = data["rule"]
            if rule_name not in REGISTRY:
                return jsonify({"error": f"unknown rule '{rule_name}' in snapshot"}), 400

            from cellauto.engine import (
                SNAPSHOT_FORMAT_VERSION,
                _decode_rng_state,
            )

            rule_cls = REGISTRY[rule_name]
            rule_config = data.get("rule_config", {}) or {}
            rule = rule_cls(**rule_config) if rule_config else rule_cls()
            engine = Engine(
                width=data["width"],
                height=data["height"],
                rule=rule,
                seed=int(data["seed"]),
            )
            engine.step_count = int(data["step_count"])
            engine.state = rule.deserialize_state(data["state"])
            # Restore RNG state. v3 ships a JSON-native list (safe);
            # v1/v2 shipped a base64-encoded pickle, which we refuse on
            # the web path entirely — accepting it would be RCE. Old
            # snapshots still load; we reseed deterministically from the
            # stored seed instead. See docs/PUNCHLIST.md P0-1.
            version = data.get("version", 1)
            rng_state = data.get("rng_state")
            if rng_state is not None and hasattr(rule, "rng"):
                if version >= SNAPSHOT_FORMAT_VERSION and isinstance(rng_state, list):
                    rule.rng.setstate(_decode_rng_state(rng_state))
                else:
                    log.warning(
                        "session_load: legacy v%s snapshot — discarding pickled "
                        "rng_state, reseeding from seed=%s",
                        version,
                        data["seed"],
                    )
                    rule.rng.seed(int(data["seed"]))
        except (KeyError, TypeError, ValueError) as e:
            return jsonify({"error": f"bad snapshot: {e}"}), 400
        with s.lock:
            store.replace_engine(sid, engine)
        return jsonify(_state_summary(engine))

    @app.get("/api/sessions/<sid>/frame.png")
    def frame_png(sid: str) -> Any:
        s = _require(sid)
        with s.lock:
            png = _render_png(s.engine)
            filename = f"cellauto-{s.engine.rule.name}-step{s.engine.step_count}.png"
        resp = app.response_class(png, mimetype="image/png")
        if request.args.get("download"):
            resp.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        else:
            # Tell intermediaries not to cache so live frames don't get pinned.
            resp.headers["Cache-Control"] = "no-store"
        return resp

    @app.post("/api/sessions/<sid>/gif")
    def session_gif(sid: str) -> Any:
        from cellauto.export import export_gif

        s = _require(sid)
        data = request.get_json(silent=True) or {}
        try:
            steps = int(data.get("steps", 60))
            fps = int(data.get("fps", 8))
            canvas = int(data.get("canvas", 480))
        except (TypeError, ValueError):
            return jsonify({"error": "steps, fps, canvas must be integers"}), 400
        if not (1 <= steps <= MAX_GIF_STEPS):
            return jsonify({"error": f"steps must be 1..{MAX_GIF_STEPS}"}), 400
        if not (1 <= fps <= 30):
            return jsonify({"error": "fps must be 1..30"}), 400
        if not (60 <= canvas <= 1200):
            return jsonify({"error": "canvas must be 60..1200"}), 400

        # Hold the lock for the whole render: /gif and /step both mutate
        # engine.state and engine.step_count, so an interleaved /step from
        # another tab (or the play loop) would scramble the captured
        # frames. The play loop sees the request take longer, but the
        # output is consistent. The client calls stopLoop() before firing
        # /gif anyway, so this only matters for concurrent sessions.
        with s.lock:
            frames = [_capture_frame(s.engine, canvas)]
            for _ in range(steps - 1):
                s.engine.step()
                frames.append(_capture_frame(s.engine, canvas))
            filename = f"cellauto-{s.engine.rule.name}-step{s.engine.step_count}.gif"

        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        try:
            export_gif(frames, tmp_path, fps=fps)
            data_bytes = tmp_path.read_bytes()
        finally:
            tmp_path.unlink(missing_ok=True)

        resp = app.response_class(data_bytes, mimetype="image/gif")
        resp.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        return resp

    return app


def run(host: str = "127.0.0.1", port: int = 8765, debug: bool = False) -> None:
    """Start the dev server. For production, point gunicorn at ``build_app()``."""
    app = build_app()
    log.info("serving cellauto web on http://%s:%d", host, port)
    app.run(host=host, port=port, debug=debug, threaded=True)
