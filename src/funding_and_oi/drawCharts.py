import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import yfinance as yf
import time
import sys


class BTCLeverageChart:
    def __init__(self, months: int = 1.5, figsize: tuple = (13, 7.5), dpi: int = 200):
        self.months = months
        self.days_back = int(months * 30.4375)   # accurate average month length
        self.figsize = figsize
        self.dpi = dpi
        self.symbol = 'BTCUSDT'

    def fetch_binance_funding(self):
        print(f"Fetching Funding (Binance, last {self.months:.1f} months)...")
        url = 'https://fapi.binance.com/fapi/v1/fundingRate'
        all_data = []
        start_ts = int((datetime.now() - timedelta(days=self.days_back + 15)).timestamp() * 1000)
        headers = {'User-Agent': 'Mozilla/5.0'}
        while True:
            params = {'symbol': self.symbol, 'startTime': start_ts, 'limit': 1000}
            resp = requests.get(url, params=params, headers=headers)
            if resp.status_code != 200:
                break
            batch = resp.json()
            if not batch:
                break
            all_data.extend(batch)
            if len(batch) < 1000:
                break
            start_ts = int(batch[-1]['fundingTime']) + 1
            time.sleep(0.25)
        df = pd.DataFrame(all_data)
        df['fundingTime'] = pd.to_datetime(df['fundingTime'], unit='ms')
        df['fundingRate'] = pd.to_numeric(df['fundingRate']) * 100
        return df

    def fetch_binance_oi(self):
        print(f"Fetching Open Interest (Binance, last {self.months:.1f} months)...")
        url = 'https://fapi.binance.com/futures/data/openInterestHist'
        all_data = []
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        end_ts = int(datetime.now().timestamp() * 1000)
        limit = 500
        for _ in range(12):   # generous safety for up to ~12 months
            params = {'symbol': self.symbol, 'period': '1d', 'limit': limit, 'endTime': end_ts}
            resp = requests.get(url, params=params, headers=headers)
            if resp.status_code != 200:
                break
            batch = resp.json()
            if not isinstance(batch, list) or not batch:
                break
            all_data.extend(batch)
            end_ts = int(batch[-1]['timestamp']) - 86400000
            time.sleep(0.35)
        df = pd.DataFrame(all_data)
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['oi_usd_billions'] = pd.to_numeric(df['sumOpenInterestValue']) / 1_000_000_000
        return df

    def fetch_btc_price(self):
        print("Fetching BTC Price...")
        start_date = (datetime.now() - timedelta(days=self.days_back + 30)).strftime('%Y-%m-%d')
        data = yf.download('BTC-USD', start=start_date, progress=False)
        btc = data[['Close']].copy()
        if isinstance(btc.columns, pd.MultiIndex):
            btc.columns = btc.columns.get_level_values(0)
        btc = btc.reset_index()
        btc['Date'] = pd.to_datetime(btc['Date']).dt.date
        return btc

    def process_data(self, funding_df, oi_df, btc):
        funding_daily = funding_df.resample('D', on='fundingTime')['fundingRate'].mean().reset_index()
        funding_daily['Date'] = funding_daily['fundingTime'].dt.date

        oi_daily = oi_df.resample('D', on='timestamp')['oi_usd_billions'].mean().reset_index()
        oi_daily['Date'] = oi_daily['timestamp'].dt.date

        merged = pd.merge(btc, funding_daily[['Date', 'fundingRate']], on='Date', how='left')
        merged = pd.merge(merged, oi_daily[['Date', 'oi_usd_billions']], on='Date', how='left')

        cutoff = (datetime.now() - timedelta(days=self.days_back)).date()
        merged = merged[merged['Date'] >= cutoff].copy().reset_index(drop=True)
        merged['fundingRate_ma7'] = merged['fundingRate'].rolling(7, min_periods=1).mean()
        merged['oi_usd_billions'] = merged['oi_usd_billions'].ffill()
        return merged

    def plot_and_save(self, merged):
        fig, ax1 = plt.subplots(figsize=self.figsize)

        ax1.plot(merged['Date'], merged['Close'], color='#1f77b4', linewidth=2.8, label='BTC Price (USD)')
        ax1.set_ylabel('BTC Price (USD)', color='#1f77b4', fontsize=12)
        ax1.tick_params(axis='y', labelcolor='#1f77b4')

        ax3 = ax1.twinx()
        ax3.spines['right'].set_position(('outward', 60))
        ax3.plot(merged['Date'], merged['oi_usd_billions'], color='#2ca02c', linewidth=2.5, label='Open Interest ($B)')
        ax3.fill_between(merged['Date'], merged['oi_usd_billions'], color='#2ca02c', alpha=0.18)
        ax3.set_ylabel('Open Interest ($ Billions)', color='#2ca02c', fontsize=12)
        ax3.tick_params(axis='y', labelcolor='#2ca02c')

        ax2 = ax1.twinx()
        ax2.plot(merged['Date'], merged['fundingRate_ma7'], color='#ff7f0e', linewidth=2.2, label='7-day MA Funding (%)')
        ax2.bar(merged['Date'], merged['fundingRate'], color='#d62728', alpha=0.65, width=0.9, label='Daily Funding (%)')
        ax2.set_ylabel('Funding Rate (%)', color='#d62728', fontsize=12)
        ax2.tick_params(axis='y', labelcolor='#d62728')

        plt.title(f'BTC/USD — Price + Funding + Open Interest (Binance Only)\nLast {self.months:.1f} Months — Fully Automatic',
                  fontsize=15, pad=15)
        fig.legend(loc="upper left", bbox_to_anchor=(0.12, 0.88), fontsize=10, ncol=3)
        plt.grid(True, alpha=0.35)
        plt.xticks(rotation=45)
        plt.tight_layout()

        filename = f'btc_binance_price_funding_oi_{self.months:.0f}m_small.png'
        plt.savefig(filename, dpi=self.dpi, bbox_inches='tight')
        plt.show()
        print(f"\n✅ Chart saved → {filename}")

    def print_stats(self, merged):
        print(f"Positive funding days : {(merged['fundingRate'] > 0).mean()*100:.1f}%")
        print(f"Avg OI                : ${merged['oi_usd_billions'].mean():.1f}B")
        print("Last 5 days:")
        print(merged.tail(5)[['Date', 'Close', 'fundingRate', 'oi_usd_billions']].round(3))

    def run(self):
        funding_df = self.fetch_binance_funding()
        oi_df = self.fetch_binance_oi()
        btc = self.fetch_btc_price()
        merged = self.process_data(funding_df, oi_df, btc)
        self.plot_and_save(merged)
        self.print_stats(merged)


if __name__ == "__main__":
    # CLI support: python drawCharts.py 12
    months = 1.5   # default ≈45 days
    if len(sys.argv) > 1:
        try:
            months = float(sys.argv[1])
        except ValueError:
            print("Usage: python drawCharts.py [months]   e.g. python drawCharts.py 12")
            months = 1.5

    chart = BTCLeverageChart(months=months)
    chart.run()
