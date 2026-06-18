"""Run provenance — a small manifest stamped into snapshots and headless runs so
any output can be traced back to the exact code, parameters, and platform that
produced it. Best-effort and dependency-free (stdlib only); never raises.

Part of the roadmap's reproducibility track (Phase A): an instrument's outputs
must say where they came from.
"""

from __future__ import annotations

import datetime
import platform
import subprocess


def _git_sha() -> str | None:
    """Short HEAD commit hash, or None outside a git checkout / if git is absent."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        return out.stdout.strip() or None
    except Exception:
        return None


def run_manifest() -> dict:
    """Version + commit + UTC timestamp + interpreter/platform for this run."""
    from cellauto import __version__  # lazy import: avoid a cycle at module load

    return {
        "cellauto_version": __version__,
        "git_sha": _git_sha(),
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "python": platform.python_version(),
        "platform": platform.platform(),
    }
