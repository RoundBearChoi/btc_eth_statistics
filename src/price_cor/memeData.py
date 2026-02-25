import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from dune_client.client import DuneClient

# ============== INTERACTIVE KEY ==============
DUNE_API_KEY = os.getenv("DUNE_API_KEY")
if not DUNE_API_KEY:
    DUNE_API_KEY = input("🔑 Paste your full Dune API key here: ").strip()
    if not DUNE_API_KEY:
        print("❌ No key entered. Exiting.")
        exit(1)

dune = DuneClient(api_key=DUNE_API_KEY)

# ============== QUERY ==============
QUERY_ID = 4010816

print(f"\n🔄 Fetching live data from Dune Query #{QUERY_ID}...")

df = dune.get_latest_result_dataframe(QUERY_ID)

date_col = 'date_time'
platform_col = 'platform'
count_col = 'daily_token_count'

df['date'] = pd.to_datetime(df[date_col].astype(str).str.replace(' UTC', ''), errors='coerce')
df = df.sort_values('date').dropna(subset=['date'])

print("\nLatest 5 rows preview:")
print(df[['date', platform_col, count_col]].tail(5))

# Pre-compute everything
df_ma = (
    df.set_index('date')
    .groupby(platform_col)[count_col]
    .rolling(window=7, min_periods=1)
    .mean()
    .reset_index()
)

df_total = df.groupby('date')[count_col].sum().reset_index(name='total_daily')
df_total['ma7'] = df_total['total_daily'].rolling(window=7, min_periods=1).mean()

df_pivot = df.pivot(index='date', columns=platform_col, values=count_col).fillna(0)
df_share = df_pivot.div(df_pivot.sum(axis=1), axis=0) * 100
df_pivot_cum = df_pivot.cumsum()

# ============== PRINT MARKET SHARE DATA ==============
print("\n" + "="*90)
print("               CURRENT MARKET SHARE")
print("="*90)

latest_date = df['date'].max().date()
print(f"📅 Data as of: {latest_date}\n")

# --- Last 7 Days ---
seven_days_ago = df['date'].max() - pd.Timedelta(days=6)
recent = df[df['date'] >= seven_days_ago].copy()

total_7d = recent[count_col].sum()
share_7d = (recent.groupby(platform_col)[count_col]
            .sum()
            .sort_values(ascending=False)
            .reset_index())

share_7d['share_%'] = (share_7d[count_col] / total_7d * 100).round(2)
share_7d = share_7d.rename(columns={count_col: 'launches'})

print(f"LAST 7 DAYS  ({seven_days_ago.date()} → {latest_date})")
print(f"Total memecoins launched: {total_7d:,}  →  avg {total_7d/7:,.0f}/day\n")
print(share_7d.to_string(index=False, 
                        columns=['platform', 'launches', 'share_%'],
                        header=['Platform', 'Launches', '% Share']))
print("-" * 90)

# --- Latest Day ---
latest_day = df[df['date'] == df['date'].max()]
total_day = latest_day[count_col].sum()
share_day = (latest_day.groupby(platform_col)[count_col]
             .sum()
             .sort_values(ascending=False)
             .reset_index())

share_day['share_%'] = (share_day[count_col] / total_day * 100).round(2)
share_day = share_day.rename(columns={count_col: 'launches'})

print(f"LATEST 24H ({latest_date})")
print(f"Total memecoins launched: {total_day:,}\n")
print(share_day.to_string(index=False, 
                         columns=['platform', 'launches', 'share_%'],
                         header=['Platform', 'Launches', '% Share']))

# ============== COMBINED DASHBOARD (2x2) ==============
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
today = datetime.now().strftime("%B %d, %Y")

fig, axs = plt.subplots(2, 2, figsize=(24, 16), dpi=120)

# Top-left: Per-platform 7DMA lines
for platform in df_ma[platform_col].unique():
    subset = df_ma[df_ma[platform_col] == platform]
    axs[0, 0].plot(subset['date'], subset[count_col], label=platform, linewidth=2.8)
axs[0, 0].set_title("7-Day MA — Daily Memecoins by Platform", fontsize=16, pad=15)
axs[0, 0].set_ylabel("Avg Daily Creations", fontsize=12)
axs[0, 0].legend(title="Platform", bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=10)
axs[0, 0].grid(True, alpha=0.3)

# Top-right: Total aggregate
axs[0, 1].plot(df_total['date'], df_total['ma7'], color='purple', linewidth=3.5, label='7-Day MA Total')
axs[0, 1].plot(df_total['date'], df_total['total_daily'], color='purple', alpha=0.25, label='Raw Daily Total')
axs[0, 1].set_title("Total Daily Memecoins Across All Platforms\n(7-Day Moving Average)", fontsize=16, pad=15)
axs[0, 1].set_ylabel("Avg Daily Creations", fontsize=12)
axs[0, 1].legend(fontsize=11)
axs[0, 1].grid(True, alpha=0.3)

# Bottom-left: Market share % — FIXED COLORS
order = ['Pumpdotfun'] + [col for col in df_share.columns if col != 'Pumpdotfun']
df_share = df_share[order]

# Full vibrant color palette (Pump orange at bottom)
colors = {
    'Pumpdotfun': '#FF6600',   # classic Pump orange
    'LetsBonk':   '#8E44FF',   # vibrant purple
    'Moonshot':   '#FF33CC',   # hot pink
    'Bags':       '#00CCFF',   # bright cyan
    'Boop':       '#33FF99',   # lime green
    'Believeapp': '#FF1493',   # deep pink
    'Jup Studio': '#FF4500',   # red-orange
    'Moon.it':    '#A0522D',   # sienna
    'Wavebreak':  '#FFD700'    # gold
}

color_list = [colors.get(col, '#555555') for col in df_share.columns]

df_share.plot.area(stacked=True, alpha=0.92, linewidth=0.6, ax=axs[1, 0], color=color_list)
axs[1, 0].set_title("Platform Market Share % — Daily Launches", fontsize=16, pad=15)
axs[1, 0].set_ylabel("Share of Total (%)", fontsize=12)
axs[1, 0].legend(title="Platform", bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=9.5)
axs[1, 0].grid(True, alpha=0.3)

# Bottom-right: Cumulative
df_pivot_cum.plot.area(stacked=True, alpha=0.85, linewidth=0.5, ax=axs[1, 1])
axs[1, 1].set_title("Cumulative Memecoins Created by Platform", fontsize=16, pad=15)
axs[1, 1].set_ylabel("Total Tokens Deployed", fontsize=12)
axs[1, 1].legend(title="Platform", bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=9.5)
axs[1, 1].grid(True, alpha=0.3)

fig.suptitle(f"Memecoin Launch Dashboard — {today}\nPump.fun • Moonshot • LetsBonk • etc.", 
             fontsize=22, fontweight='bold', y=0.98)

plt.tight_layout(rect=[0, 0, 1, 0.94])

output_file = f"memecoin_dashboard_{timestamp}.png"
plt.savefig(output_file, dpi=120, bbox_inches='tight', facecolor='white')
print(f"\n✅ DASHBOARD SAVED → {output_file}  (2880×1920 px)")
plt.close()

print("\n🚀 Now every platform has its own bright color — market share chart should look 🔥")
