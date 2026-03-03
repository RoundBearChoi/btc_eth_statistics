import csv
import os
from datetime import datetime, timezone, timedelta
from decimal import Decimal

# Import our existing modules (must be in the same folder)
from get_base_balance import BaseBalanceChecker
from get_market_prices import CoinGeckoPrices


CSV_FILENAME = "wallet_records.csv"


def get_kst_now() -> str:
    """Return current time in KST (Korea Standard Time)"""
    kst = timezone(timedelta(hours=9))
    return datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S KST")


def main():
    print("🔍 Base Wallet Recorder (ETH + WETH + cbBTC + Prices)\n")

    # Ask for wallet address (same UX as your get_base_balance.py)
    wallet_address = input("Enter your Base wallet address: ").strip()
    if not wallet_address:
        print("❌ No address provided.")
        return

    # Initialize helpers
    balance_checker = BaseBalanceChecker()
    price_fetcher = CoinGeckoPrices()

    try:
        print("\n📡 Fetching balances from Base + prices from CoinGecko...")

        # === Fetch Balances (exact Decimal precision) ===
        eth_balance: Decimal = balance_checker.get_eth_balance(wallet_address)
        weth_balance: Decimal = balance_checker.get_weth_balance(wallet_address)
        cbbtc_balance: Decimal = balance_checker.get_cbbtc_balance(wallet_address)

        # === Fetch Prices ===
        prices = price_fetcher.get_all_prices()
        btc_price = prices.get("btc")
        eth_price = prices.get("eth")

        # === Current KST Timestamp ===
        timestamp_kst = get_kst_now()

        # === Prepare row for CSV (balances saved as exact strings) ===
        row = {
            "timestamp_kst": timestamp_kst,
            "wallet_address": wallet_address,
            "eth_balance": str(eth_balance),
            "weth_balance": str(weth_balance),
            "cbbtc_balance": str(cbbtc_balance),
            "btc_price_usd": f"{btc_price:,.2f}" if btc_price is not None else "N/A",
            "eth_price_usd": f"{eth_price:,.2f}" if eth_price is not None else "N/A",
        }

        # === Append to CSV (create file + header on first run) ===
        file_exists = os.path.isfile(CSV_FILENAME)
        with open(CSV_FILENAME, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            if not file_exists:
                writer.writeheader()
                print(f"📁 Created new file → {CSV_FILENAME}")
            writer.writerow(row)

        # === Pretty summary ===
        print("\n" + "═" * 70)
        print(f"✅ SUCCESSFULLY RECORDED — {timestamp_kst}")
        print(f"Wallet     : {wallet_address}")
        print(f"ETH        : {float(eth_balance):,.8f} ETH")
        print(f"WETH       : {float(weth_balance):,.8f} WETH")
        print(f"cbBTC      : {float(cbbtc_balance):,.8f} cbBTC")
        print("-" * 70)
        print(f"BTC Price  : ${btc_price:,.2f}" if btc_price is not None else "BTC Price  : ❌ Failed")
        print(f"ETH Price  : ${eth_price:,.2f}" if eth_price is not None else "ETH Price  : ❌ Failed")
        print("═" * 70)
        print(f"💾 Data saved to: {CSV_FILENAME} (same folder as this script)")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
    finally:
        balance_checker.close()


if __name__ == "__main__":
    main()
