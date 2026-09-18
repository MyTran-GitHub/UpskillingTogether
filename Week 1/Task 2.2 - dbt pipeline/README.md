# Customer orders dbt pipeline

The project loads the three CSV fixtures into DuckDB, builds staging views, an
incremental qualifying-order table, and the final `customer_orders` table.

## Docker schedule

Run `docker compose up -d` from this directory. Dagster is available at
<http://localhost:3000>. The `customer_orders_job_schedule` schedule is active
by default and runs every day at 06:00 America/Los_Angeles.

To execute the same job immediately and capture retry evidence:

```sh
docker compose run --rm dagster dagster job execute \
  -f orchestration/definitions.py -j customer_orders_job \
  > orchestrator_log.txt 2>&1
```

The job runs `dbt seed`, a task that fails once and retries successfully,
`dbt run`, `dbt test`, and exports `customer_orders.csv`.

## Incremental demonstration

The original `raw_*.csv` files stay unchanged. `scripts/stage_seed_data.py`
generates the seed batch through 2025-03-31 or the complete batch. With dbt
installed in `.venv`, reproduce the comparison using:

```sh
python3 scripts/stage_seed_data.py initial
.venv/bin/dbt seed --profiles-dir .
.venv/bin/dbt run --profiles-dir . --full-refresh --select int_qualifying_orders+
python3 scripts/stage_seed_data.py all
.venv/bin/dbt seed --profiles-dir .
.venv/bin/python scripts/compare_runs.py
```

The final script times incremental and full-refresh builds, compares their
outputs, and writes `NOTES.md` and the final CSV.

The orders source has a freshness check using `order_date`. Since the fixture is
historical, a wall-clock freshness check is expected to report stale data.
