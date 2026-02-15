import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import timezone

# Pool details
pool_address = "0x8c7080564b5a792a33ef2fd473fba6364d5495e5".lower()
network = "base"
timeframe = "hour"

# API endpoint
url = f"https://api.geckoterminal.com/api/v2/networks/{network}/pools/{pool_address}/ohlcv/{timeframe}"

params = {
    "limit": 168,
    "currency": "usd"
}

response = requests.get(url, params=params)

if response.status_code != 200:
    print("Error fetching data:", response.status_code, response.text)
else:
    data = response.json()
    ohlcv_list = data["data"]["attributes"]["ohlcv_list"]
    
    # Create DataFrame: [timestamp, open, high, low, close, volume_usd]
    df = pd.DataFrame(ohlcv_list, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    # Convert timestamp to datetime (UTC)
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s', utc=True)
    df = df.sort_values('datetime').reset_index(drop=True)
    
    # Human-readable hour string
    df['hour_str'] = df['datetime'].dt.strftime('%Y-%m-%d %H:00')
    
    # Daily grouping
    df['date'] = df['datetime'].dt.date
    daily = df.groupby('date')['volume'].sum().reset_index()
    daily['volume'] = daily['volume'].round(2)
    
    # Print hourly table
    print("Hourly Transaction Volume (USD) for cbBTC/WETH Uniswap V3 Pool on Base")
    print("-" * 70)
    print(f"{'Time (UTC)':<20} {'Volume (USD)':>15}")
    print("-" * 70)
    for _, row in df.iterrows():
        print(f"{row['hour_str']:<20} ${row['volume']:>14,.2f}")
    print("-" * 70)
    
    # Print daily summary
    print("\nDaily Total Volume (USD)")
    print("-" * 40)
    print(f"{'Date':<12} {'Daily Volume (USD)':>20}")
    print("-" * 40)
    for _, row in daily.iterrows():
        print(f"{str(row['date']):<12} ${row['volume']:>19,.2f}")
    print("-" * 40)
    
    total_volume = df['volume'].sum()
    print(f"Total volume over period: ${total_volume:,.2f}")
    print(f"Data points: {len(df)} hours")
    
    # Save to CSV (optional – comment out if not needed)
    df[['datetime', 'open', 'high', 'low', 'close', 'volume']].to_csv('cbbtc_weth_hourly_volume.csv', index=False)
    print("\nHourly data saved to 'cbbtc_weth_hourly_volume.csv'")
    
    # Plot 1: Hourly volume (line chart)
    plt.figure(figsize=(16, 6))
    plt.plot(df['datetime'], df['volume'], linewidth=1)
    plt.title('Hourly Transaction Volume (USD) – cbBTC/WETH on Base')
    plt.xlabel('Time (UTC)')
    plt.ylabel('Volume (USD)')
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show(block=False)
    
    # Plot 2: Daily total volume (bar chart)
    plt.figure(figsize=(10, 6))
    plt.bar(daily['date'].astype(str), daily['volume'], color='skyblue', edgecolor='navy')
    plt.title('Daily Total Transaction Volume (USD) – cbBTC/WETH on Base')
    plt.xlabel('Date')
    plt.ylabel('Daily Volume (USD)')
    plt.grid(True, axis='y', alpha=0.3)
    for i, v in enumerate(daily['volume']):
        plt.text(i, v + total_volume*0.01, f'${v:,.0f}', ha='center', va='bottom', fontsize=9)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show(block=True)
