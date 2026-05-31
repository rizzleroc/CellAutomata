# Post — Reddit viral launch: "Monkeys at keyboards" (Conway methuselah search)

**Goal:** a high-engagement Reddit post (comments + upvotes) for the CA work.
**Primary asset:** `media/magic_5650.mp4` (24s smooth Conway methuselah, gen counter on-screen).
**Reach asset:** `media/mandala_morph.mp4` (oddly-satisfying mandala loop).
**Date drafted:** 2026-05-31 · *Drafts only — for a human to publish. Nothing auto-posts.*

---

## 0) What the research says actually drives engagement (the MVP)

Distilled from current Reddit-virality guidance (sources at bottom) + the
subreddit norms in `CONTENT_PLAN.md`:

1. **Format:** a **native video/image post beats a text post** (link/media posts
   pull the large majority of top-performers and far more upvotes). Reddit
   **autoplays** native video — lead with motion.
2. **Title:** **60–90 chars**, state a **surprising FACT with a number**, tag
   `[OC]`. Statements earn upvotes; a body that ends in a **question** earns
   comments (~2× more). Do both: factual title, question in the body.
3. **First-30-minutes momentum is everything** — the algorithm rewards early
   velocity (50 upvotes in 30 min > 200 over 12 h). Post at peak
   (**Tue–Thu, 9–11 AM ET**) and **reply to every comment in the first hour.**
4. **Authenticity > marketing.** "I made this," first person, no brand voice.
   **Put the repo link in your FIRST COMMENT, not the body** (self-posts with a
   naked link get throttled/buried; a value-add comment doesn't).
5. **Skim-friendly:** short paragraphs, one hook, one ask. No wall of text.
6. **OC flair** where the sub offers it; it signals you made it.

**MVP checklist before hitting post:** native video ✔ · `[OC]` title with a
number ✔ · one genuine question ✔ · link queued for first comment ✔ · posted
Tue–Thu 9–11 ET ✔ · you're free for the next 60 min to reply ✔

---

## 1) HERO POST — r/cellular_automata  (engagement play)

> Niche but high-intent; it will dissect the method and upvote genuine OC.
> **Crossposts after it gains traction:** r/conwaysgameoflife, r/proceduralgeneration, r/generative, r/alife.

**Attach:** `media/magic_5650.mp4` (native upload, not a link).
**Flair:** `OC` (or `Discussion`).

**Title (pick one — A is the lead):**

- **A.** `I searched 6,000 random Game of Life soups — the longest-lived ran for 8,798 generations [OC]`
- B. `Monkeys at keyboards, for Conway: a 36-cell random scribble that stays alive 8,798 generations [OC]`
- C. `~10% of random Game of Life soups never settle. Here's the wildest survivor I found. [OC]`

**Body:**

> I got curious how long a *random* Game of Life pattern can stay chaotically
> alive before it collapses into still-lifes and blinkers — so I did the
> "monkeys at typewriters" thing and let a computer spray random soups.
>
> **Setup:** 6,000 random 22×22 soups on a toroidal grid, plain B3/S23. Each one
> scored by how many generations it keeps *meaningfully changing* before it
> falls into a cycle.
>
> **What came out:**
> - Not one died on the spot — but most settle within a few hundred generations.
> - **~10% (623/6,000) were still going at my 2,200-gen cutoff.**
> - Re-running the survivors with a higher cap, the champion is a **36-cell
>   scribble that churns for 8,798 generations**, peaking at **1,081 live cells**,
>   before finally dropping into period-2 blinkers.
>
> The clip is one of them (generation counter on screen — those streaks are
> gliders leaving comet trails in the render).
>
> Every find is deterministic — reproducible from a single integer seed.
>
> **Two things I genuinely can't answer and want your take on:**
> 1. On an N×N torus the state space is finite, so *everything* must eventually
>    cycle. Is there any known bound on the longest pre-cycle **transient** for a
>    given grid size?
> 2. Are bounded-grid (toroidal) methuselah records tracked anywhere? apgsearch
>    is infinite-plane — has anyone hunted long transients on a fixed torus?
>
> (Code's open source, Python/MIT — I'll drop it + the champion seed in a comment.)

**Your FIRST comment (post it within ~60s, then reply to everyone):**

> Method's about 50 lines of numpy (vectorised B3/S23 with `np.roll`, cycle
> detection by hashing each generation's grid). Built on a little open-source CA
> sandbox I've been working on. Repo + the exact seed to reproduce the 8,798-gen
> champion: https://github.com/rizzleroc/CellAutomata
>
> Reproduce the champion: `seed=917, grid=120, 36×36 soup, density 0.40` (or
> `seed=5650` for the one in the clip). Happy to share the full list of
> long-lived seeds if people want to verify or beat them.

**Engagement plan:** be at the keyboard for 60 min after posting; reply to every
comment; ask follow-ups ("want the seed?"); if it clears ~50 upvotes in the
first hour, crosspost to r/conwaysgameoflife and r/proceduralgeneration.

---

## 2) REACH POST — r/oddlysatisfying  (broad-virality play)

> Huge audience; shallow comments but massive upvote ceiling. Run this
> *separately* (different day) once the hero post validates the asset.
> **Crossposts:** r/woahdude, r/generative, r/mandalas, r/sacredgeometry.

**Attach:** `media/mandala_morph.mp4` (ideally trimmed to a clean ~15–25s loop).
**Flair:** `OC`.

**Title (lead = A):**

- **A.** `I turned a chemistry simulation into a mandala that never stops morphing [OC]`
- B. `Reaction-diffusion "chemistry," folded into symmetry — the petals split and merge forever [OC]`

**Body (oddlysatisfying wants almost none):**

> Each frame is a live Gray-Scott reaction-diffusion field folded into n-fold
> symmetry. The symmetry count is what's morphing — petals literally split and
> merge as it sweeps 6→7→8… No two frames repeat. [OC]
>
> Which symmetry order is your favorite as it goes by?

**First comment:** repo link + "it's an open-source CA sandbox, happy to explain
how the fold works."

---

## 3) Why this is the right call (mapping assets → subs)

| Asset | Hook | Best sub | Drives |
|---|---|---|---|
| `magic_5650.mp4` (methuselah) | "8,798 gens from a random scribble" + open question | r/cellular_automata | **comments / discussion** |
| `mandala_morph.mp4` (sacred geometry) | hypnotic, never-repeats | r/oddlysatisfying, r/woahdude | **reach / upvotes** |
| `monkeys_hall.mp4` (3×2 hall of fame) | leaderboard of survivors | r/conwaysgameoflife | backup / crosspost |
| `complex_reactions.mp4` | "spatiotemporal chaos" | r/generative | backup |

**Do NOT:** post all of these at once, use a salesy tone, put the link in the
body, or post-and-ghost. One asset, one sub, one hour of presence.

---

## Sources (Reddit virality, May 2026)
- Conbersa — Reddit engagement tips: https://www.conbersa.ai/learn/reddit-engagement-tips
- Single Grain — creating viral Reddit posts: https://www.singlegrain.com/digital-marketing-strategy/creating-viral-reddit-posts-content-ideas-that-drive-engagement/
- ALM Corp — Reddit brand-engagement trends 2026: https://almcorp.com/blog/reddit-brand-engagement-trends-2026/
