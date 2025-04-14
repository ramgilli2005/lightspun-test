import os
from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment variable or use default SQLite URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./claims.db")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=True)

# Function to create database tables
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Function to get a database session
def get_session():
    with Session(engine) as session:
        yield session
