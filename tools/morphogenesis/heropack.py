"""HEROPACK — turn uploaded hero clips into genuinely-viral vertical cuts at volume (the chosen path).
Per hero: auto-detect the strongest window (energy curve), then emit a variant matrix — hero+SEM REVEAL,
hero-only boomerang LOOP, optional VO — across the per-specimen hook bank. Reuses blend_cut.py + sora_finish.py
(the proven-quality engines). Outputs downloadable 1080x1920 mp4s into day folders + manifest.

  python3 tools/morphogenesis/heropack.py one <hero.mp4> <specimen> [vo.mp3]   # variants from ONE hero (proof)
  python3 tools/morphogenesis/heropack.py pack <map.json> <day>               # map=[{file,specimen,vo?}] -> a day
Specimen slug = grayscott|rna|chirality|coacervate|code|natsel|life|luca|minerals|soup|vents. Run from repo root.
"""
import os, sys, json, subprocess, re
import imageio_ffmpeg
from PIL import Image
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import factory  # reuse HOOKS
FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(HERE + "/../..")
OUT = "/tmp/factory"

def probe_dur(p):
    err = subprocess.run([FF, "-i", p], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err)
    return int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3)) if m else 8.0

def strong_window(hero, win=3.4):
    """Slide a `win`-second window over the clip's energy curve; return the (t0,t1) with the most on-screen action."""
    dur = probe_dur(hero); step = 0.5; ts = []; lit = []
    t = 0.0
    while t < dur - 0.05:
        out = subprocess.run([FF, "-nostdin", "-loglevel", "error", "-ss", f"{t}", "-i", hero,
                              "-frames:v", "1", "-vf", "scale=160:-1", "-f", "image2pipe", "-vcodec", "png", "-"],
                             capture_output=True).stdout
        try:
            im = Image.open(__import__("io").BytesIO(out)).convert("L"); a = np.asarray(im)
            lit.append(float((a > 40).mean()))
        except Exception:
            lit.append(0.0)
        ts.append(t); t += step
    if not ts: return 0.0, min(win, dur)
    k = max(1, int(round(win/step))); best_i, best_v = 0, -1
    for i in range(0, max(1, len(lit)-k+1)):
        v = sum(lit[i:i+k])/k
        if v > best_v: best_v, best_i = v, i
    t0 = ts[best_i]; return round(t0, 2), round(min(dur, t0+win), 2)

def variants(hero, specimen, t0, t1, vo=None):
    hooks = factory.HOOKS.get("ab_"+specimen, factory.HOOKS["_default"])
    jobs = []
    for i, (hk, pay, brand) in enumerate(hooks):
        gid = f"{specimen}_{i:02d}"
        caps = [[0.3, 4.6, hk, "hook"], [6.2, 10.0, pay, "sub"], [10.2, 13.6, "it's only a simulation", "sub"]]
        blend = {"src": hero, "sem": "ab_"+specimen, "id": f"hp_{gid}_blend", "t0": t0, "t1": t1,
                 "style": "reveal", "caps": caps, "brand": brand}
        if vo: blend["vo"] = vo
        jobs.append(("blend", blend))
        jobs.append(("loop", {"src": hero, "t0": t0, "t1": t1, "hook": hk, "sub": pay, "brand": brand,
                              "id": f"hp_{gid}_loop"}))
    return jobs

def run_job(kind, cfg, day_dir):
    if kind == "blend":
        env = dict(os.environ, BLEND_CFG=json.dumps(cfg)); script = "blend_cut.py"; src = f"/tmp/blend_{cfg['id']}.mp4"
    else:
        env = dict(os.environ, SORA_CFG=json.dumps(cfg)); script = "sora_finish.py"; src = f"/tmp/viral_{cfg['id']}.mp4"
    r = subprocess.run([sys.executable, f"{HERE}/{script}", *( [] if kind=="blend" else [])], env=env, cwd=ROOT,
                       capture_output=True, text=True)
    if not os.path.exists(src):
        return {"id": cfg["id"], "ok": False, "kind": kind, "err": (r.stderr or r.stdout)[-280:]}
    out = f"{day_dir}/{cfg['id']}.mp4"
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", src, "-c:v", "libx264", "-crf", "24",
                    "-preset", "veryfast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "144k",
                    "-movflags", "+faststart", out], check=True)
    return {"id": cfg["id"], "ok": True, "kind": kind, "file": out, "mb": round(os.path.getsize(out)/1e6, 1)}

def produce(pairs, day_dir, label):
    os.makedirs(day_dir, exist_ok=True); man = []
    for (hero, specimen, vo) in pairs:
        t0, t1 = strong_window(hero)
        print(f"[{specimen}] {os.path.basename(hero)} strong window {t0}-{t1}s", flush=True)
        for kind, cfg in variants(hero, specimen, t0, t1, vo):
            res = run_job(kind, cfg, day_dir); man.append(res)
            print(("  ok " if res["ok"] else "  FAIL ") + f'{res["kind"]:5} {res["id"]}' +
                  (f'  {res["mb"]}MB' if res["ok"] else f'  {res.get("err","")}'), flush=True)
    json.dump(man, open(f"{day_dir}/manifest.json", "w"), indent=1)
    ok = sum(1 for m in man if m["ok"]); print(f"[{label}] {ok}/{len(man)} ok -> {day_dir}", flush=True)
    return man

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "one"
    if mode == "one":
        hero, specimen = sys.argv[2], sys.argv[3]; vo = sys.argv[4] if len(sys.argv) > 4 else None
        produce([(hero, specimen, vo)], f"{OUT}/heroproof", "heroproof")
    elif mode == "pack":
        spec = json.load(open(sys.argv[2])); day = int(sys.argv[3])
        pairs = [(e["file"], e["specimen"], e.get("vo")) for e in spec]
        produce(pairs, f"{OUT}/day_{day:02d}", f"day{day}")
    else:
        print("usage: heropack.py one <hero.mp4> <specimen> [vo.mp3] | pack <map.json> <day>")

if __name__ == "__main__":
    main()
