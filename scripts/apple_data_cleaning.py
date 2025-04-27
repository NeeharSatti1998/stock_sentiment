import pandas as pd
import re

df = pd.read_csv("data/apple_news_data.csv")

# Remove duplicates and missing rows
df = df.drop_duplicates()
df = df.dropna(subset=["title", "date"])

# Convert date to datetime format
df["published_date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["published_date"])

# Clean the title text
def clean_title(text):
    text = str(text)
    text = text.encode("ascii", "ignore").decode()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-zA-Z0-9\s.,!?]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

df["clean_title"] = df["title"].apply(clean_title)
df = df.drop(columns=["title"])


df = df.rename(columns={"date": "scraped_at", "clean_title": "title"})
df = df[["scraped_at", "title"]]  # keep only relevant columns
df = df.reset_index(drop=True)


df.to_csv("apple_clean_data.csv", index=False)
print("File saved as apple_clean_data.csv — ready for sentiment analysis")
