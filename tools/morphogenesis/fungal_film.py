"""FUNGAL — an ontogeny. The development of one organism, told stage by stage: a single spore
breaks dormancy, branches into a body, fuses into an individual, fruits, and casts the spores that
begin it again. Visual field/camera/palette unchanged from the specimen cut — this cut adds the story.
Smoke test one frame:  python3 fungal_film.py testc 200    Full render: python3 fungal_film.py"""
import json, os, sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
W,H=1080,1920; FPS=24; WIN=1000; WX=(W-WIN)//2; WY=380
BG=(5,4,3); BONE=(236,226,206); DIM=(126,112,92)
FB="docs/web8/assets/fonts/"
def fnt(n,s):
    p=FB+n; return ImageFont.truetype(p,s) if os.path.exists(p) else ImageFont.load_default()
F_disp=lambda s: fnt("Italiana-Regular.ttf",s)
F_mono=lambda s: fnt("IBMPlexMono-Regular.ttf",s)
F_monob=lambda s: fnt("IBMPlexMono-Bold.ttf",s)
F_ital=lambda s: fnt("CrimsonPro-Italic.ttf",s)
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
def wrapped(cv,xy,s,f,fill,a,maxw,lh):
    if a<=0.01: return
    words=s.split(); lines=[]; cur=""; d=ImageDraw.Draw(cv)
    for w in words:
        t=(cur+" "+w).strip()
        if d.textlength(t,font=f)<=maxw: cur=t
        else: lines.append(cur); cur=w
    if cur: lines.append(cur)
    y0=xy[1]-(len(lines)-1)*lh/2
    for i,ln in enumerate(lines): text(cv,(xy[0],y0+i*lh),ln,f,fill,a)
ROMAN=[(10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]
def roman(n):
    s=''
    for v,sym in ROMAN:
        while n>=v: s+=sym; n-=v
    return s
SZF=1000*1000*2
def readfield(idx):
    f=open('/tmp/fungal_field.bin','rb'); f.seek(idx*SZF)
    a=np.frombuffer(f.read(SZF),np.uint16).reshape(1000,1000).astype(np.float32)/65535.0; f.close(); return a
# ---- fungal palettes: dark humus / ivory mycelium / amber fruiting / foxfire spores ----
def make_lut(stops):
    xs=np.linspace(0,1,len(stops)); out=np.zeros((256,3),np.float32); t=np.linspace(0,1,256)
    for c in range(3): out[:,c]=np.interp(t,xs,[s[c] for s in stops])
    return out
LUT_SUBST=make_lut([(4,3,2),(14,10,7),(30,22,15),(58,44,30),(96,78,54),(154,132,100),(214,198,166)])
LUT_MYCEL=make_lut([(6,6,5),(18,16,13),(40,36,29),(82,76,62),(140,132,112),(200,194,174),(240,238,224)])
LUT_FRUIT=make_lut([(8,5,3),(30,17,9),(66,36,17),(112,66,30),(164,102,46),(210,154,82),(240,208,150)])
LUT_FOXF =make_lut([(2,5,3),(6,22,11),(14,50,24),(30,92,44),(78,156,78),(156,216,124),(222,250,192)])
PALS=[LUT_SUBST,LUT_MYCEL,LUT_FRUIT,LUT_FOXF]
def palette_at(p):
    seq=[0,1,1,1,2,2,3,0]; x=p*(len(seq)-1); i=min(len(seq)-2,int(x)); t=x-i
    return PALS[seq[i]]*(1-t)+PALS[seq[i+1]]*t
def relief(h01, lut, strength=3.6):
    gy,gx=np.gradient(h01)
    lx,ly,lz=-0.50,-0.55,0.66
    nz=1.0/strength
    inv=1.0/np.sqrt(gx*gx+gy*gy+nz*nz)
    shade=np.clip((gx*lx+gy*ly+nz*lz)*inv,0,1)
    idx=np.clip((h01*255),0,255).astype(np.int32)
    base=lut[idx]
    col=base*(0.40+0.72*shade)[...,None]
    spec=np.clip(shade-0.80,0,1)*5.0*np.clip(h01-0.30,0,1)
    col+=spec[...,None]*np.array([250,238,208],np.float32)
    return np.clip(col,0,255).astype(np.uint8)
def vig(n):
    yy,xx=np.mgrid[0:n,0:n]; r=np.hypot((xx-n/2)/(n/2),(yy-n/2)/(n/2))
    return np.clip(1-0.54*np.clip(r-0.48,0,1)**1.9,0,1).astype(np.float32)[...,None]
VIG=vig(WIN)
def lerp(a,b,t): return a+(b-a)*t
def ease(z): return 0.5-0.5*np.cos(np.clip(z,0,1)*np.pi)
def cropresize(field,cs,ccx,ccy):
    cs=int(round(max(150,min(1000,cs)))); x=int(round(ccx-cs/2)); y=int(round(ccy-cs/2))
    x=max(0,min(1000-cs,x)); y=max(0,min(1000-cs,y))
    sub=field[y:y+cs,x:x+cs]
    im=Image.fromarray(sub,mode='F').resize((WIN,WIN),Image.LANCZOS)
    return np.asarray(im,np.float32)
def camera(f,NF):
    p=f/NF; climax=0.72
    cs=lerp(760,340,ease(p/climax)) if p<climax else lerp(340,560,ease((p-climax)/(1-climax)))
    margin=(1000-cs)/2*0.80
    env=np.sin(np.pi*p)**0.5
    ccx=500+margin*0.90*np.sin(p*np.pi*1.1-np.pi/2)*env
    ccy=500+margin*0.60*np.sin(p*np.pi*0.7)*env
    return cs,ccx,ccy
def render_window(f,NF):
    field=readfield(f); cs,ccx,ccy=camera(f,NF)
    h01=cropresize(field,cs,ccx,ccy)
    img=relief(h01,palette_at(f/NF)).astype(np.float32)*VIG
    return np.clip(img,0,255).astype(np.uint8), cs, float(h01.mean())
ACC=[(206,170,116),(168,196,150),(224,186,120),(150,212,120),(206,170,116)]
def accent_at(p):
    x=p*(len(ACC)-1); i=min(len(ACC)-2,int(x)); t=x-i
    a=np.array(ACC[i]); b=np.array(ACC[i+1]); return tuple((a*(1-t)+b*t).astype(int))
def reticle(d,x,y,n,AC,a=1.0):
    for cx,cy in[(x,y),(x+n,y),(x,y+n),(x+n,y+n)]:
        d.line([(cx-18,cy),(cx+18,cy)],fill=(*AC,int(110*a)),width=1)
        d.line([(cx,cy-18),(cx,cy+18)],fill=(*AC,int(110*a)),width=1)
def progress(cv,i,n,acc,a=1.0):
    d=ImageDraw.Draw(cv); y=1800; gap=26; x0=W//2-(n-1)*gap//2
    for j in range(n):
        x=x0+j*gap; r=5 if j==i else 3; fill=acc if j==i else DIM
        d.ellipse([x-r,y-r,x+r,y+r],fill=(*fill,int((255 if j==i else 110)*a)))
# ---- THE STORY: one organism's ontogeny, a line per developmental stage ----
ORDER=['germination','hyphae','mycelium','anastomosis','primordia','fruiting','sporulation','humus']
STORY={
 'germination':("Germination","A single spore breaks dormancy. From one cell, a germ tube probes the dark."),
 'hyphae':      ("Hyphae","The tube extends and branches into hyphae — each tip a mouth, feeling outward for food."),
 'mycelium':    ("Mycelium","Hyphae multiply into a mycelium: a body that is all surface, all growth, with no centre."),
 'anastomosis': ("Anastomosis","Filaments meet and fuse. The scattered threads resolve into one connected individual."),
 'primordia':   ("Primordia","Where the network runs richest, knots condense — primordia, the promise of a fruiting body."),
 'fruiting':    ("Fruiting body","A primordium differentiates and rises. The mushroom — the organism's one visible act — takes form."),
 'sporulation': ("Sporulation","The cap matures and opens, casting millions of spores out into the dark."),
 'humus':       ("Humus","The body melts back into the soil it fed on — and in every spore, the ontogeny begins again."),
}
def actno(name): return ORDER.index(name)+1
SEG_G=7; FADEU=22
def stage_alpha(f,NF):
    spf=f/NF*SEG_G; si=int(round(spf))
    db=min(abs(spf-(si-0.5)),abs(spf-(si+0.5)))
    edge=FADEU/(NF/SEG_G)
    return max(0.0,min(1.0,db/edge))
NTITLE=90; OUTRO=108
def compose_frame(f,NF,NAMES,FK):
    p=f/NF; AC=accent_at(p)
    img,cs,lum=render_window(f,NF)
    cv=Image.new("RGBA",(W,H),(*BG,255)); cv.paste(Image.fromarray(img),(WX,WY))
    d=ImageDraw.Draw(cv); reticle(d,WX,WY,WIN,AC,1.0)
    # ---------- TITLE ----------
    if f<NTITLE:
        g=min(1,f/18)*min(1,(NTITLE-1-f)/16); ov=Image.new("RGBA",(W,H),(0,0,0,int(185*g))); cv.alpha_composite(ov)
        text(cv,(W//2,150),sp("a fungal ontogeny"),F_mono(23),DIM,0.6*g)
        text(cv,(W//2,548),"MYCELIUM",F_disp(118),BONE,g)
        text(cv,(W//2,676),"the life of a single organism",F_disp(44),AC,g)
        text(cv,(W//2,792),"on·tog·e·ny — how one body unfolds, from spore to spore",F_ital(35),DIM,0.9*g)
        label(cv,(W//2,1240),"gray–scott · branching hyphae · coral → u-skate",20,DIM,0.7*g)
        return cv
    # ---------- CODA ----------
    if f>=NF-OUTRO:
        lf=f-(NF-OUTRO); g=min(1,lf/18)*min(1,(OUTRO-1-lf)/16)
        ov=Image.new("RGBA",(W,H),(0,0,0,int(205*g))); cv.alpha_composite(ov)
        text(cv,(W//2,560),sp("the cycle closes"),F_mono(22),DIM,0.6*g)
        text(cv,(W//2,712),"and in every spore",F_disp(58),BONE,g)
        text(cv,(W//2,792),"it begins again",F_disp(58),AC,g)
        text(cv,(W//2,1240),sp("one organism · spore to spore"),F_mono(18),DIM,0.55*g)
        label(cv,(W//2,1880),"cellautomata · web8 · mycelium · an ontogeny",16,DIM,0.45)
        return cv
    # ---------- LIVE: the developing organism ----------
    capA=stage_alpha(f,NF); nm=NAMES[f]; head,cap=STORY.get(nm,(nm.title(),""))
    text(cv,(W//2,138),sp("a fungal ontogeny"),F_mono(19),DIM,0.42)
    text(cv,(W//2,236),roman(actno(nm)),F_disp(54),AC,0.85*max(0.45,capA))   # act numeral
    text(cv,(W//2,308),head.upper(),F_disp(60),BONE,max(0.5,capA))            # stage name
    text(cv,(W//2,1410),sp(f"F {FK[f][0]:.4f}    k {FK[f][1]:.4f}    biomass {lum*100:4.1f}%"),F_mono(16),DIM,0.40)
    wrapped(cv,(W//2,1560),cap,F_ital(39),BONE,capA,W-150,50)                 # the narration
    progress(cv,ORDER.index(nm),len(ORDER),AC,1.0)
    label(cv,(W//2,1880),"cellautomata · web8 · mycelium · an ontogeny",16,DIM,0.42)
    return cv
if __name__=='__main__' and len(sys.argv)>2 and sys.argv[1]=='test':
    M=json.load(open('/tmp/fungal_meta.json')); SEG_G=M['SEG']; img,cs,_=render_window(int(sys.argv[2]),M['NF'])
    Image.fromarray(img).save('/tmp/fungal_test.png'); print("test frame saved cs",cs); sys.exit()
if __name__=='__main__' and len(sys.argv)>2 and sys.argv[1]=='testc':
    M=json.load(open('/tmp/fungal_meta.json')); SEG_G=M['SEG']
    compose_frame(int(sys.argv[2]),M['NF'],M['names'],M['fk']).convert("RGB").save('/tmp/fungal_testc.png'); print("chrome frame saved"); sys.exit()
# ===== FULL RENDER =====
M=json.load(open('/tmp/fungal_meta.json')); NF=M['NF']; FK=M['fk']; NAMES=M['names']; SEG_G=M['SEG']
silent="/tmp/fungal_silent.mp4"
wr=imageio_ffmpeg.write_frames(silent,(W,H),fps=FPS,codec="libx264",pix_fmt_in="rgb24",pix_fmt_out="yuv420p",macro_block_size=8,output_params=["-crf","20","-preset","medium"])
wr.send(None)
def emit(cv): wr.send(np.ascontiguousarray(np.asarray(cv.convert("RGB"),np.uint8)).tobytes())
for f in range(NF):
    emit(compose_frame(f,NF,NAMES,FK))
wr.close(); print("composited")
total=NF/FPS; out="/tmp/web8_fungal.mp4"
fade=min(3.5,total/3); fin=min(3.0,total/3); fo=max(0.0,total-fade)
af=f"[1:a][2:a][3:a]amix=inputs=3,volume=0.11,lowpass=f=420,afade=t=in:st=0:d={fin:.2f},afade=t=out:st={fo:.2f}:d={fade:.2f}[a]"
subprocess.run([FF,"-y","-hide_banner","-loglevel","error","-i",silent,
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=40:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=60:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=90:sample_rate=44100",
 "-filter_complex",af,"-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","144k","-shortest","-movflags","+faststart",out],check=True)
print(f"-> {out}  {os.path.getsize(out)/1e6:.1f} MB  {total:.1f}s")
