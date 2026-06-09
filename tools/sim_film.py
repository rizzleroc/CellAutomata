"""Film the LIVE abiogenesis simulation — the app's own visualization, in motion.

Unlike sem_feed.py (which pans over static stills), this drives the REAL engine:
for each canonical stage it runs cellauto's actual rule from its seeded initial
state and captures `render_rgb` as the simulation evolves, so what you see is the
genuine app visualization developing frame-by-frame — primordial soup churning,
Gray-Scott spots emerging and dividing, RAF networks, vesicles, selection — each
with its real governing equation + citation. (Filmed per-stage standalone rather
than via the auto-pipeline, whose soup->RD handoff seed decays to a flat field.)

  python3 tools/sim_film.py            # -> media/sim/abiogenesis_live.mp4
"""
from __future__ import annotations
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cellauto.rules.abiogenesis.pipeline import STAGE_CLASSES, STAGE_INFO, AbiogenesisExtendedPipelineRule

FF = imageio_ffmpeg.get_ffmpeg_exe()
OUT = "media/sim"
W, H = 1080, 1920
FIELD = 1000
FX, FY = (W - FIELD) // 2, 300
FPS = 30
GRID = 180
EXTENDED = True                           # True = full 12-stage arc (Soup..LUCA); False = canonical 5
CAPS = 150                                # captured frames per stage  (~5s)
BG = (8, 10, 16)
TEAL = (60, 212, 200)
CREAM = (233, 226, 208)
DIM = (124, 134, 150)

# steps advanced per captured frame, per stage index — paced from the validation
# growth curves so each pattern fully forms within its filmed window.
SPS_CANON = {0: 2, 1: 8, 2: 4, 3: 4, 4: 3}
SPS_EXT = {0: 2, 1: 4, 2: 8, 3: 3, 4: 5, 5: 4, 6: 2, 7: 6, 8: 5, 9: 5, 10: 3, 11: 6}


def _font(sz, kind="sans", bold=True):
    paths = {
        "serif": "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "mono": "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "sans": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    }
    p = paths[kind]
    return ImageFont.truetype(p, sz) if os.path.exists(p) else ImageFont.load_default()


def _spaced(s):
    return "  ".join(s.upper())


def _text(cv, xy, s, font, fill, a=1.0, anchor="mm", spacing=8):
    if a <= 0.01:
        return
    ov = Image.new("RGBA", cv.size, (0, 0, 0, 0))
    ImageDraw.Draw(ov).multiline_text(xy, s, font=font, fill=(*fill, int(255 * min(1.0, a))),
                                      anchor=anchor, align="center", spacing=spacing)
    cv.alpha_composite(ov)


def _wrap(draw, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= maxw:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def _rgb(rule, state):
    a = np.asarray(rule.render_rgb(state))
    if a.dtype != np.uint8:
        a = (np.clip(a, 0, 1) * 255).astype(np.uint8)
    if a.ndim == 2:
        a = np.repeat(a[..., None], 3, 2)
    return np.ascontiguousarray(a[..., :3])


_F = {}
def _fonts():
    if not _F:
        _F.update(badge=_font(30), tit=_font(54, "serif"), eq=_font(27, "mono"),
                  cite=_font(26, "serif", False), leg=_font(25, "sans", False), sig=_font(22))
    return _F


def _compose(rgb, info, stage, step, discrete, gin=1.0):
    f = _fonts()
    cv = Image.new("RGBA", (W, H), (*BG, 255))
    field = Image.fromarray(rgb).resize((FIELD, FIELD), Image.NEAREST if discrete else Image.LANCZOS)
    if gin < 1.0:
        field = Image.fromarray((np.asarray(field, np.float32) * gin).astype(np.uint8))
    cv.paste(field, (FX, FY))
    d = ImageDraw.Draw(cv)
    d.rectangle([FX - 1, FY - 1, FX + FIELD, FY + FIELD], outline=(*TEAL, 110), width=1)
    for (cx, cy) in [(FX, FY), (FX + FIELD, FY), (FX, FY + FIELD), (FX + FIELD, FY + FIELD)]:
        d.line([(cx - 22, cy), (cx + 22, cy)], fill=(*TEAL, 150), width=1)
        d.line([(cx, cy - 22), (cx, cy + 22)], fill=(*TEAL, 150), width=1)
    _text(cv, (W // 2, 150), f"▶  {_spaced('live simulation')}   ·   STAGE {stage}", f["badge"], TEAL, gin)
    _text(cv, (W // 2, 232), info.title, f["tit"], CREAM, gin)
    eqs = "\n".join(_wrap(d, info.principle, f["eq"], W - 120))
    _text(cv, (W // 2, FY + FIELD + 70), eqs, f["eq"], CREAM, 0.96)
    ny = FY + FIELD + 70 + (eqs.count("\n") + 1) * 38 + 22
    _text(cv, (W // 2, ny), info.citation, f["cite"], TEAL, 0.85)
    legs = "\n".join(_wrap(d, info.legend, f["leg"], W - 150))
    _text(cv, (W // 2, ny + 64), legs, f["leg"], DIM, 0.85)
    _text(cv, (W // 2, 1858), _spaced("cellautomata  ·  abiogenesis  ·  ") + f"step {step:04d}", f["sig"], DIM, 0.6)
    return np.ascontiguousarray(np.asarray(cv.convert("RGB"), np.uint8))


def render():
    os.makedirs(OUT, exist_ok=True)
    silent = "/tmp/sim_film_silent.mp4"
    wr = imageio_ffmpeg.write_frames(silent, (W, H), fps=FPS, codec="libx264",
        pix_fmt_in="rgb24", pix_fmt_out="yuv420p", macro_block_size=8,
        output_params=["-crf", "19", "-preset", "medium"])
    wr.send(None)
    if EXTENDED:
        ep = AbiogenesisExtendedPipelineRule()
        roster = list(zip(ep.stage_classes, ep.stage_infos)); sps_map = SPS_EXT
    else:
        roster = list(zip(STAGE_CLASSES, STAGE_INFO)); sps_map = SPS_CANON
    for si, (Cls, info) in enumerate(roster):
        rule = Cls()
        if hasattr(rule, "rng"):
            import random
            rule.rng = random.Random(7)
        state = rule.init_state(GRID, GRID)
        discrete = getattr(rule, "renderer_kind", "field") == "discrete"
        sps = sps_map.get(si, 4)
        step = 0
        for fi in range(CAPS):
            for _ in range(sps):
                state = rule.step(state); step += 1
            gin = min(fi / 8.0, 1.0)          # brief fade-in at each stage start
            wr.send(_compose(_rgb(rule, state), info, si, step, discrete, gin).tobytes())
        print(f"  stage {si} {info.title:22s} {CAPS} frames, {step} steps")
    wr.close()

    dur = (len(roster) * CAPS) / FPS
    out = f"{OUT}/abiogenesis_live_{'12stage' if EXTENDED else '5stage'}.mp4"
    af = (f"[1:a][2:a]amix=inputs=2,volume=0.12,lowpass=f=460,"
          f"afade=t=in:st=0:d=2,afade=t=out:st={dur-2.2:.1f}:d=2.2[a]")
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", silent,
                    "-f", "lavfi", "-t", f"{dur}", "-i", "sine=frequency=73.42:sample_rate=44100",
                    "-f", "lavfi", "-t", f"{dur}", "-i", "sine=frequency=110:sample_rate=44100",
                    "-filter_complex", af, "-map", "0:v", "-map", "[a]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "144k", "-shortest",
                    "-movflags", "+faststart", out], check=True)
    print(f"-> {out}  ({os.path.getsize(out)/1e6:.1f} MB, {dur:.0f}s, {len(roster)} stages live, grid {GRID})")


if __name__ == "__main__":
    render()
