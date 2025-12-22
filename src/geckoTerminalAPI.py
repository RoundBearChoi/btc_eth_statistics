# geckoTerminalAPI.py
import requests

BASE_URL = "https://api.geckoterminal.com/api/v2"
HEADERS = {"accept": "application/json"}

def get_supported_networks(page: int = 1) -> list[dict]:
    """Fetch the list of supported networks from GeckoTerminal."""
    url = f"{BASE_URL}/networks"
    params = {"page": page}
    response = requests.get(url, params=params, headers=HEADERS)
    response.raise_for_status()
    return response.json().get("data", [])


def get_token_data(network: str, token_address: str) -> dict:
    """
    Fetch token data (including price) for a given network and token address.
    Returns the 'attributes' dict if successful.
    """
    url = f"{BASE_URL}/networks/{network}/tokens/{token_address}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()["data"]["attributes"]
