import fs from 'fs';
globalThis.window=globalThis; globalThis.CA={RULES:{}};
const ev=(0,eval); const load=p=>ev(fs.readFileSync(p,'utf8'));
load('docs/web8/experiment/viridis.js'); load('docs/web8/experiment/sem.js');
let gs=fs.readFileSync('docs/web8/experiment/rules/grayscott.js','utf8');
gs=gs.replace('const W = 220;','const W = 1000;').replace('const H = 220;','const H = 1000;'); ev(gs);
function mul(a){return function(){a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};}
const g=CA.RULES.grayscott(); const W=g.width,H=g.height;
const pn=new Uint8ClampedArray(W*H*4), ps=new Uint8ClampedArray(W*H*4); const h=new Float32Array(W*H);
function setF(F,k){g.params.F.value=F;g.params.k.value=k;}
setF(0.0367,0.0649); g.reset();
const rng=mul(424242); for(let i=0;i<180;i++) g.paint((rng()*W)|0,(rng()*H)|0,5,'paint');
const NF=1440, FLIP1=600, FLIP2=1008;   // mitosis | labyrinth | waves(turbulent)
const fd=fs.openSync('/tmp/ms_field.bin','w'); const pop=[]; const t0=Date.now();
const wr=b=>fs.writeSync(fd,Buffer.from(b.buffer,b.byteOffset,b.byteLength));
for(let f=0;f<NF;f++){
  if(f===FLIP1) setF(0.039,0.058);
  if(f===FLIP2) setF(0.026,0.051);
  g.step();
  if(f<FLIP1){ g.renderHeight(h); window.SEM.render(h,W,H,ps,{palette:'warm-sepia',scale:1}); wr(ps); }   // mitosis: warm
  else if(f<FLIP2){ g.render(pn); wr(pn); }                                                                 // labyrinth: viridis
  else { g.renderHeight(h); window.SEM.render(h,W,H,ps,{palette:'cool-mono',scale:1}); wr(ps); }            // waves: cool
  pop.push(g.population?g.population():'');
  if(f%240===0) console.log('frame',f,((Date.now()-t0)/1000).toFixed(0)+'s',pop[f]);
}
fs.writeFileSync('/tmp/ms_meta.json',JSON.stringify({W,H,NF,FLIP1,FLIP2,pop}));
console.log('DONE',((Date.now()-t0)/1000).toFixed(0)+'s');
