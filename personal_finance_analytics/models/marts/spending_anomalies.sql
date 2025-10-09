WITH monthly_spending AS (
    SELECT
        DATE_TRUNC('month', transaction_date) as month,
        category,
        SUM(CASE WHEN transaction_type = 'expense' THEN ABS(amount) ELSE 0 END) as total_spent,
        COUNT(CASE WHEN transaction_type = 'expense' THEN 1 END) as transaction_count
    FROM {{ ref('stg_transactions') }}
    GROUP BY 1, 2
),

category_stats AS (
    SELECT
        category,
        AVG(total_spent) as avg_monthly_spending,
        STDDEV(total_spent) as stddev_spending,
        MIN(total_spent) as min_spending,
        MAX(total_spent) as max_spending
    FROM monthly_spending
    GROUP BY 1
),

spending_with_stats AS (
    SELECT
        ms.month,
        ms.category,
        ms.total_spent,
        ms.transaction_count,
        cs.avg_monthly_spending,
        cs.stddev_spending,
        cs.min_spending,
        cs.max_spending,
        CASE 
            WHEN cs.stddev_spending > 0 THEN 
                (ms.total_spent - cs.avg_monthly_spending) / cs.stddev_spending
            ELSE 0 
        END as z_score,
        ((ms.total_spent - cs.avg_monthly_spending) / cs.avg_monthly_spending) * 100 as pct_diff_from_avg
    FROM monthly_spending ms
    JOIN category_stats cs ON ms.category = cs.category
)

SELECT
    month,
    category,
    total_spent,
    transaction_count,
    ROUND(avg_monthly_spending, 2) as avg_monthly_spending,
    ROUND(z_score, 2) as z_score,
    ROUND(pct_diff_from_avg, 2) as pct_diff_from_avg,
    CASE
        WHEN ABS(z_score) > 2 THEN 'HIGH ANOMALY'
        WHEN ABS(z_score) > 1.5 THEN 'MODERATE ANOMALY'
        WHEN z_score > 1 THEN 'SLIGHTLY HIGH'
        WHEN z_score < -1 THEN 'SLIGHTLY LOW'
        ELSE 'NORMAL'
    END as anomaly_flag,
    CASE
        WHEN z_score > 0 THEN 'OVERSPENDING'
        WHEN z_score < 0 THEN 'UNDERSPENDING'
        ELSE 'AVERAGE'
    END as spending_trend
FROM spending_with_stats
ORDER BY month DESC, ABS(z_score) DESC