# drawGraphOnReplicates

import pandas as pd
import matplotlib.pyplot as plt
from loadCSV import load_from_file as _load


def draw(asset1: str, asset2: str) -> None:
    print('')
    print(' --- drawing graphs on replicates --- ')

    df = _load(f'{asset1}_{asset2}_lower_ordered.csv', ['replicate_index', 'lower_5th_pct'])

    # use a simple sequential x-axis (0, 1, 2, ...) since we're not using replicate_index
    x = range(len(df))
    

    
    # create the plot
    plt.figure(figsize=(12, 6))
    plt.bar(x, df['lower_5th_pct'], color='skyblue', edgecolor='navy', alpha=0.8)
    
    # horizontal line for the median
    median_value = df['lower_5th_pct'].median()
    
    plt.axhline(y=median_value, color='red', linestyle='--', linewidth=2,
                label=f'Median = {median_value:.6f}')
    
    # labels and title
    plt.xlabel('ordered replicates')
    plt.ylabel('lower 5th percentile values')
    plt.title(f'{asset1}-{asset2} lower 5th percentiles')
    
    # add grid for better readability
    plt.grid(True, axis='y', linestyle=':', alpha=0.7)
    
    plt.legend()
    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    draw('btc', 'eth')
