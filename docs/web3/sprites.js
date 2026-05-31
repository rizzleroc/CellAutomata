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
  // ctx is a 2-D canvas already scaled so 1 unit = 1 grid cell.
  // s is the sprite descriptor; pal is the live SEM palette Uint8Array.

  function drawProtocellSphere(ctx, s, pal) {
    const r = s.scale * 0.95;
    // Radial gradient with a hot top-left highlight (matches the SEM L = (0.4,0.3,0.85)).
    const grad = ctx.createRadialGradient(s.x - r * 0.35, s.y - r * 0.40, r * 0.05,
                                          s.x, s.y, r);
    grad.addColorStop(0.00, tint(pal, 0.98));
    grad.addColorStop(0.55, tint(pal, 0.78));
    grad.addColorStop(1.00, tint(pal, 0.18));
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(s.x, s.y, r, 0, Math.PI * 2);
    ctx.fill();
    // Tiny specular dot for that catching-light feel.
    ctx.fillStyle = "rgba(255,255,255,0.65)";
    ctx.beginPath();
    ctx.arc(s.x - r * 0.40, s.y - r * 0.45, Math.max(0.6, r * 0.10), 0, Math.PI * 2);
    ctx.fill();
  }

  function drawAmoeba(ctx, s, pal) {
    const r = s.scale * 1.2;
    const grad = ctx.createRadialGradient(s.x - r * 0.30, s.y - r * 0.30, r * 0.10,
                                          s.x, s.y, r);
    grad.addColorStop(0.00, tint(pal, 0.92));
    grad.addColorStop(0.70, tint(pal, 0.55));
    grad.addColorStop(1.00, tint(pal, 0.15));
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.ellipse(s.x, s.y, r, r * 0.85, s.angle || 0, 0, Math.PI * 2);
    ctx.fill();
    // Membrane rim.
    ctx.strokeStyle = tint(pal, 0.88);
    ctx.lineWidth = Math.max(0.5, r * 0.06);
    ctx.stroke();
  }

  function drawGranule(ctx, s, pal) {
    ctx.fillStyle = s.color || tint(pal, 0.85);
    ctx.beginPath();
    ctx.arc(s.x, s.y, Math.max(0.5, s.scale * 0.55), 0, Math.PI * 2);
    ctx.fill();
  }

  function drawChiralityGlyph(ctx, s, pal) {
    // Twin-loop "helix" glyph; the direction encodes L vs D.
    const r = s.scale * 1.1;
    const dir = s.hand === "L" ? -1 : 1;
    ctx.strokeStyle = tint(pal, s.hand === "L" ? 0.92 : 0.62);
    ctx.lineWidth = Math.max(0.6, r * 0.18);
    ctx.lineCap = "round";
    ctx.beginPath();
    // Two overlapping arcs that twist in the chosen direction.
    ctx.arc(s.x, s.y - r * 0.30, r * 0.55, Math.PI * 0.10 * dir, Math.PI * 1.10 * dir, dir < 0);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(s.x, s.y + r * 0.30, r * 0.55, Math.PI * (1 + 0.10 * dir), Math.PI * (2 + 0.10 * dir), dir < 0);
    ctx.stroke();
  }

  function drawCoacervateDroplet(ctx, s, pal) {
    const r = s.scale * 1.05;
    // Outer ring: the LLPS interface.
    ctx.strokeStyle = tint(pal, 0.82);
    ctx.lineWidth = Math.max(0.5, r * 0.10);
    ctx.beginPath();
    ctx.arc(s.x, s.y, r, 0, Math.PI * 2);
    ctx.stroke();
    // Inner gradient — concentrated chemistry.
    const grad = ctx.createRadialGradient(s.x, s.y, r * 0.10, s.x, s.y, r * 0.95);
    grad.addColorStop(0.00, tint(pal, 0.72));
    grad.addColorStop(1.00, tint(pal, 0.30) + ""); // no alpha needed
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(s.x, s.y, r * 0.95, 0, Math.PI * 2);
    ctx.fill();
  }

  function drawMineralCell(ctx, s, pal) {
    // Hexagonal honeycomb cell, edge-on.
    const r = s.scale * 0.95;
    ctx.strokeStyle = tint(pal, 0.65);
    ctx.lineWidth = Math.max(0.4, r * 0.10);
    ctx.fillStyle = tint(pal, 0.30);
    ctx.beginPath();
    for (let i = 0; i < 6; i++) {
      const a = (Math.PI / 3) * i + Math.PI / 6;
      const px = s.x + r * Math.cos(a);
      const py = s.y + r * Math.sin(a);
      if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
    }
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
  }

  function drawVesicleBilayer(ctx, s, pal) {
    // Two concentric rings = the lipid bilayer; faint fill = lumen.
    const r = s.scale * 1.0;
    const inner = r * 0.78;
    // Lumen fill (the aqueous interior).
    ctx.fillStyle = tint(pal, 0.45);
    ctx.beginPath();
    ctx.arc(s.x, s.y, inner, 0, Math.PI * 2);
    ctx.fill();
    // Outer leaflet.
    ctx.strokeStyle = tint(pal, 0.92);
    ctx.lineWidth = Math.max(0.45, r * 0.07);
    ctx.beginPath();
    ctx.arc(s.x, s.y, r, 0, Math.PI * 2);
    ctx.stroke();
    // Inner leaflet.
    ctx.strokeStyle = tint(pal, 0.78);
    ctx.lineWidth = Math.max(0.35, r * 0.05);
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
  function compose(ctx, sprites, gridW, gridH, palette) {
    if (!sprites || !sprites.length) return;
    for (const s of sprites) {
      const painter = PAINTERS[s.kind];
      if (!painter) continue;
      painter(ctx, s, palette);
    }
  }

  window.SPRITES = { compose, PAINTERS };
})();
