"""
Generates a realistic, reproducible retail transactions dataset (2 years, 3 stores).

Includes deliberate data-quality issues (duplicates, missing values, negative quantities
from returns, inconsistent casing) so the notebook can demonstrate cleaning.

    python data/generate_data.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
OUT = Path(__file__).parent / "sales.csv"

PRODUCTS = [
    # name, category, unit_price, unit_cost, base_daily_demand
    ("Basmati Rice 5kg", "Grocery", 2450, 2100, 6),
    ("Olive Oil 1L", "Grocery", 3200, 2750, 3),
    ("Cooking Oil 5L", "Grocery", 2900, 2500, 5),
    ("Green Tea 50 bags", "Beverages", 650, 480, 7),
    ("Mineral Water 1.5L", "Beverages", 120, 80, 25),
    ("Orange Juice 1L", "Beverages", 450, 320, 8),
    ("Soft Drink 1.5L", "Beverages", 220, 150, 18),
    ("Dark Chocolate 100g", "Snacks", 520, 390, 6),
    ("Potato Chips 150g", "Snacks", 280, 190, 14),
    ("Biscuits Family Pack", "Snacks", 350, 240, 10),
    ("Hand Wash 500ml", "Personal Care", 480, 340, 5),
    ("Toothpaste 120g", "Personal Care", 390, 260, 6),
    ("Shampoo 400ml", "Personal Care", 950, 690, 4),
    ("Notebook A5", "Stationery", 250, 140, 6),
    ("Ball Pens x10", "Stationery", 300, 180, 4),
    ("USB-C Cable 1m", "Electronics", 900, 520, 2),
    ("AA Batteries x4", "Electronics", 650, 410, 3),
    ("LED Bulb 12W", "Electronics", 550, 330, 3),
]
STORES = {"Clifton": 1.25, "Gulshan": 1.0, "DHA": 0.85}
PAYMENTS = ["cash", "card", "wallet"]

dates = pd.date_range("2024-11-01", "2026-10-31", freq="D")
n_customers = 1800
customer_ids = [f"C{10000 + i}" for i in range(n_customers)]
# Some customers shop far more often than others (Pareto-ish)
customer_weights = rng.pareto(1.6, n_customers) + 0.2
customer_weights /= customer_weights.sum()

rows = []
receipt = 100000
for day in dates:
    weekday_boost = 1.35 if day.dayofweek in (4, 5) else 1.0  # Fri/Sat
    month_season = 1 + 0.18 * np.sin((day.month - 3) / 12 * 2 * np.pi)
    ramadan_like = 1.4 if (day.month == 3 and day.year == 2025) or (day.month == 2 and day.year == 2026) else 1.0
    trend = 1 + (day - dates[0]).days / len(dates) * 0.22  # business grows ~22% over 2 years
    for store, store_factor in STORES.items():
        n_baskets = rng.poisson(38 * store_factor * weekday_boost * month_season * trend)
        for _ in range(n_baskets):
            receipt += 1
            customer = rng.choice(customer_ids, p=customer_weights) if rng.random() > 0.25 else None
            pay = rng.choice(PAYMENTS, p=[0.48 - 0.1 * (day.year - 2024) / 2, 0.32, 0.20 + 0.1 * (day.year - 2024) / 2])
            hour = int(np.clip(rng.normal(17, 3.5), 8, 23))
            n_items = rng.integers(1, 5)
            picks = rng.choice(len(PRODUCTS), size=n_items, replace=False, p=np.array([p[4] for p in PRODUCTS]) / sum(p[4] for p in PRODUCTS))
            for idx in picks:
                name, cat, price, cost, _ = PRODUCTS[idx]
                qty = int(rng.integers(1, 4))
                demand_mult = ramadan_like if cat in ("Grocery", "Beverages") else 1.0
                if rng.random() < 0.15 * (demand_mult - 1):
                    qty += 1
                discount = rng.choice([0, 0, 0, 0.05, 0.1])
                rows.append(
                    {
                        "receipt_no": f"BX-{receipt}",
                        "timestamp": day + pd.Timedelta(hours=hour, minutes=int(rng.integers(0, 60))),
                        "store": store,
                        "customer_id": customer,
                        "product": name,
                        "category": cat,
                        "quantity": qty,
                        "unit_price": price,
                        "unit_cost": cost,
                        "discount_pct": discount,
                        "payment_method": pay,
                    }
                )

df = pd.DataFrame(rows)

# --- inject realistic data-quality issues ---
returns = df.sample(frac=0.006, random_state=1).copy()
returns["quantity"] = -returns["quantity"]
returns["receipt_no"] = returns["receipt_no"] + "-R"
df = pd.concat([df, returns, df.sample(frac=0.004, random_state=2)], ignore_index=True)  # returns + duplicate rows
df.loc[df.sample(frac=0.01, random_state=3).index, "payment_method"] = np.nan
upper = df.sample(frac=0.01, random_state=4).index
df.loc[upper, "store"] = df.loc[upper, "store"].str.upper()
df = df.sort_values("timestamp").reset_index(drop=True)

df.to_csv(OUT, index=False)
print(f"Wrote {len(df):,} rows to {OUT}")
