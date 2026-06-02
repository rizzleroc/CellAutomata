// web4 experiment RE-RENDER harness — node, no browser.
//
//   node docs/web4/tests/render_experiments.mjs <outDir>
//
// For each of the 13 STAGE_MAP stages this loads the SAME classic scripts the
// browser does (viridis + sem + the 12 rule files, in one shared lexical scope
// so the rules see VIRIDIS_LUT), instantiates the mapped rule, applies the SAME
// preset + headless warm-up as main.js FIX 2 (MATURITY), renders the height
// field, supersamples it bilinearly to the hi-res backing (matching main.js's
// expScale = round(760 / max(W,H))), shades it through SEM.render, then applies
// the SAME colour-tint pixel math as main.js FIX 1 for the tint stages, and
// writes one PNG per stage to <outDir>. Sprites are canvas-2D-only, so they are
// SKIPPED here with a logged note (they don't affect the non-blank check).
//
// It reports per-stage pixel variance so a blank/near-flat frame is caught;
// minerals (stage5, the grayscott dup) MUST be non-zero.

import fs from "node:fs";
import vm from "node:vm";
import path from "node:path";
import zlib from "node:zlib";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const WEB4 = path.join(HERE, "..");
const EXP = path.join(WEB4, "experiment");
const OUT = process.argv[2] || path.join(HERE, "_expcheck");
fs.mkdirSync(OUT, { recursive: true });

const EXP_PALETTE = "warm-sepia";

// ── STAGE_MAP — kept in sync with main.js (web4 stage id → web3 rule id) ─────
const STAGE_MAP = {
  "stage0-miller-urey": "soup",  "stage1-grayscott": "grayscott", "stage2-raf": "raf",
  "stage3-vesicles": "vesicles", "stage4-vent": "vents",          "stage5-minerals": "grayscott",
  "stage6-chirality": "chirality", "stage7-rna": "rna",           "stage8-code": "code",
  "stage9-coacervate": "coacervate", "stage10-selection": "natural-selection",
  "stage11-luca": "luca",        "capstone-stromatolite": "life",
};

// ── SEM_LAYERS / MATURITY — copied verbatim from main.js so the harness renders
//    exactly what the live page does. ─────────────────────────────────────────
const SEM_LAYERS = {
  soup: { tint: 0.50, sprites: true }, grayscott: {}, raf: {},
  vesicles: { sprites: true }, vents: {},
  chirality: { tint: 0.60, sprites: true }, rna: {}, code: {},
  coacervate: { sprites: true },
  "natural-selection": { tint: 0.55, sprites: true },
  luca: { tint: 0.60 }, life: {},
};
const MATURITY = {
  chirality:           { preset: "homochiral sweep",  steps: 120 },
  luca:                { preset: "sharp LUCA",        steps: 60  },
  coacervate:          { preset: "few large droplets", steps: 80 },
  vesicles:            { preset: "stiff spheres",     steps: 80  },
  "natural-selection": { steps: 40 },
  soup:                { steps: 60  },
  vents:               { steps: 120 },
  raf:                 { steps: 30  },
  rna:                 { steps: 80  },
  code:                { steps: 60  },
  life:                { steps: 60  },
  grayscott:           { preset: "mitosis", seed: "randomize", steps: 600 },
};

function applyPreset(rule, label) {
  if (!rule || !label) return false;
  if (Array.isArray(rule.presets)) {
    const p = rule.presets.find((pr) => pr.label === label);
    if (p) {
      if (p.values) for (const k in p.values) {
        if (rule.params[k]) { rule.params[k].value = p.values[k]; rule.onParamChange?.(k); }
      }
      if (p.reseed) rule.reset();
      return true;
    }
  }
  const pe = rule.params && rule.params.preset;
  if (pe && Array.isArray(pe.options) && pe.options.includes(label)) {
    pe.value = label; rule.onParamChange?.("preset"); return true;
  }
  return false;
}
function warmUp(rule, ruleId) {
  const cfg = MATURITY[ruleId];
  if (!cfg) return;
  if (cfg.preset) applyPreset(rule, cfg.preset);
  if (cfg.seed && typeof rule[cfg.seed] === "function") rule[cfg.seed]();
  for (let s = 0; s < (cfg.steps | 0); s++) rule.step();
}

// ── Bilinear height upscale — identical to main.js _upscaleHeight. ───────────
function upscaleHeight(src, w, h, dst, W2, H2) {
  const sx = (w - 1) / Math.max(1, W2 - 1);
  const sy = (h - 1) / Math.max(1, H2 - 1);
  for (let y = 0; y < H2; y++) {
    const fy = y * sy, y0 = fy | 0, y1 = y0 + 1 < h ? y0 + 1 : y0, ty = fy - y0;
    for (let x = 0; x < W2; x++) {
      const fx = x * sx, x0 = fx | 0, x1 = x0 + 1 < w ? x0 + 1 : x0, tx = fx - x0;
      const a = src[y0 * w + x0], b = src[y0 * w + x1];
      const c = src[y1 * w + x0], d = src[y1 * w + x1];
      dst[y * W2 + x] = (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty;
    }
  }
}

// ── Colour-tint pass — identical math to main.js _tintSemWithColour. ─────────
function tintSemWithColour(pix, w2, h2, colour, gw, scale, amount) {
  for (let y = 0; y < h2; y++) {
    const ny = (y / scale) | 0;
    for (let x = 0; x < w2; x++) {
      const nx = (x / scale) | 0;
      const ci = (ny * gw + nx) * 4;
      const cr = colour[ci], cg = colour[ci + 1], cb = colour[ci + 2];
      const cmax = cr > cg ? (cr > cb ? cr : cb) : (cg > cb ? cg : cb);
      const cmin = cr < cg ? (cr < cb ? cr : cb) : (cg < cb ? cg : cb);
      if (cmax - cmin < 12) continue;
      const p = (y * w2 + x) * 4;
      const L = 0.299 * pix[p] + 0.587 * pix[p + 1] + 0.114 * pix[p + 2];
      const cl = 0.299 * cr + 0.587 * cg + 0.114 * cb;
      const g = cl > 1 ? L / cl : L;
      let tr = cr * g, tg = cg * g, tb = cb * g;
      if (tr > 255) tr = 255; if (tg > 255) tg = 255; if (tb > 255) tb = 255;
      pix[p]     = (pix[p]     * (1 - amount) + tr * amount) | 0;
      pix[p + 1] = (pix[p + 1] * (1 - amount) + tg * amount) | 0;
      pix[p + 2] = (pix[p + 2] * (1 - amount) + tb * amount) | 0;
    }
  }
}

// ── Minimal PNG encoder (RGBA, no filter) via zlib.deflateSync. ──────────────
function crc32(buf) {
  let c = ~0;
  for (let i = 0; i < buf.length; i++) {
    c ^= buf[i];
    for (let k = 0; k < 8; k++) c = (c >>> 1) ^ (0xEDB88320 & -(c & 1));
  }
  return (~c) >>> 0;
}
function chunk(type, data) {
  const len = Buffer.alloc(4); len.writeUInt32BE(data.length, 0);
  const t = Buffer.from(type, "ascii");
  const body = Buffer.concat([t, data]);
  const crc = Buffer.alloc(4); crc.writeUInt32BE(crc32(body), 0);
  return Buffer.concat([len, body, crc]);
}
function encodePNG(rgba, w, h) {
  const sig = Buffer.from([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]);
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(w, 0); ihdr.writeUInt32BE(h, 4);
  ihdr[8] = 8;    // bit depth
  ihdr[9] = 6;    // colour type RGBA
  ihdr[10] = 0; ihdr[11] = 0; ihdr[12] = 0;
  // Raw scanlines, each prefixed with filter byte 0.
  const stride = w * 4;
  const raw = Buffer.alloc((stride + 1) * h);
  for (let y = 0; y < h; y++) {
    raw[y * (stride + 1)] = 0;
    Buffer.from(rgba.buffer, rgba.byteOffset + y * stride, stride)
      .copy(raw, y * (stride + 1) + 1);
  }
  const idat = zlib.deflateSync(raw, { level: 6 });
  return Buffer.concat([sig, chunk("IHDR", ihdr), chunk("IDAT", idat), chunk("IEND", Buffer.alloc(0))]);
}

// ── Load the experiment bundle in a shared VM context (browser-equivalent). ──
const sandbox = { window: { CA: { RULES: {} } }, Math, Float32Array, Uint8Array, Uint8ClampedArray, console };
sandbox.CA = sandbox.window.CA;
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
const loadOrder = [
  "viridis.js", "sem.js",
  ...[...new Set(Object.values(STAGE_MAP))].map((r) => `rules/${r.replace(/-/g, "_")}.js`),
];
const bundle = loadOrder.map((f) => fs.readFileSync(path.join(EXP, f), "utf8")).join("\n;\n");
vm.runInContext(bundle, sandbox, { filename: "experiment-bundle.js" });
const SEM = sandbox.window.SEM;
const RULES = sandbox.window.CA.RULES;
if (!SEM || typeof SEM.render !== "function") { console.error("SEM.render missing"); process.exit(1); }

// Variance of the green channel — cheap "is this a flat plate?" probe.
function pixelVariance(rgba) {
  let mean = 0, n = rgba.length / 4;
  for (let i = 1; i < rgba.length; i += 4) mean += rgba[i];
  mean /= n;
  let v = 0;
  for (let i = 1; i < rgba.length; i += 4) { const d = rgba[i] - mean; v += d * d; }
  return v / n;
}

console.log(`Re-rendering ${Object.keys(STAGE_MAP).length} experiment stages → ${OUT}\n`);
let fails = 0, rendered = 0;
for (const [stageId, ruleId] of Object.entries(STAGE_MAP)) {
  try {
    const factory = RULES[ruleId];
    if (typeof factory !== "function") throw new Error(`CA.RULES["${ruleId}"] missing`);
    const rule = factory();
    rule.reset();
    warmUp(rule, ruleId);                                   // SAME preset + steps as FIX 2

    const W = rule.width, H = rule.height;
    const scale = Math.max(1, Math.round(760 / Math.max(W, H)));
    const W2 = W * scale, H2 = H * scale;

    const hb = new Float32Array(W * H);
    rule.renderHeight(hb);
    const pix = new Uint8ClampedArray(W2 * H2 * 4);
    if (scale > 1) {
      const hi = new Float32Array(W2 * H2);
      upscaleHeight(hb, W, H, hi, W2, H2);
      SEM.render(hi, W2, H2, pix, { palette: EXP_PALETTE });
    } else {
      SEM.render(hb, W, H, pix, { palette: EXP_PALETTE });
    }

    const layers = SEM_LAYERS[ruleId] || {};
    if (layers.tint && typeof rule.render === "function") {
      const colour = new Uint8ClampedArray(W * H * 4);
      rule.render(colour);
      tintSemWithColour(pix, W2, H2, colour, W, scale, layers.tint);
    }
    const spriteNote = layers.sprites ? "  (sprites: SKIPPED — canvas-2D only in node)" : "";

    // Opacity + variance gate.
    let opaque = true;
    for (let i = 3; i < pix.length; i += 4) { if (pix[i] !== 255) { opaque = false; break; } }
    const variance = pixelVariance(pix);
    const blank = variance < 1e-6;
    if (!opaque || blank) fails++;

    const png = encodePNG(pix, W2, H2);
    const file = path.join(OUT, `${stageId}.png`);
    fs.writeFileSync(file, png);
    rendered++;
    const flag = blank ? " ✗ BLANK" : (!opaque ? " ✗ NON-OPAQUE" : " ✓");
    console.log(
      `${flag} ${stageId.padEnd(22)} ${ruleId.padEnd(18)} ${W2}×${H2}` +
      `  var=${variance.toFixed(1).padStart(8)}${spriteNote}`
    );
  } catch (e) {
    fails++;
    console.error(`  ✗ ${stageId} (${ruleId}): ${e.message}`);
  }
}

console.log(`\n${rendered} PNGs written to ${OUT}; ${fails} blank/failed.`);
process.exit(fails === 0 ? 0 : 1);
