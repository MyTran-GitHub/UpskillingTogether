{{ config(materialized='view') }}

select
    cast(order_id as integer) as order_id,
    cast(customer_id as integer) as customer_id,
    cast(order_date as date) as order_date,
    lower(trim(status)) as status
from {{ source('raw', 'raw_orders') }}
