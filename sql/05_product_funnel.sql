-- 05_product_funnel.sql
-- IMPORTANT DATA-QUALITY FINDING (see docs/data-profile.md): in this
-- obfuscated sample dataset, item_id and item_category are NOT consistent
-- between pre-purchase events (view_item, add_to_cart -- which agree with
-- each other: 416/427 viewed item_ids also appear as add_to_cart item_ids)
-- and purchase events (only 5/427 viewed item_ids and 15/75 view/cart
-- categories appear anywhere in purchase line items). This looks like an
-- artifact of how Google obfuscated/re-keyed this particular public
-- sample, not a real-world GA4 behavior. Consequence: a per-item or
-- per-category view -> cart -> purchase rate CANNOT be computed honestly
-- here, because "purchase of item X" and "view of item X" don't refer to
-- the same X. So this query reports three things separately instead of
-- chaining them:
--   'category_view_to_cart' -> view-to-cart rate by item_category, using
--        only view_item + add_to_cart (same, consistent taxonomy)
--   'item_view_to_cart'     -> items viewed a lot but rarely carted, using
--        only view_item + add_to_cart (same, consistent item_id space)
--   'purchase_category'     -> top categories by revenue from purchase
--        events only, in purchase events' own (different) category
--        taxonomy -- NOT comparable row-for-row to the view/cart rows
-- Columns are generically named (metric_1/metric_2/metric_3/pct_1) because
-- they mean different things per query_type; see the comments above each
-- CTE for the mapping.

WITH view_cart_events AS (
  SELECT
    event_name,
    COALESCE(item.item_category, '(not set)') AS item_category,
    item.item_id,
    COALESCE(item.item_name, '(not set)') AS item_name
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`,
    UNNEST(items) AS item
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
    AND event_name IN ('view_item', 'add_to_cart')
),

purchase_items AS (
  SELECT
    COALESCE(item.item_category, '(not set)') AS item_category,
    item.quantity,
    item.item_revenue
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`,
    UNNEST(items) AS item
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
    AND event_name = 'purchase'
),

-- metric_1 = views, metric_2 = carts, metric_3 = NULL, pct_1 = view_to_cart_pct
category_view_to_cart AS (
  SELECT
    'category_view_to_cart' AS query_type,
    item_category AS segment_label,
    COUNTIF(event_name = 'view_item') AS metric_1,
    COUNTIF(event_name = 'add_to_cart') AS metric_2,
    CAST(NULL AS INT64) AS metric_3,
    ROUND(SAFE_DIVIDE(COUNTIF(event_name = 'add_to_cart'), COUNTIF(event_name = 'view_item')) * 100, 2)
      AS pct_1
  FROM view_cart_events
  GROUP BY item_category
),

-- metric_1 = views, metric_2 = carts, metric_3 = NULL, pct_1 = view_to_cart_pct
-- limited to items viewed >= 50 times, worst view-to-cart rate first
item_view_to_cart AS (
  SELECT
    'item_view_to_cart' AS query_type,
    CONCAT(item_name, ' [', item_id, ']') AS segment_label,
    COUNTIF(event_name = 'view_item') AS metric_1,
    COUNTIF(event_name = 'add_to_cart') AS metric_2,
    CAST(NULL AS INT64) AS metric_3,
    ROUND(SAFE_DIVIDE(COUNTIF(event_name = 'add_to_cart'), COUNTIF(event_name = 'view_item')) * 100, 2)
      AS pct_1
  FROM view_cart_events
  GROUP BY item_id, item_name
  HAVING COUNTIF(event_name = 'view_item') >= 50
  ORDER BY pct_1 ASC, metric_1 DESC
  LIMIT 20
),

-- metric_1 = orders (purchase line items), metric_2 = units (sum quantity),
-- metric_3 = revenue_usd, pct_1 = NULL. Uses purchase events' OWN category
-- taxonomy -- do not compare segment_label values to the two CTEs above.
purchase_category AS (
  SELECT
    'purchase_category' AS query_type,
    item_category AS segment_label,
    COUNT(*) AS metric_1,
    CAST(SUM(quantity) AS INT64) AS metric_2,
    CAST(ROUND(SUM(item_revenue)) AS INT64) AS metric_3,
    CAST(NULL AS FLOAT64) AS pct_1
  FROM purchase_items
  GROUP BY item_category
  ORDER BY metric_3 DESC
  LIMIT 20
)

SELECT * FROM category_view_to_cart
UNION ALL
SELECT * FROM item_view_to_cart
UNION ALL
SELECT * FROM purchase_category
ORDER BY query_type, metric_1 DESC;
