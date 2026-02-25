import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
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
QUERY_ID = 4010816

print(f"\n🔄 Fetching live data from Dune Query #{QUERY_ID}...")

df = dune.get_latest_result_dataframe(QUERY_ID)

print("\n✅ Columns found:", df.columns.tolist())

# ============== EXPLICIT COLUMNS FOR YOUR EXACT QUERY ==============
date_col = 'date_time'
platform_col = 'platform'
count_col = 'daily_token_count'

# Clean date
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

# ============== PLOT & SAVE TO PNG (HD but small file) ==============
plt.figure(figsize=(16, 9))  # 16:9 → exactly 1920×1080 at dpi=120

for platform in df_ma[platform_col].unique():
    subset = df_ma[df_ma[platform_col] == platform]
    plt.plot(subset['date'], subset[count_col], label=platform, linewidth=2.5)

plt.title("7-Day Moving Average — Daily Memecoins Deployed\n(Pumpdotfun / Moonshot / LetsBonk etc.)",
          fontsize=16, pad=20)
plt.ylabel("Avg Daily Creations", fontsize=12)
plt.xlabel("Date", fontsize=12)
plt.legend(title="Platform", bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=11)
plt.grid(True, alpha=0.3)

plt.tight_layout()

# Save as PNG
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
output_file = f"memecoins_7dma_{timestamp}.png"

plt.savefig(output_file,
            dpi=120,              # → 1920×1080 (full HD)
            bbox_inches='tight',
            facecolor='white')

print(f"\n📊 Chart saved → {output_file}")
print(f"   Resolution: 1920×1080 px")
print(f"   File size: {os.path.getsize(output_file) / 1024:.1f} KB")

plt.close()   # frees memory, no window
print("✅ Done! Run again anytime for a fresh chart.")
