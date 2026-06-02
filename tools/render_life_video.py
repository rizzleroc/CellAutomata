"""Render the real-time Stage XIII "live SEM feed" as a smooth 1080p60 MP4.

Offline cinematic render (NOT a runtime feature): ~7 simulation steps are
interpolated across ~350 frames at 60fps so bodies drift in real time while the
cilia fringe undulates; fixed-pattern grain (no flicker); baked 384px sprites.

Requires (bake/render-time only):  pip install imageio imageio-ffmpeg
Run:  python tools/render_life_video.py   ->  writes /tmp/shots/LIFE_8kq.mp4
Edit W/H/SUB/N_STEPS at the top for resolution / length / pacing.
"""
from __future__ import annotations
import math
import random
import numpy as np
from PIL import Image
import imageio
from cellauto.rules.abiogenesis.stage_life import AbiogenesisStageLife
from cellauto.rules.abiogenesis import life_sprites as LSP
from cellauto.rules.abiogenesis import life_sem as LS

W, H = 1920, 1080
# Real-time pacing: very few sim steps spread over many interpolated sub-frames,
# so bodies barely drift (like real microbes under a scope) while the CILIA do
# the visible motion. ~1/50 the body speed of the previous clip.
SUB = 50          # interpolated sub-frames per sim step
N_STEPS = 7       # sim steps captured  -> 7 steps over ~350 frames @ 60fps
MAX_ORG = 40
MARGIN = 0.08
GRAIN_SEED = 7    # fixed → coherent fixed-pattern grain (no flicker)


def snapshot(rule, state):
    orgs = sorted(state.organisms.values(), key=lambda o: -o.energy)[:MAX_ORG]
    div_oid = max(orgs, key=lambda o: (o.n_divisions, o.energy)).oid if orgs else -1
    d = {}
    gh, gw = state.substrate.shape
    for o in orgs:
        ef = min(o.energy / max(rule.e_div, 1e-6), 1.6)
        d[o.oid] = (o.x / max(1, gw - 1), o.y / max(1, gh - 1), ef, o.facing, o.oid == div_oid)
    return d, state.substrate.copy()


def main():
    cells, div = LSP.load_atlas()
    nF = len(div)
    rule = AbiogenesisStageLife(rng=random.Random(7), substrate_regen=0.02)
    st = rule.init_state(60, 60)
    for _ in range(26):
        st = rule.step(st)
    keys = [snapshot(rule, st)]
    for _ in range(N_STEPS):
        st = rule.step(st)
        keys.append(snapshot(rule, st))

    # stable bubbly floor texture (computed once → coherent across frames)
    floor_base = np.asarray(
        LSP._bubbly_substrate(W, H, np.random.RandomState(7)).convert("RGB"), np.float32
    )
    base_r = min(W, H) * 0.058

    writer = imageio.get_writer(
        "/tmp/shots/LIFE_8kq.mp4", fps=60, codec="libx264", quality=9,
        macro_block_size=8, ffmpeg_params=["-pix_fmt", "yuv420p", "-crf", "16"],
    )
    phase = 0.0
    fc = 0
    for ki in range(len(keys) - 1):
        (a, sub_a), (b, sub_b) = keys[ki], keys[ki + 1]
        shared = [o for o in b if o in a]
        shared.sort(key=lambda o: -b[o][2])
        for s in range(SUB):
            t = s / SUB
            phase += 0.05   # slow interior churn / body wobble (real time)
            fc += 1
            food = (1 - t) * sub_a + t * sub_b
            fimg = Image.fromarray(
                (np.clip(food, 0, 1) * 255).astype("uint8")
            ).resize((W, H), Image.BILINEAR)
            ffield = np.asarray(fimg, np.float32) / 255.0
            floor = floor_base * (0.30 + 0.70 * ffield)[..., None]
            canvas = Image.fromarray(np.clip(floor, 0, 255).astype("uint8"), "RGB").convert("RGBA")
            placed = []
            for oid in shared:
                ax, ay, aef, afac, _ = a[oid]
                bx, by, bef, bfac, bdiv = b[oid]
                gx = (1 - t) * ax + t * bx
                gy = (1 - t) * ay + t * by
                ef = (1 - t) * aef + t * bef
                depth = gy
                cx = (MARGIN + (1 - 2 * MARGIN) * gx) * W
                cy = (MARGIN + (1 - 2 * MARGIN) * gy) * H
                r = base_r * (0.7 + 0.5 * depth) * (0.85 + 0.35 * ef)
                placed.append((depth, oid, cx, cy, r, bfac, bdiv))
            placed.sort(key=lambda p: p[0])
            for depth, oid, cx, cy, r, fac, isdiv in placed:
                frame = int(phase * 0.5 + oid * 3) % nF
                spr = div[frame] if isdiv else cells[oid % len(cells)][frame]
                ang = fac * 45 + 2.5 * math.sin(phase * 0.5 + oid)   # gentle slow body sway
                beat = fc * 0.55 + oid                               # fast undulating cilia (per-cell offset)
                LSP._paste_cell(canvas, spr, cx, cy, r, depth, ang, furniture=True, jitter_key=oid, beat=beat)
            graded = LSP._grade(canvas, np.random.RandomState(GRAIN_SEED))
            finished = LS.photographic_finish(graded, seed=GRAIN_SEED)
            frame_img = np.asarray(LS._overlay(Image.fromarray(finished, "RGB")), dtype=np.uint8)
            writer.append_data(frame_img)
    writer.close()
    import os

    print("video", os.path.getsize("/tmp/shots/LIFE_8kq.mp4") // 1024, "KB",
          (len(keys) - 1) * SUB, "frames")


if __name__ == "__main__":
    main()
