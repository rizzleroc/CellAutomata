// generic per-rule generator: node gen.mjs <ruleid> <warmup> <frames> <steps> <modes>
import fs from 'fs';
globalThis.window=globalThis; globalThis.CA={RULES:{}};
const ev=(0,eval); const load=p=>ev(fs.readFileSync(p,'utf8'));
load('docs/web8/experiment/viridis.js'); load('docs/web8/experiment/sprites.js'); load('docs/web8/experiment/sem.js');
const [,,ID,WARMUP,FRAMES,STEPS,MODES,FF,KK,SCAT]=process.argv;
const warm=+WARMUP, frames=+FRAMES, steps=+STEPS, modes=MODES.split(',');
load(`docs/web8/experiment/rules/${ID}.js`);
const key=ID.replace('natural_selection','natural-selection');
const g=CA.RULES[key]();
if(FF&&g.params&&g.params.F){g.params.F.value=+FF;} if(KK&&g.params&&g.params.k){g.params.k.value=+KK;}
if(process.env.GEN_PARAMS){const o=JSON.parse(process.env.GEN_PARAMS); for(const pk in o){ if(g.params&&g.params[pk]){ g.params[pk].value=o[pk]; if(g.onParamChange){try{g.onParamChange(pk);}catch(e){}} } }}
const W=g.width,H=g.height; g.reset();
if(SCAT){function mul(a){return function(){a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};} const rng=mul(987654); for(let i=0;i<+SCAT;i++) g.paint((rng()*W)|0,(rng()*H)|0,5,'paint');}
const pn=new Uint8ClampedArray(W*H*4);
const SC = (W<=120?4:(W<=160?3:2));      // SEM supersample by grid
const ps=new Uint8ClampedArray(W*SC*H*SC*4); const h=new Float32Array(W*H);
const fds={}; for(const m of modes) if(m!=='spr') fds[m]=fs.openSync(`/tmp/g_${ID}_${m}.bin`,'w');
const wr=(fd,b)=>fs.writeSync(fd,Buffer.from(b.buffer,b.byteOffset,b.byteLength));
for(let i=0;i<warm;i++) g.step();
const spr=[], pop=[]; const t0=Date.now();
for(let f=0;f<frames;f++){
  for(let s=0;s<steps;s++) g.step();
  if(modes.includes('n')){ g.render(pn); wr(fds['n'],pn); }
  if(modes.includes('w')){ g.renderHeight(h); window.SEM.render(h,W,H,ps,{palette:'warm-sepia',scale:SC}); wr(fds['w'],ps); }
  if(modes.includes('c')){ g.renderHeight(h); window.SEM.render(h,W,H,ps,{palette:'cool-mono',scale:SC}); wr(fds['c'],ps); }
  if(modes.includes('spr')) spr.push((g.sprites?g.sprites():[]).map(s=>({x:+s.x.toFixed(1),y:+s.y.toFixed(1),s:+(s.scale||1).toFixed(2),k:s.kind,h:s.hand||null})));
  pop.push(g.population?g.population():'');
}
fs.writeFileSync(`/tmp/g_${ID}_spr.json`,JSON.stringify(spr));
fs.writeFileSync(`/tmp/g_${ID}_meta.json`,JSON.stringify({id:ID,label:g.label,W,H,SC,frames,modes,pop}));
console.log(ID,'done',W+'x'+H,'SC'+SC,((Date.now()-t0)/1000).toFixed(0)+'s','pop0:',pop[0],'popN:',pop[frames-1]);
