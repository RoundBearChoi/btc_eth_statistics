import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import yfinance as yf
import time
import sys
import warnings
warnings.filterwarnings('ignore')

class BTCLeverageChart:
    def __init__(self, days: int = 30, interval: str = '1h', figsize: tuple = (14, 8), dpi: int = 200):
        self.days_back = days
        self.interval = interval.lower()
        self.figsize = figsize
        self.dpi = dpi
        self.symbol = 'BTCUSDT'
        self.valid_intervals = ['5m', '15m', '30m', '1h']

        if self.interval not in self.valid_intervals:
            print(f"⚠️  Using 1h (recommended). Valid: 5m,15m,30m,1h")
            self.interval = '1h'

    def _make_tz_naive(self, df):
        if not df.empty and df.index.tz is not None:
            df.index = df.index.tz_convert(None)
        return df

    def fetch_binance_funding(self):
        print(f"Fetching Funding (Binance 8h candles, last {self.days_back}d)...")
        url = 'https://fapi.binance.com/fapi/v1/fundingRate'
        all_data = []
        start_ts = int((datetime.now() - timedelta(days=self.days_back + 5)).timestamp() * 1000)
        headers = {'User-Agent': 'Mozilla/5.0'}
        while True:
            params = {'symbol': self.symbol, 'startTime': start_ts, 'limit': 1000}
            resp = requests.get(url, params=params, headers=headers)
            if resp.status_code != 200 or not resp.json():
                break
            batch = resp.json()
            all_data.extend(batch)
            if len(batch) < 1000:
                break
            start_ts = int(batch[-1]['fundingTime']) + 1
            time.sleep(0.25)
        df = pd.DataFrame(all_data)
        df['timestamp'] = pd.to_datetime(df['fundingTime'], unit='ms')
        df['fundingRate'] = pd.to_numeric(df['fundingRate']) * 100
        df = df[['timestamp', 'fundingRate']].set_index('timestamp')
        return self._make_tz_naive(df)

    def fetch_binance_oi(self):
        print(f"Fetching Open Interest (Binance {self.interval} granularity, last {self.days_back}d)...")
        url = 'https://fapi.binance.com/futures/data/openInterestHist'
        all_data = []
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        end_ts = int(datetime.now().timestamp() * 1000)
        limit = 500
        for _ in range(12):
            params = {'symbol': self.symbol, 'period': self.interval, 'limit': limit, 'endTime': end_ts}
            resp = requests.get(url, params=params, headers=headers)
            if resp.status_code != 200:
                break
            batch = resp.json()
            if not isinstance(batch, list) or not batch:
                break
            all_data.extend(batch)
            minutes = int(self.interval[:-1]) if 'm' in self.interval else 60
            end_ts -= minutes * 60 * 1000
            time.sleep(0.3)
        df = pd.DataFrame(all_data)
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['oi_usd_billions'] = pd.to_numeric(df['sumOpenInterestValue']) / 1_000_000_000
            df = df[['timestamp', 'oi_usd_billions']].set_index('timestamp')
            df = self._make_tz_naive(df)
        return df

    def fetch_btc_price(self):
        print(f"Fetching BTC Price ({self.interval} granularity)...")
        data = yf.download('BTC-USD', period=f'{self.days_back}d', interval=self.interval, progress=False)
        btc = data[['Close']].copy()
        if isinstance(btc.columns, pd.MultiIndex):
            btc.columns = btc.columns.get_level_values(0)
        btc.index.name = 'timestamp'
        btc = btc.rename(columns={'Close': 'price'})
        return self._make_tz_naive(btc)

    def process_data(self, funding_df, oi_df, price_df):
        freq = self.interval.replace('m', 'T').replace('h', 'h')
        price = price_df.resample(freq).last()
        oi = oi_df.resample(freq).mean()
        funding = funding_df.resample(freq).mean().reindex(price.index).ffill()

        merged = pd.concat([price, oi, funding], axis=1, sort=False)
        merged = merged.dropna(subset=['price']).reset_index()
        merged['fundingRate_ma7'] = merged['fundingRate'].rolling(7, min_periods=1).mean()
        return merged

    def plot_and_save(self, merged):
        fig, ax1 = plt.subplots(figsize=self.figsize)

        # Blue price line on top (zorder=10)
        ax1.plot(merged['timestamp'], merged['price'], color='#1f77b4', linewidth=2.8, label='BTC Price (USD)', zorder=10)
        ax1.set_ylabel('BTC Price (USD)', color='#1f77b4', fontsize=12)
        ax1.tick_params(axis='y', labelcolor='#1f77b4')

        # Green OI
        ax3 = ax1.twinx()
        ax3.spines['right'].set_position(('outward', 60))
        ax3.plot(merged['timestamp'], merged['oi_usd_billions'], color='#2ca02c', linewidth=2.5, label='Open Interest ($B)', zorder=5)
        ax3.fill_between(merged['timestamp'], merged['oi_usd_billions'], color='#2ca02c', alpha=0.18)
        ax3.set_ylabel('Open Interest ($ Billions)', color='#2ca02c', fontsize=12)
        ax3.tick_params(axis='y', labelcolor='#2ca02c')

        # Red funding bars — now highly transparent + slightly narrower
        ax2 = ax1.twinx()
        ax2.plot(merged['timestamp'], merged['fundingRate_ma7'], color='#ff7f0e', linewidth=2.2, label='MA Funding Rate (%)', zorder=9)
        #ax2.bar(merged['timestamp'], merged['fundingRate'], color='#d62728', alpha=0.35, width=0.85, label='Funding Rate (%)', zorder=3)
        ax2.set_ylabel('Funding Rate (%)', color='#d62728', fontsize=12)
        ax2.tick_params(axis='y', labelcolor='#d62728')

        plt.title(f'BTC/USD — Price + Funding + Open Interest (Binance)\nLast {self.days_back} Days @ {self.interval}',
                  fontsize=15, pad=15)
        fig.legend(loc="upper left", bbox_to_anchor=(0.12, 0.88), fontsize=10, ncol=3)
        plt.grid(True, alpha=0.35)
        plt.xticks(rotation=45)
        plt.tight_layout()

        filename = f'btc_binance_price_funding_oi_{self.days_back}d_{self.interval}.png'
        plt.savefig(filename, dpi=self.dpi, bbox_inches='tight')
        plt.close()
        print(f"\n✅ Chart saved → {filename}")

    def print_stats(self, merged):
        print(f"Positive funding periods : {(merged['fundingRate'] > 0).mean()*100:.1f}%")
        print(f"Avg OI                   : ${merged['oi_usd_billions'].mean():.1f}B")
        print("Last 10 rows:")
        print(merged.tail(10)[['timestamp', 'price', 'fundingRate', 'oi_usd_billions']].round(4))

    def run(self):
        funding_df = self.fetch_binance_funding()
        oi_df = self.fetch_binance_oi()
        price_df = self.fetch_btc_price()
        merged = self.process_data(funding_df, oi_df, price_df)
        self.plot_and_save(merged)
        self.print_stats(merged)


if __name__ == "__main__":
    days = 30
    interval = '1h'
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except:
            pass
    if len(sys.argv) > 2:
        interval = sys.argv[2]

    chart = BTCLeverageChart(days=days, interval=interval)
    chart.run()
