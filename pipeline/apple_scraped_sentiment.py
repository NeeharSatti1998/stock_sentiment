import pandas as pd
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from transformers import pipeline
import re
from datetime import datetime
import os

vader = SentimentIntensityAnalyzer()
finbert = pipeline("sentiment-analysis", model="yiyanghkust/finbert-tone")

# Data cleaning
def clean_text(text):
    text = str(text)
    text = text.encode("ascii", "ignore").decode()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-zA-Z0-9\s.,!?]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# VADER sentiment
def get_vader_sentiment(text):
    score = vader.polarity_scores(text)['compound']
    if score >= 0.05:
        return 'positive'
    elif score <= -0.05:
        return 'negative'
    else:
        return 'neutral'

# FinBERT sentiment
def get_finbert_sentiment(text):
    result = finbert(text[:512])[0]
    return result['label'].lower()

# Sentiment tagging process
def sentiment_tagging(input_csv):
    df = pd.read_csv(input_csv)

    df['title'] = df['title'].apply(clean_text)
    df['vader_sentiment'] = df['title'].apply(get_vader_sentiment)
    df['finbert_sentiment'] = df['title'].apply(get_finbert_sentiment)

    today_str = datetime.utcnow().strftime("%Y-%m-%d")

    output_folder = "processed_data"
    os.makedirs(output_folder, exist_ok=True)

    output_filename = os.path.join(output_folder, f"apple_news_with_sentiment_{today_str}.csv")

    df.to_csv(output_filename, index=False)
    print(f"Saved sentiment-tagged data to {output_filename}")
    print(df[['symbol', 'title', 'vader_sentiment', 'finbert_sentiment']].head())

if __name__ == "__main__":
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    input_file = f"scraped_data/apple_news_scraped_{today_str}.csv"

    print(f"Processing sentiment for {input_file}...")
    sentiment_tagging(input_file)
