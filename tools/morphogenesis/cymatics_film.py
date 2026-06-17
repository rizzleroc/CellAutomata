"""CYMATICS — sound made visible. A driven square Chladni plate: at each drive frequency the standing-wave
displacement u(x,y)=Σ A_mn(F)·sin(mπx)sin(nπy) leaves "sand" on the nodes (|u|≈0). Sweeping F morphs the
figure through the classic sequence. An 8-agent swarm searched driver position / damping / frequency for the
most striking sweeps; this reel plays eight of them frame-by-frame as the drive climbs. Reads /tmp/g_cym*_n.bin.
Preview: python3 cymatics_film.py test <globalframe>   Full: python3 cymatics_film.py"""
import json, os, sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
W,H,FPS=1080,1920,24; WIN=1000; WX=(W-WIN)//2; WY=400
BG=(6,7,11); BONE=(234,228,214); DIM=(132,140,156); AC=(168,198,226)   # cool steel-blue instrument accent vs warm sand
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
def vig(n):   # gentle — the plate's clamped edge is itself a bright nodal border, don't crush it
    yy,xx=np.mgrid[0:n,0:n]; r=np.hypot((xx-n/2)/(n/2),(yy-n/2)/(n/2))
    return np.clip(1-0.28*np.clip(r-0.66,0,1)**1.8,0,1).astype(np.float32)[...,None]
VIG=vig(WIN)
# the swarm's eight best frequency sweeps (tag, name, f0, f1, what the sweep morphs through)
ANIMS=[
 ("cymsharp","Pure Eigenmodes",3.16,5.0,"low damping holds each mode pure — a ring, a grid and a four-point star surface as the drive climbs"),
 ("cymctr","Quatrefoil to Sunburst",4.6,7.6,"a centred drive blooms from a four-lobed quatrefoil through a square star into a radiating sunburst rosette"),
 ("cymblend","Woven Standing Waves",8.0,16.0,"heavy damping blends neighbouring modes — nodal lines interlace into a woven eye and a basketwork target"),
 ("cymoff","Off-Axis Drive",6.0,16.0,"shifting the driver off-centre breaks the symmetry: concentric webs collapse into a leopard-spot bullseye"),
 ("cymedge","Edge-Driven Fan",5.0,14.0,"driving near one edge rakes the figure aside — a fan-eye opens into a peacock bullseye"),
 ("cymquarter","Corner Whirl",8.0,22.0,"a corner drive winds the field — a whirl-eye spins out into a dense woven lattice as the pitch rises"),
 ("cymhi","Lacework Rosettes",16.5,18.6,"at high frequency dozens of modes overlap into intricate lacework rosettes, fine as frost"),
 ("cymasym","Spiral Mandala",16.0,23.0,"an asymmetric high-frequency drive coils the nodes into a spiral fingerprint, then a crystalline mandala mesh"),
]
_M={}
def meta(tag):
    if tag not in _M: _M[tag]=json.load(open(f'/tmp/g_{tag}_meta.json'))
    return _M[tag]
def frame(tag,f):
    m=meta(tag); W0,H0=m['W'],m['H']; fb=W0*H0*4; fr=max(0,min(m['frames']-1,int(f)))
    fp=open(f'/tmp/g_{tag}_n.bin','rb'); fp.seek(fr*fb)
    a=np.frombuffer(fp.read(fb),np.uint8).reshape(H0,W0,4)[:,:,:3].astype(np.float32); fp.close(); return a
def window(tag,f):
    a=frame(tag,f)                                                       # LUT already maps to full range, no norm needed
    im=np.asarray(Image.fromarray(a.astype(np.uint8)).resize((WIN,WIN),Image.BICUBIC),np.float32)  # smooth field -> bicubic
    return np.clip(im*VIG,0,255).astype(np.uint8)
def reticle(d,x,y,n,a=1.0):
    for cx,cy in[(x,y),(x+n,y),(x,y+n),(x+n,y+n)]:
        d.line([(cx-22,cy),(cx+22,cy)],fill=(*AC,int(150*a)),width=1); d.line([(cx,cy-22),(cx,cy+22)],fill=(*AC,int(150*a)),width=1)
    d.rectangle([x-1,y-1,x+n,y+n],outline=(*AC,int(55*a)),width=1)
TITLE=100; CODA=110; FADE=12
SEGS=[meta(t)['frames'] for t,_,_,_,_ in ANIMS]
NF=TITLE+sum(SEGS)+CODA
def loc(f):
    if f<TITLE: return ('title',0,f)
    g=f-TITLE
    for k,L in enumerate(SEGS):
        if g<L: return ('plate',k,g)
        g-=L
    return ('coda',0,g)
def compose(f):
    kind,k,lf=loc(f); cv=Image.new("RGBA",(W,H),(*BG,255)); d=ImageDraw.Draw(cv)
    if kind=='title':
        g=min(1,lf/18)*min(1,(TITLE-1-lf)/16)
        label(cv,(W//2,560),"sound made visible · a driven chladni plate",21,AC,0.7*g)
        text(cv,(W//2,840),"CYMATICS",F_disp(132),BONE,g)
        text(cv,(W//2,1000),"standing waves draw figures in sand",F_ital(46),AC,g)
        label(cv,(W//2,1340),"eight resonance sweeps · found by an 8-agent swarm",19,DIM,0.7*g)
        return cv
    if kind=='coda':
        g=min(1,lf/18)*min(1,(CODA-1-lf)/16)
        label(cv,(W//2,600),"raise the pitch, redraw the figure",20,AC,0.65*g)
        text(cv,(W//2,860),"form is frozen frequency",F_disp(60),BONE,g)
        label(cv,(W//2,1320),"cellautomata · cymatics",17,DIM,0.5*g)
        return cv
    tag,name,f0,f1,cap=ANIMS[k]; L=SEGS[k]; a=min(1,lf/FADE)*min(1,(L-1-lf)/FADE)
    img=window(tag,lf); win=Image.fromarray(img)
    if a<1: win=Image.blend(Image.new("RGB",(WIN,WIN),BG),win,a)
    cv.paste(win,(WX,WY)); reticle(d,WX,WY,WIN,a)
    text(cv,(W//2,150),roman(k+1),F_disp(70),AC,0.9*a)
    text(cv,(W//2,246),name.upper(),F_disp(58),BONE,a)
    fnow=f0+(f1-f0)*(lf/max(1,L-1))                                       # live drive-frequency readout, ticking up
    text(cv,(W//2,312),f"DRIVE  {fnow:5.2f}      SWEEP  {f0:.2f} – {f1:.2f}",F_mono(21),AC,0.92*a)
    # frequency scrubber under the plate — fills as the sweep climbs
    sx0,sy,prog=WX,1432,lf/max(1,L-1); mxp=sx0+int(WIN*prog)
    d.line([(sx0,sy),(sx0+WIN,sy)],fill=(*DIM,int(55*a)),width=1)
    d.line([(sx0,sy),(mxp,sy)],fill=(*AC,int(150*a)),width=2)
    d.polygon([(mxp-5,sy-8),(mxp+5,sy-8),(mxp,sy-1)],fill=(*AC,int(205*a)))
    wrapped(cv,(W//2,1486),cap,F_ital(38),BONE,a,W-150,50)
    for j in range(len(ANIMS)):
        x=W//2-(len(ANIMS)-1)*18+j*36; r=5 if j==k else 3; fill=AC if j==k else DIM
        d.ellipse([x-r,1858-r,x+r,1858+r],fill=(*fill,255 if j==k else 110))
    label(cv,(W//2,1900),"cellautomata · cymatics",14,DIM,0.4)
    return cv
if __name__=='__main__' and len(sys.argv)>2 and sys.argv[1]=='test':
    compose(int(sys.argv[2])).convert("RGB").save('/tmp/cym_film_test.png'); print("NF",NF,"segs",SEGS); sys.exit()
silent="/tmp/cym_silent.mp4"
wr=imageio_ffmpeg.write_frames(silent,(W,H),fps=FPS,codec="libx264",pix_fmt_in="rgb24",pix_fmt_out="yuv420p",macro_block_size=8,output_params=["-crf","19","-preset","medium"])
wr.send(None)
for f in range(NF): wr.send(np.ascontiguousarray(np.asarray(compose(f).convert("RGB"),np.uint8)).tobytes())
wr.close(); print("composited",NF)
total=NF/FPS; out="/tmp/web8_cymatics.mp4"
fade=min(3.5,total/3); fin=min(3.0,total/3); fo=max(0.0,total-fade)
af=f"[1:a][2:a][3:a]amix=inputs=3,volume=0.10,lowpass=f=540,afade=t=in:st=0:d={fin:.2f},afade=t=out:st={fo:.2f}:d={fade:.2f}[a]"
subprocess.run([FF,"-y","-hide_banner","-loglevel","error","-i",silent,
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=58:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=87:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=116:sample_rate=44100",
 "-filter_complex",af,"-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","144k","-shortest","-movflags","+faststart",out],check=True)
print(f"-> {out}  {os.path.getsize(out)/1e6:.1f} MB  {total:.1f}s")
