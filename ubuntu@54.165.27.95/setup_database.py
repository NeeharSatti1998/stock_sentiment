import sqlite3


def create_database():
    conn = sqlite3.connect("stock_sentiment.db")
    cursor = conn.cursor()

    # Create table for news + prediction
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS news_sentiment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_scraped TEXT,
        vader_score REAL,
        finbert_sentiment INTEGER,
        day_of_week INTEGER,
        sentiment_agreement INTEGER,
        news_length INTEGER,
        model_prediction INTEGER
    )
    ''')

    # Create table for actual stock prices
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stock_prices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_scraped TEXT,
        stock_close REAL
    )
    ''')

    # Create table for prediction vs actual
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS prediction_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prediction_date TEXT,
        model_prediction INTEGER,
        real_movement INTEGER,
        correct_or_not INTEGER
    )
    ''')

    conn.commit()
    conn.close()
    print("Database and tables created successfully!")

if __name__ == "__main__":
    create_database()