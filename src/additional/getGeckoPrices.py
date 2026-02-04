import requests
from datetime import datetime, timezone
import pandas as pd
import time

# List of assets (symbols lowercase)
assets = ['cbbtc', 'weth', 'cake']

# Preferred name fragments for disambiguation (lowercase)
preferred_names = {
    'cbbtc': 'coinbase wrapped btc',
    'weth': 'wrapped ether',
    'cake': 'pancakeswap'
}

# Fetch full coins list for dynamic ID lookup
coins_list_url = "https://api.coingecko.com/api/v3/coins/list"
try:
    response = requests.get(coins_list_url)
    response.raise_for_status()
    coins_list = response.json()
    print("Fetched CoinGecko coins list for dynamic ID mapping.\n")
except Exception as e:
    coins_list = []
    print(f"Failed to fetch coins list ({e}), falling back to hardcoded IDs if needed.\n")

# Fallback hardcoded IDs (in case list fetch fails)
fallback_id_map = {
    'cbbtc': 'coinbase-wrapped-btc',
    'weth': 'weth',
    'cake': 'pancakeswap'
}

# Dictionary to hold daily closing prices {symbol: {date: price}}
raw_data = {}

print("Fetching data from CoinGecko...\n")

for symbol in assets:
    # Dynamic ID lookup
    if coins_list:
        candidates = [c for c in coins_list if c['symbol'] == symbol.lower()]
        if candidates:
            preferred = preferred_names.get(symbol, '').lower()
            matching = [c for c in candidates if preferred in c['name'].lower() or preferred in c['id']]
            if matching:
                coin_id = matching[0]['id']
            else:
                coin_id = candidates[0]['id']  # fallback to first
                print(f"Multiple matches for {symbol.upper()}, using {coin_id} ({candidates[0]['name']})")
        else:
            coin_id = fallback_id_map.get(symbol)
            print(f"No match found for {symbol.upper()} in coins list, trying fallback ID {coin_id}")
    else:
        coin_id = fallback_id_map.get(symbol)
    
    if not coin_id:
        print(f"No CoinGecko ID available for {symbol.upper()}")
        continue
    
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        'vs_currency': 'usd',
        'days': '10'
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        json_data = response.json()
        prices = json_data['prices']  # List of [timestamp_ms, price]
        
        daily_closes = {}
        for timestamp_ms, price in prices:
            # Fixed deprecation: use timezone-aware UTC
            date = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc).date()
            daily_closes[date] = price  # Latest price per day = "close"
        
        raw_data[symbol.upper()] = daily_closes  # Use uppercase symbol in output
        print(f"Fetched data for {symbol.upper()} ({coin_id})")
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"404 Error for {symbol.upper()} ({coin_id}): Coin ID may be invalid or temporarily unavailable.")
        else:
            print(f"Error fetching {symbol.upper()}: {e}")
    except Exception as e:
        print(f"Unexpected error for {symbol.upper()}: {e}")
    
    time.sleep(1.5)  # Slightly longer delay to be extra safe with rate limits

# Create DataFrame if we have data
if raw_data:
    df = pd.DataFrame(raw_data)
    
    # Convert index to datetime and sort descending
    df.index = pd.to_datetime(df.index)
    df = df.sort_index(ascending=False)
    
    # Limit to most recent 10 days (will include NaN for assets with shorter history)
    df = df.head(10)
    
    # Round and format
    df = df.round(2)
    
    print("\nRecent 10-day historical closing prices (USD, latest price per UTC day):")
    print(df)
else:
    print("No data was fetched.")
