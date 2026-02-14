import requests

# PancakeSwap V3 cbBTC/WETH pool address on Base
pair_address = "0xc211e1f853a898bd1302385ccde55f33a8c4b3f3"

# DexScreener API endpoint for this pair
url = f"https://api.dexscreener.com/latest/dex/pairs/base/{pair_address}"

try:
    response = requests.get(url)
    response.raise_for_status()  # Raise error if request fails
    data = response.json()

    # Handle both possible response formats ("pair" or "pairs")
    if "pair" in data:
        pair = data["pair"]
    elif "pairs" in data and len(data["pairs"]) > 0:
        pair = data["pairs"][0]
    else:
        raise ValueError("No pair data found")

    # priceNative is the price of the base token in the quote token
    price_native = float(pair["priceNative"])

    base_symbol = pair["baseToken"]["symbol"]
    quote_symbol = pair["quoteToken"]["symbol"]

    if base_symbol == "cbBTC" and quote_symbol == "WETH":
        eth_per_cbbtc = price_native
    elif base_symbol == "WETH" and quote_symbol == "cbBTC":
        eth_per_cbbtc = 1 / price_native
    else:
        raise ValueError(f"Unexpected tokens: {base_symbol}/{quote_symbol}")

    print(f"Current realtime rate on PancakeSwap (Base):")
    print(f"1 cbBTC ≈ {eth_per_cbbtc:.10f} ETH")
    print(f"(Liquidity: ~${pair['liquidity']['usd']:,.0f} USD)")

except Exception as e:
    print(f"Error fetching data: {e}")
    print("Check your internet connection or try again later.")
