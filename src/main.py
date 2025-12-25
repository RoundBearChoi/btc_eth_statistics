from getPriceRatio import createPriceFile
from getPriceChange import generate_price_change  

if __name__ == "__main__":
    createPriceFile('BTC', 'ETH')   # BTC/ETH ratio
    # createPriceFile('SOL', 'BTC') # Example: SOL/BTC ratio
    # createPriceFile('BTC', 'SOL') # BTC/SOL ratio

    generate_price_change('BTC', 'ETH')
