"""Animated amoeba mascot — the cellauto colony's friendly avatar.

A small self-contained ``ttk.Frame`` containing a Tk canvas that draws a
single round-eyed amoeba and breathes life into the app chrome:

  - the eyes wander a little so it always feels like it's looking around
  - it blinks every few seconds
  - the body bobs gently up and down
  - it changes expression when the simulation is running or paused

Pure Tk canvas primitives, no PIL dependency at runtime.  Uses ``after``
loops for animation, which means it shares the main Tk event loop and
will pause cleanly when the window is destroyed.
"""

from __future__ import annotations

import math
import random
import tkinter as tk
from typing import Any

BODY_TEAL = "#39d4c8"
BODY_TEAL_HI = "#5ee7dc"
BODY_MAGENTA = "#d439a4"
EYE_WHITE = "#fdf6e3"
PUPIL = "#0a0e16"
HIGHLIGHT = "#ffffff"
BG = "#0a0e16"


class AmoebaMascot(tk.Canvas):
    """Animated amoeba drawn on a small square Tk canvas."""

    def __init__(self, master: Any, size: int = 64, **kwargs: Any) -> None:
        super().__init__(
            master,
            width=size,
            height=size,
            background=BG,
            highlightthickness=0,
            borderwidth=0,
            **kwargs,
        )
        self._size = size
        self._cx = size / 2
        self._cy = size / 2
        self._frame = 0
        self._happy = True  # smile vs neutral
        self._rng = random.Random(0xCE11)
        # Item handles so we can reconfigure rather than recreate each frame.
        self._body: int | None = None
        self._highlight: int | None = None
        self._eye_l: int | None = None
        self._eye_r: int | None = None
        self._pupil_l: int | None = None
        self._pupil_r: int | None = None
        self._mouth: int | None = None
        # Target gaze (where the pupils want to be, relative to centre, in
        # units of "max pupil offset"). Wanders smoothly over time.
        self._gaze_target = (0.0, 0.0)
        self._gaze = (0.0, 0.0)
        self._blink_in = self._rng.randint(80, 180)
        self._blink_for = 0
        self._build()
        self._tick()

    # ── Lifecycle ───────────────────────────────────────────────────────────

    def set_happy(self, happy: bool) -> None:
        if happy == self._happy:
            return
        self._happy = happy
        self._draw_mouth()

    # ── Drawing ─────────────────────────────────────────────────────────────

    def _build(self) -> None:
        s = self._size
        cx, cy = self._cx, self._cy
        # Body radius — slightly squashed.
        r = s * 0.38

        # Soft outer body.
        self._body = self.create_oval(
            cx - r,
            cy - r,
            cx + r,
            cy + r,
            fill=BODY_TEAL,
            outline="",
        )
        # Subtle inner highlight — gives a 3D feel.
        h_r = r * 0.55
        self._highlight = self.create_oval(
            cx - h_r * 0.9,
            cy - r * 0.85,
            cx + h_r * 0.4,
            cy - r * 0.10,
            fill=BODY_TEAL_HI,
            outline="",
        )

        # Eyes (whites). Positioned in the upper half.
        self._eye_white_r = max(2.0, s * 0.10)
        self._pupil_r = max(1.0, self._eye_white_r * 0.55)
        self._eye_dx = s * 0.16
        self._eye_dy = -s * 0.06
        ew = self._eye_white_r
        for side, attr in ((-1, "_eye_l"), (1, "_eye_r")):
            ex = cx + side * self._eye_dx
            ey = cy + self._eye_dy
            setattr(
                self,
                attr,
                self.create_oval(
                    ex - ew,
                    ey - ew,
                    ex + ew,
                    ey + ew,
                    fill=EYE_WHITE,
                    outline="",
                ),
            )
        for side, attr in ((-1, "_pupil_l"), (1, "_pupil_r")):
            ex = cx + side * self._eye_dx
            ey = cy + self._eye_dy
            pr = self._pupil_r
            setattr(
                self,
                attr,
                self.create_oval(
                    ex - pr,
                    ey - pr,
                    ex + pr,
                    ey + pr,
                    fill=PUPIL,
                    outline="",
                ),
            )

        self._draw_mouth()

    def _draw_mouth(self) -> None:
        if self._mouth is not None:
            self.delete(self._mouth)
        s = self._size
        cx, cy = self._cx, self._cy
        mw = s * 0.22
        mh = s * 0.14
        my = cy + s * 0.10
        if self._happy:
            # Smile arc.
            self._mouth = self.create_arc(
                cx - mw / 2,
                my,
                cx + mw / 2,
                my + mh,
                start=200,
                extent=140,
                style="arc",
                outline=PUPIL,
                width=max(1, int(s / 32)),
            )
        else:
            # Neutral O.
            r = s * 0.05
            self._mouth = self.create_oval(
                cx - r,
                my + r,
                cx + r,
                my + 3 * r,
                fill=PUPIL,
                outline="",
            )

    # ── Animation tick (~30 fps via 33 ms after()) ──────────────────────────

    def _tick(self) -> None:
        self._frame += 1
        s = self._size

        # Gaze drift — pick a new target every ~50 frames.
        if self._frame % 50 == 0:
            self._gaze_target = (
                self._rng.uniform(-1, 1),
                self._rng.uniform(-0.6, 0.6),
            )
        # Smoothly approach the gaze target.
        gx = self._gaze[0] + (self._gaze_target[0] - self._gaze[0]) * 0.08
        gy = self._gaze[1] + (self._gaze_target[1] - self._gaze[1]) * 0.08
        self._gaze = (gx, gy)

        # Body bob — sinusoidal vertical wobble.
        bob = math.sin(self._frame * 0.07) * (s * 0.02)

        # Blink scheduling.
        if self._blink_for > 0:
            self._blink_for -= 1
        else:
            self._blink_in -= 1
            if self._blink_in <= 0:
                self._blink_for = 5  # frames the eye is closed
                self._blink_in = self._rng.randint(80, 180)

        self._redraw(bob, self._blink_for > 0)

        try:
            self.after(33, self._tick)
        except tk.TclError:
            return  # widget destroyed

    def _redraw(self, bob: float, blinking: bool) -> None:
        cx, cy = self._cx, self._cy + bob
        s = self._size
        r = s * 0.38

        # Body + highlight follow the bob.
        self.coords(self._body, cx - r, cy - r, cx + r, cy + r)
        h_r = r * 0.55
        self.coords(self._highlight, cx - h_r * 0.9, cy - r * 0.85, cx + h_r * 0.4, cy - r * 0.10)

        ew = self._eye_white_r
        pr = self._pupil_r
        gx, gy = self._gaze
        max_off = ew - pr - 0.5  # pupil stays inside the eye white

        for side, eye_id, pup_id in (
            (-1, self._eye_l, self._pupil_l),
            (1, self._eye_r, self._pupil_r),
        ):
            ex = cx + side * self._eye_dx
            ey = cy + self._eye_dy
            if blinking:
                # Squash the eye white to a thin slit.
                self.coords(eye_id, ex - ew, ey - 0.6, ex + ew, ey + 0.6)
                self.coords(pup_id, ex, ey, ex, ey)
                self.itemconfigure(pup_id, fill="")
            else:
                self.coords(eye_id, ex - ew, ey - ew, ex + ew, ey + ew)
                px = ex + gx * max_off
                py = ey + gy * max_off
                self.coords(pup_id, px - pr, py - pr, px + pr, py + pr)
                self.itemconfigure(pup_id, fill=PUPIL)

        # Mouth follows the body bob.
        mw = s * 0.22
        mh = s * 0.14
        my = cy + s * 0.10
        if self._happy:
            self.coords(self._mouth, cx - mw / 2, my, cx + mw / 2, my + mh)
        else:
            r2 = s * 0.05
            self.coords(self._mouth, cx - r2, my + r2, cx + r2, my + 3 * r2)
