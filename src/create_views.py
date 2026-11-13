"""Phase 5: create a `portfolio` dataset in GCP_PROJECT and one BigQuery VIEW
per analysis, pointed straight at the public GA4 table, so Looker Studio can
connect to live views instead of static CSVs.
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import bigquery

from bq_client import PROJECT, run_ddl

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DATASET = os.environ.get("PORTFOLIO_DATASET", "portfolio")
ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = ROOT / "sql"

VIEWS = {
    "kpis_daily": "01_kpis_daily.sql",
    "funnel": "02_funnel.sql",
    "funnel_by_segment": "03_funnel_segments.sql",
    "cohorts": "04_cohort_retention.sql",
    "product_funnel": "05_product_funnel.sql",
    "time_patterns": "06_time_patterns.sql",
}


def ensure_dataset():
    client = bigquery.Client(project=PROJECT)
    dataset_id = f"{PROJECT}.{DATASET}"
    try:
        client.get_dataset(dataset_id)
        print(f"Dataset {dataset_id} already exists")
    except Exception:
        ds = bigquery.Dataset(dataset_id)
        ds.location = "US"
        client.create_dataset(ds)
        print(f"Created dataset {dataset_id}")


def main():
    ensure_dataset()
    for view_name, sql_file in VIEWS.items():
        body = (SQL_DIR / sql_file).read_text(encoding="utf-8")
        ddl = f"CREATE OR REPLACE VIEW `{PROJECT}.{DATASET}.{view_name}` AS\n{body}"
        run_ddl(ddl, label=f"view:{view_name}")


if __name__ == "__main__":
    main()
