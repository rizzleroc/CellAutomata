// docs/slime · Slime Studio — an interactive Physarum polycephalum lab.
// Place nutrients, watch the mould grow paths that connect them; a live SEM
// micrograph feed shades the same field as a depth-lit electron micrograph.
// Zero dependencies. Same agent model as the lab's slime work (Jones 2010 /
// Tero & Nakagaki 2010): sense-rotate-deposit-diffuse, plus food attractors.
(() => {
  'use strict';
  const G = 200, N = G * G, TAU = Math.PI * 2;
  const clamp = (v, a, b) => (v < a ? a : v > b ? b : v);
  const lerp = (a, b, t) => a + (b - a) * t;

  // ---- fields + agents ----
  const T = new Float32Array(N), Tn = new Float32Array(N), mx = new Float32Array(N);
  const CAP = 34000, ax = new Float32Array(CAP), ay = new Float32Array(CAP), ah = new Float32Array(CAP);
  let pop = 0;
  const sa = 22 * Math.PI / 180, ra = 26 * Math.PI / 180, so = 9, ssz = 1.0;
  let dep = 5.6, decay = 0.90, targetPop = 20000, running = true, speed = 2;

  const nodes = [];                       // nutrient sites {x,y} in grid coords
  const cx = G / 2, cy = G / 2;

  function seed() {
    pop = 0;
    for (let i = 0; i < 1500; i++) {
      const a = Math.random() * TAU, r = Math.sqrt(Math.random()) * 6;
      ax[i] = clamp(cx + Math.cos(a) * r, 1, G - 2);
      ay[i] = clamp(cy + Math.sin(a) * r, 1, G - 2);
      ah[i] = Math.random() * TAU;
    }
    pop = 1500;
  }
  function addNode(gx, gy) {
    gx = clamp(gx | 0, 2, G - 3); gy = clamp(gy | 0, 2, G - 3);
    nodes.push({ x: gx, y: gy });
  }
  function scatter(n) {
    nodes.length = 0;
    for (let i = 0; i < n; i++) {
      const a = Math.random() * TAU, r = Math.sqrt(Math.random()) * G * 0.42;
      addNode(cx + Math.cos(a) * r, cy + Math.sin(a) * r);
    }
  }
  function reset() { T.fill(0); mx.fill(0); nodes.length = 0; seed(); scatter(11); }

  function stampFood() {
    for (const c of nodes) {
      const gx = c.x | 0, gy = c.y | 0;
      for (let dy = -2; dy <= 2; dy++) for (let dx = -2; dx <= 2; dx++) {
        const d2 = dx * dx + dy * dy; if (d2 > 4) continue;
        const x = gx + dx, y = gy + dy; if (x < 0 || y < 0 || x >= G || y >= G) continue;
        const v = 78 * (1 - Math.sqrt(d2) / 2 * 0.4), i = y * G + x; if (v > T[i]) T[i] = v;
      }
    }
  }
  function sense(x, y, a) { const sx = (x + Math.cos(a) * so) | 0, sy = (y + Math.sin(a) * so) | 0; if (sx < 0 || sy < 0 || sx >= G || sy >= G) return -1; return T[sy * G + sx]; }
  function agents() {
    for (let i = 0; i < pop; i++) {
      const x = ax[i], y = ay[i], h = ah[i];
      const f = sense(x, y, h), fl = sense(x, y, h - sa), fr = sense(x, y, h + sa);
      let nh = h;
      if (f >= fl && f >= fr) {} else if (f < fl && f < fr) nh += (Math.random() < .5 ? -1 : 1) * ra; else if (fl > fr) nh -= ra; else nh += ra;
      let nx = x + Math.cos(nh) * ssz, ny = y + Math.sin(nh) * ssz;
      if (nx < 1 || ny < 1 || nx >= G - 1 || ny >= G - 1) { nh = Math.atan2(cy - y, cx - x) + (Math.random() - .5); nx = x; ny = y; }
      ax[i] = nx; ay[i] = ny; ah[i] = nh;
      const ci = (ny | 0) * G + (nx | 0); T[ci] = Math.min(T[ci] + dep, 460);
    }
  }
  function diffuse() {
    const dk = decay;
    for (let y = 0; y < G; y++) { const ym = y > 0 ? y - 1 : 0, yp = y < G - 1 ? y + 1 : y;
      for (let x = 0; x < G; x++) { const xm = x > 0 ? x - 1 : 0, xp = x < G - 1 ? x + 1 : x, i = y * G + x;
        const s = T[ym * G + xm] + T[ym * G + x] + T[ym * G + xp] + T[y * G + xm] + T[y * G + x] + T[y * G + xp] + T[yp * G + xm] + T[yp * G + x] + T[yp * G + xp];
        Tn[i] = s * 0.1111111 * dk;
      } } T.set(Tn);
  }
  function grow() {
    if (pop >= targetPop) return;
    const add = Math.min(160, targetPop - pop, CAP - pop);
    for (let k = 0; k < add; k++) { const j = (Math.random() * pop) | 0;
      ax[pop] = clamp(ax[j] + (Math.random() * 3 - 1.5), 1, G - 2); ay[pop] = clamp(ay[j] + (Math.random() * 3 - 1.5), 1, G - 2); ah[pop] = Math.random() * TAU; pop++;
    }
  }
  function track() { for (let i = 0; i < N; i++) { const v = T[i]; if (v > mx[i]) mx[i] = v; else mx[i] *= 0.994; } }
  function step() { stampFood(); agents(); diffuse(); grow(); track(); }

  // ---- renderers (write into G×G ImageData; upscaled by the DOM) ----
  const hsh = (x, y) => { let n = (x * 374761393 + y * 668265263) >>> 0; n = (n ^ (n >> 13)) * 1274126177 >>> 0; return ((n >>> 0) % 1000) / 1000; };

  // A) INTERACTIVE — living paths: bright chrome-yellow veins + residual wash on tan agar
  const AGAR = [26, 24, 18], WASH = [70, 62, 30], SHEET = [246, 226, 64], VEIN = [232, 198, 22], CORE = [150, 118, 20];
  function renderPaths(data) {
    const NORM = 46;
    for (let y = 0; y < G; y++) { const ym = y > 0 ? y - 1 : 0, yp = y < G - 1 ? y + 1 : y;
      for (let x = 0; x < G; x++) { const xm = x > 0 ? x - 1 : 0, xp = x < G - 1 ? x + 1 : x, i = y * G + x, o = i * 4;
        const h = clamp(T[i] / NORM, 0, 1), e = clamp(mx[i] / NORM, 0, 1);
        let r = AGAR[0], g = AGAR[1], b = AGAR[2];
        const w = clamp(e * 1.6, 0, 0.3); r = lerp(r, WASH[0], w); g = lerp(g, WASH[1], w); b = lerp(b, WASH[2], w);
        if (h > 0.02) {
          const gx = (T[y * G + xp] - T[y * G + xm]) / NORM, gy = (T[yp * G + x] - T[ym * G + x]) / NORM;
          const nz = 1 / Math.sqrt(gx * gx * 9 + gy * gy * 9 + 1), lam = clamp(nz * 0.8 + 0.2, 0, 1);
          let cr, cg, cb; const hy = h * h * (3 - 2 * h);
          if (hy < 0.55) { const u = hy / 0.55; cr = lerp(SHEET[0], VEIN[0], u); cg = lerp(SHEET[1], VEIN[1], u); cb = lerp(SHEET[2], VEIN[2], u); }
          else { const u = (hy - 0.55) / 0.45; cr = lerp(VEIN[0], CORE[0], u); cg = lerp(VEIN[1], CORE[1], u); cb = lerp(VEIN[2], CORE[2], u); }
          const I = 0.62 + 0.5 * lam, al = clamp((h - 0.02) / 0.14, 0, 1);
          r = lerp(r, cr * I, al); g = lerp(g, cg * I, al); b = lerp(b, cb * I, al);
        }
        data[o] = r; data[o + 1] = g; data[o + 2] = b; data[o + 3] = 255;
      } }
    // nutrient nodes
    for (const c of nodes) { const gx = c.x | 0, gy = c.y | 0, lit = T[gy * G + gx] > 6;
      for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) { const x = gx + dx, y = gy + dy; if (x < 0 || y < 0 || x >= G || y >= G) continue; const o = (y * G + x) * 4;
        const col = lit ? [252, 248, 232] : [150, 200, 150]; const a = (dx === 0 && dy === 0) ? 0.95 : 0.4;
        data[o] = lerp(data[o], col[0], a); data[o + 1] = lerp(data[o + 1], col[1], a); data[o + 2] = lerp(data[o + 2], col[2], a); } }
  }

  // B) LIVE·SEM FEED — depth-shaded warm-sepia electron micrograph of the same field
  const SEM_LO = [14, 11, 9], SEM_HI = [242, 224, 196];
  function renderSEM(data) {
    const NORM = 48, relief = 3.0;
    for (let y = 0; y < G; y++) { const ym = y > 0 ? y - 1 : 0, yp = y < G - 1 ? y + 1 : y;
      for (let x = 0; x < G; x++) { const xm = x > 0 ? x - 1 : 0, xp = x < G - 1 ? x + 1 : x, i = y * G + x, o = i * 4;
        const h = clamp(T[i] / NORM, 0, 1);
        const gx = (T[y * G + xp] - T[y * G + xm]) / NORM * relief, gy = (T[yp * G + x] - T[ym * G + x]) / NORM * relief;
        const nz = 1 / Math.sqrt(gx * gx + gy * gy + 1);
        const lam = clamp(nz * 0.72 + (-gx * nz) * 0.28 + (-gy * nz) * (-0.30), 0, 1);
        const spec = Math.pow(clamp(nz, 0, 1), 22) * 0.35;
        const mott = 0.94 + 0.12 * hsh(x, y);
        let v = (0.10 + 0.62 * lam * (0.35 + 0.9 * h)) * mott + spec;   // depth from height + relief
        v = clamp(v, 0, 1);
        data[o] = lerp(SEM_LO[0], SEM_HI[0], v); data[o + 1] = lerp(SEM_LO[1], SEM_HI[1], v); data[o + 2] = lerp(SEM_LO[2], SEM_HI[2], v); data[o + 3] = 255;
      } }
  }

  // ---- DOM wiring ----
  const paths = document.getElementById('paths'), feed = document.getElementById('feed');
  const pctx = paths.getContext('2d'), fctx = feed.getContext('2d');
  const off = document.createElement('canvas'); off.width = G; off.height = G; const octx = off.getContext('2d');
  const imgA = octx.createImageData(G, G), imgB = octx.createImageData(G, G);
  pctx.imageSmoothingEnabled = false; fctx.imageSmoothingEnabled = true;

  function fit(c) { const r = c.getBoundingClientRect(), dpr = Math.min(devicePixelRatio || 1, 2);
    c.width = Math.max(1, r.width * dpr | 0); c.height = Math.max(1, r.height * dpr | 0); }
  function fitAll() { fit(paths); fit(feed); pctx.imageSmoothingEnabled = false; fctx.imageSmoothingEnabled = true; }
  addEventListener('resize', fitAll);

  function blit(ctx, img) { octx.putImageData(img, 0, 0); ctx.drawImage(off, 0, 0, ctx.canvas.width, ctx.canvas.height); }

  // pointer → place nutrients (drag paints)
  let painting = false;
  function place(ev, c) { const r = c.getBoundingClientRect(); const gx = (ev.clientX - r.left) / r.width * G, gy = (ev.clientY - r.top) / r.height * G; addNode(gx, gy); refreshReadout(); }
  for (const c of [paths, feed]) {
    c.addEventListener('pointerdown', e => { painting = true; place(e, c); c.setPointerCapture(e.pointerId); hideHint(); });
    c.addEventListener('pointermove', e => { if (painting) place(e, c); });
    c.addEventListener('pointerup', () => { painting = false; });
  }

  // controls
  const $ = id => document.getElementById(id);
  const elNodes = $('rNodes'), elCover = $('rCover'), elAgents = $('rAgents');
  function refreshReadout() { elNodes.textContent = nodes.length; elAgents.textContent = pop.toLocaleString(); }
  let coverT = 0;
  function coverage() { let c = 0; for (let i = 0; i < N; i++) if (T[i] > 3) c++; return c / N; }

  $('play').addEventListener('click', () => { running = !running; $('play').textContent = running ? '❚❚ Pause' : '► Play'; $('play').setAttribute('aria-pressed', running); });
  $('reset').addEventListener('click', () => { reset(); refreshReadout(); });
  $('scatter').addEventListener('click', () => { scatter(11); refreshReadout(); hideHint(); });
  $('clearFood').addEventListener('click', () => { nodes.length = 0; refreshReadout(); });
  const spd = $('speed'); spd.addEventListener('input', () => { speed = +spd.value; $('vSpeed').textContent = speed + '×'; });
  const vig = $('vigor'); vig.addEventListener('input', () => { const v = +vig.value; decay = lerp(0.86, 0.945, v / 100); dep = lerp(4.4, 6.6, v / 100); $('vVigor').textContent = v < 34 ? 'lean' : v < 67 ? 'balanced' : 'lush'; });

  const hint = $('hint'); let hinted = false; function hideHint() { if (!hinted) { hinted = true; hint.classList.add('gone'); } }
  setTimeout(hideHint, 7000);

  // ---- pro / paywall — a real paid gate on the 4K micrograph export ----
  let pro = false;
  const proBtn = $('proBtn'), exportBtn = $('exportBtn'), paywall = $('paywall');
  proBtn.addEventListener('click', () => { if (!pro) paywall.hidden = false; });
  $('pwClose').addEventListener('click', () => { paywall.hidden = true; });
  function goPro() { pro = true; paywall.hidden = true; proBtn.textContent = '✓ Pro'; proBtn.classList.add('owned'); exportBtn.disabled = false; }
  $('pwOne').addEventListener('click', goPro);
  $('pwAll').addEventListener('click', goPro);
  exportBtn.addEventListener('click', () => {
    if (!pro) { paywall.hidden = false; return; }
    const R = 2048; renderSEM(imgB.data); octx.putImageData(imgB, 0, 0);
    const c = document.createElement('canvas'); c.width = R; c.height = R; const cc = c.getContext('2d');
    cc.imageSmoothingEnabled = true; cc.drawImage(off, 0, 0, R, R);
    c.toBlob(b => { if (!b) return; const url = URL.createObjectURL(b), a = document.createElement('a');
      a.href = url; a.download = 'slime-studio-sem-' + R + '.png'; document.body.appendChild(a); a.click(); a.remove(); }, 'image/png');
  });

  // ---- loop ----
  let last = performance.now(), acc = 0;
  function frame(now) {
    const dt = now - last; last = now;
    if (running) for (let s = 0; s < speed; s++) step();
    renderPaths(imgA.data); blit(pctx, imgA);
    renderSEM(imgB.data); blit(fctx, imgB);
    acc += dt; if (acc > 400) { acc = 0; coverT = coverage(); elCover.textContent = (coverT * 100).toFixed(1) + '%'; refreshReadout(); }
    requestAnimationFrame(frame);
  }
  fitAll(); reset(); refreshReadout();
  requestAnimationFrame(t => { last = t; requestAnimationFrame(frame); });
})();
