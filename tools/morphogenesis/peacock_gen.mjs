// PEACOCK — iridescent ocelli. Spot/mitosis domes rendered later as concentric eye-spots
// (gold rim → emerald → peacock-blue → dark pupil) with structural-colour sheen.
import fs from 'fs';
globalThis.window=globalThis; globalThis.CA={RULES:{}};
const ev=(0,eval); const load=p=>ev(fs.readFileSync(p,'utf8'));
load('docs/web8/experiment/viridis.js');
let gs=fs.readFileSync('docs/web8/experiment/rules/grayscott.js','utf8');
gs=gs.replace('const W = 220;','const W = 1000;').replace('const H = 220;','const H = 1000;'); ev(gs);
function mul(a){return function(){a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};}
const g=CA.RULES.grayscott(); const W=g.width,H=g.height; const h=new Float32Array(W*H); const u16=new Uint16Array(W*H);
function setF(F,k){g.params.F.value=F;g.params.k.value=k;}
const WP=[
 ['spots',0.030,0.062],
 ['mitosis',0.0367,0.0649],
 ['spots',0.033,0.063],
 ['mitosis',0.0366,0.0648],
 ['spots',0.030,0.062]
];
const NF=+(process.env.MORPH_NF||2880), SEG=WP.length-1;
setF(WP[0][1],WP[0][2]); g.reset();
const rng=mul(19283746);
for(let i=0;i<110;i++) g.paint((rng()*W)|0,(rng()*H)|0,5,'paint');
const fd=fs.openSync('/tmp/peacock_field.bin','w'); const fk=[],names=[],pop=[]; const t0=Date.now();
for(let f=0;f<NF;f++){
  const p=f/NF*SEG; const s=Math.min(SEG-1,Math.floor(p)); const t=p-s;
  const F=WP[s][1]+(WP[s+1][1]-WP[s][1])*t, k=WP[s][2]+(WP[s+1][2]-WP[s][2])*t;
  setF(F,k); g.step();
  g.renderHeight(h); for(let i=0;i<h.length;i++){let v=h[i]; v=v<0?0:(v>1?1:v); u16[i]=(v*65535)|0;}
  fs.writeSync(fd,Buffer.from(u16.buffer,u16.byteOffset,u16.byteLength));
  fk.push([+F.toFixed(4),+k.toFixed(4)]); names.push(WP[Math.round(p)][0]); pop.push(g.population?g.population():'');
  if(f%288===0) console.log('frame',f,((Date.now()-t0)/1000).toFixed(0)+'s',names[f],'Σv',pop[f]);
}
fs.closeSync(fd);
fs.writeFileSync('/tmp/peacock_meta.json',JSON.stringify({W,H,NF,SEG,WP,fk,names,pop}));
console.log('DONE',((Date.now()-t0)/1000).toFixed(0)+'s');
