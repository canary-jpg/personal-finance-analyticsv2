import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

np.random.seed(42)
random.seed(42)

categories = {
    'Groceries': ['Whole Foods', 'Trader Joes', 'Safeway', 'Target', 'Costco'],
    'Dining': ['Chipotle', 'Starbucks', 'Local Cafe', 'Pizza Place', 'Thai Restaurant'],
    'Transportation': ['Uber', 'Lyft', 'Gas Station', 'Public Transit'],
    'Entertainment': ['Netflix', 'Spotify', 'Movie Theater', 'Gym Membership'],
    'Shopping': ['Amazon', 'Target', 'Clothing Store', 'Best Buy'],
    'Utilities': ['Electric Company', 'Internet Provider', 'Phone Bill'],
    'Healthcare': ['Pharmacy', 'Doctor Visit', 'Dental Office'],
    'Income': ['Paycheck', 'Freelance Payment']
}

end_date = datetime.now()
start_date = end_date - timedelta(days=180)
date_range = pd.date_range(start=start_date, end=end_date, freq='D')

transactions = []

# Generate recurring income
for month_offset in range(6):
    bill_date = start_date + timedelta(days=30 * month_offset)
    for week in [0, 2]:
        transactions.append({
            'date': bill_date + timedelta(days=week * 7),
            'description': 'Paycheck Direct Deposit',
            'amount': 3500.00,
            'category': 'Income',
            'account_type': 'Checking'
        })

# Generate random transactions
for date in date_range:
    if random.random() < 0.3:
        continue
    
    num_transactions = random.randint(1, 4)
    for _ in range(num_transactions):
        category = random.choice([cat for cat in categories.keys() if cat != 'Income'])
        merchant = random.choice(categories[category])
        
        if category == 'Groceries':
            amount = -random.uniform(20, 150)
        elif category == 'Dining':
            amount = -random.uniform(8, 65)
        else:
            amount = -random.uniform(10, 100)
        
        transactions.append({
            'date': date,
            'description': merchant,
            'amount': round(amount, 2),
            'category': category,
            'account_type': random.choice(['Checking', 'Credit Card'])
        })

df = pd.DataFrame(transactions)
df = df.sort_values('date').reset_index(drop=True)
df.insert(0, 'transaction_id', range(1, len(df) + 1))
df['date'] = df['date'].dt.strftime('%Y-%m-%d')

df.to_csv('data/transactions.csv', index=False)
print(f"Generated {len(df)} transactions")