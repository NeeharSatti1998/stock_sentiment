#!/bin/bash

# Activate your virtual environment
source ~/stock_sentiment/venv/bin/activate

# Run the full pipeline step by step
echo ">>> Running apple_news_scraper.py..."
python3 ~/stock_sentiment/pipeline/apple_news_scraper.py

echo ">>> Running apple_scraped_sentiment.py..."
python3 ~/stock_sentiment/pipeline/apple_scraped_sentiment.py

echo ">>> Running apple_scraped_stocks.py..."
python3 ~/stock_sentiment/pipeline/apple_scraped_stocks.py

echo ">>> Running prediction_checker.py..."
python3 ~/stock_sentiment/pipeline/prediction_checker.py
