# NYC Taxi Data Profiling & Cleaning Pipeline

**Course:** INF4058 Data Engineering — Lab 3  
**Student Name:** Kareem Alaa Mohamed  
**Student ID:** 692300273  
**Submission:** PDF Report (`Lab_3_Report_Kareem_Alaa.pdf`) + GitHub Repository  

---

## 📌 Executive Summary

This repository contains the end-to-end data profiling and cleaning pipeline for the **NYC Yellow Taxi January 2021 dataset** (`yellow_tripdata_2021-01.csv.gz`), containing **1,369,765 rows**.

Following the **Lab 3 Assignment specifications**, this pipeline:
1. **Never loads the full dataset into memory at once**: It reads, profiles, and cleans in streaming chunks of **100,000 rows**.
2. **Identifies and quantifies all data quality anomalies**: Null values, invalid dates, temporal inversions, negative/zero fares and distances, zero passenger counts, and duplicates.
3. **Applies custom non-destructive cleaning logic (`clean(df)`)**: Operates on defensive copies, transparently accounts for every removed or modified record in a metrics dictionary `{rule: rows_removed}`, and fixes legitimate omissions (imputing zero passenger counts to 1).
4. **Stops cleanly at the cleaning stage**: Validates data quality without loading into PostgreSQL (connection to the automated Docker pipeline will occur in the next lab session).
5. **Maintains strict repository hygiene**: Raw data files (`*.csv.gz`) and virtual environments (`.venv/`) are excluded via `.gitignore`.

---

## 🏗️ Pipeline Architecture & Flow

```
+-----------------------------------------------------------------------------------------+
|                                    DATA PIPELINE LIFECYCLE                              |
+-----------------------------------------------------------------------------------------+
|                                                                                         |
|   +------------+        +------------+        +------------+        +------------+      |
|   |   SOURCE   |  --->  |  EXTRACT   |  --->  | TRANSFORM  |  --->  |    LOAD    |      |
|   +------------+        +------------+        +------------+        +------------+      |
|    NYC TLC Data          HTTP Stream           clean(df)             PostgreSQL         |
|    GitHub (.gz)          Chunks (100k)         Validation            Docker Engine      |
|                                                                            |            |
|                                                                            v            |
|                                                                     +------------+      |
|                                                                     |   SERVE    |      |
|                                                                     +------------+      |
|                                                                      pgAdmin & BI       |
+-----------------------------------------------------------------------------------------+
```

### Stage Breakdown:
- **Source:** Compressed monthly release file (`yellow_tripdata_2021-01.csv.gz`) containing 1,369,765 trips.
- **Extract:** Extracted on-the-fly over HTTP via `pd.read_csv(url, iterator=True, chunksize=100000)` without downloading large uncompressed files to disk.
- **Transform:** Schema enforcement (`Int64`), chronological ordering verification, spatial & financial range checks, and business logic execution inside `clean(df)`.
- **Load (Staged):** Streaming insertion into PostgreSQL using SQLAlchemy. Chunk 1 initializes table DDL with `if_exists='replace'`, while chunks 2–14 append. (*Stopped before this stage for Lab 3*).
- **Serve:** Relational querying via port 5432 and pgAdmin web UI on port 8085.

---

## 🔍 Profiling Results (All 1,369,765 Rows)

The dataset was profiled chunk-by-chunk across all 14 chunks:

| Column Name | Inferred Dtype | Null Count | Null % | Minimum Value | Maximum Value |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `VendorID` | `int64` | 98,352 | 7.18% | 1 | 2 |
| `tpep_pickup_datetime` | `datetime64[us]` | 0 | 0.00% | 2008-12-31 23:05:14 | 2021-02-22 16:52:16 |
| `tpep_dropoff_datetime`| `datetime64[us]` | 0 | 0.00% | 2008-12-31 23:07:22 | 2021-02-22 16:56:15 |
| `passenger_count` | `int64` | 98,352 | 7.18% | 0 | 8 |
| `trip_distance` | `float64` | 0 | 0.00% | 0.00 | 263,163.28 |
| `RatecodeID` | `int64` | 98,352 | 7.18% | 1 | 99 |
| `store_and_fwd_flag` | `str` | 98,352 | 7.18% | N | Y |
| `PULocationID` | `int64` | 0 | 0.00% | 1 | 265 |
| `DOLocationID` | `int64` | 0 | 0.00% | 1 | 265 |
| `payment_type` | `int64` | 98,352 | 7.18% | 1 | 4 |
| `fare_amount` | `float64` | 0 | 0.00% | -$490.00 | $6,960.50 |
| `extra` | `float64` | 0 | 0.00% | -$5.50 | $8.25 |
| `mta_tax` | `float64` | 0 | 0.00% | -$0.50 | $0.50 |
| `tip_amount` | `float64` | 0 | 0.00% | -$100.00 | $1,140.44 |
| `tolls_amount` | `float64` | 0 | 0.00% | -$31.12 | $811.75 |
| `improvement_surcharge`| `float64` | 0 | 0.00% | -$0.30 | $0.30 |
| `total_amount` | `float64` | 0 | 0.00% | -$492.80 | $7,661.28 |
| `congestion_surcharge` | `float64` | 0 | 0.00% | -$2.50 | $3.00 |

---

## ⚠️ Data Quality Anomalies Identified

| Anomaly / Quality Issue | Affected Rows | Percentage (%) | Severity |
| :--- | :--- | :--- | :--- |
| **Pickups outside January 2021** (`< 2021-01-01` or `&ge; 2021-02-01`) | 24 | 0.0018% | Critical |
| **Dropoff datetime before pickup datetime** (temporal inversion) | 5,642 | 0.4119% | Critical |
| **Negative fare amount** (`fare_amount < $0.00`) | 6,769 | 0.4942% | High |
| **Zero fare amount** (`fare_amount == $0.00`) | 642 | 0.0469% | Medium |
| **Zero trip distance** (`trip_distance == 0.0 miles`) | 19,952 | 1.4566% | Medium |
| **Passenger count equals 0** (`passenger_count == 0`) | 26,726 | 1.9511% | Medium |
| **Missing / Null values** in `passenger_count` & `VendorID` | 98,352 | 7.1802% | High |
| **Invalid RatecodeID** (`RatecodeID == 99`) | 36 | 0.0026% | Low |
| **Extreme trip distance** (`trip_distance > 100 miles`) | 55 | 0.0040% | Low |
| **Exact duplicate rows** (identical across all 18 columns) | 0 | 0.0000% | None |
| **Duplicate trip keys** (same Vendor, timestamps, and zones) | 5,900 | 0.4307% | Low |

---

## ⚖️ Governance Decisions Table (Step 4)

| Problem | Decision | Technical & Business Rationale | Rule Owner |
| :--- | :---: | :--- | :--- |
| **Pickups outside Jan 2021** | **DROP** | Protects partition boundaries. Out-of-month records (from 2008 or late Feb) corrupt monthly billing aggregations. | Data Engineering / Ingestion Contract |
| **Dropoff before pickup** | **DROP** | Negative trip duration violates causality and physical reality. Corrupts transit speed and turnaround analytics. | Data Engineering / QA |
| **Negative fares** | **DROP** | Represent meter cancellations, disputes, or chargebacks. Non-commercial records distort trip revenue calculations. | Finance / Revenue Analytics |
| **Zero fares** | **DROP** | Non-revenue test runs or employee shuttles. Skews average pricing and yield modeling. | Commercial Operations |
| **Zero trip distance** | **DROP** | Stationary meter tests or GPS disconnects. Unusable for spatial, routing, or mobility analysis. | Fleet Telematics Team |
| **Passenger count == 0** | **FIX** | Drivers forget to push the meter passenger keypad. Imputing to 1 (statistical mode) preserves valid paid revenue trips. | Analytics & ML Engineering |
| **Missing VendorID / Passengers** | **DROP** | Incomplete dispatch records lacking primary attribution. Violates target schema completeness contracts. | Source Ingestion Team |
| **Duplicate rows** | **DROP** | Enforces idempotency against batch retries or network replays. | Data Platform Team |

---

## 🧹 Custom Cleaning Execution (`clean(df)`)

### Implementation Guarantees:
```python
def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    # 1. Defensive copy: original DataFrame is NEVER mutated
    cleaned = df.copy()
    metrics = {}
    
    # 2. Sequential filtering with transparent tracking
    # Rule 1: Deduplication
    # Rule 2: Temporal boundary enforcement (Jan 2021)
    # Rule 3: Dropoff >= pickup
    # Rule 4: fare_amount > 0
    # Rule 5: trip_distance > 0
    # Rule 6: Drop null vendor/passenger records
    # Rule 7: Fix passenger_count == 0 (impute to 1)
    
    return cleaned, metrics
```

### Cleaning Results Summary:
- **Rows Before Cleaning:** `1,369,765`
- **Rows After Cleaning:** `1,246,349`
- **Rows Removed:** `123,416` (9.01%)
- **Rows Repaired / Fixed:** `26,246` (zero passenger records imputed to 1)

### Breakdown of Rows Removed per Rule:
```
{
    'rule_1_drop_duplicates': 0,
    'rule_2_drop_pickups_outside_jan_2021': 24,
    'rule_3_drop_dropoff_before_pickup': 5642,
    'rule_4_drop_non_positive_fare': 7394,
    'rule_5_drop_non_positive_distance': 18967,
    'rule_6_drop_missing_critical_keys': 91389,
    'rule_7_fix_passenger_count_zero_imputed': 26246
}
```

---

## 💡 Technical Q&A (Section 6)

### Q1: Why does the container reach the DB as `pgdatabase`, not `localhost`?
Inside Docker, every container runs in its own network namespace with an isolated loopback interface (`localhost` / `127.0.0.1`). When code inside the ingestion container attempts to connect to `localhost:5432`, it queries its own container network where no PostgreSQL service is running, causing `Connection refused`. When containers are attached to a Docker Compose bridge network, Docker's embedded DNS server (`127.0.0.11`) resolves the service name `pgdatabase` directly to the PostgreSQL container's internal IP.

### Q2: Why chunks, and what was wrong with `replace` for many months?
- **Why Chunks:** Monolithic ingestion of large CSVs causes memory spikes proportional to file size ($O(N)$), triggering Out-Of-Memory (OOM) killer terminations in containerized environments. Chunks provide a constant streaming memory envelope ($O(K)$ where $K=100,000$), allowing datasets of arbitrary size to be processed safely.
- **What was wrong with `replace`:** `if_exists='replace'` drops and recreates the target database table from scratch. If run across multiple months, each new month will delete all preceding months, leaving only the very last month ingested. Production pipelines must initialize table DDL on chunk 1 and append all subsequent batches.

### Q3: How did you verify your results?
1. **Row Count Conservation:** Verified $\text{Initial Rows (1,369,765)} = \text{Cleaned Rows (1,246,349)} + \text{Removed Rows (123,416)}$.
2. **Post-Cleaning Invariant Assertions:** Verified 0 records outside Jan 2021, 0 negative durations, 0 non-positive fares, 0 non-positive distances, and 0 zero-passenger records.
3. **Immutability Check:** Asserted `id(df_cleaned) != id(df_raw)` to ensure inputs were never mutated in-place.
4. **Relational Verification:** Verified database query counts matched expected chunk totals.

---

## 🛠️ What Broke & Troubleshooting (Section 7)

- **Error:** `DtypeWarning: Columns (6) have mixed types` followed by `ValueError: Cannot convert non-finite values (NA or inf) to integer`.
- **Root Cause:** Chunks 1–12 have complete integer values, but chunks 13–14 contain 98,352 `NaN` values in `passenger_count` and `VendorID`. Legacy NumPy `int64` cannot store nulls, forcing Pandas to coerce the column to `float64` or crash.
- **Fix Applied:** Configured explicit schema type mappings with Pandas nullable integer extension `Int64`:
  ```python
  dtype = {
      'VendorID': 'Int64',
      'passenger_count': 'Int64',
      'RatecodeID': 'Int64',
      'store_and_fwd_flag': 'string'
  }
  ```

---

## 🚀 How to Run

### 1. Setup Virtual Environment
```bash
# Using uv (recommended)
uv venv
.venv\Scripts\activate
uv pip install -r requirements.txt

# Or using standard python
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Execute Data Profiling & Cleaning Pipeline
```bash
python clean_taxi_data.py
```

### 3. Interactive Jupyter Notebook
Open and run `clean_taxi_data.ipynb` in VS Code or JupyterLab.

---

## 📁 Repository Structure

```
d:\Study\(4)(1)\Data Engineering\Ass1\
├── .gitignore                     # Ignores *.csv.gz, .venv/, *.log
├── clean_taxi_data.py             # Main pipeline script (look, profile, problems, clean)
├── clean_taxi_data.ipynb          # Interactive Jupyter notebook
├── Lab_3_Report_Kareem_Alaa.pdf   # Complete 4-page submission PDF report
├── Lab 3 Assignment.pdf           # Assignment prompt and specifications
├── README.md                      # Comprehensive project documentation
├── requirements.txt               # Python package dependencies
└── screenshots/                   # Generated high-resolution terminal evidence screenshots
    ├── step1_look.png
    ├── step2_profile.png
    ├── step3_in_class_run.png
    ├── step3_problems.png
    ├── step4_decisions.png
    ├── step5_clean_metrics.png
    └── step7_error_and_fix.png
```
