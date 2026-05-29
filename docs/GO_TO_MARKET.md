# cellauto — Go-to-Market & Promotion Kit

*Where the users come from, in what order, and the exact copy to post.* Pair
with [MONETIZATION.md](MONETIZATION.md) and [PRICING.md](PRICING.md).

The strategy is **growth-led, not ads-led**: the free browser explorer and the
museum-grade visuals are inherently shareable. We point that at the channels
where curiosity + science + generative art already live, then convert the tail
to paid via the Preview Meter and Sponsors.

> Note: this kit is *copy and a plan you run*. Claude can't and won't post to
> external sites or create third-party accounts from this environment — the
> drafts below are ready for you to publish.

---

## 1. Positioning

> **cellauto turns the origin of life into something you can play with.** Drag
> two sliders and watch chemistry self-replicate, divide, and cross the line
> into biology — 12 scientifically-cited stages, from primordial soup to LUCA,
> running in your browser.

- **One-liner (consumer):** "Watch chemistry become life — in your browser."
- **One-liner (education):** "A citation-backed, NGSS-ready origin-of-life lab."
- **One-liner (art):** "Museum-grade generative plates from real abiogenesis sims."

---

## 2. Launch sequence (4 weeks)

| Week | Move | Goal |
|---|---|---|
| 0 | Enable **GitHub Sponsors**; ship pricing page + waitlist; run the **validation survey** (see VALIDATION_KIT). | Baseline demand + price signal. |
| 1 | **Show HN** + **r/cellular_automata**, r/proceduralgeneration, r/generative. | First spike of free users; gather feedback. |
| 2 | **Product Hunt** launch with the GIF + museum plates. | Broaden beyond the science crowd. |
| 3 | Education outreach: NSTA/teacher communities, r/Professors, museum/edu newsletters. | Seed Classroom/Institution pipeline. |
| 4 | Recap post + "what we learned"; turn on paid waitlist → first cohort. | Convert; iterate price from real data. |

Don't launch everywhere at once — each channel is a *separate* learning loop.

---

## 3. Channels (ranked by fit)

1. **Hacker News (Show HN)** — perfect audience overlap (science + CA + a clever
   web demo). The single highest-leverage launch.
2. **Reddit:** r/cellular_automata, r/proceduralgeneration, r/generative,
   r/compsci, r/abiogenesis, r/biology, r/Physics (lead with the GIF, not a sales pitch).
3. **Product Hunt** — for reach beyond developers; the visuals carry it.
4. **X/Bluesky/Mastodon** — the thread below; tag #genuary / generative-art and
   #sciart communities.
5. **Education:** NSTA, CommonSense Education, r/Professors, r/Teachers, science-
   museum educator mailing lists. Slow but high-ticket.
6. **YouTube/TikTok shorts** — a 20-second "chemistry divides into a cell" clip is
   tailor-made for the algorithm.
7. **SEO** — own "origin of life simulator", "abiogenesis simulation",
   "reaction diffusion online", "Gray-Scott explorer".

---

## 4. Ready-to-post copy

### Show HN
> **Show HN: cellauto – watch chemistry become life in your browser (12 cited stages)**
>
> I built an origin-of-life sandbox. The live demo runs the Gray-Scott
> reaction-diffusion PDE on a canvas — drag F and k and you get self-replicating,
> dividing "protocell" spots from four numbers. The full Python build walks 12
> scientifically-cited stages, coupled end to end: primordial soup → alkaline
> hydrothermal vents (real Wood-Ljungdahl chemistry) → autocatalytic sets
> (Kauffman/Hordijk-Steel) → homochirality → RNA world → genetic code → coacervates
> → vesicles → protocell selection (Eigen-Schuster ODE) → LUCA distillation.
>
> Every constant traces to a published measurement. MIT licensed; 141 tests.
> Live demo: [link] · Code: https://github.com/rizzleroc/CellAutomata
>
> Happy to talk about the science or the rendering.

### Reddit (r/cellular_automata / r/generative)
> **From four numbers to a dividing cell — a live Gray-Scott explorer (+ a 12-stage origin-of-life pipeline)**
>
> [GIF of mitosis preset]
>
> Two sliders (feed/kill) traverse the whole Pearson regime map — spots, stripes,
> mitosis, waves, labyrinth. It's the web front end of a bigger abiogenesis sim
> (soup → vents → RNA world → … → LUCA), all citation-backed and open source.
> No install, runs in the browser: [link]

### X / Bluesky thread
> 1/ Four numbers. One PDE. And you get cells that divide.
> This is the Gray-Scott reaction-diffusion equation Turing proposed in 1952 as
> the chemistry behind biological pattern. Live in your browser 👇 [link]
>
> 2/ It's the front door to cellauto — an origin-of-life sandbox that walks 12
> *cited* stages from primordial soup to LUCA, the last universal common
> ancestor. Real Wood-Ljungdahl chemistry, real Eigen-Schuster ODE.
>
> 3/ Free to play, open source, 141 tests. If you make science or generative art,
> the Pro tier exports 4K museum plates. ⭐ + sponsor: [repo]

### Education outreach email (cold, to a science teacher / dept.)
> Subject: A free, citation-backed origin-of-life lab for your class
>
> Hi [name] — I built cellauto, an interactive origin-of-life simulator. Students
> drag two sliders and watch chemistry self-replicate and divide; the full tool
> walks 12 stages from primordial soup to LUCA, each tied to the primary
> literature. It's free to use in the browser and as a desktop app.
>
> I'm putting together an NGSS-aligned lesson bundle + a teacher dashboard for
> classrooms. If that's useful, I'd love 15 minutes of feedback — and early
> access is free for your class. Demo: [link]

---

## 5. Assets you already have (use them)

- **Hero GIF** — the mitosis preset (`exports/`), the single best shareable.
- **Museum plates** — `docs/generated/*.png` (Genesis, Prima Materia, Twelve
  Tableaux): the Product Hunt gallery + the Pro upsell.
- **Release poster** — `docs/generated/release_poster_v3_4.png`.
- **Live demo** — `docs/web/index.html` (deploy to GitHub Pages).

Make a 20-second screen-capture of the mitosis preset → that's your TikTok/Shorts/PH video.

---

## 6. Metrics to watch

| Funnel stage | Metric | Why |
|---|---|---|
| Acquisition | unique visitors, ⭐, demo sessions | channel fit |
| Activation | % who move a slider / change a preset | does the hook land? |
| Interest | waitlist signups, Sponsor clicks | demand signal |
| Revenue | Preview-Meter → upgrade rate, MRR | conversion |
| Education | demo→email replies, Classroom trials | B2B pipeline |

Instrument the free demo *before* launch so week-1 traffic isn't wasted.
