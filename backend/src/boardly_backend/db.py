import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Database-agnostic on purpose: SQLite today, Postgres later without a
# rewrite, just a different DATABASE_URL.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./boardly.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()
