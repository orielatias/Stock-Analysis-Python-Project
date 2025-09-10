# app/risk_engine.py
import pandas as pd
from sqlalchemy import select
from .db import SessionLocal
from .models import Price, News, RiskScore

"""
This file combines price and news data to compute daily stock risk scores.
Calculates volatility from prices and sentiment from news, then normalizes them.
Stores combined risk scores in the database for analysis and visualization.

"""

# Compute % daily returns from closing prices per stock
def _compute_daily_returns(prices: pd.DataFrame) -> pd.DataFrame:
    # Sort + compute percent change per stock
    prices = prices.sort_values(["stock", "date"]).copy()
    prices["ret"] = prices.groupby("stock")["close"].pct_change()
    return prices

# Compute 20-day rolling volatility (std of returns) per stock
def _compute_volatility(prices: pd.DataFrame, window=20) -> pd.DataFrame:
    """
    20-day rolling standard deviation (std) of daily returns per stock.
    Returns: stock, date, vol_20d
    """
    prices = _compute_daily_returns(prices).sort_values(["stock", "date"])

    vols = []
    for stock, g in prices.groupby("stock"):
        g = g.set_index("date").copy()
        vol_series = g["ret"].rolling(window).std()
        df = vol_series.reset_index()
        df["stock"] = stock
        df.rename(columns={"ret": "vol_20d"}, inplace=True)
        vols.append(df)

    return pd.concat(vols, ignore_index=True)  # stock, date, vol_20d

# Compute 7-day rolling average of news sentiment per stock
def _compute_news_sentiment(news: pd.DataFrame, window_days=7) -> pd.DataFrame:
    if news.empty:
        return pd.DataFrame(columns=["stock", "date", "news_sent_7d"])
    news = news.copy()
    news["date"] = pd.to_datetime(news["published_at"]).dt.date
    daily = (
        news.groupby(["stock", "date"])["sentiment"]
            .mean()
            .reset_index()
            .sort_values(["stock", "date"])
    )
    # Build continuous daily index per stock and 7d rolling mean
    frames = []
    for st, g in daily.groupby("stock"):
        idx = pd.date_range(g["date"].min(), g["date"].max(), freq="D").date
        s = g.set_index("date")["sentiment"].reindex(idx).rolling(window_days, min_periods=1).mean()
        frames.append(pd.DataFrame({"stock": st, "date": idx, "news_sent_7d": s.values}))
    return pd.concat(frames, ignore_index=True)

# Normalize a series to mean 0, standard deviation (std) 1
def _zscore(s: pd.Series) -> pd.Series:
    # zscore = how far value is from average
    mu = s.mean()
    sd = s.std(ddof=0)
    if sd == 0 or pd.isna(sd):
        return (s - mu)  # all zeros if sd==0
    return (s - mu) / sd

# Orchestrate: load data, compute volatility + sentiment, calculate
# risk scores, and save into DB
def write_risk_scores():
    # 1) Pull prices & news from DB
    with SessionLocal() as s:
        prices = pd.read_sql(select(Price), s.bind)
        news   = pd.read_sql(select(News),  s.bind)

    if prices.empty:
        print("No prices found; run etl_prices first.")
        return

    # 2) Compute features
    vol  = _compute_volatility(prices)       # stock, date, vol_20d
    sent = _compute_news_sentiment(news)     # stock, date, news_sent_7d

    # 3) Join; fill missing sentiment with 0 (neutral)
    df = pd.merge(vol, sent, on=["stock", "date"], how="left")
    df["news_sent_7d"] = df["news_sent_7d"].fillna(0.0)

    # 4) Z-score per day across stocks, then total risk score
    out = []
    for d, g in df.groupby("date"):
        g = g.copy()
        # If some vol are NaN (insufficient window), keep them but treat gracefully in z-score
        g["vol_fill"] = g["vol_20d"].fillna(g["vol_20d"].median())
        g["vol_z"]  = _zscore(g["vol_fill"])
        g["sent_z"] = _zscore(g["news_sent_7d"])
        g["total_score"] = 0.6 * g["vol_z"] + 0.4 * (-g["sent_z"])
        out.append(g[["stock","date","vol_20d","news_sent_7d","vol_z","sent_z","total_score"]])
    out = pd.concat(out, ignore_index=True)

    # 5) Upsert into DB
    with SessionLocal() as s:
        for _, r in out.iterrows():
            existing = s.execute(
                select(RiskScore).where(RiskScore.stock == r.stock, RiskScore.date == r.date)
            ).scalar_one_or_none()
            if existing:
                existing.vol_20d      = float(r.vol_20d) if pd.notnull(r.vol_20d) else None
                existing.news_sent_7d = float(r.news_sent_7d)
                existing.vol_z        = float(r.vol_z)
                existing.sent_z       = float(r.sent_z)
                existing.total_score  = float(r.total_score)
            else:
                s.add(RiskScore(
                    stock=r.stock,
                    date=r.date,
                    vol_20d=float(r.vol_20d) if pd.notnull(r.vol_20d) else None,
                    news_sent_7d=float(r.news_sent_7d),
                    vol_z=float(r.vol_z),
                    sent_z=float(r.sent_z),
                    total_score=float(r.total_score),
                ))
        s.commit()
    print("Risk scores updated.")

if __name__ == "__main__":
    write_risk_scores()
