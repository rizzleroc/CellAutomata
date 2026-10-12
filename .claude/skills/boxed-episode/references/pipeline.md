# BOXED pipeline — exact steps

Conventions: `$B` = the working root from `engine/setup.sh` (normally `<session scratchpad>/boxed`); episode folder
`$B/ep<N>/` (lower-case, e.g. `ep5`); run Python as `cd $B && LD_LIBRARY_PATH=$B/lib python3 ...`; `SK=.claude/skills/boxed-episode`.
Rough wall-clock for an 11-minute episode: script 30 min · voices 25 min · timeline/cues/shot list 40 min ·
shots 2–3 h (parallel agents) · audio 30 min · render 45–60 min · encode + QC 20 min.

## 0. Layout
```
$B/
  eng/                     engine package (from the skill) + shots_ep<N>.py, shots_ep<N>_base.py, shots_ep<N>_<owner>.py
  fonts/  lib/             fetched fonts, libEGL/libGLESv2 symlinks
  render.py  render_segs.py  mix.py  finalize.sh     (from templates/, EPN set to ep<N>)
  ep<N>/
    make_script.py  script.json  BRIEF.md  SHOTS_BY_OWNER.md  make_cues.py  cues.json
    vo/ (raw ElevenLabs)  vo_wav/ (trimmed 48 kHz)  music_el/  sfx_el/
    tools/ (build_timeline.py, shotlist.py)   audio/ (music.py, sfx.py -> music.wav, sfx.wav)
    timeline.json  lipsync.json  acting.json
    out/ (stills, contact sheets, segs/, video.mp4, mix.wav, boxed_ep<N>.srt, boxed_ep<N>_part*.mp4)
```
```bash
bash $SK/engine/setup.sh && export B=...   # once per container
N=5; mkdir -p $B/ep$N/{tools,audio,vo,out}
cp $SK/templates/make_script.py $SK/templates/make_cues.py $B/ep$N/
cp $SK/templates/build_timeline.py $SK/templates/shotlist.py $B/ep$N/tools/
cp $SK/templates/music.py $SK/templates/sfx.py $B/ep$N/audio/
cp $SK/templates/render.py $SK/templates/render_segs.py $SK/templates/mix.py $SK/templates/finalize.sh $B/
sed -i "s/EPN = \"ep5\"/EPN = \"ep$N\"/" $B/render.py $B/render_segs.py $B/mix.py
cp $SK/templates/shots_epN_base.py $B/eng/shots_ep${N}_base.py && sed -i "s/EPN = \"ep5\"/EPN = \"ep$N\"/" $B/eng/shots_ep${N}_base.py
cp .claude/skills/video-production/scripts/{grab.py,sheet.py} $B/ep$N/tools/
```

## 1. Script → `script.json`
Edit `make_script.py`: `(id, speaker, subtitle text, tts text)`. Speakers HOST / GUEST / AUD / ANN / PLANET (voice
IDs in the bible). ids: C## cold open, H## host, Z## Zee, G## Gary, S## segment (game show etc.), A## ad, P## planet.
`python3 ep$N/make_script.py` prints lines / words / estimated speech. Budget: eleven_v3 with tags speaks
≈2.3–2.5 words/s → 1,250 words ≈ 510–540 s of speech → an 11:00 show. Numbers/dates spelled out in `tts`
("three hundred seventy-five B.C."), shown normally in `text`.

## 2. Voices (whip MCP → ElevenLabs)
Call `whipgen_help` once per session, `whipgen_status` to confirm the daemon. Then for every line:
```
mcp__whip__whipgen_elevenlabs_speak(text=<tts>, voiceId=<voice>, modelId="eleven_v3", stability=0.5,
    similarityBoost=0.75, name="ep<N>_<ID>", returnBytes=true [, outputFormat="pcm_24000" for lines under ~4 s])
```
Fire 6–8 calls per message. Each result "exceeds maximum allowed tokens" and spills to
`~/.claude/projects/<proj>/<session>/tool-results/*.txt` — that is the success path. Harvest after each batch:
`python3 ep$N/tools/grab.py ep$N/vo ep${N}_` (PCM is wrapped at 24 kHz by default). Check:
`ls ep$N/vo | wc -l` == line count, `md5sum ep$N/vo/* | sort | awk '{print $1}' | uniq -d` prints nothing.

## 3. Timeline
Edit `SEQ` in `tools/build_timeline.py`: `("line", id, gap_after)` and `("slot", NAME, seconds)` for montage beats
with no dialogue (COLD_IN, TITLE, LIGHTS_UP, APPLAUSE, CAVE_IN, GAMESHOW_IN, AD_IN, BUMPER, OUTSIDE, ENDCARD,
STINGER, BLACK...). `FLEX` weights decide which slots stretch/shrink to hit `TARGET`. Run it; it trims + resamples
VO to `vo_wav/` (48 kHz mono), tightens inner pauses > 0.75 s to 0.6 s, and prints slot lengths. If `stretch` is
strongly negative, raise TARGET (11:00) or cut lines — never let the finale slot drop under ~20 s.

## 4. Lip sync + acting
```bash
python3 -c "import sys; sys.path.insert(0,'.'); from eng import lipsync; lipsync.build('ep$N/vo_wav','ep$N/timeline.json','ep$N/lipsync.json')"
python3 ep$N/make_cues.py
python3 -c "import sys; sys.path.insert(0,'.'); from eng import acting; acting.precompute('ep$N/timeline.json','ep$N/lipsync.json','ep$N/acting.json','ep$N/cues.json')"
```
`make_cues.py` holds the gesture library (reusable: desk, ask, lean_in, card, read, point_up, spread, chin, wave,
self, panic, welcome, to_audience, whisper, sigh, dreamy, bow, bunny, behind, clutch, flat_rect, mic / lap, wag,
pinch, paper, shrug, temple, open_arms, explain, explain2, count, jar, point_up, hands_head, hold_box, peek, heart,
somber, two, dot, one, gentle, big, wave_hi, conduct, chain, wall, puppet, flicker, turn_around), `HAND_ABS`
directions for new gestures, `CUES` (line, fraction, actor, gesture) and `REACT` (line, f0, f1, actor, overrides —
face modes, glitch, pupil, brows, smile, lid). Then measure arm jumps (should be continuous swings, no single-drawing
snaps > 40° modulo 360).

## 5. Shot list + per-owner sheets
Edit `SHOTS` in `tools/shotlist.py`: `(id, anchor "L:<line>" | "S:<slot>", owner, description)`; each shot runs to
the next. Owners: `main` (you) + one per montage sequence. Run it, then
`cp $SK/templates/shots_by_owner.py $B/ && python3 shots_by_owner.py ep$N` → `ep<N>/SHOTS_BY_OWNER.md` (each owner's
shots with the dialogue lines inside them and shot-relative times).

## 6. Base module + world kit
`eng/shots_ep<N>_base.py`: keep the generic helpers (loud_at, vis_at, line_at, spk_loud, gary, studio, caption,
thought_bubble, vignette, darkness, firelight...), replace THE CAVE KIT with this episode's environment kit
(backgrounds + reusable props/creatures in house style) and test-render it on a contact sheet BEFORE briefing agents.

## 7. Brief + shot authors
Fill `templates/BRIEF.md` → `ep<N>/BRIEF.md` (episode synopsis, the kit, any special rules). Spawn one Agent per
owner, all in ONE message, `subagent_type: "boxed-shot-author"` (or general-purpose with the agent file's text),
`run_in_background: true`, prompt = "read BRIEF.md + SHOTS_BY_OWNER.md (owner X); write ONLY eng/shots_ep<N>_X.py;
shots: <per-shot creative direction keyed to the line timings>". 45–80 s of screen time per agent works well.

## 8. Main unit
`eng/shots_ep<N>.py` (`from .shots_ep<N>_base import *`): cold open, title, talk-show beats (`studio(...)` with
camera moves via `cam_lerp`), cutaways to Gary (`audience_cu`), host crisis (face modes + glitch + set effects), tag,
endcard, stinger. Use `engine/examples/shots_ep4.py` as the pattern library (light_mask, dark_stage, sunny_set...).
Stills: `python3 render.py --stills 5 13 16.5 ... --out ep$N/out/main` → `python3 ep$N/tools/sheet.py ep$N/out/main ep$N/out/main/sheet` → Read.

## 9. Music + SFX + mix
- Music: one `whipgen_elevenlabs_music(prompt, musicLengthMs, name="ep<N>_M_<CUE>", returnBytes=true)` per cue
  (4–5 per message; ~8–40 s each; up to 100 s per call works). Harvest: `grab.py ep$N/music_el ep${N}_M_`.
  Place with `PLAN` in `audio/music.py` (cue, start, end, fade in, fade out, trim dB) → `audio/music.wav`.
- SFX: `whipgen_elevenlabs_sound_effects(text, durationSeconds, name="ep<N>_S_<name>", returnBytes=true
  [, outputFormat="pcm_24000" for < 3 s])`. Harvest with `grab.py ep$N/sfx_el ep${N}_S_ --rate 48000` (SFX PCM comes
  back at 48 kHz). Place with `cues()` in `audio/sfx.py` (`c(name, t, dur, gain)`, `bed(name, a, b)` loops) → `sfx.wav`.
- `python3 mix.py --music ep$N/audio/music.wav --sfx ep$N/audio/sfx.wav` → `ep$N/out/mix.wav` + `boxed_ep<N>.srt`.

## 10. Render
```bash
nohup python3 render_segs.py --owners main --workers 2 > ep$N/out/segs_main.log 2>&1 &   # early, while agents work
python3 render_segs.py --owners cave,game --workers 4          # as modules are approved (skips finished segments)
python3 render_segs.py --shots T012_cave_reveal               # re-render one shot after a fix
python3 render_segs.py --concat                               # -> ep$N/out/video.mp4
```
≈1 s per drawing per worker; 11:00 = 7,920 drawings. Watch `df` (segments are ~1–2 MB/s of video).

## 11. Deliver
`bash finalize.sh ep$N "0 113.66 part1" "113.66 219.35 part2" ...` (split at shot starts, ~110 s per part) →
`boxed_ep<N>_part*.mp4` each < 29.5 MB. Extract a frame from each part into a contact sheet and LOOK. Send with
`SendUserFile` (all parts + `.srt`, `display: "attach"` for the srt), give runtime + highlights, offer revisions,
and offer to commit engine/skill improvements (ask first; feature branch only; draft PR).
