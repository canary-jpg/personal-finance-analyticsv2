WITH daily_spending AS (
    SELECT
        transaction_date,
        SUM(CASE WHEN transaction_type = 'expense' THEN ABS(amount) ELSE 0 END) as daily_expenses,
        SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE 0 END) as daily_income,
        COUNT(*) as transaction_count
    FROM {{ ref('stg_transactions') }}
    GROUP BY 1
),

daily_portfolio AS (
    SELECT
        stock_date,
        SUM(portfolio_value) as total_portfolio_value,
        SUM(daily_gain) as total_daily_gain
    FROM {{ ref('portfolio_performance') }}
    GROUP BY 1
),

weather AS (
    SELECT
        weather_date,
        temperature_f,
        weather_condition,
        weather_description
    FROM {{ ref('stg_weather_data') }}
)

SELECT
    COALESCE(s.transaction_date, p.stock_date, w.weather_date) as date,
    COALESCE(s.daily_expenses, 0) as expenses,
    COALESCE(s.daily_income, 0) as income,
    s.transaction_count,
    p.total_portfolio_value,
    p.total_daily_gain as portfolio_gain,
    w.temperature_f,
    w.weather_condition,
    w.weather_description,
    COALESCE(s.daily_income - s.daily_expenses, 0) + COALESCE(p.total_daily_gain, 0) as total_daily_change
FROM daily_spending s
FULL OUTER JOIN daily_portfolio p ON s.transaction_date = p.stock_date
FULL OUTER JOIN weather w ON s.transaction_date = w.weather_date
ORDER BY date DESC