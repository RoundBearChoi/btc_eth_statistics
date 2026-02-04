import requests
from pprint import pprint

def get_erc20_balance(token_address: str, wallet_address: str) -> int:
    """Fetch raw ERC20 balance via Base RPC (returns integer in wei-like units)"""
    rpc_url = "https://mainnet.base.org"
    # Correct balanceOf selector: 0x70a08231 + left-padded address (64 hex chars)
    padded_address = wallet_address[2:].lower().zfill(64)
    data = "0x70a08231" + padded_address
    
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_call",
        "params": [{"to": token_address.lower(), "data": data}, "latest"],
        "id": 1
    }
    
    try:
        response = requests.post(rpc_url, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json().get("result", "0x0")
        return int(result, 16)
    except Exception as e:
        print(f"RPC error fetching ERC20 balance for {token_address}: {e}")
        return 0

def get_native_balance(wallet_address: str) -> float:
    """Fetch native ETH balance on Base"""
    rpc_url = "https://mainnet.base.org"
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBalance",
        "params": [wallet_address.lower(), "latest"],
        "id": 1
    }
    
    try:
        response = requests.post(rpc_url, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json().get("result", "0x0")
        return int(result, 16) / 1e18
    except Exception as e:
        print(f"RPC error fetching native balance: {e}")
        return 0.0

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
  
    # Pretty-print the full raw data
    print("\n--- Full Pool Data (Pretty-Printed) ---")
    pprint(pool_data)
    print("\n")
  
    # Use clean pool_name for symbols
    pair_name = pool_data.get("pool_name") or pool_data.get("name", "UNKNOWN / UNKNOWN")
    base_symbol, quote_symbol = [s.strip() for s in pair_name.split(" / ")]
    if " " in quote_symbol:
        quote_symbol = quote_symbol.split()[0]

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
        print(f" 1 {quote_symbol} = {inverse_price:.10f} {base_symbol}")
  
    # USD prices if available
    base_usd = float(pool_data.get("base_token_price_usd", 0))
    quote_usd = float(pool_data.get("quote_token_price_usd", 0))
    if base_usd:
        print(f"{base_symbol} USD Price: ${base_usd:,.2f}")
    if quote_usd:
        print(f"{quote_symbol} USD Price: ${quote_usd:,.2f}")
  
    # Common financial metrics (fixed liquidity label)
    financial_metrics = {
        "volume_usd_h24": "24h Volume",
        "reserve_in_usd": "Liquidity",
        "fdv_usd": "FDV",
        "market_cap_usd": "Market Cap",
    }
    for key, label in financial_metrics.items():
        if key in pool_data:
            val = float(pool_data[key])
            print(f"{label}: ${val:,.0f}")
  
    # Price changes
    if "price_change_percentage" in pool_data and isinstance(pool_data["price_change_percentage"], dict):
        changes = pool_data["price_change_percentage"]
        for period in ["m5", "h1", "h6", "h24"]:
            if period in changes and changes[period] is not None:
                try:
                    pct = float(changes[period])
                    sign = "+" if pct >= 0 else ""
                    period_label = period.upper().replace("M", "min").replace("H", "h")
                    print(f"Price Change ({period_label}): {sign}{pct:.2f}%")
                except:
                    pass

    # === ADDITIONAL SECTION: Your wallet balances & rebalancing suggestion ===
    user_address = "0xC6869E01c4A9F3c982D63eEC8A104cA141ECC187"

    # Hardcoded token addresses
    base_token_address = "0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf"  # cbBTC
    quote_token_address = "0x4200000000000000000000000000000000000006"  # WETH on Base

    # Decimals
    base_decimals = 8
    quote_decimals = 18

    # Balances
    base_balance_raw = get_erc20_balance(base_token_address, user_address)
    quote_balance_raw = get_erc20_balance(quote_token_address, user_address)
    native_balance = get_native_balance(user_address)

    base_balance = base_balance_raw / (10 ** base_decimals)
    quote_balance = quote_balance_raw / (10 ** quote_decimals)
    effective_quote = quote_balance + native_balance  # Native ETH is easily wrappable to WETH

    print("\n=== Your On-Chain Balances (Base chain only) ===")
    print(f"{base_symbol}: {base_balance:,.10f}")
    print(f"{quote_symbol}: {quote_balance:,.10f}")
    print(f"Native ETH (Base): {native_balance:,.10f}")
    print(f"→ Total {quote_symbol} equivalent: {effective_quote:,.10f} (WETH + wrappable native ETH)")

    # USD values
    base_value_usd = base_balance * base_usd
    quote_value_usd = quote_balance * quote_usd
    native_value_usd = native_balance * quote_usd
    total_value_usd = base_value_usd + quote_value_usd + native_value_usd

    print(f"Value: ≈ ${base_value_usd:,.2f} ({base_symbol}) + ${quote_value_usd:,.2f} ({quote_symbol}) + ${native_value_usd:,.2f} (native) = ${total_value_usd:,.2f}")

    # Rebalancing (to ≈50/50 USD value using current pool price)
    print("\n=== Rebalance Suggestion (to ≈50/50 USD value) ===")
    print("Note: Assumes no price impact/fees. Real swaps on DEX have ~0.01% fee + potential impact.")
    if native_balance > 0:
        print("→ First wrap your native ETH → WETH (free/low-cost in most wallets/DEXs).")

    if base_balance == 0 and effective_quote == 0:
        print("→ No cbBTC or ETH/WETH detected on Base.")
        return
    
    target_quote = base_balance * current_price
    diff_quote = effective_quote - target_quote

    tolerance = 1e-8
    if abs(diff_quote) < tolerance:
        print("→ Already balanced at current pool price!")
    else:
        if diff_quote > 0:
            # Excess WETH/ETH → swap half the excess to cbBTC
            swap_weth = diff_quote / 2
            expected_cbbtc = swap_weth / current_price
            print(f"→ Swap ≈ {swap_weth:.10f} {quote_symbol} → ≈ {expected_cbbtc:.10f} {base_symbol}")
        else:
            # Excess cbBTC → swap half to WETH
            swap_cbbtc = (-diff_quote) / (2 * current_price)
            expected_weth = swap_cbbtc * current_price
            print(f"→ Swap ≈ {swap_cbbtc:.10f} {base_symbol} → ≈ {expected_weth:.10f} {quote_symbol}")
        
        print("   This will make your cbBTC and ETH/WETH holdings roughly equal in USD value.")

if __name__ == '__main__':
    get_internal_price()
