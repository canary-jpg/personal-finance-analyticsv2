WITH daily_portfolio AS (
    SELECT
        stock_date,
        symbol,
        price,
        shares_owned,
        portfolio_value,
        LAG(portfolio_value) OVER (PARTITION BY symbol ORDER BY stock_date) as prev_day_value
    FROM {{ ref('stg_stock_data') }}
),

portfolio_with_gains AS (
    SELECT
        stock_date,
        symbol,
        price,
        shares_owned,
        portfolio_value,
        portfolio_value - prev_day_value as daily_gain,
        CASE 
            WHEN prev_day_value > 0 THEN 
                ((portfolio_value - prev_day_value) / prev_day_value) * 100
            ELSE 0
        END as daily_gain_pct
    FROM daily_portfolio
)

SELECT
    stock_date,
    symbol,
    price,
    shares_owned,
    ROUND(portfolio_value, 2) as portfolio_value,
    ROUND(daily_gain, 2) as daily_gain,
    ROUND(daily_gain_pct, 2) as daily_gain_pct,
    SUM(portfolio_value) OVER (PARTITION BY stock_date) as total_portfolio_value
FROM portfolio_with_gains
ORDER BY stock_date DESC, symbol