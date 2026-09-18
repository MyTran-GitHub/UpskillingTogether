{{ config(materialized='view') }}

select
    cast(customer_id as integer) as customer_id,
    trim(first_name) || ' ' || trim(last_name) as customer_name,
    cast(signup_date as date) as signup_date
from {{ source('raw', 'raw_customers') }}
