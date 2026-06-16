"""ARGENTUM — scanning-electron-micrograph plate. Pure false-grey relief, sensor grain,
stepped magnification with dwell, instrument HUD. The only colourless reel.
Smoke test:  python3 argentum_film.py test 24      Full render:  python3 argentum_film.py"""
import json, os, sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
W,H=1080,1920; FPS=24; WIN=1000; WX=(W-WIN)//2; WY=380
BG=(6,6,8); BONE=(232,233,236); DIM=(126,130,138)
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
def label(cv,xy,s,size,fill,a=1.0,anc="mm",maxw=W-90):
    # letter-spaced mono that always fits the frame: relax spacing then shrink before it can clip
    s=s.upper()
    for gap in ("  "," ",""):
        for sz in range(size,size-4,-1):
            t=gap.join(s)
            if ImageDraw.Draw(cv).textlength(t,font=F_mono(sz))<=maxw:
                text(cv,xy,t,F_mono(sz),fill,a,anc); return
    text(cv,xy," ".join(s),F_mono(size-3),fill,a,anc)
SZF=1000*1000*2
def readfield(idx):
    f=open('/tmp/argentum_field.bin','rb'); f.seek(idx*SZF)
    a=np.frombuffer(f.read(SZF),np.uint16).reshape(1000,1000).astype(np.float32)/65535.0; f.close(); return a
# ---- false-grey LUTs: a whisper of cool / warm so the plate drifts without ever being "coloured"
def make_lut(stops):
    xs=np.linspace(0,1,len(stops)); out=np.zeros((256,3),np.float32); t=np.linspace(0,1,256)
    for c in range(3): out[:,c]=np.interp(t,xs,[s[c] for s in stops])
    return out
LUT_COOL=make_lut([(7,8,11),(34,37,42),(86,90,96),(140,144,150),(196,199,204),(232,234,238),(250,251,253)])
LUT_WARM=make_lut([(11,9,7),(42,38,33),(96,90,82),(150,144,134),(204,199,190),(236,234,228),(252,251,246)])
PALS=[LUT_COOL,LUT_WARM]
def palette_at(p):  # cool -> warm -> cool, almost imperceptible
    seq=[0,1,0]; x=p*(len(seq)-1); i=min(len(seq)-2,int(x)); t=x-i
    return PALS[seq[i]]*(1-t)+PALS[seq[i+1]]*t
def relief(h01, lut, strength=4.6):
    gy,gx=np.gradient(h01)
    lx,ly,lz=-0.62,-0.46,0.64                      # hard raking light = crisp SEM topography
    nz=1.0/strength
    inv=1.0/np.sqrt(gx*gx+gy*gy+nz*nz)
    shade=np.clip((gx*lx+gy*ly+nz*lz)*inv,0,1)
    idx=np.clip((h01*255),0,255).astype(np.int32)
    base=lut[idx]
    col=base*(0.30+0.80*shade)[...,None]
    spec=np.clip(shade-0.86,0,1)*8.0*np.clip(h01-0.30,0,1)
    col+=spec[...,None]*np.array([250,250,252],np.float32)
    return np.clip(col,0,255).astype(np.uint8)
def vig(n):
    yy,xx=np.mgrid[0:n,0:n]; r=np.hypot((xx-n/2)/(n/2),(yy-n/2)/(n/2))
    return np.clip(1-0.46*np.clip(r-0.56,0,1)**1.7,0,1).astype(np.float32)[...,None]
VIG=vig(WIN)
def smooth5(t): t=min(1,max(0,t)); return t*t*t*(t*(t*6-15)+10)
def lerp(a,b,t): return a+(b-a)*t
def cropresize(field,cs,ccx,ccy):
    cs=int(round(max(150,min(1000,cs)))); x=int(round(ccx-cs/2)); y=int(round(ccy-cs/2))
    x=max(0,min(1000-cs,x)); y=max(0,min(1000-cs,y))
    sub=field[y:y+cs,x:x+cs]
    im=Image.fromarray(sub,mode='F').resize((WIN,WIN),Image.LANCZOS)
    return np.asarray(im,np.float32)
# Stepped magnification: the operator turns the mag dial, dwells, turns again.
ZK=[(0.00,920),(0.16,560),(0.30,560),(0.46,360),(0.60,360),(0.76,235),(0.88,235),(1.00,178)]
def stepzoom(p):
    for i in range(len(ZK)-1):
        p0,c0=ZK[i]; p1,c1=ZK[i+1]
        if p<=p1: return lerp(c0,c1,smooth5(0 if p1==p0 else (p-p0)/(p1-p0)))
    return ZK[-1][1]
def camera(f,NF):
    p=f/NF; cs=stepzoom(p)
    margin=(1000-cs)/2*0.82; prog=smooth5(p)
    ccx=lerp(500,548,prog)+margin*0.18*np.sin(p*np.pi*1.3)
    ccy=lerp(500,462,prog)+margin*0.18*np.cos(p*np.pi*1.1)
    return cs,ccx,ccy
def render_window(f,NF):
    field=readfield(f); cs,ccx,ccy=camera(f,NF)
    h01=cropresize(field,cs,ccx,ccy)
    img=relief(h01,palette_at(f/NF)).astype(np.float32)*VIG
    img=img+np.random.normal(0,2.2,img.shape)      # faint detector grain — the SEM tell
    return np.clip(img,0,255).astype(np.uint8), cs
def reticle(d,x,y,n,a=1.0):                          # plain instrument frame, no colour
    d.rectangle([x-1,y-1,x+n,y+n],outline=(*DIM,int(90*a)),width=1)
    for cx,cy in[(x,y),(x+n,y),(x,y+n),(x+n,y+n)]:
        d.line([(cx-20,cy),(cx+20,cy)],fill=(*BONE,int(150*a)),width=1)
        d.line([(cx,cy-20),(cx,cy+20)],fill=(*BONE,int(150*a)),width=1)
def mag(cs): return int(round(700000/cs/50)*50)      # plausible SEM magnification readout
NTITLE=84
def compose_frame(f,NF,NAMES,FK):
    img,cs=render_window(f,NF)
    cv=Image.new("RGBA",(W,H),(*BG,255)); cv.paste(Image.fromarray(img),(WX,WY))
    d=ImageDraw.Draw(cv); reticle(d,WX,WY,WIN,1.0)
    if f<NTITLE:
        g=min(1,f/16)*min(1,(NTITLE-1-f)/16); ov=Image.new("RGBA",(W,H),(0,0,0,int(150*g))); cv.alpha_composite(ov)
        text(cv,(W//2,150),sp("scanning electron micrograph"),F_mono(22),DIM,0.6*g)
        text(cv,(W//2,560),"ARGENTUM",F_disp(110),BONE,g)
        text(cv,(W//2,690),"a specimen, magnified",F_disp(44),BONE,0.85*g)
        label(cv,(W//2,1240),"gray–scott · false-grey relief · no colour added",20,DIM,0.7*g)
    else:
        nm=NAMES[f]
        text(cv,(W//2,150),sp("electron micrograph"),F_mono(20),DIM,0.55)
        text(cv,(W//2,250),nm.upper(),F_disp(70),BONE,1.0)
        text(cv,(W//2,320),sp("specimen field"),F_mono(18),DIM,0.5)
        # µm scalebar (1 cell = 0.2 µm); bar 150 px wide
        sx=WX+8; sy=WY+WIN+40; bar_um=0.03*cs
        d.line([(sx,sy),(sx+150,sy)],fill=(*BONE,210),width=3)
        for xx in (sx,sx+150): d.line([(xx,sy-7),(xx,sy+7)],fill=(*BONE,210),width=3)
        text(cv,(sx+75,sy+26),f"{bar_um:.1f} µm" if bar_um<10 else f"{bar_um:.0f} µm",F_mono(20),BONE,0.85)
        text(cv,(WX+WIN-8,sy+12),sp(f"mag  × {mag(cs):,}"),F_monob(20),BONE,0.9,anc="rm")
        text(cv,(WX+WIN-8,sy+44),sp(f"gen {f*10:,}"),F_mono(17),DIM,0.6,anc="rm")
        # SEM instrument banner along the very bottom
        label(cv,(W//2,1872),"HV 15.0 kV · WD 9.4 mm · spot 3.0 · det ETD-SE · cellautomata web8",17,DIM,0.5)
    return cv
if __name__=='__main__' and len(sys.argv)>2 and sys.argv[1]=='test':
    M=json.load(open('/tmp/argentum_meta.json')); img,cs=render_window(int(sys.argv[2]),M['NF'])
    Image.fromarray(img).save('/tmp/argentum_test.png'); print("test frame saved cs",cs); sys.exit()
if __name__=='__main__' and len(sys.argv)>2 and sys.argv[1]=='testc':
    M=json.load(open('/tmp/argentum_meta.json'))
    compose_frame(int(sys.argv[2]),M['NF'],M['names'],M['fk']).convert("RGB").save('/tmp/argentum_testc.png'); print("chrome frame saved"); sys.exit()
# ===== FULL RENDER =====
M=json.load(open('/tmp/argentum_meta.json')); NF=M['NF']; FK=M['fk']; NAMES=M['names']
silent="/tmp/argentum_silent.mp4"
wr=imageio_ffmpeg.write_frames(silent,(W,H),fps=FPS,codec="libx264",pix_fmt_in="rgb24",pix_fmt_out="yuv420p",macro_block_size=8,output_params=["-crf","20","-preset","medium"])
wr.send(None)
def emit(cv): wr.send(np.ascontiguousarray(np.asarray(cv.convert("RGB"),np.uint8)).tobytes())
for f in range(NF):
    emit(compose_frame(f,NF,NAMES,FK))
wr.close(); print("composited")
total=NF/FPS; out="/tmp/web8_argentum.mp4"
# Lab-equipment hum: 50 / 100 / 150 Hz harmonic stack, lowpassed — the column's quiet drone.
fade=min(3.5,total/3); fin=min(3.0,total/3); fo=max(0.0,total-fade)
af=f"[1:a][2:a][3:a]amix=inputs=3,volume=0.10,lowpass=f=600,afade=t=in:st=0:d={fin:.2f},afade=t=out:st={fo:.2f}:d={fade:.2f}[a]"
subprocess.run([FF,"-y","-hide_banner","-loglevel","error","-i",silent,
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=50:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=100:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=150:sample_rate=44100",
 "-filter_complex",af,"-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","144k","-shortest","-movflags","+faststart",out],check=True)
print(f"-> {out}  {os.path.getsize(out)/1e6:.1f} MB  {total:.1f}s")
