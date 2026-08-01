/* Studio engines — the 8 simulation kernels behind the 13 tiles.
   Classic script (no module) so it loads from file:// and is vm-testable
   headlessly (tests/controls.mjs). Registers window.StudioEngines.
   Kernel interface: constructor(w,h,preset) · step() · render(ctx) ·
   controls() · randomize() · optional pointer(px,py,down). */
(() => {
  const PALS = { aurora:['rgba(150,232,212,.55)','rgba(38,150,205,.5)'], ember:['rgba(250,210,120,.55)','rgba(230,90,40,.5)'], ice:['rgba(200,230,255,.6)','rgba(90,140,220,.5)'] };

  // ===================== kernels =====================
  class Flow {
    constructor(w,h){ this.w=w;this.h=h;this.spd=1.5;this.fade=0.16;this.freq=5.2;this.pal='aurora';this.psz=1;this.t=0;this.accumulates=true;this.setN(Math.min(4000,(w*h*0.02)|0)); }
    setN(n){ this.N=n|0;this.x=new Float32Array(this.N);this.y=new Float32Array(this.N);this.l=new Float32Array(this.N);this.s=1234567>>>0;for(let i=0;i<this.N;i++)this.spawn(i); }
    spawn(i){ this.s=(this.s*1664525+1013904223)>>>0;this.x[i]=this.s/4294967296*this.w;this.s=(this.s*1664525+1013904223)>>>0;this.y[i]=this.s/4294967296*this.h;this.s=(this.s*1664525+1013904223)>>>0;this.l[i]=18+this.s/4294967296*70; }
    pot(x,y){ const t=this.t,F=this.freq;return Math.sin(x*F+t*0.5)*Math.cos(y*F*0.9-t*0.42)+0.6*Math.sin((x+y)*F*0.65-t*0.3)+0.4*Math.cos((x*2.1-y*3.4)*F*0.57+t*0.6); }
    pointer(px,py,down){ if(!down)return; const n=Math.min(this.N,((this.N*0.03)|0)+24),rd=this.w*0.03; for(let k=0;k<n;k++){const i=(Math.random()*this.N)|0;this.x[i]=px+(Math.random()-0.5)*rd;this.y[i]=py+(Math.random()-0.5)*rd;this.l[i]=44+Math.random()*44;} }
    step(){ this.t+=0.02;const w=this.w,h=this.h,e=0.012,sp=this.spd;for(let i=0;i<this.N;i++){const nx=this.x[i]/w,ny=this.y[i]/h,gx=this.pot(nx+e,ny)-this.pot(nx-e,ny),gy=this.pot(nx,ny+e)-this.pot(nx,ny-e),a=Math.atan2(-gx,gy);this.x[i]+=Math.cos(a)*sp;this.y[i]+=Math.sin(a)*sp;if(--this.l[i]<=0||this.x[i]<0||this.y[i]<0||this.x[i]>=w||this.y[i]>=h)this.spawn(i);} }
    render(ctx){ ctx.globalCompositeOperation='source-over';ctx.fillStyle='rgba(5,8,20,'+this.fade+')';ctx.fillRect(0,0,this.w,this.h);ctx.globalCompositeOperation='lighter';const P=PALS[this.pal];const s=Math.max(1,(this.w/360*this.psz)|0);for(let i=0;i<this.N;i++){ctx.fillStyle=this.l[i]>48?P[0]:P[1];ctx.fillRect(this.x[i]|0,this.y[i]|0,s,s);}ctx.globalCompositeOperation='source-over'; }
    controls(){ return [
      {t:'range',key:'spd',label:'Speed',min:0.4,max:3,step:0.05,get:()=>this.spd,set:v=>this.spd=v,fmt:v=>v.toFixed(2)},
      {t:'range',key:'fade',label:'Trails',min:0.05,max:0.4,step:0.01,get:()=>this.fade,set:v=>this.fade=v,fmt:v=>(0.45-v).toFixed(2)},
      {t:'range',key:'swirl',label:'Swirl',min:3,max:8,step:0.1,get:()=>this.freq,set:v=>this.freq=v,fmt:v=>v.toFixed(1)},
      {t:'range',key:'n',label:'Density',min:800,max:32000,step:200,get:()=>this.N,set:v=>this.setN(v),fmt:v=>(v|0).toLocaleString()},
      {t:'range',key:'glow',label:'Glow',min:0.5,max:3,step:0.1,get:()=>this.psz,set:v=>this.psz=v,fmt:v=>v.toFixed(1)+'×'},
      {t:'seg',key:'pal',label:'Palette',opts:[['aurora','Aurora'],['ember','Ember'],['ice','Ice']],get:()=>this.pal,set:v=>this.pal=v},
      {t:'button',label:'🎲 Randomize',act:()=>this.randomize()},
    ]; }
    randomize(){ this.spd=0.6+Math.random()*2.2;this.freq=3.5+Math.random()*4;this.fade=0.08+Math.random()*0.28;this.pal=['aurora','ember','ice'][Math.random()*3|0]; }
  }
  class RD {
    constructor(w,h,preset){ this.w=w;this.h=h;this.gw=96;this.gh=Math.max(24,Math.round(96*h/w));this.sub=6;this.pal=preset==='mitosis'?'ember':'teal';const P=preset==='mitosis'?[0.0367,0.0649]:[0.030,0.0595];this.F=P[0];this.k=P[1];this.du=0.16;this.reseed();this.off=document.createElement('canvas');this.off.width=this.gw;this.off.height=this.gh;this.octx=this.off.getContext('2d');this.img=this.octx.createImageData(this.gw,this.gh); }
    setGrid(gw){ this.gw=gw|0;this.gh=Math.max(24,Math.round(this.gw*this.h/this.w));this.off.width=this.gw;this.off.height=this.gh;this.img=this.octx.createImageData(this.gw,this.gh);this.reseed(); }
    reseed(){ const n=this.gw*this.gh;this.U=new Float32Array(n).fill(1);this.V=new Float32Array(n);this.Un=new Float32Array(n);this.Vn=new Float32Array(n);let s=((this.F*1e7)|0)^987;const r=()=>{s=(s*16807)%2147483647;return s/2147483647;};for(let b=0;b<38;b++){const cx=(r()*this.gw)|0,cy=(r()*this.gh)|0;for(let dy=-2;dy<=2;dy++)for(let dx=-2;dx<=2;dx++){const x=(cx+dx+this.gw)%this.gw,y=(cy+dy+this.gh)%this.gh,i=y*this.gw+x;this.V[i]=0.5;this.U[i]=0.3;}} }
    step(){ const gw=this.gw,gh=this.gh,U=this.U,V=this.V,Un=this.Un,Vn=this.Vn,F=this.F,k=this.k;for(let s=0;s<this.sub;s++){for(let y=0;y<gh;y++){const ym=(y-1+gh)%gh,yp=(y+1)%gh;for(let x=0;x<gw;x++){const xm=(x-1+gw)%gw,xp=(x+1)%gw,i=y*gw+x,u=U[i],v=V[i];const lu=(U[ym*gw+xm]+U[ym*gw+xp]+U[yp*gw+xm]+U[yp*gw+xp])*0.05+(U[ym*gw+x]+U[yp*gw+x]+U[y*gw+xm]+U[y*gw+xp])*0.2-u;const lv=(V[ym*gw+xm]+V[ym*gw+xp]+V[yp*gw+xm]+V[yp*gw+xp])*0.05+(V[ym*gw+x]+V[yp*gw+x]+V[y*gw+xm]+V[y*gw+xp])*0.2-v;const uvv=u*v*v;Un[i]=u+(this.du*lu-uvv+F*(1-u));Vn[i]=v+(0.08*lv+uvv-(F+k)*v);}}U.set(Un);V.set(Vn);} }
    pointer(px,py,down){ if(!down)return; const gx=(px/this.w*this.gw)|0,gy=(py/this.h*this.gh)|0,R=Math.max(2,(this.gw/28)|0);for(let dy=-R;dy<=R;dy++)for(let dx=-R;dx<=R;dx++){if(dx*dx+dy*dy>R*R)continue;const x=(gx+dx+this.gw)%this.gw,y=(gy+dy+this.gh)%this.gh,i=y*this.gw+x;this.V[i]=0.5;this.U[i]=0.25;} }
    render(ctx){ const d=this.img.data,V=this.V,n=this.gw*this.gh,pal=this.pal;for(let i=0;i<n;i++){const h=Math.min(1,V[i]/0.34),o=i*4;if(pal==='ember'){d[o]=18+h*236;d[o+1]=8+h*150;d[o+2]=26+h*30;}else if(pal==='mono'){const g=18+h*220;d[o]=g;d[o+1]=g;d[o+2]=g+h*10;}else{d[o]=8+h*44;d[o+1]=22+h*206;d[o+2]=34+h*150;}d[o+3]=255;}this.octx.putImageData(this.img,0,0);ctx.imageSmoothingEnabled=true;ctx.drawImage(this.off,0,0,this.w,this.h); }
    controls(){ return [
      {t:'range',key:'f',label:'Feed F',min:0.01,max:0.08,step:0.001,get:()=>this.F,set:v=>this.F=v,fmt:v=>v.toFixed(3)},
      {t:'range',key:'k',label:'Kill k',min:0.04,max:0.075,step:0.0005,get:()=>this.k,set:v=>this.k=v,fmt:v=>v.toFixed(4)},
      {t:'range',key:'rate',label:'Rate',min:2,max:12,step:1,get:()=>this.sub,set:v=>this.sub=v,fmt:v=>v|0},
      {t:'range',key:'grid',label:'Detail',min:96,max:384,step:32,get:()=>this.gw,set:v=>this.setGrid(v),fmt:v=>v+'²'},
      {t:'range',key:'du',label:'Diffuse',min:0.10,max:0.24,step:0.005,get:()=>this.du,set:v=>this.du=v,fmt:v=>v.toFixed(3)},
      {t:'seg',key:'pal',label:'Palette',opts:[['teal','Teal'],['ember','Ember'],['mono','Mono']],get:()=>this.pal,set:v=>this.pal=v},
      {t:'button',label:'🎲 Randomize',act:()=>this.randomize()},
      {t:'button',label:'Reseed',act:()=>this.reseed()},
    ]; }
    randomize(){ const P=[[0.037,0.065],[0.030,0.0595],[0.026,0.054],[0.014,0.045],[0.058,0.062],[0.022,0.051],[0.039,0.058]];const p=P[Math.random()*P.length|0];this.F=p[0];this.k=p[1];this.pal=['teal','ember','mono'][Math.random()*3|0];this.reseed(); }
    // Export fidelity: double the field past the desk cap so 4K carries genuinely
    // finer Gray–Scott structure (features live in cell units), not an upscale.
    fidelity(mode){ const t=Math.min(mode==='still'?1024:512,this.gw*2); if(t>this.gw)this.setGrid(t); }
    warmPlan(mode){ const s=130+(this.gw>>2); return {steps: mode==='still'?Math.min(400,s):Math.min(160,40+(this.gw>>3))}; }
  }
  class Slime {
    constructor(w,h,preset){ this.w=w;this.h=h;this.G=82;const G=this.G,N=G*G;this.T=new Float32Array(N);this.Tn=new Float32Array(N);this.preset=preset;this.fold=preset==='kaleido';this.pal=preset==='cosmic'?'cool':this.fold?'spectral':'warm';this.speed=2;this.decay=0.92;this.dep=5.4;this.sa=0.38;this.so=6;this.foldN=6;this.hue=0;this.NP=1500;this.ax=new Float32Array(this.NP);this.ay=new Float32Array(this.NP);this.ah=new Float32Array(this.NP);this.nodes=[];this.s=444;this.reseedAgents();if(preset==='tokyo'||preset==='growth')this.scatter(preset==='growth'?18:14);this.off=document.createElement('canvas');this.off.width=G;this.off.height=G;this.octx=this.off.getContext('2d');this.img=this.octx.createImageData(G,G); }
    r(){ this.s=(this.s*16807)%2147483647;return this.s/2147483647; }
    reseedAgents(){ const G=this.G,cx=G/2,cy=G/2;for(let i=0;i<this.NP;i++){if(this.preset==='growth'){const a=this.r()*6.283,rr=Math.sqrt(this.r())*4;this.ax[i]=cx+Math.cos(a)*rr;this.ay[i]=cy+Math.sin(a)*rr;}else{this.ax[i]=this.r()*G;this.ay[i]=this.r()*G;}this.ah[i]=this.r()*6.283;} }
    scatter(n){ this.nodes.length=0;const G=this.G,cx=G/2,cy=G/2;n=n||14;for(let i=0;i<n;i++){const a=this.r()*6.283,rr=Math.sqrt(this.r())*G*0.4;this.nodes.push({x:cx+Math.cos(a)*rr,y:cy+Math.sin(a)*rr});} }
    setGrid(G){ G=G|0;this.G=G;const N=G*G;this.T=new Float32Array(N);this.Tn=new Float32Array(N);this.off.width=G;this.off.height=G;this.img=this.octx.createImageData(G,G);this.nodes.length=0;this.reseedAgents();if(this.preset==='tokyo'||this.preset==='growth')this.scatter(this.preset==='growth'?18:14); }
    setAgents(np){ np=np|0;this.NP=np;this.ax=new Float32Array(np);this.ay=new Float32Array(np);this.ah=new Float32Array(np);this.reseedAgents(); }
    clearFood(){ this.nodes.length=0; }
    reset(){ this.T.fill(0);this.reseedAgents();this.scatter(14); }
    pointer(px,py,down){ if(down){ this.nodes.push({x:px/this.w*this.G,y:py/this.h*this.G}); } }
    sns(x,y,a){ const G=this.G,sx=(x+Math.cos(a)*this.so)|0,sy=(y+Math.sin(a)*this.so)|0;if(sx<0||sy<0||sx>=G||sy>=G)return -1;return this.T[sy*G+sx]; }
    _step(){ const G=this.G,T=this.T,Tn=this.Tn;for(const c of this.nodes){const gx=c.x|0,gy=c.y|0;for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++){const x=gx+dx,y=gy+dy;if(x<0||y<0||x>=G||y>=G)continue;const i=y*G+x;if(72>T[i])T[i]=72;}}for(let i=0;i<this.NP;i++){const x=this.ax[i],y=this.ay[i],h=this.ah[i],f=this.sns(x,y,h),fl=this.sns(x,y,h-this.sa),fr=this.sns(x,y,h+this.sa);let nh=h;if(f>=fl&&f>=fr){}else if(f<fl&&f<fr)nh+=(Math.random()<.5?-1:1)*0.45;else if(fl>fr)nh-=0.45;else nh+=0.45;let nx=x+Math.cos(nh),ny=y+Math.sin(nh);if(nx<1||ny<1||nx>=G-1||ny>=G-1){nh=Math.atan2(G/2-y,G/2-x)+Math.random()-0.5;nx=x;ny=y;}this.ax[i]=nx;this.ay[i]=ny;this.ah[i]=nh;const ci=(ny|0)*G+(nx|0);T[ci]=Math.min(T[ci]+this.dep,400);}const dk=this.decay;for(let y=0;y<G;y++){const ym=y>0?y-1:0,yp=y<G-1?y+1:y;for(let x=0;x<G;x++){const xm=x>0?x-1:0,xp=x<G-1?x+1:x;const su=T[ym*G+xm]+T[ym*G+x]+T[ym*G+xp]+T[y*G+xm]+T[y*G+x]+T[y*G+xp]+T[yp*G+xm]+T[yp*G+x]+T[yp*G+xp];Tn[y*G+x]=su*0.1111111*dk;}}T.set(Tn); }
    step(){ for(let s=0;s<this.speed;s++)this._step();this.hue+=0.7*this.speed; }
    col(h,o,d){ if(this.pal==='warm'){d[o]=20+h*232;d[o+1]=16+h*196;d[o+2]=10+h*58;}else if(this.pal==='cool'){d[o]=18+h*70;d[o+1]=28+h*150;d[o+2]=42+h*212;}else{const hh=this.hue*0.008+h*0.6;d[o]=20+h*(Math.sin(6.283*hh)*.5+.5)*235;d[o+1]=20+h*(Math.sin(6.283*(hh+.33))*.5+.5)*235;d[o+2]=20+h*(Math.sin(6.283*(hh+.66))*.5+.5)*235;} }
    render(ctx){ const G=this.G,d=this.img.data,T=this.T,N=G*G;for(let i=0;i<N;i++){const h=Math.min(1,1-Math.exp(-T[i]/26));this.col(h,i*4,d);d[i*4+3]=255;}this.octx.putImageData(this.img,0,0);if(this.fold){ctx.fillStyle='#050409';ctx.fillRect(0,0,this.w,this.h);ctx.save();ctx.translate(this.w/2,this.h/2);const R=Math.max(this.w,this.h)*0.72,nf=this.foldN,wid=Math.tan(Math.PI/nf)*R;for(let s=0;s<nf;s++){ctx.save();ctx.rotate(s*2*Math.PI/nf);if(s%2)ctx.scale(1,-1);ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(R,-wid);ctx.lineTo(R,wid);ctx.closePath();ctx.clip();ctx.imageSmoothingEnabled=true;ctx.drawImage(this.off,-R*0.05,-R*0.5,R*1.1,R);ctx.restore();}ctx.restore();}else{ctx.imageSmoothingEnabled=true;ctx.drawImage(this.off,0,0,this.w,this.h);} }
    controls(){ const b=[
      {t:'range',key:'spd',label:'Speed',min:1,max:5,step:1,get:()=>this.speed,set:v=>this.speed=v,fmt:v=>v+'×'},
      {t:'range',key:'decay',label:'Decay',min:0.86,max:0.95,step:0.005,get:()=>this.decay,set:v=>this.decay=v,fmt:v=>v.toFixed(3)},
      {t:'range',key:'dep',label:'Deposit',min:3,max:8,step:0.2,get:()=>this.dep,set:v=>this.dep=v,fmt:v=>v.toFixed(1)},
      {t:'range',key:'sense',label:'Sensor°',min:0.15,max:0.9,step:0.03,get:()=>this.sa,set:v=>this.sa=v,fmt:v=>(v*57.3|0)+'°'},
      {t:'range',key:'reach',label:'Reach',min:3,max:14,step:1,get:()=>this.so,set:v=>this.so=v,fmt:v=>v|0},
      {t:'seg',key:'grid',label:'Detail',opts:[[82,'82²'],[128,'128²'],[192,'192²'],[256,'256²'],[320,'320²']],get:()=>this.G,set:v=>this.setGrid(v)},
      {t:'range',key:'colony',label:'Colony',min:1500,max:26000,step:500,get:()=>this.NP,set:v=>this.setAgents(v),fmt:v=>(v|0).toLocaleString()+' cells'},
      {t:'seg',key:'pal',label:'Palette',opts:[['warm','Gold'],['cool','Cosmic'],['spectral','Spectral']],get:()=>this.pal,set:v=>this.pal=v}];
      if(this.fold)b.push({t:'range',key:'sym',label:'Symmetry',min:3,max:12,step:1,get:()=>this.foldN,set:v=>this.foldN=v,fmt:v=>v+'-fold'});
      b.push({t:'button',label:'Scatter nutrients',act:()=>this.scatter(14)});
      b.push({t:'button',label:'Clear food',act:()=>this.clearFood()});
      b.push({t:'button',label:'🎲 Randomize',act:()=>this.randomize()});
      b.push({t:'button',label:'Reset',act:()=>this.reset()});
      return b; }
    randomize(){ this.decay=0.87+Math.random()*0.07;this.dep=3.5+Math.random()*4;this.speed=1+(Math.random()*4|0);this.pal=['warm','cool','spectral'][Math.random()*3|0];if(this.fold)this.foldN=3+(Math.random()*9|0);this.reset(); }
    // Export fidelity: finer trail grid + a proportionally larger colony, so 4K
    // shows more vessels, not fatter pixels. Area-scaled agents keep coverage.
    fidelity(mode){ const still=mode==='still',g0=this.G,t=Math.min(still?640:448,g0*2);
      if(t>g0){ const r=t/g0; this.setGrid(t); this.setAgents(Math.min(still?60000:40000,Math.round(this.NP*r*r))); } }
    warmPlan(mode){ const s=Math.round(130*Math.sqrt(this.G/82)); return {steps: mode==='still'?s:Math.max(40,s>>1)}; }
  }
  class Boids {
    constructor(w,h){ this.w=w;this.h=h;this.mode='roost';this.cohW=0.06;this.trail=0.2;this.wild=true;this.fal={x:-1e5,y:-1e5,vx:0,vy:0,active:false,cool:120};this.ptr={x:-1e5,y:-1e5,on:false};this.sep=1;this.top=2.3;this.gusts=[];this.accumulates=true;this.setN(320); }
    setN(n){ this.N=n|0;const N=this.N;this.x=new Float32Array(N);this.y=new Float32Array(N);this.vx=new Float32Array(N);this.vy=new Float32Array(N);let s=77;const r=()=>{s=(s*16807)%2147483647;return s/2147483647;};for(let i=0;i<N;i++){this.x[i]=r()*this.w;this.y[i]=r()*this.h;const a=r()*6.283;this.vx[i]=Math.cos(a)*1.5;this.vy[i]=Math.sin(a)*1.5;} }
    gust(){ this.gusts.push({x:this.ptr.on?this.ptr.x:this.w/2,y:this.ptr.on?this.ptr.y:this.h/2,t:1}); }
    pointer(x,y,down){ this.ptr.x=x;this.ptr.y=y;this.ptr.on=true;if(down)this.gusts.push({x,y,t:1}); }
    step(){ const N=this.N,x=this.x,y=this.y,vx=this.vx,vy=this.vy,w=this.w,h=this.h,cw=this.cohW;
      // falcon
      if(this.mode==='falcon'&&this.ptr.on){this.fal.active=true;this.fal.x=this.ptr.x;this.fal.y=this.ptr.y;}
      else if(this.wild){ if(!this.fal.active){ if(--this.fal.cool<=0){let cx=0,cy=0;for(let i=0;i<N;i++){cx+=x[i];cy+=y[i];}cx/=N;cy/=N;const e=Math.random()*4|0;this.fal.x=e===1?w+30:e===3?-30:Math.random()*w;this.fal.y=e===0?-30:e===2?h+30:Math.random()*h;const a=Math.atan2(cy-this.fal.y,cx-this.fal.x);this.fal.vx=Math.cos(a)*4.5;this.fal.vy=Math.sin(a)*4.5;this.fal.active=true;} } else { this.fal.x+=this.fal.vx;this.fal.y+=this.fal.vy;if(this.fal.x<-80||this.fal.x>w+80||this.fal.y<-80||this.fal.y>h+80){this.fal.active=false;this.fal.cool=120+Math.random()*150;} } }
      else this.fal.active=false;
      const falR=this.mode==='falcon'?150:120;
      // spatial hash (cell = 26px = the alignment/cohesion radius) so the flock scales past O(N²)
      const cs=26,cols=(w/cs|0)+3,rows=(h/cs|0)+3;
      if(!this._heads||this._heads.length!==cols*rows)this._heads=new Int32Array(cols*rows);
      if(!this._next||this._next.length!==N)this._next=new Int32Array(N);
      const heads=this._heads,nxt=this._next;heads.fill(-1);
      const cellX=px=>{let c=(px/cs|0)+1;return c<0?0:c>=cols?cols-1:c;},cellY=py=>{let c=(py/cs|0)+1;return c<0?0:c>=rows?rows-1:c;};
      for(let i=0;i<N;i++){const ci=cellY(y[i])*cols+cellX(x[i]);nxt[i]=heads[ci];heads[ci]=i;}
      for(let i=0;i<N;i++){let ax=0,ay=0,cx=0,cy=0,sx=0,sy=0,na=0;const xi=x[i],yi=y[i];
        let bcx=cellX(xi);bcx=bcx<1?1:bcx>=cols-1?cols-2:bcx;let bcy=cellY(yi);bcy=bcy<1?1:bcy>=rows-1?rows-2:bcy;
        for(let oy=-1;oy<=1;oy++)for(let ox=-1;ox<=1;ox++)for(let j=heads[(bcy+oy)*cols+(bcx+ox)];j!==-1;j=nxt[j]){if(j===i)continue;const dx=x[j]-xi,dy=y[j]-yi,d2=dx*dx+dy*dy;if(d2<676){ax+=vx[j];ay+=vy[j];cx+=x[j];cy+=y[j];na++;if(d2<81&&d2>0.01){const inv=1/Math.sqrt(d2);sx-=dx*inv;sy-=dy*inv;}}}
        let fx=0,fy=0;if(na){ax/=na;ay/=na;fx+=(ax-vx[i])*0.06;fy+=(ay-vy[i])*0.06;fx+=(cx/na-xi)*cw*0.033;fy+=(cy/na-yi)*cw*0.033;}fx+=sx*0.09*this.sep;fy+=sy*0.09*this.sep;
        if(xi<18)fx+=0.3;else if(xi>w-18)fx-=0.3;if(yi<18)fy+=0.3;else if(yi>h-18)fy-=0.3;let panic=0;
        if(this.ptr.on&&this.mode!=='falcon'){const dx=this.ptr.x-xi,dy=this.ptr.y-yi,d2=dx*dx+dy*dy;if(d2<130*130&&d2>1){const inv=1/Math.sqrt(d2),f=1-Math.sqrt(d2)/130;if(this.mode==='roost'){fx+=dx*inv*0.16*f;fy+=dy*inv*0.16*f;}else{fx-=dx*inv*0.9*f;fy-=dy*inv*0.9*f;panic=f;}}}
        if(this.fal.active){const dx=this.fal.x-xi,dy=this.fal.y-yi,d2=dx*dx+dy*dy;if(d2<falR*falR&&d2>1){const inv=1/Math.sqrt(d2),f=1-Math.sqrt(d2)/falR;fx-=dx*inv*1.4*f*f;fy-=dy*inv*1.4*f*f;if(f>panic)panic=f;}}
        for(let g=0;g<this.gusts.length;g++){const G=this.gusts[g],dx=xi-G.x,dy=yi-G.y,d2=dx*dx+dy*dy;if(d2<160*160&&d2>1){const inv=1/Math.sqrt(d2),f=G.t*(1-Math.sqrt(d2)/160);fx+=dx*inv*2.4*f;fy+=dy*inv*2.4*f;}}
        vx[i]+=fx;vy[i]+=fy;let sp=Math.hypot(vx[i],vy[i]);const top=this.top+panic*1.6;if(sp>top){vx[i]=vx[i]/sp*top;vy[i]=vy[i]/sp*top;}else if(sp<1&&sp>0){vx[i]=vx[i]/sp;vy[i]=vy[i]/sp;}x[i]+=vx[i];y[i]+=vy[i];}
      for(let g=this.gusts.length-1;g>=0;g--){this.gusts[g].t-=0.05;if(this.gusts[g].t<=0)this.gusts.splice(g,1);} }
    render(ctx){ ctx.fillStyle='rgba(11,13,24,'+this.trail+')';ctx.fillRect(0,0,this.w,this.h);ctx.globalCompositeOperation='lighter';ctx.lineWidth=Math.max(1,this.w/360);for(let i=0;i<this.N;i++){const a=Math.atan2(this.vy[i],this.vx[i]);ctx.strokeStyle='hsla('+(30+((a+3.14159)/6.2832)*212)+',85%,63%,0.6)';ctx.beginPath();ctx.moveTo(this.x[i],this.y[i]);ctx.lineTo(this.x[i]-this.vx[i]*2.4,this.y[i]-this.vy[i]*2.4);ctx.stroke();}ctx.globalCompositeOperation='source-over';if(this.fal.active){ctx.fillStyle='rgba(239,75,82,.95)';ctx.beginPath();ctx.arc(this.fal.x,this.fal.y,Math.max(3,this.w/150),0,6.2832);ctx.fill();} }
    controls(){ return [
      {t:'seg',key:'cursor',label:'Cursor',opts:[['roost','Roost'],['scatter','Scatter'],['falcon','Falcon']],get:()=>this.mode,set:v=>this.mode=v},
      {t:'range',key:'n',label:'Flock',min:200,max:6000,step:100,get:()=>this.N,set:v=>this.setN(v),fmt:v=>(v|0).toLocaleString()+' birds'},
      {t:'range',key:'coh',label:'Cohesion',min:0,max:2.4,step:0.1,get:()=>this.cohW/0.06,set:v=>this.cohW=v*0.06,fmt:v=>v.toFixed(1)},
      {t:'range',key:'sep',label:'Spacing',min:0,max:2.5,step:0.1,get:()=>this.sep,set:v=>this.sep=v,fmt:v=>v.toFixed(1)},
      {t:'range',key:'spd',label:'Speed',min:1.4,max:4,step:0.1,get:()=>this.top,set:v=>this.top=v,fmt:v=>v.toFixed(1)},
      {t:'range',key:'trail',label:'Trails',min:0.08,max:0.4,step:0.02,get:()=>this.trail,set:v=>this.trail=v,fmt:v=>(0.48-v).toFixed(2)},
      {t:'toggle',key:'wild',label:'Wild falcon',get:()=>this.wild,set:v=>this.wild=v},
      {t:'button',label:'Gust',act:()=>this.gust()},
      {t:'button',label:'🎲 Randomize',act:()=>this.randomize()},
    ]; }
    randomize(){ this.cohW=Math.random()*0.14;this.trail=0.1+Math.random()*0.28;this.mode=['roost','scatter','falcon'][Math.random()*3|0]; }
  }
  // --- Lenia: continuous cellular automata — smooth, self-organising lifeforms ---
  class Lenia {
    constructor(w,h,preset){ this.w=w;this.h=h;this.G=72;this.R=10;this.dt=0.15;this.mu=0.135;this.sig=0.028;this.pal='plasma';this.s=98765;
      this._kernel();this.A=new Float32Array(this.G*this.G);this.B=new Float32Array(this.G*this.G);this.seed();
      this.off=document.createElement('canvas');this.off.width=this.G;this.off.height=this.G;this.octx=this.off.getContext('2d');this.img=this.octx.createImageData(this.G,this.G); }
    _rand(){ this.s=(this.s*16807)%2147483647;return this.s/2147483647; }
    _kernel(){ const R=this.R,ox=[],oy=[],wt=[];let sum=0;for(let dy=-R;dy<=R;dy++)for(let dx=-R;dx<=R;dx++){const r=Math.sqrt(dx*dx+dy*dy)/R;if(r>1||r<1e-6)continue;const k=Math.exp(-((r-0.5)*(r-0.5))/(2*0.15*0.15));ox.push(dx);oy.push(dy);wt.push(k);sum+=k;}this.koX=Int16Array.from(ox);this.koY=Int16Array.from(oy);this.kw=Float32Array.from(wt.map(v=>v/sum)); }
    seed(){ const G=this.G,A=this.A,N=G*G;for(let i=0;i<N;i++)A[i]=this._rand()<0.5?this._rand():0; }
    stamp(gx,gy){ const G=this.G,A=this.A,r=6;gx|=0;gy|=0;for(let dy=-r;dy<=r;dy++)for(let dx=-r;dx<=r;dx++){if(dx*dx+dy*dy>r*r)continue;let x=gx+dx,y=gy+dy;if(x<0)x+=G;else if(x>=G)x-=G;if(y<0)y+=G;else if(y>=G)y-=G;const i=y*G+x;A[i]=Math.min(1,A[i]+0.7);} }
    pointer(px,py,down){ if(!down)return;this.stamp(px/this.w*this.G,py/this.h*this.G); }
    step(){ const G=this.G,A=this.A,B=this.B,koX=this.koX,koY=this.koY,kw=this.kw,K=kw.length,mu=this.mu,sig=this.sig,dt=this.dt;
      for(let y=0;y<G;y++){const row=y*G;for(let x=0;x<G;x++){let u=0;for(let k=0;k<K;k++){let xx=x+koX[k];if(xx<0)xx+=G;else if(xx>=G)xx-=G;let yy=y+koY[k];if(yy<0)yy+=G;else if(yy>=G)yy-=G;u+=A[yy*G+xx]*kw[k];}const g=2*Math.exp(-((u-mu)*(u-mu))/(2*sig*sig))-1;let v=A[row+x]+dt*g;B[row+x]=v<0?0:v>1?1:v;}}A.set(B); }
    render(ctx){ const G=this.G,d=this.img.data,A=this.A,N=G*G,pal=this.pal;for(let i=0;i<N;i++){const h=A[i],o=i*4;let r,g,b;if(pal==='plasma'){r=13+h*242;g=8+h*80+h*h*90;b=70+h*150-h*h*90;}else if(pal==='aurora'){r=8+h*70;g=18+h*225;b=38+h*180;}else{const v=h*255;r=v;g=v;b=v;}d[o]=r;d[o+1]=g;d[o+2]=b;d[o+3]=255;}this.octx.putImageData(this.img,0,0);ctx.imageSmoothingEnabled=true;ctx.drawImage(this.off,0,0,this.w,this.h); }
    randomize(){ this.mu=0.12+this._rand()*0.06;this.sig=0.022+this._rand()*0.02;this.dt=0.10+this._rand()*0.10;this.seed(); }
    // Export fidelity (stills only): double the world AND the kernel radius so the
    // physics is preserved while every lifeform carries twice the cell detail.
    // Video stays at the live grid — the doubled kernel is too heavy in real time.
    fidelity(mode){ if(mode!=='still')return; this.G=144; this.R=Math.min(24,this.R*2); this._kernel();
      this.A=new Float32Array(this.G*this.G); this.B=new Float32Array(this.G*this.G); this.seed();
      this.off.width=this.G; this.off.height=this.G; this.img=this.octx.createImageData(this.G,this.G); }
    warmPlan(mode){ return {steps: mode==='still'?80:40}; }
    controls(){ return [
      {t:'range',key:'mu',label:'Growth μ',min:0.08,max:0.30,step:0.005,get:()=>this.mu,set:v=>this.mu=v,fmt:v=>v.toFixed(3)},
      {t:'range',key:'sig',label:'Width σ',min:0.012,max:0.050,step:0.001,get:()=>this.sig,set:v=>this.sig=v,fmt:v=>v.toFixed(3)},
      {t:'range',key:'dt',label:'Rate',min:0.05,max:0.25,step:0.01,get:()=>this.dt,set:v=>this.dt=v,fmt:v=>v.toFixed(2)},
      {t:'range',key:'r',label:'Radius',min:6,max:15,step:1,get:()=>this.R,set:v=>{this.R=v;this._kernel();},fmt:v=>v|0},
      {t:'seg',key:'pal',label:'Palette',opts:[['plasma','Plasma'],['aurora','Aurora'],['mono','Mono']],get:()=>this.pal,set:v=>this.pal=v},
      {t:'button',label:'🎲 Randomize',act:()=>this.randomize()},
      {t:'button',label:'Reseed',act:()=>this.seed()},
    ]; }
  }
  // --- Cymatics: Chladni standing-wave plate; sand collects on the nodal lines ---
  class Cymatics {
    constructor(w,h,preset){ this.w=w;this.h=h;this.G=200;this.m=5;this.n=3;this.sharp=42;this.pal='mono';this.t=0;this.auto=true;this.spd=1;this.pokes=[];
      this.off=document.createElement('canvas');this.off.width=this.G;this.off.height=this.G;this.octx=this.off.getContext('2d');this.img=this.octx.createImageData(this.G,this.G); }
    step(){ this.t+=0.008*this.spd;for(let i=this.pokes.length-1;i>=0;i--){this.pokes[i].t-=0.02;if(this.pokes[i].t<=0)this.pokes.splice(i,1);} }
    pointer(px,py,down){ if(down)this.pokes.push({x:px/this.w,y:py/this.h,t:1}); }
    render(ctx){ const G=this.G,d=this.img.data,pal=this.pal;const drift=this.auto?Math.sin(this.t)*0.7:0;const m=this.m+drift,n=this.n-drift,ph=Math.sin(this.t*1.3)*0.45+1;
      for(let y=0;y<G;y++){const fy=y/(G-1);for(let x=0;x<G;x++){const fx=x/(G-1);let f=(Math.cos(n*Math.PI*fx)*Math.cos(m*Math.PI*fy)-Math.cos(m*Math.PI*fx)*Math.cos(n*Math.PI*fy))*ph;for(let pk=0;pk<this.pokes.length;pk++){const P=this.pokes[pk],ex=fx-P.x,ey=fy-P.y,dd=Math.sqrt(ex*ex+ey*ey);f+=Math.cos(dd*38-this.t*7)*P.t*Math.exp(-dd*3.5);}const s=Math.exp(-f*f*this.sharp);const o=(y*G+x)*4;let r,g,b;if(pal==='mono'){const v=18+s*236;r=v;g=v;b=v;}else if(pal==='ember'){r=20+s*235;g=10+s*150;b=8+s*40;}else{r=14+s*60;g=24+s*205;b=40+s*150;}d[o]=r;d[o+1]=g;d[o+2]=b;d[o+3]=255;}}this.octx.putImageData(this.img,0,0);ctx.imageSmoothingEnabled=true;ctx.drawImage(this.off,0,0,this.w,this.h); }
    randomize(){ this.m=2+(Math.random()*8|0);this.n=1+(Math.random()*7|0);this.sharp=25+Math.random()*50|0; }
    // Export fidelity: the plate is closed-form, so stills are computed at the true
    // output height (2160² for 4K) — pixel-exact nodal lines; video runs at 480².
    fidelity(mode){ const t=mode==='still'?this.h:480; if(t>this.G){ this.G=t; this.off.width=t; this.off.height=t; this.img=this.octx.createImageData(t,t); } }
    warmPlan(){ return {steps:8}; }
    controls(){ return [
      {t:'range',key:'m',label:'Mode m',min:1,max:11,step:1,get:()=>this.m,set:v=>this.m=v,fmt:v=>v|0},
      {t:'range',key:'n',label:'Mode n',min:1,max:11,step:1,get:()=>this.n,set:v=>this.n=v,fmt:v=>v|0},
      {t:'range',key:'grain',label:'Grain',min:15,max:80,step:1,get:()=>this.sharp,set:v=>this.sharp=v,fmt:v=>v|0},
      {t:'seg',key:'pal',label:'Palette',opts:[['mono','Sand'],['ember','Ember'],['teal','Teal']],get:()=>this.pal,set:v=>this.pal=v},
      {t:'range',key:'spd',label:'Speed',min:0.2,max:3,step:0.1,get:()=>this.spd,set:v=>this.spd=v,fmt:v=>v.toFixed(1)+'×'},
      {t:'toggle',key:'auto',label:'Auto-morph',get:()=>this.auto,set:v=>this.auto=v},
      {t:'button',label:'🎲 Randomize',act:()=>this.randomize()},
    ]; }
  }
  // --- DLA: diffusion-limited aggregation — dendritic crystal growth ---
  class DLA {
    constructor(w,h,preset){ this.w=w;this.h=h;this.G=200;this.N=this.G*this.G;this.grid=new Uint8Array(this.N);this.age=new Float32Array(this.N);this.pal='ice';this.rate=700;this.t=0;this.NW=1600;this.s=31337;
      this.cx=this.G>>1;this.cy=this.G>>1;this.rad=6;this.bias=0.25;
      this.wx=new Float32Array(this.NW);this.wy=new Float32Array(this.NW);this.reset();
      this.off=document.createElement('canvas');this.off.width=this.G;this.off.height=this.G;this.octx=this.off.getContext('2d');this.img=this.octx.createImageData(this.G,this.G); }
    _r(){ this.s=(this.s*16807)%2147483647;return this.s/2147483647; }
    reset(){ this.grid.fill(0);this.age.fill(0);this.t=0;this.rad=5;const G=this.G,c=(G/2)|0;for(let dy=-2;dy<=2;dy++)for(let dx=-2;dx<=2;dx++){if(dx*dx+dy*dy<=4){const i=(c+dy)*G+(c+dx);this.grid[i]=1;this.age[i]=1;}}for(let i=0;i<this.NW;i++)this._spawn(i); }
    _spawn(i){ const a=this._r()*6.283,rr=this.rad+3+this._r()*5;this.wx[i]=this.cx+Math.cos(a)*rr;this.wy[i]=this.cy+Math.sin(a)*rr; }
    setWalkers(n){ n=n|0;const old=this.NW;this.NW=n;const nx=new Float32Array(n),ny=new Float32Array(n);for(let i=0;i<n;i++){if(i<old){nx[i]=this.wx[i];ny[i]=this.wy[i];}else{nx[i]=this._r()*this.G;ny[i]=this._r()*this.G;}}this.wx=nx;this.wy=ny; }
    seedAt(gx,gy){ const G=this.G;gx|=0;gy|=0;if(gx>=0&&gy>=0&&gx<G&&gy<G){this.grid[gy*G+gx]=1;this.age[gy*G+gx]=this.t||1;} }
    pointer(px,py,down){ if(!down)return;this.seedAt(px/this.w*this.G,py/this.h*this.G); }
    step(){ this.t++;const G=this.G,grid=this.grid,age=this.age,cx=this.cx,cy=this.cy;let stuck=0;const killR=Math.min(G*0.72,this.rad*1.7);
      for(let i=0;i<this.NW;i++){ let x,y;const wxi=this.wx[i]|0,wyi=this.wy[i]|0;
        if(this._r()<this.bias){ x=wxi+(cx>wxi?1:cx<wxi?-1:0);y=wyi+(cy>wyi?1:cy<wyi?-1:0); }
        else { x=wxi+(this._r()*3|0)-1;y=wyi+(this._r()*3|0)-1; }
        if(x<0)x=0;else if(x>=G)x=G-1;if(y<0)y=0;else if(y>=G)y=G-1;
        const ddx=x-cx,ddy=y-cy;if(ddx*ddx+ddy*ddy>killR*killR){this._spawn(i);continue;}
        this.wx[i]=x;this.wy[i]=y;
        if(stuck<this.rate){let hit=false;for(let dy=-1;dy<=1&&!hit;dy++)for(let dx=-1;dx<=1;dx++){const xx=x+dx,yy=y+dy;if(xx<0||yy<0||xx>=G||yy>=G)continue;if(grid[yy*G+xx]){hit=true;break;}}
          if(hit){grid[y*G+x]=1;age[y*G+x]=this.t;stuck++;const dc=Math.sqrt(ddx*ddx+ddy*ddy);if(dc+4>this.rad)this.rad=Math.min(G*0.5-2,dc+4);this._spawn(i);}} } }
    render(ctx){ const G=this.G,d=this.img.data,grid=this.grid,age=this.age,N=this.N,t=Math.max(1,this.t),pal=this.pal;for(let i=0;i<N;i++){const o=i*4;if(grid[i]){const a=age[i]/t;let r,g,b;if(pal==='ice'){r=110+a*145;g=175+a*80;b=228+a*27;}else if(pal==='ember'){r=205+a*50;g=55+a*165;b=18+a*46;}else{const v=95+a*160;r=v;g=v;b=v;}d[o]=r;d[o+1]=g;d[o+2]=b;}else{d[o]=6;d[o+1]=7;d[o+2]=12;}d[o+3]=255;}
      for(let i=0;i<this.NW;i+=3){const x=this.wx[i]|0,y=this.wy[i]|0,o=(y*G+x)*4;if(!grid[y*G+x]){d[o]=Math.min(255,d[o]+40);d[o+1]=Math.min(255,d[o+1]+44);d[o+2]=Math.min(255,d[o+2]+60);}}
      this.octx.putImageData(this.img,0,0);ctx.imageSmoothingEnabled=false;ctx.drawImage(this.off,0,0,this.w,this.h); }
    randomize(){ this.rate=300+(Math.random()*1600|0);this.pal=['ice','ember','mono'][Math.random()*3|0]; }
    // Export fidelity: a larger lattice with more walkers, then (warmPlan) the
    // crystal is grown until it actually fills the frame — real dendrites at 4K.
    fidelity(mode){ const t=mode==='still'?600:320; if(t>this.G){ this.G=t; this.N=t*t; this.grid=new Uint8Array(this.N); this.age=new Float32Array(this.N);
      this.cx=t>>1; this.cy=t>>1; this.off.width=t; this.off.height=t; this.img=this.octx.createImageData(t,t);
      this.setWalkers(Math.min(27000,this.NW*3)); this.reset(); } }
    warmPlan(mode){ return {steps: mode==='still'?6000:2000, done:()=>this.rad>=this.G*0.42}; }
    controls(){ return [
      {t:'range',key:'rate',label:'Growth rate',min:100,max:5000,step:100,get:()=>this.rate,set:v=>this.rate=v,fmt:v=>(v|0)+'/f'},
      {t:'range',key:'walkers',label:'Walkers',min:400,max:9000,step:200,get:()=>this.NW,set:v=>this.setWalkers(v),fmt:v=>(v|0).toLocaleString()},
      {t:'range',key:'bias',label:'Density',min:0.05,max:0.55,step:0.05,get:()=>this.bias,set:v=>this.bias=v,fmt:v=>v.toFixed(2)},
      {t:'seg',key:'pal',label:'Palette',opts:[['ice','Frost'],['ember','Ember'],['mono','Silver']],get:()=>this.pal,set:v=>this.pal=v},
      {t:'button',label:'🎲 Randomize',act:()=>this.randomize()},
      {t:'button',label:'Reset',act:()=>this.reset()},
    ]; }
  }
  // --- Starling Storm: Flock2-style murmuration — orientation waves, banking flight, a stooping predator, rendered as a dusk density cloud ---
  class Starling {
    constructor(w,h){ this.w=w;this.h=h;this.dg=Math.max(120,Math.min(240,(Math.max(w,h)/6)|0));this.coh=0.7;this.turn=0.15;this.sep=1;this.cruise=2.9;this.hunt=true;
      this.pred={x:-1e5,y:-1e5,active:false,cool:90,vx:0,vy:0,manual:false};this.dens=new Float32Array(this.dg*this.dg);
      this.off=document.createElement('canvas');this.off.width=this.dg;this.off.height=this.dg;this.octx=this.off.getContext('2d');this.img=this.octx.createImageData(this.dg,this.dg);this.setN(2600); }
    setN(n){ this.N=n|0;const N=this.N;this.x=new Float32Array(N);this.y=new Float32Array(N);this.vx=new Float32Array(N);this.vy=new Float32Array(N);let s=91;const r=()=>{s=(s*16807)%2147483647;return s/2147483647;};const cx=this.w/2,cy=this.h/2;for(let i=0;i<N;i++){const a=r()*6.283,rr=Math.sqrt(r())*Math.min(this.w,this.h)*0.42;this.x[i]=cx+Math.cos(a)*rr;this.y[i]=cy+Math.sin(a)*rr;const va=r()*6.283;this.vx[i]=Math.cos(va)*2;this.vy[i]=Math.sin(va)*2;} }
    pointer(px,py,down){ this.pred.x=px;this.pred.y=py;this.pred.manual=down;if(down)this.pred.active=true; }
    step(){ const N=this.N,x=this.x,y=this.y,vx=this.vx,vy=this.vy,w=this.w,h=this.h,cx=w/2,cy=h/2,P=this.pred;
      if(P.manual){ P.active=true; }
      else if(this.hunt){ if(!P.active){ if(--P.cool<=0){ let mx=0,my=0;for(let i=0;i<N;i++){mx+=x[i];my+=y[i];}mx/=N;my/=N;const e=Math.random()*4|0;P.x=e===1?w+40:e===3?-40:Math.random()*w;P.y=e===0?-40:e===2?h+40:Math.random()*h;const a=Math.atan2(my-P.y,mx-P.x);P.vx=Math.cos(a)*5.5;P.vy=Math.sin(a)*5.5;P.active=true; } } else { P.x+=P.vx;P.y+=P.vy;if(P.x<-90||P.x>w+90||P.y<-90||P.y>h+90){P.active=false;P.cool=90+Math.random()*130;} } }
      else P.active=false;
      const cs=30,cols=(w/cs|0)+3,rows=(h/cs|0)+3;if(!this._heads||this._heads.length!==cols*rows)this._heads=new Int32Array(cols*rows);if(!this._next||this._next.length!==N)this._next=new Int32Array(N);const heads=this._heads,nxt=this._next;heads.fill(-1);
      const cX=p=>{let c=(p/cs|0)+1;return c<0?0:c>=cols?cols-1:c;},cY=p=>{let c=(p/cs|0)+1;return c<0?0:c>=rows?rows-1:c;};
      for(let i=0;i<N;i++){const ci=cY(y[i])*cols+cX(x[i]);nxt[i]=heads[ci];heads[ci]=i;}
      const turn=this.turn,cohW=this.coh*0.0035,sepW=0.9*this.sep,cru=this.cruise;
      for(let i=0;i<N;i++){const xi=x[i],yi=y[i],hvx=vx[i],hvy=vy[i];let ax=0,ay=0,mx=0,my=0,sx=0,sy=0,na=0;let bcx=cX(xi);bcx=bcx<1?1:bcx>=cols-1?cols-2:bcx;let bcy=cY(yi);bcy=bcy<1?1:bcy>=rows-1?rows-2:bcy;
        for(let oy=-1;oy<=1;oy++)for(let ox=-1;ox<=1;ox++)for(let j=heads[(bcy+oy)*cols+(bcx+ox)];j!==-1;j=nxt[j]){if(j===i)continue;const dx=x[j]-xi,dy=y[j]-yi,d2=dx*dx+dy*dy;if(d2<900){ax+=vx[j];ay+=vy[j];mx+=x[j];my+=y[j];na++;if(d2<250&&d2>0.01){const inv=1/Math.sqrt(d2);sx-=dx*inv;sy-=dy*inv;}}}
        let dvx=hvx,dvy=hvy;if(na){ax/=na;ay/=na;mx=mx/na-xi;my=my/na-yi;dvx=hvx+(ax-hvx)*0.12+mx*cohW+sx*sepW;dvy=hvy+(ay-hvy)*0.12+my*cohW+sy*sepW;}
        dvx+=(cx-xi)*0.00034;dvy+=(cy-yi)*0.00034;
        if(P.active){const dx=P.x-xi,dy=P.y-yi,d2=dx*dx+dy*dy;if(d2<150*150&&d2>1){const inv=1/Math.sqrt(d2),ff=1-Math.sqrt(d2)/150;dvx-=dx*inv*3.2*ff*ff;dvy-=dy*inv*3.2*ff*ff;}}
        const cur=Math.atan2(hvy,hvx),des=Math.atan2(dvy,dvx);let da=des-cur;while(da>Math.PI)da-=6.283;while(da<-Math.PI)da+=6.283;const nh=cur+(da>turn?turn:da<-turn?-turn:da);let sp=Math.hypot(hvx,hvy);sp+=(cru-sp)*0.06;vx[i]=Math.cos(nh)*sp;vy[i]=Math.sin(nh)*sp;x[i]+=vx[i];y[i]+=vy[i];if(x[i]<-25)x[i]=w+25;else if(x[i]>w+25)x[i]=-25;if(y[i]<-25)y[i]=h+25;else if(y[i]>h+25)y[i]=-25;}}
    render(ctx){ const G=this.dg,dens=this.dens,d=this.img.data;for(let i=0;i<dens.length;i++)dens[i]*=0.66;
      for(let i=0;i<this.N;i++){const gx=(this.x[i]/this.w*G)|0,gy=(this.y[i]/this.h*G)|0;if(gx<1||gy<1||gx>=G-1||gy>=G-1)continue;const b=gy*G+gx;dens[b]+=1;dens[b-1]+=0.35;dens[b+1]+=0.35;dens[b-G]+=0.35;dens[b+G]+=0.35;}
      const gain=1.5*(this._gain||1);
      for(let y=0;y<G;y++){const fy=y/(G-1),skyR=250-fy*182,skyG=182-fy*132,skyB=152-fy*66;for(let x=0;x<G;x++){const i=y*G+x,o=i*4;let dv=1-Math.exp(-dens[i]*gain);const k=1-dv*0.93;d[o]=(skyR*k+dv*12)|0;d[o+1]=(skyG*k+dv*9)|0;d[o+2]=(skyB*k+dv*16)|0;d[o+3]=255;}}
      this.octx.putImageData(this.img,0,0);ctx.imageSmoothingEnabled=true;ctx.drawImage(this.off,0,0,this.w,this.h);
      if(this.pred.active){ctx.fillStyle='rgba(18,12,22,.92)';ctx.beginPath();ctx.arc(this.pred.x,this.pred.y,Math.max(3,this.w/240),0,6.283);ctx.fill();} }
    randomize(){ this.coh=0.35+Math.random()*1.2;this.turn=0.1+Math.random()*0.12;this.sep=0.5+Math.random()*1.3;this.setN([2000,3000,4200,5600][Math.random()*4|0]); }
    // Export fidelity: finer density cloud (birds resolve as birds, not blur).
    // The splat gain scales with cell area so the flock keeps its optical weight.
    fidelity(mode){ const t=mode==='still'?Math.min(720,(this.h/3)|0):480;
      if(t>this.dg){ this._gain=(t/this.dg)*(t/this.dg); this.dg=t; this.dens=new Float32Array(t*t); this.off.width=t; this.off.height=t; this.img=this.octx.createImageData(t,t); } }
    controls(){ return [
      {t:'range',key:'n',label:'Flock',min:800,max:8000,step:200,get:()=>this.N,set:v=>this.setN(v),fmt:v=>(v|0).toLocaleString()+' birds'},
      {t:'range',key:'coh',label:'Cohesion',min:0.2,max:2.6,step:0.1,get:()=>this.coh,set:v=>this.coh=v,fmt:v=>v.toFixed(1)},
      {t:'range',key:'sep',label:'Spacing',min:0.2,max:2.2,step:0.1,get:()=>this.sep,set:v=>this.sep=v,fmt:v=>v.toFixed(1)},
      {t:'range',key:'turn',label:'Agility',min:0.06,max:0.26,step:0.01,get:()=>this.turn,set:v=>this.turn=v,fmt:v=>v.toFixed(2)},
      {t:'range',key:'spd',label:'Speed',min:1.8,max:4.5,step:0.1,get:()=>this.cruise,set:v=>this.cruise=v,fmt:v=>v.toFixed(1)},
      {t:'toggle',key:'hunt',label:'Predator',get:()=>this.hunt,set:v=>this.hunt=v},
      {t:'button',label:'🎲 Randomize',act:()=>this.randomize()},
    ]; }
  }
  // --- Fractal Worlds: an animated Julia/Mandelbrot builder — morphing worlds; click to seed ---
  class Fractal {
    constructor(w,h){ this.w=w;this.h=h;this.G=Math.min(440,Math.max(300,(Math.max(w,h)/2.6)|0));this.maxI=90;this.mode='julia';this.zoom=1.4;this.t=0;this.pal='fire';this.autoC=true;this.morph=1;this.cr=-0.4;this.ci=0.6;
      this.off=document.createElement('canvas');this.off.width=this.G;this.off.height=this.G;this.octx=this.off.getContext('2d');this.img=this.octx.createImageData(this.G,this.G); }
    step(){ this.t+=0.0035*this.morph;if(this.autoC&&this.mode==='julia'){this.cr=0.7885*Math.cos(this.t*1.25);this.ci=0.7885*Math.sin(this.t*1.25);} }
    _col(mu,d,o){ const pal=this.pal,p=mu*0.38;let r,g,b;
      if(pal==='fire'){ r=170+85*Math.sin(p);g=80+95*Math.sin(p-1.15);b=30+70*Math.sin(p-2.4); }
      else if(pal==='ice'){ r=60+80*Math.sin(p+3.1);g=130+120*Math.sin(p+1.0);b=170+85*Math.sin(p); }
      else { const q=p+this.t*0.6;r=128+127*Math.sin(q);g=128+127*Math.sin(q+2.094);b=128+127*Math.sin(q+4.188); }
      d[o]=r<0?0:r>255?255:r;d[o+1]=g<0?0:g>255?255:g;d[o+2]=b<0?0:b>255?255:b; }
    _scan(py,iw,ih,d){ const maxI=this.maxI,z=this.zoom,jul=this.mode==='julia',cr=this.cr,ci=this.ci,zx=z*iw/ih;
      const iy=(py/ih-0.5)*2*z; for(let px=0;px<iw;px++){ const ix=(px/iw-0.5)*2*zx;
        let zr,zi,ar,ai; if(jul){zr=ix;zi=iy;ar=cr;ai=ci;}else{zr=0;zi=0;ar=ix-0.6;ai=iy;}
        let i=0,zr2=zr*zr,zi2=zi*zi; for(;i<maxI&&zr2+zi2<=16;i++){zi=2*zr*zi+ai;zr=zr2-zi2+ar;zr2=zr*zr;zi2=zi*zi;}
        const o=(py*iw+px)*4; if(i>=maxI){d[o]=6;d[o+1]=4;d[o+2]=12;}else{const mu=i+1-Math.log(Math.log(Math.sqrt(zr2+zi2)+1e-9)/Math.log(2)+1e-9);this._col(mu<0?0:mu,d,o);} d[o+3]=255; } }
    _fit(iw,ih){ if(this.off.width!==iw||this.off.height!==ih){this.off.width=iw;this.off.height=ih;this.img=this.octx.createImageData(iw,ih);} }
    render(ctx){ const iw=Math.min(this.w,this._cap||2400),ih=Math.max(1,Math.round(iw*this.h/this.w));
      this._fit(iw,ih); const d=this.img.data;
      for(let py=0;py<ih;py++)this._scan(py,iw,ih,d);
      this.octx.putImageData(this.img,0,0);ctx.imageSmoothingEnabled=true;ctx.drawImage(this.off,0,0,this.w,this.h); }
    // Pro still: iterate EVERY output pixel (no internal cap) in ~32-row bands,
    // yielding between bands so the page stays responsive and progress can show.
    async still(ctx,onProg){ const iw=this.w,ih=this.h; this._fit(iw,ih); const d=this.img.data;
      for(let py=0;py<ih;py++){ this._scan(py,iw,ih,d);
        if((py&31)===31){ if(onProg)onProg(py/ih); await new Promise(r=>typeof requestAnimationFrame==='function'?requestAnimationFrame(r):typeof setTimeout==='function'?setTimeout(r,0):r()); } }
      this.octx.putImageData(this.img,0,0);ctx.drawImage(this.off,0,0,iw,ih); if(onProg)onProg(1); }
    // Export fidelity: stills are computed at true output resolution (via still());
    // video raises the live cap 1100 → 1600 — the honest real-time ceiling.
    fidelity(mode){ this._cap = mode==='video' ? 1600 : this.w; }
    pointer(px,py,down){ if(!down)return;this.autoC=false;this.mode='julia';this.cr=(px/this.w-0.5)*2*this.zoom*(this.w/this.h);this.ci=(py/this.h-0.5)*2*this.zoom; }
    randomize(){ this.mode=Math.random()<0.78?'julia':'mandelbrot';const a=Math.random()*6.283,rr=0.72+Math.random()*0.08;this.cr=rr*Math.cos(a);this.ci=rr*Math.sin(a);this.pal=['fire','ice','psy'][Math.random()*3|0];this.autoC=Math.random()<0.5; }
    controls(){ return [
      {t:'seg',key:'set',label:'Set',opts:[['julia','Julia'],['mandelbrot','Mandelbrot']],get:()=>this.mode,set:v=>this.mode=v},
      {t:'range',key:'zoom',label:'Zoom',min:0.4,max:2.2,step:0.05,get:()=>this.zoom,set:v=>this.zoom=v,fmt:v=>v.toFixed(2)+'×'},
      {t:'range',key:'iter',label:'Detail',min:50,max:350,step:10,get:()=>this.maxI,set:v=>this.maxI=v,fmt:v=>v+' it'},
      {t:'range',key:'morph',label:'Morph',min:0,max:3,step:0.1,get:()=>this.morph,set:v=>this.morph=v,fmt:v=>v.toFixed(1)+'×'},
      {t:'seg',key:'pal',label:'Palette',opts:[['fire','Fire'],['ice','Ice'],['psy','Neon']],get:()=>this.pal,set:v=>this.pal=v},
      {t:'toggle',key:'auto',label:'Auto-morph',get:()=>this.autoC,set:v=>this.autoC=v},
      {t:'button',label:'🎲 Randomize',act:()=>this.randomize()},
    ]; }
  }
  const make = (kind,w,h,preset) => kind==='flow'?new Flow(w,h):kind==='rd'?new RD(w,h,preset):kind==='slime'?new Slime(w,h,preset):kind==='boids'?new Boids(w,h):kind==='lenia'?new Lenia(w,h,preset):kind==='cymatics'?new Cymatics(w,h,preset):kind==='dla'?new DLA(w,h,preset):kind==='starling'?new Starling(w,h):kind==='fractal'?new Fractal(w,h):new Boids(w,h);

  // ===================== tools =====================
  const TOOLS = [
    {name:'Flow Field',kind:'flow',tag:'particles',pro:false,blurb:'Hundreds of thousands of particles streaming through an evolving curl-noise field into luminous vortices. Tune speed, swirl, trails and density.'},
    {name:'Reaction–Diffusion',kind:'rd',preset:'genesis',tag:'reaction-diffusion',pro:false,blurb:'Order self-organising out of chaos — the Gray–Scott model. Dial the feed (F) and kill (k) rates to sweep between worms, spots and mazes.'},
    {name:'Mitosis',kind:'rd',preset:'mitosis',tag:'reaction-diffusion',pro:true,blurb:'The dividing-cell regime of Gray–Scott — spots that grow, stretch and split. Same F/k desk.'},
    {name:'Slime Network',kind:'slime',preset:'tokyo',tag:'agents',pro:false,blurb:'Physarum grows transport paths between nutrients you place. Speed, decay, deposit, and click the canvas to drop food.'},
    {name:'Organism Growth',kind:'slime',preset:'growth',tag:'agents',pro:true,blurb:'A single seed erupts into a branching vascular network reaching out to its nutrients.'},
    {name:'Kaleidoscope',kind:'slime',preset:'kaleido',tag:'symmetry',pro:true,blurb:'A living field folded through N-fold mirror symmetry, hue-cycling. Set the symmetry from 3- to 12-fold.'},
    {name:'Cosmic Physarum',kind:'slime',preset:'cosmic',tag:'agents',pro:true,blurb:'The slime rendered as a luminous deep-space galaxy.'},
    {name:'Murmuration',kind:'boids',tag:'flocking',pro:false,blurb:'A living flock from three rules. Herd with Roost, push with Scatter, or become the Falcon; tune the flock size, cohesion and trails, and click to gust.'},
    {name:'Lenia',kind:'lenia',tag:'artificial life',pro:true,blurb:'Continuous cellular automata — smooth, self-organising lifeforms that glide, pulse and split. Tune the growth window (μ, σ) and click to plant new cells; each setting is a different species.'},
    {name:'Cymatics',kind:'cymatics',tag:'standing waves',pro:false,blurb:'Chladni-plate resonance — sand collecting on the nodal lines of a vibrating plate. Sweep the modes m and n; auto-morph shimmers between them.'},
    {name:'Crystal · DLA',kind:'dla',tag:'growth',pro:true,blurb:'Diffusion-limited aggregation — a seed grows dendritic frost as random walkers stick on contact. Click to plant new seeds; dial the growth rate and walker count.'},
    {name:'Starling Storm',kind:'starling',tag:'flocking',pro:true,blurb:'A dusk murmuration in the Flock2 idiom — orientation waves ripple through a banking flock as a stooping predator carves it open. Click and hold to be the falcon.'},
    {name:'Fractal Worlds',kind:'fractal',tag:'fractal',pro:true,blurb:'A living Julia set that morphs endlessly through parameter space — infinite worlds building and dissolving. Click to seed your own, switch to Mandelbrot, and zoom.'},
  ];
  window.StudioEngines = { make, TOOLS, Flow, RD, Slime, Boids, Lenia, Cymatics, DLA, Starling, Fractal, PALS };
})();
