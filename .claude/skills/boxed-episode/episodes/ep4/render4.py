#!/usr/bin/env python3
"""BOXED ep4 renderer ('THE CAVE', 11:00). Animates on twos: one drawing per 2 frames at 24 fps.
   python3 render4.py                       # full render, 6 workers -> ep4/out/video.mp4
   python3 render4.py --stills 10 37 66 ... # single frames at those seconds -> ep4/out/still_<t>.png
   python3 render4.py --range A B path      # (internal / partial) render drawings [A,B) to path
Shot functions T###_* are collected from eng.shots_ep4 and the shots_ep4_<owner> modules (whichever exist);
a shot with no function yet renders as a labelled placeholder card."""
import importlib, json, math, os, subprocess, sys, time, traceback
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
EP = os.path.join(HERE, "ep4")
FF = "/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
OUT = os.path.join(EP, "out")
MODULES = ["shots_ep4", "shots_ep4_cave", "shots_ep4_game", "shots_ep4_escape", "shots_ep4_sun", "shots_ep4_ad", "shots_ep4_return", "shots_ep4_out"]
WIPES = {"T005_lights_up", "T033_ad", "T034_bumper", "T052_outside"}


def load():
    reg = {}
    for m in MODULES:
        try:
            mod = importlib.import_module("eng." + m)
        except ModuleNotFoundError as e:
            if e.name == "eng." + m:
                continue
            raise
        for k in dir(mod):
            if k.startswith("T") and k[1:4].isdigit() and callable(getattr(mod, k)):
                reg[k] = getattr(mod, k)
    tl = json.load(open(os.path.join(EP, "timeline.json")))
    acting = json.load(open(os.path.join(EP, "acting.json")))
    return reg, tl, acting


def placeholder(cv, sh, t):
    from eng.core import paint, PAL
    from eng.letters import paint_text
    import skia
    cv.drawRect(skia.Rect.MakeLTRB(0, 0, 1920, 1080), paint((40, 34, 60)))
    paint_text(cv, sh["id"], 960, 420, font="londrina", size=90, fill=PAL["yellow"], ink_w=4, shadow=(5, 5), seed=1)
    paint_text(cv, f"[{sh['owner']}]  {t:5.2f}s / {sh['t1'] - sh['t0']:.2f}s", 960, 540, font="londrina", size=50, fill=PAL["cream"], ink_w=0, shadow=None, seed=2)


def draw(d, reg, tl, acting):
    from eng import core
    from eng.core import new_surface, finish
    from eng.shots_a import ribbon_wipe
    t = d / 12.0
    core.set_drawing(d)
    shots = tl["shots"]
    sh = shots[-1]
    for s in shots:
        if s["t0"] <= t < s["t1"]:
            sh = s
            break
    A = acting[min(d, len(acting) - 1)]
    surf = new_surface()
    cv = surf.getCanvas()
    core.INKMUL = 1.0
    fn = reg.get(sh["id"])
    if fn is None:
        placeholder(cv, sh, t - sh["t0"])
    else:
        fn(cv, t - sh["t0"], t, A)
    core.INKMUL = 1.0
    for s in shots:
        if s["id"] in WIPES and abs(t - s["t0"]) < 0.3:
            ribbon_wipe(cv, (t - (s["t0"] - 0.3)) / 0.6, seed=int(s["t0"] * 10))
    img = finish(surf, d)
    return post(img, t, sh, tl)


def post(img, t, sh, tl):
    lt = t - sh["t0"]
    dur = sh["t1"] - sh["t0"]
    out = img
    if t < 0.4:
        out = (out.astype(np.float32) * (t / 0.4)).astype(np.uint8)
    if t > 657.6:
        k = min(1.0, (t - 657.6) / 0.8)
        out = (out.astype(np.float32) * (1 - k)).astype(np.uint8)
    hook = POST.get(sh["id"])
    if hook is not None:
        out = hook(out, lt, dur, t)
    return out


POST = {}            # shot id -> fn(img, lt, dur, t) for pixel-level effects (filled by shot modules via register_post)


def register_posts(reg_mods):
    for m in MODULES:
        try:
            mod = importlib.import_module("eng." + m)
        except ModuleNotFoundError:
            continue
        POST.update(getattr(mod, "POST", {}))


def render_range(a, b, path):
    reg, tl, acting = load()
    register_posts(MODULES)
    p = subprocess.Popen([FF, "-y", "-v", "error", "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", "1920x1080", "-framerate", "24", "-i", "-",
                          "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    t0 = time.time()
    for d in range(a, b):
        try:
            fr = np.ascontiguousarray(draw(d, reg, tl, acting))
        except Exception:
            print(f"ERROR at drawing {d} (t={d / 12:.2f})", flush=True); traceback.print_exc(); raise
        p.stdin.write(fr.tobytes()); p.stdin.write(fr.tobytes())
        if (d - a) % 120 == 0:
            print(f"[{a}-{b}] d={d} t={d / 12:.1f} {(time.time() - t0) / max(1, d - a + 1):.2f}s/drawing", flush=True)
    p.stdin.close(); p.wait()


def main_full(nw=4):
    os.makedirs(OUT, exist_ok=True)
    tl = json.load(open(os.path.join(EP, "timeline.json")))
    n = int(math.ceil(tl["duration"] * 12))
    cuts = [round(n * k / nw) for k in range(nw + 1)]
    env = dict(os.environ); env["LD_LIBRARY_PATH"] = os.path.join(HERE, "lib")
    procs, segs = [], []
    for k in range(nw):
        seg = os.path.join(OUT, f"seg{k}.mp4"); segs.append(seg)
        procs.append(subprocess.Popen([sys.executable, __file__, "--range", str(cuts[k]), str(cuts[k + 1]), seg], env=env))
    codes = [p.wait() for p in procs]
    if any(codes):
        raise SystemExit(f"worker failed: {codes}")
    with open(os.path.join(OUT, "segs.txt"), "w") as f:
        for s in segs:
            f.write(f"file '{s}'\n")
    subprocess.run([FF, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(OUT, "segs.txt"), "-c", "copy", os.path.join(OUT, "video.mp4")], check=True)
    print("VIDEO ->", os.path.join(OUT, "video.mp4"))


def stills(times, outdir=None):
    from PIL import Image
    outdir = outdir or OUT
    os.makedirs(outdir, exist_ok=True)
    reg, tl, acting = load()
    register_posts(MODULES)
    for tt in times:
        d = int(round(float(tt) * 12))
        t0 = time.time()
        Image.fromarray(draw(d, reg, tl, acting)).save(os.path.join(outdir, f"still_{float(tt):06.2f}.png"))
        print(f"still {tt} ({time.time() - t0:.1f}s)", flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--range":
        render_range(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
    elif len(sys.argv) > 1 and sys.argv[1] == "--stills":
        args = sys.argv[2:]
        od = None
        if "--out" in args:
            i = args.index("--out"); od = args[i + 1]; args = args[:i] + args[i + 2:]
        stills(args, od)
    else:
        main_full()
