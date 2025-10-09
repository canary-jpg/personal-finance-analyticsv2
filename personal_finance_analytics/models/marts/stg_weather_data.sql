SELECT
    date::DATE as weather_date,
    temp as temperature_f,
    feels_like as feels_like_f,
    humidity,
    TRIM(weather_condition) as weather_condition,
    TRIM(description) as weather_description
FROM {{ source('raw', 'raw_weather_data') }}