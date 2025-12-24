# main.py

from getHistoricClosing import fetch_crypto_daily_closing
from getPriceRatio import createPriceFile

if __name__ == "__main__":
    print("Starting crypto historical data fetches...\n")
    
    # Bitcoin 
    btc_path = fetch_crypto_daily_closing('BTC')
    print(f"BTC data saved to: {btc_path}\n")
    
    # Ethereum  
    eth_path = fetch_crypto_daily_closing('ETH')
    print(f"ETH data saved to: {eth_path}\n")
   
    createPriceFile()
