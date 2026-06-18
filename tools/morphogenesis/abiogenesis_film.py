"""ABIOGENESIS — the origin of life under the electron microscope. A premium vertical reel: thirteen
stages from a lifeless chemistry to a living one, each the lab's own depth-shaded SEM micrograph of
the real simulation, found by a 13-agent swarm that searched every rule for its most award-grade look.
Cinematic grade: eased documentary camera (sub-pixel Ken-Burns), bloom + halation + film grain, and a
microscope HUD (numeral · name · scale-bar · magnification · reticle · lower-third caption).
Sources: tools/morphogenesis/abio_gen.sh  →  /tmp/g_ab_*_{w,c}.bin
Preview a frame: python3 abiogenesis_film.py test <globalframe>   Full: python3 abiogenesis_film.py"""
import json, os, sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
W, H, FPS = 1080, 1920, 24
WIN = 980; WX = (W - WIN) // 2; WY = 430
BG = (5, 6, 9); BONE = (236, 230, 216); DIM = (128, 134, 148)
AC_W = (214, 178, 120)      # warm-sepia stage accent (amber bone)
AC_C = (156, 190, 220)      # cool-mono stage accent (steel)
FB = "docs/web8/assets/fonts/"
def fnt(n, s): p = FB + n; return ImageFont.truetype(p, s) if os.path.exists(p) else ImageFont.load_default()
F_disp = lambda s: fnt("Italiana-Regular.ttf", s)
F_mono = lambda s: fnt("IBMPlexMono-Regular.ttf", s)
F_ital = lambda s: fnt("CrimsonPro-Italic.ttf", s)
def text(cv, xy, s, f, fill, a=1.0, anc="mm", spc=8):
    if a <= 0.01: return
    ov = Image.new("RGBA", cv.size, (0, 0, 0, 0))
    ImageDraw.Draw(ov).multiline_text(xy, s, font=f, fill=(*fill, int(255 * min(1, a))), anchor=anc, align="center", spacing=spc)
    cv.alpha_composite(ov)
def tlen(s, f): return ImageDraw.Draw(Image.new("RGB", (4, 4))).textlength(s, font=f)
def label(cv, xy, s, size, fill, a=1.0, anc="mm", maxw=W - 90):
    s = s.upper()
    for gap in ("  ", " ", ""):
        for sz in range(size, max(9, size - 5), -1):
            t = gap.join(list(s))
            if tlen(t, F_mono(sz)) <= maxw: text(cv, xy, t, F_mono(sz), fill, a, anc); return
    text(cv, xy, s, F_mono(max(9, size - 5)), fill, a, anc)
def wrapped(cv, xy, s, f, fill, a, maxw, lh):
    if a <= 0.01: return
    words = s.split(); lines = []; cur = ""
    for w in words:
        t = (cur + " " + w).strip()
        if tlen(t, f) <= maxw: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    for i, ln in enumerate(lines): text(cv, (xy[0], xy[1] + i * lh), ln, f, fill, a)
ROMAN = [(10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')]
def roman(n):
    s = ''
    for v, sym in ROMAN:
        while n >= v: s += sym; n -= v
    return s
def smooth(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)            # smoothstep ease

# ── cinematic grade helpers ────────────────────────────────────────────────
def vig(n):
    yy, xx = np.mgrid[0:n, 0:n]; r = np.hypot((xx - n / 2) / (n / 2), (yy - n / 2) / (n / 2))
    return np.clip(1 - 0.34 * np.clip(r - 0.62, 0, 1) ** 1.8, 0, 1).astype(np.float32)[..., None]
VIG = vig(WIN)
def grade(im, warm, gA=5.0):
    """im: float HxWx3 0..255. Adds bloom + halation + filmic contrast + per-frame grain + vignette."""
    # filmic contrast: gentle S-curve, lift blacks slightly
    x = im / 255.0
    x = np.clip(0.045 + 0.93 * x, 0, 1)
    x = x * x * (3 - 2 * x)                                                      # smoothstep contrast
    im = x * 255.0
    # bloom: blur the bright highlights and screen them back, tinted (halation)
    hi = np.clip(im - 172, 0, 255)
    hib = np.asarray(Image.fromarray(hi.astype(np.uint8)).filter(ImageFilter.GaussianBlur(16)), np.float32)
    tint = np.array([1.0, 0.86, 0.66] if warm else [0.72, 0.86, 1.0], np.float32)
    im = im + hib * 0.55 * tint
    # film grain — fresh each frame, slightly stronger in the mids (organic; also masks the SEM dither)
    lum = im.mean(2, keepdims=True) / 255.0
    g = np.random.randn(WIN, WIN, 1).astype(np.float32) * gA * (0.5 + 1.1 * lum * (1 - lum) * 4)
    im = im + g
    im = im * VIG
    return np.clip(im, 0, 255)

# ── stages (the swarm's picks) ─────────────────────────────────────────────
# tag: GEN_OUT stem suffix (/tmp/g_<tag>_<mode>.bin) · mode w=warm-sepia c=cool-mono
# cam = (size0,size1, cx0,cy0, cx1,cy1) crop square as fraction of buffer (size0>size1 = push-in)
# pf  = play-fraction (source advances over first pf of segment, then holds) · seg = output frames
# sb  = (scale-bar label, magnification label)  — evocative microscope HUD
S = [
 dict(tag="ab_soup", id="soup", mode='w', name="Primordial Soup", num=1, seg=156, pf=0.85,
      cam=(0.62,0.50, 0.50,0.40, 0.50,0.36), sb=("5 µm","× 4 200"),
      cap="Spark-forged organics rain into a lifeless pool — the first molecules of a world not yet alive."),
 dict(tag="ab_grayscott", id="grayscott", mode='c', name="Reaction–Diffusion", num=2, seg=240, pf=1.0,
      cam=(0.94,0.62, 0.50,0.50, 0.52,0.48), sb=("10 µm","× 2 600"),
      cap="Bare chemistry — no genes, no membranes — self-organises into bodies that bud and divide."),
 dict(tag="ab_vents", id="vents", mode='c', name="Alkaline Vents", num=3, seg=208, pf=0.58,
      cam=(0.60,0.42, 0.50,0.60, 0.50,0.40), sb=("2 µm","× 12 000"),
      cap="Across a porous mineral chimney, a proton gradient ignites the first carbon-fixing metabolism."),
 dict(tag="ab_minerals", id="minerals", mode='w', name="Mineral Catalysis", num=4, seg=196, pf=0.60,
      cam=(1.0,0.82, 0.50,0.50, 0.50,0.50), sb=("2 µm","× 9 500"),
      cap="On montmorillonite clay, activated monomers condense and link into the first short chains."),
 dict(tag="ab_raf", id="raf", mode='w', name="Autocatalytic Set", num=5, seg=200, pf=0.40,
      cam=(0.56,0.37, 0.42,0.44, 0.55,0.55), sb=("1 µm","× 18 000"),
      cap="A closed web of reactions ignites and, all at once, begins to make itself."),
 dict(tag="ab_coacervate", id="coacervate", mode='c', name="Coacervate Droplets", num=6, seg=212, pf=1.0,
      cam=(0.60,0.44, 0.50,0.50, 0.46,0.52), sb=("5 µm","× 5 000"),
      cap="Oily microspheres condense from the primordial broth — the first membrane-less compartments."),
 dict(tag="ab_chirality", id="chirality", mode='c', name="Homochirality", num=7, seg=238, pf=1.0,
      cam=(0.90,0.60, 0.50,0.55, 0.45,0.50), sb=("5 µm","× 6 400"),
      cap="Rival handedness domains coarsen and merge as the field commits, irreversibly, to one chirality."),
 dict(tag="ab_rna", id="rna", mode='c', name="RNA World", num=8, seg=200, pf=0.78,
      cam=(0.95,0.74, 0.50,0.50, 0.50,0.50), sb=("1 µm","× 16 000"),
      cap="A self-copying RNA replicates outward — a master sequence and its faint mutant cloud."),
 dict(tag="ab_code", id="code", mode='c', name="The Genetic Code", num=9, seg=198, pf=0.65,
      cam=(0.72,0.56, 0.40,0.50, 0.60,0.50), sb=("2 µm","× 10 000"),
      cap="A scrambled codon map anneals into an error-minimising lattice — the genetic code crystallising."),
 dict(tag="ab_natsel", id="natural_selection", mode='c', name="Natural Selection", num=10, seg=200, pf=0.72,
      cam=(0.72,0.50, 0.50,0.50, 0.50,0.50), sb=("5 µm","× 5 800"),
      cap="Replicators bloom across the soup; the fitter colonies accumulate and crowd out the void."),
 dict(tag="ab_luca", id="luca", mode='w', name="LUCA", num=11, seg=200, pf=0.70,
      cam=(0.82,0.56, 0.50,0.50, 0.50,0.50), sb=("2 µm","× 13 000"),
      cap="From a churning soup of countless lineages, one last universal ancestor crystallises — and inherits the world."),
 dict(tag="ab_life", id="life", mode='w', name="Life", num=12, seg=224, pf=0.70,
      cam=(0.58,0.42, 0.44,0.50, 0.48,0.50), sb=("5 µm","× 7 000"),
      cap="Self-replicating code colonises the plate — programs that eat, divide and inherit. Life, running."),
]
ACTS = {1:"I · Chemistry",2:"I · Chemistry",3:"II · Energy & Surfaces",4:"II · Energy & Surfaces",
        5:"III · Self-Making",6:"III · Self-Making",
        7:"IV · Information",8:"IV · Information",9:"IV · Information",
        10:"V · Life",11:"V · Life",12:"V · Life"}
def acc(st): return AC_W if st['mode'] == 'w' else AC_C

_M = {}
def meta(tag):
    if tag not in _M: _M[tag] = json.load(open(f'/tmp/g_{tag}_meta.json'))
    return _M[tag]
def src_frame(st, lf):
    m = meta(st['tag']); n = m['frames']; p = min(1.0, (lf / max(1, st['seg'] - 1)) / st['pf'])
    return min(n - 1, int(round(p * (n - 1))))
def window(st, lf):
    m = meta(st['tag']); pw = m['W'] * m['SC']; ph = m['H'] * m['SC']; fb = pw * ph * 4
    fr = src_frame(st, lf)
    fp = open(f"/tmp/g_{st['tag']}_{st['mode']}.bin", 'rb'); fp.seek(fr * fb)
    a = np.frombuffer(fp.read(fb), np.uint8).reshape(ph, pw, 4)[:, :, :3]; fp.close()
    e = smooth(lf / max(1, st['seg'] - 1))
    sz0, sz1, cx0, cy0, cx1, cy1 = st['cam']
    sz = (sz0 + (sz1 - sz0) * e) * pw
    cx = (cx0 + (cx1 - cx0) * e) * pw; cy = (cy0 + (cy1 - cy0) * e) * ph
    x0 = min(max(cx - sz / 2, 0), pw - sz); y0 = min(max(cy - sz / 2, 0), ph - sz)
    im = np.asarray(Image.fromarray(a).resize((WIN, WIN), Image.LANCZOS, box=(x0, y0, x0 + sz, y0 + sz)), np.float32)
    if st.get('soft'):   # smooth out high-frequency field weave (keeps large forms; reads as soft micrograph)
        im = np.asarray(Image.fromarray(im.astype(np.uint8)).filter(ImageFilter.GaussianBlur(st['soft'])), np.float32)
    return grade(im, st['mode'] == 'w')

def reticle(d, x, y, n, ac, a=1.0):
    for cx, cy in [(x, y), (x + n, y), (x, y + n), (x + n, y + n)]:
        d.line([(cx - 20, cy), (cx + 20, cy)], fill=(*ac, int(140 * a)), width=1)
        d.line([(cx, cy - 20), (cx, cy + 20)], fill=(*ac, int(140 * a)), width=1)
    d.rectangle([x - 1, y - 1, x + n, y + n], outline=(*ac, int(48 * a)), width=1)
def hud(cv, d, st, a):
    ac = acc(st); scale, mag = st['sb']
    # scale bar bottom-left inside the window
    bx, by, bw = WX + 24, WY + WIN - 30, 120
    d.line([(bx, by), (bx + bw, by)], fill=(*BONE, int(210 * a)), width=3)
    for ex in (bx, bx + bw): d.line([(ex, by - 6), (ex, by + 6)], fill=(*BONE, int(210 * a)), width=2)
    text(cv, (bx + bw / 2, by - 18), scale, F_mono(19), BONE, 0.9 * a, "mm")
    # magnification + detector tag bottom-right
    text(cv, (WX + WIN - 24, WY + WIN - 34), mag, F_mono(20), ac, 0.9 * a, "rm")
    text(cv, (WX + WIN - 24, WY + WIN - 60), "SEM · HV 15kV", F_mono(14), DIM, 0.7 * a, "rm")

# ── timeline ───────────────────────────────────────────────────────────────
TITLE = 118; CODA = 132; FADE = 14
SEGS = [('title', None, TITLE)] + [('plate', st, st['seg']) for st in S] + [('coda', None, CODA)]
NF = sum(s[2] for s in SEGS)
def loc(f):
    acc_ = 0
    for kind, data, n in SEGS:
        if f < acc_ + n: return kind, data, f - acc_, n
        acc_ += n
    return SEGS[-1][0], SEGS[-1][1], 0, SEGS[-1][2]
def compose(f):
    kind, st, lf, n = loc(f); cv = Image.new("RGBA", (W, H), (*BG, 255)); d = ImageDraw.Draw(cv)
    if kind == 'title':
        g = min(1, lf / 20) * min(1, (n - 1 - lf) / 18)
        label(cv, (W // 2, 560), "the origin of life · under the electron microscope", 21, AC_C, 0.7 * g)
        text(cv, (W // 2, 850), "ABIOGENESIS", F_disp(118), BONE, g)
        text(cv, (W // 2, 1010), "how a dead chemistry became a living one", F_ital(46), AC_W, g)
        label(cv, (W // 2, 1346), "twelve stages · scanning electron micrographs", 19, DIM, 0.7 * g)
        return cv
    if kind == 'coda':
        g = min(1, lf / 20) * min(1, (n - 1 - lf) / 18)
        label(cv, (W // 2, 596), "from a lifeless broth, the first living thing", 20, AC_W, 0.66 * g)
        text(cv, (W // 2, 850), "everything alive", F_disp(62), BONE, g)
        text(cv, (W // 2, 936), "shares this beginning", F_disp(62), AC_C, g)
        label(cv, (W // 2, 1320), "cellautomata · abiogenesis", 17, DIM, 0.5 * g)
        return cv
    ac = acc(st); a = min(1, lf / FADE) * min(1, (n - 1 - lf) / FADE)
    img = window(st, lf); win = Image.fromarray(img.astype(np.uint8))
    if a < 1: win = Image.blend(Image.new("RGB", (WIN, WIN), BG), win, a)
    cv.paste(win, (WX, WY)); reticle(d, WX, WY, WIN, ac, a); hud(cv, d, st, a)
    text(cv, (W // 2, 156), roman(st['num']), F_disp(66), ac, 0.9 * a)
    text(cv, (W // 2, 252), st['name'].upper(), F_disp(58), BONE, a)
    label(cv, (W // 2, 326), ACTS[st['num']] + "  ·  scanning electron micrograph", 15, DIM, 0.55 * a)
    wrapped(cv, (W // 2, WY + WIN + 60), st['cap'], F_ital(37), BONE, a, W - 156, 50)
    # progress ticks
    for j, s2 in enumerate(S):
        x = W // 2 - (len(S) - 1) * 15 + j * 30; r = 4 if s2 is st else 2
        fill = ac if s2 is st else DIM
        d.ellipse([x - r, 1862 - r, x + r, 1862 + r], fill=(*fill, 255 if s2 is st else 105))
    label(cv, (W // 2, 1902), "catalytic silence · abiogenesis", 13, DIM, 0.4)
    return cv

if __name__ == '__main__' and len(sys.argv) > 2 and sys.argv[1] == 'test':
    compose(int(sys.argv[2])).convert("RGB").save('/tmp/abio_test.png'); print("NF", NF, "segs", [s[2] for s in SEGS]); sys.exit()
silent = "/tmp/abio_silent.mp4"
wr = imageio_ffmpeg.write_frames(silent, (W, H), fps=FPS, codec="libx264", pix_fmt_in="rgb24", pix_fmt_out="yuv420p", macro_block_size=8, output_params=["-crf", "18", "-preset", "medium"])
wr.send(None)
for f in range(NF): wr.send(np.ascontiguousarray(np.asarray(compose(f).convert("RGB"), np.uint8)).tobytes())
wr.close(); print("composited", NF)
total = NF / FPS; out = "/tmp/web8_abiogenesis.mp4"
fade = min(4.0, total / 3); fin = min(3.2, total / 3); fo = max(0.0, total - fade)
af = f"[1:a][2:a][3:a][4:a]amix=inputs=4,volume=0.10,lowpass=f=500,afade=t=in:st=0:d={fin:.2f},afade=t=out:st={fo:.2f}:d={fade:.2f}[a]"
subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", silent,
 "-f", "lavfi", "-t", f"{total}", "-i", "sine=frequency=42:sample_rate=44100",
 "-f", "lavfi", "-t", f"{total}", "-i", "sine=frequency=63:sample_rate=44100",
 "-f", "lavfi", "-t", f"{total}", "-i", "sine=frequency=84:sample_rate=44100",
 "-f", "lavfi", "-t", f"{total}", "-i", "sine=frequency=168:sample_rate=44100",
 "-filter_complex", af, "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "144k", "-shortest", "-movflags", "+faststart", out], check=True)
print(f"-> {out}  {os.path.getsize(out)/1e6:.1f} MB  {total:.1f}s")
