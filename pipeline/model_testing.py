import pandas as pd
import numpy as np
import joblib
from datetime import datetime
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Load today's new data
today_str = datetime.now().strftime("%Y-%m-%d")
df = pd.read_csv(f"final_data/apple_final_data_{today_str}.csv")

# Preprocessing
df['vader_sentiment'] = df['vader_sentiment'].map({'positive': 1, 'neutral': 0, 'negative': -1})
df['finbert_sentiment'] = df['finbert_sentiment'].map({'positive': 1, 'neutral': 0, 'negative': -1})
df['day_of_week'] = pd.to_datetime(df['scraped_at']).dt.weekday
df['sentiment_agreement'] = (df['vader_sentiment'] == df['finbert_sentiment']).astype(int)
df['news_length'] = df['title'].astype(str).apply(len)

# Vader Score
vader = SentimentIntensityAnalyzer()
df['vader_score'] = df['title'].apply(lambda x: vader.polarity_scores(x)['compound'])


features = ['vader_score', 'finbert_sentiment', 'day_of_week', 'sentiment_agreement', 'news_length']
X_fresh = df[features]

# Load saved model
model = joblib.load("app/apple_stock_sentiment_model.pkl")   

# Predict
predictions = model.predict(X_fresh)

# Show predictions
df['predicted_label'] = predictions

print(df[['title', 'predicted_label','label']])
