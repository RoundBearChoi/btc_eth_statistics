from getWalletBalance import procCSV
from getPanRate import get_cbbtc_eth_rate_pancakeswap


def get_swap_amount():
    cbbtc_balance, eth_balance = procCSV()
    print('')
    print(' --- getting swap amount --- ')
    print(f'cbbtc balance: {cbbtc_balance:.8f}')
    print(f'eth balance: {eth_balance:.8f}')

    market_rate, market_liquidity = get_cbbtc_eth_rate_pancakeswap()
    print(f'market rate: {market_rate}')


if __name__ == '__main__':
    get_swap_amount()
