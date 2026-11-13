"""Phase 1 data profiling: date range, event volume, users/sessions/purchases,
and event_name counts for the GA4 sample dataset. Writes docs/data-profile.md.
"""
from pathlib import Path

from bq_client import run_query

ROOT = Path(__file__).resolve().parent.parent
TABLE = "`bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`"

QUERIES = {
    "date_range": f"""
        SELECT MIN(event_date) AS min_date, MAX(event_date) AS max_date,
               COUNT(DISTINCT _TABLE_SUFFIX) AS n_daily_tables
        FROM {TABLE}
    """,
    "core_counts": f"""
        WITH sess AS (
          SELECT
            user_pseudo_id,
            (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS ga_session_id,
            event_name,
            ecommerce.transaction_id AS transaction_id
          FROM {TABLE}
        )
        SELECT
          COUNT(*) AS total_events,
          COUNT(DISTINCT user_pseudo_id) AS total_users,
          COUNT(DISTINCT IF(ga_session_id IS NOT NULL,
                CONCAT(user_pseudo_id, '-', CAST(ga_session_id AS STRING)), NULL)) AS total_sessions,
          COUNTIF(ga_session_id IS NULL) AS events_missing_session_id,
          COUNT(DISTINCT IF(event_name = 'purchase', transaction_id, NULL)) AS total_purchases
        FROM sess
    """,
    "event_name_counts": f"""
        SELECT event_name, COUNT(*) AS n_events
        FROM {TABLE}
        GROUP BY event_name
        ORDER BY n_events DESC
    """,
    "device_category_quirks": f"""
        SELECT COALESCE(device.category, '(null)') AS device_category, COUNT(*) AS n_events
        FROM {TABLE}
        GROUP BY device_category
        ORDER BY n_events DESC
    """,
    "country_quirks": f"""
        SELECT COALESCE(geo.country, '(null)') AS country, COUNT(*) AS n_events
        FROM {TABLE}
        GROUP BY country
        ORDER BY n_events DESC
        LIMIT 15
    """,
    "traffic_source_quirks": f"""
        SELECT COALESCE(traffic_source.medium, '(null)') AS medium,
               COALESCE(traffic_source.source, '(null)') AS source,
               COUNT(*) AS n_events
        FROM {TABLE}
        GROUP BY medium, source
        ORDER BY n_events DESC
        LIMIT 15
    """,
    "item_category_quirks": f"""
        SELECT COALESCE(item.item_category, '(null)') AS item_category, COUNT(*) AS n_item_rows
        FROM {TABLE}, UNNEST(items) AS item
        GROUP BY item_category
        ORDER BY n_item_rows DESC
        LIMIT 15
    """,
    "item_identity_overlap": f"""
        WITH v AS (
          SELECT DISTINCT item.item_id FROM {TABLE}, UNNEST(items) AS item
          WHERE event_name = 'view_item'
        ),
        c AS (
          SELECT DISTINCT item.item_id FROM {TABLE}, UNNEST(items) AS item
          WHERE event_name = 'add_to_cart'
        ),
        p AS (
          SELECT DISTINCT item.item_id FROM {TABLE}, UNNEST(items) AS item
          WHERE event_name = 'purchase'
        )
        SELECT
          (SELECT COUNT(*) FROM v) AS distinct_viewed_items,
          (SELECT COUNT(*) FROM c) AS distinct_carted_items,
          (SELECT COUNT(*) FROM p) AS distinct_purchased_items,
          (SELECT COUNT(*) FROM v JOIN c USING (item_id)) AS overlap_view_cart_items,
          (SELECT COUNT(*) FROM v JOIN p USING (item_id)) AS overlap_view_purchase_items
    """,
    "category_identity_overlap": f"""
        WITH vc AS (
          SELECT DISTINCT item.item_category AS cat FROM {TABLE}, UNNEST(items) AS item
          WHERE event_name IN ('view_item', 'add_to_cart')
        ),
        p AS (
          SELECT DISTINCT item.item_category AS cat FROM {TABLE}, UNNEST(items) AS item
          WHERE event_name = 'purchase'
        )
        SELECT
          (SELECT COUNT(*) FROM vc) AS distinct_view_cart_categories,
          (SELECT COUNT(*) FROM p) AS distinct_purchase_categories,
          (SELECT COUNT(*) FROM vc JOIN p USING (cat)) AS overlap_categories
    """,
}


def main():
    results = {}
    for name, sql in QUERIES.items():
        df = run_query(sql, label=name)
        results[name] = df
        out_csv = ROOT / "data" / f"profile_{name}.csv"
        df.to_csv(out_csv, index=False)

    write_markdown(results)


def write_markdown(results):
    dr = results["date_range"].iloc[0]
    cc = results["core_counts"].iloc[0]
    ev = results["event_name_counts"]
    dev = results["device_category_quirks"]
    geo = results["country_quirks"]
    traf = results["traffic_source_quirks"]
    itc = results["item_category_quirks"]
    iio = results["item_identity_overlap"].iloc[0]
    cio = results["category_identity_overlap"].iloc[0]

    lines = []
    lines.append("# Data Profile: GA4 Obfuscated Sample E-commerce Dataset")
    lines.append("")
    lines.append(f"Source table: `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`")
    lines.append("")
    lines.append("## Date range")
    lines.append("")
    lines.append(f"- Min `event_date`: **{dr['min_date']}**")
    lines.append(f"- Max `event_date`: **{dr['max_date']}**")
    lines.append(f"- Number of daily shard tables present: **{dr['n_daily_tables']}**")
    lines.append("")
    lines.append("## Core volume")
    lines.append("")
    lines.append(f"- Total events: **{int(cc['total_events']):,}**")
    lines.append(f"- Distinct users (`user_pseudo_id`): **{int(cc['total_users']):,}**")
    lines.append(f"- Distinct sessions (`user_pseudo_id` + `ga_session_id`): **{int(cc['total_sessions']):,}**")
    lines.append(f"- Events missing `ga_session_id`: **{int(cc['events_missing_session_id']):,}** "
                  f"(excluded from all session-level analysis)")
    lines.append(f"- Distinct purchases (`transaction_id` on `purchase` events): **{int(cc['total_purchases']):,}**")
    lines.append("")
    lines.append("## Event name counts")
    lines.append("")
    lines.append("| event_name | count |")
    lines.append("|---|---|")
    for _, r in ev.iterrows():
        lines.append(f"| {r['event_name']} | {int(r['n_events']):,} |")
    lines.append("")
    lines.append("## Obfuscation / data-quality quirks observed")
    lines.append("")
    lines.append("### device.category")
    lines.append("")
    lines.append("| device_category | n_events |")
    lines.append("|---|---|")
    for _, r in dev.iterrows():
        lines.append(f"| {r['device_category']} | {int(r['n_events']):,} |")
    lines.append("")
    lines.append("### geo.country (top 15)")
    lines.append("")
    lines.append("| country | n_events |")
    lines.append("|---|---|")
    for _, r in geo.iterrows():
        lines.append(f"| {r['country']} | {int(r['n_events']):,} |")
    lines.append("")
    lines.append("### traffic_source.medium / source (top 15)")
    lines.append("")
    lines.append("| medium | source | n_events |")
    lines.append("|---|---|---|")
    for _, r in traf.iterrows():
        lines.append(f"| {r['medium']} | {r['source']} | {int(r['n_events']):,} |")
    lines.append("")
    lines.append("### items.item_category (top 15, item-row granularity)")
    lines.append("")
    lines.append("| item_category | n_item_rows |")
    lines.append("|---|---|")
    for _, r in itc.iterrows():
        lines.append(f"| {r['item_category']} | {int(r['n_item_rows']):,} |")
    lines.append("")
    lines.append("## How obfuscation / quirks are handled in this project")
    lines.append("")
    lines.append(
        "- `<Other>`, `(not set)`, `(data deleted)` and NULL values in dimension columns "
        "(device, geo, traffic_source, item_category) are kept as their own explicit "
        "category in every GROUP BY (coalesced to a readable label like `(not set)`), "
        "never silently filtered out -- dropping them would shrink the denominator and "
        "inflate rates computed on the remaining rows."
    )
    lines.append(
        "- Rows with no `ga_session_id` event param are excluded from every **session**-level "
        "query (funnel, cohort-by-session, time patterns) because they cannot be assigned to "
        "a session; the excluded count is reported above so the exclusion is auditable."
    )
    lines.append(
        "- `purchase` events are de-duplicated by `ecommerce.transaction_id` before computing "
        "revenue/orders/AOV, since the same transaction can fire more than one `purchase` "
        "event in GA4 (e.g. a confirmation-page reload)."
    )
    lines.append(
        f"- **`item_id`/`item_category` are not consistent between pre-purchase and purchase "
        f"events in this sample.** `view_item` and `add_to_cart` agree with each other "
        f"({int(iio['overlap_view_cart_items']):,} of {int(iio['distinct_viewed_items']):,} "
        f"distinct viewed `item_id`s also appear on `add_to_cart`), but only "
        f"{int(iio['overlap_view_purchase_items']):,} of those {int(iio['distinct_viewed_items']):,} "
        f"viewed `item_id`s, and only {int(cio['overlap_categories']):,} of "
        f"{int(cio['distinct_view_cart_categories']):,} view/cart `item_category` values, ever "
        f"appear on a `purchase` line item ({int(iio['distinct_purchased_items']):,} distinct "
        f"purchased `item_id`s exist, in a largely different value space). This looks like an "
        f"artifact of how Google obfuscated/re-keyed this particular public sample rather than "
        f"real GA4 behavior. Consequence: `sql/05_product_funnel.sql` reports view-to-cart rate "
        f"by category/item (consistent taxonomy) and top purchased categories by revenue "
        f"(purchase events' own, different taxonomy) as **separate** results instead of chaining "
        f"them into one view→cart→purchase rate per item."
    )
    lines.append("")

    out_path = ROOT / "docs" / "data-profile.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
