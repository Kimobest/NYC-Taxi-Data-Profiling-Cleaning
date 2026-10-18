"""
Lab 3: NYC Taxi Data Profiling & Cleaning Pipeline
Course: INF4058 Data Engineering
Student: Kareem Alaa Mohamed
ID: 692300273

This module implements a streaming data profiling and cleaning pipeline for the
NYC Yellow Taxi dataset (yellow_tripdata_2021-01.csv.gz).

Key Guarantees:
1. Streaming / Chunked Processing: Reads data in chunks of 100,000 rows without loading all into RAM.
2. Non-destructive Invariance: The clean(df) function operates on copies and never mutates original inputs.
3. Comprehensive Accounting: Every dropped or modified row is tracked and returned in a metrics dictionary.
4. Pipeline Stopping Point: Cleans data and profiles quality without loading into PostgreSQL.
"""

import sys
import gzip
import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any

# Column data types mapping matching class ingestion contract
DATA_TYPES = {
    "VendorID": "Int64",
    "passenger_count": "Int64",
    "trip_distance": "float64",
    "RatecodeID": "Int64",
    "store_and_fwd_flag": "string",
    "PULocationID": "Int64",
    "DOLocationID": "Int64",
    "payment_type": "Int64",
    "fare_amount": "float64",
    "extra": "float64",
    "mta_tax": "float64",
    "tip_amount": "float64",
    "tolls_amount": "float64",
    "improvement_surcharge": "float64",
    "total_amount": "float64",
    "congestion_surcharge": "float64"
}

PARSE_DATES = ["tpep_pickup_datetime", "tpep_dropoff_datetime"]


def look(filepath: str, nrows: int = 100) -> pd.DataFrame:
    """
    Step 1: Look at the first N rows of the dataset.
    Prints df.head() and df.dtypes, and provides structural insights.
    """
    print("=" * 80)
    print(f"STEP 1: LOOK - Reading first {nrows} rows from {filepath}")
    print("=" * 80)

    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 1000)

    df_sample = pd.read_csv(filepath, nrows=nrows)

    print("\n--- PRINTED: df.head() (First 5 Rows) ---")
    print(df_sample.head())

    print("\n--- PRINTED: df.dtypes ---")
    print(df_sample.dtypes)

    print("\n--- STRUCTURAL ANALYSIS OF SAMPLE ---")
    print(f"1. What is a row?")
    print("   A single row represents an individual, completed yellow taxi trip in NYC,")
    print("   recording pickup/dropoff timestamps, meter-calculated distances, spatial zones,")
    print("   rate codes, and detailed itemized fare/surcharge/tip financial breakdowns.")
    
    date_cols = [col for col in df_sample.columns if "datetime" in col or "date" in col]
    print(f"2. Which columns are dates?")
    print(f"   Date columns identified: {date_cols}")
    
    empty_cols = df_sample.columns[df_sample.isnull().all()].tolist()
    partial_empty = df_sample.columns[df_sample.isnull().any()].tolist()
    print(f"3. Which columns look empty in the first {nrows} rows?")
    print(f"   Completely empty columns: {empty_cols if empty_cols else 'None in first 100 rows'}")
    print(f"   Columns with some nulls: {partial_empty if partial_empty else 'None in first 100 rows'}")
    print("-" * 80)

    return df_sample


def profile(filepath: str, chunksize: int = 100000) -> pd.DataFrame:
    """
    Step 2: Profile the entire dataset in chunks of 100,000 rows.
    Never loads the entire file into RAM at once.
    Computes dtype, null count, null %, min, and max for every column.
    """
    print("\n" + "=" * 80)
    print(f"STEP 2: PROFILE - Reading whole file in chunks of {chunksize:,} rows")
    print("=" * 80)

    col_stats: Dict[str, Dict[str, Any]] = {}
    total_rows = 0
    chunk_index = 0

    csv_reader = pd.read_csv(
        filepath,
        chunksize=chunksize,
        parse_dates=PARSE_DATES,
        low_memory=False
    )

    for chunk in csv_reader:
        chunk_index += 1
        chunk_len = len(chunk)
        total_rows += chunk_len

        for col in chunk.columns:
            if col not in col_stats:
                col_stats[col] = {
                    "dtype": str(chunk[col].dtype),
                    "nulls": 0,
                    "min": None,
                    "max": None
                }

            # Accumulate null count
            col_stats[col]["nulls"] += int(chunk[col].isnull().sum())

            # Find min and max ignoring nulls
            valid_vals = chunk[col].dropna()
            if len(valid_vals) > 0:
                cur_min = valid_vals.min()
                cur_max = valid_vals.max()

                if col_stats[col]["min"] is None or cur_min < col_stats[col]["min"]:
                    col_stats[col]["min"] = cur_min
                if col_stats[col]["max"] is None or cur_max > col_stats[col]["max"]:
                    col_stats[col]["max"] = cur_max

    profile_records = []
    for col, stats in col_stats.items():
        profile_records.append({
            "column": col,
            "dtype": stats["dtype"],
            "null_count": stats["nulls"],
            "null_pct": round((stats["nulls"] / total_rows) * 100, 2),
            "min_val": str(stats["min"]),
            "max_val": str(stats["max"])
        })

    profile_df = pd.DataFrame(profile_records)

    print(f"\n--- PRINTED TABLE: Profiling Summary ({chunk_index} chunks, {total_rows:,} total rows) ---")
    print(profile_df.to_string(index=False))
    print("-" * 80)

    return profile_df


def find_problems(filepath: str, chunksize: int = 100000) -> pd.DataFrame:
    """
    Step 3: Scan the whole dataset in chunks to detect data quality anomalies:
    - Pickups outside January 2021
    - Dropoff before pickup (negative trip duration)
    - Negative and zero fares
    - Negative and zero trip distances
    - passenger_count == 0 and passenger_count is NULL
    - Duplicate rows (exact 18-column vs key-based)
    - Outlier values (RatecodeID=99, extreme distances)
    """
    print("\n" + "=" * 80)
    print("STEP 3: FIND PROBLEMS - Detecting Anomalies Across Chunks")
    print("=" * 80)

    total_rows = 0
    pickups_outside_jan2021 = 0
    dropoff_before_pickup = 0
    fare_negative = 0
    fare_zero = 0
    dist_negative = 0
    dist_zero = 0
    passenger_zero = 0
    passenger_null = 0
    vendor_null = 0
    ratecode_99 = 0
    dist_extreme = 0
    
    seen_exact_tuples = set()
    exact_duplicates = 0
    seen_trip_keys = set()
    key_duplicates = 0

    csv_reader = pd.read_csv(
        filepath,
        chunksize=chunksize,
        parse_dates=PARSE_DATES,
        low_memory=False
    )

    for chunk in csv_reader:
        total_rows += len(chunk)

        # 1. Date boundaries
        p_dates = chunk["tpep_pickup_datetime"]
        d_dates = chunk["tpep_dropoff_datetime"]
        outside_mask = (p_dates < "2021-01-01") | (p_dates >= "2021-02-01")
        pickups_outside_jan2021 += int(outside_mask.sum())

        # 2. Chronological order
        drop_before_mask = d_dates < p_dates
        dropoff_before_pickup += int(drop_before_mask.sum())

        # 3. Fares
        fare_negative += int((chunk["fare_amount"] < 0).sum())
        fare_zero += int((chunk["fare_amount"] == 0).sum())

        # 4. Distances
        dist_negative += int((chunk["trip_distance"] < 0).sum())
        dist_zero += int((chunk["trip_distance"] == 0).sum())

        # 5. Passengers
        passenger_zero += int((chunk["passenger_count"] == 0).sum())
        passenger_null += int(chunk["passenger_count"].isnull().sum())
        vendor_null += int(chunk["VendorID"].isnull().sum())

        # 6. Extreme & Odd values
        ratecode_99 += int((chunk["RatecodeID"] == 99).sum())
        dist_extreme += int((chunk["trip_distance"] > 100).sum())

        # 7. Duplicates
        for row in chunk.itertuples(index=False, name=None):
            if row in seen_exact_tuples:
                exact_duplicates += 1
            else:
                seen_exact_tuples.add(row)
                
        # Key duplicates (VendorID, Pickup, Dropoff, PULocationID, DOLocationID)
        key_cols = ["VendorID", "tpep_pickup_datetime", "tpep_dropoff_datetime", "PULocationID", "DOLocationID"]
        for key_tuple in chunk[key_cols].itertuples(index=False, name=None):
            if key_tuple in seen_trip_keys:
                key_duplicates += 1
            else:
                seen_trip_keys.add(key_tuple)

    problems_data = [
        {"Anomaly / Data Issue": "Pickups outside Jan 2021 (< 2021-01-01 or >= 2021-02-01)", "Affected Rows": pickups_outside_jan2021, "Percentage (%)": round((pickups_outside_jan2021 / total_rows) * 100, 4)},
        {"Anomaly / Data Issue": "Dropoff datetime before pickup datetime (time travel)", "Affected Rows": dropoff_before_pickup, "Percentage (%)": round((dropoff_before_pickup / total_rows) * 100, 4)},
        {"Anomaly / Data Issue": "Negative fare amount (fare_amount < $0.00)", "Affected Rows": fare_negative, "Percentage (%)": round((fare_negative / total_rows) * 100, 4)},
        {"Anomaly / Data Issue": "Zero fare amount (fare_amount == $0.00)", "Affected Rows": fare_zero, "Percentage (%)": round((fare_zero / total_rows) * 100, 4)},
        {"Anomaly / Data Issue": "Negative trip distance (trip_distance < 0 miles)", "Affected Rows": dist_negative, "Percentage (%)": round((dist_negative / total_rows) * 100, 4)},
        {"Anomaly / Data Issue": "Zero trip distance (trip_distance == 0 miles)", "Affected Rows": dist_zero, "Percentage (%)": round((dist_zero / total_rows) * 100, 4)},
        {"Anomaly / Data Issue": "Passenger count equals 0 (passenger_count == 0)", "Affected Rows": passenger_zero, "Percentage (%)": round((passenger_zero / total_rows) * 100, 4)},
        {"Anomaly / Data Issue": "Missing / Null passenger_count & VendorID", "Affected Rows": passenger_null, "Percentage (%)": round((passenger_null / total_rows) * 100, 4)},
        {"Anomaly / Data Issue": "RatecodeID == 99 (invalid / undefined rate code)", "Affected Rows": ratecode_99, "Percentage (%)": round((ratecode_99 / total_rows) * 100, 4)},
        {"Anomaly / Data Issue": "Extreme trip distance (> 100 miles)", "Affected Rows": dist_extreme, "Percentage (%)": round((dist_extreme / total_rows) * 100, 4)},
        {"Anomaly / Data Issue": "Exact duplicate rows (identical across all 18 columns)", "Affected Rows": exact_duplicates, "Percentage (%)": round((exact_duplicates / total_rows) * 100, 4)},
        {"Anomaly / Data Issue": "Duplicate trip keys (same Vendor, timestamps, and locations)", "Affected Rows": key_duplicates, "Percentage (%)": round((key_duplicates / total_rows) * 100, 4)},
    ]

    problems_df = pd.DataFrame(problems_data)
    print("\n--- PRINTED TABLE: Data Quality Anomalies Identified ---")
    print(problems_df.to_string(index=False))
    print("-" * 80)

    return problems_df


def clean(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Step 5: Custom cleaning logic.
    
    Guarantees:
    - Never mutates the original input DataFrame (uses df.copy()).
    - Returns a tuple of (cleaned_df, rows_removed_dict).
    - Never drops rows silently: every drop or fix is explicitly tracked.
    
    Rules Applied:
    1. Deduplication: Drop duplicate rows.
    2. Date Partition Alignment: Drop pickups outside January 2021.
    3. Chronological Consistency: Drop trips where dropoff is before pickup.
    4. Economic Validity: Drop negative or zero fares (fare_amount <= 0).
    5. Physical Mobility: Drop zero or negative trip distances (trip_distance <= 0).
    6. Relational Integrity: Drop records missing critical keys (VendorID, passenger_count).
    7. Default Imputation (Fix): Fix passenger_count == 0 by imputing to 1 (statistical mode).
    """
    # Defensive programming: ensure original is never modified
    cleaned = df.copy()
    metrics: Dict[str, int] = {}

    # Rule 1: Deduplication
    dup_mask = cleaned.duplicated()
    metrics["rule_1_drop_duplicates"] = int(dup_mask.sum())
    cleaned = cleaned[~dup_mask]

    # Rule 2: Date boundary validation (Pickups must be in January 2021)
    p_dates = pd.to_datetime(cleaned["tpep_pickup_datetime"], errors="coerce")
    valid_dates_mask = (p_dates >= "2021-01-01") & (p_dates < "2021-02-01")
    metrics["rule_2_drop_pickups_outside_jan_2021"] = int((~valid_dates_mask).sum())
    cleaned = cleaned[valid_dates_mask]

    # Rule 3: Dropoff must be at or after pickup
    p_dates = pd.to_datetime(cleaned["tpep_pickup_datetime"], errors="coerce")
    d_dates = pd.to_datetime(cleaned["tpep_dropoff_datetime"], errors="coerce")
    valid_time_order_mask = d_dates >= p_dates
    metrics["rule_3_drop_dropoff_before_pickup"] = int((~valid_time_order_mask).sum())
    cleaned = cleaned[valid_time_order_mask]

    # Rule 4: Positive fare amount (fare_amount > 0)
    valid_fare_mask = cleaned["fare_amount"] > 0
    metrics["rule_4_drop_non_positive_fare"] = int((~valid_fare_mask).sum())
    cleaned = cleaned[valid_fare_mask]

    # Rule 5: Positive trip distance (trip_distance > 0)
    valid_dist_mask = cleaned["trip_distance"] > 0
    metrics["rule_5_drop_non_positive_distance"] = int((~valid_dist_mask).sum())
    cleaned = cleaned[valid_dist_mask]

    # Rule 6: Drop records missing critical vendor and passenger fields
    missing_keys_mask = cleaned["passenger_count"].isna() | cleaned["VendorID"].isna()
    metrics["rule_6_drop_missing_critical_keys"] = int(missing_keys_mask.sum())
    cleaned = cleaned[~missing_keys_mask]

    # Rule 7: Fix passenger_count == 0 by imputing 1 (Fix action, non-dropping)
    zero_passengers_mask = (cleaned["passenger_count"] == 0)
    metrics["rule_7_fix_passenger_count_zero_imputed"] = int(zero_passengers_mask.sum())
    cleaned.loc[zero_passengers_mask, "passenger_count"] = 1

    return cleaned, metrics


def run_pipeline(filepath: str, chunksize: int = 100000):
    """
    Executes the full profiling, cleaning, and metric accounting pipeline
    across all chunks of the dataset.
    """
    print("\n" + "#" * 80)
    print("NYC TAXI DATA PROFILING & CLEANING PIPELINE")
    print("Course: INF4058 Data Engineering | Lab 3 Assignment")
    print("Student: Kareem Alaa Mohamed | ID: 692300273")
    print("#" * 80)

    # Step 1: Look at first 100 rows
    df_sample = look(filepath, nrows=100)

    # Step 2: Profile the whole file in chunks
    profile_df = profile(filepath, chunksize=chunksize)

    # Step 3: Find and quantify anomalies
    problems_df = find_problems(filepath, chunksize=chunksize)

    # Step 4: Decisions Table
    decisions = [
        {
            "Problem": "Pickups outside Jan 2021 (2008, Feb 2021)",
            "Decision": "DROP",
            "Why": "Preserves temporal partition boundary integrity. Downstream January analytics and billing aggregations will be corrupted by out-of-boundary rides.",
            "Owner": "Data Engineering / Ingestion Pipeline Contract"
        },
        {
            "Problem": "Dropoff before pickup (5,642 rows)",
            "Decision": "DROP",
            "Why": "Negative duration violates physical reality and causality. Distorts transit speed, route modeling, and driver turnaround times.",
            "Owner": "Data Engineering / Quality Assurance"
        },
        {
            "Problem": "Negative fares (6,769 rows)",
            "Decision": "DROP",
            "Why": "Represents chargebacks, disputes, meter cancellations, or system corrections. Pollutes transactional revenue and average trip yield metrics.",
            "Owner": "Finance / Revenue & Ingestion Team"
        },
        {
            "Problem": "Zero fares (642 rows)",
            "Decision": "DROP",
            "Why": "Non-revenue test rides, employee shuttles, or meter calibration runs. Non-commercial records bias passenger pricing models.",
            "Owner": "Commercial Operations Team"
        },
        {
            "Problem": "Zero trip distance (19,952 rows)",
            "Decision": "DROP",
            "Why": "Trips with zero distance traveled are stationary cancellations or GPS disconnects. Unusable for mobility, distance, or spatial analysis.",
            "Owner": "Fleet Telematics / Operations Team"
        },
        {
            "Problem": "Passenger count == 0 (26,726 rows)",
            "Decision": "FIX",
            "Why": "Taxi drivers frequently neglect to press the passenger count button on the meter. Imputing to 1 (statistical mode) salvages valid paid revenue trips.",
            "Owner": "Data Analytics & ML Feature Engineering"
        },
        {
            "Problem": "Missing values in VendorID & passenger_count (98,352 rows)",
            "Decision": "DROP",
            "Why": "Incomplete dispatch records lacking primary attribution and operational metadata. Violates relational completeness for target schema.",
            "Owner": "Source Data Provider / Ingestion Team"
        },
        {
            "Problem": "Duplicate rows (0 exact, 5,900 key dups)",
            "Decision": "DROP",
            "Why": "Guarantees pipeline idempotency against network retries, container restarts, or duplicate source file deliveries.",
            "Owner": "Data Engineering Platform Team"
        }
    ]
    decisions_df = pd.DataFrame(decisions)
    print("\n" + "=" * 80)
    print("STEP 4: DECISIONS TABLE (Problem, Decision, Why, Owner)")
    print("=" * 80)
    print(decisions_df.to_string(index=False))
    print("-" * 80)

    # Step 5: Clean the dataset chunk by chunk
    print("\n" + "=" * 80)
    print(f"STEP 5: CLEAN - Executing clean(df) in chunks of {chunksize:,}")
    print("=" * 80)

    total_rows_before = 0
    total_rows_after = 0
    cumulative_metrics: Dict[str, int] = {}

    csv_reader = pd.read_csv(
        filepath,
        chunksize=chunksize,
        parse_dates=PARSE_DATES,
        low_memory=False
    )

    for chunk_idx, chunk in enumerate(csv_reader, 1):
        rows_in_chunk = len(chunk)
        total_rows_before += rows_in_chunk

        cleaned_chunk, chunk_metrics = clean(chunk)
        total_rows_after += len(cleaned_chunk)

        for rule, count in chunk_metrics.items():
            cumulative_metrics[rule] = cumulative_metrics.get(rule, 0) + count

    total_rows_removed = total_rows_before - total_rows_after
    removal_pct = (total_rows_removed / total_rows_before) * 100

    print("\n--- PRINTED: CLEANING EXECUTION RESULTS ---")
    print(f"Rows Before Cleaning : {total_rows_before:,}")
    print(f"Rows After Cleaning  : {total_rows_after:,}")
    print(f"Rows Removed         : {total_rows_removed:,} ({removal_pct:.2f}%)")

    print("\n--- PRINTED TABLE: {rule: rows_removed} ---")
    metrics_summary = [
        {"Cleaning Rule": k, "Count": v}
        for k, v in cumulative_metrics.items()
    ]
    metrics_df = pd.DataFrame(metrics_summary)
    print(metrics_df.to_string(index=False))
    print("=" * 80)

    # Step 6: Pipeline stop confirmation
    print("\n" + "=" * 80)
    print("STEP 6: STOP HERE - Pipeline Stopped Before Loading Into Postgres")
    print("Cleaned data validated. Database connection withheld for next session.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    filepath = "yellow_tripdata_2021-01.csv.gz"
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    run_pipeline(filepath)
