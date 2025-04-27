import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import os

today_str = datetime.now().strftime("%Y-%m-%d")
input_file = f"processed_data/apple_news_with_sentiment_{today_str}.csv"

print(f"Reading sentiment data from {input_file}...")
df = pd.read_csv(input_file)

df['scraped_at'] = pd.to_datetime(df['scraped_at'])
df['headline_date'] = df['scraped_at'].dt.date

symbols = df['symbol'].unique()

start_date = df['headline_date'].min() - timedelta(days=1)
end_date = df['headline_date'].max() + timedelta(days=2)

price_data = {}

# Download stock price data
for symbol in symbols:
    print(f"Fetching price data for {symbol}...")
    data = yf.download(symbol, start=start_date, end=end_date)
    if data.empty:
        print(f"No data for {symbol}. Skipping.")
        continue
    data = data[['Close']].reset_index()
    data.columns = ['date', 'close']
    price_data[symbol] = data

# Merge news with stock price
all_rows = []

for symbol in symbols:
    if symbol not in price_data:
        continue

    print(f"Processing {symbol} data...")
    df_stock = df[df['symbol'] == symbol].copy()
    price_df = price_data[symbol].copy()

    df_stock['headline_date'] = pd.to_datetime(df_stock['headline_date']).dt.date
    price_df['date'] = pd.to_datetime(price_df['date']).dt.date

    # Merge today's close
    merged = pd.merge(df_stock, price_df, left_on='headline_date', right_on='date', how='left')

    # Merge next day's close (smart way)
    price_df_next = price_df.copy()
    price_df_next['date'] = price_df_next['date'] + timedelta(days=1) 
    merged = pd.merge(merged, price_df_next[['date', 'close']], left_on='headline_date', right_on='date', how='left', suffixes=('', '_next'))


    merged['label'] = (merged['close_next'] > merged['close']).astype(int)

    print(f"\n--- DEBUG: {symbol} ---")
    print("Sample headline_date:", merged['headline_date'].unique()[:5])
    print("Sample close dates:", price_df['date'].unique()[:5])

    all_rows.append(merged)


final_df = pd.concat(all_rows)
final_df = final_df.dropna(subset=['close', 'close_next'])


output_folder = 'final_data'
os.makedirs(output_folder, exist_ok=True)

output_file = os.path.join(output_folder, f"apple_final_data_{today_str}.csv")
final_df.to_csv(output_file, index=False)

print(f"Saved labeled data to {output_file}")
print(final_df[['symbol', 'title', 'vader_sentiment', 'finbert_sentiment', 'close', 'close_next', 'label']].head())
