# app/etl_news.py
import time, requests
import pandas as pd
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from sqlalchemy.exc import IntegrityError
from .settings import MARKETAUX, STOCKS
from .db import SessionLocal
from .models import News

"""
This is the ETL (Extract Transform and Load) pipline
for news and loads into the news table
VADER: it's a sentiment analysis tool that measures whether
a piece of text is positive, negative, neutral, or a mix
"""

# Make sure VADER (Valence Aware Dictionary and sEntiment Reasoner) is available
try:
    nltk.data.find("sentiment/vader_lexicon.zip") # Lexicon = Dictionary
except LookupError:
    nltk.download("vader_lexicon", quiet=True)

sia = SentimentIntensityAnalyzer()

URL = "https://api.marketaux.com/v1/news/all"

def fetch_news(stock: str, limit=20) -> pd.DataFrame:
    """
    Pull recent news for one stock (headline-level).
    """
    params = {
        "symbols": stock,
        "filter_entities": "true",
        "language": "en",
        "api_token": MARKETAUX,
        "limit": limit,
    }
    r = get_with_backoff(URL, params=params)
    payload = r.json()
    items = payload.get("data", [])
    rows = []
    for a in items:
        title = a.get("title") or ""
        rows.append({
            "stock": stock,
            "published_at": a.get("published_at"),  # ISO string
            "title": title,
            "url": a.get("url"),
            "source": a.get("source"),
            "sentiment": sia.polarity_scores(title)["compound"],
            "raw": a,
        })
    return pd.DataFrame(rows)

def load_news(df: pd.DataFrame) -> int:
    """
    Insert-only loader (deduped via unique constraint).
    Returns number of inserted rows.
    """
    if df.empty:
        return 0
    inserted = 0
    with SessionLocal() as s:
        for _, row in df.iterrows():
            try:
                s.add(News(**row.to_dict()))
                s.commit()
                inserted += 1
            except IntegrityError:
                s.rollback()  # duplicate, skip
    return inserted

def run_all(stocks=None, per_stock_limit=20, pause_sec=2):
    stocks = stocks or STOCKS
    total = 0
    for i, st in enumerate(stocks, start=1):
        df = fetch_news(st, limit=per_stock_limit)
        ins = load_news(df)
        print(f"{st}: +{ins} news rows")
        total += ins
        if i < len(stocks):
            time.sleep(pause_sec)
    print(f"Done. Inserted {total} total news rows.")

def get_with_backoff(url, params, retries=3, pause=20):
    for i in range(retries):
        r = requests.get(url, params=params, timeout=30)
        if r.status_code == 200 and "Note" not in r.text:
            return r
        time.sleep(pause * (i+1))
    raise RuntimeError("API unavailable or rate-limited")


if __name__ == "__main__":
    run_all()
