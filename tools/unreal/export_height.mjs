#!/usr/bin/env node
// =============================================================================
// export_height.mjs  —  the science bridge
// -----------------------------------------------------------------------------
// Runs the repo's OWN Gray-Scott reaction-diffusion PDE (a direct port of
// docs/web3/rules/grayscott.js) and dumps the true `v` height-field to a
// 16-bit grayscale PNG that Unreal Engine imports as a displacement map.
//
// Why this exists: the spots that grow, split and replicate in the Gray-Scott
// "mitosis" regime ARE the dividing cells. Instead of asking a video model to
// hallucinate cell division, we hand UE the real simulated surface and let the
// renderer do lighting / glow / depth. Deterministic in, deterministic out.
//
// No npm dependencies. Pure Node (>=16). 16-bit PNG is written by hand with
// zlib (built in). Verified in the authoring sandbox.
//
//   node export_height.mjs                                  # single hero map
//   STEPS=4000 PRESET=mitosis SEED=1337 RES=1024 \
//     OUT=protocell_height.png node export_height.mjs
//
//   # real division flipbook (the spots actually divide across frames):
//   STEPS=1100 FRAMES=72 FRAME_STEP=16 RES=512 OUTDIR=seq node export_height.mjs
//
// Env:
//   PRESET     spots|stripes|mitosis|waves|labyrinth  (default mitosis)
//   F, k       override the Pearson F/k directly       (optional)
//   STEPS      visible frames to warm up (x SUBSTEPS)  (default 4000)
//   SEED       PRNG seed for the initial perturbation  (default 1337)
//   RES        output resolution; bilinear-resampled   (default native 220)
//   OUT        single-frame output png  (default ./protocell_height.png)
//   NORM       minmax|fixed  height normalisation       (default minmax)
//   FRAMES     N>0 -> export a sequence of N frames     (default 0 = single)
//   FRAME_STEP visible steps between exported frames    (default 16)
//   OUTDIR     directory for sequence frames            (default ./seq)
//
// NORM note: for a SEQUENCE, fixed normalisation is forced so heights are
// comparable frame-to-frame (a per-frame minmax stretch would make the surface
// "breathe" as the global max drifts). Single-frame export defaults to minmax.
//
// DENSITY note: with PRESET=mitosis the colony starts as a populated cluster
// (~19% coverage at STEPS=1100) and divides outward to a full lattice (~45%).
// Lower STEPS for a sparser, faster-growing start; raise it for a settled
// steady-state field. No sparse tail at steady state.
// =============================================================================

import zlib from "node:zlib";
import { writeFileSync, mkdirSync } from "node:fs";

// ---- exact constants from docs/web3/rules/grayscott.js -----------------------
const W = 220;
const H = 220;
const Du = 0.16;
const Dv = 0.08;
const DT = 1.0;
const SUBSTEPS = 10; // PDE substeps per visible frame, same as the web rule

// Pearson (1993) presets — identical numbers to the web rule and the Python
// GRAY_SCOTT_PRESETS table. "mitosis" is the self-replicating / dividing regime.
const PRESETS = {
  spots:     { F: 0.035,  k: 0.065  },
  stripes:   { F: 0.040,  k: 0.060  },
  mitosis:   { F: 0.0367, k: 0.0649 },
  waves:     { F: 0.014,  k: 0.045  },
  labyrinth: { F: 0.039,  k: 0.058  },
};

// ---- config from env ---------------------------------------------------------
const presetName = (process.env.PRESET || "mitosis").toLowerCase();
const preset = PRESETS[presetName] || PRESETS.mitosis;
const F = process.env.F !== undefined ? parseFloat(process.env.F) : preset.F;
const k = process.env.k !== undefined ? parseFloat(process.env.k) : preset.k;
const STEPS = parseInt(process.env.STEPS || "4000", 10);
const SEED = parseInt(process.env.SEED || "1337", 10);
const RES = parseInt(process.env.RES || String(W), 10);
const OUT = process.env.OUT || "protocell_height.png";
const FRAMES = parseInt(process.env.FRAMES || "0", 10);
const FRAME_STEP = parseInt(process.env.FRAME_STEP || "16", 10);
const OUTDIR = process.env.OUTDIR || "seq";
const NORM = (process.env.NORM || (FRAMES > 0 ? "fixed" : "minmax")).toLowerCase();

// ---- deterministic PRNG (mulberry32) — replaces Math.random for repeatability
function mulberry32(a) {
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const rand = mulberry32(SEED);

// ---- simulation buffers ------------------------------------------------------
let u  = new Float32Array(W * H);
let v  = new Float32Array(W * H);
let un = new Float32Array(W * H);
let vn = new Float32Array(W * H);

function seed() {
  u.fill(1.0);
  v.fill(0.0);
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
  for (let i = 0; i < v.length; i++) {
    v[i] += (rand() - 0.5) * 0.02;
    if (v[i] < 0) v[i] = 0;
    else if (v[i] > 1) v[i] = 1;
  }
}

function substep(F, k) {
  for (let y = 0; y < H; y++) {
    const ym = (y - 1 + H) % H;
    const yp = (y + 1) % H;
    for (let x = 0; x < W; x++) {
      const xm = (x - 1 + W) % W;
      const xp = (x + 1) % W;
      const ic = y * W + x;
      const il = y * W + xm;
      const ir = y * W + xp;
      const iuu = ym * W + x;
      const id = yp * W + x;
      const lapU = u[il] + u[ir] + u[iuu] + u[id] - 4 * u[ic];
      const lapV = v[il] + v[ir] + v[iuu] + v[id] - 4 * v[ic];
      const uc = u[ic];
      const vc = v[ic];
      const uvv = uc * vc * vc;
      let uNew = uc + DT * (Du * lapU - uvv + F * (1.0 - uc));
      let vNew = vc + DT * (Dv * lapV + uvv - (F + k) * vc);
      if (uNew < 0) uNew = 0; else if (uNew > 1) uNew = 1;
      if (vNew < 0) vNew = 0; else if (vNew > 1) vNew = 1;
      un[ic] = uNew;
      vn[ic] = vNew;
    }
  }
  let t = u; u = un; un = t;
  t = v; v = vn; vn = t;
}

// ---- 16-bit grayscale PNG writer (no deps) -----------------------------------
const CRC_TABLE = (() => {
  const t = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let kk = 0; kk < 8; kk++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1;
    t[n] = c >>> 0;
  }
  return t;
})();
function crc32(buf) {
  let c = 0xFFFFFFFF;
  for (let i = 0; i < buf.length; i++) c = CRC_TABLE[(c ^ buf[i]) & 0xFF] ^ (c >>> 8);
  return (c ^ 0xFFFFFFFF) >>> 0;
}
function chunk(type, data) {
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length, 0);
  const body = Buffer.concat([Buffer.from(type, "ascii"), data]);
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(body), 0);
  return Buffer.concat([len, body, crc]);
}
function writePng16Gray(path, width, height, samples16) {
  const sig = Buffer.from([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]);
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 16;  // bit depth
  ihdr[9] = 0;   // colour type 0 = grayscale
  const rowBytes = width * 2;
  const raw = Buffer.alloc(height * (rowBytes + 1));
  let o = 0;
  for (let y = 0; y < height; y++) {
    raw[o++] = 0; // filter: none
    for (let x = 0; x < width; x++) {
      const s = samples16[y * width + x];
      raw[o++] = (s >>> 8) & 0xFF; // big-endian sample
      raw[o++] = s & 0xFF;
    }
  }
  const idat = zlib.deflateSync(raw, { level: 9 });
  writeFileSync(path, Buffer.concat([
    sig, chunk("IHDR", ihdr), chunk("IDAT", idat), chunk("IEND", Buffer.alloc(0)),
  ]));
}

// ---- bilinear resample of the v field to RES x RES (toroidal-friendly) -------
function resample(field, srcW, srcH, dstW, dstH) {
  if (dstW === srcW && dstH === srcH) return field.slice();
  const out = new Float32Array(dstW * dstH);
  for (let y = 0; y < dstH; y++) {
    const fy = (y / dstH) * srcH;
    const y0 = Math.floor(fy) % srcH;
    const y1 = (y0 + 1) % srcH;
    const ty = fy - Math.floor(fy);
    for (let x = 0; x < dstW; x++) {
      const fx = (x / dstW) * srcW;
      const x0 = Math.floor(fx) % srcW;
      const x1 = (x0 + 1) % srcW;
      const tx = fx - Math.floor(fx);
      const a = field[y0 * srcW + x0];
      const b = field[y0 * srcW + x1];
      const c = field[y1 * srcW + x0];
      const d = field[y1 * srcW + x1];
      const top = a + (b - a) * tx;
      const bot = c + (d - c) * tx;
      out[y * dstW + x] = top + (bot - top) * ty;
    }
  }
  return out;
}

// Encode the current v field (resampled + normalised) to a 16-bit PNG and
// return coverage stats. NORM=fixed assumes v in [0,1]; minmax stretches.
function encodeField(path) {
  const field = resample(v, W, H, RES, RES); // renderHeight: v IS the height
  let lo = Infinity, hi = -Infinity, sum = 0, nonzero = 0;
  for (let i = 0; i < field.length; i++) {
    const val = field[i];
    if (val < lo) lo = val;
    if (val > hi) hi = val;
    sum += val;
    if (val > 0.05) nonzero++;
  }
  let scale, offset;
  if (NORM === "fixed") { offset = 0; scale = 1; }
  else { offset = lo; scale = hi > lo ? 1 / (hi - lo) : 1; }
  const samples = new Uint16Array(field.length);
  for (let i = 0; i < field.length; i++) {
    let t = (field[i] - offset) * scale;
    if (t < 0) t = 0; else if (t > 1) t = 1;
    samples[i] = Math.round(t * 65535);
  }
  writePng16Gray(path, RES, RES, samples);
  return { lo, hi, mean: sum / field.length, coverage: nonzero / field.length };
}

// ---- main --------------------------------------------------------------------
console.error(
  `[export_height] preset=${presetName} F=${F} k=${k} steps=${STEPS} ` +
  `seed=${SEED} res=${RES} norm=${NORM}` +
  (FRAMES > 0 ? `  frames=${FRAMES} frameStep=${FRAME_STEP} outdir=${OUTDIR}` : "")
);
seed();
for (let s = 0; s < STEPS; s++) {
  for (let n = 0; n < SUBSTEPS; n++) substep(F, k);
}

if (FRAMES > 0) {
  // SEQUENCE: keep stepping the sim and dump a frame every FRAME_STEP steps.
  // UE imports this as a heightmap flipbook -> the spots really divide on screen.
  mkdirSync(OUTDIR, { recursive: true });
  let minCov = 1;
  for (let f = 0; f < FRAMES; f++) {
    const name = `${OUTDIR}/protocell_height.${String(f).padStart(4, "0")}.png`;
    const st = encodeField(name);
    minCov = Math.min(minCov, st.coverage);
    if (f === 0 || f === FRAMES - 1 || f % 12 === 0) {
      console.error(
        `[export_height]  frame ${String(f).padStart(4, "0")}  ` +
        `coverage=${(st.coverage * 100).toFixed(1)}%  mean=${st.mean.toFixed(3)}`
      );
    }
    for (let s = 0; s < FRAME_STEP; s++) {
      for (let n = 0; n < SUBSTEPS; n++) substep(F, k);
    }
  }
  console.error(`[export_height] wrote ${FRAMES} frames to ${OUTDIR}/  (min coverage ${(minCov * 100).toFixed(1)}%)`);
} else {
  // SINGLE FRAME
  const st = encodeField(OUT);
  console.error(
    `[export_height] wrote ${OUT}  ${RES}x${RES} 16-bit  ` +
    `v in [${st.lo.toFixed(3)}, ${st.hi.toFixed(3)}]  mean=${st.mean.toFixed(3)}  ` +
    `coverage=${(st.coverage * 100).toFixed(1)}%`
  );
  if (st.coverage < 0.04) {
    console.error(
      "[export_height] WARNING: sparse field (<4% coverage). " +
      "Increase STEPS or use PRESET=mitosis to get a denser dividing-cell surface."
    );
  }
}
