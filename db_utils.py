# db_utils.py
import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import text
from dotenv import load_dotenv

from sqlalchemy import MetaData, Table
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError

# Load .env file
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def get_engine():
    return create_engine(DATABASE_URL)

def upload_dataframe(df: pd.DataFrame, table_name: str, if_exists="append"):
    engine = get_engine()
    with engine.connect() as connection:
        df.to_sql(table_name, con=connection, if_exists=if_exists, index=False)
        print(f"✅ Uploaded to table: {table_name}")

def get_hospital_ids():
    engine = get_engine()
    with engine.connect() as connection:
        result = connection.execute(text("SELECT id FROM hospitals ORDER BY id;"))
        hospital_ids = [row[0] for row in result.fetchall()]
    return hospital_ids

def get_hospital_id_names():
    """
    Returns a list of (hospital_id, hospital_name) tuples,
    ordered by hospital_id.
    """
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, name FROM hospitals ORDER BY id;")
        ).fetchall()
    # row is a Row object, so you can access by index or by key
    return [(row[0], row[1]) for row in rows]

def get_hospital_id_names_fixed():
    """
    Returns a list of (hospital_id, hospital_name) tuples for 논현동,
    ordered by hospital_id.
    """
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT
                id,
                name
            FROM hospitals
            WHERE
                district_code = '110001'
                AND type_code     = '31'
                AND town          = '논현동'
            ORDER BY id
        """)).fetchall()

    # each row is (id, name)
    return [(row[0], row[1]) for row in rows]

def upload_dataframe_ignore_dups(
    df: pd.DataFrame,
    table_name: str,
    if_exists: str = "append",
    pk: list[str] | None = None
):
    """
    - If pk is None: behaves like df.to_sql(..., if_exists=if_exists)
    - If pk is provided and if_exists='append', does a bulk INSERT ... ON CONFLICT DO NOTHING
      based on those pk columns.
    """
    engine = get_engine()

    if pk is None or if_exists != "append":
        # Simple path: use pandas
        with engine.connect() as conn:
            df.to_sql(table_name, con=conn, if_exists=if_exists, index=False)
            print(f"✅ Uploaded to table: {table_name} (mode={if_exists})")
        return

    # Upsert path
    metadata = MetaData()
    table = Table(table_name, metadata, autoload_with=engine)

    records = df.to_dict(orient="records")
    if not records:
        print(f"⚠️ No records to insert into {table_name}")
        return

    stmt = insert(table).on_conflict_do_nothing(index_elements=pk)

    try:
        with engine.begin() as conn:
            conn.execute(stmt, records)
        print(f"✅ Upserted {len(records)} rows into {table_name}, duplicates skipped on {pk}")
    except SQLAlchemyError as e:
        print(f"❌ Failed to upsert into {table_name}: {e}")
        raise