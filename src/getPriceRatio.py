import pandas as pd
import os

# Global variables to cache the data (loaded only once)
_combined_df = None
_price_csv_path = 'btc_eth_price.csv'  # Output file with date included

def _load_data(btc_file='btc_daily_closing_2years.csv', eth_file='eth_daily_closing_2years.csv'):
    print("==========================================================================================")
    print("calculating btc:eth price..")
    global _combined_df
    if _combined_df is not None:
        return _combined_df
    
    if not os.path.exists(btc_file):
        raise FileNotFoundError(f"BTC file not found: {btc_file}")
    if not os.path.exists(eth_file):
        raise FileNotFoundError(f"ETH file not found: {eth_file}")
    
    btc_df = pd.read_csv(btc_file)
    eth_df = pd.read_csv(eth_file)
    
    # Set date as index for fast lookup
    btc_df.set_index('date', inplace=True)
    eth_df.set_index('date', inplace=True)
    
    # Combine
    combined = pd.concat([btc_df, eth_df], axis=1)
    combined.columns = ['btc', 'eth']
    combined['ratio'] = combined['btc'] / combined['eth']
    
    # Save the price/ratio CSV WITH the date column
    result_df = combined.reset_index()[['date', 'btc', 'eth', 'ratio']]
    result_df.to_csv(_price_csv_path, index=False)
    print(f"All daily prices and ratios (with dates) saved to '{_price_csv_path}' ({len(result_df)} rows).")
    
    _combined_df = combined
    return _combined_df

def getPrice(date_str, btc_file='btc_daily_closing_2years.csv', eth_file='eth_daily_closing_2years.csv'):
    """
    Get BTC price, ETH price, and BTC/ETH ratio for a specific date.
    
    Args:
        date_str (str): Date in 'YYYY-MM-DD' format (e.g., '2025-12-24')
        btc_file (str): Path to BTC CSV file
        eth_file (str): Path to ETH CSV file
    
    Returns:
        dict or None: {'date': str, 'btc': float, 'eth': float, 'ratio': float}
                      Returns None if date not found.
    """
    df = _load_data(btc_file, eth_file)
    
    if date_str not in df.index:
        print(f"Warning: Date {date_str} not found in the data.")
        return None
    
    row = df.loc[date_str]
    return {
        'date': date_str,
        'btc': float(row['btc']),
        'eth': float(row['eth']),
        'ratio': float(row['ratio'])
    }

# Example usage when running the script directly
if __name__ == "__main__":
    # This will trigger data loading and CSV creation
    today_price = getPrice('2025-12-24')
    if today_price:
        print("\nCurrent prices (December 24, 2025):")
        print(f"BTC: ${today_price['btc']:,.2f}")
        print(f"ETH: ${today_price['eth']:,.2f}")
        print(f"BTC/ETH ratio: {today_price['ratio']:.4f}")
    
    # Example historical lookup
    print("\nHistorical example:")
    print(getPrice('2023-11-26'))
