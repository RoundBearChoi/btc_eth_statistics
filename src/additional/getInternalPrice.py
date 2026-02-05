import requests
from web3 import Web3
import json

# Market ratio from CoinGecko: 1 BTC ≈ X ETH (since cbBTC ≈ BTC and WETH ≈ ETH)
coingecko_url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=eth"
response = requests.get(coingecko_url)
data = response.json()
market_ratio = data["bitcoin"]["eth"]
print(f"Market ratio (from CoinGecko): 1 cbBTC ≈ {market_ratio:.10f} WETH\n")

# Pool ratio on Base chain (PancakeSwap V3 pool)
pool_address = "0xc211e1f853a898bd1302385ccde55f33a8c4b3f3"
base_rpc = "https://mainnet.base.org"  # Public Base RPC (may have rate limits; use Alchemy/Infura for heavy use)
w3 = Web3(Web3.HTTPProvider(base_rpc))

# Known addresses (checksummed)
WETH_ADDR = "0x4200000000000000000000000000000000000006"
CBBTC_ADDR = "0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf"

# Minimal ABI for Uniswap V3-compatible pool (token0, token1, slot0)
abi = json.loads('''
[
  {
    "inputs": [],
    "name": "slot0",
    "outputs": [
      {"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"},
      {"internalType": "int24", "name": "tick", "type": "int24"},
      {"internalType": "uint16", "name": "observationIndex", "type": "uint16"},
      {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"},
      {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"},
      {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"},
      {"internalType": "bool", "name": "unlocked", "type": "bool"}
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "token0",
    "outputs": [{"internalType": "address", "name": "", "type": "address"}],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "token1",
    "outputs": [{"internalType": "address", "name": "", "type": "address"}],
    "stateMutability": "view",
    "type": "function"
  }
]
''')

contract = w3.eth.contract(address=Web3.to_checksum_address(pool_address), abi=abi)

# Query contract
token0 = contract.functions.token0().call()
token1 = contract.functions.token1().call()
slot0_data = contract.functions.slot0().call()
sqrt_price_x96 = slot0_data[0]

# Compute price (token1 per token0)
price_token1_per_token0 = (sqrt_price_x96 / (2 ** 96)) ** 2

# Determine ratio: how many WETH per 1 cbBTC
if token0.lower() == WETH_ADDR.lower() and token1.lower() == CBBTC_ADDR.lower():
    pool_ratio = 1 / price_token1_per_token0  # WETH per cbBTC
elif token0.lower() == CBBTC_ADDR.lower() and token1.lower() == WETH_ADDR.lower():
    pool_ratio = price_token1_per_token0  # Already WETH per cbBTC
else:
    pool_ratio = None
    print("Error: Unexpected token order in pool!")

if pool_ratio is not None:
    print(f"Pool ratio (current price in pool): 1 cbBTC ≈ {pool_ratio:.10f} WETH")
