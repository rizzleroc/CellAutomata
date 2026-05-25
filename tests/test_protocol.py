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
    """Each rule must initialise, step without raising, and produce a
    state with the right shape + at least one population statistic.

    Pre-v3.5 this test asserted ``new_state is not None or state is not
    None`` — a tautology (always True after init_state runs). PUNCHLIST
    P2-6 swapped that for the per-rule invariants below.
    """
    from collections.abc import Mapping

    import numpy as np

    from cellauto.engine import Engine

    for name, cls in REGISTRY.items():
        # Construct via Engine so RNG seeding goes through the documented
        # path (rules expect `engine.seed` → `rule.rng`).
        engine = Engine(width=16, height=16, rule=cls(), seed=1)

        # init_state must produce a non-None state.
        assert engine.state is not None, f"{name}.init_state returned None"

        # population() must return a non-empty Mapping[str, int|float]
        # with at least one stat.
        pop = engine.rule.population(engine.state)
        assert isinstance(pop, Mapping), f"{name}.population() returned {type(pop)}"
        assert len(pop) > 0, f"{name}.population() is empty"
        for k, v in pop.items():
            assert isinstance(k, str), f"{name}.population key {k!r} not str"
            assert isinstance(v, (int, float, np.integer, np.floating)), (
                f"{name}.population[{k!r}] = {v!r} ({type(v)})"
            )

        # step() must not raise on a fresh state.
        engine.step()
        assert engine.step_count == 1, f"{name}: step_count didn't advance"

        # The state shape after step must still be coherent — i.e. the
        # rule's render_rgb must produce an (H, W, 3) uint8 array
        # (every rule in REGISTRY implements render_rgb per the Rule
        # protocol).
        rgb = engine.rule.render_rgb(engine.state)
        rgb = np.asarray(rgb)
        assert rgb.ndim == 3 and rgb.shape[2] == 3, (
            f"{name}.render_rgb returned shape {rgb.shape}, expected (H, W, 3)"
        )
        assert rgb.dtype == np.uint8, f"{name}.render_rgb returned dtype {rgb.dtype}, expected uint8"
