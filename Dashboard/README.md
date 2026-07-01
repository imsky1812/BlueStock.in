# Power BI Dashboard Implementation Blueprint

This guide provides the complete documentation to implement the **Bluestock Mutual Fund Analytics Dashboard** in Microsoft Power BI.

---

## 1. Project Files Directory
- **[bluestock_theme.json](file:///d:/BlueStock.in/Dashboard/bluestock_theme.json)**: Custom corporate theme JSON.
- **[dax_measures.txt](file:///d:/BlueStock.in/Dashboard/dax_measures.txt)**: List of all custom calculations and measures.

---

## 2. Step 1: Ingest Data (CSVs)
Open Power BI Desktop, click **Get Data > Text/CSV**, and import the following 8 cleaned CSV files located in `d:\BlueStock.in\Day 2 - Cleaned data + SQLite DB loaded\data\processed`:
1. `01_fund_master.csv` (Rename table to **`dim_fund`**)
2. `dim_date.csv` (Rename table to **`dim_date`**)
3. `02_nav_history.csv` (Rename table to **`fact_nav`**)
4. `08_investor_transactions.csv` (Rename table to **`fact_transactions`**)
5. `09_portfolio_holdings.csv` (Rename table to **`fact_portfolio_holdings`**)
6. `03_aum_by_fund_house.csv` (Rename table to **`fact_aum`**)
7. `04_monthly_sip_inflows.csv` (Rename table to **`fact_monthly_sip_inflows`**)
8. `06_industry_folio_count.csv` (Rename table to **`fact_industry_folio_count`**)
9. `10_benchmark_indices.csv` (Rename table to **`fact_benchmark_indices`**)

Click **Load** to load the tables into the semantic model.

---

## 3. Step 2: Establish Schema Relationships (Model View)
Navigate to the **Model View** on the left panel. Organize the tables into a **Star Schema** with the dimensions surrounding the facts:

### Mappings:
1. **`fact_nav` <-> `dim_fund`**:
   - Field: `amfi_code`
   - Multiplicity: Many-to-One (`* : 1`)
   - Cross filter direction: **Single** (dim_fund filters fact_nav)
   - Status: **Active**

2. **`fact_nav` <-> `dim_date`**:
   - Field: `date` (format: YYYY-MM-DD)
   - Multiplicity: Many-to-One (`* : 1`)
   - Cross filter direction: **Single**
   - Status: **Active**

3. **`fact_transactions` <-> `dim_fund`**:
   - Field: `amfi_code`
   - Multiplicity: Many-to-One (`* : 1`)
   - Cross filter direction: **Single**
   - Status: **Active**

4. **`fact_transactions` <-> `dim_date`**:
   - Field: `transaction_date` in `fact_transactions` to `date` in `dim_date`
   - Multiplicity: Many-to-One (`* : 1`)
   - Cross filter direction: **Single**
   - Status: **Active**

5. **`fact_benchmark_indices` <-> `dim_date`**:
   - Field: `date`
   - Multiplicity: Many-to-One (`* : 1`)
   - Cross filter direction: **Single**
   - Status: **Active**

6. **`fact_portfolio_holdings` <-> `dim_fund`**:
   - Field: `amfi_code`
   - Multiplicity: Many-to-One (`* : 1`)
   - Cross filter direction: **Single**

7. **`fact_portfolio_holdings` <-> `dim_date`**:
   - Field: `portfolio_date` in `fact_portfolio_holdings` to `date` in `dim_date`
   - Multiplicity: Many-to-One (`* : 1`)
   - Cross filter direction: **Single**

---

## 4. Step 3: Apply Custom Theme
1. Go to the **View** tab in the top menu bar.
2. In the **Themes** dropdown, click **Browse for themes**.
3. Select **`bluestock_theme.json`** from the `d:\BlueStock.in\Dashboard` folder.
This will load the Bluestock color palette and apply visual borders, curved corners (8px), and drop shadows to all visual elements.

---

## 5. Step 4: Create DAX Measures
Open the **Data View**, right-click any table, and select **New Measure**. Copy and paste the DAX formulas from **`dax_measures.txt`** into the formula bar.

---

## 6. Step 5: Design Pages

### Page 1: Industry Overview
- **Visuals Layout:**
  - **Header:** Title text block "Bluestock Mutual Fund Analytics - Industry Overview" + Bluestock Logo.
  - **Row 1: KPI Cards** (4 separate Card visuals):
    1. **Total AUM**: Value: `[Latest_Industry_AUM_Lakh_Cr]` (Display unit: Lakh Crore)
    2. **Monthly SIP Inflow**: Value: `[Latest_SIP_Inflow_Cr]` (Display unit: Crore)
    3. **Total Folios**: Value: `[Latest_Total_Folios_Cr]` (Display unit: Crore)
    4. **Active Schemes**: Value: `[Total_Schemes]`
  - **Row 2: Left Visual - Industry AUM Trend (Line Chart)**:
    - X-Axis: `dim_date[date]` (Year/Month hierarchy)
    - Y-Axis: `fact_aum[aum_lakh_crore]`
    - Legend: `fact_aum[fund_house]` (Displays share of AUM over time)
  - **Row 2: Right Visual - AUM by Asset Management Company (Clustered Bar Chart)**:
    - Y-Axis: `fact_aum[fund_house]`
    - X-Axis: `fact_aum[aum_crore]`
    - Sorted by: `aum_crore` in descending order

### Page 2: Fund Performance
- **Visuals Layout:**
  - **Top Row Slicers** (3 Slicer visuals in horizontal layout):
    - Slicer 1: `dim_fund[fund_house]`
    - Slicer 2: `dim_fund[category]`
    - Slicer 3: `dim_fund[plan]` (Direct vs Regular)
  - **Middle Row: Left Visual - Risk-Return Profile (Scatter Plot / Bubble Chart)**:
    - X-Axis: `[Return_3Yr_CAGR]`
    - Y-Axis: `[Annualized_Volatility]`
    - Details: `dim_fund[scheme_name]`
    - Legend: `dim_fund[category]`
    - Size: `fact_performance[aum_crore]`
  - **Middle Row: Right Visual - NAV vs Benchmark (Line Chart)**:
    - X-Axis: `dim_date[date]`
    - Y-Axis: `fact_nav[nav]` (Average) vs `fact_benchmark_indices[close_value]` (Normalized values or dual axis)
  - **Bottom Row: Scorecard Table (Table Visual)**:
    - Columns: `[Scorecard_Rank]`, `dim_fund[scheme_name]`, `[Return_3Yr_CAGR]`, `[Sharpe_Ratio]`, `[Sortino_Ratio]`, `dim_fund[expense_ratio_pct]`, `[Max_Drawdown]`, `[Composite_Score]`
    - Sort: Sort by `Scorecard_Rank` ascending (or `Composite_Score` descending).

### Page 3: Investor Analytics
- **Visuals Layout:**
  - **Top Row Slicers:** State, Age Group, City Tier.
  - **Row 1: Left Visual - Transaction Value by State (Clustered Column Chart)**:
    - X-Axis: `fact_transactions[state]`
    - Y-Axis: `fact_transactions[amount_inr]` (Sum)
    - Sorted by: `amount_inr` descending
  - **Row 1: Right Visual - Transaction Type Split (Donut Chart)**:
    - Legend: `fact_transactions[transaction_type]` (SIP vs Lumpsum vs Redemption)
    - Values: `fact_transactions[amount_inr]` (Sum)
  - **Row 2: Left Visual - Avg SIP Size by Age Group (Clustered Column Chart)**:
    - X-Axis: `fact_transactions[age_group]`
    - Y-Axis: `fact_transactions[amount_inr]` (Average)
    - Filter applied to visual: `fact_transactions[transaction_type] = "SIP"`
  - **Row 2: Right Visual - Monthly Transaction Volume (Area / Line Chart)**:
    - X-Axis: `dim_date[date]` (Year/Month)
    - Y-Axis: `COUNT(fact_transactions[transaction_id])`

### Page 4: SIP & Market Trends
- **Visuals Layout:**
  - **Row 1: Dual-Axis Chart - SIP Inflow vs Nifty 50 Close (Line and Stacked Column Chart)**:
    - Shared X-Axis: `dim_date[date]` (Year/Month)
    - Column Y-Axis: `fact_monthly_sip_inflows[sip_inflow_crore]`
    - Line Y-Axis: `fact_benchmark_indices[close_value]` (Filtered where `index_name = "NIFTY50"`)
  - **Row 2: Left Visual - Category Inflow Heatmap / Matrix**:
    - Rows: `fact_category_inflows[category]`
    - Columns: `fact_category_inflows[month]`
    - Values: `fact_category_inflows[net_inflow_crore]`
    - Conditional Formatting: Background color scale enabled to display inflow heat.
  - **Row 2: Right Visual - Top 5 Categories by Inflow FY25 (Horizontal Bar Chart)**:
    - Y-Axis: `fact_category_inflows[category]`
    - X-Axis: `fact_category_inflows[net_inflow_crore]` (Filtered to show Top 5 by Sum, date range: FY25).

---

## 7. Step 6: Add Interactivity & Navigation
1. **Drill-through Page:**
   - Create a new blank page named **`NAV Detail`**.
   - Add a line chart of daily NAVs (`fact_nav[nav]` by `dim_date[date]`).
   - In the **Drill-through** field panel on this page, drag `dim_fund[scheme_name]`.
   - Now, users can right-click any fund row in the Page 2 Scorecard Table and select **Drill-through > NAV Detail** to view its NAV chart.
2. **Tooltips:**
   - Verify that default tooltips are enabled on all scatter plots, bar charts, and line graphs.
   - For the scatter plot, ensure tooltips display the AUM, exact CAGR, Volatility, and Sharpe ratio of the selected bubble.
