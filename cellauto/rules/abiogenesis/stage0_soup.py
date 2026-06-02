"""Stage 0 — Primordial soup.

Discrete cells in random Brownian-style mixing. Same-species cells in
proximity can combine into protocells (Stage 4 / Rule 4 of the original
README). Activated intermediates carry an ``is_new`` flag for one step; only
freshly-changed cells react.

This is the original v1.0 four-rule sketch implemented honestly, including
the Rule 3 gating fix that v2.0 left as a no-op. The mechanics live in
``cellauto.rules.natural_selection``; here we wrap them with the
scientifically-honest name and a citation block.

References (full text in ``docs/science.md``):
    Oparin, A. I. (1924). The Origin of Life.
    Haldane, J. B. S. (1929). The Origin of Life. Rationalist Annual.
    Miller, S. L. (1953). A production of amino acids under possible primitive
        Earth conditions. Science, 117(3046), 528-529.
"""

from __future__ import annotations

from dataclasses import dataclass

from cellauto.rules.natural_selection import NaturalSelectionRule


@dataclass
class AbiogenesisStage0Soup(NaturalSelectionRule):
    name: str = "abiogenesis-stage0-soup"
    # SEM opt-in marker. The app routes Stage 0 through the SEM field renderer
    # only when this is truthy AND SEM mode is on; inert until app.py reads it.
    # A dataclass field (not a ClassVar) is safe here: every field on the base
    # NaturalSelectionRule has a default, so appending another defaulted field
    # keeps AbiogenesisStage0Soup() constructible with no args.
    sem_eligible: bool = True

    # Sparse caps so the micrograph reads as a granular soup with a FEW
    # distinct protocell bodies — NOT a tiled wall of balls. (In this rule
    # ``is_ameba`` is the dominant cell state, ~90% of the grid, so one sprite
    # per ameba cell floods the frame; we instead place a handful of well-
    # spread protocell bodies plus a light scatter of particulate granules.)
    _MAX_PROTOCELLS = 5
    _MAX_GRANULES = 26
    # Cap the candidate pool scanned for spatial spread so render_sprites stays
    # cheap (called per frame) on large grids; deterministic subsample.
    _SPREAD_POOL = 512

    def render_sprites(self, state) -> list[tuple[int, int, str, float]]:
        """Emit a sparse, SEM-honest sprite set from the discrete soup grid.

        Scientific mapping (see Cell semantics in natural_selection.py):
          - ``is_ameba`` cells are assembled-protocell material. Because they
            dominate the grid, we DON'T draw one per cell; instead a small,
            spatially-spread set of protocell bodies is placed so they read as
            separate compartments suspended in the soup.
          - a light scatter of granules (monomer specks) marks particulate
            matter: freshly-reacted ``is_new`` sites first, then a strided
            slice of settled cells, so the soup carries texture without
            crowding the field.

        Returns ``(sim_x, sim_y, name, scale)`` tuples. Deterministic given the
        grid (no randomness); ``[]`` for an empty/zero-size grid.
        """
        w = getattr(state, "width", 0)
        h = getattr(state, "height", 0)
        if w <= 0 or h <= 0:
            return []

        span = max(w, h)
        # Small specks; a few modest bodies. Tuned against the SEM field so the
        # sprites accent the micrograph rather than tiling over it.
        granule_scale = 3.0 * (720.0 / span) / 48.0
        protocell_scale = 0.6 * (8.0 * (720.0 / span) / 96.0)

        amebas: list[tuple[int, int]] = []
        new_cells: list[tuple[int, int]] = []
        settled_cells: list[tuple[int, int]] = []

        cells = state.cells
        for y in range(h):
            row = cells[y]
            for x in range(w):
                c = row[x]
                if c.is_ameba:
                    amebas.append((x, y))
                elif c.is_new:
                    new_cells.append((x, y))
                else:
                    settled_cells.append((x, y))

        sprites: list[tuple[int, int, str, float]] = []

        # A handful of distinct protocell bodies, spread across the field.
        for px, py in self._spatial_spread(amebas, self._MAX_PROTOCELLS, w, h):
            sprites.append((px, py, "stage0/protocell.png", protocell_scale))

        # Light particulate granule scatter: prefer freshly-reacted sites, then
        # backfill from a strided slice of settled cells. Deterministic.
        granules = self._subsample(new_cells, self._MAX_GRANULES)
        budget = self._MAX_GRANULES - len(granules)
        if budget > 0 and settled_cells:
            stride = max(1, len(settled_cells) // budget)
            granules.extend(self._subsample(settled_cells[::stride], budget))
        for gx, gy in granules:
            sprites.append((gx, gy, "stage0/granule.png", granule_scale))

        return sprites

    @staticmethod
    def _subsample(items: list[tuple[int, int]], limit: int) -> list[tuple[int, int]]:
        """Deterministically keep at most ``limit`` items, evenly strided."""
        if limit <= 0:
            return []
        if len(items) <= limit:
            return list(items)
        stride = len(items) / float(limit)
        return [items[int(i * stride)] for i in range(limit)]

    @classmethod
    def _spatial_spread(cls, items: list[tuple[int, int]], n: int, w: int, h: int) -> list[tuple[int, int]]:
        """Pick ``n`` items spread across the WxH field via a coarse lattice +
        nearest-candidate match. Deterministic; avoids the row-major clustering
        a flat stride produces when the source set covers the whole grid."""
        if not items or n <= 0:
            return []
        pool = cls._subsample(items, cls._SPREAD_POOL)
        cols = max(1, int(round((n * w / max(1, h)) ** 0.5)))
        rows = max(1, (n + cols - 1) // cols)
        chosen: list[tuple[int, int]] = []
        used: set[tuple[int, int]] = set()
        for r in range(rows):
            for c in range(cols):
                if len(chosen) >= n:
                    break
                ax = int((c + 0.5) * w / cols)
                ay = int((r + 0.5) * h / rows)
                best: tuple[int, int] | None = None
                best_d = -1
                for x, y in pool:
                    if (x, y) in used:
                        continue
                    d = (x - ax) ** 2 + (y - ay) ** 2
                    if best is None or d < best_d:
                        best_d = d
                        best = (x, y)
                if best is not None:
                    used.add(best)
                    chosen.append(best)
        return chosen
