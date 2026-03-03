from decimal import Decimal
from web3 import Web3

# =====================
# CONFIG (don't change these)
# =====================
CBBTC_ADDRESS = "0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf"   # Official cbBTC on Base

ERC20_ABI = [
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}
]

# =====================
# CONNECT TO BASE + VERIFY
# =====================
w3 = Web3(Web3.HTTPProvider('https://mainnet.base.org'))   # Official Base RPC

print("Connecting to Base...")

if not w3.is_connected():
    raise Exception("❌ Failed to connect to Base. Check your internet or try another RPC.")

chain_id = w3.eth.chain_id
print(f"Connected! Chain ID: {chain_id}")

if chain_id == 8453:
    print("✅ You are on **Base Mainnet**")
else:
    raise Exception(f"⚠️ Wrong network! Connected to chain {chain_id} instead of Base (8453)")

# =====================
# YOUR BALANCE FUNCTION (unchanged)
# =====================
def get_cbbtc_balance(w3, wallet_address):
    contract = w3.eth.contract(address=Web3.to_checksum_address(CBBTC_ADDRESS), abi=ERC20_ABI)
    decimals = contract.functions.decimals().call()
    raw_balance = contract.functions.balanceOf(Web3.to_checksum_address(wallet_address)).call()
    return Decimal(raw_balance) / Decimal(10 ** decimals)

# =====================
# ASK FOR WALLET AND SHOW BALANCE
# =====================
if __name__ == "__main__":
    print('')
    wallet_address = input("Enter your Base wallet address: ").strip()
    
    if not wallet_address:
        print("No address entered.")
    else:
        try:
            balance = get_cbbtc_balance(w3, wallet_address)
            print(f"\n✅ Balance: {balance} cbBTC")
        except Exception as e:
            print(f"❌ Error checking balance: {str(e)}")
