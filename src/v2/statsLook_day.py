import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

# ====================== 1. LOAD & CLEAN DATA ======================
df = pd.read_csv('btc_eth_day_paired.csv')
df = df.iloc[:, [0, -1]].copy()
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
monthly_display['mean'] = monthly_display['mean'] * 100

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

# ====================== 5. DYNAMIC BALANCED RANGE (Interactive) ======================
print("\n" + "="*70)
print("💡 DYNAMIC BALANCED RANGE SETUP")
print("="*70)
print("Choose how wide you want the daily BTC/ETH ratio range:")
print("1) 95th percentile  → Wider / safer     (~±2.9%)")
print("2) 90th percentile  → Recommended balance (~±2.2%)")
print("3) 85th percentile  → Tighter           (~±1.8%)")
print("4) Custom percentile")

while True:
    choice = input("\nEnter 1-4 (or press Enter for default 90th): ").strip()
    
    if choice == "" or choice == "2":
        PERCENTILE = 90
        break
    elif choice == "1":
        PERCENTILE = 95
        break
    elif choice == "3":
        PERCENTILE = 85
        break
    elif choice == "4":
        try:
            custom = float(input("Enter custom percentile (e.g. 92 or 88): "))
            if 50 < custom < 100:
                PERCENTILE = custom
                break
            else:
                print("Please enter a number between 50 and 100.")
        except:
            print("Invalid → using default 90")
            PERCENTILE = 90
            break
    else:
        print("Please enter 1, 2, 3 or 4.")

print(f"✅ Using {PERCENTILE}th percentile")

# Calculation
abs_changes = np.abs(changes)
p = np.percentile(abs_changes, PERCENTILE)
balanced_range_pct = round(p * 100, 1)
coverage_pct = (abs_changes <= p).mean() * 100

print(f"\n💡 DYNAMIC BALANCED RANGE RECOMMENDATION ({PERCENTILE}th percentile)")
print(f"   ±{balanced_range_pct}% around the 10:00 KST ratio")
print(f"   Covers {coverage_pct:.1f}% of all {len(changes)} historical days")

# ====================== 6. VISUALS + SAVE AS PNG (COMPACT) ======================
print("\n🎨 Saving in Compact resolution (super small file size)...")

# Compact: 1680×1320 px — looks great on your monitor, maximum memory saver
plt.figure(figsize=(14, 11), dpi=120)

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

# Clean box text (removed the percentile update line)
plt.figtext(0.5, 0.04,
            f"💡 DYNAMIC BALANCED RANGE for cbBTC-ETH pool (10am–10pm KST)\n"
            f"±{balanced_range_pct}% around the 10:00 KST ratio\n"
            f"Covers {coverage_pct:.1f}% of all {len(changes)} historical days",
            ha='center', va='bottom', fontsize=12, fontweight='bold',
            bbox=dict(boxstyle="round,pad=1.2", facecolor="#E6F3FF", edgecolor="#1E88E5", linewidth=2),
            linespacing=1.6)

# Clean filename (no suffix)
png_filename = f"ratio_daily_analysis_{int(PERCENTILE)}.png"
plt.savefig(png_filename, 
            dpi=120, 
            bbox_inches='tight',
            pil_kwargs={'compression': 9, 'optimize': True})

plt.close()

print(f"\n📸 Chart saved → {png_filename}")
print("   (1680×1320 px — super compact, looks great on your monitor)")

print("\n🎯 Done! Run again anytime to choose a different percentile.")
