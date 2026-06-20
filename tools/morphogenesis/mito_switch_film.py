import json, os, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
W,H=1080,1920; FPS=24; WIN=1000; WX=(W-WIN)//2; WY=380
BG=(8,10,15); BONE=(232,226,212); DIM=(140,146,158)
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
M=json.load(open('/tmp/ms_meta.json')); GW,GH=M['W'],M['H']; NF=M['NF']; FLIP1=M['FLIP1']; FLIP2=M['FLIP2']; POP=M['pop']
SZF=GW*GH*4; fbin=open('/tmp/ms_field.bin','rb')
def readf(idx):
    fbin.seek(idx*SZF); return np.frombuffer(fbin.read(SZF),np.uint8).reshape(GH,GW,4)[...,:3]
def vig(n):
    yy,xx=np.mgrid[0:n,0:n]; r=np.hypot((xx-n/2)/(n/2),(yy-n/2)/(n/2))
    return np.clip(1-0.40*np.clip(r-0.58,0,1)**1.6,0,1).astype(np.float32)[...,None]
VIG=vig(WIN)
def smooth(t): return t*t*(3-2*t)
def lerp(a,b,t): return a+(b-a)*t
def view(arr,cs,ccx,ccy):
    cs=int(round(max(120,min(GW,cs)))); x=int(round(ccx-cs/2)); y=int(round(ccy-cs/2))
    x=max(0,min(GW-cs,x)); y=max(0,min(GH-cs,y))
    crop=np.ascontiguousarray(arr[y:y+cs,x:x+cs])
    im=Image.fromarray(crop).resize((WIN,WIN),Image.LANCZOS)
    out=np.clip(np.asarray(im,np.float32)*VIG,0,255).astype(np.uint8); return Image.fromarray(out)
# phases
PH=[('MITOSIS',0.0367,0.0649,(226,178,116)),('LABYRINTH',0.039,0.058,(96,208,150)),('WAVES',0.026,0.051,(122,186,234))]
CHIPS=['MITOSIS','LABYRINTH','WAVES']
def phase(f): return 0 if f<FLIP1 else (1 if f<FLIP2 else 2)
def cam(f):
    if f<FLIP1:
        p=f/FLIP1; cs=lerp(360,780,smooth(p)); cx=500+26*np.sin(f/55); cy=500
    elif f<FLIP2:
        p=(f-FLIP1)/(FLIP2-FLIP1); cs=lerp(720,600,smooth(p)); cx=500+40*np.sin(f/60); cy=485
    else:
        p=(f-FLIP2)/(NF-FLIP2); cs=lerp(600,710,smooth(p)); cx=500; cy=500+34*np.sin(f/55)
    for S in (FLIP1,FLIP2):
        if S<=f<S+14: cs*= (0.80+0.20*((f-S)/14))   # zoom-punch on the flip
    return cs,cx,cy
def reticle(d,x,y,n,AC,a=1.0):
    for cx,cy in[(x,y),(x+n,y),(x,y+n),(x+n,y+n)]:
        d.line([(cx-22,cy),(cx+22,cy)],fill=(*AC,int(150*a)),width=1); d.line([(cx,cy-22),(cx,cy+22)],fill=(*AC,int(150*a)),width=1)
    d.rectangle([x-1,y-1,x+n,y+n],outline=(*AC,int(75*a)),width=1)
def selector(cv,active,AC,flash=0.0):
    d=ImageDraw.Draw(cv); n=3; x0=90; tot=W-180; cw=tot/n
    text(cv,(W//2,250),sp("rule"),F_mono(18),DIM,0.55)
    for i,name in enumerate(CHIPS):
        cx=x0+cw*(i+0.5); on=(i==active)
        col=BONE if on else DIM
        text(cv,(cx,300),name,F_mono(26 if on else 22),col,1.0 if on else 0.5)
        if on:
            wln=d.textlength(name,font=F_mono(26)); bw=(0.6+0.4*flash)
            d.line([(cx-wln/2,322),(cx+wln/2,322)],fill=(*AC,int(255*bw)),width=4)
        if i<n-1:
            ar=("▸") ; text(cv,(x0+cw*(i+1),300),ar,F_mono(20),DIM,0.4)
silent="/tmp/msw_silent.mp4"
wr=imageio_ffmpeg.write_frames(silent,(W,H),fps=FPS,codec="libx264",pix_fmt_in="rgb24",pix_fmt_out="yuv420p",macro_block_size=8,output_params=["-crf","20","-preset","medium"])
wr.send(None)
def emit(cv): wr.send(np.ascontiguousarray(np.asarray(cv.convert("RGB"),np.uint8)).tobytes())
def badge(k): return 0.55+0.45*(0.5+0.5*np.sin(2*np.pi*(k/FPS)/2.2))
CAPS={0:"one spot becomes two — two become four — mitosis fills the dish.",
      1:"flip the switch: feed & kill change live — the dividing spots reach out and weave a maze.",
      2:"flip again: the maze comes apart into living turbulence — the same field, never the same twice."}
NTITLE=72
for f in range(NF):
    ph=phase(f); name,F,k,AC=PH[ph]; cs,cx,cy=cam(f)
    arr=readf(f).astype(np.float32)
    if ph==1: arr=np.clip(arr*1.7,0,255)        # lift the dark viridis labyrinth
    base=view(arr.astype(np.uint8),cs,cx,cy)
    cv=Image.new("RGBA",(W,H),(*BG,255)); cv.paste(base,(WX,WY))
    d=ImageDraw.Draw(cv); reticle(d,WX,WY,WIN,AC,1.0)
    # flip flash
    flash=0.0
    for S in (FLIP1,FLIP2):
        if S<=f<S+8: flash=max(flash,1.0-(f-S)/8)
    if flash>0.01:
        ov=Image.new("RGBA",(W,H),(*AC,int(105*flash))); cv.alpha_composite(ov)
    # title beat
    if f<NTITLE:
        fa=min(1,f/16); fo=min(1,(NTITLE-1-f)/14); g=fa*fo
        ov=Image.new("RGBA",(W,H),(0,0,0,int(150*g)) ); cv.alpha_composite(ov)
        text(cv,(W//2,150),sp("cellautomata · web8 · 1000² field"),F_mono(22),DIM,0.6*g)
        text(cv,(W//2,840),"MITOSIS",F_disp(150),BONE,g)
        text(cv,(W//2,965),"flip the switch — change the rule",F_disp(46),AC,g)
        text(cv,(W//2,1150),sp("grow it · then change feed & kill live"),F_mono(22),DIM,0.7*g)
    else:
        text(cv,(W//2,150),"▶  "+sp("live"),F_monob(26),AC,badge(f))
        selector(cv,ph,AC,flash)
        sx=WX+8; sy=WY+WIN+40
        d.line([(sx,sy),(sx+140,sy)],fill=(*BONE,210),width=2)
        for xx in (sx,sx+140): d.line([(xx,sy-6),(xx,sy+6)],fill=(*BONE,210),width=2)
        cs2=int(150/WIN*cs); text(cv,(sx+70,sy+24),f"{cs2} cells",F_mono(22),DIM,0.85)
        text(cv,(WX+WIN-8,sy+12),sp(f"F {F} · k {k}"),F_mono(20),AC,0.85,anc="rm")
        if POP[f]: text(cv,(WX+WIN-8,sy+44),sp(POP[f]),F_mono(17),DIM,0.6,anc="rm")
        # caption (fade near each phase start)
        pstart=[0,FLIP1,FLIP2][ph]; into=f-pstart; cfa=min(1.0,into/24)*min(1.0,( [FLIP1,FLIP2,NF][ph]-f)/40)
        capl="\n".join(wrap(d,CAPS[ph],F_disp(40),W-150))
        text(cv,(W//2,1640),capl,F_disp(40),BONE,0.95*max(0,cfa),spc=12)
        text(cv,(W//2,1866),sp("cellautomata · web8 · one field, live rule-flips"),F_mono(18),DIM,0.5)
    emit(cv)
wr.close(); print("composited")
total=NF/FPS
out="/tmp/web8_mitosis_switch_1000.mp4"
af=f"[1:a][2:a][3:a]amix=inputs=3,volume=0.13,lowpass=f=520,afade=t=in:st=0:d=2.5,afade=t=out:st={total-3:.1f}:d=3[a]"
subprocess.run([FF,"-y","-hide_banner","-loglevel","error","-i",silent,
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=56:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=84:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=168:sample_rate=44100",
 "-filter_complex",af,"-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","144k","-shortest","-movflags","+faststart",out],check=True)
print(f"-> {out}  {os.path.getsize(out)/1e6:.1f} MB  {total:.1f}s")
