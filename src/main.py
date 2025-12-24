# main.py

from getHistoricClosing import fetch_crypto_daily_closing
from getPriceRatio import getPrice

if __name__ == "__main__":
    print("Starting crypto historical data fetches...\n")
    
    # Bitcoin 
    btc_path = fetch_crypto_daily_closing('BTC')
    print(f"BTC data saved to: {btc_path}\n")
    
    # Ethereum  
    eth_path = fetch_crypto_daily_closing('ETH')
    print(f"ETH data saved to: {eth_path}\n")
    
    today_price = getPrice('2025-12-24')
    if today_price:
        print("Today's prices:")
        print(f"BTC: ${today_price['btc']:,.2f}")
        print(f"ETH: ${today_price['eth']:,.2f}")
        print(f"BTC/ETH ratio: {today_price['ratio']:.4f}")
