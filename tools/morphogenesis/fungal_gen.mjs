// FUNGAL — the mycelial journey. From a scatter of spores, branching hyphae sweep the
// dark substrate, fuse into a living network, knot into primordia, swell into fruiting
// bodies, and release a new generation of spores. The Gray–Scott coral / worms / u-skate
// regimes ARE branching hyphal growth — so the path is one long colonisation arc rather
// than a loop. Sparse seeding so the mycelium takes the whole reel to claim the dark.
// NF overridable for smoke tests:  MORPH_NF=120 node tools/morphogenesis/fungal_gen.mjs
import fs from 'fs';
globalThis.window=globalThis; globalThis.CA={RULES:{}};
const ev=(0,eval); const load=p=>ev(fs.readFileSync(p,'utf8'));
load('docs/web8/experiment/viridis.js');
let gs=fs.readFileSync('docs/web8/experiment/rules/grayscott.js','utf8');
gs=gs.replace('const W = 220;','const W = 1000;').replace('const H = 220;','const H = 1000;'); ev(gs);
function mul(a){return function(){a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};}
const g=CA.RULES.grayscott(); const W=g.width,H=g.height; const h=new Float32Array(W*H); const u16=new Uint16Array(W*H);
function setF(F,k){g.params.F.value=F;g.params.k.value=k;}
// The fungal life cycle as a one-way colonisation through the alive band (HANDOFF Lesson 1).
// germinate -> extend hyphae -> dense mycelial mat -> fuse network -> pin primordia ->
// fruit (caps divide) -> sporulate (release) -> settle back into dark humus.
const WP=[
 ['germination',0.0545,0.0620],   // coral: spores sprout branching tips
 ['hyphae',     0.0320,0.0570],   // worms: long filaments extend & branch
 ['mycelium',   0.0390,0.0580],   // labyrinth: dense interconnected mat
 ['anastomosis',0.0300,0.0560],   // worms: threads fuse into one network
 ['primordia',  0.0600,0.0640],   // u-skate: knots bud — the first pins
 ['fruiting',   0.0367,0.0649],   // mitosis: caps swell and divide
 ['sporulation',0.0390,0.0645],   // negatons: bodies open and scatter spores
 ['humus',      0.0260,0.0540]    // turbulent: the colony settles into dark soil
];
const NF=+(process.env.MORPH_NF||2880), SEG=WP.length-1;
setF(WP[0][1],WP[0][2]); g.reset();
// Sparse scatter — 64 spores, small nuclei. The mycelial front sweeps slowly = visible drama.
const rng=mul(8675309);
for(let i=0;i<64;i++) g.paint((rng()*W)|0,(rng()*H)|0,4,'paint');
const fd=fs.openSync('/tmp/fungal_field.bin','w'); const fk=[],names=[],pop=[]; const t0=Date.now();
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
fs.writeFileSync('/tmp/fungal_meta.json',JSON.stringify({W,H,NF,SEG,WP,fk,names,pop}));
console.log('DONE',((Date.now()-t0)/1000).toFixed(0)+'s');
