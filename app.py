import io
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.pipeline import clean_logistics_data, build_risk_summary, load_to_sqlite

st.set_page_config(page_title="Logistics Intelligence", page_icon="📦", layout="wide")
st.title("📦 Logistics Intelligence & Delivery Risk")
st.caption("Explore shipment performance, delivery delays, and operational risk.")

DB_PATH = Path("data/processed/logistics.db")
DEFAULT_CSV = Path("data/raw/DataCoSupplyChainDataset.csv")

def load_source(uploaded_file):
    if uploaded_file is not None:
        return pd.read_csv(uploaded_file, encoding_errors="replace", low_memory=False)
    if DEFAULT_CSV.exists():
        return pd.read_csv(DEFAULT_CSV, encoding_errors="replace", low_memory=False)
    return None

uploaded = st.sidebar.file_uploader("Upload logistics CSV", type=["csv"])
st.sidebar.markdown("**Or** place `DataCoSupplyChainDataset.csv` in `data/raw/`.")
st.sidebar.info("The app supports the DataCo Smart Supply Chain dataset and CSVs with equivalent columns.")

try:
    raw = load_source(uploaded)
except Exception as exc:
    st.error(f"Could not read the CSV: {exc}")
    st.stop()

if raw is None:
    st.info("Upload your logistics CSV to begin. The dashboard will clean the data, save a SQLite snapshot, and show delivery-risk metrics.")
    st.markdown("""
    **Expected useful columns** (names can vary slightly):
    - `Late_delivery_risk` or `Delivery Status`
    - `Days for shipping (real)` and `Days for shipment (scheduled)`
    - `Order Region`, `Shipping Mode`, `Sales`, `Order Item Quantity`
    """)
    st.stop()

with st.spinner("Cleaning data and preparing dashboard..."):
    cleaned, quality = clean_logistics_data(raw)
    risk = build_risk_summary(cleaned)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    load_to_sqlite(cleaned, DB_PATH)

st.sidebar.success(f"Loaded {len(raw):,} rows")
st.sidebar.caption(f"After cleaning: {len(cleaned):,} rows")

def first_existing(df, candidates):
    return next((c for c in candidates if c in df.columns), None)

risk_col = first_existing(cleaned, ["Late_delivery_risk", "late_delivery_risk", "late_delivery"])
status_col = first_existing(cleaned, ["Delivery Status", "delivery_status"])
actual_days = first_existing(cleaned, ["Days for shipping (real)", "days_for_shipping_real"])
scheduled_days = first_existing(cleaned, ["Days for shipment (scheduled)", "days_for_shipment_scheduled"])
sales_col = first_existing(cleaned, ["Sales", "sales", "Order Item Total", "Order Item Product Price"])
region_col = first_existing(cleaned, ["Order Region", "Order Country", "Market", "Region"])
shipping_col = first_existing(cleaned, ["Shipping Mode", "shipping_mode"])
quantity_col = first_existing(cleaned, ["Order Item Quantity", "quantity"])

late_rate = float(cleaned[risk_col].mean() * 100) if risk_col else None
avg_delay = None
if actual_days and scheduled_days:
    delay = pd.to_numeric(cleaned[actual_days], errors="coerce") - pd.to_numeric(cleaned[scheduled_days], errors="coerce")
    avg_delay = float(delay.mean())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Shipments", f"{len(cleaned):,}")
c2.metric("Late-risk rate", f"{late_rate:.1f}%" if late_rate is not None else "Not available")
c3.metric("Avg. days vs schedule", f"{avg_delay:+.2f}" if avg_delay is not None else "Not available")
c4.metric("Columns available", f"{cleaned.shape[1]}")

if risk_col:
    st.subheader("Delivery risk distribution")
    risk_counts = cleaned[risk_col].map({0: "On-time / lower risk", 1: "Late risk"}).fillna("Unknown").value_counts().rename_axis("Risk").reset_index(name="Shipments")
    st.plotly_chart(px.pie(risk_counts, names="Risk", values="Shipments", hole=0.45), use_container_width=True)
else:
    st.warning("No recognized late-delivery-risk column was found. Upload a dataset with `Late_delivery_risk` or `Delivery Status` to view risk charts.")

left, right = st.columns(2)
with left:
    st.subheader("Shipments by region")
    if region_col:
        region_data = cleaned[region_col].fillna("Unknown").value_counts().head(12).rename_axis("Region").reset_index(name="Shipments")
        st.plotly_chart(px.bar(region_data, x="Shipments", y="Region", orientation="h"), use_container_width=True)
    else:
        st.info("No region-like column found.")
with right:
    st.subheader("Shipping mode mix")
    if shipping_col:
        mode_data = cleaned[shipping_col].fillna("Unknown").value_counts().rename_axis("Shipping Mode").reset_index(name="Shipments")
        st.plotly_chart(px.bar(mode_data, x="Shipping Mode", y="Shipments"), use_container_width=True)
    else:
        st.info("No shipping-mode column found.")

if actual_days and scheduled_days:
    st.subheader("Actual vs scheduled shipping time")
    chart = cleaned[[actual_days, scheduled_days]].apply(pd.to_numeric, errors="coerce").dropna()
    chart = chart.rename(columns={actual_days: "Actual days", scheduled_days: "Scheduled days"})
    chart = chart.sample(min(5000, len(chart)), random_state=42) if len(chart) > 5000 else chart
    st.plotly_chart(px.scatter(chart, x="Scheduled days", y="Actual days", opacity=0.45), use_container_width=True)

if risk_col and region_col:
    st.subheader("Risk rate by region")
    region_risk = cleaned.groupby(region_col, dropna=False)[risk_col].agg(["mean", "count"]).reset_index()
    region_risk.columns = ["Region", "Risk rate", "Shipments"]
    region_risk = region_risk[region_risk["Shipments"] >= 20].sort_values("Risk rate", ascending=False).head(15)
    region_risk["Risk rate (%)"] = region_risk["Risk rate"] * 100
    st.plotly_chart(px.bar(region_risk, x="Region", y="Risk rate (%)", hover_data=["Shipments"]), use_container_width=True)

st.subheader("Data quality summary")
q1, q2, q3 = st.columns(3)
q1.metric("Duplicate rows removed", f"{quality['duplicates_removed']:,}")
q2.metric("Rows retained", f"{len(cleaned):,}")
q3.metric("Missing cells after cleaning", f"{int(cleaned.isna().sum().sum()):,}")
with st.expander("View missing-value profile"):
    missing = quality["missing_before"].rename("Missing values before cleaning").to_frame()
    missing = missing[missing.iloc[:, 0] > 0].sort_values("Missing values before cleaning", ascending=False)
    st.dataframe(missing, use_container_width=True)
with st.expander("Explore cleaned data"):
    st.dataframe(cleaned.head(500), use_container_width=True)

csv_bytes = cleaned.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download cleaned CSV", data=csv_bytes, file_name="logistics_cleaned.csv", mime="text/csv")
st.caption(f"SQLite snapshot saved at `{DB_PATH}`. This prototype is intended for portfolio/demo use; validate data and access controls before production deployment.")
