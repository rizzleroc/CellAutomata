#!/usr/bin/env python3
"""BOXED effects stem (TEMPLATE; cues() below is the Ep4 example) (48 kHz stereo, full episode) from the ElevenLabs samples in ../sfx_el.
Cue sheet is built here from the timeline (line/slot anchors); every sample is RMS-normalised per category."""
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
L = {l["id"]: l for l in TL["lines"]}
S = {s["id"]: s for s in TL["slots"]}
DUR = TL["duration"]
# category target RMS (dBFS) - beds sit low, spot effects sit higher
LEVEL = dict(applause=-21, cheer=-21, laugh_big=-21, laugh_small=-23, ooh=-23, aww=-23, gasp=-22, mock=-22,
             fire=-30, drips=-29, cave_wind=-29, morning=-30, night=-30, water=-27, echo_voices=-27,
             chains=-22, drag=-24, rumble=-22, gong=-22, flash=-22, spotlight=-21, lights_on=-21, tv_on=-24, static=-25, glitch=-24,
             ding=-20, buzzer=-21, drumroll=-23, kaching=-21, scratch=-21, slide=-22, sparkle=-25, pings=-25)


def t0(k):
    return L[k]["t0"]


def t1(k):
    return L[k]["t1"]


def frac(k, f):
    return L[k]["t0"] + (L[k]["t1"] - L[k]["t0"]) * f


C = []


def c(name, t, dur=None, gain=1.0, pan=0.0, fade=0.25):
    C.append(dict(name=name, t=float(t), dur=dur, gain=gain, pan=pan, fade=fade))


def bed(name, a, b, gain=1.0, pan=0.0):
    """Loop an ambience sample from a to b with crossfades."""
    x = SAMPLES[name]
    ln = x.shape[1] / SR - 1.0
    t = a
    while t < b:
        c(name, t, dur=min(ln + 1.0, b - t + 0.5), gain=gain, pan=pan, fade=1.0)
        t += ln


SAMPLES = {}


def load(name):
    for ext in (".mp3", ".wav"):
        p = os.path.join(EP, "sfx_el", f"{os.path.basename(EP)}_S_{name}{ext}")
        if os.path.exists(p):
            raw = subprocess.run([FF, "-v", "quiet", "-i", p, "-ar", str(SR), "-ac", "2", "-f", "f32le", "-"], capture_output=True).stdout
            x = np.frombuffer(raw, np.float32).reshape(-1, 2).T.astype(np.float64)
            m = x.mean(0)
            hop = SR // 20
            r = np.array([np.sqrt(np.mean(m[i:i + hop] ** 2)) for i in range(0, max(1, len(m) - hop), hop)])
            top = np.sort(r)[int(len(r) * 0.5):] if len(r) > 2 else r
            rms = float(np.sqrt(np.mean(top ** 2)) + 1e-9)
            return x * (10 ** (LEVEL.get(name, -24) / 20) / rms)
    raise FileNotFoundError(name)


def cues():
    # ---- cold open (dark studio)
    c("tv_on", 1.15, gain=0.9)
    tb = frac("C03", 0.78)
    c("slide", tb + 0.2, gain=0.5)
    c("ooh", t0("C04") + 0.7, gain=0.45)
    c("laugh_small", t1("C05") + 0.1)
    c("laugh_big", t1("C06") + 0.05)
    c("flash", S["TITLE"]["t0"] - 0.25, gain=0.8)
    # ---- title + intro
    c("fire", S["TITLE"]["t0"], dur=S["TITLE"]["t1"] - S["TITLE"]["t0"] + 0.5, gain=0.7, fade=0.6)
    c("lights_on", S["LIGHTS_UP"]["t0"] + 0.25)
    c("applause", S["LIGHTS_UP"]["t0"] + 1.4, dur=4.0, gain=0.6)
    c("laugh_small", t1("H01") + 0.05)
    c("glitch", t0("H02") + 5.6, gain=0.7); c("scratch", t0("H02") + 5.65, gain=0.6)
    c("applause", S["APPLAUSE"]["t0"] - 0.4, dur=5.0); c("cheer", S["APPLAUSE"]["t0"] - 0.2, dur=3.5, gain=0.6)
    c("aww", t1("G00") + 0.05, gain=0.9); c("laugh_small", t1("G00") + 1.0, gain=0.7)
    c("spotlight", t1("Z02") - 1.3, gain=0.8)
    # ---- the cave
    c("cave_wind", S["CAVE_IN"]["t0"] - 0.1, dur=6.0, gain=0.9)
    bed("drips", S["CAVE_IN"]["t0"] + 0.5, t0("H10") + 0.2, gain=0.8)
    bed("fire", t0("Z05"), t0("H10") + 0.2, gain=0.6)
    c("chains", frac("Z03", 0.62), gain=0.7); c("chains", frac("Z04", 0.12), gain=0.9); c("chains", frac("Z04", 0.42), gain=0.6)
    c("echo_voices", frac("Z08", 0.3), dur=5.0, gain=0.8)
    c("ooh", t1("Z08") - 1.0, gain=0.4)
    c("scratch", t0("H08") - 0.12, gain=0.7)
    c("laugh_small", t1("H09") + 0.05)
    c("cheer", S["SHADOWPLAY"]["t0"] + 2.0, dur=3.5, gain=0.45)
    c("sparkle", frac("Z11", 0.8), gain=0.8)
    # ---- game show
    c("lights_on", S["GAMESHOW_IN"]["t0"] + 0.05, gain=0.7); c("sparkle", S["GAMESHOW_IN"]["t0"] + 0.8)
    c("kaching", frac("S01", 0.55), gain=0.8)
    c("drumroll", t0("S02") + 0.1, dur=3.0, gain=0.6)
    c("ding", t0("S03") + 0.02); c("cheer", t0("S03") + 0.3, dur=3.5, gain=0.7); c("applause", t1("S03") - 0.4, dur=3.5, gain=0.5)
    c("laugh_small", t1("S04") + 0.1)
    # ---- escape
    c("chains", frac("Z12", 0.4), gain=0.9)
    c("spotlight", S["SPOTLIGHT"]["t0"] + 0.9); c("ooh", S["SPOTLIGHT"]["t0"] + 1.15, gain=0.5)
    c("fire", t0("Z13"), dur=16.0, gain=0.8, fade=0.8); c("flash", t0("Z13") + 0.35, gain=0.9)
    c("laugh_big", t1("G02") + 0.1, gain=0.8)
    c("laugh_small", t1("G03") + 0.05, gain=0.6)
    c("laugh_small", t1("H12") + 0.05)
    c("cave_wind", t0("Z15"), dur=6.0, gain=0.6)
    c("drag", t0("Z15") + 1.5, dur=6.0, gain=0.8); c("drag", S["ASCENT"]["t0"], dur=6.0, gain=0.7)
    c("flash", S["ASCENT"]["t1"] - 0.6, gain=1.0)
    c("morning", t0("G04"), dur=12.0, gain=0.6, fade=1.0)
    # ---- the sun
    c("water", frac("Z17", 0.02), gain=0.9)
    c("morning", frac("Z17", 0.45), dur=12.0, gain=0.5, fade=1.5)
    c("night", t0("Z18") + 0.2, dur=8.0, gain=0.8, fade=1.0)
    c("sparkle", S["SUNRISE"]["t0"] + 1.0); c("ooh", S["SUNRISE"]["t0"] + 3.4, gain=0.5)
    c("sparkle", t0("P01"), gain=0.7)
    c("aww", t1("G05") + 0.1, gain=0.55)
    c("gasp", t1("Z20") + 0.05, gain=0.7)
    c("static", t1("H14") - 0.05, dur=0.6, gain=0.8); c("glitch", t1("H14"), gain=0.7)
    # ---- the ad
    c("tv_on", S["AD_IN"]["t0"] + 0.1, gain=0.6)
    c("sparkle", t0("A02") + 0.7); c("kaching", t1("A02") - 0.5, gain=0.7)
    c("pings", t0("A03") + 0.4, dur=5.0, gain=0.8); c("chains", frac("A03", 0.6), gain=0.6)
    c("sparkle", t1("A04") - 2.0)
    c("static", S["BUMPER"]["t0"] - 0.2, dur=0.5, gain=0.7)
    # ---- the return
    c("cheer", t0("H16") + 0.25, dur=4.0, gain=0.8); c("applause", t0("H16") + 0.6, dur=3.5, gain=0.5)
    c("cave_wind", t0("Z22"), dur=6.0, gain=0.6)
    bed("drips", t0("Z22") + 0.5, t1("Z26") + 0.5, gain=0.7)
    bed("fire", S["RETURN"]["t0"], t1("Z26") + 0.5, gain=0.45)
    c("buzzer", t0("G07") + 1.7, gain=0.9)
    c("mock", S["LAUGH"]["t0"] - 0.25, dur=4.0, gain=1.0); c("mock", t0("Z23") + 0.6, dur=3.5, gain=0.5)
    c("laugh_small", t1("H17") + 0.05)
    c("rumble", t0("Z24") + 1.0, gain=0.8); c("chains", frac("Z24", 0.55), gain=0.6); c("gong", t1("Z24") - 0.7, gain=0.8)
    c("gasp", t1("Z24") + 0.05, gain=0.7)
    c("gong", t1("Z25") - 1.6, gain=0.6)
    # ---- modern + meltdown
    c("pings", S["MODERN"]["t0"] - 0.2, dur=5.0, gain=0.9)
    c("glitch", t1("H22") - 0.3, gain=0.6)
    c("glitch", t0("H23") + 0.15, gain=0.8); c("static", t0("H23") + 2.25, dur=0.5, gain=0.7); c("glitch", t0("H23") + 5.0, gain=0.8)
    c("laugh_big", t1("Z28") + 0.05, gain=0.8)
    c("rumble", t0("H24") + 0.15, gain=0.7); c("static", t0("H24") + 0.4, dur=2.5, gain=0.6)
    c("laugh_small", t1("H24") + 0.1)
    for k in range(4):
        c("slide", t0("H25") + 3.0 + k * 0.28, gain=0.45)
    c("laugh_small", t1("H25") + 0.1)
    # ---- the way out
    c("sparkle", t1("Z32") - 1.5)
    c("ooh", t1("Z33") + 0.1, gain=0.4)
    c("rumble", S["TURN"]["t0"] + 0.9, gain=0.9); c("flash", S["TURN"]["t0"] + 3.6, gain=0.8); c("ooh", S["TURN"]["t0"] + 4.2, gain=0.6)
    c("morning", S["TURN"]["t0"] + 4.0, dur=12.0, gain=0.5, fade=1.0)
    c("cheer", S["OUTSIDE"]["t0"] + 0.5, dur=4.0, gain=0.7); c("applause", S["OUTSIDE"]["t1"] - 4.0, dur=4.0, gain=0.6)
    # ---- tag + stinger
    c("laugh_small", t1("G08") + 0.1)
    c("laugh_big", frac("H30", 0.62), gain=0.55)
    c("applause", t1("H31") + 0.05, dur=6.0, gain=0.8); c("cheer", t1("H31") + 0.1, dur=4.0, gain=0.6)
    c("drips", S["STINGER"]["t0"], dur=8.0, gain=0.8, fade=0.8); c("fire", S["STINGER"]["t0"], dur=8.0, gain=0.4, fade=0.8)
    c("slide", t0("G09") + 0.35, gain=0.35)


def main():
    names = set(LEVEL)
    for n in names:
        try:
            SAMPLES[n] = load(n)
        except FileNotFoundError:
            print("missing sample", n)
    cues()
    N = int(DUR * SR)
    out = np.zeros((2, N))
    for q in C:
        x = SAMPLES.get(q["name"])
        if x is None:
            continue
        i0 = int(q["t"] * SR)
        if i0 >= N:
            continue
        n = x.shape[1] if q["dur"] is None else min(x.shape[1], int(q["dur"] * SR))
        n = min(n, N - i0)
        seg = x[:, :n] * q["gain"]
        k = min(n, int(0.01 * SR)); seg[:, :k] *= np.linspace(0, 1, k)
        if q["dur"] is not None:
            k = min(n, int(q["fade"] * SR)); seg[:, -k:] *= np.linspace(1, 0, k)
            k2 = min(n, int(q["fade"] * SR * 0.5)); seg[:, :k2] *= np.linspace(0, 1, k2)
        p = q["pan"]
        seg[0] *= np.cos((p + 1) * np.pi / 4) * 1.4142; seg[1] *= np.sin((p + 1) * np.pi / 4) * 1.4142
        out[:, i0:i0 + n] += seg
    pk = np.abs(out).max()
    if pk > 0.95:
        out *= 0.95 / pk
    a = (np.clip(out.T, -1, 1) * 32767).astype("<i2")
    with wave.open(os.path.join(HERE, "sfx.wav"), "wb") as f:
        f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR); f.writeframes(a.tobytes())
    print(f"SFX -> {os.path.join(HERE, 'sfx.wav')}  ({len(C)} cues, peak {pk:.2f})")


if __name__ == "__main__":
    main()
