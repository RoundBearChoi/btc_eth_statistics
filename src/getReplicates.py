# getReplicates.py

import os
import pandas as pd
import math

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

    totalRows = len(df)
    heuristics = round(math.sqrt(totalRows))
    print(f"loaded {os.path.abspath(filePath)}")
    print(f"total rows: {totalRows}.. heuristics: {heuristics}..")



