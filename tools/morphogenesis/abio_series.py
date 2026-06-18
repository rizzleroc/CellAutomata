"""ABIOGENESIS — THE SERIES. Four ~2-minute BBC-style episodes on the origin of life, built on the same
SEM-micrograph pipeline as abiogenesis_film.py. Each episode covers three specimens; each specimen gets
three shots (establishing -> detail push-in -> macro hold) with evolving narration — a real documentary
rhythm. Cinematic grade: eased sub-pixel camera, half-res bloom + halation + film grain, microscope HUD,
and series continuity (episode title cards + a "next time" teaser).
Sources: tools/morphogenesis/abio_gen.sh  ->  /tmp/g_ab_*_{w,c}.bin
  python3 abio_series.py test <ep> <frame>     # preview one frame (ep 1..4)
  python3 abio_series.py <ep>                   # render /tmp/web8_abio_epN.mp4
"""
import json, os, sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
W, H, FPS = 1080, 1920, 24
WIN = 980; WX = (W - WIN) // 2; WY = 430
BG = (5, 6, 9); BONE = (236, 230, 216); DIM = (128, 134, 148)
AC_W = (214, 178, 120)      # warm-sepia accent
AC_C = (156, 190, 220)      # cool-mono accent
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
def smooth(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)

# ── cinematic grade (half-res bloom for speed) ───────────────────────────────
def vig(n):
    yy, xx = np.mgrid[0:n, 0:n]; r = np.hypot((xx - n / 2) / (n / 2), (yy - n / 2) / (n / 2))
    return np.clip(1 - 0.34 * np.clip(r - 0.62, 0, 1) ** 1.8, 0, 1).astype(np.float32)[..., None]
VIG = vig(WIN)
def grade(im, warm, gA=3.6):
    x = im / 255.0
    x = np.clip(0.045 + 0.93 * x, 0, 1); x = x * x * (3 - 2 * x); im = x * 255.0
    hi = np.clip(im - 172, 0, 255)                                               # bloom: blur highlights at half-res
    small = Image.fromarray(hi.astype(np.uint8)).resize((WIN // 2, WIN // 2), Image.BILINEAR).filter(ImageFilter.GaussianBlur(8))
    hib = np.asarray(small.resize((WIN, WIN), Image.BILINEAR), np.float32)
    tint = np.array([1.0, 0.86, 0.66] if warm else [0.72, 0.86, 1.0], np.float32)
    im = im + hib * 0.55 * tint
    lum = im.mean(2, keepdims=True) / 255.0
    im = im + np.random.randn(WIN, WIN, 1).astype(np.float32) * gA * (0.5 + 1.1 * lum * (1 - lum) * 4)
    return np.clip(im * VIG, 0, 255)

# ── specimen registry (the swarm's picks; ctr/wide frame each specimen) ───────
# mode w=warm-sepia c=cool-mono · ctr=center of interest (frac) · wide=widest crop frac
# rise=tilt the camera upward (vents chimney) · caps=[establish, detail, macro]
STAGE = {
 'soup': dict(tag='ab_soup', mode='w', name="Primordial Soup", sb=("5 µm", "× 4 200"), ctr=(0.50, 0.42), wide=0.82, rise=False,
   caps=["Four billion years ago — an ocean of water, gas and rock, and not one living thing.",
         "Lightning and ultraviolet light forge simple organics that rain down into the sea.",
         "They gather in the shallows, yet this is only chemistry — nothing here can copy or survive."]),
 'grayscott': dict(tag='ab_grayscott', mode='c', name="Reaction–Diffusion", sb=("10 µm", "× 2 600"), ctr=(0.52, 0.50), wide=0.94, rise=False,
   caps=["Stir the right chemicals together and pattern appears unbidden — no template, no plan.",
         "Each spot feeds, swells and splits in two — a chemical rehearsal for cell division.",
         "From a featureless broth, the first sign that matter can shape itself into bodies."]),
 'raf': dict(tag='ab_raf', mode='w', name="Autocatalytic Set", sb=("1 µm", "× 18 000"), ctr=(0.50, 0.50), wide=0.78, rise=False,
   caps=["A lone self-copying molecule is unlikely; a web that builds each other is not.",
         "Each reaction's product is the next one's catalyst — the loop closing upon itself.",
         "All at once the network ignites: a chemistry that, together, makes itself."]),
 'vents': dict(tag='ab_vents', mode='c', name="Alkaline Vents", sb=("2 µm", "× 12 000"), ctr=(0.50, 0.50), wide=0.64, rise=True,
   caps=["On the black sea floor, warm alkaline water threads up through mineral chimneys.",
         "Across each paper-thin wall stands a gradient of protons — a battery built of rock.",
         "That gradient drives carbon into molecules: the first metabolism, older than the cell."]),
 'minerals': dict(tag='ab_minerals', mode='w', name="Mineral Catalysis", sb=("2 µm", "× 9 500"), ctr=(0.50, 0.50), wide=0.84, rise=False,
   caps=["The young Earth's clays are no mere mud — their layered faces are chemical workbenches.",
         "Activated building-blocks line up along the mineral surface and bond, end to end.",
         "Linked together, they become the first short chains — forerunners of RNA."]),
 'coacervate': dict(tag='ab_coacervate', mode='c', name="Coacervate Droplets", sb=("5 µm", "× 5 000"), ctr=(0.50, 0.50), wide=0.78, rise=False,
   caps=["Some molecules shun water, drawing together into glistening oily droplets.",
         "Each droplet hoards its reactions within — an inside, set apart from the world.",
         "No wall yet, but already a refuge where the chemistry of life can concentrate."]),
 'chirality': dict(tag='ab_chirality', mode='c', name="Homochirality", sb=("5 µm", "× 6 400"), ctr=(0.48, 0.52), wide=0.90, rise=False,
   caps=["Many of life's molecules come in two mirror forms — one left-handed, one right.",
         "Chemistry makes both alike, yet life keeps only one. The field must choose.",
         "Domains of a single handedness spread and merge until the mirror is gone for good."]),
 'rna': dict(tag='ab_rna', mode='c', name="RNA World", sb=("1 µm", "× 16 000"), ctr=(0.50, 0.50), wide=0.90, rise=False,
   caps=["One molecule can play both parts at once — the message, and the machine that copies it.",
         "RNA replicates outward from a master sequence, carrying its mistakes along.",
         "A master and its drifting cloud of mutants — the first thing that could truly evolve."]),
 'code': dict(tag='ab_code', mode='c', name="The Genetic Code", sb=("2 µm", "× 10 000"), ctr=(0.50, 0.50), wide=0.74, rise=False,
   caps=["Information needs a language: which triplet of letters shall mean which amino acid.",
         "A scrambled, accidental mapping anneals, slowly, toward order.",
         "It settles into a code that minimises error — the dictionary all life still reads."]),
 'natsel': dict(tag='ab_natsel', mode='c', name="Natural Selection", sb=("5 µm", "× 5 800"), ctr=(0.50, 0.50), wide=0.68, rise=False,
   caps=["Let things copy imperfectly while resources run short, and selection is inevitable.",
         "The fitter replicators bloom and spread; the rest are crowded into the dark.",
         "No designer and no goal — only what survives long enough to copy again."]),
 'luca': dict(tag='ab_luca', mode='w', name="LUCA", sb=("2 µm", "× 13 000"), ctr=(0.50, 0.50), wide=0.84, rise=False,
   caps=["Countless lineages contended in the early world; almost all left no heirs.",
         "One lineage's chemistry prevailed, and seeded every survivor that followed.",
         "The last universal common ancestor — the root from which all life still grows."]),
 'life': dict(tag='ab_life', mode='w', name="Life", sb=("5 µm", "× 7 000"), ctr=(0.44, 0.50), wide=0.66, rise=False,
   caps=["Self-replicating, mutating, open-ended — by every test that matters, this is alive.",
         "Programs that eat, divide and inherit, spreading to colonise their world.",
         "From a lifeless chemistry, life — and in four billion years it has never once stopped."]),
}
EPISODES = [
 dict(n=1, title="A Dead World Stirs", log="raw chemistry on a lifeless planet", stages=['soup','grayscott','raf'], aud=[40,60,80,160]),
 dict(n=2, title="Cradles in the Deep", log="where the first life found power and shelter", stages=['vents','minerals','coacervate'], aud=[44,66,88,176]),
 dict(n=3, title="The Thread of Information", log="the molecules that learned to remember", stages=['chirality','rna','code'], aud=[38,57,76,152]),
 dict(n=4, title="Life Begins", log="the lineage that never broke", stages=['natsel','luca','life'], aud=[46,69,92,184]),
]
def acc(st): return AC_W if st['mode'] == 'w' else AC_C
_M = {}
def meta(tag):
    if tag not in _M: _M[tag] = json.load(open(f'/tmp/g_{tag}_meta.json'))
    return _M[tag]
def read_src(tag, mode, frac):
    m = meta(tag); pw = m['W'] * m['SC']; ph = m['H'] * m['SC']; fb = pw * ph * 4
    fr = min(m['frames'] - 1, max(0, int(round(frac * (m['frames'] - 1)))))
    fp = open(f'/tmp/g_{tag}_{mode}.bin', 'rb'); fp.seek(fr * fb)
    a = np.frombuffer(fp.read(fb), np.uint8).reshape(ph, pw, 4)[:, :, :3]; fp.close()
    return a, pw, ph
def crop_to_win(a, pw, ph, sz, cx, cy):
    s = sz * pw; x0 = min(max(cx * pw - s / 2, 0), pw - s); y0 = min(max(cy * ph - s / 2, 0), ph - s)
    return np.asarray(Image.fromarray(a).resize((WIN, WIN), Image.LANCZOS, box=(x0, y0, x0 + s, y0 + s)), np.float32)
def shot_img(st, sh, lf):
    e = smooth(lf / max(1, sh['L'] - 1))
    sf0, sf1 = sh['sf']; frac = sf0 + (sf1 - sf0) * e
    sz0, sz1, cx0, cy0, cx1, cy1 = sh['cam']
    sz = sz0 + (sz1 - sz0) * e; cx = cx0 + (cx1 - cx0) * e; cy = cy0 + (cy1 - cy0) * e
    a, pw, ph = read_src(st['tag'], st['mode'], frac)
    return grade(crop_to_win(a, pw, ph, sz, cx, cy), st['mode'] == 'w')
def build_shots(st):
    cx, cy = st['ctr']; w = st['wide']; ry = 0.10 if st['rise'] else 0.0
    return [
      dict(kind=0, sf=(0.00, 0.55), cam=(w, w * 0.87, cx - 0.02, cy + ry, cx + 0.02, cy + ry * 0.4), L=280),
      dict(kind=1, sf=(0.42, 0.86), cam=(w * 0.60, w * 0.46, cx, cy + ry * 0.5, cx + 0.03, cy - 0.02), L=270),
      dict(kind=2, sf=(0.80, 1.00), cam=(w * 0.42, w * 0.35, cx - 0.03, cy, cx + 0.03, cy), L=252),
    ]

# ── microscope HUD ───────────────────────────────────────────────────────────
def reticle(d, x, y, n, ac, a=1.0):
    for cx, cy in [(x, y), (x + n, y), (x, y + n), (x + n, y + n)]:
        d.line([(cx - 20, cy), (cx + 20, cy)], fill=(*ac, int(140 * a)), width=1)
        d.line([(cx, cy - 20), (cx, cy + 20)], fill=(*ac, int(140 * a)), width=1)
    d.rectangle([x - 1, y - 1, x + n, y + n], outline=(*ac, int(48 * a)), width=1)
def hud(cv, d, st, a):
    ac = acc(st); scale, mag = st['sb']
    bx, by, bw = WX + 24, WY + WIN - 30, 120
    d.line([(bx, by), (bx + bw, by)], fill=(*BONE, int(210 * a)), width=3)
    for ex in (bx, bx + bw): d.line([(ex, by - 6), (ex, by + 6)], fill=(*BONE, int(210 * a)), width=2)
    text(cv, (bx + bw / 2, by - 18), scale, F_mono(19), BONE, 0.9 * a, "mm")
    text(cv, (WX + WIN - 24, WY + WIN - 34), mag, F_mono(20), ac, 0.9 * a, "rm")
    text(cv, (WX + WIN - 24, WY + WIN - 60), "SEM · HV 15kV", F_mono(14), DIM, 0.7 * a, "rm")

# ── episode timeline ─────────────────────────────────────────────────────────
EP = None; TITLE = 176; TEASER = 200; FADE = 14
def build_segs(ep):
    segs = [('title', dict(ep=ep), TITLE)]
    for si, tag in enumerate(ep['stages']):
        st = STAGE[tag]
        for sh in build_shots(st):
            segs.append(('shot', dict(st=st, sh=sh, si=si, ep=ep), sh['L']))
    segs.append(('teaser', dict(ep=ep), TEASER))
    return segs
def loc(segs, f):
    acc_ = 0
    for kind, data, n in segs:
        if f < acc_ + n: return kind, data, f - acc_, n
        acc_ += n
    return segs[-1][0], segs[-1][1], segs[-1][2] - 1, segs[-1][2]
def compose(ep, segs, f):
    kind, data, lf, n = loc(segs, f); cv = Image.new("RGBA", (W, H), (*BG, 255)); d = ImageDraw.Draw(cv)
    if kind == 'title':
        g = min(1, lf / 22) * min(1, (n - 1 - lf) / 20)
        label(cv, (W // 2, 470), "abiogenesis · a field study in four parts", 19, AC_C, 0.65 * g)
        label(cv, (W // 2, 720), f"episode {roman(ep['n'])}", 26, AC_W, 0.9 * g)
        text(cv, (W // 2, 900), ep['title'], F_disp(96), BONE, g)
        text(cv, (W // 2, 1040), ep['log'], F_ital(44), AC_C, g)
        label(cv, (W // 2, 1360), "scanning electron micrographs of a living chemistry", 17, DIM, 0.6 * g)
        return cv
    if kind == 'teaser':
        nxt = EPISODES[ep['n']] if ep['n'] < len(EPISODES) else None
        if nxt:
            bst = STAGE[nxt['stages'][0]]; img = shot_img(bst, dict(sf=(0.4, 0.7), cam=(bst['wide'] * 0.7, bst['wide'] * 0.62, bst['ctr'][0], bst['ctr'][1], bst['ctr'][0], bst['ctr'][1]), L=n), lf)
            g = min(1, lf / 18) * min(1, (n - 1 - lf) / 16)
            win = Image.fromarray((img * 0.34).astype(np.uint8)); cv.paste(win, (WX, WY))
            label(cv, (W // 2, 300), "next", 30, AC_W, 0.9 * g)
            text(cv, (W // 2, 980), nxt['title'], F_disp(70), BONE, g)
            label(cv, (W // 2, 1120), f"episode {roman(nxt['n'])} · {nxt['log']}", 17, AC_C, 0.7 * g)
        else:
            g = min(1, lf / 20) * min(1, (n - 1 - lf) / 18)
            label(cv, (W // 2, 596), "from a lifeless broth, the first living thing", 20, AC_W, 0.66 * g)
            text(cv, (W // 2, 850), "everything alive", F_disp(62), BONE, g)
            text(cv, (W // 2, 936), "shares this beginning", F_disp(62), AC_C, g)
            label(cv, (W // 2, 1320), "cellautomata · abiogenesis", 17, DIM, 0.5 * g)
        return cv
    # ── shot ──
    st = data['st']; sh = data['sh']; si = data['si']; ac = acc(st)
    a = min(1, lf / FADE) * min(1, (n - 1 - lf) / FADE)
    img = shot_img(st, sh, lf); win = Image.fromarray(img.astype(np.uint8))
    if a < 1: win = Image.blend(Image.new("RGB", (WIN, WIN), BG), win, a)
    cv.paste(win, (WX, WY)); reticle(d, WX, WY, WIN, ac, a); hud(cv, d, st, a)
    text(cv, (W // 2, 156), roman(si + 1), F_disp(64), ac, 0.85 * a)
    text(cv, (W // 2, 250), st['name'].upper(), F_disp(56), BONE, a)
    label(cv, (W // 2, 324), f"episode {roman(ep['n'])} · {ep['title']}", 15, DIM, 0.55 * a)
    wrapped(cv, (W // 2, WY + WIN + 60), st['caps'][sh['kind']], F_ital(37), BONE, a, W - 156, 50)
    for j in range(len(ep['stages'])):                                            # specimen progress (3 per episode)
        x = W // 2 - (len(ep['stages']) - 1) * 17 + j * 34; r = 5 if j == si else 3
        fill = ac if j == si else DIM
        d.ellipse([x - r, 1862 - r, x + r, 1862 + r], fill=(*fill, 255 if j == si else 110))
        if j == si:                                                              # sub-ticks for the 3 shots
            for k in range(3):
                tx = x - 16 + k * 16; rr = 2 if k == sh['kind'] else 1
                d.ellipse([tx - rr, 1882 - rr, tx + rr, 1882 + rr], fill=(*ac, 220 if k == sh['kind'] else 90))
    label(cv, (W // 2, 1908), "catalytic silence · abiogenesis", 13, DIM, 0.4)
    return cv

if __name__ == '__main__':
    if len(sys.argv) > 3 and sys.argv[1] == 'test':
        ep = EPISODES[int(sys.argv[2]) - 1]; segs = build_segs(ep); EP = ep
        nf = sum(s[2] for s in segs)
        compose(ep, segs, int(sys.argv[3])).convert("RGB").save('/tmp/abser_test.png')
        print("EP", ep['n'], "NF", nf, f"({nf/FPS:.1f}s)", "segs", len(segs)); sys.exit()
    epn = int(sys.argv[1]); ep = EPISODES[epn - 1]; EP = ep; segs = build_segs(ep)
    NF = sum(s[2] for s in segs)
    silent = f"/tmp/abser_ep{epn}_silent.mp4"
    wr = imageio_ffmpeg.write_frames(silent, (W, H), fps=FPS, codec="libx264", pix_fmt_in="rgb24", pix_fmt_out="yuv420p", macro_block_size=8, output_params=["-crf", "18", "-preset", "medium"])
    wr.send(None)
    for f in range(NF): wr.send(np.ascontiguousarray(np.asarray(compose(ep, segs, f).convert("RGB"), np.uint8)).tobytes())
    wr.close(); print("composited", NF)
    total = NF / FPS; out = f"/tmp/web8_abio_ep{epn}.mp4"
    fade = min(4.0, total / 3); fin = min(3.2, total / 3); fo = max(0.0, total - fade)
    a1, a2, a3, a4 = ep['aud']
    af = f"[1:a][2:a][3:a][4:a]amix=inputs=4,volume=0.10,lowpass=f=500,afade=t=in:st=0:d={fin:.2f},afade=t=out:st={fo:.2f}:d={fade:.2f}[a]"
    subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", silent,
     "-f", "lavfi", "-t", f"{total}", "-i", f"sine=frequency={a1}:sample_rate=44100",
     "-f", "lavfi", "-t", f"{total}", "-i", f"sine=frequency={a2}:sample_rate=44100",
     "-f", "lavfi", "-t", f"{total}", "-i", f"sine=frequency={a3}:sample_rate=44100",
     "-f", "lavfi", "-t", f"{total}", "-i", f"sine=frequency={a4}:sample_rate=44100",
     "-filter_complex", af, "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "144k", "-shortest", "-movflags", "+faststart", out], check=True)
    print(f"-> {out}  {os.path.getsize(out)/1e6:.1f} MB  {total:.1f}s")
