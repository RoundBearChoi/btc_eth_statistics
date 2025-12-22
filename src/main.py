import requests
import json

# Base URL
base_url = "https://api.geckoterminal.com/api/v2"

# Endpoint to list networks
url = f"{base_url}/networks"

# Parameters
params = {"page": 1}

# Headers (only accept, no User-Agent specified on purpose)
headers = {
    "accept": "application/json"
}

# Make the GET request
response = requests.get(url, params=params, headers=headers)

# NEW: Print the exact User-Agent that requests sent
print("Sent User-Agent:", response.request.headers['User-Agent'])

# Check if successful
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
    print(response.text[:500])  # Show first part of error
