# analyzePrices.py
import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

sns.set_style("darkgrid")
plt.rcParams['figure.figsize'] = (12, 8)

class PriceAnalyzer:
    def __init__(self, token1: str, token2: str):
        self.name1 = token1.upper()
        self.name2 = token2.upper()
        self.filename = f"{self.name1}_{self.name2}_daily_closing_prices_2y.csv"

    def load_data(self):
        if not os.path.exists(self.filename):
            print(f"❌ CSV not found: {self.filename}")
            print("   Run first: python getPrices.py eth uni")
            sys.exit(1)
        
        df = pd.read_csv(self.filename, index_col='Date', parse_dates=True)
        self.df = df[[self.name1, self.name2]].dropna()
        print(f"✅ Loaded {len(self.df):,} days ({self.df.index[0].date()} → {self.df.index[-1].date()})")

    def analyze_and_plot(self):
        df = self.df.copy()
        col1, col2 = self.name1, self.name2

        # 1. Price Ratio
        df['Ratio'] = df[col1] / df[col2]
        
        # 2. Daily log returns (best for correlation)
        df['Ret1'] = np.log(df[col1] / df[col1].shift(1))
        df['Ret2'] = np.log(df[col2] / df[col2].shift(1))
        df = df.dropna()

        # 3. Key stats
        corr = df['Ret1'].corr(df['Ret2'])
        rolling_corr_30 = df['Ret1'].rolling(30).corr(df['Ret2'])
        rolling_corr_90 = df['Ret1'].rolling(90).corr(df['Ret2'])

        print("\n" + "="*60)
        print(f"📊 CORRELATION ANALYSIS: {col1} vs {col2}")
        print("="*60)
        print(f"Overall correlation of daily returns : {corr:.4f} ({'Very High' if abs(corr)>0.8 else 'High' if abs(corr)>0.6 else 'Moderate' if abs(corr)>0.4 else 'Low'})")
        print(f"30-day rolling corr (latest)         : {rolling_corr_30.iloc[-1]:.4f}")
        print(f"90-day rolling corr (latest)         : {rolling_corr_90.iloc[-1]:.4f}")
        print(f"ETH/UNI ratio (today)                : {df['Ratio'].iloc[-1]:.4f}")
        print(f"Ratio 30-day change                  : {(df['Ratio'].iloc[-1]/df['Ratio'].iloc[-30] - 1)*100:+.1f}%")
        print("="*60)

        # ====================== CHARTS ======================
        fig = plt.figure()

        # Chart 1: Normalized Prices
        ax1 = fig.add_subplot(2, 2, 1)
        norm = df[[col1, col2]] / df[[col1, col2]].iloc[0] * 100
        norm.plot(ax=ax1, title=f'Normalized Prices (start = 100)')
        ax1.set_ylabel('Index')

        # Chart 2: Price Ratio
        ax2 = fig.add_subplot(2, 2, 2)
        df['Ratio'].plot(ax=ax2, color='purple', title=f'{col1}/{col2} Price Ratio')
        ax2.axhline(df['Ratio'].mean(), color='gray', linestyle='--', alpha=0.7)

        # Chart 3: Rolling Correlation
        ax3 = fig.add_subplot(2, 2, 3)
        rolling_corr_30.plot(ax=ax3, label='30-day', color='orange')
        rolling_corr_90.plot(ax=ax3, label='90-day', color='blue')
        ax3.axhline(corr, color='red', linestyle='--', label=f'Overall ({corr:.3f})')
        ax3.set_title('Rolling Correlation of Returns')
        ax3.legend()

        # Chart 4: Returns Scatter
        ax4 = fig.add_subplot(2, 2, 4)
        sns.regplot(x=df['Ret2'], y=df['Ret1'], ax=ax4, scatter_kws={'alpha':0.4}, line_kws={'color':'red'})
        ax4.set_xlabel(f'{col2} Daily Log Return')
        ax4.set_ylabel(f'{col1} Daily Log Return')
        ax4.set_title('Return Scatter + Regression')

        plt.tight_layout()
        plot_file = f"{col1}_{col2}_correlation_analysis.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        print(f"\n💾 Charts saved as: {plot_file}")
        plt.show()

        # Bonus: Save full data with metrics
        df.to_csv(f"{col1}_{col2}_full_analysis.csv")
        print(f"💾 Full dataset with returns & ratio saved as: {col1}_{col2}_full_analysis.csv")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python analyzePrices.py <token1> <token2>")
        print("Example: python analyzePrices.py eth uni")
        sys.exit(1)

    analyzer = PriceAnalyzer(sys.argv[1], sys.argv[2])
    analyzer.load_data()
    analyzer.analyze_and_plot()
