from dotenv import load_dotenv
from app.utils.database import load_database_url, create_db_engine
from app.core.hospital_search import search_hospitals
from sqlalchemy import text, MetaData, Table, Column, String, ForeignKey, create_engine, inspect
from collections import defaultdict
from openai import OpenAI
import json
import os
import numpy as np
from typing import Dict, List, Any
from datetime import datetime

def analyze_review_categories() -> List[Dict[str, Any]]:
    """
    Analyze review category statistics from database
    
    Returns:
        List[Dict[str, Any]]: Category-wise review count statistics
    """
    # Load database connection
    load_dotenv()
    db_url = load_database_url()
    engine = create_db_engine(db_url)
    
    query = text("""
        SELECT category, COUNT(*) as count
        FROM review_chunks
        GROUP BY category
        ORDER BY count DESC
    """)

    with engine.connect() as conn:
        result = conn.execute(query)
        categories = result.mappings().all()
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"review_categories_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=== Review Category Analysis ===\n")
            f.write(f"Total categories: {len(categories)}\n\n")
            f.write("Reviews by category:\n")
            for category in categories:
                f.write(f"- {category['category']}: {category['count']} reviews\n")
        
        print(f"Category analysis results saved to {filename}")
        return categories

def create_review_summaries_table(engine) -> None:
    """
    Create table to store review summaries
    
    Args:
        engine: SQLAlchemy engine object
    """
    metadata = MetaData()
    
    # Check if table exists and drop it
    inspector = inspect(engine)
    if 'review_summaries' in inspector.get_table_names():
        print("Dropping existing review_summaries table...")
        with engine.connect() as conn:
            try:
                conn.execute(text('DROP TABLE IF EXISTS review_summaries;'))
                conn.commit()
                print("Existing table dropped successfully.")
            except Exception as e:
                print(f"Error dropping table: {str(e)}")
                conn.rollback()
                raise
    
    # Create review_summaries table
    review_summaries = Table(
        'review_summaries',
        metadata,
        Column('hospital_id', String, ForeignKey('hospitals.id'), primary_key=True),
        Column('name', String),
        Column('review', String),
        Column('embedding', String)  # PostgreSQL vector type will be set in the raw SQL
    )
    
    # Create the table with vector extension
    with engine.connect() as conn:
        try:
            # Enable vector extension if not already enabled
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector;'))
            
            # Create table with vector type for embedding
            conn.execute(text("""
                CREATE TABLE review_summaries (
                    hospital_id TEXT PRIMARY KEY REFERENCES hospitals(id),
                    name TEXT,
                    review TEXT,
                    embedding vector(1536)
                );
            """))
            conn.commit()
            print("review_summaries table created successfully.")
        except Exception as e:
            print(f"Error creating table: {str(e)}")
            conn.rollback()
            raise

def generate_review_summaries(hospital_reviews: Dict[str, Dict[str, List[Dict[str, str]]]]) -> Dict[str, str]:
    """
    Generate hospital review summaries using GPT
    
    Args:
        hospital_reviews: Hospital reviews grouped by ID and category
        
    Returns:
        Dict[str, str]: Hospital ID to summary mapping
    """
    # OpenAI API setup
    load_dotenv()
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    processed_hospitals = {}
    total_hospitals = len(hospital_reviews)
    
    for idx, (hospital_id, category_reviews) in enumerate(hospital_reviews.items(), 1):
        print(f"[{idx}/{total_hospitals}] Processing hospital ID {hospital_id}...")
        
        # Combine review text by category into a single string
        review_text = ""
        for category, reviews in category_reviews.items():
            review_text += f"{category}:\n"
            for review in reviews:
                review_text += f"{review['chunk_text']}\n"
            review_text += "\n"
        
        # Generate GPT prompt
        prompt = f"""
                    당신은 병원 리뷰를 분석하여 핵심 내용을 정리하는 언어모델입니다. 이 요약은 병원별 특성을 벡터 임베딩하여, 사용자 요구와의 의미 유사도를 비교해 병원을 추천하는 데 사용됩니다.

                    따라서 다음 지침을 따라 **정보를 간결하고 의미 있게 요약**하세요.

                    [요약 목적]
                    - 최종 출력은 하나의 문자열로 생성되어 의미 기반 임베딩에 사용됩니다.
                    - 모델 성능을 고려해 **최대 300 토큰 이내**로 요약해주세요.

                    [작성 지침]
                    - 각 카테고리 안의 내용을 **객관적으로 요약**하고, "좋다", "추천", "든든하다" 등 **감성 표현은 제거**합니다.
                    - **긍정적인 내용과 부정적인 내용이 모두 있는 경우**, 둘 다 **균형 있게 반영**하세요.
                    - **중복되는 표현은 통합하여 간결하게** 정리하고, **카테고리 간 정보 이동은 하지 않습니다.**
                    - 정보가 없는 카테고리는 생략 가능합니다.
                    - 최종 출력은 다음 예시처럼, **카테고리 이름 + 요약된 문장**으로 구성된 하나의 문자열이어야 합니다.

                    [카테고리별 포함 기준]
                    - 검사/진료: 검사 종류, 진료 절차, 치료 방식 등
                    - 전문성/친절도: 의사의 설명 방식, 태도, 전문성
                    - 환경/시설: 병원 내 공간, 청결 상태, 장비 상태 등
                    - 예약/안내: 예약 시스템, 접수 과정, 안내 서비스
                    - 교통/접근성: 병원 위치, 대중교통, 주차 등
                    - 비용: 진료비, 시술비, 보험 적용 여부 등
                    - 기타: 위 항목에 포함되지 않는 기타 참고 정보

                    [출력 형식 예시]
                    검사/진료: 위내시경 및 혈액 검사 진행, 일부 검사 과정 설명 부족.  
                    전문성/친절도: 의료진 설명은 명확했으나 일부 직원 응대 미흡.  
                    환경/시설: 대기실은 넓고 청결했으나 검사실 냉방 불편함.  
                    예약/안내: 모바일 예약은 편리하나 안내 간호사 설명 부족.  
                    교통/접근성: 역 근처로 접근성은 좋았으나 주차 공간 협소.  
                    비용: 초진비는 적정하나 비급여 항목 일부는 고가.  
                    기타: 병원 내 안내 표지판 부족으로 초진 시 혼란.

                    [리뷰 정보]
                    {review_text}

                    위 형식과 어조를 따라 요약을 작성하세요.
                    """
        
        try:
            # Call GPT API
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a hospital review analyst who carefully categorizes and summarizes reviews based on their content and relevance."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            # Process response
            summary = response.choices[0].message.content
            processed_hospitals[hospital_id] = summary
            
            # Generate embedding and save to DB immediately
            try:
                # Generate embedding
                embedding = get_embedding(summary, client)
                if not embedding:
                    print(f"Failed to generate embedding (hospital_id: {hospital_id})")
                    continue
                
                # Connect to database
                db_url = load_database_url()
                engine = create_db_engine(db_url)
                
                with engine.connect() as conn:
                    # Get hospital name
                    name_query = text("SELECT name FROM hospitals WHERE id = :id")
                    name_result = conn.execute(name_query, {"id": hospital_id})
                    hospital_name = name_result.scalar()
                    
                    # Save to database
                    upsert_query = text("""
                        INSERT INTO review_summaries (hospital_id, name, review, embedding)
                        VALUES (:hospital_id, :name, :review, :embedding)
                        ON CONFLICT (hospital_id) DO UPDATE
                        SET review = :review, embedding = :embedding
                    """)
                    
                    conn.execute(upsert_query, {
                        "hospital_id": hospital_id,
                        "name": hospital_name,
                        "review": summary,
                        "embedding": embedding
                    })
                    conn.commit()
                    print(f"Hospital ID {hospital_id} processed successfully")
                
            except Exception as e:
                print(f"Error processing hospital ID {hospital_id}: {str(e)}")
                continue
                
        except Exception as e:
            print(f"Error processing hospital {hospital_id}: {str(e)}")
            processed_hospitals[hospital_id] = "Error processing reviews"
    
    return processed_hospitals

def get_embedding(text: str, client: OpenAI) -> List[float]:
    """
    Generate text embedding using OpenAI's text-embedding-3-small model
    
    Args:
        text: Text to embed
        client: OpenAI client
        
    Returns:
        List[float]: Embedding vector
    """
    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding: {str(e)}")
        return []

def process_hospital_reviews(city: str = "서울", district: str = "강남구", limit: int = 200) -> Dict[str, str]:
    """
    Process hospital reviews and save summaries to database
    
    Args:
        city: City name
        district: District name
        limit: Limit on number of hospitals to process
        
    Returns:
        Dict[str, str]: Hospital ID to summary mapping
    """
    # Load database connection
    load_dotenv()
    db_url = load_database_url()
    engine = create_db_engine(db_url)
    
    # Create review_summaries table if it doesn't exist
    # create_review_summaries_table(engine)
    
    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    query = text("""
        SELECT h.id, h.name, rc.chunk_text, rc.embedding, rc.category
        FROM hospitals h
        JOIN city c ON h.city_code = c.code
        JOIN district d ON h.district_code = d.code
        JOIN review_chunks rc ON h.id = rc.hospital_id
        WHERE c.name = :city
          AND d.name = :district
          AND rc.category != '기타'
        ORDER BY h.id
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query, {
            "city": city,
            "district": district,
            "limit": limit
        })
        rows = result.mappings().all()
        
        # Group reviews by hospital ID and category
        hospital_reviews = defaultdict(lambda: defaultdict(list))
        for row in rows:
            hospital_reviews[row['id']][row['category']].append({
                'chunk_text': row['chunk_text'],
                'embedding': row['embedding']
            })
        
        # Process reviews with GPT
        processed_hospitals = generate_review_summaries(hospital_reviews)
        
        # Save results to file
        filename = f"hospital_reviews_{city}_{district}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"=== {city} {district} Hospital Review Summary ===\n")
            f.write(f"Hospitals found: {len(hospital_reviews)}\n\n")
            
            for hospital_id, summary in processed_hospitals.items():
                f.write(f"\nHospital ID: {hospital_id}\n")
                f.write("=== Review Summary ===\n")
                f.write(summary)
                f.write("\n" + "=" * 50 + "\n")
        
        print(f"Review summary results saved to {filename}")
        return processed_hospitals

if __name__ == "__main__":
    # analyze_review_categories()
    process_hospital_reviews()
