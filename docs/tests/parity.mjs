// parity.mjs — the shared-file byte-drift gate.
//
// The convention here is "each client owns its copy" of shared helpers — which
// is exactly how web7's sem.js silently fell a generation behind its siblings
// (issue #68). This gate ends that: the copies that are SUPPOSED to be
// identical now fail CI the moment they drift.
//
//   node docs/tests/parity.mjs
//
// Scope (the live copies after the lab consolidation):
//   sem.js — lab/experiment/ + ontogeny/ (pondwater/slime ship no sem.js)
//   pro.js — hub root + lab/ + slime/ + studio/ (one Pro token site-wide)

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const DOCS = resolve(dirname(fileURLToPath(import.meta.url)), '..');
let fails = 0;
const ok = (c, m) => { if (!c) { console.error('  ✗ ' + m); fails++; } else console.log('  ✓ ' + m); };
const bytes = (p) => readFileSync(resolve(DOCS, p));
const same = (a, b) => Buffer.compare(bytes(a), bytes(b)) === 0;

console.log('sem.js (the SEM depth-shading pipeline):');
ok(same('lab/experiment/sem.js', 'ontogeny/sem.js'),
   'byte-identical: docs/lab/experiment/sem.js ↔ docs/ontogeny/sem.js');

console.log('pro.js (the shared CatSilPro unlock):');
for (const p of ['lab/pro.js', 'slime/pro.js', 'studio/pro.js']) {
  ok(same('pro.js', p), `byte-identical: docs/${p} ↔ docs/pro.js`);
}

console.log(fails ? `\nFAIL — ${fails} drifted cop${fails === 1 ? 'y' : 'ies'}` : '\nOK — no drift in the shared copies');
process.exit(fails ? 1 : 0);
