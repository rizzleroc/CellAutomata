// cellauto v4 preview — live SEM-grade renderer.
//
// Runs the SAME Gray-Scott reaction-diffusion engine as the v3.7 explorer,
// then applies the v4.0 Phase-1 depth-shading pipeline described in
// docs/PRD_SEM_VISUALIZATION.md §6 entirely in the browser:
//
//   height = v-field  →  blur  →  gradients → surface normals
//   →  Lambertian + ambient + specular  →  ambient occlusion (Laplacian)
//   →  micro-noise  →  warm-sepia / cool-mono tone-map LUT.
//
// This is an honest preview: every lit pixel is still driven by the real
// PDE. The full v4 renders all 12 stages in the desktop client.
(function () {
  "use strict";

  const W = 220, H = 220;
  const Du = 0.16, Dv = 0.08, DT = 1.0, SUBSTEPS = 10;
  let F = 0.0367, k = 0.0649; // "mitosis" — the most cinematic feed by default

  let u = new Float32Array(W * H), v = new Float32Array(W * H);
  let uN = new Float32Array(W * H), vN = new Float32Array(W * H);
  const hb = new Float32Array(W * H);              // blurred height
  const noise = new Float32Array(W * H);
  for (let i = 0; i < noise.length; i++) noise[i] = Math.random();

  const canvas = document.getElementById("sem-canvas");
  const ctx = canvas.getContext("2d");
  const img = ctx.createImageData(W, H);
  const px = img.data;

  // ── Palette LUTs ──────────────────────────────────────────────────────────
  function buildLUT(stops) {
    const lut = new Uint8Array(256 * 3);
    for (let i = 0; i < 256; i++) {
      const t = i / 255;
      let a = stops[0], b = stops[stops.length - 1];
      for (let s = 0; s < stops.length - 1; s++) {
        if (t >= stops[s].t && t <= stops[s + 1].t) { a = stops[s]; b = stops[s + 1]; break; }
      }
      const span = (b.t - a.t) || 1, f = (t - a.t) / span;
      lut[i * 3 + 0] = Math.round(a.c[0] + (b.c[0] - a.c[0]) * f);
      lut[i * 3 + 1] = Math.round(a.c[1] + (b.c[1] - a.c[1]) * f);
      lut[i * 3 + 2] = Math.round(a.c[2] + (b.c[2] - a.c[2]) * f);
    }
    return lut;
  }
  const LUT_SEPIA = buildLUT([
    { t: 0.00, c: [26, 20, 15] }, { t: 0.35, c: [74, 59, 48] },
    { t: 0.70, c: [150, 125, 95] }, { t: 1.00, c: [230, 220, 197] },
  ]);
  const LUT_MONO = buildLUT([
    { t: 0.00, c: [8, 11, 18] }, { t: 0.40, c: [34, 52, 56] },
    { t: 0.80, c: [120, 160, 158] }, { t: 1.00, c: [230, 224, 208] },
  ]);
  let LUT = LUT_SEPIA;

  // ── Lighting constants ────────────────────────────────────────────────────
  const Ll = Math.hypot(0.4, 0.3, 0.85);
  const lx = 0.4 / Ll, ly = 0.3 / Ll, lz = 0.85 / Ll;
  let hx = lx, hy = ly, hz = lz + 1;                 // half-vector with view (0,0,1)
  const hl = Math.hypot(hx, hy, hz); hx /= hl; hy /= hl; hz /= hl;
  // Tone-map: a raised v-form catches the light (bright) against a darker
  // granular substrate. SUBSTRATE = flat-field floor; RELIEF = how much height
  // brightens. LIT mixes flat ambient with directional shading.
  const Z = 7.0, SUBSTRATE = 0.12, RELIEF = 1.9, SPEC = 0.4, SHINE = 20, AO = 0.6, NOISE_AMT = 0.06;

  // ── Engine ────────────────────────────────────────────────────────────────
  function reset() {
    u.fill(1.0); v.fill(0.0);
    const r = 6, cx = W / 2 | 0, cy = H / 2 | 0;
    const patches = [[cx, cy]];
    for (let n = 0; n < 7; n++) patches.push([(20 + Math.random() * (W - 40)) | 0, (20 + Math.random() * (H - 40)) | 0]);
    for (const [px0, py0] of patches)
      for (let y = py0 - r; y < py0 + r; y++)
        for (let x = px0 - r; x < px0 + r; x++) { const i = ((y + H) % H) * W + ((x + W) % W); u[i] = 0.5; v[i] = 0.25; }
    for (let i = 0; i < v.length; i++) { v[i] += (Math.random() - 0.5) * 0.02; if (v[i] < 0) v[i] = 0; if (v[i] > 1) v[i] = 1; }
    shadeAndRender();
  }

  function substep() {
    for (let y = 0; y < H; y++) {
      const ym = (y - 1 + H) % H, yp = (y + 1) % H;
      for (let x = 0; x < W; x++) {
        const xm = (x - 1 + W) % W, xp = (x + 1) % W, i = y * W + x;
        const lapU = u[y * W + xm] + u[y * W + xp] + u[ym * W + x] + u[yp * W + x] - 4 * u[i];
        const lapV = v[y * W + xm] + v[y * W + xp] + v[ym * W + x] + v[yp * W + x] - 4 * v[i];
        const uc = u[i], vc = v[i], uvv = uc * vc * vc;
        let un = uc + DT * (Du * lapU - uvv + F * (1 - uc));
        let vn = vc + DT * (Dv * lapV + uvv - (F + k) * vc);
        if (un < 0) un = 0; else if (un > 1) un = 1;
        if (vn < 0) vn = 0; else if (vn > 1) vn = 1;
        uN[i] = un; vN[i] = vn;
      }
    }
    let t = u; u = uN; uN = t; t = v; v = vN; vN = t;
  }

  // ── SEM depth-shading ─────────────────────────────────────────────────────
  function shadeAndRender() {
    for (let y = 0; y < H; y++) {                    // 3×3 box blur → hb
      const ym = (y - 1 + H) % H, yp = (y + 1) % H;
      for (let x = 0; x < W; x++) {
        const xm = (x - 1 + W) % W, xp = (x + 1) % W, i = y * W + x;
        hb[i] = (v[ym * W + xm] + v[ym * W + x] + v[ym * W + xp]
               + v[y * W + xm] + v[i] + v[y * W + xp]
               + v[yp * W + xm] + v[yp * W + x] + v[yp * W + xp]) / 9;
      }
    }
    for (let y = 0; y < H; y++) {
      const ym = (y - 1 + H) % H, yp = (y + 1) % H;
      for (let x = 0; x < W; x++) {
        const xm = (x - 1 + W) % W, xp = (x + 1) % W, i = y * W + x;
        const gx = (hb[y * W + xp] - hb[y * W + xm]) * Z;
        const gy = (hb[yp * W + x] - hb[ym * W + x]) * Z;
        const nl = Math.sqrt(gx * gx + gy * gy + 1);
        const nx = -gx / nl, ny = -gy / nl, nz = 1 / nl;
        let ndl = nx * lx + ny * ly + nz * lz; if (ndl < 0) ndl = 0;
        let ndh = nx * hx + ny * hy + nz * hz; if (ndh < 0) ndh = 0;
        const spec = Math.pow(ndh, SHINE) * SPEC;
        const lap = hb[y * W + xm] + hb[y * W + xp] + hb[ym * W + x] + hb[yp * W + x] - 4 * hb[i];
        let ao = 1 - AO * Math.max(0, lap * 4); if (ao < 0) ao = 0;
        const lit = 0.5 + 0.5 * ndl;                       // directional relief
        let I = (SUBSTRATE + RELIEF * hb[i]) * lit * ao + spec + (noise[i] - 0.5) * NOISE_AMT;
        if (I < 0) I = 0; else if (I > 1) I = 1;
        const idx = (I * 255 | 0) * 3, p = i * 4;
        px[p] = LUT[idx]; px[p + 1] = LUT[idx + 1]; px[p + 2] = LUT[idx + 2]; px[p + 3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
  }

  // ── Transport ─────────────────────────────────────────────────────────────
  let running = false, raf = 0;
  const badge = document.getElementById("sem-badge");
  const playBtn = document.getElementById("btn-play");
  const stopBtn = document.getElementById("btn-stop");
  const stepBtn = document.getElementById("btn-step");

  function tick() { if (!running) return; for (let s = 0; s < SUBSTEPS; s++) substep(); shadeAndRender(); raf = requestAnimationFrame(tick); }
  function play() { if (running) return; running = true; badge.classList.add("live"); playBtn.disabled = true; stopBtn.disabled = false; stepBtn.disabled = true; tick(); }
  function stop() { running = false; badge.classList.remove("live"); cancelAnimationFrame(raf); playBtn.disabled = false; stopBtn.disabled = true; stepBtn.disabled = false; }

  // ── Controls ──────────────────────────────────────────────────────────────
  const fSlider = document.getElementById("f-slider");
  const kSlider = document.getElementById("k-slider");
  const fReadout = document.getElementById("f-readout");
  const kReadout = document.getElementById("k-readout");

  function syncReadouts() { fReadout.textContent = F.toFixed(4); kReadout.textContent = k.toFixed(4); fSlider.value = F; kSlider.value = k; }

  document.querySelectorAll("[data-preset]").forEach((chip) => {
    chip.addEventListener("click", () => {
      const p = PEARSON_PRESETS[chip.dataset.preset];
      if (!p) return;
      F = p.F; k = p.k; syncReadouts();
      document.querySelectorAll("[data-preset]").forEach((c) => c.classList.toggle("active", c === chip));
    });
  });
  fSlider.addEventListener("input", () => { F = parseFloat(fSlider.value); fReadout.textContent = F.toFixed(4); document.querySelectorAll("[data-preset]").forEach((c) => c.classList.remove("active")); });
  kSlider.addEventListener("input", () => { k = parseFloat(kSlider.value); kReadout.textContent = k.toFixed(4); document.querySelectorAll("[data-preset]").forEach((c) => c.classList.remove("active")); });

  playBtn.addEventListener("click", play);
  stopBtn.addEventListener("click", stop);
  stepBtn.addEventListener("click", () => { for (let s = 0; s < SUBSTEPS; s++) substep(); shadeAndRender(); });
  document.getElementById("btn-reset").addEventListener("click", () => { stop(); reset(); });

  const palBtn = document.getElementById("btn-palette");
  palBtn.addEventListener("click", () => {
    const mono = LUT === LUT_SEPIA;
    LUT = mono ? LUT_MONO : LUT_SEPIA;
    document.body.classList.toggle("mono", mono);
    palBtn.textContent = mono ? "PALETTE · COOL-MONO" : "PALETTE · WARM-SEPIA";
    if (!running) shadeAndRender();
  });

  window.addEventListener("keydown", (e) => {
    if (e.code === "Space" && document.activeElement.tagName !== "INPUT") { e.preventDefault(); running ? stop() : play(); }
  });

  // ── Start ─────────────────────────────────────────────────────────────────
  reset(); syncReadouts(); play();
})();
