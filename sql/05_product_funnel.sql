-- 05_product_funnel.sql
-- Two outputs in one result set (query_type column distinguishes them):
--   'category'  -> view-to-cart and cart-to-purchase rates by item_category
--   'item'      -> items with high view volume but a low view-to-purchase
--                   rate (viewed a lot, rarely bought)
-- Granularity note: GA4's `items` is an array nested inside each event row
-- (one event can list several items), so we UNNEST it and count item-level
-- occurrences, not sessions.

-- MIN_VIEWS_FOR_ITEM_RANKING threshold is inlined below as a literal (50)
-- rather than DECLAREd -- see the note in 03_funnel_segments.sql on why
-- this project avoids BigQuery scripts (DECLARE + multi-statement) in
-- favor of single-statement queries.

WITH item_events AS (
  SELECT
    event_name,
    COALESCE(item.item_category, '(not set)') AS item_category,
    item.item_id,
    COALESCE(item.item_name, '(not set)') AS item_name
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`,
    UNNEST(items) AS item
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
    AND event_name IN ('view_item', 'add_to_cart', 'purchase')
),

by_category AS (
  SELECT
    'category' AS query_type,
    item_category AS segment_label,
    COUNTIF(event_name = 'view_item') AS views,
    COUNTIF(event_name = 'add_to_cart') AS carts,
    COUNTIF(event_name = 'purchase') AS purchases,
    ROUND(SAFE_DIVIDE(COUNTIF(event_name = 'add_to_cart'), COUNTIF(event_name = 'view_item')) * 100, 2)
      AS view_to_cart_pct,
    ROUND(SAFE_DIVIDE(COUNTIF(event_name = 'purchase'), COUNTIF(event_name = 'add_to_cart')) * 100, 2)
      AS cart_to_purchase_pct
  FROM item_events
  GROUP BY item_category
),

by_item AS (
  SELECT
    'item' AS query_type,
    CONCAT(item_name, ' [', item_id, ']') AS segment_label,
    COUNTIF(event_name = 'view_item') AS views,
    COUNTIF(event_name = 'add_to_cart') AS carts,
    COUNTIF(event_name = 'purchase') AS purchases,
    ROUND(SAFE_DIVIDE(COUNTIF(event_name = 'add_to_cart'), COUNTIF(event_name = 'view_item')) * 100, 2)
      AS view_to_cart_pct,
    ROUND(SAFE_DIVIDE(COUNTIF(event_name = 'purchase'), COUNTIF(event_name = 'view_item')) * 100, 2)
      AS cart_to_purchase_pct  -- for 'item' rows this column holds view-to-purchase %
  FROM item_events
  GROUP BY item_id, item_name
  HAVING COUNTIF(event_name = 'view_item') >= 50
  ORDER BY cart_to_purchase_pct ASC, views DESC
  LIMIT 20
)

SELECT * FROM by_category
UNION ALL
SELECT * FROM by_item
ORDER BY query_type, views DESC;
