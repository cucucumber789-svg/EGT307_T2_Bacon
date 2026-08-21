"""SQLAlchemy engine and session setup.

One engine per process; routes open short-lived sessions via SessionLocal()
and must close them when done.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import Config

engine = create_engine(Config.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


def get_db():
    """Yield a database session that is always closed afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
