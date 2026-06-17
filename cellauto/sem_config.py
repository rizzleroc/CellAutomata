"""Persisted SEM / render preferences — deliberately tkinter-free.

Split out of ``cellauto.app`` so the SEM render pipeline (and its tests) can be
imported and exercised **headlessly**, without pulling in tkinter. ``cellauto.app``
re-exports these names for backward compatibility. All I/O is best-effort: it
never raises and never blocks — a fresh account simply gets the defaults.
"""

from __future__ import annotations

import json
from pathlib import Path

_CONFIG_PATH = Path.home() / ".cellauto" / "config.json"


def _load_sem_config() -> dict:
    """Load persisted preferences. Returns an empty dict if absent/unreadable —
    never raises. First launch on a fresh account just uses defaults (SEM mode
    ON, warm-sepia)."""
    try:
        return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_sem_config(cfg: dict) -> None:
    """Persist preferences. Silently swallows IO errors — never user-visible."""
    try:
        _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        _CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    except Exception:
        pass
