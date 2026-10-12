# BOXED — series bible

## The show
- **Premise:** a late-night talk show "broadcast from inside the box". The host is literally a television; the guest
  Zee is a simulant; the studio floats in a psychedelic cosmos; the audience is a crowd of eyeball creatures.
- **Each episode** adapts ONE viral idea into talk-show comedy + montage set pieces. The guest explains, the host
  reacts / misunderstands / panics, Gary heckles from the audience, the montages visualise the idea with dream logic.
- **Tone:** big-hearted, absurd, smart. Philosophy delivered accurately (quote the source, word for word where it
  matters), jokes on every beat, one genuinely moving moment, one comic personal crisis for the host, a musical or
  euphoric finale, sign-off "Stay boxed!".
- **Runtime:** 10:00 (the user asked for "10 mins" in Ep3); 11:00 is fine when speech runs long (Ep4). 16:9 1080p24.

## Episode log
| # | Title | Source | Runtime | Notable devices |
|---|-------|--------|---------|-----------------|
| 1 | How to Hack the Simulation | Roman Yampolskiy on Lex Fridman (host/guest roles) | short | the format is born; Zee's paper/jar/box props |
| 2 | One in Billions | Elon Musk, Code Conference 2016 ("one in billions" answer) | ~5 min | Gary debuts (audience mic); Pong/evolution montage; vertical cut + SRT; arms IK rewrite after user feedback |
| 3 | The Dream of Life | Alan Watts' thought experiment, hide-and-seek, "you were supposed to dance" | 10:00 | cold open with sleeping host; dream montages; infomercial ad break; the planet speaks; dance finale; 6 parts |
| 4 | The Cave | Plato, *Republic* VII (c. 375 BC), quotes after Jowett (1871) | 11:00 | dark-studio cold open + hand-shadow BUNNY gag; "Guess That Shadow!" game show; Cave Phone Pro ad; host realises he IS the cave wall (PROPERTY OF THE CAVE sticker on his back); Socrates on a Greek vase; sunrise flower parade; post-credits bunny; 7 montage authors + main unit; delivered in 7 dialogue-safe parts |

## Episode structure (Ep3/Ep4 shape — reuse it)
| Block | Length | Notes |
|-------|--------|-------|
| Cold open | 25–35 s | a gag that sets up the theme (sleeping host; studio in the dark) → "Roll the titles!" |
| Title card | ~8 s | BOXED + EPISODE N + title, themed to the episode; TITLE music sting |
| Intro | ~50 s | host welcome (always a "I'm a television" joke), recap of the season, guest welcome + applause |
| Act 1–2 | 3–4 min | Zee explains in beats; each beat cuts to a montage set piece under her VO, back to the studio for host reactions |
| Cliffhanger → ad break | 35–40 s | "Not quite." / "We'll be right back!" → a parody commercial (announcer voice), Gary testimonial |
| Bumper | 4 s | BOXED station ident |
| Act 3 | 2–3 min | the dark turn (consequences) |
| The host's crisis | ~1 min | the idea applies to HIM (he's a TV) — the comedy peak, face modes + glitches |
| Resolution | ~1 min | the wisdom, said simply; the visual metaphor made literal |
| Finale | 25–40 s | music-driven euphoric set piece (dance, sunrise parade) |
| Tag + sign-off | ~20 s | Gary callback, host thanks, Zee's last word, "And stay boxed!" |
| Endcard + stinger | 10 s + ~7 s | credits incl. source + "voices, music & sound generated with ElevenLabs"; a post-credits callback |

## Cast
### HOST (spk `HOST`)
- **Design:** lanky MC with a **teal CRT TV head** (case `PAL teal` with `tealdk` shading + stipple, orange knobs,
  grille, antenna dome, two silver antennae with orange balls); dark screen `(16,34,52)` with a **phosphor line-art
  face** `PHOS (190,255,214)` (eyes, brows, lip-synced mouth), scanlines, a rolling bar, occasional glitch. **Magenta
  tux** with darker lapels + yellow piping, white shirt V, **yellow bowtie with an orange knot**, gold buttons,
  dark cable neck, blue trousers, white cartoon **gloves** with cuffs. `draw_host` (`eng/cast.py`), head scale 1.12.
- **Face modes** (`face=`): normal, sleep (Z's), static, heart, me (tiny TV on his TV), spiral, x, grid (screens
  inside screens — "I'm a flat rectangle"), knife (shopping channel), wave, chord ("BWAAAM!"); `glitch` 0..1.
- **Voice:** ElevenLabs `iP95p4xoKVk53GoZ742B` (showman, quick, insecure). Mix chain = "TV speaker" EQ + small echo.
- **Character:** sincere showman, insecure about being a television ("My doctor says I should get outside more, but
  I'm not weatherproof"), panics loudly, deadpans "Honestly? Relatable."

### ZEE (spk `GUEST`)
- **Design:** violet simulant, **round head** (`HEAD_K 1.17`) with a **magenta hair cap and scalloped fringe**, two
  antennae with **yellow balls**, **enormous teal eyes** (dark crescent, big pupil, two highlights) under **heavy
  violet lids** (`lid` 0.32 default), lashes at the outer corners, brows on the fringe, pink blush ovals with dots,
  freckles; **cream turtleneck** with an **orange triangle + eye** emblem; **orange bell-bottoms**, acid-green
  sneakers; violet rubber-hose arms with cream sleeves; four-finger mitten hands. `draw_zee` (`eng/zee.py`).
- **Voice:** `cgSgspJ2msm6clMCkdW9` (warm, calm, playful, perfect deadpan). Clean chain.
- **Character:** the wise one; explains simply; teases the host kindly ("You're a very efficient cave.").

### GARY (spk `AUD`)
- **Design:** a big eyeball (white with red veins, teal iris, black pupil, violet lid) on a **striped cream sweater
  (orange stripes) with a red "G"**; little mouth under the iris; sits in the eyeball audience; mic optional.
  When he stands or walks: **cream rubber-hose legs and red sneakers** (the standard since Ep4), white four-finger
  hands. Seated in the audience: `gary(cv, x, y_eye, s, T)` (`eyeball_creature`, mouth auto-synced). Anything more
  (standing, walking, turning, gestures, tears, spiral/heart/$ eyes, sunglasses): `gary_full(cv, x, floor_y, s, T,
  **pose)` = `eng/gary.py draw_gary`. Never a home-made copy (Ep4's authors built five, with five kinds of legs).
- **Voice:** `rHWSYoq8UlV0YIBKMryp` (earnest, excitable). Chain = handheld audience mic + room echo.
- **Character:** sweet, literal, over-invested; gets the episode's guest role when the idea needs a "volunteer"
  (Ep4: the freed prisoner; sunglasses at the end).

### Others
- **ANNOUNCER** (`ANN`) `nPczCjzI2devNBz1zQrb` — infomercials; broadcast compression.
- **THE PLANET** (`PLANET`) `pqHfZKP75CvOlQylNhV4` — the ringed orange sky planet with heavy orange lids; pitched
  down + cosmic echo; one line per episode at most (Ep4: played the sun — "Oh. Hey, Gary.").
- **Eyeball audience** — rows of dark round creatures with pastel eyes (`audience_rows`); Ep4 chained them as the
  prisoners (`prisoner()` in the Ep4 cave kit).
- **Sky regulars** — skull moon, eye-bats, jellyfish, a wizard, a pyramid with an eye and rays, a mushroom, an
  eyeball walker, a small acid-green planet (all in `eng/world.py`, placed by `sets.cosmos`).

## The set (`sets.talkshow`)
Floating island stage (violet top, orange/red/maroon/night strata with drips) over the **cosmos** sky (dusk bands of
night/violet/magenta/orange/yellow, rotating sunburst, stars, floaters, a striped cosmic ribbon, hills); the
**BOXED sign** with a pink glow; host **desk** (orange panelled pill, red end, yellow eye emblem, long yellow plank top)
with a teal **mug**; orange **couch** with a red cushion (back drawn before Zee, front after); teal stippled **side
table** + pink **lava lamp**; pink **lamp**; **plant** with eyeball flowers; rainbow rug.
Standard placement: `HOST_POS = (640, 930, s=0.78, legs=False)`, `GUEST_POS = (1350, 975, s=0.72, legs=False)`.
Cameras (`Cam` dicts): `CAM_WIDE (0, 30, 1.02)`, `CAM_TWO (40, 40, 1.3)`, `CAM_HOST (-320, -20, 1.85)`,
`CAM_ZEE (390, 40, 1.85)`. Screen position of a world point: `sets.Cam(None, cam).to_screen(X, Y, parallax)`.

## Palette (`eng.core.PAL`)
ink (20,10,26) · white (255,252,240) · cream (255,238,196) · magenta (255,46,166) · hotpink (255,120,196) ·
violet (126,56,255) · vdark (78,28,170) · blue (34,96,255) · deepblue (22,30,120) · night (26,10,58) · void (14,6,34) ·
orange (255,120,24) · red (214,22,48) · maroon (110,8,38) · teal (28,226,200) · tealdk (0,150,150) · acid (170,255,0) ·
yellow (255,214,0) · gold (255,170,30) · lilac (200,150,255) · mint (150,255,210) · peach (255,176,120).
Palettes of the sky: `dusk` (default), `deep`, `acid`.

## Lettering (`eng.letters.paint_text`)
shrik (Shrikhand — the BOXED logo and big titles, drips), londrina (captions), bangers (comic / game show / labels),
marker (handwritten credits), caveat (asides), chewy, bagel, titan, wet, londrina_r. Always ink outline + shadow.

## Title card + endcard conventions
- **Title:** big "BOXED" (shrik, yellow, magenta shadow, drips) over halo rings in a themed backdrop; "EPISODE <N>"
  (londrina, cream); the episode title in multi-colour fills; sparkles; TITLE music (70s psychedelic funk).
- **Endcard:** pink sunburst, BOXED + "EPISODE N · TITLE", credits ("Adapted from <source>", "Original characters ·
  voices, music & sound generated with ElevenLabs"), "STAY BOXED." (acid green), Zee + host (+ Gary) waving.

## Running gags
"I'm a television" · Gary in the audience · the planet's sleepy face · a parody ad every episode · "Stay boxed!" ·
recaps of previous episodes · Ep4's hand-shadow bunny (Gary's best friend, RIP) — bring it back.

## House music prompts (ElevenLabs music; keep the sonic identity)
- **TITLE (11 s):** "Instrumental TV show title theme, 70s psychedelic funk: punchy wah-wah guitar riff, groovy bass,
  Hammond organ swirl, bright brass fanfare, tight funk drums. Bold, colorful, Adult Swim cartoon talk show opening.
  Builds fast and ends on a big final brass hit with cymbal. No vocals."
- **TALK bed (30–80 s):** "Instrumental laid-back late-night talk show lounge jazz bed: brushed drums, warm upright
  bass walking slowly, mellow Rhodes electric piano comping, soft muted trumpet hints. Low intensity background music
  under talking, relaxed and witty, steady, no big melodies. No vocals."
- **AD (40 s):** "Instrumental cheesy 1980s TV infomercial music: upbeat corporate synth-pop, bright synth brass stabs,
  slap bass, gated drums, sparkly chimes, relentlessly optimistic product commercial jingle. No vocals."
- **BUMPER (5 s):** "Instrumental short funky TV station ident sting, about 4 seconds: a slick wah-wah guitar lick,
  organ stab and a snappy drum fill, ending abruptly on a punchy hit. Retro 70s cartoon network bumper. No vocals."
- **OUTRO (16–40 s):** "Instrumental warm closing theme of a late-night cartoon talk show: mellow funk groove with
  Rhodes piano, gentle wah guitar and soft brass, happy and satisfied, ... No vocals."
- Episode-specific cues are described by mood + instruments + arc ("builds to...", "ends with...") + "No vocals".

## House SFX set (ElevenLabs sound effects)
applause, cheer, laugh_big, laugh_small, ooh, aww, gasp, static (CRT burst), glitch, tv_on, lights_on, spotlight,
sparkle, ding / buzzer / drumroll / kaching (game show + ads), scratch (record), slide (whistle boing), plus the
episode's world ambiences (Ep4: fire, drips, cave_wind, chains, echo_voices, drag, rumble, gong, morning, night, water,
pings, mock laughter).
