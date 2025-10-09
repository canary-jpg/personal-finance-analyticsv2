SELECT
    date::DATE as stock_date,
    TRIM(symbol) as symbol,
    price,
    shares_owned,
    portfolio_value,
    price * shares_owned as calculated_value
FROM {{ source('raw', 'raw_stock_data') }}