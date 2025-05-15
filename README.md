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
- Trained model is stored in AWS S3 (`apple_stock_sentiment_model.pkl`) and automatically downloaded by the EC2 instance on each run.

---
## Project Structure


<p>stock_sentiment/<br>
├── app/<br>
│   ├── main.py                        # FastAPI app for model API<br>
│   └── apple_stock_sentiment_model.pkl  # Trained XGBoost model<br>
├── pipeline/<br>
│   ├── apple_news_scraper.py         # Scrape latest Apple news<br>
│   ├── apple_scraped_sentiment.py    # Sentiment analysis & prediction<br>
│   ├── apple_scraped_stocks.py       # Store daily close price<br>
│   └── prediction_checker.py         # Compare yesterday’s predictions<br>
├── final_data/                       # Final labeled price+sentiment<br>
├── processed_data/                   # Sentiment-tagged news<br>
├── scraped_data/                     # Raw scraped headlines<br>
├── requirements.txt                  # Python dependencies<br>
└── README.md                         # Project documentation<br>

<p>
---



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

- Visualizes daily sentiment predictions and accuracy directly from the MySQL database.

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
- Storing the data in AWS RDS database
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


