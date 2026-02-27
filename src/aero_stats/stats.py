import requests
import pandas as pd
from datetime import datetime
import time

def fetch_ohlcv(pool_address, currency="usd", aggregate=15, limit=500, before_ts=None):
    url = f"https://api.geckoterminal.com/api/v2/networks/base/pools/{pool_address}/ohlcv/minute"
    params = {
        "aggregate": aggregate,
        "limit": limit,
        "currency": currency
    }
    if before_ts:
        params["before_timestamp"] = before_ts
    r = requests.get(url, params=params)
    if r.status_code != 200:
        print(f"Error {r.status_code} for currency={currency}: {r.text}")
        return None
    data = r.json()
    return data.get("data", {}).get("attributes", {}).get("ohlcv_list", [])

def get_full_history(pool_address):
    all_usd = []
    all_ratio = []
    before_ts = None
    page = 0
    
    print("Fetching full 15-min history (USD + WETH/cbBTC ratio)...")
    while page < 100:
        print(f"  Page {page+1}...")
        batch_usd = fetch_ohlcv(pool_address, currency="usd", before_ts=before_ts)
        batch_ratio = fetch_ohlcv(pool_address, currency="token", before_ts=before_ts)
        
        if not batch_usd or not batch_ratio:
            break
            
        all_usd.extend(batch_usd)
        all_ratio.extend(batch_ratio)
        
        before_ts = batch_usd[-1][0] - 1
        if len(batch_usd) < 400:
            break
        time.sleep(1.2)
        page += 1
    
    # Build DataFrame
    df_usd = pd.DataFrame(all_usd, columns=['timestamp', 'open_usd', 'high_usd', 'low_usd', 'close_usd', 'volume_usd'])
    df_ratio = pd.DataFrame(all_ratio, columns=['timestamp', 'open_ratio', 'high_ratio', 'low_ratio', 'close_ratio', 'volume_ratio'])
    
    df = pd.merge(df_usd, df_ratio, on='timestamp', how='inner')
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
    df = df.set_index('datetime').sort_index()
    
    print(f"\n✅ Done! {len(df):,} candles from {df.index[0]} → {df.index[-1]} UTC")
    print("Columns added:")
    print("   close_usd     = 1 WETH in USD")
    print("   close_ratio   = 1 WETH in cbBTC  ← this is your internal pool price")
    print(f"Latest: 1 WETH = {df['close_usd'].iloc[-1]:.2f} USD = {df['close_ratio'].iloc[-1]:.6f} cbBTC")
    
    # Bonus: implied cbBTC price
    df['close_cbbtc_usd'] = df['close_usd'] / df['close_ratio']
    print(f"Implied cbBTC price: ${df['close_cbbtc_usd'].iloc[-1]:,.0f}")
    
    df.to_csv("aerodrome_weth_cbbtc_15min_full.csv")
    print("💾 Saved as aerodrome_weth_cbbtc_15min_full.csv")
    return df

# ====================== RUN ======================
POOL = "0x22aee3699b6a0fed71490c103bd4e5f3309891d5"
df = get_full_history(POOL)
