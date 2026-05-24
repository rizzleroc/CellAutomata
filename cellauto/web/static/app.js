// cellauto web client
//
// Drives the Flask backend: creates a session, ticks it on a timer, paints
// the returned PNG into the canvas. State lives on the server (so the
// existing Python rule code does all the science); this file is just the
// view + controls.

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
  tutorialTitle: document.getElementById("tutorial-title"),
  tutorialBody: document.getElementById("tutorial-body"),
};

const state = {
  sessionId: null,
  rules: [],
  rulesByName: new Map(),
  playing: false,
  loopHandle: null,
  pendingTick: false,
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
  renderTutorial();
}

function renderTutorial() {
  const r = state.rulesByName.get(els.rule.value);
  if (!r) return;
  els.tutorialTitle.textContent = r.name;
  els.tutorialBody.innerHTML = "";
  for (const line of r.tutorial) {
    const li = document.createElement("li");
    li.textContent = line;
    els.tutorialBody.appendChild(li);
  }
}

function applySummary(s) {
  els.stepCount.textContent = s.step_count;
  els.fps.textContent = s.fps;
  els.seedOut.textContent = s.seed;
  const pop = Object.entries(s.population)
    .map(([k, v]) => `${k}: ${typeof v === "number" ? v.toLocaleString() : v}`)
    .join("   ");
  els.population.textContent = pop || "(no population stats for this rule)";
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

async function createSession() {
  await stopLoop();
  const body = {
    rule: els.rule.value,
    grid: Number(els.grid.value),
  };
  const seedVal = els.seed.value.trim();
  if (seedVal !== "") body.seed = Number(seedVal);

  let s;
  if (state.sessionId) {
    s = await api("POST", `/api/sessions/${state.sessionId}/reset`, body);
  } else {
    s = await api("POST", "/api/sessions", body);
    state.sessionId = s.session_id;
  }
  applySummary(s);
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

function startLoop() {
  if (state.loopHandle) return;
  state.playing = true;
  els.play.textContent = "⏸ Pause";
  els.play.classList.add("active");
  const hzToInterval = () => Math.max(16, Math.round(1000 / Number(els.speed.value)));
  const tick = async () => {
    if (!state.playing) return;
    await stepOnce(1);
    state.loopHandle = setTimeout(tick, hzToInterval());
  };
  state.loopHandle = setTimeout(tick, hzToInterval());
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
    createSession().catch((e) => alert("reset failed: " + e.message));
  });
  els.rule.addEventListener("change", () => {
    renderTutorial();
    createSession().catch((e) => alert("rule switch failed: " + e.message));
  });
  els.speed.addEventListener("input", () => {
    els.speedLabel.textContent = `${els.speed.value}/s`;
  });
}

async function init() {
  bindUI();
  try {
    await loadRules();
    await createSession();
  } catch (e) {
    alert("init failed: " + e.message);
  }
}

init();
