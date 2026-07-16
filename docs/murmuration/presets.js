// Murmuration — regime presets.
//
// Each preset is a full parameter override that pushes the same model into a
// qualitatively different flock, the way tuning real starling parameters moves
// you between a tight defensive ball and a loose migratory ribbon. They are the
// "regime picker" that the rest of the lab exposes for every rule.
//
// Only the keys listed are overridden; anything omitted keeps the model default
// (see PARAMS in flock.js). `id` is used in the share-URL hash.

export const PRESETS = [
  {
    id: 'dusk',
    name: 'Starling dusk',
    blurb: 'A balanced evening murmuration over the roost — the model at rest.',
    params: {
      birds: 1200, viewRadius: 16, fov: 300, neighbors: 7,
      separation: 1.5, alignment: 1.2, cohesion: 1.6, sepRadius: 4,
      boundary: 110, boundaryPull: 1.0, wind: 0,
      cruiseSpeed: 12, maxSpeed: 22, minSpeed: 7, maxBank: 45,
      agility: 1.6, liftComp: 0.5, power: 1.4, predator: 0,
    },
  },
  {
    id: 'ball',
    name: 'Defensive ball',
    blurb: 'High cohesion and personal space knot the flock into a dense sphere.',
    params: {
      birds: 1500, viewRadius: 20, fov: 320, neighbors: 9,
      separation: 2.0, alignment: 0.8, cohesion: 2.0, sepRadius: 5,
      boundary: 80, boundaryPull: 1.6, wind: 0,
      cruiseSpeed: 11, maxSpeed: 20, minSpeed: 7, maxBank: 55,
      agility: 2.2, liftComp: 0.6, power: 1.5, predator: 0,
    },
  },
  {
    id: 'sheet',
    name: 'Loose sheet',
    blurb: 'Strong alignment, weak cohesion — a broad, thin, rippling curtain.',
    params: {
      birds: 1400, viewRadius: 22, fov: 300, neighbors: 6,
      separation: 1.2, alignment: 2.2, cohesion: 0.35, sepRadius: 4.5,
      boundary: 150, boundaryPull: 0.7, wind: 0,
      cruiseSpeed: 14, maxSpeed: 24, minSpeed: 8, maxBank: 40,
      agility: 1.2, liftComp: 0.45, power: 1.3, predator: 0,
    },
  },
  {
    id: 'waves',
    name: 'Orientation waves',
    blurb: "The paper's headline: agile, tightly-coupled birds pass turning waves through the flock unprompted.",
    params: {
      birds: 1800, viewRadius: 14, fov: 320, neighbors: 8,
      separation: 1.6, alignment: 1.8, cohesion: 1.3, sepRadius: 3.5,
      boundary: 95, boundaryPull: 1.2, wind: 0,
      cruiseSpeed: 13, maxSpeed: 24, minSpeed: 7, maxBank: 60,
      agility: 2.8, liftComp: 0.4, power: 1.6, predator: 0,
    },
  },
  {
    id: 'panic',
    name: 'Predator panic',
    blurb: 'A peregrine stoops through the roost — watch the flash-expansion and the bait ball.',
    params: {
      birds: 1600, viewRadius: 16, fov: 320, neighbors: 8,
      separation: 1.7, alignment: 1.3, cohesion: 1.2, sepRadius: 4,
      boundary: 105, boundaryPull: 1.1, wind: 0,
      cruiseSpeed: 13, maxSpeed: 26, minSpeed: 7, maxBank: 65,
      agility: 3.0, liftComp: 0.4, power: 1.7,
      predator: 1, fear: 4.0, fearRadius: 34,
    },
  },
  {
    id: 'migration',
    name: 'Migration line',
    blurb: 'Weak cohesion, dominant alignment and a steady crosswind draw the flock into a streaming ribbon.',
    params: {
      birds: 900, viewRadius: 24, fov: 280, neighbors: 5,
      separation: 1.1, alignment: 2.6, cohesion: 0.3, sepRadius: 5,
      boundary: 180, boundaryPull: 0.5, wind: 5,
      cruiseSpeed: 16, maxSpeed: 28, minSpeed: 9, maxBank: 35,
      agility: 1.0, liftComp: 0.55, power: 1.4, predator: 0,
    },
  },
];

export const PRESET_BY_ID = Object.fromEntries(PRESETS.map((p) => [p.id, p]));

export default PRESETS;
