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

# ── SQLite connection ─────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./vendorlens.db")

logger.info("Connecting to Database at %s", DATABASE_URL)

engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("LOG_LEVEL", "INFO").upper() == "DEBUG",
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
