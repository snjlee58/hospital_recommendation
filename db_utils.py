# db_utils.py
import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

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
