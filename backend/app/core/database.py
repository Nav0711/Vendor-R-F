from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from urllib.parse import quote_plus
from pathlib import Path
import logging
import os

logger = logging.getLogger(__name__)

# Load .env from the backend/ root (3 levels up from app/core/)
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent.parent / ".env")

# ── MySQL connection ──────────────────────────────────────────────────────────
# VendorLens uses MySQL. A full DATABASE_URL (if set) takes precedence; otherwise
# the URL is assembled from the discrete MYSQL_* variables in .env.
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DB_USER = os.getenv("MYSQL_USER", "root")
    DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    DB_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
    DB_PORT = os.getenv("MYSQL_PORT", "3306")
    DB_NAME = os.getenv("MYSQL_DB", "vendorlens")
    # quote_plus so special characters in the password don't break the URL
    DATABASE_URL = (
        f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    )

logger.info("Connecting to MySQL at %s:%s", os.getenv("MYSQL_HOST", "127.0.0.1"), os.getenv("MYSQL_PORT", "3306"))

engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("LOG_LEVEL", "INFO").upper() == "DEBUG",
    pool_pre_ping=True,   # transparently recycle stale MySQL connections
    pool_recycle=3600,    # avoid MySQL's default 8h "server has gone away" timeout
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
