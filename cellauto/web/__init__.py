"""Browser-facing wrapper around the engine.

A small Flask app exposes the existing Engine and Rule registry over HTTP
so the same simulations the Tk GUI runs can be driven from a browser. Per-
session sims live in-memory on the server; frames are rendered with each
rule's existing ``render_rgb`` and shipped as PNG bytes.

Run via ``cellauto web`` once the optional ``[web]`` extras are installed.
"""

from cellauto.web.server import build_app, run

__all__ = ["build_app", "run"]
