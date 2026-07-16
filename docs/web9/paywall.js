// web9 · Pro paywall — access is now REGISTRATION-GATED. The Instrument's
// Parameters rail (tweak the knobs, drive the transport, export CSV / copy a
// run link) is locked until you register and claim an access code.
//
// The offer: the FIRST 10 PEOPLE get a code for FREE. Register with a name +
// email and you're handed one of ten free access codes on the spot; once all
// ten are claimed the free tier closes and a code costs $9.99 (demo checkout).
// Either way you leave with a shareable code — redeem it on any device to
// unlock. Watching the live specimen stays free; only control/measure/export
// is gated.
//
// Static-site reality: there is no server, so the "10 free" ledger and the
// unlock live in localStorage — the same honest client-side model as the rest
// of the site (not a security boundary). Pure DOM; injects its own modal and
// the Parameters-rail lock overlay so index.html stays lean.

const LS_KEY = 'cellauto_web9_pro';        // unlock flag ('all' once unlocked)
const REG_KEY = 'cellauto_web9_registry';  // { claimed: [{name,email,code,free}] }
const FREE_LIMIT = 10;                      // the first ten codes are on the house

// Legacy demo tokens — still redeemable so already-shared codes keep working.
// (Case-insensitive, dashes/spaces tolerated.)
const TOKENS = new Set(['CATALYST-SILENCE', 'INSTRUMENT-PRO', 'CS-PRO-2026']);

const normToken = (s) => String(s || '').trim().toUpperCase().replace(/\s+/g, '-');

// ── access codes: FNV-1a checksum makes a code verifiable offline (not secret) ──
function cksum(s) {
  let h = 2166136261 >>> 0;
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; }
  return ('0000' + (h >>> 0).toString(36).toUpperCase()).slice(-4);
}
// A registration code is well-formed and checksum-valid: CS-REG-XXXX-CCCC.
const makeCode = (body) => `CS-REG-${body}-${cksum('CS-REG-' + body)}`;

const CODE_ALPHABET = '0123456789ABCDEFGHJKLMNPQRSTUVWXYZ'; // Crockford-ish (no I/L/O/U)
function randomBody() {
  let out = '';
  try {
    const buf = new Uint32Array(4);
    (window.crypto || window.msCrypto).getRandomValues(buf);
    for (let i = 0; i < 4; i++) out += CODE_ALPHABET[buf[i] % CODE_ALPHABET.length];
  } catch {
    for (let i = 0; i < 4; i++) out += CODE_ALPHABET[Math.floor(Math.random() * CODE_ALPHABET.length)];
  }
  return out;
}
const mintCode = () => makeCode(randomBody());

// The ten free codes — deterministic bodies, checksums computed at load so they
// are always well-formed. First registrant claims FR01, next FR02, and so on.
const FREE_CODES = Array.from({ length: FREE_LIMIT }, (_, i) => makeCode('FR' + String(i + 1).padStart(2, '0')));

// A code redeems if it's a legacy token, a free code, or a checksum-valid mint.
function validToken(s) {
  const t = normToken(s);
  if (!t) return false;
  if (TOKENS.has(t) || FREE_CODES.includes(t)) return true;
  const m = t.match(/^CS-REG-([0-9A-Z]{4})-([0-9A-Z]{4})$/);
  return !!m && cksum('CS-REG-' + m[1]) === m[2];
}

// ── the free-code ledger (pure over a registry object; localStorage wrappers below) ──
const freeRemaining = (claimedCount) => Math.max(0, FREE_LIMIT - claimedCount);
const nextFreeCode = (claimedCodes) => FREE_CODES.find((c) => !claimedCodes.includes(c)) || null;

function claimFree(registry, name, email) {
  const code = nextFreeCode(registry.claimed.map((c) => c.code));
  if (!code) return { ok: false, full: true };
  registry.claimed.push({ name: String(name || '').trim(), email: String(email || '').trim(), code, free: true });
  return { ok: true, code };
}

const isPro = () => { try { return localStorage.getItem(LS_KEY) === 'all'; } catch { return false; } };
const setPro = () => { try { localStorage.setItem(LS_KEY, 'all'); } catch { /* private mode: session only */ } };

function readRegistry() {
  try {
    const o = JSON.parse(localStorage.getItem(REG_KEY) || 'null');
    return o && Array.isArray(o.claimed) ? o : { claimed: [] };
  } catch { return { claimed: [] }; }
}
function writeRegistry(reg) { try { localStorage.setItem(REG_KEY, JSON.stringify(reg)); } catch { /* private mode */ } }
const remainingFree = () => freeRemaining(readRegistry().claimed.length);

const validEmail = (s) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(s || '').trim());

const $ = (id) => document.getElementById(id);
const el = (html) => { const t = document.createElement('template'); t.innerHTML = html.trim(); return t.content.firstElementChild; };

// ── the paywall modal (injected once) ───────────────────────────────────────
function ensureModal() {
  let m = $('pwModal');
  if (m) return m;
  m = el(`
    <div id="pwModal" class="pw-modal" role="dialog" aria-modal="true" aria-labelledby="pwTitle" hidden>
      <div class="pw-scrim" data-close="1"></div>
      <div class="pw-card" role="document">
        <button class="pw-x" id="pwClose" type="button" aria-label="Close">×</button>
        <div class="pw-kicker">◆ cellauto · the Instrument</div>
        <h3 id="pwTitle">Register for an access code</h3>
        <p class="pw-cap">Controlling the instrument — the live knobs, the step/reset transport, CSV
          export and shareable run links — needs an access code. Register below and
          <strong>the first ten people get one free</strong>.</p>
        <p class="pw-remain" id="pwRemain" aria-live="polite"></p>

        <form class="pw-reg" id="pwRegForm" autocomplete="off">
          <input id="pwName" class="pw-field" type="text" placeholder="Your name" aria-label="Your name" autocomplete="name">
          <input id="pwEmail" class="pw-field" type="email" placeholder="you@example.com" aria-label="Email" autocomplete="email" inputmode="email" spellcheck="false">
          <button class="pw-btn" id="pwClaim" type="submit">Claim my free code</button>
        </form>

        <div class="pw-code" id="pwCode" hidden>
          <span class="pw-code-label">Your access code</span>
          <code class="pw-code-val" id="pwCodeVal"></code>
          <span class="pw-code-sub">Saved on this device — redeem it anywhere to unlock.</span>
        </div>

        <div class="pw-or"><span>already have a code?</span></div>
        <form class="pw-redeem" id="pwForm" autocomplete="off">
          <input id="pwToken" class="pw-token" type="text" inputmode="text"
                 placeholder="Access code" aria-label="Access code" spellcheck="false">
          <button class="pw-redeem-btn" id="pwRedeem" type="submit">Redeem</button>
        </form>
        <p class="pw-msg" id="pwMsg" role="status" aria-live="polite"></p>
        <p class="pw-note">No charge for the first ten. A code unlocks this device and is yours to share.</p>
      </div>
    </div>`);
  document.body.appendChild(m);

  const close = () => hide();
  m.querySelector('.pw-scrim').addEventListener('click', close);
  $('pwClose').addEventListener('click', close);

  // Register → claim a free code (or, once sold out, buy one via demo checkout).
  $('pwRegForm').addEventListener('submit', (e) => {
    e.preventDefault();
    const name = $('pwName').value.trim();
    const email = $('pwEmail').value.trim();
    if (!name) { msg('Enter your name to register.', false); return; }
    if (!validEmail(email)) { msg('Enter a valid email to register.', false); return; }

    const reg = readRegistry();
    if (remainingFree() > 0) {
      const res = claimFree(reg, name, email);
      writeRegistry(reg);
      unlock('You’re in — free code claimed.', res.code);
    } else {
      // Free tier closed: mint a paid code (demo checkout — nothing is charged).
      const code = mintCode();
      reg.claimed.push({ name, email, code, free: false });
      writeRegistry(reg);
      unlock('Registered — access code issued.', code);
    }
  });

  // Redeem an existing code.
  $('pwForm').addEventListener('submit', (e) => {
    e.preventDefault();
    const code = $('pwToken').value;
    if (validToken(code)) { unlock('Code accepted — unlocked.'); }
    else { msg(code.trim() ? 'That code isn’t valid. Check for typos.' : 'Enter a code to redeem.', false); }
  });

  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !m.hidden) close(); });
  return m;
}

// Reflect the current free-slot count in the modal (register vs. sold-out copy).
function refreshModal() {
  const left = remainingFree();
  const remainEl = $('pwRemain');
  const claim = $('pwClaim');
  if (remainEl) {
    remainEl.textContent = left > 0
      ? `${left} of ${FREE_LIMIT} free codes remaining`
      : 'All 10 free codes are claimed — a code is $9.99 (demo checkout).';
    remainEl.classList.toggle('is-soldout', left === 0);
  }
  if (claim) claim.textContent = left > 0 ? 'Claim my free code' : 'Register — get a code ($9.99)';
  const codeBox = $('pwCode'); if (codeBox) codeBox.hidden = true;
}

function msg(text, good = true) {
  const em = $('pwMsg'); if (!em) return;
  em.textContent = text; em.classList.toggle('is-bad', !good); em.classList.toggle('is-good', good);
}

// ── the Parameters-rail lock overlay (injected once, survives paramList rebuilds) ──
function ensureLock() {
  const panel = $('paramPanel');
  if (!panel || panel.querySelector('.param-lock')) return;
  const lock = el(`
    <div class="param-lock" aria-hidden="true">
      <div class="param-lock-card">
        <span class="param-lock-ico" aria-hidden="true">◆</span>
        <p class="param-lock-cap">Register for an access code to tweak parameters and control this simulation.</p>
        <button class="param-lock-btn" id="paramUnlock" type="button">Claim a free code</button>
        <span class="param-lock-sub">watching the live specimen is free</span>
      </div>
    </div>`);
  panel.appendChild(lock);
  lock.querySelector('#paramUnlock').addEventListener('click', open);
}

// ── state application ────────────────────────────────────────────────────────
function applyLock() {
  const pro = isPro();
  document.body.classList.toggle('pw-pro', pro);
  const panel = $('paramPanel');
  if (panel) panel.classList.toggle('pw-locked', !pro);
  const b = $('proBtn');
  if (b) {
    b.textContent = pro ? '✓ Unlocked' : '◆ Get a free code';
    b.classList.toggle('is-pro', pro);
  }
}

function show() { const m = ensureModal(); refreshModal(); m.hidden = false; requestAnimationFrame(() => m.classList.add('show')); const t = $('pwName'); if (t) setTimeout(() => t.focus(), 60); }
function hide() { const m = $('pwModal'); if (!m) return; m.classList.remove('show'); setTimeout(() => { m.hidden = true; }, 180); }
function open() { msg('', true); show(); }

// Unlock; when a fresh code was issued, reveal it so the user can save/share it.
function unlock(note, code) {
  setPro();
  applyLock();
  msg(note || 'Unlocked.', true);
  if (code) {
    const box = $('pwCode'), val = $('pwCodeVal');
    if (box && val) { val.textContent = code; box.hidden = false; }
    setTimeout(hide, 2600); // linger so the code can be copied
  } else {
    setTimeout(hide, 650);
  }
}

// ── boot ─────────────────────────────────────────────────────────────────────
function boot() {
  ensureModal();
  ensureLock();
  applyLock();
  const proBtn = $('proBtn');
  if (proBtn) proBtn.addEventListener('click', open);
  // Belt-and-braces: even if the overlay is scrolled out of view, a locked click
  // on an export control opens the paywall instead of firing main.js's handler.
  for (const id of ['obsCsvBtn', 'obsLinkBtn']) {
    const em = $(id);
    if (em) em.addEventListener('click', (e) => {
      if (!isPro()) { e.preventDefault(); e.stopImmediatePropagation(); open(); }
    }, true);
  }
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
else boot();

// Exposed for tests and for console redemption if you prefer: Paywall.redeem('…').
export const Paywall = {
  LS_KEY, REG_KEY, TOKENS, FREE_CODES, FREE_LIMIT,
  isPro, setPro, validToken, normToken, makeCode, mintCode, cksum,
  freeRemaining, nextFreeCode, claimFree, remainingFree, validEmail, applyLock, open,
  redeem: (code) => { if (validToken(code)) { unlock('Code accepted — unlocked.'); return true; } return false; },
  // Register from the console: Paywall.register('Ada', 'ada@x.io') → { ok, code }.
  register: (name, email) => {
    if (!validEmail(email)) return { ok: false, error: 'invalid-email' };
    const reg = readRegistry();
    if (freeRemaining(reg.claimed.length) > 0) {
      const res = claimFree(reg, name, email);
      writeRegistry(reg); setPro(); applyLock();
      return res;
    }
    const code = mintCode();
    reg.claimed.push({ name: String(name || '').trim(), email: String(email || '').trim(), code, free: false });
    writeRegistry(reg); setPro(); applyLock();
    return { ok: true, code, paid: true };
  },
};
if (typeof window !== 'undefined') window.Paywall = Paywall;
