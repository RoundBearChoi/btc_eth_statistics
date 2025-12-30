# analyzeReplicates.py

import pandas as pd
from loadCSV import load_from_file as _load


def analyze_reps(asset1: str, asset2: str) -> None:
    print('')
    print(' --- analyzing replicates --- ')
    
    df = _load(f'{asset1}_{asset2}_replicates_ordered.csv', ['replicate_index', 'date', f'{asset1}_{asset2}_price', 'change_pct'])

    # get 0~5th percentile from each replicate_index and save to asset1_asset2_0_5_replicates_ordered.csv

    # get 95~100th percentile from each replicate_index and save to asset1_asset2_95_100_replicates_ordered.csv


if __name__ == '__main__':
    analyze_reps('btc', 'eth')
