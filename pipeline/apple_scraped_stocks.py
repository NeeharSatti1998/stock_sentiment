import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import os
import glob
import pytz
import mysql.connector

db_config = {
    'host': 'apple-stock-sentiment-db.cobaiu8aw8xi.us-east-1.rds.amazonaws.com',
    'user': 'admin',
    'password': 'SanthiKesava99',
    'database': 'apple_stock_sentiment'
}
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()


# Get today's date in Eastern Time
eastern = pytz.timezone('US/Eastern')
#today_date = datetime.now(eastern).date()
#testing

today_date = datetime(2025, 4, 29).date()


# Define symbol(s) to track
symbols = ['AAPL']  # You can extend this if needed

for symbol in symbols:
    print(f"Fetching {symbol} closing price for {today_date}...")
    data = yf.download(symbol, start=today_date, end=today_date + timedelta(days=1))
    
    if data.empty:
        print(f"No data found for {symbol} on {today_date}. Market might be closed.")
        continue

    close_price = float(data['Close'].values[0])
    
    insert_query = """
        INSERT INTO stock_price_data (symbol, date, close_price)
        VALUES (%s, %s, %s)
    """
    cursor.execute(insert_query, (symbol, today_date, close_price))
    conn.commit()
    print(f"Inserted {symbol} closing price into DB: {close_price}")

# Close connection
cursor.close()
conn.close()