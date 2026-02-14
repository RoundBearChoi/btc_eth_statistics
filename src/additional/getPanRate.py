import requests
from typing import Tuple, Optional


def get_cbbtc_eth_rate_pancakeswap() -> Tuple[Optional[float], Optional[float]]:
    """
    Fetches the current cbBTC/WETH exchange rate on PancakeSwap V3 (Base chain)
    via DexScreener API.
    
    Returns:
        Tuple[float, float] | Tuple[None, None]:
            (eth_per_cbbtc, liquidity_usd)
            - eth_per_cbbtc: How many ETH 1 cbBTC is worth (float)
            - liquidity_usd: Total USD liquidity in the pool (float)
        Returns (None, None) if any error occurs (network, API, or data issue).
    """
    pair_address = "0xc211e1f853a898bd1302385ccde55f33a8c4b3f3"
    url = f"https://api.dexscreener.com/latest/dex/pairs/base/{pair_address}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Handle both possible response formats
        if "pair" in data:
            pair = data["pair"]
        elif "pairs" in data and len(data["pairs"]) > 0:
            pair = data["pairs"][0]
        else:
            print("No pair data found in API response")
            return None, None

        price_native = float(pair["priceNative"])
        base_symbol = pair["baseToken"]["symbol"]
        quote_symbol = pair["quoteToken"]["symbol"]

        if base_symbol == "cbBTC" and quote_symbol == "WETH":
            eth_per_cbbtc = price_native
        elif base_symbol == "WETH" and quote_symbol == "cbBTC":
            eth_per_cbbtc = 1 / price_native
        else:
            print(f"Unexpected tokens: {base_symbol}/{quote_symbol}")
            return None, None

        liquidity_usd = pair.get("liquidity", {}).get("usd", 0.0)

        return eth_per_cbbtc, liquidity_usd

    except requests.RequestException as e:
        print(f"Network/error fetching data: {e}")
        return None, None
    except (KeyError, ValueError, TypeError) as e:
        print(f"Error parsing API response: {e}")
        return None, None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None, None


# Example usage
if __name__ == "__main__":
    rate, liquidity = get_cbbtc_eth_rate_pancakeswap()
    if rate is not None:
        print("Current realtime rate on PancakeSwap (Base):")
        print(f"1 cbBTC ≈ {rate:.10f} ETH")
        print(f"(Liquidity: ~${liquidity:,.0f} USD)")
    else:
        print("Failed to retrieve rate. Check connection or try again later.")
