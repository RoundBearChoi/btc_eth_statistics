import ccxt
import pandas as pd
import pytz
import os
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

class UniswapV3StatsAnalyzer:
    """
    Now with 4 charts: 5-bucket bar + boxplot + overall histogram + NEW hourly trend line.
    7am–10pm KST + hourly recommendations (clean output).
    """

    def __init__(self, symbol: str = 'ETH/USDT', timeframe: str = '15m', days_back: int = 730):
        self.symbol = symbol
        self.timeframe = timeframe
        self.days_back = days_back
        self.full_df = None
        self.df_active = None
        self.exchange = None

    def fetch_data(self):
        print(f"Fetching {self.days_back} days of {self.timeframe} {self.symbol} data... (~20-40s)")

        self.exchange = ccxt.binance({'enableRateLimit': True})

        since = int((datetime.now(pytz.utc) - timedelta(days=self.days_back)).timestamp() * 1000)
        all_ohlcv = []

        while True:
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, self.timeframe, since=since, limit=1000)
            if not ohlcv:
                break
            all_ohlcv.extend(ohlcv)
            since = ohlcv[-1][0] + 1
            if len(ohlcv) < 1000:
                break

        df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True).dt.tz_convert('Asia/Seoul')
        df = df.set_index('timestamp').sort_index()

        self.full_df = df.copy()
        self.df_active = df.between_time('07:00', '22:00').copy()

        print(f"Loaded {len(self.df_active):,} candles (7am–10pm KST).")

        os.makedirs('raw_data', exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = self.symbol.replace('/', '_')
        self.full_df.to_csv(f"raw_data/{base}_{self.timeframe}_full_kst_{ts}.csv")
        self.df_active.to_csv(f"raw_data/{base}_{self.timeframe}_active_7am10pm_kst_{ts}.csv")
        print(f"✅ Raw data saved to raw_data/\n")

    def compute_window_stats(self, sub_df: pd.DataFrame, label: str):
        print(f"=== {label} ===")
        for hours in [2, 3]:
            periods = int(hours * 60 / 15) if self.timeframe == '15m' else hours
            sub_df[f'{hours}h_return'] = sub_df['close'].pct_change(periods) * 100
            sub_df[f'{hours}h_range'] = (
                sub_df['high'].rolling(periods).max() -
                sub_df['low'].rolling(periods).min()
            ) / sub_df['close'].shift(periods) * 100

            print(f"\n{hours}h Rolling:")
            stats = sub_df[[f'{hours}h_return', f'{hours}h_range']].describe(
                percentiles=[0.5, 0.75, 0.9, 0.95]
            )
            print(stats.round(3))

            print("  Per-bucket median range:")
            for s, e in [('07:00','10:00'), ('10:00','13:00'), ('13:00','16:00'), ('16:00','19:00'), ('19:00','22:00')]:
                bucket = sub_df.between_time(s, e)
                print(f"    {s}-{e}: {bucket[f'{hours}h_range'].median():.3f}%")
        print("")

    def generate_charts(self):
        if self.df_active is None or '3h_range' not in self.df_active.columns:
            return

        os.makedirs('charts', exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = self.symbol.replace('/', '_')
        sns.set_style("darkgrid")

        # --- 5-bucket charts (kept exactly as before — clean & beautiful) ---
        buckets = []
        bucket_names = ['07-10', '10-13', '13-16', '16-19', '19-22']
        for s, e in [('07:00','10:00'), ('10:00','13:00'), ('13:00','16:00'), ('16:00','19:00'), ('19:00','22:00')]:
            b = self.df_active.between_time(s, e)['3h_range'].dropna()
            buckets.append(b)
        bucket_df = pd.DataFrame(dict(zip(bucket_names, buckets)))

        # Chart 1: Bar + percentiles (5 buckets)
        plt.figure(figsize=(11, 6))
        medians = [b.median() for b in buckets]
        p75 = [b.quantile(0.75) for b in buckets]
        p90 = [b.quantile(0.90) for b in buckets]
        x = range(5)
        plt.bar(x, medians, color='#1f77b4', alpha=0.8, label='Median 3h range')
        plt.errorbar(x, medians, yerr=[[0]*5, [p75[i]-medians[i] for i in x]], fmt='none', ecolor='orange', capsize=6, label='75th')
        plt.errorbar(x, medians, yerr=[[0]*5, [p90[i]-medians[i] for i in x]], fmt='none', ecolor='red', capsize=6, label='90th')
        plt.xticks(x, bucket_names)
        plt.ylabel('% Range')
        plt.title(f'{self.symbol} 3h Range by Time Bucket (7am–10pm KST)')
        plt.legend()
        plt.tight_layout()
        plt.savefig(f"charts/{base}_bar_ranges_{ts}.png", dpi=200)
        plt.close()

        # Chart 2: Box plot (5 buckets)
        plt.figure(figsize=(11, 6))
        sns.boxplot(data=bucket_df, palette="Blues")
        plt.ylabel('% 3h Range')
        plt.title(f'{self.symbol} 3h Range Distribution by Time of Day (7am–10pm KST)')
        plt.xlabel('Time Bucket (KST)')
        plt.tight_layout()
        plt.savefig(f"charts/{base}_boxplot_{ts}.png", dpi=200)
        plt.close()

        # Chart 3: Overall Histogram
        plt.figure(figsize=(10, 6))
        sns.histplot(self.df_active['3h_range'], bins=80, kde=True, color='#1f77b4')
        balanced = round(self.df_active['3h_range'].quantile(0.75) * 1.10, 1)
        safe = round(self.df_active['3h_range'].quantile(0.90) * 0.82, 1)
        agg = round(self.df_active['3h_range'].quantile(0.75) * 0.88, 1)
        plt.axvline(balanced, color='green', linestyle='--', linewidth=2.5, label=f'Balanced ±{balanced}%')
        plt.axvline(safe, color='red', linestyle='--', linewidth=2.5, label=f'Safe ±{safe}%')
        plt.axvline(agg, color='purple', linestyle='--', linewidth=2.5, label=f'Aggressive ±{agg}%')
        plt.xlabel('% 3h Range')
        plt.title(f'{self.symbol} Overall 3h Range Distribution (7am–10pm KST, Full 2 Years)')
        plt.legend()
        plt.tight_layout()
        plt.savefig(f"charts/{base}_histogram_{ts}.png", dpi=200)
        plt.close()

        # === NEW Chart 4: Hourly Trend Line ===
        plt.figure(figsize=(15, 6.5))
        hourly_medians = []
        hourly_p75 = []
        hourly_p90 = []
        hour_labels = []
        for h in range(7, 22):
            start = f"{h:02d}:00"
            end = f"{h+1:02d}:00"
            bucket = self.df_active.between_time(start, end)['3h_range'].dropna()
            hourly_medians.append(bucket.median())
            hourly_p75.append(bucket.quantile(0.75))
            hourly_p90.append(bucket.quantile(0.90))
            hour_labels.append(f"{h:02d}-{h+1:02d}")

        x = range(len(hour_labels))
        plt.plot(x, hourly_medians, marker='o', linewidth=3.5, color='#1f77b4', label='Median 3h range')
        plt.plot(x, hourly_p75, marker='s', linestyle='--', linewidth=2.2, color='orange', label='75th percentile')
        plt.plot(x, hourly_p90, marker='^', linestyle='--', linewidth=2.2, color='red', label='90th percentile')
        plt.xticks(x, hour_labels, rotation=45, ha='right')
        plt.ylabel('% 3h Range')
        plt.title(f'{self.symbol} Hourly 3h Range Trend (7am–10pm KST)')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.savefig(f"charts/{base}_hourly_trend_{ts}.png", dpi=200)
        plt.close()

        print("✅ 4 Charts saved to charts/ folder (now includes beautiful hourly trend!)\n")

    def print_range_recommendations(self):
        print("\n" + "="*85)
        print("🚀 UNISWAP V3 ACTIVE LP RANGE RECOMMENDATIONS (3-hour horizon)")
        print("                 7:00 AM – 10:00 PM KST")
        print("="*85)

        def print_recs(label, range_series):
            series = range_series.dropna()
            if len(series) < 100:
                print(f"\n{label}: Not enough data")
                return
            p75 = series.quantile(0.75)
            p90 = series.quantile(0.90)
            balanced = round(p75 * 1.10, 1)
            safe     = round(p90 * 0.82, 1)
            agg      = round(p75 * 0.88, 1)
            print(f"\n{label}:")
            print(f"   Balanced     → ±{balanced}%")
            print(f"   Safe         → ±{safe}%")
            print(f"   Aggressive   → ±{agg}%")

        print("Overall (full 7am–10pm):")
        print_recs("Full Active Window", self.df_active['3h_range'])

        print("\n" + "-"*70)
        print("🕒 HOURLY RECOMMENDATIONS (3h range ending in this hour)")
        print("-"*70)
        for h in range(7, 22):
            start = f"{h:02d}:00"
            end   = f"{h + 1:02d}:00"
            name  = f"🕒 {start} – {end}"
            bucket = self.df_active.between_time(start, end)
            print_recs(name, bucket['3h_range'])

        print("\n✅ Done! Run weekly for fresh numbers & charts.")

    def run(self):
        self.fetch_data()
        if self.df_active is None or len(self.df_active) == 0:
            print("Error: No data.")
            return

        now = self.df_active.index.max()
        self.compute_window_stats(self.df_active, "FULL 2 YEARS")
        self.compute_window_stats(self.df_active[self.df_active.index > now - pd.Timedelta(days=365)], "LAST 1 YEAR")
        self.compute_window_stats(self.df_active[self.df_active.index > now - pd.Timedelta(days=180)], "LAST 6 MONTHS")

        self.generate_charts()
        self.print_range_recommendations()


# ====================== RUN ======================
if __name__ == "__main__":
    analyzer = UniswapV3StatsAnalyzer(
        symbol='ETH/USDT',   # ← change to 'BTC/USDT' anytime
        timeframe='15m',
        days_back=730
    )
    analyzer.run()
