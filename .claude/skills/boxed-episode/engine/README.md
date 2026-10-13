# BOXED engine snapshot

The canonical copy of the BOXED drawing engine (Python 3.11 + skia-python), kept here because the working copy lives
in the session scratchpad and is wiped whenever the container resets.

- `eng/` — `core` (drawing kit, boil, paper/grain), `letters` (hand-painted lettering), `world` (sky + creatures +
  props), `sets` (parallax camera, cosmos, the talk-show set), `zee` / `cast` (the performers), `acting` (IK +
  performance track), `lipsync`, `shots_a` (shot helpers), `shots_ep2` (seated Gary + audience helpers live here),
  `gary` (`draw_gary`: the standard full-body Gary — legs, turns, arms, every expression).
- Finished episodes' source lives in `../episodes/ep<N>/` (Ep4: all nine shot modules, scripts and data), as idioms
  to copy from and to re-render from.
- `setup.sh [B]` — recreate a working engine: copies `eng/`, fetches the 10 Google Fonts, links libEGL/libGLESv2 from
  the Playwright chromium, installs Python deps, runs an import check.

When an episode improves an engine module, copy it back here so the next episode starts from it (and ask the user
before committing). Fonts are not committed: they are fetched from google/fonts (SIL OFL 1.1 / Apache 2.0).
