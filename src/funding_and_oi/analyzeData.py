import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
import seaborn as sns

# ====================== LOAD DATA ======================
df = pd.read_csv('btc_eth_funding_spread_2y.csv', parse_dates=['open_time'])
df.set_index('open_time', inplace=True)
df.sort_index(inplace=True)

# ====================== BASIC STATS ======================
print("=== BASIC STATS ===")
print(df[['btc_close', 'eth_close', 'btc_funding', 'eth_funding', 'funding_spread']].describe())

print("\n=== FUNDING DIRECTIONAL SKEW ===")
print(f"BTC funding positive: {(df['btc_funding'] > 0).mean():.1%}")
print(f"ETH funding positive: {(df['eth_funding'] > 0).mean():.1%}")
print(f"Spread positive (BTC > ETH): {(df['funding_spread'] > 0).mean():.1%}")
print(f"Spread skewness: {stats.skew(df['funding_spread']):.3f}")

abs_spread = np.abs(df['funding_spread'])

# ====================== MAIN PNG ======================
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

plt.savefig('btc_eth_funding_main.png', dpi=180, bbox_inches='tight', facecolor='white')

# ====================== EXTRA PNG ======================
fig_extra = plt.figure(figsize=(16, 9), constrained_layout=True)

ax5 = fig_extra.add_subplot(1, 2, 1)
sns.histplot(df['funding_spread'], bins=100, kde=True, color='purple', ax=ax5)
ax5.axvline(0, color='gray', ls='--')
ax5.set_title('Distribution of Funding Spread')
ax5.set_xlabel('Funding Spread')

ax6 = fig_extra.add_subplot(1, 2, 2)
sc2 = ax6.scatter(df['btc_eth_ratio'], df['funding_spread'],
                  c=abs_spread, cmap='RdYlGn_r', alpha=0.6, s=4)
fig_extra.colorbar(sc2, ax=ax6, label='|Spread| Skew Magnitude')
ax6.axhline(0, color='gray', ls='--')
ax6.set_xlabel('BTC/ETH Price Ratio')
ax6.set_ylabel('Funding Spread')
ax6.set_title('BTC/ETH Ratio vs Funding Spread')

fig_extra.suptitle(f'BTC-ETH Funding Extra Charts\n{df.index[0].date()} — {df.index[-1].date()}', 
                   fontsize=16, fontweight='bold')

plt.savefig('btc_eth_funding_extra.png', dpi=200, bbox_inches='tight', facecolor='white')

# ====================== 24H RATIO CHANGE ======================
df['ratio_24h_change'] = df['btc_eth_ratio'].shift(-96) - df['btc_eth_ratio']

# ====================== HIGHLIGHTED LARGE SPREAD CHART ======================
plt.figure(figsize=(12, 8))
plt.scatter(df['funding_spread'], df['ratio_24h_change'],
            c='lightgray', s=3, alpha=0.4, label='All data (small spread)')

large_mask = abs_spread > 0.00015
sc3 = plt.scatter(df.loc[large_mask, 'funding_spread'], 
                  df.loc[large_mask, 'ratio_24h_change'],
                  c=abs_spread[large_mask], cmap='RdYlGn_r', s=20, alpha=0.95, 
                  edgecolor='black', linewidth=0.5, label='Large spread (>0.00015)')

plt.colorbar(sc3, label='|Current Spread| → Skew Magnitude (Large spreads only)')
plt.axhline(0, color='gray', ls='--', lw=1)
plt.axvline(0, color='gray', ls='--', lw=1)
plt.xlabel('Current Funding Spread (BTC - ETH)')
plt.ylabel('BTC/ETH Ratio Change over Next 24h')
plt.title('Large Funding Spreads Highlighted vs Future BTC/ETH Ratio Move')
plt.legend()
plt.savefig('btc_eth_spread_vs_future_ratio.png', dpi=180, bbox_inches='tight')
plt.close()

# ====================== PREDICT LARGE RATIO MOVES ======================
large_ratio_threshold = df['ratio_24h_change'].abs().quantile(0.90)
df['large_ratio_move'] = df['ratio_24h_change'].abs() > large_ratio_threshold

print(f"\n=== PREDICTING LARGE BTC/ETH RATIO MOVES (top 10% magnitude) ===")
print(f"Large move threshold (|24h ratio change|): {large_ratio_threshold:.4f}")

baseline = df['large_ratio_move'].mean()
when_large_spread = df[abs_spread > 0.00015]['large_ratio_move'].mean()

print(f"Baseline probability of large move: {baseline:.1%}")
print(f"When |spread| > 0.00015 → probability of large move: {when_large_spread:.1%}")
print(f"Lift: {when_large_spread / baseline:.2f}x more likely")

plt.figure(figsize=(12, 8))
plt.scatter(df['funding_spread'], df['ratio_24h_change'],
            c='lightgray', s=3, alpha=0.4)

large_move_mask = df['large_ratio_move']
plt.scatter(df.loc[large_move_mask, 'funding_spread'], 
            df.loc[large_move_mask, 'ratio_24h_change'],
            c='red', s=25, alpha=0.9, edgecolor='black', linewidth=0.5, 
            label=f'Large ratio move (|Δ| > {large_ratio_threshold:.4f})')

plt.axhline(0, color='gray', ls='--', lw=1)
plt.axvline(0, color='gray', ls='--', lw=1)
plt.xlabel('Current Funding Spread (BTC - ETH)')
plt.ylabel('BTC/ETH Ratio Change over Next 24h')
plt.title('Large BTC/ETH Ratio Moves Highlighted')
plt.legend()
plt.savefig('btc_eth_large_ratio_moves.png', dpi=180, bbox_inches='tight')
plt.close()

df['funding_spread_abs'] = abs_spread
big_div = df.nlargest(10, 'funding_spread_abs')
print("\nTop 10 largest funding spreads and 24h BTC/ETH ratio change afterward:")
print(big_div[['funding_spread', 'ratio_24h_change']].round(6))

# ====================== SIMPLE SINGLE-LINE 14D FUNDING SPREAD CHART (KST) ======================
print("\nGenerating Simple 14D Funding Spread Chart (single line, tight Y, KST)...")

end_time = df.index.max()
start_time = end_time - pd.Timedelta(days=14)
recent_df = df[(df.index >= start_time) & (df.index <= end_time)].copy()

# Convert to KST (UTC+9, no DST)
recent_df = recent_df.copy()
recent_df.index = recent_df.index.tz_localize('UTC').tz_convert('Asia/Seoul')

if len(recent_df) < 20:
    print("   Warning: Less than 14d of data — using last 1400 points as fallback")
    recent_df = df.tail(1400).copy()
    recent_df.index = recent_df.index.tz_localize('UTC').tz_convert('Asia/Seoul')

fig, ax = plt.subplots(figsize=(15, 8.5))

spread_scaled = recent_df['funding_spread'] * 1_000_000

# Clean single purple line only
ax.plot(recent_df.index, spread_scaled, 
        color='purple', lw=3.5, marker='o', markersize=3.5, 
        label='BTC-ETH Funding Spread (Delta)')

ax.axhline(0, color='black', ls='--', lw=1.5)

# Tight Y-zoom focused only on the actual spread values
data_min = spread_scaled.min()
data_max = spread_scaled.max()
data_range = data_max - data_min
if data_range < 0.1:
    data_range = 1.0
padding = 0.25 * data_range
ax.set_ylim(data_min - padding, data_max + padding)

# Big current-value annotation
current_spread = recent_df['funding_spread'].iloc[-1]
current_scaled = current_spread * 1_000_000

ax.annotate(f'CURRENT SPREAD\n{current_spread:+.8f}\n({current_scaled:+.2f} ×10⁻⁶)', 
            xy=(recent_df.index[-1], current_scaled),
            xytext=(35, 45 if current_spread >= 0 else -70),
            textcoords='offset points',
            fontsize=15, fontweight='bold', ha='left',
            bbox=dict(boxstyle="round,pad=0.8", facecolor='yellow', alpha=0.95))

ax.set_title('BTC - ETH Funding Rate Difference (Last 14 Days)', fontsize=18, fontweight='bold', pad=20)
ax.set_ylabel('Spread × 1,000,000', fontsize=14)
ax.set_xlabel('Time (KST)')                    # ← now KST
ax.legend(fontsize=12, loc='upper right')
ax.grid(True, alpha=0.35)

# Updated suptitle with KST time
fig.suptitle(f'Latest data: {recent_df.index[-1].strftime("%Y-%m-%d %H:%M KST")}', 
             fontsize=13, y=0.97)

plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('btc_eth_funding_14d_delta.png', dpi=260, bbox_inches='tight', facecolor='white')
plt.close()

print(f"   • btc_eth_funding_14d_delta.png  (KST version | Current: {current_spread:+.8f})")

# ====================== FINAL MESSAGE ======================
print("\n✅ ALL DONE! Files saved:")
print("   • btc_eth_funding_main.png")
print("   • btc_eth_funding_extra.png")
print("   • btc_eth_spread_vs_future_ratio.png")
print("   • btc_eth_large_ratio_moves.png")
print("   • btc_eth_funding_14d_delta.png")
