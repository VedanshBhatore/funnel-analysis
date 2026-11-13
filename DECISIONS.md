# Decisions Log

One line per decision: what was decided + why. Appended as the project proceeds.

- **Dataset**: used `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*` exactly as specified (Google Merchandise Store GA4 sample, Nov 2020-Jan 2021) — real public data, no scraping/synthetic data needed.
- **Repo layout**: `sql/`, `src/`, `data/`, `charts/`, `docs/` top-level, flat `analysis.ipynb` at root — matches the spec's tech-stack section exactly so graders/reviewers can navigate by convention.
- **Python env**: pinned exact versions in `requirements.txt` (google-cloud-bigquery 3.26.0, pandas 2.2.3, matplotlib 3.9.2, scipy 1.14.1, statsmodels 0.14.4) — reproducibility; avoids "works on my machine" drift for a portfolio piece others may try to run.
- **BigQuery auth**: used Application Default Credentials (`gcloud auth application-default login`) rather than a service-account JSON key — ADC is the standard sandbox-friendly flow and avoids committing/managing a long-lived key file.
- **Cost control**: every query script calls a BigQuery dry run first and prints estimated bytes scanned before executing; all table scans filter on `_TABLE_SUFFIX` to the Nov 2020-Jan 2021 range and SELECT only needed columns, to stay inside the BigQuery sandbox free tier (1 TB/month).
- **Session identification**: used `(SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id')` combined with `user_pseudo_id` as the session key, since GA4 export has no native `session_id` column — this is the standard GA4 BigQuery pattern.
- **`make` availability**: the Makefile is written for GNU Make (per spec) but this Windows dev machine has no `make` on PATH; phases were run by invoking the underlying `python src/...py` commands directly, and `make all` is re-verified in Phase 6 wherever `make` is available (or documented as equivalent-commands-run if not).
- **Obfuscation handling**: documented explicitly in `docs/data-profile.md` — placeholder values like `(data deleted)`, `<Other>`, and NULL dimension values are kept as their own category in GROUP BYs (never silently dropped) so funnel/segment denominators stay correct; only rows missing the fields required for a given query's join/key (e.g. no `ga_session_id`) are excluded, and that exclusion count is reported.
