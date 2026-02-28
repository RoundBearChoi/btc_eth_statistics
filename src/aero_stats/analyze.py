import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import timedelta
import warnings
warnings.filterwarnings('ignore')

sns.set_style("darkgrid")
plt.rcParams['figure.figsize'] = (22, 15)
plt.rcParams['font.size'] = 13

# ====================== CONFIG ======================
CSV_FILE = 'aerodrome_0x22aee3699b6a0fed71490c103bd4e5f3309891d5_15min_max2.0y.csv'
ASSET = 'WETH-cbBTC Pool (USD)'

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

# ====================== ROLLING 3H ======================
window = 12
df['rolling_high'] = df['high_usd'].rolling(window=window, min_periods=8).max()
df['rolling_low']  = df['low_usd'].rolling(window=window, min_periods=8).min()
df['rolling_range_pct'] = (df['rolling_high'] - df['rolling_low']) / df['rolling_low'] * 100

hourly_trend = df.groupby('hour_kst')['rolling_range_pct'].agg(
    median='median', p75=lambda x: x.quantile(0.75), p90=lambda x: x.quantile(0.90)
).reindex(range(24))

# ====================== HOURLY RECOMMENDATIONS ======================
print("\n📊 Generating hourly recommendations...")

df['hour_start'] = df.index.floor('h')

hourly = df.groupby(['date', 'hour_start']).agg({
    'high_usd': 'max', 'low_usd': 'min'
}).reset_index()
hourly['range_pct'] = (hourly['high_usd'] - hourly['low_usd']) / hourly['low_usd'] * 100

hourly['hour_kst'] = hourly['hour_start'].dt.hour

stats_hourly = hourly.groupby('hour_kst')['range_pct'].agg([
    'count', 
    ('Median', 'median'), 
    ('P75', lambda x: x.quantile(0.75)), 
    ('P90', lambda x: x.quantile(0.90))
]).round(3).reindex(range(24)).reset_index()

stats_hourly['Bucket'] = stats_hourly['hour_kst'].apply(
    lambda x: f"{x:02d}:00 – {(x+1):02d}:00" if x < 23 else "23:00 – 00:00"
)

stats_hourly['Balanced']   = (stats_hourly['Median'] * 1.60).round(1)
stats_hourly['Safe']       = (stats_hourly['Median'] * 1.80).round(1)
stats_hourly['Aggressive'] = (stats_hourly['Median'] * 1.30).round(1)

stats_hourly = stats_hourly.rename(columns={'count': 'Samples'})

overall_median = hourly['range_pct'].median().round(3)
overall_p75 = hourly['range_pct'].quantile(0.75).round(3)
overall_p90 = hourly['range_pct'].quantile(0.90).round(3)

overall_row = pd.DataFrame([{
    'Bucket': 'Overall Full 24h',
    'Median': overall_median,
    'P75': overall_p75,
    'P90': overall_p90,
    'Balanced': (overall_median * 1.60).round(1),
    'Safe': (overall_median * 1.80).round(1),
    'Aggressive': (overall_median * 1.30).round(1),
    'Samples': len(hourly)
}])

final_df = pd.concat([
    overall_row,
    stats_hourly[['Bucket', 'Median', 'P75', 'P90', 'Balanced', 'Safe', 'Aggressive', 'Samples']]
], ignore_index=True)

final_df = final_df[['Bucket', 'Median', 'P75', 'P90', 'Balanced', 'Safe', 'Aggressive', 'Samples']]

final_df.to_csv('weth_cbbtc_hourly_recommendations.csv', index=False)

print("✅ Hourly CSV saved → weth_cbbtc_hourly_recommendations.csv")
print(final_df.to_string(index=False))

# ====================== BIG DASHBOARD PNG ======================
print("\n🎨 Generating full dashboard PNG...")

fig, axes = plt.subplots(2, 3, figsize=(22, 15))

# [ALL YOUR PLOTTING CODE BELOW STAYS 100% UNCHANGED]
cutoff = df.index.max() - pd.Timedelta(days=90)
recent_grouped = df[df.index >= cutoff].groupby(['date', 'bucket_start']).agg({
    'high_usd': 'max', 'low_usd': 'min'
}).reset_index()
recent_grouped['range_pct'] = (recent_grouped['high_usd'] - recent_grouped['low_usd']) / recent_grouped['low_usd'] * 100
recent_grouped['time_bucket'] = recent_grouped['bucket_start'].apply(lambda x: f'{x:02d}-{(x+3):02d}')
recent_stats = recent_grouped.groupby('time_bucket')['range_pct'].median().reindex(bucket_order)

ax = axes[0,0]
x = np.arange(len(bucket_stats))
ax.bar(x - 0.2, bucket_stats['median'], 0.2, label='Full History', color='#1f77b4')
ax.bar(x, recent_stats, 0.2, label='Last 90d', color='#ff7f0e')
ax.set_xticks(x)
ax.set_xticklabels(bucket_order, rotation=45)
ax.set_ylabel('% 3h Range')
ax.set_title('3h Range by Time Bucket (KST)')
ax.legend()

sns.boxplot(data=grouped, x='time_bucket', y='range_pct', ax=axes[0,1], order=bucket_order, showfliers=False)
axes[0,1].set_xticklabels(axes[0,1].get_xticklabels(), rotation=45)
axes[0,1].set_title('Full History Distribution')

sns.histplot(grouped['range_pct'], bins=150, kde=True, ax=axes[0,2], color='skyblue')
axes[0,2].axvline(2.4, color='lime', ls='--', lw=2, label='Balanced ±2.4%')
axes[0,2].axvline(1.9, color='purple', ls='--', lw=2, label='Aggressive ±1.9%')
axes[0,2].set_title('Overall 3h Range Distribution')
axes[0,2].legend()

ax = axes[1,0]
ax.plot(hourly_trend.index, hourly_trend['median'], 'o-', label='Median', color='#1f77b4', lw=3)
ax.plot(hourly_trend.index, hourly_trend['p90'], '^-', label='90th', color='#d62728')
ax.set_xticks(range(24))
ax.set_xlabel('Hour (KST)')
ax.set_title('Hourly 3h Range Trend (rolling)')
ax.legend()

df['dow'] = df.index.dayofweek
dow_hour = df.pivot_table(values='rolling_range_pct', index='dow', columns='hour_kst', aggfunc='median')
sns.heatmap(dow_hour, cmap='YlOrRd', annot=True, fmt='.2f', ax=axes[1,1])
axes[1,1].set_title('Median 3h Range by Day & Hour (KST)\n0=Mon … 6=Sun')
axes[1,1].set_xlabel('Hour (KST)')
axes[1,1].set_ylabel('Day of Week')

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

# ==================== OPTIMIZED SAVE ====================
plt.savefig('weth_cbbtc_3h_analysis_full.png', 
            dpi=180,
            bbox_inches='tight',
            pil_kwargs={'optimize': True, 'compress_level': 9})

print("✅ Big dashboard saved → weth_cbbtc_3h_analysis_full.png (~500 KB target)")

# ====================== REPORT ======================
with open('weth_cbbtc_volatility_report.txt', 'w') as f:
    f.write("WETH-cbBTC Pool Volatility Report (KST)\n")
    f.write("="*60 + "\n\n")
    f.write(f"Period: {df.index[0].date()} → {df.index[-1].date()}\n\n")
    f.write(f"Most volatile 3h bucket: {bucket_stats.loc[bucket_stats['median'].idxmax(), 'time_bucket']} "
            f"({bucket_stats['median'].max():.2f}%)\n")
    f.write(f"Calmest 3h bucket: {bucket_stats.loc[bucket_stats['median'].idxmin(), 'time_bucket']} "
            f"({bucket_stats['median'].min():.2f}%)\n\n")
    f.write(f"Hottest hour (1h): {stats_hourly.loc[stats_hourly['Median'].idxmax(), 'Bucket']}\n")
    f.write(f"Calmest hour (1h): {stats_hourly.loc[stats_hourly['Median'].idxmin(), 'Bucket']}\n")

print("\n🎉 ALL DONE! Now both files are perfect 🔥")
