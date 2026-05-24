# Production container for `cellauto web`.
#
# Used by Railway (or any container host) to serve the Flask web sandbox.
# Locally: `cellauto web` is still the dev-server path; this image runs
# gunicorn for production traffic.

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install deps first (pyproject + readme/license are all setuptools needs
# to resolve the project metadata), then copy the source. Keeps the
# expensive pip layer cached across source-only changes.
COPY pyproject.toml README.md LICENSE ./
COPY cellauto ./cellauto
RUN pip install ".[web]"

# Railway injects $PORT at runtime; default to 8765 for local `docker run`.
ENV PORT=8765
EXPOSE 8765

# One worker is intentional: session state is per-process (see
# cellauto/web/wsgi.py). The shell form lets $PORT expand at start.
CMD gunicorn cellauto.web.wsgi:app \
    --bind 0.0.0.0:${PORT} \
    --workers 1 \
    --threads 4 \
    --timeout 60 \
    --access-logfile -
