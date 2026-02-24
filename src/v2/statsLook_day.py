import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

# ====================== 1. LOAD & CLEAN DATA ======================
df = pd.read_csv('btc_eth_day_paired.csv')
df = df.iloc[:, [0, -1]].copy()                     # first + last column (robust)
df.columns = ['KST_Datetime', 'Ratio_Relative_Change']

df['Date'] = pd.to_datetime(
    df['KST_Datetime'].str.replace(' KST', ''), 
    errors='coerce'
)

df['Ratio_Relative_Change'] = pd.to_numeric(
    df['Ratio_Relative_Change'], 
    errors='coerce'
)

df = df.dropna().set_index('Date')

print(f"✅ Loaded {len(df):,} daily observations")
print(f"Period     : {df.index.min().date()} → {df.index.max().date()}\n")

changes = df['Ratio_Relative_Change']

# ====================== 2. OVERALL STATISTICS ======================
print("=== OVERALL STATISTICS ===")
print("-" * 45)
print(f"Mean               : {changes.mean():.6f}  ({changes.mean()*100:6.3f}%)")
print(f"Median             : {changes.median():.6f}")
print(f"Std Dev            : {changes.std():.6f}  (~{changes.std()*100:.2f}%)")
print(f"Positive days      : {(changes > 0).mean()*100:.2f}%  ({(changes > 0).sum()}/{len(changes)})")

t_stat, p_value = stats.ttest_1samp(changes, 0)
print(f"\nT-test p-value (mean == 0) : {p_value:.4f} → {'Not significant' if p_value > 0.05 else 'Significant'}")

# ====================== 3. MONTHLY BLOCK METHOD ======================
print("\n=== MONTHLY BLOCK ANALYSIS (brutally effective) ===")
print("-" * 60)

monthly = df['Ratio_Relative_Change'].resample('ME').agg({
    'count': 'count',
    'mean': 'mean',
    'std': 'std',
    'positive_pct': lambda x: (x > 0).mean() * 100
})

monthly_display = monthly[['mean', 'positive_pct', 'count']].copy()
monthly_display['mean'] = monthly_display['mean'] * 100   # show as %

print(monthly_display.round(4))
monthly_display.to_csv('ratio_monthly_blocks.csv')
print(f"\n📁 Monthly blocks saved → ratio_monthly_blocks.csv")

# ====================== 4. ROLLING 30-DAY BLOCKS ======================
print("\n=== ROLLING 30-DAY BLOCKS (last 10 shown) ===")
rolling = df['Ratio_Relative_Change'].rolling(window=30, min_periods=15).agg({
    'mean': 'mean',
    'positive_pct': lambda x: (x > 0).mean() * 100
})

print(rolling.tail(10).round(4))

# ====================== 5. DYNAMIC BALANCED RANGE (derived from YOUR data) ======================
# This is fully automatic — no hard-coded number
# We take the 95th percentile of absolute changes → exactly the range that has historically kept you in-range 95% of the time
abs_changes = np.abs(changes)
p95 = np.percentile(abs_changes, 95)          # this is the key line
balanced_range_pct = round(p95 * 100, 1)      # e.g. 2.7 or 2.8 — updates every time you add new rows

coverage_pct = (abs_changes <= p95).mean() * 100   # will always be ~95%

print(f"\n💡 DYNAMIC BALANCED RANGE RECOMMENDATION (derived from data)")
print(f"   ±{balanced_range_pct}% around the 10:00 KST ratio")
print(f"   Covers {coverage_pct:.1f}% of all {len(changes)} historical days")
print(f"   (95th percentile of |daily moves| — automatically updates as you add new data)")

# ====================== 6. VISUALS + SAVE AS PNG (with dynamic recommendation) ======================
plt.figure(figsize=(14, 11))   # slightly taller for the box

plt.subplot(2, 2, 1)
sns.histplot(changes*100, bins=80, kde=True, color='skyblue')
plt.axvline(0, color='red', linestyle='--')
plt.xlabel('Daily Change (%)')
plt.title('Distribution of Daily Ratio Relative Change')

plt.subplot(2, 2, 2)
(changes*100).plot(alpha=0.7, color='steelblue')
plt.axhline(0, color='red', linestyle='--', alpha=0.6)
plt.ylabel('Change (%)')
plt.title('Daily Ratio_Relative_Change (10:00 → 22:00 KST)')

plt.subplot(2, 2, 3)
monthly['mean'].plot(kind='bar', color='lightcoral')
plt.axhline(0, color='black', linestyle='--')
plt.title('Monthly Mean Relative Change')
plt.xticks(rotation=45)

plt.subplot(2, 2, 4)
rolling['mean'].plot(color='darkorange')
plt.axhline(0, color='red', linestyle='--')
plt.title('30-Day Rolling Mean (regime detector)')

plt.tight_layout(rect=[0, 0.08, 1, 0.95])

# === DYNAMIC RECOMMENDATION BOX ON THE PNG ===
plt.figtext(0.5, 0.04,
            f"💡 DYNAMIC BALANCED RANGE for cbBTC-ETH pool (10am–10pm KST)\n"
            f"±{balanced_range_pct}% around the 10:00 KST ratio\n"
            f"Covers {coverage_pct:.1f}% of all {len(changes)} historical days\n"
            f"(95th percentile — updates automatically when you add new data)",
            ha='center', va='bottom', fontsize=13, fontweight='bold',
            bbox=dict(boxstyle="round,pad=1.2", facecolor="#E6F3FF", edgecolor="#1E88E5", linewidth=2),
            linespacing=1.6)

# SAVE AS HIGH-QUALITY PNG
plt.savefig('ratio_daily_analysis.png', dpi=300, bbox_inches='tight')
print(f"\n📸 Chart saved as ratio_daily_analysis.png (300 DPI — dynamic range included!)")

plt.show()

print("\n🎯 Done! The recommended range is now 100% derived from your data.")
print("   Add new rows to the CSV → run the script again → range updates automatically.")
