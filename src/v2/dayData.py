import pandas as pd
import os

class DayDataProcessor:
    """
    Loads btc_eth_prices_kst_10am_10pm_2years.csv and creates daily paired rows
    exactly like sample sort.csv + the two requested columns:
    
    • Ratio_Difference     = PM_ratio - AM_ratio
    • Ratio_Relative_Change = (PM_ratio - AM_ratio) / AM_ratio   ← decimal form (NOT %)
    
    Example for your last row (2026-02-23):
        Ratio_Difference      = -0.1418641661
        Ratio_Relative_Change = -0.00409156566492   ← exactly what you asked for
    """
    
    def __init__(self, input_file='btc_eth_prices_kst_10am_10pm_2years.csv'):
        self.input_file = input_file
        self.output_file = 'btc_eth_daily_paired.csv'   # change to "sample sort.csv" if you want

    def load_data(self):
        """Load CSV and prepare data."""
        if not os.path.exists(self.input_file):
            raise FileNotFoundError(f"❌ Input file '{self.input_file}' not found!")

        df = pd.read_csv(self.input_file)
        print(f"✅ Loaded {len(df):,} records from {self.input_file}")

        # Clean datetime
        df['KST_Datetime'] = pd.to_datetime(
            df['KST_Datetime'].str.replace(' KST', '', regex=False),
            format='%Y-%m-%d %H:%M'
        )

        df['Date'] = df['KST_Datetime'].dt.date
        df['BTC_ETH_Ratio'] = df['BTC_Price'] / df['ETH_Price']

        return df.sort_values('KST_Datetime').reset_index(drop=True)

    def create_daily_pairs(self):
        """Build the paired daily rows."""
        df = self.load_data()
        daily_rows = []

        for date, group in df.groupby('Date'):
            group = group.sort_values('KST_Datetime').reset_index(drop=True)

            if len(group) >= 2:
                am = group.iloc[0]   # 10:00 KST
                pm = group.iloc[1]   # 22:00 KST

                am_ratio = am['BTC_ETH_Ratio']
                pm_ratio = pm['BTC_ETH_Ratio']

                # === Your requested calculations ===
                ratio_diff = round(pm_ratio - am_ratio, 10)
                ratio_rel_change = round(
                    (pm_ratio - am_ratio) / am_ratio, 14
                ) if am_ratio != 0 else 0.0

                row = [
                    am['KST_Datetime'].strftime('%Y-%m-%d %H:%M KST'),
                    am['Time_of_Day'],
                    am['BTC_Price'],
                    am['ETH_Price'],
                    round(am_ratio, 10),

                    pm['KST_Datetime'].strftime('%Y-%m-%d %H:%M KST'),
                    pm['Time_of_Day'],
                    pm['BTC_Price'],
                    pm['ETH_Price'],
                    round(pm_ratio, 10),

                    ratio_diff,          # column 11
                    ratio_rel_change     # column 12 ← now decimal form
                ]
                daily_rows.append(row)
            else:
                print(f"⚠️  Skipping incomplete day {date} (only {len(group)} record(s))")

        # Column names (AM block + PM block + 2 new columns)
        columns = [
            'KST_Datetime', 'Time_of_Day', 'BTC_Price', 'ETH_Price', 'BTC_ETH_Ratio',   # AM
            'KST_Datetime', 'Time_of_Day', 'BTC_Price', 'ETH_Price', 'BTC_ETH_Ratio',   # PM
            'Ratio_Difference', 'Ratio_Relative_Change'                                 # NEW
        ]

        result_df = pd.DataFrame(daily_rows, columns=columns)

        # Save with high precision so the relative change keeps all 14 decimals
        result_df.to_csv(self.output_file, index=False, float_format='%.14f')
        
        print(f"\n🎉 Success! Created {len(result_df):,} daily rows.")
        print(f"💾 Saved to → {self.output_file}")
        print("\nPreview of the LAST row (your 2026-02-23 data):")
        print(result_df.tail(1)[['Ratio_Difference', 'Ratio_Relative_Change']].to_string(index=False))

        return result_df


if __name__ == "__main__":
    processor = DayDataProcessor()
    processor.create_daily_pairs()
