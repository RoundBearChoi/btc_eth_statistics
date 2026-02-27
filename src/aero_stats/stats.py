import requests
import pandas as pd
import time
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional

class AerodromeSlipstreamFetcher:
    """
    Smart resume-capable fetcher for Aerodrome Slipstream pools on Base.
    - First run: full history
    - Future runs: ONLY new candles since last save
    - Clear progress: shows the newest date on every page
    """
    
    def __init__(self, pool_address: str, network: str = "base"):
        self.pool_address = pool_address.lower()
        self.network = network
        self.base_url = f"https://api.geckoterminal.com/api/v2/networks/{network}/pools/{pool_address}/ohlcv/minute"
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
    
    def _fetch_batch(self, currency: str, before_ts: Optional[int] = None, aggregate: int = 15, limit: int = 500) -> list:
        params = {"aggregate": aggregate, "limit": limit, "currency": currency}
        if before_ts is not None:
            params["before_timestamp"] = before_ts
            
        for attempt in range(6):
            resp = self.session.get(self.base_url, params=params)
            
            if resp.status_code == 200:
                data = resp.json()
                return data.get("data", {}).get("attributes", {}).get("ohlcv_list", [])
            
            if resp.status_code == 429:
                wait = (2 ** attempt) * 7
                print(f"   ⏳ Rate limit hit — waiting {wait}s...")
                time.sleep(wait)
                continue
            print(f"❌ Error {resp.status_code} for {currency}")
            return []
        return []
    
    def fetch_full_history(self, aggregate: int = 15, csv_path: Optional[str] = None) -> pd.DataFrame:
        if csv_path is None:
            csv_path = f"aerodrome_{self.pool_address[:8]}_15min_full.csv"
        
        csv_path = Path(csv_path)
        existing_df = None
        last_saved_ts = None
        
        if csv_path.exists():
            print(f"📂 Found existing file: {csv_path.name} — resuming...")
            existing_df = pd.read_csv(csv_path, parse_dates=['datetime'], index_col='datetime')
            last_saved_ts = int(existing_df['timestamp'].max())
            last_dt = datetime.fromtimestamp(last_saved_ts, tz=UTC)
            print(f"   Last saved: {last_dt.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        
        all_usd = []
        all_ratio = []
        before_ts = None
        page = 0
        
        print("🚀 Starting smart fetch...")
        
        while page < 200:
            print(f"   Page {page + 1}...", end=" ")
            
            batch_usd = self._fetch_batch("usd", before_ts, aggregate)
            batch_ratio = self._fetch_batch("token", before_ts, aggregate)
            
            if not batch_usd or not batch_ratio:
                print("✅ No more new data.")
                break
                
            all_usd.extend(batch_usd)
            all_ratio.extend(batch_ratio)
            
            # Show the newest candle in this batch
            newest_ts = batch_usd[0][0]   # first item = newest
            newest_dt = datetime.fromtimestamp(newest_ts, tz=UTC)
            print(f"→ newest candle at {newest_dt.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            
            before_ts = newest_ts - 1
            
            # If we already have this data, stop
            if last_saved_ts and newest_ts <= last_saved_ts:
                print("   No newer data found.")
                break
                
            if len(batch_usd) < 400:
                break
                
            time.sleep(2.3)
            page += 1
        
        if not all_usd:
            print("⚠️ No new candles fetched this run.")
            return existing_df if existing_df is not None else pd.DataFrame()
        
        # Build new data
        df_new_usd = pd.DataFrame(all_usd, columns=['timestamp', 'open_usd', 'high_usd', 'low_usd', 'close_usd', 'volume_usd'])
        df_new_ratio = pd.DataFrame(all_ratio, columns=['timestamp', 'open_ratio', 'high_ratio', 'low_ratio', 'close_ratio', 'volume_ratio'])
        
        df_new = pd.merge(df_new_usd, df_new_ratio, on='timestamp')
        df_new['datetime'] = pd.to_datetime(df_new['timestamp'], unit='s')
        df_new = df_new.set_index('datetime').sort_index()
        df_new['close_cbbtc_usd'] = df_new['close_usd'] / df_new['close_ratio']
        
        # Merge
        if existing_df is not None:
            df = pd.concat([existing_df, df_new])
            df = df[~df.index.duplicated(keep='last')].sort_index()
            print(f"   Added {len(df_new)} new candles → Total now: {len(df):,}")
        else:
            df = df_new
            print(f"   Full history downloaded: {len(df):,} candles")
        
        df.to_csv(csv_path)
        print(f"💾 Saved to {csv_path.name}")
        
        print(f"\n✅ Final range: {df.index[0]} → {df.index[-1]} UTC")
        print(f"   Latest: 1 WETH = {df['close_usd'].iloc[-1]:.2f} USD = {df['close_ratio'].iloc[-1]:.6f} cbBTC "
              f"(cbBTC ≈ ${df['close_cbbtc_usd'].iloc[-1]:,.0f})")
        
        return df


# ====================== RUN ======================
if __name__ == "__main__":
    fetcher = AerodromeSlipstreamFetcher("0x22aee3699b6a0fed71490c103bd4e5f3309891d5")
    df = fetcher.fetch_full_history()
    
    print("\nLast 3 rows preview:")
    print(df[['close_usd', 'close_ratio', 'close_cbbtc_usd', 'volume_usd']].tail(3))
