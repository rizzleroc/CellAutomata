"""LAB TOUR — a 60-second grand tour of the whole web8 origin-of-life lab: every simulation,
in canonical order, each as an SEM specimen plate (numeral · name · one-line caption), building
the arc from prebiotic chemistry to digital life.

Reads the SEM clips made by gen.mjs:  node tools/morphogenesis/gen.mjs <id> 200 130 1 w
Preview a frame:  python3 lab_tour_film.py test <globalframe>
Full render:      python3 lab_tour_film.py   ->  /tmp/web8_lab_tour.mp4
"""
import json, os, sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
W,H=1080,1920; FPS=24; WIN=1000; WX=(W-WIN)//2; WY=400
BG=(7,8,12); BONE=(232,226,212); DIM=(140,146,158); AC=(214,180,128)
FB="docs/web8/assets/fonts/"
def fnt(n,s):
    p=FB+n; return ImageFont.truetype(p,s) if os.path.exists(p) else ImageFont.load_default()
F_disp=lambda s: fnt("Italiana-Regular.ttf",s)
F_mono=lambda s: fnt("IBMPlexMono-Regular.ttf",s)
F_monob=lambda s: fnt("IBMPlexMono-Bold.ttf",s)
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
    words=s.split(); lines=[]; cur=""
    d=ImageDraw.Draw(cv)
    for w in words:
        t=(cur+" "+w).strip()
        if d.textlength(t,font=f)<=maxw: cur=t
        else: lines.append(cur); cur=w
    if cur: lines.append(cur)
    for i,ln in enumerate(lines):
        text(cv,(xy[0],xy[1]+i*lh),ln,f,fill,a)
ROMAN=[(10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]
def roman(n):
    s=''
    for v,sym in ROMAN:
        while n>=v: s+=sym; n-=v
    return s
# canonical lab order: id, plate name, one-line caption. Drop/reorder freely.
STAGES=[
 ("soup","Miller–Urey","Lightning in a primordial sky forges the first organic molecules."),
 ("grayscott","Reaction–Diffusion","Bare chemistry self-organises into spots, stripes, and dividing forms."),
 ("raf","Autocatalytic Set","A closed web of reactions that collectively makes itself."),
 ("vesicles","Vesicles","Lipids fold into the first membranes — an inside and an outside."),
 ("vents","Alkaline Vents","Proton gradients at the sea floor drive the first metabolism."),
 ("minerals","Mineral Catalysis","Clay surfaces line monomers up into the first polymers."),
 ("chirality","Homochirality","Life commits to one handedness; the mirror form dies away."),
 ("rna","RNA World","A molecule that is both gene and enzyme begins to copy itself."),
 ("code","The Genetic Code","A mapping from nucleotide triplet to amino acid crystallises."),
 ("coacervate","Coacervates","Droplets concentrate the chemistry into the first protocells."),
 ("natural_selection","Natural Selection","Replicators compete, and the fitter lineages persist."),
 ("luca","LUCA","Every lineage converges on one last universal common ancestor."),
 ("life","Digital Life","Self-replicating code evolves, open-ended — life proper."),
]
def meta(id): return json.load(open(f'/tmp/g_{id}_meta.json'))
def read_sem(id, simf, m):
    W0,H0,SC=m['W'],m['H'],m['SC']; pw,ph=W0*SC,H0*SC; fb=pw*ph*4
    simf=max(0,min(m['frames']-1,int(simf)))
    f=open(f'/tmp/g_{id}_w.bin','rb'); f.seek(simf*fb)
    a=np.frombuffer(f.read(fb),np.uint8).reshape(ph,pw,4)[:,:,:3].astype(np.float32); f.close()
    return a, pw
def vig(n):
    yy,xx=np.mgrid[0:n,0:n]; r=np.hypot((xx-n/2)/(n/2),(yy-n/2)/(n/2))
    return np.clip(1-0.42*np.clip(r-0.58,0,1)**1.7,0,1).astype(np.float32)[...,None]
VIG=vig(WIN)
def window_img(id, m, t):                                # t in 0..1 across the segment (Ken-Burns + sim time)
    simf=t*(m['frames']-1)
    a,pw=read_sem(id,simf,m)
    zoom=1.0+0.10*t                                      # slow push-in
    cs=int(pw/zoom); off=int((pw-cs)*0.5 + (pw-cs)*0.18*np.sin(t*np.pi))
    x=max(0,min(pw-cs,off)); y=max(0,min(pw-cs,int((pw-cs)*0.5)))
    sub=a[y:y+cs,x:x+cs]
    im=np.asarray(Image.fromarray(sub.astype(np.uint8)).resize((WIN,WIN),Image.LANCZOS),np.float32)
    return np.clip(im*VIG,0,255).astype(np.uint8)
def reticle(d,x,y,n,a=1.0):
    for cx,cy in[(x,y),(x+n,y),(x,y+n),(x+n,y+n)]:
        d.line([(cx-22,cy),(cx+22,cy)],fill=(*AC,int(150*a)),width=1); d.line([(cx,cy-22),(cx,cy+22)],fill=(*AC,int(150*a)),width=1)
    d.rectangle([x-1,y-1,x+n,y+n],outline=(*AC,int(60*a)),width=1)
def progress(cv,i,n):
    d=ImageDraw.Draw(cv); y=1854; gap=26; x0=W//2-(n-1)*gap//2
    for j in range(n):
        x=x0+j*gap; r=5 if j==i else 3
        fill=AC if j==i else DIM
        d.ellipse([x-r,y-r,x+r,y+r],fill=(*fill,255 if j==i else 120))
# ---- timeline ----
TITLE=114; SEG=102; FADE=12
NF=TITLE+SEG*len(STAGES)
def seg_at(f):                                          # -> (stage_index, local_t, alpha) or (None,..) in title
    if f<TITLE: return None,0,0
    k=(f-TITLE)//SEG; lf=(f-TITLE)-k*SEG
    k=min(k,len(STAGES)-1)
    a=min(1,lf/FADE)*min(1,(SEG-1-lf)/FADE)            # fade each plate in/out
    return k,lf/SEG,a
def compose_frame(f):
    cv=Image.new("RGBA",(W,H),(*BG,255)); d=ImageDraw.Draw(cv)
    if f<TITLE:
        g=min(1,f/18)*min(1,(TITLE-1-f)/16)
        text(cv,(W//2,560),sp("a laboratory of beginnings"),F_mono(22),DIM,0.7*g)
        text(cv,(W//2,860),"ORIGINS",F_disp(150),BONE,g)
        text(cv,(W//2,1010),"thirteen stages, from chemistry to life",F_ital(46),AC,g)
        label(cv,(W//2,1360),"cellautomata · web8 · the origin-of-life lab",20,DIM,0.7*g)
        return cv
    k,t,a=seg_at(f); id,name,cap=STAGES[k]; m=meta(id)
    img=window_img(id,m,t)
    win=Image.fromarray(img);
    if a<1: win=Image.blend(Image.new("RGB",(WIN,WIN),BG),win,a)
    cv.paste(win,(WX,WY)); reticle(d,WX,WY,WIN,a)
    # plate chrome
    text(cv,(W//2,150),roman(k+1),F_disp(72),AC,0.9*a)
    text(cv,(W//2,250),name.upper(),F_disp(60),BONE,a)
    text(cv,(W//2,322),sp("live specimen"),F_mono(17),DIM,0.5*a)
    wrapped(cv,(W//2,WY+WIN+70),cap,F_ital(40),BONE,a,W-150,52)
    label(cv,(W//2,WY+WIN+184),m.get('label',id),17,DIM,0.6*a)
    progress(cv,k,len(STAGES))
    label(cv,(W//2,1892),"cellautomata · web8 · origins",15,DIM,0.4)
    return cv
if __name__=='__main__' and len(sys.argv)>2 and sys.argv[1]=='test':
    compose_frame(int(sys.argv[2])).convert("RGB").save('/tmp/lab_tour_test.png'); print("saved",NF,"frames total"); sys.exit()
# ===== FULL RENDER =====
silent="/tmp/lab_tour_silent.mp4"
wr=imageio_ffmpeg.write_frames(silent,(W,H),fps=FPS,codec="libx264",pix_fmt_in="rgb24",pix_fmt_out="yuv420p",macro_block_size=8,output_params=["-crf","19","-preset","medium"])
wr.send(None)
def emit(cv): wr.send(np.ascontiguousarray(np.asarray(cv.convert("RGB"),np.uint8)).tobytes())
for f in range(NF):
    emit(compose_frame(f))
wr.close(); print("composited",NF)
total=NF/FPS; out="/tmp/web8_lab_tour.mp4"
fade=min(3.5,total/3); fin=min(3.0,total/3); fo=max(0.0,total-fade)
af=f"[1:a][2:a][3:a]amix=inputs=3,volume=0.12,lowpass=f=500,afade=t=in:st=0:d={fin:.2f},afade=t=out:st={fo:.2f}:d={fade:.2f}[a]"
subprocess.run([FF,"-y","-hide_banner","-loglevel","error","-i",silent,
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=52:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=78:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=156:sample_rate=44100",
 "-filter_complex",af,"-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","144k","-shortest","-movflags","+faststart",out],check=True)
print(f"-> {out}  {os.path.getsize(out)/1e6:.1f} MB  {total:.1f}s")
