"""ORIGINS — the whole arc, one reel: from Conway's GAME OF LIFE (life as a pure rule),
through the twelve-stage ORIGIN OF LIFE lab (life as chemistry), to ONTOGENY (life as you).
Every beat is an SEM specimen plate (numeral · name · caption) under one microscope.

Sources (regenerate first):
  node tools/morphogenesis/gen.mjs conway 0 130 1 n              -> /tmp/g_conway_n.bin
  for the 12 lab sims:  node tools/morphogenesis/gen.mjs <id> 200 130 1 <mode>
  ONTO_PRESET=singleton node tools/morphogenesis/ontogeny_gen.mjs -> /tmp/ontogeny_field.bin
Preview a frame:  python3 origin_film.py test <globalframe>      Full: python3 origin_film.py
"""
import json, os, sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
W,H=1080,1920; FPS=24; WIN=1000; WX=(W-WIN)//2; WY=400
BG=(7,8,12); BONE=(232,226,212); DIM=(140,146,158); AC=(214,180,128)
TEALB=(116,244,231)
FB="docs/web8/assets/fonts/"
def fnt(n,s):
    p=FB+n; return ImageFont.truetype(p,s) if os.path.exists(p) else ImageFont.load_default()
F_disp=lambda s: fnt("Italiana-Regular.ttf",s)
F_mono=lambda s: fnt("IBMPlexMono-Regular.ttf",s)
F_ital=lambda s: fnt("CrimsonPro-Italic.ttf",s)
def sp(s): return "  ".join(s.upper())
def text(cv,xy,s,f,fill,a=1.0,anc="mm",spc=8):
    if a<=0.01: return
    ov=Image.new("RGBA",cv.size,(0,0,0,0))
    ImageDraw.Draw(ov).multiline_text(xy,s,font=f,fill=(*fill,int(255*min(1,a))),anchor=anc,align="center",spacing=spc)
    cv.alpha_composite(ov)
def label(cv,xy,s,size,fill,a=1.0,anc="mm",maxw=W-90):
    s=s.upper()
    for gap in ("  "," ",""):
        for sz in range(size,size-4,-1):
            t=gap.join(s)
            if ImageDraw.Draw(cv).textlength(t,font=F_mono(sz))<=maxw:
                text(cv,xy,t,F_mono(sz),fill,a,anc); return
    text(cv,xy," ".join(s),F_mono(size-3),fill,a,anc)
def wrapped(cv,xy,s,f,fill,a,maxw,lh):
    words=s.split(); lines=[]; cur=""; d=ImageDraw.Draw(cv)
    for w in words:
        t=(cur+" "+w).strip()
        if d.textlength(t,font=f)<=maxw: cur=t
        else: lines.append(cur); cur=w
    if cur: lines.append(cur)
    for i,ln in enumerate(lines): text(cv,(xy[0],xy[1]+i*lh),ln,f,fill,a)
ROMAN=[(1000,'M'),(900,'CM'),(500,'D'),(400,'CD'),(100,'C'),(90,'XC'),(50,'L'),(40,'XL'),(10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]
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

# ── specimen sources ──
_meta={}
def lab_meta(id):
    if id not in _meta: _meta[id]=json.load(open(f'/tmp/g_{id}_meta.json'))
    return _meta[id]
def read_lab(id,simf,mode):
    m=lab_meta(id); W0,H0,SC=m['W'],m['H'],m['SC']; pw,ph=(W0*SC,H0*SC) if mode=='w' else (W0,H0); fb=pw*ph*4
    simf=max(0,min(m['frames']-1,int(simf)))
    f=open(f'/tmp/g_{id}_{mode}.bin','rb'); f.seek(simf*fb)
    a=np.frombuffer(f.read(fb),np.uint8).reshape(ph,pw,4)[:,:,:3].astype(np.float32); f.close(); return a,pw
ONTO=None
def onto_meta():
    global ONTO
    if ONTO is None: ONTO=json.load(open('/tmp/ontogeny_meta.json'))
    return ONTO
def read_onto(frac):
    m=onto_meta(); OUT=m['W']; NF=m['NF']; SZ=OUT*OUT*3
    fi=max(0,min(NF-1,int(frac*NF)))
    f=open('/tmp/ontogeny_field.bin','rb'); f.seek(fi*SZ)
    a=np.frombuffer(f.read(SZ),np.uint8).reshape(OUT,OUT,3).astype(np.float32); f.close(); return a,OUT
def window(act,t):
    if act['kind']=='lab':
        a,pw=read_lab(act['id'],t*(lab_meta(act['id'])['frames']-1),act['mode'])
        resample=Image.LANCZOS if act['mode']=='w' else Image.NEAREST
    else:
        f0,f1=act['range']; a,pw=read_onto(f0+(f1-f0)*t); resample=Image.LANCZOS
    zoom=act['zoom']*(1.0+0.08*t)
    cs=int(round(pw/zoom)); cs=max(8,min(pw,cs))
    off=int((pw-cs)*0.5+(pw-cs)*0.18*np.sin(t*np.pi))
    x=max(0,min(pw-cs,off)); y=max(0,min(pw-cs,int((pw-cs)*0.5)))
    sub=a[y:y+cs,x:x+cs]
    im=np.asarray(Image.fromarray(sub.astype(np.uint8)).resize((WIN,WIN),resample),np.float32)
    return np.clip(im*VIG,0,255).astype(np.uint8)

# ── the arc ──
SEC=[("The Game of Life","life as a pure rule",(150,214,176)),
     ("The Origin of Life","life as chemistry",(214,180,128)),
     ("The Origin of You","life as a person",(116,244,231))]
LAB=[
 ("soup","Miller–Urey","Lightning in a primordial sky forges the first organic molecules.","n",1.0),
 ("grayscott","Reaction–Diffusion","Bare chemistry self-organises into spots, stripes, and dividing forms.","w",1.5),
 ("raf","Autocatalytic Set","A closed web of reactions that collectively makes itself.","n",1.0),
 ("vesicles","Vesicles","Lipids fold into the first membranes — an inside and an outside.","w",1.0),
 ("vents","Alkaline Vents","Proton gradients at the sea floor drive the first metabolism.","n",1.0),
 ("minerals","Mineral Catalysis","Clay surfaces line monomers up into the first polymers.","n",1.0),
 ("chirality","Homochirality","Life commits to one handedness; the mirror form dies away.","n",1.0),
 ("rna","RNA World","A molecule that is both gene and enzyme begins to copy itself.","n",1.3),
 ("code","The Genetic Code","A mapping from nucleotide triplet to amino acid crystallises.","w",1.0),
 ("natural_selection","Natural Selection","Replicators compete, and the fitter lineages persist.","n",1.5),
 ("luca","LUCA","Every lineage converges on one last universal common ancestor.","n",1.8),
 ("life","Digital Life","Self-replicating code evolves, open-ended — life proper.","n",1.4),
]
ONTO_ACTS=[
 ((0.08,0.14),"Fertilisation","Sperm meets egg; two half-genomes fuse into one new cell — 46 chromosomes."),
 ((0.15,0.27),"Cleavage","That single cell divides, and divides again — 2, 4, 8 — a ball of cells."),
 ((0.57,0.64),"The Fetus","From one cell a whole body forms; by week eight every organ is present."),
 ((0.70,0.77),"Birth","Forty weeks on, the programme that began with the origin of life runs once more — as you."),
]
# build the timeline of segments
TITLE=110; BANNER=58; SEG=96; CODA=126; FADE=12
SEGS=[('title',None,TITLE),('banner',0,BANNER)]
SEGS.append(('plate',{'kind':'lab','id':'conway','mode':'n','zoom':1.5,'sec':0,'num':'0',
   'name':"The Game of Life","cap":"Four rules on a grid — and gliders, oscillators, and still lifes appear. Life, as pure computation."},SEG))
SEGS.append(('banner',1,BANNER))
for i,(id,nm,cap,mode,z) in enumerate(LAB):
    SEGS.append(('plate',{'kind':'lab','id':id,'mode':mode,'zoom':z,'sec':1,'num':roman(i+1),'name':nm,'cap':cap},SEG))
SEGS.append(('banner',2,BANNER))
for i,(rng,nm,cap) in enumerate(ONTO_ACTS):
    SEGS.append(('plate',{'kind':'onto','range':rng,'zoom':1.15,'sec':2,'num':roman(13+i),'name':nm,'cap':cap},SEG))
SEGS.append(('coda',None,CODA))
NF=sum(s[2] for s in SEGS)
NPLATES=sum(1 for s in SEGS if s[0]=='plate')
def locate(f):
    acc=0
    for kind,data,n in SEGS:
        if f<acc+n: return kind,data,(f-acc),n
        acc+=n
    return SEGS[-1][0],SEGS[-1][1],0,SEGS[-1][2]

def progress(cv,done,total,acc):
    d=ImageDraw.Draw(cv); x0,x1,y=120,960,1858
    d.line([(x0,y),(x1,y)],fill=(*DIM,90),width=2)
    d.line([(x0,y),(x0+(x1-x0)*done/total,y)],fill=(*acc,230),width=2)
    tx=x0+(x1-x0)*done/total; d.ellipse([tx-4,y-4,tx+4,y+4],fill=(*acc,255))

def plate_index(upto_kind_data):
    # ordinal of the current plate among all plates (for the progress bar)
    idx=0
    for kind,data,n in SEGS:
        if kind=='plate':
            idx+=1
            if data is upto_kind_data: return idx
    return idx

def compose_frame(f):
    kind,data,lf,n=locate(f)
    cv=Image.new("RGBA",(W,H),(*BG,255)); d=ImageDraw.Draw(cv)
    if kind=='title':
        g=min(1,lf/18)*min(1,(n-1-lf)/16)
        text(cv,(W//2,520),sp("cellautomata · the whole arc"),F_mono(22),DIM,0.7*g)
        text(cv,(W//2,830),"ORIGINS",F_disp(154),BONE,g)
        text(cv,(W//2,990),"from the game of life to the origin of you",F_ital(46),AC,g)
        label(cv,(W//2,1340),"conway · abiogenesis · ontogeny",20,DIM,0.7*g)
        return cv
    if kind=='banner':
        nm,sub,acc=SEC[data]; g=min(1,lf/16)*min(1,(n-1-lf)/14)
        text(cv,(W//2,560),roman(data+1),F_disp(76),acc,0.9*g)
        text(cv,(W//2,860),nm.upper(),F_disp(96),BONE,g)
        text(cv,(W//2,1000),sub,F_ital(46),acc,0.95*g)
        return cv
    if kind=='coda':
        g=min(1,lf/18)*min(1,(n-1-lf)/16)
        text(cv,(W//2,560),sp("one story, told three times"),F_mono(22),DIM,0.7*g)
        text(cv,(W//2,820),"a rule became a chemistry,",F_disp(60),BONE,g)
        text(cv,(W//2,910),"a chemistry became you",F_disp(60),TEALB,g)
        label(cv,(W//2,1320),"cellautomata · origins · conway → ontogeny",18,DIM,0.6*g)
        return cv
    # ---- plate ----
    sec=data['sec']; acc=SEC[sec][2]; t=lf/n
    a=min(1,lf/FADE)*min(1,(n-1-lf)/FADE)
    img=window(data,t); win=Image.fromarray(img)
    if a<1: win=Image.blend(Image.new("RGB",(WIN,WIN),BG),win,a)
    cv.paste(win,(WX,WY)); reticle(d,WX,WY,WIN,acc,a)
    text(cv,(W//2,150),data['num'],F_disp(72),acc,0.9*a)
    text(cv,(W//2,250),data['name'].upper(),F_disp(60),BONE,a)
    text(cv,(W//2,322),sp(SEC[sec][0]),F_mono(16),DIM,0.5*a)
    wrapped(cv,(W//2,WY+WIN+70),data['cap'],F_ital(40),BONE,a,W-150,52)
    progress(cv,plate_index(data),NPLATES,acc)
    label(cv,(W//2,1900),"cellautomata · origins",15,DIM,0.4)
    return cv

if __name__=='__main__' and len(sys.argv)>2 and sys.argv[1]=='test':
    compose_frame(int(sys.argv[2])).convert("RGB").save('/tmp/origin_test.png'); print("NF",NF,"plates",NPLATES); sys.exit()
# ===== FULL RENDER =====
silent="/tmp/origin_silent.mp4"
wr=imageio_ffmpeg.write_frames(silent,(W,H),fps=FPS,codec="libx264",pix_fmt_in="rgb24",pix_fmt_out="yuv420p",macro_block_size=8,output_params=["-crf","19","-preset","medium"])
wr.send(None)
def emit(cv): wr.send(np.ascontiguousarray(np.asarray(cv.convert("RGB"),np.uint8)).tobytes())
for f in range(NF): emit(compose_frame(f))
wr.close(); print("composited",NF)
total=NF/FPS; out="/tmp/web8_origins.mp4"
fade=min(3.5,total/3); fin=min(3.0,total/3); fo=max(0.0,total-fade)
af=f"[1:a][2:a][3:a]amix=inputs=3,volume=0.11,lowpass=f=480,afade=t=in:st=0:d={fin:.2f},afade=t=out:st={fo:.2f}:d={fade:.2f}[a]"
subprocess.run([FF,"-y","-hide_banner","-loglevel","error","-i",silent,
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=48:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=72:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=144:sample_rate=44100",
 "-filter_complex",af,"-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","144k","-shortest","-movflags","+faststart",out],check=True)
print(f"-> {out}  {os.path.getsize(out)/1e6:.1f} MB  {total:.1f}s")
