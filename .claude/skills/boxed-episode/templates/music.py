#!/usr/bin/env python3
"""Assemble the episode score (TEMPLATE; PLAN below is the Ep4 example) (music.wav, 48 kHz stereo, full episode) from the ElevenLabs cues in ../music_el.
Each cue is loudness-matched, placed at its segment start, faded in/out at segment edges, and given a trim."""
import json, os, subprocess, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
EP = os.path.dirname(HERE)
try:
    import imageio_ffmpeg
    FF = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FF = "/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
SR = 48000
TL = json.load(open(os.path.join(EP, "timeline.json")))
DUR = TL["duration"]
L = {l["id"]: l for l in TL["lines"]}
S = {s["id"]: s for s in TL["slots"]}

# cue, start, end (hard stop with fade), fade_in, fade_out, trim dB
PLAN = [
    ("DARK_IN", 0.30, S["TITLE"]["t0"] + 0.05, 1.5, 0.15, -5.0),
    ("TITLE", S["TITLE"]["t0"] - 0.05, L["H01"]["t0"] + 1.2, 0.0, 1.0, 0.0),
    ("TALK_A", L["H01"]["t0"] - 0.4, S["CAVE_IN"]["t0"] + 0.3, 2.0, 0.8, -6.0),
    ("CAVE", S["CAVE_IN"]["t0"] - 0.15, L["H10"]["t0"] + 0.3, 1.5, 0.8, -3.0),
    ("GAMESHOW", S["GAMESHOW_IN"]["t0"] - 0.05, L["Z12"]["t0"] + 0.3, 0.05, 0.6, -1.5),
    ("ESCAPE", L["Z12"]["t0"] - 0.15, S["ASCENT"]["t0"] + 0.2, 1.2, 0.5, -4.5),
    ("ASCENT", S["ASCENT"]["t0"] - 0.1, S["SUNRISE"]["t0"] + 0.3, 0.4, 0.8, -2.0),
    ("SUNRISE", S["SUNRISE"]["t0"] - 0.1, L["H13"]["t0"] + 0.6, 0.2, 1.0, 0.0),
    ("CLIFF", L["Z20"]["t1"] - 0.25, S["AD_IN"]["t0"] + 0.3, 0.0, 0.2, -1.0),
    ("AD", S["AD_IN"]["t0"] + 0.1, S["BUMPER"]["t0"] + 0.1, 0.2, 0.5, -3.0),
    ("BUMPER", S["BUMPER"]["t0"] - 0.02, S["BUMPER"]["t1"] + 0.6, 0.0, 0.5, -1.0),
    ("TALK_B", S["BUMPER"]["t1"] + 0.3, L["Z22"]["t0"] + 7.4, 1.5, 1.5, -6.0),
    ("RETURN", L["Z22"]["t0"] + 7.1, L["Z26"]["t1"] + 0.4, 2.0, 1.5, -4.0),
    ("MODERN", L["H20"]["t0"] - 0.2, L["H23"]["t0"] + 0.05, 0.8, 0.3, -5.0),
    ("PANIC", L["H23"]["t0"] - 0.03, L["Z29"]["t0"] + 0.2, 0.05, 0.5, -5.0),
    ("WISDOM", L["Z29"]["t0"] - 0.15, S["TURN"]["t0"] + 0.2, 1.5, 0.6, -5.5),
    ("TURN", S["TURN"]["t0"] - 0.1, S["OUTSIDE"]["t0"] + 0.1, 0.2, 0.1, -1.0),
    ("OUTSIDE", S["OUTSIDE"]["t0"] - 0.05, S["ENDCARD"]["t0"] + 0.3, 0.0, 1.5, 1.0),
    ("OUTRO", S["ENDCARD"]["t0"] - 0.1, S["STINGER"]["t0"] + 0.9, 0.6, 1.6, -3.0),
]


def load(name):
    raw = subprocess.run([FF, "-v", "quiet", "-i", os.path.join(EP, "music_el", f"{os.path.basename(EP)}_M_{name}.mp3"), "-ar", str(SR), "-ac", "2", "-f", "f32le", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)


def loud_rms(x):
    m = x.mean(1)
    hop = SR // 10
    r = np.array([np.sqrt(np.mean(m[i:i + hop] ** 2)) for i in range(0, len(m) - hop, hop)])
    top = np.sort(r)[int(len(r) * 0.4):]
    return float(np.sqrt(np.mean(top ** 2)) + 1e-9)


def main():
    N = int(DUR * SR)
    out = np.zeros((N, 2))
    ref = 10 ** (-20 / 20)
    for name, t0, t1, fi, fo, trim in PLAN:
        x = load(name)
        x = x * (ref / loud_rms(x)) * 10 ** (trim / 20)
        i0 = int(round(t0 * SR))
        n = min(len(x), int((t1 - t0) * SR), N - i0)
        seg = x[:n].copy()
        if fi > 0:
            k = min(n, int(fi * SR)); seg[:k] *= np.linspace(0, 1, k)[:, None] ** 1.5
        if fo > 0:
            k = min(n, int(fo * SR)); seg[-k:] *= np.linspace(1, 0, k)[:, None] ** 1.5
        out[i0:i0 + n] += seg
        print(f"  {name:10s} {t0:7.2f} -> {t0 + n / SR:7.2f}  ({len(x) / SR:5.1f}s cue, trim {trim:+.1f} dB)")
    pk = np.abs(out).max()
    if pk > 0.95:
        out *= 0.95 / pk
    a = (np.clip(out, -1, 1) * 32767).astype("<i2")
    with wave.open(os.path.join(HERE, "music.wav"), "wb") as f:
        f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR); f.writeframes(a.tobytes())
    print("MUSIC ->", os.path.join(HERE, "music.wav"), f"peak {pk:.2f}")


if __name__ == "__main__":
    main()
