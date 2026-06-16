"""Engine — owns a Grid (or Field) + Rule and drives steps, snapshots, and stats.

v2.0.x: this rebuild closes three Phase 2 P0 bugs:
  - save/load resumes the RNG state precisely (was: re-seeded from scratch,
    so resumed runs diverged from continuous runs).
  - rule config round-trips through snapshots (was: lost on load).
  - persistent step-duration tracking is now a deque instead of pop(0) on a
    list (was: O(N) per step).
"""

from __future__ import annotations

import json
import logging
import random
import time
from collections import deque
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cellauto.rules.base import Rule

log = logging.getLogger(__name__)


def _decode_rng_state(raw: Any) -> tuple:
    """Validate and rebuild a ``random.Random`` state from JSON.

    Snapshots are untrusted input (the save → share → load feature), so the RNG
    state is accepted ONLY in the plain ``random.getstate()`` shape —
    ``(int, sequence-of-ints, float | None)`` — and anything else is refused
    rather than executed. Legacy base64/pickle snapshots (a ``str``) are
    rejected outright. This is what keeps ``Engine.load`` from being an RCE sink
    (SEC-001): nothing here ever unpickles.
    """
    if isinstance(raw, str):
        raise ValueError(
            "refusing to load a legacy pickled rng_state; re-save the snapshot "
            "with this version (pickle loading was removed for security)"
        )
    if not isinstance(raw, (list, tuple)) or len(raw) != 3:
        raise ValueError("invalid rng_state in snapshot: expected a 3-element sequence")
    version, internal, gauss_next = raw
    if not isinstance(version, int) or isinstance(version, bool):
        raise ValueError("invalid rng_state in snapshot: version must be an int")
    if not isinstance(internal, (list, tuple)) or not all(
        isinstance(x, int) and not isinstance(x, bool) for x in internal
    ):
        raise ValueError("invalid rng_state in snapshot: internal state must be ints")
    if gauss_next is not None and not isinstance(gauss_next, (int, float)):
        raise ValueError("invalid rng_state in snapshot: gauss_next must be a number or null")
    state = (version, tuple(internal), None if gauss_next is None else float(gauss_next))
    try:
        # Validate against the real RNG without disturbing any live instance.
        random.Random().setstate(state)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError(f"invalid rng_state in snapshot: {exc}") from exc
    return state


@dataclass
class Engine:
    width: int
    height: int
    rule: Rule
    seed: int = field(default_factory=lambda: random.randint(0, 2**31 - 1))
    step_count: int = 0
    _step_durations: deque = field(default_factory=lambda: deque(maxlen=60), init=False)
    state: Any = field(init=False)  # Grid OR Field, depending on rule

    def __post_init__(self) -> None:
        if hasattr(self.rule, "rng"):
            self.rule.rng = random.Random(self.seed)
        self.state = self.rule.init_state(self.width, self.height)
        log.info(
            "engine init width=%d height=%d rule=%s seed=%d",
            self.width,
            self.height,
            self.rule.name,
            self.seed,
        )

    # Backward compat: existing tests reference engine.grid.
    @property
    def grid(self) -> Any:
        return self.state

    def step(self) -> None:
        t0 = time.perf_counter()
        new_state = self.rule.step(self.state)
        if new_state is not None:
            self.state = new_state
        self.step_count += 1
        self._step_durations.append(time.perf_counter() - t0)

    def fps(self) -> float:
        if not self._step_durations:
            return 0.0
        avg = sum(self._step_durations) / len(self._step_durations)
        return 1.0 / avg if avg > 0 else 0.0

    def population(self) -> Mapping[str, int]:
        return self.rule.population(self.state)

    # ---- Persistence --------------------------------------------------------

    def to_dict(self) -> dict:
        """JSON-safe snapshot including RNG state and rule config.

        rng_state is the plain ``random.Random.getstate()`` tuple — (version,
        internal-state ints, gauss_next) — serialised directly as JSON. No
        pickle, so loading a snapshot can never execute code (see
        ``_decode_rng_state``).
        """
        return {
            "version": 2,
            "rule": self.rule.name,
            "rule_config": self.rule.to_config() if hasattr(self.rule, "to_config") else {},
            "seed": self.seed,
            "width": self.width,
            "height": self.height,
            "step_count": self.step_count,
            "rng_state": list(self.rule.rng.getstate())
            if hasattr(self.rule, "rng")
            else None,
            "state": self.rule.serialize_state(self.state),
        }

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2))
        log.info("saved snapshot to %s (step=%d)", path, self.step_count)

    @classmethod
    def load(cls, path: str | Path, rule_registry: dict[str, type]) -> Engine:
        data = json.loads(Path(path).read_text())
        rule_name = data["rule"]
        if rule_name not in rule_registry:
            raise ValueError(f"unknown rule '{rule_name}' in snapshot")
        rule_cls = rule_registry[rule_name]
        rule_config = data.get("rule_config", {})
        rule = rule_cls(**rule_config) if rule_config else rule_cls()
        engine = cls(
            width=data["width"],
            height=data["height"],
            rule=rule,
            seed=data["seed"],
        )
        engine.step_count = data["step_count"]
        engine.state = rule.deserialize_state(data["state"])
        # Restore the RNG precisely so load-then-step matches a continuous run.
        # SECURITY (SEC-001): rng_state is validated JSON, never unpickled, so a
        # crafted snapshot cannot execute code on load.
        if data.get("rng_state") is not None and hasattr(rule, "rng"):
            rule.rng.setstate(_decode_rng_state(data["rng_state"]))
        log.info("loaded snapshot from %s (rule=%s step=%d)", path, rule_name, engine.step_count)
        return engine
