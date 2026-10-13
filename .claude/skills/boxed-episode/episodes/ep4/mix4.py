#!/usr/bin/env python3
"""BOXED ep4 mix: 5 voices (host through a 'TV speaker', Zee clean, Gary on a handheld audience mic, the infomercial
announcer with broadcast compression, the planet huge and cosmic) + score (ducked under dialogue) + SFX,
loudness-normalised. Also writes a speaker-labelled .srt.
   python3 mix3.py [--music ep4/audio/music.wav] [--sfx ep4/audio/sfx.wav]
"""
import json, os, subprocess, sys, wave
import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
EP = os.path.join(HERE, "ep4")
FF = "/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
SR = 48000
VOICES = {  # spk: (stem, ffmpeg chain, target line RMS dBFS)
    "HOST": ("host", "highpass=f=140,lowpass=f=8500,equalizer=f=2600:t=q:w=1.2:g=3.0,equalizer=f=400:t=q:w=1.0:g=-1.5,"
                     "acompressor=threshold=-22dB:ratio=3.5:attack=8:release=160:makeup=4,aecho=0.85:0.6:22:0.15,alimiter=limit=0.95", -16.0),
    "GUEST": ("guest", "highpass=f=85,equalizer=f=220:t=q:w=1.0:g=1.0,equalizer=f=5200:t=q:w=1.6:g=1.5,"
                       "acompressor=threshold=-21dB:ratio=3:attack=10:release=180:makeup=4,alimiter=limit=0.95", -16.0),
    "AUD": ("gary", "highpass=f=120,lowpass=f=9000,equalizer=f=3200:t=q:w=1.0:g=2.5,equalizer=f=300:t=q:w=1.0:g=-1.5,"
                    "acompressor=threshold=-22dB:ratio=3:attack=8:release=150:makeup=3,aecho=0.8:0.55:38|74:0.14|0.07,alimiter=limit=0.95", -16.5),
    "ANN": ("announcer", "highpass=f=90,equalizer=f=120:t=q:w=1.0:g=2.0,equalizer=f=3500:t=q:w=1.2:g=3.0,"
                         "acompressor=threshold=-26dB:ratio=5:attack=4:release=90:makeup=6,alimiter=limit=0.95", -15.5),
    "PLANET": ("planet", "asetrate=43200,aresample=48000,atempo=1.111111,highpass=f=60,equalizer=f=150:t=q:w=1.0:g=3.0,"
                         "acompressor=threshold=-22dB:ratio=3:attack=10:release=200:makeup=3,aecho=0.8:0.7:90|180|320:0.35|0.25|0.15,alimiter=limit=0.95", -16.0),
}
NAMES = {"HOST": "HOST", "GUEST": "ZEE", "AUD": "GARY", "ANN": "ANNOUNCER", "PLANET": "THE SUN"}
DISPLAY = [("Boxed", "BOXED"), ("seventy-five", "75"), ("Seventy-five", "75"), ("Ninety-eight inches", '98 inches'), ("4K", "4K")]


def display_text(s):
    for a, b in DISPLAY:
        s = s.replace(a, b)
    return s


def run(*a):
    r = subprocess.run([FF, "-y", "-v", "error", *a], capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-1500:]); raise SystemExit(1)


def wav_out(path, x):
    x = np.clip(x, -1, 1)
    a = (x * 32767).astype("<i2")
    with wave.open(path, "wb") as f:
        f.setnchannels(1 if x.ndim == 1 else x.shape[1]); f.setsampwidth(2); f.setframerate(SR); f.writeframes(a.tobytes())


def srt(tl, path):
    def ts(s):
        h = int(s // 3600); m = int(s % 3600 // 60); sec = s % 60
        return f"{h:02d}:{m:02d}:{int(sec):02d},{int((sec % 1) * 1000):03d}"
    lines = tl["lines"]
    with open(path, "w") as f:
        for i, ln in enumerate(lines, 1):
            end = ln['t1'] + 0.2
            if i < len(lines):
                end = min(end, lines[i]['t0'] - 0.05)                # never overlap the next cue
            f.write(f"{i}\n{ts(ln['t0'])} --> {ts(end)}\n{NAMES[ln['spk']]}: {display_text(ln['text'])}\n\n")


def main():
    args = sys.argv[1:]
    music = args[args.index("--music") + 1] if "--music" in args else None
    sfx = args[args.index("--sfx") + 1] if "--sfx" in args else None
    tl = json.load(open(os.path.join(EP, "timeline.json")))
    N = int(tl["duration"] * SR)
    tmp = os.path.join(EP, "out", "mix"); os.makedirs(tmp, exist_ok=True)
    stems = {spk: np.zeros(N, np.float32) for spk in VOICES}
    for ln in tl["lines"]:
        a, sr = sf.read(os.path.join(EP, "vo_wav", ln["id"] + ".wav"), dtype="float32")
        assert sr == SR
        i0 = int(ln["t0"] * SR); i1 = min(N, i0 + len(a))
        stems[ln["spk"]][i0:i1] += a[: i1 - i0]
    procd = []
    for spk, (stem, chain, target) in VOICES.items():
        if not np.any(stems[spk]):
            continue
        wav_out(f"{tmp}/{stem}_dry.wav", stems[spk])
        run("-i", f"{tmp}/{stem}_dry.wav", "-af", chain, "-ar", str(SR), f"{tmp}/{stem}.wav")
        x, _sr = sf.read(f"{tmp}/{stem}.wav")
        x = np.pad(x, (0, max(0, N - len(x))))[:N]
        lv = [20 * np.log10(np.sqrt(np.mean(x[int(l["t0"] * _sr):int(l["t1"] * _sr)] ** 2)) + 1e-9) for l in tl["lines"] if l["spk"] == spk]
        g = 10 ** ((target - float(np.mean(lv))) / 20)
        print(f"  {stem:10s}: line RMS {np.mean(lv):.1f} dB -> gain {20 * np.log10(g):+.1f} dB")
        wav_out(f"{tmp}/{stem}.wav", np.clip(x * g, -1, 1))
        procd.append(f"{tmp}/{stem}.wav")
    ins = []
    for p in procd:
        ins += ["-i", p]
    run(*ins, "-filter_complex", "".join(f"[{k}:a]" for k in range(len(procd))) + f"amix=inputs={len(procd)}:normalize=0[v]", "-map", "[v]",
        "-ar", str(SR), "-ac", "1", f"{tmp}/vo.wav")
    ins = ["-i", f"{tmp}/vo.wav"]
    fc = "[0:a]asplit=2[v1][v2];"
    k = 1
    beds = []
    if music and os.path.exists(music):
        ins += ["-i", music]
        fc += f"[{k}:a]volume=1.0[m];[m][v2]sidechaincompress=threshold=0.05:ratio=3.5:attack=25:release=600:makeup=1[md];"
        beds.append("[md]"); k += 1
    else:
        fc += "[v2]anullsink;"
    if sfx and os.path.exists(sfx):
        ins += ["-i", sfx]
        fc = fc.replace("[0:a]asplit=2[v1][v2];", "[0:a]asplit=3[v1][v2][v3];")
        fc += f"[{k}:a]volume=1.0[sx0];[sx0][v3]sidechaincompress=threshold=0.06:ratio=2.2:attack=8:release=220:makeup=1[sx];"
        beds.append("[sx]"); k += 1
    fc += "[v1]aformat=channel_layouts=stereo[vs];[vs]" + "".join(beds) + f"amix=inputs={1 + len(beds)}:duration=first:normalize=0[mx];"
    fc += "[mx]loudnorm=I=-15:TP=-1.5:LRA=11[out]"
    run(*ins, "-filter_complex", fc, "-map", "[out]", "-ar", str(SR), "-ac", "2", "-c:a", "pcm_s16le", os.path.join(EP, "out", "mix.wav"))
    srt(tl, os.path.join(EP, "out", "boxed_ep04.srt"))
    print("MIX ->", os.path.join(EP, "out", "mix.wav"))


if __name__ == "__main__":
    main()
