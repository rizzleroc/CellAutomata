"""Compatibility stub for the v1.0 entry point.

v1.0 launched the GUI via ``python main.py``.  v2.0+ ships as a real
package; the canonical entry point is now the ``cellauto`` CLI.  This
file exists only so people pulling the new code into an old workflow get
a clear migration message instead of a confusing crash.

PHASE2_BRUTAL §7 punch list item P3-26.
"""

from __future__ import annotations

import sys


MIGRATION_NOTICE = """\
cellauto v2.0 reorganised the project as an installable package.
The ``python main.py`` entry point no longer exists; ``main.py`` is now
a deprecation stub.

  Quick start (replaces ``python main.py``):

      pip install -e .
      cellauto gui                          # GUI sandbox
      cellauto simulate --rule conway       # headless
      cellauto export --rule abiogenesis-stage1-grayscott

  Or run as a module without installing:

      python -m cellauto gui

See ``README.md`` and ``CHANGELOG.md`` for the full migration notes.
"""


def main() -> int:
    sys.stderr.write(MIGRATION_NOTICE)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
