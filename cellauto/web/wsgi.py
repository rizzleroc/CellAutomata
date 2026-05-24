"""WSGI entrypoint for production servers (Railway, gunicorn, etc.).

    gunicorn cellauto.web.wsgi:app --bind 0.0.0.0:$PORT --workers 1

One worker is the right default: sessions live in process memory (see
``_SessionStore``), so multi-worker setups would scatter a user's sim
state across processes. If you scale out, swap the store for Redis
first.
"""

from __future__ import annotations

from cellauto.web.server import build_app

app = build_app()
