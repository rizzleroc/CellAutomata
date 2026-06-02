"""Deferred-parity pin for Stage XIII digital life.

The web (JS/V8) re-implementation of the virtual CPU must eventually be
verified bit-for-bit against this Python reference VM. That cross-runtime
parity check is a PRD Phase 5.3 / V8 deferred item, so this test exists only
to make the deferral *visible* in the test report (it shows up as a skip)
rather than silently missing.
"""

from __future__ import annotations

import pytest


@pytest.mark.skip(
    reason="Web/Python VM parity is PRD Phase 5.3 / V8 deferred item — see docs/PRD_LIFE_DIGITAL_ORGANISMS.md §6"
)
def test_web_python_vm_parity():
    # Placeholder: when V8 lands, drive identical genomes through both the
    # Python execute_one and the JS VM and assert identical register/energy
    # traces step-for-step.
    pass
