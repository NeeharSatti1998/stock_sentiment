from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import numpy as np

app = FastAPI(title="Stock Sentiment Predictor API")

model = joblib.load('app/apple_stock_sentiment_model.pkl')

class StockSentimentRequest(BaseModel):
    vader_score: float
    finbert_sentiment: int
    day_of_week: int
    sentiment_agreement: int
    news_length: int

@app.post("/predict")
def predict_sentiment(data: StockSentimentRequest):
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
        "prediction": int(prediction),  # 0 = Price Down, 1 = Price Up
        "meaning": "Price Up" if prediction == 1 else "Price Down"
    }