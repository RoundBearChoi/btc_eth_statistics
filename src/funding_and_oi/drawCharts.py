import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import yfinance as yf
import time

# ============== CONFIG ==============
YEARS_BACK = 2          # ← change to 1, 3, 8, whatever you want
START_DATE_FUNDING = '2024-01-01'   # only fetch recent funding (faster)
# ====================================

def fetch_binance_funding(symbol='BTCUSDT', start_date=START_DATE_FUNDING):
    url = 'https://fapi.binance.com/fapi/v1/fundingRate'
    all_data = []
    start_ts = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp() * 1000)
    limit = 1000
    while True:
        params = {'symbol': symbol, 'startTime': start_ts, 'limit': limit}
        resp = requests.get(url, params=params)
        batch = resp.json()
        if not batch:
            break
        all_data.extend(batch)
        if len(batch) < limit:
            break
        start_ts = int(batch[-1]['fundingTime']) + 1
        time.sleep(0.2)
    
    df = pd.DataFrame(all_data)
    df['fundingTime'] = pd.to_datetime(df['fundingTime'], unit='ms')
    df['fundingRate'] = pd.to_numeric(df['fundingRate']) * 100   # in %
    return df

# ==================== FETCH DATA ====================
funding_df = fetch_binance_funding()

# BTC price
data = yf.download('BTC-USD', start='2023-01-01', progress=False)
btc = data[['Close']].copy()
if isinstance(btc.columns, pd.MultiIndex):
    btc.columns = btc.columns.get_level_values(0)
btc = btc.reset_index()
btc['Date'] = pd.to_datetime(btc['Date']).dt.date

# Daily avg funding
funding_daily = funding_df.resample('D', on='fundingTime')['fundingRate'].mean().reset_index()
funding_daily['Date'] = funding_daily['fundingTime'].dt.date

merged = pd.merge(btc, funding_daily[['Date', 'fundingRate']], on='Date', how='left')

# ==================== ZOOM TO LAST N YEARS ====================
cutoff = (datetime.now() - timedelta(days=YEARS_BACK * 365.25)).date()
merged = merged[merged['Date'] >= cutoff].copy()

# 7-day MA for smoother funding view (very useful on 2y chart)
merged['fundingRate_ma7'] = merged['fundingRate'].rolling(window=7, min_periods=1).mean()

# ==================== PLOT ====================
fig, ax1 = plt.subplots(figsize=(16, 9))

# Price (left axis)
ax1.plot(merged['Date'], merged['Close'], color='#1f77b4', linewidth=2.8, label='BTC Price (USD)')
ax1.set_ylabel('BTC Price (USD)', color='#1f77b4', fontsize=13)
ax1.tick_params(axis='y', labelcolor='#1f77b4')

# Funding (right axis)
ax2 = ax1.twinx()
ax2.bar(merged['Date'], merged['fundingRate'], color='#d62728', alpha=0.65, width=0.85, label='Daily Avg Funding Rate (%)')
ax2.plot(merged['Date'], merged['fundingRate_ma7'], color='#ff7f0e', linewidth=2.2, label='7-day MA Funding Rate (%)')
ax2.set_ylabel('Funding Rate (%)', color='#d62728', fontsize=13)
ax2.tick_params(axis='y', labelcolor='#d62728')

plt.title(f'BTC/USD vs Binance Perpetual Funding Rate — Last {YEARS_BACK} Years', fontsize=17, pad=20)
fig.legend(loc="upper left", bbox_to_anchor=(0.12, 0.88), fontsize=11)
plt.grid(True, alpha=0.35)
plt.xticks(rotation=45)
plt.tight_layout()

plt.savefig(f'btc_funding_{YEARS_BACK}y_chart.png', dpi=300, bbox_inches='tight')
plt.show()

print(f"✅ Chart saved → btc_funding_{YEARS_BACK}y_chart.png")
print("\nLast 10 rows:\n", merged.tail(10)[['Date', 'Close', 'fundingRate', 'fundingRate_ma7']].round(4))
