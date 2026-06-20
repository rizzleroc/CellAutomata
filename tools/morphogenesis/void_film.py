"""VOID — X-ray inverted look, electric dark palette, static camera"""
import json, os, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
W,H=1080,1920; FPS=24; WIN=1000; WX=(W-WIN)//2; WY=380
BG=(0,0,3); BONE=(230,230,245); DIM=(90,100,130)
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
    f=open('/tmp/void_field.bin','rb'); f.seek(idx*SZF)
    a=np.frombuffer(f.read(SZF),np.uint16).reshape(GH,GW).astype(np.float32)/65535.0; f.close(); return a

# ---- VOID palette: bright luminous background → dark voids
# Input: inverted h01 (1-v), so background=bright, patterns=dark
def make_lut(stops):
    xs=np.linspace(0,1,len(stops)); out=np.zeros((256,3),np.float32); t=np.linspace(0,1,256)
    for c in range(3): out[:,c]=np.interp(t,xs,[s[c] for s in stops])
    return out

# VOID palette A: deep dark → electric blue → ice cyan → white (neon void)
LUT_ELEC=make_lut([(0,0,8),(2,6,40),(10,30,90),(20,80,160),(60,160,220),(140,220,255),(240,250,255)])
# VOID palette B: deep plum → violet → lavender → white
LUT_PLUM=make_lut([(5,0,10),(30,5,50),(80,20,100),(140,60,160),(200,120,220),(235,200,245),(250,245,255)])
# VOID palette C: navy → azure → sky → white
LUT_AZURE=make_lut([(0,5,20),(0,20,60),(0,60,120),(20,120,200),(80,180,240),(180,230,255),(245,252,255)])
PALS=[LUT_ELEC,LUT_PLUM,LUT_AZURE]

def palette_at(p):
    # elec → plum → azure → plum → elec
    seq=[0,1,2,1,0]; x=p*(len(seq)-1); i=min(len(seq)-2,int(x)); t=x-i
    return PALS[seq[i]]*(1-t)+PALS[seq[i+1]]*t

def relief(h01, lut, strength=3.8):
    # INVERT: voids show as luminous, patterns as dark cavities
    h_inv = 1.0 - h01
    gy,gx=np.gradient(h_inv)
    lx,ly,lz=0.58,0.52,0.58   # light from lower-right (opposite of lo_film)
    nz=1.0/strength
    inv=1.0/np.sqrt(gx*gx+gy*gy+nz*nz)
    shade=np.clip((gx*lx+gy*ly+nz*lz)*inv,0,1)
    idx=np.clip((h_inv*255),0,255).astype(np.int32)
    base=lut[idx]
    col=base*(0.35+0.75*shade)[...,None]
    # Cool blue specular on the bright void areas
    spec=np.clip(shade-0.78,0,1)*6.0*np.clip(h_inv-0.3,0,1)
    col+=spec[...,None]*np.array([220,240,255],np.float32)
    return np.clip(col,0,255).astype(np.uint8)

def vig(n):
    yy,xx=np.mgrid[0:n,0:n]; r=np.hypot((xx-n/2)/(n/2),(yy-n/2)/(n/2))
    return np.clip(1-0.55*np.clip(r-0.52,0,1)**2.0,0,1).astype(np.float32)[...,None]
VIG=vig(WIN)
def smooth(t): return t*t*(3-2*t)
def smooth5(t): t=min(1,max(0,t)); return t*t*t*(t*(t*6-15)+10)   # smootherstep: 0 1st & 2nd deriv at ends
def lerp(a,b,t): return a+(b-a)*t

def cropresize(field,cs,ccx,ccy):
    cs=int(round(max(150,min(1000,cs)))); x=int(round(ccx-cs/2)); y=int(round(ccy-cs/2))
    x=max(0,min(1000-cs,x)); y=max(0,min(1000-cs,y))
    sub=field[y:y+cs,x:x+cs]
    im=Image.fromarray(sub,mode='F').resize((WIN,WIN),Image.LANCZOS)
    return np.asarray(im,np.float32)

def camera(f,NF):
    # Very slow zoom-out: start zoomed-in on a detail, slowly pull back to reveal the void field
    p=f/NF
    cs=lerp(300,900,smooth5(p))                 # eased pull-back: 300->900 cells (smootherstep)
    # Pan amplitude scaled to a fraction of available margin -> never touches the clip (no jerks)
    margin=(1000-cs)/2*0.82
    env=np.sin(np.pi*p)**0.6                     # ease pan in at start, out at end
    ccx=500+margin*0.60*np.sin(p*np.pi*2.0)*env
    ccy=500+margin*0.60*np.cos(p*np.pi*1.5)*env
    return cs,ccx,ccy

def render_window(f,NF):
    field=readfield(f); cs,ccx,ccy=camera(f,NF)
    h01=cropresize(field,cs,ccx,ccy)
    img=relief(h01,palette_at(f/NF)).astype(np.float32)*VIG
    return np.clip(img,0,255).astype(np.uint8), cs

# Accent: electric blue → violet → icy white → violet → blue
ACC_VOID=[(80,160,255),(160,80,240),(200,240,255),(160,80,240),(80,160,255)]
def accent_at(p):
    seq=[0,1,2,3,4]; x=p*(len(seq)-1); i=min(len(seq)-2,int(x)); t=x-i
    a=np.array(ACC_VOID[seq[i]]); b=np.array(ACC_VOID[seq[i+1]]); return tuple((a*(1-t)+b*t).astype(int))

M=json.load(open('/tmp/void_meta.json')); NF=M['NF']; WP=M['WP']; FK=M['fk']; NAMES=M['names']; POP=M['pop']
silent="/tmp/void_silent.mp4"
wr=imageio_ffmpeg.write_frames(silent,(W,H),fps=FPS,codec="libx264",pix_fmt_in="rgb24",pix_fmt_out="yuv420p",macro_block_size=8,output_params=["-crf","20","-preset","medium"])
wr.send(None)
def emit(cv): wr.send(np.ascontiguousarray(np.asarray(cv.convert("RGB"),np.uint8)).tobytes())

NTITLE=84
for f in range(NF):
    p=f/NF; AC=accent_at(p)
    img,cs=render_window(f,NF)
    cv=Image.new("RGBA",(W,H),(*BG,255)); cv.paste(Image.fromarray(img),(WX,WY))
    d=ImageDraw.Draw(cv)
    # Minimal reticle: just corner marks, no box
    for cx2,cy2 in[(WX,WY),(WX+WIN,WY),(WX,WY+WIN),(WX+WIN,WY+WIN)]:
        d.line([(cx2-18,cy2),(cx2+18,cy2)],fill=(*AC,100),width=1)
        d.line([(cx2,cy2-18),(cx2,cy2+18)],fill=(*AC,100),width=1)

    if f<NTITLE:
        g2=min(1,f/16)*min(1,(NTITLE-1-f)/16)
        ov=Image.new("RGBA",(W,H),(0,0,0,int(160*g2))); cv.alpha_composite(ov)
        text(cv,(W//2,150),sp("void cartography"),F_mono(22),DIM,0.6*g2)
        text(cv,(W//2,560),"THE VOID",F_disp(110),BONE,g2)
        text(cv,(W//2,690),"anti-patterns in the dark ocean",F_disp(42),AC,g2)
        text(cv,(W//2,1240),sp("gray–scott · negaton & hole regimes · inverted"),F_mono(20),DIM,0.7*g2)
    else:
        text(cv,(W//2,150),"▶  "+sp("live"),F_monob(24),AC,0.6)
        nm=NAMES[f]; text(cv,(W//2,250),nm.upper(),F_disp(70),BONE,1.0)
        text(cv,(W//2,320),sp("void morphology"),F_mono(18),DIM,0.5)

        # Scale bar — bottom left of window
        sx=WX+8; sy=WY+WIN+40
        d.line([(sx,sy),(sx+120,sy)],fill=(*BONE,160),width=2)
        for xx in (sx,sx+120): d.line([(xx,sy-6),(xx,sy+6)],fill=(*BONE,160),width=2)
        text(cv,(sx+60,sy+24),f"{int(150/WIN*cs)} cells",F_mono(20),DIM,0.7)

        # F/k bottom right
        text(cv,(WX+WIN-8,sy+12),sp(f"F {FK[f][0]:.4f} · k {FK[f][1]:.4f}"),F_mono(19),AC,0.8,anc="rm")
        text(cv,(WX+WIN-8,sy+42),sp(f"generation {f*10:,}"),F_mono(17),DIM,0.55,anc="rm")

        # Void coverage (inverted pop = void fraction)
        pv=POP[f]
        if pv:
            void_pct=max(0,100-int(pv)/10000*100) if isinstance(pv,int) else 0
            text(cv,(W//2,1870),sp(f"void coverage · {void_pct:.0f}%  generation {f:,}"),F_mono(17),DIM,0.45)

    emit(cv)

wr.close(); print("composited")
total=NF/FPS; out="/tmp/web8_void.mp4"
# Low drone tones: 43/65/86 Hz — deep subterranean void ambience
af=f"[1:a][2:a][3:a]amix=inputs=3,volume=0.11,lowpass=f=420,afade=t=in:st=0:d=3,afade=t=out:st={total-3.5:.1f}:d=3.5[a]"
subprocess.run([FF,"-y","-hide_banner","-loglevel","error","-i",silent,
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=43:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=65:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=86:sample_rate=44100",
 "-filter_complex",af,"-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","144k","-shortest","-movflags","+faststart",out],check=True)
print(f"-> {out}  {os.path.getsize(out)/1e6:.1f} MB  {total:.1f}s")
