# Security Policy

## Supported versions

CellAutomata is an educational cellular-automata / abiogenesis sandbox. Security
fixes are applied to the latest `main`. There is no long-term support branch.

| Version | Supported |
|---|---|
| latest `main` | ✅ |
| older tags | ❌ (please upgrade) |

## Reporting a vulnerability

**Please do not open a public issue for security vulnerabilities.**

Report privately via GitHub's coordinated disclosure:
[**Report a vulnerability**](https://github.com/rizzleroc/CellAutomata/security/advisories/new)
(Repository → **Security** → **Advisories** → **Report a vulnerability**).

Please include: affected file/path, version/commit, a description of the issue
and its impact, and reproduction steps or a proof of concept if available.

We aim to acknowledge reports within a few days and to agree a coordinated
disclosure timeline before any details are made public.

## Important trust boundaries for users

- **Snapshot / save files (`.json`) are code-trust artifacts.** Loading a
  simulation snapshot deserializes data produced by whoever created the file.
  **Only open snapshots from sources you trust.** Treat shared `.json`
  snapshots like you would any executable attachment. (Hardening of the
  snapshot loader is tracked in the project's security backlog.)
- **`CELLAUTO_SPRITE_DIR` and other asset-path overrides** cause the app to load
  and decode images from the directory you point them at. Do not point them at
  untrusted directories.
- **The web clients** (`docs/web*`) are static, client-side simulations with no
  backend and no authentication; they store no personal data beyond a single
  local "welcome dismissed" flag in `localStorage`.

## Scope

In scope: the `cellauto` Python package (desktop GUI + CLI), the static web
clients under `docs/`, the build/CI configuration, and the container/deploy
configuration.

Out of scope: third-party dependencies (report those upstream; we track and
update them here), and the developer-only scripts under `tools/` except where
they process untrusted input.

## Acknowledgements

A full white-box security audit of the project was completed on 2026-06-03; see
[`docs/PRD_SECURITY_AUDIT.md`](docs/PRD_SECURITY_AUDIT.md) and the tracking epic
for status of known issues and their remediation.
