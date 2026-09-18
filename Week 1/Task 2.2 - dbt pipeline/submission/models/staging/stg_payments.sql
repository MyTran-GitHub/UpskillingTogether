{{ config(materialized='view') }}

select
    cast(payment_id as integer) as payment_id,
    cast(order_id as integer) as order_id,
    cast(amount as decimal(12, 2)) as amount,
    lower(trim(method)) as method
from {{ source('raw', 'raw_payments') }}
