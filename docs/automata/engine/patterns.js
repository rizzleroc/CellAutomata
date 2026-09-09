// patterns.js — the pattern library and the two interchange formats.
//
// RLE (run-length encoded, the LifeWiki/Golly standard): `b` dead, `o` alive,
// `$` end of row, `!` end of pattern, a leading integer is a run count. The
// multi-state extension uses `.` for 0 and `A`..`X` for states 1..24.
// PLAIN text: one row per line; `.` = 0, `O`/`#`/`*` = 1, digits 2–9 and
// letters used by Wireworld (`#` wire, `H` head, `T` tail) for higher states.

export function parseRLE(text) {
  const lines = String(text).split(/\r?\n/).filter((l) => l.trim() && !l.startsWith('#'));
  let width = 0, height = 0, rule = null;
  let body = '';
  for (const l of lines) {
    const hdr = l.match(/^x\s*=\s*(\d+)\s*,\s*y\s*=\s*(\d+)(?:\s*,\s*rule\s*=\s*(\S+))?/i);
    if (hdr) { width = +hdr[1]; height = +hdr[2]; rule = hdr[3] || null; } else body += l.trim();
  }
  const rows = [[]]; let run = '';
  outer: for (const ch of body) {
    if (/[0-9]/.test(ch)) { run += ch; continue; }
    const n = run ? +run : 1; run = '';
    switch (true) {
      case ch === 'b' || ch === '.': rows[rows.length - 1].push(...new Array(n).fill(0)); break;
      case ch === 'o': rows[rows.length - 1].push(...new Array(n).fill(1)); break;
      case /[A-X]/.test(ch): rows[rows.length - 1].push(...new Array(n).fill(ch.charCodeAt(0) - 64)); break;
      case ch === '$': for (let i = 0; i < n; i++) rows.push([]); break;
      case ch === '!': break outer;
      default: throw new SyntaxError(`bad RLE token "${ch}"`);
    }
  }
  while (rows.length && rows[rows.length - 1].length === 0) rows.pop();
  const w = Math.max(width, ...rows.map((r) => r.length), 1);
  const h = Math.max(height, rows.length, 1);
  const cells = new Uint8Array(w * h);
  rows.forEach((r, y) => r.forEach((v, x) => { cells[y * w + x] = v; }));
  return { width: w, height: h, cells, rule };
}

export function toRLE(pattern, ruleName) {
  const { width: w, height: h, cells } = pattern;
  const sym = (v) => (v === 0 ? 'b' : v === 1 ? 'o' : String.fromCharCode(64 + v));
  let out = `x = ${w}, y = ${h}${ruleName ? `, rule = ${ruleName}` : ''}\n`;
  let line = '';
  const emit = (n, s) => { line += (n > 1 ? n : '') + s; };
  let blankRows = 0;
  for (let y = 0; y < h; y++) {
    let x = 0, rowStr = '';
    // trim trailing dead cells in a row
    let end = w; while (end > 0 && !cells[y * w + end - 1]) end--;
    if (end === 0) { blankRows++; continue; }
    if (blankRows) { line += (blankRows + 1 > 2 ? blankRows + 1 : (blankRows + 1 === 2 ? '2' : '')) + '$'; blankRows = 0; }
    else if (y > 0) line += '$';
    while (x < end) {
      const v = cells[y * w + x]; let n = 1;
      while (x + n < end && cells[y * w + x + n] === v) n++;
      rowStr += (n > 1 ? n : '') + sym(v); x += n;
    }
    line += rowStr;
  }
  out += line + '!';
  return out;
}

export function parsePlain(text, { map } = {}) {
  const M = Object.assign({ '.': 0, ' ': 0, O: 1, o: 1, '*': 1, '#': 1, H: 2, T: 3 }, map || {});
  const rows = String(text).replace(/^\n+|\n+$/g, '').split('\n').map((r) => r.replace(/\s+$/, ''));
  const w = Math.max(...rows.map((r) => r.length), 1), h = rows.length;
  const cells = new Uint8Array(w * h);
  rows.forEach((r, y) => { for (let x = 0; x < r.length; x++) {
    const ch = r[x];
    const v = /[0-9]/.test(ch) ? +ch : (ch in M ? M[ch] : 0);
    cells[y * w + x] = v;
  } });
  return { width: w, height: h, cells };
}

// Crop a grid's live bounding box into a pattern (for RLE export).
export function fromGrid(grid) {
  const b = grid.bounds();
  if (!b) return { width: 1, height: 1, cells: new Uint8Array(1) };
  const cells = new Uint8Array(b.width * b.height);
  for (let y = 0; y < b.height; y++) for (let x = 0; x < b.width; x++) {
    cells[y * b.width + x] = grid.cells[(b.y0 + y) * grid.width + (b.x0 + x)];
  }
  return { width: b.width, height: b.height, cells };
}

// ── The library ─────────────────────────────────────────────────────────────
// Each entry: id, name, family it belongs to, rule hint, the pattern, and what
// it demonstrates. The engine test locks the ones with known dynamics.
export const LIBRARY = [
  { id: 'glider',      family: 'lifelike', rule: 'B3/S23', name: 'Glider',           period: 4, speed: 'c/4 diagonal', rle: 'bob$2bo$3o!' },
  { id: 'lwss',        family: 'lifelike', rule: 'B3/S23', name: 'Lightweight spaceship', period: 4, speed: 'c/2 orthogonal', rle: 'bo2bo$o4b$o3bo$4o!' },
  { id: 'rpentomino',  family: 'lifelike', rule: 'B3/S23', name: 'R-pentomino',      note: 'Five cells that take 1103 generations to settle.', rle: 'b2o$2ob$bo!' },
  { id: 'acorn',       family: 'lifelike', rule: 'B3/S23', name: 'Acorn',            note: 'Seven cells; 5206 generations of growth.', rle: 'bo5b$3bo3b$2o2b3o!' },
  { id: 'diehard',     family: 'lifelike', rule: 'B3/S23', name: 'Diehard',          note: 'Vanishes completely after 130 generations.', rle: '6bob$2o6b$bo3b3o!' },
  { id: 'gosper',      family: 'lifelike', rule: 'B3/S23', name: 'Gosper glider gun', period: 30, note: 'Emits a glider every 30 generations (Gosper 1970).', rle: '24bo$22bobo$12b2o6b2o12b2o$11bo3bo4b2o12b2o$2o8bo5bo3b2o$2o8bo3bob2o4bobo$10bo5bo7bo$11bo3bo$12b2o!' },
  { id: 'pulsar',      family: 'lifelike', rule: 'B3/S23', name: 'Pulsar',           period: 3, rle: '2b3o3b3o2b2$o4bobo4bo$o4bobo4bo$o4bobo4bo$2b3o3b3o2b2$2b3o3b3o2b$o4bobo4bo$o4bobo4bo$o4bobo4bo2$2b3o3b3o!' },
  { id: 'pentadecathlon', family: 'lifelike', rule: 'B3/S23', name: 'Pentadecathlon', period: 15, rle: '2bo4bo2b$2ob4ob2o$2bo4bo!' },
  { id: 'block',       family: 'lifelike', rule: 'B3/S23', name: 'Block',            period: 1, rle: '2o$2o!' },
  { id: 'blinker',     family: 'lifelike', rule: 'B3/S23', name: 'Blinker',          period: 2, rle: '3o!' },
  { id: 'beacon',      family: 'lifelike', rule: 'B3/S23', name: 'Beacon',           period: 2, rle: '2o$2o$2b2o$2b2o!' },
  { id: 'replicator',  family: 'lifelike', rule: 'B36/S23', name: 'HighLife replicator', period: 12, note: 'Copies itself every 12 generations.', rle: '2b3o$bo2bo$o3bo$o2bob$3o!' },
  { id: 'seedv',       family: 'lifelike', rule: 'B2/S',   name: 'Seeds chevron',    note: 'Five cells in a V are enough to ignite Seeds.', rle: '2bo$bo$o$bo$2bo!' },
  { id: 'ww_loop',     family: 'wireworld', name: 'Loop clock', period: 32, note: 'One electron circulating a 32-cell loop; a tap wire pulses once per lap.',
    plain: '.############.\n#............#\nH............#\nT............#\n#............#\n.############.\n.......#......\n.......#......\n.......#......' },
  { id: 'ww_diode',    family: 'wireworld', name: 'Diode', note: 'Electrons pass left→right (3-wire column, then the 2-wire column); the mirror image blocks them.',
    plain: '.......##.....\nTH######.#####\n.......##.....' },
  { id: 'ww_clocks',   family: 'wireworld', name: 'Two clocks', note: 'A 32-cell loop and a 24-cell loop, each tapping a wire: two different periods side by side.',
    plain: '.############....########.\n#............#..#........#\nH............#..H........#\nT............#..T........#\n#............#..#........#\n.############....########.\n.......#...........#......\n.......#...........#......\n.......#...........#......' },
];

export function libraryPattern(entry) {
  if (entry.rle) return parseRLE(entry.rle);
  if (entry.plain) return parsePlain(entry.plain);
  throw new Error(`library entry ${entry.id} has no pattern`);
}
export const byId = (id) => LIBRARY.find((p) => p.id === id) || null;
