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
const MODULES = ["scene.js", "main.js", "apparatus/miller_urey.js", "apparatus/placeholder.js", "tests/smoke.mjs"];
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

// 4. main.js wires the full pipeline registry + the hero apparatus import.
const main = read("main.js");
assert(/from\s+["']\.\/apparatus\/miller_urey\.js["']/.test(main),
  "main.js does not import the Miller–Urey apparatus");
assert(/buildPlaceholder/.test(main), "main.js does not use buildPlaceholder for pending stages");
const phCount = (main.match(/ph\(/g) || []).length;
// 13-stage pipeline = 1 hero (miller-urey) + 12 placeholder entries (stages 1–11 + capstone)
assert(phCount >= 12, `expected ≥12 placeholder stage entries, found ${phCount}`);

// 5. apparatus modules export what main.js expects.
const mu = read("apparatus/miller_urey.js");
assert(/export\s+function\s+buildMillerUrey/.test(mu), "miller_urey.js missing buildMillerUrey export");
assert(/export\s+const\s+meta/.test(mu), "miller_urey.js missing meta export");
assert(/anim\.update\s*=/.test(mu), "miller_urey.js apparatus has no anim.update");
assert(/anim\.setRunning\s*=/.test(mu), "miller_urey.js apparatus has no anim.setRunning");
const ph = read("apparatus/placeholder.js");
assert(/export\s+function\s+buildPlaceholder/.test(ph), "placeholder.js missing buildPlaceholder export");

// 6. scene.js sets up the photoreal pillars (PBR env + ACES + bloom).
const scene = read("scene.js");
assert(/ACESFilmicToneMapping/.test(scene), "scene.js does not use ACES tone-mapping");
assert(/RoomEnvironment/.test(scene), "scene.js does not set up image-based lighting");
assert(/UnrealBloomPass/.test(scene), "scene.js does not add bloom (spark glow)");

console.log(`\n${checks} checks passed, ${failures} failure(s).`);
process.exit(failures === 0 ? 0 : 1);
