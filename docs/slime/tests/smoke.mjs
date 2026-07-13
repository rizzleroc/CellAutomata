// docs/slime · Slime Studio — zero-dependency structural smoke gate.
// Proves the page parses, wires every control the sim drives, and keeps both
// renderings (the interactive path view + the live SEM feed) and the Physarum
// engine intact. Run: node docs/slime/tests/smoke.mjs
import { readFileSync } from 'node:fs';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const DIR = join(dirname(fileURLToPath(import.meta.url)), '..');
let pass = 0; const fails = [];
const ok = (cond, msg) => { if (cond) pass++; else fails.push(msg); };

const html = readFileSync(join(DIR, 'index.html'), 'utf8');
const js = readFileSync(join(DIR, 'slime.js'), 'utf8');

// page wiring
ok(/<script src="slime\.js">/.test(html), 'index.html loads slime.js');
ok(/href="styles\.css"/.test(html), 'index.html loads styles.css');
ok(/<canvas id="paths"/.test(html), 'has the interactive path canvas');
ok(/<canvas id="feed"/.test(html), 'has the live SEM feed canvas');
ok(/watch it grow the paths/i.test(html) || /grow paths/i.test(html), 'names the grow-paths behaviour');
ok(/href="\.\.\/index\.html"/.test(html), 'links back to the hub');

// every id the sim reads must exist in the markup
for (const id of ['paths', 'feed', 'play', 'reset', 'scatter', 'clearFood',
                  'speed', 'vSpeed', 'vigor', 'vVigor', 'colony', 'vColony', 'res', 'vRes',
                  'rNodes', 'rCover', 'rAgents', 'hint']) {
  ok(new RegExp(`id="${id}"`).test(html), `markup has #${id}`);
}

// slime.js must parse
try { execSync(`node --check "${join(DIR, 'slime.js')}"`); pass++; }
catch (e) { fails.push('slime.js failed node --check: ' + e.message); }

// the Physarum engine + both renderers are present
for (const fn of ['stampFood', 'function agents', 'function diffuse', 'function grow',
                  'renderPaths', 'renderSEM', 'function step', 'function setGrid']) {
  ok(js.includes(fn), `slime.js defines ${fn}`);
}
// higher-resolution / larger-colony controls are wired to the engine
ok(/getElementById\('res'\)|\$\('res'\)/.test(js) && /setGrid\(/.test(js), 'Detail control drives setGrid (adjustable grid resolution)');
ok(/getElementById\('colony'\)|\$\('colony'\)/.test(js) && /targetPop\s*=/.test(js), 'Colony control drives targetPop (larger agent sets)');
ok(/getElementById\('paths'\)/.test(js) && /getElementById\('feed'\)/.test(js), 'sim binds both canvases');
ok(/addNode/.test(js) && /pointerdown/.test(js), 'pointer places nutrients');
ok(/requestAnimationFrame/.test(js), 'runs an animation loop');

if (fails.length) { console.error(`slime smoke: ${fails.length} FAILURES\n - ` + fails.join('\n - ')); process.exit(1); }
console.log(`Slime Studio smoke: ${pass} checks passed, 0 failures`);
