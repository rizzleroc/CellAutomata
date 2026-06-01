// web4 lab smoke tests — run with `node docs/web4/tests/smoke.mjs`.
//
// web4 is WebGL + ES-modules (Three.js), so it can't use web2/web3's vm-IIFE
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
import path from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const WEB4 = path.join(HERE, "..");

let failures = 0, checks = 0;
const fail = (m) => { failures++; console.error(`  ✗ ${m}`); };
const ok = () => { checks++; };
const assert = (cond, m) => (cond ? ok() : fail(m));
const read = (rel) => fs.readFileSync(path.join(WEB4, rel), "utf8");
const exists = (rel) => fs.existsSync(path.join(WEB4, rel));

console.log("Running web4 lab smoke tests…\n");

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
    execFileSync(process.execPath, ["--check", path.join(WEB4, rel)], { stdio: "pipe" });
    ok();
  } catch (e) {
    fail(`syntax error in ${rel}: ${String(e.stderr || e).slice(0, 200)}`);
  }
  // relative (./ or ../) imports must point at real files
  const src = read(rel);
  const dir = path.dirname(path.join(WEB4, rel));
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
}

// 6. scene.js sets up the photoreal pillars (PBR env + ACES + bloom).
const scene = read("scene.js");
assert(/ACESFilmicToneMapping/.test(scene), "scene.js does not use ACES tone-mapping");
assert(/RoomEnvironment/.test(scene), "scene.js does not set up image-based lighting");
assert(/UnrealBloomPass/.test(scene), "scene.js does not add bloom (spark glow)");

console.log(`\n${checks} checks passed, ${failures} failure(s).`);
process.exit(failures === 0 ? 0 : 1);
