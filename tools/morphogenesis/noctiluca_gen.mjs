// NOCTILUCA — deep-sea bioluminescence. Living light drifting in black water.
// Path emphasises MOTION (turbulent / worms / u-skate solitons / negatons) so the
// field never settles — it swims. Sparse seeding so the glow front takes the whole
// reel to sweep the dark. NF overridable for smoke tests:  MORPH_NF=48 node ...
import fs from 'fs';
globalThis.window=globalThis; globalThis.CA={RULES:{}};
const ev=(0,eval); const load=p=>ev(fs.readFileSync(p,'utf8'));
load('docs/web8/experiment/viridis.js');
let gs=fs.readFileSync('docs/web8/experiment/rules/grayscott.js','utf8');
gs=gs.replace('const W = 220;','const W = 1000;').replace('const H = 220;','const H = 1000;'); ev(gs);
function mul(a){return function(){a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};}
const g=CA.RULES.grayscott(); const W=g.width,H=g.height; const h=new Float32Array(W*H); const u16=new Uint16Array(W*H);
function setF(F,k){g.params.F.value=F;g.params.k.value=k;}
// Oceanic drift path — all waypoints sit in the alive band (see HANDOFF Lesson 1).
// turbulent roil -> filaments -> dense network -> gliding solitons -> swimming negatons -> back to the deep.
const WP=[
 ['turbulent',0.026,0.053],
 ['worms',0.030,0.056],
 ['labyrinth',0.039,0.058],
 ['worms',0.032,0.057],
 ['u-skate',0.060,0.064],
 ['worms',0.030,0.056],
 ['negatons',0.039,0.0645],
 ['turbulent',0.026,0.054]
];
const NF=+(process.env.MORPH_NF||2880), SEG=WP.length-1;
setF(WP[0][1],WP[0][2]); g.reset();
// Sparse scatter — 90 small nuclei. Growth front sweeps slowly = visible drama.
const rng=mul(13371337);
for(let i=0;i<90;i++) g.paint((rng()*W)|0,(rng()*H)|0,5,'paint');
const fd=fs.openSync('/tmp/noctiluca_field.bin','w'); const fk=[],names=[],pop=[]; const t0=Date.now();
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
fs.writeFileSync('/tmp/noctiluca_meta.json',JSON.stringify({W,H,NF,SEG,WP,fk,names,pop}));
console.log('DONE',((Date.now()-t0)/1000).toFixed(0)+'s');
