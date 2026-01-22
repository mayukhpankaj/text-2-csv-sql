# Trading ETL API

A FastAPI application for CSV → SQLite ETL and analytics for trading data.

<img width="3120" height="2032" alt="Untitled" src="https://github.com/user-attachments/assets/a5e93c91-45ad-487a-83e8-2f1500fa5101" />


## Features

- ETL pipeline to load trades and holdings from CSV files into SQLite database
- REST API endpoints for analytics:
  - `/analytics/trades-per-fund` - Get trade count per portfolio
  - `/analytics/top-funds` - Get top funds by YTD returns
  - `/etl/run` - Run the ETL process

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Initialize the database:
```bash
sqlite3 trading.db < schema.sql
```

3. Place your CSV files:
   - `trades.csv` - Trade allocation data
   - `holdings.csv` - Holdings data

4. Run the API server:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation.
