import pandas as pd
import os

class DayDataProcessor:
    """
    Loads btc_eth_prices_kst_10am_10pm_2years.csv and rearranges it into
    a daily paired format (exactly like your sample sort.csv):
    
    One row per day → AM (10:00 KST) + BTC/ETH ratio + PM (22:00 KST) + BTC/ETH ratio
    """
    
    def __init__(self, input_file='btc_eth_prices_kst_10am_10pm_2years.csv'):
        self.input_file = input_file
        self.output_file = 'btc_eth_daily_paired.csv'   # you can rename if you want "sample sort.csv"

    def load_data(self):
        """Load the CSV and prepare datetime + ratio."""
        if not os.path.exists(self.input_file):
            raise FileNotFoundError(f"❌ Input file '{self.input_file}' not found!")

        df = pd.read_csv(self.input_file)
        print(f"✅ Loaded {len(df):,} records from {self.input_file}")

        # Clean datetime column (remove " KST" suffix if present)
        df['KST_Datetime'] = pd.to_datetime(
            df['KST_Datetime'].str.replace(' KST', '', regex=False),
            format='%Y-%m-%d %H:%M'
        )

        # Extract date for grouping
        df['Date'] = df['KST_Datetime'].dt.date

        # Calculate BTC/ETH ratio
        df['BTC_ETH_Ratio'] = df['BTC_Price'] / df['ETH_Price']

        return df.sort_values('KST_Datetime').reset_index(drop=True)

    def create_daily_pairs(self):
        """Pair every day's 10:00 KST and 22:00 KST."""
        df = self.load_data()
        daily_rows = []

        for date, group in df.groupby('Date'):
            group = group.sort_values('KST_Datetime').reset_index(drop=True)

            if len(group) >= 2:
                am = group.iloc[0]   # 10:00 KST
                pm = group.iloc[1]   # 22:00 KST

                row = [
                    am['KST_Datetime'].strftime('%Y-%m-%d %H:%M KST'),  # AM datetime
                    am['Time_of_Day'],                                 # AM time
                    am['BTC_Price'],                                   # AM BTC
                    am['ETH_Price'],                                   # AM ETH
                    round(am['BTC_ETH_Ratio'], 10),                    # AM ratio (matches sample precision)

                    pm['KST_Datetime'].strftime('%Y-%m-%d %H:%M KST'), # PM datetime
                    pm['Time_of_Day'],                                 # PM time
                    pm['BTC_Price'],                                   # PM BTC
                    pm['ETH_Price'],                                   # PM ETH
                    round(pm['BTC_ETH_Ratio'], 10)                     # PM ratio
                ]
                daily_rows.append(row)
            else:
                print(f"⚠️  Skipping incomplete day {date} (only {len(group)} record(s))")

        # Create DataFrame with exact column order like your sample
        columns = [
            'KST_Datetime', 'Time_of_Day', 'BTC_Price', 'ETH_Price', 'BTC_ETH_Ratio',
            'KST_Datetime', 'Time_of_Day', 'BTC_Price', 'ETH_Price', 'BTC_ETH_Ratio'
        ]
        result_df = pd.DataFrame(daily_rows, columns=columns)

        # Save exactly like sample sort.csv (no index, floating-point precision preserved)
        result_df.to_csv(self.output_file, index=False, float_format='%.10f')
        
        print(f"\n🎉 Success! Created {len(result_df):,} daily paired rows.")
        print(f"💾 Saved to → {self.output_file}")
        print("\nFirst row preview (matches your sample format):")
        print(result_df.head(1).to_string(index=False))

        return result_df


if __name__ == "__main__":
    processor = DayDataProcessor()
    processor.create_daily_pairs()
