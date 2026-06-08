"""needle.py — find the needle in the haystack.

Every discovery hunt cached its evolved reaction-diffusion source fields
(discovery/{animhunt,mandalax}/src_*.npz, 240px + 360px). This re-folds ALL of
them through a richer compound-kaleidoscope sweep than any single hunt tried
(more fold orders, more octaves), scores each by the mandala complexity metric,
ranks globally, and lays the winners on one contact sheet so the truly perfect
visualizations can be picked by eye — then rendered at 2160 in curated palettes.

    python tools/needle.py --sweep     # score every source, render the contact sheet
    python tools/needle.py --render "id1,id2,..."   # final 2160 stills of the picks
"""
from __future__ import annotations
import argparse, glob, json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mandala_x as MX                      # Kal, compound, score, colorize, PAL

FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FM = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
RANK = "discovery/needle_rank.json"

# richer than any single hunt swept
N1 = (6, 8, 10, 12, 16, 24)
N2 = (3, 5, 6)
OCTS = (1, 2, 3)
PAL_CYCLE = ["nebula", "ice", "fire", "emerald", "amethyst", "aqua", "rose", "ember", "gold"]


def sources():
    out = []
    for grp in ("mandalax", "animhunt"):
        for f in sorted(glob.glob(f"discovery/{grp}/src_*.npz")):
            d = np.load(f)
            V = np.asarray(d["V"], np.float32)
            V = V / (V.max() + 1e-6)
            sid = f"{grp[:4]}_{os.path.basename(f).split('_')[1].split('.')[0]}"
            reg = str(d["regime"]) if "regime" in d else "gs"
            out.append(dict(id=sid, path=f, grid=V.shape[0], V=V, regime=reg))
    return out


def best_params(src, K=360):
    kal = MX.Kal(K, src["grid"])
    best = None
    for n1 in N1:
        for n2 in N2:
            if n2 >= n1:
                continue
            for octs in OCTS:
                sc = MX.score(MX.compound(kal, src["V"], n1, n2, octs))
                if best is None or sc > best[0]:
                    best = (sc, n1, n2, octs)
    return best


def render_tile(src, n1, n2, octs, pal, K):
    rgb = MX.colorize(MX.compound(MX.Kal(K, src["grid"]), src["V"], n1, n2, octs), pal)
    return Image.fromarray(rgb)


def sweep():
    srcs = sources()
    print(f"scoring {len(srcs)} sources x {len(N1)*len(N2)*len(OCTS)} symmetries ...")
    ranked = []
    for i, s in enumerate(srcs):
        sc, n1, n2, octs = best_params(s)
        ranked.append(dict(id=s["id"], regime=s["regime"], grid=s["grid"],
                           n1=n1, n2=n2, octs=octs, score=round(float(sc), 4)))
        if i % 10 == 0:
            print(f"  {i}/{len(srcs)}")
    ranked.sort(key=lambda r: -r["score"])
    json.dump({"ranked": ranked}, open(RANK, "w"), indent=2)
    by = {s["id"]: s for s in srcs}

    top = ranked[:48]
    cols, cell = 8, 320
    rows = (len(top) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell, rows * cell), (6, 7, 11))
    d = ImageDraw.Draw(sheet)
    fb, fm = ImageFont.truetype(FB, 22), ImageFont.truetype(FM, 17)
    for i, r in enumerate(top):
        pal = PAL_CYCLE[i % len(PAL_CYCLE)]
        tile = render_tile(by[r["id"]], r["n1"], r["n2"], r["octs"], pal, K=300).resize((cell - 8, cell - 8), Image.LANCZOS)
        x, y = (i % cols) * cell + 4, (i // cols) * cell + 4
        sheet.paste(tile, (x, y))
        d.text((x + 6, y + 4), f"#{i+1}", font=fb, fill=(245, 240, 220))
        d.text((x + 6, y + cell - 30), f"{r['id']} {r['n1']}x{r['n2']}o{r['octs']}", font=fm, fill=(180, 235, 230))
        d.text((x + cell - 78, y + 4), f"{r['score']:.3f}", font=fm, fill=(245, 220, 150))
    sheet.save("/tmp/needle_sheet.png")
    print(f"\nTOP 12:")
    for i, r in enumerate(top[:12]):
        print(f"  #{i+1:2d} {r['id']:10s} {r['regime']:10s} {r['n1']}x{r['n2']} o{r['octs']}  score={r['score']}")
    print("\ncontact sheet -> /tmp/needle_sheet.png   ranking -> " + RANK)


def render(ids):
    ranked = {r["id"]: r for r in json.load(open(RANK))["ranked"]}
    by = {s["id"]: s for s in sources()}
    os.makedirs("media/needles", exist_ok=True)
    fallback = ["nebula", "fire", "ice", "amethyst", "emerald", "aqua", "rose", "ember"]
    paths = []
    for i, spec in enumerate(ids):
        sid, _, pal = spec.partition(":")          # "id" or "id:palette"
        pal = pal or fallback[i % len(fallback)]
        r = ranked[sid]
        img = render_tile(by[sid], r["n1"], r["n2"], r["octs"], pal, K=2160)
        out = f"media/needles/needle_{i:02d}_{sid}_{pal}.jpg"
        img.save(out, quality=94)
        paths.append(out)
        print(f"  #{i} {sid} {r['n1']}x{r['n2']}o{r['octs']} {pal} score={r['score']} -> {out}")
    print(f"DONE — {len(ids)} needles @2160 -> media/needles/")
    return paths


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--render", type=str, default="")
    a = ap.parse_args()
    if a.sweep:
        sweep()
    elif a.render:
        render([x.strip() for x in a.render.split(",") if x.strip()])
    else:
        ap.error("need --sweep or --render id1,id2,...")


if __name__ == "__main__":
    main()
