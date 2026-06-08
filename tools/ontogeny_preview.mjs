// Render a looping APNG of the Ontogeny sequence (no deps, no MCP):
// gametes -> fertilisation -> cleavage -> the twinning split -> multiples 1/2/3/5.
import { writeFileSync } from 'node:fs';
import zlib from 'node:zlib';

const W = 340, H = 300;
const OB=[7,9,13], TEAL=[63,224,208], TEAL_D=[31,143,134], TEAL_B=[120,244,231],
      BONE=[236,231,218], BONE_D=[203,197,182], MAG=[215,123,255];

function newBuf(){ const b=Buffer.alloc(W*H*4); for(let i=0;i<W*H;i++){ b[i*4]=OB[0];b[i*4+1]=OB[1];b[i*4+2]=OB[2];b[i*4+3]=255;} return b; }
function px(b,x,y,c,a){ x|=0;y|=0; if(x<0||y<0||x>=W||y>=H||a<=0)return; if(a>1)a=1; const i=(y*W+x)*4,ia=1-a; b[i]=c[0]*a+b[i]*ia; b[i+1]=c[1]*a+b[i+1]*ia; b[i+2]=c[2]*a+b[i+2]*ia; }
function disc(b,cx,cy,r,c,a){ if(r<=0)return; const x0=Math.max(0,(cx-r-1)|0),x1=Math.min(W-1,(cx+r+1)|0),y0=Math.max(0,(cy-r-1)|0),y1=Math.min(H-1,(cy+r+1)|0); for(let y=y0;y<=y1;y++)for(let x=x0;x<=x1;x++){ const d=Math.hypot(x+0.5-cx,y+0.5-cy),cov=r-d+0.5; if(cov>0) px(b,x,y,c,a*Math.min(1,cov)); } }
function ring(b,cx,cy,r,th,c,a){ const R=r+th+1; const x0=Math.max(0,(cx-R)|0),x1=Math.min(W-1,(cx+R)|0),y0=Math.max(0,(cy-R)|0),y1=Math.min(H-1,(cy+R)|0); for(let y=y0;y<=y1;y++)for(let x=x0;x<=x1;x++){ const d=Math.hypot(x+0.5-cx,y+0.5-cy),cov=(th/2)-Math.abs(d-r)+0.5; if(cov>0) px(b,x,y,c,a*Math.min(1,cov)); } }
function cell(b,x,y,r,a){ disc(b,x,y,r,TEAL_D,a); disc(b,x-r*0.28,y-r*0.28,r*0.6,TEAL_B,a*0.95); ring(b,x,y,r,1.4,TEAL,a*0.55); }
function clusterPos(n,R){ const o=[]; for(let i=0;i<n;i++){ if(n===1){o.push([0,0]);continue;} const ang=i*2.399963,rr=R*0.74*Math.sqrt(i/n); o.push([rr*Math.cos(ang),rr*Math.sin(ang)]);} return o; }
function cluster(b,cx,cy,n,R,a){ const cr=n<=1?R*0.92:Math.max(3.0,R/Math.sqrt(n)*0.95); for(const [dx,dy] of clusterPos(n,R)) cell(b,cx+dx,cy+dy,cr,a); }
function oocyte(b,cx,cy,r,a){ disc(b,cx,cy,r,TEAL_D,a*0.5); ring(b,cx,cy,r+3,3,BONE_D,a*0.45); disc(b,cx-r*0.2,cy-r*0.2,r*0.32,TEAL_B,a*0.7); }
function sperm(b,x,y,ang,a){ disc(b,x,y,2.4,BONE,a); for(let k=1;k<=4;k++){ const t=k*2.6, wob=Math.sin(k*1.4+x*0.13)*1.7; disc(b, x-Math.cos(ang)*t+Math.cos(ang+1.57)*wob, y-Math.sin(ang)*t+Math.sin(ang+1.57)*wob, 1.9-k*0.32, BONE_D, a*(1-k*0.2)); } }
const rnd=(i)=>{const s=Math.sin(i*127.1+9.7)*43758.5453; return s-Math.floor(s);};
const ease=(t)=>t<0?0:t>1?1:t*t*(3-2*t);
const lerp=(a,b,t)=>a+(b-a)*t;

// ---- timeline (frame ranges) ----
const EX=170, EY=150;          // egg/zygote centre for the lifecycle
const SP=70;                   // twin separation
function drawFrame(f){
  const b=newBuf();
  if(f<42){
    // —— lifecycle: gametes -> fertilisation -> cleavage -> twin split ——
    if(f<13){ // gametes approach + fertilisation flash
      oocyte(b,EX,EY,24,1);
      const fert=f>=10;
      for(let i=0;i<14;i++){ const a0=i/14*6.283+0.2,d0=150, sx=EX+Math.cos(a0)*d0, sy=EY+Math.sin(a0)*d0; const spd=0.85+0.4*rnd(i); let p=ease(Math.min(1,(f/9)*spd)); const ex=EX+Math.cos(a0)*30, ey=EY+Math.sin(a0)*30; const x=lerp(sx,ex,p),y=lerp(sy,ey,p); const al=fert?Math.max(0,1-(f-10)*0.6):1; if(al>0) sperm(b,x,y,a0+3.14159,al*0.95); }
      if(fert){ const u=(f-10)/3; ring(b,EX,EY,30+u*22,3,BONE,(1-u)*0.9); ring(b,EX,EY,18+u*30,2,TEAL_B,(1-u)*0.7); }
    } else if(f<31){ // cleavage 1->2->4->8->morula(16)
      const n = f<16?1: f<19?2: f<23?4: f<27?8: 16;
      if(f<26) ring(b,EX,EY,30,2.5,BONE_D,0.35*(1-(f-13)/13)); // zona, hatching
      cluster(b,EX,EY,n,24,1);
    } else { // split -> two embryos, shared placenta (MCDA), two sacs
      const sp=ease((f-31)/9);
      disc(b,EX,EY,30+sp*34,MAG,0.12*sp);              // one shared placenta
      const lx=EX-sp*SP, rx=EX+sp*SP;
      ring(b,lx,EY,26,2,TEAL,0.5*sp); ring(b,rx,EY,26,2,TEAL,0.5*sp);  // two sacs
      cluster(b,lx,EY,16,18,1); cluster(b,rx,EY,16,18,1);
    }
  } else {
    // —— multiples gallery: 1 -> 2 -> 3 -> 5 ——
    const counts=[1,2,3,5]; const seg=Math.min(3,((f-42)/6)|0); const n=counts[seg];
    const u=((f-42)%6)/6; const pulse=1+0.06*Math.sin(u*6.283);
    for(let i=0;i<n;i++){ const x=n===1?W/2:lerp(W*0.22,W*0.78,i/(n-1)); const y=H*0.5; disc(b,x,y,24,MAG,0.12); ring(b,x,y,18,2,TEAL,0.55); cluster(b,x,y,12,13*pulse,1); }
  }
  return b;
}

// ---- PNG / APNG encoder (RGBA8) ----
const CT=(()=>{const t=[];for(let n=0;n<256;n++){let c=n;for(let k=0;k<8;k++)c=c&1?0xedb88320^(c>>>1):c>>>1;t[n]=c>>>0;}return t;})();
const crc=(b)=>{let c=0xffffffff;for(let i=0;i<b.length;i++)c=CT[(c^b[i])&0xff]^(c>>>8);return(c^0xffffffff)>>>0;};
function chunk(t,d){const L=Buffer.alloc(4);L.writeUInt32BE(d.length,0);const T=Buffer.from(t,'ascii');const C=Buffer.alloc(4);C.writeUInt32BE(crc(Buffer.concat([T,d])),0);return Buffer.concat([L,T,d,C]);}
function comp(fr){const raw=Buffer.alloc((W*4+1)*H);for(let y=0;y<H;y++){raw[y*(W*4+1)]=0;fr.copy(raw,y*(W*4+1)+1,y*W*4,y*W*4+W*4);}return zlib.deflateSync(raw);}
function apng(frames,dn,dd){
  const sig=Buffer.from([137,80,78,71,13,10,26,10]); const ihdr=Buffer.alloc(13); ihdr.writeUInt32BE(W,0);ihdr.writeUInt32BE(H,4);ihdr[8]=8;ihdr[9]=6;
  const out=[sig,chunk('IHDR',ihdr)]; const ac=Buffer.alloc(8); ac.writeUInt32BE(frames.length,0); ac.writeUInt32BE(0,4); out.push(chunk('acTL',ac));
  let seq=0;
  frames.forEach((fr,i)=>{ const fc=Buffer.alloc(26); fc.writeUInt32BE(seq++,0); fc.writeUInt32BE(W,4); fc.writeUInt32BE(H,8); fc.writeUInt16BE(dn,20); fc.writeUInt16BE(dd,22); fc[24]=0; fc[25]=0; out.push(chunk('fcTL',fc)); const cz=comp(fr); if(i===0){out.push(chunk('IDAT',cz));} else {const fd=Buffer.alloc(4+cz.length); fd.writeUInt32BE(seq++,0); cz.copy(fd,4); out.push(chunk('fdAT',fd));} });
  out.push(chunk('IEND',Buffer.alloc(0))); return Buffer.concat(out);
}

const N=66, frames=[]; for(let f=0;f<N;f++) frames.push(drawFrame(f));
writeFileSync('docs/design/ontogeny_preview.png', apng(frames,8,100));
console.log(`wrote APNG: ${N} frames, ${W}x${H}, ~${(N*0.08).toFixed(1)}s loop`);
