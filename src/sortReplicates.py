# sortReplicates.py

import os
import pandas as pd
import numpy as np
from typing import Tuple


def get_percentile_data(
    df: pd.DataFrame,
    replicate_col: str = 'replicate_index',
    change_col: str = 'change_pct',
    price_col: str = None,
    lower_percentile: float = 0.0,
    upper_percentile: float = 5.0
) -> Tuple[pd.DataFrame, float]:
    """
    Extract rows corresponding to the given percentile range (lower to upper)
    from each replicate, pool them, compute the median change_pct, and return
    the selected rows sorted by date.
    """
    if not 0 <= lower_percentile < upper_percentile <= 100:
        raise ValueError("Percentiles must satisfy 0 ≤ lower < upper ≤ 100")

    selected_rows = []
    pooled_changes = []

    for _, group in df.groupby(replicate_col):
        n = len(group)
        lower_idx = int(np.floor(lower_percentile / 100 * n))
        upper_idx = int(np.ceil(upper_percentile / 100 * n))

        # Ensure at least one row if the range overlaps
        if upper_idx > lower_idx:
            percentile_rows = group.iloc[lower_idx:upper_idx]
        elif upper_idx == lower_idx and upper_idx < n:
            percentile_rows = group.iloc[lower_idx:upper_idx + 1]  # include one row
        else:
            continue

        pooled_changes.extend(percentile_rows[change_col].values)

        cols_to_keep = ['date', change_col]
        if price_col is not None:
            cols_to_keep.insert(1, price_col)

        selected_rows.append(percentile_rows[cols_to_keep])

    if not selected_rows:
        raise ValueError(f"No rows found in {lower_percentile}–{upper_percentile}th percentile range")

    selected_df = pd.concat(selected_rows, ignore_index=True)
    selected_df = selected_df.sort_values(by='date').reset_index(drop=True)
    median_change = np.median(pooled_changes)

    return selected_df, median_change


def analyze(asset1: str, asset2: str) -> None:
    print('')
    print(' --- analyzing --- ')

    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, '..', 'data')
    asset1 = asset1.lower()
    asset2 = asset2.lower()

    file_name = f"{asset1}_{asset2}_replicates.csv"
    file_path = os.path.join(data_dir, file_name)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"file not found: {file_path}")

    df = pd.read_csv(file_path)

    price_col = f'{asset1}_{asset2}_price'
    expected_cols = ['replicate_index', 'block_index', 'date', price_col, 'change_pct']
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

    # 0–5th percentile (bottom 5%)
    bottom_df, bottom_median = get_percentile_data(
        df=df_sorted,
        price_col=price_col,
        lower_percentile=0.0,
        upper_percentile=5.0
    )
    print(f"\nmedian of pooled 0–5th percentile change_pct: {bottom_median:.4f}")

    percentile_file = f"{asset1}_{asset2}_replicates_0_5_percentiles.csv"
    percentile_path = os.path.join(data_dir, percentile_file)
    bottom_df.to_csv(percentile_path, index=False)
    print(f"0–5th percentile data saved to: {os.path.abspath(percentile_path)}")
    print(f"rows in 0–5th percentile file: {len(bottom_df)}")

    # 95–100th percentile (top 5%)
    top_df, top_median = get_percentile_data(
        df=df_sorted,
        price_col=price_col,
        lower_percentile=95.0,
        upper_percentile=100.0
    )
    print(f"\nmedian of pooled 95–100th percentile change_pct: {top_median:.4f}")

    top_file = f"{asset1}_{asset2}_replicates_95_100_percentiles.csv"
    top_path = os.path.join(data_dir, top_file)
    top_df.to_csv(top_path, index=False)
    print(f"95–100th percentile data saved to: {os.path.abspath(top_path)}")
    print(f"rows in 95–100th percentile file: {len(top_df)}")


if __name__ == "__main__":
    # Example usage
    analyze("btc", "eth")
