# Incremental demonstration

- Initial batch: orders through 2025-03-31 (2,500 raw orders; 1,698 qualifying orders).
- Second batch: all supplied rows (5,000 raw orders; 3376 qualifying orders).
- The incremental model keeps one row per qualifying order. On later runs it selects `order_date` values greater than the latest date already in its table. The customer mart is rebuilt from all stored qualifying orders.
- Incremental run over the second batch: 1.802 seconds wall time; model SQL timings: {'int_qualifying_orders': 0.08044004440307617, 'customer_orders': 0.04796171188354492}.
- Full refresh over all supplied rows on the same machine: 1.841 seconds wall time; model SQL timings: {'int_qualifying_orders': 0.08675122261047363, 'customer_orders': 0.03210926055908203}.
- Results: 400 customer rows; incremental output exactly equals full-refresh output.
- The fixture adds later-dated orders. A production pipeline would need a lookback or change tracking to handle late-arriving older orders.
- Source freshness uses `order_date` on `raw_orders`; the historical fixture is expected to be stale against today's date.

# Orchestration

- Docker Compose runs Dagster with a daily 06:00 America/Los_Angeles schedule.
- The job runs dbt seed, a fail-once op, dbt run, dbt test, and the CSV export.
- The flaky op has one automatic retry. Its first attempt fails and its first retry succeeds on each fresh Dagster run.
- `orchestrator_log.txt` records the Docker execution and retry events.
