#!/usr/bin/env python3
"""Mux per-reel voiceover WAVs into the reels, ducking the ambient bed.

Expects narration WAVs at marketing/social/voiceover/wav/reel_NN.wav (one per
reel index) — produce them with VibeVoice via generate_vibevoice.sh, or any
TTS. Outputs voiced reels to marketing/social/reels_voiced/.

The VO is loudness-normalised and sits on top of the original ambient bed,
which is lowered. If the VO is longer than the reel, the final video frame is
held (clone) so nothing is cut off.

Usage:
  python3 marketing/social/voiceover/add_voiceover.py            # all available
  python3 marketing/social/voiceover/add_voiceover.py --only 0,5
"""
from __future__ import annotations
import argparse
import glob
import os
import re
import subprocess
import sys
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
REELS = os.path.join(ROOT, "marketing", "social", "reels")
WAVS = os.path.join(ROOT, "marketing", "social", "voiceover", "wav")
OUT = os.path.join(ROOT, "marketing", "social", "reels_voiced")
BED_VOL = 0.28          # ambient bed level under the voice
VO_DELAY = 0.30         # seconds before the voice starts
DUR_RE = re.compile(r"Duration: (\d+):(\d+):(\d+\.\d+)")


def duration(path: str) -> float:
    p = subprocess.run([FF, "-hide_banner", "-i", path], capture_output=True, text=True)
    m = DUR_RE.search(p.stderr)
    if not m:
        raise RuntimeError(f"no duration for {path}")
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


def reel_for_index(i: int) -> str | None:
    hits = glob.glob(os.path.join(REELS, f"reel_{i:02d}_*.mp4"))
    return hits[0] if hits else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    idxs = ([int(x) for x in args.only.split(",") if x.strip() != ""]
            if args.only else list(range(30)))
    done = fail = skip = 0
    for i in idxs:
        reel = reel_for_index(i)
        wav = os.path.join(WAVS, f"reel_{i:02d}.wav")
        if not reel or not os.path.exists(wav):
            print(f"[skip] {i:02d}: missing {'reel' if not reel else 'wav'}")
            skip += 1
            continue
        out = os.path.join(OUT, os.path.basename(reel))
        vdur, adur = duration(reel), duration(wav)
        vo_end = VO_DELAY + adur + 0.4
        pad = max(0.0, vo_end - vdur)
        vchain = f"[0:v]tpad=stop_mode=clone:stop_duration={pad:.2f}[v]" if pad > 0.05 else "[0:v]copy[v]"
        af = (
            f"[0:a]volume={BED_VOL}[bed];"
            f"[1:a]aresample=44100,adelay={int(VO_DELAY*1000)}|{int(VO_DELAY*1000)},"
            f"loudnorm=I=-15:TP=-1.5:LRA=11,apad=pad_dur=0.3[vo];"
            f"[bed][vo]amix=inputs=2:duration=longest:normalize=0[a]"
        )
        try:
            subprocess.run(
                [FF, "-y", "-hide_banner", "-loglevel", "error",
                 "-i", reel, "-i", wav,
                 "-filter_complex", f"{vchain};{af}",
                 "-map", "[v]", "-map", "[a]",
                 "-c:v", "libx264", "-crf", "20", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                 "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out],
                check=True, capture_output=True, text=True)
            mb = os.path.getsize(out) / 1e6
            print(f"[ok]   {i:02d} {os.path.basename(out)}  vo={adur:.1f}s vid={vdur:.1f}s -> {mb:.1f}MB")
            done += 1
        except subprocess.CalledProcessError as e:
            print(f"[FAIL] {i:02d}: {e.stderr[-400:]}")
            fail += 1
    print(f"\nvoiced={done} skipped={skip} failed={fail}  -> {OUT}")
    if fail:
        sys.exit(2)


if __name__ == "__main__":
    main()
