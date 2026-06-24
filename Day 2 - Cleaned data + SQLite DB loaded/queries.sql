-- queries.sql
-- 10 Analytical SQL Queries for Mutual Fund Analytics SQLite Database
-- Day 2: Cleaned data + SQLite DB loaded

--------------------------------------------------------------------------------
-- 1. Top 5 Funds by Assets Under Management (AUM)
-- Purpose: Identifies the largest schemes in terms of capital size.
--------------------------------------------------------------------------------
SELECT 
    amfi_code,
    scheme_name,
    fund_house,
    category,
    aum_crore
FROM fact_performance
ORDER BY aum_crore DESC
LIMIT 5;

--------------------------------------------------------------------------------
-- 2. Average Net Asset Value (NAV) per Month
-- Purpose: Calculates the average NAV for each scheme on a monthly basis to track trends.
--------------------------------------------------------------------------------
SELECT 
    amfi_code,
    STRFTIME('%Y-%m', date) AS month,
    ROUND(AVG(nav), 4) AS average_nav,
    COUNT(date) AS days_in_month
FROM fact_nav
GROUP BY amfi_code, month
ORDER BY amfi_code, month;

--------------------------------------------------------------------------------
-- 3. SIP Year-over-Year (YoY) Growth (Calculated dynamically)
-- Purpose: Computes YoY growth of monthly SIP inflows by joining the table with itself 
--          offsetting by exactly 1 year (12 months).
--------------------------------------------------------------------------------
SELECT 
    current.month AS current_month,
    current.sip_inflow_crore AS current_inflow_cr,
    previous.month AS previous_year_month,
    previous.sip_inflow_crore AS previous_inflow_cr,
    ROUND(((current.sip_inflow_crore - previous.sip_inflow_crore) * 100.0 / previous.sip_inflow_crore), 2) AS calculated_yoy_growth_pct,
    current.yoy_growth_pct AS recorded_yoy_growth_pct
FROM fact_monthly_sip_inflows current
JOIN fact_monthly_sip_inflows previous 
    ON CAST(STRFTIME('%Y', current.month || '-01') AS INTEGER) = CAST(STRFTIME('%Y', previous.month || '-01') AS INTEGER) + 1
    AND STRFTIME('%m', current.month || '-01') = STRFTIME('%m', previous.month || '-01')
ORDER BY current_month;

--------------------------------------------------------------------------------
-- 4. Transactions by State
-- Purpose: Ranks states based on transaction volume (count) and total amount invested.
--------------------------------------------------------------------------------
SELECT 
    state,
    COUNT(transaction_id) AS transaction_count,
    ROUND(SUM(amount_inr), 2) AS total_investment_inr,
    ROUND(AVG(amount_inr), 2) AS avg_transaction_size_inr
FROM fact_transactions
GROUP BY state
ORDER BY total_investment_inr DESC;

--------------------------------------------------------------------------------
-- 5. Funds with Expense Ratio < 1%
-- Purpose: Finds low-cost (often direct plan) mutual funds with an expense ratio below 1%.
--------------------------------------------------------------------------------
SELECT 
    amfi_code,
    scheme_name,
    category,
    plan,
    expense_ratio_pct
FROM fact_performance
WHERE expense_ratio_pct < 1.0
ORDER BY expense_ratio_pct ASC;

--------------------------------------------------------------------------------
-- 6. Transaction Type Distribution
-- Purpose: Shows the counts, total value, and proportions of transaction types (SIP vs. Lumpsum vs. Redemption).
--------------------------------------------------------------------------------
SELECT 
    transaction_type,
    COUNT(transaction_id) AS transaction_count,
    ROUND(SUM(amount_inr), 2) AS total_amount_inr,
    ROUND(AVG(amount_inr), 2) AS average_amount_inr,
    ROUND((COUNT(transaction_id) * 100.0 / (SELECT COUNT(*) FROM fact_transactions)), 2) AS percentage_share_by_count
FROM fact_transactions
GROUP BY transaction_type
ORDER BY total_amount_inr DESC;

--------------------------------------------------------------------------------
-- 7. Top 5 Schemes with the Highest 5-Year Return
-- Purpose: Identifies the best-performing funds based on long-term 5-year annualized returns.
--------------------------------------------------------------------------------
SELECT 
    amfi_code,
    scheme_name,
    category,
    return_5yr_pct,
    risk_grade
FROM fact_performance
WHERE return_5yr_pct IS NOT NULL
ORDER BY return_5yr_pct DESC
LIMIT 5;

--------------------------------------------------------------------------------
-- 8. Average Returns and Expense Ratios Grouped by Risk Grade
-- Purpose: Examines if higher risk grades correlate with higher average returns (risk-reward profile) 
--          and how expense ratios vary across risk categories.
--------------------------------------------------------------------------------
SELECT 
    risk_grade,
    COUNT(amfi_code) AS fund_count,
    ROUND(AVG(return_1yr_pct), 2) AS avg_return_1yr,
    ROUND(AVG(return_3yr_pct), 2) AS avg_return_3yr,
    ROUND(AVG(return_5yr_pct), 2) AS avg_return_5yr,
    ROUND(AVG(expense_ratio_pct), 2) AS avg_expense_ratio_pct
FROM fact_performance
GROUP BY risk_grade
ORDER BY avg_return_3yr DESC;

--------------------------------------------------------------------------------
-- 9. Top 5 Sectors by Total Portfolio Market Value
-- Purpose: Determines the sectors with the highest allocation across all portfolios, 
--          representing overall market exposure.
--------------------------------------------------------------------------------
SELECT 
    sector,
    ROUND(SUM(market_value_cr), 2) AS total_market_value_cr,
    COUNT(DISTINCT stock_symbol) AS unique_stocks_held,
    COUNT(DISTINCT amfi_code) AS funds_holding_sector
FROM fact_portfolio_holdings
GROUP BY sector
ORDER BY total_market_value_cr DESC
LIMIT 5;

--------------------------------------------------------------------------------
-- 10. NAV Tracking vs. NIFTY50 Index values
-- Purpose: Aligns the daily NAV of SBI Bluechip Fund (AMFI: 119551) with the NIFTY50 
--          close values to facilitate tracking correlation and performance comparison.
--          Filters to show a sample of the first 15 days.
--------------------------------------------------------------------------------
SELECT 
    n.date,
    f.scheme_name,
    n.nav AS fund_nav,
    idx.close_value AS nifty50_close_value
FROM fact_nav n
JOIN dim_fund f ON n.amfi_code = f.amfi_code
JOIN fact_benchmark_indices idx ON n.date = idx.date
WHERE n.amfi_code = 119551 
  AND idx.index_name = 'NIFTY50'
ORDER BY n.date ASC
LIMIT 15;
