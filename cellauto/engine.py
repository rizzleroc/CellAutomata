"""Engine — owns a Grid (or Field) + Rule and drives steps, snapshots, and stats.

v2.0.x: this rebuild closes three Phase 2 P0 bugs:
  - save/load resumes the RNG state precisely (was: re-seeded from scratch,
    so resumed runs diverged from continuous runs).
  - rule config round-trips through snapshots (was: lost on load).
  - persistent step-duration tracking is now a deque instead of pop(0) on a
    list (was: O(N) per step).
"""

from __future__ import annotations

import base64
import json
import logging
import pickle
import random
import time
from collections import deque
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cellauto.rules.base import Rule

log = logging.getLogger(__name__)


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
            self.width, self.height, self.rule.name, self.seed,
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

        rng_state is base64-encoded pickle (the only portable, lossless way to
        round-trip a Python Random state without depending on the internals).
        """
        return {
            "version": 2,
            "rule": self.rule.name,
            "rule_config": self.rule.to_config() if hasattr(self.rule, "to_config") else {},
            "seed": self.seed,
            "width": self.width,
            "height": self.height,
            "step_count": self.step_count,
            "rng_state": base64.b64encode(pickle.dumps(self.rule.rng.getstate())).decode("ascii")
                         if hasattr(self.rule, "rng") else None,
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
            width=data["width"], height=data["height"],
            rule=rule, seed=data["seed"],
        )
        engine.step_count = data["step_count"]
        engine.state = rule.deserialize_state(data["state"])
        # Restore RNG state precisely so load-then-step matches continuous runs.
        if data.get("rng_state") and hasattr(rule, "rng"):
            rng_state = pickle.loads(base64.b64decode(data["rng_state"].encode("ascii")))
            rule.rng.setstate(rng_state)
        log.info("loaded snapshot from %s (rule=%s step=%d)", path, rule_name, engine.step_count)
        return engine
