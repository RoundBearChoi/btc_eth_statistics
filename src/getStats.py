#getStats.py

from downloadPriceData import download_crypto_daily_closing
import time 

def get_stats(asset1: str, asset2: str) -> None:
    print('')
    print('lets go baby..')

    download_crypto_daily_closing(asset1)
    time.sleep(1)
    download_crypto_daily_closing(asset2)

if __name__ == '__main__':
    get_stats('btc', 'eth')
