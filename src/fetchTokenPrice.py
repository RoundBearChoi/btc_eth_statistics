# fetchTokenPrice.py
from geckoTerminalAPI import get_token_data

def print_token_price(network: str, token_address: str, display_name: str):
    """
    Fetch and print the USD price of a token.
    display_name is what you want shown to the user (e.g., 'ETH', 'BTC').
    """
    try:
        attributes = get_token_data(network, token_address)
        name = attributes["name"]
        symbol = attributes["symbol"]
        price_usd = attributes.get("price_usd")

        if price_usd is not None:
            price_formatted = float(price_usd)
            print(f"{display_name} price ({name} - {symbol}): ${price_formatted:,.2f}")
        else:
            print(f"{display_name} price data unavailable.")
    except Exception as e:
        print(f"Error fetching {display_name} price: {e}")
