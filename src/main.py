import requests

# Base URL
base_url = "https://api.geckoterminal.com/api/v2"

# Headers
headers = {
    "accept": "application/json"
}

# Make a request early to capture the User-Agent (same as your original test)
url = f"{base_url}/networks"
params = {"page": 1}
response = requests.get(url, params=params, headers=headers)

# Print User-Agent first, exactly as in your original output
print("Sent User-Agent:", response.request.headers['User-Agent'])

# Now process the networks list
if response.status_code == 200:
    data = response.json()
    networks = data.get("data", [])
    print("\nSupported Networks:")
    for network in networks:
        attributes = network.get("attributes", {})
        name = attributes.get("name")
        print(f"- {name}")
else:
    print(f"Error: {response.status_code}")
    print(response.text[:500])
    exit()

print("\n" + "="*50 + "\n")

# Function to fetch token price
def get_token_price(network, token_address, token_name):
    url = f"{base_url}/networks/{network}/tokens/{token_address}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        attributes = response.json()["data"]["attributes"]
        name = attributes["name"]
        symbol = attributes["symbol"]
        price_usd = attributes.get("price_usd")
        if price_usd:
            print(f"{token_name} price ({name} - {symbol}): ${float(price_usd):,.2f}\n")
        else:
            print(f"{token_name} price data unavailable.\n")
    else:
        print(f"Error fetching {token_name} price: {response.status_code}")
        print(response.text[:500] + "\n")

# Fetch prices
print("Fetching current ETH price...")
get_token_price("eth", "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2", "ETH")

print("Fetching current BTC price (via WBTC)...")
get_token_price("eth", "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599", "BTC")
