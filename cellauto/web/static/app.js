// cellauto web client
//
// Drives the Flask backend: creates a session, ticks it on a timer, paints
// the returned PNG into the canvas, and surfaces per-rule controls
// (parameter sliders, presets, pipeline stage controls, snapshot save/load,
// PNG + GIF export). State lives on the server (so the existing Python rule
// code does all the science); this file is just the view + controls.

const els = {
  rule: document.getElementById("rule"),
  grid: document.getElementById("grid"),
  seed: document.getElementById("seed"),
  play: document.getElementById("play"),
  step: document.getElementById("step"),
  reset: document.getElementById("reset"),
  speed: document.getElementById("speed"),
  speedLabel: document.getElementById("speed-label"),
  stepCount: document.getElementById("step-count"),
  fps: document.getElementById("fps"),
  seedOut: document.getElementById("seed-out"),
  canvas: document.getElementById("canvas"),
  population: document.getElementById("population"),
  legend: document.getElementById("legend"),
  error: document.getElementById("error"),

  presetsWrap: document.getElementById("presets-wrap"),
  presets: document.getElementById("presets"),

  paramsWrap: document.getElementById("params-wrap"),
  params: document.getElementById("params"),
  paramsEmpty: document.getElementById("params-empty"),

  stageSelect: document.getElementById("stage-select"),
  promote: document.getElementById("promote"),
  autoPromote: document.getElementById("auto-promote"),
  stageDuration: document.getElementById("stage-duration"),

  // Wall-label stage display (left column)
  stageEyebrow: document.getElementById("stage-eyebrow"),
  stageTitleText: document.getElementById("stage-title-text"),
  stageCitationText: document.getElementById("stage-citation-text"),
  stageDetailText: document.getElementById("stage-detail-text"),
  brandMark: document.getElementById("brand-mark"),
  specimen: document.querySelector(".specimen"),
  playIcon: document.getElementById("play-icon"),
  playText: document.getElementById("play-text"),

  downloadSnapshot: document.getElementById("download-snapshot"),
  loadSnapshot: document.getElementById("load-snapshot"),
  downloadPng: document.getElementById("download-png"),
  exportGif: document.getElementById("export-gif"),
  gifSteps: document.getElementById("gif-steps"),
  gifFps: document.getElementById("gif-fps"),
  exportStatus: document.getElementById("export-status"),

  tabs: Array.from(document.querySelectorAll(".tab")),
  panes: Array.from(document.querySelectorAll(".tab-pane")),
  stageTab: document.querySelector('.tab[data-tab="stage"]'),

  tutorialBody: document.getElementById("tutorial-body"),
  tutorialPrev: document.getElementById("tutorial-prev"),
  tutorialNext: document.getElementById("tutorial-next"),
  tutorialCounter: document.getElementById("tutorial-counter"),
  tutorialToggle: document.getElementById("tutorial-toggle"),
  tutorialAll: document.getElementById("tutorial-all"),
  tutorialDialog: document.getElementById("tutorial-dialog"),
  tutorialDialogClose: document.getElementById("tutorial-dialog-close"),
  tutorialDialogTitle: document.getElementById("tutorial-dialog-title"),
};

const state = {
  sessionId: null,
  rules: [],
  rulesByName: new Map(),
  playing: false,
  loopHandle: null,
  pendingTick: false,
  tutorialIdx: 0,
  currentParams: [],
  lastSummary: null,
  ctx: els.canvas.getContext("2d"),
};

async function api(method, path, body) {
  const opts = { method, headers: { "Content-Type": "application/json" } };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(path, opts);
  if (res.status === 204) return null;
  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch { /* not JSON */ }
  if (!res.ok) throw new Error((data && data.error) || text || res.statusText);
  return data;
}

function showError(msg) {
  if (!els.error) return;
  els.error.textContent = msg;
  els.error.hidden = false;
  // Auto-clear after a few seconds so transient errors don't linger.
  if (showError._timer) clearTimeout(showError._timer);
  showError._timer = setTimeout(() => { els.error.hidden = true; }, 6000);
}

function clearError() {
  if (!els.error) return;
  els.error.hidden = true;
  if (showError._timer) clearTimeout(showError._timer);
}

async function loadRules() {
  const data = await api("GET", "/api/rules");
  state.rules = data.rules;
  state.rulesByName = new Map(data.rules.map((r) => [r.name, r]));
  els.rule.innerHTML = "";
  for (const r of data.rules) {
    const opt = document.createElement("option");
    opt.value = r.name;
    opt.textContent = r.name;
    els.rule.appendChild(opt);
  }
  els.rule.value = "abiogenesis-pipeline";
}

function renderTutorial() {
  const r = state.rulesByName.get(els.rule.value);
  if (!r) return;
  if (state.tutorialIdx >= r.tutorial.length) state.tutorialIdx = 0;
  els.tutorialBody.textContent = r.tutorial[state.tutorialIdx] || "";
  els.tutorialCounter.textContent = `${state.tutorialIdx + 1}/${r.tutorial.length}`;
  els.tutorialPrev.disabled = state.tutorialIdx === 0;
  els.tutorialNext.disabled = state.tutorialIdx >= r.tutorial.length - 1;
  if (els.tutorialDialogTitle) els.tutorialDialogTitle.textContent = r.name;
  els.tutorialAll.innerHTML = "";
  for (const line of r.tutorial) {
    const li = document.createElement("li");
    li.textContent = line;
    els.tutorialAll.appendChild(li);
  }
}

function applySummary(s) {
  state.lastSummary = s;
  els.stepCount.textContent = s.step_count;
  els.fps.textContent = s.fps;
  els.seedOut.textContent = s.seed;
  renderPopulation(s.population);

  if (s.stage_info) {
    applyStageInfo(s.stage_info);
    populateStageControls(s.stage_info);
    showLegend(s.stage_info.legend);
    setStageTabVisible(true);
  } else {
    applyRuleInfo();
    setStageTabVisible(false);
    els.legend.hidden = true;
  }
}

function applyStageInfo(info) {
  // The wall-label shows the active stage's museum info.
  els.stageEyebrow.textContent = `Stage ${toRoman(info.current_stage)} · ${info.current_stage + 1} / ${info.total_stages}`;
  els.stageTitleText.textContent = niceTitle(info.title);
  els.stageCitationText.textContent = info.citation || "";
  els.stageDetailText.textContent = info.detail || info.principle || "";
}

function applyRuleInfo() {
  // For non-pipeline rules: the wall-label shows rule metadata sourced
  // from the tutorial copy (first line is the tagline, the rest is detail).
  const r = state.rulesByName.get(els.rule.value);
  if (!r) return;
  els.stageEyebrow.textContent = "Specimen";
  els.stageTitleText.textContent = prettifyRuleName(r.name);
  els.stageCitationText.textContent = "";
  els.stageDetailText.textContent = r.tutorial[0] || "";
}

function prettifyRuleName(slug) {
  // "abiogenesis-stage1-grayscott" → "Gray-Scott"
  // "conway" → "Conway's Life"
  // "wolfram1d" → "Wolfram 1D"
  // "natural-selection" → "Natural Selection"
  const map = {
    "conway": "Conway's Life",
    "wolfram1d": "Wolfram 1D",
    "natural-selection": "Natural Selection",
    "abiogenesis-pipeline": "Abiogenesis · Canonical",
    "abiogenesis-pipeline-extended": "Abiogenesis · Extended",
    "abiogenesis-stage0-soup": "Primordial Soup",
    "abiogenesis-stage1-grayscott": "Gray-Scott",
    "abiogenesis-stage2-raf": "Autocatalytic Sets",
    "abiogenesis-stage3-vesicles": "Vesicles",
    "abiogenesis-stage4-selection": "Protocell Selection",
    "abiogenesis-rna-world": "RNA World",
    "abiogenesis-homochirality": "Homochirality",
    "abiogenesis-hydrothermal-vent": "Hydrothermal Vent",
    "abiogenesis-coacervate": "Coacervate",
    "abiogenesis-mineral-catalysis": "Mineral Catalysis",
    "abiogenesis-genetic-code": "Genetic Code",
    "abiogenesis-luca": "LUCA",
  };
  return map[slug] || slug;
}

function toRoman(n) {
  const map = [
    [1000, "M"], [900, "CM"], [500, "D"], [400, "CD"],
    [100, "C"], [90, "XC"], [50, "L"], [40, "XL"],
    [10, "X"], [9, "IX"], [5, "V"], [4, "IV"], [1, "I"],
  ];
  if (n === 0) return "0";
  let s = "";
  for (const [v, sym] of map) {
    while (n >= v) { s += sym; n -= v; }
  }
  return s;
}

function niceTitle(s) {
  // Server emits museum-card uppercase ("PRIMORDIAL SOUP"). Sentence-case
  // it for the wall label so it reads as a title, not as a banner shout.
  const lower = String(s || "").toLowerCase();
  // Title-case each word, preserving hyphens.
  return lower.replace(/(^|[\s\-–—·])([a-z])/g, (m, sep, ch) => sep + ch.toUpperCase());
}

function setStageTabVisible(visible) {
  if (!els.stageTab) return;
  els.stageTab.hidden = !visible;
  // If the stage tab is hidden but currently active, snap back to params.
  if (!visible && els.stageTab.classList.contains("active")) {
    activateTab("params");
  }
}

function activateTab(name) {
  els.tabs.forEach((t) => {
    const on = t.dataset.tab === name;
    t.classList.toggle("active", on);
    t.setAttribute("aria-selected", on ? "true" : "false");
  });
  els.panes.forEach((p) => {
    const on = p.dataset.pane === name;
    p.classList.toggle("active", on);
    p.hidden = !on;
  });
}

function renderPopulation(pop) {
  // Render as wrap-friendly key:value chips instead of a single string;
  // rules like hydrothermal-vent emit 10+ stats and orphaned line breaks
  // in a single string read poorly.
  els.population.replaceChildren();
  if (!pop) return;
  const entries = Object.entries(pop);
  if (entries.length === 0) return;
  for (const [k, v] of entries) {
    const pair = document.createElement("span");
    pair.className = "pop-pair";
    const ks = document.createElement("span");
    ks.className = "pop-key";
    ks.textContent = `${k}:`;
    const vs = document.createElement("span");
    vs.className = "pop-val";
    vs.textContent = typeof v === "number" ? v.toLocaleString() : String(v);
    pair.append(ks, vs);
    els.population.append(pair);
  }
}

function populateStageControls(info) {
  // The stage tab itself is shown/hidden via setStageTabVisible; here we
  // just populate the form. Title-case so "PRIMORDIAL SOUP" reads as
  // "Primordial soup" — the server emits the museum-card uppercase form
  // for the banner; the dropdown looks calmer in sentence case.
  const niceTitle = (s) => {
    const lower = String(s || "").toLowerCase();
    return lower.charAt(0).toUpperCase() + lower.slice(1);
  };
  const stages =
    Array.isArray(info.stages) && info.stages.length
      ? info.stages
      : Array.from({ length: info.total_stages }, (_, i) => ({
          index: i,
          title: i === info.current_stage ? info.title : "",
        }));
  const want = stages.length;
  if (els.stageSelect.options.length !== want) {
    els.stageSelect.innerHTML = "";
    for (const s of stages) {
      const opt = document.createElement("option");
      opt.value = String(s.index);
      els.stageSelect.appendChild(opt);
    }
  }
  for (const opt of els.stageSelect.options) {
    const idx = Number(opt.value);
    const title = stages[idx] && stages[idx].title;
    opt.textContent = title ? `${idx} — ${niceTitle(title)}` : String(idx);
  }
  els.stageSelect.value = String(info.current_stage);
  els.autoPromote.checked = info.auto_promote;
  if (document.activeElement !== els.stageDuration) {
    els.stageDuration.value = String(info.stage_duration);
  }
}

function showLegend(text) {
  if (!text) {
    els.legend.hidden = true;
    return;
  }
  els.legend.hidden = false;
  els.legend.textContent = text;
}

async function paintFrame() {
  if (!state.sessionId) return;
  // Cache-bust each request so the browser fetches fresh frames every tick.
  const url = `/api/sessions/${state.sessionId}/frame.png?t=${Date.now()}`;
  const img = new Image();
  await new Promise((resolve, reject) => {
    img.onload = resolve;
    img.onerror = () => reject(new Error("frame load failed"));
    img.src = url;
  });
  const { ctx } = state;
  ctx.imageSmoothingEnabled = false;
  ctx.clearRect(0, 0, els.canvas.width, els.canvas.height);
  ctx.drawImage(img, 0, 0, els.canvas.width, els.canvas.height);
}

async function refreshParams() {
  if (!state.sessionId) return;
  let payload;
  try {
    payload = await api("GET", `/api/sessions/${state.sessionId}/params`);
  } catch (e) {
    console.error(e);
    return;
  }
  state.currentParams = payload.params;
  renderParamSliders(payload);
  renderPresets(payload);
  // Empty-state shown when the rule has neither sliders nor presets.
  if (els.paramsEmpty) {
    const hasParams = payload.params && payload.params.length > 0;
    const hasPresets = payload.presets && payload.presets.length > 0;
    els.paramsEmpty.hidden = hasParams || hasPresets;
  }
}

function renderParamSliders({ params }) {
  els.params.innerHTML = "";
  if (!params || params.length === 0) {
    els.paramsWrap.hidden = true;
    return;
  }
  els.paramsWrap.hidden = false;
  for (const p of params) {
    const row = document.createElement("div");
    row.className = "param-row" + (p.reinit ? " param-reinit" : "");

    const label = document.createElement("label");
    label.htmlFor = `p-${p.attr}`;
    label.innerHTML = `${p.label}${p.reinit ? ' <em title="changes restart the simulation">⟲</em>' : ""}`;

    const range = document.createElement("input");
    range.type = "range";
    range.id = `p-${p.attr}`;
    range.min = String(p.lo);
    range.max = String(p.hi);
    range.step = String(p.step);
    range.value = String(p.value);

    const display = document.createElement("span");
    display.className = "param-value";
    display.textContent = formatNum(p.value, p.step, p.integer);

    let timer = null;
    range.addEventListener("input", () => {
      display.textContent = formatNum(Number(range.value), p.step, p.integer);
      if (timer) clearTimeout(timer);
      // Debounce: structural ("reinit") params skip the user-is-still-dragging
      // window so we don't reset state on every pixel of slider travel.
      const debounce = p.reinit ? 250 : 60;
      timer = setTimeout(() => {
        applyParam(p.attr, Number(range.value));
      }, debounce);
    });

    row.appendChild(label);
    row.appendChild(range);
    row.appendChild(display);
    els.params.appendChild(row);
  }
}

function formatNum(value, step, integer) {
  if (integer) return String(Math.round(value));
  const decimals = step < 0.01 ? 4 : step < 0.1 ? 3 : 2;
  return Number(value).toFixed(decimals);
}

async function applyParam(attr, value) {
  if (!state.sessionId) return;
  try {
    const res = await api("POST", `/api/sessions/${state.sessionId}/params`, { [attr]: value });
    applySummary(res);
    // A reinit param rebuilds the inner state — repaint immediately so the
    // user sees the new initial conditions instead of the stale grid.
    if (res.reinit) await paintFrame();
  } catch (e) {
    console.error(e);
  }
}

function renderPresets({ presets }) {
  els.presets.innerHTML = "";
  if (!presets || presets.length === 0) {
    els.presetsWrap.hidden = true;
    return;
  }
  els.presetsWrap.hidden = false;
  for (const name of presets) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = name;
    btn.className = "chip";
    btn.addEventListener("click", () => applyPreset(name));
    els.presets.appendChild(btn);
  }
}

async function applyPreset(name) {
  if (!state.sessionId) return;
  try {
    const res = await api("POST", `/api/sessions/${state.sessionId}/preset`, { name });
    applySummary(res);
    await refreshParams();
    await paintFrame();
  } catch (e) {
    showError("Preset failed: " + e.message);
  }
}

async function promoteStage() {
  if (!state.sessionId) return;
  try {
    const res = await api("POST", `/api/sessions/${state.sessionId}/promote`);
    applySummary(res);
    await refreshParams();
    await paintFrame();
  } catch (e) {
    showError("Promote failed: " + e.message);
  }
}

async function jumpToStage(n) {
  if (!state.sessionId) return;
  try {
    const res = await api("POST", `/api/sessions/${state.sessionId}/stage`, { stage: Number(n) });
    applySummary(res);
    await refreshParams();
    await paintFrame();
  } catch (e) {
    showError("Stage change failed: " + e.message);
  }
}

async function setAutoPromote(enabled, duration) {
  if (!state.sessionId) return;
  const body = { enabled };
  if (duration !== undefined) body.duration = duration;
  try {
    const res = await api("POST", `/api/sessions/${state.sessionId}/auto_promote`, body);
    applySummary(res);
  } catch (e) {
    showError("Auto-promote change failed: " + e.message);
  }
}

async function createSession() {
  await stopLoop();
  const grid = Number(els.grid.value);
  if (!Number.isFinite(grid) || grid < 4 || grid > 240) {
    showError(`Grid must be between 4 and 240 (you entered ${els.grid.value || "—"}).`);
    return;
  }
  const body = { rule: els.rule.value, grid };
  const seedVal = els.seed.value.trim();
  if (seedVal !== "") {
    const seed = Number(seedVal);
    if (!Number.isFinite(seed)) {
      showError("Seed must be a number, or leave it blank for random.");
      return;
    }
    body.seed = seed;
  }
  clearError();

  let s;
  if (state.sessionId) {
    s = await api("POST", `/api/sessions/${state.sessionId}/reset`, body);
  } else {
    s = await api("POST", "/api/sessions", body);
    state.sessionId = s.session_id;
  }
  state.tutorialIdx = 0;
  applySummary(s);
  await refreshParams();
  await paintFrame();
  renderTutorial();
}

async function stepOnce(n = 1) {
  if (!state.sessionId) return;
  if (state.pendingTick) return; // drop if a tick is in flight
  state.pendingTick = true;
  try {
    const s = await api("POST", `/api/sessions/${state.sessionId}/step`, { n });
    applySummary(s);
    await paintFrame();
  } catch (e) {
    console.error(e);
    await stopLoop();
  } finally {
    state.pendingTick = false;
  }
}

// Honor OS-level reduced motion. Caps both the on-screen tick rate and
// the slider's effective max so the canvas doesn't strobe — addresses
// WCAG 2.2.2 / 2.3.3 for vestibular / photosensitive users.
const prefersReducedMotion = window.matchMedia
  ? window.matchMedia("(prefers-reduced-motion: reduce)").matches
  : false;

function effectiveHz() {
  let hz = Number(els.speed.value) || 20;
  if (prefersReducedMotion) hz = Math.min(hz, 10);
  return Math.max(1, hz);
}

function startLoop() {
  if (state.loopHandle) return;
  state.playing = true;
  setPlayingChrome(true);
  // Batch steps when the requested rate exceeds what a single
  // step→frame.png round-trip can sustain (~30 sps). At speed=60 we ask
  // the server for 2 steps then paint once, doubling effective throughput
  // without hammering the network. MAX_STEPS_PER_REQUEST on the server
  // is 50, so the batch is safely bounded.
  const tick = async () => {
    if (!state.playing) return;
    const hz = effectiveHz();
    const batch = Math.min(20, Math.max(1, Math.ceil(hz / 30)));
    const interval = Math.max(4, Math.round((1000 * batch) / hz));
    await stepOnce(batch);
    if (state.playing) state.loopHandle = setTimeout(tick, interval);
  };
  state.loopHandle = setTimeout(tick, 4);
}

async function stopLoop() {
  state.playing = false;
  if (state.loopHandle) {
    clearTimeout(state.loopHandle);
    state.loopHandle = null;
  }
  setPlayingChrome(false);
}

function setPlayingChrome(on) {
  // Centralise all the chrome that reflects playing/paused state.
  // The brand-mark pulses, the canvas vitrine gets a stronger glow,
  // the Play button label flips to Pause.
  els.play.classList.toggle("active", on);
  if (els.playIcon) els.playIcon.textContent = on ? "⏸" : "▶";
  if (els.playText) els.playText.textContent = on ? "pause" : "play";
  if (els.brandMark) els.brandMark.classList.toggle("playing", on);
  if (els.specimen) els.specimen.classList.toggle("playing", on);
}

async function downloadSnapshot() {
  if (!state.sessionId) return;
  // Fetch as a Blob so the browser uses our filename suggestion instead of
  // opening the JSON inline.
  const res = await fetch(`/api/sessions/${state.sessionId}/snapshot.json`);
  if (!res.ok) {
    showError("Snapshot download failed.");
    return;
  }
  const cd = res.headers.get("Content-Disposition") || "";
  const m = cd.match(/filename="([^"]+)"/);
  const blob = await res.blob();
  triggerDownload(blob, (m && m[1]) || "cellauto-snapshot.json");
}

async function loadSnapshot(file) {
  if (!file || !state.sessionId) return;
  let snapshot;
  try {
    snapshot = JSON.parse(await file.text());
  } catch (e) {
    showError("Not valid JSON: " + e.message);
    return;
  }
  try {
    const res = await api("POST", `/api/sessions/${state.sessionId}/load`, snapshot);
    // The new state may use a different rule — keep the UI in sync.
    els.rule.value = res.rule;
    els.grid.value = res.grid;
    state.tutorialIdx = 0;
    applySummary(res);
    await refreshParams();
    await paintFrame();
    renderTutorial();
  } catch (e) {
    showError("Snapshot load failed: " + e.message);
  } finally {
    els.loadSnapshot.value = "";
  }
}

async function downloadFramePng() {
  if (!state.sessionId) return;
  const res = await fetch(`/api/sessions/${state.sessionId}/frame.png?download=1`);
  if (!res.ok) {
    showError("Frame download failed.");
    return;
  }
  const cd = res.headers.get("Content-Disposition") || "";
  const m = cd.match(/filename="([^"]+)"/);
  const blob = await res.blob();
  triggerDownload(blob, (m && m[1]) || "cellauto-frame.png");
}

async function exportGif() {
  if (!state.sessionId) return;
  const steps = Number(els.gifSteps.value);
  const fps = Number(els.gifFps.value);
  els.exportStatus.textContent = `Rendering ${steps} frames…`;
  els.exportGif.disabled = true;
  await stopLoop();
  try {
    const res = await fetch(`/api/sessions/${state.sessionId}/gif`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ steps, fps, canvas: 480 }),
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || res.statusText);
    }
    const cd = res.headers.get("Content-Disposition") || "";
    const m = cd.match(/filename="([^"]+)"/);
    const blob = await res.blob();
    triggerDownload(blob, (m && m[1]) || "cellauto-export.gif");
    els.exportStatus.textContent = `Exported ${steps} frames @ ${fps} fps.`;
    // Refresh the summary — the engine advanced during export.
    const summary = await api("GET", `/api/sessions/${state.sessionId}`);
    applySummary(summary);
    await paintFrame();
  } catch (e) {
    els.exportStatus.textContent = "GIF export failed: " + e.message;
  } finally {
    els.exportGif.disabled = false;
  }
}

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function bindUI() {
  els.play.addEventListener("click", () => {
    if (state.playing) stopLoop();
    else startLoop();
  });
  els.step.addEventListener("click", () => {
    stopLoop();
    stepOnce(1);
  });
  els.reset.addEventListener("click", () => {
    createSession().catch((e) => showError("Reset failed: " + e.message));
  });
  els.rule.addEventListener("change", () => {
    state.tutorialIdx = 0;
    createSession().catch((e) => showError("Rule switch failed: " + e.message));
  });
  els.speed.addEventListener("input", () => {
    els.speedLabel.textContent = `${els.speed.value}/s`;
  });

  els.stageSelect.addEventListener("change", () => {
    jumpToStage(els.stageSelect.value);
  });
  els.promote.addEventListener("click", promoteStage);
  els.autoPromote.addEventListener("change", () => {
    setAutoPromote(els.autoPromote.checked);
  });
  els.stageDuration.addEventListener("change", () => {
    const d = Number(els.stageDuration.value);
    if (d > 0) setAutoPromote(els.autoPromote.checked, d);
  });

  els.downloadSnapshot.addEventListener("click", downloadSnapshot);
  els.loadSnapshot.addEventListener("change", () => loadSnapshot(els.loadSnapshot.files[0]));
  els.downloadPng.addEventListener("click", downloadFramePng);
  els.exportGif.addEventListener("click", exportGif);

  els.tutorialPrev.addEventListener("click", () => {
    if (state.tutorialIdx > 0) { state.tutorialIdx--; renderTutorial(); }
  });
  els.tutorialNext.addEventListener("click", () => {
    const r = state.rulesByName.get(els.rule.value);
    if (r && state.tutorialIdx < r.tutorial.length - 1) {
      state.tutorialIdx++;
      renderTutorial();
    }
  });
  els.tutorialToggle.addEventListener("click", () => {
    if (typeof els.tutorialDialog.showModal === "function") {
      els.tutorialDialog.showModal();
    } else {
      els.tutorialDialog.removeAttribute("hidden");
      els.tutorialDialog.setAttribute("open", "");
    }
  });
  els.tutorialDialogClose.addEventListener("click", () => {
    if (typeof els.tutorialDialog.close === "function") {
      els.tutorialDialog.close();
    } else {
      els.tutorialDialog.removeAttribute("open");
    }
  });

  // Tab switching
  els.tabs.forEach((t) => {
    t.addEventListener("click", () => activateTab(t.dataset.tab));
  });

  // Keyboard shortcuts — keep them out of input fields so typing doesn't
  // accidentally toggle play.
  document.addEventListener("keydown", (e) => {
    if (e.target.matches("input, select, textarea")) return;
    if (e.key === " ") { e.preventDefault(); els.play.click(); }
    else if (e.key === "s") { els.step.click(); }
    else if (e.key === "r") { els.reset.click(); }
    else if (e.key === "p" && !els.stageTab.hidden) { els.promote.click(); }
  });
}

async function init() {
  bindUI();
  try {
    await loadRules();
    await createSession();
  } catch (e) {
    showError("Init failed: " + e.message);
  }
}

init();
