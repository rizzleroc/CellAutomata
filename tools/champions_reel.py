"""The Discovered — a reel of the most complex specimens the search ever found.

Reads the needle deep-search ranking (discovery/needle_deep_rank.json), takes the
top specimens, and casts each as a relit, slowly-rotating metal medallion — the
champions of an ~5,000-candidate sweep, rendered through the suite's best
treatment. Pure reuse of schedule.py's relight frame generator + compositor.

  python3 tools/champions_reel.py     # -> media/sim/the_discovered.mp4
"""
from __future__ import annotations
import json, os, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schedule as SCH

FF = SCH.FF
OUT = "media/sim"
W, H, DISC, DX, DY = SCH.W, SCH.H, SCH.DISC, SCH.DX, SCH.DY
FPS = 30
TOPN = 12
PER = 78                                   # frames per specimen (~2.6s)
METALS = ["gold", "copper", "jade", "ice", "amethyst"]
BG, GOLD, INK, DIM = SCH.BG, SCH.GOLD, SCH.INK, SCH.DIM


def _title(n):
    out = []
    for fi in range(n):
        p = fi / max(n - 1, 1)
        a = min(p / 0.16, (1 - p) / 0.16, 1.0)
        cv = Image.new("RGBA", (W, H), (*BG, 255))
        SCH._text(cv, (W // 2, 700), SCH._spaced("the discovered"), SCH._font(64), GOLD, a)
        ImageDraw.Draw(cv).line([(W // 2 - 130, 800), (W // 2 + 130, 800)], fill=(*GOLD, int(180 * a)), width=2)
        SCH._text(cv, (W // 2, 900), "≈5,000 candidates searched.\nthe 12 most complex, cast in metal.",
                  SCH._font(40, False), DIM, a, spacing=14)
        SCH._text(cv, (W // 2, 1740), SCH._spaced("cellautomata · needle deep-search"), SCH._font(26), DIM, a * 0.7)
        out.append(np.asarray(cv.convert("RGB"), np.uint8))
    return out


def _compose(disc, rank, r, gin):
    cv = Image.new("RGBA", (W, H), (*BG, 255))
    cv.paste(Image.fromarray(disc), (DX, DY))
    SCH._text(cv, (W // 2, 150), SCH._spaced("discovered specimen"), SCH._font(30), GOLD, gin * 0.9)
    SCH._text(cv, (W // 2, 252), f"#{rank:02d}   ·   {r['id']}", SCH._font(56), INK, gin)
    SCH._text(cv, (W // 2, DY + DISC + 86), f"{r['regime']}   ·   {r['n1']}-fold ✕ {r['n2']}   ·   octave {r['octs']}",
              SCH._font(38, False), DIM, gin)
    SCH._text(cv, (W // 2, DY + DISC + 168), f"complexity  {r['score']:.3f}", SCH._font(42), GOLD, gin)
    SCH._text(cv, (W // 2, 1846), SCH._spaced("cellautomata · needle deep-search"), SCH._font(24), DIM, 0.6)
    return np.asarray(cv.convert("RGB"), np.uint8)


def render():
    os.makedirs(OUT, exist_ok=True)
    ranked = json.load(open("discovery/needle_deep_rank.json"))["ranked"][:TOPN]
    silent = "/tmp/discovered_silent.mp4"
    wr = SCH._writer(silent)
    for fr in _title(int(2.4 * FPS)):
        wr.send(np.ascontiguousarray(fr).tobytes())
    for i, r in enumerate(ranked):
        V = SCH._src(r["id"])
        metal = METALS[i % len(METALS)]
        discs = SCH.frames_relit(V, r["n1"], r["n2"], r["octs"], PER, metal)
        for fi, disc in enumerate(discs):
            gin = min(fi / 9.0, 1.0)
            wr.send(np.ascontiguousarray(_compose(disc, i + 1, r, gin)).tobytes())
        print(f"  #{i+1:02d} {r['id']:14s} {metal:9s} {r['n1']}x{r['n2']}o{r['octs']} score={r['score']}")
    wr.close()

    dur = (2.4 + TOPN * PER / FPS)
    out = f"{OUT}/the_discovered.mp4"
    af = (f"[1:a][2:a]amix=inputs=2,volume=0.13,lowpass=f=460,"
          f"afade=t=in:st=0:d=1.6,afade=t=out:st={dur-2:.1f}:d=2[a]")
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", silent,
                    "-f", "lavfi", "-t", f"{dur}", "-i", "sine=frequency=82.41:sample_rate=44100",
                    "-f", "lavfi", "-t", f"{dur}", "-i", "sine=frequency=123.47:sample_rate=44100",
                    "-filter_complex", af, "-map", "0:v", "-map", "[a]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "144k", "-shortest",
                    "-movflags", "+faststart", out], check=True)
    print(f"-> {out}  ({os.path.getsize(out)/1e6:.1f} MB, {dur:.0f}s, top {TOPN} specimens)")


if __name__ == "__main__":
    render()
