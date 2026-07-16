// smoke.mjs — the on-site Studio gate.
//
// The Studio is a single self-contained page (13 generative engines) wired to
// the shared client-side Pro unlock (pro.js / window.CatSilPro). This guards:
// the page parses, all engines are present, the export path exists, and the
// paywall is the SHARED token — not the old session-only "imaginary" unlock.
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

// ── 1. the thirteen engines ──────────────────────────────────────────────────
console.log('engines:');
const m = html.match(/const TOOLS\s*=\s*\[([\s\S]*?)\];/);
ok(!!m, 'TOOLS array present');
const toolCount = m ? (m[1].match(/\{name:'/g) || []).length : 0;
ok(toolCount === 13, `13 engines declared (got ${toolCount})`);
for (const kind of ['flow', 'rd', 'slime', 'boids', 'lenia', 'cymatics', 'dla', 'starling', 'fractal']) {
  ok(html.includes(`kind:'${kind}'`), `engine kind: ${kind}`);
}

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

// ── 3. real export + home link ───────────────────────────────────────────────
console.log('exports + shell:');
ok(html.includes('3840') && html.includes('MediaRecorder'), 'real 4K (3840) video export path present');
ok(html.includes('toBlob') || html.includes('toDataURL'), 'still-export path present');
ok(/class="home" href="\.\.\/"/.test(html), 'links back to the site (../)');

// ── 4. the app script parses ─────────────────────────────────────────────────
console.log('syntax:');
const blocks = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((x) => x[1]);
const app = blocks[blocks.length - 1] || '';
const tmp = join(tmpdir(), '_studio_app_check.js');
writeFileSync(tmp, app);
try { execFileSync('node', ['--check', tmp]); ok(true, 'inline app script parses'); }
catch (e) { ok(false, 'inline app script parses — ' + String(e.stderr || e).slice(0, 200)); }

console.log(fails ? `\nFAIL — ${fails} problem(s)` : '\nOK — Studio on-site, 13 engines, shared Pro unlock');
process.exit(fails ? 1 : 0);
