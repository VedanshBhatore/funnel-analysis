# Insights

Five findings, each sourced directly from a CSV in `data/` (produced by the SQL
files in `sql/`, run via `src/run_queries.py`). Chart files are in `charts/`.

## 1. Only 0.79% of sessions convert to purchase

**Number:** 2,816 of 354,857 sessions that fired a `session_start` event reach
`purchase` — **0.79%** (`data/02_funnel.csv`, `purchase` row, `pct_of_initial`).
**Chart:** `charts/funnel.png`.

**Why it matters:** this is the single headline conversion number any PM or
exec will ask for. At under 1%, even small relative improvements translate into
large absolute revenue, because the funnel is so long and lossy that there's a
lot of room between "visits a product page" and "buys."

## 2. The leakiest step is view_item → add_to_cart (80.2% drop-off) — and the biggest absolute loss is session_start → view_item

**Number:** `add_to_cart` step: 14,897 of 75,271 sessions that viewed an item
also added to cart — a **80.21% drop-off**, the highest single-step rate in the
funnel (`data/02_funnel.csv`). By absolute session count, `session_start →
view_item` loses more sessions outright (279,586 vs. 60,374), because the base
is much bigger (354,857 → 75,271, 78.79% drop-off) — both numbers matter
depending on whether the question is "where's the worst rate" (add_to_cart) or
"where's the most revenue sitting on the table" (view_item).
**Chart:** `charts/funnel.png`.

**Side observation worth flagging:** `begin_checkout → add_shipping_info` shows
a literal **0.00% drop-off** (5,868 → 5,868 sessions, every segment we checked in
`data/03_funnel_segments.csv` shows the same pattern) — that event almost
certainly fires automatically rather than reflecting a real user decision point,
which matters when designing checkout experiments: `add_payment_info`'s 35%
drop-off right after it is likely the true second friction point in checkout.

**Why it matters:** this is the step to fix first. A product page that fails to
convert a visitor who already clicked into a specific item is the most direct,
highest-leverage lever in the whole funnel — see `docs/experiments.md`.

## 3. Paid search (cpc) traffic is the worst-converting channel, both at the leaky step and overall

**Number:** `cpc` sessions convert view_item → add_to_cart at **17.76%**
(558/3,142) vs. the site-wide 19.79%, and the `cpc` channel has the **lowest
overall purchase rate of any traffic medium with real volume: 0.59%**
(92/15,535) — worse than organic (0.65%), referral (0.98%), and `(none)`/direct
(0.78%) (`data/03_funnel_segments.csv`, `segment_type = traffic_medium`).
**Chart:** `charts/funnel_by_segment.png` (device cut shown; the medium cut is in
the CSV and in `analysis.ipynb` §3).

**Why it matters:** this is spend the business controls directly. If paid
search traffic underperforms free channels on both the leaky step and the
full funnel, that's either a targeting problem (wrong audience) or a landing
experience problem (ad promise ≠ page) — both fixable, unlike, say, "device"
(where the funnel doesn't meaningfully differ: 0.77% desktop vs 0.82% mobile vs
0.79% tablet).

## 4. Retention is a first-visit story, not a repeat-visit story — and it got worse through the quarter

**Number:** week-1 return rate is **under 1% by week 4–5 for every cohort we
can observe fully**, and week-1 retention itself **declined from 10.82% (cohort
of 2020-10-26) to a low of 2.47% (cohort of 2020-12-28)** before ticking back up
to 3.2–4.2% in January — all from `data/04_cohort_retention.csv`. Notably the
low point lands on the cohorts acquired during the Nov/Dec holiday peak (see
finding #1's traffic chart), which are also the *largest* cohorts by raw user
count (e.g. 28,545 users the week of 2020-12-07) — so the business's biggest
acquisition cohorts are also its worst-retaining ones.
**Chart:** `charts/cohort_retention_heatmap.png`.

**Why it matters:** this store's revenue is overwhelmingly driven by
first-visit conversion, not loyalty/repeat purchasing, and the holiday traffic
surge brought in the least sticky users of the whole window — likely one-time
gift shoppers. That should directly shape where the team invests next: a
retention program (lifecycle email, loyalty points) aimed generically at "all
users" is fighting an uphill battle, while improvements to first-visit
conversion (the funnel, above) compound immediately across nearly the entire
user base regardless of season.

## 5. Accessories/, Backpacks/, and Water Bottles/ convert view→cart far below the rest of the catalog

**Number:** among categories with ≥1,000 views, **Accessories/ (2.2%, 48/2,153),
Backpacks/ (3.2%, 141/4,449), and Water Bottles/ (5.8%, 178/3,081)** have the
three lowest view-to-cart rates in the catalog, vs. 20–36% for most apparel
categories (`data/05_product_funnel.csv`, `category_view_to_cart` rows).
**Chart:** `charts/product_view_to_cart.png`.

**Why it matters:** this is a merchandising-page-specific problem (pricing,
imagery, or cross-sell placement for those three categories), not a site-wide
issue — it's a cheap, scoped fix candidate (see Experiment 3 in
`docs/experiments.md`).

**Data-quality caveat that shaped this analysis:** `item_id`/`item_category` on
`purchase` events use a largely different value space than on `view_item`/
`add_to_cart` events in this obfuscated sample (full detail in
`docs/data-profile.md`) — so cart→purchase rate by item/category is not reported
here; it would silently compare unrelated identifiers.

---

## The leakiest step and where it's worst

**Leakiest step:** `view_item → add_to_cart`, 80.21% drop-off site-wide.
**Worst segment for that step:** `cpc` (paid search) traffic, 82.24% drop-off
(558 of 3,142 — i.e. a 17.76% conversion rate, vs. 19.79% site-wide).

## Three hypotheses for the view_item → add_to_cart drop-off

1. **Product-page friction** — required variant selection (size/color) or an
   unclear/low-visibility "Add to Cart" control causes visitors who are
   otherwise interested to abandon before adding to cart. This would
   disproportionately affect categories with more variants (apparel) and
   explain why some simple, single-SKU categories (Accessories, Water Bottles)
   still convert low for a *different* reason (see hypothesis 3).
   **Data that would confirm it:** client-side interaction events (rage clicks,
   dead clicks, or time-to-first-interaction on the Add to Cart button) layered
   on top of `view_item`; currently this GA4 export has no such event, so this
   would require adding custom event tracking before it could be tested.

2. **Paid-search traffic is lower-intent or mismatched to the landing page** —
   this is directly supported by data already: `cpc` converts view→cart at
   17.76% vs. 20.90% for referral traffic and 19.79% site-wide. Users arriving
   from an ad may be comparison-shopping or land on a product that doesn't match
   the ad's promise.
   **Data that would confirm it:** compare `page_location` / landing page vs. ad
   creative/keyword (not present in this GA4 export — would need Google Ads
   integration data joined by `click_id`/`gclid`), and compare average
   `engagement_time_msec` for `cpc` vs. other mediums on the `view_item` event.

3. **Price or shipping cost "sticker shock"** discovered only after clicking
   into a product discourages adding to cart, especially for low-margin,
   low-average-price categories like Accessories and Water Bottles where
   shipping cost is a larger fraction of the order value.
   **Data that would confirm it:** item `price` (already in the `items` array)
   cross-tabulated against view-to-cart rate controlling for category (does
   add-to-cart rate drop as price-as-%-of-category-median rises?), and whether
   users who scroll to a shipping-cost section (would need a custom scroll-depth
   or element-visibility event, not present today) exit at a higher rate.
