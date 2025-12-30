# analyzeReplicates.py

import pandas as pd
from loadCSV import load_from_file as _load


def get_upper_lower(asset1: str, asset2: str) -> None:
    print('')
    print(' --- getting upper lower of replicates --- ')
    
    df = _load(f'{asset1}_{asset2}_replicates_ordered.csv', ['replicate_index', 'date', f'{asset1}_{asset2}_price', 'change_pct'])

    # get 0~5th percentile from each replicate_index

    # get 95~100th percentile from each replicate_index


if __name__ == '__main__':
    get_upper_lower('btc', 'eth')
