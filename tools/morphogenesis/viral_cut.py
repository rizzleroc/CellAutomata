"""VIRAL CUT — full-bleed 15-30s vertical scroll-stoppers from the abiogenesis SEM bins (/tmp/g_ab_*_{w,c}.bin).
Fixes the viral critique: opens ON motion, BIG plain-English hook caption, hard-cut punch-in beats, loopable,
dynamic pulse audio bed (not the flat sine drone). Config via env VCUT_CFG (JSON).
  VCUT_CFG='{"tag":"ab_grayscott","hook":"NONE OF THIS IS ALIVE",...}' python3 viral_cut.py board   # filmstrip -> /tmp/vcut_<tag>.png
  VCUT_CFG='{...}' python3 viral_cut.py render                                                       # mp4 -> /tmp/viral_<tag>.mp4
Run from repo root. The 'board' mode is cheap (no encode) so a swarm can judge by eye and self-score."""
import json, os, sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
W, H, FPS = 1080, 1920, 24
BG = (5, 6, 9); BONE = (238, 232, 218); DIM = (150, 156, 168)
FB = "docs/web8/assets/fonts/"
def fnt(n, s): p = FB + n; return ImageFont.truetype(p, s) if os.path.exists(p) else ImageFont.load_default()
F_disp = lambda s: fnt("Italiana-Regular.ttf", s)
F_mono = lambda s: fnt("IBMPlexMono-Regular.ttf", s)
F_bold = lambda s: fnt("IBMPlexMono-Bold.ttf", s)
F_ital = lambda s: fnt("CrimsonPro-Italic.ttf", s)
def smooth(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
# specimen defaults: mode, center, wide(height frac), display name, scale-bar/mag, default captions
STAGE = {
 'ab_grayscott': ('c',(0.52,0.50),0.96,"Reaction–Diffusion",("10 µm","× 2 600"),["NONE OF THIS IS ALIVE","yet it divides like a cell","JUST CHEMISTRY"]),
 'ab_rna':       ('c',(0.50,0.50),0.92,"RNA World",("1 µm","× 16 000"),["A MOLECULE COPYING ITSELF","life's first replicator","RNA WORLD"]),
 'ab_chirality': ('c',(0.48,0.52),0.92,"Homochirality",("5 µm","× 6 400"),["LIFE HAD TO PICK A SIDE","why you're left-handed inside","HOMOCHIRALITY"]),
 'ab_luca':      ('w',(0.50,0.50),0.86,"LUCA",("2 µm","× 13 000"),["YOUR OLDEST ANCESTOR","everything alive shares it","LUCA"]),
 'ab_vents':     ('c',(0.50,0.50),0.66,"Alkaline Vents",("2 µm","× 12 000"),["LIFE BEGAN IN THE DARK","not a pond — a deep-sea vent","ALKALINE VENTS"]),
 'ab_minerals':  ('w',(0.50,0.50),0.86,"Mineral Catalysis",("2 µm","× 9 500"),["ROCK BUILT THE FIRST CHAINS","clay as a chemical factory","MINERAL CATALYSIS"]),
 'ab_coacervate':('c',(0.50,0.50),0.80,"Coacervates",("5 µm","× 5 000"),["THE FIRST ‘CELLS’","oily drops, no membrane yet","COACERVATES"]),
 'ab_code':      ('c',(0.50,0.50),0.76,"The Genetic Code",("2 µm","× 10 000"),["THE CODE WRITING ITSELF","how DNA learned its alphabet","GENETIC CODE"]),
 'ab_natsel':    ('c',(0.50,0.50),0.70,"Natural Selection",("5 µm","× 5 800"),["SURVIVAL, BEFORE LIFE","the fitter chemistry wins","SELECTION"]),
 'ab_life':      ('w',(0.42,0.50),0.74,"Life",("5 µm","× 7 000"),["CODE THAT'S ALIVE","it eats, divides, evolves","DIGITAL LIFE"]),
 'ab_soup':      ('w',(0.50,0.42),0.84,"Primordial Soup",("5 µm","× 4 200"),["EARTH, BEFORE LIFE","lightning making life's bricks","PRIMORDIAL SOUP"]),
}
def vigf():
    yy, xx = np.mgrid[0:H, 0:W]; r = np.hypot((xx-W/2)/(W/2), (yy-H/2)/(H/2))
    return np.clip(1 - 0.40*np.clip(r-0.55,0,1)**1.7, 0, 1).astype(np.float32)[...,None]
VIGF = vigf()
def grade(im, warm, gA=3.4):
    x = im/255.0; x = np.clip(0.03+0.94*x,0,1); xc = x*x*(3-2*x); x = 0.6*xc+0.4*x; im = x*255.0
    hi = np.clip(im-190,0,255)
    sm = Image.fromarray(hi.astype(np.uint8)).resize((W//2,H//2),Image.BILINEAR).filter(ImageFilter.GaussianBlur(7))
    hib = np.asarray(sm.resize((W,H),Image.BILINEAR),np.float32)
    tint = np.array([1.0,0.86,0.66] if warm else [0.72,0.86,1.0],np.float32)
    im = im + hib*0.42*tint
    lum = im.mean(2,keepdims=True)/255.0
    im = im + np.random.randn(H,W,1).astype(np.float32)*gA*(0.5+1.1*lum*(1-lum)*4)
    return np.clip(im*VIGF,0,255)
_M = {}
def meta(tag):
    if tag not in _M: _M[tag] = json.load(open(f'/tmp/g_{tag}_meta.json'))
    return _M[tag]
def read_src(tag, mode, frac):
    m = meta(tag); pw = m['W']*m['SC']; ph = m['H']*m['SC']; fb = pw*ph*4
    fr = min(m['frames']-1, max(0, int(round(frac*(m['frames']-1)))))
    fp = open(f'/tmp/g_{tag}_{mode}.bin','rb'); fp.seek(fr*fb)
    a = np.frombuffer(fp.read(fb),np.uint8).reshape(ph,pw,4)[:,:,:3]; fp.close()
    return a, pw, ph
def portrait_crop(a, pw, ph, szh, cx, cy):
    # full-bleed 9:16 crop: height = szh*ph, width = height*9/16 -> scale to 1080x1920
    hcrop = max(16, min(ph, szh*ph)); wcrop = min(pw, hcrop*W/H)
    x0 = min(max(cx*pw - wcrop/2, 0), pw-wcrop); y0 = min(max(cy*ph - hcrop/2, 0), ph-hcrop)
    return np.asarray(Image.fromarray(a).resize((W,H), Image.LANCZOS, box=(x0,y0,x0+wcrop,y0+hcrop)), np.float32)
# ── text ──
def _draw(cv, xy, s, f, fill, a, anc="mm"):
    if a <= 0.01: return
    ov = Image.new("RGBA", cv.size, (0,0,0,0)); ImageDraw.Draw(ov).text(xy, s, font=f, fill=(*fill,int(255*min(1,a))), anchor=anc); cv.alpha_composite(ov)
def tlen(s, f): return ImageDraw.Draw(Image.new("RGB",(4,4))).textlength(s, font=f)
def wrapfit(s, f, maxw):
    words = s.split(); lines=[]; cur=""
    for w in words:
        t=(cur+" "+w).strip()
        if tlen(t,f)<=maxw: cur=t
        else: lines.append(cur); cur=w
    if cur: lines.append(cur)
    return lines
def big_caption(cv, y, s, accent, a, kind="hook"):
    # big legible caption with a soft scrim; hook=huge mono, sub=italic serif
    if a <= 0.01 or not s: return
    if kind == "hook":
        size = 132
        for sz in range(size, 48, -4):
            f = F_bold(sz); lines = wrapfit(s.upper(), f, W-120)
            if len(lines) <= 3 and max(tlen(l,f) for l in lines) <= W-120: size = sz; break
        f = F_bold(size); lines = wrapfit(s.upper(), f, W-120); lh = int(size*1.10)
    else:
        size = 52; f = F_ital(size); lines = wrapfit(s, f, W-180); lh = int(size*1.2)
    blockh = lh*len(lines); y0 = y - blockh/2
    # scrim
    scr = Image.new("RGBA", cv.size, (0,0,0,0)); sd = ImageDraw.Draw(scr)
    pad = 66 if kind=="hook" else 46; sa = 210 if kind=="hook" else 150
    sd.rectangle([0, y0-pad, W, y0+blockh+pad], fill=(0,0,0,sa)); cv.alpha_composite(Image.fromarray(np.asarray(scr.filter(ImageFilter.GaussianBlur(26)))))
    if kind == "hook":  # accent rules bracketing the hook
        cw = max(tlen(l,f) for l in lines)
        ImageDraw.Draw(cv).line([(W/2-cw/2, y0-30),(W/2+cw/2, y0-30)], fill=(*accent,int(235*a)), width=5)
        ImageDraw.Draw(cv).line([(W/2-cw/2, y0+blockh+30),(W/2+cw/2, y0+blockh+30)], fill=(*accent,int(235*a)), width=5)
    for i,l in enumerate(lines):
        _draw(cv, (W/2, y0+lh*i+lh/2), l, f, BONE if kind=="hook" else accent, a)
def hud(cv, sb, accent, a):
    d = ImageDraw.Draw(cv); scale, mag = sb
    bx, by, bw = 40, H-150, 120
    d.line([(bx,by),(bx+bw,by)], fill=(*BONE,int(190*a)), width=3)
    for ex in (bx,bx+bw): d.line([(ex,by-6),(ex,by+6)], fill=(*BONE,int(190*a)), width=2)
    _draw(cv,(bx+bw/2,by-18),scale,F_mono(18),BONE,0.85*a,"mm")
    _draw(cv,(W-40,H-152),mag,F_mono(19),accent,0.85*a,"rm")
# ── config / beats ──
def cfg():
    c = json.loads(os.environ.get('VCUT_CFG','{}'))
    tag = c.get('tag','ab_grayscott'); st = STAGE[tag]
    mode = c.get('mode', st[0]); ctr = c.get('ctr', list(st[1])); wide = c.get('wide', st[2])
    name = c.get('name', st[3]); sb = c.get('sb', st[4]); caps = c.get('caps', st[5])
    hook = c.get('hook', caps[0]); payoff = c.get('payoff', caps[1]); brand = c.get('brand', caps[2])
    accent = tuple(c.get('accent', (230,200,120) if mode=='w' else (150,192,230)))
    durs = c.get('durs', [150,150,140])  # frames per beat (hook, detail, macro) ~18s
    cx, cy = ctr
    beats = c.get('beats') or [
      dict(sz=wide,       cx=cx, cy=cy, f0=0.00, f1=0.40, L=durs[0], cap=hook,   kind="hook"),
      dict(sz=wide*0.56,  cx=cx, cy=cy, f0=0.35, f1=0.80, L=durs[1], cap=payoff, kind="sub"),
      dict(sz=wide*0.40,  cx=cx, cy=cy, f0=0.72, f1=1.00, L=durs[2], cap=brand,  kind="brand"),
    ]
    return dict(tag=tag, id=c.get('id', tag), mode=mode, accent=accent, name=name, sb=sb, beats=beats,
                NF=sum(b['L'] for b in beats))
def frame(C, f):
    acc=0
    for bi,b in enumerate(C['beats']):
        if f < acc+b['L']:
            lf = f-acc; e = smooth(lf/max(1,b['L']-1))
            frac = b['f0'] + (b['f1']-b['f0'])*e
            sz = b['sz']*(1.0 - 0.06*e)  # gentle continued push within the beat
            a, pw, ph = read_src(C['tag'], C['mode'], frac)
            im = portrait_crop(a, pw, ph, sz, b['cx'], b['cy'])
            im = grade(im, C['mode']=='w')
            cv = Image.fromarray(im.astype(np.uint8)).convert("RGBA")
            fin = min(1.0, (f+3)/3.0) * min(1.0, (C['NF']-f)/2.0)  # bold frame-1 open (frame0 full), hard punch-cuts between beats; near-zero out-tail so end matches start for a seamless loop
            ca = 0.25 + 0.75*min(1.0, lf/10.0)
            if b['kind']=="hook":   big_caption(cv, H-470, b['cap'], C['accent'], ca, "hook")
            elif b['kind']=="sub":  big_caption(cv, H-360, b['cap'], C['accent'], ca, "sub")
            else:
                bf = F_disp(96); bw = tlen(b['cap'], bf)
                scr = Image.new("RGBA", cv.size, (0,0,0,0))
                ImageDraw.Draw(scr).ellipse([W/2-bw/2-90, H/2-150, W/2+bw/2+90, H/2+150], fill=(0,0,0,205))
                cv.alpha_composite(Image.fromarray(np.asarray(scr.filter(ImageFilter.GaussianBlur(40)))))
                ImageDraw.Draw(cv).line([(W/2-70, H/2+34),(W/2+70, H/2+34)], fill=(*C['accent'],int(200*ca)), width=3)
                _draw(cv,(W/2,H/2-26),b['cap'],bf,BONE,ca,"mm")
                _draw(cv,(W/2,H/2+72),"cellautomata",F_mono(22),C['accent'],0.7*ca,"mm")
            hud(cv, C['sb'], C['accent'], 0.9)
            if fin < 1: cv = Image.blend(Image.new("RGBA",(W,H),(*BG,255)), cv, fin)
            return cv.convert("RGB")
        acc += b['L']
    return Image.new("RGB",(W,H),BG)
def main():
    mode = sys.argv[1] if len(sys.argv)>1 else 'board'
    C = cfg()
    if mode == 'board':
        K = 6; cols=3; rows=2; tw,th = 360,640
        sheet = Image.new("RGB",(tw*cols, th*rows), (0,0,0))
        for k in range(K):
            f = int((C['NF']-1)*k/(K-1)); im = frame(C,f).resize((tw,th), Image.LANCZOS)
            sheet.paste(im, ((k%cols)*tw, (k//cols)*th))
        out = f"/tmp/vcut_{C['id']}.png"; sheet.save(out)
        print(f"board {C['id']}: {C['NF']}f ({C['NF']/FPS:.1f}s) hook='{C['beats'][0]['cap']}' -> {out}")
    else:
        silent = f"/tmp/vcut_{C['id']}_silent.mp4"
        wr = imageio_ffmpeg.write_frames(silent,(W,H),fps=FPS,codec="libx264",pix_fmt_in="rgb24",pix_fmt_out="yuv420p",macro_block_size=8,output_params=["-crf","18","-preset","medium"])
        wr.send(None)
        for f in range(C['NF']): wr.send(np.ascontiguousarray(np.asarray(frame(C,f),np.uint8)).tobytes())
        wr.close()
        total = C['NF']/FPS; out = f"/tmp/viral_{C['id']}.mp4"
        # dynamic pulse bed: sub + tremolo mid pulse + airy shimmer (NOT a flat drone)
        af = ("[1:a]volume=0.5[sub];[2:a]tremolo=f=2.0:d=0.85,volume=0.45[pul];[3:a]highpass=f=900,volume=0.10[air];"
              "[sub][pul][air]amix=inputs=3:normalize=0,lowpass=f=2200,"
              f"afade=t=in:st=0:d=0.6,afade=t=out:st={max(0,total-1.2):.2f}:d=1.2[a]")
        subprocess.run([FF,"-y","-hide_banner","-loglevel","error","-i",silent,
         "-f","lavfi","-t",f"{total}","-i","sine=frequency=46:sample_rate=44100",
         "-f","lavfi","-t",f"{total}","-i","sine=frequency=92:sample_rate=44100",
         "-f","lavfi","-t",f"{total}","-i","anoisesrc=color=brown:sample_rate=44100",
         "-filter_complex",af,"-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","160k","-shortest","-movflags","+faststart",out],check=True)
        print(f"-> {out}  {os.path.getsize(out)/1e6:.1f} MB  {total:.1f}s")
if __name__ == '__main__': main()
