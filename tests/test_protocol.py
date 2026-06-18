"""Phase 2 §2.3: confirm every registered rule actually satisfies the Rule protocol.

v2.0 marked the Protocol @runtime_checkable but never actually checked at runtime.
This test does, for every rule in REGISTRY.
"""

from cellauto.rules import REGISTRY, Rule


def test_every_registered_rule_satisfies_protocol():
    for name, cls in REGISTRY.items():
        rule = cls()
        assert isinstance(rule, Rule), f"{name} ({cls.__name__}) does not satisfy Rule protocol"


def test_every_rule_declares_renderer_kind():
    for name, cls in REGISTRY.items():
        rule = cls()
        assert rule.renderer_kind in ("discrete", "field"), f"{name} renderer_kind={rule.renderer_kind!r}"


def test_every_rule_has_to_config_returning_dict():
    for name, cls in REGISTRY.items():
        rule = cls()
        cfg = rule.to_config()
        assert isinstance(cfg, dict), f"{name}.to_config() returned {type(cfg)}"


def test_every_rule_can_init_state_and_step():
    """Smoke: each rule must be able to construct + step from an empty state."""
    for name, cls in REGISTRY.items():
        rule = cls()
        state = rule.init_state(8, 8)
        new_state = rule.step(state)
        assert new_state is not None, f"{name}.step() returned None"
