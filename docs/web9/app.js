/* web9 — SEM viewer, Unreal Engine 5.8 powered.
   - hero  : a dividing protocell (parametric cleavage matching the real 3D arc)
   - lab   : the REAL grayscott.js engine, rendered as an SEM (height field ->
             Unreal membrane material / classic sepia-mono / flat)
   - proof : count-up metrics
   - bridge: the Unreal 5.8 render-API contract (stub / simulate mode)         */
(function () {
  "use strict";

  // shared hero controller (slider + play + rotate); both the 3D and 2D heroes read it
  window.heroState = { playing: true, rotate: true, scrub: 0, zoom: 1.6 };
  (function heroControls() {
    var sl = document.getElementById("hdiv"), pl = document.getElementById("hplay"), rt = document.getElementById("hrot");
    if (!sl) return;
    sl.addEventListener("input", function () { window.heroState.playing = false; window.heroState.scrub = (+sl.value) / 100; if (pl) pl.textContent = "play"; });
    if (pl) pl.onclick = function () { window.heroState.playing = !window.heroState.playing; pl.textContent = window.heroState.playing ? "pause" : "play"; };
    if (rt) rt.onclick = function () { window.heroState.rotate = !window.heroState.rotate; rt.classList.toggle("on", window.heroState.rotate); };
    var zm = document.getElementById("hzoom");
    function zoomFromSlider(v) { return 0.005 * Math.pow(800, v / 1000); }    // 0.005x .. 4x, log
    if (zm) { window.heroState.zoom = zoomFromSlider(+zm.value); zm.addEventListener("input", function () { window.heroState.zoom = zoomFromSlider(+zm.value); }); }
    (function sync() { if (window.heroState.playing && sl && document.activeElement !== sl) sl.value = Math.round(window.heroState.scrub * 100); requestAnimationFrame(sync); })();
  })();

  // ======================= HERO: dividing protocell =======================
  (function hero() {
    var vp = document.getElementById("hero");
    if (!vp) return;
    var ctx = vp.getContext("2d");
    var W = vp.width, H = vp.height;
    var GW = 150, GH = 150;
    var oc = document.createElement("canvas"); oc.width = GW; oc.height = GH;
    var octx = oc.getContext("2d"); var img = octx.createImageData(GW, GH);

    var NS = 64, noise = new Float32Array(NS * NS), s = 2025;
    for (var i = 0; i < noise.length; i++) { s = (s * 1103515245 + 12345) & 0x7fffffff; noise[i] = s / 0x7fffffff; }
    function vn(x, y) {
      x = ((x % NS) + NS) % NS; y = ((y % NS) + NS) % NS;
      var x0 = Math.floor(x), y0 = Math.floor(y), x1 = (x0 + 1) % NS, y1 = (y0 + 1) % NS, fx = x - x0, fy = y - y0;
      var a = noise[y0 * NS + x0], b = noise[y0 * NS + x1], c = noise[y1 * NS + x0], d = noise[y1 * NS + x1];
      return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy;
    }
    var bg = []; var ss = 7;
    function rr() { ss = (ss * 16807) % 2147483647; return ss / 2147483647; }
    for (var n = 0; n < 6; n++) bg.push({ x: rr() * GW, y: rr() * GH, r: 6 + rr() * 9, acc: rr() < 0.25 });

    var frame = 0;
    var phaseEl = document.getElementById("hero-phase");
    var phases = ["single cell", "elongating", "cleavage furrow", "two daughters"];

    function field(px, py, sep, grow) {
      var cx = GW * 0.5, cy = GH * 0.5, R = 19 * grow;
      var a = Math.exp(-((px - (cx - sep)) * (px - (cx - sep)) + (py - cy) * (py - cy)) / (2 * R * R));
      var b = Math.exp(-((px - (cx + sep)) * (px - (cx + sep)) + (py - cy) * (py - cy)) / (2 * R * R));
      return a + b;
    }
    function shade() {
      var d = img.data, t = frame / 71;
      var sep = 25 * Math.max(0, (t - 0.30)) / 0.70;
      var grow = 0.72 + 0.5 * Math.min(1, t * 1.4), iso = 0.45;
      for (var y = 0; y < GH; y++) for (var x = 0; x < GW; x++) {
        var idx = y * GW + x;
        var wob = (vn(x * 0.18, y * 0.18) - 0.5) * 4;
        var f = field(x + wob, y + wob, sep, grow);
        var bgG = 0, bgA = 0;
        for (var c = 0; c < bg.length; c++) {
          var b = bg[c], dx = x - b.x, dy = y - b.y;
          var g = Math.exp(-(dx * dx + dy * dy) / (2 * b.r * b.r));
          if (g > bgG) bgG = g; if (b.acc && g > bgA) bgA = g;
        }
        var F = Math.max(f, bgG * 0.7);
        var gran = 0.5 + 0.7 * vn(x * 0.5, y * 0.5);
        var edge = Math.exp(-Math.abs(F - iso) * 7.0);
        var inside = Math.max(0, F - 0.12);
        var rimI = edge * 1.5, coreI = inside * inside * 1.6 * gran;
        var p = idx * 4;
        d[p] = Math.min(255, (coreI * 0.10 + rimI * (bgA * 1.4) + bgA * 0.16) * 255 + 4);
        d[p + 1] = Math.min(255, (coreI * 0.56 + rimI * 0.85) * 255 + 7);
        d[p + 2] = Math.min(255, (coreI * 1.0 + rimI * 1.1 + bgG * 0.08) * 255 + 12);
        d[p + 3] = 255;
      }
      octx.putImageData(img, 0, 0);
    }
    function draw() {
      ctx.clearRect(0, 0, W, H); ctx.fillStyle = "#02040a"; ctx.fillRect(0, 0, W, H);
      var fy = (H - W) / 2;
      ctx.save();
      ctx.beginPath(); ctx.arc(W / 2, fy + W / 2, W / 2 - 8, 0, 6.2832); ctx.clip();
      ctx.imageSmoothingEnabled = true;
      var z2 = (window.heroState ? window.heroState.zoom : 1.6) / 1.6;
      var dw = W * z2, ox = (W - dw) / 2, oy = fy + (W - dw) / 2;
      ctx.drawImage(oc, ox, oy, dw, dw);
      ctx.globalCompositeOperation = "lighter"; ctx.globalAlpha = 0.45;
      ctx.drawImage(oc, ox - 4, oy - 4, dw + 8, dw + 8);
      ctx.globalAlpha = 1; ctx.globalCompositeOperation = "source-over";
      var sp = (frame * 7) % W;
      var gr = ctx.createLinearGradient(sp - 26, 0, sp + 26, 0);
      gr.addColorStop(0, "rgba(150,235,255,0)"); gr.addColorStop(0.5, "rgba(180,245,255,0.28)"); gr.addColorStop(1, "rgba(150,235,255,0)");
      ctx.fillStyle = gr; ctx.fillRect(sp - 26, fy, 52, W);
      ctx.fillStyle = "rgba(210,248,255,0.5)"; ctx.fillRect(sp, fy, 2, W);
      ctx.restore();
      ctx.strokeStyle = "rgba(120,220,255,0.30)"; ctx.lineWidth = 3;
      ctx.beginPath(); ctx.arc(W / 2, fy + W / 2, W / 2 - 8, 0, 6.2832); ctx.stroke();
      ctx.font = "600 15px 'IBM Plex Mono',monospace"; ctx.fillStyle = "rgba(150,230,255,0.8)";
      ctx.textAlign = "left"; ctx.fillText("SEM · GRAY-SCOTT 3D · F0.030 k0.067", 26, fy + W + 34);
      ctx.fillStyle = "rgba(255,80,140,0.9)"; ctx.textAlign = "right"; ctx.fillText("● REC", W - 26, fy + W + 34);
      ctx.textAlign = "left"; ctx.fillStyle = "rgba(170,235,255,0.8)"; ctx.fillText("25 µm", 26, fy + W + 56);
    }
    function pid(f) { return f < 21 ? 0 : f < 34 ? 1 : f < 42 ? 2 : 3; }
    function loop() {
      if (window.__stop2D) return;
      shade(); draw();
      if (phaseEl) phaseEl.textContent = phases[pid(frame)];
      var st = window.heroState;
      if (st && !st.playing) { frame = Math.round(st.scrub * 71); }
      else { frame = (frame + 1) % 72; if (st) st.scrub = frame / 71; }
      setTimeout(function () { requestAnimationFrame(loop); }, 55);
    }
    loop();
  })();

  // ======================= LAB: the REAL engine, rendered as SEM =======================
  (function lab() {
    var cv = document.getElementById("sim");
    if (!cv || !window.CA || !CA.RULES || !CA.RULES.grayscott) return;
    var ctx = cv.getContext("2d");
    var rule = CA.RULES.grayscott();
    rule.reset();
    var W = rule.width, H = rule.height;
    var RW = 300;                 // SEM render resolution (super-sampled)
    cv.width = RW; cv.height = RW;
    var imgd = ctx.createImageData(RW, RW);
    var pixels = imgd.data;
    var heightBuf = new Float32Array(W * H);
    var region = new Float32Array(RW * RW);
    var mag = 1;
    var paused = false, frame = 0;

    var material = "unreal";
    var depth = 7.0, scanOn = true, spritesOn = false;

    var fEl = document.getElementById("F"), kEl = document.getElementById("k");
    var fOut = document.getElementById("fout"), kOut = document.getElementById("kout");
    var dEl = document.getElementById("depth"), dOut = document.getElementById("dout");
    var genEl = document.getElementById("gen"), consEl = document.getElementById("consequence");

    var CONS = {
      mitosis: "Self-replicating regime: spots grow, elongate, and split — the 2D shadow of the 3D cleavage above.",
      spots: "Stable replicating spots that bud off copies without merging.",
      stripes: "Spots merge into living stripes — pattern, not division.",
      labyrinth: "Stripes wander into a maze; the front never settles."
    };
    function syncInputs() {
      fEl.value = rule.params.F.value; kEl.value = rule.params.k.value;
      fOut.textContent = (+rule.params.F.value).toFixed(4);
      kOut.textContent = (+rule.params.k.value).toFixed(4);
    }
    function setPreset(p) {
      rule.params.preset.value = p; rule.onParamChange("preset");
      rule.reset(); syncInputs();
      if (consEl) consEl.textContent = CONS[p] || "";
      document.querySelectorAll("#presets button").forEach(function (b) {
        b.classList.toggle("on", b.dataset.p === p);
      });
    }
    document.querySelectorAll("#presets button").forEach(function (b) {
      b.onclick = function () { setPreset(b.dataset.p); };
    });
    document.querySelectorAll("#materials button").forEach(function (b) {
      b.onclick = function () {
        material = b.dataset.m;
        document.querySelectorAll("#materials button").forEach(function (o) { o.classList.toggle("on", o === b); });
      };
    });
    fEl.oninput = function () { rule.params.F.value = +fEl.value; rule.onParamChange("F"); fOut.textContent = (+fEl.value).toFixed(4); clearPresetHi(); };
    kEl.oninput = function () { rule.params.k.value = +kEl.value; rule.onParamChange("k"); kOut.textContent = (+kEl.value).toFixed(4); clearPresetHi(); };
    if (dEl) dEl.oninput = function () { depth = +dEl.value; dOut.textContent = (+dEl.value).toFixed(1); };
    var mgEl = document.getElementById("mag"), mOut = document.getElementById("mout");
    function magFromSlider(v) { return 0.005 * Math.pow(1600, v / 1000); }   // 0.005x .. 8x, log
    function fmtMag(m) { return (m < 0.1 ? m.toFixed(3) : m < 1 ? m.toFixed(2) : m.toFixed(1)) + "\u00d7"; }
    function applyMag() { mag = magFromSlider(+mgEl.value); if (mOut) mOut.textContent = fmtMag(mag); }
    if (mgEl) { mgEl.oninput = applyMag; applyMag(); }
    function clearPresetHi() { document.querySelectorAll("#presets button").forEach(function (b) { b.classList.remove("on"); }); }
    var scanBtn = document.getElementById("scan"), sprBtn = document.getElementById("sprites");
    if (scanBtn) scanBtn.onclick = function () { scanOn = !scanOn; scanBtn.classList.toggle("on", scanOn); };
    if (sprBtn) sprBtn.onclick = function () { spritesOn = !spritesOn; sprBtn.classList.toggle("on", spritesOn); };
    document.getElementById("reseed").onclick = function () { rule.reset(); };
    var pauseBtn = document.getElementById("pause");
    pauseBtn.onclick = function () { paused = !paused; pauseBtn.textContent = paused ? "resume" : "pause"; };

    function paletteFor(m) {
      if (window.SEM && SEM.PALETTES) return SEM.PALETTES[(m === "warm-sepia") ? "warm-sepia" : "cool-mono"];
      return null;
    }

    setPreset("mitosis");
    // bilinearly sample the (smooth, toroidal) height field over the magnified
    // central region into the RW x RW render buffer -> crisp round cells at any zoom
    function sampleRegion() {
      var rw2 = W / mag, rh2 = H / mag, left = (W - rw2) / 2, top = (H - rh2) / 2;
      for (var oy = 0; oy < RW; oy++) {
        var gy = top + (oy / RW) * rh2, y0 = Math.floor(gy), fy = gy - y0;
        var y0w = ((y0 % H) + H) % H, y1w = (y0w + 1) % H;
        for (var ox = 0; ox < RW; ox++) {
          var gx = left + (ox / RW) * rw2, x0 = Math.floor(gx), fx = gx - x0;
          var x0w = ((x0 % W) + W) % W, x1w = (x0w + 1) % W;
          var a0 = heightBuf[y0w * W + x0w], b0 = heightBuf[y0w * W + x1w];
          var c0 = heightBuf[y1w * W + x0w], d0 = heightBuf[y1w * W + x1w];
          region[oy * RW + ox] = (a0 * (1 - fx) + b0 * fx) * (1 - fy) + (c0 * (1 - fx) + d0 * fx) * fy;
        }
      }
    }
    function frameLoop() {
      if (!paused) {
        rule.step(); frame++;
        if (typeof rule.renderHeight === "function") rule.renderHeight(heightBuf);
        sampleRegion();
        if (material === "unreal" && window.SEM_UNREAL) {
          SEM_UNREAL.render(region, RW, RW, pixels, { depth: depth, scanX: scanOn ? ((frame * 3) % RW) / RW : null });
        } else if (material === "viridis") {
          var lut = (typeof VIRIDIS_LUT !== "undefined") ? VIRIDIS_LUT : null, ln = lut ? lut.length / 3 : 0;
          for (var i = 0; i < region.length; i++) {
            var t = region[i]; if (t < 0) t = 0; else if (t > 1) t = 1; var pp = i * 4;
            if (ln) { var li = Math.min(ln - 1, (t * ln) | 0) * 3; pixels[pp] = lut[li]; pixels[pp + 1] = lut[li + 1]; pixels[pp + 2] = lut[li + 2]; }
            else { var gv = (t * 255) | 0; pixels[pp] = pixels[pp + 1] = pixels[pp + 2] = gv; }
            pixels[pp + 3] = 255;
          }
        } else if (window.SEM) {
          SEM.render(region, RW, RW, pixels, { palette: material, heightGain: depth });
        }
        ctx.putImageData(imgd, 0, 0);
        if (spritesOn && typeof rule.sprites === "function" && window.SPRITES) {
          var rw2 = W / mag, left = (W - rw2) / 2, top = (H - (H / mag)) / 2, sc = RW / rw2;
          ctx.save(); ctx.setTransform(sc, 0, 0, sc, -left * sc, -top * sc);
          SPRITES.compose(ctx, rule.sprites(W, H), W, H, paletteFor(material));
          ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.restore();
        }
        if (genEl) genEl.textContent = "gen " + rule.generation();
      }
      requestAnimationFrame(frameLoop);
    }
    frameLoop();
  })();

  // ======================= PROOF: count-up =======================
  (function proof() {
    var seen = false;
    var sec = document.getElementById("proof-metrics");
    if (!sec) return;
    function run() {
      if (seen) return; seen = true;
      var el = sec.querySelector('[data-count]');
      if (!el) return;
      var target = parseFloat(el.getAttribute("data-count")), t0 = null;
      function tick(ts) {
        if (!t0) t0 = ts; var k = Math.min(1, (ts - t0) / 900);
        el.textContent = (target * (0.5 + 0.5 * k)).toFixed(1) + "×";
        if (k < 1) requestAnimationFrame(tick);
      }
      requestAnimationFrame(tick);
    }
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) run(); }); }, { threshold: .4 }).observe(sec);
    } else { run(); }
  })();

  // ======================= BRIDGE: live render server + hero hot-swap =======================
  (function bridge() {
    var go = document.getElementById("bgo");
    if (!go) return;
    var logEl = document.getElementById("bridge-log");
    var stateEl = document.getElementById("bridge-state");
    function log(line) { logEl.textContent += "\n" + line; logEl.scrollTop = logEl.scrollHeight; }

    function simulate() {
      log("› no server reachable — SIMULATE mode (start server.py for a live render)");
      var jid = "job_" + Math.random().toString(36).slice(2, 8);
      log("  202 { job: \"" + jid + "\", status: \"queued\" }");
      var steps = ["export_mesh.py → OBJ cleavage frames", "bundle → cleavage.bin",
                   "import_mesh_sequence.py → SM_ProtoCleave_*", "build_scene.py → membrane + mask",
                   "make_sequence.py → push-in + reveal", "render.py → 1080×1920/24 (UE GPU)"];
      var i = 0;
      (function step() {
        if (i >= steps.length) { log("✓ done (simulated)"); stateEl.textContent = "simulated ✓"; stateEl.classList.add("live"); return; }
        log("  [" + jid + "] " + steps[i++]); setTimeout(step, 360);
      })();
    }
    function poll(base, jid) {
      fetch(base + "/api/job/" + jid).then(function (r) { return r.json(); }).then(function (j) {
        log("  [" + jid + "] " + j.status);
        if (j.status === "done") {
          log("  ✓ " + j.frames + " frames, " + j.bytes + " bytes in " + j.sim_seconds + "s");
          stateEl.textContent = "live ✓"; stateEl.classList.add("live");
          if (window.protocellHero && j.bin_url) {
            log("  hot-loading the freshly simulated cell into the hero…");
            window.protocellHero.load(base + j.bin_url).then(function (ok) { log(ok ? "  ✓ hero updated with your F/k" : "  (hero load failed)"); });
          }
        } else if (j.status === "error") {
          log("  ✗ render error — " + (j.log && j.log.length ? j.log[j.log.length - 1] : "see server log")); stateEl.textContent = "error";
        } else { setTimeout(function () { poll(base, jid); }, 800); }
      }).catch(function () { log("  (lost server)"); });
    }
    go.onclick = function () {
      var url = document.getElementById("burl").value;
      var payload = { F: +document.getElementById("bF").value, k: +document.getElementById("bk").value,
                      frames: +document.getElementById("bframes").value, seed: 7, n: 64 };
      var base = ""; try { base = new URL(url, location.href).origin; } catch (e) { base = ""; }
      logEl.textContent = "› POST " + url;
      log("  " + JSON.stringify(payload));
      var done = false;
      var timer = setTimeout(function () { if (!done) { done = true; simulate(); } }, 1400);
      fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) })
        .then(function (r) { return r.json(); })
        .then(function (j) { if (done) return; done = true; clearTimeout(timer);
          if (j.job) { log("  202 { job: \"" + j.job + "\" }"); stateEl.textContent = "rendering…"; poll(base, j.job); }
          else { simulate(); } })
        .catch(function () { /* timer triggers simulate */ });
    };
  })();

})();
