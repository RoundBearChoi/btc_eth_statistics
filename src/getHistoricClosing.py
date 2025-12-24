#getHistoricClosing.py

import requests
import csv
from datetime import datetime, timedelta
import os

def fetch_crypto_daily_closing(
    crypto_symbol: str,
    fiat_symbol: str = 'USD',
    years: int = 2,
    filename: str = None
) -> str:
    """
    Fetches daily closing prices for a cryptocurrency over the specified number of years
    from CryptoCompare and saves them to a CSV file.
    Also prints the latest available closing price.
    """
    # Auto-generate filename if not provided
    if filename is None:
        filename = f"{crypto_symbol.lower()}_daily_closing_{years}years.csv"
   
    if not filename.lower().endswith('.csv'):
        filename += '.csv'

    url = "https://min-api.cryptocompare.com/data/v2/histoday"
   
    params = {
        'fsym': crypto_symbol.upper(),
        'tsym': fiat_symbol.upper(),
        'allData': 'true'
    }
    print("==========================================================================================")
    print(f"Fetching historical daily data for {crypto_symbol}/{fiat_symbol} from CryptoCompare...")
   
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Request failed: {e}")
   
    if data['Response'] != 'Success':
        raise Exception(f"API error: {data.get('Message', 'Unknown error')}")
    
    daily_data = data['Data']['Data']
   
    if not daily_data:
        raise Exception("No data returned from the API.")

    # Sort just in case (normally already chronological)
    daily_data.sort(key=lambda x: x['time'])
    
    # Calculate cutoff for filtering
    cutoff_days = years * 365 + 30
    cutoff_time = int((datetime.now() - timedelta(days=cutoff_days)).timestamp())
    recent_data = [entry for entry in daily_data if entry['time'] >= cutoff_time]

    # Get the latest entry (last in the full dataset)
    latest_entry = daily_data[-1]
    latest_date = datetime.fromtimestamp(latest_entry['time']).strftime('%Y-%m-%d')
    latest_price = latest_entry['close']
    
    print(f"Latest closing price: {latest_price:,.2f} {fiat_symbol.upper()} on {latest_date} (00:00 UTC)")

    print("==========================================================================================")
    print(f"Fetched {len(daily_data)} total daily points.")
    print(f"Filtered to {len(recent_data)} points for the last ~{years} years.")

    # Write to CSV
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['date', f'{crypto_symbol.lower()}_closing_price_{fiat_symbol.lower()}'])
       
        for entry in recent_data:
            date_str = datetime.fromtimestamp(entry['time']).strftime('%Y-%m-%d')
            closing_price = entry['close']
            writer.writerow([date_str, closing_price])

    full_path = os.path.abspath(filename)
    print(f"Data successfully saved to: {full_path}")
   
    return full_path
