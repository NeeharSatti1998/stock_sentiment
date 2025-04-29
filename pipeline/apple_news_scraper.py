import requests
import pandas as pd
from datetime import datetime
import os

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
    today = datetime.now()

    for item in data.get("news", []):
        title = item.get("title")
        link = item.get("link")
        provider = item.get("publisher")

        scraped_at = today.isoformat()

        news_list.append({
            "symbol": "AAPL",
            "title": title,
            "link": link,
            "provider": provider,
            "scraped_at": scraped_at
        })

    return news_list


def save_news_to_csv(news_list):
    today_str = datetime.now().strftime("%Y-%m-%d")
    folder = "scraped_data"
    os.makedirs(folder, exist_ok=True)  
    filename = os.path.join(folder, f"apple_news_scraped_{today_str}.csv")

    df = pd.DataFrame(news_list)
    df.to_csv(filename, index=False)
    print(f"Saved scraped news to {filename}")
    print(df[['symbol', 'title', 'scraped_at']].head())

if __name__ == "__main__":
    print("Scraping Apple news...")
    apple_news = get_apple_news()
    if apple_news:
        save_news_to_csv(apple_news)
    else:
        print("No news found or scraping failed.")
