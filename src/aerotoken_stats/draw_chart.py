import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

# 1. Load the data
df = pd.read_csv('AERO_5m_3weeks_bybit.csv')
df['datetime'] = pd.to_datetime(df['datetime'])
df = df.set_index('datetime')
df = df.sort_index()

# 2. Calculate two EMAs
df['EMA21'] = df['close'].ewm(span=21, adjust=False).mean()   # short-term (~1.75 hours)
df['EMA50'] = df['close'].ewm(span=50, adjust=False).mean()   # slightly longer (~4 hours)

# 3. Detect crossovers
df['Signal'] = np.where(df['EMA21'] > df['EMA50'], 1, 0)
df['Position'] = df['Signal'].diff()

# ================== PLOT (only last 5 days) ==================
last_date = df.index.max()
plot_df = df[df.index >= last_date - pd.Timedelta(days=5)]

plt.figure(figsize=(15, 9))

# Price + EMAs
ax1 = plt.subplot2grid((4, 1), (0, 0), rowspan=3)
ax1.plot(plot_df['close'], label='Close Price', color='black', linewidth=1.1)
ax1.plot(plot_df['EMA21'], label='EMA 21 (short)', color='#FF9800', linewidth=2)
ax1.plot(plot_df['EMA50'], label='EMA 50 (slightly longer)', color='#2196F3', linewidth=2)

# Mark crossovers
golden = plot_df[plot_df['Position'] == 1]
death = plot_df[plot_df['Position'] == -1]
ax1.scatter(golden.index, golden['EMA21'], marker='^', color='green', s=120, label='Golden Cross (Bullish)', zorder=5)
ax1.scatter(death.index, death['EMA21'], marker='v', color='red', s=120, label='Death Cross (Bearish)', zorder=5)

ax1.set_title('AERO Token - 5m Chart with EMA21 & EMA50 Crossovers (Last 5 Days)')
ax1.set_ylabel('Price (USDT)')
ax1.grid(True, alpha=0.3)
ax1.legend()

# Volume
ax2 = plt.subplot2grid((4, 1), (3, 0), sharex=ax1)
ax2.bar(plot_df.index, plot_df['volume'], color='gray', alpha=0.7)
ax2.set_ylabel('Volume')
ax2.grid(True, alpha=0.3)

plt.tight_layout()

# ====================== EXPORT TO PNG ======================
filename = f"AERO_5day_EMA_chart_{datetime.now().strftime('%Y%m%d_%H%M')}.png"
plt.savefig(filename, dpi=150, bbox_inches='tight')
print(f"✅ Chart saved as: {filename}")

plt.show()

# ================== TODAY'S TREND ANALYSIS ==================
latest = df.iloc[-1]
print("\n=== TODAY'S TREND ANALYSIS (latest data) ===")
print(f"Latest Close Price : {latest['close']:.4f}")
print(f"EMA21              : {latest['EMA21']:.4f}")
print(f"EMA50              : {latest['EMA50']:.4f}")

if latest['EMA21'] > latest['EMA50']:
    trend = "UPTREND (Bullish)"
    strength = "Strong" if latest['close'] > latest['EMA21'] else "Moderate"
else:
    trend = "DOWNTREND (Bearish)"
    strength = "Strong" if latest['close'] < latest['EMA21'] else "Moderate"

print(f"Overall Trend      : **{trend}** - {strength}")

# Recent momentum
if len(df) > 48:
    change_4h = (latest['close'] - df.iloc[-49]['close']) / df.iloc[-49]['close'] * 100
    print(f"Last 4 hours change: {change_4h:+.2f}%")
if len(df) > 289:
    change_24h = (latest['close'] - df.iloc[-289]['close']) / df.iloc[-289]['close'] * 100
    print(f"Last 24 hours change: {change_24h:+.2f}%")
print("===============================================")
