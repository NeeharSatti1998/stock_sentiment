import pandas as pd
import re
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from transformers import pipeline

# Uncomment if running for the first time
# nltk.download('vader_lexicon')

df = pd.read_csv("data/apple_clean_data.csv", encoding="utf-8")

# Clean title text
def clean_text(text):
    text = text.encode("ascii", "ignore").decode()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-zA-Z0-9\s.,!?]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

df['title'] = df['title'].apply(clean_text)

# Initialize sentiment analyzers
vader = SentimentIntensityAnalyzer()
finbert = pipeline("sentiment-analysis", model="yiyanghkust/finbert-tone")  # CPU only

# VADER Sentiment
def get_vader_sentiment(text):
    score = vader.polarity_scores(text)['compound']
    if score >= 0.05:
        return 'positive'
    elif score <= -0.05:
        return 'negative'
    else:
        return 'neutral'

df["vader_sentiment"] = df["title"].apply(get_vader_sentiment)

# FinBERT Sentiment (batched)
batch_size = 16
finbert_results = []

for i in range(0, len(df), batch_size):
    batch = df['title'].iloc[i:i+batch_size].tolist()
    preds = finbert(batch)
    finbert_results.extend([x['label'].lower() for x in preds])

df["finbert_sentiment"] = finbert_results

# Save output
df.to_csv("apple_sentiment_data.csv", index=False)
print("Saved to apple_sentiment_data.csv")
print(df[['title', 'vader_sentiment', 'finbert_sentiment']].head())
