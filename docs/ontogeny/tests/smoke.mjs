// Ontogeny page smoke test (zero-dep): every module parses, the page exposes the
// elements the controller drives, the Catalytic-Silence tokens are present, and
// the engine is wired in. No browser needed.
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

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
ok(typeof render.buildHeight === 'function', 'render.js exports buildHeight (the SEM height field)');

// 6 · SEM pipeline — the SAME depth-shading engine the other labs use ----------
ok(/src="\.\/sem\.js"/.test(html), 'index.html loads sem.js (the SEM engine) as a classic script');
ok(/LIVE · SEM/.test(html), 'the plate carries the LIVE · SEM badge');
{
  const win = { Math, Date, console }; win.window = win;
  vm.createContext(win);
  vm.runInContext(readFileSync(join(root, 'sem.js'), 'utf8'), win, { filename: 'sem.js' });
  const SEM = win.window.SEM;
  ok(SEM && typeof SEM.render === 'function', 'sem.js wires window.SEM.render');
  ok(SEM && SEM.paletteNames && SEM.paletteNames().includes('warm-sepia'), 'SEM ships the warm-sepia palette');
  const o = sim.conceive(sim.getPreset('quints').params, 1);
  const G = 72, hbuf = new Float32Array(G * G);
  render.buildHeight(hbuf, G, { outcome: o, day: 3, time: 0 });
  let hmax = 0; for (const v of hbuf) if (v > hmax) hmax = v;
  ok(hmax > 0.4, `buildHeight raises real relief (peak ${hmax.toFixed(2)})`);
  const px = new Uint8ClampedArray(G * G * 4);
  SEM.render(hbuf, G, G, px, { palette: 'warm-sepia' });
  let lit = 0, opaque = true;
  for (let i = 0; i < G * G; i++) { if (px[i * 4] > 40 || px[i * 4 + 1] > 40) lit++; if (px[i * 4 + 3] !== 255) opaque = false; }
  ok(lit > G * G * 0.05, `SEM micrograph is non-blank (${lit} lit px)`);
  ok(opaque, 'SEM micrograph is fully opaque');
}

if (fails.length) console.error('\n' + fails.map((f) => '  ✗ ' + f).join('\n'));
console.log(`\n${pass} checks passed, ${fails.length} failure(s).`);
process.exit(fails.length ? 1 : 0);
