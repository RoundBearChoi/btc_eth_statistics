#getPriceRatio.py

from datetime import date
from downloadPriceData import download_crypto_daily_closing
import pandas as pd
import os


# Cache for loaded data: key = (asset1, asset2)
_combined_cache = {}
_price_csv_template = '{}_{}_price.csv'  # e.g., btc_eth_price.csv


def get_price_ratio(asset1='btc', asset2='eth'):
    asset1_lower = asset1.lower()
    asset2_lower = asset2.lower()
    cache_key = (asset1_lower, asset2_lower)
    
    if cache_key in _combined_cache:
        return _combined_cache[cache_key]
    
    file1 = f'{asset1_lower}_daily_closing_2years.csv'
    file2 = f'{asset2_lower}_daily_closing_2years.csv'
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, '..', 'data')
    
    file1 = os.path.join(data_dir, file1)
    file2 = os.path.join(data_dir, file2)

    print("")
    print(f" --- calculating {asset1}/{asset2} price ratio ---")
    
    if not os.path.exists(file1):
        raise FileNotFoundError(f"{asset1} file not found: {file1}")
    if not os.path.exists(file2):
        raise FileNotFoundError(f"{asset2} file not found: {file2}")
    
    # Read CSV files
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)
   
    print('')
    print(df1)

    print('')
    print(df2)

    # second column is the price (first is 'date')
    price_col1 = df1.columns[1]
    price_col2 = df2.columns[1]
    
    # set date as index
    df1 = df1.set_index('date')
    df2 = df2.set_index('date')
    
    # extract only the price series
    price_series1 = df1[price_col1]
    price_series2 = df2[price_col2]
    
    # combine with inner join (only common dates)
    combined = pd.concat([price_series1, price_series2], axis=1, join='inner')
   
    print('')
    print(combined)

    combined.columns = [asset1_lower, asset2_lower]
    
    # calculate price ratio
    combined['ratio'] = combined[asset1_lower] / combined[asset2_lower]

    # save to CSV
    result_df = combined.reset_index()[['date', asset1_lower, asset2_lower, 'ratio']]

    print('')
    print(result_df)

    output_csv = _price_csv_template.format(asset1_lower, asset2_lower)
  
    # change path to ../data 
    output_csv = os.path.join(data_dir, output_csv) 

    result_df.to_csv(output_csv, index=False)

    print('')
    print(f'daily prices and ratios saved to {os.path.abspath(output_csv)}')


if __name__ == '__main__':
    get_price_ratio('btc', 'eth')
