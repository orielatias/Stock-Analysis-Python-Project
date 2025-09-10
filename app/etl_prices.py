# app/etl_prices.py
import time, requests
from datetime import datetime
import pandas as pd
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from .settings import ALPHA, STOCKS
from .db import SessionLocal
from .models import Price

"""
This ETL (Extract - Transform - Load) file loads the daily
stock prices into the prices table in the SQL database
"""

AV_URL = "https://www.alphavantage.co/query"
def fetch_prices_daily(stock: str) -> pd.DataFrame:
    """
    Pull compact daily time series (free endpoint) for one stock.
    """
    params = {
        "function": "TIME_SERIES_DAILY",   # <-- free endpoint
        "symbol": stock,
        "outputsize": "compact",
        "apikey": ALPHA
    }
    r = get_with_backoff(AV_URL, params=params)
    j = r.json() # Converts response from json to python dict object

    # Handle common AV messages
    if "Error Message" in j:
        raise ValueError(f"Alpha Vantage error for {stock}: {j['Error Message']}")
    if "Note" in j:
        raise ValueError(f"Alpha Vantage rate limit/notice for {stock}: {j['Note']}")
    if "Information" in j:
        raise ValueError(f"Alpha Vantage info for {stock}: {j['Information']}")

    # Find the key like "Time Series (Daily)" or "Time Series (Daily Adjusted)")
    # in the API response, else raise an error
    key = next((k for k in j.keys() if "Time Series" in k), None)
    if key is None:
        raise ValueError(f"Unexpected response for {stock}: {j}")

    df = pd.DataFrame(j[key]).T
    df.index = pd.to_datetime(df.index)

    # Map columns for either DAILY or DAILY_ADJUSTED shape
    cols = {c.lower(): c for c in df.columns}  # normalize
    # Both endpoints have open/high/low/close; volume could be "5. volume" or "6. volume"
    open_c  = cols.get("1. open",  None)
    high_c  = cols.get("2. high",  None)
    low_c   = cols.get("3. low",   None)
    close_c = cols.get("4. close", None)
    vol_c   = cols.get("5. volume", cols.get("6. volume", None))

    if not all([open_c, high_c, low_c, close_c, vol_c]):
        raise ValueError(f"Missing columns in AV payload for {stock}: {list(df.columns)}")

    df = df.rename(columns={
        open_c: "open",
        high_c: "high",
        low_c: "low",
        close_c: "close",
        vol_c: "volume",
    })[["open", "high", "low", "close", "volume"]].astype(float)

    df["stock"] = stock
    df["date"] = df.index.date
    return df.reset_index(drop=True)

def load_prices(df: pd.DataFrame) -> int:
    """
    Upsert-like loader: inserts rows that don't exist yet.
    Returns number of inserted rows.
    """
    inserted = 0
    with SessionLocal() as s:
        for _, row in df.iterrows():
            # Unique by (stock, date)
            exists = s.execute(
                select(Price).where(Price.stock == row.stock, Price.date == row.date)
            ).scalar_one_or_none()
            if exists:
                continue
            s.add(Price(
                stock=row.stock,
                date=row.date,
                open=row.open,
                high=row.high,
                low=row.low,
                close=row.close,
                volume=row.volume,
            ))
            try:
                s.commit()
                inserted += 1
            except IntegrityError:
                s.rollback()
    return inserted

def run_all(stocks=None):
    stocks = stocks or STOCKS
    total = 0
    for i, s in enumerate(stocks, start=1):
        df = fetch_prices_daily(s)
        inserted = load_prices(df)
        print(f"{s}: +{inserted} rows")
        total += inserted
        # Be gentle with the free tier rate limit
        if i < len(stocks):
            time.sleep(12)
    print(f"Done. Inserted {total} total rows.")

def get_with_backoff(url, params, retries=3, pause=20):
    for i in range(retries):
        r = requests.get(url, params=params, timeout=30)
        if r.status_code == 200 and "Note" not in r.text:
            return r
        time.sleep(pause * (i+1))
    raise RuntimeError("API unavailable or rate-limited")

if __name__ == "__main__":
    run_all()
