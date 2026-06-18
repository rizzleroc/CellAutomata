// web9 — deterministic organic-blob geometry.
//
// A 1:1 JS port of cellauto/blobgeom.py so the browser guide and the desktop
// colony share exactly one membrane + gaze geometry. Pure math; no deps.

export const BLOB_N = 14;

// n points around an irregular, smoothly-wobbling blob centred at (cx, cy).
// rx/ry are the base radii; `phase` advances the membrane ripple; deterministic.
export function blobPoints(cx, cy, rx, ry, { n = BLOB_N, seed = 0xce11, phase = 0, wobble = 0.12 } = {}) {
  const s0 = (seed & 0xff) * 0.013;
  const s1 = ((seed >> 8) & 0xff) * 0.021;
  const pts = [];
  for (let k = 0; k < n; k++) {
    const ang = (2 * Math.PI * k) / n;
    const w = Math.sin(ang * 3 + s0 + phase) + 0.5 * Math.sin(ang * 5 + s1 - phase * 0.7);
    const f = 1 + (wobble * w) / 1.5;
    pts.push([cx + rx * f * Math.cos(ang), cy + ry * f * Math.sin(ang)]);
  }
  return pts;
}

// A bounded, slowly-wandering pupil offset (px), clamped to the unit disk and
// scaled by maxOff so the pupil never leaves the eye-white. Deterministic.
export function gazeOffset(frame, seed, maxOff) {
  const mo = Math.max(0, maxOff);
  const a = (seed & 0xff) * 0.0245;
  const b = ((seed >> 8) & 0xff) * 0.0193;
  let gx = 0.7 * Math.sin(frame * 0.013 + a) + 0.3 * Math.sin(frame * 0.03 + b);
  let gy = 0.6 * Math.cos(frame * 0.011 + b);
  const mag = Math.hypot(gx, gy);
  if (mag > 1) {
    gx /= mag;
    gy /= mag;
  }
  return [gx * mo, gy * mo];
}
