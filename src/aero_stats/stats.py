import requests
import pandas as pd
import time
from datetime import datetime, timezone   # ← ADDED timezone
from typing import Optional


class AerodromeSlipstreamFetcher:
    """
    Robust fetcher for Aerodrome Slipstream pools.
    Now supports max_years limit (default = 2 years) + FULL contract address in filename.
    DeprecationWarning for utcfromtimestamp completely fixed.
    """

    def __init__(self, pool_address: str, network: str = "base"):
        self.pool_address = pool_address.lower()
        self.network = network
        self.base_url = f"https://api.geckoterminal.com/api/v2/networks/{network}/pools/{pool_address}/ohlcv/minute"
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def _fetch_batch(self, currency: str, before_ts: Optional[int] = None, aggregate: int = 15, limit: int = 500, retries: int = 5) -> list:
        """Fetch one batch with smart retry on 429"""
        for attempt in range(retries + 1):
            params = {"aggregate": aggregate, "limit": limit, "currency": currency}
            if before_ts:
                params["before_timestamp"] = before_ts

            response = self.session.get(self.base_url, params=params)

            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("attributes", {}).get("ohlcv_list", [])

            if response.status_code == 429:
                wait = (2 ** attempt) * 5
                print(f" ⏳ Rate limit hit (429). Waiting {wait}s before retry {attempt+1}/{retries}...")
                time.sleep(wait)
                continue

            print(f"❌ Error {response.status_code} (currency={currency}): {response.text[:150]}")
            return []

        print(f"❌ Failed after {retries} retries for currency={currency}")
        return []

    def fetch_full_history(self, aggregate: int = 15, save_csv: bool = True, 
                           filename: Optional[str] = None, max_years: Optional[float] = 2.0) -> pd.DataFrame:
        """Fetch history with optional max age limit (default 2 years)"""
        all_usd = []
        all_ratio = []
        before_ts = None
        page = 0
        max_pages = 300  # hard safety net

        print(f"🚀 Starting robust fetch for pool {self.pool_address[:10]}... (USD + internal ratio)")

        # Calculate cutoff for max_years
        cutoff_ts = None
        if max_years is not None:
            cutoff_ts = int(time.time()) - int(max_years * 365.25 * 24 * 3600)
            cutoff_date = datetime.fromtimestamp(cutoff_ts, tz=timezone.utc).strftime('%Y-%m-%d')  # ← FIXED
            print(f"📅 Capping at max {max_years} years → ignoring anything before {cutoff_date}")

        while page < max_pages:
            batch_usd = self._fetch_batch("usd", before_ts, aggregate)
            batch_ratio = self._fetch_batch("token", before_ts, aggregate)

            if not batch_usd or not batch_ratio:
                print("✅ Reached end of available data.")
                break

            # Page info with date range
            first_date = datetime.fromtimestamp(batch_usd[0][0], tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')  # ← FIXED
            oldest_in_batch_ts = batch_usd[-1][0]
            oldest_date = datetime.fromtimestamp(oldest_in_batch_ts, tz=timezone.utc).strftime('%Y-%m-%d')  # ← FIXED
            print(f" Page {page + 1:2d}... {first_date} → {oldest_date}")

            # Enforce 2-year limit
            if cutoff_ts is not None and oldest_in_batch_ts < cutoff_ts:
                print(f"   → Hit {max_years}-year limit. Trimming last batch...")
                batch_usd = [c for c in batch_usd if c[0] >= cutoff_ts]
                batch_ratio = [c for c in batch_ratio if c[0] >= cutoff_ts]
                if not batch_usd:
                    print("✅ Stopped at max 2-year limit.")
                    break

            all_usd.extend(batch_usd)
            all_ratio.extend(batch_ratio)

            before_ts = batch_usd[-1][0] - 1

            if len(batch_usd) < 400:
                break

            time.sleep(2.2)  # safe rate limit
            page += 1

        # Build clean DataFrame
        df_usd = pd.DataFrame(all_usd, columns=['timestamp', 'open_usd', 'high_usd', 'low_usd', 'close_usd', 'volume_usd'])
        df_ratio = pd.DataFrame(all_ratio, columns=['timestamp', 'open_ratio', 'high_ratio', 'low_ratio', 'close_ratio', 'volume_ratio'])

        df = pd.merge(df_usd, df_ratio, on='timestamp', how='inner')
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        df = df.set_index('datetime').sort_index()
        df['close_cbbtc_usd'] = df['close_usd'] / df['close_ratio']

        print(f"\n✅ DONE! {len(df):,} candles from {df.index[0]} → {df.index[-1]} UTC")
        print(f" Latest: 1 WETH = {df['close_usd'].iloc[-1]:.2f} USD = {df['close_ratio'].iloc[-1]:.6f} cbBTC "
              f"(cbBTC ≈ ${df['close_cbbtc_usd'].iloc[-1]:,.0f})")

        if save_csv:
            if filename is None:
                max_part = f"max{max_years}y" if max_years is not None else "full"
                filename = f"aerodrome_{self.pool_address}_{aggregate}min_{max_part}.csv"
            df.to_csv(filename)
            print(f"💾 Saved → {filename}")

        return df


# ====================== USAGE ======================
if __name__ == "__main__":
    fetcher = AerodromeSlipstreamFetcher("0x22aee3699b6a0fed71490c103bd4e5f3309891d5")
    
    df = fetcher.fetch_full_history(max_years=2.0)

    print("\nLast 3 rows preview:")
    print(df[['close_usd', 'close_ratio', 'close_cbbtc_usd', 'volume_usd']].tail(3))
