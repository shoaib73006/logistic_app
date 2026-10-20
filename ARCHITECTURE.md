# Architecture and Technical Guide

## 1. Problem statement
Logistics teams need a fast way to inspect shipment volume, late-delivery risk, shipping modes, and differences between actual and scheduled shipping time. This project provides an exploratory dashboard over a CSV source.

## 2. Functional requirements
- Accept a CSV upload or read a configured local CSV.
- Clean obvious data-quality issues and remove exact duplicate rows.
- Calculate schedule variance when actual and scheduled shipping-day columns exist.
- Show headline metrics and charts where matching columns are available.
- Persist a snapshot to SQLite and let users download cleaned data.
- Provide tests for important pipeline behavior.

## 3. Non-functional requirements
- Clear separation between UI and data-processing logic.
- Graceful handling of optional columns and file-read errors.
- Repeatable local setup with pinned minimum dependency versions.
- Avoid exporting selected direct personal identifiers in analytical output.
- Keep the prototype simple enough to run locally for a portfolio demo.

## 4. Components
- `app.py`: Streamlit UI, metrics, charts, upload/download workflow.
- `src/pipeline.py`: cleaning, feature engineering, risk summary, SQLite persistence.
- `tests/test_pipeline.py`: unit tests for deduplication, schedule variance, and risk aggregation.
- `data/raw/`: local source CSV (not bundled).
- `data/processed/`: generated SQLite database.
- `reports/`: place screenshots or run notes here.

## 5. Data flow
CSV -> Pandas DataFrame -> clean/validate -> derive schedule variance -> SQLite snapshot -> dashboard charts and CSV export.

## 6. Testing plan
- Valid CSV with expected columns.
- CSV with optional columns missing.
- Duplicate records.
- Blank text and missing numeric values.
- Invalid numeric strings and negative values in non-negative fields.
- Missing or malformed risk target.
- Empty file and unreadable file.
- Larger CSV performance and memory use.

## 7. Known limitations
This is a demonstration and exploratory analytics tool, not a production-grade service. It does not authenticate users, schedule ingestion, or train a validated ML model. If a model is added, avoid target leakage and split data before fitting preprocessing. Review whether deriving risk from delivery status is appropriate for the business question.

## 8. Suggested presentation
1. Explain the operational problem.
2. Show the ingestion and cleaning pipeline.
3. Demonstrate the KPI cards and risk distribution.
4. Show schedule variance and regional patterns.
5. Explain test coverage, limitations, and next steps.
