import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from scipy import stats
import seaborn as sns

# Load data
df = pd.read_csv('btc_eth_funding_spread_2y.csv', parse_dates=['open_time'])
df.set_index('open_time', inplace=True)
df.sort_index(inplace=True)

print("=== BASIC STATS ===")
print(df[['btc_close', 'eth_close', 'btc_funding', 'eth_funding', 'funding_spread']].describe())

print("\n=== FUNDING DIRECTIONAL SKEW ===")
print(f"BTC funding positive: {(df['btc_funding'] > 0).mean():.1%}")
print(f"ETH funding positive: {(df['eth_funding'] > 0).mean():.1%}")
print(f"Spread positive (BTC > ETH funding): {(df['funding_spread'] > 0).mean():.1%}")
print(f"Spread skewness: {stats.skew(df['funding_spread']):.3f}")

# === CHARTS ===
fig, axs = plt.subplots(3, 1, figsize=(15, 12), sharex=True, gridspec_kw={'height_ratios': [2, 1, 1]})

# 1. Prices
axs[0].plot(df.index, df['btc_close'], label='BTC', color='orange', lw=1.5)
ax0_t = axs[0].twinx()
ax0_t.plot(df.index, df['eth_close'], label='ETH', color='blue', lw=1.5)
axs[0].set_ylabel('BTC Price', color='orange')
ax0_t.set_ylabel('ETH Price', color='blue')
axs[0].legend(loc='upper left')
ax0_t.legend(loc='upper right')
axs[0].set_title('BTC & ETH Prices')

# 2. Individual funding rates
axs[1].plot(df.index, df['btc_funding'], label='BTC Funding', color='orange')
axs[1].plot(df.index, df['eth_funding'], label='ETH Funding', color='blue')
axs[1].axhline(0, color='gray', ls='--', lw=0.8)
axs[1].set_ylabel('Funding Rate')
axs[1].legend()
axs[1].set_title('Funding Rates (positive = longs pay shorts)')

# 3. Spread with color-coded skew magnitude (green=small, red=large)
abs_spread = np.abs(df['funding_spread'])
sc = axs[2].scatter(df.index, df['funding_spread'],
                    c=abs_spread,
                    cmap='RdYlGn_r',  # ← exactly what you asked for
                    s=4, alpha=0.7)
axs[2].axhline(0, color='gray', ls='--', lw=0.8)
axs[2].set_ylabel('Funding Spread (BTC - ETH)')
plt.colorbar(sc, ax=axs[2], label='|Spread| → Skew Strength (Green=balanced, Red=large skew)')
axs[2].set_title('Funding Spread + Skew Magnitude')

plt.suptitle(f'BTC-ETH Funding Analysis • {df.index[0].date()} to {df.index[-1].date()}', fontsize=16)
plt.tight_layout()
plt.savefig('funding_overview.png', dpi=300, bbox_inches='tight')
plt.show()

# Extra charts (histogram + ratio scatter + monthly)
plt.figure(figsize=(10, 6))
sns.histplot(df['funding_spread'], bins=100, kde=True, color='purple')
plt.axvline(0, color='gray', ls='--')
plt.title('Distribution of Funding Spread')
plt.savefig('spread_histogram.png', dpi=300)
plt.show()

plt.figure(figsize=(10, 6))
plt.scatter(df['btc_eth_ratio'], df['funding_spread'],
            c=np.abs(df['funding_spread']), cmap='RdYlGn_r', alpha=0.6, s=5)
plt.colorbar(label='|Spread| Skew Magnitude')
plt.axhline(0, color='gray', ls='--')
plt.xlabel('BTC/ETH Price Ratio')
plt.ylabel('Funding Spread')
plt.title('BTC/ETH Ratio vs Funding Spread')
plt.savefig('ratio_vs_spread.png', dpi=300)
plt.show()

# Monthly average (FIXED)
monthly = df['funding_spread'].resample('ME').mean()   # ← this was the only change
monthly_abs = np.abs(monthly)
plt.figure(figsize=(12, 6))
colors = plt.cm.RdYlGn_r(monthly_abs / monthly_abs.max())
plt.bar(monthly.index, monthly, color=colors, width=20)
plt.axhline(0, color='gray', ls='--')
plt.title('Monthly Average Funding Spread (Green=small skew • Red=large skew)')
plt.ylabel('Avg Spread')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('monthly_spread.png', dpi=300)
plt.show()

print("\n✅ All charts saved!")
print("   • funding_overview.png   ← main one")
print("   • monthly_spread.png     ← green/red skew you wanted")
