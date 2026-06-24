// web9 "Pro Studio" smoke test (zero-dep): the module parses, the page exposes
// every element the controller drives, the Catalytic-Silence tokens are present,
// the web8 fonts are reused (no new binaries), and the studio talks to the Pro
// API surface. No browser, no network — pure static checks. Mirrors the gates
// in docs/ontogeny/tests/smoke.mjs.
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, '..');
const read = (f) => readFileSync(join(root, f), 'utf8');
let pass = 0; const fails = [];
const ok = (c, m) => { if (c) pass++; else fails.push(m); };

console.log('Running web9 Pro Studio smoke tests…\n');

// 1 · the module parses (syntax) ----------------------------------------------
try { execFileSync(process.execPath, ['--check', join(root, 'studio.js')], { stdio: 'pipe' }); ok(true); }
catch (e) { ok(false, `studio.js fails node --check: ${String(e.stderr || e.message).slice(0, 200)}`); }

// 2 · the page exposes what the controller drives -----------------------------
const html = read('index.html');
for (const id of ['stage', 'regime', 'knobs', 'seed', 'grid', 'steps', 'size', 'palette',
  'renderBtn', 'result', 'download', 'gate', 'studio', 'stagearea', 'signin', 'upgradeBtn',
  'gateTitle', 'gateBlurb', 'status', 'account']) {
  ok(new RegExp(`id="${id}"`).test(html), `index.html missing #${id}`);
}
ok(/type="module"\s+src="\.\/studio\.js"/.test(html), 'index.html must load studio.js as a module');
ok(/aria-live="polite"/.test(html), 'missing the polite live region');
ok(/class="skip-link"/.test(html), 'missing the skip-link');
ok(/LIVE · SEM/.test(html), 'the plate carries the LIVE · SEM badge');

// 3 · Catalytic-Silence design tokens + reused fonts --------------------------
const css = read('styles.css');
ok(/--teal:\s*#3fe0d0/.test(css) && /--magenta:\s*#d77bff/.test(css), 'palette tokens (teal + magenta) present');
ok(/@font-face/.test(css) && /Italiana/.test(css) && /IBM Plex Mono/.test(css), 'museum type pack declared');
ok(/\.\.\/web8\/assets\/fonts/.test(css), 'reuses web8 self-hosted fonts (no new binaries)');
ok(/prefers-reduced-motion/.test(css), 'reduced-motion path present');

// 4 · the controller talks to the Pro API surface -----------------------------
const js = read('studio.js');
for (const ep of ['/api/public-config', '/api/rules', '/api/me/entitlement', '/api/checkout', '/api/render']) {
  ok(js.includes(ep), `studio.js must call ${ep}`);
}
ok(/Authorization/.test(js) && /getToken/.test(js), 'studio.js attaches the Clerk bearer token');
ok(/image\/png|blob\(\)/.test(js), 'studio.js consumes the PNG render response');

if (fails.length) console.error('\n' + fails.map((f) => '  ✗ ' + f).join('\n'));
console.log(`\n${pass} checks passed, ${fails.length} failure(s).`);
process.exit(fails.length ? 1 : 0);
