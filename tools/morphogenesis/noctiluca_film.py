"""NOCTILUCA — deep-sea bioluminescence. Green-gold living light, lateral submersible drift.
Smoke test one frame:  python3 noctiluca_film.py test 24   (uses whatever NF the .bin holds)
Full render:           python3 noctiluca_film.py"""
import json, os, sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
W,H=1080,1920; FPS=24; WIN=1000; WX=(W-WIN)//2; WY=380
BG=(1,3,5); BONE=(214,238,224); DIM=(86,128,116)
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
    f=open('/tmp/noctiluca_field.bin','rb'); f.seek(idx*SZF)
    a=np.frombuffer(f.read(SZF),np.uint16).reshape(1000,1000).astype(np.float32)/65535.0; f.close(); return a
# ---- bioluminescent palettes: abyssal teal / viridian glow / gold plankton ----
def make_lut(stops):
    xs=np.linspace(0,1,len(stops)); out=np.zeros((256,3),np.float32); t=np.linspace(0,1,256)
    for c in range(3): out[:,c]=np.interp(t,xs,[s[c] for s in stops])
    return out
# Hue shifts pushed into the LOW-MIDS (h01~0.2–0.45, where the GS field lives) so the WHOLE
# field changes colour per phase, not just the rare bright peaks.
LUT_ABYSS=make_lut([(0,3,8),(2,22,40),(4,52,80),(10,96,128),(40,168,180),(140,222,224),(220,250,248)])  # cold cyan / blue-teal
LUT_VIRID=make_lut([(1,8,4),(6,34,16),(16,84,36),(40,150,64),(110,212,108),(190,244,168),(230,252,214)]) # vivid green bloom
LUT_GOLD =make_lut([(2,6,2),(28,30,10),(74,68,20),(140,112,34),(204,168,60),(240,214,120),(252,248,200)])# warm chartreuse → gold
PALS=[LUT_ABYSS,LUT_VIRID,LUT_GOLD]
def palette_at(p):  # abyss -> viridian -> gold -> viridian -> abyss
    seq=[0,1,2,1,0]; x=p*(len(seq)-1); i=min(len(seq)-2,int(x)); t=x-i
    return PALS[seq[i]]*(1-t)+PALS[seq[i+1]]*t
def relief(h01, lut, strength=3.6):
    gy,gx=np.gradient(h01)
    lx,ly,lz=-0.50,-0.55,0.66
    nz=1.0/strength
    inv=1.0/np.sqrt(gx*gx+gy*gy+nz*nz)
    shade=np.clip((gx*lx+gy*ly+nz*lz)*inv,0,1)
    idx=np.clip((h01*255),0,255).astype(np.int32)
    base=lut[idx]
    col=base*(0.42+0.70*shade)[...,None]            # faint ambient glow even in the deep
    spec=np.clip(shade-0.80,0,1)*5.5*np.clip(h01-0.28,0,1)
    col+=spec[...,None]*np.array([176,255,210],np.float32)   # green-white biolight on the peaks
    return np.clip(col,0,255).astype(np.uint8)
def vig(n):
    yy,xx=np.mgrid[0:n,0:n]; r=np.hypot((xx-n/2)/(n/2),(yy-n/2)/(n/2))
    return np.clip(1-0.52*np.clip(r-0.50,0,1)**1.9,0,1).astype(np.float32)[...,None]
VIG=vig(WIN)
def lerp(a,b,t): return a+(b-a)*t
def cropresize(field,cs,ccx,ccy):
    cs=int(round(max(150,min(1000,cs)))); x=int(round(ccx-cs/2)); y=int(round(ccy-cs/2))
    x=max(0,min(1000-cs,x)); y=max(0,min(1000-cs,y))
    sub=field[y:y+cs,x:x+cs]
    im=Image.fromarray(sub,mode='F').resize((WIN,WIN),Image.LANCZOS)
    return np.asarray(im,np.float32)
def camera(f,NF):
    # Submersible DRIFT: near-constant moderate zoom, dominant slow horizontal sweep, subtle vertical bob.
    p=f/NF
    cs=lerp(560,440,0.5-0.5*np.cos(p*np.pi*2.0))      # very gentle breath around a moderate window
    margin=(1000-cs)/2*0.82
    env=np.sin(np.pi*p)**0.5
    ccx=500+margin*0.92*np.sin(p*np.pi*1.2-np.pi/2)*env   # long left->right glide
    ccy=500+margin*0.22*np.sin(p*np.pi*2.4)*env           # gentle bob
    return cs,ccx,ccy
def render_window(f,NF):
    field=readfield(f); cs,ccx,ccy=camera(f,NF)
    h01=cropresize(field,cs,ccx,ccy)
    img=relief(h01,palette_at(f/NF)).astype(np.float32)*VIG
    return np.clip(img,0,255).astype(np.uint8), cs, float(h01.mean())
ACC=[(120,240,170),(80,222,210),(222,234,140),(80,222,210),(120,240,170)]
def accent_at(p):
    x=p*(len(ACC)-1); i=min(len(ACC)-2,int(x)); t=x-i
    a=np.array(ACC[i]); b=np.array(ACC[i+1]); return tuple((a*(1-t)+b*t).astype(int))
def reticle(d,x,y,n,AC,a=1.0):
    for cx,cy in[(x,y),(x+n,y),(x,y+n),(x+n,y+n)]:
        d.line([(cx-18,cy),(cx+18,cy)],fill=(*AC,int(110*a)),width=1)
        d.line([(cx,cy-18),(cx,cy+18)],fill=(*AC,int(110*a)),width=1)
NTITLE=84
def compose_frame(f,NF,NAMES,FK):
    p=f/NF; AC=accent_at(p)
    img,cs,lum=render_window(f,NF)
    cv=Image.new("RGBA",(W,H),(*BG,255)); cv.paste(Image.fromarray(img),(WX,WY))
    d=ImageDraw.Draw(cv); reticle(d,WX,WY,WIN,AC,1.0)
    if f<NTITLE:
        g=min(1,f/16)*min(1,(NTITLE-1-f)/16); ov=Image.new("RGBA",(W,H),(0,0,0,int(165*g))); cv.alpha_composite(ov)
        text(cv,(W//2,150),sp("abyssal bioluminescence"),F_mono(22),DIM,0.6*g)
        text(cv,(W//2,560),"NOCTILUCA",F_disp(108),BONE,g)
        text(cv,(W//2,690),"living light in the dark water",F_disp(44),AC,g)
        label(cv,(W//2,1240),"gray–scott · drifting solitons · u-skate & negaton",20,DIM,0.7*g)
    else:
        text(cv,(W//2,150),"▶  "+sp("live"),F_monob(26),AC,0.6)
        nm=NAMES[f]; text(cv,(W//2,250),nm.upper(),F_disp(70),BONE,1.0)
        text(cv,(W//2,320),sp("bioluminescence"),F_mono(18),DIM,0.5)
        sx=WX+8; sy=WY+WIN+40
        d.line([(sx,sy),(sx+140,sy)],fill=(*BONE,180),width=2)
        for xx in (sx,sx+140): d.line([(xx,sy-6),(xx,sy+6)],fill=(*BONE,180),width=2)
        text(cv,(sx+70,sy+24),f"{int(150/WIN*cs)} cells",F_mono(20),DIM,0.8)
        text(cv,(WX+WIN-8,sy+12),sp(f"F {FK[f][0]:.4f} · k {FK[f][1]:.4f}"),F_mono(19),AC,0.85,anc="rm")
        text(cv,(WX+WIN-8,sy+42),sp(f"luminance {lum*100:4.1f}%"),F_mono(17),DIM,0.6,anc="rm")
        label(cv,(W//2,1880),"cellautomata · web8 · noctiluca",17,DIM,0.45)
    return cv
if __name__=='__main__' and len(sys.argv)>2 and sys.argv[1]=='test':
    M=json.load(open('/tmp/noctiluca_meta.json')); img,cs,_=render_window(int(sys.argv[2]),M['NF'])
    Image.fromarray(img).save('/tmp/noctiluca_test.png'); print("test frame saved cs",cs); sys.exit()
if __name__=='__main__' and len(sys.argv)>2 and sys.argv[1]=='testc':
    M=json.load(open('/tmp/noctiluca_meta.json'))
    compose_frame(int(sys.argv[2]),M['NF'],M['names'],M['fk']).convert("RGB").save('/tmp/noctiluca_testc.png'); print("chrome frame saved"); sys.exit()
# ===== FULL RENDER =====
M=json.load(open('/tmp/noctiluca_meta.json')); NF=M['NF']; FK=M['fk']; NAMES=M['names']
silent="/tmp/noctiluca_silent.mp4"
wr=imageio_ffmpeg.write_frames(silent,(W,H),fps=FPS,codec="libx264",pix_fmt_in="rgb24",pix_fmt_out="yuv420p",macro_block_size=8,output_params=["-crf","20","-preset","medium"])
wr.send(None)
def emit(cv): wr.send(np.ascontiguousarray(np.asarray(cv.convert("RGB"),np.uint8)).tobytes())
for f in range(NF):
    emit(compose_frame(f,NF,NAMES,FK))
wr.close(); print("composited")
total=NF/FPS; out="/tmp/web8_noctiluca.mp4"
# Deep ocean drone: 36 / 54 / 72 Hz (octave + fifth), heavy lowpass — subterranean calm.
fade=min(3.5,total/3); fin=min(3.0,total/3); fo=max(0.0,total-fade)   # guard short smoke-test clips
af=f"[1:a][2:a][3:a]amix=inputs=3,volume=0.11,lowpass=f=380,afade=t=in:st=0:d={fin:.2f},afade=t=out:st={fo:.2f}:d={fade:.2f}[a]"
subprocess.run([FF,"-y","-hide_banner","-loglevel","error","-i",silent,
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=36:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=54:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=72:sample_rate=44100",
 "-filter_complex",af,"-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","144k","-shortest","-movflags","+faststart",out],check=True)
print(f"-> {out}  {os.path.getsize(out)/1e6:.1f} MB  {total:.1f}s")
