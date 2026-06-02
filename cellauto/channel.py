"""Narrative animation channel (v4.1) — the separate "Day in the Life" layer.

cellauto has two visual channels now:

  Channel A — the GROUNDED SEM micrograph (``cellauto.renderer_sem``). Every
              pixel traces to a real ``render_rgb(state)`` value. Unchanged.
  Channel B — THIS: the anthropomorphized "day in the life of the cell" story
              layer. It composites, on top of a finished SEM frame:
                * the protagonist character (``cellauto.character``),
                * a typeset narration ribbon + day-clock (``cellauto.narrative``),
                * a gentle time-of-day light grade,
                * a small "STORY" tag so it never masquerades as instrument truth.

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
          4. a dim narration ribbon along the bottom carrying the day-clock,
             title and a width-wrapped line, with a gentle typewriter reveal
             driven by self._phase.
          5. a small tracked "STORY · DAY IN THE LIFE" tag upper-left so the
             layer is unmistakably narration, not the instrument feed.
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
        out = self._apply_day_grade(base, beat.sky)

        # Everything past here is best-effort PIL compositing; any failure
        # falls back to the already-graded frame.
        try:
            canvas = Image.fromarray(out, "RGB").convert("RGBA")
            self._composite_character(canvas, beat, height, width)
            self._draw_ribbon(canvas, beat, height, width)
            self._draw_story_tag(canvas, height, width)
            out = np.asarray(canvas.convert("RGB"), dtype=np.uint8)
        except Exception:
            out = np.ascontiguousarray(out, dtype=np.uint8)

        return out

    # ── Composition helpers (numpy + PIL, all lazy-imported) ─────────────────

    def _apply_day_grade(self, base: np.ndarray, sky: tuple[int, int, int]) -> np.ndarray:
        """Blend ``base`` toward ``sky`` with a vignette weight (gentle centre,
        stronger corners). Returns a NEW (H, W, 3) uint8 array."""
        h, w = base.shape[0], base.shape[1]
        ys = np.linspace(-1.0, 1.0, h, dtype=np.float32).reshape(h, 1)
        xs = np.linspace(-1.0, 1.0, w, dtype=np.float32).reshape(1, w)
        # Radial distance, normalised so a corner reads ~1.0.
        radius = np.sqrt(xs * xs + ys * ys) / np.float32(np.sqrt(2.0))
        # ~10% centre → ~30% corners, smoothly ramped.
        strength = (0.10 + 0.20 * (radius**2)).astype(np.float32)[..., None]
        sky_arr = np.array(sky, dtype=np.float32).reshape(1, 1, 3)
        graded = base.astype(np.float32) * (1.0 - strength) + sky_arr * strength
        return np.clip(graded, 0, 255).astype(np.uint8)

    def _composite_character(self, canvas: Any, beat: Any, height: int, width: int) -> None:
        """Render the protagonist + a soft contact shadow, lower-left."""
        from PIL import Image, ImageDraw, ImageFilter

        from cellauto.character import render_character

        size = max(16, int(height * 0.22))
        sprite = self._sprite_provider(self.stage) if self._sprite_provider else None
        char = render_character(
            size=size,
            mood=beat.mood,
            anim_phase=self._phase,
            palette=self.palette,
            sprite=sprite,
        )
        # render_character may return a duck-typed stub when PIL is missing;
        # guard for a real RGBA image with alpha_composite support.
        if not isinstance(char, Image.Image):
            return

        margin = max(4, int(height * 0.03))
        cx = margin
        cy = height - size - margin
        # Contact shadow: a soft, flattened ellipse beneath the character.
        shadow = Image.new("RGBA", (size, max(2, size // 4)), (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(shadow)
        sw, sh = shadow.size
        sdraw.ellipse((sw * 0.12, 0, sw * 0.88, sh), fill=(0, 0, 0, 110))
        shadow = shadow.filter(ImageFilter.GaussianBlur(max(1, size // 24)))
        canvas.alpha_composite(shadow, (cx, height - margin - sh))
        canvas.alpha_composite(char.convert("RGBA"), (cx, cy))

    def _draw_ribbon(self, canvas: Any, beat: Any, height: int, width: int) -> None:
        """Dim bottom plate with day-clock + title + width-wrapped line."""
        from PIL import Image, ImageDraw

        from cellauto.renderer_sem import _load_mono_font

        body_font = _load_mono_font(size=max(11, int(height * 0.026)))
        head_font = _load_mono_font(size=max(12, int(height * 0.032)))
        if body_font is None or head_font is None:
            return  # Fonts unavailable → skip text silently.

        pad = max(6, int(height * 0.02))
        line_h = max(12, int(height * 0.034))
        text_w = width - 2 * pad

        # Typewriter reveal: ramp over ~half the phase cycle, then hold full.
        phase = self._phase - int(self._phase)
        reveal = min(1.0, phase * 2.2)
        line = beat.line
        shown = line[: max(1, int(len(line) * reveal))] if line else ""

        wrapped = self._wrap(shown, body_font, text_w)
        n_body = max(1, len(wrapped))
        # Plate spans header line + body lines.
        plate_h = pad * 2 + line_h + n_body * line_h
        plate_top = height - plate_h

        plate = Image.new("RGBA", (width, plate_h), (8, 10, 14, 165))
        canvas.alpha_composite(plate, (0, plate_top))

        draw = ImageDraw.Draw(canvas)
        accent = (0x39, 0xD4, 0xC8, 235)
        bone = (0xE6, 0xDC, 0xC5, 235)
        y = plate_top + pad
        header = f"{beat.clock}  ·  {beat.title}"
        draw.text((pad, y), header, font=head_font, fill=accent)
        y += line_h
        for row in wrapped:
            draw.text((pad, y), row, font=body_font, fill=bone)
            y += line_h

    def _draw_story_tag(self, canvas: Any, height: int, width: int) -> None:
        """Small tracked 'STORY · DAY IN THE LIFE' label on a tiny plate."""
        from PIL import Image, ImageDraw

        from cellauto.renderer_sem import _load_mono_font

        font = _load_mono_font(size=max(9, int(height * 0.020)))
        if font is None:
            return
        label = "STORY · DAY IN THE LIFE"
        draw = ImageDraw.Draw(canvas)
        bbox = draw.textbbox((0, 0), label, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        px = max(3, int(width * 0.018))
        py = max(3, int(height * 0.018))
        ppx = max(3, int(width * 0.008))
        ppy = max(2, int(height * 0.006))
        plate = Image.new("RGBA", (tw + 2 * ppx, th + 2 * ppy), (8, 10, 14, 175))
        canvas.alpha_composite(plate, (px, py))
        draw.text((px + ppx, py + ppy - bbox[1]), label, font=font, fill=(0xD4, 0x39, 0xA4, 235))

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
