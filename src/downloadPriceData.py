#downloadPriceData.py

import requests
import csv
import os
from datetime import datetime, timedelta


def download_crypto_daily_closing(crypto_symbol: str, fiat_symbol: str = 'usd', years: int = 2) -> None:
    print("")
    print(f" --- downloading {crypto_symbol}/{fiat_symbol} data from cryptocompare ---")
    
    filename = f"{crypto_symbol.lower()}_daily_closing_{years}years.csv"
    url = "https://min-api.cryptocompare.com/data/v2/histoday"
   
    params = {
        'fsym': crypto_symbol.upper(),
        'tsym': fiat_symbol.upper(),
        'allData': 'true'
    }
   
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"request failed: {e}")
   
    if data['Response'] != 'Success':
        raise Exception(f"API error: {data.get('Message', 'Unknown error')}")
    
    daily_data = data['Data']['Data']
   
    if not daily_data:
        raise Exception("no data returned from the API.")

    # sort just in case (normally already chronological)
    daily_data.sort(key=lambda x: x['time'])
    
    # calculate cutoff for filtering
    '''
    get slightly more than requested years, avoiding edge cases where you might miss a few days due to the rough 365-day approximation (leap years, etc.).
    '''
    cutoff_days = years * 365 + 30
    cutoff_time = int((datetime.now() - timedelta(days=cutoff_days)).timestamp())
    recent_data = [entry for entry in daily_data if entry['time'] >= cutoff_time]

    # get the latest entry (last in the full dataset)
    latest_entry = daily_data[-1]
    latest_date = datetime.fromtimestamp(latest_entry['time']).strftime('%Y-%m-%d')
    latest_price = latest_entry['close']
    
    print(f"latest closing price: ${latest_price:,.2f} on {latest_date} (00:00 UTC)")
    print(f"fetched {len(daily_data)} total daily points")
    print(f"filtered to {len(recent_data)} points for the last ~{years} years")

    # build path to parallel /data folder
    # get the directory where this script is located (more reliable than cwd)
    script_dir = os.path.dirname(os.path.abspath(__file__))  # directory of the current script
    data_dir = os.path.join(script_dir, '..', 'data')

    # create the data directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)

    # full path for the CSV file inside the data folder
    csv_filepath = os.path.join(data_dir, filename)
    csv_filepath = csv_filepath.lower()

    # write to CSV
    with open(csv_filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['date', f'{crypto_symbol.lower()}_closing_price_{fiat_symbol.lower()}'])
        
        for entry in recent_data:
            date_str = datetime.fromtimestamp(entry['time']).strftime('%Y-%m-%d')
            closing_price = entry['close']
            writer.writerow([date_str, closing_price])

    # get absolute path for printing
    full_path = os.path.abspath(csv_filepath)
    print(f"data saved to: {full_path}")


if __name__ == '__main__':
    download_crypto_daily_closing('btc')
