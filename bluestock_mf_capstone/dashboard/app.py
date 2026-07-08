import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# 1. Page Configuration
st.set_page_config(
    page_title="Bluestock Mutual Fund Analytics Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Custom CSS Styles
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        font-size: 26px;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 20px;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 10px;
    }
    
    .card-container {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(15, 23, 42, 0.05);
        margin-bottom: 15px;
        text-align: center;
    }
    
    .card-title {
        color: #64748b;
        font-size: 13px;
        font-weight: 500;
        text-transform: uppercase;
        margin-bottom: 5px;
    }
    
    .card-value {
        color: #2563eb;
        font-size: 28px;
        font-weight: 700;
        margin: 0;
    }
</style>
""", unsafe_allow_html=True)

# Bluestock Color Palette
BLUESTOCK_COLORS = ["#0f172a", "#2563eb", "#0d9488", "#ea580c", "#e11d48", "#4f46e5", "#0891b2", "#10b981"]

# 3. Data Ingestion & Caching
from pathlib import Path
_HERE = Path(__file__).resolve().parent
DB_PATH = str(_HERE.parent / "data" / "db" / "bluestock_mf.db")


@st.cache_data
def load_db_data(query):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

@st.cache_data
def get_funds_list():
    df = load_db_data("SELECT amfi_code, scheme_name, fund_house, category, plan, expense_ratio_pct FROM dim_fund;")
    return df

@st.cache_data
def get_nav_history():
    df = load_db_data("SELECT amfi_code, date, nav FROM fact_nav;")
    df['date'] = pd.to_datetime(df['date'])
    return df

@st.cache_data
def get_benchmarks():
    df = load_db_data("SELECT date, index_name, close_value FROM fact_benchmark_indices;")
    df['date'] = pd.to_datetime(df['date'])
    return df

# Sidebar Header & Brand
st.sidebar.markdown(
    """
    <div style='text-align: center; padding: 10px 0;'>
        <h2 style='color: #2563eb; margin: 0; font-weight: 800; letter-spacing: 1px;'>BLUESTOCK</h2>
        <p style='color: #64748b; font-size: 12px; margin: 0;'>MUTUAL FUND ANALYTICS</p>
    </div>
    <hr style='margin: 10px 0 20px 0;'/>
    """,
    unsafe_allow_html=True
)

# Sidebar Navigation
query_params = st.query_params
default_page_idx = 0
if "page" in query_params:
    try:
        default_page_idx = int(query_params["page"]) - 1
        if default_page_idx < 0 or default_page_idx > 3:
            default_page_idx = 0
    except:
        pass

page = st.sidebar.radio(
    "Select Dashboard Page",
    [
        "Page 1: Industry Overview",
        "Page 2: Fund Performance",
        "Page 3: Investor Analytics",
        "Page 4: SIP & Market Trends"
    ],
    index=default_page_idx
)

# -----------------------------------------------------------------------------
# PAGE 1: INDUSTRY OVERVIEW
# -----------------------------------------------------------------------------
if page == "Page 1: Industry Overview":
    st.markdown("<div class='main-header'>Industry Overview Dashboard</div>", unsafe_allow_html=True)
    
    # Query KPIs
    # Latest AUM
    aum_df = load_db_data("SELECT SUM(aum_lakh_crore) as tot_aum FROM fact_aum WHERE date = (SELECT MAX(date) FROM fact_aum);")
    latest_aum = aum_df['tot_aum'].iloc[0] if not aum_df.empty else 81.0
    
    # Latest Monthly SIP Inflow
    sip_df = load_db_data("SELECT sip_inflow_crore FROM fact_monthly_sip_inflows WHERE month = (SELECT MAX(month) FROM fact_monthly_sip_inflows);")
    latest_sip = sip_df['sip_inflow_crore'].iloc[0] if not sip_df.empty else 31002.0 # In Cr
    
    # Latest Folio Count
    folio_df = load_db_data("SELECT total_folios_crore FROM fact_industry_folio_count WHERE month = (SELECT MAX(month) FROM fact_industry_folio_count);")
    latest_folios = folio_df['total_folios_crore'].iloc[0] if not folio_df.empty else 26.12
    
    # Industry Schemes Count
    schemes_df = load_db_data("SELECT SUM(num_schemes) as tot_schemes FROM fact_aum WHERE date = (SELECT MAX(date) FROM fact_aum);")
    latest_schemes = int(schemes_df['tot_schemes'].iloc[0]) if not schemes_df.empty else 1908
    
    # KPI Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class='card-container'>
            <div class='card-title'>Total Industry AUM</div>
            <div class='card-value'>₹{latest_aum:,.2f}L Cr</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class='card-container'>
            <div class='card-title'>Monthly SIP Inflows</div>
            <div class='card-value'>₹{latest_sip:,.0f} Cr</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class='card-container'>
            <div class='card-title'>Total Folios</div>
            <div class='card-value'>{latest_folios:,.2f} Cr</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class='card-container'>
            <div class='card-title'>Industry Schemes</div>
            <div class='card-value'>{latest_schemes:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts Row
    st.markdown("<br/>", unsafe_allow_html=True)
    chart_col1, chart_col2 = st.columns([3, 2])
    
    with chart_col1:
        st.subheader("Industry AUM Growth Trend (2022–2025)")
        # Load historical AUM trend by AMC
        df_aum_hist = load_db_data("SELECT date, fund_house, aum_lakh_crore FROM fact_aum ORDER BY date;")
        df_aum_hist['date'] = pd.to_datetime(df_aum_hist['date'])
        
        # Pivot or stack for plotting
        fig_trend = px.line(
            df_aum_hist,
            x="date",
            y="aum_lakh_crore",
            color="fund_house",
            labels={"aum_lakh_crore": "AUM (Lakh Crore)", "date": "Date", "fund_house": "AMC"},
            color_discrete_sequence=BLUESTOCK_COLORS
        )
        fig_trend.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0)
        )
        fig_trend.update_xaxes(showgrid=True, gridwidth=1, gridcolor="#f1f5f9")
        fig_trend.update_yaxes(showgrid=True, gridwidth=1, gridcolor="#f1f5f9")
        st.plotly_chart(fig_trend, use_container_width=True)
        
    with chart_col2:
        st.subheader("Latest AUM by AMC")
        # Load latest AUM by AMC
        df_aum_amc = load_db_data("""
            SELECT fund_house, SUM(aum_crore) as aum_cr 
            FROM fact_aum 
            WHERE date = (SELECT MAX(date) FROM fact_aum) 
            GROUP BY fund_house 
            ORDER BY aum_cr DESC;
        """)
        
        fig_bar = px.bar(
            df_aum_amc,
            x="aum_cr",
            y="fund_house",
            orientation="h",
            labels={"aum_cr": "AUM (Crore)", "fund_house": "AMC"},
            color_discrete_sequence=[BLUESTOCK_COLORS[1]]
        )
        fig_bar.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=10, b=0)
        )
        fig_bar.update_xaxes(showgrid=True, gridwidth=1, gridcolor="#f1f5f9")
        fig_bar.update_yaxes(showgrid=False)
        st.plotly_chart(fig_bar, use_container_width=True)

# -----------------------------------------------------------------------------
# PAGE 2: FUND PERFORMANCE
# -----------------------------------------------------------------------------
elif page == "Page 2: Fund Performance":
    st.markdown("<div class='main-header'>Fund Performance Analytics</div>", unsafe_allow_html=True)
    
    # Load base datasets
    df_funds = get_funds_list()
    df_scorecard_base = pd.read_csv(os.path.join("..", "Fund Performance Analytics", "fund_scorecard.csv"))
    df_alpha_beta = pd.read_csv(os.path.join("..", "Fund Performance Analytics", "alpha_beta.csv"))
    df_nav_hist = get_nav_history()
    df_bench = get_benchmarks()
    
    # Get risk/standard deviation from database to join
    df_risk = load_db_data("SELECT amfi_code, std_dev_ann_pct FROM fact_performance;")
    df_scorecard_full = df_scorecard_base.merge(df_risk, on="amfi_code", how="left")
    
    # Slicers in Sidebar or Top Panel
    st.sidebar.subheader("Filters (Slicers)")
    fund_houses = ["All"] + sorted(df_scorecard_full['fund_house'].unique().tolist())
    selected_house = st.sidebar.selectbox("Fund House", fund_houses)
    
    categories = ["All"] + sorted(df_scorecard_full['category'].unique().tolist())
    selected_cat = st.sidebar.selectbox("Category", categories)
    
    plans = ["All"] + sorted(df_scorecard_full['scheme_name'].apply(lambda x: "Direct" if "Direct" in x else "Regular").unique().tolist())
    selected_plan = st.sidebar.selectbox("Plan", plans)
    
    # Apply filters dynamically
    df_filtered = df_scorecard_full.copy()
    if selected_house != "All":
        df_filtered = df_filtered[df_filtered['fund_house'] == selected_house]
    if selected_cat != "All":
        df_filtered = df_filtered[df_filtered['category'] == selected_cat]
    if selected_plan != "All":
        df_filtered = df_filtered[df_filtered['scheme_name'].apply(lambda x: selected_plan in x)]
        
    # Recalculate ranks and composite scores dynamically on the filtered subset! (Mimicking RANKX in Power BI)
    if len(df_filtered) > 1:
        df_filtered['rank_3yr'] = df_filtered['return_3yr_cagr'].rank(pct=True) * 100
        df_filtered['rank_sharpe'] = df_filtered['sharpe_ratio'].rank(pct=True) * 100
        df_filtered['rank_alpha'] = df_filtered['alpha'].rank(pct=True) * 100
        df_filtered['rank_expense_inv'] = (-df_filtered['expense_ratio_pct']).rank(pct=True) * 100
        df_filtered['rank_max_dd_inv'] = df_filtered['max_drawdown'].rank(pct=True) * 100
        
        df_filtered['composite_score'] = (
            0.30 * df_filtered['rank_3yr'] +
            0.25 * df_filtered['rank_sharpe'] +
            0.20 * df_filtered['rank_alpha'] +
            0.15 * df_filtered['rank_expense_inv'] +
            0.10 * df_filtered['rank_max_dd_inv']
        )
        df_filtered['rank'] = df_filtered['composite_score'].rank(ascending=False, method='min').astype(int)
        df_filtered = df_filtered.sort_values('composite_score', ascending=False)
        
    # Layout Row 1: Scatter and Line
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Risk-Return Profile (3Yr CAGR vs Std Dev)")
        # Scatter return (X) vs risk (Y), bubble size = AUM (represented by a proxy or scorecard stats)
        # We need AUM from fact_performance
        df_aum = load_db_data("SELECT amfi_code, aum_crore FROM fact_performance;")
        df_scatter = df_filtered.merge(df_aum, on="amfi_code", how="left")
        
        fig_scatter = px.scatter(
            df_scatter,
            x="return_3Yr_cagr" if "return_3Yr_cagr" in df_scatter.columns else "return_3yr_cagr",
            y="std_dev_ann_pct",
            size="aum_crore",
            color="category",
            hover_name="scheme_name",
            labels={
                "return_3yr_cagr": "Return (3Yr CAGR %)", 
                "std_dev_ann_pct": "Risk / Volatility (Std Dev %)",
                "aum_crore": "AUM (Cr)",
                "category": "Category"
            },
            color_discrete_sequence=BLUESTOCK_COLORS
        )
        # Format X-axis as percent
        fig_scatter.update_xaxes(tickformat=".1%", showgrid=True, gridcolor="#f1f5f9")
        fig_scatter.update_yaxes(showgrid=True, gridcolor="#f1f5f9")
        fig_scatter.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=10, b=0)
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        
    with col2:
        st.subheader("NAV Chart vs Benchmark")
        # Let user select a fund from the filtered table
        funds_available = df_filtered['scheme_name'].tolist()
        if funds_available:
            selected_fund = st.selectbox("Select Fund to View NAV History", funds_available)
            selected_amfi = df_filtered[df_filtered['scheme_name'] == selected_fund]['amfi_code'].iloc[0]
            
            # Select benchmark
            benchmarks_avail = ["NIFTY100", "NIFTY50", "BSE_SMALLCAP", "NIFTY_MIDCAP150"]
            selected_bench = st.selectbox("Select Benchmark Index", benchmarks_avail)
            
            # Load NAV and Benchmark
            fund_nav = df_nav_hist[df_nav_hist['amfi_code'] == selected_amfi].sort_values('date')
            bench_close = df_bench[df_bench['index_name'] == selected_bench].sort_values('date')
            
            # Normalize to 100 on start date
            common_dates = set(fund_nav['date']).intersection(set(bench_close['date']))
            fund_nav = fund_nav[fund_nav['date'].isin(common_dates)].sort_values('date')
            bench_close = bench_close[bench_close['date'].isin(common_dates)].sort_values('date')
            
            if not fund_nav.empty and not bench_close.empty:
                fund_nav['nav_norm'] = (fund_nav['nav'] / fund_nav['nav'].iloc[0]) * 100
                bench_close['close_norm'] = (bench_close['close_value'] / bench_close['close_value'].iloc[0]) * 100
                
                fig_nav = go.Figure()
                fig_nav.add_trace(go.Scatter(
                    x=fund_nav['date'], y=fund_nav['nav_norm'],
                    name=selected_fund.split(' - ')[0],
                    line=dict(color=BLUESTOCK_COLORS[1], width=2.0)
                ))
                fig_nav.add_trace(go.Scatter(
                    x=bench_close['date'], y=bench_close['close_norm'],
                    name=selected_bench,
                    line=dict(color=BLUESTOCK_COLORS[0], width=2.0, dash='dash')
                ))
                fig_nav.update_layout(
                    title="",
                    xaxis_title="Date",
                    yaxis_title="Normalized Value (Base 100)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=0, r=0, t=10, b=0),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0)
                )
                fig_nav.update_xaxes(showgrid=True, gridcolor="#f1f5f9")
                fig_nav.update_yaxes(showgrid=True, gridcolor="#f1f5f9")
                st.plotly_chart(fig_nav, use_container_width=True)
            else:
                st.info("No overlapping dates found for NAV history.")
        else:
            st.info("No funds match the current filter selection.")
            
    # Row 2: Scorecard Table
    st.markdown("<br/>", unsafe_allow_html=True)
    st.subheader("Sortable Fund Scorecard Table")
    
    # Format percent columns
    df_display = df_filtered.copy()
    if 'return_3yr_cagr' in df_display.columns:
        df_display['return_3yr_cagr'] = df_display['return_3yr_cagr'].apply(lambda x: f"{x*100:.2f}%" if pd.notnull(x) else "")
    if 'max_drawdown' in df_display.columns:
        df_display['max_drawdown'] = df_display['max_drawdown'].apply(lambda x: f"{x*100:.2f}%" if pd.notnull(x) else "")
    if 'sharpe_ratio' in df_display.columns:
        df_display['sharpe_ratio'] = df_display['sharpe_ratio'].round(2)
    if 'alpha' in df_display.columns:
        df_display['alpha'] = df_display['alpha'].apply(lambda x: f"{x*100:.2f}%" if pd.notnull(x) else "")
    if 'composite_score' in df_display.columns:
        df_display['composite_score'] = df_display['composite_score'].round(2)
        
    table_cols = ['rank', 'scheme_name', 'fund_house', 'category', 'return_3yr_cagr', 'sharpe_ratio', 'alpha', 'expense_ratio_pct', 'max_drawdown', 'composite_score']
    st.dataframe(df_display[table_cols], hide_index=True, use_container_width=True)

# -----------------------------------------------------------------------------
# PAGE 3: INVESTOR ANALYTICS
# -----------------------------------------------------------------------------
elif page == "Page 3: Investor Analytics":
    st.markdown("<div class='main-header'>Investor Analytics Dashboard</div>", unsafe_allow_html=True)
    
    # Load raw investor transaction data
    df_tx = load_db_data("SELECT state, city_tier, age_group, transaction_type, amount_inr, transaction_date FROM fact_transactions;")
    df_tx['transaction_date'] = pd.to_datetime(df_tx['transaction_date'])
    
    # Slicers in Sidebar
    st.sidebar.subheader("Filters (Slicers)")
    states = ["All"] + sorted(df_tx['state'].dropna().unique().tolist())
    selected_state = st.sidebar.selectbox("State", states)
    
    age_groups = ["All"] + sorted(df_tx['age_group'].dropna().unique().tolist())
    selected_age = st.sidebar.selectbox("Age Group", age_groups)
    
    city_tiers = ["All"] + sorted(df_tx['city_tier'].dropna().unique().tolist())
    selected_tier = st.sidebar.selectbox("City Tier", city_tiers)
    
    # Apply filters
    df_tx_filt = df_tx.copy()
    if selected_state != "All":
        df_tx_filt = df_tx_filt[df_tx_filt['state'] == selected_state]
    if selected_age != "All":
        df_tx_filt = df_tx_filt[df_tx_filt['age_group'] == selected_age]
    if selected_tier != "All":
        df_tx_filt = df_tx_filt[df_tx_filt['city_tier'] == selected_tier]
        
    # Row 1: Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Total Transaction Amount by State")
        df_state = df_tx_filt.groupby('state')['amount_inr'].sum().reset_index().sort_values('amount_inr', ascending=False)
        fig_state = px.bar(
            df_state,
            x="state",
            y="amount_inr",
            labels={"state": "State", "amount_inr": "Total Amount (INR)"},
            color_discrete_sequence=[BLUESTOCK_COLORS[1]]
        )
        fig_state.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=10, b=0)
        )
        fig_state.update_xaxes(showgrid=False)
        fig_state.update_yaxes(showgrid=True, gridcolor="#f1f5f9")
        st.plotly_chart(fig_state, use_container_width=True)
        
    with col2:
        st.subheader("Transaction Type Distribution (SIP/Lumpsum/Redemption)")
        df_type = df_tx_filt.groupby('transaction_type')['amount_inr'].sum().reset_index()
        fig_donut = px.pie(
            df_type,
            names="transaction_type",
            values="amount_inr",
            hole=0.4,
            color_discrete_sequence=BLUESTOCK_COLORS[1:4]
        )
        fig_donut.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=10, b=0)
        )
        st.plotly_chart(fig_donut, use_container_width=True)
        
    # Row 2: Charts
    st.markdown("<br/>", unsafe_allow_html=True)
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("Age Group vs Average SIP Amount")
        df_sip_age = df_tx_filt[df_tx_filt['transaction_type'] == 'SIP'].groupby('age_group')['amount_inr'].mean().reset_index()
        fig_sip = px.bar(
            df_sip_age,
            x="age_group",
            y="amount_inr",
            labels={"age_group": "Age Group", "amount_inr": "Average SIP Amount (INR)"},
            color_discrete_sequence=[BLUESTOCK_COLORS[2]]
        )
        fig_sip.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=10, b=0)
        )
        fig_sip.update_xaxes(showgrid=False)
        fig_sip.update_yaxes(showgrid=True, gridcolor="#f1f5f9")
        st.plotly_chart(fig_sip, use_container_width=True)
        
    with col4:
        st.subheader("Monthly Transaction Volume Trend")
        df_tx_filt['month'] = df_tx_filt['transaction_date'].dt.to_period('M').astype(str)
        df_vol = df_tx_filt.groupby('month')['amount_inr'].count().reset_index()
        fig_vol = px.area(
            df_vol,
            x="month",
            y="amount_inr",
            labels={"month": "Month", "amount_inr": "Number of Transactions"},
            color_discrete_sequence=[BLUESTOCK_COLORS[5]]
        )
        fig_vol.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=10, b=0)
        )
        fig_vol.update_xaxes(showgrid=True, gridcolor="#f1f5f9")
        fig_vol.update_yaxes(showgrid=True, gridcolor="#f1f5f9")
        st.plotly_chart(fig_vol, use_container_width=True)

# -----------------------------------------------------------------------------
# PAGE 4: SIP & MARKET TRENDS
# -----------------------------------------------------------------------------
elif page == "Page 4: SIP & Market Trends":
    st.markdown("<div class='main-header'>SIP & Market Trends Dashboard</div>", unsafe_allow_html=True)
    
    # Charts Layout Row 1: Dual-Axis Chart
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.subheader("Monthly SIP Inflow vs Nifty 50 Index (2022–2025)")
        # Load SIP inflows
        df_sip_trend = load_db_data("SELECT month, sip_inflow_crore FROM fact_monthly_sip_inflows ORDER BY month;")
        
        # Load Nifty 50 daily and resample to monthly average
        df_n50 = load_db_data("SELECT date, close_value FROM fact_benchmark_indices WHERE index_name = 'NIFTY50' ORDER BY date;")
        df_n50['date'] = pd.to_datetime(df_n50['date'])
        df_n50['month'] = df_n50['date'].dt.to_period('M').astype(str)
        df_n50_monthly = df_n50.groupby('month')['close_value'].mean().reset_index()
        
        # Align
        df_aligned = df_sip_trend.merge(df_n50_monthly, on="month", how="inner")
        
        # Create dual axis plot using plotly go
        fig_dual = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Bar chart for SIP
        fig_dual.add_trace(
            go.Bar(
                x=df_aligned['month'],
                y=df_aligned['sip_inflow_crore'],
                name="SIP Inflow (Cr)",
                marker_color="#2563eb",
                opacity=0.7
            ),
            secondary_y=False
        )
        
        # Line chart for Nifty 50
        fig_dual.add_trace(
            go.Scatter(
                x=df_aligned['month'],
                y=df_aligned['close_value'],
                name="Nifty 50 (Monthly Avg)",
                line=dict(color="#0f172a", width=3.0)
            ),
            secondary_y=True
        )
        
        fig_dual.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0)
        )
        fig_dual.update_yaxes(title_text="SIP Inflow (Crore)", secondary_y=False, showgrid=True, gridcolor="#f1f5f9")
        fig_dual.update_yaxes(title_text="Nifty 50 Index Value", secondary_y=True, showgrid=False)
        fig_dual.update_xaxes(showgrid=False)
        st.plotly_chart(fig_dual, use_container_width=True)
        
    with col2:
        st.subheader("Top 5 Categories by Net Inflow (FY25)")
        # FY25 is 2024-04 to 2025-03
        fy25_months = [f"2024-{m:02d}" for m in range(4, 13)] + [f"2025-{m:02d}" for m in range(1, 4)]
        
        # Inflows by category
        df_cat_inflows = load_db_data("SELECT month, category, net_inflow_crore FROM fact_category_inflows;")
        df_fy25 = df_cat_inflows[df_cat_inflows['month'].isin(fy25_months)]
        df_top_cat = df_fy25.groupby('category')['net_inflow_crore'].sum().reset_index().sort_values('net_inflow_crore', ascending=False).head(5)
        
        fig_cat = px.bar(
            df_top_cat,
            x="net_inflow_crore",
            y="category",
            orientation="h",
            labels={"net_inflow_crore": "Net Inflow (Crore)", "category": "Category"},
            color_discrete_sequence=[BLUESTOCK_COLORS[2]]
        )
        fig_cat.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=10, b=0)
        )
        fig_cat.update_xaxes(showgrid=True, gridcolor="#f1f5f9")
        fig_cat.update_yaxes(showgrid=False)
        st.plotly_chart(fig_cat, use_container_width=True)

    # Row 2: Heatmap
    st.markdown("<br/>", unsafe_allow_html=True)
    st.subheader("Category Net Inflow Heatmap")
    
    # Pivot category inflows: index=category, columns=month, values=net_inflow_crore
    df_pivot = df_cat_inflows.pivot(index="category", columns="month", values="net_inflow_crore").fillna(0)
    
    fig_heat = px.imshow(
        df_pivot,
        labels=dict(x="Month", y="Category", color="Net Inflow (Cr)"),
        x=df_pivot.columns,
        y=df_pivot.index,
        color_continuous_scale="Viridis",
        aspect="auto"
    )
    fig_heat.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=10, b=0)
    )
    st.plotly_chart(fig_heat, use_container_width=True)
