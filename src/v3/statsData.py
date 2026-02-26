import ccxt
import pandas as pd
import pytz
from datetime import datetime, timedelta

# ================== CONFIGURATION ==================
symbol = 'ETH/USDT'      # ← Change to 'BTC/USDT' or your exact pair
timeframe = '15m'        # '15m' recommended (very precise), or '1h'
days_back = 730          # 2 full years → best statistical significance
# ===================================================

print(f"Fetching {days_back} days of {timeframe} {symbol} data... (this takes ~20-40 seconds)")

exchange = ccxt.binance({
    'enableRateLimit': True,
})

# Fetch data in chunks (Binance API limit is ~1000 candles per call)
since = int((datetime.now(pytz.utc) - timedelta(days=days_back)).timestamp() * 1000)
all_ohlcv = []

while True:
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
    if not ohlcv:
        break
    all_ohlcv.extend(ohlcv)
    since = ohlcv[-1][0] + 1
    if len(ohlcv) < 1000:
        break

df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True).dt.tz_convert('Asia/Seoul')
df = df.set_index('timestamp').sort_index()

# Filter ONLY your active 8am–8pm KST window
df_active = df.between_time('08:00', '20:00').copy()

print(f"Loaded {len(df_active):,} candles during 8am–8pm KST.\n")

# ===================== STATS FUNCTION =====================
def compute_window_stats(sub_df, label):
    print(f"=== {label} ===")
    for hours in [2, 3]:
        periods = int(hours * 60 / 15) if timeframe == '15m' else hours
        
        # Compute rolling on this sub-dataframe
        sub_df[f'{hours}h_return'] = sub_df['close'].pct_change(periods) * 100
        sub_df[f'{hours}h_range'] = (
            sub_df['high'].rolling(periods).max() -
            sub_df['low'].rolling(periods).min()
        ) / sub_df['close'].shift(periods) * 100
        
        print(f"\n{hours}h Rolling (8am–8pm KST):")
        stats = sub_df[[f'{hours}h_return', f'{hours}h_range']].describe(
            percentiles=[0.5, 0.75, 0.9, 0.95]
        )
        print(stats.round(3))
        
        # Per-bucket medians (exactly your 3-hour segments)
        print("  Per-bucket median range:")
        for s, e in [('08:00','11:00'), ('11:00','14:00'), ('14:00','17:00'), ('17:00','20:00')]:
            bucket = sub_df.between_time(s, e)
            print(f"    {s}-{e}: {bucket[f'{hours}h_range'].median():.3f}%")

# ===================== RUN STATS =====================
now = df_active.index.max()

compute_window_stats(df_active, "FULL 2 YEARS")
compute_window_stats(df_active[df_active.index > now - pd.Timedelta(days=365)], "LAST 1 YEAR")
compute_window_stats(df_active[df_active.index > now - pd.Timedelta(days=180)], "LAST 6 MONTHS")

# ===================== RANGE RECOMMENDATIONS =====================
print("\n" + "="*85)
print("🚀 UNISWAP V3 ACTIVE LP RANGE RECOMMENDATIONS (3-hour horizon)")
print("="*85)

def print_recs(label, range_series):
    p75 = range_series.quantile(0.75)
    p90 = range_series.quantile(0.90)
    balanced = round(p75 * 1.10, 1)   # slight buffer on 75th percentile
    safe     = round(p90 * 0.82, 1)
    agg      = round(p75 * 0.88, 1)
    
    print(f"\n{label}:")
    print(f"   Balanced     → ±{balanced}%   ← Recommended to start with")
    print(f"   Safe         → ±{safe}%      ← Very few rebalances")
    print(f"   Aggressive   → ±{agg}%      ← Max fee collection")

print("Overall (full 8am–8pm):")
print_recs("Full Day", df_active['3h_range'])

print("\nTime-of-Day Specific (recommended for you):")
for start, end, name in [
    ('08:00','11:00', '🌅 08:00 – 11:00'),
    ('11:00','14:00', '☀️ 11:00 – 14:00'),
    ('14:00','17:00', '🌤️ 14:00 – 17:00'),
    ('17:00','20:00', '🌆 17:00 – 20:00')
]:
    bucket = df_active.between_time(start, end)
    print_recs(name, bucket['3h_range'])

print("\n✅ Script finished! These recommendations are based 100% on your data.")
print("   Run this script weekly — it will auto-update as market regimes change.")
