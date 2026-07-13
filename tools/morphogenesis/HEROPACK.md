# Hero Pack — what to generate & upload

You generate the **hero clips** (Sora / Veo / Kling / Runway — whatever gives the best look); I turn each one
into a family of genuinely-viral vertical cuts (hero+SEM reveal, boomerang loops, hooks, optional Attenborough
VO) and assemble the 10-day, 50/day set. This is the proven-quality path — one great hero → ~15 posts.

## The look (keep every clip consistent — this is the brand)
Paste this **style suffix** onto every prompt:

> *extreme macro scientific microscopy, electric-cyan bioluminescent glow with hot magenta-pink cores,
> pitch-black background, floating particulate, soft volumetric light shafts, shallow depth of field,
> slow cinematic motion, photoreal, awe-inspiring, vertical 9:16, ~6 seconds, seamless loop.*

Reference: your dividing-cell Sora clip + the AI hero still I generated (cyan rim / magenta core / dumbbell split).

## Specs (per clip)
- **Vertical 9:16**, ~**5–8 s**, slow motion, **one clear "event"** (a division, a merge, a strike…).
- Front-load the action (the strong moment in the first ~3–4 s — I auto-detect & loop it).
- Dark background, high contrast, the cyan/magenta palette.

## The 11 specimens (slug → what the hero shows → prompt seed)
| Slug | Hero subject | Prompt seed (add the style suffix) |
|---|---|---|
| `grayscott` | cell dividing | a single bioluminescent cell pinches in the middle and splits into two daughter cells |
| `rna` | self-copying strand | a glowing helical RNA strand unzips and templates an identical copy of itself |
| `chirality` | mirror molecules | two mirror-image glowing molecules rotate; one ignites gold and dominates as the other dims |
| `coacervate` | droplets merging | glowing oily droplets drift, collide and merge into one larger pulsing proto-cell droplet |
| `code` | code assembling | luminous nucleotide letters snap onto a strand three at a time, spelling a glowing genetic code |
| `natsel` | molecules competing | many glowing molecular chains compete; the brightest replicate and crowd out the fading ones |
| `life` | digital organisms | glowing pixel-organisms swarm, reproduce and die across a dark cellular grid |
| `luca` | ancestor cell | one ancient glowing cell pulses with internal machinery at the root of a branching tree of light |
| `minerals` | clay catalysis | molecules assemble along a glowing crystalline mineral lattice surface |
| `soup` | primordial soup | lightning strikes a dark primordial sea; glowing molecules condense in the turbulent water |
| `vents` | hydrothermal vent | glowing mineral chemistry billows from a dark deep-sea hydrothermal vent chimney |

## How many
- **~3 clips per specimen → 33 total** → ~500 posts via the variant matrix. (Even **1 per specimen** gets us going.)
- More angles/seeds per specimen = more variety. Vary the camera/moment between a specimen's 3 clips.

## How to upload (important — the app renames files)
Uploads arrive with random names, so **filenames can't carry the specimen.** When you upload, just tell me the
**order/grouping** in your message, e.g. *"grayscott ×3, then rna ×3, then vents ×2…"* — I map by upload order.
Easiest: **upload one specimen's clips at a time** and name the specimen in that message. (Optionally drop a
`map.json` = `[{"file":"<path>","specimen":"rna"}, …]` and I'll use it directly.)

## What I do with them
`heropack.py` auto-detects each hero's strongest window, then per hero emits: **blend reveals** (hero → SEM
micrograph of that specimen → split-screen) and **boomerang loops**, across the per-specimen hook bank, web-
encoded + downloadable, into `day_NN/` with a manifest. Add an ElevenLabs VO mp3 per hero (optional) and it's
ducked under the bed. Start the moment your first specimen lands.
