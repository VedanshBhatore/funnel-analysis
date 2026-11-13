# Memo: Where to focus next quarter

**To:** Head of Product
**From:** [Your name], Product Analytics
**Re:** Funnel & retention analysis — Google Merchandise Store (GA4 sample, Nov 2020–Jan 2021)
**Data:** `bigquery-public-data.ga4_obfuscated_sample_ecommerce` — 4.3M events, 270K users, 360K sessions, 4,452 purchases. Full methodology in `docs/data-profile.md`; full findings in `docs/insights.md`.

## Bottom line

We convert **0.79% of sessions** to purchase. The single biggest, most fixable
leak is **view_item → add_to_cart (80.2% drop-off)** — more sessions reach a
product page and leave than at any other step relative to its own base. I
recommend we fix that first, not retention, not acquisition mix.

## Why this and not something else

1. **Retention is structurally weak and got worse through the holiday peak**
   (week-1 return fell from 10.8% in late October to 2.5% in late December,
   recovering only to ~3-4% in January; under 1% by week 4 for nearly every
   cohort). The business's biggest acquisition cohorts (holiday traffic) are
   also its worst-retaining. Fixing this is a multi-quarter lifecycle/loyalty
   investment, not a quick win, and a generic "all users" retention push would
   miss that the problem concentrates in holiday-acquired, likely one-time
   gift shoppers.
2. **Device is not the problem** — the funnel shape is nearly identical on
   desktop, mobile, and tablet (0.77–0.82% end-to-end). Don't spend a quarter
   on a mobile redesign expecting an outsized return here.
3. **Paid search (cpc) is a real, second-order problem** (17.76% view→cart vs.
   19.79% site-wide, and the lowest overall conversion of any channel with
   volume) — but it's a smaller, slower-moving lever: at ~34 cpc sessions/day
   reaching a product page, a test there takes ~9 weeks to read (see
   `docs/experiments.md`, Experiment 2). Worth fixing, not worth fixing first.
4. **The add_to_cart step is site-wide, fast to test, and cheap to ship.** At
   818 sessions/day reaching a product page, Experiment 1 (simplify the
   Add-to-Cart CTA) reaches a readable sample in **16 days**. If it lifts
   add_to_cart by even 2 points, that flows through every downstream step —
   checkout, purchase, revenue — without touching acquisition spend.

## What I'd ship, in order

1. **Now:** Experiment 1 — simplify the PDP Add-to-Cart CTA, site-wide. Primary
   metric: view→cart rate (baseline 19.79%). Guardrail: add_to_cart→purchase
   rate, AOV. Reads in ~2.3 weeks.
2. **Next:** Experiment 3 — shipping-cost transparency on Accessories/,
   Backpacks/, Water Bottles/ (the three weakest categories, 2.2–5.8%
   view→cart vs. 20–36% for apparel). Scoped, low-risk, reads in ~4 weeks.
3. **Background / lower priority:** Experiment 2 — cpc landing-page relevance.
   Worth doing, but sequence it behind the two above given its low daily
   volume and longer read time (~9 weeks).

## One thing to flag before anyone builds a checkout redesign

`begin_checkout → add_shipping_info` shows a **literal 0% drop-off** in every
segment we checked. That event almost certainly auto-fires rather than
reflecting a real user action — don't let anyone read "checkout step 1 has no
friction" from this data. The real friction in checkout is one step later,
`add_shipping_info → add_payment_info` (35% drop-off).

## What I'd want before the next review

A fourth data source we don't have today: on-page interaction events (clicks,
dead-clicks, scroll depth) on the product page itself. That's the single
highest-value instrumentation gap — it would let us distinguish hypothesis 1
(UI friction) from hypothesis 3 (price sticker shock) in `docs/insights.md`
before we even run Experiment 1, and would likely sharpen the MDE we test for.
