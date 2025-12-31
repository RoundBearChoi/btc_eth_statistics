# drawGraphOnReplicates

import pandas as pd
import matplotlib.pyplot as plt
from loadCSV import load_from_file as _load


def draw(asset1: str, asset2: str) -> None:
    print('')
    print(' --- drawing graphs on replicates --- ')

    df = _load(f'{asset1}_{asset2}_lower_ordered.csv', ['replicate_index', 'lower_5th_pct'])

    print(df)
    # Use a simple sequential x-axis (0, 1, 2, ...) since we're not using replicate_index
    x = range(len(df))
    
    # Calculate the median of the lower_5th_pct values
    median_value = df['lower_5th_pct'].median()
    
    # Create the plot
    plt.figure(figsize=(12, 6))
    plt.bar(x, df['lower_5th_pct'], color='skyblue', edgecolor='navy', alpha=0.8)
    
    # Horizontal line for the median
    plt.axhline(y=median_value, color='red', linestyle='--', linewidth=2,
                label=f'Median = {median_value:.6f}')
    
    # Labels and title
    plt.xlabel('Replicate (in original order from file)')
    plt.ylabel('Lower 5th Percentile Value')
    plt.title(f'Lower 5th Percentile across Replicates\n{asset1.upper()} vs {asset2.upper()}')
    
    # Add grid for better readability
    plt.grid(True, axis='y', linestyle=':', alpha=0.7)
    
    # Legend
    plt.legend()
    
    # Optional: tighten layout
    plt.tight_layout()
    
    # Show the plot
    plt.show()


if __name__ == '__main__':
    draw('btc', 'eth')
