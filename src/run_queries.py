"""Phase 2: run every sql/0N_*.sql file and save its result to data/0N_*.csv."""
from pathlib import Path

from bq_client import run_query

ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = ROOT / "sql"
DATA_DIR = ROOT / "data"


def main():
    sql_files = sorted(SQL_DIR.glob("0[1-6]_*.sql"))
    for sql_path in sql_files:
        sql = sql_path.read_text(encoding="utf-8")
        df = run_query(sql, label=sql_path.stem)
        out_csv = DATA_DIR / f"{sql_path.stem}.csv"
        df.to_csv(out_csv, index=False)
        print(f"  -> {out_csv} ({len(df)} rows)")


if __name__ == "__main__":
    main()
