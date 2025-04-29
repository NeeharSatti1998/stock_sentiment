# Apple Stock Sentiment Prediction 

This project builds a full pipeline that predicts whether Apple's stock price will go UP or DOWN based on financial news sentiment.  
It combines live web scraping, sentiment analysis (VADER and FinBERT), XGBoost classification, MySQL database storage, and a Streamlit dashboard.

---

 Dataset Source:

- Kaggle Dataset:  
  https://www.kaggle.com/datasets/frankossai/apple-stock-aapl-historical-financial-news-data

- Real-time news scraped using Yahoo Finance API via:
  - pipeline/apple_news_scraper.py
  - pipeline/apple_scraped_sentiment.py
  - pipeline/apple_scraped_stocks.py

---

 Model Used:

- XGBoost Classifier
- Features for prediction:
  - VADER sentiment score (compound score)
  - FinBERT sentiment label (mapped: Positive → 1, Neutral → 0, Negative → -1)
  - Day of the week (0–6)
  - Sentiment Agreement (whether VADER and FinBERT agree)
  - Length of news headline

- Trained model saved as:  
  app/apple_stock_sentiment_model.pkl
- Model also uploaded to AWS S3 for automatic loading on EC2 instances.

---

<pre> ## Project Structure ```text stock_sentiment/ ├── app/ │ ├── main.py # FastAPI app for model API │ └── apple_stock_sentiment_model.pkl # Trained XGBoost model ├── pipeline/ │ ├── apple_news_scraper.py # Scrape latest Apple news │ ├── apple_scraped_sentiment.py # Sentiment analysis & prediction │ ├── apple_scraped_stocks.py # Store daily close price │ └── prediction_checker.py # Compare yesterday’s predictions ├── final_data/ # Final labeled price+sentiment ├── processed_data/ # Sentiment-tagged news ├── scraped_data/ # Raw scraped headlines ├── requirements.txt # Python dependencies └── README.md # Project documentation ``` </pre>

 How to Run the Pipeline Locally:

1. Install dependencies:
   pip install -r requirements.txt

2. Scrape Apple news:
   python pipeline/apple_news_scraper.py

3. Perform Sentiment Analysis and Predictions:
   python pipeline/apple_scraped_sentiment.py

4. Fetch Stock Close Price:
   python pipeline/apple_scraped_stocks.py

5. (Optional) Check Previous Predictions:
   python pipeline/prediction_checker.py

---

 Run the Streamlit Dashboard:

- Visualize and manually test news impact on stock predictions:
  
  streamlit run streamlit_app.py

---

 Run the FastAPI Backend:

- To serve real-time predictions through an API:

  uvicorn app.main:app --reload

---

 Database Setup:

- Database Name: apple_stock_sentiment
- Two Tables:
  - prediction_data:  
    - Stores every news article's prediction.
  - stock_price_data:  
    - Stores Apple's daily closing prices.

---

 Automation Plan (EC2):

- Entire pipeline will be scheduled on AWS EC2 instance using cron jobs:
  - 7:00 PM EST → Scrape today's news + predict and save.
  - 4:30 PM next day → Scrape actual closing price, compare it with prediction.

- No manual intervention needed after deployment.

---

 Prediction Evaluation Logic:

- Every day multiple news items exist.
- If most of the predictions for that day = 1 → Predict "Price Up".
- If most = 0 → Predict "Price Down".

- The model is evaluated daily using the prediction_checker.py script by comparing against real closing price change.

---


