import requests
import pandas as pd
from datetime import datetime
import mysql.connector
import pytz
import os

password = os.getenv("RDS_DB_PASSWORD")

# RDS Connection
conn = mysql.connector.connect(
    host="apple-stock-sentiment-db.cobaiu8aw8xi.us-east-1.rds.amazonaws.com",
    user="admin",
    password="password",
    database="apple_stock_sentiment",
    ssl_disabled=True
)
cursor = conn.cursor()

# Create table if it doesn't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS scraped_news (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(10),
    title TEXT,
    link TEXT,
    provider TEXT,
    scraped_at DATETIME
)
""")

def get_apple_news():
    url = "https://query1.finance.yahoo.com/v1/finance/search?q=AAPL"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []

    news_list = []
    eastern = pytz.timezone("US/Eastern")
    #scraped_at = datetime.now(tz=pytz.utc).astimezone(eastern)
    #Testing
    scraped_at = eastern.localize(datetime(2025, 4, 28, 20, 22, 11))


    for item in data.get("news", []):
        news_list.append({
            "symbol": "AAPL",
            "title": item.get("title"),
            "link": item.get("link"),
            "provider": item.get("publisher"),
            "scraped_at": scraped_at
        })

    return news_list

def insert_to_db(news_list):
    for news in news_list:
        cursor.execute("""
            INSERT INTO scraped_news (symbol, title, link, provider, scraped_at)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            news['symbol'],
            news['title'],
            news['link'],
            news['provider'],
            news['scraped_at']
        ))
    conn.commit()
    print("Scraped news inserted into database.")

if __name__ == "__main__":
    print("Scraping Apple news...")
    news_data = get_apple_news()
    if news_data:
        insert_to_db(news_data)
    else:
        print("No news found or scraping failed.")

# Close connections
cursor.close()
conn.close()
