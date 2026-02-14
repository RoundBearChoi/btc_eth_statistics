from getWalletBalance import procCSV
from getPanRate import get_cbbtc_eth_rate_pancakeswap
from getUniRate import get_current_price
from getUniRate import calculate_required_weth


def get_swap_amount():
    cbbtc_balance, eth_balance = procCSV()
    print('')
    print(' --- getting swap amount --- ')
    print(f'cbbtc balance: {cbbtc_balance:.8f}')
    print(f'eth balance: {eth_balance:.8f}')

    market_rate, market_liquidity = get_cbbtc_eth_rate_pancakeswap()
    print(f'pancakeswap market rate: {market_rate}')

    current_price = get_current_price(verbose=False)
    required_weth = calculate_required_weth(current_price, verbose=False)

    print(f'uniswap pool rate: {required_weth:.8f}')


if __name__ == '__main__':
    get_swap_amount()
