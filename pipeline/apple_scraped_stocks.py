import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import os
import glob
import pytz
import mysql.connector

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root1234',  
    'database': 'apple_stock_sentiment'
}
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()


files = glob.glob("processed_data/apple_news_with_sentiment_*.csv")
if not files:
    raise FileNotFoundError("No sentiment files found. Scrape and run sentiment first!")

input_file = max(files, key=os.path.getctime)
print(f"Reading sentiment data from {input_file}...")

df = pd.read_csv(input_file)


eastern = pytz.timezone('US/Eastern')
df['scraped_at'] = pd.to_datetime(df['scraped_at'], utc=True).dt.tz_convert(eastern)
df['headline_date'] = df['scraped_at'].dt.date

symbols = df['symbol'].unique()

today_date = datetime.now(eastern).date()
#today_date = datetime.now(eastern).date()-timedelta(days=1)

price_data = {}
for symbol in symbols:
    print(f"Fetching {symbol} closing price for {today_date}...")
    data = yf.download(symbol, start=today_date, end=today_date + timedelta(days=1))
    if data.empty:
        print(f"No data for {symbol} on {today_date}. Market might be closed.")
        continue

    close_price = float(data['Close'].values[0])  
    price_data[symbol] = close_price

    insert_query = """
        INSERT INTO stock_price_data (symbol, date, close_price)
        VALUES (%s, %s, %s)
    """
    cursor.execute(insert_query, (symbol, today_date, close_price))
    conn.commit()
    print(f"Inserted {symbol} closing price: {close_price}")

output_folder = "final_data"
os.makedirs(output_folder, exist_ok=True)
output_file = os.path.join(output_folder, f"apple_close_price_only_{today_date}.csv")
pd.DataFrame([{"symbol": k, "close_price": v} for k, v in price_data.items()]).to_csv(output_file, index=False)

print(f"\n Saved today's stock close prices to {output_file}")

# Close DB 
cursor.close()
conn.close()