# CellAuto deploy image (Railway and any container host).
#
# Runs the FastAPI app server (server/app.py): it serves the free static site
# from docs/ AND gates the Pro hi-res SEM render endpoint behind Clerk + Stripe.
# The cellauto package is installed so the render endpoint can drive the real
# engine + SEM renderer headlessly (no tkinter — see server/render.py).
#
# Safe rollout: with no Clerk/Stripe env vars set the server still serves the
# static site + /healthz; Pro endpoints report "billing_not_configured" until
# the operator provides keys. See docs/PRD_WEB9_PRO.md.
FROM python:3.12-slim

WORKDIR /app

# numpy + Pillow ship manylinux wheels, so no system build toolchain is needed.
COPY pyproject.toml README.md LICENSE ./
COPY cellauto/ ./cellauto/
COPY server/ ./server/
COPY docs/ ./docs/

RUN python -m pip install --upgrade pip && pip install ".[server]"

# Railway provides $PORT; fall back to 8080 for local docker runs.
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
EXPOSE 8080

# `sh -c` so $PORT is expanded at start time; --app-dir puts /app on sys.path
# so `server.app` imports cleanly.
CMD ["sh", "-c", "exec python -m uvicorn server.app:app --host 0.0.0.0 --port ${PORT} --app-dir /app"]
