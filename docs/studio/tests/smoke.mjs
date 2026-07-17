// smoke.mjs — the on-site Studio gate.
//
// The Studio is one page + two classic scripts: engines.js (the 13 engines,
// window.StudioEngines) and pro.js (the shared client-side Pro unlock,
// window.CatSilPro). This guards: both scripts and the page parse, all
// engines are present, the export path exists, and the paywall is the SHARED
// token — not the old session-only "imaginary" unlock.
//
//   node docs/studio/tests/smoke.mjs

import { readFileSync, existsSync, writeFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, resolve, join } from 'node:path';
import { tmpdir } from 'node:os';

const DIR = resolve(dirname(fileURLToPath(import.meta.url)), '..');
let fails = 0;
const ok = (c, m) => { if (!c) { console.error('  ✗ ' + m); fails++; } else console.log('  ✓ ' + m); };

const html = readFileSync(join(DIR, 'index.html'), 'utf8');
const engines = readFileSync(join(DIR, 'engines.js'), 'utf8');

// ── 1. the thirteen engines (now in engines.js) ─────────────────────────────
console.log('engines:');
const m = engines.match(/const TOOLS\s*=\s*\[([\s\S]*?)\];/);
ok(!!m, 'TOOLS array present in engines.js');
const toolCount = m ? (m[1].match(/\{name:'/g) || []).length : 0;
ok(toolCount === 13, `13 engines declared (got ${toolCount})`);
for (const kind of ['flow', 'rd', 'slime', 'boids', 'lenia', 'cymatics', 'dla', 'starling', 'fractal']) {
  ok(engines.includes(`kind:'${kind}'`), `engine kind: ${kind}`);
}
ok(engines.includes('window.StudioEngines'), 'engines.js registers window.StudioEngines');
ok(/<script src="engines\.js"><\/script>[\s\S]*<script src="pro\.js"><\/script>/.test(html),
   'index.html loads engines.js before pro.js and the app');
ok(html.includes('window.StudioEngines'), 'app consumes window.StudioEngines');

// ── 2. shared Pro unlock (not the old imaginary one) ─────────────────────────
console.log('pro wiring:');
ok(existsSync(join(DIR, 'pro.js')), 'pro.js copy present');
ok(/<script src="pro\.js"><\/script>/.test(html), 'pro.js loaded before the app');
ok(html.includes('window.CatSilPro'), 'app reads window.CatSilPro');
ok(html.includes('CatSilPro.showPaywall'), 'unlock routes to the shared paywall');
ok(html.includes('onChange(refreshPlan)'), 'refreshes plan on unlock/clear');
ok(!/allUnlocked/.test(html) && !/imaginary/.test(html), 'old session-only "imaginary" unlock removed');
const proJs = readFileSync(join(DIR, 'pro.js'), 'utf8');
for (const api of ['isUnlocked', 'showPaywall', 'redeem', 'grantDemo', 'onChange']) {
  ok(proJs.includes(api + ':') || proJs.includes(api + ' :'), `pro.js exposes CatSilPro.${api}`);
}
ok(proJs.includes("'catsil.pro.token'"), 'pro.js uses the shared token key');
// The four pro.js copies (hub root, web10, slime, studio) must stay byte-identical —
// a fix in one that misses the others is exactly the drift CLAUDE.md warns about.
for (const other of ['../pro.js', '../lab/pro.js', '../slime/pro.js']) {
  ok(readFileSync(resolve(DIR, other), 'utf8') === proJs, `pro.js byte-identical to ${other.replace('../', 'docs/')}`);
}
ok(/showPaywall\(\{\s*title:/.test(html), 'paywall opened with Studio-voiced title');
ok(!html.includes('\\U0001f3b2') && !engines.includes('\\U0001f3b2'), 'no broken \\U escape regression');

// ── 3. real export + home link ───────────────────────────────────────────────
console.log('exports + shell:');
ok(html.includes('3840') && html.includes('MediaRecorder'), 'real 4K (3840) video export path present');
ok(html.includes('toBlob') || html.includes('toDataURL'), 'still-export path present');
ok(/class="home" href="\.\.\/"/.test(html), 'links back to the site (../)');
ok(html.includes("'v=2'"), 'share links carry the v=2 stable-key scheme');
ok(html.includes('devicePixelRatio'), 'HiDPI (devicePixelRatio) canvases');
ok(html.includes('prepareExport') && html.includes('warmPlan'), 'export fidelity pipeline present');

// ── 4. both scripts parse ────────────────────────────────────────────────────
console.log('syntax:');
try { execFileSync('node', ['--check', join(DIR, 'engines.js')]); ok(true, 'engines.js parses'); }
catch (e) { ok(false, 'engines.js parses — ' + String(e.stderr || e).slice(0, 200)); }
const blocks = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((x) => x[1]);
const app = blocks[blocks.length - 1] || '';
const tmp = join(tmpdir(), '_studio_app_check.js');
writeFileSync(tmp, app);
try { execFileSync('node', ['--check', tmp]); ok(true, 'inline app script parses'); }
catch (e) { ok(false, 'inline app script parses — ' + String(e.stderr || e).slice(0, 200)); }

console.log(fails ? `\nFAIL — ${fails} problem(s)` : '\nOK — Studio on-site, 13 engines, shared Pro unlock');
process.exit(fails ? 1 : 0);
