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

// 2b. Landing links to the paid studios — the on-site Slime Studio (nav + card)
//     and the full-feed Studio artifact.
assert((html.match(/href="\.\.\/slime\//g) || []).length >= 2, "landing must link to the on-site Slime Studio (../slime/) in both the nav and an Experiences card");
assert(/claude\.ai\/code\/artifact\//.test(html), "landing does not link to the full-feed Studio artifact");
assert(/class="lp-exp lp-exp-pro"/.test(html) && /The Studio/.test(html), "landing is missing the Pro Studio experience card");

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

// 3b. Access is registration-gated: the modal leads with a register form and
//     the source advertises the "first 10 free" ledger.
assert(/id="pwRegForm"/.test(js) && /id="pwName"/.test(js) && /id="pwEmail"/.test(js),
  "paywall.js modal has no registration form (name + email)");
assert(/FREE_LIMIT\s*=\s*10/.test(js), "the free tier must be 10 codes (FREE_LIMIT = 10)");
assert(/FREE_CODES/.test(js) && /claimFree/.test(js) && /remainingFree/.test(js),
  "paywall.js does not implement the free-code ledger (FREE_CODES / claimFree / remainingFree)");
assert(/id="pwRemain"/.test(js) && /free codes remaining/.test(js),
  "paywall.js does not surface how many free codes remain");

// 4. BEHAVIOUR: registration hands out the ten free codes, then closes; codes
//    (legacy + free + freshly minted) all validate. Evaluate the module's pure
//    logic in a sandbox (strip the DOM boot so it runs headless).
let P = null;
try {
  let src = js
    .replace(/if \(document\.readyState[\s\S]*?else boot\(\);/, "")   // drop the DOM boot
    .replace(/export\s+const\s+Paywall/, "const Paywall");           // make it a plain script
  src += "\n; globalThis.__P = { validToken, normToken, TOKENS, FREE_CODES, FREE_LIMIT, makeCode, mintCode, freeRemaining, nextFreeCode, claimFree };";
  const ctx = { console };
  ctx.globalThis = ctx;
  // Minimal window shim so mintCode()'s crypto path has a fallback.
  ctx.window = {};
  vm.createContext(ctx);
  vm.runInContext(src, ctx, { filename: "paywall-headless.js" });
  P = ctx.__P;
  ok();
} catch (e) { fail(`could not evaluate paywall logic: ${String(e.message).slice(0, 160)}`); }

if (P) {
  assert(P.TOKENS.size >= 1, "no legacy access tokens defined");
  // legacy tokens still redeem, case/space-insensitively
  assert(P.validToken("CATALYST-SILENCE"), "the handoff token CATALYST-SILENCE is not accepted");
  assert(P.validToken("  catalyst silence  "), "token validation is not case/space-insensitive");
  assert(!P.validToken("not-a-real-token"), "an invalid code was accepted");
  assert(!P.validToken(""), "an empty code was accepted");

  // exactly ten free codes, each well-formed and redeemable
  assert(P.FREE_LIMIT === 10 && P.FREE_CODES.length === 10, "there must be exactly 10 free codes");
  assert(P.FREE_CODES.every((c) => P.validToken(c)), "a free code does not validate");
  assert(new Set(P.FREE_CODES).size === 10, "the free codes are not distinct");

  // a freshly minted (paid) code is checksum-valid; a tampered one is not
  const minted = P.mintCode();
  assert(P.validToken(minted), "a freshly minted code does not validate");
  assert(!P.validToken(minted.replace(/.$/, minted.endsWith("Z") ? "0" : "Z")), "a tampered code was accepted");

  // registration ledger: first 10 registrants get a free code, the 11th does not
  const reg = { claimed: [] };
  const issued = [];
  for (let i = 0; i < 10; i++) {
    assert(P.freeRemaining(reg.claimed.length) === 10 - i, `free-remaining count wrong at claim ${i}`);
    const r = P.claimFree(reg, `User ${i}`, `u${i}@x.io`);
    assert(r.ok && P.validToken(r.code), `claim ${i} did not yield a valid free code`);
    issued.push(r.code);
  }
  assert(new Set(issued).size === 10, "free-code claims were not unique");
  assert(P.freeRemaining(reg.claimed.length) === 0, "free tier did not close after 10 claims");
  const eleventh = P.claimFree(reg, "Overflow", "of@x.io");
  assert(!eleventh.ok && eleventh.full, "an 11th free claim was granted (free tier must be closed)");
}

console.log(`\n${checks} checks passed, ${failures} failure(s).`);
process.exit(failures === 0 ? 0 : 1);
