"""WILD OUTCOMES — a gallery of the strangest ways a human life can begin, straight from the
ontogeny engine's Outcome panel: identical MCMA, conjoined, 2+1 triplets, quintuplets, triploidy,
trisomy 21, chimerism, the vanishing twin. Each plate develops its real specimen (per-scenario
bins from ontogeny_gen.mjs) under the verdict + the flags that make it wild.
Preview:  python3 wild_film.py test <globalframe>     Full: python3 wild_film.py
"""
import json, os, sys, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
W,H,FPS=1080,1920,24
OB=(7,9,13); PLATE=(10,14,22); INK=(236,231,218); INKS=(203,197,182); MUT=(154,146,128); MUTD=(138,132,116)
TEAL=(63,224,208); TEALB=(116,244,231); MAG=(215,123,255); AMBER=(255,207,107)
HAIR=(236,231,218)
FB="docs/web8/assets/fonts/"
def fnt(n,s): p=FB+n; return ImageFont.truetype(p,s) if os.path.exists(p) else ImageFont.load_default()
F_disp=lambda s: fnt("Italiana-Regular.ttf",s)
F_mono=lambda s: fnt("IBMPlexMono-Regular.ttf",s)
F_monob=lambda s: fnt("IBMPlexMono-Bold.ttf",s)
F_ital=lambda s: fnt("CrimsonPro-Italic.ttf",s)
def text(cv,xy,s,f,fill,a=1.0,anc="mm"):
    if a<=0.01: return
    ov=Image.new("RGBA",cv.size,(0,0,0,0)); ImageDraw.Draw(ov).text(xy,s,font=f,fill=(*fill,int(255*min(1,a))),anchor=anc); cv.alpha_composite(ov)
def tlen(s,f): return ImageDraw.Draw(Image.new("RGB",(4,4))).textlength(s,font=f)
def kick(cv,xy,s,size,fill,a=1.0,anc="mm",maxw=W-90):
    s=s.upper()
    for gap in ("  "," ",""):
        for sz in range(size,max(9,size-5),-1):
            t=gap.join(list(s))
            if tlen(t,F_mono(sz))<=maxw: text(cv,xy,t,F_mono(sz),fill,a,anc); return
    text(cv,xy,s,F_mono(max(9,size-5)),fill,a,anc)
def wrapped(cv,xy,s,f,fill,a,maxw,lh):
    if a<=0.01: return
    words=s.split(); lines=[]; cur=""
    for w in words:
        t=(cur+" "+w).strip()
        if tlen(t,f)<=maxw: cur=t
        else: lines.append(cur); cur=w
    if cur: lines.append(cur)
    y0=xy[1]-(len(lines)-1)*lh/2
    for i,ln in enumerate(lines): text(cv,(xy[0],y0+i*lh),ln,f,fill,a)
def layer(cv,fn):
    ov=Image.new("RGBA",cv.size,(0,0,0,0)); fn(ImageDraw.Draw(ov)); cv.alpha_composite(ov)
def rrect(d,box,rad,fill=None,outline=None,wid=1): d.rounded_rectangle(box,radius=rad,fill=fill,outline=outline,width=wid)
ROMAN=[(10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]
def roman(n):
    s=''
    for v,sym in ROMAN:
        while n>=v: s+=sym; n-=v
    return s
# flag → (display, warn)
FLAG={"triploidy":("triploidy · 69 · non-viable",True),"trisomy21":("trisomy 21",False),
      "chimera":("chimera · two cell lines",False),"conjoined":("conjoined",True),
      "vanishing-twin":("vanishing twin",False)}
# the line-up
SCEN=[("mz-mcma","Identical · MCMA","one placenta, one shared sac"),
      ("conjoined","Conjoined Twins","the split that never finished"),
      ("triplets-2-1","Triplets · 2 + 1","an identical pair, plus one"),
      ("quints","Quintuplets","five lives at once"),
      ("triploidy","Triploidy","a second sperm got in — 69"),
      ("trisomy","Trisomy 21","one extra chromosome 21"),
      ("chimerism","Chimera","two lineages fused into one"),
      ("vanishing","Vanishing Twin","conceived, then reabsorbed")]
_M={}
def meta(p):
    if p not in _M: _M[p]=json.load(open(f'/tmp/onto_{p}_meta.json'))
    return _M[p]
ST_X,ST_Y,STW=130,360,820
def readspec(p,frac):
    m=meta(p); OUT=m['W']; NF=m['NF']; SZ=OUT*OUT*3
    fi=max(0,min(NF-1,int(frac*NF)))
    f=open(f'/tmp/onto_{p}_field.bin','rb'); f.seek(fi*SZ)
    a=np.frombuffer(f.read(SZ),np.uint8).reshape(OUT,OUT,3); f.close()
    return Image.fromarray(a).resize((STW,STW),Image.LANCZOS), fi
def pills(cv,cx,y,items,a=1.0):   # flag chips, centered
    fm=F_mono(18); gap=18
    widths=[tlen(t.upper(),fm)+44 for t,_ in items]; tot=sum(widths)+gap*(len(items)-1)
    x=cx-tot/2
    for (t,warn),w in zip(items,widths):
        col=AMBER if warn else MAG
        layer(cv,lambda d,x=x,w=w,col=col: rrect(d,[x,y-22,x+w,y+22],22,outline=(*col,int(200*a)),wid=1,fill=(*col,int(26*a))))
        text(cv,(x+w/2,y),t.upper(),fm,col,a,anc="mm"); x+=w+gap
TITLE=96; SEG=150; CODA=112; FADE=16
NSC=len(SCEN); NF=TITLE+SEG*NSC+CODA
def locate(f):
    if f<TITLE: return ('title',0,f)
    if f>=TITLE+SEG*NSC: return ('coda',0,f-(TITLE+SEG*NSC))
    k=(f-TITLE)//SEG; return ('plate',min(k,NSC-1),(f-TITLE)-k*SEG)
def compose(f):
    kind,k,lf=locate(f); cv=Image.new("RGBA",(W,H),(*OB,255))
    if kind=='title':
        g=min(1,lf/16)*min(1,(TITLE-1-lf)/14)
        kick(cv,(W//2,540),"cellauto · ontogeny · the outcome panel",22,TEAL,0.7*g)
        text(cv,(W//2,820),"WILD OUTCOMES",F_disp(118),INK,g)
        text(cv,(W//2,968),"every way a life can begin",F_ital(46),AMBER,g)
        kick(cv,(W//2,1300),"eight scenarios · one seeded engine",18,MUTD,0.6*g)
        return cv
    if kind=='coda':
        g=min(1,lf/16)*min(1,(CODA-1-lf)/14)
        kick(cv,(W//2,560),"same rules · wildly different lives",22,TEAL,0.7*g)
        text(cv,(W//2,800),"from one cell,",F_disp(60),INK,g)
        text(cv,(W//2,892),"every possible you",F_disp(60),TEALB,g)
        kick(cv,(W//2,1300),"cellauto · ontogeny · wild outcomes",17,MUTD,0.5*g)
        return cv
    p,name,sub=SCEN[k]; m=meta(p); o=m['outcome']; a=min(1,lf/FADE)*min(1,(SEG-1-lf)/FADE)
    flags=[FLAG.get(fl,(fl,False)) for fl in o['flags']]
    warn=any(w for _,w in flags); acc=AMBER if warn else TEAL
    frac=0.12+0.62*(lf/SEG)                       # develop fertilisation -> birth across the plate
    spec,fi=readspec(p,frac); fr=m['fr'][min(fi,len(m['fr'])-1)]
    # stage
    layer(cv,lambda d:rrect(d,[ST_X-14,ST_Y-14,ST_X+STW+14,ST_Y+STW+14],14,fill=(*PLATE,255),outline=(*acc,int(46*a))))
    cv.paste(spec,(ST_X,ST_Y))
    # corner mats
    layer(cv,lambda d:[ (d.line([(x,y),(x+sx*24,y)],fill=(*acc,int(90*a)),width=1),d.line([(x,y),(x,y+sy*24)],fill=(*acc,int(90*a)),width=1))
        for x,sx in ((ST_X,1),(ST_X+STW,-1)) for y,sy in ((ST_Y,1),(ST_Y+STW,-1)) ])
    # header
    kick(cv,(W//2,140),f"wild outcome {roman(k+1)} / {roman(NSC)}",20,MUTD,0.8*a)
    text(cv,(W//2,224),name.upper(),F_disp(62),INK,a)
    kick(cv,(W//2,292),sub,16,acc,0.7*a)
    kick(cv,(ST_X+10,ST_Y+STW-26),fr['metaDay'],16,MUTD,0.8*a,anc="lm")
    text(cv,(ST_X+STW-10,ST_Y+24),"● LIVE",F_mono(18),MAG,0.7*a,anc="rm")
    # verdict
    text(cv,(190,1300),str(o['n']),F_disp(110),acc,a)
    text(cv,(300,1272),o['label'].title(),F_disp(44),INK,a,anc="lm")
    zyg=o['zygosity']+(f" · {o['choType']}" if o['choType'] else "")
    text(cv,(302,1326),zyg,F_ital(30),MUT,0.95*a,anc="lm")
    # the wild part — flags
    if flags: pills(cv,W//2,1430,flags,a)
    # stats strip + note
    chs=" / ".join(map(str,o['chromosomes']))
    kick(cv,(W//2,1502),f"eggs {o['nOocytes']}   ·   placentas {o['placentas']}   ·   sacs {o['sacs']}   ·   {chs} chromosomes",17,MUTD,0.7*a)
    wrapped(cv,(W//2,1600),m['hint'],F_ital(28),MUT,0.92*a,980,36)
    # progress
    layer(cv,lambda d:[d.ellipse([W//2-(NSC-1)*15+j*30-4,1820-4,W//2-(NSC-1)*15+j*30+4,1820+4],fill=(*(acc if j==k else MUTD),255 if j==k else 110)) for j in range(NSC)])
    kick(cv,(W//2,1878),"cellauto · ontogeny · wild outcomes",15,MUTD,0.45)
    return cv
if __name__=='__main__' and len(sys.argv)>2 and sys.argv[1]=='test':
    compose(int(sys.argv[2])).convert("RGB").save('/tmp/wild_test.png'); print("NF",NF,"per-plate",SEG); sys.exit()
# ===== FULL RENDER =====
silent="/tmp/wild_silent.mp4"
wr=imageio_ffmpeg.write_frames(silent,(W,H),fps=FPS,codec="libx264",pix_fmt_in="rgb24",pix_fmt_out="yuv420p",macro_block_size=8,output_params=["-crf","19","-preset","medium"])
wr.send(None)
for f in range(NF): wr.send(np.ascontiguousarray(np.asarray(compose(f).convert("RGB"),np.uint8)).tobytes())
wr.close(); print("composited",NF)
total=NF/FPS; out="/tmp/web8_wild_outcomes.mp4"
fade=min(3.5,total/3); fin=min(3.0,total/3); fo=max(0.0,total-fade)
af=f"[1:a][2:a][3:a]amix=inputs=3,volume=0.10,lowpass=f=520,afade=t=in:st=0:d={fin:.2f},afade=t=out:st={fo:.2f}:d={fade:.2f}[a]"
subprocess.run([FF,"-y","-hide_banner","-loglevel","error","-i",silent,
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=55:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=82.5:sample_rate=44100",
 "-f","lavfi","-t",f"{total}","-i","sine=frequency=110:sample_rate=44100",
 "-filter_complex",af,"-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","144k","-shortest","-movflags","+faststart",out],check=True)
print(f"-> {out}  {os.path.getsize(out)/1e6:.1f} MB  {total:.1f}s")
