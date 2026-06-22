// SEM (Scanning Electron Micrograph) renderer — v4.0 port.
//
// Takes a single-channel height field (Float32Array, values in [0,1]) and
// writes an RGBA image into the supplied pixel buffer, depth-shaded under
// a fixed directional light, with ambient occlusion, procedural noise,
// and tone-mapping through a 256-entry sepia (or cool-mono) LUT.
//
// Pipeline (mirrors cellauto/renderer_sem.py Phase 1 in the PRD):
//   blur σ≈0.7  →  Sobel gradients  →  normals
//                →  Lambertian + ambient + specular
//                →  ambient occlusion (subtract α·∇²H)
//                →  procedural noise overlay
//                →  tone-map through warm-sepia / cool-mono LUT
//
// Light direction L = normalise(0.4, 0.3, 0.85); ambient = 0.2;
// specular exponent = 32; noise opacity ≈ 0.06.
(function () {
  "use strict";

  // ── Palette LUTs (256 entries × 3 bytes) ────────────────────────────────
  // Warm-sepia: matches the PRD reference image — desaturated dark brown
  //   at low intensity → bone-cream at high.  Background #2a221c (42,34,28)
  //   to highlight #e6dcc5 (230,220,197), with a subtle warm midtone.
  // Cool-mono: extends the existing Catalytic Silence palette into 3-D
  //   shading.  Obsidian #0a0e16 → bone #e6e0d0.
  function makeLut(stops) {
    // stops: array of { t: 0..1, rgb: [r,g,b] }, sorted by t ascending.
    const lut = new Uint8Array(256 * 3);
    for (let i = 0; i < 256; i++) {
      const t = i / 255;
      // find bracketing stops.
      let a = stops[0], b = stops[stops.length - 1];
      for (let j = 0; j < stops.length - 1; j++) {
        if (t >= stops[j].t && t <= stops[j+1].t) {
          a = stops[j]; b = stops[j+1]; break;
        }
      }
      const span = Math.max(1e-9, b.t - a.t);
      const f = (t - a.t) / span;
      lut[i*3]   = Math.round(a.rgb[0] + f * (b.rgb[0] - a.rgb[0]));
      lut[i*3+1] = Math.round(a.rgb[1] + f * (b.rgb[1] - a.rgb[1]));
      lut[i*3+2] = Math.round(a.rgb[2] + f * (b.rgb[2] - a.rgb[2]));
    }
    return lut;
  }

  const PALETTES = {
    "warm-sepia": makeLut([
      { t: 0.00, rgb: [ 26,  20,  16] },  // deep cocoa
      { t: 0.18, rgb: [ 60,  47,  36] },
      { t: 0.42, rgb: [122,  95,  68] },
      { t: 0.70, rgb: [190, 158, 116] },
      { t: 0.92, rgb: [230, 220, 197] },  // bone-cream highlight
      { t: 1.00, rgb: [248, 240, 220] },
    ]),
    "cool-mono": makeLut([
      { t: 0.00, rgb: [ 10,  14,  22] },  // obsidian
      { t: 0.30, rgb: [ 35,  46,  60] },
      { t: 0.62, rgb: [ 90, 112, 124] },
      { t: 0.88, rgb: [200, 200, 188] },
      { t: 1.00, rgb: [230, 224, 208] },  // warm bone
    ]),
  };

  // ── Persistent scratch buffers (sized lazily per grid) ──────────────────
  let _w = 0, _h = 0;
  let _blurA, _blurB, _noise;

  function ensureScratch(w, h) {
    if (w === _w && h === _h) return;
    _w = w; _h = h;
    _blurA = new Float32Array(w * h);
    _blurB = new Float32Array(w * h);
    _noise = new Float32Array(w * h);
    // Pre-bake a single-octave value-noise field (stays stable across
    // frames — the SEM substrate doesn't crawl).  Smoothed once with a
    // 3×3 box filter.
    const raw = new Float32Array(w * h);
    for (let i = 0; i < raw.length; i++) raw[i] = Math.random();
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const xm = (x - 1 + w) % w, xp = (x + 1) % w;
        const ym = (y - 1 + h) % h, yp = (y + 1) % h;
        _noise[y*w + x] = (
          raw[ym*w + xm] + raw[ym*w + x] + raw[ym*w + xp] +
          raw[y *w + xm] + raw[y *w + x] + raw[y *w + xp] +
          raw[yp*w + xm] + raw[yp*w + x] + raw[yp*w + xp]
        ) * (1/9) - 0.5;     // centred ±0.5
      }
    }
  }

  // Separable 3-tap Gaussian (σ ≈ 0.7) — kernel [0.25, 0.5, 0.25].
  // Two-buffer ping-pong: horizontal pass src→A, vertical pass A→B.
  function blur(h, w, src) {
    const A = _blurA, B = _blurB;
    // Horizontal pass.
    for (let y = 0; y < h; y++) {
      const off = y * w;
      for (let x = 0; x < w; x++) {
        const xm = (x - 1 + w) % w, xp = (x + 1) % w;
        A[off + x] = 0.25 * src[off + xm] + 0.5 * src[off + x] + 0.25 * src[off + xp];
      }
    }
    // Vertical pass.
    for (let y = 0; y < h; y++) {
      const ym = (y - 1 + h) % h, yp = (y + 1) % h;
      for (let x = 0; x < w; x++) {
        B[y*w + x] = 0.25 * A[ym*w + x] + 0.5 * A[y*w + x] + 0.25 * A[yp*w + x];
      }
    }
    return B;
  }

  // ── Main render ─────────────────────────────────────────────────────────
  function render(height, w, h, pixels, opts) {
    opts = opts || {};
    ensureScratch(w, h);
    const palette = PALETTES[opts.palette] || PALETTES["warm-sepia"];
    const ambient = 0.20;
    const specWeight = 0.30;
    const aoStrength = 0.08;
    const noiseGain = 0.06;
    const heightGain = 6.0;     // amplifies subtle field gradients
    // Light direction L = (0.4, 0.3, 0.85) normalised.
    const Lx = 0.4, Ly = 0.3, Lz = 0.85;
    const Lmag = Math.sqrt(Lx*Lx + Ly*Ly + Lz*Lz);
    const lx = Lx/Lmag, ly = Ly/Lmag, lz = Lz/Lmag;
    // Halfway vector H = normalise(L + V), V = (0,0,1).
    const Hx = lx, Hy = ly, Hz = lz + 1;
    const Hmag = Math.sqrt(Hx*Hx + Hy*Hy + Hz*Hz);
    const hx = Hx/Hmag, hy = Hy/Hmag, hz = Hz/Hmag;

    const smoothed = blur(h, w, height);

    for (let y = 0; y < h; y++) {
      const ym = (y - 1 + h) % h, yp = (y + 1) % h;
      for (let x = 0; x < w; x++) {
        const xm = (x - 1 + w) % w, xp = (x + 1) % w;
        const ic = y * w + x;

        // Centred-difference gradients on smoothed field.
        const dx = (smoothed[y *w + xp] - smoothed[y *w + xm]) * heightGain;
        const dy = (smoothed[yp*w + x ] - smoothed[ym*w + x ]) * heightGain;
        // Normal = normalise((-dx, -dy, 1)).
        const nz = 1;
        const nmag = Math.sqrt(dx*dx + dy*dy + 1);
        const nx = -dx / nmag, ny = -dy / nmag, nzn = nz / nmag;

        // Lambertian shading.
        let lamb = nx*lx + ny*ly + nzn*lz;
        if (lamb < 0) lamb = 0;

        // Specular highlight (Blinn-Phong, exponent 32).
        let spec = nx*hx + ny*hy + nzn*hz;
        if (spec < 0) spec = 0;
        spec = Math.pow(spec, 32) * specWeight;

        // Ambient occlusion via laplacian of the smoothed field.  Convex
        // (positive lap) gets brighter; concave (negative lap → creases)
        // gets darker.  Subtract max(0, -lap) to specifically dim creases.
        const lap = smoothed[y*w + xm] + smoothed[y*w + xp]
                  + smoothed[ym*w + x] + smoothed[yp*w + x]
                  - 4 * smoothed[ic];
        const ao = Math.max(0, -lap) * aoStrength;

        // Noise overlay (stable, pre-baked).
        const noise = _noise[ic] * noiseGain;

        // Final intensity, biased by the underlying scalar so that
        // "empty substrate" stays dim and "active chemistry" lights up.
        const presence = 0.4 + 0.6 * Math.min(1, Math.max(0, smoothed[ic]));
        let intensity = (ambient + lamb + spec - ao + noise) * presence;
        if (intensity < 0) intensity = 0;
        if (intensity > 1) intensity = 1;

        const idx = Math.min(255, (intensity * 255) | 0) * 3;
        const p = ic * 4;
        pixels[p]   = palette[idx];
        pixels[p+1] = palette[idx+1];
        pixels[p+2] = palette[idx+2];
        pixels[p+3] = 255;
      }
    }
  }

  window.SEM = {
    PALETTES,
    render,
    paletteNames: () => Object.keys(PALETTES),
  };
})();
