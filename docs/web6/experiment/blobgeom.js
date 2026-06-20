// Living-colony geometry — JS port of cellauto/blobgeom.py.
//
// Pure math (Math only), no canvas/DOM, so the colony's *shape and motion* can
// be unit-tested headlessly in node (see tests/colony.mjs) exactly like the
// Python blobgeom is. Loaded as a CLASSIC script before the rule files so
// natural_selection.js's renderPhotoreal() can reach it as window.CA.blob.
//
//   blobPoints — an irregular, smoothly-wobbling closed membrane outline whose
//     per-angle radius is perturbed by a 3rd + 5th harmonic seeded by `seed`;
//     advancing `phase` each frame makes the membrane breathe with no random
//     state, so every cell is a pure function of its inputs.
//   gazeOffset — a bounded, slowly-wandering pupil offset (lissajous of frame),
//     clamped to the unit disk and scaled by maxOff so the pupil never leaves
//     the eye-white. Deterministic per seed.
//   lighten / isLight — the 3D-sheen blend + luma test from renderer.py.
//   blobPath — stroke a smoothed closed path of the points onto a 2D context
//     (quadratic-midpoint smoothing ≈ Tk's smooth=True spline).
(function () {
  "use strict";
  window.CA = window.CA || { RULES: {} };

  var BLOB_N = 14;

  function blobPoints(cx, cy, rx, ry, opts) {
    opts = opts || {};
    var n = opts.n || BLOB_N;
    var seed = (opts.seed == null) ? 0xCE11 : opts.seed;
    var phase = opts.phase || 0.0;
    var wobble = (opts.wobble == null) ? 0.12 : opts.wobble;
    var s0 = (seed & 0xFF) * 0.013;
    var s1 = ((seed >> 8) & 0xFF) * 0.021;
    var pts = [];
    for (var k = 0; k < n; k++) {
      var ang = 2.0 * Math.PI * k / n;
      // Low-frequency wobble: 3rd + 5th harmonic so the outline reads organic
      // (lumpy) rather than a clean ellipse; phase drifts it slowly.
      var w = Math.sin(ang * 3.0 + s0 + phase) + 0.5 * Math.sin(ang * 5.0 + s1 - phase * 0.7);
      var f = 1.0 + wobble * w / 1.5;
      pts.push([cx + rx * f * Math.cos(ang), cy + ry * f * Math.sin(ang)]);
    }
    return pts;
  }

  function gazeOffset(frame, seed, maxOff) {
    var mo = Math.max(0.0, maxOff);
    var a = (seed & 0xFF) * 0.0245;
    var b = ((seed >> 8) & 0xFF) * 0.0193;
    var gx = 0.7 * Math.sin(frame * 0.013 + a) + 0.3 * Math.sin(frame * 0.030 + b);
    var gy = 0.6 * Math.cos(frame * 0.011 + b);
    var mag = Math.hypot(gx, gy);
    if (mag > 1.0) { gx /= mag; gy /= mag; }
    return [gx * mo, gy * mo];
  }

  function lighten(r, g, b, amount) {
    if (amount == null) amount = 0.42;
    return [
      (r + (255 - r) * amount) | 0,
      (g + (255 - g) * amount) | 0,
      (b + (255 - b) * amount) | 0,
    ];
  }

  function isLight(r, g, b) {
    return (0.299 * r + 0.587 * g + 0.114 * b) > 170; // rec601 luma
  }

  // Deterministic [0,1) value from a cell coordinate (matches renderer.py _hash01).
  function hash01(x, y) {
    var h = ((x * 73856093) ^ (y * 19349663)) & 0xFFFFFF;
    return h / 0x1000000;
  }

  // Trace a smoothed closed blob path; caller does fill()/stroke().
  function blobPath(ctx, pts) {
    var n = pts.length;
    function mid(i) {
      var j = (i + 1) % n;
      return [(pts[i][0] + pts[j][0]) / 2, (pts[i][1] + pts[j][1]) / 2];
    }
    var m0 = mid(n - 1);
    ctx.beginPath();
    ctx.moveTo(m0[0], m0[1]);
    for (var i = 0; i < n; i++) {
      var m = mid(i);
      ctx.quadraticCurveTo(pts[i][0], pts[i][1], m[0], m[1]);
    }
    ctx.closePath();
  }

  window.CA.blob = {
    BLOB_N: BLOB_N,
    blobPoints: blobPoints,
    gazeOffset: gazeOffset,
    lighten: lighten,
    isLight: isLight,
    hash01: hash01,
    blobPath: blobPath,
  };
})();
