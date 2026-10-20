# Logistics Intelligence & Delivery Risk Dashboard

A portfolio-ready logistics analytics application that cleans shipment data, summarizes delivery risk, visualizes operational performance, and stores a cleaned snapshot in SQLite.

## Features
- Upload a CSV or load the DataCo dataset from `data/raw/`
- Duplicate removal, whitespace cleanup, type conversion, missing-value handling, and basic validity checks
- Schedule variance and over-schedule feature engineering
- Delivery risk, region, shipping mode, and schedule comparison charts
- SQLite snapshot of cleaned shipments
- Download cleaned data
- Basic automated tests with `pytest`

## Tech stack
Python, Pandas, Streamlit, Plotly, SQLite, Pytest.

## Dataset
Download the DataCo Smart Supply Chain dataset from its original public hosting page or your internship-provided source. Put the CSV at:
`data/raw/DataCoSupplyChainDataset.csv`
Do not commit datasets containing personal or restricted information. Alternatively, upload a compatible CSV from the dashboard.

## Run locally (Windows PowerShell)
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

## Run tests
```powershell
python -m pytest -q
```

## Outputs
- `data/processed/logistics.db`: SQLite demo snapshot
- Dashboard download: `logistics_cleaned.csv`

## Architecture
`CSV input -> cleaning/validation pipeline -> feature engineering -> SQLite snapshot -> Streamlit dashboard and CSV export`

## Data-quality and modeling notes
- The app performs exploratory analytics, not a validated production prediction service.
- Missing-value imputation is intentionally simple and should be reviewed for the dataset and business use case.
- For machine-learning model development, split train/test first and fit imputation, scaling, and encoding only on training data to prevent leakage.
- Review data permissions and remove personal identifiers before sharing or deploying.

## Future improvements
1. Add role-based authentication and controlled database access.
2. Add a trained baseline classifier with cross-validation and precision/recall reporting.
3. Add logging, schema validation, CI tests, and deployment monitoring.
4. Add time-based monitoring for delivery-risk changes.
