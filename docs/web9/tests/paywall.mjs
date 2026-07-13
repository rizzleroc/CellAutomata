// web9 · Pro paywall gate — run with `node docs/web9/tests/paywall.mjs`.
//
// Guards the monetization layer: the landing "Go Pro" link is present, the
// paywall module + styles are wired, the Parameters rail is the gated surface,
// and — behaviourally — a real access token unlocks (case/space-insensitive).
// Zero-dependency; non-zero exit gates CI. Additive to the existing web9 gates.

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

console.log("Running web9 Pro paywall gate…\n");

// 1. Files exist and the module parses.
assert(exists("paywall.js"), "paywall.js is missing");
assert(exists("paywall.css"), "paywall.css is missing");
if (exists("paywall.js")) {
  try { execFileSync(process.execPath, ["--check", path.join(ROOT, "paywall.js")], { stdio: "pipe" }); ok(); }
  catch (e) { fail(`syntax error in paywall.js: ${String(e.stderr || e).slice(0, 160)}`); }
}

// 2. index.html surfaces the paid link on the home page and loads the layer.
const html = read("index.html");
assert(/href="\.\/paywall\.css"/.test(html), "index.html does not load paywall.css");
assert(/src="\.\/paywall\.js"/.test(html), "index.html does not load paywall.js");
assert(/id="proBtn"/.test(html), "index.html landing is missing the Go Pro button (#proBtn)");
// the Go Pro button lives in the landing hero CTA (the home page), not buried in the lab
assert(/class="lp-cta"[\s\S]*id="proBtn"[\s\S]*<\/div>/.test(html), "the Go Pro button is not in the landing hero CTA");

// 3. paywall.js gates the right surface and exposes a token API.
const js = read("paywall.js");
assert(/export\s+const\s+Paywall\s*=/.test(js), "paywall.js does not export Paywall");
assert(/const\s+TOKENS\s*=\s*new Set\(/.test(js), "paywall.js defines no access-token set");
assert(/localStorage/.test(js), "paywall.js does not persist unlock state");
assert(/paramPanel/.test(js) && /pw-locked/.test(js), "paywall.js does not gate the Parameters rail (#paramPanel / pw-locked)");
for (const id of ["obsCsvBtn", "obsLinkBtn"]) assert(js.includes(id), `paywall.js does not guard the export control #${id}`);
// the gate must veil #paramPanel in CSS (position + locked-state display)
const css = read("paywall.css");
assert(/#paramPanel\.pw-locked\s+\.param-lock/.test(css), "paywall.css does not reveal the lock overlay when #paramPanel is locked");
assert(!/#caa86a/i.test(css), "paywall.css must not reintroduce the web6 brass accent");

// 4. BEHAVIOUR: a real access token actually unlocks, case/space-insensitively.
//    Evaluate the module's pure token logic in a sandbox (strip the DOM boot so
//    it runs headless), then exercise validToken().
let P = null;
try {
  let src = js
    .replace(/if \(document\.readyState[\s\S]*?else boot\(\);/, "")   // drop the DOM boot
    .replace(/export\s+const\s+Paywall/, "const Paywall");           // make it a plain script
  src += "\n; globalThis.__P = { validToken, normToken, TOKENS };";
  const ctx = { console };
  ctx.globalThis = ctx;
  vm.createContext(ctx);
  vm.runInContext(src, ctx, { filename: "paywall-headless.js" });
  P = ctx.__P;
  ok();
} catch (e) { fail(`could not evaluate paywall token logic: ${String(e.message).slice(0, 160)}`); }

if (P) {
  assert(P.TOKENS.size >= 1, "no access tokens defined");
  const sample = [...P.TOKENS][0];
  assert(P.validToken(sample), `the shipped token ${sample} does not validate`);
  assert(P.validToken(`  ${sample.toLowerCase()}  `), "token validation is not case/space-insensitive");
  assert(!P.validToken("not-a-real-token"), "an invalid token was accepted");
  assert(!P.validToken(""), "an empty token was accepted");
  // the token documented in the PR / handoff must be live
  assert(P.validToken("CATALYST-SILENCE"), "the handoff token CATALYST-SILENCE is not accepted");
}

console.log(`\n${checks} checks passed, ${failures} failure(s).`);
process.exit(failures === 0 ? 0 : 1);
