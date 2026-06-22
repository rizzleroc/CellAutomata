// sem_unreal.js — the SEM, Unreal Engine 5.8 powered (high-detail cells).
//
// Same contract as sem.js (window.SEM_UNREAL.render): takes a height field
// (Float32Array in [0,1]) and writes RGBA. The Gray-Scott field is a smooth
// dome, so cellular DETAIL is synthesized and masked by the real cell shape so
// it moves with the cell:
//   bright crisp membrane (Fresnel + iso band)
//   fractal-noise cytoplasm granularity (table-based value-noise fbm)
//   a dense nucleus (height^p) with its own clumped texture
//   internal lamellae rings + a cool diffuse body
// Colours match build_scene.py: deep-blue core, electric-cyan rim.
(function () {
  "use strict";

  // ---- value-noise table (no sin; cheap fbm) ----
  var VT = 256, _vt = null;
  function buildVT() {
    if (_vt) return;
    var raw = new Float32Array(VT * VT), s = 20240;
    for (var i = 0; i < raw.length; i++) { s = (s * 1103515245 + 12345) & 0x7fffffff; raw[i] = s / 0x7fffffff; }
    _vt = new Float32Array(VT * VT);
    for (var y = 0; y < VT; y++) for (var x = 0; x < VT; x++) {
      var xm = (x - 1 + VT) % VT, xp = (x + 1) % VT, ym = (y - 1 + VT) % VT, yp = (y + 1) % VT;
      _vt[y * VT + x] = (raw[ym*VT+xm]+raw[ym*VT+x]+raw[ym*VT+xp]+raw[y*VT+xm]+raw[y*VT+x]+raw[y*VT+xp]+raw[yp*VT+xm]+raw[yp*VT+x]+raw[yp*VT+xp]) / 9;
    }
  }
  function vnoise(x, y) {
    x = x % VT; if (x < 0) x += VT; y = y % VT; if (y < 0) y += VT;
    var x0 = x | 0, y0 = y | 0, x1 = (x0 + 1) % VT, y1 = (y0 + 1) % VT, fx = x - x0, fy = y - y0;
    var a = _vt[y0*VT+x0], b = _vt[y0*VT+x1], c = _vt[y1*VT+x0], d = _vt[y1*VT+x1];
    return (a*(1-fx)+b*fx)*(1-fy)+(c*(1-fx)+d*fx)*fy;
  }
  function fbm(x, y, oct) {
    var v = 0, amp = 0.5, f = 1;
    for (var i = 0; i < oct; i++) { v += amp * vnoise(x * f, y * f); f *= 2; amp *= 0.5; }
    return v;
  }

  // ---- smoothing scratch ----
  var _w = 0, _h = 0, _A, _B;
  function ensure(w, h) { if (w === _w && h === _h) return; _w = w; _h = h; _A = new Float32Array(w * h); _B = new Float32Array(w * h); }
  function blur(w, h, src) {
    var A = _A, B = _B, y, x;
    for (y = 0; y < h; y++) { var o = y * w; for (x = 0; x < w; x++) { var xm = (x-1+w)%w, xp = (x+1)%w; A[o+x] = 0.25*src[o+xm]+0.5*src[o+x]+0.25*src[o+xp]; } }
    for (y = 0; y < h; y++) { var ym = (y-1+h)%h, yp = (y+1)%h; for (x = 0; x < w; x++) { B[y*w+x] = 0.25*A[ym*w+x]+0.5*A[y*w+x]+0.25*A[yp*w+x]; } }
    return B;
  }

  // opts: { depth, core:[r,g,b], rimCol:[r,g,b], detail (noise freq), scanX }
  function render(height, w, h, pixels, opts) {
    opts = opts || {};
    buildVT(); ensure(w, h);
    var hg = opts.depth || 7.0;
    var core = opts.core || [0.05, 0.28, 0.95];
    var rimC = opts.rimCol || [0.45, 0.97, 1.0];
    var nucC = [0.65, 0.90, 1.0];
    var nf = opts.detail || 0.34;
    var sm = blur(w, h, height);
    var hi = 1e-6; for (var i = 0; i < sm.length; i++) if (sm[i] > hi) hi = sm[i];
    var inv = 1 / hi;
    var scanPx = (opts.scanX == null) ? -1 : opts.scanX * w;
    var cr0 = core[0], cr1 = core[1], cr2 = core[2];
    var rr0 = rimC[0], rr1 = rimC[1], rr2 = rimC[2];
    var nr0 = nucC[0], nr1 = nucC[1], nr2 = nucC[2];

    for (var y = 0; y < h; y++) {
      var ym = (y - 1 + h) % h, yp = (y + 1) % h;
      for (var x = 0; x < w; x++) {
        var xm = (x - 1 + w) % w, xp = (x + 1) % w, ic = y * w + x;
        var hh = sm[ic], hn = hh * inv; if (hn > 1) hn = 1;
        if (hn < 0.02) {                       // background: keep it black, skip detail
          var pb = ic * 4; pixels[pb] = 2; pixels[pb+1] = 4; pixels[pb+2] = 9; pixels[pb+3] = 255; continue;
        }
        var dx = (sm[y*w+xp] - sm[y*w+xm]) * hg, dy = (sm[yp*w+x] - sm[ym*w+x]) * hg;
        var d = 1 - 1 / Math.sqrt(dx*dx + dy*dy + 1);   // 1 - normal.z
        var fres = d * d;                                // rim (exp 2)

        // ---- synthesized INNER WORKINGS (masked by the cell, moves with it) ----
        var inside = hn;
        var cyto = fbm(x * nf, y * nf, 3);                            // granular cytoplasm
        var ridg = fbm(x * nf * 0.7 + 5, y * nf * 0.7 + 9, 3);
        var rr = 2 * ridg - 1; if (rr < 0) rr = -rr;
        var fil = (1 - rr); fil = fil * fil * fil;                     // thin cytoskeletal filaments
        var od = fbm(x * nf * 1.7 + 20, y * nf * 1.7 + 3, 2);         // organelle field
        var orgDots = od > 0.58 ? (od - 0.58) * 2.6 : 0;             // discrete organelles
        var nuc = hn - 0.62; nuc = nuc > 0 ? nuc * nuc * 6.0 : 0;     // small dense nucleus
        var cellMask = hn < 0.25 ? hn * 4 : 1;
        var md = (hn - 0.30); if (md < 0) md = -md; md *= 9;
        var memb = (md < 1 ? 1 - md : 0) * cellMask;                 // translucent membrane line
        var diff = (-dx*0.4 - dy*0.3) + 0.85; if (diff < 0) diff = 0; diff *= inside * 0.18;

        var bodyTex = inside * (0.06 + 0.22 * cyto);                  // dim translucent base WITH dark gaps
        var filI = fil * inside * inside;                             // bright filament web
        var orgI = orgDots * inside;                                  // discrete organelles
        var nucI = nuc * 0.5;                                         // smaller, dimmer nucleus
        var R = cr0*bodyTex + rr0*filI*0.7 + 0.50*orgI + 0.60*nucI + rr0*(fres*1.1 + memb*0.8) + diff*0.25;
        var G = cr1*bodyTex + rr1*filI*0.9 + 0.85*orgI + 0.88*nucI + rr1*(fres*1.0 + memb*0.85) + diff*0.55;
        var B = cr2*bodyTex + rr2*filI*1.0 + 1.00*orgI + 1.00*nucI + rr2*(fres*1.0 + memb*0.95) + diff*0.75;

        if (scanPx >= 0) { var ds = x - scanPx; if (ds < 0) ds = -ds; if (ds < 14) { var sb = (1 - ds/14) * 0.5; G += sb; B += sb*1.1; R += sb*0.2; } }

        var br = 1.45, p = ic * 4;
        pixels[p]     = Math.min(255, R * 255 * br + 2);
        pixels[p + 1] = Math.min(255, G * 255 * br + 4);
        pixels[p + 2] = Math.min(255, B * 255 * br + 9);
        pixels[p + 3] = 255;
      }
    }
  }

  window.SEM_UNREAL = { render: render };
})();
