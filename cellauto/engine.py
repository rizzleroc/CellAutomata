"""Engine — owns a Grid (or Field) + Rule and drives steps, snapshots, and stats.

v2.0.x: this rebuild closes three Phase 2 P0 bugs:
  - save/load resumes the RNG state precisely (was: re-seeded from scratch,
    so resumed runs diverged from continuous runs).
  - rule config round-trips through snapshots (was: lost on load).
  - persistent step-duration tracking is now a deque instead of pop(0) on a
    list (was: O(N) per step).

v3.5: snapshot format v3 — RNG state is round-tripped through a JSON-safe
representation of ``random.Random.getstate()`` instead of pickle bytes,
closing the arbitrary-code-execution path on the public web sandbox
(see docs/PUNCHLIST.md P0-1). v2 snapshots are still loadable but their
pickled rng_state is refused for safety; loading a v2 snapshot reseeds
the RNG from the snapshot's stored seed and step_count instead, which
preserves the rule config + state but not the exact stream position.
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

SNAPSHOT_FORMAT_VERSION = 3


def _encode_rng_state(rng: random.Random) -> list:
    """Serialize ``random.Random.getstate()`` to a JSON-safe nested list.

    ``Random.getstate()`` returns ``(version, tuple_of_625_ints, gauss_next)``
    where ``gauss_next`` is ``float | None``. All three are natively
    JSON-encodable once the inner tuple is widened to a list.
    """
    version, internal, gauss_next = rng.getstate()
    return [version, list(internal), gauss_next]


def _decode_rng_state(encoded: list) -> tuple:
    """Inverse of ``_encode_rng_state``. Validates structure to avoid
    handing arbitrary data to ``Random.setstate`` (which would
    AttributeError or ValueError, not RCE — but we may as well be loud)."""
    if not isinstance(encoded, list) or len(encoded) != 3:
        raise ValueError("rng_state must be a 3-element list [version, internal, gauss_next]")
    version, internal, gauss_next = encoded
    if not isinstance(version, int):
        raise ValueError("rng_state[0] must be int")
    if not isinstance(internal, list) or not all(isinstance(x, int) for x in internal):
        raise ValueError("rng_state[1] must be a list of ints")
    if gauss_next is not None and not isinstance(gauss_next, (int, float)):
        raise ValueError("rng_state[2] must be null or a number")
    return (version, tuple(internal), gauss_next)


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

    @property
    def active_rule(self) -> Rule:
        """Return the rule whose parameters / population / render are
        currently in effect.

        For pipeline rules this is the inner rule of the active stage
        (so parameter sliders track which stage you're looking at).
        For standalone rules it's just ``self.rule``.

        PUNCHLIST P2-1 (partial): this was hand-rolled as
        ``getattr(state, "inner_rule", None) or rule`` in 5+ places
        across ``app.py`` and ``web/server.py``. Centralising it on
        Engine eliminates that duplication.
        """
        inner = getattr(self.state, "inner_rule", None)
        return inner if inner is not None else self.rule

    @property
    def active_state(self) -> Any:
        """Companion to ``active_rule``: returns the inner state for
        pipelines, ``self.state`` otherwise. Use these together when
        calling ``rule.population(state)`` / ``rule.render_rgb(state)``
        without caring whether you've been handed a pipeline or a
        standalone rule."""
        inner = getattr(self.state, "inner_state", None)
        return inner if inner is not None else self.state

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

        Format v3: ``rng_state`` is a JSON-native nested list returned by
        ``_encode_rng_state``. v1/v2 snapshots encoded it as base64 pickle
        bytes — a deserialisation hazard we deliberately no longer emit
        and no longer trust on load. See docs/PUNCHLIST.md P0-1.
        """
        return {
            "version": SNAPSHOT_FORMAT_VERSION,
            "rule": self.rule.name,
            "rule_config": self.rule.to_config() if hasattr(self.rule, "to_config") else {},
            "seed": self.seed,
            "width": self.width,
            "height": self.height,
            "step_count": self.step_count,
            "rng_state": _encode_rng_state(self.rule.rng) if hasattr(self.rule, "rng") else None,
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
        # Build via __new__ + manual init so we skip the wasteful
        # rule.init_state in __post_init__ — Engine.load overwrites
        # engine.state immediately from the snapshot. Avoids ~5-10 ms
        # per load on an 80×80 RAF (PUNCHLIST P2-4).
        engine = cls.__new__(cls)
        engine.width = data["width"]
        engine.height = data["height"]
        engine.rule = rule
        engine.seed = data["seed"]
        engine.step_count = 0
        engine._step_durations = deque(maxlen=60)
        engine.state = None  # filled in below
        if hasattr(rule, "rng"):
            rule.rng = random.Random(data["seed"])
        engine.step_count = data["step_count"]
        engine.state = rule.deserialize_state(data["state"])
        # Restore RNG state. Format v3 ships a JSON-native list (safe);
        # v1/v2 shipped a base64-encoded pickle, which we refuse to
        # deserialise — accepting it would be an RCE on the public web
        # sandbox. Old snapshots still load; we just reseed deterministically
        # from the stored seed instead of restoring the exact stream offset.
        version = data.get("version", 1)
        rng_state = data.get("rng_state")
        if rng_state is not None and hasattr(rule, "rng"):
            if version >= 3 and isinstance(rng_state, list):
                rule.rng.setstate(_decode_rng_state(rng_state))
            else:
                log.warning(
                    "snapshot %s uses legacy v%s rng_state (pickle); "
                    "ignoring it and reseeding from seed=%s — the resumed "
                    "run will diverge from a continuous run. Re-save the "
                    "snapshot to upgrade it to v%d.",
                    path,
                    version,
                    data["seed"],
                    SNAPSHOT_FORMAT_VERSION,
                )
                rule.rng.seed(data["seed"])
        log.info("loaded snapshot from %s (rule=%s step=%d)", path, rule_name, engine.step_count)
        return engine
