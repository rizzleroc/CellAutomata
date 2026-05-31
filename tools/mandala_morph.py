"""Mandala morph film — sequence through sacred-geometry keyframes, morphing one
into the next. Each keyframe is a live Gray-Scott field folded into its own
n-fold symmetry; transitions blend the folded fields AND crossfade palettes, so
the symmetry order, texture, and colour all transform continuously. Loops.

  python3 tools/mandala_morph.py --out media/mandala_morph.mp4
"""
from __future__ import annotations
import argparse, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mandala as M
from cellauto.engine import Engine
from cellauto.rules import REGISTRY

FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
RULE = M.RULE

# keyframes spanning symmetry orders, textures, palettes
KEYS = [
    ("spots", 12, "gold"), ("labyrinth", 8, "ice"), ("chaos", 6, "amethyst"),
    ("coral", 16, "ember"), ("maze", 10, "emerald"), ("stripes", 9, "rose"),
    ("turbulence", 7, "ice"), ("solitons", 6, "gold"),
]


def fold(v, n):
    """Cheap D_n fold: C_n rotations (max) + one reflection."""
    acc = v.copy()
    for j in range(1, n):
        acc = np.maximum(acc, M._rot(v, 360.0 * j / n))
    acc = np.maximum(acc, np.ascontiguousarray(acc[:, ::-1]))
    return M.radial_mask(acc)


def colorize_blend(fa, pa, fb, pb, alpha, size):
    a = fa / (fa.max() + 1e-6)
    b = fb / (fb.max() + 1e-6)
    f = (1 - alpha) * a + alpha * b
    idx = (np.clip(f, 0, 1) ** 0.8 * 255).astype(np.uint8)
    ca = M.PALS[pa][idx].astype(np.float32)
    cb = M.PALS[pb][idx].astype(np.float32)
    rgb = ((1 - alpha) * ca + alpha * cb).astype(np.uint8)
    return Image.fromarray(rgb).resize((size, size), Image.BICUBIC)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", type=int, default=160)
    ap.add_argument("--size", type=int, default=1080)
    ap.add_argument("--hold", type=float, default=4.0)
    ap.add_argument("--trans", type=float, default=3.0)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--out", default="media/mandala_morph.mp4")
    a = ap.parse_args()

    print("warming engines ...")
    engines = []
    for name, n, pal in KEYS:
        rule = REGISTRY[RULE](**M.REGIMES[name])
        eng = Engine(width=a.grid, height=a.grid, rule=rule, seed=1)
        for _ in range(M.REG_STEPS[name]):
            eng.step()
        engines.append(eng)

    def field(i):
        return np.asarray(engines[i].state.v, np.float32)

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    wr = imageio_ffmpeg.write_frames(a.out, (a.size, a.size), fps=a.fps, codec="libx264",
        pix_fmt_in="rgb24", pix_fmt_out="yuv420p", macro_block_size=2,
        output_params=["-crf", "18", "-preset", "medium"])
    wr.send(None)
    lf = ImageFont.truetype(FB, 30)
    H, T = int(a.hold * a.fps), int(a.trans * a.fps)
    nk = len(KEYS)

    def label(img, txt):
        d = ImageDraw.Draw(img)
        d.text((28, a.size - 50), txt, font=lf, fill=(236, 242, 250))

    for ki in range(nk):
        name, n, pal = KEYS[ki]
        nj, (name2, n2, pal2) = (ki + 1) % nk, KEYS[(ki + 1) % nk]
        # hold on keyframe ki
        for _ in range(H):
            engines[ki].step()
            fa = fold(field(ki), n)
            img = colorize_blend(fa, pal, fa, pal, 0.0, a.size).convert("RGB")
            label(img, f"{n}-FOLD · {name}")
            wr.send(np.ascontiguousarray(np.asarray(img, np.uint8)).tobytes())
        # transition ki -> next
        for t in range(T):
            engines[ki].step(); engines[nj].step()
            alpha = (t + 1) / T
            ea = 0.5 - 0.5 * np.cos(np.pi * alpha)        # smoothstep
            fa = fold(field(ki), n)
            fb = fold(field(nj), n2)
            img = colorize_blend(fa, pal, fb, pal2, ea, a.size).convert("RGB")
            label(img, f"{n}-FOLD · {name}   →   {n2}-FOLD · {name2}")
            wr.send(np.ascontiguousarray(np.asarray(img, np.uint8)).tobytes())
        print(f"  {name}({n}) -> {name2}({n2})")
    wr.close()
    total = nk * (a.hold + a.trans)
    print(f"DONE -> {a.out} ({os.path.getsize(a.out)/1e6:.1f} MB, {total:.0f}s, {nk} keyframes)")


if __name__ == "__main__":
    main()
