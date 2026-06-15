"""ORIGIN HOOK — a scroll-stopping intro prepended to web8_origins.mp4. Opens on the ending
image (the newborn) — "THIS IS YOU" — then rewinds the whole arc (fetus → cells → chemistry →
ancestor → a Conway grid) and punches "FROM A RULE, TO YOU · WATCH" before the reel plays it
forward. Built locally from stills sampled out of the reel. -> /tmp/web8_origins_hooked.mp4
"""
import os, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
W,H,FPS=1080,1920,24
BG=(7,8,12); BONE=(236,231,218); TEAL=(116,244,231); DIM=(150,150,162)
FB="docs/web8/assets/fonts/"
def fnt(n,s): p=FB+n; return ImageFont.truetype(p,s) if os.path.exists(p) else ImageFont.load_default()
F_disp=lambda s: fnt("Italiana-Regular.ttf",s)
F_mono=lambda s: fnt("IBMPlexMono-Regular.ttf",s)
F_monob=lambda s: fnt("IBMPlexMono-Bold.ttf",s)
F_ital=lambda s: fnt("CrimsonPro-Italic.ttf",s)
def text(cv,xy,s,f,fill,a=1.0,anc="mm"):
    if a<=0.01: return
    ov=Image.new("RGBA",cv.size,(0,0,0,0))
    ImageDraw.Draw(ov).text(xy,s,font=f,fill=(*fill,int(255*min(1,a))),anchor=anc)
    cv.alpha_composite(ov)
def spc(s,g="  "): return g.join(list(s.upper()))
def loadspec(name):
    a=np.asarray(Image.open(f'/tmp/hk_{name}.png').convert("RGB"))
    return Image.fromarray(a[400:1400,40:1040])     # just the specimen window (no tour chrome)
SPECS={n:loadspec(n) for n in ['baby','fetus','cells','gs','luca','conway']}
def vig_overlay():
    yy,xx=np.mgrid[0:H,0:W]
    r=np.hypot((xx-W/2)/(W*0.66),(yy-820)/(H*0.46))
    al=(np.clip(r-0.5,0,1)**1.6*220).astype(np.uint8)
    ov=np.zeros((H,W,4),np.uint8); ov[...,3]=al
    return Image.fromarray(ov,"RGBA")
VIGOV=vig_overlay()
SCRIM=None
def scrim():
    global SCRIM
    if SCRIM is None:
        s=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(s)
        d.rectangle([0,0,W,500],fill=(7,8,12,140)); d.rectangle([0,1440,W,H],fill=(7,8,12,165))
        SCRIM=s
    return SCRIM
def place(cv,name,scale=1.06,cy=860):
    side=int(W*scale)
    im=SPECS[name].resize((side,side),Image.LANCZOS)
    cv.paste(im,((W-side)//2,int(cy-side/2)))
    cv.alpha_composite(VIGOV); cv.alpha_composite(scrim())
NF_HOOK=162
CUTS=[('fetus','a fetus'),('cells','a clump of cells'),('gs','raw chemistry'),
      ('luca','one ancestor'),('conway','a rule on a grid')]
def compose_hook(f):
    cv=Image.new("RGBA",(W,H),(*BG,255))
    if f<52:                                   # the newborn — "this is you"
        place(cv,'baby',1.04+0.06*(f/52))
        text(cv,(W//2,300),"THIS IS YOU.",F_disp(118),BONE,min(1,max(0,(f-5)/10)))
        if f>=34: text(cv,(W//2,1560),"but you began as —",F_ital(50),DIM,min(1,(f-34)/9))
    elif f<112:                                # rewind through the arc
        idx=min(4,(f-52)//12); lf=(f-52)-idx*12; name,lbl=CUTS[idx]
        place(cv,name,1.06+0.05*(lf/12))
        a=min(1,lf/3)*min(1,(12-lf)/3)
        text(cv,(W//2,1560),spc(lbl),F_mono(34),TEAL if idx==4 else BONE,0.92*a)
        text(cv,(W//2,300),spc("rewinding"),F_mono(20),DIM,0.45*a)
    elif f<134:                                # land on the rule
        place(cv,'conway',1.06+0.04*((f-112)/22))
        text(cv,(W//2,1540),"it began as a game.",F_disp(60),BONE,min(1,(f-112)/8)*min(1,(134-f)/6))
    else:                                       # the punch
        lf=f-134; a=min(1,lf/8)
        text(cv,(W//2,760),"FROM A RULE —",F_disp(74),BONE,a)
        text(cv,(W//2,884),"TO YOU.",F_disp(98),TEAL,a)
        if lf>=12: text(cv,(W//2,1130),spc("watch"),F_monob(42),TEAL,min(1,(lf-12)/6))
    return cv
# ---- render the hook ----
hs="/tmp/hook_silent.mp4"
wr=imageio_ffmpeg.write_frames(hs,(W,H),fps=FPS,codec="libx264",pix_fmt_in="rgb24",pix_fmt_out="yuv420p",macro_block_size=8,output_params=["-crf","19","-preset","medium"])
wr.send(None)
for f in range(NF_HOOK): wr.send(np.ascontiguousarray(np.asarray(compose_hook(f).convert("RGB"),np.uint8)).tobytes())
wr.close()
th=NF_HOOK/FPS
# rising tension drone
af=f"[1:a][2:a][3:a]amix=inputs=3,volume='min(0.24,0.04*t)':eval=frame,lowpass=f=460,afade=t=in:st=0:d=0.6[a]"
subprocess.run([FF,"-y","-hide_banner","-loglevel","error","-i",hs,
 "-f","lavfi","-t",f"{th}","-i","sine=frequency=55:sample_rate=44100",
 "-f","lavfi","-t",f"{th}","-i","sine=frequency=82.5:sample_rate=44100",
 "-f","lavfi","-t",f"{th}","-i","sine=frequency=110:sample_rate=44100",
 "-filter_complex",af,"-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","144k","-shortest","/tmp/hook.mp4"],check=True)
print("hook built",th,"s")
# ---- concat hook + origins ----
out="/tmp/web8_origins_hooked.mp4"
subprocess.run([FF,"-y","-hide_banner","-loglevel","error","-i","/tmp/hook.mp4","-i","/tmp/web8_origins.mp4",
 "-filter_complex","[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]",
 "-map","[v]","-map","[a]","-c:v","libx264","-pix_fmt","yuv420p","-crf","19","-preset","medium",
 "-c:a","aac","-b:a","144k","-movflags","+faststart",out],check=True)
print(f"-> {out}  {os.path.getsize(out)/1e6:.1f} MB")
