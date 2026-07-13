// web9 · Pro paywall — gates the Instrument's Parameters rail (tweak the knobs,
// drive the transport, export CSV / copy a run link) behind a one-tap unlock,
// with a redeemable access token so you can "pay for now" without a charge.
//
// Additive by design: the free view keeps the live apparatus + SEM micrograph
// running and every stage browsable. Only the instrument's control/measure/
// export surface is gated — matching the product model "unlock to tweak
// parameters and control this simulation." Pure DOM; injects its own modal and
// lock overlay so index.html stays lean and the existing web9 gates are untouched.

const LS_KEY = 'cellauto_web9_pro';

// Demo access tokens. Redeem one in the paywall to unlock everything for now —
// nothing is charged. (A static site has no payment backend, so these are the
// honest "pay for now" mechanism; case-insensitive, dashes/spaces tolerated.)
const TOKENS = new Set(['CATALYST-SILENCE', 'INSTRUMENT-PRO', 'CS-PRO-2026']);

const normToken = (s) => String(s || '').trim().toUpperCase().replace(/\s+/g, '-');
const validToken = (s) => TOKENS.has(normToken(s));

const isPro = () => { try { return localStorage.getItem(LS_KEY) === 'all'; } catch { return false; } };
const setPro = () => { try { localStorage.setItem(LS_KEY, 'all'); } catch { /* private mode: session only */ } };

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
        <h3 id="pwTitle">Unlock the Instrument</h3>
        <p class="pw-cap">Unlock to tweak parameters and control this simulation — the live knobs,
          the step/reset transport, plus CSV export and shareable run links.</p>
        <div class="pw-buys">
          <button class="pw-btn" id="pwOne" type="button">Unlock — $1</button>
          <button class="pw-all" id="pwAll" type="button">Or unlock everything — $9.99</button>
        </div>
        <div class="pw-or"><span>or redeem an access token</span></div>
        <form class="pw-redeem" id="pwForm" autocomplete="off">
          <input id="pwToken" class="pw-token" type="text" inputmode="text"
                 placeholder="Access token" aria-label="Access token" spellcheck="false">
          <button class="pw-redeem-btn" id="pwRedeem" type="submit">Redeem</button>
        </form>
        <p class="pw-msg" id="pwMsg" role="status" aria-live="polite"></p>
        <p class="pw-note">Demo checkout — nothing is charged. An access token unlocks this device.</p>
      </div>
    </div>`);
  document.body.appendChild(m);

  const close = () => hide();
  m.querySelector('.pw-scrim').addEventListener('click', close);
  $('pwClose').addEventListener('click', close);
  $('pwOne').addEventListener('click', () => unlock('Unlocked — enjoy the Instrument.'));
  $('pwAll').addEventListener('click', () => unlock('Everything unlocked — thank you!'));
  $('pwForm').addEventListener('submit', (e) => {
    e.preventDefault();
    const code = $('pwToken').value;
    if (validToken(code)) { unlock('Token accepted — unlocked.'); }
    else { msg(code.trim() ? 'That token isn’t valid. Check for typos.' : 'Enter a token to redeem.', false); }
  });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !m.hidden) close(); });
  return m;
}

function msg(text, good = true) {
  const el = $('pwMsg'); if (!el) return;
  el.textContent = text; el.classList.toggle('is-bad', !good); el.classList.toggle('is-good', good);
}

// ── the Parameters-rail lock overlay (injected once, survives paramList rebuilds) ──
function ensureLock() {
  const panel = $('paramPanel');
  if (!panel || panel.querySelector('.param-lock')) return;
  const lock = el(`
    <div class="param-lock" aria-hidden="true">
      <div class="param-lock-card">
        <span class="param-lock-ico" aria-hidden="true">◆</span>
        <p class="param-lock-cap">Unlock to tweak parameters and control this simulation.</p>
        <button class="param-lock-btn" id="paramUnlock" type="button">Unlock — $1</button>
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
  if (b) { b.textContent = pro ? '✓ Pro — unlocked' : '◆ Go Pro — $1'; b.classList.toggle('is-pro', pro); }
}

function show() { const m = ensureModal(); m.hidden = false; requestAnimationFrame(() => m.classList.add('show')); const t = $('pwToken'); if (t) setTimeout(() => t.focus(), 60); }
function hide() { const m = $('pwModal'); if (!m) return; m.classList.remove('show'); setTimeout(() => { m.hidden = true; }, 180); }
function open() { msg('', true); show(); }

function unlock(note) {
  setPro();
  applyLock();
  msg(note || 'Unlocked.', true);
  setTimeout(hide, 650);
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
    const el = $(id);
    if (el) el.addEventListener('click', (e) => {
      if (!isPro()) { e.preventDefault(); e.stopImmediatePropagation(); open(); }
    }, true);
  }
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
else boot();

// Exposed for tests and for console redemption if you prefer: Paywall.redeem('…').
export const Paywall = {
  LS_KEY, TOKENS, isPro, setPro, validToken, normToken, applyLock, open,
  redeem: (code) => { if (validToken(code)) { unlock('Token accepted — unlocked.'); return true; } return false; },
};
if (typeof window !== 'undefined') window.Paywall = Paywall;
