'''
# main.py
from geckoTerminalAPI import get_supported_networks
from fetchTokenPrice import print_token_price

def print_supported_networks():
    print("\n==================================================\n")
   
    print("Fetching supported networks...\n")
    networks = get_supported_networks()
    print("Supported Networks:")
    for network in networks:
        name = network["attributes"]["name"]
        print(f"- {name}")

def print_btc_eth_price():
    print("\n==================================================\n")
    
    tokens = [
        ("eth", "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2", "ETH"),   # WETH on Ethereum
        ("eth", "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599", "BTC"),   # WBTC on Ethereum
    ]

    for network, address, name in tokens:
        print(f"Fetching current {name} price...")
        print_token_price(network, address, name)
        print()  # Empty line for readability

def main():
    print_supported_networks()
    print_btc_eth_price()

if __name__ == "__main__":
    print("\n==================================================\n")
   
    # Capture and print the default User-Agent used by requests (as in your original script)
    import requests
    print("Sent User-Agent:", requests.utils.default_user_agent())
    print()
    main()
'''


import requests
import csv
from datetime import datetime, timedelta

# API endpoint
url = "https://min-api.cryptocompare.com/data/v2/histoday"

# Parameters to get all historical daily data for BTC/USD
params = {
    'fsym': 'BTC',
    'tsym': 'USD',
    'allData': 'true'  # Fetches all available history
}

print("making request on cryptocompare..")

# Make the request
response = requests.get(url, params=params)
data = response.json()

if data['Response'] != 'Success':
    raise Exception(f"API error: {data.get('Message', 'Unknown error')}")

# Extract the list of daily data points
daily_data = data['Data']['Data']

# Calculate timestamp for ~2 years ago (730 days)
two_years_ago = int((datetime.now() - timedelta(days=730)).timestamp())

# Filter to the last 2 years
recent_data = [entry for entry in daily_data if entry['time'] >= two_years_ago]

print(f"Fetched {len(daily_data)} total daily points.")
print(f"Filtered to {len(recent_data)} points for the last ~2 years.")

# Write to CSV
csv_filename = 'btc_daily_closing_2years.csv'
with open(csv_filename, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['date', 'btc_closing_price_usd'])  # Header
    for entry in recent_data:
        date_str = datetime.fromtimestamp(entry['time']).strftime('%Y-%m-%d')
        closing_price = entry['close']
        writer.writerow([date_str, closing_price])

print(f"Data saved to {csv_filename}")
