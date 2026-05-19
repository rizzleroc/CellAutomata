"""Engine — owns a Grid + Rule and drives steps, snapshots, and stats."""

from __future__ import annotations

import json
import logging
import random
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cellauto.grid import Grid
from cellauto.rules.base import Rule
from cellauto.rules.wolfram1d import Wolfram1DRule

log = logging.getLogger(__name__)


@dataclass
class Engine:
    width: int
    height: int
    rule: Rule
    seed: int = field(default_factory=lambda: random.randint(0, 2**31 - 1))
    step_count: int = 0
    _last_step_time: float = field(default=0.0, init=False)
    _step_durations: list[float] = field(default_factory=list, init=False)
    grid: Grid[Any] = field(init=False)

    def __post_init__(self) -> None:
        # Re-seed the rule's RNG so runs are reproducible from `seed`.
        if hasattr(self.rule, "rng"):
            self.rule.rng = random.Random(self.seed)
        self.grid = Grid.filled(self.width, self.height, self.rule.state_factory)
        # Wolfram needs a seeded initial generation.
        if isinstance(self.rule, Wolfram1DRule):
            self.rule.initial_seed(self.grid)
        log.info(
            "engine init width=%d height=%d rule=%s seed=%d",
            self.width, self.height, self.rule.name, self.seed,
        )

    def step(self) -> None:
        t0 = time.perf_counter()
        self.grid = self.rule.step(self.grid)
        self.step_count += 1
        dt = time.perf_counter() - t0
        self._step_durations.append(dt)
        if len(self._step_durations) > 60:
            self._step_durations.pop(0)
        self._last_step_time = dt

    def fps(self) -> float:
        if not self._step_durations:
            return 0.0
        avg = sum(self._step_durations) / len(self._step_durations)
        return 1.0 / avg if avg > 0 else 0.0

    def population(self) -> Mapping[str, int]:
        return self.rule.population(self.grid)

    # ---- Persistence --------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "version": 1,
            "rule": self.rule.name,
            "seed": self.seed,
            "width": self.width,
            "height": self.height,
            "step_count": self.step_count,
            "cells": [[self.rule.serialize_cell(self.grid.cells[y][x])
                       for x in range(self.width)] for y in range(self.height)],
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
        rule = rule_registry[rule_name]()
        engine = cls(
            width=data["width"],
            height=data["height"],
            rule=rule,
            seed=data["seed"],
        )
        engine.step_count = data["step_count"]
        engine.grid.cells = [[rule.deserialize_cell(data["cells"][y][x])
                              for x in range(data["width"])] for y in range(data["height"])]
        log.info("loaded snapshot from %s (rule=%s step=%d)", path, rule_name, engine.step_count)
        return engine
