# sortReplicates.py

import os
import pandas as pd
import numpy as np
from analyzeReplicates import analyze_reps


def sort_reps(asset1: str, asset2: str) -> None:
    print('')
    print(' --- sorting replicates --- ')

    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, '..', 'data')
    asset1 = asset1.lower()
    asset2 = asset2.lower()

    file_name = f"{asset1}_{asset2}_replicates.csv"
    file_path = os.path.join(data_dir, file_name)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"file not found: {file_path}")

    df = pd.read_csv(file_path)

    expected_cols = ['replicate_index', 'block_index', 'date', f'{asset1}_{asset2}_price', 'change_pct']
    missing = [col for col in expected_cols if col not in df.columns]
    if missing:
        raise ValueError(f"missing expected column(s): {missing}")

    # Sort each replicate by change_pct (lowest to highest)
    df_sorted = df.sort_values(by=['replicate_index', 'change_pct'], ascending=[True, True])

    # Drop block_index if present
    if 'block_index' in df_sorted.columns:
        df_sorted = df_sorted.drop(columns=['block_index'])

    df_sorted = df_sorted.reset_index(drop=True)

    # Save fully sorted replicates
    sorted_file = f"{asset1}_{asset2}_replicates_ordered.csv"
    sorted_path = os.path.join(data_dir, sorted_file)
    df_sorted.to_csv(sorted_path, index=False)
    print(f"sorted replicates saved to: {os.path.abspath(sorted_path)}")
    print(f"total rows: {len(df_sorted)}")
    print(f"unique replicates: {df_sorted['replicate_index'].nunique()}")

    analyze_reps(asset1, asset2)


if __name__ == "__main__":
    sort_reps("btc", "eth")
