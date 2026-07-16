// catalog.mjs — the free/paid manifest gate.
//
// Guards the single source of truth (catalog.js) against drift and against the
// front door: catalog.json must mirror catalog.js exactly, every tool must
// point at something real, and docs/index.html must link + tier-label every
// tool. If a client is added/retired or a tier flips, this fails until the
// manifest, the mirror, and the front door all agree.
//
//   node docs/tests/catalog.mjs

import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve, join } from 'node:path';

const DOCS = resolve(dirname(fileURLToPath(import.meta.url)), '..');
let fails = 0;
const ok = (c, m) => { if (!c) { console.error('  ✗ ' + m); fails++; } else console.log('  ✓ ' + m); };

const { CATALOG } = await import('../catalog.js');
const index = readFileSync(join(DOCS, 'index.html'), 'utf8');

// ── 1. shape ────────────────────────────────────────────────────────────────
console.log('shape:');
const catIds = new Set(CATALOG.categories.map((c) => c.id));
ok(CATALOG.tools.length >= 8, `${CATALOG.tools.length} tools declared`);
ok(CATALOG.tiers.some((t) => t.id === 'free') && CATALOG.tiers.some((t) => t.id === 'pro'), 'free + pro tiers present');
for (const t of CATALOG.tools) {
  const base = String(t.path).split('#')[0];
  ok(t.id && t.name && t.path && t.category, `${t.id}: has id/name/path/category`);
  ok(catIds.has(t.category), `${t.id}: category "${t.category}" is defined`);
  ok(t.access === 'free' || t.access === 'freemium', `${t.id}: access is free|freemium (${t.access})`);
  if (t.access === 'freemium') {
    ok(t.create === 'pro' && Array.isArray(t.pro) && t.pro.length > 0, `${t.id}: freemium ⇒ create:pro + pro[] listed`);
  } else {
    ok(t.create === 'free', `${t.id}: free ⇒ create:free`);
  }
  // path resolves to something real (unless external URL)
  const external = t.external || /^https?:/.test(t.path);
  if (!external) ok(existsSync(join(DOCS, base)), `${t.id}: path "${base}" exists on disk`);
}

// ── 2. mirror: catalog.json must equal catalog.js ────────────────────────────
console.log('mirror (catalog.json ↔ catalog.js):');
const json = JSON.parse(readFileSync(join(DOCS, 'catalog.json'), 'utf8'));
ok(JSON.stringify(json) === JSON.stringify(CATALOG),
  'catalog.json is byte-identical to catalog.js (regenerate if this fails)');

// ── 3. front door links + tier-labels every tool ─────────────────────────────
console.log('front door (index.html):');
for (const t of CATALOG.tools) {
  if (t.id === 'plates') { ok(/id="plates"/.test(index), 'plates: #plates section present'); continue; }
  if (t.id === 'reel')   { ok(index.includes(t.path), `reel: links ${t.path}`); continue; }
  ok(index.includes('"' + t.path + '"') || index.includes("'" + t.path + "'"), `${t.id}: links ${t.path}`);
  ok(index.includes(t.name), `${t.id}: names "${t.name}"`);
}
ok(/class="chip free"/.test(index), 'renders Free tier chips');
ok(/class="chip pro"/.test(index), 'renders Pro tier chips');
ok(/id="plans"/.test(index) && /Go Pro/.test(index), 'plans section + Go Pro unlock present');

// ── 4. token model agrees with pro.js + PRICING exists ───────────────────────
console.log('token model:');
const proJs = readFileSync(join(DOCS, 'pro.js'), 'utf8');
ok(proJs.includes("'" + CATALOG.tokenModel.key + "'"), `pro.js uses key ${CATALOG.tokenModel.key}`);
ok(existsSync(join(DOCS, 'PRICING.md')), 'PRICING.md exists');
const pricing = readFileSync(join(DOCS, 'PRICING.md'), 'utf8');
for (const t of CATALOG.tools.filter((x) => x.access === 'freemium')) {
  ok(pricing.includes(t.path), `PRICING.md documents ${t.id} (${t.path})`);
}

console.log(fails ? `\nFAIL — ${fails} problem(s)` : '\nOK — catalog, mirror, and front door agree');
process.exit(fails ? 1 : 0);
