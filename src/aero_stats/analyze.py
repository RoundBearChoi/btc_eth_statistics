import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import timedelta
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (16, 10)

# ====================== CONFIG ======================
CSV_FILE = 'aerodrome_0x22aee3699b6a0fed71490c103bd4e5f3309891d5_15min_max2.0y.csv'
ASSET = 'Aerodrome Token (USD)'

# Load & convert to KST (UTC+9)
df = pd.read_csv(CSV_FILE)
df['datetime_utc'] = pd.to_datetime(df['datetime'])
df['datetime_kst'] = df['datetime_utc'] + timedelta(hours=9)
df = df.set_index('datetime_kst').sort_index()

print(f"Loaded {len(df):,} 15min candles | {df.index[0]} → {df.index[-1]} KST")

# ====================== FIXED 3H BUCKETS (non-overlapping) ======================
df['date'] = df.index.date
df['hour_kst'] = df.index.hour
df['bucket_start'] = (df['hour_kst'] // 3) * 3

grouped = df.groupby(['date', 'bucket_start']).agg({
    'high_usd': 'max',
    'low_usd': 'min',
    'volume_usd': 'sum'
}).reset_index()

grouped['range_pct'] = (grouped['high_usd'] - grouped['low_usd']) / grouped['low_usd'] * 100
grouped['time_bucket'] = grouped['bucket_start'].apply(lambda x: f'{x:02d}-{(x+3):02d}')

bucket_stats = grouped.groupby('time_bucket')['range_pct'].agg([
    'count', 'median', 
    ('p75', lambda x: x.quantile(0.75)),
    ('p90', lambda x: x.quantile(0.90))
]).round(3).reset_index()

bucket_order = [f'{i:02d}-{(i+3):02d}' for i in range(0,24,3)]
bucket_stats = bucket_stats.set_index('time_bucket').reindex(bucket_order).reset_index()

print("\n=== 3h Range Stats by Time Bucket (KST) ===")
print(bucket_stats)
bucket_stats.to_csv('3h_range_stats_by_bucket.csv', index=False)

# ====================== ROLLING 3H (FIXED - THIS WAS THE ERROR) ======================
window = 12  # 3 hours = exactly 12 × 15min candles
df['rolling_high'] = df['high_usd'].rolling(window=window, min_periods=8).max()
df['rolling_low']  = df['low_usd'].rolling(window=window, min_periods=8).min()
df['rolling_range_pct'] = (df['rolling_high'] - df['rolling_low']) / df['rolling_low'] * 100

df['hour_kst'] = df.index.hour
hourly_trend = df.groupby('hour_kst')['rolling_range_pct'].agg(
    median='median',
    p75=lambda x: x.quantile(0.75),
    p90=lambda x: x.quantile(0.90)
).reindex(range(24))

# ====================== PLOTS ======================
fig, axes = plt.subplots(2, 2, figsize=(20, 16))

# 1. Bar + percentiles
ax = axes[0, 0]
x = np.arange(len(bucket_stats))
ax.bar(x - 0.2, bucket_stats['median'], 0.2, label='Median', color='tab:blue')
ax.bar(x, bucket_stats['p75'], 0.2, label='75th', color='tab:orange')
ax.bar(x + 0.2, bucket_stats['p90'], 0.2, label='90th', color='tab:red')
ax.set_xticks(x)
ax.set_xticklabels(bucket_stats['time_bucket'], rotation=45)
ax.set_ylabel('% 3h Range')
ax.set_title(f'3h Range by Time Bucket (KST) — {ASSET}')
ax.legend()
ax.grid(True, alpha=0.3)

# 2. Boxplot distribution
ax = axes[0, 1]
sns.boxplot(data=grouped, x='time_bucket', y='range_pct', ax=ax, order=bucket_order, showfliers=False)
ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
ax.set_title('Distribution by Time of Day')
ax.set_ylabel('% 3h Range')

# 3. Overall histogram
ax = axes[1, 0]
sns.histplot(grouped['range_pct'], bins=120, kde=True, color='skyblue', ax=ax)
ax.axvline(2.4, color='green', ls='--', lw=2, label='Balanced ±2.4%')
ax.axvline(2.6, color='red', ls='--', lw=2, label='Safe ±2.6%')
ax.axvline(1.9, color='purple', ls='--', lw=2, label='Aggressive ±1.9%')
ax.set_xlabel('% 3h Range')
ax.set_title('Overall 3h Range Distribution')
ax.legend()

# 4. Hourly rolling trend
ax = axes[1, 1]
ax.plot(hourly_trend.index, hourly_trend['median'], 'o-', label='Median', color='tab:blue', lw=2)
ax.plot(hourly_trend.index, hourly_trend['p75'], 's-', label='75th', color='tab:orange')
ax.plot(hourly_trend.index, hourly_trend['p90'], '^-', label='90th', color='tab:red')
ax.set_xticks(range(0,24))
ax.set_xlabel('Hour of Day (KST)')
ax.set_ylabel('% 3h Range')
ax.set_title('Hourly 3h Range Trend (rolling windows)')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('3h_range_analysis_full.png', dpi=300, bbox_inches='tight')
print("\n✅ Main analysis chart saved: 3h_range_analysis_full.png")

# ====================== VOLATILITY CLOCK ======================
fig = plt.figure(figsize=(10,10))
ax = fig.add_subplot(111, projection='polar')
vals = hourly_trend['median'].values
norm = plt.Normalize(vals.min(), vals.max())
cmap = plt.cm.RdYlGn_r

theta = np.linspace(0, 2*np.pi, 24, endpoint=False)
width = 2*np.pi / 24
ax.bar(theta, vals, width=width, color=cmap(norm(vals)), alpha=0.85)

ax.set_theta_zero_location('N')
ax.set_theta_direction(-1)
ax.set_xticks(theta)
ax.set_xticklabels([f'{h:02d}' for h in range(24)], fontsize=11)
ax.set_yticklabels([])
ax.set_title(f'24h Volatility Clock — Median 3h Range % (KST)\n{ASSET}', pad=30)
plt.savefig('volatility_clock.png', dpi=300, bbox_inches='tight')
print("✅ Volatility clock saved: volatility_clock.png")

print("\n🎉 All done! Open the two PNGs + 3h_range_stats_by_bucket.csv")
