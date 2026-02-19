import requests
import csv
import os
import pandas as pd
from loadCSV import load_from_file as _load
from saveCSV import save_to_file as _save
from datetime import datetime, timedelta, timezone


def download_new_file(fileName: str, cryptoSymbol: str) -> bool:
    existingDF = _load(fileName, ['date',f'{cryptoSymbol.lower()}_closing_price_usd'])

    if existingDF.empty:
        print('no existing data.. downloading new data..')
        return True

    latest = existingDF.iloc[-1]['date']
    latestDate = datetime.fromisoformat(latest).date()
    print(f'latest entry(utc): {latestDate}')

    currentUTC = datetime.now(timezone.utc).date()
    print(f'current utc: {currentUTC}')

    if latestDate < currentUTC:
        print('data is behind.. downloading new data..')
        return True
    else:
        print('data is up to date.. no need to download..')
        return False


def download_crypto_daily_closing(crypto_symbol: str, fiat_symbol: str = 'usd', years: int = 2) -> None:
    print('')
    print(f' --- checking data on {crypto_symbol} --- ')

    #fileName = f'{crypto_symbol.lower()}_daily_closing_{years}years.csv'
    fileName = f'{crypto_symbol.lower()}_daily_closing.csv'

    if not download_new_file(fileName, crypto_symbol):
        # skip download if existing data is good
        return
    
    params = {
        'fsym': crypto_symbol.upper(),
        'tsym': fiat_symbol.upper(),
        'allData': 'true'
    }
    
    url = 'https://min-api.cryptocompare.com/data/v2/histoday'
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f'request failed: {e}')
   
    if data['Response'] != 'Success':
        raise Exception(f'API error: {data.get('Message', 'Unknown error')}')
    
    daily_data = data['Data']['Data']
   
    if not daily_data:
        raise Exception('no data returned from the API')

    # sort just in case (normally already chronological)
    daily_data.sort(key=lambda x: x['time'])

    # calculate cutoff for filtering
    # get slightly more than requested years, avoiding edge cases where you might miss a few days due to the rough 365-day approximation (leap years, etc.).
    cutoff_days = years * 365 + 30
    cutoff_time = int((datetime.now() - timedelta(days=cutoff_days)).timestamp())
    recent_data = [entry for entry in daily_data if entry['time'] >= cutoff_time]

    # get latest entry (just to print)
    latest_entry = daily_data[-1]
    latest_date = datetime.fromtimestamp(latest_entry['time']).strftime('%Y-%m-%d')
    latest_price = latest_entry['close']

    print('')
    print(f'latest closing price: ${latest_price:,.2f} on {latest_date} (00:00 UTC)')
    print(f'fetched {len(daily_data)} total daily points')
    print(f'filtered to {len(recent_data)} points for the last ~{years} years')

    # convert to DataFrame and save to file
    rows = []
    for entry in recent_data:
        date_str = datetime.fromtimestamp(entry['time']).strftime('%Y-%m-%d')
        price = entry['close']
        rows.append({'date': date_str, f'{crypto_symbol.lower()}_closing_price_usd': price})

    df = pd.DataFrame(rows)

    _save(df, fileName)


if __name__ == '__main__':
    download_crypto_daily_closing('btc')
