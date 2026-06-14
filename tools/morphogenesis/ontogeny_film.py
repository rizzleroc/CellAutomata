"""ONTOGENY — the docs/ontogeny UI, as a vertical reel. The real SEM specimen (from
ontogeny_gen.mjs) is dropped into a faithful rebuild of the app's vitrine: the register,
the stage with corner-mats + LIVE·SEM badge + the live count, the caption, and the
diagnosis (verdict · membranes · stats · timeline). Palette/fonts = "Catalytic Silence".
Smoke a frame:  python3 ontogeny_film.py testc 900     Full: python3 ontogeny_film.py"""
import json, os, sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
W, H, FPS = 1080, 1920, 24
# ── Catalytic Silence palette (styles.css :root) ──
OB=(7,9,13); OB2=(10,14,21); PLATE=(10,14,22)
INK=(236,231,218); INKS=(203,197,182); MUT=(154,146,128); MUTD=(138,132,116)
TEAL=(63,224,208); TEALB=(116,244,231); TEALD=(31,143,134); MAG=(215,123,255); AMBER=(255,207,107)
HAIR=(236,231,218)
FB="docs/web8/assets/fonts/"
def fnt(n,s):
    p=FB+n; return ImageFont.truetype(p,s) if os.path.exists(p) else ImageFont.load_default()
F_disp =lambda s: fnt("Italiana-Regular.ttf",s)
F_read =lambda s: fnt("CrimsonPro-Regular.ttf",s)
F_ital =lambda s: fnt("CrimsonPro-Italic.ttf",s)
F_mono =lambda s: fnt("IBMPlexMono-Regular.ttf",s)
F_monob=lambda s: fnt("IBMPlexMono-Bold.ttf",s)
def text(cv,xy,s,f,fill,a=1.0,anc="mm",spc=8):
    if a<=0.01: return
    ov=Image.new("RGBA",cv.size,(0,0,0,0))
    ImageDraw.Draw(ov).multiline_text(xy,s,font=f,fill=(*fill,int(255*min(1,a))),anchor=anc,align="center",spacing=spc)
    cv.alpha_composite(ov)
def tlen(s,f): return ImageDraw.Draw(Image.new("RGB",(4,4))).textlength(s,font=f)
def spaced(s,gap=" "): return gap.join(list(s))
def kicker(cv,xy,s,size,fill,a=1.0,anc="mm",maxw=W-80):   # letter-spaced mono caps, auto-fit
    s=s.upper()
    for gap in ("  "," ",""):
        for sz in range(size,max(9,size-5),-1):
            t=gap.join(list(s))
            if tlen(t,F_mono(sz))<=maxw:
                text(cv,xy,t,F_mono(sz),fill,a,anc); return
    text(cv,xy,s,F_mono(max(9,size-5)),fill,a,anc)
def segrow(cv,y,items,size,center=True,x=None):           # a row of coloured (text,colour) chips
    fm=F_mono(size); tot=sum(tlen(t,fm) for t,_ in items)
    cx=(W/2-tot/2) if center else x
    for t,c in items:
        text(cv,(cx,y),t,fm,c,1.0,anc="lm"); cx+=tlen(t,fm)
def wrapped(cv,xy,s,f,fill,a,maxw,lh,anc="ma"):
    if a<=0.01: return
    words=s.split(); lines=[]; cur=""
    for w in words:
        t=(cur+" "+w).strip()
        if tlen(t,f)<=maxw: cur=t
        else: lines.append(cur); cur=w
    if cur: lines.append(cur)
    for i,ln in enumerate(lines): text(cv,(xy[0],xy[1]+i*lh),ln,f,fill,a,anc)
    return len(lines)
def layer(cv,fn):
    ov=Image.new("RGBA",cv.size,(0,0,0,0)); fn(ImageDraw.Draw(ov)); cv.alpha_composite(ov)
def rrect(d,box,rad,fill=None,outline=None,wid=1):
    d.rounded_rectangle(box,radius=rad,fill=fill,outline=outline,width=wid)

M=None
def meta():
    global M
    if M is None: M=json.load(open('/tmp/ontogeny_meta.json'))
    return M
def readspec(f):
    m=meta(); OUT=m['W']; SZ=OUT*OUT*3
    fp=open('/tmp/ontogeny_field.bin','rb'); fp.seek(f*SZ)
    a=np.frombuffer(fp.read(SZ),np.uint8).reshape(OUT,OUT,3); fp.close(); return a

# ── stage geometry ──
STX,STY,STW,STH=40,206,1000,966
SPM=30; SIDE=STW-2*SPM
def draw_specimen(cv,f):
    a=readspec(f)
    im=Image.fromarray(a).resize((SIDE,STH-2*SPM),Image.LANCZOS)
    cv.paste(im,(STX+SPM,STY+SPM))
def corner_mats(cv):
    def fn(d):
        ins=24; L=26; c=(*TEAL,90)
        xs=[STX+ins,STX+STW-ins]; ys=[STY+ins,STY+STH-ins]
        for i,x in enumerate(xs):
            for j,y in enumerate(ys):
                sx=1 if i==0 else -1; sy=1 if j==0 else -1
                d.line([(x,y),(x+sx*L,y)],fill=c,width=1); d.line([(x,y),(x,y+sy*L)],fill=c,width=1)
    layer(cv,fn)
def badge(cv,running=True):     # LIVE · SEM pill, top-right of the stage
    bx,by=STX+STW-30,STY+30; txt="LIVE · SEM"; tw=tlen(spaced(txt,' '),F_mono(20))
    pw=tw+58; ph=42; x0=bx-pw; y0=by
    layer(cv,lambda d:(rrect(d,[x0,y0,bx,y0+ph],ph//2,fill=(7,9,13,170),outline=(*HAIR,28),wid=1),
                       d.ellipse([x0+18-6,y0+ph//2-6,x0+18+6,y0+ph//2+6],fill=(*MAG,255))))
    text(cv,(x0+34,y0+ph//2),spaced(txt,' '),F_mono(20),INKS,0.95,anc="lm")
def show_count(cv,cx,y,n,unit,sub,a=1.0):
    num=str(n); fn=F_monob(82); fu=F_mono(36)
    nw=tlen(num,fn); uw=tlen(" "+unit,fu); tw=nw+uw
    layer(cv,lambda d:rrect(d,[cx-tw/2-28,y-52,cx+tw/2+28,y+70],18,fill=(7,9,13,135)))  # legibility plate
    text(cv,(cx-tw/2,y),num,fn,TEALB,a,anc="lm"); text(cv,(cx-tw/2+nw,y),(" "+unit),fu,(216,207,184),a,anc="lm")
    if sub: kicker(cv,(cx,y+52),sub,19,(201,191,168),0.9*a)

# ── diagnosis: membranes mini-diagram (faithful to render.js, fixed MCDA-twin case) ──
def membranes(cv,box,outcome,a=1.0):
    x0,y0,x1,y1=box; cx,cy=(x0+x1)/2,(y0+y1)/2; R=min(x1-x0,y1-y0)*0.34
    def fn(d):
        rrect(d,box,12,fill=(*OB2,int(255*a)),outline=(*HAIR,int(26*a)))
        n=outcome['n']
        if n>=2 and outcome.get('choType') in ('MCDA','MCMA','conjoined'):
            d.ellipse([cx-R,cy-R,cx+R,cy+R],fill=(215,123,255,int(36*a)),outline=(215,123,255,int(110*a)),width=1)  # shared placenta
            for s in (-1,1):
                sx=cx+s*R*0.40; sr=R*0.56
                d.ellipse([sx-sr,cy-sr,sx+sr,cy+sr],outline=(*TEAL,int(160*a)),width=2)                          # amnion
                d.ellipse([sx-R*0.22,cy-R*0.10,sx+R*0.10,cy+R*0.30],fill=(*TEALB,int(230*a)))                    # fetus body
                d.ellipse([sx+R*0.02,cy-R*0.34,sx+R*0.26,cy-R*0.10],fill=(*TEALB,int(230*a)))                    # head
        else:
            d.ellipse([cx-R,cy-R,cx+R,cy+R],fill=(215,123,255,int(34*a)),outline=(215,123,255,int(100*a)),width=1)
            d.ellipse([cx-R*0.6,cy-R*0.6,cx+R*0.6,cy+R*0.6],outline=(*TEAL,int(160*a)),width=2)
            d.ellipse([cx-R*0.22,cy-R*0.05,cx+R*0.12,cy+R*0.32],fill=(*TEALB,int(230*a)))
            d.ellipse([cx+R*0.0,cy-R*0.30,cx+R*0.26,cy-R*0.05],fill=(*TEALB,int(230*a)))
    layer(cv,fn)

def timeline(cv,p,idx,last,y=1812,a=1.0):
    x0,x1=80,1000
    def fn(d):
        d.line([(x0,y),(x1,y)],fill=(*HAIR,40),width=2)
        d.line([(x0,y),(x0+(x1-x0)*p,y)],fill=(*TEAL,200),width=2)
        for j in range(last+1):
            tx=x0+(x1-x0)*(j/last); r=2
            d.ellipse([tx-r,y-r,tx+r,y+r],fill=(*MUTD,120))
        tx=x0+(x1-x0)*p
        d.ellipse([tx-6,y-6,tx+6,y+6],fill=(*OB,255),outline=(*TEAL,255),width=2)
    layer(cv,fn)

def header(cv,fr,a=1.0):
    # brand line
    layer(cv,lambda d:d.ellipse([54-7,92-7,54+7,92+7],fill=(*TEAL,int(255*a))))   # running dot
    bx=80; text(cv,(bx,92),"cellauto",F_disp(54),INK,a,anc="lm")
    bw=tlen("cellauto",F_disp(54)); rx=bx+bw+22
    layer(cv,lambda d:d.line([(rx,92),(rx+30,92)],fill=(*TEAL,int(46*a)),width=1))
    text(cv,(rx+44,94),"ontogeny · the origin of a life",F_ital(30),MUT,a,anc="lm")
    # meta row (DAY · PHASE · cat.)
    segrow(cv,152,[(fr['metaDay'],TEAL),("   ·   ",MUTD),(fr['metaPhase'],INKS),
                   ("   ·   ",MUTD),("CAT. — ONTOGENESIS",MUTD)],22)
    layer(cv,lambda d:d.line([(40,188),(1040,188)],fill=(*HAIR,34),width=1))

NTITLE=84; OUTRO=96
def compose_frame(f):
    m=meta(); fr=m['fr'][f]; o=m['outcome']; NF=m['NF']; last=m['LAST']
    cv=Image.new("RGBA",(W,H),(*OB,255))
    # ---------- TITLE ----------
    if f<NTITLE:
        draw_specimen(cv,f); g=min(1,f/16)*min(1,(NTITLE-1-f)/16)
        cv.alpha_composite(Image.new("RGBA",(W,H),(*OB,int(210*g))))
        kicker(cv,(W//2,150),"cellauto · catalogue — ontogenesis",22,TEAL,0.7*g)
        text(cv,(W//2,560),"ONTOGENY",F_disp(122),INK,g)
        text(cv,(W//2,694),"the origin of a life",F_disp(48),TEAL,g)
        text(cv,(W//2,800),"one egg, one sperm — and the day it splits in two",F_ital(34),MUT,0.92*g)
        kicker(cv,(W//2,1240),"live · sem micrograph · seeded conception engine · seed 7",17,MUTD,0.65*g)
        return cv
    # ---------- CODA ----------
    if f>=NF-OUTRO:
        draw_specimen(cv,f); lf=f-(NF-OUTRO); g=min(1,lf/16)*min(1,(OUTRO-1-lf)/14)
        cv.alpha_composite(Image.new("RGBA",(W,H),(*OB,int(214*g))))
        kicker(cv,(W//2,556),"born",22,TEAL,0.7*g)
        text(cv,(W//2,706),"two lives, one origin",F_disp(60),INK,g)
        text(cv,(W//2,798),"monozygotic · MCDA · one placenta, two sacs",F_ital(30),MUT,0.9*g)
        kicker(cv,(W//2,1240),"cellauto · ontogeny · the origin of a life",17,MUTD,0.6*g)
        return cv
    # ---------- the VITRINE ----------
    header(cv,fr)
    # stage plate + specimen + mats + badge + scale + count
    layer(cv,lambda d:rrect(d,[STX,STY,STX+STW,STY+STH],14,fill=(*PLATE,255),outline=(*TEAL,40),wid=1))
    draw_specimen(cv,f); corner_mats(cv); badge(cv)
    kicker(cv,(STX+34,STY+STH-30),fr['scale'],18,MUTD,0.85,anc="lm")
    show_count(cv,W//2,STY+STH-150,fr['cn'],fr['cu'],fr['cs'])
    # caption
    kicker(cv,(W//2,1206),fr['capLabel'],22,TEAL,0.9)
    text(cv,(W//2,1262),fr['capTitle'],F_disp(56),INK,1.0)
    wrapped(cv,(W//2,1306),fr['capBlurb'],F_read(30),MUT,0.95,940,38,anc="ma")
    # diagnosis
    layer(cv,lambda d:d.line([(60,1432),(1020,1432)],fill=(*HAIR,40),width=1))
    kicker(cv,(60,1464),"outcome · the diagnosis",20,INKS,0.9,anc="lm",maxw=520)
    kicker(cv,(1020,1464),f"seed {m['seed']}",18,MUTD,0.7,anc="rm",maxw=300)
    # verdict (left)
    text(cv,(150,1556),str(o['n']),F_disp(104),TEAL,1.0)
    text(cv,(252,1530),o['label'].title(),F_disp(42),INK,1.0,anc="lm")
    zyg=o['zygosity']+(f" · {o['choType']}" if o['choType'] else "")
    text(cv,(254,1582),zyg,F_ital(28),MUT,0.95,anc="lm")
    # membranes (right)
    membranes(cv,(700,1492,884,1622),o)
    kicker(cv,(792,1640),o['choType'] or 'singleton',14,MUTD,0.85,maxw=220)
    # stats strip (centered)
    chs=" / ".join(map(str,o['chromosomes']))
    segrow(cv,1690,[("EGGS ",MUTD),(str(o['nOocytes']),INK),("    PLACENTAS ",MUTD),(str(o['placentas']),INK),
                    ("    SACS ",MUTD),(str(o['sacs']),INK),("    CHROMOSOMES ",MUTD),(chs,INK)],19)
    # note + timeline + footer
    wrapped(cv,(W//2,1716),m['hint'],F_ital(23),MUT,0.9,1000,30,anc="ma")
    timeline(cv,fr['p'],fr['i'],last)
    kicker(cv,(W//2,1866),"cellautomata · ontogeny",16,MUTD,0.5)
    return cv

if __name__=='__main__' and len(sys.argv)>2 and sys.argv[1]=='testc':
    compose_frame(int(sys.argv[2])).convert("RGB").save('/tmp/ontogeny_testc.png'); print("NF",meta()['NF']); sys.exit()
# ===== FULL RENDER =====
m=meta(); NF=m['NF']
silent="/tmp/ontogeny_silent.mp4"
wr=imageio_ffmpeg.write_frames(silent,(W,H),fps=FPS,codec="libx264",pix_fmt_in="rgb24",pix_fmt_out="yuv420p",macro_block_size=8,output_params=["-crf","19","-preset","medium"])
wr.send(None)
def emit(cv): wr.send(np.ascontiguousarray(np.asarray(cv.convert("RGB"),np.uint8)).tobytes())
for f in range(NF): emit(compose_frame(f))
wr.close(); print("composited",NF)
total=NF/FPS; out="/tmp/web8_ontogeny.mp4"
# a soft, clinical drone — fifth-stacked, lightly low-passed
fade=min(3.5,total/3); fin=min(3.0,total/3); fo=max(0.0,total-fade)
af=f"[1:a][2:a][3:a]amix=inputs=3,volume=0.10,lowpass=f=520,afade=t=in:st=0:d={fin:.2f},afade=t=out:st={fo:.2f}:d={fade:.2f}[a]"
subprocess.run([FF,"-y","-hide_banner","-loglevel","error","-i",silent,
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=55:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=82.5:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=110:sample_rate=44100",
 "-filter_complex",af,"-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","144k","-shortest","-movflags","+faststart",out],check=True)
print(f"-> {out}  {os.path.getsize(out)/1e6:.1f} MB  {total:.1f}s")
