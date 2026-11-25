import plotly.graph_objects as go
import streamlit as st

from common import pkr, setup
from src.analysis import PALETTE, forecast_monthly

df = setup("Forecast", "🔮")
st.title("🔮 Revenue forecast")
st.caption("Baseline model: linear trend + month-of-year seasonality (scikit-learn LinearRegression), with a 95% band from residual spread.")

horizon = st.slider("Months ahead", 3, 12, 6)
if df["month"].nunique() < 13:
    st.warning("Select at least 13 months of data so the model can learn seasonality.")
    st.stop()

f = forecast_monthly(df, horizon)
hist = f[f["revenue"].notna()]
fut = f[f["forecast"].notna()]

fig = go.Figure()
fig.add_trace(go.Scatter(x=fut["month"], y=fut["high"], mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip"))
fig.add_trace(go.Scatter(x=fut["month"], y=fut["low"], mode="lines", fill="tonexty", fillcolor="rgba(217,164,65,0.25)", line=dict(width=0), name="95% band"))
fig.add_trace(go.Scatter(x=hist["month"], y=hist["revenue"], name="Actual", line=dict(color=PALETTE[0], width=3)))
fig.add_trace(go.Scatter(x=hist["month"], y=hist["fitted"], name="Model fit", line=dict(color=PALETTE[1], dash="dot")))
bridge_x = [hist["month"].iloc[-1], *fut["month"]]
bridge_y = [hist["revenue"].iloc[-1], *fut["forecast"]]
fig.add_trace(go.Scatter(x=bridge_x, y=bridge_y, name="Forecast", line=dict(color=PALETTE[3], width=3)))
fig.update_layout(height=460, legend=dict(orientation="h", y=1.1), margin=dict(t=10, l=0, r=0), yaxis_title="PKR")
st.plotly_chart(fig, width="stretch")

mape = (abs(hist["revenue"] - hist["fitted"]) / hist["revenue"]).mean()
c = st.columns(3)
c[0].metric("In-sample MAPE", f"{mape:.1%}")
c[1].metric(f"Next {horizon} months (forecast)", pkr(fut["forecast"].sum()))
c[2].metric("Same period last year", pkr(hist["revenue"].tail(12).head(horizon).sum()))

st.subheader("Forecast table")
st.dataframe(
    fut.assign(month=fut["month"].dt.strftime("%b %Y"))[["month", "low", "forecast", "high"]].style.format({"low": "{:,.0f}", "forecast": "{:,.0f}", "high": "{:,.0f}"}),
    hide_index=True,
    width="stretch",
)
st.caption("Next steps: try Prophet / SARIMA and a holdout back-test; add promotions and holidays as regressors.")
