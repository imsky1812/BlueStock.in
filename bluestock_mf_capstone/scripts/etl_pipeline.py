"""
etl_pipeline.py
===============
BlueStock Fintech Internship -- Capstone Project I: Mutual Fund Analytics
Unified ETL Pipeline (D1)

Runs end-to-end:
  1. Validates raw CSV files exist
  2. Loads all 10 datasets
  3. Cleans each dataset (dates, types, ffill for NAV, dedup)
  4. Loads cleaned data into SQLite (bluestock_mf.db) via star schema
  5. Writes data quality report

Usage:
  python scripts/etl_pipeline.py

Requirements: pandas, numpy, sqlalchemy
"""

from __future__ import annotations

import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG  (all paths relative to project root -- no hard-coded absolute paths)
# ─────────────────────────────────────────────────────────────────────────────
ROOT_DIR       = Path(__file__).resolve().parent.parent
RAW_DIR        = ROOT_DIR / "data" / "raw"
PROCESSED_DIR  = ROOT_DIR / "data" / "processed"
DB_DIR         = ROOT_DIR / "data" / "db"
REPORTS_DIR    = ROOT_DIR / "reports"
SCHEMA_PATH    = ROOT_DIR / "sql" / "schema.sql"
DB_PATH        = DB_DIR / "bluestock_mf.db"

# Ensure output directories exist
for d in (PROCESSED_DIR, DB_DIR, REPORTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(REPORTS_DIR / "etl_pipeline.log", mode="w", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

SEP = "=" * 70

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 -- LOAD RAW CSVs
# ─────────────────────────────────────────────────────────────────────────────

RAW_FILES = {
    "fund_master":         "01_fund_master.csv",
    "nav_history":         "02_nav_history.csv",
    "aum_by_fund_house":   "03_aum_by_fund_house.csv",
    "monthly_sip_inflows": "04_monthly_sip_inflows.csv",
    "category_inflows":    "05_category_inflows.csv",
    "industry_folio_count":"06_industry_folio_count.csv",
    "scheme_performance":  "07_scheme_performance.csv",
    "investor_transactions":"08_investor_transactions.csv",
    "portfolio_holdings":  "09_portfolio_holdings.csv",
    "benchmark_indices":   "10_benchmark_indices.csv",
}


def load_raw_csvs() -> dict[str, pd.DataFrame]:
    """Load all 10 raw CSVs from data/raw/.  Raises if any file is missing."""
    log.info(SEP)
    log.info("STEP 1 -- Loading raw CSV files from: %s", RAW_DIR)
    log.info(SEP)

    dfs: dict[str, pd.DataFrame] = {}
    missing: list[str] = []

    for key, fname in RAW_FILES.items():
        path = RAW_DIR / fname
        if not path.exists():
            missing.append(str(path))
            log.warning("  [MISSING] %s", path)
            continue
        try:
            df = pd.read_csv(path, low_memory=False)
            dfs[key] = df
            log.info("  Loaded %-30s  %7d rows x %d cols", fname, df.shape[0], df.shape[1])
        except Exception as exc:
            log.error("  [ERROR] Could not read %s: %s", path, exc)
            raise

    if missing:
        raise FileNotFoundError(
            f"ETL aborted -- {len(missing)} CSV file(s) not found:\n" + "\n".join(missing)
        )

    log.info("  [OK] All %d CSV files loaded successfully.", len(dfs))
    return dfs


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 -- DATA CLEANING
# ─────────────────────────────────────────────────────────────────────────────

def clean_fund_master(df: pd.DataFrame) -> pd.DataFrame:
    log.info("  Cleaning fund_master …")
    df = df.copy()
    df["launch_date"]        = pd.to_datetime(df["launch_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["expense_ratio_pct"]  = pd.to_numeric(df["expense_ratio_pct"],  errors="coerce")
    df["exit_load_pct"]      = pd.to_numeric(df["exit_load_pct"],      errors="coerce")
    df["min_sip_amount"]     = pd.to_numeric(df["min_sip_amount"],     errors="coerce")
    df["min_lumpsum_amount"] = pd.to_numeric(df["min_lumpsum_amount"], errors="coerce")
    df = df.drop_duplicates(subset=["amfi_code"])
    return df


def clean_nav_history(df: pd.DataFrame, all_amfi_codes: pd.Series) -> pd.DataFrame:
    """
    Clean NAV history:
      - Parse dates
      - Remove NAV ≤ 0
      - Reindex to full trading-day range and ffill() for weekends/holidays
      - Remove duplicates
    """
    log.info("  Cleaning nav_history (ffill for weekends/holidays) …")
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
    df = df[df["nav"] > 0]
    df = df.sort_values(["amfi_code", "date"])
    df = df.drop_duplicates(subset=["amfi_code", "date"])

    # Build a full date range (Mon–Fri only) spanning the data
    min_date = df["date"].min()
    max_date = df["date"].max()
    full_range = pd.date_range(start=min_date, end=max_date, freq="B")  # business days

    cleaned_parts: list[pd.DataFrame] = []
    for amfi_code, grp in df.groupby("amfi_code"):
        grp = grp.set_index("date")[["nav"]]
        grp = grp.reindex(full_range)
        grp["nav"] = grp["nav"].ffill()          # fill weekends/holidays
        grp["nav"] = grp["nav"].bfill()          # backfill any leading NaNs
        grp = grp.dropna()
        grp["amfi_code"] = amfi_code
        grp = grp.reset_index().rename(columns={"index": "date"})
        grp["date"] = grp["date"].dt.strftime("%Y-%m-%d")
        cleaned_parts.append(grp)

    result = pd.concat(cleaned_parts, ignore_index=True)
    log.info("    nav_history: %d rows after cleaning.", len(result))
    return result


def clean_aum(df: pd.DataFrame) -> pd.DataFrame:
    log.info("  Cleaning aum_by_fund_house …")
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["aum_lakh_crore"] = pd.to_numeric(df["aum_lakh_crore"], errors="coerce")
    df["aum_crore"]      = pd.to_numeric(df["aum_crore"],      errors="coerce")
    df["num_schemes"]    = pd.to_numeric(df["num_schemes"],    errors="coerce").fillna(0).astype(int)
    df = df.drop_duplicates(subset=["date", "fund_house"])
    return df


def clean_monthly_sip(df: pd.DataFrame) -> pd.DataFrame:
    log.info("  Cleaning monthly_sip_inflows …")
    df = df.copy()
    num_cols = ["sip_inflow_crore", "active_sip_accounts_crore", "new_sip_accounts_lakh", "sip_aum_lakh_crore", "yoy_growth_pct"]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.drop_duplicates(subset=["month"])
    return df


def clean_category_inflows(df: pd.DataFrame) -> pd.DataFrame:
    log.info("  Cleaning category_inflows …")
    df = df.copy()
    df["net_inflow_crore"] = pd.to_numeric(df["net_inflow_crore"], errors="coerce")
    df = df.drop_duplicates(subset=["month", "category"])
    return df


def clean_folio_count(df: pd.DataFrame) -> pd.DataFrame:
    log.info("  Cleaning industry_folio_count …")
    df = df.copy()
    num_cols = ["total_folios_crore", "equity_folios_crore", "debt_folios_crore", "hybrid_folios_crore", "others_folios_crore"]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.drop_duplicates(subset=["month"])
    return df


def clean_scheme_performance(df: pd.DataFrame) -> pd.DataFrame:
    log.info("  Cleaning scheme_performance …")
    df = df.copy()
    num_cols = ["return_1yr_pct", "return_3yr_pct", "return_5yr_pct",
                "benchmark_3yr_pct", "alpha", "beta", "sharpe_ratio",
                "sortino_ratio", "std_dev_ann_pct", "max_drawdown_pct",
                "aum_crore", "expense_ratio_pct", "morningstar_rating"]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.drop_duplicates(subset=["amfi_code"])
    return df


def clean_investor_transactions(df: pd.DataFrame) -> pd.DataFrame:
    log.info("  Cleaning investor_transactions …")
    df = df.copy()
    df["transaction_date"]   = pd.to_datetime(df["transaction_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["amount_inr"]         = pd.to_numeric(df["amount_inr"],         errors="coerce")
    df["annual_income_lakh"] = pd.to_numeric(df["annual_income_lakh"], errors="coerce")
    df = df.dropna(subset=["transaction_date", "amount_inr"])
    df = df[df["amount_inr"] > 0]
    df = df.drop_duplicates()
    return df


def clean_portfolio_holdings(df: pd.DataFrame) -> pd.DataFrame:
    log.info("  Cleaning portfolio_holdings …")
    df = df.copy()
    df["weight_pct"]       = pd.to_numeric(df["weight_pct"],       errors="coerce")
    df["market_value_cr"]  = pd.to_numeric(df["market_value_cr"],  errors="coerce")
    df["current_price_inr"]= pd.to_numeric(df["current_price_inr"],errors="coerce")
    df["portfolio_date"]   = pd.to_datetime(df["portfolio_date"],   errors="coerce").dt.strftime("%Y-%m-%d")
    df = df.drop_duplicates(subset=["amfi_code", "stock_symbol", "portfolio_date"])
    return df


def clean_benchmark_indices(df: pd.DataFrame) -> pd.DataFrame:
    log.info("  Cleaning benchmark_indices …")
    df = df.copy()
    df["date"]        = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["close_value"] = pd.to_numeric(df["close_value"], errors="coerce")
    df = df.dropna(subset=["date", "close_value"])
    df = df.drop_duplicates(subset=["date", "index_name"])
    return df


def clean_all(dfs: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    log.info(SEP)
    log.info("STEP 2 -- Cleaning all datasets")
    log.info(SEP)

    amfi_codes = dfs["fund_master"]["amfi_code"]
    cleaned = {
        "fund_master":          clean_fund_master(dfs["fund_master"]),
        "nav_history":          clean_nav_history(dfs["nav_history"], amfi_codes),
        "aum_by_fund_house":    clean_aum(dfs["aum_by_fund_house"]),
        "monthly_sip_inflows":  clean_monthly_sip(dfs["monthly_sip_inflows"]),
        "category_inflows":     clean_category_inflows(dfs["category_inflows"]),
        "industry_folio_count": clean_folio_count(dfs["industry_folio_count"]),
        "scheme_performance":   clean_scheme_performance(dfs["scheme_performance"]),
        "investor_transactions":clean_investor_transactions(dfs["investor_transactions"]),
        "portfolio_holdings":   clean_portfolio_holdings(dfs["portfolio_holdings"]),
        "benchmark_indices":    clean_benchmark_indices(dfs["benchmark_indices"]),
    }

    # Save cleaned CSVs
    for key, df in cleaned.items():
        out_path = PROCESSED_DIR / f"{key}_cleaned.csv"
        df.to_csv(out_path, index=False)

    log.info("  [OK] Cleaned CSVs saved to: %s", PROCESSED_DIR)
    return cleaned


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 -- BUILD DIM_DATE
# ─────────────────────────────────────────────────────────────────────────────

def build_dim_date(dfs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Derive all unique dates across fact tables to populate dim_date."""
    log.info("  Building dim_date …")
    all_dates: set[str] = set()
    for key in ["nav_history", "aum_by_fund_house", "investor_transactions", "benchmark_indices", "portfolio_holdings"]:
        date_col = "date" if key != "investor_transactions" else "transaction_date"
        if key == "portfolio_holdings":
            date_col = "portfolio_date"
        if date_col in dfs[key].columns:
            all_dates.update(dfs[key][date_col].dropna().unique())

    dates_dt = pd.to_datetime(sorted(all_dates))
    dim_date = pd.DataFrame({"date": dates_dt.strftime("%Y-%m-%d")})
    dim_date["year"]        = dates_dt.year
    dim_date["month"]       = dates_dt.month
    dim_date["day"]         = dates_dt.day
    dim_date["quarter"]     = dates_dt.quarter
    dim_date["day_of_week"] = dates_dt.dayofweek
    dim_date["day_name"]    = dates_dt.day_name()
    dim_date["month_name"]  = dates_dt.month_name()
    dim_date["is_weekend"]  = (dates_dt.dayofweek >= 5).astype(int)
    return dim_date


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 -- LOAD INTO SQLITE
# ─────────────────────────────────────────────────────────────────────────────

def load_schema(conn: sqlite3.Connection) -> None:
    """Execute schema.sql to create all tables if they don't exist."""
    if SCHEMA_PATH.exists():
        sql = SCHEMA_PATH.read_text(encoding="utf-8")
        conn.executescript(sql)
        log.info("  Schema applied from: %s", SCHEMA_PATH)
    else:
        log.warning("  schema.sql not found at %s -- skipping DDL step.", SCHEMA_PATH)


def load_to_sqlite(cleaned: dict[str, pd.DataFrame]) -> None:
    log.info(SEP)
    log.info("STEP 3 -- Loading into SQLite: %s", DB_PATH)
    log.info(SEP)

    engine = create_engine(f"sqlite:///{DB_PATH}")

    with sqlite3.connect(DB_PATH) as conn:
        load_schema(conn)

    dim_date = build_dim_date(cleaned)

    table_map = {
        "dim_fund":                  cleaned["fund_master"].rename(columns={"risk_category": "risk_category"}),
        "dim_date":                  dim_date,
        "fact_nav":                  cleaned["nav_history"],
        "fact_aum":                  cleaned["aum_by_fund_house"],
        "fact_monthly_sip_inflows":  cleaned["monthly_sip_inflows"],
        "fact_category_inflows":     cleaned["category_inflows"],
        "fact_industry_folio_count": cleaned["industry_folio_count"],
        "fact_performance":          cleaned["scheme_performance"],
        "fact_transactions":         cleaned["investor_transactions"],
        "fact_portfolio_holdings":   cleaned["portfolio_holdings"],
        "fact_benchmark_indices":    cleaned["benchmark_indices"],
    }

    for table, df in table_map.items():
        try:
            df.to_sql(table, engine, if_exists="replace", index=False, chunksize=10_000)
            log.info("  [OK] Loaded %-35s  %7d rows", table, len(df))
        except Exception as exc:
            log.error("  [ERROR] Failed to load %s: %s", table, exc)
            raise

    log.info("  [OK] All tables loaded into SQLite database.")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5 -- DATA QUALITY REPORT
# ─────────────────────────────────────────────────────────────────────────────

def write_quality_report(raw_dfs: dict[str, pd.DataFrame], clean_dfs: dict[str, pd.DataFrame]) -> None:
    log.info(SEP)
    log.info("STEP 4 -- Writing data quality report")
    log.info(SEP)

    lines: list[str] = [
        f"DATA QUALITY REPORT -- Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 70,
        "",
        f"{'Dataset':<30} {'Raw Rows':>10} {'Clean Rows':>11} {'Nulls (raw)':>12} {'Dups (raw)':>11}",
        "-" * 70,
    ]

    for key in raw_dfs:
        raw  = raw_dfs[key]
        cln  = clean_dfs.get(key, raw)
        nulls = raw.isnull().sum().sum()
        dups  = raw.duplicated().sum()
        lines.append(
            f"{key:<30} {len(raw):>10,} {len(cln):>11,} {nulls:>12,} {dups:>11,}"
        )

    lines += [
        "",
        "=" * 70,
        "AMFI CODE CROSS-VALIDATION",
        "-" * 70,
    ]

    fm_codes  = set(raw_dfs["fund_master"]["amfi_code"].dropna().astype(str))
    nav_codes = set(raw_dfs["nav_history"]["amfi_code"].dropna().astype(str))
    lines.append(f"fund_master AMFI codes  : {len(fm_codes):,}")
    lines.append(f"nav_history AMFI codes  : {len(nav_codes):,}")
    lines.append(f"Matched                 : {len(fm_codes & nav_codes):,}")
    lines.append(f"Missing in nav_history  : {len(fm_codes - nav_codes):,}")

    report_path = REPORTS_DIR / "data_quality_report.txt"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    log.info("  [OK] Report saved to: %s", report_path)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    start = datetime.now()
    log.info("=" * 70)
    log.info("  BLUESTOCK MF CAPSTONE -- ETL PIPELINE")
    log.info("  Started: %s", start.strftime("%Y-%m-%d %H:%M:%S"))
    log.info("=" * 70)

    try:
        raw_dfs   = load_raw_csvs()
        clean_dfs = clean_all(raw_dfs)
        load_to_sqlite(clean_dfs)
        write_quality_report(raw_dfs, clean_dfs)
    except Exception as exc:
        log.error("ETL FAILED: %s", exc)
        sys.exit(1)

    elapsed = (datetime.now() - start).total_seconds()
    log.info("")
    log.info("=" * 70)
    log.info("  ETL PIPELINE COMPLETE -- %.1f seconds", elapsed)
    log.info("  Database  : %s", DB_PATH)
    log.info("  Processed : %s", PROCESSED_DIR)
    log.info("  Report    : %s", REPORTS_DIR / "data_quality_report.txt")
    log.info("=" * 70)


if __name__ == "__main__":
    main()

