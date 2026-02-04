import requests
from pprint import pprint


def get_internal_price() -> None:
    # Pool address (lowercase as required by the API)
    pool_address = "0xc211e1f853a898bd1302385ccde55f33a8c4b3f3"
    # Chain
    network = "base"
    # GeckoTerminal API base
    base_url = "https://api.geckoterminal.com/api/v2"
   
    # Step 1: Fetch pool info
    pool_url = f"{base_url}/networks/{network}/pools/{pool_address}"
    pool_response = requests.get(pool_url)
    if pool_response.status_code != 200:
        print("Error: Could not fetch pool information (check if the pool exists or try again later).")
        return
   
    pool_data = pool_response.json()["data"]["attributes"]
   
    # Pretty-print the full raw data (much nicer than default dict print)
    print("\n--- Full Pool Data (Pretty-Printed) ---")
    pprint(pool_data)
    print("\n")
   
    # Extract pair name and symbols
    pair_name = pool_data.get("name") or pool_data.get("pool_name", "UNKNOWN / UNKNOWN")
    base_symbol, quote_symbol = [s.strip() for s in pair_name.split(" / ")]
   
    # Current price (base in quote)
    price_key = "base_token_price_quote_token"
    if price_key not in pool_data:
        print("Price data not available.")
        return
    current_price = float(pool_data[price_key])
   
    print("=== Pool Summary ===")
    print(f"Pair: {base_symbol}/{quote_symbol}")
    print(f"Pool Address: {pool_address.upper()}")
    print(f"Price: 1 {base_symbol} = {current_price:.8f} {quote_symbol}")
    if current_price > 0:
        inverse_price = 1 / current_price
        print(f"       1 {quote_symbol} = {inverse_price:.10f} {base_symbol}")
   
    # USD prices if available
    if "base_token_price_usd" in pool_data:
        base_usd = float(pool_data["base_token_price_usd"])
        print(f"{base_symbol} USD Price: ${base_usd:,.2f}")
    if "quote_token_price_usd" in pool_data:
        quote_usd = float(pool_data["quote_token_price_usd"])
        print(f"{quote_symbol} USD Price: ${quote_usd:,.2f}")
   
    # Common financial metrics
    financial_metrics = {
        "volume_usd_h24": "24h Volume",
        "liquidity_usd": "Liquidity",
        "fdv_usd": "FDV",
        "market_cap_usd": "Market Cap",
    }
    for key, label in financial_metrics.items():
        if key in pool_data:
            val = float(pool_data[key])
            print(f"{label}: ${val:,.0f}")
   
    # Price changes (handles both dict format and individual keys)
    printed_changes = False
    if "price_change_percentage" in pool_data and isinstance(pool_data["price_change_percentage"], dict):
        changes = pool_data["price_change_percentage"]
        for period in ["m5", "h1", "h6", "h24"]:
            if period in changes and changes[period] is not None:
                try:
                    pct = float(changes[period])
                    sign = "+" if pct >= 0 else ""
                    period_label = period.upper().replace("M", "min").replace("H", "h")
                    print(f"Price Change ({period_label}): {sign}{pct:.2f}%")
                    printed_changes = True
                except:
                    pass
    # Fallback to individual keys if needed
    if not printed_changes:
        for period in ["m5", "h1", "h6", "h24"]:
            key = f"price_change_percentage_{period}"
            if key in pool_data:
                pct = float(pool_data[key])
                sign = "+" if pct >= 0 else ""
                period_label = period.upper().replace("M", "min").replace("H", "h")
                print(f"Price Change ({period_label}): {sign}{pct:.2f}%")
   
    # 24h transactions if available
    buys_key = "transactions_h24_buys"
    sells_key = "transactions_h24_sells"
    if buys_key in pool_data and sells_key in pool_data:
        buys = int(float(pool_data[buys_key]))
        sells = int(float(pool_data[sells_key]))
        print(f"24h Transactions: Buys {buys:,} | Sells {sells:,} | Total {buys + sells:,}")


if __name__ == '__main__':
    get_internal_price()
