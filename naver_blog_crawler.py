import json
import time
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from llm_utils import chunk_review_with_llm   # <— your LLM chunking function

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
    for url in links:
        print("\n\n" + "#" * 80)
        print(f"URL: {url}\n")
        raw = get_blog_post_content(url)
        if not raw:
            print("⚠️  No content, skipping.")
            continue

        print("📄 Raw review text:\n", raw[:500], "…\n")  # print first 500 chars

        try:
            chunks = chunk_review_with_llm(raw)
            print("🤖 LLM‐Chunked JSON:")
            print(json.dumps(chunks, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"❌ Chunking failed: {e}")

    driver.quit()
