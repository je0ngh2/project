from flask import Flask, render_template, request
import sqlite3
import random
from selenium import webdriver as wb
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import requests
from bs4 import BeautifulSoup
from gensim.summarization import summarize
from selenium.common.exceptions import NoSuchElementException
from scipy.linalg import triu
import re
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

options = Options()
options.add_argument("--headless")
options.add_argument("window-size=1400,1500")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("start-maximized")
options.add_argument("enable-automation")
options.add_argument("--disable-infobars")
options.add_argument("--disable-dev-shm-usage")

service = Service('./chromedriver')
driver = wb.Chrome(service=service, options=options)

url = "https://news.naver.com/section/100"
driver.get(url)

time.sleep(1)



# 테이블이 존재하지 않으면 생성하는 함수
def create_table(db_name):
    conn = sqlite3.connect(db_name)
    curs = conn.cursor()
    
    # 테이블 존재 여부 확인
    curs.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='contact';")
    table_exists = curs.fetchone()

    # 테이블이 존재하면 삭제
    if table_exists:  
        delete_sql = "DELETE FROM contact"
        curs.execute(delete_sql)
        curs.execute("DELETE FROM sqlite_sequence WHERE name='contact'")
        conn.commit()

    # 테이블 생성 쿼리
    sql = """
    CREATE TABLE IF NOT EXISTS contact(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        article TEXT,
        body TEXT,
        video_url TEXT,
        image_url TEXT,
        thumbnail_url TEXT
    )
    """
    curs.execute(sql)
    conn.commit()
    curs.close()
    conn.close()

# 데이터를 테이블에 삽입하는 함수
def insert_data(db_name, title, article, body, video_url, image_url, thumbnail_url):
    conn = sqlite3.connect(db_name)
    curs = conn.cursor()
    
    # 데이터 삽입 쿼리
    insert_sql = "INSERT INTO contact (title, article, body, video_url, image_url, thumbnail_url) VALUES (?, ?, ?, ?, ?, ?)"
    curs.execute(insert_sql, (title, article, body, video_url, image_url, thumbnail_url))
    conn.commit()
    
    curs.close()
    conn.close()

# 기사 내용 길이에 따라 요약하는 함수
def summarize_article(article_text):
    text_length = len(article_text)
    if text_length >= 1500:
        summary = summarize(article_text, 0.1)
    elif text_length >= 1400:
        summary = summarize(article_text, 0.11)
    elif text_length >= 1300:
        summary = summarize(article_text, 0.12)
    elif text_length >= 1200:
        summary = summarize(article_text, 0.13)
    elif text_length >= 1100:
        summary = summarize(article_text, 0.14)
    elif text_length >= 1000:
        summary = summarize(article_text, 0.15)
    elif text_length >= 900:
        summary = summarize(article_text, 0.16)
    elif text_length >= 750:
        summary = summarize(article_text, 0.2)
    elif text_length >= 500:
        summary = summarize(article_text, 0.3)
    elif text_length >= 200:
        summary = summarize(article_text, 0.5)
    else:
        summary = article_text
    return summary

# 각 섹션에서 기사를 수집하는 함수
def collect_articles(section_name, db_name, section_index, menu_index):
    # 섹션 클릭
    section_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, f".Nlnb_menu_inner li:nth-child({menu_index}) span"))
    )
    section_button.click()
    print(f"{section_name} 섹션 클릭 완료")

    # 헤드라인 배너 클릭
    headline_banner = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "#newsct>div>div>a"))
    )
    headline_banner.click()
    print(f"헤드라인 배너 클릭 완료")

    # 최대 10개 기사를 순차적으로 처리
    article_count = 0
    for i in range(10):
        try:
            # 뉴스 기사 링크 클릭
            news_title_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, f"#newsct div>ul>li{'+li'*i}>div>div a"))
            )
            news_title_button.click()
            time.sleep(5) 
            print(f"기사 {i+1} 클릭 완료")

            # 뉴스 제목 로드 대기
            news_titles = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#title_area>span"))
            )
            
            news_title_text = news_titles.text
            print(f"제목: {news_title_text}")

            # 기사 본문 로드 대기
            article_body = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#dic_area"))
            )
            article_text = article_body.text
            print(f"기사 길이: {len(article_text)}")

            # 비디오 URL 추출
            video_url = None
            thumbnail_url = None
            try:
                video_element = driver.find_element(By.CSS_SELECTOR, "#video_area_0>div>div+div+div+div+div+div>div>div>a")
                video_url = video_element.get_attribute("href") if video_element else None
                # 썸네일 URL 추출
                thumbnail_element = driver.find_element(By.CSS_SELECTOR, "#video_area_0>div>div.pzp-pc__video+div")
                style_text = thumbnail_element.get_attribute("outerHTML") if thumbnail_element else None
                if style_text:
                    match = re.search(r'url\(["\']?(.*?)["\']?\)', style_text)
                    thumbnail_url = match.group(1) if match else None
                print(f"영상 url : {video_url}")
                print(f"썸네일 url : {thumbnail_url}")
            except NoSuchElementException:
                video_url = None
                thumbnail_url = None

            # 이미지 URL 추출
            image_url = None
            try:
                image_element = driver.find_element(By.ID, "img1")
                image_url = image_element.get_attribute("src") if image_element else None
                print(f"이미지 url : {image_url}")
            except NoSuchElementException:
                image_url = None

            # 기사 요약
            summary = summarize_article(article_text)
            print(f"요약: {summary}")

            body = article_text.strip() if summary else "No content available"
            title = news_title_text.strip() if news_title_text else "Unknown Title"
            article = summary.strip() if summary else "No content available"
            
            # 데이터베이스에 삽입
            insert_data(db_name, news_title_text, summary, article_text, video_url, image_url, thumbnail_url)
            print(f"기사 {i+1} 데이터베이스 삽입 완료")

            # 이전 페이지로 돌아가기
            driver.back()
            time.sleep(5)

        except NoSuchElementException:
            print()
        finally:
            print()

# 주요 실행 함수
def main():
    # 수집할 섹션 리스트
    sections = [
        ("Politic", "politics.db", 2, 2),
        ("Economy", "economy.db", 3, 3),
        ("Society", "society.db", 4, 4),
        ("Culture", "culture.db", 5, 5),
        ("IT_Science", "it_science.db", 6, 6),
        ("World", "world.db", 7, 7)
    ]

    for section_name, db_name, section_index, menu_index in sections:
        # 각 섹션에 대해 테이블 생성
        create_table(db_name)
        # 각 섹션의 기사 수집
        collect_articles(section_name, db_name, section_index, menu_index)

    # 모든 기사 수집 후 드라이버 종료
    driver.quit()

# 실행
if __name__ == "__main__":
    main()
