-- 02_funnel.sql
-- Session-level funnel: session_start -> view_item -> add_to_cart ->
-- begin_checkout -> add_shipping_info -> add_payment_info -> purchase.
--
-- "A step only counts if the earlier steps happened in the same session":
-- we compute one boolean flag per step per session (did this event_name
-- ever occur in this session), then AND each flag with every prior step's
-- flag so a session that skipped a step (e.g. add_to_cart logged without a
-- preceding view_item, which can happen from a saved cart or a replay)
-- does not get credited for the later steps either.

WITH session_flags AS (
  SELECT
    CONCAT(user_pseudo_id, '-', CAST(
      (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id')
      AS STRING)) AS session_key,
    LOGICAL_OR(event_name = 'session_start') AS has_session_start,
    LOGICAL_OR(event_name = 'view_item') AS has_view_item,
    LOGICAL_OR(event_name = 'add_to_cart') AS has_add_to_cart,
    LOGICAL_OR(event_name = 'begin_checkout') AS has_begin_checkout,
    LOGICAL_OR(event_name = 'add_shipping_info') AS has_add_shipping_info,
    LOGICAL_OR(event_name = 'add_payment_info') AS has_add_payment_info,
    LOGICAL_OR(event_name = 'purchase') AS has_purchase
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
    AND (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') IS NOT NULL
  GROUP BY session_key
),

sequential AS (
  SELECT
    has_session_start AS step1,
    has_session_start AND has_view_item AS step2,
    has_session_start AND has_view_item AND has_add_to_cart AS step3,
    has_session_start AND has_view_item AND has_add_to_cart AND has_begin_checkout AS step4,
    has_session_start AND has_view_item AND has_add_to_cart AND has_begin_checkout
      AND has_add_shipping_info AS step5,
    has_session_start AND has_view_item AND has_add_to_cart AND has_begin_checkout
      AND has_add_shipping_info AND has_add_payment_info AS step6,
    has_session_start AND has_view_item AND has_add_to_cart AND has_begin_checkout
      AND has_add_shipping_info AND has_add_payment_info AND has_purchase AS step7
  FROM session_flags
),

counts AS (
  SELECT
    1 AS step_order, 'session_start' AS step_name, COUNTIF(step1) AS sessions FROM sequential
  UNION ALL
  SELECT 2, 'view_item', COUNTIF(step2) FROM sequential
  UNION ALL
  SELECT 3, 'add_to_cart', COUNTIF(step3) FROM sequential
  UNION ALL
  SELECT 4, 'begin_checkout', COUNTIF(step4) FROM sequential
  UNION ALL
  SELECT 5, 'add_shipping_info', COUNTIF(step5) FROM sequential
  UNION ALL
  SELECT 6, 'add_payment_info', COUNTIF(step6) FROM sequential
  UNION ALL
  SELECT 7, 'purchase', COUNTIF(step7) FROM sequential
)

SELECT
  step_order,
  step_name,
  sessions,
  ROUND(SAFE_DIVIDE(sessions, FIRST_VALUE(sessions) OVER (ORDER BY step_order)) * 100, 2)
    AS pct_of_initial,
  ROUND(SAFE_DIVIDE(sessions, LAG(sessions) OVER (ORDER BY step_order)) * 100, 2)
    AS step_conversion_pct,
  ROUND(100 - SAFE_DIVIDE(sessions, LAG(sessions) OVER (ORDER BY step_order)) * 100, 2)
    AS dropoff_pct
FROM counts
ORDER BY step_order;
