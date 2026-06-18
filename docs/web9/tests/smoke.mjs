// web7 lab smoke tests — run with `node docs/web7/tests/smoke.mjs`.
//
// web7 is WebGL + ES-modules (Three.js), so it can't use web2/web3's vm-IIFE
// harness — there's no GL context in node. Instead this is a zero-dependency
// STRUCTURAL gate that catches the regressions a static WebGL bundle would
// otherwise ship unnoticed:
//   - a broken importmap (the page can't resolve `three` at all),
//   - a renamed/missing module that an import still points at,
//   - a syntax error in any module (node --check),
//   - the stage registry or apparatus exports drifting out of shape.
//
// Pure assertions; exits non-zero on the first hard failure so it gates CI.

import fs from "node:fs";
import vm from "node:vm";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, "..");

let failures = 0, checks = 0;
const fail = (m) => { failures++; console.error(`  ✗ ${m}`); };
const ok = () => { checks++; };
const assert = (cond, m) => (cond ? ok() : fail(m));
const read = (rel) => fs.readFileSync(path.join(ROOT, rel), "utf8");
const exists = (rel) => fs.existsSync(path.join(ROOT, rel));

console.log("Running web7 lab smoke tests…\n");

// 1. index.html: importmap is valid JSON and maps `three` + addons to a CDN.
const html = read("index.html");
const mapMatch = html.match(/<script type="importmap">([\s\S]*?)<\/script>/);
assert(!!mapMatch, "index.html has no importmap");
if (mapMatch) {
  let map;
  try { map = JSON.parse(mapMatch[1]); ok(); } catch (e) { fail(`importmap is not valid JSON: ${e.message}`); }
  if (map) {
    assert(typeof map.imports?.three === "string" && /three/.test(map.imports.three),
      "importmap does not map bare specifier `three`");
    assert(typeof map.imports?.["three/addons/"] === "string",
      "importmap does not map `three/addons/`");
  }
}

// 2. index.html references files that exist.
for (const rel of ["styles.css", "main.js"]) {
  assert(html.includes(rel), `index.html does not reference ${rel}`);
  assert(exists(rel), `referenced file missing: ${rel}`);
}

// 3. Every JS module passes `node --check`, and its relative imports resolve.
const APPARATUS = [
  "miller_urey", "grayscott_dish", "raf_flask", "vesicle_microscope", "vent_reactor",
  "mineral_flask", "chirality_polarimeter", "rna_thermocycler", "code_bench",
  "coacervate_microscope", "microfluidic_chip", "luca_console", "stromatolite",
];
const MODULES = [
  "scene.js", "main.js", "apparatus/lib.js", "apparatus/placeholder.js", "tests/smoke.mjs",
  ...APPARATUS.map((a) => `apparatus/${a}.js`),
];
for (const rel of MODULES) {
  assert(exists(rel), `module missing: ${rel}`);
  if (!exists(rel)) continue;
  try {
    execFileSync(process.execPath, ["--check", path.join(ROOT, rel)], { stdio: "pipe" });
    ok();
  } catch (e) {
    fail(`syntax error in ${rel}: ${String(e.stderr || e).slice(0, 200)}`);
  }
  // relative (./ or ../) imports must point at real files
  const src = read(rel);
  const dir = path.dirname(path.join(ROOT, rel));
  for (const m of src.matchAll(/from\s+["'](\.[^"']+)["']/g)) {
    const target = path.resolve(dir, m[1]);
    assert(fs.existsSync(target), `${rel}: import "${m[1]}" resolves to missing file`);
  }
}

// 4. main.js wires every apparatus into the registry.
const main = read("main.js");
for (const a of APPARATUS) {
  assert(new RegExp(`from\\s+["']\\.\\/apparatus\\/${a}\\.js["']`).test(main),
    `main.js does not import apparatus/${a}.js`);
}
assert(/const\s+STAGES\s*=\s*\[/.test(main), "main.js has no STAGES registry");
assert(/buildPlaceholder/.test(main), "main.js dropped the buildPlaceholder fallback");

// 5. Every apparatus module exports a contract-shaped `meta` (id + build) and a
//    build() that installs the anim contract (setRunning / getProgress / update).
const SPECIMEN = new Set(["stromatolite"]); // capstone: setRunning/getProgress may be no-ops
for (const a of APPARATUS) {
  const src = read(`apparatus/${a}.js`);
  assert(/export\s+const\s+meta\s*=/.test(src), `${a}.js missing meta export`);
  assert(/\bid:\s*['"][\w-]+['"]/.test(src), `${a}.js meta has no id`);
  assert(/\bbuild\b/.test(src), `${a}.js meta has no build reference`);
  assert(/userData/.test(src) && /\banim\b/.test(src), `${a}.js never installs an anim on group.userData`);
  assert(/setRunning/.test(src), `${a}.js anim missing setRunning`);
  assert(/getProgress/.test(src), `${a}.js anim missing getProgress`);
  if (!SPECIMEN.has(a)) assert(/update/.test(src), `${a}.js anim missing update`);
}
const ph = read("apparatus/placeholder.js");
assert(/export\s+function\s+buildPlaceholder/.test(ph), "placeholder.js missing buildPlaceholder export");

// All 13 stages (Stage 0 + 11 pipeline + capstone) must be in the registry.
const stageBlock = main.match(/const\s+STAGES\s*=\s*\[([\s\S]*?)\]/);
assert(!!stageBlock, "could not parse STAGES registry");
if (stageBlock) {
  const names = stageBlock[1].split(",").map((s) => s.trim()).filter(Boolean);
  assert(names.length === 13, `expected 13 stages in registry, found ${names.length}`);
  // web9: the catalogue must walk the engine's canonical scientific order
  // (cellauto EXTENDED_STAGE_CLASSES) — not web8's legacy "5 canonical stages
  // first, extras appended" layout. This locks the 13-stage science to the
  // order the abiogenesis pipeline actually runs the stages in.
  const CANONICAL = [
    "millerUrey", "vent", "grayscott", "minerals", "raf", "chirality",
    "rna", "code", "coacervate", "vesicles", "selection", "luca", "stromatolite",
  ];
  assert(JSON.stringify(names) === JSON.stringify(CANONICAL),
    `STAGES not in canonical scientific order.\n      expected: ${CANONICAL.join(", ")}\n      found:    ${names.join(", ")}`);
}

// 6. scene.js sets up the photoreal pillars (PBR env + ACES + bloom).
const scene = read("scene.js");
assert(/ACESFilmicToneMapping/.test(scene), "scene.js does not use ACES tone-mapping");
assert(/RoomEnvironment/.test(scene), "scene.js does not set up image-based lighting");
assert(/UnrealBloomPass/.test(scene), "scene.js does not add bloom (spark glow)");

// ── 7. Live SEM experiment integration ──────────────────────────────────────
// This is the split-screen lab→experiment feature. It bridges ES modules and
// CLASSIC scripts via globals, so a regression here (a renamed rule key, a
// dropped <script>, viridis.js loaded after a rule that reads VIRIDIS_LUT, a
// STAGE_MAP value with no copied rule) would ship green under the checks above.
// This block gates all of those structurally AND at runtime.

// 7a. Parse STAGE_MAP out of main.js and confirm every key matches a meta id.
const META_IDS = {
  miller_urey: "stage0-miller-urey", grayscott_dish: "stage1-grayscott",
  raf_flask: "stage2-raf", vesicle_microscope: "stage3-vesicles",
  vent_reactor: "stage4-vent", mineral_flask: "stage5-minerals",
  chirality_polarimeter: "stage6-chirality", rna_thermocycler: "stage7-rna",
  code_bench: "stage8-code", coacervate_microscope: "stage9-coacervate",
  microfluidic_chip: "stage10-selection", luca_console: "stage11-luca",
  stromatolite: "capstone-stromatolite",
};
const mapBlock = main.match(/const\s+STAGE_MAP\s*=\s*\{([\s\S]*?)\}/);
assert(!!mapBlock, "main.js has no STAGE_MAP");
const stageMap = {};
if (mapBlock) {
  for (const m of mapBlock[1].matchAll(/['"]([\w-]+)['"]\s*:\s*['"]([\w-]+)['"]/g)) {
    stageMap[m[1]] = m[2];
  }
  const metaIdSet = new Set(Object.values(META_IDS));
  assert(Object.keys(stageMap).length === 13,
    `STAGE_MAP should have 13 entries, found ${Object.keys(stageMap).length}`);
  for (const stageId of Object.keys(stageMap)) {
    assert(metaIdSet.has(stageId), `STAGE_MAP key "${stageId}" is not a real apparatus meta id`);
  }
}

// 7b. index.html loads viridis.js + sem.js + the mapped rule files as CLASSIC
//     scripts (no type=module) BEFORE the module main.js, in a safe order.
const classicSrcs = [...html.matchAll(/<script\s+src="(\.\/experiment\/[^"]+)"\s*>/g)].map((m) => m[1]);
const moduleTag = html.match(/<script\s+type="module"\s+src="\.\/main\.js"\s*>/);
assert(!!moduleTag, "index.html does not load main.js as a module");
const moduleIdx = moduleTag ? html.indexOf(moduleTag[0]) : -1;
for (const src of classicSrcs) {
  assert(html.indexOf(`src="${src}"`) < moduleIdx,
    `classic script ${src} must be loaded BEFORE the module main.js`);
  const rel = src.replace(/^\.\//, "");
  assert(exists(rel), `index.html references missing experiment file ${src}`);
  // must NOT be a module (globals wouldn't bridge to main.js)
  assert(!new RegExp(`type="module"[^>]*src="${src.replace(/[.\/]/g, "\\$&")}"`).test(html)
       && !new RegExp(`src="${src.replace(/[.\/]/g, "\\$&")}"[^>]*type="module"`).test(html),
    `experiment script ${src} must be a CLASSIC script, not a module`);
}
// Index each experiment <script> tag by its src, in document (= execution) order.
const tagIdx = (src) => html.indexOf(`src="./experiment/${src}"`);
const viridisIdx = tagIdx("viridis.js");
const semIdx = tagIdx("sem.js");
assert(viridisIdx > -1 && semIdx > -1, "index.html must load viridis.js and sem.js");
// viridis.js (defines the bare global VIRIDIS_LUT) must precede EVERY rule that
// reads it — checked against the actual reader files, not just the first rule,
// so a reordered/duplicated viridis tag can't slip a reader ahead of its LUT.
const VIRIDIS_READERS = ["grayscott.js", "life.js"];
for (const r of VIRIDIS_READERS) {
  const ri = tagIdx(`rules/${r}`);
  assert(ri > -1, `index.html does not load rules/${r}`);
  assert(viridisIdx > -1 && viridisIdx < ri,
    `viridis.js must load before rules/${r} (it reads VIRIDIS_LUT)`);
}
// every STAGE_MAP value must have a copied rule file loaded as a classic script,
// using the underscore filename convention (natural-selection → natural_selection.js).
for (const ruleId of new Set(Object.values(stageMap))) {
  const file = `experiment/rules/${ruleId.replace(/-/g, "_")}.js`;
  assert(exists(file), `STAGE_MAP value "${ruleId}" has no copied rule file (${file})`);
  assert(html.includes(`src="./${file}"`), `index.html does not load ${file}`);
}

// 7c. The second canvas + 3-way toggle markup exists.
assert(/id="expCanvas"/.test(html), "index.html missing the experiment canvas (#expCanvas)");
assert(/id="expCaption"/.test(html), "index.html missing the SEM caption (#expCaption)");
assert(/id="viewToggle"/.test(html), "index.html missing the view toggle (#viewToggle)");
for (const v of ["lab", "split", "exp"]) {
  assert(new RegExp(`data-view="${v}"`).test(html), `view toggle missing a "${v}" button`);
}

// 7d. main.js drives the SEM pipeline with web3's exact convention.
assert(/SEM\.render\s*\(/.test(main), "main.js does not call SEM.render");
assert(/renderHeight\s*\(/.test(main), "main.js does not call renderHeight (SEM depth path)");
assert(/putImageData/.test(main), "main.js does not blit the experiment frame");

// 7e. RUNTIME: load the classic scripts the way the browser does (one shared
//     lexical scope so rules see VIRIDIS_LUT), then confirm every STAGE_MAP rule
//     instantiates, resets, steps, and passes through SEM.render to a painted,
//     fully-opaque RGBA buffer — i.e. the experiment canvas can't be blank.
const sandbox = { window: { CA: { RULES: {} } }, Math, Float32Array, Uint8Array, Uint8ClampedArray, console };
sandbox.CA = sandbox.window.CA;
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
const EXP = path.join(ROOT, "experiment");
const loadOrder = [
  "viridis.js", "sem.js",
  ...[...new Set(Object.values(stageMap))].map((r) => `rules/${r.replace(/-/g, "_")}.js`),
];
// Concatenate so VIRIDIS_LUT (a bare top-level const) is in scope for the rules,
// exactly as sibling classic <script> tags share scope in the browser. Read
// defensively: a missing file reported by 7b above shouldn't crash this block.
let SEM = null, RULES = null;
const missing = loadOrder.filter((f) => !fs.existsSync(path.join(EXP, f)));
if (missing.length) {
  fail(`experiment files missing, cannot load bundle: ${missing.join(", ")}`);
} else {
  const bundle = loadOrder.map((f) => fs.readFileSync(path.join(EXP, f), "utf8")).join("\n;\n");
  try {
    vm.runInContext(bundle, sandbox, { filename: "experiment-bundle.js" });
    SEM = sandbox.window.SEM;
    RULES = sandbox.window.CA.RULES;
    ok();
  } catch (e) {
    fail(`experiment classic scripts failed to load: ${String(e.message).slice(0, 160)}`);
  }
}
assert(SEM && typeof SEM.render === "function", "window.SEM.render not defined after loading sem.js");
if (SEM && RULES) {
  for (const [stageId, ruleId] of Object.entries(stageMap)) {
    const factory = RULES[ruleId];
    if (typeof factory !== "function") { fail(`CA.RULES["${ruleId}"] (for ${stageId}) is not a factory`); continue; }
    try {
      const rule = factory();
      assert(Number.isInteger(rule.width) && Number.isInteger(rule.height) && rule.width > 0,
        `${ruleId}: bad width/height`);
      assert(typeof rule.renderHeight === "function", `${ruleId}: missing renderHeight (SEM path)`);
      rule.reset();
      for (let s = 0; s < 12; s++) rule.step();
      const ht = new Float32Array(rule.width * rule.height);
      rule.renderHeight(ht);
      const pixels = new Uint8ClampedArray(rule.width * rule.height * 4);
      SEM.render(ht, rule.width, rule.height, pixels, { palette: "warm-sepia" });
      // Must be fully opaque (no transparent gaps) and not a single flat colour.
      let opaque = true, distinct = new Set();
      for (let i = 0; i < pixels.length; i += 4) {
        if (pixels[i + 3] !== 255) { opaque = false; break; }
        distinct.add((pixels[i] << 16) | (pixels[i + 1] << 8) | pixels[i + 2]);
      }
      assert(opaque, `${ruleId} (${stageId}): SEM output has non-opaque pixels`);
      assert(distinct.size > 1, `${ruleId} (${stageId}): SEM output is a single flat colour (blank)`);
    } catch (e) {
      fail(`${ruleId} (${stageId}) SEM pipeline threw: ${String(e.message).slice(0, 160)}`);
    }
  }
}

console.log(`\n${checks} checks passed, ${failures} failure(s).`);
process.exit(failures === 0 ? 0 : 1);
