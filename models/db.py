import os
import mysql.connector
from dotenv import load_dotenv

# .env 파일 불러오기
if not load_dotenv():
    raise Exception(".env 파일을 찾을 수 없음.")

# 환경 변수 로드
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_ROOT_PASSWORD = os.getenv("MYSQL_ROOT_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

# mysql 연결
def get_db_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user="root",
        password=MYSQL_ROOT_PASSWORD,
        database=MYSQL_DATABASE
    )

# 테이블 자동 생성
def create_tables():
    conn = get_db_connection() # mysql 연결 함수
    cursor = conn.cursor() # cursor()로 객체 생성
    # 게시판 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS board (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(30) NOT NULL,
            author VARCHAR(30) NOT NULL,
            content TEXT NOT NULL,
            filename VARCHAR(255),
            created_at DATE DEFAULT (CURRENT_DATE),
            views INT DEFAULT 0,
            is_secret BOOLEAN DEFAULT FALSE,
            post_password VARCHAR(100)
        )
    """)
    # board라는 이름의 테이블이 없다면 생성
    # id / 자동 증가 / 기본키
    # 제목 / 30자 문자열 / null값 X
    # 작성자 / 30자 문자열 / null값 X
    # 내용 / 긴 문자열 / null값 X
    # 파일 이름 / 255자 문자열
    # 작성 날짜 / 날짜 / 값 지정 없으면 현재 날짜로 세팅
    # 조회수 / 정수 / 디폴트값 0
    # 비밀글 여부 / 불리안 / 디폴트값 false
    # 비밀글 비밀번호 / 100자 문자열

    # 사용자 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(50) NOT NULL,
            school VARCHAR(100) NOT NULL,
            birthdate DATE NOT NULL,
            password VARCHAR(255) NOT NULL,
            profile_image VARCHAR(255)
        )
    """)
    # users라는 이름의 테이블이 없다면 생성
    # id / 30자 문자열 / 기본키
    # 이름 / 30자 문자열 / null값 X
    # 학교 / 100자 문자열 / null값 X
    # 생일 / 날짜 / null값 X
    # 비밀번호 / 255자 문자열 / null값 X
    # 프로필 사진 / 255자 문자열
    
    conn.commit() # db 변경 내용 저장
    cursor.close() # cursor 닫기
    conn.close() # mysql 연결 끊기