"""
compute_metrics.py
==================
BlueStock Fintech Internship — Capstone Project I
Performance & Risk Metrics Computation (D4)

Computes:
  - CAGR (252 trading-day annualisation)
  - Sharpe Ratio (annualised)
  - Beta vs. benchmark
  - Alpha (Jensen's)
  - Max Drawdown
  - VaR 95% and CVaR 95% (Historical)

Writes results to data/processed/fund_metrics.csv
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

ROOT_DIR  = Path(__file__).resolve().parent.parent
DB_PATH   = ROOT_DIR / "data" / "db" / "bluestock_mf.db"
OUT_DIR   = ROOT_DIR / "data" / "processed"
RISK_FREE = 0.065 / 252   # 6.5% annual risk-free rate → daily


def connect() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}. Run etl_pipeline.py first.")
    return sqlite3.connect(DB_PATH)


def load_data(conn: sqlite3.Connection):
    funds = pd.read_sql("SELECT * FROM dim_fund", conn)
    nav   = pd.read_sql("SELECT * FROM fact_nav", conn, parse_dates=["date"])
    bench = pd.read_sql("SELECT * FROM fact_benchmark_indices", conn, parse_dates=["date"])
    return funds, nav, bench


def compute_returns(nav: pd.DataFrame) -> pd.DataFrame:
    """Compute daily % returns per fund."""
    nav = nav.sort_values(["amfi_code", "date"])
    nav["daily_return"] = nav.groupby("amfi_code")["nav"].pct_change()
    return nav


def compute_benchmark_returns(bench: pd.DataFrame, index_name: str = "NIFTY 50") -> pd.Series:
    b = bench[bench["index_name"] == index_name].sort_values("date")
    b = b.set_index("date")["close_value"]
    return b.pct_change().rename("bench_return")


def cagr(nav_series: pd.Series, n_trading_days: int) -> float:
    """Annualise with 252 trading days — never calendar days."""
    if n_trading_days < 2:
        return float("nan")
    start, end = nav_series.iloc[0], nav_series.iloc[-1]
    if start <= 0:
        return float("nan")
    years = n_trading_days / 252
    return (end / start) ** (1 / years) - 1


def sharpe(returns: pd.Series) -> float:
    excess = returns - RISK_FREE
    std = excess.std()
    if std == 0 or np.isnan(std):
        return float("nan")
    return (excess.mean() / std) * np.sqrt(252)


def max_drawdown(nav_series: pd.Series) -> float:
    roll_max = nav_series.cummax()
    drawdown = (nav_series - roll_max) / roll_max
    return drawdown.min()


def beta(fund_returns: pd.Series, bench_returns: pd.Series) -> float:
    aligned = pd.concat([fund_returns, bench_returns], axis=1).dropna()
    if len(aligned) < 10:
        return float("nan")
    cov = aligned.cov().iloc[0, 1]
    var = aligned.iloc[:, 1].var()
    return cov / var if var != 0 else float("nan")


def alpha_jensen(fund_returns: pd.Series, bench_returns: pd.Series, b: float) -> float:
    if np.isnan(b):
        return float("nan")
    aligned = pd.concat([fund_returns, bench_returns], axis=1).dropna()
    avg_fund  = aligned.iloc[:, 0].mean() * 252
    avg_bench = aligned.iloc[:, 1].mean() * 252
    rf_ann    = RISK_FREE * 252
    return avg_fund - (rf_ann + b * (avg_bench - rf_ann))


def var_cvar(returns: pd.Series, confidence: float = 0.95) -> tuple[float, float]:
    clean = returns.dropna()
    if len(clean) < 30:
        return float("nan"), float("nan")
    var = clean.quantile(1 - confidence)
    cvar = clean[clean <= var].mean()
    return var * 100, cvar * 100


def compute_all_metrics(conn: sqlite3.Connection) -> pd.DataFrame:
    funds, nav, bench = load_data(conn)
    nav = compute_returns(nav)
    bench_ret = compute_benchmark_returns(bench)

    records = []
    for _, row in funds.iterrows():
        amfi = row["amfi_code"]
        fund_nav = nav[nav["amfi_code"] == amfi].sort_values("date")
        fund_ret = fund_nav.set_index("date")["daily_return"].dropna()

        if len(fund_ret) < 30:
            continue

        n_days = len(fund_ret)
        nav_series = fund_nav.set_index("date")["nav"]

        b   = beta(fund_ret, bench_ret)
        var, cvar = var_cvar(fund_ret)

        records.append({
            "amfi_code":        amfi,
            "scheme_name":      row["scheme_name"],
            "fund_house":       row["fund_house"],
            "category":         row.get("category", ""),
            "n_trading_days":   n_days,
            "cagr_pct":         round(cagr(nav_series, n_days) * 100, 4),
            "sharpe_ratio":     round(sharpe(fund_ret), 4),
            "beta":             round(b, 4),
            "alpha_pct":        round(alpha_jensen(fund_ret, bench_ret, b) * 100, 4),
            "max_drawdown_pct": round(max_drawdown(nav_series) * 100, 4),
            "var_95_pct":       round(var, 4),
            "cvar_95_pct":      round(cvar, 4),
            "std_dev_daily_pct":round(fund_ret.std() * 100, 4),
        })

    df = pd.DataFrame(records)
    return df


if __name__ == "__main__":
    print("Computing fund metrics …")
    with connect() as conn:
        df = compute_all_metrics(conn)

    out = OUT_DIR / "fund_metrics.csv"
    df.to_csv(out, index=False)
    print(f"✓  Metrics saved → {out}")
    print(df[["scheme_name", "cagr_pct", "sharpe_ratio", "beta", "var_95_pct"]].to_string(index=False))
