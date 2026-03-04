import requests
import pandas as pd
import time
from datetime import datetime
import random  # for jitter

# ────────────────────────────────────────────────
# CONFIG
# ────────────────────────────────────────────────
MIN_LIQUIDITY_USD = 1_000_000
MIN_DAILY_TX      = 10_000
MAX_PAGES_PER_DEX = 6               # lowered to reduce call volume
SORT_BY           = 'daily_tx'
SORT_ASCENDING    = False
OUTPUT_CSV        = f"geckoterminal_high_activity_pools_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

TARGET_DEXES = [
    ("solana",    "orca"),               # very active, good matches
    ("base",      "aerodrome-slipstream"), # strong results in your run
    ("eth",       "uniswap_v3"),
    # ("solana",    "raydium"),          # comment out if rate-limited
    # ("base",      "uniswap_v3"),
    # ("bsc",       "pancakeswap-v3"),
    # ("arbitrum",  "uniswap_v3"),
]

# Rate limit safety
CALLS_PER_MIN_CAP = 25              # stay under 30
SLEEP_BETWEEN_PAGES = 5             # seconds
SLEEP_BETWEEN_DEXES = 12
RETRY_ATTEMPTS_429 = 3

# ────────────────────────────────────────────────
def rate_limit_sleep():
    time.sleep(SLEEP_BETWEEN_PAGES + random.uniform(0, 1.5))  # jitter

def fetch_and_filter(network, dex, max_pages=MAX_PAGES_PER_DEX):
    collected = []
    call_count_this_session = 0

    for page in range(1, max_pages + 1):
        url = f"https://api.geckoterminal.com/api/v2/networks/{network}/dexes/{dex}/pools"
        params = {"page": page, "limit": 100}
        # Try sorting by tx count if endpoint supports it
        # params["order"] = "h24_tx_count_desc"   # uncomment & test

        for attempt in range(RETRY_ATTEMPTS_429 + 1):
            try:
                resp = requests.get(url, params=params, timeout=12)
                if resp.status_code == 429:
                    wait = 60 * (2 ** attempt) + random.randint(0, 10)  # 60s → 120s → 240s
                    print(f"429 on {network}/{dex} page {page} (attempt {attempt+1}/{RETRY_ATTEMPTS_429+1}) → waiting {wait}s")
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                data = resp.json()
                pools = data.get("data", [])
                if not pools:
                    break

                for p in pools:
                    attrs = p.get("attributes", {})
                    liq = float(attrs.get("liquidity_usd") or attrs.get("reserve_in_usd", 0))
                    vol_h24 = float(attrs.get("volume_usd", {}).get("h24", 0))
                    tx = attrs.get("transactions", {}).get("h24", {})
                    daily_tx = (tx.get("buys", 0) or 0) + (tx.get("sells", 0) or 0)

                    if liq >= MIN_LIQUIDITY_USD and daily_tx >= MIN_DAILY_TX:
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
                rate_limit_sleep()
                call_count_this_session += 1
                if call_count_this_session >= CALLS_PER_MIN_CAP:
                    print("Approaching call cap → extra 60s pause")
                    time.sleep(60)
                    call_count_this_session = 0
                break  # success → next page

            except requests.exceptions.HTTPError as e:
                print(f"HTTP error on {network}/{dex} page {page}: {e}")
                if attempt == RETRY_ATTEMPTS_429:
                    break
            except Exception as e:
                print(f"Unexpected error: {e}")
                break

    return collected

# ────────────────────────────────────────────────
all_matches = []
for net, dex in TARGET_DEXES:
    print(f"\nScanning {net}/{dex}...")
    matches = fetch_and_filter(net, dex)
    all_matches.extend(matches)
    time.sleep(SLEEP_BETWEEN_DEXES + random.uniform(0, 5))

# Process & save (same as before)
if all_matches:
    df = pd.DataFrame(all_matches)
    df = df.sort_values(SORT_BY, ascending=SORT_ASCENDING)
    print(f"\nFound {len(df)} pools matching criteria.")
    print("Top 15 by", SORT_BY, ":")
    print(df.head(15)[["network", "dex", "name", "liquidity_usd", "volume_h24_usd", "daily_tx", "buys_24h", "sells_24h"]].to_string(index=False))
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Saved to: {OUTPUT_CSV}")
else:
    print("No matches found this run.")

print("Done. If still hitting 429 quickly, reduce TARGET_DEXES or increase sleeps further.")
