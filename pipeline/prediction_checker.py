import mysql.connector
from datetime import datetime, timedelta
import pytz

# Setup timezone
eastern = pytz.timezone("US/Eastern")
today = datetime.now(eastern).date()

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

# Actual movement
prev_close = prev_row[0]
today_close = today_row[0]
actual_movement = 1 if today_close > prev_close else 0

# Model majority prediction
num_ones = predictions.count(1)
num_zeros = predictions.count(0)
model_majority = 1 if num_ones > num_zeros else 0

# Accuracy count (classic way)
correct = sum(1 for pred in predictions if pred == actual_movement)
total = len(predictions)
accuracy = correct / total

# Insert into accuracy log
cursor.execute("""
    INSERT INTO prediction_accuracy_log 
    (prediction_date, accuracy, total_predictions, correct_predictions)
    VALUES (%s, %s, %s, %s)
""", (yesterday, accuracy, total, correct))
conn.commit()

# Print summary
print(f"\nYesterday's closing price: {prev_close}")
print(f"Today's closing price: {today_close}")
print(f"Actual stock movement: {'UP' if actual_movement == 1 else 'DOWN'}")
print(f"Model majority prediction: {'UP' if model_majority == 1 else 'DOWN'}")

if model_majority == actual_movement:
    print("The model was RIGHT.")
else:
    print("The model was WRONG.")

cursor.close()
conn.close()
