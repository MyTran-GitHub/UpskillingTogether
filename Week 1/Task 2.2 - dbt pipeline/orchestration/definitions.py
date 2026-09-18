"""Scheduled local dbt pipeline with one deliberate, automatically retried failure."""

import csv
import subprocess
from pathlib import Path

import duckdb
from dagster import (
    DefaultScheduleStatus,
    Definitions,
    OpExecutionContext,
    RetryPolicy,
    ScheduleDefinition,
    in_process_executor,
    job,
    op,
)


ROOT = Path(__file__).resolve().parents[1]
CSV_COLUMNS = (
    "customer_id",
    "customer_name",
    "n_orders",
    "total_amount",
    "first_order_date",
    "most_recent_order_date",
)


def run_dbt(context: OpExecutionContext, command: str) -> None:
    result = subprocess.run(
        ["dbt", command, "--no-partial-parse", "--profiles-dir", str(ROOT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    context.log.info(result.stdout)
    if result.returncode:
        context.log.error(result.stderr)
        raise RuntimeError(f"dbt {command} failed with exit code {result.returncode}")


@op
def load_seeds(context: OpExecutionContext) -> str:
    run_dbt(context, "seed")
    return "seeds loaded"


@op(retry_policy=RetryPolicy(max_retries=1, delay=0))
def flaky_once(context: OpExecutionContext, _seeded: str) -> str:
    attempt = context.retry_number + 1
    if attempt == 1:
        print("FLAKY_TASK attempt=1 failed intentionally", flush=True)
        context.log.error("FLAKY_TASK attempt=1 failed intentionally")
        raise RuntimeError("Intentional first-attempt failure")
    print("FLAKY_TASK attempt=2 succeeded on first retry", flush=True)
    context.log.info("FLAKY_TASK attempt=2 succeeded on first retry")
    return "retry succeeded"


@op
def build_models(context: OpExecutionContext, _retried: str) -> str:
    run_dbt(context, "run")
    return "models built"


@op
def test_models(context: OpExecutionContext, _built: str) -> str:
    run_dbt(context, "test")
    return "tests passed"


@op
def export_mart(context: OpExecutionContext, _tested: str) -> None:
    with duckdb.connect(str(ROOT / "data" / "pipeline.duckdb"), read_only=True) as connection:
        rows = connection.execute(
            "select * from main.customer_orders order by customer_id"
        ).fetchall()
    destination = ROOT / "customer_orders.csv"
    destination.parent.mkdir(exist_ok=True)
    with destination.open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(CSV_COLUMNS)
        writer.writerows(rows)
    context.log.info(f"Exported {len(rows)} customers to {destination}")


@job(executor_def=in_process_executor)
def customer_orders_job():
    export_mart(test_models(build_models(flaky_once(load_seeds()))))


daily_customer_orders = ScheduleDefinition(
    job=customer_orders_job,
    cron_schedule="0 6 * * *",
    execution_timezone="America/Los_Angeles",
    default_status=DefaultScheduleStatus.RUNNING,
)

defs = Definitions(jobs=[customer_orders_job], schedules=[daily_customer_orders])
