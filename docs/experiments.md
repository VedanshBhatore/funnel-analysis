# Experiment Designs

Three A/B tests targeting the leakiest funnel step (`view_item → add_to_cart`,
80.21% drop-off site-wide — see `docs/insights.md`). All baseline rates are read
directly from `data/02_funnel.csv`, `data/03_funnel_segments.csv`, and
`data/05_product_funnel.csv`. All sample sizes are computed with `statsmodels`
power analysis (α = 0.05, power = 0.8, two-sided) in `src/power_analysis.py` —
run it yourself with `python src/power_analysis.py`; the numbers below are its
actual output, not estimates.

```python
# src/power_analysis.py (excerpt) -- the actual function used for all 3 tests
import math
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

power_analysis = NormalIndPower()

def solve(name, baseline, mde_abs, daily_eligible):
    target = baseline + mde_abs
    effect_size = proportion_effectsize(baseline, target)
    n_per_arm = power_analysis.solve_power(
        effect_size=effect_size, alpha=0.05, power=0.8, ratio=1.0, alternative="two-sided"
    )
    n_per_arm_ceil = math.ceil(n_per_arm)
    total_n = n_per_arm_ceil * 2
    duration_days = math.ceil(total_n / daily_eligible)
    return n_per_arm_ceil, total_n, duration_days
```

---

## Experiment 1: Simplify the product-page Add-to-Cart CTA (site-wide)

**Hypothesis:** product-page friction (unclear/low-visibility Add to Cart
control, or required variant selection before the button is enabled) causes
some otherwise-interested visitors to leave without adding to cart.

**Change:** make "Add to Cart" a persistent, high-contrast, always-enabled
primary button (move variant selection to *after* add-to-cart, or default to
the most common variant), tested against the current PDP.

**Primary metric:** session-level `view_item → add_to_cart` conversion rate.

**Guardrail metrics:** `add_to_cart → purchase` rate (make sure we're not just
creating low-intent carts that never convert further), average order value,
PDP bounce rate.

**Baseline rate:** 19.79% (14,897 / 75,271 sessions — `data/02_funnel.csv`).

**Minimum detectable effect:** +2.0 percentage points absolute (→ 21.79%,
+10.1% relative) — a visible, business-meaningful lift for a UI-only change.

**Sample size (statsmodels, α=0.05, power=0.8):**
- Effect size (Cohen's h) = 0.0493
- **6,460 sessions per arm, 12,920 total**

**Expected duration:** site-wide `view_item` traffic averages **818.2
sessions/day** over the 92-day window in this dataset (75,271 / 92). At that
rate: **16 days (~2.3 weeks)** to reach the required sample, assuming traffic
is split 50/50 across the two arms.

---

## Experiment 2: Paid-search (cpc) landing-page relevance fix

**Hypothesis:** `cpc` (paid search) traffic underperforms because the landing
product page doesn't match ad intent/promise, not because of a general site
issue — supported by `cpc` already converting view→cart below every other
channel with real volume (17.76% vs. 19.79% site-wide, 20.90% referral).

**Change:** for sessions arriving via `cpc`, serve a landing variant that
echoes the ad's category/keyword context (e.g., a category-matched hero and
highlighted item) instead of the generic PDP.

**Primary metric:** `view_item → add_to_cart` conversion rate, `cpc` sessions
only.

**Guardrail metrics:** `cpc` channel's overall purchase conversion rate (make
sure the lift carries through checkout), cost-per-acquisition on paid spend,
PDP bounce rate for `cpc` sessions.

**Baseline rate:** 17.76% (558 / 3,142 `cpc` sessions —
`data/03_funnel_segments.csv`, `segment_type = traffic_medium`).

**Minimum detectable effect:** +5.0 percentage points absolute (→ 22.76%,
+28.2% relative) — set larger than Experiment 1 because `cpc` daily volume is
much lower (see duration below); a smaller MDE would make the test
impractically long.

**Sample size (statsmodels, α=0.05, power=0.8):**
- Effect size (Cohen's h) = 0.1246
- **1,011 sessions per arm, 2,022 total**

**Expected duration:** `cpc` sessions reaching `view_item` average **34.2
sessions/day** (3,142 / 92). At that rate: **60 days (~8.6 weeks)**.
**PM note:** this is a long test for a single channel-specific fix — if faster
iteration is needed, consider bundling `cpc` with other paid-medium segments,
or treat this as a lower-priority, longer-running test behind Experiment 1.

---

## Experiment 3: Shipping-cost transparency on chronically weak categories

**Hypothesis:** "sticker shock" from shipping cost discovered only after
clicking into a product disproportionately hurts categories where shipping is
a large fraction of order value — the three lowest view-to-cart categories
(Accessories/, Backpacks/, Water Bottles/) are all low-average-price items.

**Change:** surface shipping cost / free-shipping threshold directly on the
product page (not just at checkout) for these three categories.

**Primary metric:** pooled `view_item → add_to_cart` rate for Accessories/,
Backpacks/, and Water Bottles/.

**Guardrail metrics:** average order value (threshold messaging could
push cart size up or down), site-wide `view_item → add_to_cart` rate (confirm
no negative spillover if the shipping badge is shared UI).

**Baseline rate:** 3.79% (367 / 9,683 item-views pooled across the three
categories — `data/05_product_funnel.csv`, `category_view_to_cart` rows for
`Accessories/`, `Backpacks/`, `Water Bottles/`).

**Minimum detectable effect:** +2.2 percentage points absolute (→ 5.99%, +58%
relative) — a large relative ask, but these categories are starting from such
a low base that a smaller absolute lift is barely distinguishable from noise
at achievable sample sizes.

**Sample size (statsmodels, α=0.05, power=0.8):**
- Effect size (Cohen's h) = 0.1027
- **1,490 views per arm, 2,980 total**

**Expected duration:** these three categories combined average **105.2
item-views/day** (9,683 / 92; note this is item-row volume, a close proxy for
distinct product-page views in these categories, not exact session count).
At that rate: **29 days (~4.1 weeks)**.

---

## Suggested sequencing

Run **Experiment 1 first** — it's site-wide, reaches its sample size fastest
(16 days), and a win there compounds across the whole funnel immediately. Run
**Experiment 3** second (4 weeks, scoped and low-risk). Treat **Experiment 2**
as a longer-running background test given its small daily `cpc` volume, or
revisit it once paid-search spend/volume increases.
