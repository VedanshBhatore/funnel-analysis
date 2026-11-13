-- 06_time_patterns.sql
-- Session conversion rate by day of week and hour of day.
-- Day/hour bucket is taken from each session's first event timestamp.
-- event_timestamp is UTC in the GA4 export and this dataset does not
-- expose a reliable per-event local timezone (device.time_zone_offset_seconds
-- is not populated in this obfuscated sample), so all times below are UTC
-- -- documented in docs/data-profile.md.

WITH session_events AS (
  SELECT
    CONCAT(user_pseudo_id, '-', CAST(
      (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id')
      AS STRING)) AS session_key,
    event_timestamp,
    event_name
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
    AND (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') IS NOT NULL
),

session_level AS (
  SELECT
    session_key,
    MIN(event_timestamp) AS session_start_ts,
    MAX(IF(event_name = 'purchase', 1, 0)) AS has_purchase
  FROM session_events
  GROUP BY session_key
),

bucketed AS (
  SELECT
    FORMAT_TIMESTAMP('%A', TIMESTAMP_MICROS(session_start_ts)) AS day_of_week,
    EXTRACT(DAYOFWEEK FROM TIMESTAMP_MICROS(session_start_ts)) AS day_of_week_num,
    EXTRACT(HOUR FROM TIMESTAMP_MICROS(session_start_ts)) AS hour_of_day_utc,
    has_purchase
  FROM session_level
)

SELECT
  day_of_week,
  day_of_week_num,
  hour_of_day_utc,
  COUNT(*) AS sessions,
  SUM(has_purchase) AS converting_sessions,
  ROUND(SAFE_DIVIDE(SUM(has_purchase), COUNT(*)) * 100, 2) AS conversion_rate_pct
FROM bucketed
GROUP BY day_of_week, day_of_week_num, hour_of_day_utc
ORDER BY day_of_week_num, hour_of_day_utc;
