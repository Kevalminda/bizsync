# BizSync

Configurable business data synchronization engine.

Current real-world use case:
Flipkart CSV -> structured records -> Google Sheets.

The generic engine is designed so source-specific column names and unique keys
can be configured instead of hard-coded.

## Current MVP
- CSV and XLSX ingestion
- Header normalization
- Configurable source -> target mapping
- Required-field validation
- Configurable duplicate keys
- New / updated / unchanged classification
- Flipkart sample configuration

## Run

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m app.cli sample_data/flipkart_sample.csv
