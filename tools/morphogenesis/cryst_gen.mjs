// CRYSTALLOGENESIS — coral/labyrinth territory, 4 growing nuclei
import fs from 'fs';
globalThis.window=globalThis; globalThis.CA={RULES:{}};
const ev=(0,eval); const load=p=>ev(fs.readFileSync(p,'utf8'));
load('docs/web8/experiment/viridis.js');
let gs=fs.readFileSync('docs/web8/experiment/rules/grayscott.js','utf8');
gs=gs.replace('const W = 220;','const W = 1000;').replace('const H = 220;','const H = 1000;'); ev(gs);
function mul(a){return function(){a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};}
const g=CA.RULES.grayscott(); const W=g.width,H=g.height; const h=new Float32Array(W*H); const u16=new Uint16Array(W*H);
function setF(F,k){g.params.F.value=F;g.params.k.value=k;}
// Crystalline: mitosis seeding → labyrinth → deep coral → stripes → labyrinth → coral (mineral growth)
const WP=[
 ['mitosis',0.0367,0.0649],
 ['labyrinth',0.039,0.058],
 ['coral',0.0545,0.062],
 ['stripes',0.042,0.060],
 ['labyrinth',0.040,0.059],
 ['coral',0.055,0.063],
 ['labyrinth',0.039,0.058],
 ['coral',0.0545,0.062]
];
const NF=2880, SEG=WP.length-1;
setF(WP[0][1],WP[0][2]); g.reset();
// 4 nucleation sites — one in each quadrant corner region (like crystal nuclei)
const nuclei=[[180,180],[820,180],[180,820],[820,820],[500,500],[350,350],[650,650],[350,650],[650,350]];
for(const [cx,cy] of nuclei) g.paint(cx,cy,18,'paint');
const fd=fs.openSync('/tmp/cryst_field.bin','w'); const fk=[],names=[],pop=[]; const t0=Date.now();
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
fs.writeFileSync('/tmp/cryst_meta.json',JSON.stringify({W,H,NF,SEG,WP,fk,names,pop}));
console.log('DONE',((Date.now()-t0)/1000).toFixed(0)+'s');
