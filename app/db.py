from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .settings import DB_URL

"""
This class sets up the connection and session to the database.
"""

# Engine = connection object to the database.
engine = create_engine(DB_URL, future=True, echo=False)

# Way of communication to the db (insert, query, update)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# Parent class for all models
Base = declarative_base()
