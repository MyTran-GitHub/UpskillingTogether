"""Time the two builds, compare their results, and export the final mart."""

import csv
import json
import shutil
import subprocess
import time
from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[1]
LOCAL_DBT = ROOT / ".venv" / "bin" / "dbt"
DBT = str(LOCAL_DBT) if LOCAL_DBT.exists() else shutil.which("dbt")
if DBT is None:
    raise RuntimeError("dbt is not installed in .venv or on PATH")
DATABASE = ROOT / "data" / "pipeline.duckdb"
OUTPUT = ROOT
COLUMNS = (
    "customer_id",
    "customer_name",
    "n_orders",
    "total_amount",
    "first_order_date",
    "most_recent_order_date",
)


def run_and_time(label, full_refresh=False):
    command = [DBT, "run", "--profiles-dir", str(ROOT), "--select", "int_qualifying_orders+"]
    if full_refresh:
        command.append("--full-refresh")
    started = time.perf_counter()
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    elapsed = time.perf_counter() - started
    (ROOT / "data" / f"{label}_run.log").write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(f"{label} dbt run failed; see data/{label}_run.log")
    run_results = json.loads((ROOT / "target" / "run_results.json").read_text())
    model_times = {
        item["unique_id"].rsplit(".", 1)[-1]: item["execution_time"]
        for item in run_results["results"]
    }
    return elapsed, model_times


def read_mart():
    with duckdb.connect(str(DATABASE), read_only=True) as connection:
        return connection.execute(
            "select * from main.customer_orders order by customer_id"
        ).fetchall()


incremental_seconds, incremental_models = run_and_time("incremental")
incremental_rows = read_mart()
with duckdb.connect(str(DATABASE), read_only=True) as connection:
    qualifying_count = connection.execute(
        "select count(*) from main.int_qualifying_orders"
    ).fetchone()[0]

refresh_seconds, refresh_models = run_and_time("full_refresh", full_refresh=True)
refresh_rows = read_mart()
if incremental_rows != refresh_rows:
    raise AssertionError("Incremental result differs from the full refresh")

OUTPUT.mkdir(exist_ok=True)
with (OUTPUT / "customer_orders.csv").open("w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(COLUMNS)
    writer.writerows(refresh_rows)

(OUTPUT / "NOTES.md").write_text(
    f"""# Incremental demonstration

- Initial batch: orders through 2025-03-31 (2,500 raw orders; 1,698 qualifying orders).
- Second batch: all supplied rows (5,000 raw orders; {qualifying_count} qualifying orders).
- The incremental model keeps one row per qualifying order. On later runs it selects `order_date` values greater than the latest date already in its table. The customer mart is rebuilt from all stored qualifying orders.
- Incremental run over the second batch: {incremental_seconds:.3f} seconds wall time; model SQL timings: {incremental_models}.
- Full refresh over all supplied rows on the same machine: {refresh_seconds:.3f} seconds wall time; model SQL timings: {refresh_models}.
- Results: {len(refresh_rows)} customer rows; incremental output exactly equals full-refresh output.
- The fixture adds later-dated orders. A production pipeline would need a lookback or change tracking to handle late-arriving older orders.
- Source freshness uses `order_date` on `raw_orders`; the historical fixture is expected to be stale against today's date.

# Orchestration

- Docker Compose runs Dagster with a daily 06:00 America/Los_Angeles schedule.
- The job runs dbt seed, a fail-once op, dbt run, dbt test, and the CSV export.
- The flaky op has one automatic retry. Its first attempt fails and its first retry succeeds on each fresh Dagster run.
- `orchestrator_log.txt` records the Docker execution and retry events.
"""
)

print(f"incremental: {incremental_seconds:.3f}s; full refresh: {refresh_seconds:.3f}s")
print(f"qualifying orders: {qualifying_count}; customers: {len(refresh_rows)}")
print("incremental result equals full refresh; exported customer_orders.csv")
