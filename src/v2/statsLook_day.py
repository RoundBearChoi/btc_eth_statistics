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

# ====================== 3. MONTHLY BLOCK ANALYSIS ======================
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

# ====================== 5. BLOCK BOOTSTRAP - OVERALL MEAN ======================
print("\n" + "="*70)
print("=== BLOCK BOOTSTRAP ANALYSIS (preserves serial dependence) ===")
print("="*70)

changes_np = df['Ratio_Relative_Change'].values
n = len(changes_np)
print(f"Using {n:,} daily observations | Block size = 21 days (~3 weeks)")

np.random.seed(42)

def moving_block_bootstrap(series, block_size=21, n_boot=5000):
    n = len(series)
    boot_means = np.empty(n_boot)
    n_blocks = int(np.ceil(n / block_size))
    for i in range(n_boot):
        starts = np.random.randint(0, n - block_size + 1, size=n_blocks)
        sample = np.concatenate([series[s:s+block_size] for s in starts])[:n]
        boot_means[i] = sample.mean()
    return boot_means

boot_means = moving_block_bootstrap(changes_np)
mean_boot = boot_means.mean()
ci95_mean = np.percentile(boot_means, [2.5, 97.5])
p_boot = np.mean(np.abs(boot_means) >= np.abs(changes_np.mean())) * 2

print(f"\nOverall mean relative change")
print(f"   Original : {changes_np.mean():+.6f} ({changes_np.mean()*100:+.3f}%)")
print(f"   Bootstrap mean : {mean_boot:+.6f}")
print(f"   95% CI         : [{ci95_mean[0]:+.6f}, {ci95_mean[1]:+.6f}]")
print(f"   Bootstrapped p-value (mean=0) : {p_boot:.4f} → {'Significant' if p_boot <= 0.05 else 'Not significant'}")

# ====================== 6. DYNAMIC BALANCED RANGE (Interactive) ======================
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

abs_changes = np.abs(changes)
p = np.percentile(abs_changes, PERCENTILE)
balanced_range_pct = round(p * 100, 1)
coverage_pct = (abs_changes <= p).mean() * 100

print(f"\n💡 DYNAMIC BALANCED RANGE RECOMMENDATION ({PERCENTILE}th percentile)")
print(f"   ±{balanced_range_pct}% around the 10:00 KST ratio")
print(f"   Covers {coverage_pct:.1f}% of all {len(changes)} historical days")

# ====================== 7. BLOCK BOOTSTRAP FOR YOUR CHOSEN PERCENTILE ======================
print(f"\n🔬 Block-bootstrap 95% CI for your chosen {PERCENTILE}th percentile...")

abs_np = np.abs(changes_np)

def bootstrap_percentile(data, percentile, block_size=21, n_boot=3000):
    n = len(data)
    n_blocks = int(np.ceil(n / block_size))
    boot_pcts = np.empty(n_boot)
    for i in range(n_boot):
        starts = np.random.randint(0, n - block_size + 1, size=n_blocks)
        sample = np.concatenate([data[s:s+block_size] for s in starts])[:n]
        boot_pcts[i] = np.percentile(np.abs(sample), percentile)
    return boot_pcts

boot_p = bootstrap_percentile(abs_np, percentile=PERCENTILE, n_boot=3000)
ci95_p = np.percentile(boot_p, [2.5, 97.5])

print(f"   Original {PERCENTILE}th percentile : ±{p*100:.1f}%")
print(f"   Block-bootstrap 95% CI          : ±[{ci95_p[0]*100:.1f}%, {ci95_p[1]*100:.1f}%]")

# ====================== 8. VISUALS + SAVE PNG (final clean version) ======================
print("\n🎨 Saving final chart...")

plt.figure(figsize=(14, 14), dpi=120)

plt.subplot(3, 2, 1)
sns.histplot(changes*100, bins=80, kde=True, color='skyblue')
plt.axvline(0, color='red', linestyle='--')
plt.xlabel('Daily Change (%)')
plt.title('Distribution of Daily Ratio Relative Change')

plt.subplot(3, 2, 2)
(changes*100).plot(alpha=0.7, color='steelblue')
plt.axhline(0, color='red', linestyle='--', alpha=0.6)
plt.ylabel('Change (%)')
plt.title('Daily Ratio_Relative_Change (10:00 → 22:00 KST)')

plt.subplot(3, 2, 3)
monthly['mean'].plot(kind='bar', color='lightcoral')
plt.axhline(0, color='black', linestyle='--')
plt.title('Monthly Mean Relative Change')
plt.xticks(rotation=45)

plt.subplot(3, 2, 4)
rolling['mean'].plot(color='darkorange')
plt.axhline(0, color='red', linestyle='--')
plt.title('30-Day Rolling Mean (regime detector)')

# Bootstrap histogram (bottom left)
plt.subplot(3, 2, 5)
sns.histplot(boot_p * 100, bins=60, kde=True, color='mediumpurple')
plt.axvline(p*100, color='red', linestyle='--', linewidth=2.5, label=f'Original ({p*100:.1f}%)')
plt.axvline(ci95_p[0]*100, color='black', linestyle='--', linewidth=1.5, label='95% CI lower')
plt.axvline(ci95_p[1]*100, color='black', linestyle='--', linewidth=1.5, label='95% CI upper')
plt.xlabel(f'Bootstrapped {PERCENTILE}th Percentile of |Daily Change| (%)')
plt.title('Block-Bootstrap Distribution of Chosen Percentile')
plt.legend(fontsize=9, loc='upper right')

plt.tight_layout(rect=[0, 0.085, 1, 0.96])

# UPDATED BOTTOM TEXT BOX WITH CI VALUES
plt.figtext(0.5, 0.015,
            f"💡 DYNAMIC BALANCED RANGE for cbBTC-ETH pool (10am–10pm KST)\n"
            f"±{balanced_range_pct}% around the 10:00 KST ratio • Covers {coverage_pct:.1f}% of {len(changes)} historical days\n"
            f"Block-bootstrap 95% CI for {PERCENTILE}th percentile: [{ci95_p[0]*100:.1f}%, {ci95_p[1]*100:.1f}%]",
            ha='center', va='bottom', fontsize=11, fontweight='bold',
            bbox=dict(boxstyle="round,pad=1.0", facecolor="#E6F3FF", edgecolor="#1E88E5", linewidth=2))

png_filename = f"ratio_daily_analysis_{int(PERCENTILE)}.png"
plt.savefig(png_filename, 
            dpi=120, 
            bbox_inches='tight',
            pil_kwargs={'compression': 9, 'optimize': True})

plt.close()

print(f"\n📸 Chart saved → {png_filename}")
