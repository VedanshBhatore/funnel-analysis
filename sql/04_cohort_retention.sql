-- 04_cohort_retention.sql
-- Weekly cohorts by first-visit week, showing % of each cohort's users
-- who return in weeks 1-8 after their first visit (week 0 = the cohort's
-- first week itself, always 100% by construction).

WITH user_dates AS (
  SELECT
    user_pseudo_id,
    PARSE_DATE('%Y%m%d', event_date) AS activity_date
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
  GROUP BY user_pseudo_id, activity_date
),

first_visit AS (
  SELECT
    user_pseudo_id,
    MIN(DATE_TRUNC(activity_date, WEEK(MONDAY))) AS cohort_week
  FROM user_dates
  GROUP BY user_pseudo_id
),

user_activity_weeks AS (
  SELECT DISTINCT
    ud.user_pseudo_id,
    fv.cohort_week,
    DATE_TRUNC(ud.activity_date, WEEK(MONDAY)) AS activity_week
  FROM user_dates ud
  JOIN first_visit fv USING (user_pseudo_id)
),

week_offsets AS (
  SELECT
    user_pseudo_id,
    cohort_week,
    DATE_DIFF(activity_week, cohort_week, WEEK) AS week_number
  FROM user_activity_weeks
  WHERE DATE_DIFF(activity_week, cohort_week, WEEK) BETWEEN 0 AND 8
),

cohort_sizes AS (
  SELECT cohort_week, COUNT(DISTINCT user_pseudo_id) AS cohort_size
  FROM first_visit
  GROUP BY cohort_week
),

retention AS (
  SELECT
    cohort_week,
    week_number,
    COUNT(DISTINCT user_pseudo_id) AS active_users
  FROM week_offsets
  GROUP BY cohort_week, week_number
)

SELECT
  cs.cohort_week,
  cs.cohort_size,
  r.week_number,
  r.active_users,
  ROUND(SAFE_DIVIDE(r.active_users, cs.cohort_size) * 100, 2) AS retention_pct
FROM cohort_sizes cs
JOIN retention r USING (cohort_week)
ORDER BY cs.cohort_week, r.week_number;
