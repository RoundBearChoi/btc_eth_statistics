import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta, timezone
import time

# ================== FETCH FUNCTIONS ==================
def fetch_funding_rates(symbol: str, start_time=None, end_time=None, limit: int = 1000):
    url = "https://fapi.binance.com/fapi/v1/fundingRate"
    params = {'symbol': symbol.upper(), 'limit': limit}
    if start_time:
        params['startTime'] = int(start_time.timestamp() * 1000)
    if end_time:
        params['endTime'] = int(end_time.timestamp() * 1000)
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    
    if not data:
        return pd.DataFrame(columns=['fundingTime', 'fundingRate'])
    
    df = pd.DataFrame(data)
    df['fundingTime'] = pd.to_datetime(df['fundingTime'], unit='ms')
    df['fundingRate'] = pd.to_numeric(df['fundingRate'])
    return df[['fundingTime', 'fundingRate']]

def get_full_funding_history(symbol: str, years: int = 2):
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=int(365.25 * years))
    all_dfs = []
    current_start = start
    
    while True:
        df = fetch_funding_rates(symbol, current_start, end, limit=1000)
        if df.empty or len(df) == 0:
            break
        all_dfs.append(df)
        if len(df) < 1000:
            break
        current_start = df['fundingTime'].iloc[-1] + timedelta(milliseconds=10)
        time.sleep(0.2)
    
    if not all_dfs:
        return pd.DataFrame()
    
    full = pd.concat(all_dfs).drop_duplicates(subset=['fundingTime']).sort_values('fundingTime').reset_index(drop=True)
    return full

def fetch_klines(symbol: str, interval: str = '15m', start_time=None, end_time=None, limit: int = 1000):
    url = "https://fapi.binance.com/fapi/v1/klines"
    params = {'symbol': symbol.upper(), 'interval': interval, 'limit': limit}
    if start_time:
        params['startTime'] = int(start_time.timestamp() * 1000)
    if end_time:
        params['endTime'] = int(end_time.timestamp() * 1000)
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    
    if not data:
        return pd.DataFrame()
    
    cols = ['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'n', 'tbb', 'tbq', 'ignore']
    df = pd.DataFrame(data, columns=cols)
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    for c in ['open', 'high', 'low', 'close', 'volume']:
        df[c] = pd.to_numeric(df[c])
    return df.set_index('open_time')

def get_full_klines(symbol: str, interval: str = '15m', years: int = 2):
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=int(365.25 * years))
    all_dfs = []
    current_start = start
    
    while True:
        df = fetch_klines(symbol, interval, current_start, end, limit=1000)
        if df.empty or len(df) == 0:
            break
        all_dfs.append(df)
        if len(df) < 1000:
            break
        current_start = df.index[-1] + timedelta(milliseconds=10)
        time.sleep(0.2)
    
    if not all_dfs:
        return pd.DataFrame()
    
    full = pd.concat(all_dfs).drop_duplicates().sort_index()
    return full

def merge_price_funding(price_df: pd.DataFrame, funding_df: pd.DataFrame) -> pd.DataFrame:
    funding = funding_df.set_index('fundingTime')
    combined = price_df.join(funding['fundingRate'], how='left')
    combined['fundingRate'] = combined['fundingRate'].ffill()
    return combined

# ================== BTC-ETH ANALYSIS ==================
def analyze_btc_eth_pair(btc_merged: pd.DataFrame, eth_merged: pd.DataFrame):
    combined = btc_merged[['close', 'fundingRate']].rename(columns={'close':'btc_close', 'fundingRate':'btc_funding'}) \
                .join(
                    eth_merged[['close', 'fundingRate']].rename(columns={'close':'eth_close', 'fundingRate':'eth_funding'}), 
                    how='inner'
                )
    
    combined['btc_eth_ratio'] = combined['btc_close'] / combined['eth_close']
    combined['funding_spread'] = combined['btc_funding'] - combined['eth_funding']
    
    # Future returns
    combined['ratio_return_8h'] = combined['btc_eth_ratio'].pct_change(periods=32).shift(-32)
    combined['ratio_return_24h'] = combined['btc_eth_ratio'].pct_change(periods=96).shift(-96)
    
    print("\n=== BTC vs ETH FUNDING SPREAD ANALYSIS ===")
    print(combined['funding_spread'].describe())
    
    corr8 = combined['funding_spread'].corr(combined['ratio_return_8h'])
    corr24 = combined['funding_spread'].corr(combined['ratio_return_24h'])
    print(f"\nCorrelation (funding_spread → next 8h BTC/ETH ratio change): {corr8:.4f}")
    print(f"Correlation (funding_spread → next 24h BTC/ETH ratio change): {corr24:.4f}")
    
    # Extreme spread analysis (lowered threshold so we see real examples)
    high = combined[combined['funding_spread'] > 0.00015]
    low  = combined[combined['funding_spread'] < -0.00015]
    
    print(f"\nWhen BTC funding premium > +0.015% (n={len(high)}): avg next 8h BTC/ETH return = {high['ratio_return_8h'].mean():.4%}")
    print(f"When ETH funding premium > +0.015% (n={len(low)}):  avg next 8h BTC/ETH return = {low['ratio_return_8h'].mean():.4%}")
    
    return combined

# ================== PLOTTING (now saves HTML - works on WSL!) ==================
def save_plot(combined: pd.DataFrame, hours: int = None):
    if hours:
        end = combined.index.max()
        start = end - timedelta(hours=hours)
        df = combined.loc[start:]
        name = f"last_{hours}h"
        title = f"WETH-cbBTC Proxy — Last {hours} Hours"
    else:
        df = combined
        name = "full_2y"
        title = "2-Year: BTC/ETH Ratio vs Funding Spread (WETH-cbBTC)"
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=df.index, y=df['btc_eth_ratio'], name='BTC/ETH Ratio', line=dict(color='gold', width=2)), secondary_y=False)
    fig.add_trace(go.Bar(x=df.index, y=df['funding_spread']*10000, name='Funding Spread (bps)', marker_color='cyan', opacity=0.65), secondary_y=True)
    
    fig.update_layout(
        title=title,
        xaxis_title="Time",
        yaxis_title="BTC/ETH Ratio",
        yaxis2_title="Funding Spread (basis points)",
        template="plotly_dark",
        height=680,
        xaxis_rangeslider_visible=True
    )
    
    filename = f"btc_eth_funding_spread_{name}.html"
    fig.write_html(filename)
    print(f"✅ Saved interactive plot: {filename}")
    print(f"   → Double-click it to open in your browser (full zoom & slider)")

# ================== MAIN ==================
if __name__ == "__main__":
    INTERVAL = '15m'
    YEARS = 2
    
    print("Fetching 2 years of BTC data...")
    btc_price = get_full_klines('BTCUSDT', INTERVAL, YEARS)
    btc_fund  = get_full_funding_history('BTCUSDT', YEARS)
    
    print("Fetching 2 years of ETH data...")
    eth_price = get_full_klines('ETHUSDT', INTERVAL, YEARS)
    eth_fund  = get_full_funding_history('ETHUSDT', YEARS)
    
    print("Merging and analyzing...")
    btc_merged = merge_price_funding(btc_price, btc_fund)
    eth_merged = merge_price_funding(eth_price, eth_fund)
    
    combined = analyze_btc_eth_pair(btc_merged, eth_merged)
    
    combined.to_csv("btc_eth_funding_spread_2y.csv")
    print(f"\nData saved to CSV! Total rows: {len(combined)}")
    
    # Save plots as HTML (no more gio error)
    save_plot(combined)           # full 2-year
    for h in [6, 12, 24]:
        save_plot(combined, hours=h)
    
    print("\n✅ All done! Open the .html files in your browser.")
    print("   Drag the bottom slider to zoom into the last 6–12 hours exactly as you wanted.")
