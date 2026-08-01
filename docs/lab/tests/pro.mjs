// lab · Pro gate (CatSilPro) — run with `node docs/lab/tests/pro.mjs`.
//
// The flagship speaks ONE Pro language: the shared, checksummed CatSilPro
// token (catsil.pro.token) that also unlocks studio/slime/the hub. This gate
// guards the monetization layer: pro.js is wired and byte-identical to the
// hub's copy, the Parameters rail + instrument export are the gated surfaces,
// the 4000² plate export pill survives, and web9's bespoke paywall stays
// retired. Behaviourally, a freshly-minted token must verify (FNV checksum).
// Zero-dependency; non-zero exit gates CI.

import fs from "node:fs";
import vm from "node:vm";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, "..");
let failures = 0, checks = 0;
const fail = (m) => { failures++; console.error(`  ✗ ${m}`); };
const ok = () => { checks++; };
const assert = (cond, m) => (cond ? ok() : fail(m));
const read = (rel) => fs.readFileSync(path.join(ROOT, rel), "utf8");
const exists = (rel) => fs.existsSync(path.join(ROOT, rel));

console.log("Running lab Pro gate (CatSilPro)…\n");

// 1. pro.js exists, parses, and is byte-identical to the hub root's copy.
assert(exists("pro.js"), "pro.js is missing");
if (exists("pro.js")) {
  try { execFileSync(process.execPath, ["--check", path.join(ROOT, "pro.js")], { stdio: "pipe" }); ok(); }
  catch (e) { fail(`syntax error in pro.js: ${String(e.stderr || e).slice(0, 160)}`); }
  assert(read("pro.js") === read("../pro.js"),
    "lab/pro.js has drifted from docs/pro.js — propagate to all copies");
}
const proJs = read("pro.js");
for (const api of ["isUnlocked", "showPaywall", "redeem", "grantDemo", "onChange"]) {
  assert(proJs.includes(api + ":") || proJs.includes(api + " :"), `pro.js does not expose CatSilPro.${api}`);
}
assert(proJs.includes("'catsil.pro.token'"), "pro.js does not use the shared token key");

// 2. index.html loads pro.js before main.js, and the bespoke paywall stays dead.
const html = read("index.html");
assert(/<script src="\.\/pro\.js"><\/script>[\s\S]*<script type="module" src="\.\/main\.js">/.test(html),
  "pro.js must load (classic) before the main module");
assert(!/paywall\.(js|css)/.test(html) && !/landing\.(js|css)/.test(html),
  "web9's bespoke paywall/landing must not return — Pro is CatSilPro only");
assert(!exists("paywall.js") && !exists("landing.js"), "stray paywall.js/landing.js on disk");

// 3. main.js gates the right surfaces through CatSilPro.
const main = read("main.js");
assert(/ensureParamLock/.test(main) && /\.param-lock/.test(main),
  "main.js must inject the Parameters-rail lock overlay");
assert(/reflectParamLock/.test(main) && /pw-locked/.test(main),
  "main.js must reflect lock state via #paramPanel.pw-locked");
assert(/CatSilPro\.onChange\(reflectParamLock\)/.test(main),
  "unlocking must live-update the rail (CatSilPro.onChange)");
assert(/proGate/.test(main) && /obsCsvBtn/.test(main) && /obsLinkBtn/.test(main),
  "instrument CSV/link export must pass through the Pro gate");
assert(/showPaywall\(\{\s*title:\s*PRO_TITLE/.test(main) && /Unlock the Instrument/.test(main),
  "the paywall must speak the flagship language ('Unlock the Instrument')");
assert(/exportProPlate/.test(main) && /CatSilPro\.isUnlocked\(\)/.test(main),
  "the 4000² plate export must remain CatSilPro-gated");

// 4. Behaviour: a freshly-minted token verifies (the FNV checksum is real).
try {
  const sandbox = { window: {}, document: undefined, localStorage: undefined };
  sandbox.window.addEventListener = () => {};
  vm.runInNewContext(proJs, sandbox);
  const P = sandbox.window.CatSilPro;
  assert(P && typeof P.verify === "function", "CatSilPro did not register in a bare sandbox");
  if (P) {
    const t = P.grantDemo();
    assert(typeof t === "string" && P.verify(t), `minted token does not verify: ${t}`);
    assert(!P.verify("CATSIL-AAAA-AAAA-ZZZZZZ"), "a wrong-checksum token must NOT verify");
  }
} catch (e) {
  fail(`pro.js did not run headlessly: ${String(e.message).slice(0, 160)}`);
}

console.log(`\n${checks} checks passed, ${failures} failure(s).`);
process.exit(failures === 0 ? 0 : 1);
