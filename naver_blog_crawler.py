import json
import time
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from llm_utils import chunk_review_with_llm   # <— your LLM chunking function

from db_utils import get_hospital_id_names
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

if __name__ == "__main__":
    id_names     = get_hospital_id_names()
    start_idx    = 0
    batch_size   = 1
    request_count = 0

    # Only iterate from start_idx up to batch_size items
    for hosp_id, hosp_name in id_names[start_idx : start_idx + batch_size]:
        request_count += 1
        print(f"[{request_count}/{batch_size}] 🔍 Searching reviews for: {hosp_name} (ID={hosp_id})")

        # 1) Search Naver Blog for that hospital name + '후기'
        try:
            blog_posts = search_naver_blog(f"{hosp_name} 후기")
        except Exception as e:
            print(f"⚠️  검색 API 오류: {e}")
            continue

        # 2) For each returned post
        for post in blog_posts:
            url = post["link"]
            print("📝 Title:", post["title"])
            print("🔗 Link:", url)

            # 3) Crawl raw text
            content = get_blog_post_content(url)
            if not content:
                print("⚠️  크롤링 실패, 건너뜀.")
                continue

            print("📄 Raw review text (first 200 chars):", content[:200], "…")

            # 4) Chunk via LLM
            try:
                chunks = chunk_review_with_llm(content)
            except Exception as e:
                print(f"❌ Chunking failed: {e}")
                continue

            # 5) Show the chunk JSON
            print("🤖 LLM‐Chunked JSON:")
            print(json.dumps(chunks, ensure_ascii=False, indent=2))

            # (Here you could call your `ingest_review(...)` to embed & store)

            # Be gentle with rate limits
            time.sleep(0.1)

    # Finally, close your Selenium driver
    from naver_blog_crawler import driver
    driver.quit()