# getReplicates.py

import os
import csv
import pandas as pd
import math
import numpy as np

def generate_replicates(asset1: str, asset2: str) -> None:
    print("")
    print(" --- generating replicates ---")
    
    scriptDir = os.path.dirname(os.path.abspath(__file__))
    dataDir = os.path.join(scriptDir, '..', 'data')

    asset1 = asset1.lower()
    asset2 = asset2.lower()

    fileName = f"{asset1}_{asset2}_price_change.csv"
    filePath = os.path.join(dataDir,fileName)

    if not os.path.exists(filePath):
        raise FileNotFoundError(f"file not found: {filePath}")

    df = pd.read_csv(filePath)
    
    expectedCols = ['date', 'ratio', 'change_pct']
    missing = [col for col in expectedCols if col not in df.columns]
    if missing:
        raise ValueError(f"missing expected column: {missing}")

    print(f"loaded {os.path.abspath(filePath)}")

    # create {asset1}_{asset2}_replicates.csv under /data
    # headers replicate_index,block_index,date_index,{asset1}_{asset2}_price,change_pct
    fieldnames = ['replicate_index', 'block_index', 'date_index', f'{asset1}_{asset2}_price', 'change_pct']
    with open(os.path.join(dataDir, f'{asset1}_{asset2}_replicates.csv'), 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

    # write data
    blockCount = math.ceil(len(df) / round(math.sqrt(len(df))))

    for i in range(blockCount):
        generate_block(0, i, df)


def generate_block(repIndex: int, blockIndex: int, df: pd.DataFrame) -> None:
    totalRows = len(df)
    heuristics = round(math.sqrt(totalRows))

    rng = np.random.default_rng()
    randInt = rng.integers(0, totalRows)

    print("")
    print(f"generated randInt between 0 to {totalRows}: {randInt}")

    for i in range(heuristics):
        idx = (randInt + i) % totalRows  # modular arithmetic handles the wrap-around
        row_str = ', '.join(df.iloc[idx].astype(str))
        print(f"block {blockIndex}, index {idx}, {row_str}")

