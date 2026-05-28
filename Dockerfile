# Static-only deploy of docs/ for Railway (and any other container host).
#
# Slim Python base, copy docs/, run the stdlib HTTP server. No project
# deps installed — this image only ships the static site, not the
# cellauto Python package.
FROM python:3.12-slim

WORKDIR /site
COPY docs/ /site/

# Railway provides $PORT; fall back to 8080 for local docker runs.
ENV PORT=8080
EXPOSE 8080

# `sh -c` so $PORT is expanded at start time (Railway sets it per-deploy).
CMD ["sh", "-c", "exec python -m http.server \"$PORT\" --bind 0.0.0.0"]
