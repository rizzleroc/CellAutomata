// The roster — every organism the sample can contain, floor to ceiling of the
// microscopic food web. Ordered by real size so the specimen picker reads as a
// climb up the ladder of complexity: prokaryote → protist → the metazoans.

import { meta as bacterium } from './bacterium.js';
import { meta as paramecium } from './paramecium.js';
import { meta as rotifer } from './rotifer.js';
import { meta as tardigrade } from './tardigrade.js';
import { meta as nematode } from './nematode.js';
import { meta as daphnia } from './daphnia.js';

export const ROSTER = [bacterium, paramecium, rotifer, tardigrade, nematode, daphnia];
export const BY_ID = Object.fromEntries(ROSTER.map((m) => [m.id, m]));
