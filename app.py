import os
import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, jsonify
from dotenv import load_dotenv

if not load_dotenv():
    raise Exception(".env 파일을 찾을 수 없음.")

app = Flask(__name__)

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
def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS board (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(30) NOT NULL,
            author VARCHAR(30) NOT NULL,
            content TEXT NOT NULL,
            created_at DATE DEFAULT (CURRENT_DATE),
            views INT DEFAULT 0
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

@app.route("/")
def home():
    return render_template('home.html')

@app.route("/board")
def board():
    conn = get_db_connection()
    if conn is None:
        return "DB 연결 실패", 500

    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT id, title, author, created_at, views FROM board ORDER BY created_at DESC")
            posts = cursor.fetchall()  #데이터를 리스트 형태로 가져옴

        return render_template("board.html", data_list=posts)  #데이터를 html에 전달
    except mysql.connector.Error as e:
        return f"게시글 불러오기 오류: {e}", 500
    finally:
        conn.close()

@app.route("/write", methods=["GET", "POST"])
def write():
    # GET 요청시 write.html 반환
    if request.method == "GET":
        return render_template('write.html')
    
    # POST 요청시 수행
    # html 각 name속성을 가진 폼에서 입력된 내용 가져오기
    title = request.form.get("title")
    author = request.form.get("author")
    content = request.form.get("content")

    # 입력 검사
    if not all([title, author, content]):
        return "모든 필드를 입력해주세요.", 400
    
    # DB 연결
    conn = get_db_connection()
    if conn is None:
        return "DB 연결 실패", 500

    # 게시글 데이터 삽입 SQL문 실행
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO board (title, author, content) VALUES (%s, %s, %s)",
                (title, author, content)
            )
        conn.commit()
        return redirect(url_for("board"))
    except mysql.connector.Error as e:
        return f"글 작성 중 오류 발생: {e}", 500
    finally:
        conn.close()

@app.route("/post/<int:post_id>")
def post(post_id):
    conn = get_db_connection()
    if conn is None:
        return "DB 연결 실패", 500

    try:
        with conn.cursor(dictionary=True) as cursor:
            # 조회수 증가
            cursor.execute("UPDATE board SET views = views + 1 WHERE id = %s", (post_id,))
            conn.commit()

            # 게시글 조회
            cursor.execute("SELECT * FROM board WHERE id = %s", (post_id,))
            post = cursor.fetchone()

            if post is None:
                return "존재하지 않는 게시글입니다.", 404

        return render_template("post.html", post=post)
    except mysql.connector.Error as e:
        return f"게시글 조회 중 오류 발생: {e}", 500
    finally:
        conn.close()

# 게시글 수정
@app.route("/edit/<int:post_id>", methods=["GET", "POST"])
def edit(post_id):
    conn = get_db_connection()
    if conn is None:
        return "DB 연결 실패", 500

    try:
        with conn.cursor(dictionary=True) as cursor:
            if request.method == "GET":
                # 게시글 조회
                cursor.execute("SELECT * FROM board WHERE id = %s", (post_id,))
                post = cursor.fetchone()
                if not post:
                    return "존재하지 않는 게시글입니다.", 404
                return render_template("edit.html", post=post)

            # 수정된 내용
            title = request.form.get("title")
            author = request.form.get("author")
            content = request.form.get("content")

            if not all([title, author, content]):
                return "모든 필드를 입력해주세요.", 400

            # 수정된 내용으로 업데이트
            cursor.execute("""
                UPDATE board SET title = %s, author = %s, content = %s
                WHERE id = %s
            """, (title, author, content, post_id))
            conn.commit()
            return redirect(url_for('post', post_id=post_id))
    finally:
        conn.close()

# 게시글 삭제
@app.route("/delete/<int:post_id>")
def delete(post_id):
    conn = get_db_connection()
    if conn is None:
        return "DB 연결 실패", 500

    try:
        with conn.cursor() as cursor:
            # db에서 삭제
            cursor.execute("DELETE FROM board WHERE id = %s", (post_id,))
            conn.commit()
        return redirect(url_for('board'))
    finally:
        conn.close()



if __name__ == "__main__":
    create_table()
    app.run(host="0.0.0.0", port=5000, debug=os.getenv("FLASK_DEBUG") == "True")
