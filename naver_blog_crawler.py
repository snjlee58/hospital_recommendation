from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# 웹드라이버 설정
options = webdriver.ChromeOptions()
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
# options.add_argument("--headless") # Run in headless mode
service = Service(ChromeDriverManager().install())

links = [
    "https://blog.naver.com/melon_815/222689879387",
    "https://blog.naver.com/pamada_salon/223584940093",
    "https://blog.naver.com/ton100ya/222906332890",
    # "https://vikanmichael.tistory.com/2591",
    # "https://j3r3g321-22.tistory.com/273"
    ]

#본문 크롤링
import time

# 크롬 드라이버 설치
driver = webdriver.Chrome(service=service, options=options)
driver.implicitly_wait(3)

#블로그 링크 하나씩 불러서 크롤링
contents = []
for i in links:
    #블로그 링크 하나씩 불러오기
    driver.get(i)
    time.sleep(1)
    #블로그 안 본문이 있는 iframe에 접근하기
    driver.switch_to.frame("mainFrame")
    #본문 내용 크롤링하기
    try:
        a = driver.find_element(By.CSS_SELECTOR,'div.se-main-container').text
        contents.append(a)
    # NoSuchElement 오류시 예외처리(구버전 블로그에 적용)
    except NoSuchElementException:
        a = driver.find_element(By.CSS_SELECTOR,'div#content-area').text
        contents.append(a)
    # print(본문: \n', a)
    print(a)

driver.quit() #창닫기
print("<<본문 크롤링이 완료되었습니다.>>")