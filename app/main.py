from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import numpy as np
import boto3
import os
import botocore.exceptions

app = FastAPI(title="Stock Sentiment Predictor API")

# S3 bucket details
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

class StockSentimentRequest(BaseModel):
    vader_score: float
    finbert_sentiment: int
    day_of_week: int
    sentiment_agreement: int
    news_length: int

@app.post("/predict")
def predict_sentiment(data: StockSentimentRequest):
    """Make a stock price prediction."""
    features = np.array([
        [
            data.vader_score,
            data.finbert_sentiment,
            data.day_of_week,
            data.sentiment_agreement,
            data.news_length
        ]
    ])

    prediction = model.predict(features)[0]

    return {
        "prediction": int(prediction),
        "meaning": "Price Up" if prediction == 1 else "Price Down"
    }
