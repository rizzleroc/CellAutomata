// web8 — turn a natural request into ONE whitelisted lab action. Pure (no DOM),
// so it unit-tests under node and runs in the browser. The guide executes the
// returned action against the WEB8 bridge; nothing here can touch anything the
// user couldn't reach by hand.

// stage keyword → registered stage id (matches main.js STAGES ids).
const STAGE_KEYWORDS = [
  [/\b(soup|miller|urey|primordial|spark|stage\s*0)\b/, 'stage0-miller-urey'],
  [/(reaction.?diffusion|gray.?scott|turing|stage\s*1)\b/, 'stage1-grayscott'],
  [/\b(autocatalytic|autocatalysis|raf|kauffman|stage\s*2)\b/, 'stage2-raf'],
  [/\b(vesicle|vesicles|lipid|micelle|stage\s*3)\b/, 'stage3-vesicles'],
  [/\b(vent|hydrothermal|alkaline|chemiosmo\w*|proton|stage\s*4)\b/, 'stage4-vent'],
  [/\b(mineral|minerals|clay|montmorillonite|stage\s*5)\b/, 'stage5-minerals'],
  [/\b(chirality|chiral|homochirality|soai|handed\w*|stage\s*6)\b/, 'stage6-chirality'],
  [/\b(rna|ribozyme|stage\s*7)\b/, 'stage7-rna'],
  [/\b(genetic.?code|\bcode\b|translation|codon|ribosome|stage\s*8)\b/, 'stage8-code'],
  [/\b(coacervate|coacervates|oparin|droplet|stage\s*9)\b/, 'stage9-coacervate'],
  [/\b(protocell|selection|microfluidic|hypercycle|stage\s*10)\b/, 'stage10-selection'],
  [/\b(luca|last universal|tree of life|stage\s*11)\b/, 'stage11-luca'],
  [/\b(stromatolite|capstone|fossil)\b/, 'capstone-stromatolite'],
];

function stageOf(t) {
  for (const [re, id] of STAGE_KEYWORDS) if (re.test(t)) return id;
  return null;
}

export function parseIntent(text) {
  const t = (text || '').toLowerCase().trim();
  if (!t) return { kind: 'noop' };
  const has = (re) => re.test(t);
  const stageId = stageOf(t);

  if (has(/\b(help|what can you|what do you do|commands?|options)\b/)) return { kind: 'help' };

  // A question (what/why/how/explain/?) → narrate (the named stage, or the current one).
  if (has(/\b(what|why|how|explain|describe|tell me|meaning)\b/) || t.includes('?')) {
    return { kind: 'explain', value: stageId || null };
  }

  if (has(/\b(stop|pause|halt|freeze)\b/)) return { kind: 'run', value: false };

  // Assemble/explode before nav, so "put it back together" isn't read as "back".
  if (has(/\b(explode|exploded|take .*apart|pull apart|disassemble|apart)\b/)) return { kind: 'explode', value: 1 };
  if (has(/\b(assemble|reassemble|together|whole|intact)\b/)) return { kind: 'explode', value: 0 };

  // Explicit "go to / show <stage>" beats the generic run/go verb.
  if (stageId && has(/\b(show|go to|goto|switch|switch to|load|open|take me|jump|navigate)\b/)) {
    return { kind: 'stage', value: stageId };
  }
  if (has(/\b(next|forward|advance)\b/)) return { kind: 'stage', value: 'next' };
  if (has(/\b(previous|prev|back|before)\b/)) return { kind: 'stage', value: 'prev' };

  if (has(/\b(run|start|play|resume|begin|^go$|^go )\b/)) return { kind: 'run', value: true };
  if (has(/\bstep\b/)) return { kind: 'step' };
  if (has(/\b(reset|reseed|restart|again)\b/)) return { kind: 'reset' };

  if (has(/\b(faster|speed up|quicker|hurry|fast)\b/)) return { kind: 'speed', value: 'up' };
  if (has(/\b(slower|slow down|slow|calm)\b/)) return { kind: 'speed', value: 'down' };

  if (has(/(micrograph|microscope|\bsem\b|specimen only|micro only|just the micrograph)/)) return { kind: 'view', value: 'exp' };
  if (has(/(apparatus only|lab only|just the lab|3d only|only the apparatus)/)) return { kind: 'view', value: 'lab' };
  if (has(/\b(split|both|side by side)\b/)) return { kind: 'view', value: 'split' };

  // bare stage name with no verb → switch to it.
  if (stageId) return { kind: 'stage', value: stageId };

  return { kind: 'unknown' };
}

// chips the guide offers — label shown, text fed back through parseIntent.
export const SUGGESTIONS = [
  { label: 'Explain this', text: 'what is this?' },
  { label: 'Run it', text: 'run' },
  { label: 'Faster', text: 'faster' },
  { label: 'Split view', text: 'split' },
  { label: 'Next stage', text: 'next' },
  { label: 'RNA world', text: 'go to rna world' },
];
