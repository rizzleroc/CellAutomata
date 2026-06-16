"""TERRA — morphogenetic cartography. Hypsometric tint + contour isolines, diagonal survey pan.
Smoke test:  python3 terra_film.py test 470   /   chrome: python3 terra_film.py testc 470
Full render: python3 terra_film.py"""
import json, os, sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
W,H=1080,1920; FPS=24; WIN=1000; WX=(W-WIN)//2; WY=380
BG=(6,9,14); BONE=(226,228,224); DIM=(120,134,134)
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
    f=open('/tmp/terra_field.bin','rb'); f.seek(idx*SZF)
    a=np.frombuffer(f.read(SZF),np.uint16).reshape(1000,1000).astype(np.float32)/65535.0; f.close(); return a
# ---- hypsometric palettes (ocean -> shelf -> coast -> lowland -> highland -> mountain -> snow)
def make_lut(stops):
    xs=np.linspace(0,1,len(stops)); out=np.zeros((256,3),np.float32); t=np.linspace(0,1,256)
    for c in range(3): out[:,c]=np.interp(t,xs,[s[c] for s in stops])
    return out
LUT_VERDANT=make_lut([(8,20,55),(22,72,122),(60,134,160),(210,200,150),(96,152,84),(140,140,72),(120,94,62),(240,242,246)])
LUT_ARID   =make_lut([(10,18,46),(28,68,104),(74,128,140),(214,190,138),(150,150,84),(168,138,72),(132,92,58),(242,240,236)])
PALS=[LUT_VERDANT,LUT_ARID]
def palette_at(p):  # verdant -> arid -> verdant (seasonal drift)
    seq=[0,1,0]; x=p*(len(seq)-1); i=min(len(seq)-2,int(x)); t=x-i
    return PALS[seq[i]]*(1-t)+PALS[seq[i+1]]*t
NB=14  # contour intervals
def topo(h01, lut):
    he=np.clip((h01-0.02)*2.2,0,1)                 # stretch so voids read as ocean, ridges as highland/snow
    gy,gx=np.gradient(h01)
    lx,ly,lz=-0.55,-0.50,0.68; nz=1.0/3.2
    inv=1.0/np.sqrt(gx*gx+gy*gy+nz*nz)
    shade=np.clip((gx*lx+gy*ly+nz*lz)*inv,0,1)
    idx=np.clip(he*255,0,255).astype(np.int32)
    col=lut[idx]*(0.55+0.50*shade)[...,None]       # matte terrain (little gloss)
    spec=np.clip(shade-0.80,0,1)*4.0*np.clip(he-0.86,0,1)
    col+=spec[...,None]*np.array([245,248,252],np.float32)   # snow glint on the peaks only
    band=np.floor(he*NB).astype(np.int32)          # contour isolines
    edge=np.zeros(he.shape,bool)
    edge[:,1:]|=band[:,1:]!=band[:,:-1]; edge[1:,:]|=band[1:,:]!=band[:-1,:]
    col[edge]*=0.52
    col[(band%4==0)&edge]*=0.74                     # index (major) contours darker
    return np.clip(col,0,255).astype(np.uint8)
def vig(n):
    yy,xx=np.mgrid[0:n,0:n]; r=np.hypot((xx-n/2)/(n/2),(yy-n/2)/(n/2))
    return np.clip(1-0.40*np.clip(r-0.60,0,1)**1.6,0,1).astype(np.float32)[...,None]
VIG=vig(WIN)
def lerp(a,b,t): return a+(b-a)*t
def cropresize(field,cs,ccx,ccy):
    cs=int(round(max(150,min(1000,cs)))); x=int(round(ccx-cs/2)); y=int(round(ccy-cs/2))
    x=max(0,min(1000-cs,x)); y=max(0,min(1000-cs,y))
    sub=field[y:y+cs,x:x+cs]
    im=Image.fromarray(sub,mode='F').resize((WIN,WIN),Image.LANCZOS)
    return np.asarray(im,np.float32)
def camera(f,NF):
    # Steady DIAGONAL survey sweep at near-constant moderate zoom (the cartographer reading the plate).
    p=f/NF
    cs=lerp(720,560,0.5-0.5*np.cos(p*np.pi*2.0))
    margin=(1000-cs)/2*0.82; env=np.sin(np.pi*p)**0.5
    ccx=500+margin*0.85*np.sin(p*np.pi*1.0-np.pi/2)*env    # full left -> right
    ccy=500+margin*0.85*np.sin(p*np.pi*0.8-np.pi/2)*env    # top -> bottom (diagonal)
    return cs,ccx,ccy
def render_window(f,NF):
    field=readfield(f); cs,ccx,ccy=camera(f,NF)
    h01=cropresize(field,cs,ccx,ccy)
    img=topo(h01,palette_at(f/NF)).astype(np.float32)*VIG
    return np.clip(img,0,255).astype(np.uint8), cs, ccx, ccy
ACC=[(224,176,96),(96,178,176),(214,150,80),(96,178,176),(224,176,96)]
def accent_at(p):
    x=p*(len(ACC)-1); i=min(len(ACC)-2,int(x)); t=x-i
    a=np.array(ACC[i]); b=np.array(ACC[i+1]); return tuple((a*(1-t)+b*t).astype(int))
def graticule(d,x,y,n,AC,a=1.0):
    d.rectangle([x-1,y-1,x+n,y+n],outline=(*AC,int(80*a)),width=1)
    for i in range(1,8):                              # edge ticks = a survey graticule
        gx=x+n*i/8; gy=y+n*i/8
        d.line([(gx,y),(gx,y+10)],fill=(*AC,int(90*a)),width=1); d.line([(gx,y+n-10),(gx,y+n)],fill=(*AC,int(90*a)),width=1)
        d.line([(x,gy),(x+10,gy)],fill=(*AC,int(90*a)),width=1); d.line([(x+n-10,gy),(x+n,gy)],fill=(*AC,int(90*a)),width=1)
def compass(cv,d,cx,cy,AC):
    d.ellipse([cx-22,cy-22,cx+22,cy+22],outline=(*AC,150),width=1)
    d.polygon([(cx,cy-20),(cx-6,cy+4),(cx+6,cy+4)],fill=(*AC,200))      # north arrow
    d.polygon([(cx,cy+20),(cx-6,cy-4),(cx+6,cy-4)],fill=(*BONE,70))
    text(cv,(cx,cy-34),"N",F_monob(18),AC,0.9)
NTITLE=84
def compose_frame(f,NF,NAMES,FK):
    p=f/NF; AC=accent_at(p)
    img,cs,ccx,ccy=render_window(f,NF)
    cv=Image.new("RGBA",(W,H),(*BG,255)); cv.paste(Image.fromarray(img),(WX,WY))
    d=ImageDraw.Draw(cv); graticule(d,WX,WY,WIN,AC,1.0)
    if f<NTITLE:
        g=min(1,f/16)*min(1,(NTITLE-1-f)/16); ov=Image.new("RGBA",(W,H),(0,0,0,int(150*g))); cv.alpha_composite(ov)
        text(cv,(W//2,150),sp("morphogenetic cartography"),F_mono(22),DIM,0.6*g)
        text(cv,(W//2,560),"TERRA",F_disp(124),BONE,g)
        text(cv,(W//2,690),"reading the field as living terrain",F_disp(42),AC,g)
        label(cv,(W//2,1240),"gray–scott · hypsometric tint · 14 contour intervals",20,DIM,0.7*g)
    else:
        text(cv,(W//2,150),sp("survey plate"),F_mono(20),DIM,0.55)
        nm=NAMES[f]; text(cv,(W//2,250),nm.upper(),F_disp(70),BONE,1.0)
        text(cv,(W//2,320),sp("terrain morphology"),F_mono(18),DIM,0.5)
        compass(cv,d,WX+44,WY+44,AC)
        sx=WX+8; sy=WY+WIN+40; bar_km=0.15*cs               # 1 cell = 1 km
        d.line([(sx,sy),(sx+150,sy)],fill=(*BONE,200),width=2)
        for xx in (sx,sx+150): d.line([(xx,sy-6),(xx,sy+6)],fill=(*BONE,200),width=2)
        text(cv,(sx+75,sy+24),f"{bar_km:.0f} km",F_mono(20),DIM,0.8)
        lat=12+ (1-ccy/1000)*46; lon=8+ ccx/1000*64          # decorative survey reference
        text(cv,(WX+WIN-8,sy+12),sp(f"{lat:04.1f}°N · {lon:04.1f}°E"),F_mono(19),AC,0.85,anc="rm")
        text(cv,(WX+WIN-8,sy+42),sp(f"elev gen {f*10:,}"),F_mono(17),DIM,0.6,anc="rm")
        label(cv,(W//2,1880),"cellautomata · web8 · terra survey · contour interval 60 m",17,DIM,0.45)
    return cv
if __name__=='__main__' and len(sys.argv)>2 and sys.argv[1]=='test':
    M=json.load(open('/tmp/terra_meta.json')); img,cs,_,_=render_window(int(sys.argv[2]),M['NF'])
    Image.fromarray(img).save('/tmp/terra_test.png'); print("test frame saved cs",cs); sys.exit()
if __name__=='__main__' and len(sys.argv)>2 and sys.argv[1]=='testc':
    M=json.load(open('/tmp/terra_meta.json'))
    compose_frame(int(sys.argv[2]),M['NF'],M['names'],M['fk']).convert("RGB").save('/tmp/terra_testc.png'); print("chrome frame saved"); sys.exit()
# ===== FULL RENDER =====
M=json.load(open('/tmp/terra_meta.json')); NF=M['NF']; FK=M['fk']; NAMES=M['names']
silent="/tmp/terra_silent.mp4"
wr=imageio_ffmpeg.write_frames(silent,(W,H),fps=FPS,codec="libx264",pix_fmt_in="rgb24",pix_fmt_out="yuv420p",macro_block_size=8,output_params=["-crf","20","-preset","medium"])
wr.send(None)
def emit(cv): wr.send(np.ascontiguousarray(np.asarray(cv.convert("RGB"),np.uint8)).tobytes())
for f in range(NF):
    emit(compose_frame(f,NF,NAMES,FK))
wr.close(); print("composited")
total=NF/FPS; out="/tmp/web8_terra.mp4"
# Earthy drone: 41 / 61 / 82 Hz, lowpassed — the low hum of a survey room.
fade=min(3.5,total/3); fin=min(3.0,total/3); fo=max(0.0,total-fade)
af=f"[1:a][2:a][3:a]amix=inputs=3,volume=0.11,lowpass=f=440,afade=t=in:st=0:d={fin:.2f},afade=t=out:st={fo:.2f}:d={fade:.2f}[a]"
subprocess.run([FF,"-y","-hide_banner","-loglevel","error","-i",silent,
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=41:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=61:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=82:sample_rate=44100",
 "-filter_complex",af,"-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","144k","-shortest","-movflags","+faststart",out],check=True)
print(f"-> {out}  {os.path.getsize(out)/1e6:.1f} MB  {total:.1f}s")
