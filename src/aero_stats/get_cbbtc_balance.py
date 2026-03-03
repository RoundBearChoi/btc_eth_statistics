from decimal import Decimal
from web3 import Web3

class CbBTCBalanceChecker:
    # =====================
    # CONFIG (don't change these)
    # =====================
    CBBTC_ADDRESS = "0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf"   # Official cbBTC on Base

    ERC20_ABI = [
        {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
        {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}
    ]

    def __init__(self):
        # =====================
        # CONNECT TO BASE + VERIFY
        # =====================
        self.w3 = Web3(Web3.HTTPProvider('https://mainnet.base.org'))   # Official Base RPC

        print("Connecting to Base...")

        if not self.w3.is_connected():
            raise Exception("❌ Failed to connect to Base. Check your internet or try another RPC.")

        chain_id = self.w3.eth.chain_id
        print(f"Connected! Chain ID: {chain_id}")

        if chain_id == 8453:
            print("✅ You are on **Base Mainnet**")
        else:
            raise Exception(f"⚠️ Wrong network! Connected to chain {chain_id} instead of Base (8453)")

    # =====================
    # BALANCE CHECK - cbBTC (ERC20)
    # =====================
    def get_cbbtc_balance(self, wallet_address):
        contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.CBBTC_ADDRESS), 
            abi=self.ERC20_ABI
        )
        decimals = contract.functions.decimals().call()
        raw_balance = contract.functions.balanceOf(
            Web3.to_checksum_address(wallet_address)
        ).call()
        return Decimal(raw_balance) / Decimal(10 ** decimals)

    # =====================
    # NEW: ETH BALANCE (Native token)
    # =====================
    def get_eth_balance(self, wallet_address):
        """Get native ETH balance on Base.
        Returns a Decimal with full precision using all 18 decimal points allowed for ETH on Base/EVM chains."""
        raw_balance_wei = self.w3.eth.get_balance(
            Web3.to_checksum_address(wallet_address)
        )
        # ETH on Base is ALWAYS 18 decimals (no contract call needed)
        return Decimal(raw_balance_wei) / Decimal(10 ** 18)

    # =====================
    # CLEANUP + CONFIRMATION (now guaranteed to print)
    # =====================
    def close(self):
        """Properly disconnect (if available) and always show confirmation"""
        if hasattr(self.w3, 'provider') and hasattr(self.w3.provider, 'disconnect'):
            self.w3.provider.disconnect()
        
        print("Disconnected from Base RPC")

    # =====================
    # RUN (user prompt) - now shows BOTH balances
    # =====================
    def run(self):
        print('')
        wallet_address = input("Enter your Base wallet address: ").strip()
        
        if not wallet_address:
            print("No address entered.")
            return
        
        try:
            eth_balance = self.get_eth_balance(wallet_address)
            cbbtc_balance = self.get_cbbtc_balance(wallet_address)
            
            print(f"\n✅ ETH Balance   : {eth_balance} ETH")
            print(f"✅ cbBTC Balance : {cbbtc_balance} cbBTC")
        except Exception as e:
            print(f"❌ Error checking balance: {str(e)}")


if __name__ == "__main__":
    checker = CbBTCBalanceChecker()      # create
    checker.run()                        # ask for address + show both balances
    checker.close()                      # ← explicit close right after run!
