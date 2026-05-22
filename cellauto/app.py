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

from cellauto.engine import Engine
from cellauto.export import export_gif
from cellauto.mascot import AmoebaMascot
from cellauto.renderer import DiscreteRenderer, FieldRenderer, cmap_viridis
from cellauto.rules import REGISTRY
from cellauto.rules.abiogenesis.pipeline import stage_info
from cellauto.rules.abiogenesis.science import GRAY_SCOTT_PRESETS
from cellauto.rules.params import PARAM_SPECS, PEARSON_PRESET_RULES, ParamSpec
from cellauto.tutorial import tutorial_for

ASSETS_DIR = Path(__file__).parent / "assets"
ICON_PATH = ASSETS_DIR / "icon.png"
FONTS_DIR = ASSETS_DIR / "fonts"

log = logging.getLogger(__name__)

CANVAS_SIZE = 600
DEFAULT_GRID = 60
DEFAULT_FPS = 8.0

# ── Catalytic Silence palette ───────────────────────────────────────────────
BG = "#0a0e16"  # obsidian
TEXT = "#e6e0d0"  # warm bone (museum caption)
TEXT_DIM = "#8c8a82"  # quiet bone
HAIRLINE = "#1f4f4c"  # desaturated teal — for thin separators
HAIRLINE_HI = "#39d4c8"  # accent teal — for canvas rim and focus
RECORD_M = "#d439a4"  # magenta — counterpoint, only on record
STOP_R = "#7a3036"  # restrained brick — only on stop

# Window is fixed so iterations never reflow the layout.
WINDOW_W = 720
WINDOW_H = 1000


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

        self._setup_theme()
        self._build_widgets()
        self._build_menu()
        self._apply_window_icon()
        self._renderer = None
        self._new_engine(rule_name=rule_name, grid_size=grid_size, seed=seed)
        self._anim_frame = 0
        self._animate()

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
        # ttk needs an actual sans for combobox text; we keep the platform one.
        self._fam_ui = first("Segoe UI", "TkDefaultFont")

        self._font_title = (self._fam_display, 22)
        self._font_eyebrow = (self._fam_mono, 9)  # tracked microcaps
        self._font_section_num = (self._fam_display, 16)  # Roman numerals
        self._font_section = (self._fam_mono, 9, "bold")
        self._font_button = (self._fam_mono, 9, "bold")
        self._font_label = (self._fam_mono, 9)
        self._font_value = (self._fam_mono, 10)
        self._font_caption = (self._fam_italic, 11, "italic")
        self._font_ui_widget = (self._fam_ui, 9)

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
            foreground=[("disabled", "#3a3934")],
            bordercolor=[("active", HAIRLINE_HI), ("disabled", "#262421")],
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
            foreground=[("disabled", "#3a3934")],
            bordercolor=[("disabled", "#262421"), ("active", HAIRLINE_HI)],
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
            foreground=[("disabled", "#3a3934")],
            bordercolor=[("disabled", "#262421"), ("active", STOP_R)],
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
            foreground=[("disabled", "#3a3934")],
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
        if kind == "field":
            self._renderer = FieldRenderer(canvas=self.canvas, canvas_size=CANVAS_SIZE)
        else:
            self._renderer = DiscreteRenderer(canvas=self.canvas, canvas_size=CANVAS_SIZE)
        self._renderer.reset(w, h)

    # ── Layout primitives ───────────────────────────────────────────────────

    def _hairline(self, parent: tk.Widget, color: str = HAIRLINE, height: int = 1) -> tk.Frame:
        return tk.Frame(parent, background=color, height=height, borderwidth=0, highlightthickness=0)

    def _section(
        self, parent: tk.Widget, roman: str, name: str, pad_top: int = 14, pad_bottom: int = 8
    ) -> tk.Frame:
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
        self._build_configuration(outer)
        self._build_transport(outer)
        self._build_register(outer)
        self._build_marginalia(outer)

    def _build_header(self, parent: ttk.Frame) -> None:

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

        ttk.Label(title_col, text="  ".join("PLATE I  ·  CELLAUTO  ·  MMXXVI"), style="Eyebrow.TLabel").pack(
            anchor="center"
        )
        ttk.Label(title_col, text="cellauto", style="Title.TLabel").pack(anchor="center", pady=(4, 2))
        ttk.Label(
            title_col,
            text="five observations on the coalescence of chemistry into pattern",
            style="Caption.TLabel",
        ).pack(anchor="center")
        self._hairline(header, color=HAIRLINE_HI).pack(fill="x", pady=(16, 0), anchor="center")

    def _build_observation(self, parent: ttk.Frame) -> None:
        body = self._section(parent, "I", "OBSERVATION", pad_top=18)

        # Frame with a 2-px teal rim — same vocabulary as the plate's specimens.
        frame = tk.Frame(body, background=HAIRLINE_HI, highlightthickness=0)
        frame.pack(anchor="center", pady=(2, 0))
        self.canvas = tk.Canvas(
            frame, width=CANVAS_SIZE, height=CANVAS_SIZE, background=BG, highlightthickness=0, borderwidth=2
        )
        self.canvas.pack(padx=2, pady=2)
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
        jump_picker = ttk.Combobox(
            self._pipeline_row,
            textvariable=self._jump_var,
            values=["0", "1", "2", "3", "4"],
            width=3,
            state="readonly",
        )
        jump_picker.pack(side="left", padx=(0, 18))
        jump_picker.bind("<<ComboboxSelected>>", lambda _e: self._on_jump_to_stage())
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
        """Show the JUMP / AUTO-PROMOTE / DUR controls only for the pipeline rule."""
        rule = self.engine.rule
        if getattr(rule, "name", "") == "abiogenesis-pipeline":
            if not self._pipeline_row.winfo_ismapped():
                self._pipeline_row.pack(fill="x", pady=(8, 0), before=self._param_frame)
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
        # Pearson regime preset picker (Gray-Scott only) — sets F and k together.
        if getattr(target, "name", "") in PEARSON_PRESET_RULES:
            prow = ttk.Frame(self._param_frame)
            prow.pack(fill="x", pady=(0, 6))
            ttk.Label(prow, text="preset", style="Apparatus.TLabel", width=16).pack(side="left")
            self._preset_var.set("")
            picker = ttk.Combobox(
                prow,
                textvariable=self._preset_var,
                width=12,
                state="readonly",
                values=list(GRAY_SCOTT_PRESETS),
            )
            picker.pack(side="left")
            picker.bind("<<ComboboxSelected>>", lambda _e: self._on_preset_change())
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
                command=lambda _v, s=spec: self._on_param_change(s),
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

    def _on_param_change(self, spec: ParamSpec) -> None:
        var, readout, _ = self._param_vars[spec.attr]
        value: float = var.get()
        if spec.integer:
            value = int(round(value))
        setattr(self._param_target(), spec.attr, value)
        readout.set(self._fmt_param(value, spec))
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
        ttk.Label(
            body,
            textvariable=self._status_pop_var,
            style="Value.TLabel",
            anchor="w",
            wraplength=WINDOW_W - 80,
            justify="left",
        ).pack(anchor="w", fill="x")

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
            ("poster", "Chemistry into life — full arc"),
        ):
            gallerymenu.add_command(label=label, command=lambda k=key: self._open_gallery(k))
        gallerymenu.add_separator()
        gallerymenu.add_command(
            label="Hero — Gray-Scott close-up", command=lambda: self._open_gallery("hero")
        )
        gallerymenu.add_command(label="Pipeline strip", command=lambda: self._open_gallery("pipeline"))
        gallerymenu.add_command(
            label="Prima Materia — Plate XII", command=lambda: self._open_gallery("prima")
        )
        gallerymenu.add_separator()
        gallerymenu.add_command(label="Reaction network (Stage 2 RAF)…", command=self._open_network_view)
        menubar.add_cascade(label="Gallery", menu=gallerymenu)

        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Start tutorial", command=self._tutorial_start)
        helpmenu.add_command(label="About", command=self._about)
        menubar.add_cascade(label="Help", menu=helpmenu)

        self.master_window.config(menu=menubar)
        self.master_window.bind_all("<Control-n>", lambda _e: self._reseed())
        self.master_window.bind_all("<Control-o>", lambda _e: self._open_snapshot())
        self.master_window.bind_all("<Control-s>", lambda _e: self._save_snapshot())
        self.master_window.bind_all("<Control-q>", lambda _e: self._quit())
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
        self._stats_history.clear()
        self._init_renderer()
        self._render()
        self._update_status()
        self._rebuild_parameters()
        self._sync_pipeline_row()

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
        current_kind = "field" if isinstance(self._renderer, FieldRenderer) else "discrete"
        if expected_kind != current_kind:
            self._init_renderer()
        self._render()
        self._update_status()
        self._record_stats_sample()
        self._maybe_capture_frame()

    def _record_stats_sample(self) -> None:
        """Append the current population dict to the time-series buffer."""
        sample = {"step": int(self.engine.step_count), **dict(self.engine.population())}
        self._stats_history.append(sample)
        if len(self._stats_history) > self._stats_history_cap:
            del self._stats_history[: len(self._stats_history) - self._stats_history_cap]

    def _play(self) -> None:
        if self.running:
            return
        self.running = True
        self.play_button.configure(state="disabled")
        self.step_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        if hasattr(self, "mascot"):
            self.mascot.set_happy(True)
        self._loop()

    def _stop(self) -> None:
        self.running = False
        self.play_button.configure(state="normal")
        self.step_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        if hasattr(self, "mascot"):
            self.mascot.set_happy(False)

    def _loop(self) -> None:
        if not self.running:
            return
        self._step_once()
        delay_ms = max(int(1000 / max(self.fps_var.get(), 1)), 16)
        self.canvas.after(delay_ms, self._loop)

    def _animate(self) -> None:
        """Continuous ~20 fps tick so the amoeba colony breathes/blinks even
        while the simulation is paused. Independent of the sim step loop."""
        self._anim_frame += 1
        renderer = self._renderer
        if isinstance(renderer, DiscreteRenderer) and renderer.animated:
            try:
                renderer.animate(self._anim_frame)
            except tk.TclError:
                return
        try:
            self.master_window.after(50, self._animate)
        except tk.TclError:
            return

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
        messagebox.showinfo("Saved", f"Snapshot saved to\n{path}")

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
            messagebox.showinfo("No frames", "No frames captured.")
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
        messagebox.showinfo("Exported", f"GIF saved to\n{path}")

    def _export_csv(self) -> None:
        """Export the recorded per-step population stats as a CSV. Recording
        happens in ``_record_stats_sample`` and is capped to keep memory
        bounded; RESTART clears it."""
        if not self._stats_history:
            messagebox.showinfo("Stats", "No samples recorded yet — step or play the simulation first.")
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
            img = Image.fromarray(arr, "RGB").resize((CANVAS_SIZE, CANVAS_SIZE), Image.NEAREST)
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
                    messagebox.showinfo("Exported", f"GIF saved to\n{path}")

                threading.Thread(target=save_worker, daemon=True).start()
                return
            frames.append(self._snapshot_frame())
            self.engine.step()
            self._render()
            progress_var.set(i + 1)
            status_lbl.config(text=f"frame {i + 1:02d} / {n_frames}")
            self.after(1, lambda _i=i: capture_frame(_i + 1))

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
    }

    def _open_network_view(self) -> None:
        """Render and show the current Stage 2 reaction network with its RAF
        highlighted — the on-demand payoff of the Hordijk-Steel algorithm."""
        state = self.engine.state
        inner = getattr(state, "inner_state", None)
        candidate = inner if inner is not None and hasattr(inner, "network") else state
        if not (hasattr(candidate, "network") and hasattr(candidate, "raf")):
            messagebox.showinfo(
                "Reaction network",
                "Switch to Stage 2 (autocatalytic sets) to view its reaction network and RAF.",
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
        lbl.image = photo  # keep a reference so it isn't garbage-collected
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
            messagebox.showerror("Couldn't open", str(exc))
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
        if kind == "field" and isinstance(self._renderer, FieldRenderer):
            self._renderer.render(rule.render_rgb(self.engine.state))
        elif isinstance(self._renderer, DiscreteRenderer):
            self._renderer.render(lambda x, y: rule.render_cell(self.engine.state, x, y))
        else:
            self._init_renderer()
            self._render()

    def _update_status(self) -> None:
        pop = "    ".join(f"{k}={v}" for k, v in self.engine.population().items())
        rule_name = self.engine.rule.name
        if len(rule_name) > 24:
            rule_name = rule_name[:21] + "…"
        self._status_rule_var.set(rule_name)
        self._status_seed_var.set(str(self.engine.seed))
        self._status_step_var.set(str(self.engine.step_count))
        self._status_fps_var.set(f"{self.engine.fps():.1f}")
        self._status_pop_var.set(pop or "—")
        self._sync_stage_caption()

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
        if stage is None:
            self._displayed_stage = None
            return
        info = stage_info(stage)
        self.canvas.create_text(
            14,
            12,
            anchor="nw",
            fill=TEXT,
            font=self._font_eyebrow,
            text=f"STAGE {info.index} · {info.title}",
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
        # On entering a new stage, announce it in the marginalia and stop any
        # in-progress manual tutorial walk so the chapter intro is visible.
        if stage != getattr(self, "_displayed_stage", None):
            self._displayed_stage = stage
            self._tutorial_index = -1
            self.tutorial_var.set(f"{info.principle}  —  {info.detail}  ({info.citation})")
            # The pipeline's inner rule changed, so refresh the parameter sliders
            # and the JUMP combobox.
            self._rebuild_parameters()
            self._sync_pipeline_row()

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
        self.canvas.create_rectangle(x0, y0, x1, y1, fill="#0e1218", outline=HAIRLINE, tags="sparkline")
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
        for label, y, anchor in ((hi_label, y_top, "se"), (lo_label, y_bot, "ne")):
            self.canvas.create_text(
                x0 - 5,
                y,
                anchor=anchor,
                fill=TEXT_DIM,
                font=self._font_eyebrow,
                text=label,
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
