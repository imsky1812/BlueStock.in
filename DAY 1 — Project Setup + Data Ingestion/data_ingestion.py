"""
data_ingestion.py
=================
DAY 1 — Capstone Project I: Mutual Fund Analytics
Bluestock Fintech Internship

Purpose:
  - Load all 10 CSV datasets from data/raw/
  - Print .shape, .dtypes, .head() for each
  - Note data anomalies
  - Explore fund_master (unique fund houses, categories, sub-categories, risk grades)
  - Validate AMFI codes across fund_master and nav_history
  - Write a short data quality summary to reports/data_quality_summary.txt
"""

import os
import glob
import pandas as pd
import numpy as np
from datetime import datetime

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
DATA_RAW       = os.path.join("data", "raw")
DATA_PROCESSED = os.path.join("data", "processed")
REPORTS_DIR    = "reports"

os.makedirs(DATA_PROCESSED, exist_ok=True)
os.makedirs(REPORTS_DIR,    exist_ok=True)

SEPARATOR = "=" * 70

# ─────────────────────────────────────────────
# SECTION 1 — LOAD ALL CSV DATASETS
# ─────────────────────────────────────────────

def load_all_csvs(raw_dir: str) -> dict[str, pd.DataFrame]:
    """
    Discover and load every .csv file inside raw_dir.
    Returns a dict: {filename_stem: DataFrame}
    """
    csv_files = sorted(glob.glob(os.path.join(raw_dir, "*.csv")))

    if not csv_files:
        print(f"[WARNING] No CSV files found in '{raw_dir}'.")
        print(f"          Place your 10 dataset CSVs inside '{raw_dir}/' and re-run.\n")
        return {}

    print(SEPARATOR)
    print(f"  LOADING {len(csv_files)} CSV FILE(S) FROM: {raw_dir}")
    print(SEPARATOR)

    datasets: dict[str, pd.DataFrame] = {}

    for path in csv_files:
        name = os.path.splitext(os.path.basename(path))[0]
        try:
            df = pd.read_csv(path, low_memory=False)
            datasets[name] = df
            print(f"\n{'-'*60}")
            print(f"  Dataset : {name}")
            print(f"{'-'*60}")
            print(f"  Shape   : {df.shape}  ({df.shape[0]:,} rows × {df.shape[1]} cols)")
            print("\n  dtypes:")
            print(df.dtypes.to_string())
            print("\n  head(3):")
            print(df.head(3).to_string())
            _flag_anomalies(df, name)
        except Exception as exc:
            print(f"  [ERROR] Could not read '{path}': {exc}")

    return datasets


def _flag_anomalies(df: pd.DataFrame, name: str) -> None:
    """Print a quick anomaly summary for a single DataFrame."""
    issues = []

    # Missing values
    null_counts = df.isnull().sum()
    null_cols   = null_counts[null_counts > 0]
    if not null_cols.empty:
        for col, cnt in null_cols.items():
            pct = cnt / len(df) * 100
            issues.append(f"  [WARNING] '{col}' has {cnt:,} nulls ({pct:.1f}%)")

    # Duplicate rows
    dup_count = df.duplicated().sum()
    if dup_count:
        issues.append(f"  [WARNING] {dup_count:,} fully duplicate rows detected")

    # Numeric columns with negative values (might be anomalous for NAV/returns)
    for col in df.select_dtypes(include=[np.number]).columns:
        neg = (df[col] < 0).sum()
        if neg:
            issues.append(f"  [WARNING] '{col}' contains {neg:,} negative value(s)")

    # Possible date columns - check for unparseable values
    for col in df.columns:
        if any(kw in col.lower() for kw in ["date", "dt", "time"]):
            try:
                pd.to_datetime(df[col], errors="raise")
            except Exception:
                bad = pd.to_datetime(df[col], errors="coerce").isna().sum()
                if bad:
                    issues.append(f"  [WARNING] '{col}' has {bad:,} unparseable date(s)")

    if issues:
        print("\n  Anomalies:")
        for msg in issues:
            print(msg)
    else:
        print("\n  [OK] No obvious anomalies detected.")


# ─────────────────────────────────────────────
# SECTION 2 — EXPLORE FUND MASTER
# ─────────────────────────────────────────────

def explore_fund_master(datasets: dict[str, pd.DataFrame]) -> pd.DataFrame | None:
    """
    Finds the fund_master DataFrame (by key containing 'fund_master' or 'fundmaster'),
    then prints unique values for fund_house, category, sub_category, and risk_grade.
    Returns the DataFrame for downstream use.
    """
    # Try to find the fund_master by key name
    fm_key = None
    for key in datasets:
        if "fund_master" in key.lower() or "fundmaster" in key.lower():
            fm_key = key
            break

    if fm_key is None:
        print("\n[INFO] fund_master dataset not found by name. Looking for 'amfi_code' column…")
        for key, df in datasets.items():
            cols_lower = [c.lower() for c in df.columns]
            if "amfi_code" in cols_lower or "scheme_code" in cols_lower:
                fm_key = key
                print(f"       Using '{key}' as fund master (has amfi_code/scheme_code column).")
                break

    if fm_key is None:
        print("[WARNING] Could not identify fund_master dataset. Skipping fund master exploration.")
        return None

    fm: pd.DataFrame = datasets[fm_key]

    print(f"\n{SEPARATOR}")
    print(f"  FUND MASTER EXPLORATION  -  '{fm_key}'")
    print(SEPARATOR)

    # Flexible column detection
    col_map = {}
    for target, keywords in {
        "fund_house":    ["fund_house", "amc", "amc_name", "fund_house_name"],
        "category":      ["category",   "scheme_category"],
        "sub_category":  ["sub_category", "subcategory", "scheme_sub_category"],
        "risk_grade":    ["risk_grade", "risk", "riskometer", "risk_level"],
        "amfi_code":     ["amfi_code",  "scheme_code", "amfi"],
    }.items():
        for col in fm.columns:
            if col.lower() in keywords:
                col_map[target] = col
                break

    for label, col_name in col_map.items():
        if label == "amfi_code":
            continue
        uniq = fm[col_name].dropna().unique()
        print(f"\n  [{label.upper()}]  ({col_name})  -  {len(uniq)} unique values:")
        for val in sorted(uniq):
            print(f"    - {val}")

    # AMFI scheme code structure
    if "amfi_code" in col_map:
        codes = fm[col_map["amfi_code"]].dropna()
        print(f"\n  [AMFI CODE STRUCTURE]")
        print(f"    Total codes : {len(codes):,}")
        print(f"    Sample      : {codes.head(10).tolist()}")
        code_lengths = codes.astype(str).str.len().value_counts().sort_index()
        print(f"    Code lengths:\n{code_lengths.to_string()}")

    return fm


# ─────────────────────────────────────────────
# SECTION 3 — VALIDATE AMFI CODES
# ─────────────────────────────────────────────

def validate_amfi_codes(datasets: dict[str, pd.DataFrame], fund_master: pd.DataFrame | None) -> str:
    """
    Confirm every AMFI code in fund_master exists in nav_history.
    Returns a text summary.
    """
    summary_lines: list[str] = []
    summary_lines.append(f"DATA QUALITY SUMMARY - Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    summary_lines.append("=" * 60)

    if fund_master is None:
        msg = "[SKIP] fund_master not available; AMFI validation skipped."
        print(f"\n{msg}")
        summary_lines.append(msg)
        return "\n".join(summary_lines)

    # Detect AMFI code column in fund_master
    fm_code_col = None
    for col in fund_master.columns:
        if col.lower() in ["amfi_code", "scheme_code", "amfi"]:
            fm_code_col = col
            break

    if fm_code_col is None:
        msg = "[WARNING] No AMFI code column found in fund_master."
        print(f"\n{msg}")
        summary_lines.append(msg)
        return "\n".join(summary_lines)

    fm_codes = set(fund_master[fm_code_col].dropna().astype(str))

    # Find nav_history dataset
    nav_key = None
    for key in datasets:
        if "nav_history" in key.lower() or "navhistory" in key.lower() or "nav" in key.lower():
            nav_key = key
            break

    print(f"\n{SEPARATOR}")
    print(f"  AMFI CODE VALIDATION")
    print(SEPARATOR)

    if nav_key is None:
        msg = f"[WARNING] nav_history dataset not found. Available datasets: {list(datasets.keys())}"
        print(f"  {msg}")
        summary_lines.append(msg)
    else:
        nav_df = datasets[nav_key]
        # Detect code column in nav_history
        nav_code_col = None
        for col in nav_df.columns:
            if col.lower() in ["amfi_code", "scheme_code", "amfi", "fund_code"]:
                nav_code_col = col
                break

        if nav_code_col is None:
            msg = f"[WARNING] No AMFI code column found in '{nav_key}'."
            print(f"  {msg}")
            summary_lines.append(msg)
        else:
            nav_codes  = set(nav_df[nav_code_col].dropna().astype(str))
            missing    = fm_codes - nav_codes
            extra      = nav_codes - fm_codes
            matched    = fm_codes & nav_codes

            print(f"  fund_master codes : {len(fm_codes):,}")
            print(f"  nav_history codes : {len(nav_codes):,}")
            print(f"  Matched           : {len(matched):,}")
            print(f"  Missing in nav    : {len(missing):,}")
            print(f"  + Extra in nav    : {len(extra):,}")

            if missing:
                print(f"\n  Codes in fund_master NOT in nav_history (first 20):")
                for code in sorted(missing)[:20]:
                    print(f"    {code}")

            summary_lines.append(f"fund_master AMFI codes   : {len(fm_codes):,}")
            summary_lines.append(f"nav_history AMFI codes   : {len(nav_codes):,}")
            summary_lines.append(f"Matched codes            : {len(matched):,}")
            summary_lines.append(f"Missing in nav_history   : {len(missing):,}")
            summary_lines.append(f"Extra in nav_history     : {len(extra):,}")
            if missing:
                summary_lines.append(f"Missing codes (sample)   : {sorted(missing)[:10]}")

    # Per-dataset quality stats
    summary_lines.append("\n" + "-" * 60)
    summary_lines.append("PER-DATASET QUALITY STATS")
    summary_lines.append("-" * 60)
    for name, df in datasets.items():
        total_cells  = df.shape[0] * df.shape[1]
        null_cells   = df.isnull().sum().sum()
        null_pct     = null_cells / total_cells * 100 if total_cells else 0
        dup_rows     = df.duplicated().sum()
        line = (f"{name:<30} | rows={df.shape[0]:>7,} | cols={df.shape[1]:>3} "
                f"| nulls={null_pct:>5.1f}% | dups={dup_rows:>5,}")
        summary_lines.append(line)

    return "\n".join(summary_lines)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    print(f"\n{'#'*70}")
    print(f"  CAPSTONE PROJECT I - MUTUAL FUND ANALYTICS")
    print(f"  DAY 1: Data Ingestion (ETL)")
    print(f"{'#'*70}\n")

    # 1. Load all CSVs
    datasets = load_all_csvs(DATA_RAW)

    # 2. Explore fund master
    fund_master = explore_fund_master(datasets)

    # 3. Validate AMFI codes
    summary = validate_amfi_codes(datasets, fund_master)

    # 4. Save data quality summary
    summary_path = os.path.join(REPORTS_DIR, "data_quality_summary.txt")
    with open(summary_path, "w") as f:
        f.write(summary)
    print(f"\n\n[OK] Data quality summary saved -> {summary_path}")

    # 5. Save combined processed snapshot (if any data loaded)
    for name, df in datasets.items():
        out_path = os.path.join(DATA_PROCESSED, f"{name}_cleaned.csv")
        df.to_csv(out_path, index=False)
    if datasets:
        print(f"[OK] Processed CSVs saved   -> {DATA_PROCESSED}/")

    print(f"\n{'#'*70}")
    print(f"  Day 1 data_ingestion.py - COMPLETE")
    print(f"{'#'*70}\n")


if __name__ == "__main__":
    main()
