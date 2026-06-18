"""End-to-end CLI smoke tests: invoke ``python -m cellauto ...`` as a real
subprocess. Guards the argparse wiring and the ``simulate`` JSON contract that
no in-process test currently covers. Fast and deterministic; the headless
``simulate`` path needs numpy but no display, so it runs in CI and any venv.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "cellauto", *args],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_cli_help_lists_subcommands():
    proc = _run("--help")
    assert proc.returncode == 0
    for sub in ("simulate", "export", "gui"):
        assert sub in proc.stdout


def test_cli_requires_subcommand():
    # The subparser is required, so no subcommand is an argparse error (exit 2).
    proc = _run()
    assert proc.returncode == 2


def test_cli_simulate_emits_valid_population_json():
    # Tiny headless Wolfram run: deterministic, numpy-light, no display needed.
    proc = _run(
        "simulate",
        "--rule",
        "wolfram1d",
        "--grid",
        "9",
        "--steps",
        "3",
        "--seed",
        "0",
        "--rule-config",
        "rule_number=110",
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["rule"] == "wolfram1d"
    assert payload["step_count"] == 3
    assert payload["seed"] == 0
    assert "live_now" in payload["population"]
    # provenance: the headless run carries its params + a manifest (Phase A).
    assert payload["params"]["steps"] == 3
    assert payload["params"]["rule_config"] == ["rule_number=110"]
    assert payload["manifest"]["cellauto_version"]


def test_cli_unknown_rule_is_rejected():
    proc = _run("simulate", "--rule", "not-a-real-rule")
    assert proc.returncode != 0
