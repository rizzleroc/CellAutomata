# Social assets

## `cellauto_progress.mp4`

A 33-second vertical (1080×1920) "progress" sizzle reel for cellauto — built
for TikTok (@ai.news760) and other vertical-video feeds.

**It is made entirely from the real project:** the motion segments are genuine
headless `cellauto export` simulator output (Gray-Scott division, hydrothermal
vent, homochirality, RNA world, coacervates), inter-cut with the project's own
museum plates (`docs/hero.png`, `docs/pipeline.png`, `docs/genesis.png`,
`docs/prima-materia.png`) and title/stats/CTA cards.

### Reproduce it

```bash
pip install -e .                          # the cellauto package (numpy, Pillow)
pip install imageio-ffmpeg                # bundled static ffmpeg
bash marketing/social/render_footage.sh   # writes real sim GIFs to exports/
python3 marketing/social/build_progress_video.py
# -> marketing/social/assets/cellauto_progress.mp4
```

Text is rendered with Pillow (the bundled ffmpeg has no `drawtext`); ffmpeg
handles compositing, Ken-Burns motion, crossfades, H.264/AAC encoding, and a
subtle ambient audio bed. Edit the `scenes` list in `build_progress_video.py`
to change copy, ordering, or timing.

> Publishing is manual — download the MP4 and upload it to TikTok yourself.
