"""Rule catalog — the set of stages the Pro Studio can render, plus each one's
real knob set and (where it has one) its regime/preset picker.

This is the server-side source of truth for input validation and the payload
behind ``GET /api/rules``. It exposes the **field-renderer** abiogenesis stages
(those with a ``render_rgb(state)`` the SEM pipeline consumes); discrete-renderer
stages (Stage 0 soup, Conway, Wolfram, protocell-selection) and the meta
pipeline rules are intentionally excluded from the MVP (see PRD §3).

By surfacing the full ``PARAM_SPECS`` knob set per rule (not the partial set the
web clients expose) plus the Gray-Scott regime picker, this directly serves
standing requirement **#65** for the stages it covers.
"""

from __future__ import annotations

from dataclasses import dataclass

from cellauto.rules import REGISTRY
from cellauto.rules.abiogenesis.science import GRAY_SCOTT_PRESETS
from cellauto.rules.params import PARAM_SPECS, PEARSON_PRESET_RULES

# Human-facing labels for the stage picker. Falls back to a derived label.
_NAME_LABELS: dict[str, str] = {
    "abiogenesis-stage1-grayscott": "Stage I · Reaction–diffusion (Gray-Scott)",
    "abiogenesis-stage2-raf": "Stage II · Autocatalytic sets (RAF)",
    "abiogenesis-stage3-vesicles": "Stage III · Vesicles",
    "abiogenesis-hydrothermal-vent": "Stage IV · Hydrothermal vent",
    "abiogenesis-mineral-catalysis": "Stage V · Mineral catalysis",
    "abiogenesis-homochirality": "Stage VI · Homochirality",
    "abiogenesis-rna-world": "Stage VII · RNA world",
    "abiogenesis-genetic-code": "Stage VIII · Genetic code",
    "abiogenesis-coacervate": "Stage IX · Coacervates",
    "abiogenesis-luca": "Stage XI · LUCA",
}


def _derive_label(name: str) -> str:
    base = name.replace("abiogenesis-", "").replace("-", " ").strip()
    return base[:1].upper() + base[1:]


def _is_field_rule(name: str) -> bool:
    """True iff the rule renders via ``render_rgb`` (the SEM pipeline's input).

    Excludes the meta pipeline rules (their renderer depends on the active
    stage) and any rule that can't be constructed with defaults.
    """
    if name.startswith("abiogenesis-pipeline"):
        return False
    cls = REGISTRY.get(name)
    if cls is None:
        return False
    try:
        rule = cls()
    except Exception:
        return False
    return getattr(rule, "renderer_kind", "discrete") == "field" and hasattr(rule, "render_rgb")


def _presets_for(name: str) -> list[str]:
    if name in PEARSON_PRESET_RULES:
        return list(GRAY_SCOTT_PRESETS.keys())
    return []


@dataclass(frozen=True)
class RuleEntry:
    name: str
    label: str
    presets: tuple[str, ...]
    # ParamSpec objects from cellauto.rules.params (attr/label/lo/hi/step/integer).
    params: tuple

    def param_specs(self) -> dict:
        return {p.attr: p for p in self.params}


def _build() -> dict[str, RuleEntry]:
    entries: dict[str, RuleEntry] = {}
    for name in REGISTRY:
        if not _is_field_rule(name):
            continue
        entries[name] = RuleEntry(
            name=name,
            label=_NAME_LABELS.get(name, _derive_label(name)),
            presets=tuple(_presets_for(name)),
            params=tuple(PARAM_SPECS.get(name, [])),
        )
    return entries


# Built once at import.
FIELD_RULES: dict[str, RuleEntry] = _build()


def is_field_rule(name: str) -> bool:
    return name in FIELD_RULES


def rule_entry(name: str) -> RuleEntry | None:
    return FIELD_RULES.get(name)


def catalog_payload() -> list[dict]:
    """JSON-serialisable catalog for ``GET /api/rules``."""
    out: list[dict] = []
    for entry in FIELD_RULES.values():
        out.append(
            {
                "name": entry.name,
                "label": entry.label,
                "renderer": "field",
                "presets": list(entry.presets),
                "params": [
                    {
                        "attr": p.attr,
                        "label": p.label,
                        "lo": p.lo,
                        "hi": p.hi,
                        "step": p.step,
                        "integer": bool(p.integer),
                    }
                    for p in entry.params
                ],
            }
        )
    return out
