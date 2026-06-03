// web7 design-contract tests — run with `node docs/web7/tests/design.mjs`.
//
// smoke.mjs guards the ENGINE contract (importmap, modules, STAGE_MAP, the live
// SEM pipeline). This file guards the "Catalytic Silence" DESIGN contract — the
// thing web7 exists to deliver — so a refactor can't quietly regress the
// world-class shell back toward the web6 brass/amber look or drop the
// accessibility scaffolding. Zero-dependency structural assertions; non-zero
// exit gates CI.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, "..");
let failures = 0, checks = 0;
const fail = (m) => { failures++; console.error(`  ✗ ${m}`); };
const ok = () => { checks++; };
const assert = (cond, m) => (cond ? ok() : fail(m));
const read = (rel) => fs.readFileSync(path.join(ROOT, rel), "utf8");
const exists = (rel) => fs.existsSync(path.join(ROOT, rel));

console.log("Running web7 design-contract tests…\n");

const html = read("index.html");
const css = read("styles.css");
const main = read("main.js");

// 1. Self-hosted laboratory typography — no runtime network dependency. -------
const FONTS = [
  "Italiana-Regular.ttf", "CrimsonPro-Regular.ttf", "CrimsonPro-Italic.ttf",
  "IBMPlexMono-Regular.ttf", "IBMPlexMono-Bold.ttf",
];
for (const f of FONTS) assert(exists(`assets/fonts/${f}`), `missing self-hosted font assets/fonts/${f}`);
for (const fam of ["Italiana", "Crimson Pro", "IBM Plex Mono"])
  assert(new RegExp(`@font-face[\\s\\S]*?font-family:\\s*"${fam}"`).test(css), `styles.css does not @font-face "${fam}"`);
assert(/font-display:\s*swap/.test(css), "fonts should declare font-display: swap");

// 2. The Catalytic Silence palette — obsidian ground, luminous teal, bone ink. -
assert(/--obsidian:\s*#0[0-9a-f]{5}/i.test(css), "missing obsidian ground token");
assert(/--teal:\s*#3fe0d0/i.test(css), "missing the luminous teal token (#3fe0d0)");
assert(/--ink:\s*#ece7da/i.test(css), "missing the bone-white ink token (#ece7da)");
assert(/--magenta:/i.test(css), "missing the magenta counterpoint token");
// the web6 brass/amber identity must be GONE — this is the whole point of web7
assert(!/#caa86a/i.test(css), "web6 brass accent (#caa86a) is still present — web7 must drop it");
assert(!/--accent:\s*#caa86a/i.test(css), "web6 --accent brass variable leaked into web7");

// 3. Museum-vitrine landmarks + semantics. ------------------------------------
assert(/class="vitrine"/.test(html), "missing .vitrine root");
assert(/<header class="register"/.test(html), "missing the top register (museum header)");
assert(/<nav class="index"/.test(html), "missing the stage index (nav)");
assert(/<main class="specimen"/.test(html), "missing the specimen main");
assert(/<aside class="key"/.test(html), "missing the specimen key (aside)");
assert(/class="brand-word"/.test(html) && /Italiana/.test(css), "missing the didone titular gesture");

// 4. The SEM scientific-plate framing (matches the goal mockup). --------------
assert(/class="plate"/.test(html), "missing the SEM plate frame");
assert(/plate-badge/.test(html) && /LIVE\s*·\s*SEM/.test(html), "missing the LIVE · SEM plate badge");
assert(/plate-scale/.test(html), "missing the scale bar");
assert(/id="expEmpty"/.test(html) && /specimen pending/.test(html), "missing the tasteful empty/pending state");

// 5. Accessibility scaffolding (the AAA bar). ---------------------------------
assert(/class="skip-link"/.test(html), "missing skip-link");
// attribute-order-agnostic: one <div> carrying both id="srStatus" and aria-live="polite"
assert(/<div\b(?=[^>]*\bid="srStatus")(?=[^>]*\baria-live="polite")[^>]*>/.test(html),
  "missing the polite screen-reader live region");
assert(/role="radiogroup"/.test(html), "view toggle should be a radiogroup");
assert(/aria-checked=/.test(html), "view toggle radios need aria-checked");
assert(/id="runBtn"[^>]*aria-pressed=/.test(html) || /aria-pressed=/.test(html), "run control needs aria-pressed");
assert(/:focus-visible\s*\{/.test(css), "missing a visible focus style");
assert(/@media\s*\(prefers-reduced-motion:\s*reduce\)/.test(css), "missing prefers-reduced-motion handling");
assert(/sr-only/.test(css), "missing .sr-only utility");

// 6. The controller wires the presentation layer. ----------------------------
assert(/is-running/.test(main) && /is-running/.test(css), "running 'breath' state not wired");
assert(/aria-current/.test(main), "active stage not exposed via aria-current");
assert(/function toRoman/.test(main), "Roman-numeral plate numbering missing");
assert(/srStatus|announce\(/.test(main), "no screen-reader announcements");
assert(/ArrowDown/.test(main), "stage index lacks keyboard navigation");
assert(/prefers-reduced-motion/.test(main), "controller ignores reduced-motion preference");

// 7. Responsive — the vitrine must adapt. -------------------------------------
assert(/@media\s*\(max-width:\s*\d+px\)/.test(css), "no responsive breakpoints");

// 8. Resilience & interaction polish. -----------------------------------------
assert(/es-module-shims/.test(html), "missing the import-map polyfill (Safari 16.0–16.3 / older Firefox)");
assert(/<noscript>/.test(html), "missing the <noscript> fallback");
assert(/__labReady/.test(html) && /__labReady/.test(main), "missing the offline failsafe handshake");
assert(/function hasWebGL/.test(main), "no WebGL capability probe");
assert(/instrument offline/.test(html) || /instrument offline/.test(main), "no graceful engine-failure notice");
assert(/id="stageSelect"/.test(html) && /stageSelect/.test(main), "missing the mobile stage switcher");
assert(/cursor:\s*grab/.test(css), "the 3D viewport lacks a grab affordance");
assert(/viewport-hint/.test(html) && /viewport-hint/.test(css), "missing the drag-to-rotate hint");
assert(/THREE\.Spherical/.test(main), "no keyboard orbit for the apparatus");
assert(/font-display:\s*optional/.test(css), "the didone display face should be font-display: optional");

console.log(`\n${checks} checks passed, ${failures} failure(s).`);
process.exit(failures === 0 ? 0 : 1);
