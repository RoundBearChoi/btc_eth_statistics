#getStats.py

from downloadPriceData import download_crypto_daily_closing


def get_stats(asset1: str, asset2: str) -> None:
    print('')
    print('lets go baby..')
    download_crypto_daily_closing('btc')


if __name__ == '__main__':
    get_stats('btc', 'eth')
