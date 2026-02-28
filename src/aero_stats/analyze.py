import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import timedelta
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

sns.set_style("darkgrid")
plt.rcParams['figure.figsize'] = (18, 12)
plt.rcParams['font.size'] = 12

# ====================== CONFIG ======================
CSV_FILE = 'aerodrome_0x22aee3699b6a0fed71490c103bd4e5f3309891d5_15min_max2.0y.csv'
ASSET = 'Aerodrome Token (USD)'

df = pd.read_csv(CSV_FILE)
df['datetime_utc'] = pd.to_datetime(df['datetime'])
df['datetime_kst'] = df['datetime_utc'] + timedelta(hours=9)
df = df.set_index('datetime_kst').sort_index()

print(f"✅ Loaded {len(df):,} candles | {df.index[0].date()} → {df.index[-1].date()} KST")

# ====================== 3H BUCKETS ======================
df['date'] = df.index.date
df['hour_kst'] = df.index.hour
df['bucket_start'] = (df['hour_kst'] // 3) * 3

grouped = df.groupby(['date', 'bucket_start']).agg({
    'high_usd': 'max', 'low_usd': 'min'
}).reset_index()
grouped['range_pct'] = (grouped['high_usd'] - grouped['low_usd']) / grouped['low_usd'] * 100
grouped['time_bucket'] = grouped['bucket_start'].apply(lambda x: f'{x:02d}-{(x+3):02d}')

bucket_order = [f'{i:02d}-{(i+3):02d}' for i in range(0,24,3)]
bucket_stats = grouped.groupby('time_bucket')['range_pct'].agg([
    'count', 'median', ('p75', lambda x: x.quantile(0.75)), ('p90', lambda x: x.quantile(0.90))
]).round(3).reindex(bucket_order).reset_index()

print("\n=== 3h Range Stats by Time Bucket (KST) ===")
print(bucket_stats)

# ====================== ROLLING 3H ======================
window = 12
df['rolling_high'] = df['high_usd'].rolling(window=window, min_periods=8).max()
df['rolling_low']  = df['low_usd'].rolling(window=window, min_periods=8).min()
df['rolling_range_pct'] = (df['rolling_high'] - df['rolling_low']) / df['rolling_low'] * 100

hourly_trend = df.groupby('hour_kst')['rolling_range_pct'].agg(
    median='median', p75=lambda x: x.quantile(0.75), p90=lambda x: x.quantile(0.90)
).reindex(range(24))

# ====================== LAST 90 DAYS ======================
cutoff = df.index.max() - pd.Timedelta(days=90)
recent = df[df.index >= cutoff]
print(f"\n📅 Last 90 days: {len(recent):,} candles")

recent_grouped = recent.groupby(['date', 'bucket_start']).agg({
    'high_usd': 'max', 'low_usd': 'min'
}).reset_index()
recent_grouped['range_pct'] = (recent_grouped['high_usd'] - recent_grouped['low_usd']) / recent_grouped['low_usd'] * 100
recent_grouped['time_bucket'] = recent_grouped['bucket_start'].apply(lambda x: f'{x:02d}-{(x+3):02d}')

recent_stats = recent_grouped.groupby('time_bucket')['range_pct'].median().round(3).reindex(bucket_order)

# ====================== PLOTS ======================
fig, axes = plt.subplots(2, 3, figsize=(22, 14))

# 1. Bar chart
ax = axes[0,0]
x = np.arange(len(bucket_stats))
ax.bar(x - 0.2, bucket_stats['median'], 0.2, label='Full History', color='#1f77b4')
ax.bar(x, recent_stats, 0.2, label='Last 90d', color='#ff7f0e')
ax.set_xticks(x)
ax.set_xticklabels(bucket_stats['time_bucket'], rotation=45)
ax.set_ylabel('% 3h Range')
ax.set_title('3h Range by Time Bucket (KST)')
ax.legend()

# 2. Boxplot
sns.boxplot(data=grouped, x='time_bucket', y='range_pct', ax=axes[0,1], order=bucket_order, showfliers=False)
axes[0,1].set_xticklabels(axes[0,1].get_xticklabels(), rotation=45)
axes[0,1].set_title('Full History Distribution')

# 3. Overall histogram
sns.histplot(grouped['range_pct'], bins=150, kde=True, ax=axes[0,2], color='skyblue')
axes[0,2].axvline(2.4, color='lime', ls='--', lw=2, label='Balanced ±2.4%')
axes[0,2].axvline(1.9, color='purple', ls='--', lw=2, label='Aggressive ±1.9%')
axes[0,2].set_title('Overall 3h Range Distribution')
axes[0,2].legend()

# 4. Rolling trend
ax = axes[1,0]
ax.plot(hourly_trend.index, hourly_trend['median'], 'o-', label='Median', color='#1f77b4', lw=3)
ax.plot(hourly_trend.index, hourly_trend['p90'], '^-', label='90th', color='#d62728')
ax.set_xticks(range(24))
ax.set_xlabel('Hour (KST)')
ax.set_title('Hourly 3h Range Trend (rolling)')
ax.legend()

# 5. Day-of-week heatmap
df['dow'] = df.index.dayofweek
dow_hour = df.pivot_table(values='rolling_range_pct', index='dow', columns='hour_kst', aggfunc='median')
sns.heatmap(dow_hour, cmap='YlOrRd', annot=True, fmt='.2f', ax=axes[1,1])
axes[1,1].set_title('Median 3h Range by Day & Hour (KST)\n0=Mon … 6=Sun')
axes[1,1].set_xlabel('Hour (KST)')
axes[1,1].set_ylabel('Day of Week')

# 6. Volatility clock
ax = fig.add_subplot(2, 3, 6, projection='polar')
vals = hourly_trend['median'].values
norm = plt.Normalize(vals.min(), vals.max())
theta = np.linspace(0, 2*np.pi, 24, endpoint=False)
ax.bar(theta, vals, width=2*np.pi/24, color=plt.cm.RdYlGn_r(norm(vals)), alpha=0.9)
ax.set_theta_zero_location('N')
ax.set_theta_direction(-1)
ax.set_xticks(theta)
ax.set_xticklabels([f'{h:02d}' for h in range(24)])
ax.set_title('24h Volatility Clock (KST)')

plt.tight_layout()
plt.savefig('aerodrome_3h_analysis_v2.png', dpi=300, bbox_inches='tight')
print("✅ Full dashboard saved: aerodrome_3h_analysis_v2.png")

# ====================== REPORT ======================
with open('aerodrome_volatility_report.txt', 'w') as f:
    f.write("Aerodrome Token Volatility Report (KST)\n")
    f.write("="*50 + "\n\n")
    f.write(f"Period: {df.index[0].date()} → {df.index[-1].date()}\n")
    f.write(f"Most volatile 3h bucket: {bucket_stats.loc[bucket_stats['median'].idxmax(), 'time_bucket']} "
            f"({bucket_stats['median'].max():.2f}% median)\n")
    f.write(f"Calmest 3h bucket: {bucket_stats.loc[bucket_stats['median'].idxmin(), 'time_bucket']} "
            f"({bucket_stats['median'].min():.2f}% median)\n\n")
    f.write("Last 90 days top bucket: " + recent_stats.idxmax() + f" ({recent_stats.max():.2f}%)\n")

print("\n📊 KEY INSIGHTS:")
print(f"   🔥 Hottest window: {bucket_stats.loc[bucket_stats['median'].idxmax(), 'time_bucket']} KST")
print(f"   🧊 Calmest window: {bucket_stats.loc[bucket_stats['median'].idxmin(), 'time_bucket']} KST")
print(f"   Last 90d hottest: {recent_stats.idxmax()} KST")
print("\n📁 Files created:")
print("   • aerodrome_3h_analysis_v2.png")
print("   • aerodrome_volatility_report.txt")
print("   • 3h_range_stats_by_bucket.csv (already saved earlier)")

print("\n🎉 Done! Open the big PNG and the report.txt — let me know what you want next 🔥")
