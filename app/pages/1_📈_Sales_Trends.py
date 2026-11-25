import plotly.express as px
import streamlit as st

from common import setup

df = setup("Sales Trends", "📈")
st.title("📈 Sales trends")

if df.empty:
    st.warning("No data for the selected filters.")
    st.stop()

daily = df.groupby("date")["revenue"].sum().reset_index()
daily["7-day average"] = daily["revenue"].rolling(7).mean()
st.subheader("Daily revenue")
fig = px.line(daily, x="date", y=["revenue", "7-day average"], labels={"value": "PKR", "date": "", "variable": ""})
fig.update_traces(selector=dict(name="revenue"), opacity=0.35)
fig.update_layout(height=360, legend=dict(orientation="h", y=1.1), margin=dict(t=10, l=0, r=0))
st.plotly_chart(fig, width="stretch")

c1, c2 = st.columns(2)
with c1:
    st.subheader("When do customers shop?")
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    heat = df.pivot_table(index="weekday", columns="hour", values="receipt_no", aggfunc="nunique").reindex(order)
    fig = px.imshow(heat, color_continuous_scale=["#faf6ef", "#d9a441", "#c2562f", "#7a3e65"], aspect="auto", labels=dict(color="Orders"))
    fig.update_layout(height=360, margin=dict(t=10, l=0, r=0))
    st.plotly_chart(fig, width="stretch")
with c2:
    st.subheader("Payment method mix over time")
    pay = df.groupby(["month", "payment_method"])["revenue"].sum().reset_index()
    pay["share"] = pay["revenue"] / pay.groupby("month")["revenue"].transform("sum")
    fig = px.area(pay, x="month", y="share", color="payment_method", labels={"share": "Share", "month": ""})
    fig.update_layout(height=360, yaxis_tickformat=".0%", legend=dict(orientation="h", y=1.12), margin=dict(t=10, l=0, r=0))
    st.plotly_chart(fig, width="stretch")

st.subheader("Store performance by month")
sm = df.groupby(["month", "store"])["revenue"].sum().reset_index()
fig = px.bar(sm, x="month", y="revenue", color="store", barmode="group", labels={"revenue": "PKR", "month": ""})
fig.update_layout(height=340, legend=dict(orientation="h", y=1.12), margin=dict(t=10, l=0, r=0))
st.plotly_chart(fig, width="stretch")
