from pathlib import Path
import sqlite3
import pandas as pd

RISK_CANDIDATES = ["Late_delivery_risk", "late_delivery_risk", "late_delivery"]
STATUS_CANDIDATES = ["Delivery Status", "delivery_status"]
ACTUAL_CANDIDATES = ["Days for shipping (real)", "days_for_shipping_real"]
SCHEDULED_CANDIDATES = ["Days for shipment (scheduled)", "days_for_shipment_scheduled"]
IDENTIFIER_CANDIDATES = ["Customer Email", "Customer Fname", "Customer Lname", "Order Customer Id"]

def _find(df, names):
    return next((name for name in names if name in df.columns), None)

def clean_logistics_data(raw: pd.DataFrame):
    """Return cleaned data and a small quality report. Does not mutate raw."""
    df = raw.copy()
    missing_before = df.isna().sum().sort_values(ascending=False)
    before = len(df)
    df = df.drop_duplicates().copy()
    duplicates_removed = before - len(df)

    # Normalize whitespace in text columns and make blank strings missing.
    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = df[col].astype("string").str.strip()
        df[col] = df[col].replace("", pd.NA)

    # Convert well-known operational numeric columns without coercing ID-like fields.
    numeric_candidates = [
        "Days for shipping (real)", "Days for shipment (scheduled)",
        "Benefit per order", "Sales per customer", "Order Item Discount",
        "Order Item Discount Rate", "Order Item Product Price",
        "Order Item Profit Ratio", "Order Item Quantity", "Sales",
        "Order Item Total", "Order Profit Per Order", "Late_delivery_risk",
        "Latitude", "Longitude"
    ]
    for col in numeric_candidates:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Parse known date columns if present.
    for col in ["order date (DateOrders)", "shipping date (DateOrders)", "Order Date", "Shipping Date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Replace impossible negative values in selected non-negative operational fields with missing.
    for col in ["Days for shipping (real)", "Days for shipment (scheduled)", "Order Item Quantity",
                "Order Item Product Price", "Sales", "Order Item Total"]:
        if col in df.columns:
            df.loc[df[col] < 0, col] = pd.NA

    # Derive late risk from status only if no usable binary target exists.
    risk_col = _find(df, RISK_CANDIDATES)
    if risk_col:
        df[risk_col] = pd.to_numeric(df[risk_col], errors="coerce")
        df[risk_col] = df[risk_col].where(df[risk_col].isin([0, 1]), pd.NA)
        if df[risk_col].isna().all():
            risk_col = None
    if risk_col is None:
        status_col = _find(df, STATUS_CANDIDATES)
        if status_col:
            status = df[status_col].astype("string").str.lower()
            df["Late_delivery_risk"] = status.str.contains("late", na=False).astype("int8")

    # Impute only selected numeric columns; do not blanket-impute every numeric ID.
    for col in df.select_dtypes(include=["number"]).columns:
        if df[col].isna().any() and col not in ["Late_delivery_risk"]:
            median = df[col].median()
            if pd.notna(median):
                df[col] = df[col].fillna(median)

    # Fill missing categorical values so group-by charts remain informative.
    for col in df.select_dtypes(include=["object", "string", "category"]).columns:
        df[col] = df[col].fillna("Unknown")

    # Drop direct personal identifiers from the analytical output when present.
    drop_cols = [c for c in IDENTIFIER_CANDIDATES if c in df.columns]
    if drop_cols:
        df = df.drop(columns=drop_cols)

    # Add schedule variance when both fields exist.
    actual = _find(df, ACTUAL_CANDIDATES)
    scheduled = _find(df, SCHEDULED_CANDIDATES)
    if actual and scheduled:
        df["Schedule_variance_days"] = df[actual] - df[scheduled]
        df["Is_over_schedule"] = (df["Schedule_variance_days"] > 0).astype("int8")

    quality = {
        "duplicates_removed": duplicates_removed,
        "missing_before": missing_before,
        "rows_before": before,
    }
    return df, quality

def build_risk_summary(df: pd.DataFrame):
    risk_col = _find(df, RISK_CANDIDATES)
    if not risk_col:
        return pd.DataFrame(columns=["metric", "value"])
    return pd.DataFrame({
        "metric": ["shipments", "late_risk_rate"],
        "value": [len(df), pd.to_numeric(df[risk_col], errors="coerce").mean()]
    })

def load_to_sqlite(df: pd.DataFrame, db_path):
    """Replace the demo snapshot table in SQLite."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    export = df.copy()
    for col in export.select_dtypes(include=["datetimetz", "datetime64[ns]"]).columns:
        export[col] = export[col].astype("string")
    with sqlite3.connect(db_path) as connection:
        export.to_sql("shipments", connection, if_exists="replace", index=False)
        pd.DataFrame([{"row_count": len(export), "column_count": len(export.columns)}]).to_sql(
            "dataset_metadata", connection, if_exists="replace", index=False
        )
    return db_path
