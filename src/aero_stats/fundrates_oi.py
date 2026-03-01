import pandas as pd
from pathlib import Path

print("📁 Files found:")
for f in sorted(Path('.').glob('*.*')):
    if f.suffix.lower() in ['.csv', '.parquet']:
        print(f"   • {f.name}")

# ================== CONFIG ==================
spot_file = 'aerodrome_0x22aee3699b6a0fed71490c103bd4e5f3309891d5_15min_max2.0y.csv'
funding_file = 'ETHBTC_funding_2y.csv'           # full 2y ETH/BTC funding
oi_file = 'ETHBTCUSDT_oi_15m_2y.csv'             # your Bybit 15m OI file
funding_btc_file = 'BTCUSDT_funding_2y.csv'
funding_eth_file = 'ETHUSDT_funding_2y.csv'
# ===========================================

print(f"\n🔄 Loading spot data: {spot_file}")

spot = pd.read_csv(spot_file)

# Normalize spot datetime
time_cols = ['datetime', 'timestamp', 'time', 'ts', 'date', 'block_time']
datetime_col = next((col for col in time_cols if col.lower() in [c.lower() for c in spot.columns]), None)
if not datetime_col:
    raise ValueError(f"Could not find time column. Columns: {list(spot.columns)}")

spot['datetime'] = pd.to_datetime(spot[datetime_col], utc=True)
if datetime_col != 'datetime':
    spot = spot.drop(columns=[datetime_col])
spot = spot.sort_values('datetime').reset_index(drop=True)

print(f"✅ Spot loaded: {len(spot):,} rows | {spot['datetime'].min()} → {spot['datetime'].max()}")

# Load funding
funding = pd.read_csv(funding_file)
funding['datetime'] = pd.to_datetime(funding['timestamp'], unit='ms', utc=True)

# Load OI
oi = pd.read_csv(oi_file)
oi['datetime'] = pd.to_datetime(oi['timestamp'], unit='ms', utc=True)

print(f"\n🔍 OI columns: {list(oi.columns)}")   # ← This will tell us the exact names

# Load synthetic funding
funding_btc = pd.read_csv(funding_btc_file)
funding_eth = pd.read_csv(funding_eth_file)
funding_btc['datetime'] = pd.to_datetime(funding_btc['timestamp'], unit='ms', utc=True)
funding_eth['datetime'] = pd.to_datetime(funding_eth['timestamp'], unit='ms', utc=True)

# Normalize precision
for df_temp in [spot, funding, oi, funding_btc, funding_eth]:
    df_temp['datetime'] = df_temp['datetime'].astype('datetime64[ms, UTC]')

# Auto-detect OI columns (works for Binance AND Bybit)
open_col = next((col for col in oi.columns if 'open' in col.lower() and 'interest' in col.lower() and 'value' not in col.lower()), None)
value_col = next((col for col in oi.columns if any(x in col.lower() for x in ['value', 'usd', 'notional'])), None)

if not open_col or not value_col:
    raise ValueError(f"Could not detect OI columns. Available: {list(oi.columns)}")

print(f"✅ Using OI columns → contracts: '{open_col}' | USD: '{value_col}'")

# ================== MERGE ==================
df = pd.merge_asof(
    spot,
    funding[['datetime', 'fundingRate']].rename(columns={'fundingRate': 'funding_rate_ethbtc'}),
    on='datetime', direction='backward'
)

df = pd.merge_asof(
    df,
    oi[['datetime', open_col, value_col]].rename(columns={open_col: 'oi_contracts', value_col: 'oi_usd'}),
    on='datetime', direction='backward'
)

# Synthetic funding
df = pd.merge_asof(df, funding_eth[['datetime', 'fundingRate']].rename(columns={'fundingRate': 'funding_rate_eth'}), on='datetime', direction='backward')
df = pd.merge_asof(df, funding_btc[['datetime', 'fundingRate']].rename(columns={'fundingRate': 'funding_rate_btc'}), on='datetime', direction='backward')
df['funding_rate_synthetic'] = df['funding_rate_eth'] - df['funding_rate_btc']

# Forward-fill funding
for col in ['funding_rate_ethbtc', 'funding_rate_eth', 'funding_rate_btc', 'funding_rate_synthetic']:
    df[col] = df[col].ffill()

print(f"\n🎉 MERGE COMPLETE! Final dataset: {len(df):,} rows")
print(df[['datetime', 'funding_rate_ethbtc', 'funding_rate_synthetic', 'oi_usd']].tail(8))

# Save
output_file = 'weth_cbbtc_15m_with_funding_oi.parquet'
df.to_parquet(output_file, index=False)
print(f"💾 Saved → {output_file}")
print("\n✅ You now have perfectly aligned 15min spot + funding + OI data!")
