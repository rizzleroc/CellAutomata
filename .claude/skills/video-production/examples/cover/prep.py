#!/usr/bin/env python3
"""Cover prep: from art.png (2880 rectified, Real-ESRGAN x4) build the 2.5D layer stack + textures.
Polygons are authored on the 720-px preview grid (x4 -> 2880). Outputs layers/*.png (RGBA) + bg.png + spine.png."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "layers")
os.makedirs(OUT, exist_ok=True)
K = 4
art = np.asarray(Image.open(os.path.join(HERE, "art.png")).convert("RGB")).astype(np.float32)
S = art.shape[0]

POLY = {
    "title": [(0, 0), (720, 0), (720, 118), (690, 126), (640, 120), (590, 128), (560, 140), (520, 138), (480, 143), (430, 140), (380, 144),
              (330, 139), (280, 142), (230, 136), (180, 141), (130, 139), (80, 143), (40, 140), (0, 146)],
    "suits": [(0, 192), (40, 196), (75, 205), (100, 199), (140, 204), (160, 240), (166, 284), (226, 296), (229, 313), (172, 319), (150, 326),
              (128, 328), (124, 350), (104, 362), (98, 470), (0, 470)],
    "sign1": [(527, 157), (683, 151), (687, 253), (614, 256), (615, 300), (603, 300), (601, 258), (531, 258)],
    "sign2": [(559, 298), (703, 294), (705, 440), (632, 441), (633, 484), (619, 484), (618, 441), (561, 441)],
    "flag": [(431, 251), (470, 268), (535, 296), (531, 330), (520, 386), (480, 372), (414, 354), (420, 300)],
    "pedal": [(8, 528), (95, 519), (172, 559), (210, 598), (238, 628), (224, 692), (160, 702), (26, 645), (4, 566)],
    "ticket_vip": [(319, 610), (512, 588), (544, 688), (338, 708)],
    "ticket_cancel": [(488, 562), (530, 532), (692, 558), (704, 606), (690, 653), (509, 642)],
}
ELLIPSES = {"bowl": [((343, 396), (215, 189)), ((343, 204), (121, 26))]}
FEATHER = {"title": 6, "suits": 10, "sign1": 5, "sign2": 5, "flag": 4, "pedal": 6, "ticket_vip": 4, "ticket_cancel": 4, "bowl": 8}


def mask_of(name, grow=0):
    m = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(m)
    if name in POLY:
        pts = [(x * K, y * K) for x, y in POLY[name]]
        d.polygon(pts, fill=255)
        if grow:
            d.line(pts + [pts[0]], fill=255, width=grow * 2)
    else:
        for (cx, cy), (rx, ry) in ELLIPSES[name]:
            d.ellipse([(cx - rx - grow / K) * K, (cy - ry - grow / K) * K, (cx + rx + grow / K) * K, (cy + ry + grow / K) * K], fill=255)
    return m


def pushpull(rgb, w):
    """Fill pixels where w==0 from their surroundings (multi-scale push-pull)."""
    if min(rgb.shape[:2]) <= 4:
        tot = w.sum()
        mean = (rgb * w[..., None]).sum((0, 1)) / max(tot, 1e-6)
        return np.where(w[..., None] > 0, rgb, mean)
    h, wd = rgb.shape[:2]
    h2, w2 = (h + 1) // 2, (wd + 1) // 2
    pad_rgb = np.zeros((h2 * 2, w2 * 2, 3), np.float32); pad_rgb[:h, :wd] = rgb * w[..., None]
    pad_w = np.zeros((h2 * 2, w2 * 2), np.float32); pad_w[:h, :wd] = w
    sw = pad_w.reshape(h2, 2, w2, 2).sum((1, 3))
    srgb = pad_rgb.reshape(h2, 2, w2, 2, 3).sum((1, 3)) / np.maximum(sw[..., None], 1e-6)
    filled = pushpull(srgb, np.minimum(1.0, sw))
    up = np.stack([np.asarray(Image.fromarray(filled[..., c].astype(np.float32), 'F').resize((wd, h), Image.BILINEAR)) for c in range(3)], -1)
    return rgb * w[..., None] + up * (1 - w[..., None])


def soft(name, grow=0):
    return np.asarray(mask_of(name, grow).filter(ImageFilter.GaussianBlur(FEATHER[name] * K / 2)), np.float32) / 255.0


def save_layer(name, rgb, alpha):
    ys, xs = np.where(alpha > 0.004)
    y0, y1, x0, x1 = max(0, ys.min() - 4), min(S, ys.max() + 5), max(0, xs.min() - 4), min(S, xs.max() + 5)
    rgba = np.dstack([rgb[y0:y1, x0:x1], alpha[y0:y1, x0:x1] * 255]).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").save(os.path.join(OUT, f"{name}.png"))
    return [int(x0), int(y0)]


def local_fill(rgb, hole):
    """Fill `hole` (0..1) from nearby pixels at quarter resolution, then add grain."""
    sm = Image.fromarray(rgb.astype(np.uint8)).resize((S // 4, S // 4), Image.BOX)
    hw = np.asarray(Image.fromarray((hole * 255).astype(np.uint8)).resize((S // 4, S // 4), Image.BOX), np.float32) / 255.0
    f = pushpull(np.asarray(sm, np.float32), (hw < 0.01).astype(np.float32))
    f = np.asarray(Image.fromarray(np.clip(f, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2)), np.float32)
    fup = np.asarray(Image.fromarray(np.clip(f, 0, 255).astype(np.uint8)).resize((S, S), Image.BICUBIC), np.float32)
    rng = np.random.default_rng(11)
    fup = fup + rng.normal(0, 6.0, (S // 2, S // 2, 1)).repeat(2, 0).repeat(2, 1)
    h = np.asarray(Image.fromarray((hole * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(10)), np.float32)[..., None] / 255.0
    return rgb * (1 - h) + fup * h


def main():
    import json
    offs = {}
    m = {n: soft(n) for n in ("title", "suits", "sign1", "sign2", "flag", "ticket_cancel", "bowl")}
    for n in ("title", "suits", "sign1", "sign2", "flag", "ticket_cancel"):
        offs[n] = save_layer(n, art, m[n])
    flag_hole = np.asarray(mask_of("flag", grow=40), np.float32) / 255.0
    bowl_rgb = local_fill(art, flag_hole)
    offs["bowl"] = save_layer("bowl", bowl_rgb, m["bowl"] * (1 - m["suits"]))
    json.dump(offs, open(os.path.join(OUT, "offsets.json"), "w"))
    union = np.zeros((S, S), np.float32)
    for n in ("title", "suits", "sign1", "sign2", "flag", "ticket_cancel", "bowl"):
        union = np.maximum(union, np.asarray(mask_of(n, grow=70), np.float32) / 255.0)
    rng = np.random.default_rng(7)
    # background plate: fill under the movers, then add matching grain so the fill is not a smear
    known = (union < 0.5).astype(np.float32)
    small = 4
    sm = Image.fromarray(art.astype(np.uint8)).resize((S // small, S // small), Image.BOX)
    kw = Image.fromarray((known * 255).astype(np.uint8)).resize((S // small, S // small), Image.BOX)
    f = pushpull(np.asarray(sm, np.float32), (np.asarray(kw, np.float32) / 255.0 > 0.99).astype(np.float32))
    f = np.asarray(Image.fromarray(np.clip(f, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)), np.float32)
    fup = np.asarray(Image.fromarray(np.clip(f, 0, 255).astype(np.uint8)).resize((S, S), Image.BICUBIC), np.float32)
    rng = np.random.default_rng(7)
    grain = rng.normal(0, 7.0, (S // 2, S // 2, 1)).repeat(2, 0).repeat(2, 1)
    soft = np.asarray(Image.fromarray((known * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(12)), np.float32)[..., None] / 255.0
    bg = art * soft + (fup + grain) * (1 - soft)
    Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)).save(os.path.join(OUT, "bg.png"))
    # spine: paper texture + the cover's own title lettering rotated, + the advisory box
    paper = art[40 * K:120 * K, 0:20 * K].mean((0, 1))
    sp_h, sp_w = 3000, 250
    spine = np.ones((sp_h, sp_w, 3), np.float32) * paper
    spine += rng.normal(0, 6, (sp_h, sp_w, 1))
    title = Image.fromarray(art[22 * K:132 * K, 12 * K:570 * K].astype(np.uint8))
    tit = np.asarray(title, np.float32)
    redness = np.clip((tit[..., 0] - (tit[..., 1] + tit[..., 2]) / 2 - 30) / 60, 0, 1)
    tl = Image.fromarray(np.dstack([tit, redness * 255]).astype(np.uint8), "RGBA").rotate(-90, expand=True)
    tl = tl.resize((int(tl.width * 2280 / tl.height), 2280), Image.LANCZOS)
    sp = Image.fromarray(np.clip(spine, 0, 255).astype(np.uint8)).convert("RGBA")
    sp.alpha_composite(tl, ((sp_w - tl.width) // 2, 120))
    pa = Image.fromarray(art[14 * K:101 * K, 582 * K:701 * K].astype(np.uint8)).rotate(-90, expand=True)
    pa = pa.resize((int(pa.width * 190 / pa.height * 0 + 190), int(pa.height * 190 / pa.width)), Image.LANCZOS) if False else pa.resize((200, int(200 * pa.height / pa.width)))
    sp.alpha_composite(pa.convert("RGBA"), ((sp_w - pa.width) // 2, sp_h - pa.height - 90))
    sp.convert("RGB").save(os.path.join(HERE, "spine.png"))
    Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)).resize((720, 720), Image.LANCZOS).save(os.path.join(HERE, "bg_720.png"))
    print("layers ->", OUT)


if __name__ == "__main__":
    main()
