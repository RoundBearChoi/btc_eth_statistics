from getHistoricClosing import fetch_crypto_daily_closing
from getPriceRatio import createPriceFile

if __name__ == "__main__":
    print("Starting crypto historical data fetches...\n")
    
    # Fetch data for desired assets
    assets = ['BTC', 'ETH', 'SOL']  # Add more as needed
    
    fetched_paths = {}
    for asset in assets:
        path = fetch_crypto_daily_closing(asset)
        print(f"{asset} data saved to: {path}\n")
        fetched_paths[asset] = path
    
    createPriceFile('BTC', 'ETH')   # BTC/ETH ratio
    # createPriceFile('SOL', 'BTC') # Example: SOL/BTC ratio
    # createPriceFile('BTC', 'SOL') # BTC/SOL ratio
