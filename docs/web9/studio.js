// cellauto · Pro Studio controller.
//
// Boots Clerk from /api/public-config, gates on /api/me/entitlement, builds the
// control panel from /api/rules, and POSTs /api/render to fetch a hi-res SEM
// micrograph PNG. Zero build step — a plain ES module. The heavy lifting (the
// render) happens server-side; this file is just the cockpit.

const $ = (sel) => document.querySelector(sel);
const status = (m) => { const el = $('#status'); if (el) el.textContent = m; };

let CFG = {};
let RULES = [];
let studioReady = false;

const api = async (path, opts = {}) => {
  const headers = Object.assign({}, opts.headers);
  const clerk = window.Clerk;
  if (clerk && clerk.session) {
    try { const t = await clerk.session.getToken(); if (t) headers.Authorization = 'Bearer ' + t; } catch { /* ignore */ }
  }
  return fetch(path, Object.assign({}, opts, { headers }));
};

const setBusy = (b) => {
  $('#vitrine')?.classList.toggle('is-busy', b);
  const btn = $('#renderBtn'); if (btn) btn.disabled = b;
};

function show(mode) {
  $('#gate').hidden = mode !== 'gate';
  $('#studio').hidden = mode !== 'studio';
  $('#stagearea').hidden = mode !== 'studio';
}

// ── boot ─────────────────────────────────────────────────────────────────────

async function boot() {
  try { CFG = await (await fetch('/api/public-config')).json(); } catch { CFG = {}; }

  if (CFG.devUnlocked) { await enterStudio(); return; }
  if (!CFG.authConfigured || !CFG.clerkPublishableKey) { showGate('unconfigured'); return; }

  try {
    await loadClerk(CFG.clerkPublishableKey);
  } catch (e) {
    showGate('error', 'Could not load the sign-in module.');
    return;
  }
  wireAccount();
  window.Clerk.addListener((payload) => { if ('user' in payload) route(); });
  await route();
}

async function route() {
  const clerk = window.Clerk;
  if (!clerk || !clerk.user) { showGate('signedout'); return; }
  let ent = { entitled: false, reason: 'error' };
  try { ent = await (await api('/api/me/entitlement')).json(); } catch { /* keep default */ }
  if (ent.entitled) await enterStudio();
  else showGate('upgrade');
}

// ── Clerk loader (CDN, derived from the publishable key) ─────────────────────

function frontendApi(pk) {
  // pk_(test|live)_<base64("frontend-api$")>
  const enc = pk.split('_').slice(2).join('_');
  try { return atob(enc).replace(/\$+$/, ''); } catch { return ''; }
}

function injectScript(src, pk) {
  return new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = src; s.async = true; s.crossOrigin = 'anonymous';
    s.setAttribute('data-clerk-publishable-key', pk);
    s.onload = resolve;
    s.onerror = () => reject(new Error('clerk script failed to load'));
    document.head.appendChild(s);
  });
}

async function loadClerk(pk) {
  const fapi = frontendApi(pk);
  if (!fapi) throw new Error('bad publishable key');
  await injectScript(`https://${fapi}/npm/@clerk/clerk-js@5/dist/clerk.browser.js`, pk);
  await window.Clerk.load();
}

function wireAccount() {
  const clerk = window.Clerk;
  const acct = $('#account');
  if (!acct) return;
  if (clerk && clerk.user) {
    const email = clerk.user.primaryEmailAddress?.emailAddress || 'signed in';
    acct.innerHTML = `<span class="who">${email}</span><button class="btn ghost" id="signOutBtn" style="width:auto;padding:6px 12px">Sign out</button>`;
    $('#signOutBtn').onclick = () => clerk.signOut(() => route());
  } else {
    acct.innerHTML = '<a class="who" href="../">← back to the lab</a>';
  }
}

// ── gate ─────────────────────────────────────────────────────────────────────

function showGate(kind, msg) {
  show('gate');
  const title = $('#gateTitle');
  const blurb = $('#gateBlurb');
  const upgrade = $('#upgradeBtn');
  const signin = $('#signin');
  signin.innerHTML = '';
  upgrade.hidden = true;

  if (kind === 'unconfigured') {
    title.textContent = 'Pro Studio — coming soon';
    blurb.textContent = 'Hi-res SEM export is not configured on this deployment yet.';
  } else if (kind === 'error') {
    title.textContent = 'Something went wrong';
    blurb.textContent = msg || 'Please try again.';
  } else if (kind === 'signedout') {
    title.textContent = 'Pro Studio';
    blurb.textContent = 'Sign in to render publication-quality micrographs.';
    try { window.Clerk.mountSignIn(signin); } catch { /* ignore */ }
  } else if (kind === 'upgrade') {
    title.textContent = 'Upgrade to Pro';
    blurb.textContent = 'Render any stage as a 4000×4000 SEM micrograph and download the PNG.';
    $('#gatePrice').textContent = CFG.priceLabel ? `· ${CFG.priceLabel}` : '';
    upgrade.hidden = false;
    upgrade.onclick = startCheckout;
  }
  wireAccount();
}

async function startCheckout() {
  setBusy(true); status('Opening checkout…');
  try {
    const res = await api('/api/checkout', { method: 'POST' });
    const data = await res.json();
    if (res.ok && data.url) { window.location.href = data.url; return; }
    showGate('error', data.detail || 'Checkout is unavailable.');
  } catch {
    showGate('error', 'Checkout is unavailable.');
  } finally { setBusy(false); }
}

// ── studio ───────────────────────────────────────────────────────────────────

async function enterStudio() {
  show('studio');
  wireAccount();
  if (!studioReady) {
    try { RULES = await (await fetch('/api/rules')).json(); } catch { RULES = []; }
    buildStages();
    buildSizeOptions(CFG.limits?.maxSize || 4000);
    applyLimits();
    $('#stage').addEventListener('change', onStageChange);
    $('#renderBtn').addEventListener('click', doRender);
    onStageChange();
    studioReady = true;
  }
}

function buildStages() {
  const sel = $('#stage');
  sel.innerHTML = RULES.map((r) => `<option value="${r.name}">${r.label}</option>`).join('');
}

function buildSizeOptions(maxSize) {
  const candidates = [1024, 2048, 3000, 4000, maxSize].filter((s) => s <= maxSize);
  const uniq = [...new Set(candidates)].sort((a, b) => a - b);
  const sel = $('#size');
  sel.innerHTML = uniq.map((s) => `<option value="${s}"${s === 2048 ? ' selected' : ''}>${s}×${s}</option>`).join('');
  if (!uniq.includes(2048)) sel.value = String(uniq[uniq.length - 1]);
}

function applyLimits() {
  const lim = CFG.limits || {};
  if (lim.maxGrid) $('#grid').max = lim.maxGrid;
  if (lim.maxSteps) $('#steps').max = lim.maxSteps;
}

function currentRule() {
  return RULES.find((r) => r.name === $('#stage').value);
}

function onStageChange() {
  const rule = currentRule();
  if (!rule) return;
  const wrap = $('#regimeWrap');
  if (rule.presets && rule.presets.length) {
    wrap.hidden = false;
    $('#regime').innerHTML = rule.presets.map((p) => `<option value="${p}">${p}</option>`).join('');
  } else {
    wrap.hidden = true;
    $('#regime').innerHTML = '';
  }
  buildKnobs(rule);
}

function buildKnobs(rule) {
  const host = $('#knobs');
  host.innerHTML = '';
  for (const p of rule.params) {
    const mid = p.integer ? Math.round((p.lo + p.hi) / 2) : +((p.lo + p.hi) / 2).toFixed(4);
    const row = document.createElement('div');
    row.className = 'knob off';
    row.dataset.attr = p.attr;
    row.dataset.int = p.integer ? '1' : '0';
    row.innerHTML =
      `<input type="checkbox" class="en" aria-label="override ${p.label}">` +
      `<label class="nm">${p.label}</label>` +
      `<input type="range" min="${p.lo}" max="${p.hi}" step="${p.step}" value="${mid}" disabled>` +
      `<span class="val">auto</span>`;
    const en = row.querySelector('.en');
    const rng = row.querySelector('input[type=range]');
    const val = row.querySelector('.val');
    en.addEventListener('change', () => {
      rng.disabled = !en.checked;
      row.classList.toggle('off', !en.checked);
      val.textContent = en.checked ? rng.value : 'auto';
    });
    rng.addEventListener('input', () => { val.textContent = rng.value; });
    host.appendChild(row);
  }
}

function gatherParams() {
  const params = {};
  for (const row of document.querySelectorAll('#knobs .knob')) {
    const en = row.querySelector('.en');
    if (!en.checked) continue;
    const rng = row.querySelector('input[type=range]');
    const v = Number(rng.value);
    params[row.dataset.attr] = row.dataset.int === '1' ? Math.round(v) : v;
  }
  return params;
}

async function doRender() {
  const rule = currentRule();
  if (!rule) return;
  setBusy(true);
  status('Rendering micrograph…');
  const body = {
    rule: rule.name,
    params: gatherParams(),
    seed: Number($('#seed').value),
    grid: Number($('#grid').value),
    steps: Number($('#steps').value),
    size: Number($('#size').value),
    palette: $('#palette').value,
  };
  if (!$('#regimeWrap').hidden) body.preset = $('#regime').value;

  try {
    const res = await api('/api/render', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      let detail = `HTTP ${res.status}`;
      try { detail = (await res.json()).detail || detail; } catch { /* ignore */ }
      if (res.status === 402) { showGate('upgrade'); return; }
      status('Render failed: ' + detail);
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const img = $('#result');
    const prev = img.dataset.url;
    if (prev) URL.revokeObjectURL(prev);
    img.dataset.url = url;
    img.src = url;
    img.hidden = false;
    $('#placeholder').hidden = true;
    const dl = $('#download');
    dl.href = url;
    dl.download = `cellauto-${rule.name}-${body.size}.png`;
    dl.hidden = false;
    $('#renderMeta').textContent = `${body.size}×${body.size} · ${Math.round(blob.size / 1024)} KB`;
    status('Render complete.');
  } catch (e) {
    status('Render failed: network error.');
  } finally {
    setBusy(false);
  }
}

boot();
