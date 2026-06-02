"""Narrative animation channel (v4.1) — the separate "Day in the Life" layer.

cellauto has two visual channels now:

  Channel A — the GROUNDED SEM micrograph (``cellauto.renderer_sem``). Every
              pixel traces to a real ``render_rgb(state)`` value. Unchanged.
  Channel B — THIS: the anthropomorphized "day in the life of the cell" story
              layer. It composites, on top of a finished SEM frame:
                * the protagonist character (``cellauto.character``),
                * a typeset narration ribbon + day-clock (``cellauto.narrative``),
                * a gentle time-of-day light grade,
                * a lower-third "DAY IN THE LIFE" kicker so it never masquerades
                  as instrument truth.

Channel B has its **own animation clock**, independent of the simulation step
loop AND of the SEM badge pulse: the character breathes/blinks and the ribbon
can ken-burns/typewriter on its own cadence even while the sim is paused.

It plugs into the render path as a *post-compositor*: ``SemRenderer`` calls
``compose(frame)`` after its own chrome overlay when a channel is installed
(``SemRenderer.post_compositor``). When the channel is disabled the SEM frame
is returned untouched, so Channel A is never altered — Channel B is purely
additive and toggleable.

Interface contract (locked):

    NarrativeChannel(size, palette=..., enabled=False)
      .enabled                         bool — when False, compose() is identity
      .tick(dt=0.05) -> None           advance the channel's own clock
      .set_stage(stage, pipeline_len)  point the narration at a pipeline stage
      .set_palette(name)               warm-sepia | cool-mono
      .set_sprite_provider(fn)         fn(stage)->PIL RGBA|None for the body art
      .set_reduced_motion(bool)        freeze the clock-driven motion
      .compose(base_rgb) -> np.ndarray (H,W,3) uint8  — additive overlay
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from cellauto.narrative import NarrativeScript

# Per-beat staging table: mood -> (scale_h, anchor_fx, baseline_fy).
#   scale_h     sprite edge as a fraction of frame HEIGHT
#   anchor_fx   horizontal anchor (rule-of-thirds, off the hard corner)
#   baseline_fy vertical contact line as a fraction of frame HEIGHT
_STAGE_PLAN: dict[str, tuple[float, float, float]] = {
    "curious": (0.40, 0.30, 0.70),
    "calm": (0.36, 0.30, 0.68),
    "excited": (0.46, 0.33, 0.72),
    "struggling": (0.42, 0.28, 0.74),
    "triumphant": (0.46, 0.34, 0.66),
    "weary": (0.34, 0.27, 0.74),
    "reborn": (0.32, 0.31, 0.69),
}
_DEFAULT_PLAN: tuple[float, float, float] = (0.36, 0.30, 0.69)

# Per-time-of-day grade script: time_of_day -> (wash, d_value, d_sat).
#   wash     extra blend weight toward beat.sky (added on top of the vignette
#            base, so corners still read stronger than the centre).
#   d_value  multiplicative exposure nudge (noon high-key, night darker).
#   d_sat    saturation gain so dawn/dusk read tinted, noon stays clean-bright.
# Strengthened over the old flat 0.10→0.30 wash so the dawn-pink / noon-bright /
# dusk-coral / night-indigo progression actually reads, while staying tasteful
# (values stay clear of blown highlights; saturation moves are gentle).
_DAY_GRADE: dict[str, tuple[float, float, float]] = {
    "dawn": (0.22, 0.99, 1.12),
    "morning": (0.16, 1.04, 1.05),
    "noon": (0.20, 1.09, 0.96),
    "afternoon": (0.20, 1.01, 1.12),
    "dusk": (0.26, 0.95, 1.20),
    "night": (0.30, 0.80, 1.06),
}
_DEFAULT_GRADE: tuple[float, float, float] = (0.18, 1.0, 1.0)


def _plan_for(beat: Any) -> tuple[float, float, float]:
    """Resolve the staging plan for a beat's mood, defaulting when unknown."""
    return _STAGE_PLAN.get(str(getattr(beat, "mood", "")), _DEFAULT_PLAN)


def _grade_for(time_of_day: Any) -> tuple[float, float, float]:
    """Resolve the (wash, d_value, d_sat) grade script for a time-of-day key."""
    return _DAY_GRADE.get(str(time_of_day), _DEFAULT_GRADE)


# Per-time-of-day contact-shadow script: time_of_day ->
#   (dx_frac, length, softness, opacity, coolness).
#     dx_frac   lateral offset of the cast core, as a fraction of foot width
#               (signed: + casts to the right; magnitude grows toward a low sun).
#     length    multiplier on the wide cast ellipse width (1.0 = directly beneath).
#     softness  multiplier on the blur radius (sharp at noon, soft at dawn/night).
#     opacity   multiplier on the darkening strength (dark noon, faint night).
#     coolness  -1..+1 shadow tint bias: + cools toward indigo, - warms to coral.
_DAY_SHADOW: dict[str, tuple[float, float, float, float, float]] = {
    "dawn": (0.18, 1.20, 1.35, 0.78, 0.10),
    "morning": (0.30, 1.45, 1.05, 0.92, -0.10),
    "noon": (0.04, 1.00, 0.80, 1.05, 0.00),
    "afternoon": (-0.42, 1.95, 1.20, 0.90, -0.30),
    "dusk": (-0.55, 2.20, 1.40, 0.80, -0.45),
    "night": (0.10, 1.15, 1.55, 0.50, 0.55),
}
_DEFAULT_SHADOW: tuple[float, float, float, float, float] = (0.0, 1.0, 1.0, 1.0, 0.0)


def _shadow_for(time_of_day: Any) -> tuple[float, float, float, float, float]:
    """Resolve the (dx, length, softness, opacity, coolness) shadow script."""
    return _DAY_SHADOW.get(str(time_of_day), _DEFAULT_SHADOW)


def _scrim_h_for(height: int) -> int:
    """Shared narration-scrim height (pixels). Single source of truth so the
    ribbon scrim and the character keep-out ledge can never drift apart."""
    return int(height * 0.34)


@dataclass
class NarrativeChannel:
    """Stateful compositor + clock for the Day-in-the-Life story channel."""

    size: int
    palette: str = "warm-sepia"
    enabled: bool = False
    reduced_motion: bool = False

    # Live narration target.
    stage: int = 0
    pipeline_len: int = 12

    # Internal animation clock — advanced ONLY by tick(), never by the sim.
    _phase: float = 0.0
    _script: NarrativeScript = field(default_factory=NarrativeScript)
    _sprite_provider: Callable[[int], Any] | None = None

    # Per-instance memo for the gradient scrim, keyed (width, scrim_h), so the
    # ~20 Hz hot path allocates the ramp once per resolution.
    _scrim_cache: dict[tuple[int, int], Any] = field(default_factory=dict)

    # ── App-facing setters ───────────────────────────────────────────────────

    def set_stage(self, stage: int, pipeline_len: int) -> None:
        self.stage = int(stage)
        self.pipeline_len = max(1, int(pipeline_len))

    def set_palette(self, name: str) -> None:
        self.palette = name

    def set_enabled(self, on: bool) -> None:
        self.enabled = bool(on)

    def set_reduced_motion(self, on: bool) -> None:
        self.reduced_motion = bool(on)

    def set_sprite_provider(self, fn: Callable[[int], Any] | None) -> None:
        """Install a callback mapping a stage index to a PIL RGBA body sprite
        (or None for fully-procedural). The channel calls it lazily and is
        expected to cache; the provider itself should be cheap/cached."""
        self._sprite_provider = fn

    # ── Clock ────────────────────────────────────────────────────────────────

    def tick(self, dt: float = 0.05) -> None:
        """Advance the channel's own animation phase. Called from app._animate
        at ~20 Hz, independent of play/pause. Reduced motion freezes it.

        Advances ``self._phase`` modulo 1.0 over a ~4 s cycle so a full
        breathe/blink cycle takes ~4 s at the ~20 Hz call rate. No-op (freezes
        the phase) when ``reduced_motion`` is set. Never raises.
        """
        if self.reduced_motion:
            return
        try:
            self._phase = (self._phase + float(dt) / 4.0) % 1.0
        except (TypeError, ValueError):
            # Defensive: a bad dt must never break the animation loop.
            return

    # ── Composition ──────────────────────────────────────────────────────────

    def compose(self, base_rgb: np.ndarray) -> np.ndarray:
        """Composite Channel B over a finished SEM frame.

        ``base_rgb`` is an (H, W, 3) uint8 array (the chrome'd SEM micrograph,
        already at whatever resolution the renderer produced). Returns a new
        (H, W, 3) uint8 array. When ``enabled`` is False this is the identity
        (returns base_rgb unchanged) so Channel A is never disturbed.

        Builds, at base_rgb's resolution (so it works at hi-res too):
          1. resolve beat = self._script.beat_for(self.stage, pipeline_len=...).
          2. a subtle vignette-weighted time-of-day wash toward beat.sky
             (gentle in the centre, stronger in the corners — a "moment in a
             day" tint, not a flat colour cast).
          3. the protagonist character (cellauto.character.render_character),
             alpha-composited lower-left over a soft elliptical contact shadow.
          4. a cinematic lower-third carrying a tracked "DAY IN THE LIFE"
             kicker + demoted day-clock, a serif hero title and an italic
             width-wrapped narration line over a gradient scrim, with a gentle
             typewriter reveal driven by self._phase. The kicker doubles as the
             provenance mark so the layer is unmistakably narration, not the
             instrument feed.
        numpy+PIL only; never mutates base_rgb; never raises in the hot path.
        """
        if not self.enabled:
            return base_rgb

        try:
            from PIL import Image
        except Exception:
            # No PIL → cannot composite; hand back an untouched copy so the
            # output is still a fresh (H, W, 3) uint8 array (never the input).
            return np.array(base_rgb, dtype=np.uint8, copy=True)

        base = np.asarray(base_rgb, dtype=np.uint8)
        if base.ndim != 3 or base.shape[2] != 3:
            # Malformed input — return a copy untouched rather than raise.
            return np.array(base_rgb, dtype=np.uint8, copy=True)
        height, width = int(base.shape[0]), int(base.shape[1])

        beat = self._script.beat_for(self.stage, pipeline_len=self.pipeline_len)

        # 1. Time-of-day grade (numpy, vignette-weighted).
        out = self._apply_day_grade(base, beat.sky, getattr(beat, "time_of_day", None))

        # Everything past here is best-effort PIL compositing; any failure
        # falls back to the already-graded frame.
        try:
            canvas = Image.fromarray(out, "RGB").convert("RGBA")
            self._composite_character(canvas, beat, height, width)
            self._draw_ribbon(canvas, beat, height, width)
            out = np.asarray(canvas.convert("RGB"), dtype=np.uint8)
        except Exception:
            out = np.ascontiguousarray(out, dtype=np.uint8)

        return out

    # ── Composition helpers (numpy + PIL, all lazy-imported) ─────────────────

    def _apply_day_grade(
        self,
        base: np.ndarray,
        sky: tuple[int, int, int],
        time_of_day: Any = None,
    ) -> np.ndarray:
        """Blend ``base`` toward ``sky`` with a vignette weight (gentle centre,
        stronger corners), then apply a per-time-of-day value+saturation shift so
        the dawn-pink / noon-bright / dusk-coral / night-indigo arc actually reads
        instead of being swallowed by the sepia. Stays vignette-weighted (never a
        flat cast) and tasteful (clamped, no posterization). Returns a NEW
        (H, W, 3) uint8 array; any failure degrades to the legacy gentle grade."""
        try:
            return self._graded_strong(base, sky, time_of_day)
        except Exception:
            # Fallback: legacy gentle vignette wash (kept verbatim).
            h, w = base.shape[0], base.shape[1]
            ys = np.linspace(-1.0, 1.0, h, dtype=np.float32).reshape(h, 1)
            xs = np.linspace(-1.0, 1.0, w, dtype=np.float32).reshape(1, w)
            radius = np.sqrt(xs * xs + ys * ys) / np.float32(np.sqrt(2.0))
            strength = (0.10 + 0.20 * (radius**2)).astype(np.float32)[..., None]
            sky_arr = np.array(sky, dtype=np.float32).reshape(1, 1, 3)
            graded = base.astype(np.float32) * (1.0 - strength) + sky_arr * strength
            return np.clip(graded, 0, 255).astype(np.uint8)

    def _graded_strong(
        self,
        base: np.ndarray,
        sky: tuple[int, int, int],
        time_of_day: Any,
    ) -> np.ndarray:
        """Strengthened time-of-day grade (see _apply_day_grade)."""
        h, w = base.shape[0], base.shape[1]
        wash, d_value, d_sat = _grade_for(time_of_day)

        ys = np.linspace(-1.0, 1.0, h, dtype=np.float32).reshape(h, 1)
        xs = np.linspace(-1.0, 1.0, w, dtype=np.float32).reshape(1, w)
        # Radial distance, normalised so a corner reads ~1.0.
        radius = np.sqrt(xs * xs + ys * ys) / np.float32(np.sqrt(2.0))
        # Vignette weight: a modest centre floor plus a per-beat wash that ramps
        # toward the corners, so the tint is still a "moment in a day", never flat.
        base_w = 0.06 + np.float32(wash) * (radius * radius)
        strength = np.clip(base_w, 0.0, 0.55).astype(np.float32)[..., None]

        sky_arr = np.array(sky, dtype=np.float32).reshape(1, 1, 3)
        graded = base.astype(np.float32) * (1.0 - strength) + sky_arr * strength

        # Per-beat value shift (exposure), gentle and clamped well under blow-out.
        dv = float(np.clip(d_value, 0.6, 1.18))
        graded = graded * dv

        # Per-beat saturation shift around each pixel's own luminance, so the
        # grade reads as a colour script (cool-pink dawn, clean-bright noon, warm
        # coral dusk, cool indigo night) without posterizing.
        ds = float(np.clip(d_sat, 0.7, 1.35))
        lum = (0.2126 * graded[..., 0] + 0.7152 * graded[..., 1] + 0.0722 * graded[..., 2])[..., None]
        graded = lum + (graded - lum) * ds

        return np.clip(graded, 0, 255).astype(np.uint8)

    def _composite_character(self, canvas: Any, beat: Any, height: int, width: int) -> None:
        """Seat the protagonist IN the SEM substrate: scale per beat mood, anchor
        on a rule-of-thirds axis off the hard corner, measure the sprite's real
        alpha footprint so the shadow meets the body, keep clear of the SEM
        chrome + narration scrim, and multiply a two-part ground (wide soft cast
        + tight occlusion core) into the micrograph before compositing the body.

        Any failure in the new geometry degrades to the legacy soft-ellipse
        contact shadow (kept verbatim as the fallback). Never raises."""
        from PIL import Image, ImageDraw, ImageFilter

        from cellauto.character import render_character

        try:
            scale_h, anchor_fx, baseline_fy = _plan_for(beat)
            size = max(48, min(int(height * scale_h), int(min(width, height) * 0.60)))
            char = render_character(
                size=size,
                mood=beat.mood,
                anim_phase=self._phase,
                palette=self.palette,
                sprite=(self._sprite_provider(self.stage) if self._sprite_provider else None),
            )
            if not isinstance(char, Image.Image):
                return
            char = char.convert("RGBA")

            axis_x = int(width * anchor_fx)
            paste_x = axis_x - size // 2
            base_y_target = int(height * baseline_fy)

            # Real alpha footprint — the float fix: meet the body's true edge.
            alpha = np.asarray(char)[..., 3]
            ys, xs = np.where(alpha > 24)
            if xs.size:
                foot_l, foot_r = int(xs.min()), int(xs.max())
                foot_b = int(ys.max())
                foot_cx = (foot_l + foot_r) * 0.5
                foot_w = max(2, foot_r - foot_l)
            else:
                foot_b = size
                foot_cx = size * 0.5
                foot_w = size
            paste_y = base_y_target - foot_b

            # Keep-outs: SEM badge (top-right), scale bar (bottom-left), and the
            # narration scrim ledge (SAME scrim_h as _draw_ribbon — shared helper).
            scrim_h = _scrim_h_for(height)
            keepouts = [
                (int(width * 0.52), 0, width, int(height * 0.11)),
                (0, int(height * 0.92), int(width * 0.46), height),
                (0, height - scrim_h, width, height),
            ]

            def _intersects(b: tuple[int, int, int, int], k: tuple[int, int, int, int]) -> bool:
                return not (b[2] <= k[0] or b[0] >= k[2] or b[3] <= k[1] or b[1] >= k[3])

            box = (paste_x, paste_y, paste_x + size, paste_y + size)
            for _ in range(6):  # bounded, never infinite
                hit = next((k for k in keepouts if _intersects(box, k)), None)
                if hit is None:
                    break
                kx0, ky0, kx1, ky1 = hit
                if ky1 >= height - 2 and paste_y + size > ky0:
                    paste_y = ky0 - size
                elif kx0 > width // 2 and paste_x + size > kx0:
                    paste_x = kx0 - size
                else:
                    paste_y = max(paste_y, ky1)
                if paste_y < 0 or paste_x < 0:
                    size = max(48, int(size * 0.88))
                    paste_x = axis_x - size // 2
                    paste_y = base_y_target - size
                box = (paste_x, paste_y, paste_x + size, paste_y + size)
            paste_x = max(0, min(paste_x, width - size))
            paste_y = max(0, min(paste_y, height - size))
            contact_cx = paste_x + foot_cx
            contact_y = paste_y + foot_b

            # Time-of-day shadow script: a low sun throws the cast long & lateral
            # (afternoon/dusk), noon drops it short & dark straight down, night is
            # faint & cool, dawn soft with a slight offset. Defaults to the prior
            # behaviour for an unknown time-of-day, so this path degrades cleanly.
            try:
                sh_dx, sh_len, sh_soft, sh_op, sh_cool = _shadow_for(getattr(beat, "time_of_day", None))
            except Exception:
                sh_dx, sh_len, sh_soft, sh_op, sh_cool = _DEFAULT_SHADOW
            cast_dx = sh_dx * foot_w
            cast_cx = contact_cx + cast_dx

            # Two-part ground multiplied into the substrate so the grain shows
            # through: wide soft cast shadow (stretched per the sun angle) + tight
            # dark occlusion core anchored directly under the real footprint.
            sh_w = max(2, int(foot_w * 1.55 * sh_len))
            occ_w = int(foot_w * 0.95)
            occ_h = max(3, int(foot_w * 0.22))
            mask = Image.new("L", (width, height), 0)
            md = ImageDraw.Draw(mask)
            md.ellipse(
                (
                    cast_cx - sh_w / 2,
                    contact_y - max(4, int(foot_w * 0.42)) * 0.35,
                    cast_cx + sh_w / 2,
                    contact_y + max(4, int(foot_w * 0.42)) * 0.65,
                ),
                fill=70,
            )
            md.ellipse(
                (
                    contact_cx - occ_w / 2,
                    contact_y - occ_h * 0.5,
                    contact_cx + occ_w / 2,
                    contact_y + occ_h * 0.9,
                ),
                fill=150,
            )
            blur_r = max(2, int(foot_w * 0.06 * max(0.25, sh_soft)))
            mask = mask.filter(ImageFilter.GaussianBlur(blur_r))
            rgb = np.asarray(canvas.convert("RGB"), dtype=np.float32)
            m = np.asarray(mask, dtype=np.float32)[..., None] / 255.0
            # Darkening strength tracks the sun height (dark noon, faint night),
            # capped at the original 0.85 so the multiply can never go negative.
            dark = float(np.clip(0.85 * sh_op, 0.0, 0.92))
            # Per-channel tint: warm shadows lean coral (lift R, drop B), cool
            # shadows lean indigo (lift B, drop R). |coolness| stays small so the
            # ground never tints the substrate where the mask is zero.
            cool = float(np.clip(sh_cool, -1.0, 1.0))
            tint = np.array(
                [1.0 - 0.12 * cool, 1.0 - 0.04 * abs(cool), 1.0 + 0.14 * cool],
                dtype=np.float32,
            ).reshape(1, 1, 3)
            shade = (1.0 - dark * m) * (1.0 - m + m * tint)
            rgb = rgb * shade
            ground = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
            canvas.paste(ground, (0, 0))

            # Body composites LAST, on top of its own ground.
            canvas.alpha_composite(char, (paste_x, paste_y))
        except Exception:
            # Fallback: legacy soft-ellipse contact shadow, lower-left.
            size = max(16, int(height * 0.22))
            sprite = self._sprite_provider(self.stage) if self._sprite_provider else None
            char = render_character(
                size=size,
                mood=beat.mood,
                anim_phase=self._phase,
                palette=self.palette,
                sprite=sprite,
            )
            if not isinstance(char, Image.Image):
                return
            margin = max(4, int(height * 0.03))
            cx = margin
            cy = height - size - margin
            shadow = Image.new("RGBA", (size, max(2, size // 4)), (0, 0, 0, 0))
            sdraw = ImageDraw.Draw(shadow)
            sw, sh = shadow.size
            sdraw.ellipse((sw * 0.12, 0, sw * 0.88, sh), fill=(0, 0, 0, 110))
            shadow = shadow.filter(ImageFilter.GaussianBlur(max(1, size // 24)))
            canvas.alpha_composite(shadow, (cx, height - margin - sh))
            canvas.alpha_composite(char.convert("RGBA"), (cx, cy))

    @staticmethod
    def _accent_from_sky(sky: Any) -> tuple[int, int, int]:
        """Derive the single overlay accent from ``beat.sky`` — the same source
        that drives the day-grade, so accent and grade can never disagree.

        Lifts a dark (night) sky's luminance to a visible ~0.62, then applies a
        mild saturation lift so the rule reads as an accent, not a wash.
        Returns an RGB tuple."""
        c = np.array(sky, dtype=np.float32)
        lum = (0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]) / 255.0
        c = np.clip(c * (0.62 / max(lum, 1e-3)), 0, 255)
        m = c.mean()
        c = np.clip(m + (c - m) * 1.25, 0, 255)
        return (int(c[0]), int(c[1]), int(c[2]))

    @staticmethod
    def _scrim_rgba(
        width: int, scrim_h: int, ink: tuple[int, int, int] = (7, 9, 12), a_max: int = 190
    ) -> Any:
        """A vertical gradient scrim RGBA image: transparent at the top edge,
        ramping (smoothstep) to ``a_max`` alpha at the bottom — no hard edge."""
        from PIL import Image

        t = np.linspace(0.0, 1.0, max(1, scrim_h), dtype=np.float32)
        eased = t * t * (3.0 - 2.0 * t)
        alpha = (eased * a_max).astype(np.uint8)[:, None]
        rgb = np.empty((scrim_h, width, 3), np.uint8)
        rgb[:] = ink
        a = np.broadcast_to(alpha, (scrim_h, width))[..., None]
        return Image.fromarray(np.concatenate([rgb, a], axis=2), "RGBA")

    def _scrim_for(self, width: int, scrim_h: int) -> Any:
        """Memoized gradient scrim keyed (width, scrim_h)."""
        key = (int(width), int(scrim_h))
        cached = self._scrim_cache.get(key)
        if cached is None:
            cached = self._scrim_rgba(width, scrim_h)
            self._scrim_cache[key] = cached
        return cached

    @staticmethod
    def _ink_text(draw: Any, xy: tuple[int, int], s: str, font: Any, fill: Any) -> None:
        """Draw ``s`` with a 1px ink drop-shadow first, for legibility over
        bright (noon) skies, then the glyphs themselves."""
        draw.text((xy[0] + 1, xy[1] + 1), s, font=font, fill=(0, 0, 0, 110))
        draw.text(xy, s, font=font, fill=fill)

    def _draw_ribbon(self, canvas: Any, beat: Any, height: int, width: int) -> None:
        """Cinematic lower-third: gradient scrim, tracked mono kicker + demoted
        clock, a sky-derived accent rule, a serif hero title and an italic serif
        narration line with a typewriter reveal. Never raises."""
        from PIL import ImageDraw

        from cellauto.renderer_sem import _load_mono_font, _load_serif_font

        # Typography — hierarchy manufactured by SCALE (title ~2.6x clock).
        title_font = _load_serif_font(max(22, int(height * 0.052)))
        body_font = _load_serif_font(max(13, int(height * 0.030)), italic=True)
        label_font = _load_mono_font(max(9, int(height * 0.018)))  # kicker + clock ONLY
        if title_font is None or body_font is None or label_font is None:
            return  # Fonts unavailable → skip text silently.

        # Palette-aware ink vocabulary (rhymes with the SEM chrome). The scrim
        # base ink (7, 9, 12) lives in _scrim_rgba's default.
        warm = self.palette != "cool-mono"
        BONE = (0xF4, 0xEC, 0xDB) if warm else (0xEC, 0xF1, 0xF5)  # noqa: N806 — hero title
        BODY = (0xCB, 0xC2, 0xB0) if warm else (0xC2, 0xCB, 0xD4)  # noqa: N806 — narration
        CAP = (0x9A, 0x90, 0x7E) if warm else (0x8C, 0x97, 0xA4)  # noqa: N806 — kicker + clock
        try:
            ACCENT = self._accent_from_sky(beat.sky)  # noqa: N806 — sky-derived accent
        except Exception:
            ACCENT = BONE  # noqa: N806

        pad = max(10, int(width * 0.055))  # editorial side margin

        # Gradient scrim (memoized), composited first.
        scrim_h = _scrim_h_for(height)
        canvas.alpha_composite(self._scrim_for(width, scrim_h), (0, height - scrim_h))
        draw = ImageDraw.Draw(canvas)

        # Typewriter reveal (deterministic in self._phase). To avoid an orphan
        # stray glyph (e.g. a lone "I") at the start of each beat, SUPPRESS the
        # narration line until the reveal has produced a substantive fragment:
        # at least the first whole word (>= 2 chars, so a one-letter "I" alone
        # does not unlock) OR >= 3 characters. Sub-word reveals draw nothing.
        phase = self._phase - int(self._phase)
        reveal = min(1.0, phase * 2.2)
        line = beat.line or ""
        n_chars = int(len(line) * reveal)
        shown = self._reveal_text(line, n_chars)
        wrapped = self._wrap(shown, body_font, width - 2 * pad) if shown else []

        # Bottom-up layout.
        row_h = int(height * 0.040)
        body_h = len(wrapped) * row_h
        y_body = height - max(10, int(height * 0.03)) - body_h
        y_title = y_body - int(height * 0.062)
        y_rule = y_title - max(2, height // 360) - int(height * 0.006)
        y_kick = max(int(height * 0.02), y_rule - int(height * 0.024))

        # Kicker + demoted clock (mono, tracked, faint — provenance, appears once).
        kicker = " ".join("DAY IN THE LIFE")
        draw.text((pad, y_kick), kicker, font=label_font, fill=CAP + (150,))
        clk = " ".join(beat.clock)
        cw = draw.textbbox((0, 0), clk, font=label_font)[2]
        draw.text((width - pad - cw, y_kick), clk, font=label_font, fill=CAP + (120,))

        # Accent rule — the ONLY accent chrome; left-anchored, partial-width.
        tw = draw.textbbox((0, 0), beat.title, font=title_font)[2]
        rule_w = min(tw, width - 2 * pad)
        draw.line([(pad, y_rule), (pad + rule_w, y_rule)], fill=ACCENT + (235,), width=max(2, height // 360))

        # Hero serif title with a 1px ink shadow (noon legibility).
        draw.text((pad + 1, y_title + 1), beat.title, font=title_font, fill=(0, 0, 0, 130))
        draw.text((pad, y_title), beat.title, font=title_font, fill=BONE + (245,))

        # Italic serif narration, dimmer, with the same 1px ink shadow per row.
        y = y_body
        for row in wrapped:
            self._ink_text(draw, (pad, y), row, body_font, BODY + (235,))
            y += row_h

    @staticmethod
    def _reveal_text(line: str, n_chars: int) -> str:
        """Typewriter slice that suppresses orphan sub-word fragments.

        Returns ``line[:n_chars]`` once the reveal is substantive — at least the
        first whole word (>= 2 chars, so a lone "I" does not unlock the line) OR
        >= 3 revealed characters — and an empty string for any earlier (sub-word)
        reveal, so a stray first glyph is never drawn. Deterministic in n_chars;
        never raises."""
        try:
            if not line or n_chars <= 0:
                return ""
            n = min(int(n_chars), len(line))
            if n >= 3:
                return line[:n]
            # First whole word completed? (a delimiter at/after position n, and
            # the word itself is >= 2 chars so single-letter words stay hidden).
            head = line[:n]
            first_word = head.split()[0] if head.split() else ""
            word_done = n < len(line) and line[n].isspace()
            if word_done and len(first_word) >= 2:
                return head
            return ""
        except Exception:
            # Defensive: fall back to the legacy slice (never raise into render).
            return line[: max(1, int(n_chars))] if line else ""

    @staticmethod
    def _wrap(text: str, font: Any, max_w: int) -> list[str]:
        """Greedy word-wrap ``text`` to fit ``max_w`` pixels under ``font``."""
        if not text:
            return [""]

        def _measure(s: str) -> int:
            try:
                bbox = font.getbbox(s)
                return int(bbox[2] - bbox[0])
            except Exception:
                return len(s) * max(1, getattr(font, "size", 8) // 2)

        words = text.split()
        lines: list[str] = []
        cur = ""
        for word in words:
            trial = word if not cur else cur + " " + word
            if _measure(trial) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines or [""]
