"""DEEP SEARCH — the rare and the moving. A motion-weighted swarm of 16 agents combed ~1,900 points
of Gray-Scott F/k space and surfaced what the first pass missed: spiral & target waves, gliding
soliton swarms, invasion fronts, defect lattices, dendritic webs, ring cells. 512², aurora relief +
bloom, slow macro dive. Reads /tmp/ds_field.bin (gs_deepsearch_gen).
Preview: python3 gs_deepsearch_film.py test <f>   Full: python3 gs_deepsearch_film.py"""
import json, os, sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
W,H,FPS=1080,1920,24; WIN=1000; WX=(W-WIN)//2; WY=400
BG=(6,5,12); BONE=(238,232,222); DIM=(150,140,160); AC=(250,200,120)
FB="docs/web8/assets/fonts/"
def fnt(n,s): p=FB+n; return ImageFont.truetype(p,s) if os.path.exists(p) else ImageFont.load_default()
F_disp=lambda s: fnt("Italiana-Regular.ttf",s)
F_mono=lambda s: fnt("IBMPlexMono-Regular.ttf",s)
F_ital=lambda s: fnt("CrimsonPro-Italic.ttf",s)
def text(cv,xy,s,f,fill,a=1.0,anc="mm",spc=8):
    if a<=0.01: return
    ov=Image.new("RGBA",cv.size,(0,0,0,0)); ImageDraw.Draw(ov).multiline_text(xy,s,font=f,fill=(*fill,int(255*min(1,a))),anchor=anc,align="center",spacing=spc); cv.alpha_composite(ov)
def tlen(s,f): return ImageDraw.Draw(Image.new("RGB",(4,4))).textlength(s,font=f)
def label(cv,xy,s,size,fill,a=1.0,anc="mm",maxw=W-90):
    s=s.upper()
    for gap in ("  "," ",""):
        for sz in range(size,max(9,size-5),-1):
            t=gap.join(list(s))
            if tlen(t,F_mono(sz))<=maxw: text(cv,xy,t,F_mono(sz),fill,a,anc); return
    text(cv,xy,s,F_mono(max(9,size-5)),fill,a,anc)
def wrapped(cv,xy,s,f,fill,a,maxw,lh):
    if a<=0.01: return
    words=s.split(); lines=[]; cur=""
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
M=json.load(open('/tmp/ds_meta.json')); R=M['R']; MF=M['M']; PAT=M['patterns']; NP=len(PAT)
SZ=R*R*2
def readfield(idx,lf):
    g=idx*MF+min(MF-1,max(0,lf)); f=open('/tmp/ds_field.bin','rb'); f.seek(g*SZ)
    a=np.frombuffer(f.read(SZ),np.uint16).reshape(R,R).astype(np.float32)/65535.0; f.close(); return a
def make_lut(stops):
    xs=np.linspace(0,1,len(stops)); out=np.zeros((256,3),np.float32); t=np.linspace(0,1,256)
    for c in range(3): out[:,c]=np.interp(t,xs,[s[c] for s in stops])
    return out
LUT=make_lut([(6,5,20),(28,12,60),(74,18,104),(150,30,120),(214,64,84),(244,130,58),(250,200,108),(252,242,212)])
def relief(h01):
    gy,gx=np.gradient(h01); lx,ly,lz=-0.5,-0.55,0.66; nz=1/3.4
    inv=1.0/np.sqrt(gx*gx+gy*gy+nz*nz); shade=np.clip((gx*lx+gy*ly+nz*lz)*inv,0,1)
    hs=np.clip(h01/0.40,0,1); idx=np.clip(hs*255,0,255).astype(np.int32); base=LUT[idx]
    col=base*(0.36+0.78*shade)[...,None]
    spec=np.clip(shade-0.82,0,1)*5.0*np.clip(hs-0.25,0,1)
    col+=spec[...,None]*np.array([255,240,210],np.float32)
    return col
def vig(n):
    yy,xx=np.mgrid[0:n,0:n]; r=np.hypot((xx-n/2)/(n/2),(yy-n/2)/(n/2))
    return np.clip(1-0.5*np.clip(r-0.5,0,1)**1.8,0,1).astype(np.float32)[...,None]
VIG=vig(WIN)
def ease(z): z=min(1,max(0,z)); return z*z*(3-2*z)
def window(idx,lf,t):
    a=readfield(idx,lf)
    z=ease(t); cs=R*(0.52-0.22*z); cs=max(48.0,min(float(R),cs))        # float crop size — no integer stepping
    cxp=0.5+0.10*np.sin(t*np.pi-0.6); x0=(R-cs)*float(np.clip(cxp,0,1)); y0=(R-cs)*0.5
    x0=max(0.0,min(R-cs,x0)); y0=max(0.0,min(R-cs,y0))
    # sub-pixel crop+zoom in one LANCZOS pass via a float box → glass-smooth camera (no jitter)
    h01=np.asarray(Image.fromarray(a,mode='F').resize((WIN,WIN),Image.LANCZOS,box=(x0,y0,x0+cs,y0+cs)),np.float32)
    col=relief(h01)
    bp=np.clip(col-165,0,255).astype(np.uint8)
    blur=np.asarray(Image.fromarray(bp).filter(ImageFilter.GaussianBlur(9)),np.float32)
    col=np.clip(col+0.55*blur,0,255)*VIG
    return np.clip(col,0,255).astype(np.uint8)
def reticle(d,x,y,n,a=1.0):
    for cx,cy in[(x,y),(x+n,y),(x,y+n),(x+n,y+n)]:
        d.line([(cx-22,cy),(cx+22,cy)],fill=(*AC,int(150*a)),width=1); d.line([(cx,cy-22),(cx,cy+22)],fill=(*AC,int(150*a)),width=1)
    d.rectangle([x-1,y-1,x+n,y+n],outline=(*AC,int(55*a)),width=1)
TITLE=110; SEG=MF; CODA=126; FADE=18
NF=TITLE+SEG*NP+CODA
def loc(f):
    if f<TITLE: return ('title',0,f)
    if f>=TITLE+SEG*NP: return ('coda',0,f-(TITLE+SEG*NP))
    k=(f-TITLE)//SEG; return ('plate',min(k,NP-1),(f-TITLE)-k*SEG)
def compose(f):
    kind,k,lf=loc(f); cv=Image.new("RGBA",(W,H),(*BG,255)); d=ImageDraw.Draw(cv)
    if kind=='title':
        g=min(1,lf/20)*min(1,(TITLE-1-lf)/16)
        label(cv,(W//2,560),"a swarm searched the F/k plane",22,AC,0.7*g)
        text(cv,(W//2,840),"DEEP SEARCH",F_disp(128),BONE,g)
        text(cv,(W//2,990),"the rarest, most restless patterns it found",F_ital(42),AC,g)
        label(cv,(W//2,1330),"16 agents · ~1,900 points · motion-weighted",19,DIM,0.7*g)
        return cv
    if kind=='coda':
        g=min(1,lf/20)*min(1,(CODA-1-lf)/16)
        label(cv,(W//2,560),"spirals & waves hide in two numbers",20,AC,0.65*g)
        text(cv,(W//2,820),"keep looking,",F_disp(60),BONE,g)
        text(cv,(W//2,910),"it keeps giving",F_disp(60),AC,g)
        label(cv,(W//2,1300),"cellautomata · deep search",17,DIM,0.55*g)
        return cv
    p=PAT[k]; t=lf/SEG; a=min(1,lf/FADE)*min(1,(SEG-1-lf)/FADE)
    img=window(k,lf,t); win=Image.fromarray(img)
    if a<1: win=Image.blend(Image.new("RGB",(WIN,WIN),BG),win,a)
    cv.paste(win,(WX,WY)); reticle(d,WX,WY,WIN,a)
    text(cv,(W//2,150),roman(k+1),F_disp(72),AC,0.9*a)
    text(cv,(W//2,250),p['name'].upper(),F_disp(58),BONE,a)
    label(cv,(W//2,322),f"F {p['F']:.4f}   ·   k {p['k']:.4f}",18,AC,0.7*a)
    wrapped(cv,(W//2,WY+WIN+64),p['cap'],F_ital(38),BONE,a,W-150,50)
    for j in range(NP):
        x=W//2-(NP-1)*18+j*36; r=5 if j==k else 3; fill=AC if j==k else DIM
        d.ellipse([x-r,1858-r,x+r,1858+r],fill=(*fill,255 if j==k else 110))
    label(cv,(W//2,1900),"cellautomata · deep search",14,DIM,0.4)
    return cv
if __name__=='__main__' and len(sys.argv)>2 and sys.argv[1]=='test':
    compose(int(sys.argv[2])).convert("RGB").save('/tmp/ds_test.png'); print("NF",NF,"patterns",NP); sys.exit()
silent="/tmp/ds_silent.mp4"
wr=imageio_ffmpeg.write_frames(silent,(W,H),fps=FPS,codec="libx264",pix_fmt_in="rgb24",pix_fmt_out="yuv420p",macro_block_size=8,output_params=["-crf","18","-preset","medium"])
wr.send(None)
for f in range(NF): wr.send(np.ascontiguousarray(np.asarray(compose(f).convert("RGB"),np.uint8)).tobytes())
wr.close(); print("composited",NF)
total=NF/FPS; out="/tmp/web8_deepsearch.mp4"
fade=min(3.5,total/3); fin=min(3.0,total/3); fo=max(0.0,total-fade)
af=f"[1:a][2:a][3:a]amix=inputs=3,volume=0.11,lowpass=f=560,afade=t=in:st=0:d={fin:.2f},afade=t=out:st={fo:.2f}:d={fade:.2f}[a]"
subprocess.run([FF,"-y","-hide_banner","-loglevel","error","-i",silent,
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=49:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=73.5:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=98:sample_rate=44100",
 "-filter_complex",af,"-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","144k","-shortest","-movflags","+faststart",out],check=True)
print(f"-> {out}  {os.path.getsize(out)/1e6:.1f} MB  {total:.1f}s")
