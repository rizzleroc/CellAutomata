"""BLEND CUT — fuse a generative clip (Sora-style, photoreal glow) with the tool's own SEM micrograph of the
SAME phenomenon, into one narrated vertical cut. The narrative is the reveal: "this looks alive" (Sora) ->
"it's a reaction-diffusion SIMULATION" (SEM from our bins) -> "yet it divides like life" (split-screen).
Optional ElevenLabs voiceover mp3 is ducked over a pulse bed; captions double the VO so it reads silent too.

  BLEND_CFG='{"src":"/path/sora.mp4","sem":"ab_grayscott","vo":"/tmp/vo.mp3","id":"blend_gs",
              "t0":0.25,"t1":3.65,"style":"reveal"}' python3 tools/morphogenesis/blend_cut.py
Run from repo root. style: "reveal" (default) | "split" (side-by-side throughout). vo optional (pulse bed if absent)."""
import os, sys, json, subprocess, re, numpy as np
from PIL import Image, ImageDraw, ImageFilter
import imageio_ffmpeg
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import viral_cut as vc
FF = imageio_ffmpeg.get_ffmpeg_exe()
W, H, FPS = vc.W, vc.H, vc.FPS

def read_window(src, t0, t1):
    cmd = [FF, "-v", "error", "-ss", f"{t0}", "-to", f"{t1}", "-i", src,
           "-vf", f"scale={W}:{H}:flags=lanczos", "-r", f"{FPS}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    nf = len(raw) // (W * H * 3)
    a = np.frombuffer(raw[:nf * W * H * 3], np.uint8).reshape(nf, H, W, 3)
    return [a[i].astype(np.float32) for i in range(nf)]

def punch(im):
    """Boost the SEM micrograph: percentile contrast-stretch + S-curve + unsharp relief, so the
    reaction-diffusion structure reads dramatically against the photoreal half."""
    x = im.astype(np.float32)
    lo, hi = np.percentile(x, 2), np.percentile(x, 98)
    x = np.clip((x - lo) / max(1e-3, hi - lo) * 255, 0, 255)
    n = np.clip(0.5 + (x/255 - 0.5) * 1.4, 0, 1) * 255                # contrast S-curve
    blur = np.asarray(Image.fromarray(n.astype(np.uint8)).filter(ImageFilter.GaussianBlur(6)), np.float32)
    return np.clip(n + 0.65 * (n - blur), 0, 255)                     # unsharp relief (tuned to limit bitrate)

def sem_frame(tag, mode, cx, cy, frac, sz, warm):
    a, pw, ph = vc.read_src(tag, mode, frac)
    return punch(vc.grade(vc.portrait_crop(a, pw, ph, sz, cx, cy), warm))   # float32 HxWx3

def ramp(x): return float(np.clip(x, 0, 1))

def probe_dur(path):
    err = subprocess.run([FF, "-i", path], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err)
    return int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3)) if m else None

def main():
    c = json.loads(os.environ.get("BLEND_CFG", "{}"))
    src = c["src"]; sem = c.get("sem", "ab_grayscott"); cid = c.get("id", "blend")
    t0 = c.get("t0", 0.25); t1 = c.get("t1", 3.65); style = c.get("style", "reveal")
    vo = c.get("vo")  # optional ElevenLabs narration mp3
    st = vc.STAGE[sem]; mode = st[0]; cx, cy = st[1]; wide = st[2]; sb = st[4]
    accent = tuple(c.get("accent", (150, 196, 235))); warm = (mode == "w")

    # caption beats double as the VO timeline (so the cut reads with sound off)
    caps = c.get("caps") or [
        (0.3, 4.6, "THIS ISN'T A CELL", "hook"),
        (6.2, 10.0, "no DNA. no membrane. no life.", "sub"),
        (10.2, 13.6, "just two chemicals, two rules.", "sub"),
        (14.0, 16.8, "yet it divides like it's alive.", "sub"),
    ]
    brand = c.get("brand", "CATALYTIC SILENCE")
    REF = 18.0                                              # reference timeline the caps are authored against
    dur = probe_dur(vo) if (vo and os.path.exists(vo)) else None
    TOTAL = c.get("total", (dur + 1.4) if dur else REF)    # fit the narration if VO is supplied
    k = TOTAL / REF; NF = int(TOTAL * FPS)                 # proportionally stretch caps to the real length

    sora = read_window(src, t0, t1)
    if len(sora) < 8: raise SystemExit(f"too few Sora frames ({len(sora)})")
    boom = sora + sora[-2:0:-1]                              # seamless Sora loop for its screen-time

    def sora_at(f):  return boom[f % len(boom)]
    def visual(f):
        p = (f / FPS) / TOTAL                                # normalized progress -> auto-scales to any length
        if style == "split":
            return splitscreen(sora_at(f), sem_frame(sem, mode, cx, cy, ramp(p), wide*(1-0.3*p), warm), accent)
        # reveal: Sora -> (crossfade) -> SEM push-in -> split-screen tag
        if p < 0.255:                                        # Sora photoreal
            return sora_at(f)
        if p < 0.333:                                        # crossfade Sora -> SEM
            a = ramp((p-0.255)/0.078)
            return sora_at(f)*(1-a) + sem_frame(sem, mode, cx, cy, 0.0, wide, warm)*a
        if p < 0.767:                                        # SEM micrograph, slow push-in
            fr = ramp((p-0.333)/0.434)
            return sem_frame(sem, mode, cx, cy, fr, wide*(1-0.34*fr), warm)
        return splitscreen(sora_at(f), sem_frame(sem, mode, cx, cy, 1.0, wide*0.66, warm), accent)

    silent = f"/tmp/blend_{cid}_silent.mp4"
    wr = imageio_ffmpeg.write_frames(silent, (W, H), fps=FPS, codec="libx264", pix_fmt_in="rgb24",
                                     pix_fmt_out="yuv420p", macro_block_size=8, output_params=["-crf", "20", "-preset", "medium"])
    wr.send(None)
    for f in range(NF):
        t = f / FPS
        base = np.clip(visual(f), 0, 255).astype(np.uint8)
        cv = Image.fromarray(base).convert("RGBA")
        fade = min(1.0, (f+1)/4.0) * min(1.0, (NF-f)/8.0)   # open + tail
        for (cs, ce, txt, kind) in caps:
            a = ramp((t-cs*k)/0.6) * ramp((ce*k-t)/0.6)     # caps stretch with the narration length
            if a > 0.01:
                y = H-470 if kind == "hook" else H-360
                vc.big_caption(cv, y, txt, accent, a, kind)
        ab = ramp((t-(TOTAL-1.7))/0.6)                       # brand end-card
        if ab > 0.01:
            from PIL import ImageFilter
            bf = vc.F_disp(86); bw = vc.tlen(brand, bf)
            scr = Image.new("RGBA", cv.size, (0, 0, 0, 0))
            ImageDraw.Draw(scr).ellipse([W/2-bw/2-90, H/2-130, W/2+bw/2+90, H/2+130], fill=(0, 0, 0, 205))
            cv.alpha_composite(Image.fromarray(np.asarray(scr.filter(ImageFilter.GaussianBlur(38)))))
            vc._draw(cv, (W/2, H/2-18), brand, bf, vc.BONE, ab, "mm")
            vc._draw(cv, (W/2, H/2+66), "cellautomata", vc.F_mono(22), accent, 0.7*ab, "mm")
        vc.hud(cv, sb, accent, 0.9)
        if fade < 1: cv = Image.blend(Image.new("RGBA", (W, H), (*vc.BG, 255)), cv, fade)
        wr.send(np.ascontiguousarray(np.asarray(cv.convert("RGB"), np.uint8)).tobytes())
    wr.close()

    out = f"/tmp/blend_{cid}.mp4"
    mux_audio(silent, out, TOTAL, vo)
    print(f"-> {out}  {os.path.getsize(out)/1e6:.1f} MB  {TOTAL:.1f}s  style={style}  vo={'yes' if vo else 'pulse-bed'}")

def splitscreen(top, bot, accent):
    out = np.empty((H, W, 3), np.float32); half = H//2
    out[:half] = np.asarray(Image.fromarray(np.clip(top,0,255).astype(np.uint8)).resize((W, half), Image.LANCZOS), np.float32)
    out[half:] = np.asarray(Image.fromarray(np.clip(bot,0,255).astype(np.uint8)).resize((W, H-half), Image.LANCZOS), np.float32)
    out[half-3:half+3] = np.array(accent, np.float32)       # divider rule
    cv = Image.fromarray(out.astype(np.uint8)).convert("RGBA")
    vc._draw(cv, (40, half-44), "RENDER", vc.F_mono(26), vc.BONE, 0.85, "lm")
    vc._draw(cv, (40, half+44), "SIMULATION", vc.F_mono(26), accent, 0.9, "lm")
    return np.asarray(cv.convert("RGB"), np.float32)

def mux_audio(silent, out, T, vo):
    if vo and os.path.exists(vo):   # ElevenLabs VO on top of a ducked pulse bed
        af = ("[2:a]volume=0.5[s];[3:a]tremolo=f=2.0:d=0.85,volume=0.4[p];[4:a]highpass=f=900,volume=0.08[ai];"
              "[s][p][ai]amix=inputs=3:normalize=0,lowpass=f=2200[bed];"
              "[bed][1:a]sidechaincompress=threshold=0.04:ratio=6:attack=20:release=320[bd];"
              f"[bd][1:a]amix=inputs=2:normalize=0,afade=t=in:st=0:d=0.5,afade=t=out:st={max(0,T-1.0):.2f}:d=1.0[a]")
        ins = ["-i", vo, "-f", "lavfi", "-t", f"{T}", "-i", "sine=frequency=46:sample_rate=44100",
               "-f", "lavfi", "-t", f"{T}", "-i", "sine=frequency=92:sample_rate=44100",
               "-f", "lavfi", "-t", f"{T}", "-i", "anoisesrc=color=brown:sample_rate=44100"]
    else:                           # pulse bed only (draft / no VO yet)
        af = ("[1:a]volume=0.5[s];[2:a]tremolo=f=2.0:d=0.85,volume=0.45[p];[3:a]highpass=f=900,volume=0.10[ai];"
              "[s][p][ai]amix=inputs=3:normalize=0,lowpass=f=2200,"
              f"afade=t=in:st=0:d=0.6,afade=t=out:st={max(0,T-1.2):.2f}:d=1.2[a]")
        ins = ["-f", "lavfi", "-t", f"{T}", "-i", "sine=frequency=46:sample_rate=44100",
               "-f", "lavfi", "-t", f"{T}", "-i", "sine=frequency=92:sample_rate=44100",
               "-f", "lavfi", "-t", f"{T}", "-i", "anoisesrc=color=brown:sample_rate=44100"]
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", silent, *ins,
        "-filter_complex", af, "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac",
        "-b:a", "176k", "-shortest", "-movflags", "+faststart", out], check=True)

if __name__ == "__main__":
    main()
