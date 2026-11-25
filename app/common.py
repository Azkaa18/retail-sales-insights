import sys
from pathlib import Path

import plotly.io as pio
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.analysis import PALETTE, load_clean  # noqa: E402

pio.templates["earth"] = pio.templates["plotly_white"]
pio.templates["earth"].layout.colorway = PALETTE
pio.templates["earth"].layout.font = {"family": "Inter, sans-serif", "color": "#2e2a26"}
pio.templates["earth"].layout.paper_bgcolor = "rgba(0,0,0,0)"
pio.templates["earth"].layout.plot_bgcolor = "rgba(0,0,0,0)"
pio.templates.default = "earth"

CSS = """
<style>
[data-testid="stMetric"] { background:#fff; border:1px solid #e7dccb; border-radius:14px; padding:14px 16px; }
[data-testid="stMetricLabel"] p { text-transform:uppercase; letter-spacing:.06em; font-size:12px; color:#7d6f60; font-weight:600; }
[data-testid="stSidebar"] { background:#2e2a26; }
[data-testid="stMetricValue"] { font-size:26px; }
[data-testid="stSidebar"] h3, [data-testid="stSidebar"] label p, [data-testid="stSidebarNav"] span { color:#efe6d6 !important; }
h1 { letter-spacing:-.02em; }
</style>
"""


@st.cache_data(show_spinner="Loading sales data…")
def data():
    return load_clean()


def setup(title: str, icon: str = "📊"):
    st.set_page_config(page_title=f"{title} · Retail Sales Insights", page_icon=icon, layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    df = data()
    with st.sidebar:
        st.markdown("### Filters")
        stores = st.multiselect("Store", sorted(df["store"].unique()), default=sorted(df["store"].unique()))
        cats = st.multiselect("Category", sorted(df["category"].unique()), default=sorted(df["category"].unique()))
        lo, hi = df["date"].min().date(), df["date"].max().date()
        rng = st.date_input("Date range", (lo, hi), min_value=lo, max_value=hi)
    if isinstance(rng, tuple) and len(rng) == 2:
        df = df[(df["date"].dt.date >= rng[0]) & (df["date"].dt.date <= rng[1])]
    return df[df["store"].isin(stores) & df["category"].isin(cats)]


def pkr(v: float) -> str:
    if abs(v) >= 1e8:
        return f"PKR {v / 1e6:,.0f}M"
    if abs(v) >= 1e6:
        return f"PKR {v / 1e6:,.1f}M"
    return f"PKR {v:,.0f}"
