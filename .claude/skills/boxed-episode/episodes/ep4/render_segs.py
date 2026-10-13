#!/usr/bin/env python3
"""Render ep4 shot-by-shot into ep4/out/segs/seg_<d0>.mp4 (drawing ranges), skipping segments that already exist,
then (with --concat) join all segments in order into ep4/out/video.mp4.
   python3 render_segs.py --owners main --workers 2      # render only shots of these owners
   python3 render_segs.py --shots T001_dark_open ...     # (re)render specific shots
   python3 render_segs.py --concat"""
import json, math, os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
EP = os.path.join(HERE, "ep4")
SEGS = os.path.join(EP, "out", "segs")
FF = "/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"


def ranges():
    tl = json.load(open(os.path.join(EP, "timeline.json")))
    n = int(math.ceil(tl["duration"] * 12))
    out = []
    for s in tl["shots"]:
        a = int(math.ceil(s["t0"] * 12 - 1e-9)); b = min(n, int(math.ceil(s["t1"] * 12 - 1e-9)))
        if b > a:
            out.append((s["id"], s["owner"], a, b))
    return out, n


def main():
    args = sys.argv[1:]
    rs, n = ranges()
    os.makedirs(SEGS, exist_ok=True)
    if "--concat" in args:
        files = []
        for sid, owner, a, b in rs:
            f = os.path.join(SEGS, f"seg_{a:05d}.mp4")
            if not os.path.exists(f):
                raise SystemExit(f"missing segment for {sid} ({a}-{b})")
            files.append(f)
        lst = os.path.join(SEGS, "list.txt")
        open(lst, "w").write("".join(f"file '{f}'\n" for f in files))
        subprocess.run([FF, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", os.path.join(EP, "out", "video.mp4")], check=True)
        print("VIDEO ->", os.path.join(EP, "out", "video.mp4"))
        return
    owners = args[args.index("--owners") + 1].split(",") if "--owners" in args else None
    shots = None
    if "--shots" in args:
        shots = [a for a in args[args.index("--shots") + 1:] if not a.startswith("--")]
    nw = int(args[args.index("--workers") + 1]) if "--workers" in args else 2
    force = "--force" in args
    todo = []
    for sid, owner, a, b in rs:
        if owners and owner not in owners:
            continue
        if shots and sid not in shots:
            continue
        f = os.path.join(SEGS, f"seg_{a:05d}.mp4")
        if os.path.exists(f) and not force and not shots:
            continue
        todo.append((sid, a, b, f))
    env = dict(os.environ); env["LD_LIBRARY_PATH"] = os.path.join(HERE, "lib")
    running = []
    t0 = time.time()
    while todo or running:
        while todo and len(running) < nw:
            sid, a, b, f = todo.pop(0)
            tmp = f + ".part.mp4"
            p = subprocess.Popen(["nice", "-n", "15", sys.executable, os.path.join(HERE, "render4.py"), "--range", str(a), str(b), tmp], env=env,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            running.append((p, sid, tmp, f, a, b))
        time.sleep(2)
        for item in running[:]:
            p, sid, tmp, f, a, b = item
            if p.poll() is not None:
                running.remove(item)
                if p.returncode == 0:
                    os.replace(tmp, f)
                    print(f"done {sid} ({b - a} drawings) t+{time.time() - t0:.0f}s", flush=True)
                else:
                    print(f"FAILED {sid}: {p.stderr.read().decode()[-1500:]}", flush=True)


if __name__ == "__main__":
    main()
