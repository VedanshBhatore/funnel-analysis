-- 03_funnel_segments.sql
-- Same 7-step session funnel as 02_funnel.sql, broken out by device
-- category, traffic medium, traffic source, and country (top 10 by
-- session volume). Segments with fewer than MIN_TRUSTED_SESSIONS sessions
-- at the first step are flagged low_sample = TRUE and should not be used
-- to make decisions (step-conversion % is noisy on small denominators).

-- MIN_TRUSTED_SESSIONS threshold is inlined below as a literal (100)
-- rather than DECLAREd, so this stays a single-statement query: BigQuery
-- scripts (DECLARE + multiple statements) return results via a child job,
-- which the plain query() + result() pattern in src/bq_client.py does not
-- follow.

WITH session_base AS (
  SELECT
    CONCAT(user_pseudo_id, '-', CAST(
      (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id')
      AS STRING)) AS session_key,
    ANY_VALUE(device.category) AS device_category,
    ANY_VALUE(traffic_source.medium) AS traffic_medium,
    ANY_VALUE(traffic_source.source) AS traffic_source,
    ANY_VALUE(geo.country) AS country,
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
    device_category, traffic_medium, traffic_source, country,
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
  FROM session_base
),

top_countries AS (
  SELECT country
  FROM sequential
  WHERE step1
  GROUP BY country
  ORDER BY COUNT(*) DESC
  LIMIT 10
),

segmented AS (
  SELECT 'device_category' AS segment_type, COALESCE(device_category, '(not set)') AS segment_value,
         step1, step2, step3, step4, step5, step6, step7
  FROM sequential
  UNION ALL
  SELECT 'traffic_medium', COALESCE(traffic_medium, '(not set)'),
         step1, step2, step3, step4, step5, step6, step7
  FROM sequential
  UNION ALL
  SELECT 'traffic_source', COALESCE(traffic_source, '(not set)'),
         step1, step2, step3, step4, step5, step6, step7
  FROM sequential
  UNION ALL
  SELECT 'country', COALESCE(country, '(not set)'),
         step1, step2, step3, step4, step5, step6, step7
  FROM sequential
  WHERE country IN (SELECT country FROM top_countries)
),

counts AS (
  SELECT segment_type, segment_value, 1 AS step_order, 'session_start' AS step_name,
         COUNTIF(step1) AS sessions
  FROM segmented GROUP BY 1, 2
  UNION ALL
  SELECT segment_type, segment_value, 2, 'view_item', COUNTIF(step2)
  FROM segmented GROUP BY 1, 2
  UNION ALL
  SELECT segment_type, segment_value, 3, 'add_to_cart', COUNTIF(step3)
  FROM segmented GROUP BY 1, 2
  UNION ALL
  SELECT segment_type, segment_value, 4, 'begin_checkout', COUNTIF(step4)
  FROM segmented GROUP BY 1, 2
  UNION ALL
  SELECT segment_type, segment_value, 5, 'add_shipping_info', COUNTIF(step5)
  FROM segmented GROUP BY 1, 2
  UNION ALL
  SELECT segment_type, segment_value, 6, 'add_payment_info', COUNTIF(step6)
  FROM segmented GROUP BY 1, 2
  UNION ALL
  SELECT segment_type, segment_value, 7, 'purchase', COUNTIF(step7)
  FROM segmented GROUP BY 1, 2
),

first_step AS (
  SELECT segment_type, segment_value, sessions AS initial_sessions
  FROM counts
  WHERE step_order = 1
)

SELECT
  c.segment_type,
  c.segment_value,
  c.step_order,
  c.step_name,
  c.sessions,
  ROUND(SAFE_DIVIDE(c.sessions, f.initial_sessions) * 100, 2) AS pct_of_initial,
  ROUND(SAFE_DIVIDE(c.sessions, LAG(c.sessions) OVER (
    PARTITION BY c.segment_type, c.segment_value ORDER BY c.step_order)) * 100, 2)
    AS step_conversion_pct,
  ROUND(100 - SAFE_DIVIDE(c.sessions, LAG(c.sessions) OVER (
    PARTITION BY c.segment_type, c.segment_value ORDER BY c.step_order)) * 100, 2)
    AS dropoff_pct,
  f.initial_sessions < 100 AS low_sample
FROM counts c
JOIN first_step f USING (segment_type, segment_value)
ORDER BY c.segment_type, f.initial_sessions DESC, c.step_order;
