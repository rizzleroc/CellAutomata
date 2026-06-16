"""PEACOCK — iridescent ocelli. Each dome is coloured concentrically by height (gold rim →
emerald → peacock-blue → dark pupil) so spots read as feather 'eyes'. Slow pull-back reveal.
test <f> / testc <f> preview modes; full render writes /tmp/web8_peacock.mp4."""
import json, os, sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
W,H=1080,1920; FPS=24; WIN=1000; WX=(W-WIN)//2; WY=380
BG=(2,8,11); BONE=(224,238,232); DIM=(96,128,124)
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
    f=open('/tmp/peacock_field.bin','rb'); f.seek(idx*SZF)
    a=np.frombuffer(f.read(SZF),np.uint16).reshape(1000,1000).astype(np.float32)/65535.0; f.close(); return a
def make_lut(stops):
    xs=np.linspace(0,1,len(stops)); out=np.zeros((256,3),np.float32); t=np.linspace(0,1,256)
    for c in range(3): out[:,c]=np.interp(t,xs,[s[c] for s in stops])
    return out
# concentric eye: ground -> gold rim -> emerald -> peacock blue -> dark pupil, by height
LUT_EYE=make_lut([(3,12,16),(150,110,38),(28,150,96),(26,98,172),(16,40,96),(10,22,64),(8,16,52)])
def ocelli(h01, strength=3.4):
    gy,gx=np.gradient(h01)
    gm=np.sqrt(gx*gx+gy*gy)
    nz=1.0/strength; lx,ly,lz=-0.48,-0.55,0.66
    inv=1.0/np.sqrt(gx*gx+gy*gy+nz*nz)
    shade=np.clip((gx*lx+gy*ly+nz*lz)*inv,0,1)
    he=np.clip(h01*2.6,0,1)                                       # gain so a dome spans the full eye ramp
    idx=np.clip(he*255,0,255).astype(np.int32)
    col=LUT_EYE[idx]*(0.42+0.72*shade)[...,None]
    spec=np.clip(shade-0.80,0,1)*5.0*np.clip(h01-0.18,0,1)
    col+=spec[...,None]*np.array([120,235,210],np.float32)        # cyan-green structural glint
    return np.clip(col,0,255).astype(np.uint8)
def vig(n):
    yy,xx=np.mgrid[0:n,0:n]; r=np.hypot((xx-n/2)/(n/2),(yy-n/2)/(n/2))
    return np.clip(1-0.48*np.clip(r-0.54,0,1)**1.8,0,1).astype(np.float32)[...,None]
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
    # Tight — each dome must fill enough pixels to read as a concentric eye. Slow push + drift among eyes.
    p=f/NF
    cs=lerp(300,200,smooth5(p))
    margin=(1000-cs)/2*0.82; env=np.sin(np.pi*p)**0.6
    ccx=500+margin*0.55*np.sin(p*np.pi*1.6-np.pi/2)*env
    ccy=500+margin*0.55*np.cos(p*np.pi*1.3)*env
    return cs,ccx,ccy
def render_window(f,NF):
    field=readfield(f); cs,ccx,ccy=camera(f,NF)
    h01=cropresize(field,cs,ccx,ccy)
    img=ocelli(h01).astype(np.float32)*VIG
    return np.clip(img,0,255).astype(np.uint8), cs
ACC=[(44,176,150),(212,172,72),(58,120,202),(212,172,72),(44,176,150)]
def accent_at(p):
    x=p*(len(ACC)-1); i=min(len(ACC)-2,int(x)); t=x-i
    a=np.array(ACC[i]); b=np.array(ACC[i+1]); return tuple((a*(1-t)+b*t).astype(int))
def reticle(d,x,y,n,AC,a=1.0):
    for cx,cy in[(x,y),(x+n,y),(x,y+n),(x+n,y+n)]:
        d.line([(cx-20,cy),(cx+20,cy)],fill=(*AC,int(130*a)),width=1)
        d.line([(cx,cy-20),(cx,cy+20)],fill=(*AC,int(130*a)),width=1)
    d.rectangle([x-1,y-1,x+n,y+n],outline=(*AC,int(55*a)),width=1)
NTITLE=84
def compose_frame(f,NF,NAMES,FK):
    p=f/NF; AC=accent_at(p)
    img,cs=render_window(f,NF)
    cv=Image.new("RGBA",(W,H),(*BG,255)); cv.paste(Image.fromarray(img),(WX,WY))
    d=ImageDraw.Draw(cv); reticle(d,WX,WY,WIN,AC,1.0)
    if f<NTITLE:
        g=min(1,f/16)*min(1,(NTITLE-1-f)/16); ov=Image.new("RGBA",(W,H),(0,0,0,int(150*g))); cv.alpha_composite(ov)
        text(cv,(W//2,150),sp("iridescent ocelli"),F_mono(22),DIM,0.6*g)
        text(cv,(W//2,560),"PEACOCK",F_disp(118),BONE,g)
        text(cv,(W//2,690),"a hundred eyes in the fan",F_disp(42),AC,g)
        label(cv,(W//2,1240),"gray–scott · spot regime · structural blue",20,DIM,0.7*g)
    else:
        text(cv,(W//2,150),"▶  "+sp("live"),F_monob(26),AC,0.6)
        nm=NAMES[f]; text(cv,(W//2,250),nm.upper(),F_disp(70),BONE,1.0)
        text(cv,(W//2,320),sp("ocellus"),F_mono(18),DIM,0.5)
        sx=WX+8; sy=WY+WIN+40
        d.line([(sx,sy),(sx+140,sy)],fill=(*BONE,190),width=2)
        for xx in (sx,sx+140): d.line([(xx,sy-6),(xx,sy+6)],fill=(*BONE,190),width=2)
        text(cv,(sx+70,sy+24),f"{int(150/WIN*cs)} cells",F_mono(20),DIM,0.8)
        text(cv,(WX+WIN-8,sy+12),sp(f"F {FK[f][0]:.4f} · k {FK[f][1]:.4f}"),F_mono(19),AC,0.85,anc="rm")
        text(cv,(WX+WIN-8,sy+42),sp(f"generation {f*10:,}"),F_mono(17),DIM,0.6,anc="rm")
        label(cv,(W//2,1880),"cellautomata · web8 · peacock",17,DIM,0.45)
    return cv
if __name__=='__main__' and len(sys.argv)>2 and sys.argv[1]=='test':
    M=json.load(open('/tmp/peacock_meta.json')); img,cs=render_window(int(sys.argv[2]),M['NF'])
    Image.fromarray(img).save('/tmp/peacock_test.png'); print("test frame saved cs",cs); sys.exit()
if __name__=='__main__' and len(sys.argv)>2 and sys.argv[1]=='testc':
    M=json.load(open('/tmp/peacock_meta.json'))
    compose_frame(int(sys.argv[2]),M['NF'],M['names'],M['fk']).convert("RGB").save('/tmp/peacock_testc.png'); print("chrome frame saved"); sys.exit()
M=json.load(open('/tmp/peacock_meta.json')); NF=M['NF']; FK=M['fk']; NAMES=M['names']
silent="/tmp/peacock_silent.mp4"
wr=imageio_ffmpeg.write_frames(silent,(W,H),fps=FPS,codec="libx264",pix_fmt_in="rgb24",pix_fmt_out="yuv420p",macro_block_size=8,output_params=["-crf","20","-preset","medium"])
wr.send(None)
def emit(cv): wr.send(np.ascontiguousarray(np.asarray(cv.convert("RGB"),np.uint8)).tobytes())
for f in range(NF):
    emit(compose_frame(f,NF,NAMES,FK))
wr.close(); print("composited")
total=NF/FPS; out="/tmp/web8_peacock.mp4"
# Regal shimmer: 49 / 98 / 147 Hz (octaves + fifth).
fade=min(3.5,total/3); fin=min(3.0,total/3); fo=max(0.0,total-fade)
af=f"[1:a][2:a][3:a]amix=inputs=3,volume=0.11,lowpass=f=600,afade=t=in:st=0:d={fin:.2f},afade=t=out:st={fo:.2f}:d={fade:.2f}[a]"
subprocess.run([FF,"-y","-hide_banner","-loglevel","error","-i",silent,
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=49:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=98:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=147:sample_rate=44100",
 "-filter_complex",af,"-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","144k","-shortest","-movflags","+faststart",out],check=True)
print(f"-> {out}  {os.path.getsize(out)/1e6:.1f} MB  {total:.1f}s")
