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
    
    # Sort each replicate by change_pct from lowest to highest
    df_sorted = df.sort_values(by=['replicate_index', 'change_pct'], ascending=[True, True])
    
    # Remove the block_index column
    if 'block_index' in df_sorted.columns:
        df_sorted = df_sorted.drop(columns=['block_index'])
    
    # Reset index for clean output
    df_sorted = df_sorted.reset_index(drop=True)
    
    # Save to new file without block_index
    new_fileName = f"{asset1}_{asset2}_replicates_ordered.csv"
    new_filePath = os.path.join(dataDir, new_fileName)
    df_sorted.to_csv(new_filePath, index=False)
    
    print(f"sorted replicates saved to: {os.path.abspath(new_filePath)}")
    print(f"total rows: {len(df_sorted)}")
    print(f"number of unique replicates: {df_sorted['replicate_index'].nunique()}")
