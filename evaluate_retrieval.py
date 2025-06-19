import os
import pandas as pd
import numpy as np
from sqlalchemy import text
from dotenv import load_dotenv
from app.core.hospital_search import HospitalSearchEngine
from app.utils.database import get_database_connection
from openai import OpenAI

# Load environment
load_dotenv()

# Instantiate the client with the API key
client = OpenAI()

# Initialize engine and search
engine = get_database_connection()
search_engine = HospitalSearchEngine(engine=engine)

# Step 1: Get review samples
def fetch_review_samples(n=10):
    query = text("""
        SELECT
            hospital_id,
            name AS hospital_name,
            review AS summary
        FROM review_summaries
        WHERE review IS NOT NULL AND review != ''
        LIMIT :limit
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {'limit': n})
        rows = result.fetchall()
    return pd.DataFrame(rows, columns=["hospital_id", "hospital_name", "summary"])


# Step 2: Generate query from summary
def generate_user_query(summary: str) -> str:
    prompt = f"""아래는 병원 후기에 대한 요약입니다. 사용자가 병원을 찾으려고 할 때 검색창에 입력할 법한 쿼리를 한 문장으로 작성해주세요.

후기 요약: "{summary}"

쿼리:"""
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "당신은 병원 검색을 위한 사용자 쿼리를 생성하는 전문가입니다."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=40
    )
    return response.choices[0].message.content.strip()

# Step 3: Run hospital search (dummy metadata)
def run_search(query_text):
    return search_engine.search_hospitals(
        query_text,
        city_name="서울특별시",
        district_name="강남구",
        hospital_type_name="병원",
        department_name="정형외과",
        limit=10
    )

# Step 4: Evaluation
def compute_metrics(true_hospital, results, k=5):
    """
    Compute recall@k: whether the true hospital is in the top-k results.
    """
    predicted_ids = [res['hospital_id'] for res in results[:k]]
    recall_at_k = 1.0 if true_hospital in predicted_ids else 0.0
    return {
        'recall@{}'.format(k): recall_at_k
    }
