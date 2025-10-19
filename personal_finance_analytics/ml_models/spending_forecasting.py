import pandas as pd 
import snowflake.connector
from prophet import Prophet 
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv


load_dotenv()

#connect to Snowflake
conn = snowflake.connector.connect(
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASSWORD'),
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    warehouse='COMPUTE_WH',
    database='PERSONAL_FINANCES',
    schema='PUBLIC'
)

#get historical spending by category
query="""
SELECT
    transaction_date as ds,
    category,
    SUM(ABS(amount)) as y
FROM stg_transactions
WHERE transaction_type = 'expense'
GROUP BY transaction_date, category
ORDER BY transaction_date
"""

df = pd.read_sql(query, conn)
conn.close()

#snowflake returns uppercase column names, convert to lowercase
df.columns = df.columns.str.lower()

#sanity check
print(f"Loaded {len(df)} rows of data")
print(f"Columns: {df.columns.tolist()}")
print(f"Date range: {df['ds'].min()} to {df['ds'].max()}")

#forecast for each category
forecasts = {}
categories = df['category'].unique()

for category in categories:
    print(f"\nForecasting for {category}...")

    #prepare data for Prophet
    cat_data = df[df['category'] == category][['ds', 'y']].copy()
    cat_data['ds'] = pd.to_datetime(cat_data['ds'])

    #train Prophet model
    model = Prophet(
        daily_seasonality=False,
        weekly_seasonality=True,
        yearly_seasonality=False,
        changepoint_prior_scale=0.05
    )
    model.fit(cat_data)

    #make future dataframe (30 days ahead)
    future = model.make_future_dataframe(periods=30)
    forecast = model.predict(future)

    #store forecasts
    forecasts[category] = {
        'historical': cat_data,
        'forecast': forecast,
        'model': model 
    }

    #print next 7 days prediction
    next_week = forecast.tail(7)[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
    print(f"Next 7 days forecast:")
    print(next_week.to_string(index=False))

#create visualization
print("\n\nGenerating forecasting visualization...")

fig = go.Figure()

for category in list(categories)[:3]:
    forecast_data = forecasts[category]['forecast']
    historical_data = forecasts[category]['historical']

    #historical data
    fig.add_trace(go.Scatter(
        x=historical_data['ds'],
        y=historical_data['y'],
        mode='markers',
        name=f'{category} (actual)',
        marker=dict(size=4)
    ))

    #forecast
    fig.add_trace(go.Scatter(
        x=forecast_data['ds'],
        y=forecast_data['yhat'],
        mode='lines',
        name=f'{category} (forecast)',
        line=dict(dash='dash')
    ))

fig.update_layout(
    title='Spending Forecast by Category (Next 30 Days)',
    xaxis_title='Date',
    yaxis_title='Daily Spending ($)',
    height=600
)

fig.write_html('spending_forecast.html')
print("Forecast saved to spending_forecast.html")

#calculate total forecasted spending for next month
print("\n\n==== MONTHLY FORECAST SUMMARY ===")
total_forecast = 0
for category in categories:
    next_30 = forecasts[category]['forecast'].tail(30)['yhat'].sum()
    total_forecast += next_30
    print(f"{category}: ${next_30:.2f}")

print(f"\nTotal forecasted spending (next 30 days): ${total_forecast:.2f}")