import ccxt
import pandas as pd
import pytz
import os
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

class UniswapV3StatsAnalyzer:
    """
    Full 24h KST analysis in ONE clean combined chart (2x2).
    Title no longer overlaps + hourly recommendations exported to CSV.
    """

    def __init__(self, symbol: str = 'ETH/USDT', timeframe: str = '15m', days_back: int = 730, chart_dpi: int = 165):
        self.symbol = symbol
        self.timeframe = timeframe
        self.days_back = days_back
        self.chart_dpi = chart_dpi
        self.full_df = None
        self.df_24h = None
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
        self.df_24h = df.copy()

        print(f"Loaded {len(self.df_24h):,} candles (Full 24h KST).")

        os.makedirs('raw_data', exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = self.symbol.replace('/', '_')
        self.full_df.to_csv(f"raw_data/{base}_{self.timeframe}_full_kst_{ts}.csv")
        self.df_24h.to_csv(f"raw_data/{base}_{self.timeframe}_24h_kst_{ts}.csv")
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
            for s, e in [('00:00','03:00'), ('03:00','06:00'), ('06:00','09:00'), ('09:00','12:00'),
                        ('12:00','15:00'), ('15:00','18:00'), ('18:00','21:00'), ('21:00','00:00')]:
                bucket = sub_df.between_time(s, e)
                print(f"    {s}-{e if e != '00:00' else '24:00'}: {bucket[f'{hours}h_range'].median():.3f}%")
        print("")

    def generate_charts(self):
        if self.df_24h is None or '3h_range' not in self.df_24h.columns:
            return

        os.makedirs('charts', exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = self.symbol.replace('/', '_')
        sns.set_style("darkgrid")

        bucket_intervals = [
            ('00:00','03:00'), ('03:00','06:00'), ('06:00','09:00'), ('09:00','12:00'),
            ('12:00','15:00'), ('15:00','18:00'), ('18:00','21:00'), ('21:00','00:00')
        ]
        bucket_names = ['00-03', '03-06', '06-09', '09-12', '12-15', '15-18', '18-21', '21-24']

        buckets = [self.df_24h.between_time(s, e)['3h_range'].dropna() for s, e in bucket_intervals]
        bucket_df = pd.DataFrame(dict(zip(bucket_names, buckets)))

        # === ONE COMBINED CHART (2x2) ===
        fig, axs = plt.subplots(2, 2, figsize=(22, 16), constrained_layout=False)

        # Top-left: Bar
        medians = [b.median() for b in buckets]
        p75 = [b.quantile(0.75) for b in buckets]
        p90 = [b.quantile(0.90) for b in buckets]
        x = range(8)
        axs[0, 0].bar(x, medians, color='#1f77b4', alpha=0.8, label='Median 3h range')
        axs[0, 0].errorbar(x, medians, yerr=[[0]*8, [p75[i]-medians[i] for i in x]], fmt='none', ecolor='orange', capsize=6, label='75th')
        axs[0, 0].errorbar(x, medians, yerr=[[0]*8, [p90[i]-medians[i] for i in x]], fmt='none', ecolor='red', capsize=6, label='90th')
        axs[0, 0].set_xticks(x)
        axs[0, 0].set_xticklabels(bucket_names)
        axs[0, 0].set_ylabel('% Range')
        axs[0, 0].set_title('3h Range by Time Bucket')
        axs[0, 0].legend()

        # Top-right: Boxplot
        sns.boxplot(data=bucket_df, palette="Blues", ax=axs[0, 1])
        axs[0, 1].set_ylabel('% 3h Range')
        axs[0, 1].set_title('Distribution by Time of Day')
        axs[0, 1].set_xlabel('Time Bucket (KST)')

        # Bottom-left: Histogram
        sns.histplot(self.df_24h['3h_range'], bins=80, kde=True, color='#1f77b4', ax=axs[1, 0])
        balanced = round(self.df_24h['3h_range'].quantile(0.75) * 1.10, 1)
        safe = round(self.df_24h['3h_range'].quantile(0.90) * 0.82, 1)
        agg = round(self.df_24h['3h_range'].quantile(0.75) * 0.88, 1)
        axs[1, 0].axvline(balanced, color='green', linestyle='--', linewidth=2.5, label=f'Balanced ±{balanced}%')
        axs[1, 0].axvline(safe, color='red', linestyle='--', linewidth=2.5, label=f'Safe ±{safe}%')
        axs[1, 0].axvline(agg, color='purple', linestyle='--', linewidth=2.5, label=f'Aggressive ±{agg}%')
        axs[1, 0].set_xlabel('% 3h Range')
        axs[1, 0].set_title('Overall 3h Range Distribution (~2 Years)')
        axs[1, 0].legend()

        # Bottom-right: Hourly Trend
        hourly_medians, hourly_p75, hourly_p90, hour_labels = [], [], [], []
        for h in range(24):
            start = f"{h:02d}:00"
            end = f"{(h + 1) % 24:02d}:00"
            bucket = self.df_24h.between_time(start, end)['3h_range'].dropna()
            hourly_medians.append(bucket.median())
            hourly_p75.append(bucket.quantile(0.75))
            hourly_p90.append(bucket.quantile(0.90))
            hour_labels.append(f"{h:02d}-{(h+1)%24:02d}")

        x = range(24)
        axs[1, 1].plot(x, hourly_medians, marker='o', linewidth=3, color='#1f77b4', label='Median 3h range')
        axs[1, 1].plot(x, hourly_p75, marker='s', linestyle='--', linewidth=2, color='orange', label='75th')
        axs[1, 1].plot(x, hourly_p90, marker='^', linestyle='--', linewidth=2, color='red', label='90th')
        axs[1, 1].set_xticks(x)
        axs[1, 1].set_xticklabels(hour_labels, rotation=45, ha='right')
        axs[1, 1].set_ylabel('% 3h Range')
        axs[1, 1].set_title('Hourly 3h Range Trend')
        axs[1, 1].grid(True, alpha=0.3)
        axs[1, 1].legend()

        # Main title with safe spacing
        fig.suptitle(
            f'{self.symbol} Full 24h Uniswap V3 3h Range Analysis (KST)\n'
            f'~2 Years • {len(self.df_24h):,} candles',
            fontsize=18, y=0.96
        )
        fig.tight_layout(rect=[0, 0, 1, 0.93])   # ← extra top space so title never overlaps

        plt.savefig(f"charts/{base}_combined_24h_{ts}.png", dpi=self.chart_dpi, bbox_inches='tight')
        plt.close()

        print(f"✅ All-in-one chart saved (no overlap!) → charts/{base}_combined_24h_{ts}.png\n")

    def print_range_recommendations(self):
        print("\n" + "="*90)
        print("🚀 UNISWAP V3 LP RANGE RECOMMENDATIONS (3-hour horizon)")
        print("                      FULL 24 HOURS KST")
        print("="*90)

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
            return balanced, safe, agg, round(series.median(), 3), round(p75, 3), round(p90, 3), len(series)

        # Collect data for CSV
        recs_list = []
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = self.symbol.replace('/', '_')

        print("Overall (full 24h):")
        res = print_recs("Full 24h", self.df_24h['3h_range'])
        if res:
            balanced, safe, agg, med, p75v, p90v, samples = res
            recs_list.append(['Overall Full 24h', med, p75v, p90v, balanced, safe, agg, samples])

        print("\n" + "-"*80)
        print("🕒 HOURLY RECOMMENDATIONS")
        print("-"*80)
        for h in range(24):
            start = f"{h:02d}:00"
            end   = f"{(h + 1) % 24:02d}:00"
            name  = f"{start} – {end}"
            bucket = self.df_24h.between_time(start, end)
            res = print_recs(name, bucket['3h_range'])
            if res:
                balanced, safe, agg, med, p75v, p90v, samples = res
                recs_list.append([name, med, p75v, p90v, balanced, safe, agg, samples])

        # === SAVE CSV ===
        os.makedirs('charts', exist_ok=True)  # reuse charts folder
        df_recs = pd.DataFrame(recs_list, columns=[
            'Bucket', 'Median', 'P75', 'P90', 'Balanced', 'Safe', 'Aggressive', 'Samples'
        ])
        csv_path = f"charts/{base}_hourly_recommendations_{ts}.csv"
        df_recs.to_csv(csv_path, index=False)
        print(f"\n✅ Hourly recommendations CSV saved → {csv_path}\n")

        print("\n✅ Done! Run weekly for fresh numbers & charts.")

    def run(self):
        self.fetch_data()
        if self.df_24h is None or len(self.df_24h) == 0:
            print("Error: No data.")
            return

        now = self.df_24h.index.max()
        self.compute_window_stats(self.df_24h, "FULL 2 YEARS")
        self.compute_window_stats(self.df_24h[self.df_24h.index > now - pd.Timedelta(days=365)], "LAST 1 YEAR")
        self.compute_window_stats(self.df_24h[self.df_24h.index > now - pd.Timedelta(days=180)], "LAST 6 MONTHS")

        self.generate_charts()
        self.print_range_recommendations()


# ====================== RUN ======================
if __name__ == "__main__":
    analyzer = UniswapV3StatsAnalyzer(
        symbol='ETH/USDT',   # ← change to 'BTC/USDT' anytime
        timeframe='15m',
        days_back=730,
        chart_dpi=165        # 145 = smaller files, 180 = sharper
    )
    analyzer.run()
