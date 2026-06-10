// Ontogeny page smoke test (zero-dep): every module parses, the page exposes the
// elements the controller drives, the Catalytic-Silence tokens are present, and
// the engine is wired in. No browser needed.
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, '..');
const read = (f) => readFileSync(join(root, f), 'utf8');
let pass = 0; const fails = [];
const ok = (c, m) => { if (c) pass++; else fails.push(m); };

console.log('Running ontogeny smoke tests…\n');

// 1 · every module parses (syntax) --------------------------------------------
for (const f of ['sim.js', 'render.js', 'app.js']) {
  try { execFileSync(process.execPath, ['--check', join(root, f)], { stdio: 'pipe' }); ok(true); }
  catch (e) { ok(false, `${f} fails node --check: ${String(e.stderr || e.message).slice(0, 200)}`); }
}

// 2 · the page exposes what the controller drives ------------------------------
const html = read('index.html');
for (const id of ['stage', 'membranes', 'presetList', 'paramList', 'playBtn', 'stepBtn',
  'resetBtn', 'scrub', 'reseedBtn', 'verdictCount', 'verdictLabel', 'verdictZyg',
  'statEggs', 'statPlacentas', 'statSacs', 'statChromo', 'flags', 'capTitle', 'capBlurb', 'metaDay', 'srStatus']) {
  ok(new RegExp(`id="${id}"`).test(html), `index.html missing #${id}`);
}
ok(/type="module"\s+src="\.\/app\.js"/.test(html), 'index.html must load app.js as a module');
ok(/aria-live="polite"/.test(html), 'missing the polite live region');
ok(/class="skip-link"/.test(html), 'missing the skip-link');
ok(/<canvas[^>]*id="stage"/.test(html) && /<canvas[^>]*id="membranes"/.test(html), 'both canvases present');

// 3 · Catalytic-Silence design tokens -----------------------------------------
const css = read('styles.css');
ok(/--teal:\s*#3fe0d0/.test(css) && /--magenta:\s*#d77bff/.test(css), 'palette tokens (teal + magenta) present');
ok(/@font-face/.test(css) && /Italiana/.test(css) && /IBM Plex Mono/.test(css), 'museum type pack declared');
ok(/web8\/assets\/fonts/.test(css), 'reuses web8 self-hosted fonts (no new binaries)');
ok(/prefers-reduced-motion/.test(css), 'reduced-motion path present');

// 4 · engine wired into the page ----------------------------------------------
const app = read('app.js');
ok(/from '\.\/sim\.js'/.test(app) && /from '\.\/render\.js'/.test(app), 'app.js imports the engine + renderer');

// 5 · engine import + a sanity conception -------------------------------------
const sim = await import('../sim.js');
ok(typeof sim.conceive === 'function', 'sim.js exports conceive()');
ok(Array.isArray(sim.PRESETS) && sim.PRESETS.length >= 12, `sim.js ships the conditions (${sim.PRESETS?.length})`);
const r = sim.conceive(sim.getPreset('mz-mcda').params, 1);
ok(r.n === 2 && r.choType === 'MCDA', 'engine yields MCDA identical twins for the flagship preset');
const render = await import('../render.js');
ok(typeof render.drawSpecimen === 'function' && typeof render.drawMembranes === 'function', 'render.js exports the draw fns');

if (fails.length) console.error('\n' + fails.map((f) => '  ✗ ' + f).join('\n'));
console.log(`\n${pass} checks passed, ${fails.length} failure(s).`);
process.exit(fails.length ? 1 : 0);
