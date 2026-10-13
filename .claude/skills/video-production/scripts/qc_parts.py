#!/usr/bin/env python3
"""QC encoded delivery parts before sending: size vs the 30 MiB upload cap, duration (and the total), streams,
integrated loudness and TRUE PEAK measured on the encoded AAC (the encoder adds overshoot the mix didn't have), plus
frames at each part's start / 25% / 50% / 75% / end tiled into contact sheets to LOOK at.

  python3 qc_parts.py OUT_DIR PREFIX [--cap-mib 30] [--tp-max -1.0]
    e.g. python3 qc_parts.py $B/ep4/out boxed_ep04   ->   $B/ep4/out/qc_parts/sheet_*.png
Exit status 1 if any part is over the cap or its true peak is above --tp-max."""
import argparse
import glob
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def ffmpeg_exe():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


FF = ffmpeg_exe()


def probe(path):
    r = subprocess.run([FF, "-hide_banner", "-i", path], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r)
    dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else 0.0
    return dur, [ln.strip() for ln in r.splitlines() if ln.strip().startswith("Stream #")]


def loudness(path):
    r = subprocess.run([FF, "-hide_banner", "-nostats", "-i", path, "-map", "0:a", "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    tail = r[r.rfind("Summary:"):]
    i = re.search(r"I:\s+(-?[\d.]+) LUFS", tail)
    p = re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", tail)
    return (float(i.group(1)) if i else None), (float(p.group(1)) if p and p.group(1) != "-inf" else None)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out_dir")
    ap.add_argument("prefix")
    ap.add_argument("--cap-mib", type=float, default=30.0)
    ap.add_argument("--tp-max", type=float, default=-1.0, help="max true peak (dBTP) allowed on the encoded audio")
    a = ap.parse_args()
    parts = sorted(glob.glob(os.path.join(a.out_dir, f"{a.prefix}_part*.mp4")),
                   key=lambda p: int(re.search(r"part(\d+)\.mp4$", p).group(1)))
    if not parts:
        sys.exit(f"no {a.prefix}_part*.mp4 in {a.out_dir}")
    qc = os.path.join(a.out_dir, "qc_parts")
    os.makedirs(qc, exist_ok=True)
    for f in glob.glob(os.path.join(qc, "*.png")):
        os.remove(f)
    cap = a.cap_mib * 1024 * 1024
    total, bad = 0.0, []
    for p in parts:
        size = os.path.getsize(p)
        dur, streams = probe(p)
        total += dur
        lufs, tp = loudness(p)
        flags = []
        if size >= cap:
            flags.append("TOO BIG")
        if tp is not None and tp > a.tp_max:
            flags.append(f"PEAK > {a.tp_max:g} dBTP")
        if flags:
            bad.append(os.path.basename(p))
        n = re.search(r"part(\d+)\.mp4$", p).group(1)
        print(f"{os.path.basename(p)}  {size / 1e6:6.2f} MB ({size / cap * 100:5.1f}% of cap)  {dur:8.3f} s  "
              f"I={lufs} LUFS  TP={tp} dBTP  {' '.join(flags) or 'OK'}")
        for s in streams:
            print("     ", s[:118])
        for k, frac in enumerate((0.0, 0.25, 0.5, 0.75, 1.0)):
            t = min(max(dur * frac, 0.05), dur - 0.08)
            subprocess.run([FF, "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", p, "-frames:v", "1",
                            os.path.join(qc, f"still_p{n}_{k}_{t:06.2f}.png")], check=True)  # sheet.py labels name[6:]
    print(f"total {total:.3f} s over {len(parts)} parts  ->  {'ALL OK' if not bad else 'FAILED: ' + ', '.join(bad)}")
    subprocess.run([sys.executable, os.path.join(HERE, "sheet.py"), qc, os.path.join(qc, "sheet")], check=True)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
