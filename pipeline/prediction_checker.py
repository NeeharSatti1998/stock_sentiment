import mysql.connector
from datetime import datetime, timedelta
import pytz

# Setup timezone
eastern = pytz.timezone("US/Eastern")
#today = datetime.now(eastern).date()
#testing
today = datetime(2025, 4, 29).date()
yesterday = today - timedelta(days=1)

# Connect to MySQL
db_config = {
    'host': 'apple-stock-sentiment-db.cobaiu8aw8xi.us-east-1.rds.amazonaws.com',
    'user': 'admin',
    'password': 'SanthiKesava99',
    'database': 'apple_stock_sentiment'
}
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# Create log table if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS prediction_accuracy_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    prediction_date DATE,
    accuracy FLOAT,
    total_predictions INT,
    correct_predictions INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")


# Fetch predictions made on yesterday's news
cursor.execute("""
    SELECT prediction FROM prediction_data
    WHERE DATE(scraped_at) = %s
""", (yesterday,))
predictions = [row[0] for row in cursor.fetchall()]

if not predictions:
    print("No predictions found for yesterday.")
    cursor.close()
    conn.close()
    exit()

# Fetch closing prices for yesterday and today
cursor.execute("""
    SELECT close_price FROM stock_price_data
    WHERE symbol = 'AAPL' AND date = %s
""", (yesterday,))
prev_row = cursor.fetchone()

cursor.execute("""
    SELECT close_price FROM stock_price_data
    WHERE symbol = 'AAPL' AND date = %s
""", (today,))
today_row = cursor.fetchone()

if not prev_row or not today_row:
    print("Missing stock price data for one of the days.")
    cursor.close()
    conn.close()
    exit()

# Determine actual market movement
prev_close = prev_row[0]
today_close = today_row[0]
actual_label = int(today_close > prev_close)

# Compare predictions to actual movement
correct = sum(1 for pred in predictions if pred == actual_label)
total = len(predictions)
accuracy = correct / total

# Store results in DB
cursor.execute("""
    INSERT INTO prediction_accuracy_log 
    (prediction_date, accuracy, total_predictions, correct_predictions)
    VALUES (%s, %s, %s, %s)
""", (yesterday, accuracy, total, correct))
conn.commit()

print(f"Accuracy for {yesterday}: {accuracy*100:.2f}% ({correct}/{total} correct)")

cursor.close()
conn.close()
