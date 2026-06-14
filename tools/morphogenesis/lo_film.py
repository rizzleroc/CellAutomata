import json, os, sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
W,H=1080,1920; FPS=24; WIN=1000; WX=(W-WIN)//2; WY=380
BG=(7,8,12); BONE=(232,226,212); DIM=(140,146,158)
FB="docs/web8/assets/fonts/"
def fnt(n,s):
    p=FB+n; return ImageFont.truetype(p,s) if os.path.exists(p) else ImageFont.load_default()
F_disp=lambda s: fnt("Italiana-Regular.ttf",s)
F_mono=lambda s: fnt("IBMPlexMono-Regular.ttf",s)
F_monob=lambda s: fnt("IBMPlexMono-Bold.ttf",s)
def sp(s): return "  ".join(s.upper())
def text(cv,xy,s,f,fill,a=1.0,anc="mm",spc=8):
    if a<=0.01: return
    ov=Image.new("RGBA",cv.size,(0,0,0,0))
    ImageDraw.Draw(ov).multiline_text(xy,s,font=f,fill=(*fill,int(255*min(1,a))),anchor=anc,align="center",spacing=spc)
    cv.alpha_composite(ov)
def wrap(d,s,f,mw):
    o=[];c=""
    for w in s.split():
        t=(c+" "+w).strip()
        if d.textlength(t,font=f)<=mw: c=t
        else: o.append(c);c=w
    if c:o.append(c)
    return o
SZF=1000*1000*2
def readfield(idx,GW=1000,GH=1000):
    f=open('/tmp/lo_field.bin','rb'); f.seek(idx*SZF)
    a=np.frombuffer(f.read(SZF),np.uint16).reshape(GH,GW).astype(np.float32)/65535.0; f.close(); return a
# ---- palettes (warm-bone, cool-jade, violet-ash) as 256 LUTs ----
def make_lut(stops):
    xs=np.linspace(0,1,len(stops)); out=np.zeros((256,3),np.float32); t=np.linspace(0,1,256)
    for c in range(3): out[:,c]=np.interp(t,xs,[s[c] for s in stops])
    return out
LUT_WARM=make_lut([(26,18,13),(86,56,34),(160,112,68),(214,172,114),(242,230,200),(253,247,230)])
LUT_JADE=make_lut([(16,26,24),(34,78,70),(58,134,116),(120,196,166),(206,234,214),(238,250,240)])
LUT_VIOL=make_lut([(22,16,30),(64,44,92),(118,84,150),(176,138,198),(220,202,234),(246,238,251)])
PALS=[LUT_WARM,LUT_JADE,LUT_VIOL]
def palette_at(p):  # p in 0..1 across runtime -> blend palettes (warm->jade->violet->jade->warm)
    seq=[0,1,2,1,0]; x=p*(len(seq)-1); i=min(len(seq)-2,int(x)); t=x-i
    return PALS[seq[i]]*(1-t)+PALS[seq[i+1]]*t
def relief(h01, lut, strength=3.4):
    gy,gx=np.gradient(h01)
    lx,ly,lz=-0.52,-0.58,0.63
    nz=1.0/strength
    inv=1.0/np.sqrt(gx*gx+gy*gy+nz*nz)
    shade=np.clip((gx*lx+gy*ly+nz*lz)*inv,0,1)
    idx=np.clip((h01*255),0,255).astype(np.int32)
    base=lut[idx]                                  # HxWx3
    col=base*(0.48+0.66*shade)[...,None]
    spec=np.clip(shade-0.82,0,1)*5.0*np.clip(h01-0.25,0,1)
    col+=spec[...,None]*np.array([255,250,235],np.float32)
    return np.clip(col,0,255).astype(np.uint8)
def vig(n):
    yy,xx=np.mgrid[0:n,0:n]; r=np.hypot((xx-n/2)/(n/2),(yy-n/2)/(n/2))
    return np.clip(1-0.42*np.clip(r-0.58,0,1)**1.7,0,1).astype(np.float32)[...,None]
VIG=vig(WIN)
def smooth(t): return t*t*(3-2*t)
def lerp(a,b,t): return a+(b-a)*t
def cropresize(field,cs,ccx,ccy):
    cs=int(round(max(150,min(1000,cs)))); x=int(round(ccx-cs/2)); y=int(round(ccy-cs/2))
    x=max(0,min(1000-cs,x)); y=max(0,min(1000-cs,y))
    sub=field[y:y+cs,x:x+cs]
    im=Image.fromarray(sub,mode='F').resize((WIN,WIN),Image.LANCZOS)
    return np.asarray(im,np.float32)
def camera(f,NF):
    p=f/NF
    cs=lerp(800,430,0.5-0.5*np.cos(p*np.pi*7))           # smooth breathing zoom (wide <-> detail)
    ccx=500+300*np.sin(p*np.pi*2.0)
    ccy=500+300*np.cos(p*np.pi*1.6)
    ccx=np.clip(ccx,cs/2,1000-cs/2); ccy=np.clip(ccy,cs/2,1000-cs/2)
    return cs,ccx,ccy
def render_window(f,NF,strength=3.4):
    field=readfield(f); cs,ccx,ccy=camera(f,NF)
    h01=cropresize(field,cs,ccx,ccy)
    img=relief(h01,palette_at(f/NF),strength).astype(np.float32)*VIG
    return np.clip(img,0,255).astype(np.uint8), cs
# ---- phase-diagram inset ----
def pmap(cv,cx,cy,size,WP,fk,f,AC):
    d=ImageDraw.Draw(cv); Fmin,Fmax=0.020,0.064; kmin,kmax=0.049,0.0665
    x0,y0=cx-size/2,cy-size/2
    def XY(F,k): return (x0+(F-Fmin)/(Fmax-Fmin)*size, y0+size-(k-kmin)/(kmax-kmin)*size)
    d.rectangle([x0,y0,x0+size,y0+size],outline=(*DIM,110),width=1)
    text(cv,(cx,y0-16),sp("f – k  phase map"),F_mono(15),DIM,0.6)
    pts=[XY(w[1],w[2]) for w in WP]
    d.line(pts,fill=(*BONE,60),width=1)
    for w in WP:
        px,py=XY(w[1],w[2]); d.ellipse([px-2,py-2,px+2,py+2],fill=(*BONE,90))
    tr=max(0,f-220)
    trail=[XY(fk[i][0],fk[i][1]) for i in range(tr,f+1,4)]
    if len(trail)>1: d.line(trail,fill=(*AC,150),width=2)
    px,py=XY(fk[f][0],fk[f][1]); d.ellipse([px-9,py-9,px+9,py+9],outline=AC,width=2); d.ellipse([px-4,py-4,px+4,py+4],fill=AC)
def reticle(d,x,y,n,AC,a=1.0):
    for cx,cy in[(x,y),(x+n,y),(x,y+n),(x+n,y+n)]:
        d.line([(cx-22,cy),(cx+22,cy)],fill=(*AC,int(150*a)),width=1); d.line([(cx,cy-22),(cx,cy+22)],fill=(*AC,int(150*a)),width=1)
    d.rectangle([x-1,y-1,x+n,y+n],outline=(*AC,int(70*a)),width=1)
ACC=[(228,180,120),(120,206,170),(176,150,224)]
def accent_at(p):
    seq=[0,1,2,1,0]; x=p*(len(seq)-1); i=min(len(seq)-2,int(x)); t=x-i
    a=np.array(ACC[seq[i]]); b=np.array(ACC[seq[i+1]]); return tuple((a*(1-t)+b*t).astype(int))
if __name__=='__main__' and len(sys.argv)>2 and sys.argv[1]=='test':
    img,cs=render_window(int(sys.argv[2]),2880); Image.fromarray(img).save('/tmp/lo_test.png'); print("test frame saved",cs); sys.exit()
# ===== FULL RENDER =====
M=json.load(open('/tmp/lo_meta.json')); NF=M['NF']; WP=M['WP']; FK=M['fk']; NAMES=M['names']; POP=M['pop']
silent="/tmp/lo_silent.mp4"
wr=imageio_ffmpeg.write_frames(silent,(W,H),fps=FPS,codec="libx264",pix_fmt_in="rgb24",pix_fmt_out="yuv420p",macro_block_size=8,output_params=["-crf","20","-preset","medium"])
wr.send(None)
def emit(cv): wr.send(np.ascontiguousarray(np.asarray(cv.convert("RGB"),np.uint8)).tobytes())
NTITLE=84; prevname=None
for f in range(NF):
    p=f/NF; AC=accent_at(p)
    img,cs=render_window(f,NF)
    cv=Image.new("RGBA",(W,H),(*BG,255)); cv.paste(Image.fromarray(img),(WX,WY))
    d=ImageDraw.Draw(cv); reticle(d,WX,WY,WIN,AC,1.0)
    if f<NTITLE:
        g=min(1,f/16)*min(1,(NTITLE-1-f)/16); ov=Image.new("RGBA",(W,H),(0,0,0,int(150*g))); cv.alpha_composite(ov)
        text(cv,(W//2,150),sp("the annals of catalytic silence"),F_mono(22),DIM,0.6*g)
        text(cv,(W//2,560),"MORPHOGENESIS",F_disp(104),BONE,g)
        text(cv,(W//2,680),"one field · a long drift through every form",F_disp(44),AC,g)
        text(cv,(W//2,1240),sp("gray–scott · feed & kill drifting across the phase map"),F_mono(20),DIM,0.7*g)
    else:
        text(cv,(W//2,150),"▶  "+sp("live"),F_monob(26),AC,0.7)
        nm=NAMES[f]; text(cv,(W//2,250),nm.upper(),F_disp(70),BONE,1.0)
        # chapter flash on regime change
        if nm!=prevname: prevname=nm
        text(cv,(W//2,320),sp("morphology"),F_mono(18),DIM,0.5)
        sx=WX+8; sy=WY+WIN+40
        d.line([(sx,sy),(sx+140,sy)],fill=(*BONE,200),width=2)
        for xx in (sx,sx+140): d.line([(xx,sy-6),(xx,sy+6)],fill=(*BONE,200),width=2)
        text(cv,(sx+70,sy+24),f"{int(150/WIN*cs)} cells",F_mono(20),DIM,0.8)
        text(cv,(WX+WIN-8,sy+12),sp(f"F {FK[f][0]:.4f} · k {FK[f][1]:.4f}"),F_mono(19),AC,0.85,anc="rm")
        text(cv,(WX+WIN-8,sy+42),sp(f"generation {f*10:,}"),F_mono(17),DIM,0.6,anc="rm")
        pmap(cv,176,1530,150,WP,FK,f,AC)
        text(cv,(W//2,1880),sp("cellautomata · web8 · one continuous field"),F_mono(17),DIM,0.45)
    emit(cv)
wr.close(); print("composited")
total=NF/FPS; out="/tmp/web8_morphogenesis.mp4"
af=f"[1:a][2:a][3:a]amix=inputs=3,volume=0.12,lowpass=f=500,afade=t=in:st=0:d=3,afade=t=out:st={total-3.5:.1f}:d=3.5[a]"
subprocess.run([FF,"-y","-hide_banner","-loglevel","error","-i",silent,
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=52:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=78:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=156:sample_rate=44100",
 "-filter_complex",af,"-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","144k","-shortest","-movflags","+faststart",out],check=True)
print(f"-> {out}  {os.path.getsize(out)/1e6:.1f} MB  {total:.1f}s")
