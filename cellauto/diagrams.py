"""Per-stage apparatus diagrams (v4.0.7 — E1).

Procedural PIL renderings of the experimental setup each pipeline stage is
modelling. Same Catalytic Silence aesthetic as the rest of the app:
obsidian ground, bone-cream linework, dim hairline-teal accents, single
italic-serif caption per label.

Wired into ``app.py:_show_how_it_works`` so the user sees the apparatus
sitting above the prose description, not just the rendered output of the
simulation. Closes the v4.0.6 audit gap E1 ("we're showing results without
showing the experiment that produces them").

Each ``render_*`` returns a PIL ``Image.Image``; the caller is responsible
for converting to ``ImageTk.PhotoImage`` for display. Deterministic: same
size + palette → byte-identical output, so PNG export is stable.
"""

from __future__ import annotations

import math
from typing import Any

from PIL import Image, ImageDraw

# Catalytic Silence palette (same hex values as the rest of the app).
BG = (0x0A, 0x0E, 0x16)  # obsidian
BONE = (0xE6, 0xE0, 0xD0)  # bone-cream lines + text
BONE_DIM = (0x9A, 0x96, 0x8A)  # dimmer bone for secondary labels
ACCENT = (0x39, 0xD4, 0xC8)  # teal accent for "active" or "key" elements
HAIRLINE = (0x1F, 0x4F, 0x4C)  # dim hairline for grid + frame
RED_HOT = (0xC8, 0x6B, 0x4A)  # warm orange-red for heat source / spark


def _load_font(size: int) -> Any:
    """Best-effort load of a serif italic OR mono font for diagram labels.

    Prefers the bundled IBM Plex Mono so apparatus labels match the rest of
    the app's typography. Falls back to ImageFont.load_default() on systems
    without the bundled fonts.
    """
    from pathlib import Path

    from PIL import ImageFont

    fonts_dir = Path(__file__).resolve().parent / "assets" / "fonts"
    candidates = [
        fonts_dir / "IBMPlexMono-Regular.ttf",
        fonts_dir / "IBMPlexMono-Bold.ttf",
        fonts_dir / "CrimsonPro-Italic.ttf",
    ]
    for c in candidates:
        if c.is_file():
            try:
                return ImageFont.truetype(str(c), size=size)
            except Exception:
                continue
    return ImageFont.load_default()


def _new_canvas(width: int, height: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """New diagram canvas: obsidian ground + 1-px hairline frame inset."""
    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)
    # Thin hairline frame so each diagram reads as its own "specimen plate".
    draw.rectangle((1, 1, width - 2, height - 2), outline=HAIRLINE, width=1)
    return img, draw


def _label(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: Any,
    fill: tuple[int, int, int] = BONE_DIM,
    anchor: str = "lt",
) -> None:
    """Draw a label with a tiny leader-line tick (Catalytic Silence convention)."""
    draw.text(xy, text, font=font, fill=fill, anchor=anchor)


def _leader(
    draw: ImageDraw.ImageDraw,
    src: tuple[int, int],
    dst: tuple[int, int],
    fill: tuple[int, int, int] = HAIRLINE,
) -> None:
    """Hairline leader line connecting a label to its labelled element."""
    draw.line((src[0], src[1], dst[0], dst[1]), fill=fill, width=1)


# --- Stage 0 — Miller-Urey spark-discharge apparatus -----------------------


def render_miller_urey(width: int = 640, height: int = 320) -> Image.Image:
    """The Miller-Urey 1953 spark-discharge experiment.

    Layout (left → right):
        boiling-water flask  →  rising vapour tube  →  spark-gap chamber
        (CH₄/NH₃/H₂/H₂O)  →  condenser coil  →  product trap (amino acids).
    """
    img, draw = _new_canvas(width, height)
    font = _load_font(11)
    title_font = _load_font(14)
    cap_font = _load_font(10)

    draw.text((16, 10), "MILLER–UREY · 1953", font=title_font, fill=BONE)
    draw.text(
        (16, 28),
        "Spark-discharge synthesis of amino acids from a reducing atmosphere",
        font=cap_font,
        fill=BONE_DIM,
    )

    # 1. Heat source under boiling flask (left).
    flask_cx, flask_cy = 90, 220
    flask_r = 38
    # Flame under flask — small triangle in warm red.
    flame_y = flask_cy + flask_r + 8
    for w in (12, 8, 4):
        draw.polygon(
            [
                (flask_cx - w, flame_y + 18),
                (flask_cx + w, flame_y + 18),
                (flask_cx, flame_y),
            ],
            outline=RED_HOT,
        )
    # Boiling-water flask (round body + neck).
    draw.ellipse(
        (flask_cx - flask_r, flask_cy - flask_r, flask_cx + flask_r, flask_cy + flask_r),
        outline=BONE,
        width=2,
    )
    # Water surface inside flask (teal accent for "active" boiling).
    draw.arc(
        (flask_cx - flask_r + 4, flask_cy - flask_r // 2, flask_cx + flask_r - 4, flask_cy + flask_r),
        180,
        360,
        fill=ACCENT,
        width=1,
    )
    # Neck of flask going up.
    neck_x0, neck_x1 = flask_cx - 6, flask_cx + 6
    neck_top = flask_cy - flask_r - 36
    draw.line((neck_x0, flask_cy - flask_r + 4, neck_x0, neck_top), fill=BONE, width=2)
    draw.line((neck_x1, flask_cy - flask_r + 4, neck_x1, neck_top), fill=BONE, width=2)
    _leader(draw, (40, flame_y + 9), (flask_cx - 14, flame_y + 9))
    _label(draw, (10, flame_y + 4), "heat", font, anchor="lt")
    _label(draw, (10, 196), "warm", font, anchor="lt")
    _label(draw, (10, 210), "ocean", font, anchor="lt")

    # 2. Top horizontal tube connecting flask neck → spark chamber.
    tube_y0, tube_y1 = neck_top - 12, neck_top + 12
    chamber_cx, chamber_cy = 320, 110
    chamber_w, chamber_h = 110, 90
    draw.line((neck_x0, neck_top, neck_x0, tube_y0), fill=BONE, width=2)
    draw.line((neck_x1, neck_top, neck_x1, tube_y0), fill=BONE, width=2)
    # Top tube — horizontal then bend up to chamber.
    draw.line((neck_x0, tube_y0, chamber_cx - chamber_w // 2, tube_y0), fill=BONE, width=2)
    draw.line((neck_x1, tube_y1, chamber_cx - chamber_w // 2, tube_y1), fill=BONE, width=2)
    # Small upward arrows in the tube to show vapour flow.
    for tx in (140, 200, 260):
        draw.polygon(
            [(tx, tube_y0 + 2), (tx + 6, tube_y0 + 6), (tx, tube_y0 + 10)],
            outline=BONE_DIM,
        )

    # 3. Spark-gap chamber (centre-top, large rectangle).
    cx0, cy0 = chamber_cx - chamber_w // 2, chamber_cy - chamber_h // 2
    cx1, cy1 = chamber_cx + chamber_w // 2, chamber_cy + chamber_h // 2
    draw.rectangle((cx0, cy0, cx1, cy1), outline=BONE, width=2)
    # Two electrodes hanging into the chamber.
    el_y_top = cy0
    el_y_tip = cy0 + chamber_h - 30
    el_x_l, el_x_r = chamber_cx - 18, chamber_cx + 18
    draw.line((el_x_l, el_y_top, el_x_l, el_y_tip), fill=BONE, width=2)
    draw.line((el_x_r, el_y_top, el_x_r, el_y_tip), fill=BONE, width=2)
    # Spark arc — jagged teal zigzag between electrode tips.
    arc_points = [
        (el_x_l, el_y_tip),
        (chamber_cx - 8, el_y_tip + 6),
        (chamber_cx + 4, el_y_tip - 4),
        (chamber_cx - 2, el_y_tip + 4),
        (el_x_r, el_y_tip),
    ]
    for a, b in zip(arc_points, arc_points[1:], strict=False):
        draw.line((a[0], a[1], b[0], b[1]), fill=ACCENT, width=2)
    # Gas composition labels inside chamber.
    draw.text((cx0 + 6, cy0 + 4), "CH₄ NH₃", font=cap_font, fill=BONE_DIM)
    draw.text((cx0 + 6, cy0 + 16), "H₂  H₂O", font=cap_font, fill=BONE_DIM)
    _label(draw, (chamber_cx + 48, cy0 - 6), "spark gap →", font, anchor="ls")
    _label(
        draw,
        (cx0 - 4, cy0 - 20),
        "reducing atmosphere",
        font,
        anchor="rt",
    )

    # 4. Right vertical tube → condenser coil → product trap.
    cond_x = 470
    cond_y_top, cond_y_bot = cy1, 240
    draw.line((cx1, cy0 + 18, cond_x, cy0 + 18), fill=BONE, width=2)
    draw.line((cx1, cy0 + 18 - 12, cond_x, cy0 + 18 - 12), fill=BONE, width=2)
    # Vertical descent to condenser.
    draw.line((cond_x, cy0 + 18, cond_x, cond_y_top + 30), fill=BONE, width=2)
    draw.line((cond_x + 12, cy0 + 18 - 12, cond_x + 12, cond_y_top + 30), fill=BONE, width=2)
    # Condenser coil — series of small horizontal ellipses.
    coil_top, coil_bot = cond_y_top + 30, cond_y_bot - 20
    coil_steps = 7
    coil_step_h = (coil_bot - coil_top) / coil_steps
    for i in range(coil_steps):
        y = coil_top + int(i * coil_step_h)
        draw.arc(
            (cond_x - 14, y, cond_x + 26, y + int(coil_step_h)),
            10,
            170,
            fill=BONE,
            width=2,
        )
    _label(draw, (cond_x + 44, (coil_top + coil_bot) // 2 - 6), "condenser", font, anchor="ls")
    _label(draw, (cond_x + 44, (coil_top + coil_bot) // 2 + 8), "coil", font, anchor="ls")

    # 5. Product trap (round-bottom flask at bottom).
    trap_cx, trap_cy = cond_x + 6, coil_bot + 38
    trap_r = 34
    draw.ellipse(
        (trap_cx - trap_r, trap_cy - trap_r, trap_cx + trap_r, trap_cy + trap_r),
        outline=BONE,
        width=2,
    )
    # Trapped fluid (teal accent) — amino-acid solution.
    draw.chord(
        (trap_cx - trap_r + 4, trap_cy - 8, trap_cx + trap_r - 4, trap_cy + trap_r - 4),
        20,
        160,
        fill=BG,
        outline=ACCENT,
        width=1,
    )
    # Fill the lower half of the trap with stippled teal.
    for fy in range(trap_cy + 4, trap_cy + trap_r - 6, 4):
        for fx in range(trap_cx - trap_r + 12, trap_cx + trap_r - 10, 6):
            # Draw only inside the circle.
            if (fx - trap_cx) ** 2 + (fy - trap_cy) ** 2 < (trap_r - 6) ** 2:
                draw.point((fx, fy), fill=ACCENT)
    _label(draw, (trap_cx + trap_r + 10, trap_cy - 6), "product", font, anchor="ls")
    _label(draw, (trap_cx + trap_r + 10, trap_cy + 6), "trap", font, anchor="ls")
    _label(draw, (trap_cx + trap_r + 10, trap_cy + 22), "amino", font, anchor="ls", fill=ACCENT)
    _label(draw, (trap_cx + trap_r + 10, trap_cy + 34), "acids", font, anchor="ls", fill=ACCENT)

    # 6. Bottom caption — the experiment's outcome.
    draw.text(
        (16, height - 22),
        "after 1 week → glycine, alanine, formic acid in measured yields → "
        "MILLER_UREY_SPECIES sample weight in app",
        font=cap_font,
        fill=BONE_DIM,
    )
    return img


# --- Stage 1 — Gray-Scott continuous-flow reactor --------------------------


def render_gray_scott_reactor(width: int = 640, height: int = 320) -> Image.Image:
    """Continuous-flow reactor producing Turing-pattern self-replicating spots."""
    img, draw = _new_canvas(width, height)
    font = _load_font(11)
    title_font = _load_font(14)
    cap_font = _load_font(10)

    draw.text((16, 10), "GRAY–SCOTT · continuous-flow reactor", font=title_font, fill=BONE)
    draw.text(
        (16, 28),
        "Far-from-equilibrium reaction-diffusion → self-replicating spots",
        font=cap_font,
        fill=BONE_DIM,
    )

    # Reservoirs (left): u feed (large) + waste tank (smaller).
    feed_cx, feed_cy, feed_r = 70, 130, 38
    draw.ellipse(
        (feed_cx - feed_r, feed_cy - feed_r, feed_cx + feed_r, feed_cy + feed_r),
        outline=BONE,
        width=2,
    )
    draw.text((feed_cx - 6, feed_cy - 6), "u", font=title_font, fill=ACCENT)
    _label(draw, (feed_cx - feed_r - 4, feed_cy - feed_r - 16), "feed reservoir", font, anchor="lt")
    _label(draw, (feed_cx + feed_r + 8, feed_cy - 6), "F (feed rate)", font, anchor="ls")

    # Petri-dish / gel stage in centre (the reactor).
    dish_cx, dish_cy, dish_w, dish_h = 320, 180, 220, 110
    dish_x0, dish_y0 = dish_cx - dish_w // 2, dish_cy - dish_h // 2
    dish_x1, dish_y1 = dish_cx + dish_w // 2, dish_cy + dish_h // 2
    draw.rectangle((dish_x0, dish_y0, dish_x1, dish_y1), outline=BONE, width=2)
    draw.text(
        (dish_cx - 60, dish_cy - dish_h // 2 - 18),
        "gel reactor (u + v ↔ pattern)",
        font=cap_font,
        fill=BONE_DIM,
    )
    # Self-replicating spots inside the dish — bone-cream blobs.
    for sx, sy, r in [
        (dish_x0 + 30, dish_cy - 18, 8),
        (dish_x0 + 58, dish_cy + 10, 6),
        (dish_x0 + 86, dish_cy - 12, 9),
        (dish_x0 + 120, dish_cy + 18, 7),
        (dish_x0 + 150, dish_cy - 20, 8),
        (dish_x0 + 180, dish_cy + 8, 6),
        (dish_x0 + 200, dish_cy - 6, 5),
    ]:
        draw.ellipse((sx - r, sy - r, sx + r, sy + r), outline=BONE, fill=None, width=1)
        # Tiny lit cap (top-left)
        draw.point((sx - r // 3, sy - r // 3), fill=BONE)

    # Inlet tube (left): feed → dish.
    draw.line((feed_cx + feed_r, feed_cy, dish_x0, dish_cy - 10), fill=BONE, width=2)
    # Arrow head at the inlet.
    draw.polygon(
        [(dish_x0, dish_cy - 10), (dish_x0 - 8, dish_cy - 14), (dish_x0 - 8, dish_cy - 6)],
        fill=BONE,
    )

    # Outlet tube (right): dish → waste.
    waste_cx, waste_cy, waste_r = 560, 200, 30
    draw.line((dish_x1, dish_cy + 10, waste_cx - waste_r, waste_cy), fill=BONE, width=2)
    draw.polygon(
        [
            (waste_cx - waste_r, waste_cy),
            (waste_cx - waste_r - 8, waste_cy - 4),
            (waste_cx - waste_r - 8, waste_cy + 4),
        ],
        fill=BONE,
    )
    draw.ellipse(
        (waste_cx - waste_r, waste_cy - waste_r, waste_cx + waste_r, waste_cy + waste_r),
        outline=BONE,
        width=2,
    )
    _label(draw, (waste_cx - 12, waste_cy + waste_r + 6), "waste", font, anchor="lt")
    _label(draw, (dish_x1 + 8, dish_cy + 4), "F + k", font, anchor="ls", fill=ACCENT)

    # v autocatalyst loop — return arrow from dish back into itself.
    loop_y = dish_y0 - 24
    draw.arc(
        (dish_cx - 40, loop_y - 20, dish_cx + 40, loop_y + 40),
        180,
        360,
        fill=ACCENT,
        width=2,
    )
    draw.polygon(
        [(dish_cx + 38, loop_y + 16), (dish_cx + 30, loop_y + 12), (dish_cx + 30, loop_y + 20)],
        fill=ACCENT,
    )
    _label(draw, (dish_cx + 48, loop_y - 8), "v autocatalyst loop", font, anchor="ls", fill=ACCENT)

    # Bottom caption — control variant.
    draw.text(
        (16, height - 22),
        "Control: F = 0 ⇒ v decays exponentially → no spots ever form (pinned in tests)",
        font=cap_font,
        fill=BONE_DIM,
    )
    return img


# --- Stage 2 — Kauffman RAF reactor vessel ---------------------------------


def render_raf_vessel(width: int = 640, height: int = 320) -> Image.Image:
    """Random reaction network with a highlighted reflexively-autocatalytic loop."""
    img, draw = _new_canvas(width, height)
    font = _load_font(11)
    title_font = _load_font(14)
    cap_font = _load_font(10)

    draw.text((16, 10), "KAUFFMAN RAF · catalytic-network reactor", font=title_font, fill=BONE)
    draw.text(
        (16, 28),
        "Random chemistry contains a self-sustaining loop above a connectivity threshold",
        font=cap_font,
        fill=BONE_DIM,
    )

    # Vessel — large round flask in centre.
    vx, vy, vr = 200, 180, 110
    draw.ellipse((vx - vr, vy - vr, vx + vr, vy + vr), outline=BONE, width=2)

    # Food set arrow at top of vessel.
    draw.line((vx, 60, vx, vy - vr - 8), fill=BONE_DIM, width=2)
    draw.polygon([(vx, vy - vr - 6), (vx - 5, vy - vr - 14), (vx + 5, vy - vr - 14)], fill=BONE_DIM)
    _label(draw, (vx + 10, 64), "food set f (continuously fed in)", font, anchor="ls")

    # Species nodes inside vessel (small labelled circles).
    species = [
        ("a", vx - 50, vy - 30, BONE),
        ("b", vx + 10, vy - 50, BONE),
        ("c", vx + 50, vy + 0, BONE),
        ("d", vx + 20, vy + 50, BONE),
        ("e", vx - 50, vy + 30, BONE),
        ("f", vx - 70, vy - 10, ACCENT),  # the food species, accent
    ]
    node_r = 9
    for name, sx, sy, fill in species:
        draw.ellipse((sx - node_r, sy - node_r, sx + node_r, sy + node_r), outline=fill, width=2)
        draw.text((sx - 4, sy - 6), name, font=cap_font, fill=fill)

    # RAF closure — arrows forming a cycle a → b → c → d → e → a, highlighted teal.
    cycle_indices = [0, 1, 2, 3, 4, 0]
    for i, j in zip(cycle_indices, cycle_indices[1:], strict=False):
        sx, sy = species[i][1], species[i][2]
        tx, ty = species[j][1], species[j][2]
        # Mid-point arrow.
        draw.line((sx, sy, tx, ty), fill=ACCENT, width=2)
        mx, my = (sx + tx) // 2, (sy + ty) // 2
        # Direction-perpendicular arrowhead
        dx, dy = tx - sx, ty - sy
        d = math.hypot(dx, dy) or 1
        ux, uy = dx / d, dy / d
        ah_x = mx + ux * 4
        ah_y = my + uy * 4
        draw.polygon(
            [
                (ah_x, ah_y),
                (mx - uy * 4, my + ux * 4),
                (mx + uy * 4, my - ux * 4),
            ],
            fill=ACCENT,
        )

    # Catalyst hint — small dashed arc from f to one of the cycle arrows.
    for dash_x in range(species[5][1] + 8, species[0][1] - 8, 6):
        dash_y = species[5][2] + int(
            (species[0][2] - species[5][2]) * (dash_x - species[5][1]) / max(1, species[0][1] - species[5][1])
        )
        draw.point((dash_x, dash_y), fill=BONE_DIM)
        draw.point((dash_x, dash_y + 1), fill=BONE_DIM)

    # RHS legend panel.
    leg_x = 410
    draw.text((leg_x, 80), "RAF closure", font=title_font, fill=ACCENT)
    draw.text((leg_x, 104), "(Hordijk & Steel 2004)", font=cap_font, fill=BONE_DIM)
    draw.text((leg_x, 130), "• every reaction is catalysed", font=font, fill=BONE)
    draw.text((leg_x, 148), "• catalyst itself is in the set", font=font, fill=BONE)
    draw.text((leg_x, 166), "• reactants come from the food set f", font=font, fill=BONE)
    draw.text((leg_x, 198), "Connectivity threshold:", font=font, fill=BONE_DIM)
    draw.text((leg_x, 214), "n_reactions / n_species ≳ 1.0", font=font, fill=ACCENT)

    draw.text(
        (16, height - 22),
        "Control: catalysis_level = 0 ⇒ closure returns ∅, no RAF, chemistry decays.",
        font=cap_font,
        fill=BONE_DIM,
    )
    return img


# --- Stage 3 — CMC bilayer formation ---------------------------------------


def render_cmc_bilayer(width: int = 640, height: int = 320) -> Image.Image:
    """Fatty-acid concentration vs CMC threshold → membrane self-assembly."""
    img, draw = _new_canvas(width, height)
    font = _load_font(11)
    title_font = _load_font(14)
    cap_font = _load_font(10)

    draw.text((16, 10), "CMC BILAYER · self-assembling membrane", font=title_font, fill=BONE)
    draw.text(
        (16, 28),
        "Decanoic acid (C₁₀) above its CMC (~85 mM) clusters into vesicle bilayers",
        font=cap_font,
        fill=BONE_DIM,
    )

    # Solution column (left) with y-axis concentration.
    col_x, col_y0, col_y1 = 60, 60, 290
    col_w = 90
    draw.rectangle((col_x, col_y0, col_x + col_w, col_y1), outline=BONE, width=2)
    # Concentration ramp on the right axis of the column.
    axis_x = col_x + col_w + 14
    draw.line((axis_x, col_y0, axis_x, col_y1), fill=BONE_DIM, width=1)
    for i, label in enumerate(("200 mM", "100 mM", "0 mM")):
        y = col_y0 + i * (col_y1 - col_y0) // 2
        draw.line((axis_x - 4, y, axis_x + 4, y), fill=BONE_DIM, width=1)
        draw.text((axis_x + 8, y - 6), label, font=cap_font, fill=BONE_DIM)
    # CMC threshold line (dashed teal).
    cmc_y = col_y0 + int((col_y1 - col_y0) * (1 - 85 / 200))
    for dx in range(col_x, col_x + col_w, 6):
        draw.line((dx, cmc_y, dx + 3, cmc_y), fill=ACCENT, width=1)
    draw.text((axis_x + 8, cmc_y - 6), "CMC ≈ 85 mM", font=font, fill=ACCENT)

    # Above-CMC: bilayer rings starting to nucleate.
    for vx, vy, vr in [
        (col_x + 22, col_y0 + 50, 12),
        (col_x + 60, col_y0 + 88, 14),
        (col_x + 36, col_y0 + 132, 10),
    ]:
        draw.ellipse((vx - vr, vy - vr, vx + vr, vy + vr), outline=BONE, width=2)
        draw.ellipse((vx - vr + 4, vy - vr + 4, vx + vr - 4, vy + vr - 4), outline=BONE_DIM, width=1)

    # Below-CMC: scattered free amphiphiles (small teal-tipped lines).
    for dx in range(col_x + 10, col_x + col_w - 6, 14):
        for dy in range(cmc_y + 14, col_y1 - 10, 16):
            # Head (teal dot) + tail (bone line).
            draw.line((dx, dy, dx, dy + 8), fill=BONE_DIM, width=1)
            draw.point((dx, dy), fill=ACCENT)

    # Centre: zoomed-in bilayer diagram showing the lipid double-layer.
    z_x0, z_x1 = 280, 540
    z_y_mid = 180
    draw.text((z_x0, 60), "membrane bilayer (zoom)", font=cap_font, fill=BONE_DIM)
    # Inner ring (vesicle outline).
    draw.ellipse((z_x0, z_y_mid - 60, z_x1, z_y_mid + 60), outline=BONE, width=2)
    # Outer layer of lipids — heads pointing outward.
    n_lipids = 24
    z_cx, z_cy = (z_x0 + z_x1) // 2, z_y_mid
    z_rx, z_ry = (z_x1 - z_x0) // 2 - 8, 50
    for i in range(n_lipids):
        theta = 2 * math.pi * i / n_lipids
        # Outer layer head + tail
        ox = z_cx + math.cos(theta) * z_rx
        oy = z_cy + math.sin(theta) * z_ry
        ix = z_cx + math.cos(theta) * (z_rx - 14)
        iy = z_cy + math.sin(theta) * (z_ry - 14)
        draw.line((ox, oy, ix, iy), fill=BONE, width=1)
        draw.ellipse((ox - 2, oy - 2, ox + 2, oy + 2), outline=ACCENT, fill=ACCENT)
        # Inner layer
        ix2 = z_cx + math.cos(theta) * (z_rx - 28)
        iy2 = z_cy + math.sin(theta) * (z_ry - 22)
        ix3 = z_cx + math.cos(theta) * (z_rx - 16)
        iy3 = z_cy + math.sin(theta) * (z_ry - 16)
        draw.line((ix2, iy2, ix3, iy3), fill=BONE, width=1)
        draw.ellipse((ix2 - 2, iy2 - 2, ix2 + 2, iy2 + 2), outline=ACCENT, fill=ACCENT)
    _label(draw, (z_x1 + 8, z_y_mid - 18), "hydrophilic head", font, anchor="ls", fill=ACCENT)
    _label(draw, (z_x1 + 8, z_y_mid + 0), "hydrophobic tail", font, anchor="ls", fill=BONE)

    draw.text(
        (16, height - 22),
        "Control: cmc_threshold > peak ⇒ no bilayer ever forms (vesicle_count = 0).",
        font=cap_font,
        fill=BONE_DIM,
    )
    return img


# --- Stage 4 — Protocell selection lineage ---------------------------------


def render_protocell_selection(width: int = 640, height: int = 320) -> Image.Image:
    """Population of protocells under Eigen-Schuster replicator dynamics."""
    img, draw = _new_canvas(width, height)
    font = _load_font(11)
    title_font = _load_font(14)
    cap_font = _load_font(10)

    draw.text((16, 10), "PROTOCELL SELECTION · Eigen–Schuster ODE", font=title_font, fill=BONE)
    draw.text(
        (16, 28),
        "Heritable variation + bounded chemistry ⇒ Darwinian selection",
        font=cap_font,
        fill=BONE_DIM,
    )

    # Lineage: 3 generations of protocells with genome bars + arrows.
    gen_y = (90, 180, 270)
    gen_label = ("generation N", "growth + division", "selection (N+2)")
    for i, (gy, label) in enumerate(zip(gen_y, gen_label, strict=False)):
        draw.text((16, gy - 12), label, font=cap_font, fill=BONE_DIM)
        for j in range(5):
            cx = 110 + j * 90
            # Fitness varies — lit cap brighter on the fitter ones.
            fitness = (i * 5 + j) / 14.0
            cr = 22
            draw.ellipse((cx - cr, gy - cr, cx + cr, gy + cr), outline=BONE, width=2)
            # Lit cap colour proportional to fitness.
            cap_color = ACCENT if fitness > 0.55 else BONE_DIM
            draw.ellipse(
                (cx - 6, gy - cr + 4, cx + 4, gy - cr + 14),
                outline=cap_color,
                fill=cap_color,
            )
            # Genome bar — n binary loci.
            bar_y = gy + cr + 4
            for k in range(6):
                bit = ((i * 5 + j + k * 3) % 7) > 3
                color = ACCENT if bit else BONE_DIM
                draw.rectangle(
                    (cx - 12 + k * 4, bar_y, cx - 9 + k * 4, bar_y + 5),
                    fill=color,
                )

    # Arrows down the column showing growth → division → selection.
    for j in range(5):
        cx = 110 + j * 90
        draw.line((cx, gen_y[0] + 50, cx, gen_y[1] - 30), fill=BONE_DIM, width=1)
        draw.line((cx, gen_y[1] + 50, cx, gen_y[2] - 30), fill=BONE_DIM, width=1)
        draw.polygon(
            [(cx, gen_y[1] - 28), (cx - 3, gen_y[1] - 33), (cx + 3, gen_y[1] - 33)],
            fill=BONE_DIM,
        )
        draw.polygon(
            [(cx, gen_y[2] - 28), (cx - 3, gen_y[2] - 33), (cx + 3, gen_y[2] - 33)],
            fill=BONE_DIM,
        )

    # Legend on the right showing fitness mapping.
    leg_x = 560
    draw.text((leg_x, 70), "Fitness", font=font, fill=BONE_DIM)
    draw.ellipse((leg_x, 90, leg_x + 12, 102), outline=ACCENT, fill=ACCENT)
    draw.text((leg_x + 18, 91), "high (selected)", font=cap_font, fill=ACCENT)
    draw.ellipse((leg_x, 110, leg_x + 12, 122), outline=BONE_DIM, fill=BONE_DIM)
    draw.text((leg_x + 18, 111), "low (purged)", font=cap_font, fill=BONE_DIM)

    draw.text(
        (16, height - 22),
        "Control: mutation_rate > ε_c ⇒ master sequence melts → error catastrophe.",
        font=cap_font,
        fill=BONE_DIM,
    )
    return img


# --- Stage II (extended pipeline) — alkaline hydrothermal vent -------------


def render_vent_chimney(width: int = 640, height: int = 320) -> Image.Image:
    """Lane/Martin/Russell alkaline hydrothermal vent (Lost-City type).

    Layout:
        ocean (acidic, pH ≈ 5.5)  →  porous mineral chimney wall (alkaline pH ≈ 10)
        H₂ feed rising from below  +  CO₂ feed from the surrounding ocean
        →  Wood-Ljungdahl carbon fixation at the wall interface  →  acetate.

    The proton gradient across the wall powers carbon fixation; flatten
    the gradient (vent_alkalinity = ocean_acidity) and the chemistry halts.
    """
    img, draw = _new_canvas(width, height)
    font = _load_font(11)
    title_font = _load_font(14)
    cap_font = _load_font(10)

    draw.text((16, 10), "ALKALINE HYDROTHERMAL VENT · Lost-City type", font=title_font, fill=BONE)
    draw.text(
        (16, 28),
        "pH gradient → proton-motive force → Wood-Ljungdahl carbon fixation",
        font=cap_font,
        fill=BONE_DIM,
    )

    # Ocean (light dim wash on left + right).
    ocean_y0, ocean_y1 = 60, height - 36
    for ox in (60, width - 60):
        # subtle blue-ish water hint via teal dots
        for oy in range(ocean_y0 + 10, ocean_y1 - 4, 14):
            draw.point((ox - 22, oy), fill=ACCENT)
            draw.point((ox + 22, oy + 7), fill=ACCENT)
    _label(draw, (16, ocean_y0 + 8), "ocean", font, anchor="lt")
    _label(draw, (16, ocean_y0 + 22), "pH ≈ 5.5", font, anchor="lt", fill=ACCENT)
    _label(draw, (16, ocean_y0 + 36), "acidic", font, anchor="lt")
    _label(draw, (width - 16, ocean_y0 + 8), "ocean", font, anchor="rt")
    _label(draw, (width - 16, ocean_y0 + 22), "(CO₂-rich)", font, anchor="rt", fill=ACCENT)

    # Chimney — central vertical porous column.
    ch_x0, ch_x1 = 250, 390
    ch_y0, ch_y1 = 70, height - 50
    draw.rectangle((ch_x0, ch_y0, ch_x1, ch_y1), outline=BONE, width=2)
    # Pore texture inside the chimney wall.
    for py in range(ch_y0 + 6, ch_y1 - 6, 8):
        for px in range(ch_x0 + 6, ch_x1 - 6, 12):
            jitter = ((px * 31 + py * 17) % 5) - 2
            draw.ellipse(
                (px + jitter, py, px + 4 + jitter, py + 4),
                outline=HAIRLINE,
            )
    draw.text((ch_x0 + 10, ch_y0 - 22), "chimney wall (porous)", font=cap_font, fill=BONE_DIM)
    _label(draw, ((ch_x0 + ch_x1) // 2, ch_y0 + 14), "vent interior", font, anchor="mt")
    _label(
        draw,
        ((ch_x0 + ch_x1) // 2, ch_y0 + 30),
        "pH ≈ 10",
        font,
        anchor="mt",
        fill=ACCENT,
    )
    _label(draw, ((ch_x0 + ch_x1) // 2, ch_y0 + 44), "alkaline", font, anchor="mt")

    # H₂ feed rising from below.
    draw.line(((ch_x0 + ch_x1) // 2, ch_y1, (ch_x0 + ch_x1) // 2, ch_y1 + 12), fill=BONE, width=2)
    for k in range(3):
        ay = ch_y1 + 10 - k * 8
        draw.polygon(
            [
                ((ch_x0 + ch_x1) // 2 - 6, ay + 4),
                ((ch_x0 + ch_x1) // 2 + 6, ay + 4),
                ((ch_x0 + ch_x1) // 2, ay - 4),
            ],
            outline=ACCENT,
        )
    _label(
        draw,
        ((ch_x0 + ch_x1) // 2, ch_y1 + 18),
        "H₂ from serpentinisation",
        font,
        anchor="mt",
        fill=ACCENT,
    )

    # CO₂ feed from sides (curved arrows pointing into the wall).
    for sy in (160, 220):
        # Left
        draw.line((130, sy, ch_x0 - 6, sy + 4), fill=BONE_DIM, width=1)
        draw.polygon([(ch_x0 - 6, sy + 4), (ch_x0 - 14, sy), (ch_x0 - 14, sy + 8)], fill=BONE_DIM)
        # Right
        draw.line((width - 130, sy, ch_x1 + 6, sy + 4), fill=BONE_DIM, width=1)
        draw.polygon([(ch_x1 + 6, sy + 4), (ch_x1 + 14, sy), (ch_x1 + 14, sy + 8)], fill=BONE_DIM)
    _label(draw, (90, 154), "CO₂", font, anchor="lt", fill=ACCENT)
    _label(draw, (width - 90, 154), "CO₂", font, anchor="rt", fill=ACCENT)

    # Wood-Ljungdahl reaction box at the wall interface.
    wl_x, wl_y = ch_x1 + 16, 180
    wl_w, wl_h = 130, 70
    draw.rectangle((wl_x, wl_y, wl_x + wl_w, wl_y + wl_h), outline=ACCENT, width=1)
    draw.text((wl_x + 4, wl_y + 4), "Wood-Ljungdahl", font=cap_font, fill=ACCENT)
    draw.text((wl_x + 4, wl_y + 18), "2 CO₂ + 4 H₂", font=cap_font, fill=BONE)
    draw.text((wl_x + 4, wl_y + 32), "  → CH₃COOH", font=cap_font, fill=BONE)
    draw.text((wl_x + 4, wl_y + 48), "(acetate)", font=cap_font, fill=BONE_DIM)

    # Thermodynamic readouts (top-right inset).
    th_x, th_y = ch_x1 + 16, 80
    draw.text((th_x, th_y), "PMF ≈ 266 mV", font=font, fill=ACCENT)
    draw.text((th_x, th_y + 14), "ΔG ≈ −25.7 kJ/mol", font=font, fill=ACCENT)
    draw.text((th_x, th_y + 28), "(Faraday × Nernst)", font=cap_font, fill=BONE_DIM)

    # Bottom caption — control variant.
    draw.text(
        (16, height - 22),
        "Control: pH_alkaline = pH_acidic ⇒ PMF = 0 ⇒ acetate yield collapses to zero.",
        font=cap_font,
        fill=BONE_DIM,
    )
    return img


# --- Extended pipeline — mineral-surface catalysis -------------------------

# Extra palette tones for the new diagrams (kept local; not app-wide hex).
CLAY = (0xC9, 0xA6, 0x6B)  # montmorillonite tan
MAGENTA = (0xC0, 0x5A, 0xA8)  # R-domain (homochirality)
GOLD = (0xD8, 0xB0, 0x55)  # coacervate-rich droplets


def render_mineral_clay(width: int = 640, height: int = 320) -> Image.Image:
    """Montmorillonite-clay surface catalysing condensation polymerisation.

    Free monomers diffuse in bulk water above; polymer chains accumulate ON
    the charged clay surface (teal-green) while the bulk stays monomeric
    (Ferris 1996; Cairns-Smith 1982).
    """
    img, draw = _new_canvas(width, height)
    font = _load_font(11)
    title_font = _load_font(14)
    cap_font = _load_font(10)

    draw.text((16, 10), "MINERAL CATALYSIS · montmorillonite clay", font=title_font, fill=BONE)
    draw.text(
        (16, 28),
        "Condensation polymerisation localised to the charged clay surface",
        font=cap_font,
        fill=BONE_DIM,
    )

    # Bulk water region (upper) and clay band (lower) on the grid floor.
    grid_x0, grid_x1 = 40, width - 40
    water_y0 = 60
    clay_y0, clay_y1 = 222, 264
    draw.rectangle((grid_x0, water_y0, grid_x1, clay_y1), outline=BONE, width=2)
    # Water/clay interface line.
    draw.line((grid_x0, clay_y0, grid_x1, clay_y0), fill=BONE_DIM, width=1)

    # Clay band — hatched + stippled tan to read as a charged mineral surface.
    for hx in range(grid_x0 + 4, grid_x1 - 2, 10):
        draw.line((hx, clay_y0 + 2, hx + 8, clay_y1 - 2), fill=CLAY, width=1)
    for sx in range(grid_x0 + 6, grid_x1 - 4, 8):
        for sy in range(clay_y0 + 6, clay_y1 - 4, 8):
            draw.point((sx, sy), fill=CLAY)
    # Charge ticks (− symbols) along the clay surface line.
    for cxp in range(grid_x0 + 12, grid_x1 - 8, 28):
        draw.line((cxp, clay_y0 - 4, cxp + 5, clay_y0 - 4), fill=CLAY, width=1)
    _label(draw, (grid_x0 + 6, clay_y1 + 6), "montmorillonite clay (charged surface)", font, fill=CLAY)

    # Free monomers diffusing in the bulk water — scattered bone dots.
    monomer_pts = []
    for i in range(40):
        mx = grid_x0 + 14 + ((i * 53 + 17) % (grid_x1 - grid_x0 - 28))
        my = water_y0 + 14 + ((i * 37 + 11) % (clay_y0 - water_y0 - 24))
        monomer_pts.append((mx, my))
        draw.ellipse((mx - 2, my - 2, mx + 2, my + 2), outline=BONE_DIM, fill=BONE_DIM)
    _leader(draw, (grid_x1 - 150, water_y0 + 22), (grid_x1 - 60, water_y0 + 30))
    _label(draw, (grid_x1 - 230, water_y0 + 14), "monomers (bulk water)", font, anchor="lt")

    # Polymer chains ON the clay — short teal beaded chains rooted at the surface.
    for cx in range(grid_x0 + 26, grid_x1 - 20, 56):
        py = clay_y0 - 2
        prev = (cx, py)
        for seg in range(5):
            nx = cx + ((seg * 7 + cx) % 5) - 2
            ny = py - 7 - seg * 8
            draw.line((prev[0], prev[1], nx, ny), fill=ACCENT, width=2)
            draw.ellipse((nx - 2, ny - 2, nx + 2, ny + 2), outline=ACCENT, fill=ACCENT)
            prev = (nx, ny)
    _leader(draw, (grid_x0 + 150, clay_y0 - 40), (grid_x0 + 90, clay_y0 - 24))
    _label(draw, (grid_x0 + 152, clay_y0 - 48), "polymer chains on clay", font, anchor="lt", fill=ACCENT)

    draw.text(
        (16, height - 22),
        "Control: bulk-water rate = clay rate ⇒ localisation vanishes (polymer no longer favours the clay).",
        font=cap_font,
        fill=BONE_DIM,
    )
    return img


# --- Extended pipeline — homochirality (Frank 1953) ------------------------


def render_homochirality(width: int = 640, height: int = 320) -> Image.Image:
    """Frank-1953 mirror-symmetry breaking → competing chiral domains.

    Autocatalysis + mutual antagonism makes the racemic state unstable; the
    2-D field breaks into teal L-dominant and magenta R-dominant domains
    separated by a dark racemic boundary.
    """
    img, draw = _new_canvas(width, height)
    font = _load_font(11)
    title_font = _load_font(14)
    cap_font = _load_font(10)

    draw.text((16, 10), "HOMOCHIRALITY · Frank 1953 model", font=title_font, fill=BONE)
    draw.text(
        (16, 28),
        "Asymmetric autocatalysis + antagonism ⇒ spontaneous symmetry breaking",
        font=cap_font,
        fill=BONE_DIM,
    )

    # Reaction-scheme list (left panel).
    rx = 20
    draw.text((rx, 60), "reactions", font=font, fill=BONE_DIM)
    draw.text((rx, 80), "A + L → 2L", font=font, fill=ACCENT)
    draw.text((rx, 98), "A + R → 2R", font=font, fill=MAGENTA)
    draw.text((rx, 116), "L + R → inert", font=font, fill=BONE)
    draw.text((rx, 134), "(antagonism k_x)", font=cap_font, fill=BONE_DIM)

    # 2-D field split into chiral domains (right block).
    # Scale with canvas so the block stays right of the reaction list and
    # never inverts (fx1 < fx0) at small widths.
    fx0 = int(width * 0.328)  # 210 at 640
    fy0 = int(height * 0.20)  # 64 at 320
    fx1 = max(fx0 + 1, width - 30)
    fy1 = max(fy0 + 1, height - 44)
    draw.rectangle((fx0, fy0, fx1, fy1), outline=BONE, width=2)
    cell = max(8, min(22, (fx1 - fx0) // 8))
    cols = (fx1 - fx0) // cell
    rows = (fy1 - fy0) // cell
    for r in range(rows):
        for c in range(cols):
            # Deterministic domain assignment: a couple of patches per hand,
            # with a dark racemic seam where they meet.
            v = (c * 7 + r * 11) % 5
            x0 = fx0 + c * cell + 2
            y0 = fy0 + r * cell + 2
            x1 = x0 + cell - 3
            y1 = y0 + cell - 3
            if v in (0, 1):
                draw.rectangle((x0, y0, x1, y1), fill=ACCENT)
            elif v in (3, 4):
                draw.rectangle((x0, y0, x1, y1), fill=MAGENTA)
            else:
                # Racemic boundary cell — dark with a faint hairline.
                draw.rectangle((x0, y0, x1, y1), outline=HAIRLINE, fill=BG)
    _label(draw, (fx0 + 6, fy0 + 6), "L-dominant", font, anchor="lt", fill=BG)
    _label(draw, (fx1 - 6, fy0 + 6), "R-dominant", font, anchor="rt", fill=BG)
    _label(draw, ((fx0 + fx1) // 2, fy1 - 14), "racemic boundary", font, anchor="mb", fill=BONE_DIM)

    draw.text(
        (16, height - 22),
        "Control: antagonism k_x → 0 ⇒ stable racemic state, no symmetry breaking.",
        font=cap_font,
        fill=BONE_DIM,
    )
    return img


# --- Extended pipeline — RNA world (spatial Eigen quasispecies) ------------


def render_rna_world(width: int = 640, height: int = 320) -> Image.Image:
    """Spatial Eigen quasispecies with an explicit error-threshold readout.

    Grid cells coloured by Hamming distance to a master strand (bright =
    master, dark = mutant); below ε_c the population is a quasispecies cloud,
    above it the master is lost (error catastrophe).
    """
    img, draw = _new_canvas(width, height)
    font = _load_font(11)
    title_font = _load_font(14)
    cap_font = _load_font(10)

    draw.text((16, 10), "RNA WORLD · spatial Eigen quasispecies", font=title_font, fill=BONE)
    draw.text(
        (16, 28),
        "Fitness-weighted colonisation + per-base error → quasispecies / catastrophe",
        font=cap_font,
        fill=BONE_DIM,
    )

    # Grid of cells coloured by Hamming distance to the master.
    # Scale with canvas so the grid + right-hand column survive small sizes.
    gx0 = int(width * 0.047)
    gy0 = int(height * 0.20)
    gx1 = max(gx0 + 1, int(width * 0.516))
    gy1 = max(gy0 + 1, int(height * 0.84))
    cell = max(6, int((gx1 - gx0) / 12))
    cols = max(1, (gx1 - gx0) // cell)
    rows = max(1, (gy1 - gy0) // cell)
    draw.rectangle((gx0, gy0, gx1, gy1), outline=BONE, width=1)
    for r in range(rows):
        for c in range(cols):
            # Hamming distance proxy → brightness; a few "master" cells stay bright.
            d = (c * 5 + r * 9 + (c * r) % 3) % 6
            shade = max(0, 0xE6 - d * 38)
            col = (shade, shade, max(0, shade - 0x14))
            x0 = gx0 + c * cell + 1
            y0 = gy0 + r * cell + 1
            x1 = max(x0 + 1, x0 + cell - 2)
            y1 = max(y0 + 1, y0 + cell - 2)
            draw.rectangle((x0, y0, x1, y1), fill=col)
            if d == 0:
                draw.rectangle((x0, y0, x1, y1), outline=ACCENT, width=1)
    _label(draw, (gx0, gy1 + 6), "bright = master · dark = mutant", font, anchor="lt")

    # Right-hand column anchored just past the grid's right edge.
    rx = gx1 + 6

    # Colonisation arrow into an empty cell.
    ay = int(height * 0.375)
    arrow_x1 = max(rx + 1, gx1 + 40)
    draw.line((rx, ay, arrow_x1, ay), fill=ACCENT, width=2)
    draw.polygon([(arrow_x1, ay), (arrow_x1 - 8, ay - 4), (arrow_x1 - 8, ay + 4)], fill=ACCENT)
    _label(draw, (rx, ay - 20), "fitness-weighted", font, anchor="lt", fill=ACCENT)
    _label(draw, (rx, ay + 10), "colonisation", font, anchor="lt", fill=ACCENT)

    # Error-threshold readout box — width fills to the right margin, clamped.
    bx = rx
    by = int(height * 0.475)
    bx1 = max(bx + 1, width - 24)
    bh = int(height * 0.18)
    draw.rectangle((bx, by, bx1, by + bh), outline=ACCENT, width=1)
    draw.text((bx + 6, by + 4), "error threshold", font=cap_font, fill=BONE_DIM)
    draw.text((bx + 6, by + 18), "ε_c = ln(σ)/L", font=font, fill=ACCENT)
    draw.text((bx + 6, by + 36), "≈ ln(10)/16 ≈ 0.14", font=font, fill=ACCENT)

    # Contrast: below ε_c vs above ε_c.
    draw.text((bx, int(height * 0.706)), "below ε_c: quasispecies cloud", font=cap_font, fill=ACCENT)
    draw.text((bx, int(height * 0.756)), "above ε_c: error catastrophe (melt)", font=cap_font, fill=RED_HOT)

    draw.text(
        (16, height - 22),
        "Control: per-base error ε > ε_c ⇒ master sequence lost, population melts to random.",
        font=cap_font,
        fill=BONE_DIM,
    )
    return img


# --- Extended pipeline — genetic code (Vetsigian-Woese-Goldenfeld) ---------


def render_genetic_code(width: int = 640, height: int = 320) -> Image.Image:
    """Coevolution of message and code → emergence of a universal genetic code.

    A cell carries both a codon strand and its own private codon→amino-acid
    table; decoding yields a peptide compared to a target catalyst; fitness
    selects both strand (mutation) and code (rare swaps) into neighbours.
    """
    img, draw = _new_canvas(width, height)
    title_font = _load_font(14)
    cap_font = _load_font(10)

    draw.text((16, 10), "GENETIC CODE · Vetsigian–Woese–Goldenfeld", font=title_font, fill=BONE)
    draw.text(
        (16, 28),
        "Message + code coevolve → population converges on one shared code",
        font=cap_font,
        fill=BONE_DIM,
    )

    # The cell — a rounded box carrying strand + code table.
    # Scale the box so its right edge (which anchors the whole right-hand
    # column + consensus box) tracks the canvas and never lands past the
    # right margin at small widths.
    cx0 = int(width * 0.0375)  # 24 at 640
    cy0 = int(height * 0.20)  # 64 at 320
    cx1 = max(cx0 + 1, min(int(width * 0.391), width - 90))  # 250 at 640
    cy1 = max(cy0 + 1, int(height * 0.781))  # 250 at 320
    draw.rectangle((cx0, cy0, cx1, cy1), outline=BONE, width=2)
    draw.text((cx0 + 8, cy0 + 4), "one cell", font=cap_font, fill=BONE_DIM)

    # RNA strand of codons.
    draw.text((cx0 + 8, cy0 + 22), "strand:", font=cap_font, fill=BONE_DIM)
    codons = ("AUG", "GCU", "CAA", "UUC")
    for i, cod in enumerate(codons):
        bx = cx0 + 12 + i * 50
        by = cy0 + 38
        draw.rectangle((bx, by, bx + 44, by + 16), outline=ACCENT, width=1)
        draw.text((bx + 4, by + 3), cod, font=cap_font, fill=ACCENT)

    # Private codon→amino-acid table.
    draw.text((cx0 + 8, cy0 + 64), "private code (codon→aa):", font=cap_font, fill=BONE_DIM)
    table = (("AUG", "M"), ("GCU", "A"), ("CAA", "Q"), ("UUC", "F"))
    for i, (cod, aa) in enumerate(table):
        ty = cy0 + 82 + i * 16
        draw.text((cx0 + 12, ty), f"{cod} → {aa}", font=cap_font, fill=BONE)

    # "decode" arrow → peptide.
    draw.line((cx1 + 6, 110, cx1 + 60, 110), fill=ACCENT, width=2)
    draw.polygon([(cx1 + 60, 110), (cx1 + 52, 106), (cx1 + 52, 114)], fill=ACCENT)
    draw.text((cx1 + 8, 92), "decode", font=cap_font, fill=ACCENT)
    px, py = cx1 + 72, 104
    for i, aa in enumerate("MAQF"):
        draw.ellipse((px + i * 18, py, px + i * 18 + 14, py + 14), outline=BONE, width=1)
        draw.text((px + i * 18 + 3, py + 1), aa, font=cap_font, fill=BONE)
    draw.text((cx1 + 72, py + 20), "peptide", font=cap_font, fill=BONE_DIM)

    # Compared to a target catalyst.
    draw.text((cx1 + 72, 150), "compare vs", font=cap_font, fill=BONE_DIM)
    draw.text((cx1 + 72, 164), "target catalyst", font=cap_font, fill=BONE)
    draw.line((cx1 + 90, 178, cx1 + 90, 210), fill=BONE_DIM, width=1)
    draw.polygon([(cx1 + 90, 210), (cx1 + 86, 202), (cx1 + 94, 202)], fill=BONE_DIM)
    draw.text((cx1 + 72, 212), "fitness → selection", font=cap_font, fill=BONE_DIM)
    draw.text((cx1 + 72, 226), "copy strand (mutation)", font=cap_font, fill=BONE_DIM)
    draw.text((cx1 + 72, 240), "+ code (rare swaps)", font=cap_font, fill=BONE_DIM)

    # Consensus readout box — fills to the right margin, clamped so it never
    # inverts when the cell box sits close to the right edge.
    bx, by = cx1 + 6, int(height * 0.20)
    bx1 = max(bx + 1, width - 24)
    draw.rectangle((bx, by, bx1, by + 18), outline=ACCENT, width=1)
    draw.text((bx + 4, by + 3), "code_consensus → 1.0 = universal code", font=cap_font, fill=ACCENT)

    draw.text(
        (16, height - 22),
        "Control: code_mutation = 0 ⇒ codes never converge (consensus stays near random).",
        font=cap_font,
        fill=BONE_DIM,
    )
    return img


# --- Extended pipeline — coacervates (Cahn-Hilliard LLPS) ------------------


def render_coacervate(width: int = 640, height: int = 320) -> Image.Image:
    """Cahn-Hilliard liquid-liquid phase separation → coacervate droplets.

    A near-uniform mixture separates into gold coacervate-rich droplets in a
    dark dilute phase, then coarsens (Ostwald ripening): a small droplet
    dissolves to feed a larger one. Total φ is conserved.
    """
    img, draw = _new_canvas(width, height)
    font = _load_font(11)
    title_font = _load_font(14)
    cap_font = _load_font(10)

    draw.text((16, 10), "COACERVATES · Cahn–Hilliard LLPS", font=title_font, fill=BONE)
    draw.text(
        (16, 28),
        "Conserved liquid-liquid phase separation → membraneless droplets",
        font=cap_font,
        fill=BONE_DIM,
    )

    # Phase-separation field (dark dilute phase with gold droplets).
    # Scale with the canvas so the field + the right-hand equation box both
    # fit and never invert at small widths.
    fx0 = int(width * 0.047)  # 30 at 640
    fy0 = int(height * 0.1875)  # 60 at 320
    fx1 = max(fx0 + 1, int(width * 0.625))  # 400 at 640
    fy1 = max(fy0 + 1, int(height * 0.8375))  # 268 at 320
    draw.rectangle((fx0, fy0, fx1, fy1), outline=BONE, width=2)
    draw.text((fx0 + 6, fy0 - 18 + 18), "", font=cap_font, fill=BONE_DIM)
    # Gold coacervate-rich droplets in the dark dilute phase.
    droplets = [
        (fx0 + 70, fy0 + 60, 30),
        (fx0 + 170, fy0 + 120, 42),
        (fx0 + 280, fy0 + 70, 26),
        (fx0 + 250, fy0 + 160, 18),
        (fx0 + 100, fy0 + 150, 14),
    ]
    for dx, dy, dr in droplets:
        draw.ellipse((dx - dr, dy - dr, dx + dr, dy + dr), outline=GOLD, fill=GOLD)
        # Slight darker core hint so they read as dense liquid drops.
        draw.ellipse((dx - dr + 4, dy - dr + 4, dx - dr + 10, dy - dr + 10), outline=BG)
    _label(draw, (fx0 + 6, fy1 + 6), "gold = coacervate-rich · dark = dilute phase", font, anchor="lt")

    # Coarsening arrow: small droplet (left) dissolving to feed a larger one.
    small = droplets[4]
    large = droplets[1]
    draw.line((small[0] + small[2], small[1], large[0] - large[2], large[1]), fill=ACCENT, width=2)
    draw.polygon(
        [
            (large[0] - large[2], large[1]),
            (large[0] - large[2] - 8, large[1] - 4),
            (large[0] - large[2] - 8, large[1] + 4),
        ],
        fill=ACCENT,
    )
    _label(draw, (fx0 + 60, fy0 + 184), "Ostwald ripening", font, anchor="lt", fill=ACCENT)

    # Cahn-Hilliard equation box (right) — anchored just past the field box
    # and filling to the right margin, clamped so it never inverts.
    bx, by = fx1 + 20, int(height * 0.34375)  # 420, 110 at 640x320
    bh = int(height * 0.2875)  # 92 at 320
    bx1 = max(bx + 1, width - 24)
    draw.rectangle((bx, by, bx1, by + bh), outline=ACCENT, width=1)
    draw.text((bx + 6, by + 6), "Cahn–Hilliard", font=cap_font, fill=BONE_DIM)
    draw.text((bx + 6, by + 24), "μ = φ³ − φ − κ∇²φ", font=cap_font, fill=ACCENT)
    draw.text((bx + 6, by + 44), "∂φ/∂t = M∇²μ", font=cap_font, fill=ACCENT)
    draw.text((bx + 6, by + 64), "(conserved φ)", font=cap_font, fill=BONE)

    draw.text(
        (16, height - 22),
        "Control: composition far off-critical / large κ ⇒ few-to-no droplets; total φ is conserved.",
        font=cap_font,
        fill=BONE_DIM,
    )
    return img


# --- Extended pipeline — LUCA distillation (Weiss 2016) --------------------


def render_luca(width: int = 640, height: int = 320) -> Image.Image:
    """Comparative-genomics distillation of the inferred LUCA core.

    Several surviving lineages, each a row of gene-presence bits; the shared
    core (genes present in ≥70% of lineages) is highlighted in ACCENT — the
    invariant that every lineage inherited (Weiss 2016).
    """
    img, draw = _new_canvas(width, height)
    font = _load_font(11)
    title_font = _load_font(14)
    cap_font = _load_font(10)

    draw.text((16, 10), "LUCA DISTILLATION · comparative genomics", font=title_font, fill=BONE)
    draw.text(
        (16, 28),
        "Threshold-relaxed intersection of gene families across lineages",
        font=cap_font,
        fill=BONE_DIM,
    )

    # Gene-presence matrix: rows = lineages, cols = gene families.
    n_genes = 14
    n_lineages = 6
    cell = 24
    grid_x0 = 120
    grid_y0 = 70
    box = 16
    # Deterministic presence pattern; the first 6 columns are the shared core.
    core_cols = set(range(6))

    def present(lin: int, gene: int) -> bool:
        if gene in core_cols:
            # Core gene present in ≥70% of lineages (drop in at most one).
            return not (gene == 2 and lin == 4)
        # Accessory / deleterious genes — sparse, lineage-specific.
        return ((lin * 7 + gene * 5 + (lin * gene) % 3) % 4) == 0

    # Column header tick for the core region.
    core_x1 = grid_x0 + 6 * cell - (cell - box)
    draw.rectangle((grid_x0 - 2, grid_y0 - 14, core_x1, grid_y0 - 4), outline=ACCENT, width=1)
    draw.text((grid_x0, grid_y0 - 30), "inferred LUCA core (≥70% prevalence)", font=cap_font, fill=ACCENT)

    for lin in range(n_lineages):
        ly = grid_y0 + lin * cell
        draw.text((16, ly + 2), f"lineage {lin + 1}", font=cap_font, fill=BONE_DIM)
        for gene in range(n_genes):
            gx = grid_x0 + gene * cell
            is_core = gene in core_cols
            if present(lin, gene):
                fill = ACCENT if is_core else BONE
                draw.rectangle((gx, ly, gx + box, ly + box), outline=fill, fill=fill)
            else:
                draw.rectangle((gx, ly, gx + box, ly + box), outline=HAIRLINE, fill=BG)

    _label(
        draw,
        (grid_x0, grid_y0 + n_lineages * cell + 6),
        "filled = gene present · empty = absent",
        font,
        anchor="lt",
    )

    # luca_size readout box.
    bx = grid_x0 + n_genes * cell + 16
    if bx > width - 150:
        bx = width - 170
    by = grid_y0
    draw.rectangle((bx, by, bx + 150, by + 52), outline=ACCENT, width=1)
    draw.text((bx + 6, by + 6), "luca_size →", font=cap_font, fill=BONE_DIM)
    draw.text((bx + 6, by + 22), "essential-gene", font=cap_font, fill=ACCENT)
    draw.text((bx + 6, by + 36), "count", font=cap_font, fill=ACCENT)

    draw.text(
        (16, height - 22),
        "Control: high maintenance cost / no benefit ⇒ core collapses; "
        "prevalence threshold recovers the invariant.",
        font=cap_font,
        fill=BONE_DIM,
    )
    return img


# --- Control (NULL experiment) twins ---------------------------------------
#
# E2: each stage's apparatus diagram gets a CONTROL twin — the null experiment
# with the stage's key driver disabled. The dialog shows the experiment and
# the control side by side, like a real lab figure. We avoid 12 bespoke
# renderers: one parametrised ``_control_plate`` draws the shared specimen
# frame + a struck-through "disabled driver" label + a ``kind``-dispatched
# null panel + an outcome caption; the 12 wrappers just supply the strings.
#
# Same determinism discipline as the experiment renderers: only ``math`` +
# integer-hash jitter, no ``random``/``id()``/dict-order reliance, so output
# is byte-stable for PNG export.


def _strike_label(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: Any,
    *,
    fill: tuple[int, int, int] = BONE_DIM,
) -> None:
    """Draw a label with a RED_HOT strike line through it — a disabled driver."""
    x, y = xy
    draw.text((x, y), text, font=font, fill=fill, anchor="lt")
    # Measure the text so the strike spans exactly the glyph run.
    try:
        bbox = draw.textbbox((x, y), text, font=font, anchor="lt")
        x0, _, x1, _ = bbox
        mid_y = (bbox[1] + bbox[3]) // 2
    except Exception:
        x0, x1 = x, x + max(1, len(text) * 6)
        mid_y = y + 6
    draw.line((x0 - 1, mid_y, x1 + 1, mid_y), fill=RED_HOT, width=2)


def _panel_flat_hist(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], font: Any) -> None:
    """Flat, equal-height histogram (vs a biased spike) — no biased priors."""
    x0, y0, x1, y1 = box
    base = y1 - 6
    n = 9
    bw = (x1 - x0 - 8) / n
    bar_h = (y1 - y0) // 2  # uniform, mid-height — the "flat" distribution
    for i in range(n):
        bx0 = x0 + 4 + int(i * bw)
        bx1 = x0 + 4 + int((i + 1) * bw) - 2
        draw.rectangle((bx0, base - bar_h, bx1, base), outline=BONE_DIM, fill=BG)
    draw.line((x0, base, x1, base), fill=HAIRLINE, width=1)
    draw.text((x0, y0 - 2), "flat · equal probability", font=font, fill=BONE_DIM)


def _panel_empty_field(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], font: Any) -> None:
    """Empty dish + a v-decay curve sloping to 0 — feed rate F = 0, no spots."""
    x0, y0, x1, y1 = box
    # Empty dish (rectangle), deliberately devoid of spots.
    draw.rectangle((x0, y0 + 2, x1, y1 - 18), outline=BONE_DIM, width=1)
    draw.text((x0 + 4, y0 + 4), "empty dish · no spots", font=font, fill=BONE_DIM)
    # v-decay curve sloping to 0 along the bottom strip.
    cy0, cy1 = y1 - 16, y1 - 2
    cx0, cx1 = x0 + 4, x1 - 4
    prev = None
    span = max(1, cx1 - cx0)
    for px in range(cx0, cx1 + 1, 3):
        t = (px - cx0) / span
        # exp-like decay using only math
        v = math.exp(-3.2 * t)
        py = int(cy1 - v * (cy1 - cy0))
        if prev is not None:
            draw.line((prev[0], prev[1], px, py), fill=ACCENT, width=1)
        prev = (px, py)
    draw.line((cx0, cy1, cx1, cy1), fill=HAIRLINE, width=1)


def _panel_no_cycle(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], font: Any) -> None:
    """Scattered nodes, NO closure arrows — RAF closure = ∅."""
    x0, y0, x1, y1 = box
    node_r = 6
    # Deterministic scatter of un-linked nodes.
    pts = []
    cols, rows = 4, 3
    for r in range(rows):
        for c in range(cols):
            jx = ((c * 31 + r * 17) % 7) - 3
            jy = ((c * 13 + r * 29) % 7) - 3
            nx = x0 + 18 + c * ((x1 - x0 - 28) // (cols - 1)) + jx
            ny = y0 + 16 + r * ((y1 - y0 - 34) // (rows - 1)) + jy
            pts.append((nx, ny))
    for nx, ny in pts:
        draw.ellipse(
            (nx - node_r, ny - node_r, nx + node_r, ny + node_r),
            outline=BONE_DIM,
            width=1,
        )
    # NO arrows between them — that's the whole point.
    draw.text((x0, y1 - 12), "RAF closure = ∅", font=font, fill=RED_HOT)


def _panel_no_bilayer(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], font: Any) -> None:
    """Free amphiphiles dispersed, no bilayer ring — vesicles = 0."""
    x0, y0, x1, y1 = box
    # Scattered free amphiphiles: head dot (ACCENT) + short tail (BONE_DIM).
    step_x = 22
    step_y = 18
    for ax in range(x0 + 12, x1 - 8, step_x):
        for ay in range(y0 + 14, y1 - 18, step_y):
            jx = ((ax * 7 + ay * 3) % 5) - 2
            jy = ((ax * 5 + ay * 11) % 5) - 2
            hx, hy = ax + jx, ay + jy
            draw.line((hx, hy, hx, hy + 7), fill=BONE_DIM, width=1)
            draw.point((hx, hy), fill=ACCENT)
    draw.text((x0, y1 - 12), "vesicles = 0", font=font, fill=RED_HOT)


def _panel_smear(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], font: Any) -> None:
    """Lineage rows collapsed to a uniform grey smear — error catastrophe."""
    x0, y0, x1, y1 = box
    rows = 4
    rh = (y1 - y0 - 14) // rows
    for r in range(rows):
        ry = y0 + 2 + r * rh
        # Uniform grey smear — no distinguishable loci.
        draw.rectangle((x0 + 4, ry, x1 - 4, ry + rh - 4), outline=HAIRLINE, fill=BONE_DIM)
    draw.text((x0, y1 - 12), "error catastrophe", font=font, fill=RED_HOT)


def _panel_uniform_color(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], font: Any) -> None:
    """One flat uniform colour, no proton-motive glow — PMF = 0 mV."""
    x0, y0, x1, y1 = box
    # Single flat fill, deliberately featureless (no gradient).
    draw.rectangle((x0 + 4, y0 + 2, x1 - 4, y1 - 16), outline=HAIRLINE, fill=HAIRLINE)
    draw.text((x0 + 8, y0 + 6), "no gradient", font=font, fill=BONE_DIM)
    draw.text((x0, y1 - 12), "PMF = 0 mV", font=font, fill=RED_HOT)


def _panel_everywhere(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], font: Any) -> None:
    """Two equal-height bars (on-clay ≈ bulk) — no selective concentration."""
    x0, y0, x1, y1 = box
    base = y1 - 16
    bar_h = base - y0 - 6
    bw = (x1 - x0 - 24) // 2
    # Bar 1 — on clay.
    b1x = x0 + 8
    draw.rectangle((b1x, base - bar_h, b1x + bw, base), outline=CLAY, fill=BG)
    # Bar 2 — bulk; equal height (no selective concentration).
    b2x = b1x + bw + 8
    draw.rectangle((b2x, base - bar_h, b2x + bw, base), outline=BONE_DIM, fill=BG)
    draw.line((x0, base, x1, base), fill=HAIRLINE, width=1)
    draw.text((b1x, base + 2), "on clay", font=font, fill=CLAY)
    draw.text((b2x, base + 2), "bulk", font=font, fill=BONE_DIM)


def _panel_racemic(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], font: Any) -> None:
    """Field of all-neutral cells (no chiral domains) — ee = 0.

    This is the homochirality grid with every cell taking the neutral/BG
    branch (cross-inhibition k = 0 ⇒ stable racemic state).
    """
    x0, y0, x1, y1 = box
    cell = 16
    cols = max(1, (x1 - x0 - 4) // cell)
    rows = max(1, (y1 - y0 - 16) // cell)
    for r in range(rows):
        for c in range(cols):
            cx0 = x0 + 2 + c * cell
            cy0 = y0 + 2 + r * cell
            # Every cell takes the neutral/BG branch — no teal/magenta.
            draw.rectangle((cx0, cy0, cx0 + cell - 3, cy0 + cell - 3), outline=HAIRLINE, fill=BG)
    draw.text((x0, y1 - 12), "ee = 0 · racemic", font=font, fill=RED_HOT)


def _panel_dark_noise(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], font: Any) -> None:
    """Uniform dark noise grid, master sequence lost (error rate > ε_c)."""
    x0, y0, x1, y1 = box
    cell = 16
    cols = max(1, (x1 - x0 - 4) // cell)
    rows = max(1, (y1 - y0 - 16) // cell)
    for r in range(rows):
        for c in range(cols):
            cx0 = x0 + 2 + c * cell
            cy0 = y0 + 2 + r * cell
            # Deterministic dark "noise": uniformly low shade, no bright master.
            d = (c * 5 + r * 9 + (c * r) % 3) % 4
            shade = 0x22 + d * 6  # all dark — master lost
            col = (shade, shade, max(0, shade - 4))
            draw.rectangle((cx0, cy0, cx0 + cell - 2, cy0 + cell - 2), fill=col)
    draw.text((x0, y1 - 12), "master lost", font=font, fill=RED_HOT)


def _panel_divergent(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], font: Any) -> None:
    """Several divergent private code blocks, consensus pinned low (frozen)."""
    x0, y0, x1, y1 = box
    n_blocks = 4
    bw = (x1 - x0 - 8) // n_blocks
    rows = 3
    for b in range(n_blocks):
        bx0 = x0 + 4 + b * bw
        for r in range(rows):
            ry = y0 + 4 + r * 12
            # Each block diverges: distinct deterministic fill pattern per block.
            on = ((b * 7 + r * 5) % 3) != 0
            col = ACCENT if on else HAIRLINE
            draw.rectangle((bx0, ry, bx0 + bw - 6, ry + 8), outline=col, fill=BG)
    # Consensus bar pinned low.
    cons_y = y1 - 12
    draw.line((x0 + 4, cons_y, x0 + 4 + (x1 - x0) // 6, cons_y), fill=RED_HOT, width=3)
    draw.text((x0 + (x1 - x0) // 4, cons_y - 6), "consensus low", font=font, fill=RED_HOT)


def _panel_no_droplets(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], font: Any) -> None:
    """Near-uniform field, ~0 droplets (far off-critical / large κ)."""
    x0, y0, x1, y1 = box
    # Near-uniform dark field — a faint even stipple, no gold droplets.
    draw.rectangle((x0 + 4, y0 + 2, x1 - 4, y1 - 16), outline=HAIRLINE, fill=BG)
    for sx in range(x0 + 10, x1 - 6, 12):
        for sy in range(y0 + 8, y1 - 20, 12):
            jx = (sx * 3 + sy * 7) % 3
            draw.point((sx + jx, sy), fill=HAIRLINE)
    draw.text((x0, y1 - 12), "droplets ≈ 0", font=font, fill=RED_HOT)


def _panel_inflated_core(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], font: Any) -> None:
    """Conserved core inflated to swallow accessory+deleterious genes.

    Core prevalence → 0 ⇒ the threshold no longer discriminates: everything
    reads as "core", so there is no true intersection.
    """
    x0, y0, x1, y1 = box
    n_genes = 10
    n_lin = 4
    cell_w = (x1 - x0 - 8) // n_genes
    cell_h = (y1 - y0 - 16) // n_lin
    box_w = max(3, cell_w - 3)
    box_h = max(3, cell_h - 3)
    for lin in range(n_lin):
        ly = y0 + 4 + lin * cell_h
        for gene in range(n_genes):
            gx = x0 + 4 + gene * cell_w
            # Everything inflated to "core" (ACCENT) — no discrimination left.
            draw.rectangle((gx, ly, gx + box_w, ly + box_h), outline=ACCENT, fill=ACCENT)
    draw.text((x0, y1 - 12), "no true intersection", font=font, fill=RED_HOT)


_CONTROL_PANELS = {
    "flat_hist": _panel_flat_hist,
    "empty_field": _panel_empty_field,
    "no_cycle": _panel_no_cycle,
    "no_bilayer": _panel_no_bilayer,
    "smear": _panel_smear,
    "uniform_color": _panel_uniform_color,
    "everywhere": _panel_everywhere,
    "racemic": _panel_racemic,
    "dark_noise": _panel_dark_noise,
    "divergent": _panel_divergent,
    "no_droplets": _panel_no_droplets,
    "inflated_core": _panel_inflated_core,
}


def _control_plate(
    width: int,
    height: int,
    *,
    driver: str,
    outcome: str,
    kind: str,
) -> Image.Image:
    """Render a stage's CONTROL (null-experiment) plate.

    Shared specimen-plate frame + a struck-through disabled-driver label
    (strike in RED_HOT) + a ``kind``-dispatched null panel + an outcome
    caption. Honours arbitrary ``width``/``height`` (the dialog requests
    ~336×190 but PNG export uses 640×320). Deterministic.
    """
    img, draw = _new_canvas(width, height)
    title_font = _load_font(max(9, min(14, height // 22)))
    font = _load_font(max(8, min(11, height // 28)))
    cap_font = _load_font(max(8, min(10, height // 30)))

    pad = max(6, width // 48)
    # Title — identifies this as the null experiment.
    draw.text((pad, max(4, height // 40)), "CONTROL · null experiment", font=title_font, fill=BONE_DIM)

    # Struck-through disabled-driver label.
    strike_y = max(4, height // 40) + title_font.size + 4 if hasattr(title_font, "size") else 22
    _strike_label(draw, (pad, strike_y), driver, font, fill=BONE_DIM)

    # Null panel region (the body of the plate).
    panel_top = strike_y + (font.size if hasattr(font, "size") else 12) + 8
    panel_bottom = height - (cap_font.size if hasattr(cap_font, "size") else 10) - 12
    box = (pad, panel_top, width - pad, panel_bottom)
    panel = _CONTROL_PANELS.get(kind)
    if panel is not None:
        panel(draw, box, font)

    # Outcome caption along the bottom.
    draw.text(
        (pad, height - (cap_font.size if hasattr(cap_font, "size") else 10) - 6),
        outcome,
        font=cap_font,
        fill=BONE_DIM,
    )
    return img


# Per-stage thin wrappers — supply the disabled-driver label, the null-panel
# kind, and the outcome caption. Order mirrors the apparatus renderers.


def render_control_miller_urey(width: int = 640, height: int = 320) -> Image.Image:
    return _control_plate(
        width,
        height,
        driver="Miller spark / biased priors OFF",
        outcome="flat distribution: no biased spike, all states equiprobable",
        kind="flat_hist",
    )


def render_control_gray_scott_reactor(width: int = 640, height: int = 320) -> Image.Image:
    return _control_plate(
        width,
        height,
        driver="feed rate F = 0",
        outcome="v decays to 0 → no self-replicating spots ever form",
        kind="empty_field",
    )


def render_control_raf_vessel(width: int = 640, height: int = 320) -> Image.Image:
    return _control_plate(
        width,
        height,
        driver="catalysis rate = 0",
        outcome="no reaction is catalysed → RAF closure is empty, chemistry decays",
        kind="no_cycle",
    )


def render_control_cmc_bilayer(width: int = 640, height: int = 320) -> Image.Image:
    return _control_plate(
        width,
        height,
        driver="lipid conc < CMC",
        outcome="amphiphiles stay dispersed → no bilayer, vesicle_count = 0",
        kind="no_bilayer",
    )


def render_control_protocell_selection(width: int = 640, height: int = 320) -> Image.Image:
    return _control_plate(
        width,
        height,
        driver="mutation > error threshold",
        outcome="master sequence melts → lineages collapse (error catastrophe)",
        kind="smear",
    )


def render_control_vent_chimney(width: int = 640, height: int = 320) -> Image.Image:
    return _control_plate(
        width,
        height,
        driver="vent pH = ocean pH (no gradient)",
        outcome="proton-motive force = 0 → carbon fixation halts, no acetate",
        kind="uniform_color",
    )


def render_control_mineral_clay(width: int = 640, height: int = 320) -> Image.Image:
    return _control_plate(
        width,
        height,
        driver="clay rate = bulk rate",
        outcome="no selective concentration → polymer forms everywhere equally",
        kind="everywhere",
    )


def render_control_homochirality(width: int = 640, height: int = 320) -> Image.Image:
    return _control_plate(
        width,
        height,
        driver="cross-inhibition k = 0",
        outcome="stable racemic state → no chiral domains, ee = 0",
        kind="racemic",
    )


def render_control_rna_world(width: int = 640, height: int = 320) -> Image.Image:
    return _control_plate(
        width,
        height,
        driver="error rate > error threshold",
        outcome="population melts to uniform noise → master sequence lost",
        kind="dark_noise",
    )


def render_control_genetic_code(width: int = 640, height: int = 320) -> Image.Image:
    return _control_plate(
        width,
        height,
        driver="code mutation = 0 (frozen)",
        outcome="private codes never converge → consensus pinned low",
        kind="divergent",
    )


def render_control_coacervate(width: int = 640, height: int = 320) -> Image.Image:
    return _control_plate(
        width,
        height,
        driver="far off-critical (large κ)",
        outcome="near-uniform field → essentially no droplets nucleate",
        kind="no_droplets",
    )


def render_control_luca(width: int = 640, height: int = 320) -> Image.Image:
    return _control_plate(
        width,
        height,
        driver="core prevalence → 0",
        outcome="core inflated to swallow all genes → no true intersection",
        kind="inflated_core",
    )


# --- Dispatch --------------------------------------------------------------


_RENDERERS = {
    0: render_miller_urey,
    1: render_gray_scott_reactor,
    2: render_raf_vessel,
    3: render_cmc_bilayer,
    4: render_protocell_selection,
}

# Authoritative dispatch by inner-rule name. The extended-pipeline StageInfo
# ``index`` values collide with canonical indices (a vent's index=1 would
# otherwise render the Gray-Scott reactor), so rule-name is the primary key
# and the ``_RENDERERS`` index map below is only a fallback. Every unique
# abiogenesis rule name maps to its own apparatus renderer here.
_RENDERERS_BY_RULE_NAME = {
    "abiogenesis-stage0-soup": render_miller_urey,
    "abiogenesis-stage1-grayscott": render_gray_scott_reactor,
    "abiogenesis-stage2-raf": render_raf_vessel,
    "abiogenesis-stage3-vesicles": render_cmc_bilayer,
    "abiogenesis-stage4-selection": render_protocell_selection,
    "abiogenesis-hydrothermal-vent": render_vent_chimney,
    "abiogenesis-mineral-catalysis": render_mineral_clay,
    "abiogenesis-homochirality": render_homochirality,
    "abiogenesis-rna-world": render_rna_world,
    "abiogenesis-genetic-code": render_genetic_code,
    "abiogenesis-coacervate": render_coacervate,
    "abiogenesis-luca": render_luca,
}


def render_apparatus(
    stage_index: int,
    width: int = 640,
    height: int = 320,
    *,
    rule_name: str | None = None,
) -> Image.Image | None:
    """Render the apparatus diagram for a pipeline stage, or None if not defined.

    Stage indices 0-4 correspond to the canonical pipeline (soup → reaction-
    diffusion → RAF → vesicles → selection). Stage indices outside that range
    (the v3.4 extended pipeline's 6-11) currently return None UNLESS a
    matching ``rule_name`` is passed and registered in
    ``_RENDERERS_BY_RULE_NAME`` (e.g. ``abiogenesis-hydrothermal-vent``).
    The UI quietly skips the diagram section when both lookups miss.
    """
    if rule_name is not None and rule_name in _RENDERERS_BY_RULE_NAME:
        return _RENDERERS_BY_RULE_NAME[rule_name](width, height)
    fn = _RENDERERS.get(stage_index)
    if fn is None:
        return None
    return fn(width, height)


# --- Control dispatch ------------------------------------------------------
#
# Mirrors the apparatus dispatch exactly: rule-name is the primary key (the
# extended-pipeline StageInfo indices collide with canonical 0-4), the index
# map below is the fallback for the canonical five stages.


_CONTROL_RENDERERS = {
    0: render_control_miller_urey,
    1: render_control_gray_scott_reactor,
    2: render_control_raf_vessel,
    3: render_control_cmc_bilayer,
    4: render_control_protocell_selection,
}

_CONTROL_RENDERERS_BY_RULE_NAME = {
    "abiogenesis-stage0-soup": render_control_miller_urey,
    "abiogenesis-stage1-grayscott": render_control_gray_scott_reactor,
    "abiogenesis-stage2-raf": render_control_raf_vessel,
    "abiogenesis-stage3-vesicles": render_control_cmc_bilayer,
    "abiogenesis-stage4-selection": render_control_protocell_selection,
    "abiogenesis-hydrothermal-vent": render_control_vent_chimney,
    "abiogenesis-mineral-catalysis": render_control_mineral_clay,
    "abiogenesis-homochirality": render_control_homochirality,
    "abiogenesis-rna-world": render_control_rna_world,
    "abiogenesis-genetic-code": render_control_genetic_code,
    "abiogenesis-coacervate": render_control_coacervate,
    "abiogenesis-luca": render_control_luca,
}


def render_control(
    stage_index: int,
    width: int = 640,
    height: int = 320,
    *,
    rule_name: str | None = None,
) -> Image.Image | None:
    """Render the CONTROL (null-experiment) twin of a stage's apparatus diagram.

    The null experiment is the same specimen plate with the stage's key driver
    disabled: a struck-through driver label + a schematic null panel + an
    outcome caption. Dispatch mirrors :func:`render_apparatus` — ``rule_name``
    is the primary key (extended-pipeline indices collide), ``stage_index``
    (0-4) is the fallback for the canonical pipeline. Returns ``None`` on a
    miss, like the apparatus renderer.
    """
    if rule_name is not None and rule_name in _CONTROL_RENDERERS_BY_RULE_NAME:
        return _CONTROL_RENDERERS_BY_RULE_NAME[rule_name](width, height)
    fn = _CONTROL_RENDERERS.get(stage_index)
    return fn(width, height) if fn else None
