// Sprite library — v4.1 PRD §F3 ported to JS.
//
// Each rule exposes a sprites(width, height) -> [{kind, x, y, scale, ...}]
// method.  The renderer composites these AFTER the SEM substrate via the
// 2-D canvas drawing API.  Sprites are procedural (no PNG asset pipeline)
// so the bundle stays trivially small and the colours can be tinted to
// the live palette.
//
// All coordinates are in GRID space (the rule's native width/height).
// The compositor transforms them to canvas pixels.
//
// Sprite kinds (extend the registry below to add more):
//
//   protocell-sphere   bone-coloured circular form catching light.
//                      Used by Gray-Scott (self-replicating spots).
//   amoeba             larger spherical proto-cell with a brighter rim.
//                      Used by natural-selection's amoeba cells.
//   granule            tiny coloured dot, tracer / chemical species.
//                      Used by soup.
//   chirality-glyph    left- or right-handed helix glyph (L/D).
//                      Used by chirality.
//   coacervate-droplet outlined droplet ring with internal contrast.
//                      Used by coacervate.
//   mineral-cell       hexagonal honeycomb cell, mineral-wall texture.
//                      Used by vents.
//   vesicle-bilayer    concentric ring pair (lipid bilayer).
//                      Used by vesicles.
(function () {
  "use strict";

  function tint(palette, t) {
    // Pull a colour out of an SEM palette LUT at intensity t in [0,1].
    if (!palette || !palette.length) return "rgb(230,224,208)";
    const n = palette.length / 3;
    const i = Math.min(n - 1, Math.max(0, (t * n) | 0)) * 3;
    return "rgb(" + palette[i] + "," + palette[i+1] + "," + palette[i+2] + ")";
  }

  // ── Individual sprite painters ──────────────────────────────────────────
  //
  // Design rule (v4.1.1 calm-overlay revision): EVERY painter is an
  // outline-and-tiny-core "annotation," not a filled blob.  The SEM
  // substrate underneath must remain visible through the sprite layer.
  // Filled gradients dominated and made the layer feel like a paint job
  // rather than a microscope-grade annotation.  Compose pass wraps all
  // sprites in a globalAlpha ≈ 0.75 so even rings blend with the substrate.
  //
  // ctx is a 2-D canvas at native grid resolution (1 unit = 1 grid cell).
  // s is the sprite descriptor; pal is the live SEM palette Uint8Array.

  function drawProtocellSphere(ctx, s, pal) {
    const r = s.scale * 0.95;
    // Hairline outline only — let the SEM substrate show through.
    ctx.strokeStyle = tint(pal, 0.92);
    ctx.lineWidth = Math.max(0.4, r * 0.08);
    ctx.beginPath();
    ctx.arc(s.x, s.y, r, 0, Math.PI * 2);
    ctx.stroke();
    // Catching-light specular pip — single bright pixel.
    ctx.fillStyle = tint(pal, 0.98);
    ctx.beginPath();
    ctx.arc(s.x - r * 0.35, s.y - r * 0.40, Math.max(0.4, r * 0.12), 0, Math.PI * 2);
    ctx.fill();
  }

  function drawAmoeba(ctx, s, pal) {
    const r = s.scale * 1.0;
    // Outline ring only.  Slight ellipticity from the descriptor's angle
    // keeps the colony from looking like a perfect dot grid.
    ctx.strokeStyle = tint(pal, 0.85);
    ctx.lineWidth = Math.max(0.35, r * 0.10);
    ctx.beginPath();
    ctx.ellipse(s.x, s.y, r, r * 0.85, s.angle || 0, 0, Math.PI * 2);
    ctx.stroke();
  }

  function drawGranule(ctx, s, pal) {
    // A single coloured dot, slightly translucent so trails compete.
    ctx.fillStyle = s.color || tint(pal, 0.85);
    ctx.globalAlpha = 0.85;
    ctx.beginPath();
    ctx.arc(s.x, s.y, Math.max(0.4, s.scale * 0.45), 0, Math.PI * 2);
    ctx.fill();
    ctx.globalAlpha = 1;
  }

  function drawChiralityGlyph(ctx, s, pal) {
    // Twin-loop "helix" glyph; the direction encodes L vs D.
    const r = s.scale * 1.0;
    const dir = s.hand === "L" ? -1 : 1;
    ctx.strokeStyle = tint(pal, s.hand === "L" ? 0.95 : 0.55);
    ctx.lineWidth = Math.max(0.45, r * 0.14);
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.arc(s.x, s.y - r * 0.30, r * 0.50,
            Math.PI * 0.10 * dir, Math.PI * 1.10 * dir, dir < 0);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(s.x, s.y + r * 0.30, r * 0.50,
            Math.PI * (1 + 0.10 * dir), Math.PI * (2 + 0.10 * dir), dir < 0);
    ctx.stroke();
  }

  function drawCoacervateDroplet(ctx, s, pal) {
    // Outline ring + small core dot.  No interior fill — the SEM
    // substrate IS the LLPS density gradient.
    const r = s.scale * 1.0;
    ctx.strokeStyle = tint(pal, 0.85);
    ctx.lineWidth = Math.max(0.4, r * 0.08);
    ctx.beginPath();
    ctx.arc(s.x, s.y, r, 0, Math.PI * 2);
    ctx.stroke();
    ctx.fillStyle = tint(pal, 0.75);
    ctx.beginPath();
    ctx.arc(s.x, s.y, Math.max(0.5, r * 0.18), 0, Math.PI * 2);
    ctx.fill();
  }

  function drawMineralCell(ctx, s, pal) {
    // Hexagonal honeycomb cell — STROKE only.  No fill.  The chimney
    // walls in the SEM substrate are already opaque mineral; the sprite
    // just adds the lattice geometry on top.
    const r = s.scale * 0.92;
    ctx.strokeStyle = tint(pal, 0.70);
    ctx.lineWidth = Math.max(0.3, r * 0.08);
    ctx.beginPath();
    for (let i = 0; i < 6; i++) {
      const a = (Math.PI / 3) * i + Math.PI / 6;
      const px = s.x + r * Math.cos(a);
      const py = s.y + r * Math.sin(a);
      if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
    }
    ctx.closePath();
    ctx.stroke();
  }

  function drawVesicleBilayer(ctx, s, pal) {
    // Two concentric rings = the lipid bilayer.  No lumen fill — let
    // the SEM substrate be the aqueous interior so the membrane reads
    // as a true thin shell, not a painted disk.
    const r = s.scale * 1.0;
    const inner = r * 0.76;
    ctx.strokeStyle = tint(pal, 0.95);
    ctx.lineWidth = Math.max(0.35, r * 0.06);
    ctx.beginPath();
    ctx.arc(s.x, s.y, r, 0, Math.PI * 2);
    ctx.stroke();
    ctx.strokeStyle = tint(pal, 0.78);
    ctx.lineWidth = Math.max(0.30, r * 0.04);
    ctx.beginPath();
    ctx.arc(s.x, s.y, inner, 0, Math.PI * 2);
    ctx.stroke();
  }

  const PAINTERS = {
    "protocell-sphere":   drawProtocellSphere,
    "amoeba":             drawAmoeba,
    "granule":            drawGranule,
    "chirality-glyph":    drawChiralityGlyph,
    "coacervate-droplet": drawCoacervateDroplet,
    "mineral-cell":       drawMineralCell,
    "vesicle-bilayer":    drawVesicleBilayer,
  };

  // ── Compositor entry point ──────────────────────────────────────────────
  //
  //   ctx       2-D canvas context — already drawn-into by the SEM blit.
  //   sprites   the rule's sprites() output.  Each item:
  //               { kind, x, y, scale, ...extras }
  //             x and y are in grid coordinates; scale is in grid-cell units.
  //   gridW,gridH   the rule's native grid size.
  //   palette   the live SEM palette LUT (Uint8Array), used to tint sprites.
  //
  // The ctx is at canvas resolution (typically equal to gridW × gridH).
  //
  // Compose wraps every painter call in a globalAlpha so even outlined
  // sprites blend into the SEM substrate rather than dominate it — this
  // is the v4.1.1 calm-overlay revision after the v4.1.0 launch produced
  // "distracting / sprites cover everything" feedback.
  function compose(ctx, sprites, gridW, gridH, palette) {
    if (!sprites || !sprites.length) return;
    const prevAlpha = ctx.globalAlpha;
    const prevLineCap = ctx.lineCap;
    ctx.globalAlpha = 0.72;
    ctx.lineCap = "round";
    for (const s of sprites) {
      const painter = PAINTERS[s.kind];
      if (!painter) continue;
      painter(ctx, s, palette);
    }
    ctx.globalAlpha = prevAlpha;
    ctx.lineCap = prevLineCap;
  }

  window.SPRITES = { compose, PAINTERS };
})();
