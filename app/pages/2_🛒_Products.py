import plotly.express as px
import streamlit as st

from common import pkr, setup
from src.analysis import restock_suggestions

df = setup("Products", "🛒")
st.title("🛒 Products & categories")

if df.empty:
    st.warning("No data for the selected filters.")
    st.stop()

prod = (
    df.groupby(["product", "category"])
    .agg(units=("quantity", "sum"), revenue=("revenue", "sum"), profit=("profit", "sum"))
    .reset_index()
)
prod["margin"] = prod["profit"] / prod["revenue"]

c1, c2 = st.columns([3, 2])
with c1:
    st.subheader("Revenue vs margin")
    fig = px.scatter(prod, x="revenue", y="margin", size="units", color="category", hover_name="product", size_max=48, labels={"revenue": "Revenue (PKR)", "margin": "Margin"})
    fig.update_layout(height=420, yaxis_tickformat=".0%", margin=dict(t=10, l=0, r=0))
    st.plotly_chart(fig, width="stretch")
    st.caption("Top-right = high revenue and high margin — protect stock levels for these items.")
with c2:
    st.subheader("Category share of profit")
    cat = prod.groupby("category")["profit"].sum().reset_index()
    fig = px.treemap(cat, path=["category"], values="profit", color="category")
    fig.update_layout(height=420, margin=dict(t=10, l=0, r=0))
    st.plotly_chart(fig, width="stretch")

st.subheader("Product league table")
st.dataframe(
    prod.sort_values("revenue", ascending=False).style.format({"revenue": "{:,.0f}", "profit": "{:,.0f}", "margin": "{:.1%}", "units": "{:,}"}),
    width="stretch",
    hide_index=True,
)

st.subheader("Restock planner")
cover = st.slider("Days of stock to cover", 7, 45, 14)
st.dataframe(restock_suggestions(df, cover_days=cover).style.format({"avg_daily_units": "{:.1f}"}), width="stretch", hide_index=True)
st.caption(f"Based on average daily units over the last 30 days in the selection. Revenue in view: {pkr(prod['revenue'].sum())}.")
