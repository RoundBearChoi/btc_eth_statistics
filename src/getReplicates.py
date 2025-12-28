import os
import pandas as pd
import math
import numpy as np

def generate_block(repIndex: int, blockIndex: int, df: pd.DataFrame, block_size: int) -> pd.DataFrame:
    """
    Generate a random wrapped block of rows from the DataFrame.
    """
    totalRows = len(df)
    rng = np.random.default_rng()
    randInt = rng.integers(0, totalRows)  # random starting row
    # Wrapped indices
    indices = [(randInt + i) % totalRows for i in range(block_size)]
    # Select rows: date, ratio, change_pct
    selected = df.iloc[indices, [0, 1, 2]].copy().reset_index(drop=True)
    selected.columns = ['date', 'ratio', 'change_pct']
    # Add replicate and block info
    selected.insert(0, 'replicate_index', repIndex)
    selected.insert(1, 'block_index', blockIndex)
    return selected

def generate_replicates(asset1: str, asset2: str, n_replicates: int = 10) -> None:
    print("")
    print(" --- generating replicates ---")
    scriptDir = os.path.dirname(os.path.abspath(__file__))
    dataDir = os.path.join(scriptDir, '..', 'data')
    asset1 = asset1.lower()
    asset2 = asset2.lower()
    input_file = f"{asset1}_{asset2}_price_change.csv"
    input_path = os.path.join(dataDir, input_file)

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"File not found: {input_path}")

    df = pd.read_csv(input_path)
    expectedCols = ['date', 'ratio', 'change_pct']
    missing = [col for col in expectedCols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")

    print(f"loaded {len(df)} rows from {os.path.abspath(input_path)}")

    # Output setup
    price_col_name = f'{asset1}_{asset2}_price'
    fieldnames = ['replicate_index', 'block_index', 'date', price_col_name, 'change_pct']

    output_file = os.path.join(dataDir, f'{asset1}_{asset2}_replicates.csv')

    # Block parameters
    total_rows = len(df)
    block_size = round(math.sqrt(total_rows))
    block_count = math.ceil(total_rows / block_size)

    print(f"total rows: {total_rows}")
    print(f"block size: {block_size}")
    print(f"number of blocks per replicate: {block_count}")
    print(f"total replicates: {n_replicates}")

    all_replicates = []

    for rep_index in range(n_replicates):
        #print(f"\ngenerating replicate {rep_index + 1}/{n_replicates}")
        replicate_blocks = []

        for block_index in range(block_count):
            block_df = generate_block(
                repIndex=rep_index,
                blockIndex=block_index,
                df=df,
                block_size=block_size
            )
            # Add the price column (same as ratio)
            block_df[price_col_name] = block_df['ratio']
            # Final column order
            final_block = block_df[['replicate_index', 'block_index', 'date', price_col_name, 'change_pct']]
            replicate_blocks.append(final_block)

            #first_date = block_df['date'].iloc[0]
            #print(f"  Block {block_index + 1}/{block_count} starting at {first_date}")

        # Combine blocks for this replicate
        replicate_df = pd.concat(replicate_blocks, ignore_index=True)
        all_replicates.append(replicate_df)

    # Combine all replicates into one big DataFrame
    full_df = pd.concat(all_replicates, ignore_index=True)

    # Save to CSV
    full_df.to_csv(output_file, index=False)

    print(f"\n{n_replicates} replicates saved to: {os.path.abspath(output_file)}")
    print(f"total rows in file: {len(full_df)}")
    print(f"rows per replicate: {len(full_df) // n_replicates}")
