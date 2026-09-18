{{ config(materialized='table') }}

with orders_by_customer as (
    select
        customer_id,
        count(*) as n_orders,
        sum(order_amount) as total_amount,
        min(order_date) as first_order_date,
        max(order_date) as most_recent_order_date
    from {{ ref('int_qualifying_orders') }}
    group by customer_id
)

select
    c.customer_id,
    c.customer_name,
    o.n_orders,
    o.total_amount,
    o.first_order_date,
    o.most_recent_order_date
from orders_by_customer as o
inner join {{ ref('stg_customers') }} as c
    on o.customer_id = c.customer_id
