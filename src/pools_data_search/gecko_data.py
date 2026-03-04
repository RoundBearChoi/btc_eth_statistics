import requests
import pandas as pd
import time
import random
from datetime import datetime

class GeckoPoolScanner:
    """
    GeckoTerminal pool scanner with rate-limit handling and filtering.
    
    Scans specified networks/dexes for liquidity pools meeting minimum liquidity
    and daily transaction count criteria.
    """

    def __init__(
        self,
        min_liquidity_usd=1_000_000,
        min_daily_tx=10_000,
        max_pages_per_dex=6,
        sort_by='daily_tx',
        sort_ascending=False,
        output_csv='geckoterminal_high_activity_pools.csv',
        calls_per_min_cap=25,
        sleep_between_pages=5.0,
        sleep_between_dexes=12.0,
        retry_attempts_429=3,
    ):
        self.min_liquidity_usd = min_liquidity_usd
        self.min_daily_tx = min_daily_tx
        self.max_pages_per_dex = max_pages_per_dex
        self.sort_by = sort_by
        self.sort_ascending = sort_ascending
        self.output_csv = output_csv
        
        # Rate limit controls
        self.calls_per_min_cap = calls_per_min_cap
        self.sleep_between_pages = sleep_between_pages
        self.sleep_between_dexes = sleep_between_dexes
        self.retry_attempts_429 = retry_attempts_429
        
        # Default targets (can be overridden when calling scan())
        self.default_targets = [
            ("solana",    "orca"),
            ("base",      "aerodrome-slipstream"),
            ("eth",       "uniswap_v3"),
            # ("solana",    "raydium"),
            # ("base",      "uniswap_v3"),
            # ("bsc",       "pancakeswap-v3"),
            # ("arbitrum",  "uniswap_v3"),
        ]

    def _rate_limit_sleep(self):
        time.sleep(self.sleep_between_pages + random.uniform(0, 1.5))

    def _fetch_page(self, network, dex, page):
        url = f"https://api.geckoterminal.com/api/v2/networks/{network}/dexes/{dex}/pools"
        params = {"page": page, "limit": 100}
        # params["order"] = "h24_tx_count_desc"   # uncomment if supported

        for attempt in range(self.retry_attempts_429 + 1):
            try:
                resp = requests.get(url, params=params, timeout=12)
                
                if resp.status_code == 429:
                    wait = 60 * (2 ** attempt) + random.randint(0, 10)
                    print(f"429 on {network}/{dex} page {page} (attempt {attempt+1}) → waiting {wait}s")
                    time.sleep(wait)
                    continue
                
                resp.raise_for_status()
                data = resp.json()
                return data.get("data", [])
                
            except requests.exceptions.HTTPError as e:
                print(f"HTTP error on {network}/{dex} page {page}: {e}")
                if attempt == self.retry_attempts_429:
                    return []
            except Exception as e:
                print(f"Unexpected error on {network}/{dex} page {page}: {e}")
                return []

        return []

    def scan_dex(self, network, dex):
        collected = []
        call_count = 0

        for page in range(1, self.max_pages_per_dex + 1):
            pools = self._fetch_page(network, dex, page)
            if not pools:
                break

            for p in pools:
                attrs = p.get("attributes", {})
                liq = float(attrs.get("liquidity_usd") or attrs.get("reserve_in_usd", 0))
                vol_h24 = float(attrs.get("volume_usd", {}).get("h24", 0))
                tx = attrs.get("transactions", {}).get("h24", {})
                daily_tx = (tx.get("buys", 0) or 0) + (tx.get("sells", 0) or 0)

                if liq >= self.min_liquidity_usd and daily_tx >= self.min_daily_tx:
                    collected.append({
                        "network": network,
                        "dex": dex,
                        "pool_address": p.get("id"),
                        "name": attrs.get("name"),
                        "symbol": attrs.get("symbol"),
                        "liquidity_usd": liq,
                        "volume_h24_usd": vol_h24,
                        "daily_tx": daily_tx,
                        "buys_24h": tx.get("buys", 0),
                        "sells_24h": tx.get("sells", 0),
                        "url": f"https://www.geckoterminal.com/{network}/pools/{p.get('id')}"
                    })

            print(f"{network}/{dex} - page {page}: {len(pools)} fetched, {len(collected)} match so far")
            self._rate_limit_sleep()
            call_count += 1
            if call_count >= self.calls_per_min_cap:
                print("Approaching call cap → extra 60s pause")
                time.sleep(60)
                call_count = 0

        return collected

    def scan(self, targets=None):
        if targets is None:
            targets = self.default_targets

        all_matches = []
        
        for net, dex in targets:
            print(f"\nScanning {net}/{dex}...")
            matches = self.scan_dex(net, dex)
            all_matches.extend(matches)
            time.sleep(self.sleep_between_dexes + random.uniform(0, 5))

        if not all_matches:
            print("\nNo pools found matching the criteria.")
            return pd.DataFrame()

        df = pd.DataFrame(all_matches)
        df = df.sort_values(self.sort_by, ascending=self.sort_ascending)

        print(f"\nFound {len(df)} pools matching criteria.")
        print(f"Top 15 by {self.sort_by}:")
        print(df.head(15)[[
            "network", "dex", "name", 
            "liquidity_usd", "volume_h24_usd", 
            "daily_tx", "buys_24h", "sells_24h"
        ]].to_string(index=False))

        df.to_csv(self.output_csv, index=False)
        print(f"\nResults saved to: {self.output_csv}")

        return df


# ────────────────────────────────────────────────
# Example usage
# ────────────────────────────────────────────────
if __name__ == "__main__":
    scanner = GeckoPoolScanner(
        min_liquidity_usd=1_000_000,
        min_daily_tx=10_000,
        max_pages_per_dex=6,
        # You can override targets here if you want different ones:
        # targets=[("solana", "orca"), ("base", "aerodrome-slipstream")]
    )
    
    scanner.scan()
