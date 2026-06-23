# web9 cinematic clip

Holds the featured render for the `#origin` ("The cell, rendered") section of web9.

The clip is the protocell dividing — translucent membrane, cyan Fresnel rim, dark-field
scan-sweep — generated as a vertical **9:16** scanning-microscope clip via the ASIM
"New Video Gym" (Sora) pipeline.

`index.html` lists two `<source>`s, in order:

1. `assets/video/protocell.mp4` — self-hosted (preferred). Drop the file here to use it.
2. `https://s.asim.sh/videos/3d89a86a-1b9b-463b-b48f-89361bc766c3.mp4` — the CDN URL the gym
   produced, used as a fallback until the file is self-hosted.

`video.js` keeps the `#origin` section hidden until the clip loads, so the page degrades
cleanly if neither source is reachable.

To self-host, download the CDN URL above to `protocell.mp4` in this directory (the agent's
sandbox is egress-blocked from `s.asim.sh`, so this step is done from an unrestricted machine).
