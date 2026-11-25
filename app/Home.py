import plotly.express as px
import streamlit as st

from common import pkr, setup
from src.analysis import kpis, monthly

df = setup("Overview", "🏪")

st.title("🏪 Retail Sales Insights")
st.caption("Two years of point-of-sale transactions across three stores — cleaned, analysed and forecast.")

if df.empty:
    st.warning("No data for the selected filters.")
    st.stop()

k = kpis(df)
c = st.columns(5)
c[0].metric("Revenue", pkr(k["revenue"]))
c[1].metric("Gross profit", pkr(k["profit"]), f"{k['margin']:.1%} margin")
c[2].metric("Transactions", f"{k['transactions']:,}")
c[3].metric("Avg basket", pkr(k["avg_basket"]))
c[4].metric("Return rate", f"{k['return_rate']:.2%}")

m = monthly(df)
left, right = st.columns([2, 1])
with left:
    st.subheader("Monthly revenue & profit")
    fig = px.line(m, x="month", y=["revenue", "profit"], labels={"value": "PKR", "month": "", "variable": ""})
    fig.update_traces(line_width=3)
    fig.update_traces(selector=dict(name="revenue"), fill="tozeroy", fillcolor="rgba(194,86,47,0.15)")
    fig.update_layout(height=380, legend=dict(orientation="h", y=1.1), margin=dict(t=10, l=0, r=0))
    st.plotly_chart(fig, width="stretch")
with right:
    st.subheader("Revenue by store")
    s = df.groupby("store")["revenue"].sum().reset_index()
    fig = px.pie(s, names="store", values="revenue", hole=0.6)
    fig.update_layout(height=380, margin=dict(t=10, l=0, r=0), legend=dict(orientation="h"))
    st.plotly_chart(fig, width="stretch")

st.subheader("Key findings")
best_month = m.loc[m["revenue"].idxmax()]
growth = (m["revenue"].tail(3).mean() / m["revenue"].head(3).mean() - 1) if len(m) >= 6 else 0
top_cat = df.groupby("category")["profit"].sum().idxmax()
peak_day = df.groupby("weekday")["revenue"].sum().idxmax()
st.markdown(
    f"""
- **Growth:** revenue in the latest 3 months is **{growth:+.0%}** vs. the first 3 months.
- **Best month:** {best_month['month']:%B %Y} with {pkr(best_month['revenue'])}.
- **Most profitable category:** {top_cat}.
- **Busiest day:** {peak_day} — plan cashier shifts and stock deliveries around it.
"""
)
st.info("Use the pages in the sidebar to drill into trends, products, customers and the forecast.")
