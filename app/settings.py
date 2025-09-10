import os
from dotenv import load_dotenv, find_dotenv

"""
This is the configuration hub.
Instead of hard-coding secrets or paths throughout the code
It is centralized  here so every part of the app can import from one place.
"""

# Load environment variables
load_dotenv(find_dotenv())

# API keys
ALPHA = os.environ.get("ALPHA_VINTAGE_API")
MARKETAUX = os.environ.get("MARKETAUX_API")

# Database URL - defaults to SQLite file risk.db in project root
DB_URL = os.getenv("DATABASE_URL", "sqlite:///./risk.db")

# Default stocks
STOCKS = [
    "AAPL",  # Apple
    "MSFT",  # Microsoft
    "NVDA",  # Nvidia
    "AMZN",  # Amazon
    "META",  # Meta (Facebook)
    "GOOGL", # Alphabet
    "TSLA",  # Tesla
    "JPM",   # JPMorgan Chase
    "GS",    # Goldman Sachs
    "NFLX"   # Netflix
]
