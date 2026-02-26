import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# ==================== CONFIG ====================
VOLUME_PERIOD = "7d"    # ← Change to "30d" for 1-month ranking
TOP_N = 15
# ===============================================

print(f"Fetching top DEXes by {VOLUME_PERIOD} volume...")

url = "https://api.llama.fi/overview/dexs"
r = requests.get(url)
r.raise_for_status()
data = r.json()

# Current DefiLlama API structure (Feb 2026)
df = pd.DataFrame(data.get("protocols", data))

# Robust volume column (new API uses total7d / total30d / total24h)
vol_map = {
    "7d":  "total7d",
    "30d": "total30d",
    "24h": "total24h"
}
vol_col = vol_map.get(VOLUME_PERIOD, "total7d")

if vol_col not in df.columns:
    print(f"⚠️  {vol_col} not found → checking available columns")
    print("Available columns:", list(df.columns))
    raise KeyError("Volume column missing – paste the printed columns so I can fix it")

name_col = "displayName" if "displayName" in df.columns else "name"

# Clean & rank
df = df.copy()
df["volume_b"] = pd.to_numeric(df[vol_col], errors="coerce") / 1_000_000_000
df = df.dropna(subset=["volume_b"])
df = df[df["volume_b"] > 0.01]                     # remove noise
df = df.sort_values("volume_b", ascending=False).head(TOP_N).reset_index(drop=True)

df["display_name"] = df[name_col]

print(f"\n=== TOP {TOP_N} DEXes by {VOLUME_PERIOD.upper()} VOLUME ===")
print(df[["display_name", "volume_b"]].round(3).to_string(index=False))

# ==================== MATPLOTLIB CHART ====================
plt.figure(figsize=(13, 9))
bars = plt.barh(df["display_name"][::-1], df["volume_b"][::-1], color="#2E86AB")

plt.title(f"Top {TOP_N} DEXes by {VOLUME_PERIOD.upper()} Trading Volume\n({datetime.now().strftime('%B %d, %Y')})",
          fontsize=16, pad=25, fontweight="bold")
plt.xlabel("Volume (Billions USD)", fontsize=13)
plt.grid(axis="x", alpha=0.3)

# Value labels on bars
for bar in bars:
    width = bar.get_width()
    plt.text(width + 0.08, bar.get_y() + bar.get_height()/2,
             f"${width:.2f}B", va="center", fontsize=11, fontweight="medium")

plt.tight_layout()
filename = f"top_dexes_{VOLUME_PERIOD}.png"
plt.savefig(filename, dpi=220, bbox_inches="tight")
print(f"\n✅ Chart saved as → {filename}")

plt.show()   # opens in a window (Matplotlib)
