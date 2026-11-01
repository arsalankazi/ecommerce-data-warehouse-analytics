import os
import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

# Read credentials from environment variables with sanitized fallbacks
DB_USER = os.getenv("DB_USER", "warehouse_user")
DB_PASS = os.getenv("DB_PASS", "warehouse_password")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5433")
DB_NAME = os.getenv("DB_NAME", "ecommerce_warehouse")

# URL-encode credentials to safely handle special characters
encoded_user = urllib.parse.quote_plus(DB_USER)
encoded_pass = urllib.parse.quote_plus(DB_PASS)

DATABASE_URL = f"postgresql+psycopg2://{encoded_user}:{encoded_pass}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Enterprise connection pool configuration
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_pre_ping=True,
    pool_recycle=1800
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_engine():
    return engine
