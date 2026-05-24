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

  presetsWrap: document.getElementById("presets-wrap"),
  presets: document.getElementById("presets"),
  error: document.getElementById("error"),

  paramsWrap: document.getElementById("params-wrap"),
  params: document.getElementById("params"),

  stageWrap: document.getElementById("stage-wrap"),
  stageSelect: document.getElementById("stage-select"),
  promote: document.getElementById("promote"),
  autoPromote: document.getElementById("auto-promote"),
  stageDuration: document.getElementById("stage-duration"),

  stageBanner: document.getElementById("stage-banner"),
  stageBannerIndex: document.getElementById("stage-banner-index"),
  stageBannerTitle: document.getElementById("stage-banner-title"),
  stageBannerCitation: document.getElementById("stage-banner-citation"),

  downloadSnapshot: document.getElementById("download-snapshot"),
  loadSnapshot: document.getElementById("load-snapshot"),
  downloadPng: document.getElementById("download-png"),
  exportGif: document.getElementById("export-gif"),
  gifSteps: document.getElementById("gif-steps"),
  gifFps: document.getElementById("gif-fps"),
  exportStatus: document.getElementById("export-status"),

  tutorialTitle: document.getElementById("tutorial-title"),
  tutorialBody: document.getElementById("tutorial-body"),
  tutorialAll: document.getElementById("tutorial-all"),
  tutorialPrev: document.getElementById("tutorial-prev"),
  tutorialNext: document.getElementById("tutorial-next"),
  tutorialCounter: document.getElementById("tutorial-counter"),
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
  els.tutorialTitle.textContent = r.name;
  if (state.tutorialIdx >= r.tutorial.length) state.tutorialIdx = 0;
  els.tutorialBody.textContent = r.tutorial[state.tutorialIdx] || "";
  els.tutorialCounter.textContent = `${state.tutorialIdx + 1} / ${r.tutorial.length}`;
  els.tutorialPrev.disabled = state.tutorialIdx === 0;
  els.tutorialNext.disabled = state.tutorialIdx >= r.tutorial.length - 1;
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
    showStageBanner(s.stage_info);
    populateStageControls(s.stage_info);
    showLegend(s.stage_info.legend);
  } else {
    els.stageBanner.hidden = true;
    els.stageWrap.hidden = true;
    els.legend.hidden = true;
  }
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

function showStageBanner(info) {
  els.stageBanner.hidden = false;
  els.stageBannerIndex.textContent = `Stage ${info.current_stage} / ${info.total_stages - 1}`;
  els.stageBannerTitle.textContent = info.title;
  els.stageBannerCitation.textContent = info.citation;
}

function populateStageControls(info) {
  els.stageWrap.hidden = false;
  // Rebuild the stage dropdown when the pipeline changes length OR when
  // the current stage's name doesn't match what's already there (e.g.
  // switching from the 5-stage to the 12-stage extended pipeline).
  const want = info.total_stages;
  const have = els.stageSelect.options.length;
  if (have !== want) {
    els.stageSelect.innerHTML = "";
    for (let i = 0; i < want; i++) {
      const opt = document.createElement("option");
      opt.value = String(i);
      // Title is only available for the current stage; fill in once
      // selected — until then show index only. The current stage gets
      // the friendly name appended.
      opt.textContent = i === info.current_stage ? `${i} — ${info.title}` : String(i);
      els.stageSelect.appendChild(opt);
    }
  } else {
    // Refresh the label on whichever option is current so the dropdown
    // always shows the descriptive title.
    for (const opt of els.stageSelect.options) {
      const idx = Number(opt.value);
      opt.textContent = idx === info.current_stage ? `${idx} — ${info.title}` : String(idx);
    }
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
  els.play.textContent = "⏸ Pause";
  els.play.classList.add("active");
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
  els.play.textContent = "▶ Play";
  els.play.classList.remove("active");
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

  // Keyboard shortcuts — keep them out of input fields so typing doesn't
  // accidentally toggle play.
  document.addEventListener("keydown", (e) => {
    if (e.target.matches("input, select, textarea")) return;
    if (e.key === " ") { e.preventDefault(); els.play.click(); }
    else if (e.key === "s") { els.step.click(); }
    else if (e.key === "r") { els.reset.click(); }
    else if (e.key === "p") { els.promote.click(); }
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
