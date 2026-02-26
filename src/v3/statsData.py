import ccxt
import pandas as pd
import pytz
import os
from datetime import datetime, timedelta


class UniswapV3StatsAnalyzer:
    """
    Clean, encapsulated analyzer for Uniswap V3 active LP stats.
    Exactly the same logic + now automatically saves raw data to CSV.
    """

    def __init__(self, symbol: str = 'ETH/USDT', timeframe: str = '15m', days_back: int = 730):
        self.symbol = symbol
        self.timeframe = timeframe
        self.days_back = days_back
        self.full_df = None      # full history (KST)
        self.df_active = None    # only 8am–8pm KST
        self.exchange = None

    def fetch_data(self):
        """Fetch full history, convert to KST, filter to active window, and SAVE RAW CSV."""
        print(f"Fetching {self.days_back} days of {self.timeframe} {self.symbol} data... (this takes ~20-40 seconds)")

        self.exchange = ccxt.binance({'enableRateLimit': True})

        # Fetch in chunks
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

        # Store both versions
        self.full_df = df.copy()
        self.df_active = df.between_time('08:00', '20:00').copy()

        print(f"Loaded {len(self.df_active):,} candles during 8am–8pm KST.")

        # ============== SAVE RAW DATA TO CSV ==============
        os.makedirs('raw_data', exist_ok=True)
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = self.symbol.replace('/', '_')

        full_path = f"raw_data/{base}_{self.timeframe}_full_kst_{timestamp_str}.csv"
        active_path = f"raw_data/{base}_{self.timeframe}_active_8am8pm_kst_{timestamp_str}.csv"

        self.full_df.to_csv(full_path)
        self.df_active.to_csv(active_path)

        print(f"✅ Raw data saved to 'raw_data/' folder:")
        print(f"   • Full history : {full_path.split('/')[-1]}")
        print(f"   • Active window: {active_path.split('/')[-1]}\n")

    def compute_window_stats(self, sub_df: pd.DataFrame, label: str):
        """Compute and print exactly the same stats as before."""
        print(f"=== {label} ===")

        for hours in [2, 3]:
            periods = int(hours * 60 / 15) if self.timeframe == '15m' else hours

            sub_df[f'{hours}h_return'] = sub_df['close'].pct_change(periods) * 100
            sub_df[f'{hours}h_range'] = (
                sub_df['high'].rolling(periods).max() -
                sub_df['low'].rolling(periods).min()
            ) / sub_df['close'].shift(periods) * 100

            print(f"\n{hours}h Rolling (8am–8pm KST):")
            stats = sub_df[[f'{hours}h_return', f'{hours}h_range']].describe(
                percentiles=[0.5, 0.75, 0.9, 0.95]
            )
            print(stats.round(3))

            print("  Per-bucket median range:")
            for s, e in [('08:00','11:00'), ('11:00','14:00'), ('14:00','17:00'), ('17:00','20:00')]:
                bucket = sub_df.between_time(s, e)
                print(f"    {s}-{e}: {bucket[f'{hours}h_range'].median():.3f}%")

        print("")  # clean spacing

    def print_range_recommendations(self):
        """Print the exact same beautiful recommendations as before."""
        print("\n" + "="*85)
        print("🚀 UNISWAP V3 ACTIVE LP RANGE RECOMMENDATIONS (3-hour horizon)")
        print("="*85)

        def print_recs(label, range_series):
            p75 = range_series.quantile(0.75)
            p90 = range_series.quantile(0.90)
            balanced = round(p75 * 1.10, 1)
            safe     = round(p90 * 0.82, 1)
            agg      = round(p75 * 0.88, 1)

            print(f"\n{label}:")
            print(f"   Balanced     → ±{balanced}%   ← Recommended to start with")
            print(f"   Safe         → ±{safe}%      ← Very few rebalances")
            print(f"   Aggressive   → ±{agg}%      ← Max fee collection")

        print("Overall (full 8am–8pm):")
        print_recs("Full Day", self.df_active['3h_range'])

        print("\nTime-of-Day Specific (recommended for you):")
        for start, end, name in [
            ('08:00','11:00', '🌅 08:00 – 11:00'),
            ('11:00','14:00', '☀️ 11:00 – 14:00'),
            ('14:00','17:00', '🌤️ 14:00 – 17:00'),
            ('17:00','20:00', '🌆 17:00 – 20:00')
        ]:
            bucket = self.df_active.between_time(start, end)
            print_recs(name, bucket['3h_range'])

        print("\n✅ Script finished! These recommendations are based 100% on your data.")
        print("   Run this script weekly — it will auto-update as market regimes change.")

    def run(self):
        """Run everything exactly like before (now with auto CSV save)."""
        self.fetch_data()

        if self.df_active is None or len(self.df_active) == 0:
            print("Error: No data loaded.")
            return

        now = self.df_active.index.max()

        self.compute_window_stats(self.df_active, "FULL 2 YEARS")
        self.compute_window_stats(
            self.df_active[self.df_active.index > now - pd.Timedelta(days=365)],
            "LAST 1 YEAR"
        )
        self.compute_window_stats(
            self.df_active[self.df_active.index > now - pd.Timedelta(days=180)],
            "LAST 6 MONTHS"
        )

        self.print_range_recommendations()


# ====================== RUN THE ANALYZER ======================
if __name__ == "__main__":
    # ================== CONFIGURATION ==================
    analyzer = UniswapV3StatsAnalyzer(
        symbol='ETH/USDT',      # ← Change to 'BTC/USDT' or any pair
        timeframe='15m',
        days_back=730
    )
    analyzer.run()
