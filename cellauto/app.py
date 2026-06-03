"""Tk GUI sandbox app.

Dispatches between two renderers based on ``rule.renderer_kind``:
  - "discrete" → DiscreteRenderer (canvas items per cell)
  - "field"    → FieldRenderer (numpy → PhotoImage blit)

v3.1 ‘Catalytic Silence’ visual pass:
  - Bundled Italiana / CrimsonPro Italic / IBM Plex Mono TTFs from the
    canvas-design pack, registered at runtime so Tk can render them.
  - Composition reorganised as a museum-style plate: a single titular
    serif gesture, sections separated only by thin teal hairlines and
    Roman-numeralled mono labels (I — CONFIGURATION, II — OBSERVATION,
    …). No card backgrounds, no chrome — restraint is the design.
  - Buttons are outlined specimen-card shapes, not filled colour blocks.
    Colour is information: teal for the canvas frame and primary action,
    magenta only on the record button, dim red only on the stop button.
  - Locked geometry preserved so iterations never reflow the page.
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import json
import logging
import sys
import tempfile
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont
from typing import Any

import numpy as np

from cellauto.channel import NarrativeChannel
from cellauto.engine import Engine
from cellauto.export import export_gif
from cellauto.hires import EXPORT_SIZES, export_hires_png
from cellauto.mascot import AmoebaMascot
from cellauto.renderer import DiscreteRenderer, FieldRenderer, cmap_viridis
from cellauto.renderer_sem import (
    PALETTE_COOL_MONO,
    PALETTE_WARM_SEPIA,
    SemRenderer,
    sem_is_available,
)
from cellauto.rules import REGISTRY
from cellauto.rules.abiogenesis.pipeline import stage_info
from cellauto.rules.abiogenesis.science import GRAY_SCOTT_PRESETS
from cellauto.rules.params import PARAM_SPECS, PEARSON_PRESET_RULES, ParamSpec
from cellauto.sprites import build_sprite_provider
from cellauto.tutorial import tutorial_for

ASSETS_DIR = Path(__file__).parent / "assets"
ICON_PATH = ASSETS_DIR / "icon.png"
FONTS_DIR = ASSETS_DIR / "fonts"

log = logging.getLogger(__name__)

CANVAS_SIZE = 600
DEFAULT_GRID = 60
DEFAULT_FPS = 5.0  # gentle default so the extended pipeline doesn't blow past chapter cards

# ── Catalytic Silence palette ───────────────────────────────────────────────
BG = "#0a0e16"  # obsidian
TEXT = "#e6e0d0"  # warm bone (museum caption)
TEXT_DIM = "#8c8a82"  # quiet bone
HAIRLINE = "#1f4f4c"  # desaturated teal — for thin separators
HAIRLINE_HI = "#39d4c8"  # accent teal — for canvas rim and focus
TEAL_MID = "#2c8d86"  # mid-teal — pulse mid-tone between HAIRLINE and HAIRLINE_HI
RECORD_M = "#d439a4"  # magenta — counterpoint, only on record
STOP_R = "#7a3036"  # restrained brick — only on stop
DISABLED_FG = "#3a3934"  # muted bone — disabled foreground
DISABLED_BORDER = "#262421"  # near-obsidian — disabled bordercolor
PANEL = "#0e1218"  # raised obsidian panel (intentionally not BG)
TOAST_OK = "#9ad8d0"  # bone-tinted teal — success toast, in-system
TOAST_ERR = "#d47d57"  # warm brick — error toast, same family as STOP_R

# Window is fixed so iterations never reflow the layout.
WINDOW_W = 720
WINDOW_H = 1000


# ── v4.0 config (SEM mode preferences) ──────────────────────────────────────

_CONFIG_PATH = Path.home() / ".cellauto" / "config.json"


def _load_sem_config() -> dict:
    """Load persisted v4.0 preferences. Returns an empty dict if absent /
    unreadable — never raises. The file is best-effort; first launch on a
    fresh user account just uses defaults (SEM mode ON, warm-sepia).
    """
    try:
        return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_sem_config(cfg: dict) -> None:
    """Persist v4.0 preferences. Silently swallows IO errors — never user-visible."""
    try:
        _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        _CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    except Exception:
        pass


# ── Font loading ────────────────────────────────────────────────────────────


def _register_bundled_fonts() -> None:
    """Make the bundled TTFs visible to the platform font system.

    On Windows we call gdi32.AddFontResourceExW with FR_PRIVATE so the
    fonts are only visible to this process. On other platforms there is
    no portable equivalent that doesn't require user-level cache
    rebuilds; we fall through to system fonts via the family fallback
    list in ``_setup_theme``.
    """
    if not FONTS_DIR.exists() or sys.platform != "win32":
        return
    try:
        FR_PRIVATE = 0x10
        for ttf in FONTS_DIR.glob("*.ttf"):
            ctypes.windll.gdi32.AddFontResourceExW(str(ttf), FR_PRIVATE, 0)
    except Exception as exc:  # noqa: BLE001
        log.debug("font registration failed: %s", exc)


class App(tk.Frame):
    def __init__(
        self,
        master: tk.Tk,
        rule_name: str = "abiogenesis-pipeline",
        grid_size: int = DEFAULT_GRID,
        seed: int | None = None,
    ) -> None:
        _register_bundled_fonts()
        super().__init__(master)
        self.master_window = master
        self.master_window.title("cellauto — abiogenesis sandbox")
        self.master_window.configure(background=BG)
        self.master_window.geometry(f"{WINDOW_W}x{WINDOW_H}")
        self.master_window.minsize(WINDOW_W, WINDOW_H)
        self.master_window.resizable(False, False)
        self.configure(background=BG)
        self.pack(fill="both", expand=True)

        self._tutorial_index: int = -1
        self._gif_frames: list = []
        self._recording_gif = False
        self.running = False
        # Recorded population stats per step for the sparkline overlay and CSV
        # export. Bounded so it doesn't grow without limit on long runs.
        self._stats_history: list[dict[str, int]] = []
        self._stats_history_cap = 5000
        # Full serialized-state ring for the timeline SCRUB control. Each entry
        # is {"step": int, "state": rule.serialize_state(...)}; capped because
        # field states can be ~hundreds of KB each.
        self._state_history: list[dict] = []
        self._state_history_cap = 120
        # Suppress scrub callbacks during programmatic Scale updates so dragging
        # the slider doesn't loop with restoration.
        self._scrubbing = False
        # Accessibility: 1.0 is the design baseline; View ▸ <size> picks others.
        self._font_scale: float = 1.0
        # Colourblind-safe palette toggle (currently swaps Stage 4's red→green
        # fitness disc colour for a blue→yellow ramp; other diverging maps in
        # the project — chirality teal↔magenta, vents blue↔orange, viridis —
        # are already CVD-friendly).
        self._colorblind_safe = False
        # Story-mode chapter card: a brief title/principle overlay that
        # appears when the pipeline promotes to a new stage. Counted in
        # `_animate` ticks (~20 Hz) so it fades regardless of play state.
        self._chapter_card_ticks_left = 0
        self._chapter_card_duration = 90  # ~4.5 s at 20 Hz
        # L8 + L9 — playback animation. A single 44-frame cycle (2.2 s at
        # 20 Hz) drives both the title-block status dot and the canvas
        # border pulse so they read as one visual heartbeat.
        self._playback_cycle = 44
        self._reduced_motion = False
        self._status_dot_id: int | None = None  # canvas item id for the pulse dot
        self._status_dot_canvas: tk.Canvas | None = None

        # v4.0 — SEM-grade rendering. Capability-detected at startup; if Pillow
        # is too old (no LANCZOS) we fall back to FieldRenderer and emit a
        # one-time toast (S8). Config persists in ~/.cellauto/config.json.
        self._sem_available, self._sem_unavailable_reason = sem_is_available()
        cfg = _load_sem_config()
        self._sem_mode = bool(cfg.get("sem_mode", True)) and self._sem_available
        self._sem_palette = str(cfg.get("sem_palette", PALETTE_WARM_SEPIA))
        if self._sem_palette not in (PALETTE_WARM_SEPIA, PALETTE_COOL_MONO):
            self._sem_palette = PALETTE_WARM_SEPIA
        self._sem_fallback_toast_pending = bool(cfg.get("sem_mode", True)) and not self._sem_available

        # v4.1 — Channel B (narrative "Day in the Life") + hi-res render scale.
        # The channel is an additive, toggleable post-compositor over the SEM
        # frame; render_scale (1/2/3×) supersamples the live canvas. Both persist
        # in the same config file as the SEM prefs.
        self._story_enabled = bool(cfg.get("story_enabled", False))
        self._render_scale = int(cfg.get("render_scale", 1))
        if self._render_scale not in (1, 2, 3):
            self._render_scale = 1
        self._channel = NarrativeChannel(
            size=CANVAS_SIZE,
            palette=self._sem_palette,
            enabled=self._story_enabled,
            reduced_motion=self._reduced_motion,
        )
        # Install generated protagonist body art if any is present on disk;
        # build_sprite_provider() returns None when the asset dir is empty, so
        # the channel keeps its fully-procedural body in the shipped build.
        try:
            self._channel.set_sprite_provider(build_sprite_provider())
        except Exception:
            pass

        self._setup_theme()
        self._build_widgets()
        self._build_menu()
        self._apply_window_icon()
        self._renderer: FieldRenderer | DiscreteRenderer | SemRenderer | None = None
        self._new_engine(rule_name=rule_name, grid_size=grid_size, seed=seed)
        self._anim_frame = 0
        self._animate()
        # S8 — one-time fallback notice if SEM was requested by config but
        # unavailable on this platform (e.g. Pillow too old). Scheduled after
        # widgets exist so the toast strip is ready.
        if self._sem_fallback_toast_pending:
            self.master_window.after(
                250,
                lambda: self._toast(
                    f"SEM mode unavailable, using viridis ({self._sem_unavailable_reason})",
                    kind="warn",
                ),
            )
            self._sem_fallback_toast_pending = False

    # ── Theme ───────────────────────────────────────────────────────────────

    def _setup_theme(self) -> None:
        """Configure ttk styles for the Catalytic Silence aesthetic."""
        style = ttk.Style(self.master_window)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        available = set(tkfont.families())

        def first(*candidates: str) -> str:
            for c in candidates:
                if c in available:
                    return c
            return "TkDefaultFont"

        # Resolve the three font voices the philosophy calls for.
        self._fam_display = first("Italiana", "Constantia", "Cambria", "Georgia")
        self._fam_italic = first("Crimson Pro", "CrimsonPro", "Constantia", "Georgia", "TkDefaultFont")
        self._fam_mono = first("IBM Plex Mono", "IBMPlexMono", "Cascadia Mono", "Consolas", "TkFixedFont")
        # Widget body text stays in the bundled mono; platform sans is only a
        # last-resort fallback so the system never leaks Segoe UI into the UI.
        self._fam_ui = first("IBM Plex Mono", "IBMPlexMono", "Segoe UI", "TkDefaultFont")

        # 3-tuples throughout so mypy's tk stub overloads accept the fonts as
        # arguments to canvas.create_text (the 2-tuple form only matches a
        # 1-arg overload).
        self._font_title = (self._fam_display, 22, "normal")
        self._font_eyebrow = (self._fam_mono, 9, "normal")  # tracked microcaps
        self._font_section_num = (self._fam_display, 16, "normal")  # Roman numerals
        self._font_section = (self._fam_mono, 9, "bold")
        self._font_button = (self._fam_mono, 9, "bold")
        self._font_label = (self._fam_mono, 9, "normal")
        self._font_value = (self._fam_mono, 10, "normal")
        self._font_caption = (self._fam_italic, 11, "italic")
        self._font_ui_widget = (self._fam_ui, 9, "normal")

        # Base widget colours.
        style.configure(
            ".",
            background=BG,
            foreground=TEXT,
            bordercolor=HAIRLINE,
            lightcolor=HAIRLINE,
            darkcolor=HAIRLINE,
            focuscolor=BG,
            fieldbackground=BG,
            font=self._font_ui_widget,
        )

        style.configure("TFrame", background=BG)

        style.configure("TLabel", background=BG, foreground=TEXT, font=self._font_label)
        style.configure("Title.TLabel", background=BG, foreground=TEXT, font=self._font_title)
        style.configure("Eyebrow.TLabel", background=BG, foreground=TEXT_DIM, font=self._font_eyebrow)
        style.configure("Roman.TLabel", background=BG, foreground=TEXT, font=self._font_section_num)
        style.configure("Section.TLabel", background=BG, foreground=TEXT_DIM, font=self._font_section)
        style.configure("Apparatus.TLabel", background=BG, foreground=TEXT_DIM, font=self._font_label)
        style.configure("Value.TLabel", background=BG, foreground=TEXT, font=self._font_value)
        style.configure("Caption.TLabel", background=BG, foreground=TEXT, font=self._font_caption)
        # L1 — stage wall-label title style: a small-display serif, halfway
        # between the section-numeral and the page title.
        style.configure("StageTitle.TLabel", background=BG, foreground=TEXT, font=self._font_section_num)

        # Outlined museum-card buttons.
        style.configure(
            "TButton",
            background=BG,
            foreground=TEXT,
            bordercolor=HAIRLINE,
            lightcolor=BG,
            darkcolor=BG,
            relief="solid",
            borderwidth=1,
            focusthickness=0,
            focuscolor=BG,
            padding=(18, 10),
            font=self._font_button,
        )
        style.map(
            "TButton",
            background=[("active", "#10141d"), ("pressed", BG), ("disabled", BG)],
            foreground=[("disabled", DISABLED_FG)],
            bordercolor=[("active", HAIRLINE_HI), ("disabled", DISABLED_BORDER)],
        )

        # Primary (play): teal hairline always.
        style.configure(
            "Primary.TButton",
            background=BG,
            foreground=HAIRLINE_HI,
            bordercolor=HAIRLINE_HI,
            lightcolor=BG,
            darkcolor=BG,
        )
        style.map(
            "Primary.TButton",
            background=[("active", "#0f1a1e"), ("pressed", BG), ("disabled", BG)],
            foreground=[("disabled", DISABLED_FG)],
            bordercolor=[("disabled", DISABLED_BORDER), ("active", HAIRLINE_HI)],
        )

        # Stop: restrained brick.
        style.configure(
            "Danger.TButton",
            background=BG,
            foreground=STOP_R,
            bordercolor=STOP_R,
            lightcolor=BG,
            darkcolor=BG,
        )
        style.map(
            "Danger.TButton",
            background=[("active", "#1a0e10"), ("pressed", BG), ("disabled", BG)],
            foreground=[("disabled", DISABLED_FG)],
            bordercolor=[("disabled", DISABLED_BORDER), ("active", STOP_R)],
        )

        # Record: magenta hairline.
        style.configure(
            "Record.TButton",
            background=BG,
            foreground=RECORD_M,
            bordercolor=RECORD_M,
            lightcolor=BG,
            darkcolor=BG,
        )
        style.map(
            "Record.TButton",
            background=[("active", "#1a0d18"), ("pressed", BG)],
            bordercolor=[("active", RECORD_M)],
        )

        # Combobox — flat field, hairline border, mono text.
        style.configure(
            "TCombobox",
            fieldbackground=BG,
            background=BG,
            foreground=TEXT,
            arrowcolor=HAIRLINE_HI,
            bordercolor=HAIRLINE,
            lightcolor=BG,
            darkcolor=BG,
            padding=(8, 6),
            font=self._font_value,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", BG), ("disabled", BG)],
            foreground=[("disabled", DISABLED_FG)],
            bordercolor=[("active", HAIRLINE_HI), ("focus", HAIRLINE_HI)],
            arrowcolor=[("active", TEXT)],
        )
        # Dropdown listbox (separate Toplevel — needs X resources).
        self.master_window.option_add("*TCombobox*Listbox.background", BG)
        self.master_window.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.master_window.option_add("*TCombobox*Listbox.selectBackground", HAIRLINE_HI)
        self.master_window.option_add("*TCombobox*Listbox.selectForeground", BG)
        self.master_window.option_add("*TCombobox*Listbox.font", self._font_value)
        self.master_window.option_add("*TCombobox*Listbox.borderWidth", 0)
        self.master_window.option_add("*TCombobox*Listbox.relief", "flat")

        # FPS scale — extremely thin trough.
        style.configure(
            "TScale",
            background=BG,
            troughcolor=HAIRLINE,
            bordercolor=BG,
            lightcolor=HAIRLINE_HI,
            darkcolor=HAIRLINE_HI,
        )

        # GIF-export progressbar.
        style.configure(
            "Accent.Horizontal.TProgressbar",
            troughcolor=HAIRLINE,
            background=HAIRLINE_HI,
            bordercolor=BG,
            lightcolor=HAIRLINE_HI,
            darkcolor=HAIRLINE_HI,
            thickness=8,
        )

        # Native menu — quiet obsidian.
        self.master_window.option_add("*Menu.background", BG)
        self.master_window.option_add("*Menu.foreground", TEXT)
        self.master_window.option_add("*Menu.activeBackground", HAIRLINE_HI)
        self.master_window.option_add("*Menu.activeForeground", BG)
        self.master_window.option_add("*Menu.borderWidth", 0)
        self.master_window.option_add("*Menu.font", self._font_label)

    def _apply_window_icon(self) -> None:
        if not ICON_PATH.exists():
            return
        try:
            self._window_icon = tk.PhotoImage(file=str(ICON_PATH))
            self.master_window.iconphoto(True, self._window_icon)
        except tk.TclError as exc:
            log.debug("could not set window icon: %s", exc)

    # ── Engine wiring ───────────────────────────────────────────────────────

    def _new_engine(self, rule_name: str, grid_size: int, seed: int | None) -> None:
        if rule_name not in REGISTRY:
            raise ValueError(f"unknown rule '{rule_name}'")
        rule = REGISTRY[rule_name]()
        kwargs: dict[str, Any] = {"width": grid_size, "height": grid_size, "rule": rule}
        if seed is not None:
            kwargs["seed"] = seed
        self.engine = Engine(**kwargs)
        self.rule_var.set(rule_name)
        self.grid_size_var.set(str(grid_size))
        self._init_renderer()
        self._render()
        self._update_status()
        self._rebuild_parameters()
        self._sync_pipeline_row()
        self._stats_history.clear()
        self._state_history.clear()
        self._record_state_snapshot()  # seed step 0 so the scrubber has a baseline
        # Don't carry an in-progress chapter card from the previous run into
        # the new one — _sync_stage_caption will pop a fresh one for the
        # starting stage if the rule is a pipeline.
        self._chapter_card_ticks_left = 0
        # Force chapter-card cleanup any previous overlay items that survived
        # the renderer re-init (defensive).
        try:
            self.canvas.delete("chapter_card")
        except tk.TclError:
            pass

    def _state_dims(self) -> tuple[int, int]:
        state = self.engine.state
        if hasattr(state, "width") and hasattr(state, "height"):
            return state.width, state.height
        if hasattr(state, "concentrations"):
            h, w = state.concentrations.shape[:2]
            return w, h
        if hasattr(state, "inner_state"):
            inner = state.inner_state
            if hasattr(inner, "width") and hasattr(inner, "height"):
                return inner.width, inner.height
            if hasattr(inner, "concentrations"):
                h, w = inner.concentrations.shape[:2]
                return w, h
        return self.engine.width, self.engine.height

    def _init_renderer(self) -> None:
        kind = getattr(self.engine.rule, "renderer_kind", "discrete")
        w, h = self._state_dims()
        renderer: FieldRenderer | DiscreteRenderer | SemRenderer
        inner = getattr(self.engine.state, "inner_rule", None)
        sem_eligible = bool(
            getattr(inner, "sem_eligible", False) or getattr(self.engine.rule, "sem_eligible", False)
        )
        if (kind == "field" or sem_eligible) and self._sem_mode and self._sem_available:
            renderer = SemRenderer(
                canvas=self.canvas,
                canvas_size=CANVAS_SIZE,
                palette=self._sem_palette,
                reduced_motion=self._reduced_motion,
                running=self.running,
                render_size=(self._render_scale * CANVAS_SIZE if self._render_scale > 1 else 0),
            )
            self._apply_sem_stage_label(renderer)
        elif kind == "field":
            renderer = FieldRenderer(canvas=self.canvas, canvas_size=CANVAS_SIZE)
        else:
            renderer = DiscreteRenderer(canvas=self.canvas, canvas_size=CANVAS_SIZE)
        renderer.reset(w, h)
        self._renderer = renderer
        self._sync_story_channel()

    def _pipeline_len(self) -> int:
        """Number of stages in the active pipeline (used to map the live stage
        onto a narrative beat). Plain rules with no pipeline report 12 so the
        extended day-in-the-life arc is used by default."""
        classes = getattr(self.engine.rule, "stage_classes", None)
        if classes is not None:
            try:
                return max(1, len(classes))
            except TypeError:
                pass
        return 12

    def _sync_story_channel(self) -> None:
        """Keep Channel B's enabled-state, palette, reduced-motion and pipeline
        stage in sync, and install / remove it as the SEM post-compositor. Safe
        to call whenever the renderer, stage, palette or prefs change."""
        self._channel.set_enabled(self._story_enabled)
        self._channel.set_palette(self._sem_palette)
        self._channel.set_reduced_motion(self._reduced_motion)
        stage = getattr(self.engine.state, "current_stage", None)
        self._channel.set_stage(int(stage) if stage is not None else 0, self._pipeline_len())
        if isinstance(self._renderer, SemRenderer):
            self._renderer.post_compositor = self._channel.compose if self._story_enabled else None

    def _persist_view_config(self) -> None:
        """Persist all v4.0/v4.1 view preferences together so writing one key
        (e.g. palette) never clobbers another (e.g. story toggle)."""
        _save_sem_config(
            {
                "sem_mode": self._sem_mode,
                "sem_palette": self._sem_palette,
                "story_enabled": self._story_enabled,
                "render_scale": self._render_scale,
            }
        )

    # ── Accessibility ───────────────────────────────────────────────────────

    def _apply_font_scale(self, scale: float) -> None:
        """Recompute font tuples at the given scale (1.0 is design baseline) and
        re-apply them through ttk styles so every label, button, and caption
        updates uniformly. Canvas-overlay text (stage caption, legend, sparkline)
        is redrawn via ``_sync_stage_caption`` to pick up the new sizes."""
        self._font_scale = max(0.6, min(2.0, float(scale)))
        sc = self._font_scale

        def s(base: int) -> int:
            return max(7, int(round(base * sc)))

        self._font_title = (self._fam_display, s(22), "normal")
        self._font_eyebrow = (self._fam_mono, s(9), "normal")
        self._font_section_num = (self._fam_display, s(16), "normal")
        self._font_section = (self._fam_mono, s(9), "bold")
        self._font_button = (self._fam_mono, s(9), "bold")
        self._font_label = (self._fam_mono, s(9), "normal")
        self._font_value = (self._fam_mono, s(10), "normal")
        self._font_caption = (self._fam_italic, s(11), "italic")
        self._font_ui_widget = (self._fam_ui, s(9), "normal")
        style = ttk.Style(self.master_window)
        style.configure(".", font=self._font_ui_widget)
        style.configure("TLabel", font=self._font_label)
        style.configure("Title.TLabel", font=self._font_title)
        style.configure("Eyebrow.TLabel", font=self._font_eyebrow)
        style.configure("Roman.TLabel", font=self._font_section_num)
        style.configure("Section.TLabel", font=self._font_section)
        style.configure("Apparatus.TLabel", font=self._font_label)
        style.configure("Value.TLabel", font=self._font_value)
        style.configure("Caption.TLabel", font=self._font_caption)
        style.configure("TButton", font=self._font_button)
        # Refresh on-canvas text so the overlay matches the new size immediately.
        if hasattr(self, "canvas"):
            self._sync_stage_caption()

    # ── Layout primitives ───────────────────────────────────────────────────

    def _hairline(self, parent: tk.Widget, color: str = HAIRLINE, height: int = 1) -> tk.Frame:
        return tk.Frame(parent, background=color, height=height, borderwidth=0, highlightthickness=0)

    def _section(
        self, parent: tk.Widget, roman: str, name: str, pad_top: int = 14, pad_bottom: int = 8
    ) -> ttk.Frame:
        """A section header: Italiana Roman numeral · tracked mono label,
        followed by a thin teal hairline rule. Returns the body Frame the
        caller fills with section content."""
        block = ttk.Frame(parent)
        block.pack(fill="x", pady=(pad_top, 0))

        head = ttk.Frame(block)
        head.pack(fill="x")
        ttk.Label(head, text=roman, style="Roman.TLabel").pack(side="left", padx=(0, 10))
        # Letter-spacing in Tk is faked by joining chars with spaces.
        spaced = "  ".join(name)
        ttk.Label(head, text=spaced, style="Section.TLabel").pack(side="left", pady=(6, 0))

        rule = self._hairline(block)
        rule.pack(fill="x", pady=(8, pad_bottom))

        body = ttk.Frame(block)
        body.pack(fill="x")
        return body

    # ── Layout ──────────────────────────────────────────────────────────────

    def _build_widgets(self) -> None:
        # The plate's content is taller than the locked 1000px window, so wrap
        # it in a scrollable canvas. This guarantees every section — including
        # the transport controls and the marginalia — is always reachable, on
        # any screen size, without reflowing the fixed-width museum layout.
        scroll_canvas = tk.Canvas(self, background=BG, highlightthickness=0, borderwidth=0)
        vbar = ttk.Scrollbar(self, orient="vertical", command=scroll_canvas.yview)
        scroll_canvas.configure(yscrollcommand=vbar.set)
        vbar.pack(side="right", fill="y")
        scroll_canvas.pack(side="left", fill="both", expand=True)

        outer = ttk.Frame(scroll_canvas, padding=(34, 24, 34, 22))
        win_id = scroll_canvas.create_window((0, 0), window=outer, anchor="nw")

        def _refresh_scrollregion(_e: Any = None) -> None:
            scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all"))

        outer.bind("<Configure>", _refresh_scrollregion)
        # Keep the inner frame as wide as the viewport so centred content
        # (header, canvas) stays centred rather than hugging the left edge.
        scroll_canvas.bind("<Configure>", lambda e: scroll_canvas.itemconfigure(win_id, width=e.width))
        # Mouse-wheel scrolling (Windows/macOS report delta in multiples of 120).
        scroll_canvas.bind_all(
            "<MouseWheel>", lambda e: scroll_canvas.yview_scroll(int(-e.delta / 120), "units")
        )
        self._scroll_canvas = scroll_canvas

        self._build_header(outer)
        self._build_observation(outer)
        self._build_wall_label(outer)
        self._build_configuration(outer)
        self._build_transport(outer)
        self._build_register(outer)
        self._build_marginalia(outer)

    def _build_wall_label(self, parent: ttk.Frame) -> None:
        """L1 — always-visible stage wall-label.

        Mirrors the web client's left-column "wall label" that always
        shows the active pipeline stage's title, citation, principle, and
        what the colours mean. The Tk version sits as a quiet block above
        CONFIGURATION; it auto-hides for non-pipeline rules so it doesn't
        confuse users running Conway or a single-stage rule.
        """
        body = self._section(parent, "I*", "STAGE", pad_top=4)
        self._wall_label_frame = body
        self._wall_title_var = tk.StringVar(value="")
        self._wall_principle_var = tk.StringVar(value="")
        self._wall_citation_var = tk.StringVar(value="")
        self._wall_legend_var = tk.StringVar(value="")
        # Title row — large display style + tiny "?" button (E3) that opens
        # the "How it works" panel: apparatus, methods, control, expect,
        # caveats. Until v4.0.6 these fields lived only in docs/science.md
        # and the user never saw them in the UI.
        title_row = ttk.Frame(body)
        title_row.pack(anchor="w", fill="x")
        ttk.Label(title_row, textvariable=self._wall_title_var, style="StageTitle.TLabel").pack(side="left")
        self._how_it_works_btn = ttk.Button(title_row, text="?", width=2, command=self._show_how_it_works)
        self._how_it_works_btn.pack(side="left", padx=(8, 0))
        # Citation row — small mono.
        ttk.Label(body, textvariable=self._wall_citation_var, style="Apparatus.TLabel").pack(
            anchor="w", pady=(2, 6)
        )
        # Principle (italic serif) — the one-liner that explains the stage.
        ttk.Label(
            body,
            textvariable=self._wall_principle_var,
            style="Caption.TLabel",
            wraplength=WINDOW_W - 100,
            justify="left",
        ).pack(anchor="w")
        # Legend — what the colours mean.
        ttk.Label(
            body,
            textvariable=self._wall_legend_var,
            style="Value.TLabel",
            wraplength=WINDOW_W - 100,
            justify="left",
        ).pack(anchor="w", pady=(6, 0))

    def _build_header(self, parent: ttk.Frame) -> None:
        # L12 — non-blocking toast strip. A thin horizontal label that sits
        # above the header; messages are shown via ``_toast(msg, kind=…)``
        # and auto-clear after 6 s. Keeps disruptive blocking modals out of
        # the export / snapshot UX. The widget is created hidden (height 0)
        # and pack-forgets itself when there's nothing to show.
        self._toast_frame = ttk.Frame(parent)
        self._toast_var = tk.StringVar(value="")
        self._toast_label = ttk.Label(
            self._toast_frame, textvariable=self._toast_var, style="Apparatus.TLabel"
        )
        self._toast_label.pack(side="left", padx=10, pady=4)
        self._toast_token: str | None = None
        # Don't pack the frame yet — only appear when there's a toast.

        header = ttk.Frame(parent)
        header.pack(fill="x")

        # Three columns: mascot │ centred title block │ spacer of equal width.
        mascot_col = ttk.Frame(header, width=80)
        mascot_col.pack(side="left", fill="y")
        mascot_col.pack_propagate(False)
        self.mascot = AmoebaMascot(mascot_col, size=64)
        self.mascot.pack(pady=(4, 0))

        spacer = ttk.Frame(header, width=80)
        spacer.pack(side="right", fill="y")

        title_col = ttk.Frame(header)
        title_col.pack(side="left", fill="both", expand=True)

        # Eyebrow row with the playback status dot tucked at the right.
        # L8 — pulsing brand mark: a single teal circle drawn on a 10×10
        # canvas that fades opacity (via stipple) at the playback cycle so
        # the user can see at a glance whether the sim is live.
        eyebrow_row = ttk.Frame(title_col)
        eyebrow_row.pack(anchor="center")
        ttk.Label(
            eyebrow_row,
            text="  ".join("PLATE I  ·  CELLAUTO  ·  MMXXVI"),
            style="Eyebrow.TLabel",
        ).pack(side="left")
        self._status_dot_canvas = tk.Canvas(
            eyebrow_row, width=10, height=10, background=BG, highlightthickness=0
        )
        self._status_dot_canvas.pack(side="left", padx=(8, 0))
        self._status_dot_id = self._status_dot_canvas.create_oval(1, 1, 9, 9, fill=HAIRLINE_HI, outline="")
        ttk.Label(title_col, text="cellauto", style="Title.TLabel").pack(anchor="center", pady=(4, 2))
        ttk.Label(
            title_col,
            text="observations on the coalescence of chemistry into life",
            style="Caption.TLabel",
        ).pack(anchor="center")
        self._hairline(header, color=HAIRLINE_HI).pack(fill="x", pady=(16, 0), anchor="center")

    def _build_observation(self, parent: ttk.Frame) -> None:
        body = self._section(parent, "I", "OBSERVATION", pad_top=18)

        # Frame with a 2-px teal rim — same vocabulary as the plate's specimens.
        # L9 — keep a reference so we can pulse the rim colour between
        # HAIRLINE (dim) and ACCENT (bright) at the playback cycle while
        # the sim is running.
        self._canvas_rim_frame = tk.Frame(body, background=HAIRLINE_HI, highlightthickness=0)
        self._canvas_rim_frame.pack(anchor="center", pady=(2, 0))
        self.canvas = tk.Canvas(
            self._canvas_rim_frame,
            width=CANVAS_SIZE,
            height=CANVAS_SIZE,
            background=BG,
            highlightthickness=0,
            borderwidth=2,
        )
        self.canvas.pack(padx=2, pady=2)
        # Click → per-protocell inspector for Stage 4 discs (direct rule or
        # the pipeline at stage 4); no-op otherwise.
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        # The live specimen label (stage name + colour legend) is drawn as a
        # text overlay *on* the canvas — see _sync_stage_caption. Drawing it on
        # the canvas costs zero layout space, which keeps the fixed-height
        # window from pushing the controls below the bottom edge.

    def _build_configuration(self, parent: ttk.Frame) -> None:
        body = self._section(parent, "II", "CONFIGURATION")

        row = ttk.Frame(body)
        row.pack(fill="x")

        ttk.Label(row, text="RULE", style="Apparatus.TLabel").pack(side="left", padx=(0, 8))
        self.rule_var = tk.StringVar(value="abiogenesis-pipeline")
        rule_picker = ttk.Combobox(
            row, textvariable=self.rule_var, values=list(REGISTRY), width=30, state="readonly"
        )
        rule_picker.pack(side="left", padx=(0, 22))
        rule_picker.bind("<<ComboboxSelected>>", lambda _e: self._on_rule_change())

        ttk.Label(row, text="GRID", style="Apparatus.TLabel").pack(side="left", padx=(0, 8))
        self.grid_size_var = tk.StringVar(value=str(DEFAULT_GRID))
        grid_picker = ttk.Combobox(
            row, textvariable=self.grid_size_var, values=["30", "60", "100", "150"], width=5, state="readonly"
        )
        grid_picker.pack(side="left", padx=(0, 22))
        grid_picker.bind("<<ComboboxSelected>>", lambda _e: self._on_rule_change())

        ttk.Button(row, text="RESEED", command=self._reseed).pack(side="left", padx=(0, 8))
        ttk.Button(row, text="RESTART", command=self._restart).pack(side="left", padx=(0, 8))
        ttk.Button(row, text="PROMOTE", command=self._promote_stage).pack(side="left")

        # Pipeline-only controls: direct stage navigation + auto-promote.
        # Packed/unpacked dynamically depending on whether the active rule is
        # the pipeline (see _sync_pipeline_row).
        self._pipeline_row = ttk.Frame(body)
        ttk.Label(self._pipeline_row, text="JUMP", style="Apparatus.TLabel").pack(side="left", padx=(0, 8))
        self._jump_var = tk.StringVar(value="0")
        # Combobox values are refilled per-rule by `_sync_pipeline_row` from
        # the active pipeline's `stage_classes` length, so 5-stage and
        # 10-stage pipelines both work without hardcoding.
        self._jump_picker = ttk.Combobox(
            self._pipeline_row,
            textvariable=self._jump_var,
            values=["0", "1", "2", "3", "4"],
            width=3,
            state="readonly",
        )
        self._jump_picker.pack(side="left", padx=(0, 18))
        self._jump_picker.bind("<<ComboboxSelected>>", lambda _e: self._on_jump_to_stage())
        self._auto_promote_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self._pipeline_row,
            text="AUTO-PROMOTE",
            variable=self._auto_promote_var,
            command=self._on_auto_promote_toggle,
        ).pack(side="left", padx=(0, 18))
        ttk.Label(self._pipeline_row, text="DUR", style="Apparatus.TLabel").pack(side="left", padx=(0, 6))
        self._stage_duration_var = tk.StringVar(value="60")
        ttk.Spinbox(
            self._pipeline_row,
            from_=10,
            to=500,
            increment=10,
            textvariable=self._stage_duration_var,
            width=5,
            command=self._on_stage_duration_change,
        ).pack(side="left")

        # Live scientific-parameter controls. Rebuilt whenever the active rule
        # (or pipeline stage) changes; see _rebuild_parameters. The dataclass
        # fields are read every step, so a slider change applies on the next
        # frame with no re-initialisation.
        self._param_frame = ttk.Frame(body)
        self._param_frame.pack(fill="x", pady=(12, 0))
        self._param_vars: dict[str, tuple[tk.DoubleVar, tk.StringVar, ParamSpec]] = {}
        self._preset_var = tk.StringVar(value="")

    def _sync_pipeline_row(self) -> None:
        """Show the JUMP / AUTO-PROMOTE / DUR controls for any pipeline rule
        (canonical or extended). The JUMP combobox values are refilled from
        the rule's own ``stage_classes`` so 5- and 10-stage pipelines both
        size correctly."""
        rule = self.engine.rule
        is_pipeline = hasattr(rule, "stage_classes") and hasattr(rule, "set_stage")
        if is_pipeline:
            if not self._pipeline_row.winfo_ismapped():
                self._pipeline_row.pack(fill="x", pady=(8, 0), before=self._param_frame)
            n = len(getattr(rule, "stage_classes", ()))
            self._jump_picker.configure(values=[str(i) for i in range(n)])
            stage = getattr(self.engine.state, "current_stage", 0)
            self._jump_var.set(str(int(stage)))
            self._auto_promote_var.set(bool(getattr(rule, "auto_promote", True)))
            self._stage_duration_var.set(str(int(getattr(rule, "stage_duration", 60))))
        else:
            if self._pipeline_row.winfo_ismapped():
                self._pipeline_row.pack_forget()

    def _on_jump_to_stage(self) -> None:
        try:
            n = int(self._jump_var.get())
        except ValueError:
            return
        rule = self.engine.rule
        if not hasattr(rule, "set_stage"):
            return
        rule.set_stage(self.engine.state, n)
        self._init_renderer()
        self._render()
        self._update_status()

    def _on_auto_promote_toggle(self) -> None:
        rule = self.engine.rule
        if hasattr(rule, "auto_promote"):
            rule.auto_promote = bool(self._auto_promote_var.get())

    def _on_stage_duration_change(self) -> None:
        try:
            d = int(self._stage_duration_var.get())
        except ValueError:
            return
        rule = self.engine.rule
        if hasattr(rule, "stage_duration"):
            rule.stage_duration = max(1, d)

    def _on_colorblind_toggle(self) -> None:
        """Toggle CVD-safe mode. Propagate to the active rule (or pipeline
        inner rule) so the next frame uses the alternative palette."""
        self._colorblind_safe = bool(self._colorblind_var.get())
        for target in (self.engine.rule, getattr(self.engine.state, "inner_rule", None)):
            if target is not None and hasattr(target, "colorblind_safe"):
                target.colorblind_safe = self._colorblind_safe
        self._render()
        self._update_status()

    def _toast(self, msg: str, kind: str = "info") -> None:
        """L12 — non-blocking toast. Show ``msg`` in the strip above the
        header for 6 seconds. ``kind`` chooses the colour ('info' = bone,
        'success' = bone with subtle teal, 'error' = warm brick).
        """
        if not msg:
            return
        # Colour by kind. Error and success use distinct foreground colours.
        colour = {
            "info": TEXT,
            "success": TOAST_OK,  # soft teal-bone
            "error": TOAST_ERR,  # warm brick — same family as the STOP button
        }.get(kind, TEXT)
        try:
            self._toast_label.configure(foreground=colour)
            self._toast_var.set(msg)
            self._toast_frame.pack(fill="x", side="top", before=self.winfo_children()[1])
        except (tk.TclError, IndexError):
            return
        # Cancel any pending fade and schedule a new one.
        if self._toast_token is not None:
            try:
                self.master_window.after_cancel(self._toast_token)
            except tk.TclError:
                pass
        self._toast_token = self.master_window.after(6000, self._clear_toast)

    def _clear_toast(self) -> None:
        self._toast_token = None
        try:
            self._toast_var.set("")
            self._toast_frame.pack_forget()
        except tk.TclError:
            pass

    def _on_sem_mode_toggle(self) -> None:
        """v4.0 — toggle between viridis and SEM rendering for field stages.

        Rebuilds the renderer for the active rule. Persists the choice so the
        preference survives restart. Discrete rules (Conway, Wolfram, Stage 0)
        keep their DiscreteRenderer regardless of this flag.
        """
        if not self._sem_available:
            self._sem_mode_var.set(False)
            self._toast(f"SEM mode unavailable: {self._sem_unavailable_reason}", kind="warn")
            return
        self._sem_mode = bool(self._sem_mode_var.get())
        self._persist_view_config()
        self._init_renderer()
        self._render()
        self._sync_stage_caption()

    def _on_sem_palette_change(self) -> None:
        self._sem_palette = self._sem_palette_var.get()
        if self._sem_palette not in (PALETTE_WARM_SEPIA, PALETTE_COOL_MONO):
            self._sem_palette = PALETTE_WARM_SEPIA
        self._persist_view_config()
        self._channel.set_palette(self._sem_palette)
        if isinstance(self._renderer, SemRenderer):
            self._renderer.set_palette(self._sem_palette)
            self._render()

    def _apply_sem_stage_label(self, renderer: SemRenderer) -> None:
        """Initial stage label for a freshly-built SemRenderer."""
        stage = getattr(self.engine.state, "current_stage", None)
        if stage is None:
            renderer.set_stage_label(self.engine.rule.name)
            return
        rule = self.engine.rule
        info = rule.stage_info_for(stage) if hasattr(rule, "stage_info_for") else stage_info(stage)
        renderer.set_stage_label(f"Stage {stage} — {info.title}")

    def _on_story_toggle(self) -> None:
        """v4.1 — toggle Channel B, the narrative 'Day in the Life' layer.

        The story layer is additive and reversible: enabling installs it as the
        SEM post-compositor; disabling removes it and re-renders the untouched
        SEM frame (Channel A is never altered). Persists across restart. It
        rides on the SEM micrograph, so it has no effect on discrete renderers.
        """
        self._story_enabled = bool(self._story_var.get())
        self._persist_view_config()
        self._sync_story_channel()
        if isinstance(self._renderer, SemRenderer):
            self._render()
        elif self._story_enabled:
            self._toast("Story layer rides on SEM mode — enable SEM mode to see it.", kind="info")

    def _on_render_scale_change(self) -> None:
        """v4.1 — set the live supersample factor (1/2/3×). The SEM frame is
        composed at factor×canvas then LANCZOS-downsampled for crisper output.
        Rebuilds the renderer so the new render_size takes effect."""
        scale = int(self._render_scale_var.get())
        if scale not in (1, 2, 3):
            scale = 1
        self._render_scale = scale
        self._persist_view_config()
        if isinstance(self._renderer, SemRenderer):
            self._renderer.render_size = scale * CANVAS_SIZE if scale > 1 else 0
            self._render()

    def _export_hires_png(self) -> None:
        """v4.1 — export a single composed frame at a chosen hi-res edge length
        (1080/1440/2160²). Only available in SEM mode; the export is composed
        through the same SEM + Channel-B path as the live canvas, just larger,
        so the story overlay (if on) exports crisp at full resolution."""
        if not isinstance(self._renderer, SemRenderer):
            self._toast("Hi-res PNG export needs SEM mode — enable it first.", kind="info")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png")],
            title="Export hi-res PNG",
            initialfile=f"{self.engine.rule.name}-seed{self.engine.seed}-hires.png",
        )
        if not path:
            return
        renderer = self._renderer
        rule = self.engine.rule
        base_rgb = rule.render_rgb(self.engine.state)
        # Resolve the desired edge from the menu's largest preset by default; we
        # offer the standard preset set and pick 1440² as a sensible middle.
        size = EXPORT_SIZES.get("1440²", 1440)
        try:
            export_hires_png(lambda s: renderer.compose_at(base_rgb, s), path, size)
        except Exception as exc:  # pragma: no cover — IO / PIL surface
            self._toast(f"Hi-res export failed: {exc}", kind="error")
            return
        # The export composed at `size`, leaving the renderer's cached pre-overlay
        # frame at export resolution; re-render so the live reanimate loop keeps
        # working at display resolution.
        self._render()
        self._toast(f"Hi-res PNG ({size}²) saved to {path}", kind="success")

    def _on_reduced_motion_toggle(self) -> None:
        """L6 — apply the reduced-motion preference.

        When ON: cap visible playback FPS at 10 Hz (the WCAG-suggested
        ceiling for users with vestibular or photosensitive disorders),
        freeze the title-block + canvas-rim pulse, and skip the
        chapter-card fade. The chapter card still appears but stays
        on-screen until dismissed with Escape (no auto-fade).
        """
        self._reduced_motion = bool(self._reduced_motion_var.get())
        # Force pulse to idle immediately so the user sees the change.
        self._set_pulse_phase(0.0)
        # Propagate to the SEM renderer (freezes the badge pulse).
        if isinstance(self._renderer, SemRenderer):
            self._renderer.set_reduced_motion(self._reduced_motion)
        # Propagate to Channel B (freezes the character's own animation clock).
        self._channel.set_reduced_motion(self._reduced_motion)
        # Cap any in-flight FPS slider down to 10 Hz if currently higher.
        try:
            fps_var = getattr(self, "_fps_var", None)
            if fps_var is not None and float(fps_var.get()) > 10:
                fps_var.set(10)
        except (tk.TclError, ValueError):
            pass

    def _reset_params(self) -> None:
        """Reset every slider on the active rule to its dataclass defaults."""
        target = self._param_target()
        if target is None:
            return
        defaults = type(target)()
        for spec in PARAM_SPECS.get(getattr(target, "name", ""), []):
            setattr(target, spec.attr, getattr(defaults, spec.attr))
        self._rebuild_parameters()
        self._update_status()

    def _param_target(self) -> Any:
        """The object whose attributes the sliders set: the inner stage rule
        for the pipeline, otherwise the rule itself."""
        state = getattr(self.engine, "state", None)
        inner = getattr(state, "inner_rule", None)
        return inner if inner is not None else self.engine.rule

    def _rebuild_parameters(self) -> None:
        for child in self._param_frame.winfo_children():
            child.destroy()
        self._param_vars = {}
        target = self._param_target()
        specs = PARAM_SPECS.get(getattr(target, "name", ""), [])
        if not specs:
            return
        header = ttk.Frame(self._param_frame)
        header.pack(fill="x", pady=(0, 4))
        ttk.Label(header, text="PARAMETERS", style="Section.TLabel").pack(side="left")
        ttk.Button(header, text="RESET", command=self._reset_params).pack(side="right")
        # L3 — Pearson regime preset chips (replaces the dropdown). All five
        # presets are visible at once as a row of toggle-button chips —
        # users see the full menu of Gray-Scott regimes without clicking
        # to expand.
        if getattr(target, "name", "") in PEARSON_PRESET_RULES:
            prow = ttk.Frame(self._param_frame)
            prow.pack(fill="x", pady=(0, 6))
            ttk.Label(prow, text="preset", style="Apparatus.TLabel", width=16).pack(side="left")
            chip_row = ttk.Frame(prow)
            chip_row.pack(side="left", fill="x", expand=True)
            self._preset_var.set("")
            self._preset_chip_buttons: dict[str, ttk.Button] = {}
            for name in GRAY_SCOTT_PRESETS:

                def _select(n: str = name) -> None:
                    self._preset_var.set(n)
                    self._on_preset_change()
                    self._refresh_preset_chips()

                btn = ttk.Button(chip_row, text=name, command=_select)
                btn.pack(side="left", padx=(0, 4))
                self._preset_chip_buttons[name] = btn
            self._refresh_preset_chips()
        for spec in specs:
            srow = ttk.Frame(self._param_frame)
            srow.pack(fill="x", pady=1)
            ttk.Label(srow, text=spec.label, style="Apparatus.TLabel", width=16).pack(side="left")
            value = self._effective_param_value(target, spec)
            var = tk.DoubleVar(value=float(value))
            readout = tk.StringVar(value=self._fmt_param(value, spec))
            # Register before creating the Scale: its command can fire during
            # construction, and _on_param_change looks the attr up here.
            self._param_vars[spec.attr] = (var, readout, spec)
            ttk.Scale(
                srow,
                from_=spec.lo,
                to=spec.hi,
                variable=var,
                length=300,
                command=lambda _v, s=spec: self._on_param_change(s),  # type: ignore[misc]
            ).pack(side="left", padx=(0, 8))
            ttk.Label(srow, textvariable=readout, style="Value.TLabel", width=7).pack(side="left")

    @staticmethod
    def _effective_param_value(target: Any, spec: ParamSpec) -> float:
        """Current value of a parameter, resolving Gray-Scott's F/k that
        default to None (the rule reads them from the named preset until the
        user overrides them)."""
        value = getattr(target, spec.attr, None)
        if value is None and spec.attr in ("F", "k") and hasattr(target, "preset"):
            f, k = GRAY_SCOTT_PRESETS.get(getattr(target, "preset", "spots"), GRAY_SCOTT_PRESETS["spots"])
            return f if spec.attr == "F" else k
        if value is None:
            return float(spec.lo)
        return float(value)

    @staticmethod
    def _fmt_param(value: float, spec: ParamSpec) -> str:
        return str(int(round(value))) if spec.integer else f"{float(value):.3f}"

    # L4 — debounce reinit-param slider drags. Without this, dragging a
    # structural slider (e.g. `n_species`, `seq_length`) triggers a full
    # init_state() rebuild on every Tk slider tick, which is both wasteful
    # and visually janky. The web client debounces at 250 ms for reinit
    # params and 60 ms for live params; we mirror that here.
    _PARAM_DEBOUNCE_MS_REINIT = 250
    _PARAM_DEBOUNCE_MS_LIVE = 60

    def _on_param_change(self, spec: ParamSpec) -> None:
        var, readout, _ = self._param_vars[spec.attr]
        value: float = var.get()
        if spec.integer:
            value = int(round(value))
        # Apply the value to the rule immediately (cheap attribute write)
        # and update the readout so the user sees the current number...
        setattr(self._param_target(), spec.attr, value)
        readout.set(self._fmt_param(value, spec))
        # ...but DEBOUNCE the expensive reinit / status refresh.
        delay = self._PARAM_DEBOUNCE_MS_REINIT if spec.reinit else self._PARAM_DEBOUNCE_MS_LIVE
        token = getattr(self, "_param_debounce_token", None)
        if token is not None:
            try:
                self.master_window.after_cancel(token)
            except tk.TclError:
                pass
        self._param_debounce_token = self.master_window.after(
            delay,
            lambda s=spec: self._apply_param_change(s),  # type: ignore[misc]
        )

    def _apply_param_change(self, spec: ParamSpec) -> None:
        """Fire the deferred work from ``_on_param_change`` — the reinit
        and status update — after the debounce window expires."""
        self._param_debounce_token = None  # type: ignore[assignment]
        if spec.reinit:
            self._reinit_param_target()
        self._update_status()

    def _reinit_param_target(self) -> None:
        """Re-initialise the active rule's state after a structural parameter
        change. For the pipeline we rebuild only the *inner* stage's state
        (keeping the pipeline context); otherwise we rebuild the engine's state.
        The rule's RNG is reseeded from ``engine.seed`` so the same parameters
        deterministically yield the same fresh state."""
        import random as _r

        target = self._param_target()
        state = self.engine.state
        if hasattr(state, "inner_rule") and state.inner_rule is target:
            if hasattr(target, "rng"):
                target.rng = _r.Random(self.engine.seed)
            state.inner_state = target.init_state(state.width, state.height)
        else:
            if hasattr(self.engine.rule, "rng"):
                self.engine.rule.rng = _r.Random(self.engine.seed)
            self.engine.state = self.engine.rule.init_state(self.engine.width, self.engine.height)
            self.engine.step_count = 0
            self._stats_history.clear()
        self._init_renderer()
        self._render()

    def _refresh_preset_chips(self) -> None:
        """L3 — highlight the active preset chip with the accent style; the
        rest stay in the default outline. ttk's button-state mechanism is
        too fiddly for a custom toggled look, so we swap the style instead.
        """
        chips = getattr(self, "_preset_chip_buttons", None)
        if not chips:
            return
        active = self._preset_var.get()
        for name, btn in chips.items():
            try:
                btn.configure(style="Primary.TButton" if name == active else "TButton")
            except tk.TclError:
                pass

    def _on_preset_change(self) -> None:
        name = self._preset_var.get()
        if name not in GRAY_SCOTT_PRESETS:
            return
        f, k = GRAY_SCOTT_PRESETS[name]
        target = self._param_target()
        target.F, target.k = f, k
        # Reflect the new F/k on their sliders.
        for attr, val in (("F", f), ("k", k)):
            if attr in self._param_vars:
                var, readout, spec = self._param_vars[attr]
                var.set(val)
                readout.set(self._fmt_param(val, spec))
        self._update_status()

    def _build_transport(self, parent: ttk.Frame) -> None:
        body = self._section(parent, "III", "TRANSPORT")

        row = ttk.Frame(body)
        row.pack(fill="x")

        self.step_button = ttk.Button(row, text="STEP", command=self._step_once)
        self.step_button.pack(side="left")
        self.play_button = ttk.Button(row, text="PLAY", style="Primary.TButton", command=self._play)
        self.play_button.pack(side="left", padx=(8, 0))
        self.stop_button = ttk.Button(
            row, text="STOP", style="Danger.TButton", command=self._stop, state="disabled"
        )
        self.stop_button.pack(side="left", padx=(8, 0))

        ttk.Label(row, text="FPS", style="Apparatus.TLabel").pack(side="left", padx=(22, 8))
        self.fps_var = tk.DoubleVar(value=DEFAULT_FPS)
        self.fps_value_var = tk.StringVar(value=f"{int(DEFAULT_FPS):>2d}")
        ttk.Scale(
            row,
            from_=1,
            to=60,
            variable=self.fps_var,
            orient="horizontal",
            length=170,
            command=lambda v: self.fps_value_var.set(f"{int(float(v)):>2d}"),
        ).pack(side="left")
        ttk.Label(row, textvariable=self.fps_value_var, style="Value.TLabel", width=3).pack(
            side="left", padx=(8, 0)
        )

        ttk.Button(row, text="TUTORIAL", command=self._tutorial_next).pack(side="right")
        self.record_button = ttk.Button(
            row, text="●  RECORD  GIF", style="Record.TButton", command=self._toggle_gif_record
        )
        self.record_button.pack(side="right", padx=(0, 8))

        # Timeline scrubber. Each step pushes a serialized state into a bounded
        # ring; the user can drag back to inspect any captured frame and resume
        # from there (stepping after a scrub truncates the future — timeline
        # branches rather than overwriting).
        srow = ttk.Frame(body)
        srow.pack(fill="x", pady=(8, 0))
        ttk.Label(srow, text="SCRUB", style="Apparatus.TLabel").pack(side="left", padx=(0, 8))
        self._scrub_var = tk.DoubleVar(value=0)
        self._scrub = ttk.Scale(
            srow,
            from_=0,
            to=0,
            variable=self._scrub_var,
            orient="horizontal",
            length=350,
            command=lambda _v: self._on_scrub(),
        )
        self._scrub.pack(side="left", padx=(0, 8))
        self._scrub_label_var = tk.StringVar(value="0 / 0")
        ttk.Label(srow, textvariable=self._scrub_label_var, style="Value.TLabel", width=11).pack(side="left")

    def _build_register(self, parent: ttk.Frame) -> None:
        body = self._section(parent, "IV", "REGISTER")

        self._status_rule_var = tk.StringVar(value="")
        self._status_seed_var = tk.StringVar(value="")
        self._status_step_var = tk.StringVar(value="")
        self._status_fps_var = tk.StringVar(value="")
        self._status_pop_var = tk.StringVar(value="")

        grid = ttk.Frame(body)
        grid.pack(fill="x")

        def cell(
            parent: ttk.Frame, label: str, var: tk.StringVar, width: int, col: int, padx: int = 22
        ) -> None:
            cont = ttk.Frame(parent)
            cont.grid(row=0, column=col, sticky="w", padx=(0, padx))
            ttk.Label(cont, text=label, style="Apparatus.TLabel").pack(anchor="w")
            ttk.Label(cont, textvariable=var, style="Value.TLabel", width=width, anchor="w").pack(
                anchor="w", pady=(2, 0)
            )

        cell(grid, "RULE", self._status_rule_var, 24, 0)
        cell(grid, "SEED", self._status_seed_var, 12, 1)
        cell(grid, "STEP", self._status_step_var, 8, 2)
        cell(grid, "FPS", self._status_fps_var, 6, 3, padx=0)

        ttk.Label(body, text="POPULATION", style="Apparatus.TLabel").pack(anchor="w", pady=(10, 2))
        # L7 — population stats as wrap-friendly chips. Stage II's vent
        # readout has 10+ stats and clipped on one line; rendering each
        # key:value pair as its own small label inside a flow container
        # lets them wrap naturally and stay readable.
        self._status_pop_chips = ttk.Frame(body)
        self._status_pop_chips.pack(anchor="w", fill="x")

    def _build_marginalia(self, parent: ttk.Frame) -> None:
        body = self._section(parent, "V", "MARGINALIA", pad_bottom=0)
        self.tutorial_var = tk.StringVar(value=self._tutorial_placeholder())
        ttk.Label(
            body,
            textvariable=self.tutorial_var,
            style="Caption.TLabel",
            wraplength=WINDOW_W - 80,
            justify="left",
            anchor="w",
        ).pack(anchor="w", fill="x")

    def _tutorial_placeholder(self) -> str:
        return "press TUTORIAL to advance through this rule's commentary, one citation at a time."

    # ── Menu ────────────────────────────────────────────────────────────────

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.master_window, tearoff=0, bd=0)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="New", command=self._reseed, accelerator="Ctrl+N")
        filemenu.add_command(label="Open snapshot…", command=self._open_snapshot, accelerator="Ctrl+O")
        filemenu.add_command(label="Save snapshot…", command=self._save_snapshot, accelerator="Ctrl+S")
        filemenu.add_separator()
        filemenu.add_command(label="Export frame as PNG…", command=self._export_png)
        filemenu.add_command(label="Export hi-res PNG…", command=self._export_hires_png)
        filemenu.add_command(label="Export GIF…", command=self._export_gif)
        filemenu.add_command(label="Export stats as CSV…", command=self._export_csv)
        filemenu.add_separator()
        filemenu.add_command(label="Quit", command=self._quit, accelerator="Ctrl+Q")
        menubar.add_cascade(label="File", menu=filemenu)

        gallerymenu = tk.Menu(menubar, tearoff=0)
        for key, label in (
            ("stage0", "Stage 0 — Primordial soup"),
            ("stage1", "Stage 1 — Reaction-diffusion"),
            ("stage2", "Stage 2 — Autocatalytic sets"),
            ("stage3", "Stage 3 — Vesicle formation"),
            ("stage4", "Stage 4 — Protocell selection"),
            ("stage7", "Stage VIII — Genetic code"),
            ("stage11", "Stage XII — LUCA distillation"),
            ("poster", "Chemistry into life — full arc"),
        ):
            gallerymenu.add_command(label=label, command=lambda k=key: self._open_gallery(k))  # type: ignore[misc]
        gallerymenu.add_separator()
        gallerymenu.add_command(
            label="Hero — Gray-Scott close-up", command=lambda: self._open_gallery("hero")
        )
        gallerymenu.add_command(label="Pipeline strip", command=lambda: self._open_gallery("pipeline"))
        gallerymenu.add_command(
            label="Prima Materia — Plate XII", command=lambda: self._open_gallery("prima")
        )
        gallerymenu.add_command(
            label="Genesis — twelve-stage arc",
            command=lambda: self._open_gallery("genesis"),
        )
        gallerymenu.add_command(
            label="Twelve Tableaux — pipeline plate",
            command=lambda: self._open_gallery("tableaux"),
        )
        gallerymenu.add_separator()
        gallerymenu.add_command(label="Reaction network (Stage 2 RAF)…", command=self._open_network_view)
        menubar.add_cascade(label="Gallery", menu=gallerymenu)

        viewmenu = tk.Menu(menubar, tearoff=0)
        for label, scale in (
            ("Small text", 0.85),
            ("Default text", 1.0),
            ("Large text", 1.20),
            ("Extra-large text", 1.40),
        ):
            viewmenu.add_command(label=label, command=lambda s=scale: self._apply_font_scale(s))  # type: ignore[misc]
        viewmenu.add_separator()
        self._colorblind_var = tk.BooleanVar(value=False)
        viewmenu.add_checkbutton(
            label="Colour-blind safe palette",
            variable=self._colorblind_var,
            command=self._on_colorblind_toggle,
        )
        # L6 — reduced-motion preference. Mirrors the browser's
        # prefers-reduced-motion media query: caps sim FPS at 10 Hz,
        # freezes the title-block pulse + canvas rim pulse, and skips
        # the chapter-card fade animation. Persists in-process only.
        self._reduced_motion_var = tk.BooleanVar(value=False)
        viewmenu.add_checkbutton(
            label="Reduced motion (cap fps, freeze pulses)",
            variable=self._reduced_motion_var,
            command=self._on_reduced_motion_toggle,
        )
        # v4.0 — SEM-grade rendering toggle + palette picker (S3).
        viewmenu.add_separator()
        self._sem_mode_var = tk.BooleanVar(value=self._sem_mode)
        viewmenu.add_checkbutton(
            label="SEM mode (depth-shaded micrograph)",
            variable=self._sem_mode_var,
            command=self._on_sem_mode_toggle,
            state=("normal" if self._sem_available else "disabled"),
        )
        self._sem_palette_var = tk.StringVar(value=self._sem_palette)
        sempalmenu = tk.Menu(viewmenu, tearoff=0)
        sempalmenu.add_radiobutton(
            label="Warm sepia",
            value=PALETTE_WARM_SEPIA,
            variable=self._sem_palette_var,
            command=self._on_sem_palette_change,
        )
        sempalmenu.add_radiobutton(
            label="Cool mono",
            value=PALETTE_COOL_MONO,
            variable=self._sem_palette_var,
            command=self._on_sem_palette_change,
        )
        viewmenu.add_cascade(label="SEM palette", menu=sempalmenu)
        # v4.1 — Channel B narrative "Day in the Life" layer + hi-res render
        # scale. The story layer is an additive post-compositor over the SEM
        # frame; render scale supersamples the live canvas for crisper output.
        viewmenu.add_separator()
        self._story_var = tk.BooleanVar(value=self._story_enabled)
        viewmenu.add_checkbutton(
            label="Story · Day in the Life (narrative layer)",
            variable=self._story_var,
            command=self._on_story_toggle,
            state=("normal" if self._sem_available else "disabled"),
        )
        self._render_scale_var = tk.IntVar(value=self._render_scale)
        scalemenu = tk.Menu(viewmenu, tearoff=0)
        for slabel, factor in (("1× (fast)", 1), ("2× (crisp)", 2), ("3× (max)", 3)):
            scalemenu.add_radiobutton(
                label=slabel,
                value=factor,
                variable=self._render_scale_var,
                command=self._on_render_scale_change,
            )
        viewmenu.add_cascade(label="Render scale (supersample)", menu=scalemenu)
        menubar.add_cascade(label="View", menu=viewmenu)

        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="How does this stage work?…", command=self._show_how_it_works)
        helpmenu.add_separator()
        helpmenu.add_command(label="Start tutorial", command=self._tutorial_start)
        helpmenu.add_command(label="Tutorial — all steps…", command=self._tutorial_all_steps)
        helpmenu.add_command(label="Keyboard shortcuts…", command=self._show_keyboard_help)
        helpmenu.add_command(label="About", command=self._about)
        menubar.add_cascade(label="Help", menu=helpmenu)

        self.master_window.config(menu=menubar)
        self.master_window.bind_all("<Control-n>", lambda _e: self._reseed())
        self.master_window.bind_all("<Control-o>", lambda _e: self._open_snapshot())
        self.master_window.bind_all("<Control-s>", lambda _e: self._save_snapshot())
        self.master_window.bind_all("<Control-q>", lambda _e: self._quit())
        # Single-key transport/navigation shortcuts (guarded against text-entry
        # focus so typing in a Spinbox/Combobox isn't hijacked).
        for keysym, handler in (
            ("<space>", self._key_play_pause),
            ("<Right>", self._key_step),
            ("<r>", self._key_restart),
            ("<R>", self._key_restart),
            ("<p>", self._key_promote),
            ("<P>", self._key_promote),
            ("<bracketleft>", self._key_prev_stage),
            ("<bracketright>", self._key_next_stage),
            ("<Escape>", self._key_dismiss_card),
        ):
            self.master_window.bind_all(keysym, handler)
        self.master_window.protocol("WM_DELETE_WINDOW", self._quit)

    # ── Engine control ──────────────────────────────────────────────────────

    def _on_rule_change(self) -> None:
        self._stop()
        self._new_engine(rule_name=self.rule_var.get(), grid_size=int(self.grid_size_var.get()), seed=None)
        self.tutorial_var.set(self._tutorial_placeholder())
        self._tutorial_index = -1

    def _reseed(self) -> None:
        self._stop()
        self._new_engine(rule_name=self.rule_var.get(), grid_size=int(self.grid_size_var.get()), seed=None)

    def _restart(self) -> None:
        """Rewind to step 0 *without* rerolling the seed or re-instantiating the
        rule, so any parameter changes the user made are preserved while the
        state itself is reinitialised."""
        import random as _r

        self._stop()
        rule = self.engine.rule
        if hasattr(rule, "rng"):
            rule.rng = _r.Random(self.engine.seed)
        if hasattr(rule, "_step_count"):
            rule._step_count = 0
        self.engine.state = rule.init_state(self.engine.width, self.engine.height)
        self.engine.step_count = 0
        self._init_renderer()
        self._render()
        self._update_status()
        self._rebuild_parameters()
        self._sync_pipeline_row()
        self._stats_history.clear()
        self._state_history.clear()
        self._record_state_snapshot()  # seed step 0 so the scrubber has a baseline
        self._clear_chapter_card()

    # ── Keyboard shortcuts ──────────────────────────────────────────────────

    _TEXT_ENTRY_CLASSES = frozenset(
        {
            "Entry",
            "TEntry",
            "Spinbox",
            "TSpinbox",
            "Combobox",
            "TCombobox",
            "Text",
        }
    )

    def _ignore_if_text_entry(self, event: tk.Event) -> bool:
        widget = getattr(event, "widget", None)
        try:
            cls = widget.winfo_class() if widget else ""
        except (AttributeError, tk.TclError):
            cls = ""
        return cls in self._TEXT_ENTRY_CLASSES

    def _key_play_pause(self, event: tk.Event) -> None:
        if self._ignore_if_text_entry(event):
            return
        if self.running:
            self._stop()
        else:
            self._play()

    def _key_step(self, event: tk.Event) -> None:
        if self._ignore_if_text_entry(event):
            return
        if not self.running:
            self._step_once()

    def _key_restart(self, event: tk.Event) -> None:
        if self._ignore_if_text_entry(event):
            return
        self._restart()

    def _key_promote(self, event: tk.Event) -> None:
        if self._ignore_if_text_entry(event):
            return
        self._promote_stage()

    def _key_prev_stage(self, event: tk.Event) -> None:
        if self._ignore_if_text_entry(event):
            return
        self._step_stage(-1)

    def _key_next_stage(self, event: tk.Event) -> None:
        if self._ignore_if_text_entry(event):
            return
        self._step_stage(+1)

    def _key_dismiss_card(self, event: tk.Event) -> None:
        """Escape dismisses an in-progress chapter-card overlay immediately."""
        self._clear_chapter_card()

    def _step_stage(self, delta: int) -> None:
        rule = self.engine.rule
        if not (hasattr(rule, "set_stage") and hasattr(self.engine.state, "current_stage")):
            return
        rule.set_stage(self.engine.state, self.engine.state.current_stage + delta)
        self._init_renderer()
        self._render()
        self._update_status()

    def _show_how_it_works(self) -> None:
        """v4.0.6 E3 — surface the apparatus / methods / control / expect /
        caveats prose that already lives in StageInfo (sourced from
        docs/science.md). Pops a Toplevel dialog so it doesn't compete for
        space in the fixed-window main UI.

        For the canonical 5-stage pipeline these fields are fully populated.
        For single-stage rules or for the legacy 12-stage extended pipeline
        whose StageInfo entries predate v4.0.6, the panel still opens but
        shows "(not yet documented for this stage — see docs/science.md)"
        per missing field instead of crashing.
        """
        stage = getattr(self.engine.state, "current_stage", None)
        rule = self.engine.rule
        info = None
        if stage is not None and hasattr(rule, "stage_info_for"):
            info = rule.stage_info_for(stage)
        elif stage is not None:
            from cellauto.rules.abiogenesis.pipeline import stage_info as _si

            info = _si(stage)
        if info is None:
            self._toast(
                "How-it-works is documented per pipeline stage. Switch to abiogenesis-pipeline to see it.",
                kind="info",
            )
            return

        dlg = tk.Toplevel(self.master_window)
        dlg.title(f"How it works — Stage {info.index} · {info.title}")
        dlg.configure(background=BG)
        dlg.geometry("800x680")
        try:
            dlg.transient(self.master_window)
        except tk.TclError:
            pass

        outer = ttk.Frame(dlg, padding=18)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text=f"STAGE {info.index} · {info.title}", style="Title.TLabel").pack(anchor="w")
        ttk.Label(outer, text=info.citation, style="Apparatus.TLabel").pack(anchor="w", pady=(2, 12))

        # v4.0.7 E1/E2 — embed the apparatus diagram side-by-side with the
        # matching control-experiment diagram. Both are procedural PIL renders
        # (Miller-Urey flask, Gray-Scott reactor, RAF vessel, etc.) keyed on the
        # effective rule name, with index fallback. Falls back gracefully when
        # the stage is outside the canonical set.
        try:
            from cellauto.diagrams import render_apparatus, render_control

            inner = getattr(self.engine.state, "inner_rule", None)
            rule_name = getattr(inner, "name", None) or getattr(self.engine.rule, "name", None)
            # Render at the diagrams' native design resolution (640×320), where
            # the typeset labels fit without clipping, then downscale the IMAGE
            # into the embed box (see _embed_diagram). Rendering directly at the
            # smaller embed width clipped fixed-position text — the diagrams
            # don't reflow — so we supersample-and-shrink instead.
            _NW, _NH = 640, 320
            exp_img = render_apparatus(info.index, width=_NW, height=_NH, rule_name=rule_name)
            ctrl_img = render_control(info.index, width=_NW, height=_NH, rule_name=rule_name)
        except Exception:
            exp_img = ctrl_img = None

        # Embed box for each diagram (the 2:1 native render is downscaled to fit
        # this, preserving aspect → 360×180). Two side-by-side fit the dialog.
        _EMB = (360, 180)

        def _embed_diagram(parent: ttk.Frame, pil_img: object, attr: str, caption: str) -> None:
            if pil_img is None:
                return
            from PIL import Image as _PILImage

            col = ttk.Frame(parent)
            col.pack(side="left", padx=(0, 10))
            ttk.Label(col, text=caption, style="Eyebrow.TLabel").pack(anchor="w")
            img = pil_img.convert("RGB")  # type: ignore[attr-defined]
            img.thumbnail(_EMB, _PILImage.Resampling.LANCZOS)
            w_d, h_d = img.size
            ppm_header = f"P6\n{w_d} {h_d}\n255\n".encode("ascii")
            body_bytes = img.tobytes()
            photo = tk.PhotoImage(width=w_d, height=h_d, data=ppm_header + body_bytes, format="PPM")
            # Keep a ref on the dialog so Tk doesn't GC the image.
            setattr(dlg, attr, photo)
            tk.Label(col, image=photo, background=BG, borderwidth=0).pack(anchor="w")

        if exp_img is not None or ctrl_img is not None:
            ab_row = ttk.Frame(outer)
            ab_row.pack(anchor="w", pady=(0, 12))
            _embed_diagram(ab_row, exp_img, "_apparatus_photo", "EXPERIMENT")
            _embed_diagram(ab_row, ctrl_img, "_control_photo", "CONTROL")

        # Scrollable body so long methods/caveats don't get clipped.
        canvas = tk.Canvas(outer, background=BG, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        body = ttk.Frame(canvas)
        body.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=body, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        sections = (
            ("APPARATUS", "what physical setup we're modelling", info.apparatus),
            ("METHODS", "how the engine step maps to the experiment", info.methods),
            ("CONTROL", "what the null / control experiment looks like", info.control),
            ("EXPECT TO SEE", "the visual signature of success / failure", info.expect),
            ("HONEST LIMITATIONS", "what this ISN'T", info.caveats),
            ("CONSUMES FROM PREVIOUS STAGE", "", info.consumes),
            ("PRODUCES FOR NEXT STAGE", "", info.produces),
        )
        missing = "(not yet documented for this stage — see docs/science.md)"
        for header, subhead, prose in sections:
            ttk.Label(body, text=header, style="Section.TLabel").pack(anchor="w", pady=(10, 0))
            if subhead:
                ttk.Label(body, text=subhead, style="Eyebrow.TLabel").pack(anchor="w")
            ttk.Label(
                body,
                text=prose or missing,
                style="Caption.TLabel",
                wraplength=640,
                justify="left",
            ).pack(anchor="w", pady=(4, 0))

        ttk.Button(outer, text="CLOSE", command=dlg.destroy).pack(pady=(16, 0))

    def _show_keyboard_help(self) -> None:
        dlg = tk.Toplevel(self.master_window)
        dlg.title("Keyboard shortcuts")
        dlg.configure(background=BG)
        dlg.transient(self.master_window)
        body = ttk.Frame(dlg, padding=(22, 18))
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="KEYBOARD  SHORTCUTS", style="Eyebrow.TLabel").pack(anchor="w")
        for key, what in (
            ("Space", "Play / Pause"),
            ("→  (Right arrow)", "Single step (when paused)"),
            ("R", "Restart to step 0"),
            ("P", "Promote stage (forward)"),
            ("[  /  ]", "Pipeline stage: previous / next"),
            ("Ctrl+N", "New run (reseed)"),
            ("Ctrl+O", "Open snapshot"),
            ("Ctrl+S", "Save snapshot"),
            ("Ctrl+Q", "Quit"),
        ):
            r = ttk.Frame(body)
            r.pack(fill="x", pady=(6, 0))
            ttk.Label(r, text=key, style="Value.TLabel", width=16).pack(side="left")
            ttk.Label(r, text=what, style="Apparatus.TLabel").pack(side="left")
        ttk.Label(
            body,
            style="Caption.TLabel",
            wraplength=420,
            justify="left",
            text="Shortcuts are suppressed while a Spinbox or Combobox has focus, so editing slider values doesn't trigger transport actions.",
        ).pack(anchor="w", pady=(14, 0))

    def _promote_stage(self) -> None:
        rule = self.engine.rule
        if hasattr(rule, "promote") and hasattr(self.engine.state, "current_stage"):
            rule.promote(self.engine.state)
            self._init_renderer()
            self._render()
            self._update_status()

    def _step_once(self) -> None:
        self.engine.step()
        expected_kind = getattr(self.engine.rule, "renderer_kind", "discrete")
        current_kind = "field" if isinstance(self._renderer, (FieldRenderer, SemRenderer)) else "discrete"
        if expected_kind != current_kind:
            self._init_renderer()
        self._render()
        self._update_status()
        self._record_stats_sample()
        self._record_state_snapshot()
        self._maybe_capture_frame()

    def _record_stats_sample(self) -> None:
        """Append the current population dict to the time-series buffer."""
        sample = {"step": int(self.engine.step_count), **dict(self.engine.population())}
        self._stats_history.append(sample)
        if len(self._stats_history) > self._stats_history_cap:
            del self._stats_history[: len(self._stats_history) - self._stats_history_cap]

    def _record_state_snapshot(self) -> None:
        """Push a serialized snapshot of the engine state into the scrub ring.
        If we are downstream of a scrubbed-back position (the current step is
        earlier than the buffer's tail), the future is truncated first so a new
        step after a scrub creates a fresh timeline branch."""
        if self._scrubbing:
            return
        step = int(self.engine.step_count)
        # Drop any "future" beyond this step that's left over from a scrub-back.
        while self._state_history and self._state_history[-1]["step"] >= step:
            self._state_history.pop()
        try:
            snap = self.engine.rule.serialize_state(self.engine.state)
        except Exception:  # noqa: BLE001
            return
        self._state_history.append({"step": step, "state": snap})
        if len(self._state_history) > self._state_history_cap:
            del self._state_history[: len(self._state_history) - self._state_history_cap]
        self._sync_scrub_widget(active=len(self._state_history) - 1)

    def _sync_scrub_widget(self, active: int | None = None) -> None:
        """Keep the SCRUB Scale range and label aligned with the ring buffer."""
        n = len(self._state_history)
        hi = max(n - 1, 0)
        self._scrub.configure(to=hi)
        if active is None:
            active = int(self._scrub_var.get())
        active = max(0, min(active, hi))
        # Set the var WITHOUT triggering the scrub callback.
        self._scrubbing = True
        try:
            self._scrub_var.set(active)
        finally:
            self._scrubbing = False
        if n:
            step = self._state_history[active]["step"]
            tail = self._state_history[-1]["step"]
            self._scrub_label_var.set(f"{step} / {tail}")
        else:
            self._scrub_label_var.set("0 / 0")

    def _on_scrub(self) -> None:
        """Restore engine state to the buffer entry the user dragged to.
        ``_scrubbing`` guards against re-entrance from programmatic Scale
        updates."""
        if self._scrubbing or not self._state_history:
            return
        self._scrubbing = True
        try:
            self._stop()
            idx = max(0, min(int(self._scrub_var.get()), len(self._state_history) - 1))
            entry = self._state_history[idx]
            try:
                self.engine.state = self.engine.rule.deserialize_state(entry["state"])
            except Exception:  # noqa: BLE001
                return
            self.engine.step_count = entry["step"]
            self._init_renderer()
            self._render()
            self._update_status()
            tail = self._state_history[-1]["step"]
            self._scrub_label_var.set(f"{entry['step']} / {tail}")
        finally:
            self._scrubbing = False

    def _play(self) -> None:
        if self.running:
            return
        self.running = True
        self.play_button.configure(state="disabled")
        self.step_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        if hasattr(self, "mascot"):
            self.mascot.set_happy(True)
        if isinstance(self._renderer, SemRenderer):
            self._renderer.set_running(True)
        self._loop()

    def _stop(self) -> None:
        self.running = False
        self.play_button.configure(state="normal")
        self.step_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        if hasattr(self, "mascot"):
            self.mascot.set_happy(False)
        if isinstance(self._renderer, SemRenderer):
            self._renderer.set_running(False)

    def _loop(self) -> None:
        if not self.running:
            return
        # L5 — batch stepping at high FPS. Tk's `after()` minimum granularity
        # (~16 ms ≈ 60 Hz) and the renderer cost cap visible playback at
        # ~30 Hz on most hardware. Above that, we batch multiple
        # engine.step() calls per tick and render once at the end — the
        # user sees a smooth high-throughput stream instead of clamped 30 Hz.
        # Reduced-motion mode caps to 10 Hz and disables batching.
        target_fps = max(float(self.fps_var.get()), 1.0)
        if self._reduced_motion:
            target_fps = min(target_fps, 10.0)
            steps_per_tick = 1
            delay_ms = max(int(1000 / target_fps), 16)
        elif target_fps > 30:
            # Batch: do enough steps per 16-ms tick to hit the target rate.
            delay_ms = 16
            steps_per_tick = max(1, int(round(target_fps / 60)))  # 60 Hz tick base
        else:
            steps_per_tick = 1
            delay_ms = max(int(1000 / target_fps), 16)
        for _ in range(steps_per_tick - 1):
            # Step without rendering for the in-between steps — render
            # once at the end via `_step_once` for the final pixel update.
            try:
                self.engine.step()
                self._record_stats_sample()
            except Exception:  # pragma: no cover — defensive
                break
        self._step_once()
        self.canvas.after(delay_ms, self._loop)

    def _animate(self) -> None:
        """Continuous ~20 fps tick so the amoeba colony breathes/blinks even
        while the simulation is paused. Independent of the sim step loop.

        The chapter-card fade timer ticks FIRST (and unconditionally), so a
        transient TclError inside ``renderer.animate`` can't leave a card
        pinned to the canvas forever."""
        self._anim_frame += 1
        if self._chapter_card_ticks_left > 0:
            self._chapter_card_ticks_left -= 1
            if self._chapter_card_ticks_left == 0:
                try:
                    self.canvas.delete("chapter_card")
                except tk.TclError:
                    pass
        renderer = self._renderer
        if isinstance(renderer, DiscreteRenderer) and renderer.animated:
            try:
                renderer.animate(self._anim_frame)
            except tk.TclError:
                pass  # don't return — we still need to reschedule the next tick
        # v4.1 — Channel B runs on its OWN ~20 Hz clock, independent of the sim
        # step loop: advance it and cheaply re-blit the cached SEM frame so the
        # protagonist breathes/types even while the simulation is paused.
        if self._story_enabled and not self._reduced_motion and isinstance(renderer, SemRenderer):
            self._channel.tick(0.05)
            try:
                renderer.reanimate_overlay()
            except tk.TclError:
                pass
        # L8 + L9 — drive both playback pulses from this same tick.
        self._tick_playback_pulse()
        try:
            self.master_window.after(50, self._animate)
        except tk.TclError:
            return

    def _tick_playback_pulse(self) -> None:
        """L8 + L9 — pulse the title-block status dot + canvas rim while the
        sim is running. When paused (or when reduced motion is on) the dot
        stays dim and the rim sits at its idle teal colour.

        The pulse is driven by a triangular wave over a 44-frame cycle:
        bright at the peak, dim at the trough. We pick discrete colours
        rather than alpha-blending because Tk Canvas items can't carry
        true alpha — but three stepped shades read as a pulse just fine.
        """
        # Reduced motion → freeze both pulses at idle.
        if self._reduced_motion or not getattr(self, "running", False):
            self._set_pulse_phase(0.0)
            return
        cycle = max(self._playback_cycle, 1)
        # Triangle wave in [0, 1]: 0 at the start of each cycle, 1 at the
        # midpoint, back to 0 at the end. cos-based for a smoother feel.
        import math

        t = (self._anim_frame % cycle) / cycle
        phase = 0.5 - 0.5 * math.cos(2 * math.pi * t)  # [0, 1]
        self._set_pulse_phase(phase)

    def _set_pulse_phase(self, phase: float) -> None:
        """Apply a [0, 1] pulse phase to the status dot and canvas rim.

        ``HAIRLINE_HI`` (#39d4c8) is the bright accent teal — the existing
        canvas-rim colour. ``HAIRLINE`` (#1f4f4c) is the dim hairline.

        Idle (paused / reduced motion): dot is dim, rim is at its bright
        accent (preserving the existing always-on rim aesthetic).
        Playing: dot pulses dim → mid → bright → mid → dim; rim does
        the inverse pulse around the bright pole so the playback signal
        is subtle on the canvas (rim was already a focal element) but
        unmistakable on the dot.
        """
        # Phase 0 = idle pole, phase 1 = bright pole.
        if phase < 0.34:
            dot_color = HAIRLINE  # dim
            rim_color = HAIRLINE_HI  # bright (idle preserves the existing look)
        elif phase < 0.67:
            dot_color = TEAL_MID  # mid teal
            rim_color = TEAL_MID
        else:
            dot_color = HAIRLINE_HI  # bright
            rim_color = HAIRLINE_HI  # bright
        if self._status_dot_canvas is not None and self._status_dot_id is not None:
            try:
                self._status_dot_canvas.itemconfigure(self._status_dot_id, fill=dot_color)
            except tk.TclError:
                pass
        rim = getattr(self, "_canvas_rim_frame", None)
        if rim is not None:
            try:
                rim.configure(background=rim_color)
            except tk.TclError:
                pass

    def _clear_chapter_card(self) -> None:
        """Hide any in-progress chapter card immediately (reset the fade timer
        and remove the canvas items). Called on RESEED / RESTART / new engine
        and on Escape so the old chapter's title doesn't bleed into the next."""
        self._chapter_card_ticks_left = 0
        try:
            self.canvas.delete("chapter_card")
        except tk.TclError:
            pass

    def _show_chapter_card(self, stage: int, info: Any) -> None:
        """Display a brief title/principle overlay on the canvas when a new
        stage begins. Fades automatically via the `_animate` countdown.

        v4.0.6 E4 — chapter card now carries the connected-narrative line
        when StageInfo has `consumes` / `produces` populated, so entering
        Stage III tells you what Stage II handed off and what III hands
        forward. Falls back to principle-only for stages where the
        connective tissue isn't populated yet.
        """
        try:
            self.canvas.delete("chapter_card")
        except tk.TclError:
            return
        cx = CANVAS_SIZE // 2
        cy = CANVAS_SIZE // 2
        # E4 — taller card when the narrative line is present so prose
        # doesn't compete with the citation footer.
        narrative = ""
        consumes = getattr(info, "consumes", "")
        produces = getattr(info, "produces", "")
        if consumes and produces:
            narrative = f"From last stage: {consumes}  →  Now: {produces}"
        elif produces:
            narrative = f"This stage produces: {produces}"
        elif consumes:
            narrative = f"From last stage: {consumes}"
        w, h = (520, 220) if narrative else (460, 170)
        x0, y0 = cx - w // 2, cy - h // 2
        x1, y1 = cx + w // 2, cy + h // 2
        # Dimmed plate so the card reads on top of any field background.
        self.canvas.create_rectangle(
            x0, y0, x1, y1, fill="#0a0e16", outline=HAIRLINE_HI, width=2, tags="chapter_card"
        )
        self.canvas.create_text(
            cx,
            y0 + 22,
            anchor="n",
            fill=TEXT_DIM,
            font=self._font_eyebrow,
            text=f"CHAPTER  {stage}",
            tags="chapter_card",
        )
        self.canvas.create_text(
            cx,
            y0 + 52,
            anchor="n",
            fill=TEXT,
            font=self._font_section_num,
            text=info.title,
            tags="chapter_card",
        )
        self.canvas.create_text(
            cx,
            y0 + 92,
            anchor="n",
            fill=TEXT_DIM,
            font=self._font_caption,
            width=w - 32,
            justify="center",
            text=info.principle,
            tags="chapter_card",
        )
        if narrative:
            self.canvas.create_text(
                cx,
                y0 + 142,
                anchor="n",
                fill=TEXT_DIM,
                font=self._font_eyebrow,
                width=w - 32,
                justify="center",
                text=narrative,
                tags="chapter_card",
            )
        self.canvas.create_text(
            cx,
            y1 - 18,
            anchor="s",
            fill=TEXT_DIM,
            font=self._font_eyebrow,
            text=info.citation,
            tags="chapter_card",
        )
        self.canvas.tag_raise("chapter_card")
        self._chapter_card_ticks_left = self._chapter_card_duration

    def _quit(self) -> None:
        self.running = False
        self.master_window.destroy()

    # ── Snapshots ───────────────────────────────────────────────────────────

    def _save_snapshot(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialdir="snapshots",
            initialfile=f"{self.engine.rule.name}-step{self.engine.step_count}.json",
            filetypes=[("JSON snapshot", "*.json")],
        )
        if not path:
            return
        self.engine.save(path)
        self._toast(f"Snapshot saved to {path}", kind="success")

    def _open_snapshot(self) -> None:
        path = filedialog.askopenfilename(initialdir="snapshots", filetypes=[("JSON snapshot", "*.json")])
        if not path:
            return
        self._stop()
        self.engine = Engine.load(path, REGISTRY)
        self.rule_var.set(self.engine.rule.name)
        self._init_renderer()
        self._render()
        self._update_status()

    # ── GIF recording / export ──────────────────────────────────────────────

    def _toggle_gif_record(self) -> None:
        if self._recording_gif:
            self._stop_gif_record()
        else:
            self._start_gif_record()

    def _start_gif_record(self) -> None:
        self._gif_frames = []
        self._recording_gif = True
        self.record_button.configure(text="■  STOP & SAVE")

    def _stop_gif_record(self) -> None:
        self._recording_gif = False
        self.record_button.configure(text="●  RECORD  GIF")
        if not self._gif_frames:
            self._toast("No frames captured.", kind="error")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".gif",
            initialdir="exports",
            initialfile=f"{self.engine.rule.name}-seed{self.engine.seed}.gif",
            filetypes=[("GIF", "*.gif")],
        )
        if not path:
            return
        export_gif(self._gif_frames, path, fps=max(int(self.fps_var.get()), 1))
        self._gif_frames = []
        self._toast(f"GIF saved to {path}", kind="success")

    def _export_csv(self) -> None:
        """Export the recorded per-step population stats as a CSV. Recording
        happens in ``_record_stats_sample`` and is capped to keep memory
        bounded; RESTART clears it."""
        if not self._stats_history:
            self._toast("No samples recorded yet — step or play the simulation first.", kind="error")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV", "*.csv")], title="Export stats as CSV"
        )
        if not path:
            return
        import csv

        keys: list[str] = []
        seen: set[str] = set()
        for row in self._stats_history:
            for k in row:
                if k not in seen:
                    seen.add(k)
                    keys.append(k)
        if "step" in keys:
            keys.remove("step")
            keys = ["step", *keys]
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            writer.writeheader()
            for row in self._stats_history:
                writer.writerow(row)
        log.info("exported %d stat samples to %s", len(self._stats_history), path)

    def _export_png(self) -> None:
        """Export the current frame as a PNG at the canvas resolution.

        Field rules render through ``render_rgb`` already; for discrete rules we
        rasterise via ``render_cell`` per grid cell (oval cells are drawn as
        filled circles inscribed in their cell)."""
        path = filedialog.asksaveasfilename(
            defaultextension=".png", filetypes=[("PNG", "*.png")], title="Export frame as PNG"
        )
        if not path:
            return
        from PIL import Image, ImageDraw

        rule = self.engine.rule
        kind = getattr(rule, "renderer_kind", "discrete")
        if kind == "field":
            arr = rule.render_rgb(self.engine.state)
            img = Image.fromarray(arr, "RGB").resize((CANVAS_SIZE, CANVAS_SIZE), Image.Resampling.NEAREST)
        else:
            w, h = self._state_dims()
            cw, ch = CANVAS_SIZE / w, CANVAS_SIZE / h
            img = Image.new("RGB", (CANVAS_SIZE, CANVAS_SIZE), (10, 14, 22))
            draw = ImageDraw.Draw(img)
            for y in range(h):
                for x in range(w):
                    color, shape = rule.render_cell(self.engine.state, x, y)
                    hex_ = color.lstrip("#")
                    if len(hex_) < 6:
                        continue
                    rgb = (int(hex_[0:2], 16), int(hex_[2:4], 16), int(hex_[4:6], 16))
                    box = [x * cw, y * ch, (x + 1) * cw - 1, (y + 1) * ch - 1]
                    if shape == "oval":
                        draw.ellipse(box, fill=rgb)
                    else:
                        draw.rectangle(box, fill=rgb)
        img.save(path)
        log.info("exported PNG to %s", path)

    def _export_gif(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".gif",
            initialdir="exports",
            initialfile=f"{self.engine.rule.name}-seed{self.engine.seed}.gif",
            filetypes=[("GIF", "*.gif")],
        )
        if not path:
            return

        n_frames = 60
        frames: list = []
        cancelled = False

        dlg = tk.Toplevel(self.master_window)
        dlg.title("Exporting GIF…")
        dlg.configure(background=BG)
        dlg.resizable(False, False)
        dlg.transient(self.master_window)
        dlg.grab_set()

        body = ttk.Frame(dlg, padding=(28, 22))
        body.pack(fill="both", expand=True)

        ttk.Label(body, text="  ".join("EXPORT"), style="Eyebrow.TLabel").pack(anchor="w")
        ttk.Label(body, text="rendering frames", style="Title.TLabel").pack(anchor="w", pady=(2, 0))
        self._hairline(body, color=HAIRLINE_HI).pack(fill="x", pady=(14, 16))

        progress_var = tk.IntVar(value=0)
        ttk.Progressbar(
            body, variable=progress_var, maximum=n_frames, length=380, style="Accent.Horizontal.TProgressbar"
        ).pack(fill="x")
        status_lbl = ttk.Label(body, text=f"frame 00 / {n_frames}", style="Apparatus.TLabel")
        status_lbl.pack(anchor="w", pady=(10, 18))

        def on_cancel() -> None:
            nonlocal cancelled
            cancelled = True

        cancel_btn = ttk.Button(body, text="CANCEL", style="Danger.TButton", command=on_cancel)
        cancel_btn.pack(anchor="e")

        def capture_frame(i: int) -> None:
            nonlocal cancelled
            if cancelled:
                dlg.destroy()
                return
            if i >= n_frames:
                status_lbl.config(text="saving GIF…")
                cancel_btn.config(state="disabled")
                fps = max(int(self.fps_var.get()), 1)
                captured = list(frames)

                def save_worker() -> None:
                    export_gif(captured, path, fps=fps)
                    self.after(0, _on_saved)

                def _on_saved() -> None:
                    dlg.destroy()
                    self._update_status()
                    self._toast(f"GIF saved to {path}", kind="success")

                threading.Thread(target=save_worker, daemon=True).start()
                return
            frames.append(self._snapshot_frame())
            self.engine.step()
            self._render()
            progress_var.set(i + 1)
            status_lbl.config(text=f"frame {i + 1:02d} / {n_frames}")
            self.after(1, lambda _i=i: capture_frame(_i + 1))  # type: ignore[misc]

        self.after(10, lambda: capture_frame(0))

    def _maybe_capture_frame(self) -> None:
        if self._recording_gif:
            self._gif_frames.append(self._snapshot_frame())

    def _snapshot_frame(self) -> dict:
        rule = self.engine.rule
        kind = getattr(rule, "renderer_kind", "discrete")
        if kind == "field":
            return {
                "kind": "field",
                "rgb": rule.render_rgb(self.engine.state).tolist(),
                "canvas_size": CANVAS_SIZE,
            }
        w, h = self._state_dims()
        cells = [[rule.render_cell(self.engine.state, x, y) for x in range(w)] for y in range(h)]
        return {"kind": "discrete", "width": w, "height": h, "cells": cells, "canvas_size": CANVAS_SIZE}

    # ── Tutorial (always-present caption) ───────────────────────────────────

    def _tutorial_start(self) -> None:
        self._tutorial_index = -1
        self._tutorial_next()

    def _tutorial_next(self) -> None:
        steps = tutorial_for(self.engine.rule.name)
        self._tutorial_index += 1
        if self._tutorial_index >= len(steps):
            self._tutorial_index = -1
            self.tutorial_var.set(self._tutorial_placeholder())
            return
        roman = "i ii iii iv v vi vii viii ix x".split()[min(self._tutorial_index, 9)]
        self.tutorial_var.set(f"{roman}.  {steps[self._tutorial_index]}")

    def _tutorial_all_steps(self) -> None:
        """L11 — open a modal listing every tutorial step for the current
        rule with click-to-jump. The marginalia caption updates to the
        chosen step. Mirrors the web client's "all steps at once" modal.
        """
        steps = tutorial_for(self.engine.rule.name)
        if not steps:
            self._toast("No tutorial for this rule.", kind="info")
            return
        dlg = tk.Toplevel(self.master_window)
        dlg.title("Tutorial — all steps")
        dlg.configure(background=BG)
        dlg.transient(self.master_window)
        dlg.grab_set()
        body = ttk.Frame(dlg, padding=(28, 22))
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="  ".join("TUTORIAL"), style="Eyebrow.TLabel").pack(anchor="w")
        ttk.Label(body, text=self.engine.rule.name, style="Title.TLabel").pack(anchor="w", pady=(2, 12))
        self._hairline(body, color=HAIRLINE_HI).pack(fill="x", pady=(0, 10))

        # Step list — each is a button that jumps to that step in the
        # marginalia caption when clicked.
        roman = "i ii iii iv v vi vii viii ix x xi xii xiii xiv".split()
        for idx, text in enumerate(steps):
            row = ttk.Frame(body)
            row.pack(fill="x", pady=(2, 2))
            label_text = roman[min(idx, len(roman) - 1)]

            def _jump(i: int = idx) -> None:
                # Setting _tutorial_index = i-1 means the next call to
                # _tutorial_next() (which increments first) will show step i.
                self._tutorial_index = i - 1
                self._tutorial_next()
                dlg.destroy()

            ttk.Button(row, text=f"  {label_text}.  {text}", command=_jump).pack(anchor="w", fill="x")

        ttk.Button(body, text="CLOSE", command=dlg.destroy).pack(anchor="e", pady=(14, 0))

    # ── Gallery viewer ──────────────────────────────────────────────────────

    _GALLERY_ITEMS = {
        "hero": (
            "Gray-Scott — self-replicating spots",
            "PLATE  α  ·  STAGE  I",
            "Hero composition rendered from the AAA visual identity pass. Pearson (1993) spots preset.",
            "docs/hero.png",
            (900, 506),
        ),
        "pipeline": (
            "Five stages of abiogenesis",
            "PLATE  Σ  ·  STAGES  I — V",
            "From primordial soup through reaction-diffusion, autocatalytic "
            "sets, vesicles, and protocell selection — left to right.",
            "docs/pipeline.png",
            (1100, 360),
        ),
        "prima": (
            "PRIMA MATERIA",
            "PLATE  XII  ·  MMXXVI",
            "Observational plate composed from real cellauto simulations. "
            "Design philosophy: docs/design/catalytic-silence.md.",
            "docs/prima-materia.png",
            (720, 960),
        ),
        "stage0": (
            "PRIMORDIAL SOUP",
            "PLATE  ·  STAGE  0",
            "Oparin–Haldane soup; Miller–Urey 1953 spark chemistry. Dissolved "
            "monomers mixing in a lightning-lit prebiotic ocean.",
            "docs/generated/stage0_soup.png",
            (900, 506),
        ),
        "stage1": (
            "REACTION–DIFFUSION",
            "PLATE  ·  STAGE  1",
            "Gray–Scott / Turing patterns: self-replicating spots that divide "
            "like protocells. Turing 1952; Pearson 1993.",
            "docs/generated/stage1_reaction_diffusion.png",
            (900, 506),
        ),
        "stage2": (
            "AUTOCATALYTIC SETS",
            "PLATE  ·  STAGE  2",
            "A reflexively-autocatalytic, food-generated reaction set igniting. "
            "Kauffman 1986; Hordijk & Steel 2004.",
            "docs/generated/stage2_autocatalytic.png",
            (900, 506),
        ),
        "stage3": (
            "VESICLE FORMATION",
            "PLATE  ·  STAGE  3",
            "Fatty-acid amphiphiles self-assembling into a lipid bilayer — the "
            "first compartment. Deamer 2008; Hanczyc & Szostak 2003.",
            "docs/generated/stage3_vesicles.png",
            (900, 506),
        ),
        "stage4": (
            "PROTOCELL SELECTION",
            "PLATE  ·  STAGE  4",
            "Bounded chemistry with heritable variation — the dawn of Darwinian "
            "selection. Eigen & Schuster 1977; Szostak 2017.",
            "docs/generated/stage4_selection.png",
            (900, 506),
        ),
        "poster": (
            "CHEMISTRY INTO LIFE",
            "PLATE  Ω  ·  STAGES  0 — 4",
            "The whole origin-of-life arc as one panorama: soup → patterns → "
            "autocatalysis → vesicles → protocell selection.",
            "docs/generated/pipeline_poster.png",
            (1100, 458),
        ),
        "stage7": (
            "THE CODON TABLE",
            "PLATE  ·  STAGE  VIII",
            "Genetic-code coevolution: random codes → partial consensus → "
            "crystallised code. The teal cell marks the first locked-in "
            "codon → amino-acid assignment. Vetsigian-Woese-Goldenfeld 2006.",
            "docs/generated/stage7_genetic_code_plate.png",
            (900, 1125),
        ),
        "stage11": (
            "THE CONSERVED CORE",
            "PLATE  ·  STAGE  XII",
            "LUCA distillation: gene-coverage field, the inferred 70%-prevalence "
            "core gene set as a teal-marked constellation, and the rooted tree "
            "of descent. Weiss et al. 2016.",
            "docs/generated/stage11_luca_plate.png",
            (900, 1125),
        ),
        "genesis": (
            "GENESIS",
            "PLATE  XIII  ·  MMXXVI",
            "Twelve observations on the coalescence of chemistry into life — "
            "the project's magnum opus. Every panel is real cellauto simulator "
            "output, stylised to the Catalytic Silence palette.",
            "docs/genesis.png",
            (740, 1141),
        ),
        "tableaux": (
            "TWELVE TABLEAUX",
            "PLATE  ·  THE PIPELINE",
            "12 panels reading left to right as a single procession through the "
            "chemistry-to-life arc. Generated via the whipgen MCP. Pairs with "
            "the deterministic Genesis plate.",
            "docs/generated/cellauto_twelve_tableaux.png",
            (1200, 675),
        ),
    }

    def _on_canvas_click(self, event: tk.Event) -> None:
        """If a Stage 4 ``Protocell`` lives under the click, open the inspector.
        Works for both the direct stage rule and the pipeline at stage 4."""
        state = self.engine.state
        sel = getattr(state, "inner_state", None) or state
        cells = getattr(sel, "cells", None)
        if not cells:
            return
        w, h = self._state_dims()
        gx = event.x / max(1.0, CANVAS_SIZE / w)
        gy = event.y / max(1.0, CANVAS_SIZE / h)
        for i, c in enumerate(cells):
            if not getattr(c, "alive", True):
                continue
            if (gx - c.cx) ** 2 + (gy - c.cy) ** 2 <= c.radius**2:
                self._show_protocell_inspector(i, c)
                return

    def _show_protocell_inspector(self, index: int, cell: Any) -> None:
        """Toplevel detail panel for one ``Protocell`` — surfaces the otherwise
        hidden genome, fitness, age, and radius so a learner can see *why* a
        disc is bright or dim and *what* is being selected on."""
        dlg = tk.Toplevel(self.master_window)
        dlg.title(f"Protocell #{index}")
        dlg.configure(background=BG)
        dlg.transient(self.master_window)
        body = ttk.Frame(dlg, padding=(22, 18))
        body.pack(fill="both", expand=True)
        ttk.Label(body, text=f"PROTOCELL  ·  #{index}", style="Eyebrow.TLabel").pack(anchor="w")

        def row(label: str, value: str) -> None:
            r = ttk.Frame(body)
            r.pack(fill="x", pady=(6, 0))
            ttk.Label(r, text=label, style="Apparatus.TLabel", width=12).pack(side="left")
            ttk.Label(r, text=value, style="Value.TLabel").pack(side="left")

        row("position", f"({cell.cx:.1f}, {cell.cy:.1f})")
        row("radius", f"{cell.radius:.2f}")
        row("age", f"{cell.age} steps")
        try:
            fit = float(cell.fitness())
        except Exception:  # noqa: BLE001
            fit = 0.0
        row("fitness", f"{fit:.4f}")
        genome_txt = "  ".join(f"{float(g):+.3f}" for g in cell.genome)
        ttk.Label(body, text="genome", style="Apparatus.TLabel").pack(anchor="w", pady=(8, 0))
        ttk.Label(body, text=genome_txt, style="Value.TLabel", wraplength=420, justify="left").pack(
            anchor="w"
        )
        ttk.Label(
            body,
            style="Caption.TLabel",
            wraplength=420,
            justify="left",
            text=(
                "Each genome entry is one internal species concentration. "
                "Fitness is the hypercycle-flavoured cyclic coupling "
                "Σ g[i]·g[(i+1) mod n] — zero if any species is missing, "
                "maximal at equal concentrations."
            ),
        ).pack(anchor="w", pady=(10, 0))

    def _open_network_view(self) -> None:
        """Render and show the current Stage 2 reaction network with its RAF
        highlighted — the on-demand payoff of the Hordijk-Steel algorithm."""
        state = self.engine.state
        inner = getattr(state, "inner_state", None)
        candidate = inner if inner is not None and hasattr(inner, "network") else state
        if not (hasattr(candidate, "network") and hasattr(candidate, "raf")):
            self._toast(
                "Switch to Stage 2 (autocatalytic sets) to view its reaction network and RAF.",
                kind="info",
            )
            return
        from cellauto.netviz import render_reaction_network

        img = render_reaction_network(candidate.network, candidate.raf, size=640)
        tmp = Path(tempfile.gettempdir()) / "cellauto_raf_network.png"
        img.save(tmp)

        dlg = tk.Toplevel(self.master_window)
        dlg.title("Reaction network — Stage 2 (RAF)")
        dlg.configure(background=BG)
        dlg.transient(self.master_window)
        body = ttk.Frame(dlg, padding=(20, 16))
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="AUTOCATALYTIC SET", style="Eyebrow.TLabel").pack(anchor="w")
        photo = tk.PhotoImage(file=str(tmp))
        lbl = ttk.Label(body, image=photo)
        lbl.image = photo  # type: ignore[attr-defined]  # GC-pin; Label has no formal attr
        lbl.pack(pady=(8, 8))
        ttk.Label(
            body,
            text="Hordijk-Steel closure of the live reaction network. "
            "Teal edges form the reflexively-autocatalytic, food-generated set.",
            style="Caption.TLabel",
            wraplength=600,
        ).pack(anchor="w")

    def _open_gallery(self, key: str) -> None:
        meta = self._GALLERY_ITEMS.get(key)
        if meta is None:
            return
        title, eyebrow, caption, rel_path, target_size = meta

        # Resolve image path relative to the package root, then the repo root,
        # so this works from both `pip install` and `python -m` invocations.
        candidate_roots = [
            Path(__file__).resolve().parent.parent,  # pip-installed
            Path(__file__).resolve().parents[2],  # repo root
            Path.cwd(),
        ]
        img_path = None
        for root in candidate_roots:
            p = root / rel_path
            if p.exists():
                img_path = p
                break
        if img_path is None:
            messagebox.showinfo(
                "Not found", f"Couldn't locate {rel_path}.\nTry running from the project root."
            )
            return

        dlg = tk.Toplevel(self.master_window)
        dlg.title(title)
        dlg.configure(background=BG)
        dlg.transient(self.master_window)
        dlg.grab_set()

        body = ttk.Frame(dlg, padding=(28, 22))
        body.pack(fill="both", expand=True)

        ttk.Label(body, text="  ".join(eyebrow), style="Eyebrow.TLabel").pack(anchor="center")
        ttk.Label(body, text=title, style="Title.TLabel").pack(anchor="center", pady=(4, 2))
        ttk.Label(body, text=caption, style="Caption.TLabel", wraplength=target_size[0]).pack(
            anchor="center", pady=(0, 12)
        )
        self._hairline(body, color=HAIRLINE_HI).pack(fill="x", pady=(0, 14))

        # Tk's PhotoImage handles PNG natively in Tk 8.6+. We scale via
        # subsample to fit the target size without dragging in Pillow.
        try:
            raw = tk.PhotoImage(file=str(img_path))
        except tk.TclError as exc:
            self._toast(f"Couldn't open: {exc}", kind="error")
            dlg.destroy()
            return
        tw, th = target_size
        factor = max(1, max(raw.width() // tw, raw.height() // th))
        scaled = raw.subsample(factor, factor) if factor > 1 else raw
        dlg._gallery_img = scaled  # type: ignore[attr-defined]  # GC anchor
        ttk.Label(body, image=scaled, background=BG).pack(anchor="center")

        ttk.Button(body, text="CLOSE", command=dlg.destroy).pack(anchor="e", pady=(14, 0))

    # ── About dialog ────────────────────────────────────────────────────────

    def _about(self) -> None:
        from cellauto import __version__

        dlg = tk.Toplevel(self.master_window)
        dlg.title("About cellauto")
        dlg.configure(background=BG)
        dlg.resizable(False, False)
        dlg.transient(self.master_window)
        dlg.grab_set()

        body = ttk.Frame(dlg, padding=(40, 28))
        body.pack(fill="both", expand=True)

        if ICON_PATH.exists():
            try:
                src = tk.PhotoImage(file=str(ICON_PATH))
                factor = max(1, src.width() // 96)
                dlg._icon_img = src.subsample(factor, factor)  # type: ignore[attr-defined]
                ttk.Label(body, image=dlg._icon_img).pack(pady=(0, 16))  # type: ignore[attr-defined]
            except tk.TclError:
                pass
        ttk.Label(body, text="  ".join("v" + __version__), style="Eyebrow.TLabel").pack()
        ttk.Label(body, text="cellauto", style="Title.TLabel").pack(pady=(0, 4))
        ttk.Label(body, text="an abiogenesis sandbox", style="Caption.TLabel").pack(pady=(0, 16))
        self._hairline(body, color=HAIRLINE_HI).pack(fill="x", pady=(0, 16))
        ttk.Label(
            body,
            text=(
                "primordial soup  ·  reaction-diffusion  ·\n"
                "autocatalytic sets  ·  vesicles  ·  protocell selection\n\n"
                "reference automata: Conway, Wolfram 1D.\n"
                "MIT licensed — see docs/science.md."
            ),
            justify="center",
            style="Apparatus.TLabel",
        ).pack()
        ttk.Button(body, text="CLOSE", command=dlg.destroy).pack(pady=(20, 0))

    # ── Rendering + status ──────────────────────────────────────────────────

    def _render(self) -> None:
        rule = self.engine.rule
        kind = getattr(rule, "renderer_kind", "discrete")
        inner = getattr(self.engine.state, "inner_rule", None)
        sem_eligible = bool(getattr(inner, "sem_eligible", False) or getattr(rule, "sem_eligible", False))
        want_sem = self._sem_mode and self._sem_available and (kind == "field" or sem_eligible)

        if want_sem and not isinstance(self._renderer, SemRenderer):
            self._init_renderer()
            self._render()
            return
        if isinstance(self._renderer, SemRenderer):
            sprites = None
            sprite_source = inner if inner is not None else rule
            sprite_state = getattr(self.engine.state, "inner_state", self.engine.state)
            if sprite_source is not None and hasattr(sprite_source, "render_sprites"):
                try:
                    sprites = sprite_source.render_sprites(sprite_state)
                except Exception:
                    sprites = None
            self._renderer.render(rule.render_rgb(self.engine.state), sprites=sprites)
        elif kind == "field" and isinstance(self._renderer, FieldRenderer):
            self._renderer.render(rule.render_rgb(self.engine.state))
        elif isinstance(self._renderer, DiscreteRenderer) and not want_sem:
            self._renderer.render(lambda x, y: rule.render_cell(self.engine.state, x, y))
        else:
            self._init_renderer()
            self._render()

    def _update_status(self) -> None:
        rule_name = self.engine.rule.name
        if len(rule_name) > 24:
            rule_name = rule_name[:21] + "…"
        self._status_rule_var.set(rule_name)
        self._status_seed_var.set(str(self.engine.seed))
        self._status_step_var.set(str(self.engine.step_count))
        self._status_fps_var.set(f"{self.engine.fps():.1f}")
        # L7 — rebuild the population chip flow. Keep the legacy
        # ``_status_pop_var`` in sync (some tests / debug scripts read it)
        # but the visible widget is now a wrap-friendly chip grid.
        pop_items = list(self.engine.population().items())
        pop_text = "    ".join(f"{k}={v}" for k, v in pop_items)
        self._status_pop_var.set(pop_text or "—")
        self._rebuild_population_chips(pop_items)
        self._sync_stage_caption()

    def _rebuild_population_chips(self, pop_items: list) -> None:
        """L7 — render each population stat as a chip-shaped label that
        wraps naturally in the parent frame instead of crowding one row.
        """
        chips_frame = getattr(self, "_status_pop_chips", None)
        if chips_frame is None:
            return
        # Clear previous chips.
        for child in list(chips_frame.winfo_children()):
            try:
                child.destroy()
            except tk.TclError:
                pass
        if not pop_items:
            ttk.Label(chips_frame, text="—", style="Value.TLabel").pack(anchor="w")
            return
        # Tkinter has no real flow layout; we simulate one by packing
        # each chip with side=left into a sequence of rows. We let each
        # chip take its natural width and create a new row once a
        # threshold is reached. The threshold is approximate (number of
        # chips per row scales with the window width minus the section
        # padding).
        row_pixel_budget = max(WINDOW_W - 120, 200)
        row: ttk.Frame | None = None
        current_pixels = 0
        approx_chip_pixels = 130  # conservative average for mono-style labels
        for k, v in pop_items:
            if row is None or current_pixels + approx_chip_pixels > row_pixel_budget:
                row = ttk.Frame(chips_frame)
                row.pack(anchor="w", fill="x")
                current_pixels = 0
            chip = ttk.Label(
                row,
                text=f"{k} = {v}",
                style="Apparatus.TLabel",
                padding=(8, 2, 8, 2),
            )
            chip.pack(side="left", padx=(0, 6), pady=(2, 2))
            current_pixels += approx_chip_pixels

    def _update_wall_label(self, stage: int | None) -> None:
        """L1 — refresh the always-visible stage wall-label.

        When the active rule is a pipeline (Stage IV's pipeline-extended,
        the canonical 5-stage one), show the current stage's title,
        principle, citation, and legend. Hide for non-pipeline rules
        (Conway, Wolfram, single stages) so the panel doesn't lie about
        having stage context.
        """
        frame = getattr(self, "_wall_label_frame", None)
        if frame is None:
            return
        if stage is None:
            self._wall_title_var.set("")
            self._wall_citation_var.set("")
            self._wall_principle_var.set("")
            self._wall_legend_var.set("")
            return
        rule = self.engine.rule
        info = rule.stage_info_for(stage) if hasattr(rule, "stage_info_for") else stage_info(stage)
        self._wall_title_var.set(f"{stage} · {info.title}")
        self._wall_citation_var.set(info.citation)
        self._wall_principle_var.set(info.principle)
        self._wall_legend_var.set(info.legend)

    def _sync_stage_caption(self) -> None:
        """Keep the on-canvas specimen label (and, on a transition, the
        marginalia) synced to the live pipeline stage. The pipeline state
        carries a ``current_stage``; individual rules don't, so for those we
        clear the overlay. Drawn on the canvas so it adds no layout height —
        adding widgets below the canvas in the fixed-height window would push
        the controls off the bottom edge.

        The overlay is tagged so it survives the renderers' per-frame
        ``itemconfigure`` updates and is re-raised above the image; a renderer
        re-init wipes it via ``delete("all")``, but this method runs again on
        the next status update and recreates it.
        """
        self.canvas.delete("stage_overlay")
        self._draw_legend_bar()
        self._draw_sparkline()
        stage = getattr(self.engine.state, "current_stage", None)
        # L1 — update the always-visible wall label even when there's no
        # pipeline (clear it instead). Then continue the existing canvas-
        # overlay flow below.
        self._update_wall_label(stage)
        if stage is None:
            self._displayed_stage = None
            return
        # Use the active rule's own stage_info table (the canonical 5-stage
        # pipeline and the 10-stage extended pipeline carry different infos);
        # fall back to the module-level table for backward compatibility.
        rule = self.engine.rule
        info = rule.stage_info_for(stage) if hasattr(rule, "stage_info_for") else stage_info(stage)
        self.canvas.create_text(
            14,
            12,
            anchor="nw",
            fill=TEXT,
            font=self._font_eyebrow,
            text=f"STAGE {stage} · {info.title}",
            tags="stage_overlay",
        )
        self.canvas.create_text(
            CANVAS_SIZE // 2,
            CANVAS_SIZE - 12,
            anchor="s",
            fill=TEXT_DIM,
            font=self._font_eyebrow,
            width=CANVAS_SIZE - 28,
            justify="center",
            text=info.legend,
            tags="stage_overlay",
        )
        self.canvas.tag_raise("stage_overlay")
        # Keep the SEM badge text in sync with the active stage.
        if isinstance(self._renderer, SemRenderer):
            self._renderer.set_stage_label(f"Stage {stage} — {info.title}")
        # Keep Channel B's narration pointed at the same pipeline stage.
        self._channel.set_stage(int(stage), self._pipeline_len())
        # On entering a new stage, announce it in the marginalia and stop any
        # in-progress manual tutorial walk so the chapter intro is visible.
        if stage != getattr(self, "_displayed_stage", None):
            self._displayed_stage = stage
            self._tutorial_index = -1
            self.tutorial_var.set(f"{info.principle}  —  {info.detail}  ({info.citation})")
            # The pipeline's inner rule changed, so refresh the parameter sliders
            # and the JUMP combobox, and propagate the CVD-safe flag.
            inner = getattr(self.engine.state, "inner_rule", None)
            if inner is not None and hasattr(inner, "colorblind_safe"):
                inner.colorblind_safe = self._colorblind_safe
            self._rebuild_parameters()
            self._sync_pipeline_row()
            self._show_chapter_card(stage, info)

    def _draw_sparkline(self) -> None:
        """Tiny line plot of the most recent population samples for the first
        non-meta key — gives the user a live trace of *the* characteristic stat
        for whatever rule is running (organic_cells for vents, droplets for
        coacervates, master_pct for RNA world, etc.) without spending layout."""
        self.canvas.delete("sparkline")
        if len(self._stats_history) < 2:
            return
        last = self._stats_history[-1]
        # Skip meta keys + nearly-constant ones (e.g. *_threshold_x1000).
        skip = {"step", "stage"}
        keys = [
            k
            for k in last
            if k not in skip and not k.endswith("_threshold_x1000") and not k.endswith("_threshold_x100")
        ]
        if not keys:
            return
        key = keys[0]
        values = [int(row.get(key, 0)) for row in self._stats_history[-180:]]
        x0, y0, x1, y1 = 12, CANVAS_SIZE - 78, 188, CANVAS_SIZE - 32
        self.canvas.create_rectangle(x0, y0, x1, y1, fill=PANEL, outline=HAIRLINE, tags="sparkline")
        vmin, vmax = min(values), max(values)
        span = max(vmax - vmin, 1)
        n = len(values)
        pts: list[float] = []
        for i, v in enumerate(values):
            xx = x0 + 2 + (i / max(n - 1, 1)) * (x1 - x0 - 4)
            yy = (y1 - 2) - ((v - vmin) / span) * (y1 - y0 - 4)
            pts.extend((xx, yy))
        self.canvas.create_line(*pts, fill=HAIRLINE_HI, width=2, tags="sparkline")
        self.canvas.create_text(
            x0 + 5,
            y0 + 3,
            anchor="nw",
            fill=TEXT_DIM,
            font=self._font_eyebrow,
            text=f"{key}  ·  {vmin}..{vmax}",
            tags="sparkline",
        )
        self.canvas.tag_raise("sparkline")

    def _draw_legend_bar(self) -> None:
        """Draw a colour-scale legend on the canvas for the field stages, so
        the viridis ramp (and Stage 4's red→green fitness) is decoded. On-canvas
        overlay = zero layout height. Field stages map a scalar concentration to
        viridis; Stage 4 maps protocell fitness to a red→green disc colour."""
        self.canvas.delete("legend_bar")
        target = self._param_target()
        if getattr(target, "renderer_kind", "discrete") != "field":
            return
        name = getattr(target, "name", "")
        x0, x1 = CANVAS_SIZE - 26, CANVAS_SIZE - 14
        y_top, y_bot = 44, CANVAS_SIZE - 44
        n = 48
        if name == "abiogenesis-stage4-selection":
            if self._colorblind_safe:
                colors = [
                    (int(40 + 200 * t), int(80 + 120 * t), int(180 * (1 - t) + 40 * t))
                    for t in np.linspace(0, 1, n)
                ]
            else:
                colors = [(int(255 * (1 - t)), int(255 * t), 0) for t in np.linspace(0, 1, n)]
            hi_label, lo_label = "fit 1", "fit 0"
        elif name == "abiogenesis-homochirality":
            # Diverging map: teal (L) at top ↔ magenta (R) at bottom.
            colors = [
                (int((1 - t) * 212 + t * 57), int((1 - t) * 57 + t * 212), int((1 - t) * 164 + t * 200))
                for t in np.linspace(0, 1, n)
            ]
            hi_label, lo_label = "L", "R"
        elif name == "abiogenesis-hydrothermal-vent":
            # pH map: alkaline (blue) at top ↔ acidic (orange) at bottom.
            colors = [(int(40 + (1 - t) * 170), 90, int(160 - (1 - t) * 120)) for t in np.linspace(0, 1, n)]
            hi_label, lo_label = "alk", "acid"
        elif name == "abiogenesis-coacervate":
            # Composition map: dilute (dark) ↔ coacervate-rich (gold).
            colors = [(int(20 + t * 192), int(16 + t * 164), int(24 + t * 66)) for t in np.linspace(0, 1, n)]
            hi_label, lo_label = "rich", "dilute"
        elif name == "abiogenesis-mineral-catalysis":
            # Polymer accumulation: none (dark) ↔ high (teal-green).
            colors = [(0, int(t * 235), int(t * 150)) for t in np.linspace(0, 1, n)]
            hi_label, lo_label = "polymer", "none"
        else:
            ramp = cmap_viridis(np.linspace(0.0, 1.0, n))
            colors = [(int(r), int(g), int(b)) for r, g, b in ramp]
            hi_label, lo_label = "hi", "lo"
        seg = (y_bot - y_top) / n
        for i, (r, g, b) in enumerate(colors):
            yy_bot = y_bot - seg * i
            yy_top = y_bot - seg * (i + 1)
            self.canvas.create_rectangle(
                x0,
                yy_top,
                x1,
                yy_bot,
                fill=f"#{r:02x}{g:02x}{b:02x}",
                width=0,
                tags="legend_bar",
            )
        self.canvas.create_rectangle(x0, y_top, x1, y_bot, outline=HAIRLINE, tags="legend_bar")
        # Unrolled (the two end labels) so the anchor stays a Literal rather
        # than collapsing to plain `str` through a loop variable.
        self.canvas.create_text(
            x0 - 5,
            y_top,
            anchor="se",
            fill=TEXT_DIM,
            font=self._font_eyebrow,
            text=hi_label,
            tags="legend_bar",
        )
        self.canvas.create_text(
            x0 - 5,
            y_bot,
            anchor="ne",
            fill=TEXT_DIM,
            font=self._font_eyebrow,
            text=lo_label,
            tags="legend_bar",
        )
        self.canvas.tag_raise("legend_bar")


def run(
    rule_name: str = "abiogenesis-pipeline", grid_size: int = DEFAULT_GRID, seed: int | None = None
) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    root = tk.Tk()
    App(root, rule_name=rule_name, grid_size=grid_size, seed=seed)
    root.mainloop()
