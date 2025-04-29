import mysql.connector
from datetime import datetime, timedelta
import pytz

# Setup timezone
eastern = pytz.timezone("US/Eastern")
today = datetime.now(eastern).date()
yesterday = today - timedelta(days=1)

# Connect to MySQL
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root1234',
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
    print("⚠️ Missing stock price data for one of the days.")
    cursor.close()
    conn.close()
    exit()

# Determine actual movement
prev_close = prev_row[0]
today_close = today_row[0]
actual_label = int(today_close > prev_close)

correct = sum(1 for pred in predictions if pred == actual_label)
total = len(predictions)
accuracy = correct / total

# Insert accuracy log
cursor.execute("""
    INSERT INTO prediction_accuracy_log 
    (prediction_date, accuracy, total_predictions, correct_predictions)
    VALUES (%s, %s, %s, %s)
""", (yesterday, accuracy, total, correct))
conn.commit()

print(f"✅ Accuracy for {yesterday}: {accuracy*100:.2f}% ({correct}/{total} correct)")

cursor.close()
conn.close()
