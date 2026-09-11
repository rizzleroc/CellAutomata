// smoke.mjs — the Automata Lab page gate (zero-dep). Proves the page is wired
// to the engine it ships: every element the controller binds exists, the
// classic scripts (SEM shader + the web7 stage rules, by reference) load
// before the module, the engine modules import cleanly, and the controller
// parses. Run: node docs/automata/tests/smoke.mjs
import { readFileSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const DIR = join(dirname(fileURLToPath(import.meta.url)), '..');
let pass = 0; const fails = [];
const ok = (c, m) => { if (c) pass++; else fails.push(m); };
const html = readFileSync(join(DIR, 'index.html'), 'utf8');
const app = readFileSync(join(DIR, 'app.js'), 'utf8');
const css = readFileSync(join(DIR, 'styles.css'), 'utf8');

console.log('Automata Lab — page smoke\n');

// page wiring
ok(/<script type="module" src="app\.js">/.test(html), 'index.html loads app.js as a module');
ok(/<script src="sem\.js">/.test(html) && existsSync(join(DIR, 'sem.js')), 'index.html loads the SEM shader (classic) and it exists');
ok(html.indexOf('src="sem.js"') < html.indexOf('src="app.js"'), 'sem.js precedes the module');
ok(/href="styles\.css"/.test(html), 'index.html loads styles.css');
ok(/href="\.\.\/index\.html"/.test(html), 'links back to the hub');
ok(/href="\.\.\/web7\/"/.test(html), 'links to the canonical lab');
ok(/cellular-automata laboratory/i.test(html), 'says what it is');

// every id the controller binds must exist
const ids = app.match(/for \(const id of \[([\s\S]*?)\]\) els\[id\]/);
ok(!!ids, 'controller declares its element list');
if (ids) for (const id of ids[1].match(/'([^']+)'/g).map((s) => s.slice(1, -1))) ok(new RegExp(`id="${id}"`).test(html), `markup has #${id}`);

// the four numbered steps + the specimen + instrument are all present, once
ok((html.match(/class="dh"/g) || []).length === 4, 'the desk has exactly four steps');
for (const t of ['Family', 'Rule', 'Lattice', 'Draw']) ok(new RegExp(`</span>${t}</h3>`).test(html), `step "${t}" present`);
ok(/class="views"/.test(html) && /id="cells"/.test(html) && /id="feed"/.test(html), 'lattice + micrograph views');
ok(/class="instrument"/.test(html) && /id="spark"/.test(html), 'instrument strip with sparkline');
ok(/class="transport"/.test(html), 'transport bar');

// the abiogenesis lab, by reference (never a copy)
const refs = [...html.matchAll(/<script src="\.\.\/web7\/experiment\/([^"]+)">/g)].map((m) => m[1]);
ok(refs.length === 14, `references viridis + 13 stage rules from web7 (${refs.length})`);
for (const r of refs) ok(existsSync(join(DIR, '..', 'web7', 'experiment', r)), `web7 file exists: ${r}`);
ok(refs.every((r) => html.indexOf(`experiment/${r}"`) < html.indexOf('src="app.js"')), 'stage rules load before the module');
ok(!existsSync(join(DIR, 'experiment')), 'no private copy of the stage rules (by-reference only)');

// engine modules import and expose the contract
const modules = ['engine/grid.js', 'engine/measure.js', 'engine/patterns.js', 'engine/rules/index.js', 'engine/rules/lifelike.js', 'engine/rules/ltl.js',
  'engine/rules/elementary.js', 'engine/rules/cyclic.js', 'engine/rules/wireworld.js', 'engine/rules/turmite.js', 'engine/rules/abiogenesis.js'];
for (const m of modules) ok(existsSync(join(DIR, m)), `module exists: ${m}`);
const reg = await import('../engine/rules/index.js');
ok(reg.FAMILIES.length === 7, 'seven families');
ok(reg.FAMILIES.map((f) => f.id).join() === 'lifelike,ltl,elementary,cyclic,wireworld,turmite,abiogenesis', 'family order is the desk order');
const pat = await import('../engine/patterns.js');
ok(pat.LIBRARY.length >= 15, 'pattern library present');

// controller parses + wires the pieces it promises
try { execFileSync(process.execPath, ['--check', join(DIR, 'app.js')], { stdio: 'pipe' }); pass++; } catch (e) { fails.push('app.js failed node --check'); }
for (const fn of ['buildFamilyTabs', 'buildPresets', 'buildParams', 'buildBrush', 'buildPatterns', 'setMode', 'applyRule', 'resetRun', 'stepOnce', 'measure', 'renderSEM', 'renderSpark', 'writeHash', 'readHash'])
  ok(new RegExp(`function ${fn}\\(`).test(app), `app.js defines ${fn}`);
ok(/SEM\.render\(/.test(app) && /S\.rule\.height/.test(app), 'micrograph: shared shader, stage renderHeight when available');
ok(/requestAnimationFrame\(frame\)/.test(app) && /S\.gps/.test(app), 'fixed-timestep loop');
ok(/pointerdown/.test(app) && /setPointerCapture/.test(app), 'pointer painting');
ok(/toCSV\(\)/.test(app) && /toRLE\(/.test(app) && /toBlob\(/.test(app), 'CSV, RLE and PNG exports');
ok(/Math\.min\(8, Math\.floor\(4000/.test(app), 'PNG plate is hard-bounded at 4000²');
ok(/history\.replaceState/.test(app) && /URLSearchParams/.test(app), 'run-link hash');
ok(/e\.key === ' '/.test(app), 'keyboard transport');
ok(/paintable\(\)/.test(app) && /drawStep\.hidden/.test(app), 'watch-and-tune mode hides the draw step');

// style: the Catalytic Silence grammar + responsiveness
ok(/Italiana/.test(css) && /IBM Plex Mono/.test(css) && /Crimson Pro/.test(css), 'self-hosted brand fonts');
ok(/\.\.\/web8\/assets\/fonts\//.test(css), 'fonts reused from web8');
ok(/@media \(max-width: 860px\)/.test(css) && /@media \(max-width: 1180px\)/.test(css), 'responsive breakpoints');
ok(/prefers-reduced-motion/.test(css), 'reduced-motion honoured');

if (fails.length) { console.error(`\n${fails.length} FAILURE(S):\n - ` + fails.join('\n - ')); process.exit(1); }
console.log(`${pass} checks passed, 0 failures`);
