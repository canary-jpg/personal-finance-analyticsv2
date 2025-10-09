-- Test that expenses don't spike unreasonably compared to income
-- Excludes current month since it may be incomplete
SELECT
    month,
    total_expenses,
    total_income
FROM {{ ref('monthly_financial_summary') }}
WHERE total_expenses > (total_income * 5)
  AND month < DATE_TRUNC('month', CURRENT_DATE())
  AND total_income > 0