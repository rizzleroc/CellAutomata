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
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, font as tkfont, messagebox, ttk
from typing import Any

from cellauto.engine import Engine
from cellauto.export import export_gif
from cellauto.mascot import AmoebaMascot
from cellauto.renderer import DiscreteRenderer, FieldRenderer
from cellauto.rules import REGISTRY
from cellauto.tutorial import tutorial_for

ASSETS_DIR = Path(__file__).parent / "assets"
ICON_PATH = ASSETS_DIR / "icon.png"
FONTS_DIR = ASSETS_DIR / "fonts"

log = logging.getLogger(__name__)

CANVAS_SIZE = 600
DEFAULT_GRID = 60
DEFAULT_FPS = 8.0

# ── Catalytic Silence palette ───────────────────────────────────────────────
BG          = "#0a0e16"  # obsidian
TEXT        = "#e6e0d0"  # warm bone (museum caption)
TEXT_DIM    = "#8c8a82"  # quiet bone
HAIRLINE    = "#1f4f4c"  # desaturated teal — for thin separators
HAIRLINE_HI = "#39d4c8"  # accent teal — for canvas rim and focus
RECORD_M    = "#d439a4"  # magenta — counterpoint, only on record
STOP_R      = "#7a3036"  # restrained brick — only on stop

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
    def __init__(self, master: tk.Tk, rule_name: str = "abiogenesis-pipeline",
                 grid_size: int = DEFAULT_GRID, seed: int | None = None) -> None:
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

        self._setup_theme()
        self._build_widgets()
        self._build_menu()
        self._apply_window_icon()
        self._renderer = None
        self._new_engine(rule_name=rule_name, grid_size=grid_size, seed=seed)

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
        self._fam_italic = first("Crimson Pro", "CrimsonPro", "Constantia",
                                 "Georgia", "TkDefaultFont")
        self._fam_mono = first("IBM Plex Mono", "IBMPlexMono", "Cascadia Mono",
                               "Consolas", "TkFixedFont")
        # ttk needs an actual sans for combobox text; we keep the platform one.
        self._fam_ui = first("Segoe UI", "TkDefaultFont")

        self._font_title       = (self._fam_display, 22)
        self._font_eyebrow     = (self._fam_mono, 9)        # tracked microcaps
        self._font_section_num = (self._fam_display, 16)    # Roman numerals
        self._font_section     = (self._fam_mono, 9, "bold")
        self._font_button      = (self._fam_mono, 9, "bold")
        self._font_label       = (self._fam_mono, 9)
        self._font_value       = (self._fam_mono, 10)
        self._font_caption     = (self._fam_italic, 11, "italic")
        self._font_ui_widget   = (self._fam_ui, 9)

        # Base widget colours.
        style.configure(".", background=BG, foreground=TEXT,
                        bordercolor=HAIRLINE, lightcolor=HAIRLINE,
                        darkcolor=HAIRLINE, focuscolor=BG,
                        fieldbackground=BG, font=self._font_ui_widget)

        style.configure("TFrame", background=BG)

        style.configure("TLabel", background=BG, foreground=TEXT,
                        font=self._font_label)
        style.configure("Title.TLabel", background=BG, foreground=TEXT,
                        font=self._font_title)
        style.configure("Eyebrow.TLabel", background=BG, foreground=TEXT_DIM,
                        font=self._font_eyebrow)
        style.configure("Roman.TLabel", background=BG, foreground=TEXT,
                        font=self._font_section_num)
        style.configure("Section.TLabel", background=BG, foreground=TEXT_DIM,
                        font=self._font_section)
        style.configure("Apparatus.TLabel", background=BG, foreground=TEXT_DIM,
                        font=self._font_label)
        style.configure("Value.TLabel", background=BG, foreground=TEXT,
                        font=self._font_value)
        style.configure("Caption.TLabel", background=BG, foreground=TEXT,
                        font=self._font_caption)

        # Outlined museum-card buttons.
        style.configure(
            "TButton",
            background=BG, foreground=TEXT,
            bordercolor=HAIRLINE, lightcolor=BG, darkcolor=BG,
            relief="solid", borderwidth=1,
            focusthickness=0, focuscolor=BG,
            padding=(18, 10), font=self._font_button,
        )
        style.map(
            "TButton",
            background=[("active", "#10141d"), ("pressed", BG),
                        ("disabled", BG)],
            foreground=[("disabled", "#3a3934")],
            bordercolor=[("active", HAIRLINE_HI), ("disabled", "#262421")],
        )

        # Primary (play): teal hairline always.
        style.configure("Primary.TButton",
                        background=BG, foreground=HAIRLINE_HI,
                        bordercolor=HAIRLINE_HI, lightcolor=BG, darkcolor=BG)
        style.map("Primary.TButton",
                  background=[("active", "#0f1a1e"), ("pressed", BG),
                              ("disabled", BG)],
                  foreground=[("disabled", "#3a3934")],
                  bordercolor=[("disabled", "#262421"),
                               ("active", HAIRLINE_HI)])

        # Stop: restrained brick.
        style.configure("Danger.TButton",
                        background=BG, foreground=STOP_R,
                        bordercolor=STOP_R, lightcolor=BG, darkcolor=BG)
        style.map("Danger.TButton",
                  background=[("active", "#1a0e10"), ("pressed", BG),
                              ("disabled", BG)],
                  foreground=[("disabled", "#3a3934")],
                  bordercolor=[("disabled", "#262421"),
                               ("active", STOP_R)])

        # Record: magenta hairline.
        style.configure("Record.TButton",
                        background=BG, foreground=RECORD_M,
                        bordercolor=RECORD_M, lightcolor=BG, darkcolor=BG)
        style.map("Record.TButton",
                  background=[("active", "#1a0d18"), ("pressed", BG)],
                  bordercolor=[("active", RECORD_M)])

        # Combobox — flat field, hairline border, mono text.
        style.configure("TCombobox",
                        fieldbackground=BG, background=BG, foreground=TEXT,
                        arrowcolor=HAIRLINE_HI, bordercolor=HAIRLINE,
                        lightcolor=BG, darkcolor=BG,
                        padding=(8, 6), font=self._font_value)
        style.map("TCombobox",
                  fieldbackground=[("readonly", BG), ("disabled", BG)],
                  foreground=[("disabled", "#3a3934")],
                  bordercolor=[("active", HAIRLINE_HI),
                               ("focus", HAIRLINE_HI)],
                  arrowcolor=[("active", TEXT)])
        # Dropdown listbox (separate Toplevel — needs X resources).
        self.master_window.option_add("*TCombobox*Listbox.background", BG)
        self.master_window.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.master_window.option_add("*TCombobox*Listbox.selectBackground",
                                       HAIRLINE_HI)
        self.master_window.option_add("*TCombobox*Listbox.selectForeground", BG)
        self.master_window.option_add("*TCombobox*Listbox.font",
                                       self._font_value)
        self.master_window.option_add("*TCombobox*Listbox.borderWidth", 0)
        self.master_window.option_add("*TCombobox*Listbox.relief", "flat")

        # FPS scale — extremely thin trough.
        style.configure("TScale", background=BG, troughcolor=HAIRLINE,
                        bordercolor=BG, lightcolor=HAIRLINE_HI,
                        darkcolor=HAIRLINE_HI)

        # GIF-export progressbar.
        style.configure("Accent.Horizontal.TProgressbar",
                        troughcolor=HAIRLINE, background=HAIRLINE_HI,
                        bordercolor=BG, lightcolor=HAIRLINE_HI,
                        darkcolor=HAIRLINE_HI, thickness=8)

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

    def _hairline(self, parent: tk.Widget, color: str = HAIRLINE,
                  height: int = 1) -> tk.Frame:
        return tk.Frame(parent, background=color, height=height, borderwidth=0,
                        highlightthickness=0)

    def _section(self, parent: tk.Widget, roman: str, name: str,
                 pad_top: int = 14, pad_bottom: int = 8) -> tk.Frame:
        """A section header: Italiana Roman numeral · tracked mono label,
        followed by a thin teal hairline rule. Returns the body Frame the
        caller fills with section content."""
        block = ttk.Frame(parent)
        block.pack(fill="x", pady=(pad_top, 0))

        head = ttk.Frame(block)
        head.pack(fill="x")
        ttk.Label(head, text=roman, style="Roman.TLabel").pack(side="left",
                                                                padx=(0, 10))
        # Letter-spacing in Tk is faked by joining chars with spaces.
        spaced = "  ".join(name)
        ttk.Label(head, text=spaced, style="Section.TLabel").pack(side="left",
                                                                   pady=(6, 0))

        rule = self._hairline(block)
        rule.pack(fill="x", pady=(8, pad_bottom))

        body = ttk.Frame(block)
        body.pack(fill="x")
        return body

    # ── Layout ──────────────────────────────────────────────────────────────

    def _build_widgets(self) -> None:
        outer = ttk.Frame(self, padding=(34, 24, 34, 22))
        outer.pack(fill="both", expand=True)

        self._build_header(outer)
        self._build_observation(outer)
        self._build_configuration(outer)
        self._build_transport(outer)
        self._build_register(outer)
        self._build_marginalia(outer)

    def _build_header(self, parent: ttk.Frame) -> None:
        from cellauto import __version__

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

        ttk.Label(title_col,
                  text="  ".join("PLATE I  ·  CELLAUTO  ·  MMXXVI"),
                  style="Eyebrow.TLabel").pack(anchor="center")
        ttk.Label(title_col, text="cellauto", style="Title.TLabel").pack(
            anchor="center", pady=(4, 2))
        ttk.Label(title_col,
                  text="five observations on the coalescence of chemistry into pattern",
                  style="Caption.TLabel").pack(anchor="center")
        self._hairline(header, color=HAIRLINE_HI).pack(fill="x", pady=(16, 0),
                                                       anchor="center")

    def _build_observation(self, parent: ttk.Frame) -> None:
        body = self._section(parent, "I", "OBSERVATION", pad_top=18)

        # Frame with a 2-px teal rim — same vocabulary as the plate's specimens.
        frame = tk.Frame(body, background=HAIRLINE_HI, highlightthickness=0)
        frame.pack(anchor="center", pady=(2, 0))
        self.canvas = tk.Canvas(frame, width=CANVAS_SIZE, height=CANVAS_SIZE,
                                background=BG, highlightthickness=0,
                                borderwidth=2)
        self.canvas.pack(padx=2, pady=2)

    def _build_configuration(self, parent: ttk.Frame) -> None:
        body = self._section(parent, "II", "CONFIGURATION")

        row = ttk.Frame(body)
        row.pack(fill="x")

        ttk.Label(row, text="RULE", style="Apparatus.TLabel").pack(side="left",
                                                                    padx=(0, 8))
        self.rule_var = tk.StringVar(value="abiogenesis-pipeline")
        rule_picker = ttk.Combobox(row, textvariable=self.rule_var,
                                   values=list(REGISTRY), width=30, state="readonly")
        rule_picker.pack(side="left", padx=(0, 22))
        rule_picker.bind("<<ComboboxSelected>>", lambda _e: self._on_rule_change())

        ttk.Label(row, text="GRID", style="Apparatus.TLabel").pack(side="left",
                                                                    padx=(0, 8))
        self.grid_size_var = tk.StringVar(value=str(DEFAULT_GRID))
        grid_picker = ttk.Combobox(row, textvariable=self.grid_size_var,
                                   values=["30", "60", "100", "150"],
                                   width=5, state="readonly")
        grid_picker.pack(side="left", padx=(0, 22))
        grid_picker.bind("<<ComboboxSelected>>", lambda _e: self._on_rule_change())

        ttk.Button(row, text="RESEED", command=self._reseed).pack(side="left",
                                                                   padx=(0, 8))
        ttk.Button(row, text="PROMOTE",
                   command=self._promote_stage).pack(side="left")

    def _build_transport(self, parent: ttk.Frame) -> None:
        body = self._section(parent, "III", "TRANSPORT")

        row = ttk.Frame(body)
        row.pack(fill="x")

        self.step_button = ttk.Button(row, text="STEP", command=self._step_once)
        self.step_button.pack(side="left")
        self.play_button = ttk.Button(row, text="PLAY",
                                       style="Primary.TButton", command=self._play)
        self.play_button.pack(side="left", padx=(8, 0))
        self.stop_button = ttk.Button(row, text="STOP",
                                       style="Danger.TButton",
                                       command=self._stop, state="disabled")
        self.stop_button.pack(side="left", padx=(8, 0))

        ttk.Label(row, text="FPS", style="Apparatus.TLabel").pack(side="left",
                                                                   padx=(22, 8))
        self.fps_var = tk.DoubleVar(value=DEFAULT_FPS)
        self.fps_value_var = tk.StringVar(value=f"{int(DEFAULT_FPS):>2d}")
        ttk.Scale(row, from_=1, to=60, variable=self.fps_var,
                  orient="horizontal", length=170,
                  command=lambda v: self.fps_value_var.set(
                      f"{int(float(v)):>2d}")).pack(side="left")
        ttk.Label(row, textvariable=self.fps_value_var,
                  style="Value.TLabel", width=3).pack(side="left", padx=(8, 0))

        ttk.Button(row, text="TUTORIAL",
                   command=self._tutorial_next).pack(side="right")
        self.record_button = ttk.Button(row, text="●  RECORD  GIF",
                                        style="Record.TButton",
                                        command=self._toggle_gif_record)
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

        def cell(parent: ttk.Frame, label: str, var: tk.StringVar,
                 width: int, col: int, padx: int = 22) -> None:
            cont = ttk.Frame(parent)
            cont.grid(row=0, column=col, sticky="w", padx=(0, padx))
            ttk.Label(cont, text=label, style="Apparatus.TLabel").pack(anchor="w")
            ttk.Label(cont, textvariable=var, style="Value.TLabel",
                      width=width, anchor="w").pack(anchor="w", pady=(2, 0))

        cell(grid, "RULE",   self._status_rule_var, 24, 0)
        cell(grid, "SEED",   self._status_seed_var, 12, 1)
        cell(grid, "STEP",   self._status_step_var,  8, 2)
        cell(grid, "FPS",    self._status_fps_var,   6, 3, padx=0)

        ttk.Label(body, text="POPULATION", style="Apparatus.TLabel").pack(
            anchor="w", pady=(10, 2))
        ttk.Label(body, textvariable=self._status_pop_var, style="Value.TLabel",
                  anchor="w", wraplength=WINDOW_W - 80,
                  justify="left").pack(anchor="w", fill="x")

    def _build_marginalia(self, parent: ttk.Frame) -> None:
        body = self._section(parent, "V", "MARGINALIA", pad_bottom=0)
        self.tutorial_var = tk.StringVar(value=self._tutorial_placeholder())
        ttk.Label(body, textvariable=self.tutorial_var, style="Caption.TLabel",
                  wraplength=WINDOW_W - 80, justify="left", anchor="w").pack(
            anchor="w", fill="x")

    def _tutorial_placeholder(self) -> str:
        return ("press TUTORIAL to advance through this rule's commentary, "
                "one citation at a time.")

    # ── Menu ────────────────────────────────────────────────────────────────

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.master_window, tearoff=0, bd=0)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="New", command=self._reseed, accelerator="Ctrl+N")
        filemenu.add_command(label="Open snapshot…", command=self._open_snapshot,
                             accelerator="Ctrl+O")
        filemenu.add_command(label="Save snapshot…", command=self._save_snapshot,
                             accelerator="Ctrl+S")
        filemenu.add_separator()
        filemenu.add_command(label="Export GIF…", command=self._export_gif)
        filemenu.add_separator()
        filemenu.add_command(label="Quit", command=self._quit, accelerator="Ctrl+Q")
        menubar.add_cascade(label="File", menu=filemenu)

        gallerymenu = tk.Menu(menubar, tearoff=0)
        gallerymenu.add_command(label="Hero — Gray-Scott close-up",
                                command=lambda: self._open_gallery("hero"))
        gallerymenu.add_command(label="Pipeline strip",
                                command=lambda: self._open_gallery("pipeline"))
        gallerymenu.add_command(label="Prima Materia — Plate XII",
                                command=lambda: self._open_gallery("prima"))
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
        self._new_engine(rule_name=self.rule_var.get(),
                         grid_size=int(self.grid_size_var.get()), seed=None)
        self.tutorial_var.set(self._tutorial_placeholder())
        self._tutorial_index = -1

    def _reseed(self) -> None:
        self._stop()
        self._new_engine(rule_name=self.rule_var.get(),
                         grid_size=int(self.grid_size_var.get()), seed=None)

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
        self._maybe_capture_frame()

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

    def _quit(self) -> None:
        self.running = False
        self.master_window.destroy()

    # ── Snapshots ───────────────────────────────────────────────────────────

    def _save_snapshot(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".json", initialdir="snapshots",
            initialfile=f"{self.engine.rule.name}-step{self.engine.step_count}.json",
            filetypes=[("JSON snapshot", "*.json")],
        )
        if not path:
            return
        self.engine.save(path)
        messagebox.showinfo("Saved", f"Snapshot saved to\n{path}")

    def _open_snapshot(self) -> None:
        path = filedialog.askopenfilename(
            initialdir="snapshots", filetypes=[("JSON snapshot", "*.json")])
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
            defaultextension=".gif", initialdir="exports",
            initialfile=f"{self.engine.rule.name}-seed{self.engine.seed}.gif",
            filetypes=[("GIF", "*.gif")],
        )
        if not path:
            return
        export_gif(self._gif_frames, path, fps=max(int(self.fps_var.get()), 1))
        self._gif_frames = []
        messagebox.showinfo("Exported", f"GIF saved to\n{path}")

    def _export_gif(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".gif", initialdir="exports",
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

        ttk.Label(body, text="  ".join("EXPORT"),
                  style="Eyebrow.TLabel").pack(anchor="w")
        ttk.Label(body, text="rendering frames", style="Title.TLabel").pack(
            anchor="w", pady=(2, 0))
        self._hairline(body, color=HAIRLINE_HI).pack(fill="x", pady=(14, 16))

        progress_var = tk.IntVar(value=0)
        ttk.Progressbar(body, variable=progress_var, maximum=n_frames,
                        length=380,
                        style="Accent.Horizontal.TProgressbar").pack(fill="x")
        status_lbl = ttk.Label(body, text=f"frame 00 / {n_frames}",
                               style="Apparatus.TLabel")
        status_lbl.pack(anchor="w", pady=(10, 18))

        def on_cancel() -> None:
            nonlocal cancelled
            cancelled = True

        cancel_btn = ttk.Button(body, text="CANCEL",
                                style="Danger.TButton", command=on_cancel)
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
            return {"kind": "field",
                    "rgb": rule.render_rgb(self.engine.state).tolist(),
                    "canvas_size": CANVAS_SIZE}
        w, h = self._state_dims()
        cells = [[rule.render_cell(self.engine.state, x, y) for x in range(w)]
                 for y in range(h)]
        return {"kind": "discrete", "width": w, "height": h,
                "cells": cells, "canvas_size": CANVAS_SIZE}

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
        roman = "i ii iii iv v vi vii viii ix x".split()[
            min(self._tutorial_index, 9)]
        self.tutorial_var.set(
            f"{roman}.  {steps[self._tutorial_index]}"
        )

    # ── Gallery viewer ──────────────────────────────────────────────────────

    _GALLERY_ITEMS = {
        "hero": (
            "Gray-Scott — self-replicating spots",
            "PLATE  α  ·  STAGE  I",
            "Hero composition rendered from the AAA visual identity pass. "
            "Pearson (1993) spots preset.",
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
    }

    def _open_gallery(self, key: str) -> None:
        meta = self._GALLERY_ITEMS.get(key)
        if meta is None:
            return
        title, eyebrow, caption, rel_path, target_size = meta

        # Resolve image path relative to the package root, then the repo root,
        # so this works from both `pip install` and `python -m` invocations.
        candidate_roots = [
            Path(__file__).resolve().parent.parent,                # pip-installed
            Path(__file__).resolve().parents[2],                   # repo root
            Path.cwd(),
        ]
        img_path = None
        for root in candidate_roots:
            p = root / rel_path
            if p.exists():
                img_path = p
                break
        if img_path is None:
            messagebox.showinfo("Not found",
                                f"Couldn't locate {rel_path}.\n"
                                "Try running from the project root.")
            return

        dlg = tk.Toplevel(self.master_window)
        dlg.title(title)
        dlg.configure(background=BG)
        dlg.transient(self.master_window)
        dlg.grab_set()

        body = ttk.Frame(dlg, padding=(28, 22))
        body.pack(fill="both", expand=True)

        ttk.Label(body, text="  ".join(eyebrow),
                  style="Eyebrow.TLabel").pack(anchor="center")
        ttk.Label(body, text=title, style="Title.TLabel").pack(
            anchor="center", pady=(4, 2))
        ttk.Label(body, text=caption, style="Caption.TLabel",
                  wraplength=target_size[0]).pack(anchor="center", pady=(0, 12))
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

        ttk.Button(body, text="CLOSE", command=dlg.destroy).pack(
            anchor="e", pady=(14, 0))

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
        ttk.Label(body, text="  ".join("v" + __version__),
                  style="Eyebrow.TLabel").pack()
        ttk.Label(body, text="cellauto", style="Title.TLabel").pack(pady=(0, 4))
        ttk.Label(body, text="an abiogenesis sandbox",
                  style="Caption.TLabel").pack(pady=(0, 16))
        self._hairline(body, color=HAIRLINE_HI).pack(fill="x", pady=(0, 16))
        ttk.Label(
            body,
            text=("primordial soup  ·  reaction-diffusion  ·\n"
                  "autocatalytic sets  ·  vesicles  ·  protocell selection\n\n"
                  "reference automata: Conway, Wolfram 1D.\n"
                  "MIT licensed — see docs/science.md."),
            justify="center", style="Apparatus.TLabel",
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


def run(rule_name: str = "abiogenesis-pipeline", grid_size: int = DEFAULT_GRID,
        seed: int | None = None) -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    root = tk.Tk()
    App(root, rule_name=rule_name, grid_size=grid_size, seed=seed)
    root.mainloop()
