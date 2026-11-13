-- 01_kpis_daily.sql
-- Daily KPIs: users, sessions, conversion rate, revenue, average order value.
--
-- Session key: GA4 export has no native session_id column. The standard
-- pattern is user_pseudo_id + the 'ga_session_id' event param (an INT64
-- counter that is unique per user per session, but NOT globally unique on
-- its own, hence the concat with user_pseudo_id).
--
-- Revenue: ecommerce.purchase_revenue_in_usd is an event-level total
-- (already summed across items in that purchase event), so no per-item
-- double counting. We de-duplicate by ecommerce.transaction_id in case the
-- same purchase event fires more than once (e.g. page reload on the
-- confirmation page), which does happen in this dataset.

WITH events AS (
  SELECT
    event_date,
    user_pseudo_id,
    event_name,
    (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS ga_session_id,
    ecommerce.transaction_id AS transaction_id,
    ecommerce.purchase_revenue_in_usd AS purchase_revenue_in_usd
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
),

sessions AS (
  SELECT
    event_date,
    user_pseudo_id,
    CONCAT(user_pseudo_id, '-', CAST(ga_session_id AS STRING)) AS session_key,
    MAX(IF(event_name = 'purchase', 1, 0)) AS session_has_purchase
  FROM events
  WHERE ga_session_id IS NOT NULL
  GROUP BY event_date, user_pseudo_id, session_key
),

daily_sessions AS (
  SELECT
    event_date,
    COUNT(DISTINCT user_pseudo_id) AS users,
    COUNT(DISTINCT session_key) AS sessions,
    SUM(session_has_purchase) AS converting_sessions
  FROM sessions
  GROUP BY event_date
),

daily_orders AS (
  -- de-dup purchase events by transaction_id so repeat-fired purchase
  -- events don't inflate revenue or order count
  SELECT
    event_date,
    transaction_id,
    ANY_VALUE(purchase_revenue_in_usd) AS order_revenue_usd
  FROM events
  WHERE event_name = 'purchase' AND transaction_id IS NOT NULL
  GROUP BY event_date, transaction_id
),

daily_revenue AS (
  SELECT
    event_date,
    COUNT(DISTINCT transaction_id) AS orders,
    SUM(order_revenue_usd) AS revenue_usd
  FROM daily_orders
  GROUP BY event_date
)

SELECT
  ds.event_date,
  ds.users,
  ds.sessions,
  ds.converting_sessions,
  ROUND(SAFE_DIVIDE(ds.converting_sessions, ds.sessions) * 100, 2) AS conversion_rate_pct,
  COALESCE(dr.orders, 0) AS orders,
  ROUND(COALESCE(dr.revenue_usd, 0), 2) AS revenue_usd,
  ROUND(SAFE_DIVIDE(dr.revenue_usd, dr.orders), 2) AS avg_order_value_usd
FROM daily_sessions ds
LEFT JOIN daily_revenue dr USING (event_date)
ORDER BY ds.event_date;
