// The Studio — structural smoke gate. Zero-dependency. The Studio is a static
// on-site hub (no build, no JS engine of its own), so this guards the things a
// hand-edited hub page silently breaks:
//   - the page parses and reuses the shared hub stylesheet,
//   - it links to every generative engine it claims to gather,
//   - it hosts NO external "Studio" artifact link (the whole point of moving it
//     on-site / to the Railway deployment), and neither does the web9 landing.
//
// Pure assertions; exits non-zero on the first hard failure so it gates CI.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const STUDIO = path.join(HERE, '..');           // docs/studio
const DOCS = path.join(STUDIO, '..');           // docs

let failures = 0, checks = 0;
const fail = (m) => { failures++; console.error(`  ✗ ${m}`); };
const ok = () => { checks++; };
const assert = (cond, m) => (cond ? ok() : fail(m));
const read = (p) => fs.readFileSync(p, 'utf8');
const exists = (p) => fs.existsSync(p);

console.log('Running The Studio smoke tests…\n');

// 1. the page exists and reuses the shared hub grammar.
const idx = path.join(STUDIO, 'index.html');
assert(exists(idx), 'docs/studio/index.html missing');
const html = read(idx);
assert(/<link[^>]+href="\.\.\/hub\.css"/.test(html), 'studio does not reuse ../hub.css');
assert(/The Studio/.test(html) && /<title>[^<]*Studio/.test(html), 'studio page has no Studio title/heading');

// 2. it links to every engine it gathers — and each target actually exists.
const ENGINES = ['web7', 'web9', 'web10', 'ontogeny', 'pondwater', 'slime', 'murmuration'];
for (const e of ENGINES) {
  assert(new RegExp(`href="\\.\\./${e}/"`).test(html), `studio does not link engine ../${e}/`);
  assert(exists(path.join(DOCS, e, 'index.html')), `linked engine ${e} has no index.html`);
}
// the gateway links back to the hub
assert(/href="\.\.\/index\.html"/.test(html), 'studio does not link back to the hub');

// 3. NO external artifact page anywhere — the Studio is on-site now.
assert(!/claude\.ai\/code\/artifact/.test(html), 'studio still points at an external claude.ai artifact');
const web9 = read(path.join(DOCS, 'web9', 'index.html'));
assert(!/claude\.ai\/code\/artifact/.test(web9), 'web9 landing still links the external Studio artifact');
assert(/href="\.\.\/studio\/"/.test(web9), 'web9 landing does not point its Studio links at the on-site ../studio/');

// 4. the whole docs tree is clean of the external artifact (defensive).
let stray = 0;
const walk = (dir) => {
  for (const name of fs.readdirSync(dir)) {
    const p = path.join(dir, name);
    const st = fs.statSync(p);
    if (st.isDirectory()) { if (name !== 'node_modules' && name !== 'generated' && name !== 'assets') walk(p); }
    else if (name.endsWith('.html') || name.endsWith('.js')) { if (/claude\.ai\/code\/artifact/.test(read(p))) { stray++; console.error(`      ↳ external artifact link in ${path.relative(DOCS, p)}`); } }
  }
};
walk(DOCS);
assert(stray === 0, `${stray} file(s) still link the external Studio artifact`);

console.log(`\n${checks} checks passed, ${failures} failure(s).`);
process.exit(failures === 0 ? 0 : 1);
