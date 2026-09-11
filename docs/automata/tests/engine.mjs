// engine.mjs — THE SCIENCE gate for the Automata Lab. Zero-dep, runs the real
// engine modules in node and asserts published cellular-automata facts, so a
// regression that keeps the page rendering but breaks the mathematics cannot
// ship. Run: node docs/automata/tests/engine.mjs
import { Grid, mulberry32, BOUNDARIES } from '../engine/grid.js';
import { FAMILIES, familyById, valuesOf, schemaOf, presetsOf, palette, lifelike, ltl, elementary, cyclic, wireworld, turmite, abiogenesis } from '../engine/rules/index.js';
import { readFileSync, existsSync } from 'node:fs';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { parseRLE, toRLE, parsePlain, libraryPattern, byId, LIBRARY, fromGrid } from '../engine/patterns.js';
import * as M from '../engine/measure.js';

let pass = 0; const fails = [];
const ok = (c, m) => { if (c) pass++; else fails.push(m); };
const section = (t) => console.log('· ' + t);
const run = (rule, grid, n) => { for (let i = 0; i < n; i++) rule.step(grid); };
const life = lifelike.make('B3/S23');
const place = (id, w, h, opts) => { const g = new Grid(w, h, opts); g.stampCentered(libraryPattern(byId(id))); return g; };
const sameShifted = (before, grid, dx, dy) => {
  const w = grid.width, h = grid.height;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const sx = ((x - dx) % w + w) % w, sy = ((y - dy) % h + h) % h;
    if (grid.cells[y * w + x] !== before[sy * w + sx]) return false;
  }
  return true;
};

console.log('Automata Lab — engine science tests\n');

// ── 1. Lattice ──────────────────────────────────────────────────────────────
section('lattice');
{
  const g = new Grid(10, 6);
  ok(g.size === 60 && g.cells.length === 60, 'grid allocates w×h cells');
  ok(BOUNDARIES.length === 3, 'three boundary policies');
  g.set(0, 0, 1);
  ok(g.get(10, 6) === 1 && g.get(-10, -6) === 1, 'torus wraps both axes');
  const d = new Grid(10, 6, { boundary: 'dead' }); d.set(0, 0, 1);
  ok(d.get(10, 6) === 0 && d.idx(-1, 0) === -1, 'dead boundary is 0 outside');
  const m = new Grid(10, 6, { boundary: 'mirror' }); m.set(0, 0, 1);
  ok(m.get(-1, -1) === 1 && m.get(10, 0) === m.get(9, 0), 'mirror boundary reflects');
  let threw = false; try { new Grid(0, 5); } catch { threw = true; } ok(threw, 'rejects a zero-size grid');
  const r1 = mulberry32(42), r2 = mulberry32(42);
  ok(r1() === r2() && r1() === r2(), 'seeded RNG is reproducible');
  const a = new Grid(50, 50), b = new Grid(50, 50);
  a.randomize(mulberry32(9), 0.3); b.randomize(mulberry32(9), 0.3);
  ok(a.cells.every((v, i) => v === b.cells[i]), 'same seed ⇒ identical soup');
  const dens = a.population() / a.size;
  ok(dens > 0.25 && dens < 0.35, `soup density ≈ requested (${dens.toFixed(3)})`);
  const nb = a.neighbourhood('moore'); ok(nb.K === 8 && nb.tbl.length === 8 * 2500, 'Moore table has 8 entries per cell');
  ok(a.neighbourhood('vn').K === 4, 'von Neumann table has 4 entries per cell');
}

// ── 2. Rule notation ────────────────────────────────────────────────────────
section('rule notation');
{
  const f = (s) => lifelike.formatRule(lifelike.parseRule(s));
  ok(f('B3/S23') === 'B3/S23', 'B3/S23 round-trips');
  ok(f('b3s23') === 'B3/S23', 'lower-case, slash-less form parses');
  ok(f('23/3') === 'B3/S23', 'S/B legacy form parses');
  ok(f('/2/3') === 'B2/S/C3', 'S/B/C Generations form (Brian’s Brain) parses');
  ok(f('B2/S/C3') === 'B2/S/C3', 'B/S/C form parses');
  ok(f('B3/S23V') === 'B3/S23V', 'V suffix selects von Neumann');
  for (const bad of ['', 'B9/S23', 'B3/S23/C1', 'xyz', 'B3/S5V']) {
    let threw = false; try { lifelike.parseRule(bad); } catch { threw = true; }
    ok(threw, `rejects "${bad}"`);
  }
  ok(Math.abs(lifelike.langtonLambda(lifelike.parseRule('B3/S23')) - 140 / 512) < 1e-12, 'Langton λ(Life) = 140/512');
  ok(lifelike.langtonLambda(lifelike.parseRule('B/S')) === 0, 'λ of the empty rule is 0');
  ok(lifelike.langtonLambda(lifelike.parseRule('B012345678/S012345678')) === 1, 'λ of the saturating rule is 1');
  ok(lifelike.binom(8, 3) === 56 && lifelike.binom(8, 0) === 1, 'binomial helper');
  for (const c of lifelike.CATALOG) {
    let good = true; try { lifelike.parseRule(c.rule); } catch { good = false; }
    ok(good, `catalog rule "${c.name}" (${c.rule}) parses`);
  }
  ok(ltl.formatLtl(ltl.parseLtl('R5,C0,M1,S34..58,B34..45')) === 'R5,C0,M1,S34..58,B34..45', 'LtL notation round-trips');
  let threw = false; try { ltl.parseLtl('R5,C0,M1,S60..58,B34..45'); } catch { threw = true; } ok(threw, 'LtL rejects an inverted interval');
  for (const c of ltl.CATALOG) { let good = true; try { ltl.parseLtl(c.rule); } catch { good = false; } ok(good, `LtL catalog "${c.name}" parses`); }
  ok(turmite.parseTurmite('rl') === 'RL', 'turmite string normalises');
  threw = false; try { turmite.parseTurmite('RLX'); } catch { threw = true; } ok(threw, 'turmite rejects a bad letter');
}

// ── 3. Conway's Life — the canonical facts ──────────────────────────────────
section("Conway's Life");
{
  let g = place('glider', 40, 40);
  const b0 = g.bounds(); run(life, g, 4); const b4 = g.bounds();
  ok(g.population() === 5 && b4.x0 === b0.x0 + 1 && b4.y0 === b0.y0 + 1, 'glider moves (+1,+1) every 4 generations');
  g = place('block', 20, 20); run(life, g, 10); ok(g.population() === 4, 'block is a still life');
  g = place('blinker', 20, 20); const s = g.cells.slice(); run(life, g, 1);
  ok(!g.cells.every((v, i) => v === s[i]), 'blinker changes after one step');
  run(life, g, 1); ok(g.cells.every((v, i) => v === s[i]), 'blinker has period 2');
  for (const [id, p, n] of [['pulsar', 3, 48], ['pentadecathlon', 15, 12], ['beacon', 2, 8]]) {
    g = place(id, 60, 60); const s0 = g.cells.slice(); run(life, g, p);
    ok(g.cells.every((v, i) => v === s0[i]) && g.population() === n, `${id}: period ${p}, ${n} cells`);
  }
  g = new Grid(60, 60); g.stamp(libraryPattern(byId('lwss')), 30, 30); const s0 = g.cells.slice(); run(life, g, 4);
  ok(sameShifted(s0, g, -2, 0), 'LWSS translates 2 cells orthogonally per 4 generations (c/2)');
  g = place('diehard', 60, 60); run(life, g, 129); ok(g.population() > 0, 'diehard is alive at 129');
  run(life, g, 1); ok(g.population() === 0, 'diehard vanishes at generation 130');
  g = new Grid(120, 100, { boundary: 'dead' }); g.stamp(libraryPattern(byId('gosper')), 2, 2);
  ok(g.population() === 36, 'Gosper gun is 36 cells');
  const pops = []; for (let i = 0; i <= 150; i++) { if (i % 30 === 0) pops.push(g.population()); life.step(g); }
  ok(pops.every((p, i) => i === 0 || p === pops[i - 1] + 5), `gun emits one glider (5 cells) per 30 generations (${pops.join('→')})`);
  const t0 = Date.now();
  g = new Grid(560, 560, { boundary: 'dead' }); g.stampCentered(libraryPattern(byId('rpentomino'))); run(life, g, 1103);
  ok(g.population() === 116, `R-pentomino settles to 116 cells at generation 1103 (got ${g.population()}, ${Date.now() - t0} ms)`);
  // boundary matters: a glider survives on a torus and dies on a dead world
  g = new Grid(30, 30); g.stamp(libraryPattern(byId('glider')), 2, 2); run(life, g, 400); ok(g.population() === 5, 'glider survives 400 gens on a torus');
  g = new Grid(30, 30, { boundary: 'dead' }); g.stamp(libraryPattern(byId('glider')), 2, 2); run(life, g, 400); ok(g.population() !== 5 || !g.bounds() || g.bounds().x0 > 20, 'glider does not survive intact as a glider on a dead world');
}

// ── 4. Other Life-like rules ────────────────────────────────────────────────
section('Life-like family');
{
  const hl = lifelike.make('B36/S23');
  let g = place('replicator', 60, 60); ok(g.population() === 12, 'HighLife replicator is 12 cells');
  run(hl, g, 12); ok(g.population() === 24, 'HighLife replicator doubles at generation 12');
  run(hl, g, 12); ok(g.population() === 24, '…and the two copies annihilate the middle at 24 (24 cells)');
  const seeds = lifelike.make('B2/S'); g = place('seedv', 120, 120); const p = []; for (let i = 0; i < 30; i++) { seeds.step(g); p.push(g.population()); }
  ok(p[29] > 100 && p[29] > p[0], `Seeds explodes from a five-cell chevron (${p[0]}→${p[29]} cells in 30 gens)`);
  ok(g.cells.every((v) => v <= 1), 'Seeds never survives: only states 0/1');
  const lwd = lifelike.make('B3/S012345678'); g = new Grid(80, 80); g.randomize(mulberry32(3), 0.2);
  let mono = true, last = g.population(); for (let i = 0; i < 60; i++) { lwd.step(g); const n = g.population(); if (n < last) mono = false; last = n; }
  ok(mono, 'Life without Death: population never decreases');
  const bb = lifelike.make('B2/S/C3'); g = new Grid(80, 80); g.randomize(mulberry32(4), 0.3, 3); run(bb, g, 50);
  ok(bb.states === 3 && g.cells.some((v) => v === 2) && g.cells.some((v) => v === 1), "Brian's Brain keeps on + dying states in play");
  ok(g.cells.every((v) => v < 3), 'Generations states stay < C');
  // a dying state must NOT count as a live neighbour
  g = new Grid(9, 9); g.set(4, 4, 2); g.set(4, 3, 2); g.set(3, 4, 0); run(bb, g, 1);
  ok(g.get(3, 3) === 0, 'dying cells do not count toward birth');
  const vote = lifelike.make('B5678/S45678'); g = new Grid(100, 100); g.randomize(mulberry32(2), 0.5);
  const e0 = M.blockEntropy(g); run(vote, g, 50); const e1 = M.blockEntropy(g);
  ok(e0 > 3.9 && e1 < e0 - 1, `Vote coarsens a soup: block entropy ${e0.toFixed(2)} → ${e1.toFixed(2)} bits`);
  const vn = lifelike.make('B3/S23V'); g = place('glider', 30, 30); run(vn, g, 1);
  ok(g.population() !== 5 || !sameShifted(libraryPattern(byId('glider')).cells, g, 0, 0), 'von Neumann Life is a different rule');
  ok(Math.abs(vn.lambda - 14 / 32) < 1e-12, 'λ(B3/S23V) = 14/32 on the 4-neighbourhood');
}

// ── 5. Larger than Life ─────────────────────────────────────────────────────
section('Larger than Life');
{
  const asLife = ltl.make('R1,C0,M0,S2..3,B3..3');
  let g = place('glider', 40, 40); const b0 = g.bounds(); run(asLife, g, 4); const b4 = g.bounds();
  ok(g.population() === 5 && b4.x0 === b0.x0 + 1 && b4.y0 === b0.y0 + 1, 'R1 interval rule reproduces Conway’s glider exactly');
  g = new Grid(60, 60); g.randomize(mulberry32(11), 0.4); const h = g.clone();
  run(asLife, g, 30); run(life, h, 30);
  ok(g.cells.every((v, i) => v === h.cells[i]), 'LtL(R1) and Life agree on a soup for 30 generations (summed-area counting is exact)');
  const bugs = ltl.make('R5,C0,M1,S34..58,B34..45'); g = new Grid(120, 120); g.randomize(mulberry32(5), 0.5);
  run(bugs, g, 200);
  const n = g.population();
  ok(n > 0 && n < g.size * 0.5, `Bugs: a soup condenses into a few persistent bugs (${n} cells)`);
  const d = new Grid(40, 40, { boundary: 'dead' }); d.randomize(mulberry32(5), 0.5); const dd = d.clone(); run(bugs, d, 5);
  ok(!d.cells.every((v, i) => v === dd.cells[i]), 'LtL steps under a dead boundary too');
}

// ── 6. Elementary (Wolfram) ─────────────────────────────────────────────────
section('elementary 1-D');
{
  let g = new Grid(201, 40, { boundary: 'dead' }); const r30 = elementary.make({ rule: 30 }); r30.init(g);
  const col = []; for (let t = 0; t < 16; t++) { col.push(g.cells[g.row * g.width + 100]); r30.step(g); }
  ok(col.join('') === '1101110011000101', `rule 30 centre column starts 1101110011000101 (got ${col.join('')})`);
  g = new Grid(129, 70, { boundary: 'dead' }); const r90 = elementary.make({ rule: 90 }); r90.init(g);
  const gould = []; for (let t = 0; t < 16; t++) { let n = 0; for (let x = 0; x < g.width; x++) n += g.cells[g.row * g.width + x]; gould.push(n); r90.step(g); }
  const expect = [...Array(16).keys()].map((t) => 1 << t.toString(2).split('1').length - 1);
  ok(gould.every((v, i) => v === expect[i]), `rule 90 row populations follow Gould’s sequence 2^popcount(t) (${gould.join(',')})`);
  g = new Grid(100, 10); const r184 = elementary.make({ rule: 184, init: 'soup' }); r184.init(g, mulberry32(7));
  const count = (gr) => { let n = 0; for (let x = 0; x < gr.width; x++) n += gr.cells[gr.row * gr.width + x]; return n; };
  const c0 = count(g); run(r184, g, 40);
  ok(count(g) === c0 && g.row === 9 && g.generation === 40, `rule 184 conserves particles on a torus (${c0}) and the sheet scrolls`);
  g = new Grid(64, 8, { boundary: 'dead' }); const r0 = elementary.make({ rule: 0, init: 'soup' }); r0.init(g, mulberry32(1)); run(r0, g, 1);
  ok(count(g) === 0, 'rule 0 clears everything');
  g = new Grid(64, 8, { boundary: 'dead' }); const r255 = elementary.make({ rule: 255 }); r255.init(g); run(r255, g, 1);
  ok(count(g) === 64, 'rule 255 fills everything');
  g = new Grid(41, 10, { boundary: 'dead' }); const code20 = elementary.make({ rule: 20, totalistic: true, init: 'soup' }); code20.init(g, mulberry32(2)); run(code20, g, 5);
  ok(g.generation === 5 && count(g) > 0, 'totalistic code 20 runs from a soup');
  let threw = false; try { elementary.make({ rule: 256 }); } catch { threw = true; } ok(threw, 'rule 256 is rejected');
  ok(elementary.CATALOG.some((c) => c.rule === 110 && c.cls === 4), 'catalog carries rule 110 as class 4');
}

// ── 7. Excitable media ──────────────────────────────────────────────────────
section('cyclic + Greenberg–Hastings');
{
  let g = new Grid(120, 120); const cy = cyclic.make({ states: 14, threshold: 1, range: 1 }); cy.init(g, mulberry32(3));
  const e0 = M.blockEntropy(g);
  let act = 0; for (let t = 0; t < 300; t++) { const prev = g.cells.slice(); cy.step(g); act = M.activity(g, prev); }
  ok(act > 0.9, `cyclic 14/1/1 reaches the spiral phase: nearly every cell advances every step (activity ${act.toFixed(2)})`);
  ok(M.blockEntropy(g) < e0, 'cyclic self-organises: block entropy falls from the soup');
  ok(g.cells.every((v) => v < 14), 'cyclic states stay on the ring');
  g = new Grid(60, 60); const gh = cyclic.make({ model: 'gh', states: 5, threshold: 1 }); g.clear(); g.set(30, 30, 1);
  run(gh, g, 1); ok(g.get(30, 30) === 2 && g.population(1) === 8, 'GH: one excited cell excites its 8 neighbours and becomes refractory');
  run(gh, g, 3); ok(g.get(30, 30) === 0, 'GH: refractory cell returns to rest after n−1 steps');
  run(gh, g, 10); ok(g.population(1) > 8, 'GH: an expanding ring');
  const ghv = cyclic.make({ model: 'gh', states: 3, threshold: 1, neighbourhood: 'vn' }); g = new Grid(20, 20); g.set(10, 10, 1); run(ghv, g, 1);
  ok(g.population(1) === 4, 'GH on von Neumann excites 4 neighbours');
  let threw = false; try { cyclic.make({ states: 2 }); } catch { threw = true; } ok(threw, 'cyclic rejects < 3 states');
}

// ── 8. Wireworld ────────────────────────────────────────────────────────────
section('Wireworld');
{
  const ww = wireworld.make();
  const load = (id) => { const p = libraryPattern(byId(id)); const g = new Grid(p.width + 4, p.height + 4, { boundary: 'dead' }); g.stamp(p, 2, 2); return g; };
  let g = load('ww_loop');
  const at = []; for (let t = 0; t < 65; t++) { at.push(g.get(2, 4) === wireworld.HEAD ? 1 : 0); ww.step(g); }
  ok(at[0] === 1 && at[32] === 1 && at[64] === 1 && at.slice(1, 32).every((v) => v === 0), 'loop clock: the electron returns to its cell every 32 generations');
  ok(g.population(wireworld.HEAD) >= 1, 'loop clock never loses its electron');
  g = load('ww_diode'); const w = g.width;
  let reached = false; for (let t = 0; t < 30; t++) { if (g.get(w - 3, 3) === wireworld.HEAD) reached = true; ww.step(g); }
  ok(reached, 'diode passes an electron left→right to the far end of the wire');
  const mirrored = parsePlain('.......##.....\n#####.######HT\n.......##.....');
  g = new Grid(mirrored.width + 4, mirrored.height + 4, { boundary: 'dead' }); g.stamp(mirrored, 2, 2);
  reached = false; for (let t = 0; t < 60; t++) { if (g.get(2, 3) === wireworld.HEAD) reached = true; ww.step(g); }
  ok(!reached, 'mirrored diode blocks: no electron reaches the far end');
  g = load('ww_clocks'); ok(g.population(wireworld.HEAD) === 2, 'two clocks start with two electrons');
  run(ww, g, 24); ok(g.get(2 + 16, 4) === wireworld.HEAD, 'the 24-cell loop returns its electron at t=24');
  ok(g.get(2, 4) !== wireworld.HEAD, '…while the 32-cell loop’s has not yet returned');
  g = new Grid(5, 5); g.set(2, 2, wireworld.HEAD); run(ww, g, 1); ok(g.get(2, 2) === wireworld.TAIL, 'head → tail');
  run(ww, g, 1); ok(g.get(2, 2) === wireworld.WIRE, 'tail → conductor');
}

// ── 9. Turmites ─────────────────────────────────────────────────────────────
section("Langton's ant + turmites");
{
  let g = new Grid(200, 200, { boundary: 'dead' }); const ant = turmite.make({ rule: 'RL', movesPerGen: 1 }); ant.init(g);
  run(ant, g, 11000); const a = { ...ant.agents[0] }; run(ant, g, 104); const b = ant.agents[0];
  ok(Math.abs(b.x - a.x) === 2 && Math.abs(b.y - a.y) === 2 && b.dir === a.dir, `Langton's ant is on the 104-step highway after 11 000 moves (Δ=${b.x - a.x},${b.y - a.y})`);
  const pop = g.population(); run(ant, g, 104); ok(g.population() === pop + 12, 'the highway lays 12 black cells per period');
  g = new Grid(50, 50); const a2 = turmite.make({ rule: 'RL', movesPerGen: 1 }); a2.init(g); run(a2, g, 1);
  ok(g.get(25, 25) === 1 && a2.agents[0].x === 26 && a2.agents[0].y === 25, 'RL on white: turn right (east), flip, step');
  g = new Grid(50, 50); const sym = turmite.make({ rule: 'LLRR', movesPerGen: 1 }); sym.init(g); run(sym, g, 500);
  ok(sym.states === 4 && g.cells.some((v) => v === 3), 'LLRR uses four colours');
  g = new Grid(30, 30, { boundary: 'dead' }); const walker = turmite.make({ rule: 'NN', movesPerGen: 1 }); walker.init(g); run(walker, g, 40);
  ok(walker.agents[0].alive === false, 'an ant that walks off a dead world dies');
  g = new Grid(30, 30, { boundary: 'torus' }); const w2 = turmite.make({ rule: 'NN', movesPerGen: 1 }); w2.init(g); run(w2, g, 30);
  ok(w2.agents[0].alive && w2.agents[0].y === 15, 'on a torus the same ant wraps back to its row');
  g = new Grid(60, 60); const many = turmite.make({ rule: 'RL', ants: 5, movesPerGen: 4 }); many.init(g, mulberry32(1)); run(many, g, 20);
  ok(many.agents.length === 5 && g.generation === 20, 'multiple ants, movesPerGen respected');
}

// ── 10. Patterns: RLE + plain ───────────────────────────────────────────────
section('patterns');
{
  const gl = parseRLE('x = 3, y = 3, rule = B3/S23\nbo$2bo$3o!');
  ok(gl.width === 3 && gl.height === 3 && gl.rule === 'B3/S23' && gl.cells.join('') === '010001111', 'RLE header + body parse');
  ok(toRLE(gl).endsWith('bo$2bo$3o!'), 'RLE encoder emits the canonical glider');
  const gun = parseRLE(byId('gosper').rle); const rt = parseRLE(toRLE(gun));
  ok(rt.width === 36 && rt.height === 9 && rt.cells.every((v, i) => v === gun.cells[i]), 'Gosper gun survives an RLE round-trip');
  const ms = parseRLE('x = 3, y = 1\nA.B!'); ok(ms.cells.join('') === '102', 'multi-state RLE letters map to states');
  const pl = parsePlain('.O.\nH#T'); ok(pl.cells.join('') === '010213', 'plain text: . O H # T → 0 1 0 2 1 3');
  for (const p of LIBRARY) { let good = true; try { const pat = libraryPattern(p); if (!pat.cells.some((v) => v)) good = false; } catch { good = false; } ok(good, `library "${p.name}" decodes to a non-empty pattern`); }
  ok(LIBRARY.length >= 15, `library has ${LIBRARY.length} patterns`);
  let g = new Grid(20, 20); g.stamp(gl, 7, 9); const back = fromGrid(g); ok(back.width === 3 && back.cells.join('') === '010001111', 'fromGrid crops the live bounding box');
  let threw = false; try { parseRLE('x = 1, y = 1\nz!'); } catch { threw = true; } ok(threw, 'RLE rejects an unknown token');
}

// ── 11. Measurements ────────────────────────────────────────────────────────
section('measurements');
{
  let g = new Grid(40, 40); ok(M.blockEntropy(g) === 0, 'blank lattice has zero block entropy');
  g.randomize(mulberry32(1), 0.5); ok(M.blockEntropy(g) > 3.8, 'a p=½ soup has ≈4 bits of block entropy');
  const prev = g.cells.slice(); life.step(g); const a = M.activity(g, prev); ok(a > 0 && a < 1, 'activity is a fraction in (0,1)');
  ok(M.periodOf([1, 2, 1, 2, 1, 2, 1, 2, 1, 2]) === 2 && M.periodOf([1, 2, 3, 4, 5, 6, 7, 8, 9]) === 0, 'period detector');
  const series = (rule, grid, n) => { const s = []; for (let i = 0; i < n; i++) { const p = grid.cells.slice(); rule.step(grid); s.push(M.activity(grid, p)); } return s; };
  g = place('block', 40, 40); ok(M.classify(series(life, g, 40)).cls === 1, 'still life ⇒ class I');
  g = place('blinker', 40, 40); ok(M.classify(series(life, g, 40)).cls === 2, 'oscillator ⇒ class II');
  g = new Grid(80, 80); g.randomize(mulberry32(1), 0.5); ok(M.classify(series(lifelike.make('B2/S'), g, 80)).cls === 3, 'Seeds soup ⇒ class III (chaotic)');
  g = new Grid(80, 80); g.randomize(mulberry32(1), 0.3); ok(M.classify(series(life, g, 400)).cls === 4, 'Life soup ⇒ class IV (complex)');
  const log = new M.RunLog(5); for (let i = 0; i < 8; i++) log.push({ generation: i, population: i, density: 0, activity: 0, entropy: 0 });
  ok(log.rows.length === 5 && log.rows[0].generation === 3, 'RunLog is a bounded ring');
  const csv = log.toCSV(); ok(csv.split('\n').length === 6 && csv.startsWith('generation,population,density,activity,entropy'), 'CSV export has a header + rows');
}

// ── 12. The abiogenesis lab, by reference ──────────────────────────────────
// Load web7's thirteen stage rules exactly as the page does (classic scripts
// sharing one scope, viridis.js first) into a vm sandbox, then hand the
// sandbox `window` to the adapter.
section('abiogenesis · the 13 stages by reference');
{
  const WEB7 = join(dirname(fileURLToPath(import.meta.url)), '..', '..', 'web7', 'experiment');
  const html = readFileSync(join(dirname(fileURLToPath(import.meta.url)), '..', 'index.html'), 'utf8');
  const refs = [...html.matchAll(/<script src="\.\.\/web7\/experiment\/([^"]+)">/g)].map((m) => m[1]);
  ok(refs[0] === 'viridis.js', 'page loads viridis.js before the stage rules');
  ok(refs.length === 1 + abiogenesis.STAGES.length, `page references all ${abiogenesis.STAGES.length} stage rule files from web7 (${refs.length - 1})`);
  for (const r of refs) ok(existsSync(join(WEB7, r)), `referenced web7 file exists: ${r}`);
  const sandbox = { window: { CA: { RULES: {} } }, Math, Float32Array, Float64Array, Int32Array, Uint8Array, Uint16Array, Uint32Array, Uint8ClampedArray, Map, Set, console, performance, Date };
  sandbox.CA = sandbox.window.CA; sandbox.globalThis = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(refs.map((f) => readFileSync(join(WEB7, f), 'utf8')).join('\n;\n'), sandbox, { filename: 'web7-rules.js' });
  globalThis.window = sandbox.window;
  ok(abiogenesis.available(), 'adapter sees every stage factory on window.CA.RULES');
  const fam = familyById('abiogenesis');
  ok(!!fam && fam.paintable === false && typeof fam.schema === 'function', 'abiogenesis family is registered as watch-and-tune with a stage-dependent schema');
  ok(fam.validate({ stage: 'soup' }) === null && fam.validate({ stage: 'nope' }) !== null, 'validate accepts a real stage and rejects a fake one');
  for (const st of abiogenesis.STAGES) {
    const values = valuesOf(fam, { stage: st.id });
    const P = schemaOf(fam, values);
    ok(Object.keys(P).length >= 1 + (st.id === 'natural-selection' ? 1 : 1), `${st.id}: schema = stage + its own knobs (${Object.keys(P).length - 1})`);
    const rule = fam.make(values);
    ok(rule.fixedSize && rule.fixedSize.width > 0 && rule.states === abiogenesis.LEVELS, `${st.id}: fixed ${rule.fixedSize.width}×${rule.fixedSize.height} lattice, ${abiogenesis.LEVELS} relief levels`);
    const g = new Grid(rule.fixedSize.width, rule.fixedSize.height);
    rule.init(g, mulberry32(3));
    const before = g.cells.slice();
    const horizon = st.id === 'chirality' || st.id === 'luca' ? 200 : 12;   // symmetry-breaking / core formation take ~150 gens
    run(rule, g, horizon);
    ok(g.generation === horizon, `${st.id}: steps under the lab clock`);
    ok(!g.cells.every((v, i) => v === before[i]) && g.population() > 0, `${st.id}: the projected lattice evolves and holds a specimen by gen ${horizon}`);
    const H = rule.height(new Float32Array(g.size));
    let lo = 1, hi = 0; for (let i = 0; i < H.length; i++) { if (H[i] < lo) lo = H[i]; if (H[i] > hi) hi = H[i]; }
    ok(lo >= 0 && hi <= 1 + 1e-6 && hi - lo > 0.1, `${st.id}: renderHeight is a [0,1] field with relief (${lo.toFixed(2)}–${hi.toFixed(2)})`);
    ok(typeof rule.readout() === 'string' && rule.readout().length > 0, `${st.id}: has a stage readout ("${rule.readout().slice(0, 40)}")`);
    const pres = presetsOf(fam, values);
    ok(pres.every((p) => p.values.stage === st.id), `${st.id}: ${pres.length} regimes carry the stage`);
  }
  // Seeded replay: the same seed reproduces a stage exactly; a different seed differs.
  for (const id of ['soup', 'grayscott', 'rna', 'life']) {
    const mk = (seed) => { const r = fam.make(valuesOf(fam, { stage: id })); const g = new Grid(r.fixedSize.width, r.fixedSize.height); r.init(g, mulberry32(seed)); run(r, g, 8); return g.cells; };
    const a = mk(11), b = mk(11), c = mk(12);
    ok(a.every((v, i) => v === b[i]), `${id}: same seed ⇒ identical run (Math.random is swapped for the seeded generator)`);
    ok(!c.every((v, i) => v === a[i]), `${id}: different seed ⇒ different run`);
  }
  // Knobs are live through the adapter: Gray–Scott's Pearson regime (an enum
  // param) cascades into F,k via onParamChange; vents' PMF gates carbon fixation.
  const gsSchema = schemaOf(fam, { stage: 'grayscott' });
  ok(gsSchema.preset && gsSchema.preset.type === 'enum' && gsSchema.F && gsSchema.k, 'grayscott exposes Pearson preset + F + k through the schema');
  const gs0 = fam.make(valuesOf(fam, { stage: 'grayscott' }));
  const F0 = gs0.inner.params.F.value, k0 = gs0.inner.params.k.value;
  const alt = gsSchema.preset.options.find((o) => o && o !== gsSchema.preset.value);
  const gs1 = fam.make(valuesOf(fam, { stage: 'grayscott', preset: alt }), ['preset']);
  ok(gs1.inner.params.F.value !== F0 || gs1.inner.params.k.value !== k0, `Pearson regime "${alt}" cascades into F/k through onParamChange`);
  const back = fam.make(valuesOf(fam, { stage: 'grayscott', F: 0.05 }), ['F']);
  ok(back.inner.params.F.value === 0.05 && back.inner.params.preset.value === '', 'a hand-set F drops the regime to custom (cascade in the other direction)');
  const sigmaA = (pmf) => { const r = fam.make(valuesOf(fam, { stage: 'vents', pmf }), ['pmf']); const g = new Grid(r.fixedSize.width, r.fixedSize.height); r.init(g, mulberry32(1)); run(r, g, 250); const m = r.readout().match(/ΣA\s+(\d+)/); return m ? +m[1] : -1; };
  ok(sigmaA(0.6) > 20 && sigmaA(0) === 0, 'vents: PMF knob gates acetate fixation through the adapter (ΣA>0 at 0.6, =0 at 0)');
  const wrong = fam.make(valuesOf(fam, { stage: 'luca' }));
  let threw = false; try { wrong.init(new Grid(10, 10), mulberry32(1)); } catch { threw = true; } ok(threw, 'a stage refuses a lattice of the wrong size');
  ok(palette('abiogenesis', abiogenesis.LEVELS).length === abiogenesis.LEVELS, 'abiogenesis relief palette');
  ok(fam.presets.length >= 30, `all-stage regime list has ${fam.presets.length} entries`);
}

// ── 13. Registry contract (what the rule desk is generated from) ────────────
section('registry');
{
  ok(FAMILIES.length === 7, 'seven families registered');
  for (const f of FAMILIES) {
    ok(f.id && f.name && f.blurb && f.params && Array.isArray(f.presets) && typeof f.make === 'function' && typeof f.validate === 'function', `${f.id}: id/name/blurb/params/presets/make/validate`);
    ok(f.presets.length >= 3, `${f.id}: ≥3 named regimes (${f.presets.length})`);
    ok(f.validate(valuesOf(f)) === null, `${f.id}: default values validate`);
    const rule = f.make(valuesOf(f));
    ok(rule.family === f.id && rule.states >= 2 && typeof rule.step === 'function' && typeof rule.describe() === 'string', `${f.id}: make() yields a rule with family/states/step/describe`);
    for (const p of f.presets) {
      ok(typeof p.label === 'string' && p.label && p.values && typeof p.values === 'object', `${f.id} preset "${p.label}" has label + values`);
      for (const k of Object.keys(p.values)) {
        const spec = schemaOf(f, p.values)[k];
        ok(!!spec, `${f.id} preset "${p.label}" sets a real param "${k}"`);
        if (spec && spec.type === 'number') ok(p.values[k] >= spec.min && p.values[k] <= spec.max, `${f.id} preset "${p.label}" ${k}=${p.values[k]} within [${spec.min},${spec.max}]`);
        if (spec && spec.type === 'enum') ok(spec.options.includes(p.values[k]), `${f.id} preset "${p.label}" ${k} is a listed option`);
      }
      const merged = Object.assign(valuesOf(f, p.values), p.values);
      ok(f.validate(merged) === null, `${f.id} preset "${p.label}" validates`);
      if (p.pattern) ok(!!byId(p.pattern), `${f.id} preset "${p.label}" pattern "${p.pattern}" exists in the library`);
    }
    // every family steps a soup without throwing and changes something
    const g = rule.fixedSize ? new Grid(rule.fixedSize.width, rule.fixedSize.height) : new Grid(48, 48); const rng = mulberry32(8);
    if (rule.init) rule.init(g, rng); else g.randomize(rng, f.soupDensity || 0.35, rule.states);
    if (f.defaultPattern) g.stampCentered(libraryPattern(byId(f.defaultPattern)));
    const before = g.cells.slice(); run(rule, g, 5);
    ok(!g.cells.every((v, i) => v === before[i]) && g.generation === 5, `${f.id}: evolves from its default state`);
    ok(g.cells.every((v) => v < rule.states), `${f.id}: every state < rule.states`);
    const pal = palette(f.id, rule.states);
    ok(pal.length === rule.states && pal.every((c) => c.length === 3), `${f.id}: palette has one colour per state`);
  }
  ok(familyById('lifelike') === FAMILIES[0] && familyById('nope') === null, 'familyById');
}

if (fails.length) { console.error(`\n${fails.length} FAILURE(S):\n - ` + fails.join('\n - ')); process.exit(1); }
console.log(`\n${pass} checks passed, 0 failures`);
