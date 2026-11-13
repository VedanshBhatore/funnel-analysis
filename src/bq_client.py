"""Shared BigQuery helper: loads GCP_PROJECT from .env, dry-runs every query to
print bytes billed before executing it for real, and returns a pandas DataFrame.
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

PROJECT = os.environ.get("GCP_PROJECT")
if not PROJECT:
    raise RuntimeError(
        "GCP_PROJECT is not set. Copy .env.example to .env and fill in your "
        "BigQuery sandbox project id."
    )

_client = bigquery.Client(project=PROJECT)


def run_query(sql: str, label: str = ""):
    """Dry-run `sql` to print estimated bytes processed, then execute it and
    return the result as a pandas DataFrame."""
    dry_run_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    dry_job = _client.query(sql, job_config=dry_run_config)
    gb = dry_job.total_bytes_processed / 1e9
    print(f"[{label or 'query'}] dry run: {gb:.3f} GB will be processed")

    job = _client.query(sql)
    df = job.result().to_dataframe()
    print(f"[{label or 'query'}] done: {len(df)} rows returned, "
          f"{job.total_bytes_billed / 1e9:.3f} GB billed")
    return df


def run_ddl(sql: str, label: str = ""):
    """Execute a DDL statement (CREATE VIEW, etc.) with no return value."""
    job = _client.query(sql)
    job.result()
    print(f"[{label or 'ddl'}] done")
