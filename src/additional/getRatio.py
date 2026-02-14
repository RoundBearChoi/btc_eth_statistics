import math
from web3 import Web3

# Uniswap V3 pool details (on BASE chain, not Ethereum mainnet)
POOL_ADDRESS = "0x8c7080564B5A792A33Ef2FD473fbA6364d5495e5"
WETH_DECIMALS = 18
CBBTC_DECIMALS = 8

# Public Base RPC (official; alternatives if rate-limited: "https://base-mainnet.public.blastapi.io", "https://rpc.ankr.com/base", or your own Alchemy/Infura Base endpoint)
RPC_URL = "https://mainnet.base.org"

# Minimal ABI for slot0()
SLOT0_ABI = [
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
    }
]

def get_current_price():
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        raise ConnectionError("Failed to connect to Base node")
    
    pool = w3.eth.contract(address=POOL_ADDRESS, abi=SLOT0_ABI)
    sqrt_price_x96, _, _, _, _, _, _ = pool.functions.slot0().call()
    
    sqrt_price = sqrt_price_x96 / (2 ** 96)
    raw_price = sqrt_price ** 2  # token1 (cbBTC) per token0 (WETH), raw units
    adjustment = 10 ** (CBBTC_DECIMALS - WETH_DECIMALS)
    current_price = adjustment / raw_price  # Human-readable: WETH per cbBTC
    return current_price

def calculate_required_weth(
    current_price: float,
    lower_pct: float = -0.047,   # -4.7%
    upper_pct: float = 0.038,    # +3.8%
    amount_cbbtc: float = 1.0
) -> float:
    lower_price = current_price * (1 + lower_pct)
    upper_price = current_price * (1 + upper_pct)
    
    if lower_price >= current_price or upper_price <= current_price:
        raise ValueError("Invalid range")
    
    sqrt_current = math.sqrt(current_price)
    sqrt_lower = math.sqrt(lower_price)
    sqrt_upper = math.sqrt(upper_price)
    
    # Liquidity from cbBTC side
    liquidity = amount_cbbtc / (1 / sqrt_current - 1 / sqrt_upper)
    
    # Required WETH from that liquidity
    required_weth = liquidity * (sqrt_current - sqrt_lower)
    
    return required_weth

# Main execution
if __name__ == "__main__":
    try:
        current_price = get_current_price()
        print(f"Current price (WETH per cbBTC): {current_price:.10f}")
        
        required_weth = calculate_required_weth(current_price)
        print(f"Required WETH for {1.0} cbBTC in -4.7%/+3.8% range (no tick snapping): {required_weth:.10f}")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Tip: Public RPCs can be rate-limited or temporarily down. Try a different RPC from the list above, or use your own key from Alchemy/Infura (Base chain).")
