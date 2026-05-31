"""Long-form mandala film — a finished, meditative piece.

- Seamless symmetry-order morph: a continuous polar kaleidoscope whose fold
  count is interpolated (n=6 -> 7 -> 8 ...), so petals literally split/merge.
- Live reaction-diffusion source, crossfading through regimes (texture morph).
- Crossfading palettes, continuous slow rotation + breathing zoom (camera move).
- Voice-over (espeak) over an ambient bed, muxed to a finished MP4.

  python3 tools/mandala_film.py --dur 180 --out media/mandala_film.mp4
"""
from __future__ import annotations
import argparse, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mandala as M
from cellauto.engine import Engine
from cellauto.rules import REGISTRY

FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
RULE = M.RULE

REGIME_ORDER = ["spots", "labyrinth", "chaos", "coral", "maze", "turbulence", "stripes", "solitons"]
PAL_ORDER = ["gold", "ice", "amethyst", "emerald", "rose", "ember"]
SYMS = [6, 8, 12, 5, 9, 16, 7, 10, 6, 18, 8, 12, 5, 14, 9, 6, 11, 8, 16, 7, 12, 6, 10, 8]

NARRATION = [
    (2.0,   "From two reacting chemicals, and one simple rule, structure begins."),
    (27.0,  "No designer. No blueprint. Only diffusion, feedback, and time."),
    (54.0,  "Fold the living field upon itself, and geometry turns sacred."),
    (85.0,  "Six petals. Eight. Twelve. One pattern, endlessly re-seen."),
    (116.0, "Order and chaos, breathing in the very same frame."),
    (145.0, "Every form here is deterministic. And every form is alive."),
    (168.0, "Cellular automata: the mathematics of becoming."),
]


def smoothstep(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def sched(order, t, dur, xfade):
    """piecewise value with crossfade -> (i, j, w) indices into order + blend w."""
    seg = dur / len(order)
    i = min(int(t / seg), len(order) - 1)
    local = t - i * seg
    if local > seg - xfade and i < len(order) - 1:
        return i, i + 1, smoothstep((local - (seg - xfade)) / xfade)
    return i, i, 0.0


def sym_at(t, dur):
    seg = dur / (len(SYMS) - 1)
    i = min(int(t / seg), len(SYMS) - 2)
    w = smoothstep((t - i * seg) / seg)
    return SYMS[i] * (1 - w) + SYMS[i + 1] * w


class Kaleidoscope:
    def __init__(self, K, G):
        self.K, self.G = K, G
        yy, xx = np.mgrid[0:K, 0:K]
        cx = cy = K / 2.0
        self.R = np.hypot(xx - cx, yy - cy).astype(np.float32)
        self.TH = np.arctan2(yy - cy, xx - cx).astype(np.float32)
        r = self.R / (K / 2.0)
        self.mask = np.clip((0.985 - r) / 0.06, 0, 1).astype(np.float32)
        self.scale = G / float(K)

    def fold(self, V, n, phase, zoom):
        wedge = 2 * np.pi / n
        a = np.mod(self.TH + phase, wedge)
        a = np.minimum(a, wedge - a)              # mirror -> fundamental wedge
        rr = self.R * self.scale * zoom
        G = self.G
        sx = np.clip(G / 2 + rr * np.cos(a), 0, G - 1.001)
        sy = np.clip(G / 2 + rr * np.sin(a), 0, G - 1.001)
        x0 = sx.astype(np.int32); y0 = sy.astype(np.int32)
        x1 = x0 + 1; y1 = y0 + 1
        fx = sx - x0; fy = sy - y0
        return (V[y0, x0] * (1 - fx) * (1 - fy) + V[y0, x1] * fx * (1 - fy)
                + V[y1, x0] * (1 - fx) * fy + V[y1, x1] * fx * fy)

    def render(self, V, s, phase, zoom):
        nlo = int(np.floor(s)); nhi = nlo + 1; w = s - nlo
        f = (1 - w) * self.fold(V, nlo, phase, zoom) + w * self.fold(V, nhi, phase, zoom)
        return f * self.mask


# ---------- audio ----------
def build_audio(dur, path, sr=22050):
    track = np.zeros(int(dur * sr) + sr, np.int32)
    for t, line in NARRATION:
        if t >= dur:
            continue
        wv = "/tmp/_mf_vo.wav"
        subprocess.run(["espeak-ng", "-v", "en-us", "-s", "142", "-p", "40", "-g", "9",
                        "-w", wv, line], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        w = wave.open(wv, "rb"); a = np.frombuffer(w.readframes(w.getnframes()), np.int16); w.close()
        i = int(t * sr)
        end = min(i + len(a), len(track))
        track[i:end] += a[:end - i].astype(np.int32)
    n = int(dur * sr)
    tt = np.arange(n) / sr
    bed = (0.55 * np.sin(2 * np.pi * 96 * tt) + 0.4 * np.sin(2 * np.pi * 144 * tt)
           + 0.3 * np.sin(2 * np.pi * 192 * tt) + 0.22 * np.sin(2 * np.pi * 64 * tt))
    bed *= (0.6 + 0.4 * np.sin(2 * np.pi * 0.04 * tt))
    bed /= (np.max(np.abs(bed)) + 1e-9)
    f = int(3 * sr); env = np.ones(n); env[:f] = np.linspace(0, 1, f); env[-f:] = np.linspace(1, 0, f)
    bed *= env
    mix = track[:n].astype(np.float64) * 0.92 + bed * 0.13 * 32767
    mix = np.clip(mix, -32768, 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(mix.tobytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dur", type=float, default=180)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--K", type=int, default=600)
    ap.add_argument("--grid", type=int, default=200)
    ap.add_argument("--size", type=int, default=1080)
    ap.add_argument("--out", default="media/mandala_film.mp4")
    a = ap.parse_args()

    print("warming engines ...")
    engines = {}
    for name in REGIME_ORDER:
        e = Engine(width=a.grid, height=a.grid, rule=REGISTRY[RULE](**M.REGIMES[name]), seed=1)
        for _ in range(M.REG_STEPS[name]):
            e.step()
        engines[name] = e

    kal = Kaleidoscope(a.K, a.grid)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    silent = "/tmp/_mandala_silent.mp4"
    wr = imageio_ffmpeg.write_frames(silent, (a.size, a.size), fps=a.fps, codec="libx264",
        pix_fmt_in="rgb24", pix_fmt_out="yuv420p", macro_block_size=2,
        output_params=["-crf", "18", "-preset", "medium"])
    wr.send(None)
    tf = ImageFont.truetype(FB, 26); title = ImageFont.truetype(FB, 60)
    N = int(a.dur * a.fps)
    stepped = set()

    def norm(name):
        v = np.asarray(engines[name].state.v, np.float32)
        return v / (v.max() + 1e-6)

    for fi in range(N):
        t = fi / a.fps
        ri, rj, rw = sched(REGIME_ORDER, t, a.dur, 6.0)
        for idx in {ri, rj}:                       # step only active engines
            nm = REGIME_ORDER[idx]
            engines[nm].step()
        V = norm(REGIME_ORDER[ri])
        if rj != ri:
            V = (1 - rw) * V + rw * norm(REGIME_ORDER[rj])
        s = sym_at(t, a.dur)
        phase = 0.05 * t
        zoom = 1.0 / (1.0 + 0.12 * np.sin(2 * np.pi * t / 42.0))
        field = kal.render(V.astype(np.float32), s, phase, zoom)
        idx = (np.clip(field, 0, 1) ** 0.8 * 255).astype(np.uint8)
        pi, pj, pw = sched(PAL_ORDER, t, a.dur, 5.0)
        ca = M.PALS[PAL_ORDER[pi]][idx].astype(np.float32)
        rgb = ca if pj == pi else (1 - pw) * ca + pw * M.PALS[PAL_ORDER[pj]][idx].astype(np.float32)
        img = Image.fromarray(rgb.astype(np.uint8)).resize((a.size, a.size), Image.BICUBIC).convert("RGB")
        d = ImageDraw.Draw(img)
        lab = f"{round(s)}-fold"
        d.text((a.size / 2 - d.textlength(lab, font=tf) / 2, a.size - 52), lab, font=tf, fill=(210, 220, 232))
        if t < 5:                                  # title fade-in
            al = int(255 * smoothstep(t / 1.5) * smoothstep((5 - t) / 1.5))
            ov = Image.new("RGBA", img.size, (0, 0, 0, 0)); dd = ImageDraw.Draw(ov)
            tw = dd.textlength("SACRED GEOMETRY", font=title)
            dd.text((a.size / 2 - tw / 2, a.size / 2 - 36), "SACRED GEOMETRY", font=title, fill=(245, 249, 253, al))
            img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
        af = min(1.0, (fi + 1) / 12, (N - fi) / 12)
        fr = np.asarray(img, np.uint8)
        if af < 0.999:
            fr = (fr.astype(np.float32) * af).astype(np.uint8)
        wr.send(np.ascontiguousarray(fr).tobytes())
        if fi % 300 == 0:
            print(f"  frame {fi}/{N} (t={t:.0f}s, sym~{s:.1f})", flush=True)
    wr.close()

    print("building audio ...")
    narr = "/tmp/_mandala_narr.wav"
    build_audio(a.dur, narr)
    subprocess.run([FFMPEG, "-y", "-i", silent, "-i", narr, "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", "-movflags", "+faststart", a.out],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"DONE -> {a.out} ({os.path.getsize(a.out)/1e6:.1f} MB, {a.dur:.0f}s)")


if __name__ == "__main__":
    main()
