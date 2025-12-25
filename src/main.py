from getHistoricClosing import fetch_crypto_daily_closing
from getPriceRatio import createPriceFile

if __name__ == "__main__":
    print("starting crypto historical data fetches..")
    
    fetch_crypto_daily_closing('BTC')
    fetch_crypto_daily_closing('ETH')
    fetch_crypto_daily_closing('SOL')

    createPriceFile('BTC', 'ETH')   # BTC/ETH ratio
    # createPriceFile('SOL', 'BTC') # Example: SOL/BTC ratio
    # createPriceFile('BTC', 'SOL') # BTC/SOL ratio
