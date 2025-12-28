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
        print("")
        print(generate_block(0, i, df))


def generate_block(repIndex: int, blockIndex: int, df: pd.DataFrame) -> pd.DataFrame:
    totalRows = len(df)
    heuristics = round(math.sqrt(totalRows))
    rng = np.random.default_rng()
    randInt = rng.integers(0, totalRows)  # starting row index (0 to totalRows-1)
    
    # Compute the wrapped indices
    indices = [(randInt + i) % totalRows for i in range(heuristics)]
    
    # Select the consecutive (wrapped) rows from df (only the 3 columns you need: 0,1,2)
    selected = df.iloc[indices, [0, 1, 2]].reset_index(drop=True)
    
    # Add the repIndex and blockIndex as new columns (same value for all rows in this block)
    selected.insert(0, 'repIndex', repIndex)
    selected.insert(1, 'blockIndex', blockIndex)
    
    return selected
