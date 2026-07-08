# Bluestock MF Capstone — Mutual Fund Industry Analytics

> **BlueStock Fintech Internship · Batch 2026 · Submitted: 10 Jul 2026**

A comprehensive end-to-end analytics pipeline covering **40 mutual fund schemes** from India's leading AMCs — ETL, EDA, performance analytics, advanced risk metrics, interactive dashboard, and portfolio optimisation.

**Team:** Sai Sindhuja Ch · Sarvesh K Yadav · Ganga Damalathi

---

## Deliverables Checklist

| ID | Deliverable | File | Weight | Status |
|----|-------------|------|--------|--------|
| D1 | ETL Pipeline | `scripts/etl_pipeline.py` | 15% | ✅ Complete |
| D2 | SQLite Database | `data/db/bluestock_mf.db` | 10% | ✅ Complete |
| D3 | EDA Notebook | `notebooks/03_eda_analysis.ipynb` | 15% | ✅ Complete |
| D4 | Performance Metrics | `notebooks/04_performance_analytics.ipynb` | 15% | ✅ Complete |
| D5 | Interactive Dashboard | `dashboard/app.py` + `.pbix` | 20% | ✅ Complete |
| D6 | Advanced Analytics | `notebooks/05_advanced_analytics.ipynb` | 10% | ✅ Complete |
| D7 | Final Report + Slides | `reports/Final_Report.html` + `Presentation.pptx` | 15% | ✅ Complete |
| B2 | Streamlit App | `dashboard/app.py` | +10 | ✅ Complete |
| B3 | Monte Carlo Simulation | `notebooks/05_advanced_analytics.ipynb §7` | +10 | ✅ Complete |
| B4 | Markowitz Efficient Frontier | `notebooks/05_advanced_analytics.ipynb §8` | +10 | ✅ Complete |

---

## Folder Structure

```
bluestock_mf_capstone/
├── data/
│   ├── raw/               ← original downloaded CSV files (10 datasets)
│   ├── processed/         ← cleaned, merged CSVs + metric outputs
│   └── db/                ← bluestock_mf.db (SQLite) — git-ignored
├── notebooks/
│   ├── 01_data_ingestion.ipynb
│   ├── 02_data_cleaning.ipynb
│   ├── 03_eda_analysis.ipynb
│   ├── 04_performance_analytics.ipynb
│   └── 05_advanced_analytics.ipynb    ← includes B3 Monte Carlo + B4 Frontier
├── scripts/
│   ├── etl_pipeline.py               ← D1: unified ETL (pathlib, ffill, error handling)
│   ├── live_nav_fetch.py             ← fetches live NAV from mfapi.in
│   ├── compute_metrics.py            ← CAGR, Sharpe, Beta, VaR standalone
│   └── recommender.py                ← rule-based fund recommender
├── sql/
│   ├── schema.sql                    ← star schema DDL (share this, not the .db)
│   └── queries.sql                   ← analytical SQL queries
├── dashboard/
│   ├── app.py                        ← D5/B2: Streamlit interactive dashboard
│   └── bluestock_mf_dashboard.pbix   ← D5: Power BI dashboard
├── reports/
│   ├── Final_Report.html             ← D7: open in browser, print to PDF
│   ├── generate_pptx.py              ← run to generate Presentation.pptx
│   └── Presentation.pptx             ← D7: 15-slide professional presentation
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Quick Start

```bash
# 1. Clone & install dependencies
git clone https://github.com/<your-username>/bluestock_mf_capstone.git
cd bluestock_mf_capstone
pip install -r requirements.txt

# 2. Place the 10 CSV datasets in data/raw/
#    (01_fund_master.csv through 10_benchmark_indices.csv)

# 3. Run the ETL pipeline
python scripts/etl_pipeline.py
#    → cleans all 10 datasets → loads SQLite DB → writes quality report

# 4. Launch the Streamlit dashboard (B2/D5)
streamlit run dashboard/app.py

# 5. Generate the PPTX presentation (D7)
pip install python-pptx
python reports/generate_pptx.py
```

---

## Running Notebooks

```bash
jupyter notebook
# Open notebooks/ in order: 01 → 02 → 03 → 04 → 05
```

Notebook 05 includes:
- **§7 — [B3] Monte Carlo Simulation**: 1,000 GBM paths, 5-year horizon, P5/P50/P95 bands
- **§8 — [B4] Markowitz Efficient Frontier**: Min Variance + Max Sharpe portfolios for 5 equity funds

---

## Database Schema

11 tables in a star schema. To recreate the schema from scratch:

```bash
sqlite3 data/db/bluestock_mf.db < sql/schema.sql
```

See [`sql/schema.sql`](sql/schema.sql) for full DDL.

> **Note:** `*.db` files are excluded from git (see `.gitignore`). Share `schema.sql` instead.

---

## Key Technical Decisions

| Decision | Why |
|----------|-----|
| `pathlib.Path` everywhere | No hard-coded absolute paths — runs on any machine |
| `ffill()` after `reindex(freq="B")` | Correctly handles weekends + public holidays in NAV |
| 252 trading days for annualisation | CAGR/Sharpe always use trading days, never calendar days |
| `low_memory=False` for large CSVs | Prevents mixed-type inference warnings |
| Star schema in SQLite | Efficient for analytical queries without a heavy DB server |

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.11+ |
| Data Processing | Pandas 2.x, NumPy |
| Database | SQLite + SQLAlchemy |
| Visualisation | Matplotlib, Seaborn, Plotly |
| Dashboard | Streamlit + Plotly |
| Optimisation | SciPy (SLSQP) |
| Presentation | python-pptx |
| Notebooks | Jupyter |
| BI Tool | Power BI |

---

## Common Mistakes Avoided

- ❌ ~~Hard-coded file paths~~ → ✅ `pathlib.Path(__file__).resolve().parent.parent`
- ❌ ~~No holiday handling in NAV~~ → ✅ `ffill()` after `reindex(freq="B")`
- ❌ ~~Calendar days for CAGR~~ → ✅ `252 / n_trading_days`
- ❌ ~~Dashboard with no slicers~~ → ✅ Every Streamlit page has ≥2 filters
- ❌ ~~Confusing AUM units~~ → ✅ Column names include `_lakh_crore` or `_crore`
- ❌ ~~Committing .db to GitHub~~ → ✅ `*.db` in `.gitignore`; schema.sql shared instead

---

*Project started: Jun 2026 · Submitted: 10 Jul 2026 · BlueStock Fintech Internship · Batch 2026*
