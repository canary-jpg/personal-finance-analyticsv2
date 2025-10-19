import streamlit as st
import snowflake.connector
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Personal Finance Dashboard",
    page_icon="💰",
    layout="wide"
)

@st.cache_resource
def get_snowflake_connection():
    return snowflake.connector.connect(
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        warehouse='COMPUTE_WH',
        database='PERSONAL_FINANCES',
        schema='PUBLIC'
    )

@st.cache_data(ttl=600)
def load_data(query):
    conn = get_snowflake_connection()
    df = pd.read_sql(query, conn)
    return df

st.title("💰 Personal Finance Dashboard")
st.markdown("---")

# Load data
financial_summary = load_data("SELECT * FROM monthly_financial_summary ORDER BY month DESC")
daily_summary = load_data("SELECT * FROM daily_summary_dashboard ORDER BY date DESC LIMIT 90")
spending_by_weather = load_data("""
    SELECT 
        weather_condition,
        COUNT(DISTINCT transaction_date) as days,
        SUM(total_spent) as total_spending,
        AVG(total_spent) as avg_daily_spending
    FROM spending_by_weather
    WHERE weather_condition IS NOT NULL
    GROUP BY weather_condition
    ORDER BY avg_daily_spending DESC
""")

# Key Metrics
latest_month = financial_summary.iloc[0]
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Current Month Income",
        f"${latest_month['TOTAL_INCOME']:,.0f}",
        f"{latest_month['MOM_INCOME_CHANGE_PCT']:.1f}% MoM"
    )

with col2:
    st.metric(
        "Current Month Expenses", 
        f"${latest_month['TOTAL_EXPENSES']:,.0f}",
        f"{latest_month['MOM_EXPENSE_CHANGE_PCT']:.1f}% MoM"
    )

with col3:
    st.metric(
        "Net Income",
        f"${latest_month['NET_INCOME']:,.0f}",
        latest_month['FINANCIAL_HEALTH_STATUS']
    )

with col4:
    st.metric(
        "Savings Rate",
        f"{latest_month['SAVINGS_RATE_PCT']:.1f}%"
    )

st.markdown("---")

# Charts
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Income vs Expenses Trend")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=financial_summary['MONTH'],
        y=financial_summary['TOTAL_INCOME'],
        name='Income',
        line=dict(color='green', width=3)
    ))
    fig.add_trace(go.Scatter(
        x=financial_summary['MONTH'],
        y=financial_summary['TOTAL_EXPENSES'],
        name='Expenses',
        line=dict(color='red', width=3)
    ))
    fig.update_layout(height=400, hovermode='x unified')
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("💾 Savings Rate Over Time")
    fig = px.bar(
        financial_summary,
        x='MONTH',
        y='SAVINGS_RATE_PCT',
        color='FINANCIAL_HEALTH_STATUS',
        color_discrete_map={
            'EXCELLENT': 'green',
            'GOOD': 'lightgreen',
            'FAIR': 'orange',
            'CONCERNING': 'red'
        }
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

# Weather impact
st.markdown("---")
st.subheader("🌦️ Spending by Weather Condition")
fig = px.bar(
    spending_by_weather,
    x='WEATHER_CONDITION',
    y='AVG_DAILY_SPENDING',
    color='AVG_DAILY_SPENDING',
    color_continuous_scale='RdYlGn_r'
)
fig.update_layout(height=400, showlegend=False)
st.plotly_chart(fig, use_container_width=True)

# Portfolio
st.markdown("---")
st.subheader("📊 Portfolio Performance (Last 90 Days)")

daily_summary['DATE'] = pd.to_datetime(daily_summary['DATE'])
portfolio_data = daily_summary[daily_summary['TOTAL_PORTFOLIO_VALUE'].notna()]

if len(portfolio_data) > 0:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=portfolio_data['DATE'],
        y=portfolio_data['TOTAL_PORTFOLIO_VALUE'],
        fill='tozeroy',
        name='Portfolio Value',
        line=dict(color='blue', width=2)
    ))
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Portfolio Value", f"${portfolio_data['TOTAL_PORTFOLIO_VALUE'].iloc[0]:,.2f}")
    with col2:
        total_gain = portfolio_data['PORTFOLIO_GAIN'].sum()
        st.metric("Total Gain (90 days)", f"${total_gain:,.2f}")
    with col3:
        avg_gain = portfolio_data['PORTFOLIO_GAIN'].mean()
        st.metric("Avg Daily Gain", f"${avg_gain:,.2f}")

# ML Predictions Section
st.markdown("---")
st.subheader("🔮 AI-Powered Spending Forecast")

try:
    predictions = load_data("""
        SELECT 
            prediction_date,
            category,
            predicted_amount,
            predicted_lower,
            predicted_upper
        FROM ML_SPENDING_PREDICTIONS
        ORDER BY prediction_date, category
    """)
    
    # Convert date column to datetime
    predictions['PREDICTION_DATE'] = pd.to_datetime(predictions['PREDICTION_DATE'])
    
    if len(predictions) > 0:
        # Total predicted spending
        total_next_30 = predictions.groupby('PREDICTION_DATE')['PREDICTED_AMOUNT'].sum().reset_index()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "Predicted Next 30-Day Spending",
                f"${total_next_30['PREDICTED_AMOUNT'].sum():,.0f}",
                help="AI forecast based on historical patterns"
            )
        
        with col2:
            avg_daily = total_next_30['PREDICTED_AMOUNT'].mean()
            st.metric(
                "Predicted Avg Daily Spending",
                f"${avg_daily:,.2f}"
            )
        
        # Forecast chart
        st.subheader("📊 Spending Forecast by Category")
        
        # Get top 5 categories by predicted spending
        top_categories = predictions.groupby('CATEGORY')['PREDICTED_AMOUNT'].sum().nlargest(5).index
        forecast_subset = predictions[predictions['CATEGORY'].isin(top_categories)]
        
        fig = go.Figure()
        
        for category in top_categories:
            cat_data = forecast_subset[forecast_subset['CATEGORY'] == category].sort_values('PREDICTION_DATE')
            
            # Add confidence interval (shaded area)
            fig.add_trace(go.Scatter(
                x=pd.concat([cat_data['PREDICTION_DATE'], cat_data['PREDICTION_DATE'][::-1]]),
                y=pd.concat([cat_data['PREDICTED_UPPER'], cat_data['PREDICTED_LOWER'][::-1]]),
                fill='toself',
                fillcolor='rgba(0,0,0,0.1)',
                line=dict(color='rgba(255,255,255,0)'),
                showlegend=False,
                name=f'{category} range',
                hoverinfo='skip'
            ))
            
            # Prediction line
            fig.add_trace(go.Scatter(
                x=cat_data['PREDICTION_DATE'],
                y=cat_data['PREDICTED_AMOUNT'],
                name=category,
                mode='lines+markers',
                line=dict(width=2)
            ))
        
        fig.update_layout(
            height=400,
            hovermode='x unified',
            xaxis_title='Date',
            yaxis_title='Predicted Daily Spending ($)',
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Predictions table
        with st.expander("📋 View Detailed Predictions"):
            summary_by_category = predictions.groupby('CATEGORY').agg({
                'PREDICTED_AMOUNT': 'sum',
                'PREDICTED_LOWER': 'sum',
                'PREDICTED_UPPER': 'sum'
            }).reset_index()
            summary_by_category.columns = ['Category', 'Predicted Total', 'Lower Bound', 'Upper Bound']
            summary_by_category = summary_by_category.round(2)
            st.dataframe(summary_by_category, use_container_width=True, hide_index=True)
    else:
        st.info("🤖 No predictions available. Run `python ml_models/save_predictions_to_snowflake.py` to generate forecasts.")
        
except Exception as e:
    st.error(f"Error loading predictions: {e}")





# Data table
st.markdown("---")
st.subheader("📋 Recent Daily Summary")
st.dataframe(
    daily_summary.head(30),
    use_container_width=True,
    hide_index=True
)