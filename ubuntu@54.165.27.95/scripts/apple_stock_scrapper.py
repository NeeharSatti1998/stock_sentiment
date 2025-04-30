import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# Load the dataset
df = pd.read_csv("data/apple_sentiment_data.csv")


df['scraped_at'] = pd.to_datetime(df['scraped_at'])
df["headline_date"] = df["scraped_at"].dt.date


symbol = "AAPL"

# Find price data range
start_date = df["headline_date"].min() - timedelta(days=1)
end_date = df["headline_date"].max() + timedelta(days=2)

# Download stock price
print(f"Fetching price data for {symbol}...")
price_df = yf.download(symbol, start=start_date, end=end_date)
price_df = price_df[["Close"]].reset_index()
price_df.columns = ["date", "close"]

# Merge news with price
print(f"Processing {symbol} news...")
df["headline_date"] = pd.to_datetime(df["headline_date"]).dt.date
price_df["date"] = pd.to_datetime(price_df["date"]).dt.date

merged = pd.merge(df, price_df, left_on="headline_date", right_on="date", how="left")

# Get next day close
price_df["prev_date"] = price_df["date"] - timedelta(days=1)
price_df_shift = price_df[["prev_date", "close"]].copy()
price_df_shift.columns = ["date", "next_close"]

merged = pd.merge(merged, price_df_shift, on="date", how="left")

# Create label: 1 if next day close > today's close
merged["label"] = (merged["next_close"] > merged["close"]).astype(int)


final_df = merged.dropna(subset=["close", "next_close"])

# Save final labeled dataset
final_df.to_csv("apple_final_data.csv", index=False)
print("Saved to apple_final_data.csv")
print(final_df[["title", "vader_sentiment", "finbert_sentiment", "close", "next_close", "label"]].head())
