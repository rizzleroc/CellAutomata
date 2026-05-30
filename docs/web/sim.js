// Gray-Scott reaction-diffusion in the browser. Direct port of
// `gray_scott_step` from cellauto/rules/abiogenesis/science.py and the
// init pattern in stage1_grayscott.py. Toroidal 5-point Laplacian over flat
// Float32Arrays, no allocations in the hot loop, ping-pong buffers.
//
// PDE:
//     ∂u/∂t = Du ∇²u  -  u v²  +  F (1 - u)
//     ∂v/∂t = Dv ∇²v  +  u v²  -  (F + k) v
(function () {
  "use strict";

  const W = 220;
  const H = 220;
  const Du = 0.16;
  const Dv = 0.08;
  const DT = 1.0;
  const SUBSTEPS = 10;

  let F = 0.035;
  let k = 0.065;

  // Ping-pong buffers.
  let u = new Float32Array(W * H);
  let v = new Float32Array(W * H);
  let uNext = new Float32Array(W * H);
  let vNext = new Float32Array(W * H);

  const canvas = document.getElementById("gs-canvas");
  const ctx = canvas.getContext("2d");
  const imageData = ctx.createImageData(W, H);
  const pixels = imageData.data;

  const fSlider = document.getElementById("f-slider");
  const kSlider = document.getElementById("k-slider");
  const fReadout = document.getElementById("f-readout");
  const kReadout = document.getElementById("k-readout");
  const presetSelect = document.getElementById("preset");
  const playBtn = document.getElementById("btn-play");
  const stopBtn = document.getElementById("btn-stop");
  const stepBtn = document.getElementById("btn-step");
  const resetBtn = document.getElementById("btn-reset");
  const shareBtn = document.getElementById("btn-share");
  const pngBtn = document.getElementById("btn-png");

  const F_MIN = 0.0, F_MAX = 0.09;
  const K_MIN = 0.03, K_MAX = 0.075;
  const clampF = (x) => Math.min(F_MAX, Math.max(F_MIN, x));
  const clampK = (x) => Math.min(K_MAX, Math.max(K_MIN, x));

  let running = false;
  let rafHandle = 0;

  // ── Initialisation ──────────────────────────────────────────────────────

  function reset() {
    u.fill(1.0);
    v.fill(0.0);
    // Central perturbation patch — Stage 1 init mirror.
    const r = 7;
    const cx = (W / 2) | 0;
    const cy = (H / 2) | 0;
    for (let y = cy - r; y < cy + r; y++) {
      for (let x = cx - r; x < cx + r; x++) {
        const i = y * W + x;
        u[i] = 0.5;
        v[i] = 0.25;
      }
    }
    // Symmetry-breaking noise on v.
    for (let i = 0; i < v.length; i++) {
      v[i] += (Math.random() - 0.5) * 0.02;
      if (v[i] < 0) v[i] = 0;
      if (v[i] > 1) v[i] = 1;
    }
    render();
  }

  // ── One PDE substep ─────────────────────────────────────────────────────

  function substep() {
    const dt = DT;
    for (let y = 0; y < H; y++) {
      const ym = (y - 1 + H) % H;
      const yp = (y + 1) % H;
      for (let x = 0; x < W; x++) {
        const xm = (x - 1 + W) % W;
        const xp = (x + 1) % W;
        const i = y * W + x;
        const ic = i;
        const il = y * W + xm;
        const ir = y * W + xp;
        const iu = ym * W + x;
        const id = yp * W + x;
        // 5-point Laplacian (toroidal).
        const lapU = u[il] + u[ir] + u[iu] + u[id] - 4 * u[ic];
        const lapV = v[il] + v[ir] + v[iu] + v[id] - 4 * v[ic];
        const uc = u[ic];
        const vc = v[ic];
        const uvv = uc * vc * vc;
        let un = uc + dt * (Du * lapU - uvv + F * (1.0 - uc));
        let vn = vc + dt * (Dv * lapV + uvv - (F + k) * vc);
        if (un < 0) un = 0; else if (un > 1) un = 1;
        if (vn < 0) vn = 0; else if (vn > 1) vn = 1;
        uNext[ic] = un;
        vNext[ic] = vn;
      }
    }
    // Swap buffers.
    const tmpU = u; u = uNext; uNext = tmpU;
    const tmpV = v; v = vNext; vNext = tmpV;
  }

  // ── Render ──────────────────────────────────────────────────────────────

  function render() {
    const n = VIRIDIS_LUT.length / 3;
    for (let i = 0; i < W * H; i++) {
      let t = v[i];
      if (t < 0) t = 0; else if (t > 1) t = 1;
      const idx = Math.min(n - 1, (t * n) | 0) * 3;
      const p = i * 4;
      pixels[p + 0] = VIRIDIS_LUT[idx + 0];
      pixels[p + 1] = VIRIDIS_LUT[idx + 1];
      pixels[p + 2] = VIRIDIS_LUT[idx + 2];
      pixels[p + 3] = 255;
    }
    ctx.putImageData(imageData, 0, 0);
  }

  // ── Loop ────────────────────────────────────────────────────────────────

  function tick() {
    if (!running) return;
    for (let s = 0; s < SUBSTEPS; s++) substep();
    render();
    rafHandle = requestAnimationFrame(tick);
  }

  function play() {
    if (running) return;
    running = true;
    playBtn.disabled = true;
    stopBtn.disabled = false;
    stepBtn.disabled = true;
    tick();
  }

  function stop() {
    running = false;
    cancelAnimationFrame(rafHandle);
    playBtn.disabled = false;
    stopBtn.disabled = true;
    stepBtn.disabled = false;
  }

  // ── UI wiring ───────────────────────────────────────────────────────────

  function setFK(newF, newK, preset) {
    F = newF;
    k = newK;
    fSlider.value = newF;
    kSlider.value = newK;
    fReadout.textContent = newF.toFixed(3);
    kReadout.textContent = newK.toFixed(3);
    if (preset !== undefined) presetSelect.value = preset;
  }

  // ── Shareable state via the URL (the free tier's growth feature) ──────────
  // Encodes the current F/k/preset into the address bar so any state can be
  // shared as a link. Read back on load. Saving *named* runs to an account is
  // the Pro upgrade; sharing the current state is free.
  function updateURL() {
    const params = new URLSearchParams();
    const preset = presetSelect.value;
    if (preset) params.set("preset", preset);
    params.set("F", F.toFixed(3));
    params.set("k", k.toFixed(3));
    history.replaceState(null, "", location.pathname + "?" + params.toString());
  }

  function applyFromURL() {
    const params = new URLSearchParams(location.search);
    const preset = params.get("preset");
    if (preset && PEARSON_PRESETS[preset]) {
      const { F: nf, k: nk } = PEARSON_PRESETS[preset];
      setFK(nf, nk, preset);
      return true;
    }
    const pf = parseFloat(params.get("F"));
    const pk = parseFloat(params.get("k"));
    if (!Number.isNaN(pf) && !Number.isNaN(pk)) {
      setFK(clampF(pf), clampK(pk), "");
      return true;
    }
    return false;
  }

  function flash(btn, msg) {
    const prev = btn.textContent;
    btn.textContent = msg;
    setTimeout(() => { btn.textContent = prev; }, 1400);
  }

  fSlider.addEventListener("input", () => {
    F = parseFloat(fSlider.value);
    fReadout.textContent = F.toFixed(3);
    presetSelect.value = "";
    updateURL();
  });
  kSlider.addEventListener("input", () => {
    k = parseFloat(kSlider.value);
    kReadout.textContent = k.toFixed(3);
    presetSelect.value = "";
    updateURL();
  });
  presetSelect.addEventListener("change", () => {
    const name = presetSelect.value;
    if (PEARSON_PRESETS[name]) {
      const { F: nf, k: nk } = PEARSON_PRESETS[name];
      setFK(nf, nk, name);
      updateURL();
    }
  });
  playBtn.addEventListener("click", play);
  stopBtn.addEventListener("click", stop);
  stepBtn.addEventListener("click", () => {
    for (let s = 0; s < SUBSTEPS; s++) substep();
    render();
  });
  resetBtn.addEventListener("click", () => {
    stop();
    reset();
  });

  // SHARE — copy a permalink to the current F/k state.
  if (shareBtn) {
    shareBtn.addEventListener("click", async () => {
      updateURL();
      try {
        await navigator.clipboard.writeText(location.href);
        flash(shareBtn, "LINK COPIED ✓");
      } catch {
        window.prompt("Copy this link:", location.href);
      }
    });
  }

  // SAVE PNG — free single-frame export (upscaled 3× nearest-neighbour).
  // Animated GIF, 4K, and the poster generator are the Pro upgrade.
  if (pngBtn) {
    pngBtn.addEventListener("click", () => {
      const scale = 3;
      const off = document.createElement("canvas");
      off.width = W * scale;
      off.height = H * scale;
      const octx = off.getContext("2d");
      octx.imageSmoothingEnabled = false;
      octx.drawImage(canvas, 0, 0, off.width, off.height);
      off.toBlob((blob) => {
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = `cellauto-F${F.toFixed(3)}-k${k.toFixed(3)}.png`;
        a.click();
        URL.revokeObjectURL(a.href);
        flash(pngBtn, "SAVED ✓");
      });
    });
  }

  // Keyboard: Space → play/pause.
  window.addEventListener("keydown", (e) => {
    if (e.code === "Space" && document.activeElement.tagName !== "INPUT") {
      e.preventDefault();
      if (running) stop(); else play();
    }
  });

  // Start — restore a shared state from the URL, else default to "spots".
  reset();
  if (!applyFromURL()) setFK(0.035, 0.065, "spots");
  updateURL();
  play();
})();
