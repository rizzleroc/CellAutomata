# ORIGINS — render log & delivery manifest

Reverse-morphogenesis series. Each clip is generated on the ASIM video app
(`simId 343003`, portrait, text-to-video, model Sora/VEO) and returned as a
public `s.asim.sh` URL. **The URLs are the deliverable** — this container's
egress allowlist blocks `s.asim.sh` (`x-deny-reason: host_not_allowed`), so the
mp4s can't be mirrored into the repo unless `s.asim.sh` is added to the
environment's network allowlist. The URLs open fine in a normal browser.

Proven recipe (the leaf pilot that rendered cleanly):
`Vertical 9:16, locked static camera, pure solid black background. A single <SUBJECT> fills the frame. Time runs in reverse: <pattern dissolves/disperses into a flowing field, smoothing to a uniform <palette> haze>. Backward-drifting particles, hypnotic, scientific, elegant, slow motion. No text, no captions, no words on screen, no people.`

## Delivered

| # | Clip | Status | URL |
|---|------|--------|-----|
| 1 | Leaf (veins) | ✅ done | https://s.asim.sh/videos/b59ffb89-b432-46c4-acab-f9c286f906c2.mp4 |
| 2 | Leopard (spots) | ✅ done | https://s.asim.sh/videos/c38f6db3-8f0a-42e1-a8a0-9c8e0acd0d8c.mp4 |
| 3 | Zebra (stripes) | ✅ done | https://s.asim.sh/videos/7a06ba49-a0fd-4f6e-928d-1242c6548239.mp4 |
| 4 | Luna Moth (eyespots) | ⏳ rendering | — |
| 5 | Pufferfish (reticulation) | ⏳ queued | — |
| 6 | Cone Shell (Rule 30 CA) | ⏳ queued | — |

## Staged prompts (ready to fire)

**2 · Leopard** — `Vertical 9:16, locked static camera, pure solid black background. A close macro view of leopard fur, dense black rosettes on a golden coat, fills the frame. Time runs in reverse: the rosettes drift apart, dissolve and disperse into a flowing reaction-diffusion field, the spots spreading out and smoothing into a calm uniform golden haze. Backward-drifting particles, hypnotic, scientific, elegant, slow motion. No text, no captions, no words on screen, no people.`

**3 · Zebra** — `Vertical 9:16, locked static camera, pure solid black background. A close macro view of zebra hide, crisp parallel black-and-white stripes, fills the frame. Time runs in reverse: the stripes ripple, break apart and disperse into a flowing reaction-diffusion field, the bands smoothing into a uniform silver-grey haze. Backward-drifting particles, hypnotic, scientific, elegant, slow motion. No text, no captions, no words on screen, no people.`

**4 · Luna Moth** — `Vertical 9:16, locked static camera, pure solid black background. A single pale green luna moth wing with dark concentric eyespots and margin bands fills the frame. Time runs in reverse: the eyespots collapse inward to single points, the wing bands dissolve, the scales disperse into a flowing reaction-diffusion field smoothing to a uniform jade haze. Backward-drifting particles, hypnotic, scientific, elegant, slow motion. No text, no captions, no words on screen, no people.`

**5 · Pufferfish** — `Vertical 9:16, locked static camera, pure solid black background. A close macro view of pufferfish skin, a golden-brown labyrinthine maze pattern, fills the frame. Time runs in reverse: the maze-like reticulation flows and rearranges like a living simulation, then disperses and smooths into a uniform aqua haze. Backward-drifting particles, hypnotic, scientific, elegant, slow motion. No text, no captions, no words on screen, no people.`

**6 · Cone Shell** — `Vertical 9:16, locked static camera, pure solid black background. A textile cone shell with intricate brown-and-white triangular tent markings fills the frame. Time runs in reverse: the triangular tent markings resolve row by row into a one-dimensional cellular-automaton spacetime diagram of flickering black-and-white cells, then scatter into a smooth parchment haze. Backward-drifting particles, hypnotic, scientific, elegant, slow motion. No text, no captions, no words on screen, no people.`

## Fire sequence (per clip, when MCP is connected)
```
whipgen_asim_generate_video(simId="343003", prompt=<above>, orientation="portrait", noRef=true, studio=true, async=true)  -> jobId
whipgen_job_status(jobId)                          # wait for submit to register
whipgen_asim_watch_last(simId="343003", match=<subject fragment>)  -> target.videoUrl
```
