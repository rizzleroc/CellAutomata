#!/usr/bin/env python3
"""Plan where to split a finished episode into delivery parts (each < the 30 MiB upload cap) so that
  * no part starts or ends in the middle of a line of dialogue (a line split across two files sounds broken),
  * every cut is a real hard cut on a drawing boundary (a shot start, or -- with --video -- an isolated scene change
    inside a music-only stretch, e.g. a cut within a montage),
  * the number of parts is the smallest that keeps every part's video bitrate >= --min-kbps, and among those the
    longest part is as short as possible (so the worst part gets the most bits).

  python3 plan_parts.py ep4/timeline.json [--video ep4/out/video.mp4] [--min-kbps 1950] [--cap-mb 29.2] [--fps 12]

timeline.json: {"duration": s, "lines": [{"id", "t0", "t1", ...}], "shots": [{"id", "t0", "t1", ...}]}
(the BOXED timeline; any project can write this shape). Prints the plan and a ready-to-paste argument list for
finalize.sh / split_parts.sh ("start end partN" ...)."""
import argparse
import json
import math
import os
import re
import subprocess
import sys


def ffmpeg_exe():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def scene_cuts(video, thr):
    """Timestamps (s) of scene changes above `thr` in the whole video (ffmpeg scene score). The scan decodes the
    whole video (~2 min for 11 minutes of 1080p), so the result is cached next to it until the video changes."""
    st = os.stat(video)
    cache = f"{video}.scenes.json"
    key = dict(size=st.st_size, mtime=st.st_mtime, thr=thr)
    try:
        c = json.load(open(cache))
        if c.get("key") == key:
            return c["cuts"]
    except (OSError, ValueError):
        pass
    r = subprocess.run([ffmpeg_exe(), "-hide_banner", "-nostats", "-i", video, "-an",
                        "-vf", f"scale=480:-2,select='gt(scene,{thr})',showinfo", "-f", "null", "-"],
                       capture_output=True, text=True)
    cuts = [float(m) for m in re.findall(r"pts_time:([0-9.]+)", r.stderr)]
    try:
        json.dump(dict(key=key, cuts=cuts), open(cache, "w"))
    except OSError:
        pass
    return cuts


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("timeline")
    ap.add_argument("--video", help="the concatenated video: adds isolated hard cuts inside music-only stretches")
    ap.add_argument("--fps", type=float, default=12.0, help="drawing rate cuts snap to (12 = animated on twos at 24 fps)")
    ap.add_argument("--cap-mb", type=float, default=29.2, help="target size per part in MB (SendUserFile caps at 30 MiB)")
    ap.add_argument("--audio-kbps", type=float, default=128.0)
    ap.add_argument("--overhead-kbps", type=float, default=30.0, help="container + rate-control margin")
    ap.add_argument("--min-kbps", type=float, default=1950.0, help="lowest acceptable video bitrate per part")
    ap.add_argument("--margin", type=float, default=0.05, help="s of air a cut keeps from any line")
    ap.add_argument("--scene", type=float, default=0.3, help="ffmpeg scene-change threshold for --video")
    ap.add_argument("--isolate", type=float, default=0.3, help="a scene cut needs no other change within this many s")
    a = ap.parse_args()

    tl = json.load(open(a.timeline))
    lines = sorted(tl.get("lines", []), key=lambda l: l["t0"])
    shots = sorted(tl.get("shots", []), key=lambda s: s["t0"])
    D = float(tl.get("duration") or max(s["t1"] for s in shots))

    def clean(t):
        return all(not (l["t0"] - a.margin < t < l["t1"] + a.margin) for l in lines)

    def shot_at(t):
        for s in shots:
            if s["t0"] <= t < s["t1"]:
                return s["id"]
        return shots[-1]["id"] if shots else "?"

    cands = {}                                                        # t -> label
    for s in shots:
        t = math.ceil(s["t0"] * a.fps - 1e-9) / a.fps                 # the shot's first drawing (render_segs convention)
        if 0 < t < D and clean(t):
            cands[round(t, 6)] = f"start of {s['id']}"
    if a.video:
        sc = scene_cuts(a.video, a.scene)
        for i, t in enumerate(sc):
            if (i > 0 and t - sc[i - 1] < a.isolate) or (i + 1 < len(sc) and sc[i + 1] - t < a.isolate):
                continue                                              # flashes / strobes: not a clean cut point
            t = round(t * a.fps) / a.fps
            if 0 < t < D and clean(t) and all(abs(t - u) > 0.25 for u in cands):
                cands[round(t, 6)] = f"hard cut inside {shot_at(t)}"
    pts = [0.0] + sorted(cands) + [D]

    bits = a.cap_mb * 1e6 * 8
    lmax = bits / ((a.min_kbps + a.audio_kbps + a.overhead_kbps) * 1000)
    n = len(pts)
    INF = float("inf")
    kmin = max(1, math.ceil(D / lmax))
    plan = None
    for k in range(kmin, n):                                          # fewest parts first ...
        best = [[INF] * n for _ in range(k + 1)]                      # ... then minimise the longest part
        prev = [[-1] * n for _ in range(k + 1)]
        best[0][0] = 0.0
        for j in range(1, k + 1):
            for c in range(1, n):
                for i in range(c):
                    if best[j - 1][i] == INF:
                        continue
                    L = pts[c] - pts[i]
                    if L > lmax:
                        continue
                    v = max(best[j - 1][i], L)
                    if v < best[j][c]:
                        best[j][c], prev[j][c] = v, i
        if best[k][n - 1] < INF:
            # second pass over the k-part plans whose longest part is optimal: fewest cuts inside montages (prefer
            # shot starts), then the most even part lengths (smallest sum of squared lengths)
            mstar = best[k][n - 1] + 1e-6
            is_m = [0] + [int(cands[round(t, 6)].startswith("hard cut")) for t in pts[1:-1]] + [0]
            best2 = [[None] * n for _ in range(k + 1)]
            prev2 = [[-1] * n for _ in range(k + 1)]
            best2[0][0] = (0, 0.0)
            for j in range(1, k + 1):
                for c in range(1, n):
                    for i in range(c):
                        if best2[j - 1][i] is None or pts[c] - pts[i] > mstar:
                            continue
                        m0, q0 = best2[j - 1][i]
                        v = (m0 + is_m[c], q0 + (pts[c] - pts[i]) ** 2)
                        if best2[j][c] is None or v < best2[j][c]:
                            best2[j][c], prev2[j][c] = v, i
            idx, c = [], n - 1
            for j in range(k, 0, -1):
                idx.append(c)
                c = prev2[j][c]
            plan = [0] + idx[::-1]
            break
    if plan is None:
        gaps = sorted(((pts[i + 1] - pts[i], pts[i], pts[i + 1]) for i in range(n - 1)), reverse=True)[:3]
        print(f"no plan: some stretches between clean cut points are longer than {lmax:.1f} s (min {a.min_kbps:.0f} kbps):")
        for g, s0, s1 in gaps:
            print(f"  {s0:8.3f} -> {s1:8.3f}  ({g:.1f} s)")
        print("  -> pass --video to find hard cuts inside montages, or lower --min-kbps")
        sys.exit(1)

    print(f"{len(pts) - 2} clean cut candidates; longest part allowed {lmax:.1f} s at >= {a.min_kbps:.0f} kbps video")
    args = []
    for p in range(len(plan) - 1):
        s0, s1 = pts[plan[p]], pts[plan[p + 1]]
        dur = s1 - s0
        vbr = (bits / dur - (a.audio_kbps + a.overhead_kbps) * 1000) / 1000
        why = cands.get(round(s0, 6), "episode start")
        print(f"part{p + 1}: {s0:9.3f} -> {s1:9.3f}  {dur:7.2f} s  video {vbr:5.0f} kbps   cut: {why}")
        args.append(f'"{s0:.6f} {s1:.6f} part{p + 1}"'.replace(".000000 ", " ").replace(".000000\"", "\""))
    print("\nfinalize args:\n  " + " ".join(args))


if __name__ == "__main__":
    main()
