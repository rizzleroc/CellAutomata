// Pond Water Analyzer — structural smoke gate. Zero-dependency (no WebGL in
// node), so it can't render; instead it catches the regressions a static
// WebGL/ES-module bundle would otherwise ship unnoticed:
//   - a broken importmap (the page can't resolve `three`),
//   - a renamed/missing module an import still points at,
//   - a syntax error in any module (node --check),
//   - the organism roster or the anatomy contract drifting out of shape,
//   - the HUD losing an element main.js drives.
//
// Pure assertions; exits non-zero on the first hard failure so it gates CI.

import fs from "node:fs";
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

console.log("Running Pond Water Analyzer smoke tests…\n");

// 1. index.html: importmap is valid JSON and maps `three` + addons to a CDN.
const html = read("index.html");
const mapMatch = html.match(/<script type="importmap">([\s\S]*?)<\/script>/);
assert(!!mapMatch, "index.html has no importmap");
if (mapMatch) {
  let map;
  try { map = JSON.parse(mapMatch[1]); ok(); } catch (e) { fail(`importmap not valid JSON: ${e.message}`); }
  if (map) {
    assert(/three/.test(map.imports?.three || ""), "importmap does not map bare specifier `three`");
    assert(typeof map.imports?.["three/addons/"] === "string", "importmap does not map `three/addons/`");
  }
}

// 2. index.html references files that exist + loads main.js as a module.
for (const rel of ["styles.css", "main.js"]) {
  assert(html.includes(rel), `index.html does not reference ${rel}`);
  assert(exists(rel), `referenced file missing: ${rel}`);
}
assert(/<script\s+type="module"\s+src="\.\/main\.js"/.test(html), "index.html does not load main.js as a module");

// 3. Every JS module passes `node --check`, and its relative imports resolve.
const ORGANISMS = ["bacterium", "paramecium", "rotifer", "tardigrade", "nematode", "daphnia"];
const MODULES = [
  "main.js", "scene.js", "locomotion.js",
  "organisms/lib.js", "organisms/index.js",
  ...ORGANISMS.map((o) => `organisms/${o}.js`),
  "tests/smoke.mjs", "tests/life.mjs", "tests/locomotion.mjs",
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
  const src = read(rel);
  const dir = path.dirname(path.join(ROOT, rel));
  for (const m of src.matchAll(/from\s+["'](\.[^"']+)["']/g)) {
    const target = path.resolve(dir, m[1]);
    assert(fs.existsSync(target), `${rel}: import "${m[1]}" resolves to missing file`);
  }
}

// 4. The roster wires every organism, ordered by size.
const index = read("organisms/index.js");
for (const o of ORGANISMS) {
  assert(new RegExp(`from\\s+["']\\.\\/${o}\\.js["']`).test(index), `organisms/index.js does not import ${o}.js`);
}
assert(/export\s+const\s+ROSTER\s*=/.test(index), "organisms/index.js has no ROSTER export");
assert(/export\s+const\s+BY_ID\s*=/.test(index), "organisms/index.js has no BY_ID export");

// 5. Every organism module exports a contract-shaped meta.
for (const o of ORGANISMS) {
  const src = read(`organisms/${o}.js`);
  assert(/export\s+const\s+meta\s*=/.test(src), `${o}.js missing meta export`);
  for (const field of ["id", "name", "taxon", "kingdom", "micronLength", "blurb", "build"]) {
    assert(new RegExp(`\\b${field}\\b\\s*:`).test(src) || new RegExp(`\\b${field}\\b,`).test(src),
      `${o}.js meta missing field: ${field}`);
  }
  assert(/registerOrgan\s*\(/.test(src), `${o}.js registers no organs (no registerOrgan call)`);
  assert(/\blocomotion\b\s*:/.test(src), `${o}.js meta declares no locomotion gait`);
  assert(/userData\.anim\s*=/.test(src), `${o}.js never installs an anim on userData`);
  for (const m of ["setRunning", "getProgress", "update", "reset"]) {
    assert(new RegExp(`\\b${m}\\b`).test(src), `${o}.js anim missing ${m}`);
  }
}

// 6. lib.js exposes the shared anatomy grammar.
const lib = read("organisms/lib.js");
for (const fn of ["cuticle", "organ", "nucleus", "tubeBody", "ciliaRing", "ciliaCoat", "registerOrgan", "blob"]) {
  assert(new RegExp(`export\\s+function\\s+${fn}\\b`).test(lib), `lib.js does not export ${fn}`);
}

// 7. scene.js sets up the photoreal dark-field pillars.
const scene = read("scene.js");
assert(/ACESFilmicToneMapping/.test(scene), "scene.js does not use ACES tone-mapping");
assert(/RoomEnvironment/.test(scene), "scene.js does not set up image-based lighting");
assert(/UnrealBloomPass/.test(scene), "scene.js does not add bloom");
assert(/export\s+function\s+createScope/.test(scene), "scene.js does not export createScope");
assert(/FogExp2/.test(scene), "scene.js does not fog the medium (depth cue)");

// 8. main.js wires the zoom engine + roster + picking.
const main = read("main.js");
assert(/from\s+["']\.\/scene\.js["']/.test(main), "main.js does not import scene.js");
assert(/from\s+["']\.\/organisms\/index\.js["']/.test(main), "main.js does not import the roster");
assert(/from\s+["']\.\/locomotion\.js["']/.test(main) && /makeSwimmer\s*\(/.test(main),
  "main.js does not wire the locomotion swimmer");
assert(/Raycaster/.test(main), "main.js has no raycaster (click-to-focus picking)");
assert(/magAt\s*\(/.test(main) && /fieldMicrons\s*\(/.test(main), "main.js missing the magnification model");
assert(/focusInstance\b/.test(main) && /function\s+surface\b/.test(main), "main.js missing focus/surface (the dive)");
assert(/revealFrac/.test(main), "main.js does not gate organ labels on revealFrac");

// 9. The HUD elements main.js drives all exist in the page.
for (const id of [
  "stage", "magReadout", "scaleReadout", "scaleBar", "depthFill",
  "specimenName", "specimenTaxon", "specimenKingdom", "specimenBlurb", "organCount",
  "roster", "organLayer", "sampleId", "srStatus", "btnSample", "btnSurface", "btnPlay",
]) {
  assert(html.includes(`id="${id}"`), `index.html missing element #${id}`);
}

console.log(`\n${checks} checks passed, ${failures} failure(s).`);
process.exit(failures === 0 ? 0 : 1);
