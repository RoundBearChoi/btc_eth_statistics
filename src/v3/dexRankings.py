import requests
import pandas as pd
import matplotlib.pyplot as plt
import sys
from datetime import datetime

# ==================== CLI ARGUMENT ====================
if len(sys.argv) > 1:
    try:
        days = int(sys.argv[1])
        if days not in [1, 7, 30]:
            print("⚠️  Only 1, 7, or 30 supported. Defaulting to 7d")
            days = 7
    except ValueError:
        print("Usage: python dexRankings.py [1|7|30]")
        sys.exit(1)
else:
    days = 7

key_map = {
    1:  ("total24h", "24h"),
    7:  ("total7d",  "7d"),
    30: ("total30d", "30d")
}

vol_key, period = key_map[days]

print(f"Fetching current top DEXes by {period} volume...")

# ==================== FETCH ====================
url = "https://api.llama.fi/overview/dexs"
r = requests.get(url, timeout=20)
r.raise_for_status()
data = r.json()

df = pd.DataFrame(data.get("protocols", []))

# Nice display name
if "displayName" in df.columns:
    df["display_name"] = df["displayName"]
elif "name" in df.columns:
    df["display_name"] = df["name"]
else:
    df["display_name"] = df.index.astype(str)

# Smart column detection (in case DefiLlama changes keys again)
if vol_key not in df.columns:
    print(f"⚠️  {vol_key} not found, checking fallbacks...")
    fallback = f"volume{period}"
    if fallback in df.columns:
        vol_key = fallback
        print(f"   → using fallback {fallback}")
    else:
        vol_cols = [col for col in df.columns if any(x in col.lower() for x in ['total', 'volume'])]
        print(f"   Available volume columns: {vol_cols}")
        if vol_cols:
            vol_key = vol_cols[0]
            period = vol_key.replace('total', '').replace('volume', '')
            print(f"   → auto-selected {vol_key}")
        else:
            raise KeyError("No volume column found in DefiLlama response")

# Clean & rank (highest volume first)
df = df[df[vol_key] > 0].copy()
df["volume_b"] = df[vol_key] / 1_000_000_000
df = df.sort_values("volume_b", ascending=False).head(15).reset_index(drop=True)

# ==================== TABLE ====================
print(f"\n=== TOP 15 DEXes by {period} Trading Volume ===")
print(df[["display_name", "volume_b"]].round(3).to_string(index=False))

# ==================== CHART ====================
plt.figure(figsize=(11, 8))   # ← much smaller HD-friendly size

bars = plt.barh(df["display_name"], df["volume_b"],
                color='#3498db', edgecolor='black', alpha=0.85)

plt.xlabel(f"{period} Trading Volume (Billions USD)", fontsize=12)
plt.title(f"Top DEXes by {period} Volume — {datetime.now().strftime('%B %d, %Y')}",
          fontsize=14, fontweight='bold', pad=20)

plt.grid(axis='x', alpha=0.3)
plt.gca().invert_yaxis()          # ← This puts #1 at the top

# Value labels on bars
for bar in bars:
    width = bar.get_width()
    plt.text(width + 0.03, bar.get_y() + bar.get_height()/2,
             f'{width:.2f}B', va='center', fontsize=10.5, fontweight='medium')

plt.tight_layout()

filename = f"top_dexes_{period}.png"
plt.savefig(filename, dpi=250, bbox_inches='tight')  # sharp but much smaller file
plt.close()

print(f"\n✅ Chart saved → {filename}")
print("\nUsage:")
print("   python dexRankings.py        → 7-day (default)")
print("   python dexRankings.py 30     → 30-day")
print("   python dexRankings.py 1      → 24-hour")
