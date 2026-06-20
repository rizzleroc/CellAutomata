"""FACTORY — batch-produce downloadable vertical viral cuts from the SEM bins, organized for a 10-day,
50/day posting schedule (500 total). Backbone = viral_cut.py (free, local, reliable) driven by a
hook-bank x specimen x format x scene matrix. Each output is a self-contained, downloadable 1080x1920 mp4.

  python3 tools/morphogenesis/factory.py plan              # print the deterministic 500-slot schedule
  python3 tools/morphogenesis/factory.py proof             # ~6 diverse cuts to validate quality
  python3 tools/morphogenesis/factory.py day <N>           # render all 50 slots for day N (0-9)
  python3 tools/morphogenesis/factory.py range <a> <b>     # render global slots [a,b)
Run from repo root. Outputs -> /tmp/factory/day_NN/ + day_NN/manifest.json
"""
import os, sys, json, subprocess
import numpy as np
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(HERE + "/../..")
OUT = "/tmp/factory"

# specimens with SEM bins present (verified at runtime). Tag -> viral_cut STAGE key.
SPECIMENS = ["ab_grayscott", "ab_rna", "ab_chirality", "ab_coacervate", "ab_code",
             "ab_natsel", "ab_life", "ab_luca", "ab_minerals", "ab_soup", "ab_vents"]

# Hook bank — curiosity-gap + the "looks alive -> it's only X" reveal (the viral mechanic). 4 per specimen.
HOOKS = {
 "ab_grayscott": [("THIS ISN'T ALIVE","but it divides like a cell","JUST CHEMISTRY"),
                  ("IS THIS ALIVE?","it grows, splits, spreads…","it's only a simulation"),
                  ("NO DNA. NO LIFE.","yet it behaves like a cell","REACTION–DIFFUSION"),
                  ("WATCH IT DIVIDE","two chemicals, two rules","LIFELIKE CHEMISTRY")],
 "ab_rna": [("THE FIRST LIFE?","a molecule copying itself","RNA WORLD"),
            ("THIS MOLECULE REPLICATES","life's oldest trick","RNA WORLD"),
            ("BEFORE DNA…","RNA did everything","THE RNA WORLD"),
            ("LIFE STARTED HERE","one self-copying strand","RNA WORLD")],
 "ab_chirality": [("WHY YOU'RE LEFT-HANDED INSIDE","life had to pick a side","HOMOCHIRALITY"),
                  ("NATURE CHOSE A SIDE","and never looked back","HOMOCHIRALITY"),
                  ("MIRROR-IMAGE MOLECULES","only one kind survived","HOMOCHIRALITY"),
                  ("THE GREAT SYMMETRY BREAK","why life is one-handed","HOMOCHIRALITY")],
 "ab_coacervate": [("THE FIRST 'CELLS'","oily drops, no membrane yet","COACERVATES"),
                   ("LIFE IN A DROPLET","before the cell membrane","COACERVATES"),
                   ("NOT A CELL — A DROP","but it concentrates life","COACERVATES"),
                   ("PROTO-CELLS","chemistry learns to contain itself","COACERVATES")],
 "ab_code": [("THE CODE WROTE ITSELF","how DNA learned its alphabet","GENETIC CODE"),
             ("WHERE THE CODE BEGAN","chemistry into information","GENETIC CODE"),
             ("LIFE'S FIRST LANGUAGE","written by molecules","THE GENETIC CODE"),
             ("3 LETTERS = 1 AMINO ACID","the code emerges","GENETIC CODE")],
 "ab_natsel": [("SURVIVAL BEFORE LIFE","the fitter chemistry wins","SELECTION"),
               ("EVOLUTION WITHOUT LIFE","molecules compete to exist","SELECTION"),
               ("THE FITTEST CHEMISTRY","outlasts the rest","NATURAL SELECTION"),
               ("DARWIN, BUT MOLECULAR","selection before cells","SELECTION")],
 "ab_life": [("CODE THAT'S ALIVE","it eats, divides, evolves","DIGITAL LIFE"),
             ("IS SOFTWARE ALIVE?","it reproduces and mutates","DIGITAL LIFE"),
             ("LIVING PIXELS","born, breeding, dying","ARTIFICIAL LIFE"),
             ("THIS PROGRAM EVOLVES","no one designed this","DIGITAL LIFE")],
 "ab_luca": [("YOUR OLDEST ANCESTOR","everything alive shares it","LUCA"),
             ("MEET YOUR GREAT…GRANDPARENT","4 billion years back","LUCA"),
             ("ONE ANCESTOR FOR ALL LIFE","you, trees, bacteria","LUCA"),
             ("THE ROOT OF LIFE","the last common ancestor","LUCA")],
 "ab_minerals": [("ROCK BUILT THE FIRST CHAINS","clay as a factory","MINERAL CATALYSIS"),
                 ("LIFE FROM STONE","minerals assembled molecules","MINERAL CATALYSIS"),
                 ("THE FIRST CATALYST WAS ROCK","not an enzyme","MINERAL CATALYSIS"),
                 ("CLAY KICK-STARTED LIFE","a mineral assembly line","MINERAL CATALYSIS")],
 "ab_soup": [("EARTH BEFORE LIFE","lightning making life's bricks","PRIMORDIAL SOUP"),
             ("THE RECIPE FOR LIFE","just add lightning","PRIMORDIAL SOUP"),
             ("WHERE IT ALL BEGAN","a sea of raw ingredients","PRIMORDIAL SOUP"),
             ("LIFE'S FIRST KITCHEN","sparks + simple molecules","PRIMORDIAL SOUP")],
 "ab_vents": [("LIFE BEGAN IN THE DARK","not a pond — a deep-sea vent","ALKALINE VENTS"),
              ("NO SUN NEEDED","life started at the seafloor","HYDROTHERMAL VENTS"),
              ("BORN IN THE ABYSS","heat + rock + water","ALKALINE VENTS"),
              ("THE CRADLE WAS HOT","deep-sea chemistry","HYDROTHERMAL VENTS")],
 "_default": [("THIS ISN'T ALIVE","yet it behaves like life","JUST CHEMISTRY")],
}

# Format = pacing. durs are per-beat frames @24fps.
FORMATS = {"reveal": [120,120,110], "punch": [90,80,90], "slow": [150,150,140]}
# Scene = (ctr nudge, wide multiplier) applied ON TOP of the auto-framed base -> zoom/pan variety, no dead space.
SCENES = [(0.0, 1.0), (0.0, 0.78), (0.06, 0.60)]

def avail(tag): return os.path.exists(f"/tmp/g_{tag}_meta.json")

# --- content-aware auto-framing: zoom to where the structure actually is (kills dead space) ---
_AF = {}
def _bin_path(tag):
    for m in ("c", "w"):
        p = f"/tmp/g_{tag}_{m}.bin"
        if os.path.exists(p): return p
    return None
def autoframe(tag):
    """Return (ctr[x,y], wide) framing the bright content with margin. Cached per specimen."""
    if tag in _AF: return _AF[tag]
    try:
        m = json.load(open(f"/tmp/g_{tag}_meta.json")); pw, ph = m["W"]*m["SC"], m["H"]*m["SC"]; fb = pw*ph*4
        fr = int(0.7*(m["frames"]-1)); bp = _bin_path(tag)
        with open(bp, "rb") as fp:
            fp.seek(fr*fb); a = np.frombuffer(fp.read(fb), np.uint8).reshape(ph, pw, 4)[:, :, :3]
        lum = a.mean(2).astype(np.float64)
        lum = np.maximum(0.0, lum - np.percentile(lum, 65))   # drop dim substrate -> mass = real structure
        if lum.sum() < 1e3:
            _AF[tag] = ([0.5, 0.5], 0.92); return _AF[tag]
        rowm, colm = lum.sum(1), lum.sum(0)
        yi, xi = np.arange(ph)/ph, np.arange(pw)/pw
        wy, wx = rowm/rowm.sum(), colm/colm.sum()
        cy, cx = float((yi*wy).sum()), float((xi*wx).sum())
        sy = float(np.sqrt(((yi-cy)**2*wy).sum())); sx = float(np.sqrt(((xi-cx)**2*wx).sum()))
        need = max(4.2*sy, 4.2*sx*(16/9)) * 1.12              # frame the bright concentration in 9:16
        wide = min(0.97, max(0.32, need))
        _AF[tag] = ([round(cx, 3), round(cy, 3)], round(wide, 3))
    except Exception:
        _AF[tag] = ([0.5, 0.5], 0.9)
    return _AF[tag]

# Vivid grade applied at the lean re-encode: lift exposure, pop contrast/saturation, crisp the relief.
VIVID = "eq=brightness=0.05:contrast=1.24:saturation=1.5:gamma=0.94,unsharp=5:5:0.7:5:5:0.0"

def all_slots():
    """Deterministic, stable 500-ish slot list. Order interleaves specimens so each day is varied."""
    grid = []
    specs = [t for t in SPECIMENS if avail(t)]
    for fmt in FORMATS:
        for si in range(len(SCENES)):
            for hi in range(4):
                for tag in specs:
                    grid.append((tag, fmt, si, hi))
    return grid  # ~ len(specs)*3*3*4

def cfg_for(slot, gid):
    tag, fmt, si, hi = slot
    hooks = HOOKS.get(tag, HOOKS["_default"]); h = hooks[hi % len(hooks)]
    base_ctr, base_wide = autoframe(tag)
    nudge, wmult = SCENES[si]
    ctr = [min(0.82, max(0.18, base_ctr[0] + nudge)), base_ctr[1]]
    wide = round(max(0.22, base_wide * wmult), 3)
    return {"tag": tag, "id": gid, "hook": h[0], "payoff": h[1], "brand": h[2],
            "durs": FORMATS[fmt], "ctr": ctr, "wide": wide}

def render_one(slot, gid, day_dir):
    c = cfg_for(slot, gid)
    env = dict(os.environ, VCUT_CFG=json.dumps(c))
    r = subprocess.run([sys.executable, f"{HERE}/viral_cut.py", "render"], env=env, cwd=ROOT,
                       capture_output=True, text=True)
    src = f"/tmp/viral_{gid}.mp4"
    if not os.path.exists(src):
        return {"id": gid, "ok": False, "err": (r.stderr or r.stdout)[-300:]}
    out = f"{day_dir}/{gid}.mp4"   # lean re-encode + vivid grade + VBV cap (social-sized, ~15-22MB)
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", src, "-vf", VIVID,
                    "-c:v", "libx264", "-crf", "24", "-maxrate", "9M", "-bufsize", "14M", "-preset", "medium",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out], check=True)
    mb = os.path.getsize(out) / 1e6
    return {"id": gid, "ok": True, "tag": slot[0], "fmt": slot[1], "scene": slot[2], "hook": c["hook"],
            "file": out, "mb": round(mb, 1)}

def render_batch(slots, gids, day_dir, label):
    os.makedirs(day_dir, exist_ok=True)
    man = []
    for slot, gid in zip(slots, gids):
        res = render_one(slot, gid, day_dir)
        man.append(res); print(("  ok " if res["ok"] else "  FAIL ") + gid + (f'  {res.get("mb")}MB  "{res.get("hook")}"' if res["ok"] else f'  {res.get("err","")}'), flush=True)
    json.dump(man, open(f"{day_dir}/manifest.json", "w"), indent=1)
    ok = sum(1 for m in man if m["ok"])
    print(f"[{label}] {ok}/{len(man)} ok -> {day_dir}/manifest.json", flush=True)
    return man

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "plan"
    slots = all_slots()
    if mode == "plan":
        print(f"specimens with bins: {[t for t in SPECIMENS if avail(t)]}")
        print(f"total slots: {len(slots)}  (= {len(slots)//50} full days of 50 + {len(slots)%50})")
        for d in range(min(10, (len(slots)+49)//50)):
            chunk = slots[d*50:(d+1)*50]
            tags = {}
            for s in chunk: tags[s[0]] = tags.get(s[0], 0)+1
            print(f"  day {d}: {len(chunk)} slots  mix={tags}")
        return
    if mode == "proof":
        picks = [("ab_grayscott","reveal",0,0),("ab_rna","punch",1,1),("ab_coacervate","slow",2,0),
                 ("ab_life","reveal",1,2),("ab_vents","punch",0,3),("ab_chirality","slow",2,1)]
        gids = [f"proof_{i:02d}_{s[0].split('_')[1]}" for i, s in enumerate(picks)]
        render_batch(picks, gids, f"{OUT}/proof", "proof")
        return
    if mode == "day":
        d = int(sys.argv[2]); chunk = slots[d*50:(d+1)*50]
        gids = [f"d{d:02d}_{i:02d}_{s[0].split('_')[1]}" for i, s in enumerate(chunk)]
        render_batch(chunk, gids, f"{OUT}/day_{d:02d}", f"day{d}")
        return
    if mode == "range":
        a, b = int(sys.argv[2]), int(sys.argv[3]); chunk = slots[a:b]
        gids = [f"r{a+i:03d}_{s[0].split('_')[1]}" for i, s in enumerate(chunk)]
        render_batch(chunk, gids, f"{OUT}/range_{a}_{b}", f"range{a}:{b}")
        return
    print("usage: factory.py plan|proof|day <N>|range <a> <b>")

if __name__ == "__main__":
    main()
