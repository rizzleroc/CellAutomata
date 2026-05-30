// cellauto web 2.0 — main controller.
//
// Drives whichever rule the user has selected: holds the RAF loop, manages
// the ImageData blit, syncs sliders/checkboxes/buttons to the rule's
// `params` table, owns brush painting, owns URL-hash state, owns the
// FPS/gen/pop readout bar.
//
// Each rule is a tiny object registered on `CA.RULES`. The contract is
// documented at the bottom of this file.
(function () {
  "use strict";

  const RULE_ORDER = [
    "conway", "wolfram1d", "grayscott", "soup",
    "natural-selection", "chirality", "coacervate", "vents",
  ];

  // ── Per-rule marginalia ticker copy ─────────────────────────────────────
  // Short notes cycled in the marginalia section every MARGINALIA_INTERVAL_MS.
  // Mirrors the "chapter-card" mechanism described in the v4.0 PRD §5.
  // Each rule's ticker starts with a P0-A3 BUILDING-BLOCK CLAIM card
  // (terse: "this shows X, and it matters because Y"), then cycles through
  // the citation / context cards.  The claim is distinct from the
  // persistent `whatThisIs` line under the formula caption — A1 explains,
  // A3 stakes the claim.
  const MARGINALIA = {
    conway: [
      "BUILDING-BLOCK CLAIM. Off-arc reference automaton — not a building block of life. Included so anyone can sanity-check the engine against the CA everyone already knows.",
      "Conway's Game of Life — Gardner, M. (1970). \"The fantastic combinations of John Conway's new solitaire game 'life'.\" Scientific American.",
      "B3/S23: a dead cell with exactly three live neighbours is born; a live cell with two or three lives on. Every other state dies.",
      "Universal computation — Berlekamp, Conway and Guy (1982) sketch a way to encode a Turing machine in gliders. Life is decidable in principle.",
      "Paint with the mouse to seed a still life or a glider. Right-click to erase. \"r\" reseeds at the current density.",
    ],
    wolfram1d: [
      "BUILDING-BLOCK CLAIM. Off-arc reference automaton — not a building block of life. Sets the lower bound on \"how little machinery do you need to compute anything?\" — Rule 110 is Turing-complete on three input bits.",
      "Wolfram, S. (2002). A New Kind of Science. The 256 elementary one-dimensional rules partition into four classes.",
      "Rule 30 generates the column-1 sequence used in Mathematica's pseudo-random generator — chaotic class 3 behaviour.",
      "Rule 110 was proved Turing-complete — Cook, M. (2004). Universality in elementary cellular automata. Complex Systems 15:1.",
      "History scrolls upward; the bottom row is the current generation. Paint on it to perturb the seed.",
    ],
    grayscott: [
      "BUILDING-BLOCK CLAIM. This shows that pure chemistry — no genes, no cells, no rules beyond two ODE terms — can produce structures that grow, divide, and replicate. The building block: pattern.",
      "Turing, A. M. (1952). \"The chemical basis of morphogenesis.\" Phil. Trans. R. Soc. B 237:37 — the founding paper of reaction–diffusion biology.",
      "Pearson, J. E. (1993). \"Complex patterns in a simple system.\" Science 261:189 — the (F, k) parameter map this slider lives inside.",
      "Self-replicating spots are not designed; they emerge from a four-parameter PDE with no notion of \"cell\" in its equations.",
      "Try the mitosis preset (F=0.0367, k=0.0649) — each spot splits into two, then four, then eight, in finite time.",
    ],
    soup: [
      "BUILDING-BLOCK CLAIM. This shows chemistry without organisation — the starting condition for every downstream rule. The building block: matter, undirected.",
      "Oparin (1924) and Haldane (1929) — the \"primordial soup\" hypothesis: simple organics + energy → diversifying chemistry.",
      "Each tracer here is a Brownian particle, dx = √(2D·dt)·N(0,1). The trail field is the time-integrated occupancy.",
      "Six \"species\" colour-tag the tracers — a stand-in for the actual chemical diversity of Stage 0 in the Python build.",
      "Inject more matter with the brush. Tune diffusion D and drift; raise evaporation to thin the trail field.",
    ],
    "natural-selection": [
      "BUILDING-BLOCK CLAIM. This shows the first hint of compartments emerging from random mixing. Without compartments there's no individual to be selected, no inside vs outside, no life. The building block: identity.",
      "Miller, S. L. (1953). \"A production of amino acids under possible primitive Earth conditions.\" Science 117:528.",
      "Sixteen species — the Miller-Urey product mix, weighted by reported yields. Formic acid dominates; glycine, glycolic acid, alanine follow.",
      "Rule 1 mixes neighbouring colours (diffusion). Rule 2 lets same-species \"new\" pairs combine into amoebas — the first compartmentalisation.",
      "Amoebas age and die; the soup never freezes. Paint with the brush to inject a fresh patch of new chemistry.",
    ],
    chirality: [
      "BUILDING-BLOCK CLAIM. This shows how a racemic 50/50 mixture spontaneously picks a single handedness. The building block: symmetry-breaking. Without it, biology's L-amino-acid / D-sugar preference has no chemical basis.",
      "Frank, F. C. (1953). \"On spontaneous asymmetric synthesis.\" Biochim. Biophys. Acta 11:459 — autocatalysis + mutual inhibition → racemic instability.",
      "Real proteins are L-amino-acid only; real RNA is D-ribose only. Why? The Frank kinetics here are the canonical mathematical answer.",
      "The mirror symmetry of the soup is broken by a single noise kick; once one enantiomer is ahead, β·L·R amplifies the lead.",
      "Paint to inject pure L or R locally and watch the front advance into the racemic substrate.",
    ],
    coacervate: [
      "BUILDING-BLOCK CLAIM. This shows membrane-less proto-cells forming by phase separation — concentrated chemistry pulling away from a dilute background. The building block: confinement without yet inventing membranes.",
      "Oparin (1924) proposed coacervate droplets as proto-cells. Banani et al. (2017) showed modern cells use the same physics — liquid–liquid phase separation.",
      "Cahn-Hilliard: ∂φ/∂t = M ∇²(φ³ − φ − κ ∇²φ). The φ³ − φ term is the free-energy double-well; κ ∇²φ is the surface tension.",
      "Spinodal decomposition first, coarsening second — droplets grow by absorbing their neighbours, area scaling like t^(1/3).",
      "Paint a droplet seed to bias the steady-state; the system finds its own balance from any initial condition.",
    ],
    vents: [
      "BUILDING-BLOCK CLAIM. This shows the geological setting that combines free compartments (porous mineral walls) and free energy (a pH gradient) — the plausible substrate on which Stages 1–9 unfold. The building block: a place + a power source.",
      "Russell & Hall (1997), Martin & Russell (2003), Lane (2009) — alkaline hydrothermal vents as the energetically plausible origin site.",
      "The chimney's pH gradient + porous mineral honeycomb gives free energy + spatial compartmentalisation, the two preconditions for chemistry-to-life.",
      "Acetate is the canonical product of the abiotic acetyl-CoA pathway — the first carbon-fixation cycle the engine simulates here.",
      "The plume rises by drift and diffuses laterally; the mineral wall both confines it and seeds further reactions.",
    ],
  };

  const MARGINALIA_INTERVAL_MS = 6500;

  // SEM scale-bar microcopy per rule (the simulation is abstract — these
  // are stage-appropriate units, not physical SI).
  const SCALE_BAR_UNITS = {
    conway:               "10 cells",
    wolfram1d:            "16 cells",
    grayscott:            "1 μm",
    soup:                 "1 μm",
    "natural-selection":  "10 μm",
    chirality:            "1 μm",
    coacervate:           "5 μm",
    vents:                "10 μm",
  };

  // ── DOM refs ────────────────────────────────────────────────────────────
  const canvas        = document.getElementById("ca-canvas");
  const ctx           = canvas.getContext("2d");
  const ruleSelect    = document.getElementById("rule-select");
  const speedSlider   = document.getElementById("speed-slider");
  const speedReadout  = document.getElementById("speed-readout");
  const brushSlider   = document.getElementById("brush-slider");
  const brushReadout  = document.getElementById("brush-readout");
  const semCheckbox   = document.getElementById("sem-mode");
  const paletteSelect = document.getElementById("palette-select");
  const ruleControls  = document.getElementById("rule-controls");
  const playBtn       = document.getElementById("btn-play");
  const stopBtn       = document.getElementById("btn-stop");
  const stepBtn       = document.getElementById("btn-step");
  const resetBtn      = document.getElementById("btn-reset");
  const clearBtn      = document.getElementById("btn-clear");
  const randomBtn     = document.getElementById("btn-random");
  const shareBtn      = document.getElementById("btn-share");
  const fullBtn       = document.getElementById("btn-full");
  const rdRule        = document.getElementById("rd-rule");
  const rdGen         = document.getElementById("rd-gen");
  const rdPop         = document.getElementById("rd-pop");
  const rdFps         = document.getElementById("rd-fps");
  const captionEl     = document.getElementById("stage-caption");
  const detailEl      = document.getElementById("stage-detail");
  const toastEl       = document.getElementById("toast");
  const badgeTextEl   = document.querySelector(".sem-badge-text");
  const scaleBarText  = document.getElementById("scale-bar-text");
  const marginaliaEl  = document.getElementById("marginalia");
  const whatThisIsEl  = document.getElementById("what-this-is");
  const controlHintEl = document.getElementById("control-hint");
  const bodyEl        = document.body;

  // ── State ───────────────────────────────────────────────────────────────
  let currentRule = null;
  let imageData   = null;
  let heightBuf   = null;    // Float32Array reused for SEM height field
  let running     = false;
  let rafHandle   = 0;
  let lastStep    = 0;       // ms timestamp of last simulation step
  let stepsPerSec = 30;
  let brushRadius = 5;
  let fpsSamples  = [];      // ring of last frame timestamps for FPS
  let semMode     = true;    // v4.0 default-on
  let palette     = "warm-sepia";
  let marginaliaTimer = 0;
  let marginaliaIdx   = 0;

  // ── Rule dropdown ───────────────────────────────────────────────────────
  for (const id of RULE_ORDER) {
    if (!CA.RULES[id]) continue;
    const r = CA.RULES[id]();   // peek at label
    const opt = document.createElement("option");
    opt.value = id;
    opt.textContent = r.label;
    ruleSelect.appendChild(opt);
  }

  // ── Rule swap ───────────────────────────────────────────────────────────
  function setRule(id, paramsOverride) {
    if (!CA.RULES[id]) {
      console.warn("Unknown rule:", id);
      id = RULE_ORDER[0];
    }
    currentRule = CA.RULES[id]();
    ruleSelect.value = id;
    if (paramsOverride) {
      for (const k of Object.keys(paramsOverride)) {
        if (currentRule.params[k]) {
          const want = paramsOverride[k];
          const slot = currentRule.params[k];
          if (slot.type === "bool") {
            // From URL, `want` is the string "true"/"false"; coerce
            // properly. From a fresh-object override it'd be a bool.
            slot.value = (typeof want === "string") ? (want === "true") : !!want;
          } else if (slot.type === "enum") {
            slot.value = String(want);
          } else {
            slot.value = Number(want);
          }
        }
      }
      if (typeof currentRule.onParamChange === "function") {
        for (const k of Object.keys(paramsOverride)) {
          currentRule.onParamChange(k);
        }
      }
    }
    // Size the canvas + ImageData to the rule's native grid.
    canvas.width  = currentRule.width;
    canvas.height = currentRule.height;
    imageData = ctx.createImageData(currentRule.width, currentRule.height);
    heightBuf = new Float32Array(currentRule.width * currentRule.height);

    rebuildRuleControls();
    currentRule.reset();
    captionEl.textContent = currentRule.shortCaption;
    detailEl.textContent  = currentRule.formula;
    rdRule.textContent    = id;
    if (whatThisIsEl) {
      whatThisIsEl.textContent = currentRule.whatThisIs || "";
    }
    showFirstControlHint();
    if (badgeTextEl) {
      badgeTextEl.textContent = "LIVE SEM FEED · " + currentRule.shortCaption;
    }
    if (scaleBarText) {
      scaleBarText.textContent = SCALE_BAR_UNITS[id] || "1 unit";
    }
    resetMarginalia(id);
    render();
    refreshReadouts();
    writeUrlState();
  }

  // Initial control-hint = the consequence sentence for the first param.
  function showFirstControlHint() {
    if (!controlHintEl || !currentRule) return;
    const params = currentRule.params || {};
    const cc = currentRule.controlConsequence || {};
    const firstName = Object.keys(params)[0];
    controlHintEl.textContent = (firstName && cc[firstName]) || "";
  }

  function setControlHint(paramName) {
    if (!controlHintEl || !currentRule) return;
    const cc = currentRule.controlConsequence || {};
    controlHintEl.textContent = cc[paramName] || "";
  }

  function rebuildRuleControls() {
    ruleControls.innerHTML = "";
    if (!currentRule.params) return;
    for (const [name, slot] of Object.entries(currentRule.params)) {
      const row = document.createElement("div");
      row.className = "control-row";

      const label = document.createElement("label");
      label.className = "ctl-label";
      label.textContent = slot.label || name;
      row.appendChild(label);

      let input, readout;
      if (slot.type === "bool") {
        input = document.createElement("input");
        input.type = "checkbox";
        input.checked = !!slot.value;
        input.style.flex = "1";
        input.addEventListener("change", () => {
          slot.value = input.checked;
          if (currentRule.onParamChange) currentRule.onParamChange(name);
          writeUrlState();
        });
        row.appendChild(input);
      } else if (slot.type === "enum") {
        input = document.createElement("select");
        input.className = "select";
        if (!slot.options.includes("")) {
          // Allow "custom" sentinel for presets that get modified.
          const blank = document.createElement("option");
          blank.value = ""; blank.textContent = "— custom —";
          input.appendChild(blank);
        }
        for (const opt of slot.options) {
          const o = document.createElement("option");
          o.value = opt; o.textContent = opt;
          input.appendChild(o);
        }
        input.value = slot.value;
        input.addEventListener("change", () => {
          slot.value = input.value;
          if (currentRule.onParamChange) currentRule.onParamChange(name);
          syncRuleControlsToParams();
          writeUrlState();
        });
        row.appendChild(input);
      } else {
        // numeric slider
        input = document.createElement("input");
        input.type = "range";
        input.className = "slider";
        input.min  = slot.min;
        input.max  = slot.max;
        input.step = slot.step;
        input.value = slot.value;
        readout = document.createElement("span");
        readout.className = "readout";
        readout.textContent = formatNum(slot.value, slot.step);
        input.addEventListener("input", () => {
          slot.value = parseFloat(input.value);
          readout.textContent = formatNum(slot.value, slot.step);
          if (currentRule.onParamChange) currentRule.onParamChange(name);
          syncRuleControlsToParams();
          writeUrlState();
        });
        row.appendChild(input);
        row.appendChild(readout);
      }

      // P0-G2: focus/hover/interact on this control → control-hint
      // line shows what the knob does to the biology.
      const hint = () => setControlHint(name);
      input.addEventListener("focus", hint);
      input.addEventListener("input", hint);
      input.addEventListener("change", hint);
      row.addEventListener("mouseenter", hint);

      // Stash refs so syncRuleControlsToParams() can update bidirectionally.
      row.dataset.param = name;
      ruleControls.appendChild(row);
    }
  }

  // Reflect param changes (made by onParamChange) back into DOM widgets.
  function syncRuleControlsToParams() {
    if (!currentRule.params) return;
    for (const row of ruleControls.children) {
      const name = row.dataset.param;
      const slot = currentRule.params[name];
      if (!slot) continue;
      const w = row.querySelector("input, select");
      if (!w) continue;
      if (slot.type === "bool") {
        w.checked = !!slot.value;
      } else if (slot.type === "enum") {
        w.value = slot.value || "";
      } else {
        const newVal = String(slot.value);
        if (w.value !== newVal) {
          w.value = newVal;
          const ro = row.querySelector(".readout");
          if (ro) ro.textContent = formatNum(slot.value, slot.step);
        }
      }
    }
  }

  function formatNum(v, step) {
    const s = String(step);
    const dot = s.indexOf(".");
    const decimals = dot < 0 ? 0 : (s.length - dot - 1);
    return Number(v).toFixed(decimals);
  }

  // ── Loop ────────────────────────────────────────────────────────────────
  function tick(now) {
    if (!running) return;
    const interval = 1000 / stepsPerSec;
    if (!lastStep) lastStep = now;
    let advanced = false;
    // Catch up at most a few steps per frame to keep things responsive.
    let safety = 4;
    while (now - lastStep >= interval && safety-- > 0) {
      currentRule.step();
      lastStep += interval;
      advanced = true;
    }
    if (advanced) {
      render();
      recordFps(now);
      refreshReadouts();
    }
    rafHandle = requestAnimationFrame(tick);
  }

  function recordFps(now) {
    fpsSamples.push(now);
    const cutoff = now - 1000;
    while (fpsSamples.length && fpsSamples[0] < cutoff) fpsSamples.shift();
    rdFps.textContent = String(fpsSamples.length);
  }

  function render() {
    if (semMode && typeof currentRule.renderHeight === "function" && window.SEM) {
      currentRule.renderHeight(heightBuf);
      SEM.render(heightBuf, currentRule.width, currentRule.height,
                 imageData.data, { palette });
    } else {
      currentRule.render(imageData.data);
    }
    ctx.putImageData(imageData, 0, 0);
  }

  // ── Marginalia ticker ──────────────────────────────────────────────────
  function resetMarginalia(ruleId) {
    clearInterval(marginaliaTimer);
    marginaliaIdx = 0;
    const notes = MARGINALIA[ruleId] || [];
    if (!notes.length) {
      marginaliaEl.textContent = "";
      return;
    }
    marginaliaEl.textContent = notes[0];
    marginaliaTimer = setInterval(() => advanceMarginalia(ruleId), MARGINALIA_INTERVAL_MS);
  }

  function advanceMarginalia(ruleId) {
    const notes = MARGINALIA[ruleId] || [];
    if (notes.length < 2) return;
    // Respect prefers-reduced-motion — no fade, just a swap.
    const reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) {
      marginaliaIdx = (marginaliaIdx + 1) % notes.length;
      marginaliaEl.textContent = notes[marginaliaIdx];
      return;
    }
    marginaliaEl.classList.add("fading");
    setTimeout(() => {
      marginaliaIdx = (marginaliaIdx + 1) % notes.length;
      marginaliaEl.textContent = notes[marginaliaIdx];
      marginaliaEl.classList.remove("fading");
    }, 400);
  }

  function refreshReadouts() {
    rdGen.textContent = String(currentRule.generation());
    rdPop.textContent = currentRule.population();
  }

  function play() {
    if (running) return;
    running = true;
    lastStep = 0;
    fpsSamples = [];
    playBtn.disabled = true;
    stopBtn.disabled = false;
    stepBtn.disabled = true;
    rafHandle = requestAnimationFrame(tick);
  }
  function stop() {
    running = false;
    cancelAnimationFrame(rafHandle);
    playBtn.disabled = false;
    stopBtn.disabled = true;
    stepBtn.disabled = false;
    rdFps.textContent = "0";
  }

  // ── Brush painting ──────────────────────────────────────────────────────
  let painting = false;
  let paintMode = "draw";

  function canvasToGrid(ev) {
    const rect = canvas.getBoundingClientRect();
    const point = ev.touches && ev.touches[0] ? ev.touches[0] : ev;
    const px = (point.clientX - rect.left) / rect.width;
    const py = (point.clientY - rect.top) / rect.height;
    const gx = Math.max(0, Math.min(currentRule.width  - 1, (px * currentRule.width)  | 0));
    const gy = Math.max(0, Math.min(currentRule.height - 1, (py * currentRule.height) | 0));
    return [gx, gy];
  }

  function paintAt(ev) {
    const [gx, gy] = canvasToGrid(ev);
    currentRule.paint(gx, gy, brushRadius, paintMode);
    render();
    refreshReadouts();
  }

  canvas.addEventListener("mousedown", (ev) => {
    ev.preventDefault();
    painting = true;
    paintMode = (ev.button === 2 || ev.shiftKey || ev.altKey) ? "erase" : "draw";
    paintAt(ev);
  });
  canvas.addEventListener("mousemove", (ev) => {
    if (painting) paintAt(ev);
  });
  window.addEventListener("mouseup", () => { painting = false; });
  canvas.addEventListener("contextmenu", (ev) => ev.preventDefault());

  // Touch.
  canvas.addEventListener("touchstart", (ev) => {
    ev.preventDefault();
    painting = true;
    paintMode = "draw";
    paintAt(ev);
  }, { passive: false });
  canvas.addEventListener("touchmove", (ev) => {
    ev.preventDefault();
    if (painting) paintAt(ev);
  }, { passive: false });
  canvas.addEventListener("touchend", () => { painting = false; });

  // ── Buttons ─────────────────────────────────────────────────────────────
  playBtn.addEventListener("click", play);
  stopBtn.addEventListener("click", stop);
  stepBtn.addEventListener("click", () => {
    currentRule.step();
    render();
    refreshReadouts();
  });
  resetBtn.addEventListener("click", () => {
    currentRule.reset();
    render();
    refreshReadouts();
    toast("reset");
  });
  clearBtn.addEventListener("click", () => {
    currentRule.clear();
    render();
    refreshReadouts();
    toast("cleared");
  });
  randomBtn.addEventListener("click", () => {
    currentRule.randomize();
    render();
    refreshReadouts();
    toast("randomized");
  });
  shareBtn.addEventListener("click", async () => {
    writeUrlState();
    const url = window.location.href;
    try {
      await navigator.clipboard.writeText(url);
      toast("link copied");
    } catch {
      toast("copy failed — select the URL bar");
    }
  });
  fullBtn.addEventListener("click", () => {
    if (document.fullscreenElement) {
      document.exitFullscreen();
    } else if (canvas.requestFullscreen) {
      canvas.requestFullscreen().catch(() => toast("fullscreen denied"));
    }
  });

  ruleSelect.addEventListener("change", () => setRule(ruleSelect.value));

  // SEM mode toggle (v4.0 F7).
  if (semCheckbox) {
    semCheckbox.addEventListener("change", () => {
      semMode = semCheckbox.checked;
      bodyEl.dataset.sem = semMode ? "on" : "off";
      render();
      writeUrlState();
      toast(semMode ? "sem mode on" : "sem mode off");
    });
  }
  // SEM palette picker.
  if (paletteSelect) {
    paletteSelect.addEventListener("change", () => {
      palette = paletteSelect.value;
      bodyEl.dataset.palette = palette;
      render();
      writeUrlState();
    });
  }

  speedSlider.addEventListener("input", () => {
    stepsPerSec = parseInt(speedSlider.value, 10) || 1;
    speedReadout.textContent = String(stepsPerSec);
    lastStep = 0;
  });
  brushSlider.addEventListener("input", () => {
    brushRadius = parseInt(brushSlider.value, 10) || 1;
    brushReadout.textContent = String(brushRadius);
  });

  // ── Keyboard ────────────────────────────────────────────────────────────
  window.addEventListener("keydown", (ev) => {
    const tag = (document.activeElement && document.activeElement.tagName) || "";
    if (tag === "INPUT" || tag === "SELECT" || tag === "TEXTAREA") return;
    switch (ev.code) {
      case "Space":
        ev.preventDefault();
        running ? stop() : play();
        break;
      case "KeyS": stepBtn.click(); break;
      case "KeyR": resetBtn.click(); break;
      case "KeyC": clearBtn.click(); break;
      case "KeyN": randomBtn.click(); break;
      case "Digit1": setRule(RULE_ORDER[0]); break;
      case "Digit2": setRule(RULE_ORDER[1]); break;
      case "Digit3": setRule(RULE_ORDER[2]); break;
      case "Digit4": setRule(RULE_ORDER[3]); break;
      case "Digit5": if (RULE_ORDER[4]) setRule(RULE_ORDER[4]); break;
      case "Digit6": if (RULE_ORDER[5]) setRule(RULE_ORDER[5]); break;
      case "Digit7": if (RULE_ORDER[6]) setRule(RULE_ORDER[6]); break;
      case "Digit8": if (RULE_ORDER[7]) setRule(RULE_ORDER[7]); break;
      case "KeyM":
        if (semCheckbox) {
          semCheckbox.checked = !semCheckbox.checked;
          semCheckbox.dispatchEvent(new Event("change"));
        }
        break;
      case "KeyP":
        if (paletteSelect) {
          const names = SEM.paletteNames();
          const i = (names.indexOf(palette) + 1) % names.length;
          paletteSelect.value = names[i];
          paletteSelect.dispatchEvent(new Event("change"));
        }
        break;
    }
  });

  // ── URL state ───────────────────────────────────────────────────────────
  function readUrlState() {
    const hash = window.location.hash.replace(/^#/, "");
    if (!hash) return null;
    const out = { rule: null, params: {} };
    for (const part of hash.split("&")) {
      const [k, v] = part.split("=");
      if (!k) continue;
      const key = decodeURIComponent(k);
      const val = decodeURIComponent(v || "");
      if (key === "rule") out.rule = val;
      else out.params[key] = val;
    }
    return out;
  }

  function writeUrlState() {
    if (!currentRule) return;
    const parts = ["rule=" + encodeURIComponent(currentRule.id)];
    parts.push("sem=" + (semMode ? "1" : "0"));
    parts.push("palette=" + encodeURIComponent(palette));
    for (const [name, slot] of Object.entries(currentRule.params || {})) {
      parts.push(encodeURIComponent(name) + "=" + encodeURIComponent(String(slot.value)));
    }
    const next = "#" + parts.join("&");
    if (next !== window.location.hash) {
      // Replace, don't push, so the back button doesn't churn.
      history.replaceState(null, "", next);
    }
  }

  // ── Toast ───────────────────────────────────────────────────────────────
  let toastTimer = 0;
  function toast(msg) {
    toastEl.textContent = msg;
    toastEl.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toastEl.classList.remove("show"), 1400);
  }

  // ── Boot ────────────────────────────────────────────────────────────────
  stepsPerSec = parseInt(speedSlider.value, 10);
  brushRadius = parseInt(brushSlider.value, 10);
  speedReadout.textContent = String(stepsPerSec);
  brushReadout.textContent = String(brushRadius);

  const fromUrl = readUrlState();
  if (fromUrl && fromUrl.params) {
    if (fromUrl.params.sem !== undefined) {
      semMode = fromUrl.params.sem === "1";
      if (semCheckbox) semCheckbox.checked = semMode;
      delete fromUrl.params.sem;
    }
    if (fromUrl.params.palette !== undefined && SEM && SEM.PALETTES[fromUrl.params.palette]) {
      palette = fromUrl.params.palette;
      if (paletteSelect) paletteSelect.value = palette;
      delete fromUrl.params.palette;
    }
  }
  bodyEl.dataset.sem = semMode ? "on" : "off";
  bodyEl.dataset.palette = palette;
  const bootId = (fromUrl && fromUrl.rule && CA.RULES[fromUrl.rule]) ? fromUrl.rule : "grayscott";
  setRule(bootId, fromUrl ? fromUrl.params : null);
  play();

  // ── Rule contract ───────────────────────────────────────────────────────
  // A rule registered on CA.RULES is a zero-arg factory returning an object
  // with these fields:
  //
  //   id, label, formula, shortCaption  — display strings.
  //   width, height                     — native grid size in cells; the
  //                                       <canvas> is resized to match and
  //                                       drawn 1:1 via putImageData.
  //   params: { name: slot, ... }       — slot is one of:
  //       { label, min, max, step, value }            — numeric slider
  //       { label, type:"bool",  value }              — checkbox
  //       { label, type:"enum",  options:[…], value } — dropdown
  //   onParamChange?(name)              — optional hook for cross-param
  //                                       coupling (e.g. preset → F,k).
  //   step()                            — advance the simulation by one
  //                                       semantic "tick" (rules can fold
  //                                       multiple PDE substeps into one).
  //   render(pixels: Uint8ClampedArray) — write RGBA into the ImageData
  //                                       buffer of size width·height·4.
  //   reset(), clear(), randomize()     — three named initial conditions.
  //   paint(gx, gy, radius, mode)       — apply a brush stroke;
  //                                       mode ∈ "draw" | "erase".
  //   population() → string             — live readout summary.
  //   generation() → number             — tick counter for the readout.
})();
