import streamlit as st
import pandas as pd
import sqlite3
import os
import plotly.express as px
import plotly.graph_objects as go

# --- Page config ---
st.set_page_config(
    page_title="Finance Dashboard",
    page_icon="📊",
    layout="wide"
)

# --- Custom CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', sans-serif;
        background-color: #0d0d0d;
        color: #e8e8e8;
    }
    .block-container { padding: 2rem 3rem; }

    h1, h2, h3 { font-family: 'IBM Plex Mono', monospace; }

    .metric-card {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 4px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
    }
    .metric-label {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.7rem;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.3rem;
    }
    .metric-value {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1.8rem;
        font-weight: 600;
        color: #00ff88;
    }
    .metric-sub {
        font-size: 0.8rem;
        color: #666;
        margin-top: 0.2rem;
    }
    .section-header {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.75rem;
        color: #555;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        border-bottom: 1px solid #2a2a2a;
        padding-bottom: 0.5rem;
        margin: 2rem 0 1rem 0;
    }
    div[data-testid="stSelectbox"] label {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.75rem;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
</style>
""", unsafe_allow_html=True)

# --- Load data ---
@st.cache_data
def load_data():
    db_path = os.path.join(os.path.dirname(__file__), "..", "load", "financials.db")
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM financials ORDER BY company, year", conn)
    conn.close()
    return df

df = load_data()

COLORS = {
    "Amazon":    "#FF9900",
    "Apple":     "#A8B8C8",
    "Google":    "#4285F4",
    "Meta":      "#0082FB",
    "Microsoft": "#00A4EF",
}

# --- Header ---
st.markdown("# FINANCE INTELLIGENCE")
st.markdown(
    "<p style='font-family:IBM Plex Mono;font-size:0.8rem;color:#555;margin-top:-1rem;'>"
    "SEC EDGAR · 5-YEAR ANALYSIS · BIG TECH PEER GROUP</p>",
    unsafe_allow_html=True
)

# --- Filters ---
col_f1, col_f2, _ = st.columns([1, 1, 3])
with col_f1:
    companies = st.multiselect(
        "Companies",
        options=sorted(df["company"].unique()),
        default=sorted(df["company"].unique())
    )
with col_f2:
    years = st.multiselect(
        "Years",
        options=sorted(df["year"].unique()),
        default=sorted(df["year"].unique())
    )

filtered = df[df["company"].isin(companies) & df["year"].isin(years)]

# --- KPI Cards ---
st.markdown("<div class='section-header'>Snapshot · Most Recent Year</div>", unsafe_allow_html=True)

latest_year = df["year"].max()
latest = filtered[filtered["year"] == latest_year]

kpi_cols = st.columns(len(latest))
for i, (_, row) in enumerate(latest.iterrows()):
    with kpi_cols[i]:
        color = COLORS.get(row["company"], "#00ff88")
        rev = f"${row['revenue']:.0f}B" if pd.notna(row["revenue"]) else "N/A"
        margin = f"{row['net_margin_pct']:.1f}%" if pd.notna(row["net_margin_pct"]) else "N/A"
        growth = f"{row['revenue_growth_pct']:+.1f}%" if pd.notna(row["revenue_growth_pct"]) else "N/A"
        st.markdown(f"""
        <div class='metric-card' style='border-left: 3px solid {color};'>
            <div class='metric-label'>{row['company']}</div>
            <div class='metric-value' style='color:{color};font-size:1.4rem;'>{rev}</div>
            <div class='metric-sub'>Net margin: {margin} &nbsp;·&nbsp; Growth: {growth}</div>
        </div>
        """, unsafe_allow_html=True)

# --- Revenue Trend ---
st.markdown("<div class='section-header'>Revenue Trend ($ Billions)</div>", unsafe_allow_html=True)

fig_rev = go.Figure()
for company in companies:
    cdf = filtered[filtered["company"] == company].dropna(subset=["revenue"])
    fig_rev.add_trace(go.Scatter(
        x=cdf["year"], y=cdf["revenue"],
        mode="lines+markers",
        name=company,
        line=dict(color=COLORS.get(company, "#fff"), width=2),
        marker=dict(size=6),
    ))

fig_rev.update_layout(
    plot_bgcolor="#0d0d0d", paper_bgcolor="#0d0d0d",
    font=dict(family="IBM Plex Mono", color="#888", size=11),
    legend=dict(bgcolor="#0d0d0d", bordercolor="#2a2a2a", borderwidth=1),
    xaxis=dict(gridcolor="#1a1a1a", tickformat="d"),
    yaxis=dict(gridcolor="#1a1a1a", tickprefix="$", ticksuffix="B"),
    margin=dict(l=0, r=0, t=10, b=0),
    height=320,
)
st.plotly_chart(fig_rev, use_container_width=True)

# --- Margins ---
st.markdown("<div class='section-header'>Profitability Margins (%)</div>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Net Margin", "Operating Margin", "Gross Margin"])

def margin_chart(col, label):
    fig = go.Figure()
    for company in companies:
        cdf = filtered[filtered["company"] == company].dropna(subset=[col])
        fig.add_trace(go.Bar(
            x=cdf["year"], y=cdf[col],
            name=company,
            marker_color=COLORS.get(company, "#fff"),
        ))
    fig.update_layout(
        barmode="group",
        plot_bgcolor="#0d0d0d", paper_bgcolor="#0d0d0d",
        font=dict(family="IBM Plex Mono", color="#888", size=11),
        legend=dict(bgcolor="#0d0d0d", bordercolor="#2a2a2a", borderwidth=1),
        xaxis=dict(gridcolor="#1a1a1a", tickformat="d"),
        yaxis=dict(gridcolor="#1a1a1a", ticksuffix="%"),
        margin=dict(l=0, r=0, t=10, b=0),
        height=300,
    )
    st.plotly_chart(fig, use_container_width=True)

with tab1: margin_chart("net_margin_pct", "Net Margin")
with tab2: margin_chart("operating_margin_pct", "Operating Margin")
with tab3: margin_chart("gross_margin_pct", "Gross Margin")

# --- Revenue Growth & ROA side by side ---
col_l, col_r = st.columns(2)

with col_l:
    st.markdown("<div class='section-header'>Revenue Growth YoY (%)</div>", unsafe_allow_html=True)
    fig_g = go.Figure()
    for company in companies:
        cdf = filtered[filtered["company"] == company].dropna(subset=["revenue_growth_pct"])
        fig_g.add_trace(go.Scatter(
            x=cdf["year"], y=cdf["revenue_growth_pct"],
            mode="lines+markers", name=company,
            line=dict(color=COLORS.get(company, "#fff"), width=2),
            marker=dict(size=5),
        ))
    fig_g.add_hline(y=0, line_color="#333", line_dash="dot")
    fig_g.update_layout(
        plot_bgcolor="#0d0d0d", paper_bgcolor="#0d0d0d",
        font=dict(family="IBM Plex Mono", color="#888", size=11),
        legend=dict(bgcolor="#0d0d0d", bordercolor="#2a2a2a", borderwidth=1),
        xaxis=dict(gridcolor="#1a1a1a", tickformat="d"),
        yaxis=dict(gridcolor="#1a1a1a", ticksuffix="%"),
        margin=dict(l=0, r=0, t=10, b=0),
        height=280,
    )
    st.plotly_chart(fig_g, use_container_width=True)

with col_r:
    st.markdown("<div class='section-header'>Return on Assets (%)</div>", unsafe_allow_html=True)
    fig_roa = go.Figure()
    for company in companies:
        cdf = filtered[filtered["company"] == company].dropna(subset=["return_on_assets_pct"])
        fig_roa.add_trace(go.Bar(
            x=cdf["year"], y=cdf["return_on_assets_pct"],
            name=company,
            marker_color=COLORS.get(company, "#fff"),
        ))
    fig_roa.update_layout(
        barmode="group",
        plot_bgcolor="#0d0d0d", paper_bgcolor="#0d0d0d",
        font=dict(family="IBM Plex Mono", color="#888", size=11),
        legend=dict(bgcolor="#0d0d0d", bordercolor="#2a2a2a", borderwidth=1),
        xaxis=dict(gridcolor="#1a1a1a", tickformat="d"),
        yaxis=dict(gridcolor="#1a1a1a", ticksuffix="%"),
        margin=dict(l=0, r=0, t=10, b=0),
        height=280,
    )
    st.plotly_chart(fig_roa, use_container_width=True)

# --- Raw Data Table ---
st.markdown("<div class='section-header'>Raw Data</div>", unsafe_allow_html=True)
display_df = filtered.drop(columns=["id", "cik"], errors="ignore").set_index(["company", "year"])
st.dataframe(display_df.style.format({
    "revenue": "${:.1f}B",
    "gross_profit": "${:.1f}B",
    "operating_income": "${:.1f}B",
    "net_income": "${:.1f}B",
    "total_assets": "${:.1f}B",
    "total_liabilities_equity": "${:.1f}B",
    "gross_margin_pct": "{:.1f}%",
    "operating_margin_pct": "{:.1f}%",
    "net_margin_pct": "{:.1f}%",
    "revenue_growth_pct": "{:.1f}%",
    "return_on_assets_pct": "{:.1f}%",
}, na_rep="—"), use_container_width=True)

st.markdown(
    "<p style='font-family:IBM Plex Mono;font-size:0.65rem;color:#333;margin-top:3rem;'>"
    "DATA SOURCE: SEC EDGAR · BUILT WITH PYTHON, SQLITE, STREAMLIT · CHRIS</p>",
    unsafe_allow_html=True
)