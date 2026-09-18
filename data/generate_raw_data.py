"""
generate_raw_data.py
---------------------
Generates a synthetic, intentionally messy "Retail Sales" dataset
to be used as the raw input for the Data Cleaning & Visualization Project.

Injected issues:
- Missing values (NaN) in several columns
- Duplicate rows
- Outliers in Quantity and UnitPrice
- Inconsistent text casing / whitespace in categorical columns
- Mixed date formats
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

np.random.seed(42)
random.seed(42)

N = 500

regions = ["North", "South", "East", "West"]
categories = ["Electronics", "Clothing", "Home & Kitchen", "Sports", "Books"]
payment_methods = ["Credit Card", "Debit Card", "UPI", "Cash", "Wallet"]

start_date = datetime(2025, 1, 1)

rows = []
for i in range(N):
    order_id = f"ORD{1000 + i}"
    customer_id = f"CUST{np.random.randint(1, 150)}"
    region = random.choice(regions)
    category = random.choice(categories)
    payment = random.choice(payment_methods)

    quantity = np.random.randint(1, 10)
    unit_price = round(np.random.uniform(5, 500), 2)

    order_date = start_date + timedelta(days=np.random.randint(0, 270))

    rows.append({
        "OrderID": order_id,
        "CustomerID": customer_id,
        "Region": region,
        "Category": category,
        "PaymentMethod": payment,
        "Quantity": quantity,
        "UnitPrice": unit_price,
        "OrderDate": order_date.strftime("%Y-%m-%d"),
    })

df = pd.DataFrame(rows)

# --- Inject messiness ---

# 1. Missing values
for col in ["Quantity", "UnitPrice", "Region", "PaymentMethod", "CustomerID"]:
    missing_idx = df.sample(frac=0.04, random_state=np.random.randint(0, 1000)).index
    df.loc[missing_idx, col] = np.nan

# 2. Outliers
outlier_idx = df.sample(n=8, random_state=1).index
df.loc[outlier_idx, "Quantity"] = np.random.choice([120, 250, 300, 500], size=len(outlier_idx))
outlier_idx2 = df.sample(n=6, random_state=2).index
df.loc[outlier_idx2, "UnitPrice"] = np.random.choice([9999, 15000, 20000], size=len(outlier_idx2))

# 3. Inconsistent casing / whitespace
df["Region"] = df["Region"].apply(
    lambda x: x if pd.isna(x) else random.choice([x.upper(), x.lower(), f" {x} ", x])
)
df["Category"] = df["Category"].apply(
    lambda x: random.choice([x.upper(), x.lower(), f" {x}", x])
)

# 4. Mixed date formats
def mixed_date(d):
    dt = datetime.strptime(d, "%Y-%m-%d")
    fmt = random.choice(["%Y-%m-%d", "%d/%m/%Y", "%m-%d-%Y", "%d-%b-%Y"])
    return dt.strftime(fmt)

df["OrderDate"] = df["OrderDate"].apply(mixed_date)

# 5. Duplicate rows (append ~5% duplicates)
dupes = df.sample(frac=0.05, random_state=3)
df = pd.concat([df, dupes], ignore_index=True)

# Shuffle
df = df.sample(frac=1, random_state=7).reset_index(drop=True)

df.to_csv("/home/claude/data-cleaning-viz-project/data/raw_sales_data.csv", index=False)
print(f"Raw dataset generated: {df.shape[0]} rows, {df.shape[1]} columns")
