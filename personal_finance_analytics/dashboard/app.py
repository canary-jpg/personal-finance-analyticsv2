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

# Data table
st.markdown("---")
st.subheader("📋 Recent Daily Summary")
st.dataframe(
    daily_summary.head(30),
    use_container_width=True,
    hide_index=True
)