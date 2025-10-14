{{
    config(
        materialized='incremental',
        unique_key='transaction_id'
    )
}}

SELECT
    transaction_id,
    date::DATE as transaction_date,
    TRIM(description) as description,
    amount,
    TRIM(category) as category,
    TRIM(account_type) as account_type,
    CASE 
        WHEN amount > 0 THEN 'income'
        ELSE 'expense'
    END as transaction_type,
    CURRENT_TIMESTAMP() as dbt_updated_at
FROM {{ source('raw', 'raw_transactions') }}

{% if is_incremental() %}
WHERE date::DATE >= DATEADD(day, -7, CURRENT_DATE())
{% endif %}