"""Render a reaction network as a node-edge diagram, highlighting the RAF.

This surfaces the payoff of ``find_raf`` (Stage 2): the closed, food-generated,
reflexively-autocatalytic set of reactions. Species are nodes on a circle;
each reaction draws reactant→product edges through a midpoint; RAF reactions
are bright teal with their catalyst link drawn in magenta, non-RAF reactions
are dim. Food-set species are amber. Rendered with PIL so it's data-exact and
reusable (GUI popup + docs).
"""

from __future__ import annotations

import math

from PIL import Image, ImageDraw

from cellauto.rules.abiogenesis.science import Reaction, ReactionNetwork

# Catalytic Silence palette.
_BG = (10, 14, 22)
_BONE = (230, 224, 208)
_DIM = (90, 100, 110)
_DIM_EDGE = (48, 58, 70)
_TEAL = (57, 212, 200)
_MAGENTA = (212, 57, 164)
_AMBER = (230, 200, 60)
_NODE = (34, 44, 58)


def render_reaction_network(
    network: ReactionNetwork, raf: frozenset[Reaction], size: int = 720
) -> Image.Image:
    img = Image.new("RGB", (size, size), _BG)
    d = ImageDraw.Draw(img)
    n = max(1, network.n_species)
    cx = cy = size / 2
    radius = size * 0.36
    node_r = max(10, int(size * 0.022))

    def node_pos(i: int) -> tuple[float, float]:
        ang = 2 * math.pi * i / n - math.pi / 2
        return cx + radius * math.cos(ang), cy + radius * math.sin(ang)

    pos = [node_pos(i) for i in range(n)]
    raf_set = set(raf)

    # Draw non-RAF edges first (dim, underneath), then RAF edges (bright).
    for highlight in (False, True):
        for r in network.reactions:
            if (r in raf_set) != highlight:
                continue
            a, b = r.reactants
            c = r.product
            colour = _TEAL if highlight else _DIM_EDGE
            width = 3 if highlight else 1
            mx = (pos[a][0] + pos[b][0]) / 2
            my = (pos[a][1] + pos[b][1]) / 2
            d.line([pos[a], (mx, my)], fill=colour, width=width)
            d.line([pos[b], (mx, my)], fill=colour, width=width)
            d.line([(mx, my), pos[c]], fill=colour, width=width)
            # Arrowhead toward the product.
            _arrowhead(d, (mx, my), pos[c], colour, size)
            # Catalyst link (only for the RAF — the self-sustaining loop).
            if highlight and r.catalyst is not None:
                _dashed_line(d, pos[r.catalyst], (mx, my), _MAGENTA)

    # Nodes on top.
    for i, (x, y) in enumerate(pos):
        food = i in network.food_set
        fill = _AMBER if food else _NODE
        d.ellipse([x - node_r, y - node_r, x + node_r, y + node_r], fill=fill, outline=_BONE)
        label = str(i)
        d.text((x - 3 * len(label), y - 6), label, fill=_BG if food else _BONE)

    d.text(
        (16, size - 52),
        f"RAF: {len(raf_set)} of {len(network.reactions)} reactions  ·  {len(network.food_set)} food species",
        fill=_BONE,
    )
    d.text(
        (16, size - 32),
        "teal = RAF reaction    magenta = catalyst link    amber = food species",
        fill=_DIM,
    )
    return img


def _arrowhead(d: ImageDraw.ImageDraw, frm, to, colour, size: int) -> None:
    ang = math.atan2(to[1] - frm[1], to[0] - frm[0])
    h = max(6, int(size * 0.012))
    for off in (-0.4, 0.4):
        d.line(
            [to, (to[0] - h * math.cos(ang + off), to[1] - h * math.sin(ang + off))],
            fill=colour,
            width=2,
        )


def _dashed_line(d: ImageDraw.ImageDraw, frm, to, colour, dash: int = 6) -> None:
    dx, dy = to[0] - frm[0], to[1] - frm[1]
    dist = math.hypot(dx, dy) or 1.0
    steps = int(dist / dash)
    for s in range(0, steps, 2):
        t0, t1 = s / steps, min((s + 1) / steps, 1.0)
        d.line(
            [
                (frm[0] + dx * t0, frm[1] + dy * t0),
                (frm[0] + dx * t1, frm[1] + dy * t1),
            ],
            fill=colour,
            width=1,
        )
