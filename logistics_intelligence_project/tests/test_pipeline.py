import pandas as pd
from src.pipeline import clean_logistics_data, build_risk_summary

def test_deduplicates_and_derives_schedule_variance():
    raw = pd.DataFrame({
        "Late_delivery_risk": [0, 1, 1],
        "Days for shipping (real)": [2, 5, 6],
        "Days for shipment (scheduled)": [3, 4, 4],
        "Order Region": ["East", "West", "North"],
    })
    raw = pd.concat([raw, raw.iloc[[1]]], ignore_index=True)
    cleaned, quality = clean_logistics_data(raw)
    assert len(cleaned) == 3
    assert quality["duplicates_removed"] == 1
    assert "Schedule_variance_days" in cleaned.columns
    assert cleaned["Schedule_variance_days"].tolist() == [-1, 1, 2]

def test_risk_summary():
    df = pd.DataFrame({"Late_delivery_risk": [0, 1, 1, 0]})
    summary = build_risk_summary(df)
    assert summary.loc[summary.metric == "late_risk_rate", "value"].iloc[0] == 0.5
