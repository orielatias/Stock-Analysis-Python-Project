from .db import Base, engine

"""
This file is the database initalizer.
Creates tables defined in models.py inside db (risk.db)
"""

def init_db():
    Base.metadata.create_all(bind=engine)
    print("DB ready.")

if __name__ == "__main__":
    init_db()
