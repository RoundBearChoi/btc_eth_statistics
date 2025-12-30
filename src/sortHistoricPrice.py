# src/getPercentile.py

#import os
import pandas as pd
#import matplotlib.pyplot as plt
#import datetime

from loadCSV import load_from_file as _load
from saveCSV import save_to_file as _save


def sort_historic_price(asset1: str, asset2: str) -> None:
    print('')
    print(' --- sorting historic price --- ')
    
    df = _load(f'{asset1}_{asset2}_price_change.csv', ['date', 'ratio', 'change_pct'])

    print(f'sorting {len(df)} rows..')

    df_sorted = df.sort_values(by='change_pct', ascending=True)
  
    _save(df_sorted, f'{asset1}_{asset2}_price_change_ordered.csv')

    '''
    # create bar graph
    plt.figure(figsize=(14, 7))
    bars = plt.bar(range(len(df_sorted)), df_sorted['change_pct'], color='skyblue', edgecolor='navy', linewidth=0.5)
    
    # highlight negative and positive bars
    for bar in bars:
        if bar.get_height() < 0:
            bar.set_color('salmon')
    
    plt.title(f'{asset1.upper()} vs {asset2.upper()} - Daily Price Change % (Sorted Lowest to Highest)', fontsize=16)
    #plt.xlabel('Sorted Day Index (1 = worst day, last = best day)', fontsize=12)
    plt.ylabel('Price Change %', fontsize=12)
    plt.axhline(0, color='black', linewidth=1)
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # get current date and time
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # title with current date/time
    plt.title(f'{asset1.upper()} vs {asset2.upper()} - Daily Price Change % - {current_time}', fontsize=15)
    
    plt.ylabel('Price Change %', fontsize=12)
    plt.axhline(0, color='black', linewidth=1)
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # add percentile lines
    p5 = df_sorted['change_pct'].quantile(0.05)
    p95 = df_sorted['change_pct'].quantile(0.95)
    plt.axhline(p5, color='red', linestyle='--', label='5th percentile')
    plt.axhline(p95, color='red', linestyle='--', label='95th percentile')
    
    # add text labels next to the lines (placed at the right edge of the plot)
    plt.text(len(df_sorted) - 0.5, p5, f'  5th percentile: {p5:+.3f}%', 
             va='center', ha='left', color='red', fontsize=10, fontweight='bold',
             bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=3))

    plt.text(len(df_sorted) - 0.5, p95, f'  95th percentile: {p95:+.3f}%', 
             va='center', ha='left', color='red', fontsize=10, fontweight='bold',
             bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=3))

    plt.tight_layout()
    graph_file = f"{asset1}_{asset2}_change_pct_bargraph.png"
    graph_path = os.path.join(dataDir, graph_file)
    plt.savefig(graph_path)
    print(f"\nbar graph saved to: {os.path.abspath(graph_path)}")
    plt.show(block=blockOnGraph)
    '''


if __name__ == '__main__':
    sort_historic_price('btc', 'eth')
