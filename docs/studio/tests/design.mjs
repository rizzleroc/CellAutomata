// design.mjs — the Studio's Catalytic Silence design contract.
//
// The AAA pass moved the Studio onto the house system: Italiana / Crimson Pro /
// IBM Plex Mono (shared from web8), obsidian ground, teal spent on interaction,
// magenta spent only as events, dark-only, HiDPI, reduced-motion, and the
// honest-export UI (REC HUD + fidelity note). This gate stops a refactor from
// quietly regressing any of it — including back to the old violet/gold shell.
//
//   node docs/studio/tests/design.mjs

import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve, join } from 'node:path';

const DIR = resolve(dirname(fileURLToPath(import.meta.url)), '..');
let fails = 0;
const ok = (c, m) => { if (!c) { console.error('  ✗ ' + m); fails++; } else console.log('  ✓ ' + m); };

const html = readFileSync(join(DIR, 'index.html'), 'utf8');

// ── 1. shared self-hosted fonts (web8 is the canonical font home) ───────────
console.log('fonts:');
for (const f of ['Italiana-Regular.ttf', 'CrimsonPro-Regular.ttf', 'CrimsonPro-Italic.ttf',
                 'IBMPlexMono-Regular.ttf', 'IBMPlexMono-Bold.ttf']) {
  ok(existsSync(resolve(DIR, '../assets/fonts', f)), `font file exists: ${f}`);
  ok(html.includes(`../assets/fonts/${f}`), `@font-face points at ${f}`);
}
for (const fam of ['Italiana', 'Crimson Pro', 'IBM Plex Mono']) {
  ok(html.includes(`font-family:'${fam}'`), `@font-face declares ${fam}`);
}
ok(html.includes('font-display:swap') && html.includes('font-display:optional'),
   'font-display strategy (optional display face, swap for the rest)');

// ── 2. the Catalytic Silence palette — and the old shell stays dead ─────────
console.log('palette:');
for (const [name, tok] of [['obsidian ground', '--obsidian:#07090d'], ['ink', '--ink:#ece7da'],
                           ['teal', '--teal:#3fe0d0'], ['magenta', '--magenta:#d77bff']]) {
  ok(html.includes(tok), `token present: ${name} (${tok})`);
}
ok(!html.includes('#7c6cf5') && !/#f4c74b/i.test(html), 'old violet/gold accents eradicated');
ok(!html.includes('prefers-color-scheme:light') && !html.includes('data-theme'),
   'dark-only — no orphaned light theme');
ok(html.includes('color-scheme" content="dark"'), 'color-scheme meta declares dark');

// ── 3. document shell (the page used to parse in quirks mode) ────────────────
console.log('shell:');
ok(/^<!doctype html>/i.test(html), 'doctype present (no quirks mode)');
ok(html.includes('<html lang='), 'html[lang]');
ok(html.includes('charset="utf-8"'), 'charset meta');
ok(html.includes('name="viewport"'), 'viewport meta');
ok(html.includes('class="build"') && html.includes('MK I'), 'build tag (MK I) in the register bar');
ok(html.includes('brand-mark'), 'breathing brand mark');

// ── 4. accessibility + honest-export UI ─────────────────────────────────────
console.log('a11y + export UI:');
ok(html.includes(':focus-visible'), ':focus-visible affordance');
ok(html.includes('prefers-reduced-motion'), 'prefers-reduced-motion escape');
ok(html.includes('aria-live="polite"'), 'toast is aria-live');
ok(html.includes('role="dialog"') && html.includes('aria-modal'), 'desk modal is a dialog');
ok(html.includes('aria-pressed'), 'filter chips / segments carry aria-pressed');
ok(html.includes('Watching is free. Pro opens this desk'), 'paylock copy (watch free · create Pro)');
ok(html.includes('rechud') && html.includes('Stop'), 'REC HUD with Stop & save');
ok(html.includes('fidNote'), 'per-engine export fidelity note');

console.log(fails ? `\nFAIL — ${fails} problem(s)` : '\nOK — Studio speaks Catalytic Silence');
process.exit(fails ? 1 : 0);
