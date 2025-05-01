import streamlit as st
import requests
import yfinance as yf
from datetime import datetime, timedelta
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from transformers import pipeline
import re
import plotly.express as px
import pandas as pd
import mysql.connector

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


db_config = {
    'host': 'apple-stock-sentiment-db.cobaiu8aw8xi.us-east-1.rds.amazonaws.com',
    'user': 'admin',
    'password': 'SanthiKesava99',
    'database': 'apple_stock_sentiment'
}

st.header("Today's Market Sentiment Based on News")

try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    today_str = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT prediction FROM prediction_data WHERE DATE(scraped_at) = %s", (today_str,))
    results = cursor.fetchall()
    conn.close()

    predictions = [row['prediction'] for row in results]

    if predictions:
        final_vote = 1 if predictions.count(1) > predictions.count(0) else 0
        st.subheader("Final Predicted Movement for Apple Stock (Tomorrow):")
        if final_vote == 1:
            st.success("Prediction: **Price will likely go UP**")
        else:
            st.error("Prediction: **Price will likely go DOWN**")
    else:
        st.warning("No predictions available today. (Maybe pipeline hasn't run yet?)")

except Exception as e:
    st.warning(f"Error processing today's prediction from DB: {e}")

st.header(" Daily Prediction Accuracy")

try:
    db_config = {
        'host': 'apple-stock-sentiment-db.cobaiu8aw8xi.us-east-1.rds.amazonaws.com',
        'user': 'admin',
        'password': 'SanthiKesava99',
        'database': 'apple_stock_sentiment'
    }

    import mysql.connector
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT prediction_date, accuracy, total_predictions, correct_predictions
        FROM prediction_accuracy_log
        ORDER BY prediction_date DESC
        LIMIT 1
    """)
    row = cursor.fetchone()

    if row:
        pred_date, accuracy, total, correct = row

        # Fetch actual label and model label from predictions
        cursor.execute("""
            SELECT close_price FROM stock_price_data
            WHERE symbol = 'AAPL' AND date = %s
        """, (pred_date,))
        prev_price = cursor.fetchone()[0]

        cursor.execute("""
            SELECT close_price FROM stock_price_data
            WHERE symbol = 'AAPL' AND date = %s
        """, (pred_date + timedelta(days=1),))
        next_price = cursor.fetchone()[0]

        actual_movement = "UP" if next_price > prev_price else "DOWN"

        cursor.execute("""
            SELECT prediction FROM prediction_data
            WHERE DATE(scraped_at) = %s
        """, (pred_date,))
        model_preds = [r[0] for r in cursor.fetchall()]
        model_final = "UP" if model_preds.count(1) > model_preds.count(0) else "DOWN"

        is_correct = " Model Prediction was CORRECT!" if model_final == actual_movement else " Model Prediction was WRONG"

        st.markdown(f"""
        **Prediction Date:** {pred_date}  
        **Actual Market Movement:** {actual_movement}  
        **Model Prediction:** {model_final}  
        **Accuracy:** {accuracy*100:.2f}% ({correct}/{total})  
        **Result:** {is_correct}
        """)

    else:
        st.warning("No prediction accuracy data found.")

    cursor.close()
    conn.close()

except Exception as e:
    st.error(f"Error loading prediction accuracy data: {e}")
