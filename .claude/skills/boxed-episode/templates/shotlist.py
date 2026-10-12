#!/usr/bin/env python3
"""BOXED shot list (TEMPLATE; SHOTS below are the Ep4 worked example) -> timeline.json["shots"]. Each shot starts at an anchor (line/slot start) and runs to the next shot."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
EP = os.path.dirname(HERE)
TL = json.load(open(os.path.join(EP, "timeline.json")))
L = {l["id"]: l for l in TL["lines"]}
S = {s["id"]: s for s in TL["slots"]}


def at(a, off=0.0):
    kind, k = a.split(":")
    return (L[k]["t0"] if kind == "L" else S[k]["t0"]) + off


SHOTS = [  # (id, start anchor, owner, description)
    ("T001_dark_open", "S:COLD_IN", "main", "Pitch-black studio. Only the host's CRT glow lights him (whispering C01) and a huge back wall; Zee barely visible in the spill, whispering C02."),
    ("T002_bunny", "L:C03", "main", "C03-C06: host's glow throws his shadow on the wall; he makes a hand-shadow BUNNY that hops on the wall; Gary's glowing eye in the dark audience ('Ooooh! the wall is doing a bunny'); 'That's my hand, Gary.'; Gary awestruck."),
    ("T003_roll_titles", "L:C07", "main", "C07: Zee in the dark giggles 'Roll the titles!' -> snap."),
    ("T004_title", "S:TITLE", "main", "BOXED title card, cave edition: EPISODE FOUR / THE CAVE, firelight, stalactite drips, the cast as shadow puppets."),
    ("T005_lights_up", "S:LIGHTS_UP", "main", "Lights slam on: wide studio + audience; H01 welcome."),
    ("T006_host_recap", "L:H02", "main", "H02 host recap with mini-callbacks to ep1-3 on inset screens."),
    ("T007_welcome", "L:H03", "main", "H03 + APPLAUSE: wide; Zee waves, audience cheers."),
    ("T008_zee_bunny", "L:Z01", "main", "Z01 Zee CU, sorry about the bunny; G00 Gary sniffles in the audience."),
    ("T009_host_plato", "L:H04", "main", "H04 host CU with cue card."),
    ("T010_zee_allegory", "L:Z02", "main", "Z02 Zee CU; 'and it starts... in the dark' - the studio lights die at the end."),
    ("T011_cave_in", "S:CAVE_IN", "cave", "CAVE_IN: transition from the dark studio into the cave - a fall through darkness into an immense cavern; painted title THE CAVE."),
    ("T012_cave_reveal", "L:Z03", "cave", "Z03-Z04: the huge cave deep underground; a row of chained prisoners (cute-creepy eyeball creatures, the BOXED audience) sitting facing the wall, legs and necks chained, since childhood; they can only see the wall."),
    ("T013_host_yikes", "L:H05", "main", "H05 host reaction CU 'Since they were kids? Yikes.'"),
    ("T014_fire_wall", "L:Z05", "cave", "Z05-Z06: the fire behind the prisoners, the low wall like a puppet screen, carriers walking behind it holding statues (animals, people, trees); the fire throws their shadows on the cave wall."),
    ("T015_host_puppets", "L:H06", "main", "H06 host 'So it's a shadow puppet show.'"),
    ("T016_only_shadows", "L:Z07", "cave", "Z07-Z08: prisoners' POV - only shadows, never the fire, puppets or each other; carriers talk, the echo bounces off the wall, so speech bubbles seem to come from the shadows."),
    ("T017_strange", "L:H07", "main", "H07 host 'What a strange image. And what strange prisoners.'"),
    ("T018_like_ourselves", "L:Z09", "main", "Z09 'Like ourselves.' - dramatic Zee CU, then H08 host 'Sorry?', Z10 Zee + caption 'PLATO, REPUBLIC VII'."),
    ("T019_classic_plato", "L:H09", "main", "H09 host nervous laugh 'Classic Plato. Always kidding.'"),
    ("T020_shadowplay", "S:SHADOWPLAY", "cave", "SHADOWPLAY + Z11: the shadow show as the prisoners' whole world: they name the shadows, study them, hand out honours (laurels/medals) to the best guesser."),
    ("T021_gameshow_idea", "L:H10", "main", "H10 host: 'Prizes? For guessing? ...that's a GAME SHOW.' lights flash."),
    ("T022_gameshow", "S:GAMESHOW_IN", "game", "GAMESHOW_IN + S01-S04: 'GUESS THAT SHADOW!' game show inside the cave; host as quizmaster, Gary chained to a contestant podium; the wall shows a bunny then a horse; CORRECT! confetti; prize 'a lifetime supply of more shadows'; Gary sobs with joy."),
    ("T023_set_free", "L:Z12", "escape", "Z12: one prisoner (Gary) is set free - chains unlocked, made to stand up and turn around."),
    ("T024_volunteer", "L:H11", "main", "H11 + SPOTLIGHT: host asks for a volunteer, a spotlight slams onto Gary in the audience."),
    ("T025_gary_eager", "L:G01", "main", "G01 Gary in the spotlight, eager: 'Is it more bunnies?'"),
    ("T026_fire_hurts", "L:Z13", "escape", "Z13 + G02: Gary turns to the fire - blinding pain; 'MY EVERYTHING! I'm one big eye!'"),
    ("T027_puppets_reveal", "L:Z14", "escape", "Z14 + G03: someone points at the puppets: everything was a shadow of these; Gary refuses: 'The shadows were way better. Put me back.'"),
    ("T028_relatable", "L:H12", "main", "H12 host deadpan to camera: 'Honestly? Relatable.'"),
    ("T029_dragged", "L:Z15", "escape", "Z15 + ASCENT + G04: dragged up a long steep rocky path out of the cave into blinding sunlight; white-out; 'TOO MUCH OUTSIDE!'"),
    ("T030_adjust", "L:Z16", "sun", "Z16-Z18: eyes adjusting step by step: shadows -> reflections in water -> trees, flowers, people -> moon and stars at night -> morning."),
    ("T031_sun", "S:SUNRISE", "sun", "SUNRISE + P01 + G05 + Z19: the sun rises - the show's ringed planet with a sleepy face - 'Oh. Hey, Gary.'; Gary awestruck; the sun makes the seasons and years, lets you see anything, is behind everything... even the shadows."),
    ("T032_not_quite", "L:H13", "main", "H13 host moved; Z20 Zee 'Not quite.' (dramatic zoom, cliffhanger sting); H14 'We'll be right back!'"),
    ("T033_ad", "S:AD_IN", "ad", "AD_IN + A01-A04 + G06: 'CAVE PHONE PRO' infomercial: a cave wall that fits in your pocket, infinite scroll of shadows, SmartChains, Gary's neck-bent testimonial, rapid disclaimer."),
    ("T034_bumper", "S:BUMPER", "main", "BOXED station bumper."),
    ("T035_back", "L:H15", "main", "H15 host 'And we're back!'"),
    ("T036_remembers", "L:Z21", "return", "Z21 + H16: Gary in the sunshine remembers his chained friends, feels sorry for them, heads back down into the cave; H16 'A hero! The crowd goes wild!'"),
    ("T037_cant_see", "L:Z22", "game", "Z22 + RETURN + S05 + G07 + LAUGH: Gary back in the dark, eyes not adjusted - terrible at the shadow game: 'I can't see the bunny! There's a sun! It said hi to me!'; buzzer; prisoners laugh."),
    ("T038_mocked", "L:Z23", "return", "Z23: the prisoners mock him: he went up and came back with his eyes ruined; going up isn't worth thinking about."),
    ("T039_tough_crowd", "L:H17", "main", "H17 host 'Oof. Tough crowd.'"),
    ("T040_kill_him", "L:Z24", "return", "Z24: it gets darker - if anyone tried to free them and lead them up, and they could get their hands on him... they would kill him (menacing shadows, torches, no gore)."),
    ("T041_host_kill", "L:H18", "main", "H18 host 'KILL him?! For bringing them a sun?!'"),
    ("T042_socrates", "L:Z25", "return", "Z25: Socrates, Plato's teacher, asking uncomfortable questions in Athens; tried and sentenced to death in 399 BC (psychedelic Greek-vase style; hemlock cup, tasteful)."),
    ("T043_cave_fought", "L:H19", "main", "H19 + Z26: quiet two-shot, 'So the cave fought back.' 'The cave always fights back.'"),
    ("T044_ancient_history", "L:H20", "ad", "H20 + MODERN + H21: 'Nowadays nobody sits in the dark staring at flickering lights on a flat rectangle... for hours... believing whatever shows up' - modern montage: eyeball people in dark rooms lit by phones/TVs, chained by charging cables."),
    ("T045_flat_rectangle", "L:H22", "main", "H22 + Z27: the host realises he IS a flat rectangle (his screen fills with screens); Zee 'Mm-hm.'"),
    ("T046_meltdown", "L:H23", "main", "H23 + Z28 + H24: host meltdown (glitches, static), Zee deadpan 'You're a very efficient cave.'"),
    ("T047_every_wall", "L:Z29", "ad", "Z29-Z30: Plato isn't saying screens are evil; everybody watches some kind of wall: habits, feeds, assumptions - things never checked (montage of walls)."),
    ("T048_door", "L:H25", "main", "H25 host 'So how do we get out? Is there a door? Show me a door!'"),
    ("T049_education", "L:Z31", "out", "Z31-Z32: education isn't stuffing knowledge into empty heads (a funnel into a head - crossed out) - the power to see is already inside; learning is turning the whole soul around, away from the shadows, toward the light."),
    ("T050_thats_it", "L:H26", "main", "H26 + Z33 + H27: 'Turning around? That's it?' 'It's turning around... and asking: what's casting this shadow?' 'Okay. Here goes.'"),
    ("T051_turn", "S:TURN", "out", "TURN + H28 + Z34: the host's TV head slowly turns all the way around; the back wall of the BOXED set rumbles open onto a cave mouth with blazing sunrise beyond; 'Whoa. Has that always been there?' 'Always.'"),
    ("T052_outside", "S:OUTSIDE", "out", "OUTSIDE: the musical finale - host, Zee, Gary (sunglasses) and the whole unchained eyeball audience parade up out of the cave into a psychedelic sunrise; the smiling sun-planet; dancing."),
    ("T053_tag", "L:H29", "main", "H29-H31: sign-off outdoors in the sunshine: Gary in sunglasses 'Ten out of ten'; host thanks; Zee 'Turn around.'; 'And stay boxed!'"),
    ("T054_endcard", "S:ENDCARD", "main", "Endcard: BOXED ep.4 THE CAVE credits + STAY BOXED."),
    ("T055_stinger", "S:STINGER", "main", "Post-credits: pull back - the endcard is a shadow on a cave wall watched by chained eyeballs; G09 'Psst. Is the bunny coming back?'; the shadow bunny hops in; black."),
]
shots = []
for k, (sid, a, owner, desc) in enumerate(SHOTS):
    t0 = 0.0 if k == 0 else at(a)
    shots.append(dict(id=sid, t0=round(t0, 3), owner=owner, desc=desc))
for k in range(len(shots)):
    shots[k]["t1"] = shots[k + 1]["t0"] if k + 1 < len(shots) else TL["duration"]
TL["shots"] = [dict(id=s["id"], t0=s["t0"], t1=s["t1"], owner=s["owner"], desc=s["desc"]) for s in shots]
json.dump(TL, open(os.path.join(EP, "timeline.json"), "w"), indent=1)
from collections import defaultdict
tot = defaultdict(float)
for s in TL["shots"]:
    tot[s["owner"]] += s["t1"] - s["t0"]
    print(f"{s['id']:22s} {s['t0']:7.2f}-{s['t1']:7.2f} ({s['t1'] - s['t0']:5.1f}s) {s['owner']}")
print({k: round(v, 1) for k, v in tot.items()})
