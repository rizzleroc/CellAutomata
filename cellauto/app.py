"""Tk GUI sandbox app.

Dispatches between two renderers based on ``rule.renderer_kind``:
  - "discrete" → DiscreteRenderer (canvas items per cell; v3.0 P0 perf fix
    tracks shapes in our own list rather than calling canvas.type per cell)
  - "field"    → FieldRenderer (numpy → PhotoImage blit, fast for continuous fields)
"""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any

from cellauto.engine import Engine
from cellauto.export import export_gif
from cellauto.renderer import DiscreteRenderer, FieldRenderer
from cellauto.rules import REGISTRY
from cellauto.tutorial import tutorial_for

log = logging.getLogger(__name__)

CANVAS_SIZE = 600
DEFAULT_GRID = 60
DEFAULT_FPS = 8.0


class App(tk.Frame):
    def __init__(self, master: tk.Tk, rule_name: str = "abiogenesis-pipeline",
                 grid_size: int = DEFAULT_GRID, seed: int | None = None) -> None:
        super().__init__(master)
        self.master_window = master
        self.master_window.title("cellauto — abiogenesis sandbox")
        self.pack(fill="both", expand=True)
        self._tutorial_index: int = -1
        self._gif_frames: list = []
        self._recording_gif = False
        self.running = False

        self._build_widgets()
        self._build_menu()
        self._renderer = None
        self._new_engine(rule_name=rule_name, grid_size=grid_size, seed=seed)

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

    def _build_widgets(self) -> None:
        top = ttk.Frame(self)
        top.pack(side="top", fill="x", padx=8, pady=6)

        ttk.Label(top, text="Rule:").pack(side="left")
        self.rule_var = tk.StringVar(value="abiogenesis-pipeline")
        rule_picker = ttk.Combobox(top, textvariable=self.rule_var, values=list(REGISTRY),
                                   width=30, state="readonly")
        rule_picker.pack(side="left", padx=4)
        rule_picker.bind("<<ComboboxSelected>>", lambda _e: self._on_rule_change())

        ttk.Label(top, text="Grid:").pack(side="left", padx=(12, 0))
        self.grid_size_var = tk.StringVar(value=str(DEFAULT_GRID))
        grid_picker = ttk.Combobox(top, textvariable=self.grid_size_var,
                                   values=["30", "60", "100", "150"],
                                   width=5, state="readonly")
        grid_picker.pack(side="left", padx=4)
        grid_picker.bind("<<ComboboxSelected>>", lambda _e: self._on_rule_change())

        ttk.Button(top, text="Reseed", command=self._reseed).pack(side="left", padx=12)
        ttk.Button(top, text="Promote stage",
                   command=self._promote_stage).pack(side="left", padx=4)

        self.canvas = tk.Canvas(self, width=CANVAS_SIZE, height=CANVAS_SIZE,
                                background="#ffffff", highlightthickness=1,
                                highlightbackground="#cccccc")
        self.canvas.pack(padx=8, pady=4)

        controls = ttk.Frame(self)
        controls.pack(side="top", fill="x", padx=8, pady=4)

        self.step_button = ttk.Button(controls, text="Step", command=self._step_once)
        self.step_button.pack(side="left")
        self.play_button = ttk.Button(controls, text="Play", command=self._play)
        self.play_button.pack(side="left", padx=4)
        self.stop_button = ttk.Button(controls, text="Stop",
                                       command=self._stop, state="disabled")
        self.stop_button.pack(side="left")

        ttk.Label(controls, text="FPS:").pack(side="left", padx=(16, 2))
        self.fps_var = tk.DoubleVar(value=DEFAULT_FPS)
        ttk.Scale(controls, from_=1, to=60, variable=self.fps_var,
                  orient="horizontal", length=160).pack(side="left")

        ttk.Button(controls, text="Tutorial",
                   command=self._tutorial_next).pack(side="left", padx=(16, 4))
        self.record_button = ttk.Button(controls, text="Record GIF",
                                        command=self._toggle_gif_record)
        self.record_button.pack(side="left")

        self.status_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.status_var, anchor="w",
                  relief="sunken", padding=4).pack(side="bottom", fill="x")

        self.tutorial_var = tk.StringVar(value="")
        self.tutorial_label = ttk.Label(self, textvariable=self.tutorial_var, anchor="w",
                                         padding=(8, 4), background="#fff8c4",
                                         wraplength=CANVAS_SIZE)

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.master_window)
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

    def _on_rule_change(self) -> None:
        self._stop()
        self._new_engine(rule_name=self.rule_var.get(),
                         grid_size=int(self.grid_size_var.get()), seed=None)

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
        # Pipeline rule may swap renderer kind on promote.
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
        self._loop()

    def _stop(self) -> None:
        self.running = False
        self.play_button.configure(state="normal")
        self.step_button.configure(state="normal")
        self.stop_button.configure(state="disabled")

    def _loop(self) -> None:
        if not self.running:
            return
        self._step_once()
        delay_ms = max(int(1000 / max(self.fps_var.get(), 1)), 16)
        self.canvas.after(delay_ms, self._loop)

    def _quit(self) -> None:
        self.running = False
        self.master_window.destroy()

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

    def _toggle_gif_record(self) -> None:
        if self._recording_gif:
            self._stop_gif_record()
        else:
            self._start_gif_record()

    def _start_gif_record(self) -> None:
        self._gif_frames = []
        self._recording_gif = True
        self.record_button.configure(text="Stop & save GIF")

    def _stop_gif_record(self) -> None:
        self._recording_gif = False
        self.record_button.configure(text="Record GIF")
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
        frames = []
        for _ in range(60):
            frames.append(self._snapshot_frame())
            self.engine.step()
            self._render()
        export_gif(frames, path, fps=max(int(self.fps_var.get()), 1))
        self._update_status()
        messagebox.showinfo("Exported", f"GIF saved to\n{path}")

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

    def _tutorial_start(self) -> None:
        self._tutorial_index = -1
        self.tutorial_label.pack(side="top", fill="x", padx=8, pady=(0, 4))
        self._tutorial_next()

    def _tutorial_next(self) -> None:
        steps = tutorial_for(self.engine.rule.name)
        self._tutorial_index += 1
        if self._tutorial_index >= len(steps):
            self._tutorial_index = -1
            self.tutorial_label.pack_forget()
            return
        self.tutorial_var.set(
            f"[{self._tutorial_index + 1}/{len(steps)}] {steps[self._tutorial_index]}"
        )

    def _about(self) -> None:
        messagebox.showinfo(
            "About cellauto",
            "cellauto sandbox\n"
            "Abiogenesis pipeline: primordial soup → reaction-diffusion → autocatalytic\n"
            "sets → vesicles → protocell selection.\n"
            "Reference automata: Conway, Wolfram 1D.\n"
            "MIT licensed. See PRD.md and docs/science.md for citations.",
        )

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
        pop = ", ".join(f"{k}={v}" for k, v in self.engine.population().items())
        self.status_var.set(
            f"rule={self.engine.rule.name}  seed={self.engine.seed}  "
            f"step={self.engine.step_count}  fps={self.engine.fps():.1f}  |  {pop}"
        )


def run(rule_name: str = "abiogenesis-pipeline", grid_size: int = DEFAULT_GRID,
        seed: int | None = None) -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    root = tk.Tk()
    App(root, rule_name=rule_name, grid_size=grid_size, seed=seed)
    root.mainloop()
