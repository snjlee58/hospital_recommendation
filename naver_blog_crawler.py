import sys
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import json
import time

from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from sqlalchemy import Table, Column, MetaData, Text, Integer
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import insert   # <<–– use the PG dialect
from db_utils import get_engine, get_hospital_id_names
from llm_utils import chunk_review_with_llm
from embedding_utils import embed_texts        # wraps MiniLM
from sqlalchemy.exc import IntegrityError, OperationalError

from db_utils import get_hospital_id_names_fixed
from naver_api import search_naver_blog

# Selenium WebDriver setup
options = webdriver.ChromeOptions()
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
options.add_argument("--headless") # Run in headless mode
service = Service(ChromeDriverManager().install())

driver = webdriver.Chrome(service=service, options=options)
driver.implicitly_wait(3)

# DEBUG: Test Links
links = [
    "https://blog.naver.com/melon_815/222689879387",
    # "https://blog.naver.com/pamada_salon/223584940093",
    # "https://blog.naver.com/ton100ya/222906332890",
    # "https://vikanmichael.tistory.com/2591",
    # "https://j3r3g321-22.tistory.com/273"
    ]

def get_blog_post_content(url):
    #블로그 링크 하나씩 불러서 iframe에서 크롤링
    try:
        driver.get(url)
        time.sleep(1) # Wait briefly for the page to load
        driver.switch_to.frame("mainFrame") # Switch to the iframe containing the blog post content
        
        try:
            #본문 내용 크롤링하기
            content = driver.find_element(By.CSS_SELECTOR,'div.se-main-container').text
        
        except NoSuchElementException:
            # NoSuchElement 오류시 예외처리(구버전 블로그에 적용)
            content = driver.find_element(By.CSS_SELECTOR,'div#content-area').text
        
        # Always switch back to main document return content
        driver.switch_to.default_content() 
        return content   

    except Exception as e:
        print(f"Error fetching blog content from {url}: {e}") 
        return None

# ─── DB & Table reflection ──────────────────────────────────────────────────
engine   = get_engine()
metadata = MetaData()
# review_chunks_tbl = Table("review_chunks", metadata, autoload_with=engine)
review_chunks_tbl = Table(
    "review_chunks",
    metadata,
    Column("chunk_id", Integer, primary_key=True),
    Column("url", Text, nullable=False),
    Column("hospital_id", Text, nullable=False),
    Column("category", Text, nullable=False),
    Column("chunk_text", Text, nullable=False),
    Column("embedding", Vector(384), nullable=False),   # now SQLAlchemy knows this is a Vector
    autoload_with=engine,
    extend_existing=True
)

if __name__ == "__main__":
    # id_names     = get_hospital_id_names()
    # start_idx    = 10
    # batch_size   = 500
    request_count = -1

    # Only iterate from start_idx up to batch_size items
    start_idx = int(sys.argv[1])
    end_idx   = int(sys.argv[2])
    id_names = get_hospital_id_names_fixed()
    for hosp_id, hosp_name in id_names:
        request_count += 1
    # for hosp_id, hosp_name in id_names[start_idx : start_idx + batch_size]:
        print(f"[Hosp {start_idx+request_count}] 🔍 Searching reviews for: {hosp_name} (ID={hosp_id})")

        # 1) Search Naver Blog for that hospital name + '후기'
        try:
            blog_posts = search_naver_blog(f"{hosp_name} 후기")
        except Exception as e:
            print(f"⚠️  검색 API 오류: {e}")
            continue

        # 2) For each returned post
        for post_id, post in enumerate(blog_posts):
            print(f"🔗Hosp {start_idx+request_count} | Post {post_id + 1}/{len(blog_posts)}: 📝 {post['title']} (ID={hosp_id})")
            url = post["link"]

            if "blog.naver.com" not in url:
                print("🟠  네이버 블로그 링크가 아닙니다, 건너뜀.")
                continue

            # 3) Crawl raw text
            content = get_blog_post_content(url)
            if not content:
                print("⚠️  크롤링 실패, 건너뜀.")
                continue

            # 4) Chunk via LLM
            try:
                chunks = chunk_review_with_llm(content)
            except Exception as e:
                print(f"❌ Chunking failed: {e}")
                continue
            
            # 5) Show the chunk JSON
            print("🤖 LLM‐Chunked JSON:")
            print(json.dumps(chunks, ensure_ascii=False, indent=2))

            # 3) Flatten into lists
            categories, texts = [], []
            for category, sentences in chunks.items():
                for sentence in sentences:
                    categories.append(category)
                    texts.append(sentence)

            if not texts:
                print("⚪️ No chunks produced, skipping.")
                continue

            # 4) Embed all texts at once
            embeddings = embed_texts(texts)  # numpy array shape (N,384)

            # 5) Build upsert records
            records = []
            for i, txt in enumerate(texts):
                records.append({
                    "url":   url,  # Use URL as unique ID
                    "hospital_id": hosp_id,
                    "category":    categories[i],
                    "chunk_text":  txt,
                    "url":         url,
                    "embedding":   embeddings[i].tolist()
                })

            # 6) Bulk upsert into review_chunks
            stmt = insert(review_chunks_tbl).values(records).on_conflict_do_nothing(
                index_elements=["url", "chunk_text"]
            )
            try:
                with engine.begin() as conn:
                    conn.execute(stmt)
                print(f"✅ Uploaded {len(records)} chunks for {url}")
            except OperationalError as oe:
                print(f"⚠️ DB connection error on {url}, skipping chunk upload: {oe}")
                engine.dispose()   # drop any bad connections; new ones will be opened next loop
                continue
            except IntegrityError as ie:
                # some parallel race? or constraint, skip
                print(f"⚠️ IntegrityError, skipping duplicates: {ie}")
                continue
            except Exception as e:
                # catches any other exception
                print(f"⚠️ Skipping upload for {url} due to error: {e}")
                # if it’s a connection‐level issue, dispose the pool so next loop gets a fresh one
                engine.dispose()
                continue

            # Be gentle with rate limits
            time.sleep(0.1)

    # Finally, close your Selenium driver
    from naver_blog_crawler import driver
    driver.quit()