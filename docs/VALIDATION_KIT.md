# cellauto — Pricing & Demand Validation Kit

*"See if I'm right" — before building the backend.* This is the survey, the
audience, and the pass/fail thresholds you run through a feedback panel
(POND, Maze, UserTesting, PickFu, or a plain Google Form to your launch
audience) to test the monetization plan with real people.

> **About POND / external panels:** Claude (in this environment) cannot create
> third-party accounts or log into external services — there's no browser,
> credentials, or network access for that here. So *you* create the POND account;
> this kit is everything you paste in to get an answer fast. If POND turns out
> not to fit, every question below works in a Google Form, Typeform, or a Reddit/
> Discord poll just as well.

---

## 0. The one question we're answering

> **Will a broad audience (hobbyist → educator → institution) pay for cellauto,
> at what price, and is the "free taste → pay" Preview Meter the right trigger?**

If the data says no, we've spent a survey instead of a backend. That's the point.

---

## 1. Who to recruit (screener)

Aim for ~30–50 responses per segment. Quotas:

- **Hobbyists / learners** (40%): "interested in science, generative art, or
  simulations; played with an interactive sim in the last year."
- **Educators** (35%): "teach biology / chemistry / CS / general science, K-12 or
  university."
- **Creators / researchers** (15%): "make generative art OR do research touching
  simulation/origin-of-life."
- **Institution buyers** (10%): "involved in purchasing for a school, university,
  or museum."

Screen-out: people with zero interest in science *or* generative art (not our
market; their price signal is noise).

---

## 2. Show them this first

1. The **20-second mitosis GIF** (the hook).
2. The **live demo link** (`docs/web/`) — let them move the sliders.
3. One line: *"A free origin-of-life sandbox. 12 cited stages from primordial
   soup to LUCA. Below are some paid add-ons we're considering."*
4. The **[PRICING.md](PRICING.md)** table.

---

## 3. The survey

### A. Reaction (does the hook land?)
1. In one word, how did the demo make you feel? *(open text)*
2. How likely are you to share this with someone? *(0–10)*
3. Which stage/visual interested you most? *(multi-select)*

### B. Willingness to pay — Van Westendorp (the core price test)
Ask all four for the **Pro** tier (repeat for Plus if budget allows):
4. At what monthly price would this be **so cheap** you'd question its quality?
5. At what price is it a **bargain — great value**?
6. At what price does it start to feel **expensive but worth considering**?
7. At what price is it **too expensive** to consider?

> Plot the four curves; the **Optimal Price Point** is where "too cheap" crosses
> "too expensive." This tells you if $5 / $15 are right, or off.

### C. The Preview Meter (validate YOUR idea directly)
8. *"Cloud renders and HD exports run free for the first 30 seconds, then ask you
   to upgrade. Big exports and a poster generator are paid; basic play stays
   free forever."* How does that feel?
   - Totally fair / Mostly fair / Mildly annoying / Dealbreaker
9. Which free-taste threshold feels best?
   - 15s · 30s · 60s · "first export free, then pay" · "just charge a flat price"
10. What's the **one feature** that would actually make you pay? *(open text)*

### D. Segment-specific
- **Educators:** Would your school pay $299–999/yr for a classroom license with
  lesson plans + a teacher dashboard? Who approves that purchase?
- **Creators:** Would a commercial-use license for exported art matter to you? At
  what price?
- **Institutions:** Is a kiosk/on-prem museum license something you'd evaluate?

### E. Commitment (the realest signal)
11. Would you join a waitlist for the paid version? *(email capture — soft yes)*
12. Would you **pre-order Pro at 50% off** for the first 3 months? *(hard signal)*

---

## 4. Pass / fail thresholds

Decide the gates *before* you see the data:

| Signal | 🟢 Go | 🟡 Iterate | 🔴 Rethink |
|---|---|---|---|
| Share likelihood (Q2) | ≥7 avg | 5–7 | <5 |
| Preview Meter "fair" (Q8) | ≥60% fair/mostly | 40–60% | <40% (idea repels) |
| Van Westendorp OPP vs our price | within ±30% | off by 30–60% | wildly off |
| Waitlist opt-in (Q11) | ≥25% | 10–25% | <10% |
| Pre-order yes (Q12) | ≥5% | 2–5% | <2% (no real demand) |

🟢 across the board → build the billing + cloud backend. 🟡 → adjust price/
threshold and re-test. 🔴 on Preview Meter → your 30s instinct needs reshaping
(maybe flat price, or sponsorship-only). 🔴 on pre-order → don't build the SaaS
yet; lean on Sponsors + edu licensing.

---

## 5. Cheapest possible test (if no panel budget)

1. Ship the pricing page with a **"Notify me / Get early access"** button → count
   clicks (this is a built-in demand meter; instrument it).
2. Post the demo to Show HN + Reddit; read every comment for price/feature
   reactions.
3. Run a free **PickFu / Reddit poll** on the threshold question (Q9).
4. DM 10 teachers the outreach email; count replies.

Three days, ~$0, and you'll know if section 4's gates are anywhere close.
