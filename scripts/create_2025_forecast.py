"""
Create 2025 Forecast Dataset from 2024 Base Data

This script:
1. Filters data to 2024 only
2. Shifts dates to 2025 (handling leap year)
3. Adds variability (0.95-1.15 multiplier)
4. Identifies depots missing in 2024
5. Saves forecast_2025.csv

Dependencies:
    pip install pandas numpy openpyxl
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Set random seed for reproducibility
np.random.seed(42)

# ============================================================================
# Configuration
# ============================================================================
# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

# File names
INPUT_FILE = "Deposits_Trans_2023_2024.xlsx"
OUTPUT_FILE = "forecast_2025.csv"

# Column names (adjust if needed)
SHEET_NAME = "Deposit Transactions"  # Try "Deposit_Transactions" if this fails
DATE_COL = "Deposit Date"
DEPOT_COL = "Depo"  # or "Depot_ID" depending on actual column name
VOLUME_COL = "Volume (oz)"
DEPOSIT_ID_COL = "Deposit ID"  # Deposit ID column

# ============================================================================
# Main Processing
# ============================================================================

def main():
    print("=" * 70)
    print("Creating 2025 Forecast Dataset")
    print("=" * 70)
    
    # 1. Load the Excel file
    input_path = DATA_DIR / INPUT_FILE
    print(f"\n1. Loading data from: {input_path}")
    
    try:
        df = pd.read_excel(input_path, sheet_name=SHEET_NAME)
    except ValueError:
        # Try alternative sheet name
        alt_sheet_name = "Deposit_Transactions"
        print(f"   Sheet '{SHEET_NAME}' not found, trying '{alt_sheet_name}'...")
        df = pd.read_excel(input_path, sheet_name=alt_sheet_name)
    
    print(f"   Loaded {len(df):,} rows")
    print(f"   Columns: {list(df.columns)}")
    
    # Display first few rows to verify structure
    print("\n   First 5 rows:")
    print(df.head())
    
    # 2. Clean and prepare data
    print(f"\n2. Cleaning data...")
    
    # Select relevant columns (include Deposit ID if available)
    required_cols = [DATE_COL, DEPOT_COL, VOLUME_COL]
    optional_cols = [DEPOSIT_ID_COL]
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"   ERROR: Missing columns: {missing_cols}")
        print(f"   Available columns: {list(df.columns)}")
        return
    
    # Check if Deposit ID column exists
    has_deposit_id = DEPOSIT_ID_COL in df.columns
    if has_deposit_id:
        print(f"   ✓ Found Deposit ID column: {DEPOSIT_ID_COL}")
        work_cols = [DEPOSIT_ID_COL, DATE_COL, DEPOT_COL, VOLUME_COL]
    else:
        print(f"   ⚠ Warning: Deposit ID column '{DEPOSIT_ID_COL}' not found")
        print(f"   Available columns: {list(df.columns)}")
        work_cols = [DATE_COL, DEPOT_COL, VOLUME_COL]
    
    work = df[work_cols].copy()
    
    # Drop rows with missing date or depot
    initial_rows = len(work)
    work = work.dropna(subset=[DATE_COL, DEPOT_COL])
    dropped_rows = initial_rows - len(work)
    if dropped_rows > 0:
        print(f"   Dropped {dropped_rows:,} rows with missing date or depot")
    
    # Convert date to datetime
    work[DATE_COL] = pd.to_datetime(work[DATE_COL], errors='coerce')
    work = work.dropna(subset=[DATE_COL])
    
    # Ensure volume is numeric
    work[VOLUME_COL] = pd.to_numeric(work[VOLUME_COL], errors='coerce').fillna(0)
    
    # Extract year for filtering
    work['Year'] = work[DATE_COL].dt.year
    
    print(f"   Data spans years: {sorted(work['Year'].unique())}")
    print(f"   Total rows after cleaning: {len(work):,}")
    
    # 3. Identify depots in 2023 but not in 2024
    print(f"\n3. Checking for depots in 2023 but missing in 2024...")
    
    depots_2023 = set(work[work['Year'] == 2023][DEPOT_COL].unique())
    depots_2024 = set(work[work['Year'] == 2024][DEPOT_COL].unique())
    missing_depots = depots_2023 - depots_2024
    
    if missing_depots:
        print(f"   WARNING: Found {len(missing_depots)} depots in 2023 with ZERO records in 2024:")
        for depot in sorted(missing_depots):
            print(f"      - {depot}")
        print(f"   These will be excluded from the 2025 forecast (assuming inactive).")
    else:
        print(f"   ✓ All 2023 depots have records in 2024.")
    
    # 4. Filter to 2024 data only
    print(f"\n4. Filtering to 2024 data only...")
    df_2024 = work[work['Year'] == 2024].copy()
    print(f"   Filtered to {len(df_2024):,} rows from 2024")
    
    # Calculate 2024 total volume
    total_2024 = df_2024[VOLUME_COL].sum()
    print(f"   2024 Total Volume: {total_2024:,.2f} oz")
    
    # 5. Create 2025 forecast
    print(f"\n5. Creating 2025 forecast...")
    forecast = df_2024.copy()
    
    # Shift dates to 2025
    # Handle Feb 29 (leap year): drop it since 2025 is not a leap year
    def shift_to_2025(date_val):
        """Shift date to 2025, returning None for Feb 29 (leap day)"""
        if pd.isna(date_val):
            return None
        month = date_val.month
        day = date_val.day
        if month == 2 and day == 29:
            return None  # Drop Feb 29 since 2025 is not a leap year
        try:
            return pd.Timestamp(2025, month, day)
        except ValueError:
            return None  # Handle any other invalid dates
    
    forecast['Date_2025'] = forecast[DATE_COL].apply(shift_to_2025)
    
    # Drop Feb 29 rows
    initial_forecast_rows = len(forecast)
    forecast = forecast.dropna(subset=['Date_2025'])
    dropped_feb29 = initial_forecast_rows - len(forecast)
    if dropped_feb29 > 0:
        print(f"   Dropped {dropped_feb29} rows from Feb 29 (2025 is not a leap year)")
    
    # Add variability: multiply volumes by random factor between 0.95 and 1.15
    print(f"   Adding variability (multiplying volumes by 0.95-1.15)...")
    forecast['Volume_2025'] = forecast[VOLUME_COL] * np.random.uniform(0.95, 1.15, size=len(forecast))
    
    # Calculate projected 2025 total volume
    total_2025 = forecast['Volume_2025'].sum()
    print(f"   Projected 2025 Total Volume: {total_2025:,.2f} oz")
    print(f"   Change: {((total_2025 / total_2024 - 1) * 100):+.2f}%")
    
    # 6. Prepare final output DataFrame
    print(f"\n6. Preparing output...")
    
    # Prepare output DataFrame with Deposit ID if available
    # Order: Deposit ID (if exists), Date_2025, Depo, Volume_2025, then reference columns
    output_dict = {}
    
    # Add Deposit ID first if it exists
    if DEPOSIT_ID_COL in forecast.columns:
        output_dict[DEPOSIT_ID_COL] = forecast[DEPOSIT_ID_COL]
        print(f"   ✓ Including Deposit ID column in output")
    
    # Add main columns
    output_dict.update({
        'Date_2025': forecast['Date_2025'],
        DEPOT_COL: forecast[DEPOT_COL],
        'Volume_2025': forecast['Volume_2025'],
        'Date_2024_Original': forecast[DATE_COL],  # Keep for reference
        'Volume_2024_Original': forecast[VOLUME_COL]  # Keep for reference
    })
    
    output_df = pd.DataFrame(output_dict)
    
    # Sort by date and depot (and Deposit ID if available)
    sort_cols = ['Date_2025', DEPOT_COL]
    if DEPOSIT_ID_COL in output_df.columns:
        sort_cols.append(DEPOSIT_ID_COL)
    output_df = output_df.sort_values(sort_cols).reset_index(drop=True)
    
    print(f"   Final forecast dataset: {len(output_df):,} rows")
    
    # 7. Save to CSV
    print(f"\n7. Saving forecast to CSV...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / OUTPUT_FILE
    output_df.to_csv(output_path, index=False)
    print(f"   ✓ Saved to: {output_path}")
    
    # 8. Print summary statistics
    print(f"\n" + "=" * 70)
    print("SUMMARY STATISTICS")
    print("=" * 70)
    print(f"\n2024 Data:")
    print(f"  Total Transactions: {len(df_2024):,}")
    print(f"  Total Volume: {total_2024:,.2f} oz")
    print(f"  Unique Depots: {df_2024[DEPOT_COL].nunique()}")
    print(f"  Date Range: {df_2024[DATE_COL].min().date()} to {df_2024[DATE_COL].max().date()}")
    
    print(f"\n2025 Forecast:")
    print(f"  Total Transactions: {len(output_df):,}")
    print(f"  Projected Total Volume: {total_2025:,.2f} oz")
    print(f"  Unique Depots: {output_df[DEPOT_COL].nunique()}")
    print(f"  Date Range: {output_df['Date_2025'].min().date()} to {output_df['Date_2025'].max().date()}")
    print(f"  Volume Change: {((total_2025 / total_2024 - 1) * 100):+.2f}%")
    
    if missing_depots:
        print(f"\nMissing Depots (excluded from forecast):")
        print(f"  Count: {len(missing_depots)}")
        print(f"  List: {sorted(missing_depots)}")
    
    print(f"\n" + "=" * 70)
    print("✓ Forecast generation complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()

