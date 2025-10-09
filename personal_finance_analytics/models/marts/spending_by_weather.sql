SELECT
    t.transaction_date,
    w.weather_condition,
    w.temperature_f,
    t.category,
    COUNT(*) as transaction_count,
    SUM(CASE WHEN t.transaction_type = 'expense' THEN ABS(t.amount) ELSE 0 END) as total_spent
FROM {{ ref('stg_transactions') }} t
LEFT JOIN {{ ref('stg_weather_data') }} w 
    ON t.transaction_date = w.weather_date
WHERE t.transaction_type = 'expense'
GROUP BY 1, 2, 3, 4
ORDER BY 1 DESC