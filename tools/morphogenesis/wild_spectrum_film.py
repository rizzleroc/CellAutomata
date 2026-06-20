"""WILD SPECTRUM — the entire origin-of-life lab driven to its extremes, one dramatic outcome per
stage: Conway overpopulation collapse, Gray-Scott u-skate solitons, a Miller-Urey lightning storm,
runaway autocatalysis, violent vesicle budding, a proton flood, runaway polymerisation, shattered
chirality, RNA & digital-life error catastrophes, a dissolving genetic code, boom-and-bust selection,
a LUCA that never forms — capped by life's human extreme, quintuplets. Each plate is the REAL sim at
wild parameters (re-genned via gen.mjs GEN_PARAMS / ontogeny_gen ONTO_PRESET).
Preview:  python3 wild_spectrum_film.py test <f>     Full: python3 wild_spectrum_film.py
"""
import json, os, sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
W,H,FPS=1080,1920,24; WIN=1000; WX=(W-WIN)//2; WY=400
BG=(7,8,12); BONE=(232,226,212); DIM=(140,146,158); AMBER=(255,193,107); TEAL=(116,236,214)
FB="docs/web8/assets/fonts/"
def fnt(n,s): p=FB+n; return ImageFont.truetype(p,s) if os.path.exists(p) else ImageFont.load_default()
F_disp=lambda s: fnt("Italiana-Regular.ttf",s)
F_mono=lambda s: fnt("IBMPlexMono-Regular.ttf",s)
F_ital=lambda s: fnt("CrimsonPro-Italic.ttf",s)
def asc(s):   # the self-hosted fonts lack Greek / some symbols — fall back to ASCII
    for a,b in (("μ","mu"),("γ","gamma"),("β","beta"),("α","alpha"),("Δ","delta-"),("ε","eps"),
                ("Σ","sum "),("≫",">>"),("≈","~"),("→","->"),("↔","<->"),("±","+/-")):
        s=s.replace(a,b)
    return s
def text(cv,xy,s,f,fill,a=1.0,anc="mm"):
    if a<=0.01: return
    s=asc(s); ov=Image.new("RGBA",cv.size,(0,0,0,0)); ImageDraw.Draw(ov).text(xy,s,font=f,fill=(*fill,int(255*min(1,a))),anchor=anc); cv.alpha_composite(ov)
def tlen(s,f): return ImageDraw.Draw(Image.new("RGB",(4,4))).textlength(s,font=f)
def label(cv,xy,s,size,fill,a=1.0,anc="mm",maxw=W-90):
    s=asc(s).upper()
    for gap in ("  "," ",""):
        for sz in range(size,max(9,size-5),-1):
            t=gap.join(list(s))
            if tlen(t,F_mono(sz))<=maxw: text(cv,xy,t,F_mono(sz),fill,a,anc); return
    text(cv,xy,s,F_mono(max(9,size-5)),fill,a,anc)
def wrapped(cv,xy,s,f,fill,a,maxw,lh):
    if a<=0.01: return
    words=asc(s).split(); lines=[]; cur=""
    for w in words:
        t=(cur+" "+w).strip()
        if tlen(t,f)<=maxw: cur=t
        else: lines.append(cur); cur=w
    if cur: lines.append(cur)
    for i,ln in enumerate(lines): text(cv,(xy[0],xy[1]+i*lh),ln,f,fill,a)
ROMAN=[(10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]
def roman(n):
    s=''
    for v,sym in ROMAN:
        while n>=v: s+=sym; n-=v
    return s
def vig(n):
    yy,xx=np.mgrid[0:n,0:n]; r=np.hypot((xx-n/2)/(n/2),(yy-n/2)/(n/2))
    return np.clip(1-0.42*np.clip(r-0.58,0,1)**1.7,0,1).astype(np.float32)[...,None]
VIG=vig(WIN)
def reticle(d,x,y,n,acc,a=1.0):
    for cx,cy in[(x,y),(x+n,y),(x,y+n),(x+n,y+n)]:
        d.line([(cx-22,cy),(cx+22,cy)],fill=(*acc,int(150*a)),width=1); d.line([(cx,cy-22),(cx,cy+22)],fill=(*acc,int(150*a)),width=1)
    d.rectangle([x-1,y-1,x+n,y+n],outline=(*acc,int(60*a)),width=1)
# ── sources ──
_M={}
def lab_meta(i):
    if i not in _M: _M[i]=json.load(open(f'/tmp/g_{i}_meta.json'))
    return _M[i]
def read_lab(i,simf,mode):
    m=lab_meta(i); W0,H0,SC=m['W'],m['H'],m['SC']; pw,ph=(W0*SC,H0*SC) if mode=='w' else (W0,H0); fb=pw*ph*4
    simf=max(0,min(m['frames']-1,int(simf)))
    f=open(f'/tmp/g_{i}_{mode}.bin','rb'); f.seek(simf*fb)
    a=np.frombuffer(f.read(fb),np.uint8).reshape(ph,pw,4)[:,:,:3].astype(np.float32); f.close(); return a,pw
def onto_meta(p):
    k=f"onto:{p}"
    if k not in _M: _M[k]=json.load(open(f'/tmp/onto_{p}_meta.json'))
    return _M[k]
def read_onto(p,frac):
    m=onto_meta(p); OUT=m['W']; NF=m['NF']; SZ=OUT*OUT*3
    fi=max(0,min(NF-1,int(frac*NF)))
    f=open(f'/tmp/onto_{p}_field.bin','rb'); f.seek(fi*SZ)
    a=np.frombuffer(f.read(SZ),np.uint8).reshape(OUT,OUT,3).astype(np.float32); f.close(); return a,OUT
def window(it,t):
    if it['kind']=='lab':
        a,pw=read_lab(it['id'],t*(lab_meta(it['id'])['frames']-1),it['mode']); rs=Image.LANCZOS if it['mode']=='w' else Image.NEAREST
    else:
        a,pw=read_onto(it['id'],0.12+0.62*t); rs=Image.LANCZOS
    zoom=it['zoom']*(1.0+0.08*t); cs=max(8,min(pw,int(round(pw/zoom))))
    off=int((pw-cs)*0.5+(pw-cs)*0.18*np.sin(t*np.pi)); x=max(0,min(pw-cs,off)); y=max(0,min(pw-cs,int((pw-cs)*0.5)))
    im=np.asarray(Image.fromarray(a[y:y+cs,x:x+cs].astype(np.uint8)).resize((WIN,WIN),rs),np.float32)
    return np.clip(im*VIG,0,255).astype(np.uint8)
# ── the wild line-up (whole spectrum) ──
def L(id,mode,zoom,wild,sim,tag,cap,acc): return dict(kind='lab',id=id,mode=mode,zoom=zoom,wild=wild,sim=sim,tag=tag,cap=cap,acc=acc)
WILD=[
 L('conway','n',1.25,"Overpopulation Collapse","Conway · Game of Life","density 0.50",
   "Crowd the grid and life chokes on itself — a churning bloom starves back to scattered survivors.","warn"),
 L('grayscott','w',1.5,"U-skate Solitons","Reaction–Diffusion","F 0.062 · k 0.061",
   "Spots stop sitting still: they crawl, collide, and self-replicate across the whole dish.","teal"),
 L('soup','n',1.0,"Lightning Storm","Miller–Urey","spark·boil·reducing = max",
   "Max spark, max heat, a fully reducing sky — the primordial soup synthesises in a frenzy.","teal"),
 L('raf','n',1.0,"Runaway Ignition","Autocatalytic Set","catalysis 6 · decay 0",
   "Crank catalysis with nothing to undo it and the reaction web ignites — a self-making fire.","teal"),
 L('vesicles','w',1.0,"Violent Budding","Vesicles","γ 4.0 · max noise",
   "Strong phase-separation and floppy membranes: vesicles bud, bridge and burst without limit.","teal"),
 L('vents','n',1.0,"Proton Flood","Alkaline Vents","ΔpH 1.0 · max updraft",
   "A maximal proton-motive force across the vent drives the first metabolism past its limit.","teal"),
 L('minerals','n',1.0,"Runaway Polymerisation","Mineral Catalysis","k_clay 0.6 · no hydrolysis",
   "Every clay face catalysing, nothing to break the chains — monomers polymerise without brakes.","teal"),
 L('chirality','n',1.0,"Symmetry Shattered","Homochirality","α 0.3 · β 1.5",
   "Strong autocatalysis and mutual inhibition: one hand annihilates the mirror and seizes the world.","teal"),
 L('rna','n',1.3,"Error Catastrophe","RNA World","μ = 0.30",
   "Push the copy error past the threshold and the master sequence melts into noise — the quasispecies dissolves.","warn"),
 L('code','w',1.0,"The Code Dissolves","The Genetic Code","no selection · max reassign",
   "Without selection for error-minimisation, the codon → amino-acid map never crystallises.","warn"),
 L('natural_selection','n',1.5,"Boom & Bust","Natural Selection","lifespan 15",
   "Short lives drive violent turnover — populations explode and crash in waves.","warn"),
 L('luca','n',1.8,"No Common Ancestor","LUCA","max divergence · no selection",
   "Max divergence, no selection: lineages scatter and never converge — LUCA never forms.","warn"),
 L('life','n',1.4,"Genome Meltdown","Digital Life","ε ≫ 1/L",
   "Mutation past the error threshold corrupts the copy machinery itself — every lineage dies.","warn"),
 dict(kind='onto',id='quints',mode='',zoom=1.05,wild="Quintuplets",sim="Ontogeny",tag="5 zygotes",
   cap="And life carried to its human extreme: five at once — about one in fifty million by chance.",acc='teal'),
]
ACC={'warn':AMBER,'teal':TEAL}
TITLE=100; SEG=110; CODA=120; FADE=12
NSC=len(WILD); NF=TITLE+SEG*NSC+CODA
def loc(f):
    if f<TITLE: return ('title',0,f)
    if f>=TITLE+SEG*NSC: return ('coda',0,f-(TITLE+SEG*NSC))
    k=(f-TITLE)//SEG; return ('plate',min(k,NSC-1),(f-TITLE)-k*SEG)
def compose(f):
    kind,k,lf=loc(f); cv=Image.new("RGBA",(W,H),(*BG,255)); d=ImageDraw.Draw(cv)
    if kind=='title':
        g=min(1,lf/18)*min(1,(TITLE-1-lf)/16)
        text(cv,(W//2,560),"  ".join("THE LAB, OFF THE RAILS"),F_mono(22),AMBER,0.7*g)
        text(cv,(W//2,860),"WILD SPECTRUM",F_disp(118),BONE,g)
        text(cv,(W//2,1010),"every stage, driven to its extreme",F_ital(46),TEAL,g)
        label(cv,(W//2,1360),"conway · abiogenesis · ontogeny — at the edge",20,DIM,0.7*g)
        return cv
    if kind=='coda':
        g=min(1,lf/18)*min(1,(CODA-1-lf)/16)
        text(cv,(W//2,600),"  ".join("SAME RULES · WILDLY DIFFERENT ENDS"),F_mono(20),AMBER,0.65*g)
        text(cv,(W//2,840),"push any law to its limit",F_disp(58),BONE,g)
        text(cv,(W//2,928),"and life shows you the edge",F_disp(58),TEAL,g)
        label(cv,(W//2,1320),"cellautomata · wild spectrum",17,DIM,0.5*g)
        return cv
    it=WILD[k]; acc=ACC[it['acc']]; t=lf/SEG; a=min(1,lf/FADE)*min(1,(SEG-1-lf)/FADE)
    img=window(it,t); win=Image.fromarray(img)
    if a<1: win=Image.blend(Image.new("RGB",(WIN,WIN),BG),win,a)
    cv.paste(win,(WX,WY)); reticle(d,WX,WY,WIN,acc,a)
    label(cv,(W//2,138),f"wild {roman(k+1)} / {roman(NSC)}",18,DIM,0.7*a)
    text(cv,(W//2,224),it['wild'].upper(),F_disp(58),acc,a)
    label(cv,(W//2,300),f"{it['sim']}   ·   {it['tag']}",16,DIM,0.6*a)
    wrapped(cv,(W//2,WY+WIN+64),it['cap'],F_ital(38),BONE,a,W-150,50)
    # progress
    for j in range(NSC):
        x=W//2-(NSC-1)*16+j*32; r=5 if j==k else 3; fill=acc if j==k else DIM
        d.ellipse([x-r,1858-r,x+r,1858+r],fill=(*fill,255 if j==k else 110))
    label(cv,(W//2,1900),"cellautomata · wild spectrum",14,DIM,0.4)
    return cv
if __name__=='__main__' and len(sys.argv)>2 and sys.argv[1]=='test':
    compose(int(sys.argv[2])).convert("RGB").save('/tmp/wsp_test.png'); print("NF",NF,"plates",NSC); sys.exit()
# ===== FULL RENDER =====
silent="/tmp/wsp_silent.mp4"
wr=imageio_ffmpeg.write_frames(silent,(W,H),fps=FPS,codec="libx264",pix_fmt_in="rgb24",pix_fmt_out="yuv420p",macro_block_size=8,output_params=["-crf","19","-preset","medium"])
wr.send(None)
for f in range(NF): wr.send(np.ascontiguousarray(np.asarray(compose(f).convert("RGB"),np.uint8)).tobytes())
wr.close(); print("composited",NF)
total=NF/FPS; out="/tmp/web8_wild_spectrum.mp4"
fade=min(3.5,total/3); fin=min(3.0,total/3); fo=max(0.0,total-fade)
af=f"[1:a][2:a][3:a]amix=inputs=3,volume=0.11,lowpass=f=500,afade=t=in:st=0:d={fin:.2f},afade=t=out:st={fo:.2f}:d={fade:.2f}[a]"
subprocess.run([FF,"-y","-hide_banner","-loglevel","error","-i",silent,
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=50:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=75:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=150:sample_rate=44100",
 "-filter_complex",af,"-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","144k","-shortest","-movflags","+faststart",out],check=True)
print(f"-> {out}  {os.path.getsize(out)/1e6:.1f} MB  {total:.1f}s")
