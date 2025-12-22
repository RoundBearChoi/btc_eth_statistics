# main.py
from geckoTerminalAPI import get_supported_networks
from fetchTokenPrice import print_token_price

def print_supported_networks():
    print("\n==================================================\n")
   
    print("Fetching supported networks...\n")
    networks = get_supported_networks()
    print("Supported Networks:")
    for network in networks:
        name = network["attributes"]["name"]
        print(f"- {name}")

def print_btc_eth_price():
    print("\n==================================================\n")
    
    tokens = [
        ("eth", "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2", "ETH"),   # WETH on Ethereum
        ("eth", "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599", "BTC"),   # WBTC on Ethereum
    ]

    for network, address, name in tokens:
        print(f"Fetching current {name} price...")
        print_token_price(network, address, name)
        print()  # Empty line for readability

def main():
    print_supported_networks()
    print_btc_eth_price()

if __name__ == "__main__":
    print("\n==================================================\n")
   
    # Capture and print the default User-Agent used by requests (as in your original script)
    import requests
    print("Sent User-Agent:", requests.utils.default_user_agent())
    print()
    main()
