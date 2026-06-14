// Conway's Game of Life — B3/S23 on a toroidal grid. The canonical cellular
// automaton: four rules, no players, and yet gliders, oscillators, and still
// lifes emerge and persist. Here it opens the origin-of-life arc — "life" as a
// pure RULE — rendered through the same SEM height-shader as every lab stage
// (live cells stand up as bone-coloured domes), so it belongs to one world.
(function () {
  "use strict";
  window.CA = window.CA || { RULES: {} };

  const W = 120, H = 120, N = W * H;

  function make() {
    let cur = new Uint8Array(N);
    let nxt = new Uint8Array(N);
    let age = new Uint8Array(N);        // frames-alive, for a touch of height texture
    let generation = 0;

    function glider(x, y, o) {
      // four glider phases/orientations — a moving thing, so the field never dies
      const P = [[0,1],[1,2],[2,0],[2,1],[2,2]];
      for (const [dx, dy] of P) {
        const gx = ((o & 1) ? dy : dx), gy = ((o & 2) ? dx : dy);
        const xi = ((x + gx) % W + W) % W, yi = ((y + gy) % H + H) % H;
        cur[yi * W + xi] = 1;
      }
    }
    function seed() {
      cur.fill(0); nxt.fill(0); age.fill(0); generation = 0;
      for (let i = 0; i < N; i++) if (Math.random() < 0.30) cur[i] = 1;   // primordial soup
      for (let k = 0; k < 14; k++) glider((Math.random()*W)|0, (Math.random()*H)|0, (Math.random()*4)|0);
    }

    return {
      id: "conway",
      label: "Conway · Game of Life (B3/S23)",
      formula: "A cell lives iff it has 3 live neighbours, or 2 and is already alive.",
      shortCaption: "STAGE 0 · THE GAME OF LIFE",
      paletteBg: [10, 14, 22], paletteFg: [230, 224, 208],
      width: W, height: H,
      params: { density: { label: "soup density", min: 0.05, max: 0.6, step: 0.01, value: 0.30 } },

      reset() { seed(); },
      randomize() { seed(); },
      clear() { cur.fill(0); nxt.fill(0); age.fill(0); generation = 0; },

      step() {
        for (let y = 0; y < H; y++) {
          const ym = ((y - 1 + H) % H) * W, yp = ((y + 1) % H) * W, yc = y * W;
          for (let x = 0; x < W; x++) {
            const xm = (x - 1 + W) % W, xp = (x + 1) % W;
            const n = cur[ym+xm]+cur[ym+x]+cur[ym+xp]+cur[yc+xm]+cur[yc+xp]+cur[yp+xm]+cur[yp+x]+cur[yp+xp];
            const i = yc + x, a = cur[i];
            const live = (a && (n === 2 || n === 3)) || (!a && n === 3);
            nxt[i] = live ? 1 : 0;
            age[i] = live ? (a ? Math.min(255, age[i] + 1) : 1) : 0;
          }
        }
        const t = cur; cur = nxt; nxt = t;
        generation++;
      },

      // SEM height: live cells as raised domes; settled (older) cells sit a hair
      // higher so still-lifes read as solid and the churn of birth/death shimmers.
      renderHeight(out) {
        for (let i = 0; i < N; i++) out[i] = cur[i] ? (0.66 + Math.min(0.24, age[i] * 0.03)) : 0.10;
      },
      render(pixels) {
        const haveLut = (typeof VIRIDIS_LUT !== "undefined"), L = haveLut ? VIRIDIS_LUT.length/3 : 0;
        for (let i = 0; i < N; i++) {
          const p = i * 4;
          if (cur[i]) {
            if (haveLut) { const idx = Math.min(L-1,(0.55+Math.min(0.4,age[i]*0.05))*L|0)*3; pixels[p]=VIRIDIS_LUT[idx];pixels[p+1]=VIRIDIS_LUT[idx+1];pixels[p+2]=VIRIDIS_LUT[idx+2]; }
            else { pixels[p]=210; pixels[p+1]=224; pixels[p+2]=200; }
          } else { pixels[p]=10; pixels[p+1]=14; pixels[p+2]=22; }
          pixels[p+3] = 255;
        }
      },
      paint(gx, gy, radius, mode) {
        for (let dy=-radius; dy<=radius; dy++) for (let dx=-radius; dx<=radius; dx++) {
          if (dx*dx+dy*dy>radius*radius) continue;
          const x=((gx+dx)%W+W)%W, y=((gy+dy)%H+H)%H, i=y*W+x;
          cur[i] = mode === "erase" ? 0 : 1;
        }
      },
      population() { let c=0; for (let i=0;i<N;i++) c+=cur[i]; return `${c} live cells · gen ${generation}`; },
      generation() { return generation; },
    };
  }
  CA.RULES.conway = make;
})();
