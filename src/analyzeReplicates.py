# analyzeReplicates.py

import os
import pandas as pd
import numpy as np


def analyze_reps(asset1: str, asset2: str) -> None:
    print('')
    print(' --- analyzing replicates --- ')
    
    scriptDir = os.path.dirname(os.path.abspath(__file__))
    dataDir = os.path.join(scriptDir, '..', 'data')
    asset1 = asset1.lower()
    asset2 = asset2.lower()

    fileName = f'{asset1}_{asset2}_replicates_ordered.csv'
    filePath = os.path.join(dataDir, fileName)

    if not os.path.exists(filePath):
        raise FileNotFoundError(f'file not found: {filePath}')

    df = pd.read_csv(filePath)

    expectedCols = ['replicate_index','date',f'{asset1}_{asset2}_price','change_pct']
    missing = [col for col in expectedCols if col not in df.columns]
    if missing:
        raise ValueError(f'missing expected column: {missing}')

    # get 0~5th percentile from each replicate_index and save to asset1_asset2_0_5_replicates_ordered.csv

    # get 95~100th percentile from each replicate_index and save to asset1_asset2_95_100_replicates_ordered.csv


if __name__ == '__main__':
    analyze_reps('btc', 'eth')
