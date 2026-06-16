"""CRYSTALLOGENESIS — arctic ice-crystal palette, zoom-in camera, high relief"""
import json, os, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
W,H=1080,1920; FPS=24; WIN=1000; WX=(W-WIN)//2; WY=380
BG=(2,4,10); BONE=(230,240,255); DIM=(100,120,155)
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
    f=open('/tmp/cryst_field.bin','rb'); f.seek(idx*SZF)
    a=np.frombuffer(f.read(SZF),np.uint16).reshape(GH,GW).astype(np.float32)/65535.0; f.close(); return a

def make_lut(stops):
    xs=np.linspace(0,1,len(stops)); out=np.zeros((256,3),np.float32); t=np.linspace(0,1,256)
    for c in range(3): out[:,c]=np.interp(t,xs,[s[c] for s in stops])
    return out

# CRYSTAL palette A: deep navy black → cobalt → steel-blue → ice-powder → silver-white
LUT_ICE=make_lut([(2,4,14),(10,20,60),(20,60,120),(50,120,180),(120,180,220),(200,230,245),(240,250,255)])
# CRYSTAL palette B: deep teal → jade → mint → white
LUT_JADE=make_lut([(2,10,12),(10,40,50),(20,90,80),(50,150,120),(130,210,180),(210,240,225),(245,255,250)])
# CRYSTAL palette C: royal blue → cyan → ice
LUT_ROYAL=make_lut([(5,3,20),(15,10,70),(30,50,140),(60,120,200),(120,190,240),(200,230,255),(250,252,255)])
PALS=[LUT_ICE,LUT_JADE,LUT_ROYAL]

def palette_at(p):
    # ice → jade → royal → jade → ice (cold mineral sequence)
    seq=[0,1,2,1,0]; x=p*(len(seq)-1); i=min(len(seq)-2,int(x)); t=x-i
    return PALS[seq[i]]*(1-t)+PALS[seq[i+1]]*t

def relief(h01, lut, strength=5.2):
    # Higher relief strength = very dramatic 3D crystal facets
    gy,gx=np.gradient(h01)
    lx,ly,lz=-0.60,-0.45,0.66   # raking light from upper-left for crystalline drama
    nz=1.0/strength
    inv=1.0/np.sqrt(gx*gx+gy*gy+nz*nz)
    shade=np.clip((gx*lx+gy*ly+nz*lz)*inv,0,1)
    idx=np.clip((h01*255),0,255).astype(np.int32)
    base=lut[idx]
    col=base*(0.40+0.72*shade)[...,None]
    # Bright icy specular on crystal peaks (tight highlight)
    spec=np.clip(shade-0.85,0,1)*8.0*np.clip(h01-0.30,0,1)
    col+=spec[...,None]*np.array([245,252,255],np.float32)
    return np.clip(col,0,255).astype(np.uint8)

def vig(n):
    yy,xx=np.mgrid[0:n,0:n]; r=np.hypot((xx-n/2)/(n/2),(yy-n/2)/(n/2))
    return np.clip(1-0.50*np.clip(r-0.55,0,1)**1.8,0,1).astype(np.float32)[...,None]
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
    # CRYSTAL camera: slow eased DEEP ZOOM IN — full field -> macro crystal facet detail
    cs=lerp(920,180,smooth5(p))          # smootherstep zoom: 920 -> 180 cells
    # Gentle eased drift, amplitude scaled to margin so it never clips against the edge
    margin=(1000-cs)/2*0.82
    env=np.sin(np.pi*p)**0.7
    ccx=500+margin*0.45*np.sin(p*np.pi*1.6)*env
    ccy=500+margin*0.45*np.cos(p*np.pi*1.3)*env
    return cs,ccx,ccy

def render_window(f,NF):
    field=readfield(f); cs,ccx,ccy=camera(f,NF)
    h01=cropresize(field,cs,ccx,ccy)
    img=relief(h01,palette_at(f/NF)).astype(np.float32)*VIG
    return np.clip(img,0,255).astype(np.uint8), cs

# Crystal accents: silver-white → ice-blue → cyan → cobalt → silver
ACC_CRYST=[(220,235,255),(140,200,255),(60,200,240),(40,100,200),(220,235,255)]
def accent_at(p):
    seq=[0,1,2,3,4]; x=p*(len(seq)-1); i=min(len(seq)-2,int(x)); t=x-i
    a=np.array(ACC_CRYST[seq[i]]); b=np.array(ACC_CRYST[seq[i+1]]); return tuple((a*(1-t)+b*t).astype(int))

M=json.load(open('/tmp/cryst_meta.json')); NF=M['NF']; WP=M['WP']; FK=M['fk']; NAMES=M['names']; POP=M['pop']
silent="/tmp/cryst_silent.mp4"
wr=imageio_ffmpeg.write_frames(silent,(W,H),fps=FPS,codec="libx264",pix_fmt_in="rgb24",pix_fmt_out="yuv420p",macro_block_size=8,output_params=["-crf","20","-preset","medium"])
wr.send(None)
def emit(cv): wr.send(np.ascontiguousarray(np.asarray(cv.convert("RGB"),np.uint8)).tobytes())

NTITLE=84
for f in range(NF):
    p=f/NF; AC=accent_at(p)
    img,cs=render_window(f,NF)
    cv=Image.new("RGBA",(W,H),(*BG,255)); cv.paste(Image.fromarray(img),(WX,WY))
    d=ImageDraw.Draw(cv)
    # Elegant thin reticle — diamond corners
    for cx2,cy2 in[(WX,WY),(WX+WIN,WY),(WX,WY+WIN),(WX+WIN,WY+WIN)]:
        d.line([(cx2-24,cy2),(cx2+24,cy2)],fill=(*AC,90),width=1)
        d.line([(cx2,cy2-24),(cx2,cy2+24)],fill=(*AC,90),width=1)
    d.rectangle([WX-1,WY-1,WX+WIN,WY+WIN],outline=(*AC,40),width=1)

    if f<NTITLE:
        g2=min(1,f/16)*min(1,(NTITLE-1-f)/16)
        ov=Image.new("RGBA",(W,H),(0,0,0,int(170*g2))); cv.alpha_composite(ov)
        text(cv,(W//2,150),sp("mineral intelligence"),F_mono(22),DIM,0.6*g2)
        text(cv,(W//2,560),"CRYSTALLOGENESIS",F_disp(80),BONE,g2)
        text(cv,(W//2,680),"nucleation · branching · lattice",F_disp(44),AC,g2)
        text(cv,(W//2,1240),sp("gray–scott · coral & labyrinth · macro zoom"),F_mono(20),DIM,0.7*g2)
    else:
        text(cv,(W//2,150),"▶  "+sp("live"),F_monob(24),AC,0.65)
        nm=NAMES[f]; text(cv,(W//2,250),nm.upper(),F_disp(70),BONE,1.0)
        text(cv,(W//2,320),sp("crystal morphology"),F_mono(18),DIM,0.5)

        sx=WX+8; sy=WY+WIN+40
        d.line([(sx,sy),(sx+140,sy)],fill=(*BONE,180),width=2)
        for xx in (sx,sx+140): d.line([(xx,sy-6),(xx,sy+6)],fill=(*BONE,180),width=2)
        text(cv,(sx+70,sy+24),f"{int(150/WIN*cs)} cells",F_mono(20),DIM,0.8)
        text(cv,(WX+WIN-8,sy+12),sp(f"F {FK[f][0]:.4f} · k {FK[f][1]:.4f}"),F_mono(19),AC,0.85,anc="rm")
        text(cv,(WX+WIN-8,sy+42),sp(f"generation {f*10:,}"),F_mono(17),DIM,0.6,anc="rm")
        text(cv,(W//2,1880),sp("cellautomata · web8 · mineral growth"),F_mono(17),DIM,0.45)

    emit(cv)

wr.close(); print("composited")
total=NF/FPS; out="/tmp/web8_crystallogenesis.mp4"
# Crystal tones: pure fifths — 55/82/165 Hz (resonant mineral)
af=f"[1:a][2:a][3:a]amix=inputs=3,volume=0.10,lowpass=f=450,afade=t=in:st=0:d=3,afade=t=out:st={total-3.5:.1f}:d=3.5[a]"
subprocess.run([FF,"-y","-hide_banner","-loglevel","error","-i",silent,
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=55:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=82:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=165:sample_rate=44100",
 "-filter_complex",af,"-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","144k","-shortest","-movflags","+faststart",out],check=True)
print(f"-> {out}  {os.path.getsize(out)/1e6:.1f} MB  {total:.1f}s")
