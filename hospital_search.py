import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text

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

def search_hospitals(city_name, district_name, hospital_type_name, department_name, engine):
    """
    Search hospitals matching the specified filters:
    city, district, hospital type, and department.
    Returns a list of dict rows (max 10).
    """
    query = text("""
        SELECT h.name, h.address, h.tel, h.url
        FROM hospitals h
        JOIN city c ON h.city_code = c.code
        JOIN district d ON h.district_code = d.code
        JOIN hospital_type ht ON h.type_code = ht.code
        JOIN hospital_departments hd ON h.id = hd.hospital_id
        JOIN departments dp ON hd.department_code = dp.department_code
        WHERE c.name = :city
          AND d.name = :district
          AND ht.name = :hospital_type
          AND dp.department_name = :department
        LIMIT 10
    """)

    with engine.connect() as conn:
        result = conn.execute(query, {
            "city": city_name,
            "district": district_name,
            "hospital_type": hospital_type_name,
            "department": department_name
        })
        return result.mappings().all()  # Ensures compatibility with dict()