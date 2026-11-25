import plotly.express as px
import streamlit as st

from common import pkr, setup
from src.analysis import rfm_segments

df = setup("Customers", "👥")
st.title("👥 Customer segments (RFM + K-Means)")
st.caption("Recency = days since last visit · Frequency = number of visits · Monetary = total spend. Walk-in sales without a loyalty ID are excluded.")

if df["customer_id"].notna().sum() < 50:
    st.warning("Not enough identified customers in this selection.")
    st.stop()

rfm = rfm_segments(df)
seg = rfm.groupby("segment").agg(customers=("customer_id", "count"), recency=("recency", "mean"), frequency=("frequency", "mean"), monetary=("monetary", "sum")).reset_index()
seg["share_of_revenue"] = seg["monetary"] / seg["monetary"].sum()

cols = st.columns(len(seg))
for col, (_, r) in zip(cols, seg.sort_values("monetary", ascending=False).iterrows()):
    col.metric(f"{r['segment']} · customers", f"{r['customers']:,}", f"{r['share_of_revenue']:.0%} of revenue")

c1, c2 = st.columns([3, 2])
with c1:
    st.subheader("Segments in RFM space")
    fig = px.scatter(rfm, x="recency", y="frequency", size="monetary", color="segment", log_y=True, size_max=30, opacity=0.7, labels={"recency": "Days since last visit", "frequency": "Visits"})
    fig.update_layout(height=430, margin=dict(t=10, l=0, r=0))
    st.plotly_chart(fig, width="stretch")
with c2:
    st.subheader("Concentration of revenue")
    top = rfm.sort_values("monetary", ascending=False)
    top["cum_share"] = top["monetary"].cumsum() / top["monetary"].sum()
    top["customer_pct"] = range(1, len(top) + 1)
    top["customer_pct"] = top["customer_pct"] / len(top)
    fig = px.line(top, x="customer_pct", y="cum_share", labels={"customer_pct": "Share of customers", "cum_share": "Share of revenue"})
    fig.update_layout(height=430, xaxis_tickformat=".0%", yaxis_tickformat=".0%", margin=dict(t=10, l=0, r=0))
    st.plotly_chart(fig, width="stretch")
    p20 = top.loc[top["customer_pct"] <= 0.2, "monetary"].sum() / top["monetary"].sum()
    st.markdown(f"The top **20%** of loyalty customers generate **{p20:.0%}** of identified revenue.")

st.subheader("Suggested actions")
st.markdown(
    """
| Segment | Action |
|---|---|
| **Champions** | Early access to promotions, VIP loyalty tier |
| **Loyal** | Bundle offers on their favourite categories |
| **Occasional** | Weekend discount SMS to increase visit frequency |
| **At risk** | “We miss you” voucher — they haven’t visited recently |
"""
)
st.dataframe(seg.style.format({"recency": "{:.0f} days", "frequency": "{:.1f}", "monetary": "{:,.0f}", "share_of_revenue": "{:.1%}"}), hide_index=True, width="stretch")
st.caption(f"Total identified revenue: {pkr(seg['monetary'].sum())}")
