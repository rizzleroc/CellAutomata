// Murmuration — structural smoke gate. Zero-dependency (no WebGL in node), so
// it can't render; instead it catches the regressions a static WebGL/ES-module
// bundle would otherwise ship unnoticed:
//   - a broken importmap (the page can't resolve `three`),
//   - a renamed/missing module an import still points at,
//   - a syntax error in any module (node --check),
//   - the parameter schema or the regime set drifting out of shape,
//   - the HUD/control elements main.js drives going missing.
//
// Pure assertions; exits non-zero on the first hard failure so it gates CI.

import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, '..');

let failures = 0, checks = 0;
const fail = (m) => { failures++; console.error(`  ✗ ${m}`); };
const ok = () => { checks++; };
const assert = (cond, m) => (cond ? ok() : fail(m));
const read = (rel) => fs.readFileSync(path.join(ROOT, rel), 'utf8');
const exists = (rel) => fs.existsSync(path.join(ROOT, rel));

console.log('Running Murmuration smoke tests…\n');

// 1. index.html: importmap is valid JSON and maps `three` + addons to a CDN.
const html = read('index.html');
const mapMatch = html.match(/<script type="importmap">([\s\S]*?)<\/script>/);
assert(!!mapMatch, 'index.html has no importmap');
if (mapMatch) {
  let map;
  try { map = JSON.parse(mapMatch[1]); ok(); } catch (e) { fail(`importmap not valid JSON: ${e.message}`); }
  if (map) {
    assert(/three/.test(map.imports?.three || ''), 'importmap does not map bare specifier `three`');
    assert(typeof map.imports?.['three/addons/'] === 'string', 'importmap does not map `three/addons/`');
  }
}

// 2. index.html references files that exist + loads main.js as a module.
for (const rel of ['styles.css', 'main.js']) {
  assert(html.includes(rel), `index.html does not reference ${rel}`);
  assert(exists(rel), `referenced file missing: ${rel}`);
}
assert(/<script\s+type="module"\s+src="\.\/main\.js"/.test(html), 'index.html does not load main.js as a module');

// 3. Every JS module passes `node --check`, and its relative imports resolve.
const MODULES = ['main.js', 'scene.js', 'flock.js', 'bird.js', 'presets.js', 'tests/smoke.mjs', 'tests/flock.mjs', 'tests/life.mjs'];
for (const rel of MODULES) {
  assert(exists(rel), `module missing: ${rel}`);
  if (!exists(rel)) continue;
  try {
    execFileSync(process.execPath, ['--check', path.join(ROOT, rel)], { stdio: 'pipe' });
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

// 4. flock.js exposes the model contract (import it — it's framework-free).
const { PARAMS, defaultParams, Flock, mulberry32 } =
  await import(pathToFileURL(path.join(ROOT, 'flock.js')).href);
assert(Array.isArray(PARAMS) && PARAMS.length >= 15, 'flock.js PARAMS missing or too small');
assert(typeof defaultParams === 'function', 'flock.js does not export defaultParams');
assert(typeof Flock === 'function', 'flock.js does not export the Flock class');
assert(typeof mulberry32 === 'function', 'flock.js does not export mulberry32');
// the full real knob set + regime picker (cf. micrograph control-parity, #65)
const need = ['birds', 'viewRadius', 'fov', 'neighbors', 'separation', 'alignment',
  'cohesion', 'sepRadius', 'boundary', 'wind', 'cruiseSpeed', 'maxSpeed', 'minSpeed',
  'maxBank', 'agility', 'liftComp', 'power', 'predator', 'fear', 'fearRadius'];
const keys = new Set(PARAMS.map((p) => p.key));
for (const k of need) assert(keys.has(k), `PARAMS missing knob: ${k}`);
for (const p of PARAMS) {
  assert(typeof p.label === 'string' && p.group, `PARAM ${p.key} missing label/group`);
  assert(p.max > p.min && p.value >= p.min && p.value <= p.max, `PARAM ${p.key} has a bad range/default`);
}

// 5. presets.js: a real regime picker with well-shaped entries.
const { PRESETS, PRESET_BY_ID } = await import(pathToFileURL(path.join(ROOT, 'presets.js')).href);
assert(Array.isArray(PRESETS) && PRESETS.length >= 5, 'presets.js has fewer than 5 regimes');
for (const p of PRESETS) {
  for (const f of ['id', 'name', 'blurb', 'params']) assert(p[f] !== undefined, `preset ${p.id} missing ${f}`);
  assert(p.blurb.length > 12, `preset ${p.id} blurb too thin`);
  for (const k of Object.keys(p.params)) assert(keys.has(k), `preset ${p.id} sets unknown param ${k}`);
  assert(PRESET_BY_ID[p.id] === p, `PRESET_BY_ID missing ${p.id}`);
}
assert(PRESETS.some((p) => p.params.predator), 'no regime exercises the predator');
assert(PRESETS.some((p) => p.params.wind), 'no regime exercises wind');

// 6. bird.js exports the render contract.
const bird = read('bird.js');
for (const fn of ['makeFlock', 'makePredator', 'orient', 'makeScratch']) {
  assert(new RegExp(`export\\s+function\\s+${fn}\\b`).test(bird), `bird.js does not export ${fn}`);
}
assert(/InstancedMesh/.test(bird), 'bird.js does not use an InstancedMesh (won\'t scale to a murmuration)');
assert(/onBeforeCompile/.test(bird), 'bird.js has no shader wingbeat (onBeforeCompile)');

// 7. scene.js sets up the photoreal dusk-sky pillars.
const scene = read('scene.js');
assert(/ACESFilmicToneMapping/.test(scene), 'scene.js does not use ACES tone-mapping');
assert(/RoomEnvironment/.test(scene), 'scene.js does not set up image-based lighting');
assert(/UnrealBloomPass/.test(scene), 'scene.js does not add bloom');
assert(/FogExp2/.test(scene), 'scene.js does not fog the sky (aerial perspective)');
assert(/export\s+function\s+createScope/.test(scene), 'scene.js does not export createScope');

// 8. main.js wires the engine, meshes, camera modes and the shareable URL.
const main = read('main.js');
assert(/from\s+["']\.\/scene\.js["']/.test(main), 'main.js does not import scene.js');
assert(/from\s+["']\.\/flock\.js["']/.test(main), 'main.js does not import flock.js');
assert(/from\s+["']\.\/presets\.js["']/.test(main), 'main.js does not import presets.js');
assert(/from\s+["']\.\/bird\.js["']/.test(main), 'main.js does not import bird.js');
assert(/setMatrixAt/.test(main), 'main.js never writes instance matrices from the flock');
assert(/orbit/.test(main) && /follow/.test(main), 'main.js missing the camera modes');
assert(/writeHash\s*\(/.test(main) && /readHash\s*\(/.test(main), 'main.js missing the shareable-URL hash');

// 9. Every HUD / control element main.js drives exists in the page.
for (const id of [
  'stage', 'srStatus', 'regimeName', 'regimeChips', 'regimeBlurb',
  'polReadout', 'polSpark', 'telCount', 'telSpeed', 'telNN', 'telBank', 'telStalls',
  'controls', 'btnPlay', 'btnReset', 'btnCamera', 'btnShare', 'btnPanel', 'keyScrim',
]) {
  assert(html.includes(`id="${id}"`), `index.html missing element #${id}`);
}

console.log(`\n${checks} checks passed, ${failures} failure(s).`);
process.exit(failures === 0 ? 0 : 1);
