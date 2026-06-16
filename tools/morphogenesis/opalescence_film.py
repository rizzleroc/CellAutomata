"""OPALESCENCE — structural colour. Colour is NOT a palette LUT: it is computed per pixel from a
thin-film interference model (opal / nacre / oil-slick), driven by membrane thickness (height) and
curvature (gradient), drifting over time. Slow orbital push-in. The spectral reel.
Smoke test:  python3 opalescence_film.py test 470  /  chrome: ... testc 470  /  full: ..."""
import json, os, sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
W,H=1080,1920; FPS=24; WIN=1000; WX=(W-WIN)//2; WY=380
BG=(3,3,7); BONE=(236,238,245); DIM=(130,134,150)
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
    s=s.upper()
    for gap in ("  "," ",""):
        for sz in range(size,size-4,-1):
            t=gap.join(s)
            if ImageDraw.Draw(cv).textlength(t,font=F_mono(sz))<=maxw:
                text(cv,xy,t,F_mono(sz),fill,a,anc); return
    text(cv,xy," ".join(s),F_mono(size-3),fill,a,anc)
SZF=1000*1000*2
def readfield(idx):
    f=open('/tmp/opalescence_field.bin','rb'); f.seek(idx*SZF)
    a=np.frombuffer(f.read(SZF),np.uint16).reshape(1000,1000).astype(np.float32)/65535.0; f.close(); return a
# ---- thin-film interference: hue from thickness (height) + curvature (gradient), drifting in time
THICK=30.0   # interference cycles across the height range
TILT =95.0   # how strongly surface curvature shifts the hue (the oil-slick edge shimmer)
TWO3=2.0943951; FOUR3=4.1887902
def iridescent(h01, drift, strength=3.2):
    gy,gx=np.gradient(h01)
    gm=np.sqrt(gx*gx+gy*gy)
    nz=1.0/strength; lx,ly,lz=-0.50,-0.55,0.66
    inv=1.0/np.sqrt(gx*gx+gy*gy+nz*nz)
    shade=np.clip((gx*lx+gy*ly+nz*lz)*inv,0,1)
    phase=h01*THICK + gm*TILT + drift
    R=0.5+0.5*np.cos(phase); G=0.5+0.5*np.cos(phase+TWO3); B=0.5+0.5*np.cos(phase+FOUR3)
    col=np.stack([R,G,B],axis=-1)*0.82+0.18        # pearly: lift toward white, keep it lively
    col=col*(0.30+0.82*shade)[...,None]            # depth
    spec=np.clip(shade-0.78,0,1)*5.5*np.clip(h01-0.25,0,1)
    col+=spec[...,None]                              # pearly white specular on the peaks
    col*=np.clip(h01*6.0,0,1)[...,None]            # sink the deep substrate toward the dark field
    return np.clip(col*255,0,255).astype(np.uint8)
def vig(n):
    yy,xx=np.mgrid[0:n,0:n]; r=np.hypot((xx-n/2)/(n/2),(yy-n/2)/(n/2))
    return np.clip(1-0.50*np.clip(r-0.54,0,1)**1.8,0,1).astype(np.float32)[...,None]
VIG=vig(WIN)
def smooth5(t): t=min(1,max(0,t)); return t*t*t*(t*(t*6-15)+10)
def lerp(a,b,t): return a+(b-a)*t
def cropresize(field,cs,ccx,ccy):
    cs=int(round(max(150,min(1000,cs)))); x=int(round(ccx-cs/2)); y=int(round(ccy-cs/2))
    x=max(0,min(1000-cs,x)); y=max(0,min(1000-cs,y))
    sub=field[y:y+cs,x:x+cs]
    im=Image.fromarray(sub,mode='F').resize((WIN,WIN),Image.LANCZOS)
    return np.asarray(im,np.float32)
def camera(f,NF):
    # Slow majestic push-in while ORBITING — like turning a gem under a lamp.
    p=f/NF
    cs=lerp(720,360,smooth5(p))
    margin=(1000-cs)/2*0.82; env=np.sin(np.pi*p)**0.6; ang=p*np.pi*2.0   # one full orbit
    ccx=500+margin*0.55*np.cos(ang)*env
    ccy=500+margin*0.55*np.sin(ang)*env
    return cs,ccx,ccy
def render_window(f,NF):
    field=readfield(f); cs,ccx,ccy=camera(f,NF)
    h01=cropresize(field,cs,ccx,ccy)
    drift=(f/NF)*6.2832*3.0                          # 3 full hue rotations over the reel
    img=iridescent(h01,drift).astype(np.float32)*VIG
    return np.clip(img,0,255).astype(np.uint8), cs
def accent_at(p):                                    # accent cycles through the spectrum too
    ph=p*6.2832
    return (int(110+120*(0.5+0.5*np.cos(ph))), int(110+120*(0.5+0.5*np.cos(ph+TWO3))), int(110+120*(0.5+0.5*np.cos(ph+FOUR3))))
def reticle(d,x,y,n,AC,a=1.0):
    for cx,cy in[(x,y),(x+n,y),(x,y+n),(x+n,y+n)]:
        d.line([(cx-20,cy),(cx+20,cy)],fill=(*AC,int(130*a)),width=1)
        d.line([(cx,cy-20),(cx,cy+20)],fill=(*AC,int(130*a)),width=1)
    d.rectangle([x-1,y-1,x+n,y+n],outline=(*AC,int(60*a)),width=1)
NTITLE=84
def compose_frame(f,NF,NAMES,FK):
    p=f/NF; AC=accent_at(p)
    img,cs=render_window(f,NF)
    cv=Image.new("RGBA",(W,H),(*BG,255)); cv.paste(Image.fromarray(img),(WX,WY))
    d=ImageDraw.Draw(cv); reticle(d,WX,WY,WIN,AC,1.0)
    if f<NTITLE:
        g=min(1,f/16)*min(1,(NTITLE-1-f)/16); ov=Image.new("RGBA",(W,H),(0,0,0,int(150*g))); cv.alpha_composite(ov)
        text(cv,(W//2,150),sp("structural colour"),F_mono(22),DIM,0.6*g)
        text(cv,(W//2,560),"OPALESCENCE",F_disp(96),BONE,g)
        text(cv,(W//2,690),"thin-film interference in a living membrane",F_disp(40),AC,g)
        label(cv,(W//2,1240),"gray–scott · hue from thickness & curvature · no palette",20,DIM,0.7*g)
    else:
        text(cv,(W//2,150),"▶  "+sp("live"),F_monob(26),AC,0.6)
        nm=NAMES[f]; text(cv,(W//2,250),nm.upper(),F_disp(70),BONE,1.0)
        text(cv,(W//2,320),sp("iridescent membrane"),F_mono(18),DIM,0.5)
        sx=WX+8; sy=WY+WIN+40
        d.line([(sx,sy),(sx+140,sy)],fill=(*BONE,190),width=2)
        for xx in (sx,sx+140): d.line([(xx,sy-6),(xx,sy+6)],fill=(*BONE,190),width=2)
        text(cv,(sx+70,sy+24),f"{int(150/WIN*cs)} cells",F_mono(20),DIM,0.8)
        text(cv,(WX+WIN-8,sy+12),sp(f"F {FK[f][0]:.4f} · k {FK[f][1]:.4f}"),F_mono(19),AC,0.85,anc="rm")
        text(cv,(WX+WIN-8,sy+42),sp(f"generation {f*10:,}"),F_mono(17),DIM,0.6,anc="rm")
        label(cv,(W//2,1880),"cellautomata · web8 · opalescence",17,DIM,0.45)
    return cv
if __name__=='__main__' and len(sys.argv)>2 and sys.argv[1]=='test':
    M=json.load(open('/tmp/opalescence_meta.json')); img,cs=render_window(int(sys.argv[2]),M['NF'])
    Image.fromarray(img).save('/tmp/opalescence_test.png'); print("test frame saved cs",cs); sys.exit()
if __name__=='__main__' and len(sys.argv)>2 and sys.argv[1]=='testc':
    M=json.load(open('/tmp/opalescence_meta.json'))
    compose_frame(int(sys.argv[2]),M['NF'],M['names'],M['fk']).convert("RGB").save('/tmp/opalescence_testc.png'); print("chrome frame saved"); sys.exit()
# ===== FULL RENDER =====
M=json.load(open('/tmp/opalescence_meta.json')); NF=M['NF']; FK=M['fk']; NAMES=M['names']
silent="/tmp/opalescence_silent.mp4"
wr=imageio_ffmpeg.write_frames(silent,(W,H),fps=FPS,codec="libx264",pix_fmt_in="rgb24",pix_fmt_out="yuv420p",macro_block_size=8,output_params=["-crf","20","-preset","medium"])
wr.send(None)
def emit(cv): wr.send(np.ascontiguousarray(np.asarray(cv.convert("RGB"),np.uint8)).tobytes())
for f in range(NF):
    emit(compose_frame(f,NF,NAMES,FK))
wr.close(); print("composited")
total=NF/FPS; out="/tmp/web8_opalescence.mp4"
# Brighter shimmer drone: 55 / 110 / 165 Hz (octave + fifth), lightly lowpassed.
fade=min(3.5,total/3); fin=min(3.0,total/3); fo=max(0.0,total-fade)
af=f"[1:a][2:a][3:a]amix=inputs=3,volume=0.11,lowpass=f=700,afade=t=in:st=0:d={fin:.2f},afade=t=out:st={fo:.2f}:d={fade:.2f}[a]"
subprocess.run([FF,"-y","-hide_banner","-loglevel","error","-i",silent,
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=55:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=110:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=165:sample_rate=44100",
 "-filter_complex",af,"-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","144k","-shortest","-movflags","+faststart",out],check=True)
print(f"-> {out}  {os.path.getsize(out)/1e6:.1f} MB  {total:.1f}s")
