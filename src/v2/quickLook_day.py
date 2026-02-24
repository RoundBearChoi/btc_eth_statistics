import pandas as pd

class DayRatioQuickLook:
    """
    Quick-look analyzer for btc_eth_day_paired.csv
    Focuses on Ratio_Relative_Change (decimal) → shows everything in %
    """

    def __init__(self, csv_file='btc_eth_day_paired.csv'):
        self.csv_file = csv_file
        self.output_sorted = 'btc_eth_ratio_sorted_by_change.csv'
        self.df = None

    def load_data(self):
        if not pd.io.common.file_exists(self.csv_file):
            raise FileNotFoundError(f"❌ File '{self.csv_file}' not found!")

        self.df = pd.read_csv(self.csv_file)

        change_col = 'Ratio_Relative_Change'
        if change_col not in self.df.columns:
            change_col = self.df.columns[-1]

        self.df['Change_%'] = self.df[change_col] * 100

        # FIXED: No more warnings
        self.df['Date'] = self.df.iloc[:, 0].str[:10]

        print('')
        print(f"✅ Loaded {len(self.df):,} daily pairs from {self.csv_file}")
        print(f"   Period : {self.df.iloc[0]['Date']} → {self.df.iloc[-1]['Date']}")
        return self.df

    def analyze(self):
        if self.df is None:
            self.load_data()

        changes_pct = self.df['Change_%']

        print("\n" + "=" * 80)
        print("   BTC/ETH DAILY RATIO CHANGE QUICK LOOK (10:00 → 22:00 KST)")
        print("=" * 80)

        print("\n📊 SUMMARY STATISTICS (% change)")
        print(f"   Mean           : {changes_pct.mean():+8.3f}%")
        print(f"   Median         : {changes_pct.median():+8.3f}%")
        print(f"   Std Dev        : {changes_pct.std():8.3f}%")
        print(f"   Min            : {changes_pct.min():+8.3f}%")
        print(f"   Max            : {changes_pct.max():+8.3f}%")

        print("\n📈 KEY PERCENTILES (% change)")
        for p in [1, 5, 10, 25, 50, 75, 90, 95, 99]:
            val = changes_pct.quantile(p / 100)
            print(f"   {p:2d}th percentile : {val:+8.3f}%")

        positive = (changes_pct > 0).sum()
        print(f"\n📌 Positive days : {positive:,} ({positive / len(self.df) * 100:5.1f}%)")
        print(f"   Negative days : {len(self.df) - positive:,} ({(len(self.df) - positive) / len(self.df) * 100:5.1f}%)")

        print(f"\n🔥 EXTREME DAYS")
        print(f"   > +3.0% : {(changes_pct > 3.0).sum():3d} days")
        print(f"   > +2.0% : {(changes_pct > 2.0).sum():3d} days")
        print(f"   < -2.0% : {(changes_pct < -2.0).sum():3d} days")
        print(f"   < -3.0% : {(changes_pct < -3.0).sum():3d} days")

        sorted_df = self.df.sort_values('Change_%').copy()

        print("\n📉 8 WORST DAYS (biggest ratio drops)")
        print(sorted_df.head(8)[['Date', 'Change_%']].round(3).to_string(index=False))

        print("\n🏆 8 BEST DAYS (biggest ratio gains)")
        print(sorted_df.tail(8)[['Date', 'Change_%']].round(3).to_string(index=False))

        sorted_df.to_csv(self.output_sorted, index=False, float_format='%.6f')
        print(f"\n💾 Saved fully sorted file → {self.output_sorted}")

        return self.df


if __name__ == "__main__":
    analyzer = DayRatioQuickLook()
    analyzer.analyze()
