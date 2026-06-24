# Data Dictionary — Mutual Fund Analytics Database
**Day 2: Cleaned Data + SQLite DB Loaded**

This document describes the structure, data types, business definitions, constraints, and source references for all tables in the SQLite database `bluestock_mf.db`.

---

## Table Overview

The database uses a **Star Schema** to enable efficient multi-dimensional analytical queries:
- **Dimension Tables**: `dim_fund`, `dim_date`
- **Fact Tables**: `fact_nav`, `fact_transactions`, `fact_performance`, `fact_aum`
- **Supporting Fact Tables**: `fact_monthly_sip_inflows`, `fact_category_inflows`, `fact_industry_folio_count`, `fact_portfolio_holdings`, `fact_benchmark_indices`

---

## 1. Table: `dim_fund`
* **Description**: Dimension table containing static metadata for mutual fund schemes.
* **Source Reference**: `01_fund_master.csv`
* **Primary Key**: `amfi_code`

| Column Name | Data Type | Key/Constraint | Business Definition / Description |
| :--- | :--- | :--- | :--- |
| `amfi_code` | INTEGER | PRIMARY KEY | Unique Association of Mutual Funds in India (AMFI) code representing the scheme. |
| `fund_house` | TEXT | NOT NULL | Name of the Asset Management Company (AMC) managing the fund (e.g., SBI Mutual Fund). |
| `scheme_name` | TEXT | NOT NULL | Full name of the mutual fund scheme (e.g., SBI Bluechip Fund - Regular Plan - Growth). |
| `category` | TEXT | - | Broad asset class category (Equity, Debt, Hybrid, Solution Oriented, Other). |
| `sub_category` | TEXT | - | Specific investment style/focus sub-category (Large Cap, Mid Cap, Small Cap, Gilt, Liquid, etc.). |
| `plan` | TEXT | - | Plan type: `Regular` (intermediary-assisted) or `Direct` (low cost, purchased directly). |
| `launch_date` | TEXT | - | The date the scheme was launched (Formatted as `YYYY-MM-DD`). |
| `benchmark` | TEXT | - | The official index against which the scheme's performance is measured (e.g. NIFTY 100 TRI). |
| `expense_ratio_pct` | REAL | - | The annual operating expenses of the scheme, expressed as a percentage of average net assets. |
| `exit_load_pct` | REAL | - | The percentage fee charged to investors when redeeming units within a specified lock-in period. |
| `min_sip_amount` | REAL | - | Minimum investment amount required to start a Systematic Investment Plan (SIP). |
| `min_lumpsum_amount`| REAL | - | Minimum investment amount required for a one-time (lumpsum) investment. |
| `fund_manager` | TEXT | - | Name of the primary fund manager(s) responsible for making portfolio decisions. |
| `risk_category` | TEXT | - | SEBI-mandated risk label (Low, Low to Moderate, Moderate, Moderately High, High, Very High). |
| `sebi_category_code`| TEXT | - | Standard SEBI classification code (e.g., EC01, EC03). |

---

## 2. Table: `dim_date`
* **Description**: Generated calendar dimension table covering all calendar dates between `2022-01-01` and `2026-12-31`.
* **Source Reference**: Dynamically generated via Pandas `date_range`
* **Primary Key**: `date`

| Column Name | Data Type | Key/Constraint | Business Definition / Description |
| :--- | :--- | :--- | :--- |
| `date` | TEXT | PRIMARY KEY | Calendar date in standard string format `YYYY-MM-DD`. |
| `year` | INTEGER | NOT NULL | Four-digit calendar year (e.g., 2024). |
| `month` | INTEGER | NOT NULL | Calendar month number (1 = January, 12 = December). |
| `day` | INTEGER | NOT NULL | Calendar day of the month (1 to 31). |
| `quarter` | INTEGER | NOT NULL | Calendar quarter of the year (1 to 4). |
| `day_of_week` | INTEGER | NOT NULL | Zero-indexed day of the week (0 = Monday, 6 = Sunday). |
| `day_name` | TEXT | NOT NULL | Text name of the day of the week (e.g., Monday). |
| `month_name` | TEXT | NOT NULL | Full text name of the month (e.g., January). |
| `is_weekend` | INTEGER | NOT NULL | Binary flag: `1` if day is Saturday or Sunday, `0` if day is a weekday. |

---

## 3. Table: `fact_nav`
* **Description**: Fact table tracking the daily Net Asset Value (NAV) of mutual fund schemes. Missing weekend and holiday NAV values are forward-filled.
* **Source Reference**: `02_nav_history.csv`
* **Primary Key**: `(amfi_code, date)`

| Column Name | Data Type | Key/Constraint | Business Definition / Description |
| :--- | :--- | :--- | :--- |
| `amfi_code` | INTEGER | FOREIGN KEY | REFERENCES `dim_fund(amfi_code)`. Unique AMFI code of the scheme. |
| `date` | TEXT | FOREIGN KEY | REFERENCES `dim_date(date)`. Date of the NAV entry (`YYYY-MM-DD`). |
| `nav` | REAL | NOT NULL | Net Asset Value (price per unit) of the fund on that date. Value is validated to be > 0. |

---

## 4. Table: `fact_transactions`
* **Description**: Fact table recording transaction histories of investors across schemes.
* **Source Reference**: `08_investor_transactions.csv`
* **Primary Key**: `transaction_id` (Autoincrement)

| Column Name | Data Type | Key/Constraint | Business Definition / Description |
| :--- | :--- | :--- | :--- |
| `transaction_id` | INTEGER | PRIMARY KEY | Automatically incremented unique integer identifier for each transaction. |
| `investor_id` | TEXT | NOT NULL | Unique anonymized identifier representing an investor account (e.g., INV003054). |
| `transaction_date` | TEXT | FOREIGN KEY | REFERENCES `dim_date(date)`. Date the transaction occurred (`YYYY-MM-DD`). |
| `amfi_code` | INTEGER | FOREIGN KEY | REFERENCES `dim_fund(amfi_code)`. AMFI code of the mutual fund scheme. |
| `transaction_type` | TEXT | NOT NULL | Standardized transaction type: `SIP`, `Lumpsum`, or `Redemption`. |
| `amount_inr` | REAL | NOT NULL | Monetary value of the transaction in Indian Rupees (INR). Validated to be > 0. |
| `state` | TEXT | - | State where the investor resides (e.g., Maharashtra, Punjab). |
| `city` | TEXT | - | City of investor residence (e.g., Mumbai, Amritsar). |
| `city_tier` | TEXT | - | Location classifications: `T30` (Top 30 geographic areas) or `B30` (Beyond Top 30). |
| `age_group` | TEXT | - | Age group of the investor (e.g., 18-25, 26-35, 36-45, 46-55, 56+). |
| `gender` | TEXT | - | Gender of the investor (e.g., Male, Female). |
| `annual_income_lakh`| REAL | - | Investor's annual income expressed in lakhs of Indian Rupees (1 lakh = 100,000 INR). |
| `payment_mode` | TEXT | - | Payment method used: UPI, Net Banking, Cheque, or Mandate. |
| `kyc_status` | TEXT | - | Know-Your-Customer validation status. Enforced enum: `Verified` or `Pending`. |

---

## 5. Table: `fact_performance`
* **Description**: Fact table summarizing historical risk and return metrics for mutual fund schemes.
* **Source Reference**: `07_scheme_performance.csv`
* **Primary Key**: `amfi_code`

| Column Name | Data Type | Key/Constraint | Business Definition / Description |
| :--- | :--- | :--- | :--- |
| `amfi_code` | INTEGER | PRIMARY KEY | REFERENCES `dim_fund(amfi_code)`. Unique AMFI code of the scheme. |
| `scheme_name` | TEXT | NOT NULL | Full name of the mutual fund scheme. |
| `fund_house` | TEXT | NOT NULL | AMC name. |
| `category` | TEXT | - | Detailed sub-category (Large Cap, Small Cap, Gilt, Liquid, etc.). |
| `plan` | TEXT | - | Plan type: `Regular` or `Direct`. |
| `return_1yr_pct` | REAL | - | Annualized scheme return over the last 1 year (as a percentage). |
| `return_3yr_pct` | REAL | - | Annualized scheme return over the last 3 years (as a percentage). |
| `return_5yr_pct` | REAL | - | Annualized scheme return over the last 5 years (as a percentage). |
| `benchmark_3yr_pct` | REAL | - | Annualized return of the fund's benchmark index over the last 3 years (as a percentage). |
| `alpha` | REAL | - | Excess return of the fund relative to the benchmark index (positive represents outperformance). |
| `beta` | REAL | - | Sensitivity of the fund's returns relative to the benchmark index (1.0 means moves with index). |
| `sharpe_ratio` | REAL | - | Risk-adjusted return measure (return per unit of total risk). |
| `sortino_ratio` | REAL | - | Downside risk-adjusted return measure (return per unit of downside risk). |
| `std_dev_ann_pct` | REAL | - | Annualized standard deviation of weekly returns, measuring overall volatility. |
| `max_drawdown_pct` | REAL | - | The maximum peak-to-trough decline of the fund's NAV (expressed as a negative percentage). |
| `aum_crore` | REAL | - | Assets Under Management of the scheme in crores of Indian Rupees (1 crore = 10,000,000 INR). |
| `expense_ratio_pct` | REAL | - | Scheme operating expense ratio. Checked to fall between 0.1% and 2.5%. |
| `morningstar_rating`| INTEGER | - | Star rating assigned by Morningstar, based on risk-adjusted return (1 to 5). |
| `risk_grade` | TEXT | - | Qualitative risk designation (Low, Moderate, High, Very High). |

---

## 6. Table: `fact_aum`
* **Description**: Fact table tracking the Assets Under Management at the Fund House (AMC) level over time.
* **Source Reference**: `03_aum_by_fund_house.csv`
* **Primary Key**: `(date, fund_house)`

| Column Name | Data Type | Key/Constraint | Business Definition / Description |
| :--- | :--- | :--- | :--- |
| `date` | TEXT | FOREIGN KEY | REFERENCES `dim_date(date)`. Date of the AUM record (`YYYY-MM-DD`). |
| `fund_house` | TEXT | NOT NULL | Name of the Asset Management Company (AMC). |
| `aum_lakh_crore` | REAL | - | AUM in lakhs of crores of Indian Rupees (e.g. 6.05 lakh crore = 605,000 crore). |
| `aum_crore` | REAL | - | AUM in crores of Indian Rupees. |
| `num_schemes` | INTEGER | - | Count of active mutual fund schemes offered by the fund house. |

---

## 7. Table: `fact_monthly_sip_inflows`
* **Description**: Supporting fact table tracking monthly industry-wide Systematic Investment Plan (SIP) statistics.
* **Source Reference**: `04_monthly_sip_inflows.csv`
* **Primary Key**: `month`

| Column Name | Data Type | Key/Constraint | Business Definition / Description |
| :--- | :--- | :--- | :--- |
| `month` | TEXT | PRIMARY KEY | Month of the record in format `YYYY-MM`. |
| `sip_inflow_crore` | REAL | - | Total monthly inflows received through SIPs across the industry in crores INR. |
| `active_sip_accounts_crore`| REAL| - | Total number of active SIP accounts in crores. |
| `new_sip_accounts_lakh`| REAL | - | Number of new SIP accounts registered during the month in lakhs. |
| `sip_aum_lakh_crore` | REAL | - | Total assets under management accumulated through SIPs in lakhs of crores INR. |
| `yoy_growth_pct` | REAL | - | Year-over-Year percentage growth of SIP inflows compared to the same month last year. |

---

## 8. Table: `fact_category_inflows`
* **Description**: Supporting fact table detailing net inflows by fund category monthly.
* **Source Reference**: `05_category_inflows.csv`
* **Primary Key**: `(month, category)`

| Column Name | Data Type | Key/Constraint | Business Definition / Description |
| :--- | :--- | :--- | :--- |
| `month` | TEXT | - | Month of the record in format `YYYY-MM`. |
| `category` | TEXT | - | Broad mutual fund category (e.g., Large Cap, Mid Cap, Small Cap, Liquid, Gilt, ELSS). |
| `net_inflow_crore` | REAL | - | Net monthly inflows (Inflows - Redemptions) in crores INR. |

---

## 9. Table: `fact_industry_folio_count`
* **Description**: Supporting fact table tracking overall mutual fund folios in the Indian industry.
* **Source Reference**: `06_industry_folio_count.csv`
* **Primary Key**: `month`

| Column Name | Data Type | Key/Constraint | Business Definition / Description |
| :--- | :--- | :--- | :--- |
| `month` | TEXT | PRIMARY KEY | Month of the record in format `YYYY-MM`. |
| `total_folios_crore` | REAL | - | Total industry folios (investor accounts) in crores. |
| `equity_folios_crore`| REAL | - | Total equity-oriented mutual fund folios in crores. |
| `debt_folios_crore` | REAL | - | Total debt-oriented mutual fund folios in crores. |
| `hybrid_folios_crore`| REAL | - | Total hybrid-oriented mutual fund folios in crores. |
| `others_folios_crore`| REAL | - | Total folios in other categories (ETF, FOF, Gold) in crores. |

---

## 10. Table: `fact_portfolio_holdings`
* **Description**: Supporting fact table detailing specific stock holdings of each mutual fund scheme.
* **Source Reference**: `09_portfolio_holdings.csv`
* **Primary Key**: `(amfi_code, stock_symbol, portfolio_date)`

| Column Name | Data Type | Key/Constraint | Business Definition / Description |
| :--- | :--- | :--- | :--- |
| `amfi_code` | INTEGER | FOREIGN KEY | REFERENCES `dim_fund(amfi_code)`. Unique AMFI code of the holding mutual fund. |
| `stock_symbol` | TEXT | - | Stock trading ticker symbol on Indian exchanges (e.g., POWERGRID, HDFCBANK). |
| `stock_name` | TEXT | - | Official company name (e.g., Power Grid Corporation, HDFC Bank Ltd). |
| `sector` | TEXT | - | Industrial sector the company belongs to (e.g., Utilities, Banking, IT, Pharma). |
| `weight_pct` | REAL | - | Percentage allocation of the stock in the fund's total assets. |
| `market_value_cr` | REAL | - | Market value of the stock holdings in crores INR. |
| `current_price_inr` | REAL | - | Current closing price of a single stock share in INR. |
| `portfolio_date` | TEXT | FOREIGN KEY | REFERENCES `dim_date(date)`. Date of the holdings snapshot (`YYYY-MM-DD`). |

---

## 11. Table: `fact_benchmark_indices`
* **Description**: Supporting fact table tracking daily closing values of benchmark indices.
* **Source Reference**: `10_benchmark_indices.csv`
* **Primary Key**: `(date, index_name)`

| Column Name | Data Type | Key/Constraint | Business Definition / Description |
| :--- | :--- | :--- | :--- |
| `date` | TEXT | FOREIGN KEY | REFERENCES `dim_date(date)`. Calendar date (`YYYY-MM-DD`). |
| `index_name` | TEXT | - | Name of the benchmark index (e.g. NIFTY50, NIFTY100, BSE250_SMALLCAP). |
| `close_value` | REAL | - | Daily closing value/price of the index. |
