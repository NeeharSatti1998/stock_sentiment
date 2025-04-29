import streamlit as st
import requests
import yfinance as yf
from datetime import datetime, timedelta
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from transformers import pipeline
import re
import plotly.express as px
import pandas as pd

# FastAPI endpoint
API_URL = "http://localhost:8000/predict"

st.set_page_config(page_title="Apple Stock Sentiment Dashboard", layout="wide")

st.title("Apple Stock Sentiment Dashboard")

vader = SentimentIntensityAnalyzer()
finbert = pipeline("sentiment-analysis", model="yiyanghkust/finbert-tone")

def clean_text(text):
    text = str(text)
    text = text.encode("ascii", "ignore").decode()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-zA-Z0-9\s.,!?]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def prepare_features(news_text):
    news_text = clean_text(news_text)
    vader_score = vader.polarity_scores(news_text)["compound"]
    finbert_result = finbert(news_text[:512])[0]['label'].lower()

    sentiment_map = {"positive": 1, "neutral": 0, "negative": -1}
    finbert_sentiment = sentiment_map.get(finbert_result, 0)
    news_length = len(news_text)
    day_of_week = datetime.now().weekday()
    sentiment_agreement = int(
        (vader_score >= 0.05 and finbert_sentiment == 1) or
        (vader_score <= -0.05 and finbert_sentiment == -1) or
        (abs(vader_score) < 0.05 and finbert_sentiment == 0)
    )
    
    return {
        "vader_score": vader_score,
        "finbert_sentiment": finbert_sentiment,
        "day_of_week": day_of_week,
        "sentiment_agreement": sentiment_agreement,
        "news_length": news_length
    }

# News
st.header(" Predict Stock Movement from News")

news_input = st.text_area("Paste a News Headline Here:", "")

if st.button("Predict from News"):
    if news_input.strip() == "":
        st.warning("Please paste some news text.")
    else:
        features = prepare_features(news_input)
        response = requests.post(API_URL, json=features)

        if response.status_code == 200:
            prediction = response.json()
            st.success(f" Prediction: **{prediction['meaning']}**")
        else:
            st.error("Prediction failed. Please try again.")


# Dashboard
st.header("Apple Stock live")

today = datetime.now().date()

try:
    stock_data = yf.download('AAPL', start=today, end=today + timedelta(days=1), interval='5m', progress=False)

    if not stock_data.empty:
        # Flatten multi-index columns if necessary
        if isinstance(stock_data.columns, pd.MultiIndex):
            stock_data.columns = stock_data.columns.get_level_values(0)

        # Reset index
        stock_data = stock_data.reset_index()

        # Round numeric columns for cleaner display
        numeric_cols = ['Open', 'High', 'Low', 'Close']
        stock_data[numeric_cols] = stock_data[numeric_cols].round(2)

        # Plot closing price
        fig = px.line(
            stock_data,
            x='Datetime',
            y='Close',
            title=' Apple Stock Price',
            labels={'Datetime': 'Time', 'Close': 'Price (USD)'},
            template='plotly_white'
        )
        fig.update_layout(title_x=0.5)

        st.plotly_chart(fig, use_container_width=True)

        # Show data table
        st.subheader(" Intraday Stock Data")
        st.dataframe(stock_data[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']])

        st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    else:
        st.warning(" No intraday stock data available. Market might be closed.")

except Exception as e:
    st.error(f"Error fetching stock data: {e}")


st.header("📈 Today's Market Sentiment Based on News")

try:
    today_file = f"processed_data/apple_news_with_sentiment_{today}.csv"
    df_sentiment = pd.read_csv(today_file)

    # Prepare features for model
    features_list = []
    for _, row in df_sentiment.iterrows():
        vader_score = vader.polarity_scores(row['title'])['compound']
        finbert_map = {"positive": 1, "neutral": 0, "negative": -1}
        finbert_sentiment = finbert_map.get(row['finbert_sentiment'], 0)
        day_of_week = pd.to_datetime(row['scraped_at']).weekday()
        sentiment_agreement = int((row['vader_sentiment'] == row['finbert_sentiment']))
        news_length = len(row['title'])

        features_list.append([
            vader_score,
            finbert_sentiment,
            day_of_week,
            sentiment_agreement,
            news_length
        ])

    # Predict for all news
    predictions = []
    for features in features_list:
        payload = {
            "vader_score": features[0],
            "finbert_sentiment": features[1],
            "day_of_week": features[2],
            "sentiment_agreement": features[3],
            "news_length": features[4],
        }
        response = requests.post(API_URL, json=payload)
        if response.status_code == 200:
            pred = response.json()['prediction']
            predictions.append(pred)

    # Majority Vote
    if predictions:
        final_vote = 1 if predictions.count(1) > predictions.count(0) else 0
        st.subheader("📢 Final Predicted Movement for Apple Stock (Tomorrow):")
        if final_vote == 1:
            st.success("Prediction: 📈 **Price will likely go UP**")
        else:
            st.error("Prediction: 📉 **Price will likely go DOWN**")
    else:
        st.warning("No predictions available today. (Maybe news not scraped yet?)")

except Exception as e:
    st.warning(f"Error processing today's news sentiment: {e}")