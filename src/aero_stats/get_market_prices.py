import requests
import time
from typing import Optional, Dict

# ==================== GLOBAL CACHE ====================
_cache: Dict[str, float] = {}
_cache_timestamp = 0.0
CACHE_DURATION = 60  # seconds


def _fetch_all_prices() -> Dict[str, float]:
    """Fetch all 4 prices in ONE API call (best practice for CoinGecko)"""
    global _cache, _cache_timestamp

    # Use cache if still fresh
    if time.time() - _cache_timestamp < CACHE_DURATION and _cache:
        return _cache

    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin,ethereum,coinbase-wrapped-btc,weth",
        "vs_currencies": "usd"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        _cache = {
            "btc":   data.get("bitcoin",              {}).get("usd"),
            "eth":   data.get("ethereum",             {}).get("usd"),
            "cbbtc": data.get("coinbase-wrapped-btc", {}).get("usd"),
            "weth":  data.get("weth",                 {}).get("usd"),
        }
        _cache_timestamp = time.time()
        return _cache

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            print("⏳ Rate limit hit. Waiting 2 seconds and retrying...")
            time.sleep(2)
            return _fetch_all_prices()  # retry once
        print(f"❌ HTTP error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    return {"btc": None, "eth": None, "cbbtc": None, "weth": None}


# ===================== PUBLIC FUNCTIONS =====================
def get_btc_price() -> Optional[float]:
    """Current Bitcoin (BTC) price in USD"""
    return _fetch_all_prices().get("btc")


def get_eth_price() -> Optional[float]:
    """Current Ethereum (ETH) price in USD"""
    return _fetch_all_prices().get("eth")


def get_cbbtc_price() -> Optional[float]:
    """Current cbBTC (Coinbase Wrapped BTC) price in USD"""
    return _fetch_all_prices().get("cbbtc")


def get_weth_price() -> Optional[float]:
    """Current WETH (Wrapped Ether) price in USD"""
    return _fetch_all_prices().get("weth")


# ========================= EXAMPLE USAGE =========================
if __name__ == "__main__":
    prices = {
        "BTC":   get_btc_price(),
        "ETH":   get_eth_price(),
        "cbBTC": get_cbbtc_price(),
        "WETH":  get_weth_price(),
    }

    for symbol, price in prices.items():
        if price is not None:
            print(f"{symbol:5} Price : ${price:,.2f}")
        else:
            print(f"{symbol:5} Price : ❌ Failed to fetch")
