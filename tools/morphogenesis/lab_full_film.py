"""LAB (FULL) — the complete web8 origin-of-life lab: for each stage, the photoreal 3-D APPARATUS
(rendered offscreen by render_apparatus.mjs) above its live EXPERIMENT micrograph (gen.mjs SEM/native).
A 60-second tour pairing instrument + specimen, stage by stage.

Needs:  /tmp/app_<appid>.bin (+meta)   and   /tmp/g_<simid>_<mode>.bin (+meta)
Preview: python3 lab_full_film.py test <globalframe>     Full: python3 lab_full_film.py
"""
import json, os, sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
W,H=1080,1920; FPS=24
BG=(7,8,12); BONE=(232,226,212); DIM=(140,146,158); AC=(214,180,128)
# apparatus panel + micrograph inset geometry
AWX,AWY,AW,AH=40,300,1000,700
MIC=384; MX=(W-MIC)//2; MY=1150
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
    words=s.split(); lines=[]; cur=""; d=ImageDraw.Draw(cv)
    for w in words:
        t=(cur+" "+w).strip()
        if d.textlength(t,font=f)<=maxw: cur=t
        else: lines.append(cur); cur=w
    if cur: lines.append(cur)
    for i,ln in enumerate(lines): text(cv,(xy[0],xy[1]+i*lh),ln,f,fill,a)
ROMAN=[(10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]
def roman(n):
    s=''
    for v,sym in ROMAN:
        while n>=v: s+=sym; n-=v
    return s
# stage: sim_id, apparatus_id, plate name, caption, sim render mode, micrograph base-zoom
STAGES=[
 ("soup","miller_urey","Miller–Urey","Lightning in a primordial sky forges the first organic molecules.","n",1.2),
 ("grayscott","grayscott_dish","Reaction–Diffusion","Bare chemistry self-organises into spots, stripes, and dividing forms.","w",1.0),
 ("raf","raf_flask","Autocatalytic Set","A closed web of reactions that collectively makes itself.","n",1.2),
 ("vesicles","vesicle_microscope","Vesicles","Lipids fold into the first membranes — an inside and an outside.","w",1.0),
 ("vents","vent_reactor","Alkaline Vents","Proton gradients at the sea floor drive the first metabolism.","w",1.0),
 ("minerals","mineral_flask","Mineral Catalysis","Clay surfaces line monomers up into the first polymers.","w",1.0),
 ("chirality","chirality_polarimeter","Homochirality","Life commits to one handedness; the mirror form dies away.","n",1.0),
 ("rna","rna_thermocycler","RNA World","A molecule that is both gene and enzyme begins to copy itself.","n",1.3),
 ("code","code_bench","The Genetic Code","A mapping from nucleotide triplet to amino acid crystallises.","w",1.0),
 ("natural_selection","microfluidic_chip","Natural Selection","Replicators compete, and the fitter lineages persist.","n",1.5),
 ("luca","luca_console","LUCA","Every lineage converges on one last universal common ancestor.","n",1.8),
 ("life","stromatolite","Digital Life","Self-replicating code evolves, open-ended — life proper.","n",1.4),
]
def smeta(id): return json.load(open(f'/tmp/g_{id}_meta.json'))
def read_sim(id, simf, m, mode):
    W0,H0,SC=m['W'],m['H'],m['SC']; pw,ph=(W0*SC,H0*SC) if mode=='w' else (W0,H0); fb=pw*ph*4
    simf=max(0,min(m['frames']-1,int(simf)))
    f=open(f'/tmp/g_{id}_{mode}.bin','rb'); f.seek(simf*fb)
    a=np.frombuffer(f.read(fb),np.uint8).reshape(ph,pw,4)[:,:,:3].astype(np.float32); f.close()
    return a, pw
def mic_img(id, m, mode, base, t):
    a,pw=read_sim(id,t*(m['frames']-1),m,mode)
    cs=max(8,min(pw,int(round(pw/(base*(1.0+0.06*t))))))
    x=max(0,min(pw-cs,int((pw-cs)*0.5))); y=x
    sub=a[y:y+cs,x:x+cs]
    rs=Image.LANCZOS if mode=='w' else Image.NEAREST
    return np.asarray(Image.fromarray(sub.astype(np.uint8)).resize((MIC,MIC),rs),np.uint8)
def ameta(aid): return json.load(open(f'/tmp/app_{aid}_meta.json'))
def app_img(aid, am, t):
    AWp,AHp,fr=am['W'],am['H'],am['frames']; fb=AWp*AHp*4
    af=max(0,min(fr-1,int(t*(fr-1))))
    f=open(f'/tmp/app_{aid}.bin','rb'); f.seek(af*fb)
    a=np.frombuffer(f.read(fb),np.uint8).reshape(AHp,AWp,4)[:,:,:3]; f.close()
    if (AWp,AHp)!=(AW,AH): a=np.asarray(Image.fromarray(a).resize((AW,AH),Image.LANCZOS))
    return a
def frame_box(d,x,y,w,h,a=1.0,tick=22):
    for cx,cy in[(x,y),(x+w,y),(x,y+h),(x+w,y+h)]:
        d.line([(cx-tick,cy),(cx+tick,cy)],fill=(*AC,int(150*a)),width=1); d.line([(cx,cy-tick),(cx,cy+tick)],fill=(*AC,int(150*a)),width=1)
    d.rectangle([x-1,y-1,x+w,y+h],outline=(*AC,int(60*a)),width=1)
def progress(cv,i,n,a=1.0):
    d=ImageDraw.Draw(cv); y=1788; gap=26; x0=W//2-(n-1)*gap//2
    for j in range(n):
        x=x0+j*gap; r=5 if j==i else 3; fill=AC if j==i else DIM
        d.ellipse([x-r,y-r,x+r,y+r],fill=(*fill,int((255 if j==i else 120)*a)))
TITLE=114; SEG=110; FADE=12
NF=TITLE+SEG*len(STAGES)
def seg_at(f):
    if f<TITLE: return None,0,0
    k=min((f-TITLE)//SEG,len(STAGES)-1); lf=(f-TITLE)-k*SEG
    return k,lf/SEG,min(1,lf/FADE)*min(1,(SEG-1-lf)/FADE)
def blend_bg(img,a):
    if a>=1: return Image.fromarray(img)
    return Image.blend(Image.new("RGB",(img.shape[1],img.shape[0]),BG),Image.fromarray(img),max(0,a))
def compose_frame(f):
    cv=Image.new("RGBA",(W,H),(*BG,255)); d=ImageDraw.Draw(cv)
    if f<TITLE:
        g=min(1,f/18)*min(1,(TITLE-1-f)/16)
        text(cv,(W//2,560),sp("a laboratory of beginnings"),F_mono(22),DIM,0.7*g)
        text(cv,(W//2,860),"ORIGINS",F_disp(150),BONE,g)
        text(cv,(W//2,1010),"the apparatus & the experiment, stage by stage",F_ital(44),AC,g)
        label(cv,(W//2,1360),"cellautomata · web8 · the origin-of-life lab",20,DIM,0.7*g)
        return cv
    k,t,a=seg_at(f); sid,aid,name,cap,mode,zoom=STAGES[k]; sm=smeta(sid); am=ameta(aid)
    # apparatus (top)
    cv.paste(blend_bg(app_img(aid,am,t),a),(AWX,AWY)); frame_box(d,AWX,AWY,AW,AH,a)
    # micrograph (inset, bottom)
    cv.paste(blend_bg(mic_img(sid,sm,mode,zoom,t),a),(MX,MY)); frame_box(d,MX,MY,MIC,MIC,a)
    # chrome
    text(cv,(W//2,120),roman(k+1),F_disp(64),AC,0.9*a)
    text(cv,(W//2,212),name.upper(),F_disp(56),BONE,a)
    label(cv,(W//2,272),am.get('title',aid),16,DIM,0.6*a)
    label(cv,(MX+MIC//2,MY-26),"live experiment · micrograph",14,DIM,0.55*a)
    wrapped(cv,(W//2,MY+MIC+44),cap,F_ital(38),BONE,a,W-160,48)
    progress(cv,k,len(STAGES),a if a>0 else 1)
    label(cv,(W//2,1862),"cellautomata · web8 · origins",15,DIM,0.4)
    return cv
if __name__=='__main__' and len(sys.argv)>2 and sys.argv[1]=='test':
    compose_frame(int(sys.argv[2])).convert("RGB").save('/tmp/lab_full_test.png'); print("NF",NF); sys.exit()
silent="/tmp/lab_full_silent.mp4"
wr=imageio_ffmpeg.write_frames(silent,(W,H),fps=FPS,codec="libx264",pix_fmt_in="rgb24",pix_fmt_out="yuv420p",macro_block_size=8,output_params=["-crf","19","-preset","medium"])
wr.send(None)
def emit(cv): wr.send(np.ascontiguousarray(np.asarray(cv.convert("RGB"),np.uint8)).tobytes())
for f in range(NF): emit(compose_frame(f))
wr.close(); print("composited",NF)
total=NF/FPS; out="/tmp/web8_lab_full.mp4"
fade=min(3.5,total/3); fin=min(3.0,total/3); fo=max(0.0,total-fade)
af=f"[1:a][2:a][3:a]amix=inputs=3,volume=0.12,lowpass=f=500,afade=t=in:st=0:d={fin:.2f},afade=t=out:st={fo:.2f}:d={fade:.2f}[a]"
subprocess.run([FF,"-y","-hide_banner","-loglevel","error","-i",silent,
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=52:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=78:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=156:sample_rate=44100",
 "-filter_complex",af,"-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","144k","-shortest","-movflags","+faststart",out],check=True)
print(f"-> {out}  {os.path.getsize(out)/1e6:.1f} MB  {total:.1f}s")
