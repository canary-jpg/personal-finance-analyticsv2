{% macro get_incremental_filter(
    date_column='transaction_date',
    lookback_days=7
) %}

{% if is_incremental() %}
    AND {{ date_column }} >= DATEADD(day, -{{ lookback_days }}, CURRENT_DATE())
{% endif %}

{% endmacro %}