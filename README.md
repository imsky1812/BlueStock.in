# Capstone Project I — Mutual Fund Analytics
**Bluestock Fintech Internship | Batch 2026**

> A comprehensive analytics pipeline for Indian mutual fund data — ETL, live NAV ingestion, performance analytics, and dashboarding.

---

## Project Structure

```
mutual-fund-analytics/
├── data/
│   ├── raw/               ← Original CSVs + live NAV files (do not edit)
│   └── processed/         ← Cleaned / transformed datasets
├── notebooks/             ← Jupyter notebooks for EDA and analysis
├── sql/                   ← SQL scripts for schema and queries
├── dashboard/             ← Plotly Dash / Streamlit app files
├── reports/               ← Generated summaries and reports
├── data_ingestion.py      ← Day 1: Load CSVs, explore, validate
├── live_nav_fetch.py      ← Day 1: Fetch live NAV from mfapi.in
├── requirements.txt       ← Python dependencies
├── setup.sh               ← One-time project setup script
└── README.md
```

---

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/mutual-fund-analytics.git
cd mutual-fund-analytics

# 2. Install dependencies
pip install -r requirements.txt

# 3. Place the 10 provided CSV datasets in data/raw/

# 4. Run Day 1 scripts
python data_ingestion.py    # ETL: load CSVs, explore, validate
python live_nav_fetch.py    # Fetch live NAV from mfapi.in
```

---

## Day 1 Deliverables

| File | Description |
|------|-------------|
| `data_ingestion.py` | Loads all 10 CSVs, prints `.shape/.dtypes/.head()`, flags anomalies, validates AMFI codes |
| `live_nav_fetch.py` | Fetches live NAV for 6 key schemes from `api.mfapi.in`, saves CSV |
| `requirements.txt` | All Python dependencies with pinned versions |
| `reports/data_quality_summary.txt` | Auto-generated data quality report |

---

## Schemes Tracked (Live NAV)

| AMFI Code | Scheme |
|-----------|--------|
| 125497 | HDFC Top 100 Direct Plan – Growth |
| 119551 | SBI Bluechip Direct Plan – Growth |
| 120503 | ICICI Prudential Bluechip Direct Plan – Growth |
| 118632 | Nippon India Large Cap Direct Plan – Growth |
| 119092 | Axis Bluechip Direct Plan – Growth |
| 120841 | Kotak Bluechip Direct Plan – Growth |

---

## Tech Stack

- **Language**: Python 3.11+
- **Data**: Pandas, NumPy, SciPy
- **Viz**: Matplotlib, Seaborn, Plotly
- **DB**: SQLAlchemy
- **API**: mfapi.in (free AMFI NAV API)
- **Notebooks**: Jupyter

---

## Git Workflow

```bash
git add .
git commit -m "Day 1: Data ingestion complete"
git push origin main
```

---

*Project started: 20 Jun 2026 | Due: 24 Jun 2026*
