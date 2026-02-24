import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

kst_tz = pytz.timezone('Asia/Seoul')

print("Downloading hourly BTC-USD & ETH-USD data...")

# Safe start date to avoid the 730-day boundary bug
start_date = '2024-02-26'

btc_data = yf.download('BTC-USD', start=start_date, interval='1h', progress=False)
eth_data = yf.download('ETH-USD', start=start_date, interval='1h', progress=False)

def extract_kst_prices(df, asset):
    if df.empty:
        print(f"⚠️ No data for {asset}")
        return pd.DataFrame()
    
    # Convert to KST
    if df.index.tz is None:
        df.index = pd.to_datetime(df.index).tz_localize('UTC')
    df = df.tz_convert(kst_tz).copy()
    
    # Exactly 10:00 and 22:00 KST
    mask = (df.index.hour.isin([10, 22])) & (df.index.minute == 0)
    filtered = df[mask].copy()
    
    filtered['Asset'] = asset
    filtered['KST_Datetime'] = filtered.index.strftime('%Y-%m-%d %H:%M KST')
    filtered['Time_of_Day'] = filtered.index.strftime('%H:%M')
    filtered['Price'] = filtered['Open']   # price at exactly 10am/10pm KST
    
    return filtered[['KST_Datetime', 'Time_of_Day', 'Price', 'High', 'Low', 'Close', 'Volume']]

btc_prices = extract_kst_prices(btc_data, 'BTC')
eth_prices = extract_kst_prices(eth_data, 'ETH')

if btc_prices.empty and eth_prices.empty:
    print("❌ Still no data. Try running again in 5 minutes.")
else:
    combined = pd.merge(
        btc_prices[['KST_Datetime', 'Time_of_Day', 'Price']].rename(columns={'Price': 'BTC_Price'}),
        eth_prices[['KST_Datetime', 'Price']].rename(columns={'Price': 'ETH_Price'}),
        on='KST_Datetime',
        how='outer'
    ).sort_values('KST_Datetime').reset_index(drop=True)

    print(f"\n✅ Success! Total data points: {len(combined):,}")
    print("\nLast 10 rows:")
    print(combined.tail(10).to_string(index=False))

    combined.to_csv('btc_eth_prices_kst_10am_10pm_2years.csv', index=False)
    print("\n💾 Saved to: btc_eth_prices_kst_10am_10pm_2years.csv")
