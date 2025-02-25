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

# 정치 뉴스 함수
def politic_article():

    # 데이터베이스 연결
    conn = sqlite3.connect("politics.db")
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

    # 테이블 생성 (이미 존재하면 생략)
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
    
    # N뉴스 홈페이지에서 정치 버튼 클릭
    politic_botton = driver.find_element(By.CSS_SELECTOR, ".Nlnb_menu_inner li+li span")
    politic_botton.click()

    # 헤드라인 누르기 정치, 경제, 사회 ,생활/문화, IT/과학, 세계 모두 동일한 코드임
    headline_banner = driver.find_element(By.CSS_SELECTOR, "#newsct>div>div>a")
    headline_banner.click()

    # for문 돌면서 헤드라인 뉴스 10개까지 수집. 10개 이하면 try, except 구문을 통해 빠져나옴.
    try:
        for i in range(10):
            news_title_button = driver.find_element(By.CSS_SELECTOR, f"#newsct div>ul>li{'+li'*i}>div>div a")
            news_title_button.click()
            time.sleep(2)
            # 헤드라인 뉴스 들어가서 기사 제목과 기사 내용 수집
            news_titles = driver.find_element(By.CSS_SELECTOR, "#title_area>span")
            news_title_text = news_titles.text
            
            article_body = driver.find_element(By.CSS_SELECTOR, "#dic_area")
            article_text = article_body.text
            summary = summarize_article(article_text)

            # 비디오 URL 추출
            video_url = None
            thumbnail_url = None
            try:
                video_element = driver.find_element(By.CSS_SELECTOR, "#video_area_0>div>div+div+div+div+div+div>div>div>a")
                video_url = video_element.get_attribute("href") if video_element else None
                # 썸네일 URL 추출
                thumbnail_element = driver.find_element(By.CSS_SELECTOR, "#video_area_0>div>div.pzp-pc__video+div")  # 썸네일 이미지 추출
                # style 속성 가져오기
                style_text = thumbnail_element.get_attribute("outerHTML") if thumbnail_element else None

                if style_text:
                    match = re.search(r'url\(["\']?(.*?)["\']?\)', style_text)
                    thumbnail_url = match.group(1) if match else None
            except NoSuchElementException:
                video_url = None
                thumbnail_url = None
            
            # 이미지 URL 추출
            image_url = None
            try:
                image_element = driver.find_element(By.ID, "img1")  # 첫 번째 <img> 태그 선택
                image_url = image_element.get_attribute("src") if image_element else None
            except NoSuchElementException:
                image_url = None
            
            body = article_text.strip() if summary else "No content available"
            title = news_title_text.strip() if news_title_text else "Unknown Title"
            article = summary.strip() if summary else "No content available"
            
            # 데이터 추가
            insert_sql = """
            INSERT INTO contact (title, article, body, video_url, image_url, thumbnail_url)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            curs.execute(insert_sql, (title, article, body, video_url, image_url, thumbnail_url))


            # 변경 사항 저장
            conn.commit()
            
            
            driver.back()
            
            time.sleep(2)
    except NoSuchElementException:
        print()
    finally:
        # 연결 종료
        curs.close()
        conn.close()

# 경제 뉴스 함수
def economy_article():
    # 데이터베이스 연결
    conn = sqlite3.connect("economy.db")
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
    
    # 테이블 생성 (이미 존재하면 생략)
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
    
    # N뉴스 홈페이지에서 경제 버튼 클릭
    economy_botton = driver.find_element(By.CSS_SELECTOR, ".Nlnb_menu_inner li+li+li span")
    economy_botton.click()

    # 헤드라인 누르기 정치, 경제, 사회 ,생활/문화, IT/과학, 세계 모두 동일한 코드임
    headline_banner = driver.find_element(By.CSS_SELECTOR, "#newsct>div>div>a")
    headline_banner.click()

    # for문 돌면서 헤드라인 뉴스 10개까지 수집. 10개 이하면 try, except 구문을 통해 빠져나옴.
    try:
        for i in range(10):
            news_title_button = driver.find_element(By.CSS_SELECTOR, f"#newsct div>ul>li{'+li'*i}>div>div a")
            news_title_button.click()
            time.sleep(2)
            # 헤드라인 뉴스 들어가서 기사 제목과 기사 내용 수집
            news_titles = driver.find_element(By.CSS_SELECTOR, "#title_area>span")
            news_title_text = news_titles.text
            
            article_body = driver.find_element(By.CSS_SELECTOR, "#dic_area")
            article_text = article_body.text
            summary = summarize_article(article_text)
            
            # 비디오 URL 추출
            video_url = None
            thumbnail_url = None
            try:
                video_element = driver.find_element(By.CSS_SELECTOR, "#video_area_0>div>div+div+div+div+div+div>div>div>a")
                video_url = video_element.get_attribute("href") if video_element else None
                # 썸네일 URL 추출
                thumbnail_element = driver.find_element(By.CSS_SELECTOR, "#video_area_0>div>div.pzp-pc__video+div")  # 썸네일 이미지 추출
                # style 속성 가져오기
                style_text = thumbnail_element.get_attribute("outerHTML") if thumbnail_element else None

                if style_text:
                    match = re.search(r'url\(["\']?(.*?)["\']?\)', style_text)
                    thumbnail_url = match.group(1) if match else None
            except NoSuchElementException:
                video_url = None
                thumbnail_url = None

            # 이미지 URL 추출
            image_url = None
            try:
                image_element = driver.find_element(By.ID, "img1")  # 첫 번째 <img> 태그 선택
                image_url = image_element.get_attribute("src") if image_element else None
            except NoSuchElementException:
                image_url = None
            
            body = article_text.strip() if summary else "No content available"
            title = news_title_text.strip() if news_title_text else "Unknown Title"
            article = summary.strip() if summary else "No content available"

            # 데이터 추가
            insert_sql = """
            INSERT INTO contact (title, article, body, video_url, image_url, thumbnail_url)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            curs.execute(insert_sql, (title, article, body, video_url, image_url, thumbnail_url))

            # 변경 사항 저장
            conn.commit()
            
            driver.back()
            
            time.sleep(2)
    except NoSuchElementException:
        print()
    finally:
        curs.close()
        conn.close()

# 사회 뉴스 함수
def society_article():
    # 데이터베이스 연결
    conn = sqlite3.connect("society.db")
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
    
    # 테이블 생성 (이미 존재하면 생략)
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
    
    # N뉴스 홈페이지에서 경제 버튼 클릭
    society_botton = driver.find_element(By.CSS_SELECTOR, ".Nlnb_menu_inner li+li+li+li span")
    society_botton.click()

    # 헤드라인 누르기 정치, 경제, 사회 ,생활/문화, IT/과학, 세계 모두 동일한 코드임
    headline_banner = driver.find_element(By.CSS_SELECTOR, "#newsct>div>div>a")
    headline_banner.click()

    # for문 돌면서 헤드라인 뉴스 10개까지 수집. 10개 이하면 try, except 구문을 통해 빠져나옴.
    try:
        for i in range(10):
            news_title_button = driver.find_element(By.CSS_SELECTOR, f"#newsct div>ul>li{'+li'*i}>div>div a")
            news_title_button.click()
            time.sleep(2)
            # 헤드라인 뉴스 들어가서 기사 제목과 기사 내용 수집
            news_titles = driver.find_element(By.CSS_SELECTOR, "#title_area>span")
            news_title_text = news_titles.text
            
            article_body = driver.find_element(By.CSS_SELECTOR, "#dic_area")
            article_text = article_body.text
            summary = summarize_article(article_text)
            
            # 비디오 URL 추출
            video_url = None
            thumbnail_url = None
            try:
                video_element = driver.find_element(By.CSS_SELECTOR, "#video_area_0>div>div+div+div+div+div+div>div>div>a")
                video_url = video_element.get_attribute("href") if video_element else None
                # 썸네일 URL 추출
                thumbnail_element = driver.find_element(By.CSS_SELECTOR, "#video_area_0>div>div.pzp-pc__video+div")  # 썸네일 이미지 추출
                # style 속성 가져오기
                style_text = thumbnail_element.get_attribute("outerHTML") if thumbnail_element else None

                if style_text:
                    match = re.search(r'url\(["\']?(.*?)["\']?\)', style_text)
                    thumbnail_url = match.group(1) if match else None
            except NoSuchElementException:
                video_url = None
                thumbnail_url = None

            # 이미지 URL 추출
            image_url = None
            try:
                image_element = driver.find_element(By.ID, "img1")  # 첫 번째 <img> 태그 선택
                image_url = image_element.get_attribute("src") if image_element else None
            except NoSuchElementException:
                image_url = None

            body = article_text.strip() if summary else "No content available"

            title = news_title_text.strip() if news_title_text else "Unknown Title"
            article = summary.strip() if summary else "No content available"

            # 데이터 추가
            insert_sql = """
            INSERT INTO contact (title, article, body, video_url, image_url, thumbnail_url)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            curs.execute(insert_sql, (title, article, body, video_url, image_url, thumbnail_url))


            # 변경 사항 저장
            conn.commit()
            
            driver.back()
            
            time.sleep(2)
    except NoSuchElementException:
        print()
    finally:
        curs.close()
        conn.close()

# 생활/문화 뉴스 함수
def culture_article():
    # 데이터베이스 연결
    conn = sqlite3.connect("culture.db")
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
    
# # 테이블의 모든 데이터 삭제
#     delete_sql = "DELETE FROM contact"
#     curs.execute(delete_sql)

    # 테이블 생성 (이미 존재하면 생략)
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
    
    # N뉴스 홈페이지에서 생활/문화 버튼 클릭
    culture_botton = driver.find_element(By.CSS_SELECTOR, ".Nlnb_menu_inner li+li+li+li+li span")
    culture_botton.click()

    # 헤드라인 누르기 정치, 경제, 사회 ,생활/문화, IT/과학, 세계 모두 동일한 코드임
    headline_banner = driver.find_element(By.CSS_SELECTOR, "#newsct>div>div>a")
    headline_banner.click()

    # for문 돌면서 헤드라인 뉴스 10개까지 수집. 10개 이하면 try, except 구문을 통해 빠져나옴.
    try:
        for i in range(10):
            news_title_button = driver.find_element(By.CSS_SELECTOR, f"#newsct div>ul>li{'+li'*i}>div>div a")
            news_title_button.click()
            time.sleep(2)
            # 헤드라인 뉴스 들어가서 기사 제목과 기사 내용 수집
            news_titles = driver.find_element(By.CSS_SELECTOR, "#title_area>span")
            news_title_text = news_titles.text
            
            article_body = driver.find_element(By.CSS_SELECTOR, "#dic_area")
            article_text = article_body.text
            summary = summarize_article(article_text)
            
            # 비디오 URL 추출
            video_url = None
            thumbnail_url = None
            try:
                video_element = driver.find_element(By.CSS_SELECTOR, "#video_area_0>div>div+div+div+div+div+div>div>div>a")
                video_url = video_element.get_attribute("href") if video_element else None
                # 썸네일 URL 추출
                thumbnail_element = driver.find_element(By.CSS_SELECTOR, "#video_area_0>div>div.pzp-pc__video+div")  # 썸네일 이미지 추출
                # style 속성 가져오기
                style_text = thumbnail_element.get_attribute("outerHTML") if thumbnail_element else None

                if style_text:
                    match = re.search(r'url\(["\']?(.*?)["\']?\)', style_text)
                    thumbnail_url = match.group(1) if match else None
            except NoSuchElementException:
                video_url = None
                thumbnail_url = None

            # 이미지 URL 추출
            image_url = None
            try:
                image_element = driver.find_element(By.ID, "img1")  # 첫 번째 <img> 태그 선택
                image_url = image_element.get_attribute("src") if image_element else None
            except NoSuchElementException:
                image_url = None
            
            body = article_text.strip() if summary else "No content available"

            title = news_title_text.strip() if news_title_text else "Unknown Title"
            article = summary.strip() if summary else "No content available"

            # 데이터 추가
            #print(f"✅ 저장할 데이터 - Title: {title}, Article: {article}")

            insert_sql = """
            INSERT INTO contact (title, article, body, video_url, image_url, thumbnail_url)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            curs.execute(insert_sql, (title, article, body, video_url, image_url, thumbnail_url))


            # 변경 사항 저장
            time.sleep(1)
            conn.commit()
            
            
            driver.back()
            
            time.sleep(2)
    except NoSuchElementException:
        print()
    finally:
        curs.close()
        conn.close()

# IT/과학 뉴스 함수
def it_article():
    # 데이터베이스 연결
    conn = sqlite3.connect("it_science.db")
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
    
    # 테이블 생성 (이미 존재하면 생략)
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
    
    # N뉴스 홈페이지에서 IT/과학 버튼 클릭
    it_botton = driver.find_element(By.CSS_SELECTOR, ".Nlnb_menu_inner li+li+li+li+li+li span")
    it_botton.click()

    # 헤드라인 누르기 정치, 경제, 사회 ,생활/문화, IT/과학, 세계 모두 동일한 코드임
    headline_banner = driver.find_element(By.CSS_SELECTOR, "#newsct>div>div>a")
    headline_banner.click()

    # for문 돌면서 헤드라인 뉴스 10개까지 수집. 10개 이하면 try, except 구문을 통해 빠져나옴.
    try:
        for i in range(10):
            news_title_button = driver.find_element(By.CSS_SELECTOR, f"#newsct div>ul>li{'+li'*i}>div>div a")
            news_title_button.click()
            time.sleep(2)
            # 헤드라인 뉴스 들어가서 기사 제목과 기사 내용 수집
            news_titles = driver.find_element(By.CSS_SELECTOR, "#title_area>span")
            news_title_text = news_titles.text
            
            
            article_body = driver.find_element(By.CSS_SELECTOR, "#dic_area")
            article_text = article_body.text
            summary = summarize_article(article_text)
            
            # 비디오 URL 추출
            video_url = None
            thumbnail_url = None
            try:
                video_element = driver.find_element(By.CSS_SELECTOR, "#video_area_0>div>div+div+div+div+div+div>div>div>a")
                video_url = video_element.get_attribute("href") if video_element else None
                # 썸네일 URL 추출
                thumbnail_element = driver.find_element(By.CSS_SELECTOR, "#video_area_0>div>div.pzp-pc__video+div")  # 썸네일 이미지 추출
                # style 속성 가져오기
                style_text = thumbnail_element.get_attribute("outerHTML") if thumbnail_element else None

                if style_text:
                    match = re.search(r'url\(["\']?(.*?)["\']?\)', style_text)
                    thumbnail_url = match.group(1) if match else None
            except NoSuchElementException:
                video_url = None
                thumbnail_url = None

            # 이미지 URL 추출
            image_url = None
            try:
                image_element = driver.find_element(By.ID, "img1")  # 첫 번째 <img> 태그 선택
                image_url = image_element.get_attribute("src") if image_element else None
            except NoSuchElementException:
                image_url = None

            body = article_text.strip() if summary else "No content available"

            title = news_title_text.strip() if news_title_text else "Unknown Title"
            article = summary.strip() if summary else "No content available"

            # 데이터 추가
            insert_sql = """
            INSERT INTO contact (title, article, body, video_url, image_url, thumbnail_url)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            curs.execute(insert_sql, (title, article, body, video_url, image_url, thumbnail_url))


            # 변경 사항 저장
            conn.commit()
            
            
            driver.back()
            
            time.sleep(2)
    except NoSuchElementException:
        print()
    finally:
        curs.close()
        conn.close()

# 세계 뉴스 함수
def world_article():
    # 데이터베이스 연결
    conn = sqlite3.connect("world.db")
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
    
    # 테이블 생성 (이미 존재하면 생략)
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
    
    # N뉴스 홈페이지에서 세계 버튼 클릭
    world_botton = driver.find_element(By.CSS_SELECTOR, ".Nlnb_menu_inner li+li+li+li+li+li+li span")
    world_botton.click()

    # 헤드라인 누르기 정치, 경제, 사회 ,생활/문화, IT/과학, 세계 모두 동일한 코드임
    headline_banner = driver.find_element(By.CSS_SELECTOR, "#newsct>div>div>a")
    headline_banner.click()

    # for문 돌면서 헤드라인 뉴스 10개까지 수집. 10개 이하면 try, except 구문을 통해 빠져나옴.
    try:
        for i in range(10):
            news_title_button = driver.find_element(By.CSS_SELECTOR, f"#newsct div>ul>li{'+li'*i}>div>div a")
            news_title_button.click()
            time.sleep(2)
            # 헤드라인 뉴스 들어가서 기사 제목과 기사 내용 수집
            news_titles = driver.find_element(By.CSS_SELECTOR, "#title_area>span")
            news_title_text = news_titles.text
            
            article_body = driver.find_element(By.CSS_SELECTOR, "#dic_area")
            article_text = article_body.text
            summary = summarize_article(article_text)
            
            # 비디오 URL 추출
            video_url = None
            thumbnail_url = None
            try:
                video_element = driver.find_element(By.CSS_SELECTOR, "#video_area_0>div>div+div+div+div+div+div>div>div>a")
                video_url = video_element.get_attribute("href") if video_element else None
                # 썸네일 URL 추출
                thumbnail_element = driver.find_element(By.CSS_SELECTOR, "#video_area_0>div>div.pzp-pc__video+div")  # 썸네일 이미지 추출
                # style 속성 가져오기
                style_text = thumbnail_element.get_attribute("outerHTML") if thumbnail_element else None

                if style_text:
                    match = re.search(r'url\(["\']?(.*?)["\']?\)', style_text)
                    thumbnail_url = match.group(1) if match else None
            except NoSuchElementException:
                video_url = None
                thumbnail_url = None

            # 이미지 URL 추출
            image_url = None
            try:
                image_element = driver.find_element(By.ID, "img1")  # 첫 번째 <img> 태그 선택
                image_url = image_element.get_attribute("src") if image_element else None
            except NoSuchElementException:
                image_url = None

            body = article_text.strip() if summary else "No content available"

            title = news_title_text.strip() if news_title_text else "Unknown Title"
            article = summary.strip() if summary else "No content available"

            # 데이터 추가
            insert_sql = """
            INSERT INTO contact (title, article, body, video_url, image_url, thumbnail_url)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            curs.execute(insert_sql, (title, article, body, video_url, image_url, thumbnail_url))


            # 변경 사항 저장
            conn.commit()
            
            driver.back()
            
            time.sleep(2)
    except NoSuchElementException:
        print()
    finally:
        curs.close()
        conn.close()

#  기사요약
def summarize_article (article_text):
    text_length = len(article_text)
    if text_length >= 1500 :
        summary = summarize(article_text,0.1)
    elif text_length>= 1400 and text_length < 1500:
        summary = summarize(article_text,0.11)
    elif text_length>= 1300 and text_length < 1400:
        summary = summarize(article_text,0.12)
    elif text_length>= 1200 and text_length < 1300:
        summary = summarize(article_text,0.13)
    elif text_length>= 1100 and text_length < 1200:
        summary = summarize(article_text,0.14)
    elif text_length>= 1000 and text_length < 1100:
        summary = summarize(article_text,0.15)
    elif text_length>= 900 and text_length < 1000:
        summary = summarize(article_text,0.16)
    elif text_length>= 750 and text_length < 900:
        summary = summarize(article_text,0.2)
    elif text_length>= 500 and text_length < 750:
        summary = summarize(article_text,0.3)
    elif text_length >= 200 and text_length < 500:
        summary = summarize(article_text,0.5)
    else :
        summary = article_text
    return summary


culture_article()
time.sleep(5)
politic_article()
time.sleep(5)
economy_article()
time.sleep(5)
society_article()
time.sleep(5)
it_article()
time.sleep(5)
world_article()
# DB 파일 경로 매핑
