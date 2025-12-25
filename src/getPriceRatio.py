#getPriceRatio.py

from datetime import date
import pandas as pd
import os

from getHistoricClosing import fetch_crypto_daily_closing

# Cache for loaded data: key = (asset1, asset2)
_combined_cache = {}
_price_csv_template = '{}_{}_price.csv'  # e.g., btc_eth_price.csv


def _load_data(asset1='BTC', asset2='ETH'):
    asset1_lower = asset1.lower()
    asset2_lower = asset2.lower()
    cache_key = (asset1_lower, asset2_lower)
    
    if cache_key in _combined_cache:
        return _combined_cache[cache_key]
    
    file1 = f'{asset1_lower}_daily_closing_2years.csv'
    file2 = f'{asset2_lower}_daily_closing_2years.csv'
    
    script_dir = os.path.dirname(os.path.abspath(__file__))  # directory of the current script
    data_dir = os.path.join(script_dir, '..', 'data')
    
    file1 = os.path.join(data_dir, file1)
    file2 = os.path.join(data_dir, file2)

    print("")
    print("==========================================================================================")
    print(f"calculating {asset1}/{asset2} price ratio..")
    
    if not os.path.exists(file1):
        raise FileNotFoundError(f"{asset1} file not found: {file1}")
    if not os.path.exists(file2):
        raise FileNotFoundError(f"{asset2} file not found: {file2}")
    
    # Read CSV files
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)
    
    # The second column is the price (first is 'date')
    price_col1 = df1.columns[1]  # e.g., 'btc_closing_price_usd'
    price_col2 = df2.columns[1]  # e.g., 'eth_closing_price_usd'
    
    # Set date as index
    df1 = df1.set_index('date')
    df2 = df2.set_index('date')
    
    # Extract only the price series
    price_series1 = df1[price_col1]
    price_series2 = df2[price_col2]
    
    # Combine with inner join (only common dates)
    combined = pd.concat([price_series1, price_series2], axis=1, join='inner')
    combined.columns = [asset1_lower, asset2_lower]
    
    # Calculate ratio
    combined['ratio'] = combined[asset1_lower] / combined[asset2_lower]
    
    # Save to CSV
    result_df = combined.reset_index()[['date', asset1_lower, asset2_lower, 'ratio']]
    output_csv = _price_csv_template.format(asset1_lower, asset2_lower)
  
    # change path to ../data 
    output_csv = os.path.join(data_dir, output_csv) 

    result_df.to_csv(output_csv, index=False)
    print(f"all daily prices and ratios saved to '{os.path.abspath(output_csv)}' ({len(result_df)} rows).")
    
    _combined_cache[cache_key] = combined
    return combined


def getPrice(date_str, asset1='BTC', asset2='ETH'):
    df = _load_data(asset1, asset2)
    asset1_lower = asset1.lower()
    asset2_lower = asset2.lower()
    
    if date_str not in df.index:
        print(f"Warning: Date {date_str} not found in the data for {asset1}/{asset2}.")
        return None
    
    row = df.loc[date_str]
    return {
        'date': date_str,
        asset1_lower: float(row[asset1_lower]),
        asset2_lower: float(row[asset2_lower]),
        'ratio': float(row['ratio'])
    }


def createPriceFile(asset1='BTC', asset2='ETH'):
    fetch_crypto_daily_closing(asset1)
    fetch_crypto_daily_closing(asset2)

    today = date.today().strftime('%Y-%m-%d')
    
    today_price = getPrice(today, asset1, asset2)
    
    if today_price:
        asset1_lower = asset1.lower()
        asset2_lower = asset2.lower()
        print(f"today's {asset1}/{asset2} prices:")
        print(f"{asset1}: ${today_price[asset1_lower]:,.2f}")
        print(f"{asset2}: ${today_price[asset2_lower]:,.2f}")
        print(f"{asset1}/{asset2} ratio: {today_price['ratio']:.4f}")
    else:
        print(f"Could not retrieve prices for {today}.")
