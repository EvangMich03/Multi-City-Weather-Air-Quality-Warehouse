# Multi-City Weather & Air Quality Warehouse

[![Python 3.12](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-336791?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Pandas](https://img.shields.io/badge/Pandas-2.0+-150458?style=flat&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Open-Meteo](https://img.shields.io/badge/Data%20Source-Open--Meteo%20API-FF6F00?style=flat)](https://open-meteo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An end-to-end, resilient ETL (Extract, Transform, Load) data pipeline designed to ingest, process, and warehouse multi-location meteorological time-series data into a relational PostgreSQL database.

Built with production patterns in mind: **idempotent writes**, **exponential backoff retry policies**, **client-side response caching**, and **vectorized batch transformations**.

---

## 📌 Architecture Overview

```
                      +---------------------------------------+
                      |       Open-Meteo Weather API          |
                      +---------------------------------------+
                                          |
                      Batch Multi-Coordinate Request (Hourly)
                                          v
                      +---------------------------------------+
                      |         Resilience & Cache Layer      |
                      |  - SQLite Request Cache (1h TTL)      |
                      |  - Exponential Backoff Retries (5x)   |
                      +---------------------------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |       Pandas / NumPy Engine           |
                      |  - Unpack binary variable arrays      |
                      |  - Normalize UTC timestamps           |
                      |  - Relational mapping (location_id)   |
                      +---------------------------------------+
                                          |
                              Bulk UPSERT (executemany)
                                          v
+-----------------------------------------------------------------------------+
|                          PostgreSQL Data Warehouse                          |
|                                                                             |
|   +-----------------------+              +------------------------------+   |
|   |       LOCATIONS       |              |           WEATHER            |   |
|   +-----------------------+              +------------------------------+   |
|   | PK location_id (INT)  |<----+        | PK,FK location_id (INT)      |   |
|   |    city_name (VARCHAR)|     +------->| PK    forecast_time (TIMESTZ)|   |
|   |    latitude (FLOAT)   |              |       tempar (FLOAT)         |   |
|   |    longitute (FLOAT)  |              |       precipipation (FLOAT)  |   |
|   +-----------------------+              |       windspeed (FLOAT)      |   |
|                                          +------------------------------+   |
+-----------------------------------------------------------------------------+
```

---

## 🛠️ Key Engineering Features

- **Idempotent Ingestion (`UPSERT`)**:
  Both city coordinates and forecast observations use PostgreSQL `ON CONFLICT (...) DO UPDATE` statements. Re-running the pipeline at any cadence is completely safe—it refreshes forecasts without generating duplicate rows or violating unique constraints.
- **Batched API Fetching**:
  Instead of issuing sequential HTTP requests per city, coordinate arrays are bundled into a single batched query to Open-Meteo, drastically reducing network round-trips and pipeline latency.
- **Fault Tolerance & Rate Limit Protection**:
  - **Local HTTP Caching**: Backed by `requests-cache` (`.cache.sqlite`) with a 1-hour expiration to prevent redundant API calls during development or rapid iteration.
  - **Exponential Backoff**: Integrated `retry-requests` with configurable retry counts and backoff factors to absorb transient DNS or HTTP 5xx glitches.
- **Vectorized Data Transformation**:
  API variable streams are decoded directly into NumPy arrays and wrapped into a tabular Pandas DataFrame, aligning hourly intervals with standard UTC timestamps (`pd.date_range`).
- **Bulk Loading**:
  Uses `psycopg2` cursor `executemany` with tuple generation via `itertuples`, bypassing slow single-record inserts.

---

## 🗄️ Database Schema

The database employs a normalized star-like design separating geographical dimension entities from time-series fact data.

### `locations` (Dimension)
Stores target cities with geographical coordinates:
```sql
CREATE TABLE locations (
    location_id SERIAL PRIMARY KEY,
    city_name VARCHAR(100) NOT NULL,
    latitude FLOAT,
    longitute FLOAT
);
```

### `weather` (Fact / Time-Series)
Stores hourly forecast metrics tied to locations:
```sql
CREATE TABLE weather (
    location_id INT REFERENCES locations (location_id),
    forecast_time TIMESTAMPTZ NOT NULL,
    tempar FLOAT,
    precipipation FLOAT,
    windspeed FLOAT,
    PRIMARY KEY (location_id, forecast_time)
);
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.10+** (Python 3.12 recommended)
- **PostgreSQL 14+** running locally or remotely

### 2. Clone & Set Up Virtual Environment

```bash
# Clone the repository
git clone https://github.com/your-username/Multi-City-Weather-Air-Quality-Warehouse.git
cd Multi-City-Weather-Air-Quality-Warehouse

# Create a virtual environment (if not already created)
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate
# Or use the absolute path:
# source /home/evangelosge84puv/Multi-City-Weather-Air-Quality-Warehouse/venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your PostgreSQL credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```env
dbusername=your_postgres_user
dbpassword=your_postgres_password
dbname=your_database_name
```

### 5. Initialize the Database Schema

Run the SQL script against your PostgreSQL instance:

```bash
psql -U your_postgres_user -d your_database_name -f schema.sql
```

### 6. Run the ETL Pipeline

```bash
python pipeline.py
```

Console logs will indicate progress, including fetched city IDs, coordinates, and confirmation of committed transactions.

---

## 📂 Project Structure

```
├── .cache.sqlite          # Local HTTP request cache (auto-generated, git-ignored)
├── .env.example           # Template for environment credentials
├── .gitignore             # Git ignore rules for virtualenv, cache, and secrets
├── pipeline.py            # Main ETL pipeline script
├── README.md              # Project documentation
├── requirements.txt       # Project dependencies
└── schema.sql             # PostgreSQL schema definition (tables, constraints, PKs)
```

---

## 📊 Sample SQL Analytical Queries

Once data is loaded, you can run queries directly in your SQL client:

### Compare Average Temperature Across Cities
```sql
SELECT 
    l.city_name,
    ROUND(AVG(w.tempar)::numeric, 2) AS avg_temperature_celsius,
    ROUND(MAX(w.windspeed)::numeric, 2) AS max_wind_speed_kmh,
    ROUND(SUM(w.precipipation)::numeric, 2) AS total_precipitation_mm
FROM weather w
JOIN locations l ON w.location_id = l.location_id
GROUP BY l.city_name
ORDER BY avg_temperature_celsius DESC;
```

### Next 24-Hour Forecast for a Specific City
```sql
SELECT 
    w.forecast_time,
    w.tempar AS temp_c,
    w.precipipation AS rain_mm,
    w.windspeed AS wind_kmh
FROM weather w
JOIN locations l ON w.location_id = l.location_id
WHERE l.city_name = 'Berlin'
  AND w.forecast_time >= NOW()
ORDER BY w.forecast_time ASC
LIMIT 24;
```

---

## 🔮 Roadmap & Future Enhancements

- [ ] **Air Quality Ingestion**: Integrate Open-Meteo Air Quality API (PM2.5, PM10, NO2, O3, AQI) into a complementary `air_quality` fact table.
- [ ] **Data Quality Testing**: Integrate validation checks (e.g., Great Expectations or Soda Core) to detect null readings or sensor anomalies.
- [ ] **Pipeline Orchestration**: Schedule hourly automated pipeline runs using Apache Airflow or lightweight systemd/cron timers.
- [ ] **Containerization**: Add `docker-compose.yml` to spin up PostgreSQL and the ETL runner in isolated containers.
- [ ] **Analytics & Semantic Layer**: Implement a dbt (data build tool) project to build daily aggregated marts and rolling anomaly views.

---

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.
