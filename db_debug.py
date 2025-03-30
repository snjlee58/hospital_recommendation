from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# Load .env and connect to database
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

# 1. Check what tables exist
def list_tables():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public';
        """))
        print("📋 Existing tables:")
        for row in result:
            print(f"- {row[0]}")

# 2. Run any raw SQL query
def run_query(sql: str):
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        for row in result:
            print(row)

# 3. Add foreign key constraint (example: hospital_departments → hospitals)
def add_foreign_keys():
    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE hospital_departments
            ADD CONSTRAINT fk_hospital_id
            FOREIGN KEY (id)
            REFERENCES hospitals(id);
        """))

        conn.execute(text("""
            ALTER TABLE hospital_departments
            ADD CONSTRAINT fk_department_code
            FOREIGN KEY (department_code)
            REFERENCES departments(department_code);
        """))

        print("✅ Foreign key constraints added!")

def reset_hospitals_table():
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS hospitals CASCADE;"))
        conn.execute(text("""
            CREATE TABLE hospitals (
                id TEXT PRIMARY KEY,
                name TEXT,
                address TEXT,
                tel TEXT,
                url TEXT,
                city_name TEXT,
                district TEXT,
                town TEXT,
                type_name TEXT,
                lat FLOAT,
                lon FLOAT
            );
        """))
        print("✅ Created 'hospitals' table with primary key")

def reset_departments_table():
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS departments CASCADE;"))
        conn.execute(text("""
            CREATE TABLE departments (
                department_code TEXT PRIMARY KEY,
                department_name TEXT
            );
        """))
        print("✅ Created 'departments' table with primary key on department_code")

def reset_hospital_departments_table():
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS hospital_departments;"))
        conn.execute(text("""
            CREATE TABLE hospital_departments (
                hospital_id TEXT,
                department_code TEXT,
                specialist_count INT,
                PRIMARY KEY (hospital_id, department_code),
                FOREIGN KEY (hospital_id) REFERENCES hospitals(id),
                FOREIGN KEY (department_code) REFERENCES departments(department_code)
            );
        """))
        print("✅ Created 'hospital_departments' table with composite PK and FKs")


if __name__ == "__main__":
    run_query("""
    SELECT h.id, h.name, h.address, d.department_name, hd.specialist_count
    FROM hospital_departments hd
    JOIN hospitals h ON hd.hospital_id = h.id
    JOIN departments d ON hd.department_code = d.department_code
    WHERE d.department_name = '신경과';
""")
