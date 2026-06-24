import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text

# ─────────────────────────────────────────────
# PATH CONFLICT SOLVER & CONFIG
# ─────────────────────────────────────────────
BASE_DIR = r"d:\BlueStock.in\Day 2 - Cleaned data + SQLite DB loaded"
RAW_DIR = r"d:\BlueStock.in\DAY 1 — Project Setup + Data Ingestion\data\raw"
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
DB_PATH = os.path.join(BASE_DIR, "bluestock_mf.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")

os.makedirs(PROCESSED_DIR, exist_ok=True)

print("Starting Data Ingestion & Cleaning Process...")

# ─────────────────────────────────────────────
# 1. READ ALL DATASETS
# ─────────────────────────────────────────────
files = {
    "01_fund_master": "01_fund_master.csv",
    "02_nav_history": "02_nav_history.csv",
    "03_aum_by_fund_house": "03_aum_by_fund_house.csv",
    "04_monthly_sip_inflows": "04_monthly_sip_inflows.csv",
    "05_category_inflows": "05_category_inflows.csv",
    "06_industry_folio_count": "06_industry_folio_count.csv",
    "07_scheme_performance": "07_scheme_performance.csv",
    "08_investor_transactions": "08_investor_transactions.csv",
    "09_portfolio_holdings": "09_portfolio_holdings.csv",
    "10_benchmark_indices": "10_benchmark_indices.csv",
}

dfs = {}
for key, fname in files.items():
    raw_path = os.path.join(RAW_DIR, fname)
    if os.path.exists(raw_path):
        dfs[key] = pd.read_csv(raw_path, low_memory=False)
        print(f"Loaded {fname} with {len(dfs[key])} rows.")
    else:
        raise FileNotFoundError(f"Raw CSV file not found: {raw_path}")

# ─────────────────────────────────────────────
# 2. DATA CLEANING
# ─────────────────────────────────────────────

# Clean 01_fund_master
print("Cleaning 01_fund_master...")
df_fund = dfs["01_fund_master"].copy()
df_fund["launch_date"] = pd.to_datetime(df_fund["launch_date"]).dt.strftime("%Y-%m-%d")
df_fund["expense_ratio_pct"] = pd.to_numeric(df_fund["expense_ratio_pct"], errors="coerce")
df_fund["exit_load_pct"] = pd.to_numeric(df_fund["exit_load_pct"], errors="coerce")
dfs["01_fund_master"] = df_fund

# Clean 02_nav_history
# parse dates to datetime, sort by amfi_code + date, forward-fill missing NAV for holidays/weekends, remove duplicates, validate NAV > 0.
print("Cleaning 02_nav_history...")
df_nav = dfs["02_nav_history"].copy()
df_nav["date"] = pd.to_datetime(df_nav["date"])
df_nav = df_nav.drop_duplicates(subset=["amfi_code", "date"])
df_nav = df_nav[df_nav["nav"] > 0]
df_nav = df_nav.sort_values(by=["amfi_code", "date"])

# Forward-fill weekends/holidays per amfi_code
nav_cleaned_list = []
for amfi, group in df_nav.groupby("amfi_code"):
    group = group.set_index("date")
    full_range = pd.date_range(start=group.index.min(), end=group.index.max(), freq="D")
    group = group.reindex(full_range)
    group["amfi_code"] = amfi
    group["nav"] = group["nav"].ffill()
    group = group.reset_index().rename(columns={"index": "date"})
    nav_cleaned_list.append(group)

df_nav_clean = pd.concat(nav_cleaned_list, ignore_index=True)
df_nav_clean["date"] = df_nav_clean["date"].dt.strftime("%Y-%m-%d")
df_nav_clean = df_nav_clean.sort_values(by=["amfi_code", "date"]).reset_index(drop=True)
dfs["02_nav_history"] = df_nav_clean
print(f"02_nav_history cleaned and forward-filled. Expanded from {len(dfs['02_nav_history'])} to {len(df_nav_clean)} rows.")

# Clean 03_aum_by_fund_house
print("Cleaning 03_aum_by_fund_house...")
df_aum = dfs["03_aum_by_fund_house"].copy()
df_aum["date"] = pd.to_datetime(df_aum["date"]).dt.strftime("%Y-%m-%d")
dfs["03_aum_by_fund_house"] = df_aum

# Clean 04_monthly_sip_inflows
print("Cleaning 04_monthly_sip_inflows...")
df_sip = dfs["04_monthly_sip_inflows"].copy()
df_sip["month"] = df_sip["month"].astype(str).str.strip()
df_sip["sip_inflow_crore"] = pd.to_numeric(df_sip["sip_inflow_crore"], errors="coerce")
df_sip["active_sip_accounts_crore"] = pd.to_numeric(df_sip["active_sip_accounts_crore"], errors="coerce")
df_sip["yoy_growth_pct"] = pd.to_numeric(df_sip["yoy_growth_pct"], errors="coerce")
dfs["04_monthly_sip_inflows"] = df_sip

# Clean 05_category_inflows
print("Cleaning 05_category_inflows...")
df_cat = dfs["05_category_inflows"].copy()
df_cat["month"] = df_cat["month"].astype(str).str.strip()
df_cat["net_inflow_crore"] = pd.to_numeric(df_cat["net_inflow_crore"], errors="coerce")
dfs["05_category_inflows"] = df_cat

# Clean 06_industry_folio_count
print("Cleaning 06_industry_folio_count...")
df_folio = dfs["06_industry_folio_count"].copy()
df_folio["month"] = df_folio["month"].astype(str).str.strip()
dfs["06_industry_folio_count"] = df_folio

# Clean 07_scheme_performance
# validate all return values are numeric, flag anomalies, check expense_ratio range (0.1% – 2.5%).
print("Cleaning 07_scheme_performance...")
df_perf = dfs["07_scheme_performance"].copy()
return_cols = ["return_1yr_pct", "return_3yr_pct", "return_5yr_pct", "benchmark_3yr_pct"]
for col in return_cols:
    df_perf[col] = pd.to_numeric(df_perf[col], errors="coerce")

# Validate expense ratio range
if "expense_ratio_pct" in df_perf.columns:
    df_perf["expense_ratio_pct"] = pd.to_numeric(df_perf["expense_ratio_pct"], errors="coerce")
    anomalous_expense = df_perf[(df_perf["expense_ratio_pct"] < 0.1) | (df_perf["expense_ratio_pct"] > 2.5)]
    if not anomalous_expense.empty:
        print(f"[WARNING] Anomalous expense ratios detected:\n{anomalous_expense[['scheme_name', 'expense_ratio_pct']]}")
else:
    print("[ERROR] expense_ratio_pct column is missing in 07_scheme_performance!")

# Check for ratings outside 1-5 or other return anomalies
rating_col = "morningstar_rating"
if rating_col in df_perf.columns:
    df_perf[rating_col] = pd.to_numeric(df_perf[rating_col], errors="coerce").astype("Int64")
    invalid_ratings = df_perf[(df_perf[rating_col] < 1) | (df_perf[rating_col] > 5)]
    if not invalid_ratings.empty:
        print(f"[WARNING] Invalid morningstar ratings detected:\n{invalid_ratings[['scheme_name', rating_col]]}")

dfs["07_scheme_performance"] = df_perf

# Clean 08_investor_transactions
# standardise transaction_type values (SIP/Lumpsum/Redemption), validate amount > 0, fix date formats, check KYC status enum values.
print("Cleaning 08_investor_transactions...")
df_tx = dfs["08_investor_transactions"].copy()
df_tx["transaction_date"] = pd.to_datetime(df_tx["transaction_date"])

# Standardize transaction types
type_map = {
    "sip": "SIP",
    "lumpsum": "Lumpsum",
    "redemption": "Redemption"
}
df_tx["transaction_type"] = df_tx["transaction_type"].astype(str).str.strip().str.lower().map(type_map).fillna(df_tx["transaction_type"])

# Validate amount > 0
df_tx = df_tx[df_tx["amount_inr"] > 0]

# Standardize and validate KYC status
df_tx["kyc_status"] = df_tx["kyc_status"].astype(str).str.strip().str.title()
invalid_kyc = df_tx[~df_tx["kyc_status"].isin(["Verified", "Pending"])]
if not invalid_kyc.empty:
    print(f"[WARNING] Invalid KYC status enum values found: {invalid_kyc['kyc_status'].unique()}. Standardizing to 'Pending'.")
    df_tx.loc[~df_tx["kyc_status"].isin(["Verified", "Pending"]), "kyc_status"] = "Pending"

# Standardize date string
df_tx["transaction_date"] = df_tx["transaction_date"].dt.strftime("%Y-%m-%d")
df_tx = df_tx.sort_values(by=["transaction_date", "investor_id"]).reset_index(drop=True)
dfs["08_investor_transactions"] = df_tx

# Clean 09_portfolio_holdings
print("Cleaning 09_portfolio_holdings...")
df_port = dfs["09_portfolio_holdings"].copy()
df_port["portfolio_date"] = pd.to_datetime(df_port["portfolio_date"]).dt.strftime("%Y-%m-%d")
dfs["09_portfolio_holdings"] = df_port

# Clean 10_benchmark_indices
print("Cleaning 10_benchmark_indices...")
df_bench = dfs["10_benchmark_indices"].copy()
df_bench["date"] = pd.to_datetime(df_bench["date"]).dt.strftime("%Y-%m-%d")
dfs["10_benchmark_indices"] = df_bench

# ─────────────────────────────────────────────
# 3. SAVE CLEANED CSVs TO PROCESS DIRECTORY
# ─────────────────────────────────────────────
print("Saving cleaned CSVs to processed directory...")
for key, fname in files.items():
    processed_path = os.path.join(PROCESSED_DIR, fname)
    dfs[key].to_csv(processed_path, index=False)
    print(f"Saved {fname} | Rows: {len(dfs[key])}")

# ─────────────────────────────────────────────
# 4. GENERATE DATE DIMENSION
# ─────────────────────────────────────────────
print("Generating dim_date dimension...")
# Let's cover dates from 2022-01-01 to 2026-12-31 to fully envelope the datasets
start_date = "2022-01-01"
end_date = "2026-12-31"
date_range = pd.date_range(start=start_date, end=end_date)
df_date = pd.DataFrame({
    "date": date_range.strftime("%Y-%m-%d"),
    "year": date_range.year,
    "month": date_range.month,
    "day": date_range.day,
    "quarter": date_range.quarter,
    "day_of_week": date_range.dayofweek, # 0 = Monday, 6 = Sunday
    "day_name": date_range.day_name(),
    "month_name": date_range.month_name(),
    "is_weekend": date_range.dayofweek.isin([5, 6]).astype(int)
})
df_date.to_csv(os.path.join(PROCESSED_DIR, "dim_date.csv"), index=False)
print(f"dim_date generated with {len(df_date)} rows.")

# ─────────────────────────────────────────────
# 5. DATABASE CREATION AND DDL EXECUTION
# ─────────────────────────────────────────────
print(f"Initializing SQLite database at: {DB_PATH}...")
engine = create_engine(f"sqlite:///{DB_PATH}")

# Read schema.sql
if os.path.exists(SCHEMA_PATH):
    print(f"Reading DDL from: {SCHEMA_PATH}...")
    with open(SCHEMA_PATH, "r") as f:
        ddl = f.read()
    
    # SQLite allows executing multiple statements separated by semicolon using executescript
    raw_conn = engine.raw_connection()
    try:
        cursor = raw_conn.cursor()
        cursor.executescript(ddl)
        raw_conn.commit()
        print("Schema DDL executed successfully.")
    except Exception as e:
        raw_conn.rollback()
        print(f"[ERROR] Error executing schema DDL: {e}")
        raise e
    finally:
        raw_conn.close()
else:
    raise FileNotFoundError(f"Schema SQL file not found at: {SCHEMA_PATH}")

# ─────────────────────────────────────────────
# 6. INGEST DATA INTO SQLITE
# ─────────────────────────────────────────────
# Table mappings
table_mappings = {
    "01_fund_master": "dim_fund",
    "02_nav_history": "fact_nav",
    "03_aum_by_fund_house": "fact_aum",
    "04_monthly_sip_inflows": "fact_monthly_sip_inflows",
    "05_category_inflows": "fact_category_inflows",
    "06_industry_folio_count": "fact_industry_folio_count",
    "07_scheme_performance": "fact_performance",
    "08_investor_transactions": "fact_transactions",
    "09_portfolio_holdings": "fact_portfolio_holdings",
    "10_benchmark_indices": "fact_benchmark_indices",
}

# First, load dim_date
print("Loading table dim_date...")
df_date.to_sql("dim_date", engine, if_exists="append", index=False)
print("Loaded dim_date.")

# Load other tables
for key, table_name in table_mappings.items():
    print(f"Loading table {table_name} from {key}...")
    df_to_load = dfs[key].copy()
    df_to_load.to_sql(table_name, engine, if_exists="append", index=False)
    print(f"Loaded {table_name}.")

# ─────────────────────────────────────────────
# 7. ROW COUNT VERIFICATION
# ─────────────────────────────────────────────
print("\n--- Row Count Verification ---")
verification_failed = False
with engine.connect() as conn:
    # Verify dim_date
    db_count_date = conn.execute(text("SELECT COUNT(*) FROM dim_date")).scalar()
    csv_count_date = len(df_date)
    print(f"Table: dim_date | CSV: {csv_count_date:,} rows | DB: {db_count_date:,} rows | Match: {csv_count_date == db_count_date}")
    if csv_count_date != db_count_date:
        verification_failed = True

    # Verify other tables
    for key, table_name in table_mappings.items():
        db_count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
        csv_count = len(dfs[key])
        match = (csv_count == db_count)
        print(f"Table: {table_name} | CSV: {csv_count:,} rows | DB: {db_count:,} rows | Match: {match}")
        if not match:
            verification_failed = True

if verification_failed:
    print("\n[ERROR] Row count verification failed! Some counts do not match.")
else:
    print("\n[SUCCESS] Row count verification passed! All CSV counts match database table counts.")

print("Process completed successfully.")
