import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

class BTCETHOIAnalyzerStandalone:
    def __init__(self, csv_path='btc_eth_oi_standalone.csv'):
        print("🔄 Loading standalone BTC-ETH OI dataset...")
        self.df = pd.read_csv(csv_path, parse_dates=['open_time'])
        self.df.set_index('open_time', inplace=True)
        self.recent = self.df.dropna(subset=['btc_eth_oi_ratio']).copy()
        self.abs_oi_change = np.abs(self.recent['oi_ratio_24h_change'])
        self.large_oi_threshold = self.abs_oi_change.quantile(0.95)

    def _basic_stats(self):
        print("\n=== STANDALONE OI BASIC STATS ===")
        print(self.recent[['btc_eth_oi_ratio', 'btc_eth_price_ratio', 'oi_ratio_24h_change']].describe())
        print(f"\nCurrent BTC/ETH OI Ratio (USD): {self.recent['btc_eth_oi_ratio'].iloc[-1]:.3f}")
        print(f"Current BTC/ETH Price Ratio:     {self.recent['btc_eth_price_ratio'].iloc[-1]:.3f}")

    def _large_oi_vs_price_scatter(self):
        plt.figure(figsize=(12, 8))
        large_mask = self.abs_oi_change > self.large_oi_threshold
        plt.scatter(self.recent['oi_ratio_24h_change'], self.recent['price_ratio_24h_change'],
                    c='lightgray', s=5, alpha=0.4, label='All data')
        plt.scatter(self.recent.loc[large_mask, 'oi_ratio_24h_change'],
                    self.recent.loc[large_mask, 'price_ratio_24h_change'],
                    c='red', s=25, edgecolor='black', label=f'Large OI ratio move (top 5%)')
        plt.axhline(0, color='gray', ls='--')
        plt.axvline(0, color='gray', ls='--')
        plt.xlabel('Current 24h OI Ratio Change')
        plt.ylabel('Next 24h Price Ratio Change')
        plt.title('Large OI Ratio Moves vs Future BTC/ETH Price Move')
        plt.legend()
        plt.savefig('btc_eth_large_oi_vs_price.png', dpi=160, bbox_inches='tight')
        plt.close()

    def _fourteen_day_dual_chart(self):
        print("\nGenerating 14-day standalone chart (KST)...")
        end_time = self.recent.index.max()
        start_time = end_time - pd.Timedelta(days=14)
        plot_df = self.recent[(self.recent.index >= start_time) & (self.recent.index <= end_time)].copy()
        plot_df.index = plot_df.index.tz_localize('UTC').tz_convert('Asia/Seoul')

        fig, ax1 = plt.subplots(figsize=(15, 8.5))
        ax1.plot(plot_df.index, plot_df['btc_eth_oi_ratio'], color='teal', lw=3, label='BTC/ETH OI Ratio (USD)')
        ax1.set_ylabel('OI Ratio (USD)', color='teal')

        ax2 = ax1.twinx()
        ax2.plot(plot_df.index, plot_df['btc_eth_price_ratio'], color='orange', lw=2.5, label='BTC/ETH Price Ratio')
        ax2.set_ylabel('Price Ratio', color='orange')

        current_oi = plot_df['btc_eth_oi_ratio'].iloc[-1]
        ax1.annotate(f'CURRENT\nOI Ratio: {current_oi:.3f}', 
                     xy=(plot_df.index[-1], current_oi),
                     xytext=(30, 40), textcoords='offset points', fontsize=14, fontweight='bold',
                     bbox=dict(boxstyle="round,pad=0.8", facecolor='yellow', alpha=0.95))

        ax1.set_title('BTC-ETH OI Ratio vs Price Ratio (Last 14 Days)', fontsize=18, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        fig.suptitle(f'Latest: {plot_df.index[-1].strftime("%Y-%m-%d %H:%M KST")}', y=0.96)
        plt.legend(loc='upper left')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('btc_eth_oi_14d_standalone.png', dpi=160, bbox_inches='tight', facecolor='white')
        plt.close()
        print("   • btc_eth_oi_14d_standalone.png  (pure OI + price ratio)")

    def _oi_spike_detector_chart(self):
        print("\nGenerating OI Spike/Drop Detector chart (last 60 days, KST)...")
        plt.figure(figsize=(15, 7.5))
        
        # Last 60 days
        end_time = self.recent.index.max()
        start_time = end_time - pd.Timedelta(days=60)
        plot_df = self.recent[self.recent.index >= start_time].copy()
        
        # Convert to KST (matches your other chart)
        plot_df.index = plot_df.index.tz_localize('UTC').tz_convert('Asia/Seoul')
        
        # Color bars: red=spike, blue=drop, gray=normal
        colors = []
        for val in plot_df['oi_ratio_24h_change']:
            if val > self.large_oi_threshold:
                colors.append('#d62728')   # red
            elif val < -self.large_oi_threshold:
                colors.append('#1f77b4')   # blue
            else:
                colors.append('#7f7f7f')   # gray
        
        bars = plt.bar(plot_df.index, plot_df['oi_ratio_24h_change'], 
                       color=colors, alpha=0.85, width=0.85)
        
        # Red/blue threshold lines
        plt.axhline(self.large_oi_threshold, color='red', linestyle='--', lw=2.5,
                   label=f'Spike Threshold (+{self.large_oi_threshold:.4f})')
        plt.axhline(-self.large_oi_threshold, color='blue', linestyle='--', lw=2.5,
                   label=f'Drop Threshold (-{self.large_oi_threshold:.4f})')
        plt.axhline(0, color='black', lw=1)
        
        # Highlight TODAY
        latest_idx = -1
        latest_change = plot_df['oi_ratio_24h_change'].iloc[latest_idx]
        bars[latest_idx].set_color('#ffeb3b')   # bright yellow
        bars[latest_idx].set_edgecolor('black')
        bars[latest_idx].set_linewidth(3)
        
        # Status label
        if latest_change > self.large_oi_threshold:
            status = "STRONG SPIKE ↑"
            color = "red"
        elif latest_change < -self.large_oi_threshold:
            status = "STRONG DROP ↓"
            color = "blue"
        else:
            status = "Normal move"
            color = "black"
        
        plt.annotate(f'TODAY\n{latest_change:+.4f}\n{status}', 
                    xy=(plot_df.index[latest_idx], latest_change),
                    xytext=(8, 30 if latest_change > 0 else -50),
                    textcoords='offset points', fontsize=13, fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.8", facecolor='yellow', alpha=0.95))
        
        plt.title('BTC/ETH OI Ratio 24h Change — Spike / Drop Detector', 
                 fontsize=16, fontweight='bold')
        plt.ylabel('24h Change in BTC/ETH OI Ratio')
        plt.xlabel('Date (KST)')
        plt.xticks(rotation=45)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        plt.savefig('btc_eth_oi_spike_detector.png', dpi=160, bbox_inches='tight')
        plt.close()
        
        print(f"   • btc_eth_oi_spike_detector.png  →  {status} ({latest_change:+.4f})")
        print(f"     Thresholds (±95th percentile): ±{self.large_oi_threshold:.4f}")

    def run(self):
        self._basic_stats()
        self._large_oi_vs_price_scatter()
        self._fourteen_day_dual_chart()
        self._oi_spike_detector_chart()
        print("\n✅ Standalone OI Analysis complete! Charts saved:")
        print("   • btc_eth_large_oi_vs_price.png")
        print("   • btc_eth_oi_14d_standalone.png")
        print("   • btc_eth_oi_spike_detector.png   ← NEW: Today's spike/drop status!")

if __name__ == "__main__":
    analyzer = BTCETHOIAnalyzerStandalone()
    analyzer.run()
