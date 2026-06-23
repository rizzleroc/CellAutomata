# web9 cinematic clips

Holds the two origin-of-life interlude clips for the `#origin` section of web9.

Expected files — vertical **9:16**, H.264 `.mp4`, muted, loop-friendly, ~12s:

- `soup.mp4`  — **The Soup**: a Hadean hydrothermal primordial ocean.
- `spark.mp4` — **The Spark**: the first self-organizing chemistry.

`video.js` keeps the `#origin` section hidden until at least one clip loads, and
hides any individual clip whose file is missing — so the page degrades cleanly
while the footage is being produced.

Generated via the ASIM "New Video Gym" image→video pipeline. Drop the two `.mp4`
files in this directory and the section lights up automatically; no markup change
needed.
