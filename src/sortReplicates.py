#scr/sortReplicates

import os
import pandas as pd

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


