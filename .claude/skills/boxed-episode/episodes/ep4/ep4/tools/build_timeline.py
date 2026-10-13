#!/usr/bin/env python3
"""Ep4 timeline: trim + resample every VO clip to 48 kHz mono WAV (ep4/vo_wav/<ID>.wav), then lay the show out from
SEQ (lines with the gap that follows them, and named no-dialogue slots), stretching the flexible slots so the episode
lands on TARGET seconds. Writes ep4/timeline.json with lines[], slots[] and duration."""
import json, os, subprocess, sys
import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
EP = os.path.dirname(HERE)
FF = "/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
SR = 48000
TARGET = 660.0
SEQ = [
    ("slot", "COLD_IN", 3.0),
    ("line", "C01", 0.35), ("line", "C02", 0.3), ("line", "C03", 0.5), ("line", "C04", 0.35), ("line", "C05", 0.55),
    ("line", "C06", 0.5), ("line", "C07", 0.25),
    ("slot", "TITLE", 8.0),
    ("slot", "LIGHTS_UP", 2.0),
    ("line", "H01", 0.5), ("line", "H02", 0.4), ("line", "H03", 0.2),
    ("slot", "APPLAUSE", 2.6),
    ("line", "Z01", 0.3), ("line", "G00", 0.6), ("line", "H04", 0.3), ("line", "Z02", 0.5),
    ("slot", "CAVE_IN", 3.0),
    ("line", "Z03", 0.4), ("line", "Z04", 0.4), ("line", "H05", 0.3), ("line", "Z05", 0.35), ("line", "Z06", 0.4),
    ("line", "H06", 0.3), ("line", "Z07", 0.4), ("line", "Z08", 0.5), ("line", "H07", 0.6), ("line", "Z09", 0.9),
    ("line", "H08", 0.4), ("line", "Z10", 0.4), ("line", "H09", 0.3),
    ("slot", "SHADOWPLAY", 6.0),
    ("line", "Z11", 0.35), ("line", "H10", 0.3),
    ("slot", "GAMESHOW_IN", 3.5),
    ("line", "S01", 0.5), ("line", "S02", 0.5), ("line", "S03", 0.4), ("line", "S04", 0.8),
    ("line", "Z12", 0.35), ("line", "H11", 0.3),
    ("slot", "SPOTLIGHT", 2.0),
    ("line", "G01", 0.4), ("line", "Z13", 0.3), ("line", "G02", 0.4), ("line", "Z14", 0.35), ("line", "G03", 0.3), ("line", "H12", 0.5),
    ("line", "Z15", 0.2),
    ("slot", "ASCENT", 8.0),
    ("line", "G04", 0.5), ("line", "Z16", 0.4), ("line", "Z17", 0.4), ("line", "Z18", 0.3),
    ("slot", "SUNRISE", 5.0),
    ("line", "P01", 0.5), ("line", "G05", 0.8), ("line", "Z19", 0.5), ("line", "H13", 0.4), ("line", "Z20", 0.6), ("line", "H14", 0.2),
    ("slot", "AD_IN", 2.0),
    ("line", "A01", 0.4), ("line", "A02", 0.4), ("line", "A03", 0.4), ("line", "G06", 0.4), ("line", "A04", 0.6),
    ("slot", "BUMPER", 4.0),
    ("line", "H15", 0.35), ("line", "Z21", 0.35), ("line", "H16", 0.35), ("line", "Z22", 0.3),
    ("slot", "RETURN", 3.0),
    ("line", "S05", 0.4), ("line", "G07", 0.5),
    ("slot", "LAUGH", 2.0),
    ("line", "Z23", 0.4), ("line", "H17", 0.5), ("line", "Z24", 0.5), ("line", "H18", 0.6), ("line", "Z25", 0.7),
    ("line", "H19", 0.6), ("line", "Z26", 1.0),
    ("line", "H20", 0.3),
    ("slot", "MODERN", 3.0),
    ("line", "H21", 0.4), ("line", "H22", 0.4), ("line", "Z27", 0.4), ("line", "H23", 0.3), ("line", "Z28", 0.3), ("line", "H24", 0.5),
    ("line", "Z29", 0.35), ("line", "Z30", 0.4), ("line", "H25", 0.5),
    ("line", "Z31", 0.35), ("line", "Z32", 0.5), ("line", "H26", 0.35), ("line", "Z33", 0.6), ("line", "H27", 0.2),
    ("slot", "TURN", 5.0),
    ("line", "H28", 0.4), ("line", "Z34", 0.3),
    ("slot", "OUTSIDE", 20.0),
    ("line", "H29", 0.3), ("line", "G08", 0.5), ("line", "H30", 0.2), ("line", "Z35", 0.3), ("line", "H31", 0.3),
    ("slot", "ENDCARD", 10.0),
    ("slot", "STINGER", 3.0), ("line", "G09", 0.3), ("slot", "BLACK", 2.0),
]
FLEX = {"OUTSIDE": 1.6, "ASCENT": 1.0, "SHADOWPLAY": 1.0, "SUNRISE": 0.8, "TITLE": 0.25, "ENDCARD": 0.3, "MODERN": 0.8, "TURN": 0.5,
        "GAMESHOW_IN": 0.3, "CAVE_IN": 0.5, "RETURN": 0.5, "COLD_IN": 0.3, "SPOTLIGHT": 0.4}


def tighten(y, longest=0.75, keep=0.6, fade=0.012):
    """Shorten over-long inner pauses (ElevenLabs '...' gaps) to `keep` seconds, with short crossfades."""
    win = int(0.02 * SR)
    env = np.sqrt(np.convolve(y ** 2, np.ones(win) / win, mode="same"))
    q = env < max(env.max() * 10 ** (-38 / 20), 1e-4)
    out, i, last, n = [], 0, 0, len(y)
    nf = int(fade * SR)
    while i < n:
        if q[i]:
            j = i
            while j < n and q[j]:
                j += 1
            if i > 0 and j < n and (j - i) / SR > longest:
                cut0 = i + int(keep * SR / 2)
                cut1 = j - int(keep * SR / 2)
                seg = y[last:cut0].copy()
                seg[-nf:] *= np.linspace(1, 0, nf)
                out.append(seg)
                last = cut1
                nxt = y[last:last + nf].copy()
                y = y.copy(); y[last:last + nf] = nxt * np.linspace(0, 1, nf)
            i = j
        else:
            i += 1
    out.append(y[last:])
    return np.concatenate(out)


def prep(lid):
    src = None
    for ext in (".mp3", ".wav"):
        p = os.path.join(EP, "vo", f"ep4_{lid}{ext}")
        if os.path.exists(p):
            src = p
    raw = subprocess.run([FF, "-v", "quiet", "-i", src, "-ar", str(SR), "-ac", "1", "-f", "f32le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.float32).copy()
    win = int(0.01 * SR)
    env = np.sqrt(np.convolve(x ** 2, np.ones(win) / win, mode="same"))
    thr = max(env.max() * 10 ** (-42 / 20), 1e-4)
    idx = np.where(env > thr)[0]
    a = max(0, idx[0] - int(0.04 * SR)); b = min(len(x), idx[-1] + int(0.12 * SR))
    y = tighten(x[a:b])
    y[: int(0.004 * SR)] *= np.linspace(0, 1, int(0.004 * SR))
    y[-int(0.02 * SR):] *= np.linspace(1, 0, int(0.02 * SR))
    os.makedirs(os.path.join(EP, "vo_wav"), exist_ok=True)
    sf.write(os.path.join(EP, "vo_wav", f"{lid}.wav"), y, SR, subtype="PCM_16")
    return len(y) / SR


def main():
    script = {l["id"]: l for l in json.load(open(os.path.join(EP, "script.json")))["lines"]}
    seq_ids = [i for k, i, g in SEQ if k == "line"]
    assert sorted(seq_ids) == sorted(script), (set(script) - set(seq_ids), set(seq_ids) - set(script))
    durs = {lid: prep(lid) for lid in seq_ids}
    fixed = sum(durs[i] + g for k, i, g in SEQ if k == "line") + sum(g for k, i, g in SEQ if k == "slot")
    flex_total = sum(g * FLEX[i] for k, i, g in SEQ if k == "slot" and i in FLEX)
    stretch = (TARGET - fixed) / flex_total
    t = 0.0
    lines, slots = [], []
    for kind, i, g in SEQ:
        if kind == "line":
            l = script[i]
            lines.append(dict(id=i, spk=l["spk"], t0=round(t, 3), t1=round(t + durs[i], 3), text=l["text"]))
            t += durs[i] + g
        else:
            dur = max(g * 0.35, g + (g * FLEX[i] * stretch if i in FLEX else 0.0))
            slots.append(dict(id=i, t0=round(t, 3), t1=round(t + dur, 3)))
            t += dur
    tl = dict(fps=24, duration=round(t, 3), lines=lines, slots=slots, shots=[])
    json.dump(tl, open(os.path.join(EP, "timeline.json"), "w"), indent=1)
    print(f"speech {sum(durs.values()):.1f}s  fixed {fixed:.1f}s  stretch x{stretch:+.3f}  duration {t:.2f}s")
    for s in slots:
        print(f"  {s['id']:11s} {s['t0']:7.2f}-{s['t1']:7.2f}  ({s['t1'] - s['t0']:.1f}s)")


if __name__ == "__main__":
    main()
