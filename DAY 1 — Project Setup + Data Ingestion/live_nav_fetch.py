"""
live_nav_fetch.py
=================
DAY 1 — Capstone Project I: Mutual Fund Analytics
Bluestock Fintech Internship

Purpose:
  - Fetch live NAV data from mfapi.in for 6 key mutual fund schemes
  - Parse JSON response and save as raw CSV files in data/raw/
  - Print a consolidated summary table

Schemes covered:
  125497 — HDFC Top 100 Direct Plan – Growth (primary demo scheme)
  119551 — SBI Bluechip Direct Plan – Growth
  120503 — ICICI Prudential Bluechip Direct Plan – Growth
  118632 — Nippon India Large Cap Direct Plan – Growth
  119092 — Axis Bluechip Direct Plan – Growth
  120841 — Kotak Bluechip Direct Plan – Growth

API:  https://api.mfapi.in/mf/<scheme_code>
Docs: https://www.mfapi.in/
"""

import os
import json
import time
import requests
import pandas as pd
from datetime import datetime

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
DATA_RAW   = os.path.join("data", "raw")
os.makedirs(DATA_RAW, exist_ok=True)

BASE_URL   = "https://api.mfapi.in/mf"
TIMEOUT    = 15   # seconds per request
RETRY_MAX  = 3    # max retries on failure
RETRY_WAIT = 2    # seconds between retries

SCHEMES: dict[str, str] = {
    "125497": "HDFC Top 100 Direct Plan - Growth",
    "119551": "SBI Bluechip Direct Plan - Growth",
    "120503": "ICICI Prudential Bluechip Direct Plan - Growth",
    "118632": "Nippon India Large Cap Direct Plan - Growth",
    "119092": "Axis Bluechip Direct Plan - Growth",
    "120841": "Kotak Bluechip Direct Plan - Growth",
}

SEPARATOR = "=" * 70


# ─────────────────────────────────────────────
# FETCH HELPERS
# ─────────────────────────────────────────────

def fetch_nav(scheme_code: str) -> dict | None:
    """
    Fetch NAV JSON for a given scheme code from mfapi.in.
    Retries up to RETRY_MAX times on transient failures.
    Returns the parsed JSON dict, or None on failure.
    """
    url = f"{BASE_URL}/{scheme_code}"
    for attempt in range(1, RETRY_MAX + 1):
        try:
            response = requests.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            print(f"    [Attempt {attempt}/{RETRY_MAX}] Timeout for {scheme_code}. Retrying...")
        except requests.exceptions.HTTPError as e:
            print(f"    [Attempt {attempt}/{RETRY_MAX}] HTTP error {e} for {scheme_code}.")
        except requests.exceptions.ConnectionError:
            print(f"    [Attempt {attempt}/{RETRY_MAX}] Connection error for {scheme_code}. Retrying...")
        except json.JSONDecodeError:
            print(f"    [ERROR] Could not parse JSON for {scheme_code}.")
            return None

        if attempt < RETRY_MAX:
            time.sleep(RETRY_WAIT)

    print(f"    [FAILED] Could not fetch scheme {scheme_code} after {RETRY_MAX} attempts.")
    return None


def parse_nav_response(data: dict, scheme_code: str, scheme_name: str) -> pd.DataFrame | None:
    """
    Parse mfapi.in JSON response into a flat DataFrame.

    Expected JSON structure:
    {
      "meta": { "fund_house": "...", "scheme_type": "...",
                "scheme_category": "...", "scheme_code": 12345,
                "scheme_name": "..." },
      "data": [ {"date": "DD-MM-YYYY", "nav": "123.456"}, … ],
      "status": "SUCCESS"
    }
    """
    if data.get("status") != "SUCCESS":
        print(f"    [WARNING] API returned status='{data.get('status')}' for {scheme_code}.")
        return None

    meta       = data.get("meta", {})
    nav_records = data.get("data", [])

    if not nav_records:
        print(f"    [WARNING] No NAV records returned for {scheme_code}.")
        return None

    df = pd.DataFrame(nav_records)                          # columns: date, nav
    df["nav"]  = pd.to_numeric(df["nav"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y", errors="coerce")
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Enrich with metadata
    df.insert(0, "scheme_code",     scheme_code)
    df.insert(1, "scheme_name",     meta.get("scheme_name", scheme_name))
    df.insert(2, "fund_house",      meta.get("fund_house", ""))
    df.insert(3, "scheme_type",     meta.get("scheme_type", ""))
    df.insert(4, "scheme_category", meta.get("scheme_category", ""))

    return df


def save_nav_csv(df: pd.DataFrame, scheme_code: str) -> str:
    """Save NAV DataFrame as CSV to data/raw/ and return the file path."""
    filename  = f"live_nav_{scheme_code}.csv"
    filepath  = os.path.join(DATA_RAW, filename)
    df.to_csv(filepath, index=False)
    return filepath


def print_scheme_summary(df: pd.DataFrame) -> None:
    """Pretty-print key stats for one scheme."""
    latest = df.iloc[-1]
    oldest = df.iloc[0]
    print(f"    Fund House    : {latest['fund_house']}")
    print(f"    Category      : {latest['scheme_category']}")
    print(f"    Records       : {len(df):,} NAV entries")
    print(f"    Date Range    : {oldest['date'].date()}  ->  {latest['date'].date()}")
    print(f"    Latest NAV    : Rs. {latest['nav']:,.4f}  (as of {latest['date'].date()})")
    nav_min = df["nav"].min()
    nav_max = df["nav"].max()
    print(f"    52w Range (all-time)  Min=Rs. {nav_min:,.4f}  Max=Rs. {nav_max:,.4f}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    print(f"\n{'#'*70}")
    print(f"  CAPSTONE PROJECT I - MUTUAL FUND ANALYTICS")
    print(f"  DAY 1: Live NAV Fetch  |  mfapi.in")
    print(f"{'#'*70}\n")

    fetched_at   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    all_frames   = []
    summary_rows = []

    for scheme_code, scheme_name in SCHEMES.items():
        print(SEPARATOR)
        print(f"  Fetching: [{scheme_code}]  {scheme_name}")
        print(SEPARATOR)

        raw_data = fetch_nav(scheme_code)
        if raw_data is None:
            summary_rows.append({
                "scheme_code": scheme_code,
                "scheme_name": scheme_name,
                "status":      "FAILED",
                "records":     0,
                "latest_date": None,
                "latest_nav":  None,
            })
            continue

        df = parse_nav_response(raw_data, scheme_code, scheme_name)
        if df is None:
            summary_rows.append({
                "scheme_code": scheme_code,
                "scheme_name": scheme_name,
                "status":      "PARSE_ERROR",
                "records":     0,
                "latest_date": None,
                "latest_nav":  None,
            })
            continue

        filepath = save_nav_csv(df, scheme_code)
        print_scheme_summary(df)
        print(f"    [OK] Saved -> {filepath}")
        print()

        all_frames.append(df)
        summary_rows.append({
            "scheme_code": scheme_code,
            "scheme_name": df.iloc[-1]["scheme_name"],
            "status":      "OK",
            "records":     len(df),
            "latest_date": str(df.iloc[-1]["date"].date()),
            "latest_nav":  float(df.iloc[-1]["nav"]),
        })

        time.sleep(0.5)   # polite delay between API calls

    # ── Combined NAV file ──────────────────────────────────────
    if all_frames:
        combined = pd.concat(all_frames, ignore_index=True)
        combined_path = os.path.join(DATA_RAW, "live_nav_all_schemes.csv")
        combined.to_csv(combined_path, index=False)
        print(f"\n[OK] Combined NAV file saved -> {combined_path}  ({len(combined):,} rows total)")

    # ── Summary table ─────────────────────────────────────────
    summary_df = pd.DataFrame(summary_rows)
    print(f"\n{SEPARATOR}")
    print(f"  FETCH SUMMARY  |  {fetched_at}")
    print(SEPARATOR)
    print(summary_df.to_string(index=False))

    success_count = (summary_df["status"] == "OK").sum()
    print(f"\n  {success_count}/{len(SCHEMES)} schemes fetched successfully.")

    print(f"\n{'#'*70}")
    print(f"  Day 1 live_nav_fetch.py - COMPLETE")
    print(f"{'#'*70}\n")


if __name__ == "__main__":
    main()
