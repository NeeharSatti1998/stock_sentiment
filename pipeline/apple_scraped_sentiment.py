import pandas as pd
import joblib
from transformers import pipeline
import re
from datetime import datetime
import os
import mysql.connector
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import boto3
import botocore.exceptions

# Load Sentiment Models
vader = SentimentIntensityAnalyzer()
finbert = pipeline("sentiment-analysis", model="yiyanghkust/finbert-tone")

S3_BUCKET_NAME = "apple-stock-sentiment-model" 
S3_MODEL_KEY = "apple_stock_sentiment_model.pkl" 
LOCAL_MODEL_PATH = "app/apple_stock_sentiment_model.pkl"

def download_model_from_s3():
    try:
        s3 = boto3.client('s3')

        if os.path.exists(LOCAL_MODEL_PATH):
            print("Local model already exists. Skipping download...")
        else:
            print("Downloading model from S3...")
            os.makedirs(os.path.dirname(LOCAL_MODEL_PATH), exist_ok=True)
            s3.download_file(S3_BUCKET_NAME, S3_MODEL_KEY, LOCAL_MODEL_PATH)
            print("Model downloaded successfully!")

    except botocore.exceptions.ClientError as e:
        print(f"Error downloading model: {e}")

download_model_from_s3()

# Load the model
model = joblib.load(LOCAL_MODEL_PATH)

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

# Get VADER score (for feature)
def get_vader_score(text):
    return vader.polarity_scores(text)['compound']

# Insert into database
def insert_into_db(df):
    conn = mysql.connector.connect(
    host="localhost",
    user="root",           
    password="root1234",  
    database="apple_stock_sentiment"   
)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS prediction_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        scraped_at TEXT,
        title TEXT,
        vader_score REAL,
        finbert_sentiment INTEGER,
        day_of_week INTEGER,
        sentiment_agreement INTEGER,
        news_length INTEGER,
        prediction INTEGER
    )
    """)

    for _, row in df.iterrows():
        cursor.execute("""
        INSERT INTO prediction_data 
        (scraped_at, title, vader_score, finbert_sentiment, day_of_week, sentiment_agreement, news_length, prediction)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            row['scraped_at'],
            row['title'],
            row['vader_score'],
            row['finbert_sentiment'],
            row['day_of_week'],
            row['sentiment_agreement'],
            row['news_length'],
            row['prediction']
        ))

    conn.commit()
    conn.close()
    print("Data inserted into prediction_data table.")

# Full pipeline
def sentiment_tagging_and_prediction(input_csv):
    df = pd.read_csv(input_csv)

    df['title'] = df['title'].apply(clean_text)
    df['vader_sentiment'] = df['title'].apply(get_vader_sentiment)
    df['finbert_sentiment'] = df['title'].apply(get_finbert_sentiment)

    # Prepare features for prediction
    df['vader_score'] = df['title'].apply(get_vader_score)
    df['finbert_sentiment'] = df['finbert_sentiment'].map({"positive": 1, "neutral": 0, "negative": -1})
    df['day_of_week'] = pd.to_datetime(df['scraped_at']).dt.weekday
    df['sentiment_agreement'] = (df['vader_sentiment'] == df['finbert_sentiment']).astype(int)
    df['news_length'] = df['title'].apply(len)

    features = df[['vader_score', 'finbert_sentiment', 'day_of_week', 'sentiment_agreement', 'news_length']]
    df['prediction'] = model.predict(features)

    # Insert into DB
    insert_into_db(df)


    today_str = datetime.now().strftime("%Y-%m-%d")
    output_folder = "processed_data"
    os.makedirs(output_folder, exist_ok=True)
    output_filename = os.path.join(output_folder, f"apple_news_with_sentiment_{today_str}.csv")
    df.to_csv(output_filename, index=False)

    print(f"Saved sentiment-tagged and predicted data to {output_filename}")
    print(df[['title', 'vader_sentiment', 'finbert_sentiment', 'prediction']].head())

# Entry point
if __name__ == "__main__":
    today_str = datetime.now().strftime("%Y-%m-%d")
    input_file = f"scraped_data/apple_news_scraped_{today_str}.csv"

    print(f"Processing sentiment for {input_file}...")
    sentiment_tagging_and_prediction(input_file)
