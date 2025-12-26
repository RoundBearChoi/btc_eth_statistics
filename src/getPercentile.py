# src/getPercentile.py

import os
import pandas as pd

def showPercentileGraph(asset1: str, asset2: str) -> None:
    print("")
    print(" --- calculating percentiles --- ")
   
    # make sure file exists in /data
    scriptDir = os.path.dirname(os.path.abspath(__file__))
    dataDir = os.path.join(scriptDir, '..', 'data')

    asset1 = asset1.lower()
    asset2 = asset2.lower()

    fileName = f"{asset1}_{asset2}_price_change.csv"
    filePath = os.path.join(dataDir, fileName)

    if not os.path.exists(filePath):
        raise FileNotFoundError(f"file not found: {filePath}")

    df = pd.read_csv(filePath)

    expectedCols = ['date', 'ratio', 'change_pct']
    missing = [col for col in expectedCols if col not in df.columns]
    if missing:
        raise ValueError(f"missing expected column: {missing}")


