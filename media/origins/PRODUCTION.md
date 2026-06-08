# ORIGINS — *Run the clock back*

A 6-part vertical (9:16) series. Each clip opens on a **photoreal creature**, then
time reverses and the animal **disintegrates into the exact reaction-diffusion or
cellular-automaton pattern that biology used to draw it** — and that pattern, in
turn, melts back into a smooth field of morphogen, "undecided."

The hook is that this is **not a stylization**. Leaf veins, leopard rosettes,
zebra stripes, moth eyespots, pufferfish reticulation, and cone-shell markings are
*literally* the output of the same Turing / cellular-automaton math this whole
`CellAutomata` repo runs. We're just playing the tape backwards.

## Production path (locked)

- **Engine:** ASIM **VEO 3.1** end-to-end, via the whipgen MCP.
- **Per creature:** author a photoreal keyframe → image-to-video reverse-disintegration → retrieve.
- **Format:** 9:16, locked camera, dark "scientific specimen" lighting, no on-screen text (captions added in post).
- **Cost / time:** ~$0.02 keyframe + ~$0.50 video per creature ≈ **$3.1 total**; 15–25 min render each (ASIM runs ~4 in parallel).

### MCP call sequence (fired when the whipgen tools are connected)

```
for each creature:
  1. whipgen_asim_generate_image(simId="343003", prompt=<keyframe>, aspect="9:16")   # author keyframe in video-gym
  2. whipgen_asim_generate_video(simId="343003", prompt=<motion>)                     # VEO 3.1, async 15-25 min
  3. whipgen_asim_watch_last(simId="343003")                                          # block until done
  4. whipgen_asim_review_last(simId="343003")                                         # -> mp4Path (daemon) + storyboard frames
# (whipgen_asim_video_chain collapses 1-4 into one macro call.)
```

> **Retrieval caveat (known):** the daemon is on a separate host with no shared
> filesystem, so finished mp4s live daemon-side. I surface the **storyboard frames**
> `review_last` returns (small, retrievable) as previews, and attempt to pull the
> full masters into the repo where possible. Post-treatment (title card + caption
> beats + ambient drone, reusing `tools/schedule.py`) is applied to any master we
> can land locally.

---

## The six specimens

Each entry: the **science** (what real pattern it is), the **keyframe prompt**
(photoreal still), the **motion prompt** (the reverse-time VEO shot), and the
**caption beats** (added in post, reverse-chronology narration).

### 1 · LEAF — branching veins
**Science.** Leaf venation forms by *auxin canalization*: flow concentrates into
branching channels by positive feedback — a reaction-diffusion-style front frozen
into a tree (Meinhardt; Sachs). No blueprint; the network draws itself.
**Palette.** Backlit green-gold.
**Keyframe.** `Extreme macro studio photograph of a single translucent skeleton leaf, every vein glowing, centered on a pure black background, backlit, ultra-detailed, perfectly symmetrical, razor sharp focus, museum specimen.`
**Motion.** `Locked static camera. Time runs in reverse: the leaf's branching veins slowly retract and dissolve, the tissue disperses into a slow flowing field of reaction-diffusion chemistry, the branching channels un-forming and smoothing into a calm uniform green-gold haze. Particles drift backward and settle. Dark, scientific, elegant, hypnotic, slow motion. No text, no people.`
**Beats.**
1. "A leaf. Every vein exactly in place."
2. "But no hand drew these channels."
3. "Run the clock back — they were *carved by flow*, a reaction canalizing into a tree."
4. "Wind back further, and even the tree dissolves into a smooth, undecided field."

### 2 · LEOPARD — spots
**Science.** Rosettes are a Turing **spot** pattern: a short-range *activator* and a
long-range *inhibitor* settle into evenly spaced dots (Turing 1952; Murray, *How the
leopard got its spots*).
**Palette.** Gold-amber.
**Keyframe.** `Extreme macro studio photograph of leopard fur, dense black rosettes on a golden coat, centered, pure black background, ultra-detailed, shallow depth of field, dramatic raking light, museum specimen.`
**Motion.** `Locked static camera. Time reverses: the leopard's rosettes drift apart, dissolve and disperse into a flowing reaction-diffusion field, the spots spreading out and smoothing into a calm uniform golden haze. Backward-drifting particles. Dark, scientific, elegant, slow motion. No text, no people.`
**Beats.**
1. "The leopard. Every rosette, deliberate."
2. "Except nothing *chose* where they go."
3. "An activator, a faster inhibitor — chemistry spacing the spots. Turing, 1952."
4. "Run it all the way back: once, just a smooth, undecided field."

### 3 · ZEBRA — stripes
**Science.** The *same* Turing machine as the leopard, one diffusion ratio different:
change a single dial and spots become **stripes** (Bard 1981). Orientation is set by
the embryo's timing.
**Palette.** Silver / monochrome.
**Keyframe.** `Extreme macro studio photograph of zebra hide, crisp parallel black-and-white stripes, centered, pure black background, ultra-detailed, sharp, dramatic side light, museum specimen.`
**Motion.** `Locked static camera. Time reverses: the zebra's stripes ripple, break apart, and disperse into a flowing reaction-diffusion field, the bands smoothing into a uniform silver-grey haze. Backward particle drift. Dark, scientific, elegant, slow motion. No text, no people.`
**Beats.**
1. "The zebra. Bars, exact and parallel."
2. "The same machine that spotted the leopard —"
3. "— turned one dial, and spots became stripes."
4. "Before the first stripe: a blank, smooth field."

### 4 · LUNA MOTH — eyespots + wing bands
**Science.** Eyespots are concentric reaction-diffusion **target** patterns: a focus
diffuses morphogens outward in rings (Nijhout's eyespot model). The wing-margin bands
are a stripe Turing field.
**Palette.** Pale jade.
**Keyframe.** `Extreme macro studio photograph of a luna moth wing, pale green, dark concentric eyespots and margin bands, centered on pure black, backlit, ultra-detailed, symmetrical, museum specimen.`
**Motion.** `Locked static camera. Time reverses: the moth's eyespots collapse inward to single points, the wing bands dissolve, the scales disperse into a flowing reaction-diffusion field smoothing to a uniform jade haze. Backward drift. Dark, scientific, elegant, slow motion. No text, no people.`
**Beats.**
1. "The moth's wing. Eyes that never blink."
2. "Each eyespot — a ring of chemistry around a single point."
3. "Collapse the rings, erase the bands —"
4. "— and the wing returns to a smooth, waiting field."

### 5 · PUFFERFISH — reticulation
**Science.** Turing's own example, caught alive: Kondo & Asai (1995) *filmed* the
stripes on real marine fish moving and rearranging like a running reaction-diffusion
simulation. The pufferfish/boxfish maze is a 2D Turing **labyrinth**.
**Palette.** Aqua / teal.
**Keyframe.** `Extreme macro studio photograph of pufferfish skin, golden-brown labyrinthine reticulation, centered, pure black background, ultra-detailed, wet sheen, dramatic light, museum specimen.`
**Motion.** `Locked static camera. Time reverses: the fish's maze-like reticulation flows and rearranges like a living simulation, then disperses and smooths into a uniform aqua haze. Backward drift. Dark, scientific, elegant, slow motion. No text, no people.`
**Beats.**
1. "A pufferfish. A maze with no entrance."
2. "On real fish, these lines have been *filmed moving* —"
3. "— a reaction and a diffusion, computing in living skin. Kondo, 1995."
4. "Still it, smooth it, and only a blank field remains."

### 6 · CONE SHELL — Rule 30 cellular automaton  *(the tie-in)*
**Science.** The pigment pattern of *Conus textile* is a **one-dimensional cellular
automaton**: each row laid down at the growing lip is computed from the row before it
— the same class of rule as Wolfram's **Rule 30**. The shell is a CA's printout in
calcium carbonate (Wolfram, *A New Kind of Science*; Coombes).
**Palette.** Ember / parchment.
**Keyframe.** `Extreme macro studio photograph of a textile cone shell (Conus textile), intricate brown-and-white triangular tent markings, centered, pure black background, ultra-detailed, glossy, dramatic light, museum specimen.`
**Motion.** `Locked static camera. Time reverses: the shell's triangular tent markings resolve row by row into a one-dimensional cellular-automaton spacetime diagram — black-and-white cells flickering along the shell's growing edge — then scatter into a smooth parchment haze. Backward drift. Dark, scientific, elegant, slow motion. No text, no people.`
**Beats.**
1. "A cone shell. Triangles inside triangles."
2. "This isn't decoration — it's a *computer's output*."
3. "Each row computed from the last. A cellular automaton, written in shell."
4. "The same rule we run in code. This is where the whole project began."

---

## Closing card (all six)

> **ORIGINS** — every coat, every wing, every shell ran the same handful of rules.
> · CellAutomata

## Suggested release order

Leaf → Leopard → Zebra → Luna Moth → Pufferfish → **Cone Shell** (finale: the
literal cellular automaton, closing the loop back to the repo's name).
