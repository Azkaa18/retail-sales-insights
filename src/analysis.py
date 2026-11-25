"""Reusable cleaning and analysis functions shared by the notebook and the Streamlit app."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

DATA = Path(__file__).resolve().parents[1] / "data" / "sales.csv"

# Earthy palette (deliberately not the default blue).
PALETTE = ["#c2562f", "#6b7d3a", "#d9a441", "#7a3e65", "#3f6f63", "#a7754f", "#8c8c3c"]


def load_raw(path: Path | str = DATA) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():  # dataset is generated, not committed (~23 MB)
        import runpy

        runpy.run_path(str(path.parent / "generate_data.py"))
    return pd.read_csv(path, parse_dates=["timestamp"])


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Fix casing, drop exact duplicates, flag returns, fill missing payment methods, add derived columns."""
    out = df.copy()
    # Normalise casing to each store's most common spelling (e.g. "CLIFTON" -> "Clifton", keeps "DHA").
    key = out["store"].str.upper()
    canonical = out.groupby(key)["store"].agg(lambda s: s.value_counts().idxmax())
    out["store"] = key.map(canonical)
    out = out.drop_duplicates()
    out["is_return"] = out["quantity"] < 0
    out["payment_method"] = out["payment_method"].fillna("unknown")
    out["revenue"] = out["quantity"] * out["unit_price"] * (1 - out["discount_pct"])
    out["profit"] = out["revenue"] - out["quantity"] * out["unit_cost"]
    out["date"] = out["timestamp"].dt.normalize()
    out["month"] = out["timestamp"].dt.to_period("M").dt.to_timestamp()
    out["weekday"] = out["timestamp"].dt.day_name()
    out["hour"] = out["timestamp"].dt.hour
    return out


def load_clean() -> pd.DataFrame:
    return clean(load_raw())


def kpis(df: pd.DataFrame) -> dict:
    sales = df[~df["is_return"]]
    baskets = sales.groupby("receipt_no")["revenue"].sum()
    return {
        "revenue": df["revenue"].sum(),
        "profit": df["profit"].sum(),
        "margin": df["profit"].sum() / df["revenue"].sum(),
        "transactions": sales["receipt_no"].nunique(),
        "avg_basket": baskets.mean(),
        "return_rate": df["is_return"].sum() / len(df),
    }


def monthly(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("month").agg(revenue=("revenue", "sum"), profit=("profit", "sum"), orders=("receipt_no", "nunique")).reset_index()


def rfm_segments(df: pd.DataFrame, k: int = 4) -> pd.DataFrame:
    """Recency / Frequency / Monetary segmentation with K-Means."""
    known = df[df["customer_id"].notna() & ~df["is_return"]]
    snapshot = known["timestamp"].max() + pd.Timedelta(days=1)
    rfm = known.groupby("customer_id").agg(
        recency=("timestamp", lambda s: (snapshot - s.max()).days),
        frequency=("receipt_no", "nunique"),
        monetary=("revenue", "sum"),
    )
    X = StandardScaler().fit_transform(np.log1p(rfm))
    rfm["cluster"] = KMeans(n_clusters=k, n_init=10, random_state=0).fit_predict(X)

    # Name clusters by their average monetary value, highest first.
    order = rfm.groupby("cluster")["monetary"].mean().sort_values(ascending=False).index
    names = ["Champions", "Loyal", "Occasional", "At risk", "Dormant"][:k]
    rfm["segment"] = rfm["cluster"].map(dict(zip(order, names)))
    return rfm.reset_index()


def forecast_monthly(df: pd.DataFrame, horizon: int = 6) -> pd.DataFrame:
    """Linear trend + month-of-year seasonality. Simple, explainable baseline."""
    m = monthly(df)
    m["t"] = np.arange(len(m))
    m["moy"] = m["month"].dt.month
    X = pd.get_dummies(m[["t", "moy"]], columns=["moy"], drop_first=True, dtype=float)
    model = LinearRegression().fit(X, m["revenue"])
    m["fitted"] = model.predict(X)

    future = pd.DataFrame({"month": pd.date_range(m["month"].max() + pd.offsets.MonthBegin(), periods=horizon, freq="MS")})
    future["t"] = np.arange(len(m), len(m) + horizon)
    future["moy"] = future["month"].dt.month
    Xf = pd.get_dummies(future[["t", "moy"]], columns=["moy"], dtype=float).reindex(columns=X.columns, fill_value=0.0)
    future["forecast"] = model.predict(Xf)

    resid_std = (m["revenue"] - m["fitted"]).std()
    future["low"] = future["forecast"] - 1.96 * resid_std
    future["high"] = future["forecast"] + 1.96 * resid_std
    return pd.concat([m[["month", "revenue", "fitted"]], future[["month", "forecast", "low", "high"]]], ignore_index=True)


def restock_suggestions(df: pd.DataFrame, days: int = 30, cover_days: int = 14) -> pd.DataFrame:
    """Average daily units over the last `days`, and the quantity needed to cover `cover_days`."""
    recent = df[df["timestamp"] >= df["timestamp"].max() - pd.Timedelta(days=days)]
    daily = recent.groupby("product")["quantity"].sum() / days
    out = daily.rename("avg_daily_units").to_frame()
    out["units_for_cover"] = np.ceil(out["avg_daily_units"] * cover_days).astype(int)
    return out.sort_values("avg_daily_units", ascending=False).reset_index()
