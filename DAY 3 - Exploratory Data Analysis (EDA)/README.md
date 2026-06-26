# Day 3 - Exploratory Data Analysis (EDA)

This directory contains the files and outputs for the Day 3 Exploratory Data Analysis (EDA) of the BlueStock Mutual Fund Analytics project.

## Project Structure
- **[EDA_Analysis.ipynb](file:///d:/BlueStock.in/DAY%203%20-%20Exploratory%20Data%20Analysis%20(EDA)/EDA_Analysis.ipynb)**: The main Jupyter notebook containing the full analysis, code, and embedded charts.
- **[charts/](file:///d:/BlueStock.in/DAY%203%20-%20Exploratory%20Data%20Analysis%20(EDA)/charts/)**: Contains 18 high-resolution PNG exports of all the charts generated during the analysis for reports and presentations.

---

## 10 Key EDA Findings Documented in the Notebook

1. **Daily NAV Trend (Chart 1)**: All 40 schemes exhibited a clear upward trend from 2022 to 2026, driven by a prolonged bull run in 2023 and showing resilient recovery post the 2024 market correction periods.
2. **SBI AUM Leadership (Chart 2)**: SBI Mutual Fund displays absolute market leadership, growing its AUM from ₹6.05 Lakh Cr in March 2022 to a dominant ₹12.5 Lakh Cr by December 2025.
3. **Retail SIP Inflow Peaks (Chart 3)**: Monthly Systematic Investment Plan (SIP) inflows grew consistently across the industry, marking an all-time high of ₹31,002 Cr in December 2025, which underscores accelerating retail investor participation.
4. **Category Inflow Dynamics (Chart 4)**: Flexi Cap, Mid Cap, and Large & Mid Cap categories received robust and continuous net inflows between April 2024 and March 2025, demonstrating strong investor preference for diversified equity exposure.
5. **Investor Demographics (Chart 5)**: Unique investor analysis shows that 42.1% of mutual fund participants belong to the 26-35 age group, followed by 28.3% in the 36-45 age group, confirming that young-to-mid career working professionals form the core investor base.
6. **SIP Sizes by Age (Chart 6)**: While younger investors (18-25) dominate by count, the median SIP amount increases significantly with older age brackets (reaching its highest in the 46-55 and 56+ cohorts), reflecting greater investible surpluses in peak-earning years.
7. **SIP State Inflow Distributions (Chart 8)**: Geographic distribution of SIPs reveals Madhya Pradesh, Punjab, and Telangana as the leading states by total SIP transaction amounts in our database.
8. **T30 vs B30 Market Concentration (Chart 9)**: Top 30 (T30) cities represent 66.7% of total SIP investments, while Beyond Top 30 (B30) cities make up a substantial 33.3%, indicating a solid retail footprint in semi-urban and rural regions.
9. **Asset Class Correlations (Chart 11)**: Pairwise daily return analysis highlights strong correlation (coefficients 0.85 to 0.95) among equity funds, whereas correlations with debt funds (Kotak Liquid, SBI Gilt) are near zero (-0.05 to 0.05), validating the asset allocation benefit of hybrid portfolios.
10. **Equity Sector Concentration (Chart 12)**: Sector allocation donut chart analysis shows that the Banking (19.2%), IT (13.4%), and Pharma (12.0%) sectors constitute over 44% of total equity holdings on average, reflecting high exposure to these core growth sectors.

---

## Technical Specifications
The analysis queries the SQLite database (`bluestock_mf.db`) located in the Day 2 folder. It utilizes:
- **Plotly** for interactive time-series plots.
- **Seaborn & Matplotlib** for statistical and static report charts.
- **nbconvert** to automate execution and ensure all cells are pre-rendered.

### How to Run the Notebook
To run the notebook or view the interactive charts locally, ensure you have the required packages installed and execute:
```bash
pip install pandas numpy matplotlib seaborn plotly jupyter
jupyter notebook EDA_Analysis.ipynb
```
