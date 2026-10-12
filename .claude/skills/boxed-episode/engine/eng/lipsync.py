"""Audio-driven lip sync. For each dialogue line: per-frame (24 fps) loudness and three spectral bands
(F1 region, F2 region, fricative band) classify a cartoon mouth shape (X M A E I O U F) plus an
openness value; short dips between voiced frames become M/B/P closures; shapes are held >= 2 frames.
Also returns an 'emphasis' track (loudness peaks) used to drive nods and brows.
"""
import json
import numpy as np
import soundfile as sf

FPS = 24


def analyze(path):
    x, sr = sf.read(path, dtype="float32")
    if x.ndim > 1:
        x = x.mean(1)
    hop = sr // FPS
    n = int(np.ceil(len(x) / hop))
    win = 1024
    xp = np.pad(x, (win // 2, win))
    han = np.hanning(win).astype(np.float32)
    freqs = np.fft.rfftfreq(win, 1 / sr)
    b1 = (freqs >= 150) & (freqs < 900)
    b2 = (freqs >= 900) & (freqs < 2600)
    b3 = (freqs >= 2600) & (freqs < 7000)
    rms = np.zeros(n); e1 = np.zeros(n); e2 = np.zeros(n); e3 = np.zeros(n)
    for i in range(n):
        seg = xp[i * hop: i * hop + win]
        if len(seg) < win:
            seg = np.pad(seg, (0, win - len(seg)))
        rms[i] = np.sqrt(np.mean(seg[win // 4: 3 * win // 4] ** 2) + 1e-12)
        sp = np.abs(np.fft.rfft(seg * han)) ** 2
        e1[i], e2[i], e3[i] = sp[b1].sum(), sp[b2].sum(), sp[b3].sum()
    ref = np.percentile(rms[rms > 1e-4], 93) if (rms > 1e-4).any() else 1.0
    loud = np.clip(rms / max(ref, 1e-6), 0, 1.4)
    tot = e1 + e2 + e3 + 1e-12
    fric = e3 / tot
    ratio = e2 / (e1 + 1e-12)
    voiced = loud >= 0.09

    def rank(v):
        r = np.zeros(n)
        if voiced.sum() > 2:
            vv = v[voiced]; order = np.argsort(np.argsort(vv)); r[voiced] = order / max(1, len(vv) - 1)
        return r
    rq, fq = rank(ratio), rank(fric)
    vis = []
    opn = np.zeros(n)
    for i in range(n):
        L = loud[i]
        if L < 0.09:
            vis.append("X"); opn[i] = 0; continue
        o = float(np.clip((L - 0.06) / 0.85, 0, 1)) ** 0.75
        opn[i] = o
        if fq[i] > 0.86 and L < 0.7:
            vis.append("F" if fric[i] > 0.55 else "I")
        elif o > 0.62:
            vis.append("A" if rq[i] < 0.58 else "E")
        elif o > 0.3:
            vis.append("E" if rq[i] > 0.62 else ("O" if rq[i] < 0.24 else "A"))
        else:
            vis.append("U" if rq[i] < 0.3 else ("L" if rq[i] > 0.7 else "I"))
    # M/B/P closures: a short (1-3 frame) loudness dip inside voiced speech closes the lips
    for i in range(1, n - 1):
        if vis[i] == "X":
            j = i
            while j < n and vis[j] == "X":
                j += 1
            if j - i <= 3 and i > 0 and j < n and vis[i - 1] != "X":
                for k in range(i, j):
                    vis[k] = "M"; opn[k] = 0.0
        elif 0 < i < n - 1 and loud[i] < 0.8 * min(loud[i - 1], loud[i + 1]) and loud[i] < 0.3 and vis[i - 1] not in ("X", "M"):
            vis[i] = "M"; opn[i] = 0.0
    # hold every shape at least 2 frames (no single-frame flicker)
    i = 0
    while i < n:
        j = i
        while j + 1 < n and vis[j + 1] == vis[i]:
            j += 1
        if j == i and 0 < i < n - 1:
            vis[i] = vis[i - 1]
            opn[i] = 0.5 * (opn[i - 1] + opn[i])
        i = j + 1
    # emphasis: loudness peaks above the local average (stressed syllables)
    k = 9
    pad = np.pad(loud, (k, k), mode="edge")
    avg = np.convolve(pad, np.ones(2 * k + 1) / (2 * k + 1), mode="same")[k:-k]
    emph = np.clip((loud - avg - 0.08) / 0.35, 0, 1)
    emph = np.convolve(emph, np.array([0.25, 0.5, 0.25]), mode="same")
    # smooth openness a touch so mouths do not chatter
    opn = np.convolve(opn, np.array([0.2, 0.6, 0.2]), mode="same")
    opn[np.array([v in ("X", "M") for v in vis])] = 0.0
    return dict(n=int(n), vis=vis, open=[round(float(v), 3) for v in opn], loud=[round(float(v), 3) for v in loud],
                emph=[round(float(v), 3) for v in emph])


def build(vo_dir, timeline_path, out_path):
    tl = json.load(open(timeline_path))
    res = {}
    for ln in tl["lines"]:
        a = analyze(f"{vo_dir}/{ln['id']}.wav")
        a.update(t0=ln["t0"], spk=ln["spk"])
        res[ln["id"]] = a
    json.dump(res, open(out_path, "w"))
    return res


if __name__ == "__main__":
    import sys, collections
    r = build(sys.argv[1], sys.argv[2], sys.argv[3])
    for k, v in r.items():
        c = collections.Counter(v["vis"])
        print(k, v["spk"], v["n"], "frames", dict(sorted(c.items(), key=lambda z: -z[1])))
