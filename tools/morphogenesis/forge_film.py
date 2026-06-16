"""FORGE — magma/lava palette, fast oscillating camera, turbulent territory"""
import json, os, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
W,H=1080,1920; FPS=24; WIN=1000; WX=(W-WIN)//2; WY=380
BG=(4,1,0); BONE=(255,240,200); DIM=(160,120,80)
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
SZF=1000*1000*2
def readfield(idx,GW=1000,GH=1000):
    f=open('/tmp/forge_field.bin','rb'); f.seek(idx*SZF)
    a=np.frombuffer(f.read(SZF),np.uint16).reshape(GH,GW).astype(np.float32)/65535.0; f.close(); return a

def make_lut(stops):
    xs=np.linspace(0,1,len(stops)); out=np.zeros((256,3),np.float32); t=np.linspace(0,1,256)
    for c in range(3): out[:,c]=np.interp(t,xs,[s[c] for s in stops])
    return out

# FORGE palette: jet-black → deep crimson → orange-red → amber → yellow → blinding white
LUT_MAGMA=make_lut([(0,0,0),(30,2,2),(100,10,5),(180,60,10),(220,140,20),(255,210,60),(255,252,200)])
# FORGE B: obsidian → scarlet → tangerine → gold
LUT_EMBER=make_lut([(3,0,0),(60,5,2),(150,30,10),(220,100,20),(240,200,40),(255,240,120),(255,255,220)])
# FORGE C: black → dark-plum-red → magenta-red → hot-pink (volcanic with sulfur)
LUT_SULPH=make_lut([(0,0,0),(50,0,20),(130,10,60),(200,40,100),(240,120,140),(255,200,180),(255,248,240)])
PALS=[LUT_MAGMA,LUT_EMBER,LUT_SULPH]

def palette_at(p):
    # magma → ember → sulph → ember → magma (hot cycle)
    seq=[0,1,2,1,0]; x=p*(len(seq)-1); i=min(len(seq)-2,int(x)); t=x-i
    return PALS[seq[i]]*(1-t)+PALS[seq[i+1]]*t

def relief(h01, lut, strength=3.0):
    gy,gx=np.gradient(h01)
    lx,ly,lz=-0.40,-0.40,0.82   # flatter light for forge (more diffuse heat glow)
    nz=1.0/strength
    inv=1.0/np.sqrt(gx*gx+gy*gy+nz*nz)
    shade=np.clip((gx*lx+gy*ly+nz*lz)*inv,0,1)
    idx=np.clip((h01*255),0,255).astype(np.int32)
    base=lut[idx]
    col=base*(0.55+0.55*shade)[...,None]   # stronger ambient (glowing forge)
    # White-hot specular highlight
    spec=np.clip(shade-0.75,0,1)*7.0*np.clip(h01-0.35,0,1)
    col+=spec[...,None]*np.array([255,255,240],np.float32)
    return np.clip(col,0,255).astype(np.uint8)

def vig(n):
    yy,xx=np.mgrid[0:n,0:n]; r=np.hypot((xx-n/2)/(n/2),(yy-n/2)/(n/2))
    return np.clip(1-0.35*np.clip(r-0.62,0,1)**1.5,0,1).astype(np.float32)[...,None]
VIG=vig(WIN)
def smooth(t): return t*t*(3-2*t)
def smooth5(t): t=min(1,max(0,t)); return t*t*t*(t*(t*6-15)+10)
def lerp(a,b,t): return a+(b-a)*t

def cropresize(field,cs,ccx,ccy):
    cs=int(round(max(150,min(1000,cs)))); x=int(round(ccx-cs/2)); y=int(round(ccy-cs/2))
    x=max(0,min(1000-cs,x)); y=max(0,min(1000-cs,y))
    sub=field[y:y+cs,x:x+cs]
    im=Image.fromarray(sub,mode='F').resize((WIN,WIN),Image.LANCZOS)
    return np.asarray(im,np.float32)

def camera(f,NF):
    p=f/NF
    # FORGE camera: energetic but SMOOTH — eased breathing zoom + wide eased pan, no high-freq jitter
    z=0.5-0.5*np.cos(p*np.pi*4)               # ~2 full breaths across the film, perfectly smooth
    cs=lerp(360,760,z)
    # Pan amplitude as a fraction of margin -> stays inside the crop window, never clips
    margin=(1000-cs)/2*0.82
    env=np.sin(np.pi*p)**0.45                  # ease pan in/out (still lively in the middle)
    ccx=500+margin*0.66*np.sin(p*np.pi*2.6)*env
    ccy=500+margin*0.66*np.cos(p*np.pi*2.0)*env
    return cs,ccx,ccy

def render_window(f,NF):
    field=readfield(f); cs,ccx,ccy=camera(f,NF)
    h01=cropresize(field,cs,ccx,ccy)
    img=relief(h01,palette_at(f/NF)).astype(np.float32)*VIG
    return np.clip(img,0,255).astype(np.uint8), cs

# Forge accents: ember orange → hot white → amber → scarlet → ember
ACC_FORGE=[(255,140,30),(255,240,120),(255,180,60),(220,50,20),(255,140,30)]
def accent_at(p):
    seq=[0,1,2,3,4]; x=p*(len(seq)-1); i=min(len(seq)-2,int(x)); t=x-i
    a=np.array(ACC_FORGE[seq[i]]); b=np.array(ACC_FORGE[seq[i+1]]); return tuple((a*(1-t)+b*t).astype(int))

M=json.load(open('/tmp/forge_meta.json')); NF=M['NF']; WP=M['WP']; FK=M['fk']; NAMES=M['names']; POP=M['pop']
silent="/tmp/forge_silent.mp4"
wr=imageio_ffmpeg.write_frames(silent,(W,H),fps=FPS,codec="libx264",pix_fmt_in="rgb24",pix_fmt_out="yuv420p",macro_block_size=8,output_params=["-crf","20","-preset","medium"])
wr.send(None)
def emit(cv): wr.send(np.ascontiguousarray(np.asarray(cv.convert("RGB"),np.uint8)).tobytes())

NTITLE=84
for f in range(NF):
    p=f/NF; AC=accent_at(p)
    img,cs=render_window(f,NF)
    cv=Image.new("RGBA",(W,H),(*BG,255)); cv.paste(Image.fromarray(img),(WX,WY))
    d=ImageDraw.Draw(cv)
    # Thick hot reticle
    for cx2,cy2 in[(WX,WY),(WX+WIN,WY),(WX,WY+WIN),(WX+WIN,WY+WIN)]:
        d.line([(cx2-30,cy2),(cx2+30,cy2)],fill=(*AC,180),width=2)
        d.line([(cx2,cy2-30),(cx2,cy2+30)],fill=(*AC,180),width=2)
    d.rectangle([WX-1,WY-1,WX+WIN,WY+WIN],outline=(*AC,50),width=1)

    if f<NTITLE:
        g2=min(1,f/16)*min(1,(NTITLE-1-f)/16)
        ov=Image.new("RGBA",(W,H),(0,0,0,int(170*g2))); cv.alpha_composite(ov)
        text(cv,(W//2,150),sp("the forge"),F_mono(22),DIM,0.6*g2)
        text(cv,(W//2,560),"IGNITION",F_disp(120),BONE,g2)
        text(cv,(W//2,680),"chaos forged into form",F_disp(46),AC,g2)
        text(cv,(W//2,1240),sp("gray–scott · turbulent & worm regimes"),F_mono(20),DIM,0.7*g2)
    else:
        text(cv,(W//2,150),"▶  "+sp("live"),F_monob(26),AC,0.75)
        nm=NAMES[f]; text(cv,(W//2,250),nm.upper(),F_disp(74),BONE,1.0)
        text(cv,(W//2,320),sp("forge morphology"),F_mono(18),DIM,0.5)

        sx=WX+8; sy=WY+WIN+40
        d.line([(sx,sy),(sx+140,sy)],fill=(*BONE,200),width=2)
        for xx in (sx,sx+140): d.line([(xx,sy-6),(xx,sy+6)],fill=(*BONE,200),width=2)
        text(cv,(sx+70,sy+24),f"{int(150/WIN*cs)} cells",F_mono(20),DIM,0.8)
        text(cv,(WX+WIN-8,sy+12),sp(f"F {FK[f][0]:.4f} · k {FK[f][1]:.4f}"),F_mono(19),AC,0.85,anc="rm")
        text(cv,(WX+WIN-8,sy+42),sp(f"generation {f*10:,}"),F_mono(17),DIM,0.6,anc="rm")
        text(cv,(W//2,1880),sp("cellautomata · web8 · turbulent forge"),F_mono(17),DIM,0.45)

    emit(cv)

wr.close(); print("composited")
total=NF/FPS; out="/tmp/web8_forge.mp4"
# Forge tones: 64/96/128 Hz (tritone cluster — industrial tension)
af=f"[1:a][2:a][3:a]amix=inputs=3,volume=0.14,lowpass=f=600,afade=t=in:st=0:d=3,afade=t=out:st={total-3.5:.1f}:d=3.5[a]"
subprocess.run([FF,"-y","-hide_banner","-loglevel","error","-i",silent,
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=64:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=96:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=128:sample_rate=44100",
 "-filter_complex",af,"-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","144k","-shortest","-movflags","+faststart",out],check=True)
print(f"-> {out}  {os.path.getsize(out)/1e6:.1f} MB  {total:.1f}s")
