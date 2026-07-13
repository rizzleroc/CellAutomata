"""SORA FINISH — turn an external generated clip (e.g. Sora) into a finished vertical viral cut.
Unlike viral_cut.py (which renders from our SEM bins), this ingests a real MP4, fixes a deflating
energy curve by boomeranging the strong window (divide -> reform -> divide, seamless loop), upscales to
1080x1920, and overlays the repo's hook caption + microscope HUD. Reuses viral_cut's type/HUD system.
  SORA_CFG='{"src":"/path/in.mp4","t0":0.25,"t1":3.65,"hook":"THIS ISN\'T A CELL",
             "sub":"but it divides like one","brand":"JUST CHEMISTRY","id":"sora_gs"}' \
  python3 tools/morphogenesis/sora_finish.py
Run from repo root."""
import os, sys, json, subprocess, numpy as np
from PIL import Image
import imageio_ffmpeg
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import viral_cut as vc                              # big_caption, hud, fonts, VIGF, W/H/FPS
FF = imageio_ffmpeg.get_ffmpeg_exe()
W, H, FPS = vc.W, vc.H, vc.FPS

def read_window(src, t0, t1):
    cmd = [FF, "-v", "error", "-ss", f"{t0}", "-to", f"{t1}", "-i", src,
           "-vf", f"scale={W}:{H}:flags=lanczos", "-r", f"{FPS}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    nf = len(raw) // (W * H * 3)
    a = np.frombuffer(raw[:nf * W * H * 3], np.uint8).reshape(nf, H, W, 3)
    return [a[i] for i in range(nf)]

def env(a):  # ramp 0->1->0 helper over [0,1]
    return float(np.clip(a, 0, 1))

def main():
    c = json.loads(os.environ.get("SORA_CFG", "{}"))
    src = c["src"]; t0 = c.get("t0", 0.25); t1 = c.get("t1", 3.65)
    hook = c.get("hook", "THIS ISN'T A CELL"); sub = c.get("sub", "but it divides like one")
    brand = c.get("brand", "JUST CHEMISTRY"); cid = c.get("id", "sora")
    accent = tuple(c.get("accent", (150, 196, 235))); sb = tuple(c.get("sb", ("10 µm", "× 2 600")))

    fwd = read_window(src, t0, t1)
    if len(fwd) < 8: raise SystemExit(f"too few frames read ({len(fwd)}) — check src/window")
    seq = fwd + fwd[-2:0:-1]                          # boomerang: seamless, all high-energy
    NF = len(seq); T = NF / FPS

    silent = f"/tmp/sora_{cid}_silent.mp4"
    wr = imageio_ffmpeg.write_frames(silent, (W, H), fps=FPS, codec="libx264", pix_fmt_in="rgb24",
                                     pix_fmt_out="yuv420p", macro_block_size=8,
                                     output_params=["-crf", "18", "-preset", "medium"])
    wr.send(None)
    for i, fr in enumerate(seq):
        t = i / FPS
        im = (fr.astype(np.float32) * vc.VIGF)        # light vignette for text legibility
        cv = Image.fromarray(np.clip(im, 0, 255).astype(np.uint8)).convert("RGBA")
        # hook: in 0.0->1.1s, out 2.8->3.4s
        ah = env((t - 0.0) / 1.1) * env((3.5 - t) / 0.7)
        vc.big_caption(cv, H - 470, hook, accent, ah, "hook")
        # sub: in 1.5->2.4s, hold, out by end-0.6
        asub = env((t - 1.5) / 0.9) * env((T - 0.6 - t) / 0.8)
        if t > 1.4: vc.big_caption(cv, H - 360, sub, accent, asub, "sub")
        # brand end-card: last 1.6s
        ab = env((t - (T - 1.6)) / 0.6)
        if ab > 0.01:
            bf = vc.F_disp(92); bw = vc.tlen(brand, bf)
            from PIL import ImageDraw, ImageFilter
            scr = Image.new("RGBA", cv.size, (0, 0, 0, 0))
            ImageDraw.Draw(scr).ellipse([W/2-bw/2-90, H/2-140, W/2+bw/2+90, H/2+140], fill=(0, 0, 0, 200))
            cv.alpha_composite(Image.fromarray(np.asarray(scr.filter(ImageFilter.GaussianBlur(38)))))
            vc._draw(cv, (W/2, H/2-22), brand, bf, vc.BONE, ab, "mm")
            vc._draw(cv, (W/2, H/2+70), "cellautomata", vc.F_mono(22), accent, 0.7*ab, "mm")
        vc.hud(cv, sb, accent, 0.9)
        wr.send(np.ascontiguousarray(np.asarray(cv.convert("RGB"), np.uint8)).tobytes())
    wr.close()

    out = f"/tmp/viral_{cid}.mp4"
    af = ("[1:a]volume=0.5[sub];[2:a]tremolo=f=2.0:d=0.85,volume=0.45[pul];[3:a]highpass=f=900,volume=0.10[air];"
          "[sub][pul][air]amix=inputs=3:normalize=0,lowpass=f=2200,"
          f"afade=t=in:st=0:d=0.6,afade=t=out:st={max(0,T-1.2):.2f}:d=1.2[a]")
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", silent,
        "-f", "lavfi", "-t", f"{T}", "-i", "sine=frequency=46:sample_rate=44100",
        "-f", "lavfi", "-t", f"{T}", "-i", "sine=frequency=92:sample_rate=44100",
        "-f", "lavfi", "-t", f"{T}", "-i", "anoisesrc=color=brown:sample_rate=44100",
        "-filter_complex", af, "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac",
        "-b:a", "160k", "-shortest", "-movflags", "+faststart", out], check=True)
    print(f"-> {out}  {os.path.getsize(out)/1e6:.1f} MB  {T:.1f}s  ({len(fwd)}f fwd -> {NF}f boomerang)")

if __name__ == "__main__":
    main()
