"""Version-consistency gate.

The v5.0 audit found a "version lie": `pyproject.toml` and
`cellauto.__version__` were still `3.6.0` while the README badge and the top
CHANGELOG heading announced `5.0.0` — so a `pip install` / About dialog
reported the wrong version and the advertised release literally could not be
built. This test makes that class of drift a hard CI failure: the package
version, the importable `__version__`, and the newest CHANGELOG heading must
all agree.
"""

from __future__ import annotations

import re
from pathlib import Path

import cellauto

_ROOT = Path(__file__).resolve().parents[1]


def _pyproject_version() -> str:
    # Regex rather than tomllib so the gate runs on Python 3.10 (the project's
    # floor; tomllib is 3.11+). The version line is unambiguous in this file.
    text = (_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"(\d+\.\d+\.\d+)"', text, re.MULTILINE)
    assert m, "no 'version = \"X.Y.Z\"' line found in pyproject.toml"
    return m.group(1)


def _latest_changelog_version() -> str:
    text = (_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    # First "## [X.Y.Z]" heading from the top is the current release.
    m = re.search(r"^##\s*\[(\d+\.\d+\.\d+)\]", text, re.MULTILINE)
    assert m, "no '## [X.Y.Z]' release heading found in CHANGELOG.md"
    return m.group(1)


def test_pyproject_and_dunder_version_agree():
    assert _pyproject_version() == cellauto.__version__, (
        f"pyproject version {_pyproject_version()!r} != cellauto.__version__ {cellauto.__version__!r}"
    )


def test_changelog_top_entry_matches_package_version():
    assert _latest_changelog_version() == cellauto.__version__, (
        f"newest CHANGELOG entry {_latest_changelog_version()!r} != "
        f"cellauto.__version__ {cellauto.__version__!r}"
    )
