// web8 — unit tests for the intent parser (zero-dep, node).
import { parseIntent, SUGGESTIONS } from '../intents.js';

let pass = 0,
  fail = 0;
function eq(got, want, msg) {
  const a = JSON.stringify(got),
    b = JSON.stringify(want);
  if (a === b) pass++;
  else {
    fail++;
    console.error(`  ✗ ${msg}\n      got  ${a}\n      want ${b}`);
  }
}

console.log('Running web8 intent-parser tests…\n');

eq(parseIntent('run'), { kind: 'run', value: true }, 'run');
eq(parseIntent('please start it'), { kind: 'run', value: true }, 'start');
eq(parseIntent('stop'), { kind: 'run', value: false }, 'stop');
eq(parseIntent('pause the experiment'), { kind: 'run', value: false }, 'pause');
eq(parseIntent('step'), { kind: 'step' }, 'step');
eq(parseIntent('reset it'), { kind: 'reset' }, 'reset');
eq(parseIntent('faster'), { kind: 'speed', value: 'up' }, 'faster');
eq(parseIntent('slow down please'), { kind: 'speed', value: 'down' }, 'slower');
eq(parseIntent('split view'), { kind: 'view', value: 'split' }, 'split');
eq(parseIntent('show just the micrograph'), { kind: 'view', value: 'exp' }, 'micrograph view');
eq(parseIntent('lab only'), { kind: 'view', value: 'lab' }, 'lab view');
eq(parseIntent('take it apart'), { kind: 'explode', value: 1 }, 'explode');
eq(parseIntent('put it back together'), { kind: 'explode', value: 0 }, 'assemble');
eq(parseIntent('next'), { kind: 'stage', value: 'next' }, 'next');
eq(parseIntent('go back'), { kind: 'stage', value: 'prev' }, 'prev');
eq(parseIntent('show me the RNA world'), { kind: 'stage', value: 'stage7-rna' }, 'switch rna');
eq(parseIntent('vesicles'), { kind: 'stage', value: 'stage3-vesicles' }, 'bare stage name');
eq(parseIntent('what is this?'), { kind: 'explain', value: null }, 'explain current');
eq(parseIntent('what is the rna world'), { kind: 'explain', value: 'stage7-rna' }, 'explain a stage');
eq(parseIntent('help'), { kind: 'help' }, 'help');
eq(parseIntent('flibbertigibbet'), { kind: 'unknown' }, 'unknown');
eq(parseIntent(''), { kind: 'noop' }, 'empty');

if (!Array.isArray(SUGGESTIONS) || SUGGESTIONS.length < 4) {
  fail++;
  console.error('  ✗ SUGGESTIONS missing/short');
} else pass++;

console.log(`\nintents: ${pass} passed, ${fail} failed.`);
process.exit(fail ? 1 : 0);
