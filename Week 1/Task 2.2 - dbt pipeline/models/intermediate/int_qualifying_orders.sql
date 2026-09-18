{{ config(materialized='incremental', incremental_strategy='append') }}

with qualifying_orders as (
    select order_id, customer_id, order_date
    from {{ ref('stg_orders') }}
    where status in ('completed', 'shipped')
    {% if is_incremental() %}
        and order_date > (
            select coalesce(max(order_date), date '1900-01-01')
            from {{ this }}
        )
    {% endif %}
),

payment_totals as (
    select p.order_id, sum(p.amount) as order_amount
    from {{ ref('stg_payments') }} as p
    inner join qualifying_orders as o on p.order_id = o.order_id
    group by p.order_id
)

select
    o.order_id,
    o.customer_id,
    o.order_date,
    coalesce(p.order_amount, cast(0 as decimal(12, 2))) as order_amount
from qualifying_orders as o
left join payment_totals as p on o.order_id = p.order_id
