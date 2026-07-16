/* pro.js — Catalytic Silence · client-side "Pro" unlock, token-gated.
 *
 * Zero-dependency CLASSIC script (no ES-module import — include it with a plain
 * <script src="./pro.js"></script> before the client's module). Exposes a single
 * global, window.CatSilPro.
 *
 * The site is a static GitHub Pages deploy, so the paywall is deliberately a
 * CLIENT-SIDE unlock, not a server entitlement: a well-formed, shareable UNLOCK
 * TOKEN (CATSIL-XXXX-XXXX-CKSUM) persisted in localStorage under one shared key.
 * Because localStorage is per-origin, redeeming a token in ANY client (slime,
 * web10, …) unlocks Pro in ALL of them on the same origin, and it survives a
 * reload. This gates the hi-res (up to 4000²) SEM micrograph plate export.
 *
 * This is NOT a security boundary — a client-side unlock never can be. The
 * checksum only makes the token well-formed and verifiable offline, which is
 * exactly the "free taste → unlock with a token" product model (see docs/PRICING).
 *
 * API:
 *   CatSilPro.isUnlocked()            -> boolean
 *   CatSilPro.getToken()              -> string | null   (the stored token)
 *   CatSilPro.verify(token)           -> boolean         (well-formed + checksum ok)
 *   CatSilPro.redeem(token)           -> boolean         (verify, then persist)
 *   CatSilPro.grantDemo()             -> string          (mint + persist a token)
 *   CatSilPro.clear()                 -> void            (lock again; forget token)
 *   CatSilPro.showPaywall({ onUnlock, reason }) -> void  (open the modal)
 *   CatSilPro.hidePaywall()           -> void
 *   CatSilPro.onChange(fn)            -> void            (fn(unlocked) on unlock/clear)
 */
(function () {
  'use strict';

  var KEY = 'catsil.pro.token';
  var PREFIX = 'CATSIL';
  var listeners = [];

  // ── token: FNV-1a checksum makes a token verifiable offline (not a secret) ──
  function checksum(s) {
    var h = 2166136261 >>> 0;
    for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; }
    var out = (h >>> 0).toString(36).toUpperCase();
    return ('000000' + out).slice(-6);
  }

  function randomBody() {
    var alphabet = '0123456789ABCDEFGHJKLMNPQRSTUVWXYZ'; // Crockford-ish (no I/O)
    var n = 8, out = '';
    try {
      var buf = new Uint32Array(n);
      (window.crypto || window.msCrypto).getRandomValues(buf);
      for (var i = 0; i < n; i++) out += alphabet[buf[i] % alphabet.length];
    } catch (e) {
      // Fallback if crypto is unavailable — still well-formed, just less random.
      for (var j = 0; j < n; j++) out += alphabet[Math.floor(Math.random() * alphabet.length)];
    }
    return out;
  }

  function format(body) {
    return PREFIX + '-' + body.slice(0, 4) + '-' + body.slice(4, 8) + '-' + checksum(PREFIX + body);
  }

  function mint() { return format(randomBody()); }

  function verify(token) {
    if (typeof token !== 'string') return false;
    var t = token.trim().toUpperCase().replace(/\s+/g, '');
    var m = t.match(/^CATSIL-([0-9A-Z]{4})-([0-9A-Z]{4})-([0-9A-Z]{6})$/);
    if (!m) return false;
    var body = m[1] + m[2];
    return checksum(PREFIX + body) === m[3];
  }

  // ── storage ──
  function read() {
    try { return window.localStorage.getItem(KEY); } catch (e) { return memToken; }
  }
  var memToken = null; // in-memory fallback when localStorage is blocked (private mode)
  function write(token) {
    memToken = token;
    try { if (token) window.localStorage.setItem(KEY, token); else window.localStorage.removeItem(KEY); }
    catch (e) { /* ignore — memToken carries the session */ }
  }

  function getToken() { var t = read(); return (t && verify(t)) ? t : null; }
  function isUnlocked() { return !!getToken(); }

  function emit() { var u = isUnlocked(); for (var i = 0; i < listeners.length; i++) { try { listeners[i](u); } catch (e) {} } }

  function redeem(token) {
    if (!verify(token)) return false;
    write(token.trim().toUpperCase().replace(/\s+/g, ''));
    emit();
    return true;
  }
  function grantDemo() { var t = mint(); write(t); emit(); return t; }
  function clear() { write(null); emit(); }
  function onChange(fn) { if (typeof fn === 'function') listeners.push(fn); }

  // Cross-tab / cross-client sync: another tab redeeming a token unlocks this one.
  try {
    window.addEventListener('storage', function (e) { if (e.key === KEY) emit(); });
  } catch (e) {}

  // ── paywall modal (self-contained; injected on first open) ─────────────────
  var modal = null, cbUnlock = null;

  function injectStyles() {
    if (document.getElementById('catsil-pro-style')) return;
    var css = [
      '.catsil-pro-scrim{position:fixed;inset:0;z-index:9999;display:flex;align-items:center;',
      'justify-content:center;background:rgba(4,6,10,.72);backdrop-filter:blur(6px);',
      '-webkit-backdrop-filter:blur(6px);padding:20px;font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}',
      '.catsil-pro-scrim[hidden]{display:none}',
      '.catsil-pro-card{position:relative;max-width:420px;width:100%;background:#0b0e14;',
      'border:1px solid rgba(63,224,208,.28);border-radius:14px;padding:28px 26px 22px;',
      'box-shadow:0 24px 80px rgba(0,0,0,.6),0 0 0 1px rgba(215,123,255,.10);color:#e7ecef}',
      '.catsil-pro-card h3{margin:0 0 6px;font-size:19px;font-weight:600;letter-spacing:.2px;color:#fff}',
      '.catsil-pro-kick{margin:0 0 14px;font-size:11px;letter-spacing:.22em;text-transform:uppercase;color:#d77bff}',
      '.catsil-pro-card p{margin:0 0 14px;font-size:13.5px;line-height:1.55;color:#aeb7bd}',
      '.catsil-pro-card strong{color:#3fe0d0;font-weight:600}',
      '.catsil-pro-btn{display:block;width:100%;box-sizing:border-box;margin:0 0 10px;padding:12px 14px;',
      'border-radius:9px;border:1px solid transparent;font:inherit;font-size:14px;font-weight:600;cursor:pointer;',
      'background:linear-gradient(180deg,#3fe0d0,#2bb7ab);color:#04201d;transition:filter .15s}',
      '.catsil-pro-btn:hover{filter:brightness(1.08)}',
      '.catsil-pro-btn.ghost{background:transparent;border-color:rgba(215,123,255,.4);color:#d77bff}',
      '.catsil-pro-btn.ghost:hover{background:rgba(215,123,255,.10)}',
      '.catsil-pro-or{display:flex;align-items:center;gap:10px;margin:6px 0 12px;color:#5b666d;font-size:11px;letter-spacing:.14em;text-transform:uppercase}',
      '.catsil-pro-or::before,.catsil-pro-or::after{content:"";flex:1;height:1px;background:rgba(255,255,255,.08)}',
      '.catsil-pro-redeem{display:flex;gap:8px}',
      '.catsil-pro-redeem input{flex:1;min-width:0;padding:10px 12px;border-radius:8px;border:1px solid rgba(255,255,255,.14);',
      'background:#070a0f;color:#e7ecef;font:inherit;font-size:13px;letter-spacing:.06em}',
      '.catsil-pro-redeem input:focus{outline:none;border-color:#3fe0d0}',
      '.catsil-pro-redeem button{padding:0 14px;border-radius:8px;border:1px solid rgba(63,224,208,.4);',
      'background:transparent;color:#3fe0d0;font:inherit;font-size:13px;font-weight:600;cursor:pointer}',
      '.catsil-pro-redeem button:hover{background:rgba(63,224,208,.10)}',
      '.catsil-pro-token{margin:12px 0 2px;padding:11px 12px;border-radius:8px;border:1px dashed rgba(63,224,208,.4);',
      'background:rgba(63,224,208,.06);font-family:ui-monospace,"SFMono-Regular",Menlo,monospace;font-size:13px;',
      'letter-spacing:.08em;color:#3fe0d0;text-align:center;word-break:break-all}',
      '.catsil-pro-note{font-size:11.5px;color:#6b757b;margin:12px 0 0}',
      '.catsil-pro-msg{font-size:12px;margin:8px 0 0;min-height:15px}',
      '.catsil-pro-msg.ok{color:#3fe0d0}.catsil-pro-msg.err{color:#ff8a8a}',
      '.catsil-pro-x{position:absolute;top:10px;right:12px;border:none;background:none;color:#6b757b;',
      'font-size:22px;line-height:1;cursor:pointer;padding:4px}.catsil-pro-x:hover{color:#e7ecef}'
    ].join('');
    var style = document.createElement('style');
    style.id = 'catsil-pro-style';
    style.textContent = css;
    document.head.appendChild(style);
  }

  function build(reason) {
    injectStyles();
    var scrim = document.createElement('div');
    scrim.className = 'catsil-pro-scrim';
    scrim.setAttribute('role', 'dialog');
    scrim.setAttribute('aria-modal', 'true');
    scrim.setAttribute('aria-label', 'Unlock Pro');
    scrim.innerHTML =
      '<div class="catsil-pro-card">' +
        '<button class="catsil-pro-x" type="button" aria-label="Close">×</button>' +
        '<p class="catsil-pro-kick">Catalytic Silence · Pro</p>' +
        '<h3>Unlock the hi-res plate</h3>' +
        '<p>' + (reason || 'Unlock the publication-quality <strong>SEM micrograph plate</strong> export — up to <strong>4000×4000</strong> — of any stage. One unlock covers every Catalytic Silence lab on this device.') + '</p>' +
        '<button class="catsil-pro-btn js-unlock" type="button">Unlock — demo checkout</button>' +
        '<div class="catsil-pro-or">or redeem a token</div>' +
        '<div class="catsil-pro-redeem">' +
          '<input class="js-token" type="text" inputmode="text" autocomplete="off" spellcheck="false" ' +
                 'placeholder="CATSIL-XXXX-XXXX-XXXXXX" aria-label="Unlock token">' +
          '<button class="js-redeem" type="button">Apply</button>' +
        '</div>' +
        '<p class="catsil-pro-msg" role="status"></p>' +
        '<p class="catsil-pro-note">Demo checkout — nothing is charged. Your unlock token is stored locally and works across every lab here.</p>' +
      '</div>';
    return scrim;
  }

  function setMsg(text, kind) {
    if (!modal) return;
    var el = modal.querySelector('.catsil-pro-msg');
    el.textContent = text || '';
    el.className = 'catsil-pro-msg' + (kind ? ' ' + kind : '');
  }

  function finish() {
    hidePaywall();
    var fn = cbUnlock; cbUnlock = null;
    if (typeof fn === 'function') { try { fn(getToken()); } catch (e) {} }
  }

  function showToken(token, msg) {
    if (!modal) return;
    var card = modal.querySelector('.catsil-pro-card');
    var line = document.createElement('div');
    line.className = 'catsil-pro-token';
    line.textContent = token;
    var redeemRow = modal.querySelector('.catsil-pro-redeem');
    card.insertBefore(line, redeemRow);
    setMsg(msg || 'Unlocked. Save this token to unlock on another device.', 'ok');
  }

  function showPaywall(opts) {
    opts = opts || {};
    cbUnlock = opts.onUnlock || null;
    // Already unlocked? Honour it immediately.
    if (isUnlocked()) { finish(); return; }
    modal = build(opts.reason);
    document.body.appendChild(modal);
    var close = function () { hidePaywall(); };
    modal.querySelector('.catsil-pro-x').addEventListener('click', close);
    modal.addEventListener('click', function (e) { if (e.target === modal) close(); });
    document.addEventListener('keydown', escClose);
    modal.querySelector('.js-unlock').addEventListener('click', function () {
      var t = grantDemo();
      showToken(t);
      setTimeout(finish, 1400);
    });
    modal.querySelector('.js-redeem').addEventListener('click', doRedeem);
    var input = modal.querySelector('.js-token');
    input.addEventListener('keydown', function (e) { if (e.key === 'Enter') doRedeem(); });
    input.focus();
  }

  function doRedeem() {
    if (!modal) return;
    var val = modal.querySelector('.js-token').value;
    if (!val || !val.trim()) { setMsg('Enter a token to redeem.', 'err'); return; }
    if (redeem(val)) { setMsg('Token accepted — unlocking…', 'ok'); setTimeout(finish, 700); }
    else { setMsg('That token isn’t valid. Check the format and try again.', 'err'); }
  }

  function escClose(e) { if (e.key === 'Escape') hidePaywall(); }

  function hidePaywall() {
    document.removeEventListener('keydown', escClose);
    if (modal && modal.parentNode) modal.parentNode.removeChild(modal);
    modal = null;
  }

  window.CatSilPro = {
    isUnlocked: isUnlocked,
    getToken: getToken,
    verify: verify,
    redeem: redeem,
    grantDemo: grantDemo,
    clear: clear,
    showPaywall: showPaywall,
    hidePaywall: hidePaywall,
    onChange: onChange
  };
})();
