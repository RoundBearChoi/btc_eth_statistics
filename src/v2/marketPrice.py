import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz


class CryptoPriceDownloader:
    """Downloads BTC & ETH hourly data and extracts exact 10:00 / 22:00 KST prices."""

    def __init__(self):
        self.kst_tz = pytz.timezone('Asia/Seoul')
        # Safe start date to avoid the 730-day boundary bug
        self.start_date = '2024-02-26'
        self.output_file = 'btc_eth_prices_kst_10am_10pm_2years.csv'

    def _download_data(self):
        """Download raw hourly data for both assets."""
        print("Downloading hourly BTC-USD & ETH-USD data...")
        btc_data = yf.download('BTC-USD', start=self.start_date, interval='1h', progress=False)
        eth_data = yf.download('ETH-USD', start=self.start_date, interval='1h', progress=False)
        return btc_data, eth_data

    def _extract_kst_prices(self, df, asset):
        """Extract rows that fall exactly on 10:00 and 22:00 KST."""
        if df.empty:
            print(f"⚠️ No data for {asset}")
            return pd.DataFrame()

        # Convert to KST
        if df.index.tz is None:
            df.index = pd.to_datetime(df.index).tz_localize('UTC')
        df = df.tz_convert(self.kst_tz).copy()

        # Exactly 10:00 and 22:00 KST
        mask = (df.index.hour.isin([10, 22])) & (df.index.minute == 0)
        filtered = df[mask].copy()

        filtered['Asset'] = asset
        filtered['KST_Datetime'] = filtered.index.strftime('%Y-%m-%d %H:%M KST')
        filtered['Time_of_Day'] = filtered.index.strftime('%H:%M')
        filtered['Price'] = filtered['Open']   # price at exactly 10am/10pm KST

        return filtered[['KST_Datetime', 'Time_of_Day', 'Price', 'High', 'Low', 'Close', 'Volume']]

    def run(self):
        """Run the full pipeline: download → extract → merge → save."""
        btc_data, eth_data = self._download_data()

        btc_prices = self._extract_kst_prices(btc_data, 'BTC')
        eth_prices = self._extract_kst_prices(eth_data, 'ETH')

        if btc_prices.empty and eth_prices.empty:
            print("❌ Still no data. Try running again in 5 minutes.")
            return

        # Merge BTC & ETH on the exact KST datetime
        combined = pd.merge(
            btc_prices[['KST_Datetime', 'Time_of_Day', 'Price']].rename(columns={'Price': 'BTC_Price'}),
            eth_prices[['KST_Datetime', 'Price']].rename(columns={'Price': 'ETH_Price'}),
            on='KST_Datetime',
            how='outer'
        ).sort_values('KST_Datetime').reset_index(drop=True)

        print(f"\n✅ Success! Total data points: {len(combined):,}")
        print("\nLast 10 rows:")
        print(combined.tail(10).to_string(index=False))

        combined.to_csv(self.output_file, index=False)
        print(f"\n💾 Saved to: {self.output_file}")


if __name__ == "__main__":
    downloader = CryptoPriceDownloader()
    downloader.run()
