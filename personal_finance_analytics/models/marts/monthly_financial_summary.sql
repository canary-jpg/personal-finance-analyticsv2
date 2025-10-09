WITH monthly_totals AS (
    SELECT
        DATE_TRUNC('month', transaction_date) as month,
        SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE 0 END) as total_income,
        SUM(CASE WHEN transaction_type = 'expense' THEN ABS(amount) ELSE 0 END) as total_expenses,
        COUNT(CASE WHEN transaction_type = 'income' THEN 1 END) as income_transaction_count,
        COUNT(CASE WHEN transaction_type = 'expense' THEN 1 END) as expense_transaction_count
    FROM {{ ref('stg_transactions') }}
    GROUP BY 1
),

monthly_with_calcs AS (
    SELECT
        month,
        total_income,
        total_expenses,
        income_transaction_count,
        expense_transaction_count,
        total_income - total_expenses as net_income,
        CASE 
            WHEN total_income > 0 THEN 
                ((total_income - total_expenses) / total_income) * 100 
            ELSE 0 
        END as savings_rate,
        LAG(total_income) OVER (ORDER BY month) as prev_month_income,
        LAG(total_expenses) OVER (ORDER BY month) as prev_month_expenses,
        LAG(total_income - total_expenses) OVER (ORDER BY month) as prev_month_net_income
    FROM monthly_totals
)

SELECT
    month,
    ROUND(total_income, 2) as total_income,
    ROUND(total_expenses, 2) as total_expenses,
    ROUND(net_income, 2) as net_income,
    ROUND(savings_rate, 2) as savings_rate_pct,
    income_transaction_count,
    expense_transaction_count,
    ROUND(total_income - prev_month_income, 2) as mom_income_change,
    ROUND(total_expenses - prev_month_expenses, 2) as mom_expense_change,
    ROUND(net_income - prev_month_net_income, 2) as mom_net_income_change,
    CASE 
        WHEN prev_month_income > 0 THEN 
            ROUND(((total_income - prev_month_income) / prev_month_income) * 100, 2)
        ELSE NULL 
    END as mom_income_change_pct,
    CASE 
        WHEN prev_month_expenses > 0 THEN 
            ROUND(((total_expenses - prev_month_expenses) / prev_month_expenses) * 100, 2)
        ELSE NULL 
    END as mom_expense_change_pct,
    CASE
        WHEN savings_rate >= 20 THEN 'EXCELLENT'
        WHEN savings_rate >= 10 THEN 'GOOD'
        WHEN savings_rate >= 0 THEN 'FAIR'
        ELSE 'CONCERNING'
    END as financial_health_status
FROM monthly_with_calcs
ORDER BY month DESC