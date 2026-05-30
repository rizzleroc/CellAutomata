"""Render the deep-time results: a 2x2 timelapse with a giant log-scale DAY
counter ramping 10 -> 1 trillion, plus a horizon contact sheet and a per-regime
verdict (freeze / coarsen / churn forever). Visuals are real simulation data;
horizons beyond the simulated range are labelled as the stationary attractor."""
from __future__ import annotations
import glob, json, os, numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def lut(stops):
    g = np.linspace(0, 1, 256); xs = np.array([s[0] for s in stops])
    cols = np.array([s[1] for s in stops], float)
    return np.stack([np.interp(g, xs, cols[:, c]) for c in range(3)], 1).astype(np.uint8)


PAL = [
    lut([(0, (68, 1, 84)), (.25, (59, 82, 139)), (.5, (33, 145, 140)), (.75, (94, 201, 98)), (1, (253, 231, 37))]),
    lut([(0, (0, 0, 4)), (.25, (60, 15, 92)), (.5, (152, 30, 112)), (.75, (242, 92, 80)), (.9, (252, 162, 92)), (1, (252, 253, 191))]),
    lut([(0, (4, 2, 2)), (.22, (70, 12, 8)), (.5, (175, 35, 12)), (.75, (245, 120, 25)), (1, (255, 240, 175))]),
    lut([(0, (2, 4, 18)), (.3, (6, 42, 84)), (.55, (10, 125, 155)), (.8, (44, 214, 194)), (1, (228, 255, 238))]),
]


def colorize(v, pal, vmax=0.42, gamma=0.82):
    return PAL[pal][(np.clip(v.astype(np.float32) / vmax, 0, 1) ** gamma * 255).astype(np.uint8)]


def fmt_day(d):
    d = float(d)
    if d >= 1e12: return f"{d/1e12:.2f} trillion"
    if d >= 1e9:  return f"{d/1e9:.2f} billion"
    if d >= 1e6:  return f"{d/1e6:.2f} million"
    return f"{int(d):,}"


def status(act, attractor):
    if attractor: return "attractor · stationary", (150, 214, 92)
    if act > 5e-3: return "churning", (255, 150, 90)
    if act > 5e-4: return "evolving", (120, 200, 255)
    return "frozen", (150, 160, 175)


def load():
    data = []
    for fp in sorted(glob.glob("discovery/deeptime/r*.npz")):
        d = np.load(fp, allow_pickle=True)
        data.append(dict(name=str(d["name"]), F=float(d["F"]), k=float(d["k"]),
                         vs=d["vs"], gens=d["gens"], acts=d["acts"],
                         ents=d["ents"], max_gen=int(d["max_gen"])))
    return data


def frame_at(d, day):
    """index of captured frame nearest to gen<=day; attractor flag if day>max_gen."""
    g = min(day, d["max_gen"])
    i = int(np.searchsorted(d["gens"], g))
    i = max(0, min(i, len(d["gens"]) - 1))
    return i, day > d["max_gen"]


def render_video(data, out="media/deep_time.mp4"):
    P, GUT, FPS, DUR = 525, 10, 30, 30
    W = GUT + P + GUT + P + GUT  # 1080
    N = DUR * FPS
    wr = imageio_ffmpeg.write_frames(out, (W, W), fps=FPS, codec="libx264",
        pix_fmt_in="rgb24", pix_fmt_out="yuv420p", macro_block_size=2,
        output_params=["-crf", "19", "-preset", "medium"])
    wr.send(None)
    pos = [(GUT, GUT + 70), (GUT * 2 + P, GUT + 70), (GUT, GUT * 2 + P + 70), (GUT * 2 + P, GUT * 2 + P + 70)]
    big = ImageFont.truetype(FB, 60); lab = ImageFont.truetype(FB, 27)
    sub = ImageFont.truetype(FR, 21); ban = ImageFont.truetype(FB, 24)
    for fi in range(N):
        t = fi / (N - 1)
        day = 10 ** (1 + 11 * t)                      # 10 -> 1e12
        canvas = Image.new("RGB", (W, W + 70), (8, 10, 15))
        d_all_attr = True
        for di, (d, (x, y)) in enumerate(zip(data, pos)):
            idx, attr = frame_at(d, day)
            d_all_attr &= attr
            tile = Image.fromarray(colorize(d["vs"][idx], di)).resize((P, P), Image.BICUBIC)
            canvas.paste(tile, (x, y))
            dr = ImageDraw.Draw(canvas)
            st, col = status(float(d["acts"][idx]), attr)
            dr.rectangle([x, y + P - 40, x + P, y + P], fill=(6, 8, 12))
            dr.text((x + 12, y + P - 35), d["name"], font=lab, fill=(238, 244, 250))
            tw = dr.textlength(st, font=sub)
            dr.text((x + P - tw - 12, y + P - 32), st, font=sub, fill=col)
        dr = ImageDraw.Draw(canvas)
        head = f"DAY  {fmt_day(day)}"
        hw = dr.textlength(head, font=big)
        dr.text(((W - hw) / 2, 6), head, font=big, fill=(245, 249, 253))
        if d_all_attr:
            msg = "BEYOND SIMULATED TIME — STATIONARY ATTRACTOR"
            mw = dr.textlength(msg, font=ban)
            dr.text(((W - mw) / 2, W + 70 - 34), msg, font=ban, fill=(150, 214, 92))
        fr = np.asarray(canvas, np.uint8)[:W]   # crop to square
        a = min(1.0, (fi + 1) / 10, (N - fi) / 10)
        if a < 0.999:
            fr = (fr.astype(np.float32) * a).astype(np.uint8)
        wr.send(np.ascontiguousarray(fr).tobytes())
    wr.close()
    print(f"video -> {out} ({os.path.getsize(out)/1e6:.1f} MB, {DUR}s)")


def render_contact(data, out="media/deep_time_horizons.png"):
    cols = [(10, "10 days"), (1_000, "1,000 days"), (100_000, "100,000 days"),
            (10**12, "1e6–1e12 days\n(attractor)")]
    C, LBL, HEAD, GAP = 250, 210, 64, 12
    W = LBL + len(cols) * (C + GAP) + GAP
    H = HEAD + len(data) * (C + GAP) + GAP
    img = Image.new("RGB", (W, H), (10, 12, 17)); d = ImageDraw.Draw(img)
    hf = ImageFont.truetype(FB, 24); rf = ImageFont.truetype(FB, 22); sf = ImageFont.truetype(FR, 18)
    for ci, (day, lab) in enumerate(cols):
        x = LBL + ci * (C + GAP) + GAP
        d.multiline_text((x + 6, 16), lab, font=hf, fill=(210, 224, 236), spacing=4)
    for ri, dd in enumerate(data):
        y = HEAD + ri * (C + GAP) + GAP
        d.text((14, y + C // 2 - 28), dd["name"], font=rf, fill=(238, 244, 250))
        d.text((14, y + C // 2 + 4), f"F={dd['F']:.4f}\nk={dd['k']:.4f}",
               font=sf, fill=(150, 168, 186))
        for ci, (day, lab) in enumerate(cols):
            idx, attr = frame_at(dd, day)
            x = LBL + ci * (C + GAP) + GAP
            tile = Image.fromarray(colorize(dd["vs"][idx], ri)).resize((C, C), Image.BICUBIC)
            img.paste(tile, (x, y))
            st, col = status(float(dd["acts"][idx]), attr)
            d.rectangle([x, y + C - 26, x + C, y + C], fill=(6, 8, 12))
            d.text((x + 8, y + C - 23), st, font=sf, fill=col)
    img.save(out)
    print(f"contact sheet -> {out}")


def verdicts(data):
    out = []
    for d in data:
        a0, a_end = float(d["acts"][3]), float(d["acts"][-1])
        if a_end < 5e-4:
            # find freeze gen
            fz = next((int(g) for g, a in zip(d["gens"], d["acts"]) if a < 5e-4), d["max_gen"])
            verdict = f"freezes into a static structure by ~day {fz:,}"
        elif a_end > 5e-3:
            verdict = f"churns forever — bounded chaos, still moving at day {int(d['gens'][-1]):,} (act {a_end:.4f})"
        else:
            verdict = f"slowly coarsens — activity {a0:.4f}→{a_end:.4f}, never fully settles"
        out.append(dict(name=d["name"], F=d["F"], k=d["k"], act_end=round(a_end, 5),
                        ent_end=round(float(d["ents"][-1]), 3), verdict=verdict))
        print(f"  {d['name']:16} {verdict}")
    json.dump(out, open("discovery/deeptime_verdicts.json", "w"), indent=2)
    return out


def main():
    data = load()
    print(f"loaded {len(data)} regimes")
    render_video(data)
    render_contact(data)
    print("VERDICTS:")
    verdicts(data)


if __name__ == "__main__":
    main()
