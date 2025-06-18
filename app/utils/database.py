"""
Database utility functions for hospital recommendation service
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine


def load_database_url():
    """Load DATABASE_URL from .env and validate"""
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    if db_url is None:
        raise ValueError("DATABASE_URL is not set in the environment.")
    return db_url


def create_db_engine(database_url):
    """Create a SQLAlchemy engine instance"""
    return create_engine(database_url)


def get_database_connection():
    """Get database engine instance with environment configuration"""
    db_url = load_database_url()
    return create_db_engine(db_url) 