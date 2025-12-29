import os
import pandas as pd
import numpy as np

def analyze(asset1: str, asset2: str) -> None:
    print('')
    print(' --- analyzing --- ')
    
    scriptDir = os.path.dirname(os.path.abspath(__file__))
    dataDir = os.path.join(scriptDir, '..', 'data')
    asset1 = asset1.lower()
    asset2 = asset2.lower()
    
    fileName = f"{asset1}_{asset2}_replicates.csv"
    filePath = os.path.join(dataDir, fileName)
    
    if not os.path.exists(filePath):
        raise FileNotFoundError(f"file not found: {filePath}")
    
    df = pd.read_csv(filePath)
    expectedCols = ['replicate_index', 'block_index', 'date', f'{asset1}_{asset2}_price', 'change_pct']
    missing = [col for col in expectedCols if col not in df.columns]
    if missing:
        raise ValueError(f"missing expected column: {missing}")

    # Sort each replicate by change_pct from lowest to highest
    df_sorted = df.sort_values(by=['replicate_index', 'change_pct'], ascending=[True, True])
    
    # Remove the block_index column
    if 'block_index' in df_sorted.columns:
        df_sorted = df_sorted.drop(columns=['block_index'])
    
    # Reset index for clean output
    df_sorted = df_sorted.reset_index(drop=True)
    
    # Save sorted replicates
    new_fileName = f"{asset1}_{asset2}_replicates_ordered.csv"
    new_filePath = os.path.join(dataDir, new_fileName)
    df_sorted.to_csv(new_filePath, index=False)
    print(f"sorted replicates saved to: {os.path.abspath(new_filePath)}")
    print(f"total rows: {len(df_sorted)}")
    print(f"number of unique replicates: {df_sorted['replicate_index'].nunique()}")
    
    # Pool all bottom 0–5th percentile change_pct values and compute median
    price_col = f'{asset1}_{asset2}_price'
    bottom_change_pcts = []
    percentile_dfs = []
    
    for _, group in df_sorted.groupby('replicate_index'):
        n = len(group)
        k = max(1, int(np.ceil(0.05 * n))) # at least 1 row
        bottom_rows = group.iloc[:k]
        # Collect change_pct values for median
        bottom_change_pcts.extend(bottom_rows['change_pct'].values)
        # Keep the rows for saving (date, price, change_pct)
        selected = bottom_rows[['date', price_col, 'change_pct']]
        percentile_dfs.append(selected)
    
    # Compute the median from all pooled bottom 0–5% values
    median_change = np.median(bottom_change_pcts)
    print(f"median of pooled 0–5th percentile change_pct values: {median_change:.4f}")
    
    # Combine and sort the bottom percentile rows for saving
    bottom_percentile_df = pd.concat(percentile_dfs, ignore_index=True)
    bottom_percentile_df = bottom_percentile_df.sort_values(by='date').reset_index(drop=True)
    
    # Save bottom 0–5th percentile data
    percentile_fileName = f"{asset1}_{asset2}_replicates_0_5_percentiles.csv"
    percentile_filePath = os.path.join(dataDir, percentile_fileName)
    bottom_percentile_df.to_csv(percentile_filePath, index=False)
    print(f"Bottom 0–5th percentile data saved to: {os.path.abspath(percentile_filePath)}")
    print(f"Total rows in percentile file: {len(bottom_percentile_df)}")
