# Looker Studio Dashboard — Build Guide

This builds the dashboard **you** connect and assemble in Looker Studio,
against the BigQuery views created by `src/create_views.py` in dataset
`<GCP_PROJECT>.portfolio` (6 views: `kpis_daily`, `funnel`,
`funnel_by_segment`, `cohorts`, `product_funnel`, `time_patterns`).

**Important scope note before you start:** only `kpis_daily` carries a date
column (`event_date`). The other five views are pre-aggregated by the SQL
over the full Nov 2020–Jan 2021 window, so a page-level date-range filter will
only affect charts built on `kpis_daily` — it won't do anything on the funnel,
segment, cohort, product, or time-pattern charts unless you rebuild those
queries to accept a date parameter. Don't be surprised when the date control
doesn't change those pages; it's by design, not a bug.

## Step 0: Connect the data sources

1. Go to [lookerstudio.google.com](https://lookerstudio.google.com) → **Create** → **Data source**.
2. Choose the **BigQuery** connector.
3. Pick **My Projects** → your project (the `GCP_PROJECT` value in your `.env`) → dataset `portfolio` → table/view.
4. Repeat this once per view — you'll end up with **6 data sources**: `kpis_daily`, `funnel`, `funnel_by_segment`, `cohorts`, `product_funnel`, `time_patterns`.
5. Click **Create Report** on the first one (`kpis_daily`), then add the rest as additional data sources inside that same report (**Resource → Manage added data sources → Add a data source**).

---

## Page 1: Overview

**Data source:** `kpis_daily`

**Filter control (date range):**
- Add a **Date Range Control**. Field: `event_date`. Default range: 2020-11-01 to 2021-01-31 (the full dataset window — see `docs/data-profile.md`).

**Scorecards** (4, laid out in a row across the top):
| Metric | Field | Aggregation |
|---|---|---|
| Total Sessions | `sessions` | SUM |
| Total Revenue | `revenue_usd` | SUM |
| Avg Conversion Rate | `conversion_rate_pct` | AVG |
| Avg Order Value | `avg_order_value_usd` | AVG |

**Chart 1 — Time series:** Dimension: `event_date`. Metric: `sessions`. Sort: `event_date` ascending. Title: "Sessions / day".

**Chart 2 — Time series:** Dimension: `event_date`. Metric: `conversion_rate_pct`. Sort: `event_date` ascending. Title: "Conversion rate / day (%)". (Separate chart, not a second axis on Chart 1 — keep one measure per chart.)

**Suggested layout:** date range control top-right; 4 scorecards in a row below it; the two time-series charts stacked below that, full width.

---

## Page 2: Funnel

**Data source:** `funnel`

**Chart — Bar chart (horizontal):** Dimension: `step_name`. Metric: `sessions`. Sort: `step_order` ascending (add `step_order` as a hidden sort field — Chart → Sort → `step_order`, ascending). Title: "Session funnel: session_start → purchase".

**Chart — Table:** Dimensions: `step_order`, `step_name`. Metrics: `sessions`, `pct_of_initial`, `step_conversion_pct`, `dropoff_pct`. Sort: `step_order` ascending. This is the exact numeric backup for the bar chart above it.

**Suggested layout:** bar chart left/top (roughly 60% width), table to the right or below.

---

## Page 3: Funnel by Segment

**Data source:** `funnel_by_segment`

**Filter control (segment type):** Add a **Drop-down list control**. Field: `segment_type`. This lets the viewer pick `device_category`, `traffic_medium`, `traffic_source`, or `country`.

**Filter control (device, optional second control):** Add a second **Drop-down list control**. Field: `segment_value`. In the control's own **Filter** setting (not the page filter), add condition `segment_type` **exactly matches** `device_category` so this control only ever lists desktop/mobile/tablet — use it when you want to drill into device without touching the first control.

**Chart — Bar chart (horizontal):** Dimension: `segment_value`. Metric: `pct_of_initial`. Filter (chart-level): `step_order` **equals** `7` (the purchase step only — otherwise every step for every segment stacks together). Sort: `pct_of_initial` descending. Title: "Full-funnel conversion by segment".

**Chart — Table:** Dimensions: `segment_type`, `segment_value`, `step_name`. Metrics: `sessions`, `step_conversion_pct`, `dropoff_pct`, `low_sample`. Sort: `segment_type` then `sessions` descending. Conditional formatting: highlight rows where `low_sample` = `true` in a muted/grey style — those segments (under 100 sessions at step 1) shouldn't drive decisions.

**Suggested layout:** both filter controls top, bar chart below spanning full width, table below that.

---

## Page 4: Retention Cohorts

**Data source:** `cohorts`

**Chart — Pivot table with heatmap:** Row dimension: `cohort_week`. Column dimension: `week_number`. Metric: `retention_pct` (aggregation: AVG — each cohort_week/week_number pair is already one row). Enable **heatmap** cell coloring in the chart style panel (single-hue, e.g. blue, ascending). Sort rows by `cohort_week` ascending.

**Suggested layout:** single full-page chart — this is the centerpiece of the page, matches `charts/cohort_retention_heatmap.png` in the repo.

---

## Page 5: Product Funnel

**Data source:** `product_funnel`

**Chart — Bar chart (horizontal):** Dimension: `segment_label`. Metric: `pct_1`. Chart-level filter: `query_type` **exactly matches** `category_view_to_cart`. Sort: `pct_1` ascending. Title: "View → add-to-cart rate by category".

**Chart — Bar chart (horizontal), second chart:** Dimension: `segment_label`. Metric: `metric_3`. Chart-level filter: `query_type` **exactly matches** `purchase_category`. Sort: `metric_3` descending. Title: "Top categories by purchase revenue (USD)". Note in a text box on this page: *purchase-side categories use a different taxonomy than view/cart categories in this dataset — see docs/data-profile.md — don't read the two charts as one funnel.*

**Suggested layout:** the two bar charts side by side, text-box caveat note underneath both.

---

## Page 6: Time Patterns

**Data source:** `time_patterns`

**Chart — Pivot table with heatmap:** Row dimension: `day_of_week`. Column dimension: `hour_of_day_utc`. Metric: `conversion_rate_pct` (AVG). Enable heatmap coloring. Sort rows using `day_of_week_num` as a hidden sort field (ascending) so days read Sunday→Saturday instead of alphabetically.

**Suggested layout:** single full-width chart, same style as Page 4.

---

## Global filter control (device) — report-level, optional

If you want a single device filter that works across Pages 1, 3, and 5
simultaneously: Looker Studio filter controls are page-scoped by default.
To make one control affect multiple pages, add the **same** filter control
(same field, same data source) to each page you want it on — Looker Studio
treats same-field controls as linked automatically when "Apply filter to
report" isn't restricted. The cleanest version for this dataset: put the
`segment_value` (scoped to `device_category`) control from Page 3 onto Page 1
and Page 5 as well, even though Pages 1/5 don't have a `segment_type` field
themselves — Looker Studio will simply ignore it there with no effect, which
is acceptable since those pages don't carry device granularity in their
source views.

## When you're done

Click **Share → Publish**, copy the public viewer link, and paste it into the
`README.md` placeholder (`[TODO: paste your published Looker Studio link here]`).
