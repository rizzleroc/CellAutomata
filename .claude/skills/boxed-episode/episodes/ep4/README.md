# BOXED Episode 4 — "THE CAVE" (source)

Plato's Allegory of the Cave (*Republic* VII, c. 375 BC; quotes after Jowett, 1871). 11:00, 55 shots, 93 lines,
delivered on 2026-10-12 as 7 MP4 parts + an SRT. Everything needed to re-render, fix or re-cut the episode is here
except the media (ElevenLabs voice/music/SFX audio and rendered video), which is never committed.

## What's here (laid out like `$B`)
| Path | What |
| --- | --- |
| `eng/shots_ep4_base.py` | episode helpers + THE CAVE KIT (cave cross-section, wall view, prisoners, carriers, fire...) |
| `eng/shots_ep4.py` | the main unit (32 shots: cold open, title, talk beats, the host's meltdown, tag, endcard, stinger) |
| `eng/shots_ep4_{cave,game,escape,sun,ad,return,out}.py` | the 7 montage modules written by parallel shot authors |
| `render4.py`, `render_segs.py` | renderer (stills / ranges / POST hooks / wipes) and the resumable per-shot segment runner |
| `mix4.py`, `finalize4.sh` | the mix (voice chains, ducking, loudnorm, SRT) and the 7-part delivery encode |
| `ep4/make_script.py` → `script.json` | the script: 93 lines with eleven_v3 delivery tags and subtitle text |
| `ep4/timeline.json` | line timings, named slots and the 55-shot list (660 s) |
| `ep4/lipsync.json` | per-line visemes + loudness at 24 fps (derived from the audio) |
| `ep4/make_cues.py` → `cues.json` | gestures, listener reactions and hand directions |
| `ep4/BRIEF.md`, `ep4/SHOTS_BY_OWNER.md` | the shot authors' brief and per-owner shot sheets |
| `ep4/tools/`, `ep4/audio/` | timeline + shot-list builders; music (`music4.py`) and SFX (`sfx4.py`) placement plans |

`acting.json` (11 MB) is not committed: it regenerates byte-identical from the timeline, lip sync and cues.

## Restore and re-render
```bash
bash .claude/skills/boxed-episode/engine/setup.sh          # -> $B: engine, fonts, libs, deps
E=.claude/skills/boxed-episode/episodes/ep4
cp $E/eng/*.py $B/eng/ && cp $E/render4.py $E/render_segs.py $E/mix4.py $E/finalize4.sh $B/
mkdir -p $B/ep4 && cp -r $E/ep4/* $B/ep4/
cd $B && LD_LIBRARY_PATH=$B/lib python3 -c "from eng import acting; acting.precompute('ep4/timeline.json', 'ep4/lipsync.json', 'ep4/acting.json', 'ep4/cues.json')"
LD_LIBRARY_PATH=$B/lib python3 render4.py --stills 30 200 600 --out ep4/out/check   # spot-check
python3 render_segs.py --owners main,cave,game,escape,sun,ad,return,out --workers 4 && python3 render_segs.py --concat
```

## Audio (not committed)
The mix needs the ElevenLabs sources: `ep4/vo/` (93 lines), `ep4/music_el/` (19 cues), `ep4/sfx_el/` (33 samples).
While the Ep4 session's project folder exists, re-harvest them from its `tool-results/_done/` spills with
`video-production/scripts/grab.py` (`--rate 48000` for SFX), then `mix4.py --music ep4/audio/music.wav --sfx
ep4/audio/sfx.wav` after `audio/music4.py` and `audio/sfx4.py`. Re-recording the voices instead gives new takes with
new timings: the timeline, lip sync and acting track would have to be rebuilt and the shots re-timed.

## Delivery record
Cuts (from `plan_parts.py`, never mid-line): 0 · 91.17 · 195.92 · 287.08 · 385.08 · 495.33 · 586.75 · 660 s.
Parts 28.7–29.0 MB, loudness ≈ −15 LUFS, true peak −2.3 … −3.0 dBTP after limiting.
