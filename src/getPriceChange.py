# src/getPriceChange.py

import pandas as pd
import os
from getPriceRatio import createPriceFile
from getPercentile import showPercentileGraph

def generate_price_change(asset1: str, asset2: str) -> None:

    createPriceFile(asset1.upper(), asset2.upper())
    # Define paths relative to this script's location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, '..', 'data')
   
    asset1 = asset1.lower()
    asset2 = asset2.lower()

    input_filename = f"{asset1}_{asset2}_price.csv"
    input_path = os.path.join(data_dir, input_filename)

    output_filename = f"{asset1}_{asset2}_price_change.csv"
    output_path = os.path.join(data_dir, output_filename)

    # Check if input file exists
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Load the CSV
    df = pd.read_csv(input_path)
    
    # Ensure required columns exist
    expected_cols = ['date', asset1, asset2, 'ratio']
    missing = [col for col in expected_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing expected columns in input file: {missing}")
    
    # Calculate percentage change in the ratio from previous day
    df['change_pct'] = df['ratio'].pct_change() * 100
    
    # Select and reorder columns for output
    result_df = df[['date', 'ratio', 'change_pct']].copy()
    
    # Optional: round for cleaner output
    result_df['ratio'] = result_df['ratio'].round(12)
    result_df['change_pct'] = result_df['change_pct'].round(8)

    # remove day 0
    result_df = result_df.iloc[1:].reset_index(drop=True)
    print(f"{len(result_df)} rows after removing day 0")
    
    print("")
    print(" --- generating price change file ---")
    
    # Save to CSV
    result_df.to_csv(output_path, index=False)
    output_path = os.path.abspath(output_path)
    print(f"price change saved to: {output_path}")
    print("printing tail 20..")
    print(result_df.tail(20))

    showPercentileGraph(asset1, asset2)
