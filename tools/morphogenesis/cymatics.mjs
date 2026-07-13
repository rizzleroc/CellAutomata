// CYMATICS — a driven square membrane (Chladni plate). At drive frequency F the standing-wave
// displacement is the modal-resonance sum u(x,y)=Σ A_mn(F)·sin(mπx)sin(nπy), A_mn = driver / ((ω²−F²)²+(γF)²),
// ω_mn=√(m²+n²). "Sand" collects on the NODES (|u|≈0) → that's the Chladni figure. Sweeping F morphs it
// through the classic sequence. Separable sum (T-trick) so it's fast.
//   node cymatics.mjs strip <tag> <f0> <f1> <K> [N M gamma dcx dcy]   -> /tmp/cym_<tag>.png (montage)
//   node cymatics.mjs gen   <tag> <f0> <f1> <NF> [N M gamma dcx dcy]  -> /tmp/g_<tag>_n.bin (gen.mjs native format)
import fs from 'fs';
import zlib from 'node:zlib';
const A = process.argv, MODEKIND = A[2], tag = A[3], F0 = +A[4], F1 = +A[5], COUNT = +A[6] || 6;
const N = +A[7] || 240, M = +A[8] || 14, GAMMA = +A[9] || 0.7, DCX = A[10] != null ? +A[10] : 0.5, DCY = A[11] != null ? +A[11] : 0.5;
// precompute mode tables  SX[m][i] = sin(m*pi*(i+0.5)/N)
const SX = []; for (let m = 1; m <= M; m++) { const r = new Float32Array(N); for (let i = 0; i < N; i++) r[i] = Math.sin(m * Math.PI * (i + 0.5) / N); SX.push(r); }
const SY = SX; // square symmetric
const drv = []; for (let m = 1; m <= M; m++) { drv.push(Math.sin(m * Math.PI * DCX) ); } // driver coupling per axis
const drvY = []; for (let n = 1; n <= M; n++) { drvY.push(Math.sin(n * Math.PI * DCY)); }
const W2 = []; for (let m = 1; m <= M; m++) { const r = []; for (let n = 1; n <= M; n++) r.push(m * m + n * n); W2.push(r); }
const u = new Float32Array(N * N), T = new Float32Array(M * N);
// sand palette: dark plate -> amber -> cream sand on the nodes
function lut(b){ // b in 0..1 (1 = on a node)
  const stops=[[6,9,16],[18,22,34],[120,92,46],[214,170,96],[248,238,212]];
  const x=b*(stops.length-1)|0, t=b*(stops.length-1)-x, a=stops[Math.min(x,stops.length-1)],c=stops[Math.min(x+1,stops.length-1)];
  return [a[0]+(c[0]-a[0])*t, a[1]+(c[1]-a[1])*t, a[2]+(c[2]-a[2])*t];
}
function field(F){
  const A2 = []; let amax = 1e-9;
  for (let m = 0; m < M; m++){ const r = new Float32Array(M); for (let n = 0; n < M; n++){ const d = (W2[m][n] - F*F); const a = (drv[m]*drvY[n]) / (d*d + (GAMMA*F)*(GAMMA*F)); r[n]=a; } A2.push(r); }
  // T[m][j] = Σ_n A[m][n] SY[n][j]
  for (let m = 0; m < M; m++) for (let j = 0; j < N; j++){ let s=0; const Am=A2[m]; for (let n=0;n<M;n++) s+=Am[n]*SY[n][j]; T[m*N+j]=s; }
  // u[i][j] = Σ_m SX[m][i] T[m][j]
  let mx=1e-9;
  for (let i=0;i<N;i++){ const off=i*N; for (let j=0;j<N;j++){ let s=0; for (let m=0;m<M;m++) s+=SX[m][i]*T[m*N+j]; u[off+j]=s; const a=Math.abs(s); if(a>mx)mx=a; } }
  return mx;
}
function renderRGBA(out){ // out: Uint8ClampedArray N*N*4 ; sand = exp(-(u/mx/sig)^2)
  const mx = field.lastMx; const inv = 1/mx, sig = 0.060;
  for (let p=0;p<N*N;p++){ const un = u[p]*inv; const b = Math.exp(-(un*un)/(sig*sig)); const c = lut(b<0?0:b>1?1:b); const q=p*4; out[q]=c[0];out[q+1]=c[1];out[q+2]=c[2];out[q+3]=255; }
}
function frameRGBA(F,out){ field.lastMx = field(F); renderRGBA(out); }
// PNG writer
const CT=(()=>{const t=[];for(let n=0;n<256;n++){let c=n;for(let k=0;k<8;k++)c=c&1?0xedb88320^(c>>>1):c>>>1;t[n]=c>>>0;}return t;})();
const crc=(b)=>{let c=0xffffffff;for(let i=0;i<b.length;i++)c=CT[(c^b[i])&0xff]^(c>>>8);return(c^0xffffffff)>>>0;};
function chunk(ty,d){const L=Buffer.alloc(4);L.writeUInt32BE(d.length,0);const T2=Buffer.from(ty,'ascii');const C=Buffer.alloc(4);C.writeUInt32BE(crc(Buffer.concat([T2,d])),0);return Buffer.concat([L,T2,d,C]);}
function writePNG(p,w,h,rgba){const sig=Buffer.from([137,80,78,71,13,10,26,10]),ih=Buffer.alloc(13);ih.writeUInt32BE(w,0);ih.writeUInt32BE(h,4);ih[8]=8;ih[9]=6;const raw=Buffer.alloc((w*4+1)*h);for(let y=0;y<h;y++){raw[y*(w*4+1)]=0;rgba.copy(raw,y*(w*4+1)+1,y*w*4,y*w*4+w*4);}fs.writeFileSync(p,Buffer.concat([sig,chunk('IHDR',ih),chunk('IDAT',zlib.deflateSync(raw)),chunk('IEND',Buffer.alloc(0))]));}
const px=new Uint8ClampedArray(N*N*4);
if(MODEKIND==='strip'){
  const T2=Math.min(N,220), COLS=Math.min(COUNT,6), ROWS=Math.ceil(COUNT/COLS), MW=T2*COLS, MH=T2*ROWS;
  const img=Buffer.alloc(MW*MH*4); const freqs=[];
  for(let s=0;s<COUNT;s++){ const F=F0+(F1-F0)*(COUNT>1?s/(COUNT-1):0); freqs.push(+F.toFixed(2)); frameRGBA(F,px);
    const cx=(s%COLS)*T2, cy=((s/COLS)|0)*T2; for(let y=0;y<T2;y++)for(let x=0;x<T2;x++){const sp=(((y*N/T2)|0)*N+((x*N/T2)|0))*4,dp=((cy+y)*MW+cx+x)*4;img[dp]=px[sp];img[dp+1]=px[sp+1];img[dp+2]=px[sp+2];img[dp+3]=255;}}
  writePNG(`/tmp/cym_${tag}.png`,MW,MH,img);
  fs.writeFileSync(`/tmp/cym_${tag}.json`,JSON.stringify({tag,F0,F1,COUNT,N,M,gamma:GAMMA,driver:[DCX,DCY],freqs,montage:`/tmp/cym_${tag}.png (${COLS}x${ROWS}, freq low->high)`}));
  console.log(`cym strip ${tag}: ${COUNT} figures F ${F0}->${F1} -> /tmp/cym_${tag}.png  freqs ${freqs.join(',')}`);
} else { // gen -> native bin (gen.mjs format: W*H*4 RGBA per frame)
  const NF=COUNT, fd=fs.openSync(`/tmp/g_${tag}_n.bin`,'w');
  for(let f=0;f<NF;f++){ const F=F0+(F1-F0)*(f/(NF-1||1)); frameRGBA(F,px); fs.writeSync(fd,Buffer.from(px.buffer,px.byteOffset,px.byteLength)); }
  fs.closeSync(fd);
  fs.writeFileSync(`/tmp/g_${tag}_meta.json`,JSON.stringify({id:tag,label:'Cymatics · driven plate',W:N,H:N,SC:1,frames:NF,modes:['n'],pop:[]}));
  console.log(`cym gen ${tag}: ${NF} frames F ${F0}->${F1} -> /tmp/g_${tag}_n.bin`);
}
