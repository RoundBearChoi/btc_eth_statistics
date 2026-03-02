import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
import seaborn as sns

# Load data
df = pd.read_csv('btc_eth_funding_spread_2y.csv', parse_dates=['open_time'])
df.set_index('open_time', inplace=True)
df.sort_index(inplace=True)

# Stats (still printed so you see the summary)
print("=== BASIC STATS ===")
print(df[['btc_close', 'eth_close', 'btc_funding', 'eth_funding', 'funding_spread']].describe())

print("\n=== FUNDING DIRECTIONAL SKEW ===")
print(f"BTC funding positive: {(df['btc_funding'] > 0).mean():.1%}")
print(f"ETH funding positive: {(df['eth_funding'] > 0).mean():.1%}")
print(f"Spread positive (BTC > ETH): {(df['funding_spread'] > 0).mean():.1%}")
print(f"Spread skewness: {stats.skew(df['funding_spread']):.3f}")

# ====================== MAIN PNG (Prices + Rates + Spread + Monthly) ======================
fig_main = plt.figure(figsize=(16, 22), constrained_layout=True)

ax1 = fig_main.add_subplot(4, 1, 1)
ax1.plot(df.index, df['btc_close'], label='BTC Close', color='orange', lw=1.5)
ax1_twin = ax1.twinx()
ax1_twin.plot(df.index, df['eth_close'], label='ETH Close', color='blue', lw=1.5)
ax1.set_ylabel('BTC Price (USD)', color='orange')
ax1_twin.set_ylabel('ETH Price (USD)', color='blue')
ax1.legend(loc='upper left')
ax1_twin.legend(loc='upper right')
ax1.set_title('BTC & ETH Prices')

ax2 = fig_main.add_subplot(4, 1, 2)
ax2.plot(df.index, df['btc_funding'], label='BTC Funding', color='orange')
ax2.plot(df.index, df['eth_funding'], label='ETH Funding', color='blue')
ax2.axhline(0, color='gray', ls='--', lw=0.8)
ax2.set_ylabel('Funding Rate')
ax2.legend()
ax2.set_title('BTC vs ETH Funding Rates (positive = bullish skew)')

ax3 = fig_main.add_subplot(4, 1, 3)
abs_spread = np.abs(df['funding_spread'])
sc = ax3.scatter(df.index, df['funding_spread'],
                 c=abs_spread, cmap='RdYlGn_r', s=3, alpha=0.7)
ax3.axhline(0, color='gray', ls='--', lw=0.8)
ax3.set_ylabel('Funding Spread (BTC - ETH)')
fig_main.colorbar(sc, ax=ax3, label='|Spread| → Skew Magnitude (Green=small/balanced • Red=large skew)')
ax3.set_title('Funding Spread + Skew Strength')

ax4 = fig_main.add_subplot(4, 1, 4)
monthly = df['funding_spread'].resample('ME').mean()
monthly_abs = np.abs(monthly)
colors = plt.cm.RdYlGn_r(monthly_abs / monthly_abs.max())
ax4.bar(monthly.index, monthly, color=colors, width=20)
ax4.axhline(0, color='gray', ls='--')
ax4.set_title('Monthly Average Funding Spread (Green=small skew • Red=large skew)')
ax4.set_ylabel('Avg Spread')
ax4.tick_params(axis='x', rotation=45)

fig_main.suptitle(f'BTC-ETH Funding Main Analysis\n{df.index[0].date()} — {df.index[-1].date()}', 
                  fontsize=18, fontweight='bold', y=0.98)

plt.savefig('btc_eth_funding_main.png', 
            dpi=180, 
            bbox_inches='tight', 
            facecolor='white')

# ====================== EXTRA PNG (Histogram + Ratio Scatter) ======================
fig_extra = plt.figure(figsize=(16, 9), constrained_layout=True)

ax5 = fig_extra.add_subplot(1, 2, 1)
sns.histplot(df['funding_spread'], bins=100, kde=True, color='purple', ax=ax5)
ax5.axvline(0, color='gray', ls='--')
ax5.set_title('Distribution of Funding Spread')
ax5.set_xlabel('Funding Spread')

ax6 = fig_extra.add_subplot(1, 2, 2)
sc2 = ax6.scatter(df['btc_eth_ratio'], df['funding_spread'],
                  c=np.abs(df['funding_spread']), cmap='RdYlGn_r', alpha=0.6, s=4)
fig_extra.colorbar(sc2, ax=ax6, label='|Spread| Skew Magnitude')
ax6.axhline(0, color='gray', ls='--')
ax6.set_xlabel('BTC/ETH Price Ratio')
ax6.set_ylabel('Funding Spread')
ax6.set_title('BTC/ETH Ratio vs Funding Spread')

fig_extra.suptitle(f'BTC-ETH Funding Extra Charts\n{df.index[0].date()} — {df.index[-1].date()}', 
                   fontsize=16, fontweight='bold')

plt.savefig('btc_eth_funding_extra.png', 
            dpi=200, 
            bbox_inches='tight', 
            facecolor='white')

# No plt.show() → script finishes instantly
print("\n✅ DONE! Files saved silently:")
print("   • btc_eth_funding_main.png     ← Prices + Funding Rates + Spread Skew + Monthly")
print("   • btc_eth_funding_extra.png    ← Histogram + BTC/ETH Ratio Scatter")
print("   → Both files ~1.8–2.5 MB and crystal clear")
