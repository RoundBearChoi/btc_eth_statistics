import ccxt
import pandas as pd
from datetime import datetime, timedelta, timezone
import time

# ================== CONFIG (aligned to your 6-month spot) ==================
EXCHANGE = 'binance'                    # better OI history than Bybit
MAIN_SYMBOL = 'ETHBTC'                  # perfect match for WETH-cbBTC
TIMEFRAME_OI = '1h'                     # 1h gives longer history than 15m
DAYS_BACK = 250                         # ~8 months (covers your spot + buffer)
# ===========================================

print(f"🚀 Pulling 8-month data (matches your spot period) on {EXCHANGE.upper()}...")

exchange = ccxt.binance({
    'options': {'defaultType': 'future'},
    'enableRateLimit': True,
})
exchange.load_markets()

def save_df(df, filename_base, suffix):
    file = f"{filename_base}{suffix}.parquet"
    try:
        df.to_parquet(file, index=False)
        print(f"✅ Saved {len(df):,} rows → {file}")
    except Exception:
        file_csv = file.replace('.parquet', '.csv')
        df.to_csv(file_csv, index=False)
        print(f"→ Saved as CSV: {file_csv} (run 'pip install pyarrow' for parquet)")

def fetch_funding_rates(symbol: str):
    print(f"\n📈 Funding rates → {symbol}")
    since = int((datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)).timestamp() * 1000)
    all_data = []
    while True:
        try:
            rates = exchange.fetch_funding_rate_history(symbol, since=since, limit=1000)
            if not rates: break
            all_data.extend(rates)
            print(f"   → Got {len(rates)} records (total: {len(all_data):,})")
            since = rates[-1]['timestamp'] + 1
            if len(rates) < 900: break
            time.sleep(0.3)
        except Exception as e:
            print(f"   ⚠️ {e}")
            break
    if all_data:
        df = pd.DataFrame(all_data)
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        df = df.sort_values('timestamp').reset_index(drop=True)
        save_df(df, symbol.replace('/', '_'), '_funding_8m')
        print(f"   Range: {df['datetime'].min()} → {df['datetime'].max()}\n")

def fetch_open_interest(symbol: str, timeframe: str):
    print(f"📊 {timeframe} Open Interest → {symbol}")
    since = int((datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)).timestamp() * 1000)
    all_data = []
    while True:
        try:
            oi = exchange.fetch_open_interest_history(symbol, timeframe=timeframe, since=since, limit=500)
            if not oi: break
            all_data.extend(oi)
            print(f"   → Got {len(oi)} records (total: {len(all_data):,})")
            since = oi[-1]['timestamp'] + 1
            if len(oi) < 400: break
            time.sleep(0.25)
        except Exception as e:
            print(f"   → {e} (max history reached)")
            break
    if all_data:
        df = pd.DataFrame(all_data)
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        df = df.sort_values('timestamp').reset_index(drop=True)
        save_df(df, symbol.replace('/', '_'), f'_oi_{timeframe}_8m')
        print(f"   Range: {df['datetime'].min()} → {df['datetime'].max()}\n")

# ===================== RUN =====================
symbols = ['ETHBTC', 'BTCUSDT', 'ETHUSDT']
for sym in symbols:
    print("=" * 70)
    print(f"Processing {sym}")
    print("=" * 70)
    fetch_funding_rates(sym)
    fetch_open_interest(sym, TIMEFRAME_OI)

print("\n🎉 DONE! New files created with _8m suffix.")
print("Now run the merge again — it will be perfectly aligned.")
