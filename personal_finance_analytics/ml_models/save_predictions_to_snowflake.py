import pandas as pd 
import snowflake.connector
from prophet import Prophet
from datetime import datetime
import os
from dotenv import load_dotenv 

load_dotenv()

#connecting to Snowflake
conn = snowflake.connector.connect(
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASSWORD'),
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    warehouse='COMPUTE_WH',
    database='PERSONAL_FINANCES',
    schema='PUBLIC'
)

cursor = conn.cursor()

#create predictions table if it doesn't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS ML_SPENDING_PREDICTIONS (
    prediction_date DATE,
    category VARCHAR(100),
    predicted_amount FLOAT,
    predicted_lower FLOAT,
    predicted_upper FLOAT,
    model_run_date TIMESTAMP,
    PRIMARY KEY (prediction_date, category)
)
""")

#get historical data
query = """
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
df.columns = df.columns.str.lower()

categories = df['category'].unique()
all_predictions = []

# Generate predictions for each category
for category in categories:
    print(f"Forecasting {category}...")
    
    cat_data = df[df['category'] == category][['ds', 'y']].copy()
    cat_data['ds'] = pd.to_datetime(cat_data['ds'])
    
    model = Prophet(
        daily_seasonality=False,
        weekly_seasonality=True,
        yearly_seasonality=False,
        changepoint_prior_scale=0.05
    )
    model.fit(cat_data)
    
    # Predict next 30 days
    future = model.make_future_dataframe(periods=30)
    forecast = model.predict(future)
    
    # Get only future predictions (last 30 days)
    future_predictions = forecast.tail(30).copy()
    future_predictions['category'] = category
    future_predictions['model_run_date'] = datetime.now()
    
    # Select only the columns we need
    future_predictions = future_predictions[['ds', 'yhat', 'yhat_lower', 'yhat_upper', 'category', 'model_run_date']]
    
    all_predictions.append(future_predictions)

# Combine all predictions
predictions_df = pd.concat(all_predictions, ignore_index=True)

# Rename columns to match Snowflake table
predictions_df = predictions_df.rename(columns={
    'ds': 'PREDICTION_DATE',
    'yhat': 'PREDICTED_AMOUNT',
    'yhat_lower': 'PREDICTED_LOWER',
    'yhat_upper': 'PREDICTED_UPPER',
    'category': 'CATEGORY',
    'model_run_date': 'MODEL_RUN_DATE'
})

#clear old predictions
cursor.execute("DELETE FROM ML_SPENDING_PREDICTIONS")

#insert predictions
for _, row in predictions_df.iterrows():
    cursor.execute("""
    INSERT INTO ML_SPENDING_PREDICTIONS
    (prediction_date, category, predicted_amount, predicted_lower, predicted_upper, model_run_date)
    VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        row['PREDICTION_DATE'].date(),
        row['CATEGORY'],
        float(row['PREDICTED_AMOUNT']),
        float(row['PREDICTED_LOWER']),
        float(row['PREDICTED_UPPER']),
        row['MODEL_RUN_DATE'].to_pydatetime()
    ))


conn.commit()
cursor.close()
conn.close()

print(f"\n✅ Saved {len(predictions_df)} predictions to Snowflake!")
print(f"Categories: {', '.join(categories)}")