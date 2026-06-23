# web9 promo — assembly kit

Builds a vertical **9:16** promo that combines the **web9 UI**, the **rendered protocell
clip**, and an **ElevenLabs voiceover** into one `promo.mp4`.

The agent sandbox can't run this (no ffmpeg / no Chromium / egress-blocked from the clip
CDN), so run it on a machine with `node`, `ffmpeg`, and network access.

## Pieces
- `narration.txt` — the voiceover script (input for ElevenLabs).
- `capture.mjs` — Playwright screen-recording of the web9 walkthrough → 1080×1920 `.webm`.
- `build.sh` — ffmpeg mux: protocell clip (intro) + UI capture + voiceover → `promo.mp4`.

## Storyboard (~35s, matches the voiceover)
| time | visual | line |
|------|--------|------|
| 0–6s | protocell clip, full screen | "This isn't a cell. It only learned to divide." |
| 6–14s | web9 hero + SEM lab | "Two chemicals on a blank lattice…" |
| 14–22s | lab materials / scan-sweep | "web9 renders that moment… Unreal Engine 5.8 pipeline." |
| 22–30s | proof metrics | "Deterministic to the bit…" |
| 30–35s | #origin clip → footer | "Deterministic chemistry in. A dividing cell out…" |

## 1. Voiceover → `narration.mp3`
ElevenLabs TTS of `narration.txt`. Claude renders this via the whip ElevenLabs tool once that
server is back; or generate it in the ElevenLabs UI. Save as `narration.mp3` here.

## 2. Protocell clip → `protocell.mp4`
`build.sh` auto-downloads it if missing, or fetch it yourself:

    curl -fsSL https://s.asim.sh/videos/3d89a86a-1b9b-463b-b48f-89361bc766c3.mp4 -o protocell.mp4

## 3. Capture the UI → `web9.webm`

    npm i -D playwright && npx playwright install chromium
    ( cd .. && python3 -m http.server 8798 ) &     # serve docs/web9
    URL=http://localhost:8798/ DUR=30000 node capture.mjs
    mv capture/*.webm web9.webm

Run on a networked machine so the `#origin` clip loads in-page — or self-host
`protocell.mp4` into `../assets/video/` first (then the page uses the local source).

## 4. Build → `promo.mp4`

    chmod +x build.sh && ./build.sh

Env knobs: `CLIP`, `WEB9`, `VO`, `OUT`, `INTRO` (intro seconds), and `DUR` (capture length).
Tune `DUR` so intro + walkthrough ≈ the voiceover length (~35s).

## Extending
To fold in the Soup/Spark clips later, drop them here and add more inputs +
`concat=n=…` segments in `build.sh`.
