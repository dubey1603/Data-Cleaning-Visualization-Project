"""
clean_and_visualize.py
------------------------
Data Cleaning & Visualization Project

Steps:
1. Load raw dataset
2. Clean: handle missing values, duplicates, outliers, inconsistent formatting
3. Save cleaned dataset
4. Generate visualizations (dashboard-style PNGs) summarizing key insights
5. Print a summary report (used to populate the README)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os

sns.set_theme(style="whitegrid")
plt.rcParams["figure.dpi"] = 120

BASE = "/home/claude/data-cleaning-viz-project"
RAW_PATH = f"{BASE}/data/raw_sales_data.csv"
CLEAN_PATH = f"{BASE}/output/cleaned_sales_data.csv"
VISUALS_DIR = f"{BASE}/visuals"
REPORT_PATH = f"{BASE}/output/summary_report.json"

os.makedirs(VISUALS_DIR, exist_ok=True)
os.makedirs(f"{BASE}/output", exist_ok=True)

report = {}

# ---------------------------------------------------------
# 1. LOAD
# ---------------------------------------------------------
df = pd.read_csv(RAW_PATH)
report["raw_rows"] = len(df)
report["raw_cols"] = df.shape[1]
report["missing_before"] = int(df.isna().sum().sum())
report["duplicates_before"] = int(df.duplicated().sum())

# ---------------------------------------------------------
# 2. CLEAN
# ---------------------------------------------------------

# 2a. Standardize text columns (strip whitespace, title case)
for col in ["Region", "Category", "PaymentMethod"]:
    df[col] = df[col].astype(str).str.strip().str.title()
    df.loc[df[col].isin(["Nan", "None", ""]), col] = np.nan

# 2b. Parse mixed date formats
def parse_date(d):
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m-%d-%Y", "%d-%b-%Y"):
        try:
            return pd.to_datetime(d, format=fmt)
        except (ValueError, TypeError):
            continue
    return pd.NaT

df["OrderDate"] = df["OrderDate"].apply(parse_date)

# 2c. Remove exact duplicate rows
df = df.drop_duplicates()

# 2d. Handle outliers using IQR capping (winsorization) for Quantity & UnitPrice
def cap_outliers_iqr(series, factor=1.5):
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    lower, upper = q1 - factor * iqr, q3 + factor * iqr
    return series.clip(lower=max(lower, 0), upper=upper), lower, upper

outlier_summary = {}
for col in ["Quantity", "UnitPrice"]:
    before_max = df[col].max()
    df[col], low, high = cap_outliers_iqr(df[col])
    outlier_summary[col] = {
        "capped_upper_bound": round(float(high), 2),
        "original_max": round(float(before_max), 2),
        "new_max": round(float(df[col].max()), 2),
    }
report["outlier_summary"] = outlier_summary

# 2e. Handle missing values
# Numeric: fill with median; Categorical: fill with mode; Dates: drop rows with missing date
num_cols = ["Quantity", "UnitPrice"]
cat_cols = ["Region", "PaymentMethod", "CustomerID"]

for col in num_cols:
    median_val = df[col].median()
    df[col] = df[col].fillna(median_val)

for col in cat_cols:
    mode_val = df[col].mode(dropna=True)[0]
    df[col] = df[col].fillna(mode_val)

df = df.dropna(subset=["OrderDate"])

# 2f. Derived column
df["TotalAmount"] = (df["Quantity"] * df["UnitPrice"]).round(2)
df["Month"] = df["OrderDate"].dt.to_period("M").astype(str)

report["missing_after"] = int(df.isna().sum().sum())
report["duplicates_after"] = int(df.duplicated().sum())
report["clean_rows"] = len(df)
report["clean_cols"] = df.shape[1]

# Save cleaned dataset
df.to_csv(CLEAN_PATH, index=False)

# ---------------------------------------------------------
# 3. VISUALIZATIONS
# ---------------------------------------------------------

# Chart 1: Missing values before/after (bar chart)
fig, ax = plt.subplots(figsize=(6, 4))
bars = ax.bar(
    ["Missing Values\n(Before)", "Missing Values\n(After)", "Duplicates\n(Before)", "Duplicates\n(After)"],
    [report["missing_before"], report["missing_after"], report["duplicates_before"], report["duplicates_after"]],
    color=["#e76f51", "#2a9d8f", "#e76f51", "#2a9d8f"],
)
ax.bar_label(bars)
ax.set_title("Data Quality: Before vs. After Cleaning")
ax.set_ylabel("Count")
plt.tight_layout()
plt.savefig(f"{VISUALS_DIR}/01_data_quality_before_after.png")
plt.close()

# Chart 2: Revenue by Category
fig, ax = plt.subplots(figsize=(7, 4.5))
cat_rev = df.groupby("Category")["TotalAmount"].sum().sort_values(ascending=False)
sns.barplot(x=cat_rev.values, y=cat_rev.index, ax=ax, palette="crest")
ax.set_title("Total Revenue by Category")
ax.set_xlabel("Total Revenue ($)")
ax.set_ylabel("Category")
plt.tight_layout()
plt.savefig(f"{VISUALS_DIR}/02_revenue_by_category.png")
plt.close()

# Chart 3: Monthly Revenue Trend
fig, ax = plt.subplots(figsize=(8, 4.5))
monthly = df.groupby("Month")["TotalAmount"].sum().sort_index()
ax.plot(monthly.index, monthly.values, marker="o", color="#264653", linewidth=2)
ax.set_title("Monthly Revenue Trend")
ax.set_xlabel("Month")
ax.set_ylabel("Revenue ($)")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(f"{VISUALS_DIR}/03_monthly_revenue_trend.png")
plt.close()

# Chart 4: Revenue Share by Region (pie)
fig, ax = plt.subplots(figsize=(6, 6))
region_rev = df.groupby("Region")["TotalAmount"].sum()
ax.pie(region_rev.values, labels=region_rev.index, autopct="%1.1f%%",
       colors=sns.color_palette("Set2"), startangle=90)
ax.set_title("Revenue Share by Region")
plt.tight_layout()
plt.savefig(f"{VISUALS_DIR}/04_revenue_share_by_region.png")
plt.close()

# Chart 5: Payment Method Distribution
fig, ax = plt.subplots(figsize=(7, 4.5))
pm_counts = df["PaymentMethod"].value_counts()
sns.barplot(x=pm_counts.index, y=pm_counts.values, ax=ax, palette="flare")
ax.set_title("Order Count by Payment Method")
ax.set_ylabel("Number of Orders")
ax.set_xlabel("Payment Method")
plt.tight_layout()
plt.savefig(f"{VISUALS_DIR}/05_payment_method_distribution.png")
plt.close()

# Chart 6: Quantity distribution before/after outlier capping (boxplot)
raw_df = pd.read_csv(RAW_PATH)
fig, axes = plt.subplots(1, 2, figsize=(9, 4.5))
sns.boxplot(y=raw_df["Quantity"].dropna(), ax=axes[0], color="#e76f51")
axes[0].set_title("Quantity (Raw, with Outliers)")
sns.boxplot(y=df["Quantity"], ax=axes[1], color="#2a9d8f")
axes[1].set_title("Quantity (Cleaned)")
plt.tight_layout()
plt.savefig(f"{VISUALS_DIR}/06_quantity_outliers_before_after.png")
plt.close()

# ---------------------------------------------------------
# 4. TOP-LEVEL SUMMARY TABLES (for README)
# ---------------------------------------------------------
report["category_revenue"] = cat_rev.round(2).to_dict()
report["region_revenue"] = region_rev.round(2).to_dict()
report["payment_counts"] = pm_counts.to_dict()
report["top_customers"] = (
    df.groupby("CustomerID")["TotalAmount"].sum().sort_values(ascending=False).head(5).round(2).to_dict()
)
report["overall_total_revenue"] = round(float(df["TotalAmount"].sum()), 2)
report["avg_order_value"] = round(float(df["TotalAmount"].mean()), 2)

with open(REPORT_PATH, "w") as f:
    json.dump(report, f, indent=2)

print(json.dumps(report, indent=2))
