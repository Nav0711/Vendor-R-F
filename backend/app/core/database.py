from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.models import Base
from dotenv import load_dotenv
import os
from pathlib import Path

# Load .env from the script's directory
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Use SQLite for testing/development if DATABASE_URL is not set
    print("WARNING: DATABASE_URL not found, using SQLite for testing")
    DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    DATABASE_URL, 
    echo=True, 
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Database tables created!")
