import os
import pandas as pd
import matplotlib.pyplot as plt
from dune_client.client import DuneClient

# ============== INTERACTIVE KEY (no permanent save) ==============
DUNE_API_KEY = os.getenv("DUNE_API_KEY")
if not DUNE_API_KEY:
    DUNE_API_KEY = input("🔑 Paste your full Dune API key here: ").strip()
    if not DUNE_API_KEY:
        print("❌ No key entered. Exiting.")
        exit(1)

dune = DuneClient(api_key=DUNE_API_KEY)

# ============== YOUR QUERY (update if you want fresher data) ==============
QUERY_ID = 4010816   # ← Change this after checking the dashboard for newer ID

print(f"\n🔄 Fetching live data from Dune Query #{QUERY_ID}...")

df = dune.get_latest_result_dataframe(QUERY_ID)

print("\n✅ Columns found:", df.columns.tolist())

# ============== EXPLICIT COLUMNS FOR YOUR EXACT QUERY ==============
date_col = 'date_time'
platform_col = 'platform'
count_col = 'daily_token_count'

# Clean date (removes " UTC" if present)
df['date'] = pd.to_datetime(df[date_col].astype(str).str.replace(' UTC', ''), errors='coerce')
df = df.sort_values('date').dropna(subset=['date'])

print("\nLatest 5 rows preview (cleaned):")
print(df[['date', platform_col, count_col]].tail(5))

# 7-day moving average
df_ma = (
    df.set_index('date')
    .groupby(platform_col)[count_col]
    .rolling(window=7, min_periods=1)
    .mean()
    .reset_index()
)

# Latest 7d MA
latest_ma = df_ma[df_ma['date'] == df_ma['date'].max()]
print("\n" + "="*80)
print("7-DAY MOVING AVERAGE — DAILY MEMECOINS CREATED/DEPLOYED")
print("="*80)
print(latest_ma[[platform_col, count_col]].round(1).to_string(index=False))

# ============== PLOT ==============
plt.figure(figsize=(14, 7))
for platform in df_ma[platform_col].unique():
    subset = df_ma[df_ma[platform_col] == platform]
    plt.plot(subset['date'], subset[count_col], label=platform, linewidth=2.5)

plt.title("7-Day Moving Average — Daily Memecoins Deployed\n(Pumpdotfun / Moonshot / LetsBonk etc.)")
plt.ylabel("Avg Daily Creations")
plt.xlabel("Date")
plt.legend(title="Platform", bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
