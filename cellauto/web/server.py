"""Flask server exposing the cellauto Engine over HTTP.

API surface (all JSON unless noted):
    GET  /                     index page (the SPA)
    GET  /api/rules            list available rules + tutorial copy
    POST /api/sessions         body: {rule, grid, seed?, config?} → {session_id, ...}
    GET  /api/sessions/<sid>   current state (step_count, fps, population)
    POST /api/sessions/<sid>/step   body: {n: int} → state after stepping
    POST /api/sessions/<sid>/reset  body: {rule?, grid?, seed?, config?}
    DELETE /api/sessions/<sid>
    GET  /api/sessions/<sid>/frame.png  rendered RGB PNG

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
from cellauto.tutorial import tutorial_for

log = logging.getLogger(__name__)

# Hard caps so a bad client can't OOM the server.
MAX_GRID = 240
MAX_STEPS_PER_REQUEST = 50
MAX_SESSIONS = 64


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


def _state_summary(engine: Engine) -> dict:
    return {
        "rule": engine.rule.name,
        "grid": engine.width,
        "seed": engine.seed,
        "step_count": engine.step_count,
        "fps": round(engine.fps(), 1),
        "population": dict(engine.population()),
    }


@dataclass
class _Session:
    engine: Engine
    last_touched: float = field(default_factory=time.time)


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
        return jsonify(_state_summary(_require(sid).engine))

    @app.post("/api/sessions/<sid>/step")
    def step_session(sid: str) -> Any:
        s = _require(sid)
        data = request.get_json(silent=True) or {}
        n = int(data.get("n", 1))
        if not (1 <= n <= MAX_STEPS_PER_REQUEST):
            return jsonify({"error": f"n must be 1..{MAX_STEPS_PER_REQUEST}"}), 400
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
        store.replace_engine(sid, engine)
        return jsonify(_state_summary(engine))

    @app.delete("/api/sessions/<sid>")
    def delete_session(sid: str) -> Any:
        if not store.delete(sid):
            abort(404)
        return ("", 204)

    @app.get("/api/sessions/<sid>/frame.png")
    def frame_png(sid: str) -> Any:
        png = _render_png(_require(sid).engine)
        # Cache-bust via query string from the client; tell intermediaries
        # not to cache so live frames don't get pinned.
        resp = app.response_class(png, mimetype="image/png")
        resp.headers["Cache-Control"] = "no-store"
        return resp

    return app


def run(host: str = "127.0.0.1", port: int = 8765, debug: bool = False) -> None:
    """Start the dev server. For production, point gunicorn at ``build_app()``."""
    app = build_app()
    log.info("serving cellauto web on http://%s:%d", host, port)
    app.run(host=host, port=port, debug=debug, threaded=True)
