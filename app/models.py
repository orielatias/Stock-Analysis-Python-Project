from sqlalchemy import Column, Integer, String, Date, Float, Text, UniqueConstraint
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from .db import Base

"""
This file uses SQLAlchemy ORM to define classes (Price, News, RiskScore).
Each class maps to a table in the database (prices, news, risk_scores).
Each class attribute (like stock, date, close) maps to a column in that table.
"""
class Price(Base):
    __tablename__ = "prices"
    id = Column(Integer, primary_key=True)
    stock = Column(String, index=True)   # was ticker
    date = Column(Date, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    __table_args__ = (UniqueConstraint("stock", "date", name="uix_price_stock_date"),)

class News(Base):
    __tablename__ = "news"
    id = Column(Integer, primary_key=True)
    stock = Column(String, index=True)   # was ticker
    published_at = Column(String, index=True)   # ISO string
    title = Column(Text)
    url = Column(Text)
    source = Column(String)
    sentiment = Column(Float)
    raw = Column(SQLiteJSON)   # JSON for extra fields
    __table_args__ = (UniqueConstraint("stock", "published_at", "title", name="uix_news_unique"),)

class RiskScore(Base):
    __tablename__ = "risk_scores"
    id = Column(Integer, primary_key=True)
    stock = Column(String, index=True)   # was ticker
    date = Column(Date, index=True)
    vol_20d = Column(Float)
    news_sent_7d = Column(Float)
    vol_z = Column(Float)
    sent_z = Column(Float)
    total_score = Column(Float)
    __table_args__ = (UniqueConstraint("stock", "date", name="uix_risk_stock_date"),)
