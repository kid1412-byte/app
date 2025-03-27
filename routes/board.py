from flask import Blueprint, render_template, request, redirect, url_for, make_response, current_app, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.db import get_db_connection
from werkzeug.utils import secure_filename
import mysql.connector
import os

board_bp = Blueprint("board", __name__)

# 게시판 리스트
@board_bp.route("/board")
@jwt_required()
def board():
    search_type = request.args.get("search_type", "title") # 게시글 검색 기준 제목을 디폴트
    keyword = request.args.get("keyword", "") # 검색창 빈 문자열
    page = int(request.args.get("page", 1))  # 현재 페이지 번호
    per_page = 10 # 한 페이지당 게시글 갯수
    offset = (page - 1) * per_page # 게시글 몇번째부터 가져와야할지 위치

    # mysql 연결
    conn = get_db_connection()
    if conn is None:
        return "DB 연결 실패", 500

    try:
        with conn.cursor(dictionary=True) as cursor:
            like_keyword = f"%{keyword}%" # like문용 와일드 카드 추가

            if keyword:
                if search_type == "title": # 제목 기준 검색
                    count_query = "SELECT COUNT(*) as cnt FROM board WHERE title LIKE %s" # 페이지네이션용 게시글 갯수 조회
                    # 게시판 리스트용 게시글 데이터 조회
                    data_query = """SELECT * FROM board 
                                    WHERE title LIKE %s 
                                    ORDER BY created_at DESC 
                                    LIMIT %s OFFSET %s"""
                    # LIMIT = 몇개 조회할건지
                    # OFFSET = 어디서부터 조회할건지

                     # sql문에 넣을 파라미터
                    count_params = (like_keyword,) # 튜플 형태
                    data_params = (like_keyword, per_page, offset)

                elif search_type == "content": # 내용 기준 검색
                    count_query = "SELECT COUNT(*) as cnt FROM board WHERE content LIKE %s"
                    data_query = """SELECT * FROM board 
                                    WHERE content LIKE %s 
                                    ORDER BY created_at DESC 
                                    LIMIT %s OFFSET %s"""
                    count_params = (like_keyword,) # 튜플 형태
                    data_params = (like_keyword, per_page, offset)

                else:  # 제목 + 내용 기준 검색
                    count_query = "SELECT COUNT(*) as cnt FROM board WHERE title LIKE %s OR content LIKE %s"
                    data_query = """SELECT * FROM board 
                                    WHERE title LIKE %s OR content LIKE %s 
                                    ORDER BY created_at DESC 
                                    LIMIT %s OFFSET %s"""
                    count_params = (like_keyword, like_keyword)
                    data_params = (like_keyword, like_keyword, per_page, offset)
            else: # 검색 아닐 땐 전체 조회
                count_query = "SELECT COUNT(*) as cnt FROM board"
                data_query = """SELECT * FROM board 
                                ORDER BY created_at DESC 
                                LIMIT %s OFFSET %s"""
                count_params = ()
                data_params = (per_page, offset)

            # 총 게시글 수 조회
            cursor.execute(count_query, count_params)
            total_count = cursor.fetchone()["cnt"] # 전체 게시글 갯수 딕셔너리 형태인 cnt키에 해당하는 값을 받음
            total_pages = (total_count + per_page - 1) // per_page # 총 페이지 수

            # 게시글 리스트 조회
            cursor.execute(data_query, data_params)
            posts = cursor.fetchall() # 게시글 데이터 딕셔너리로 받음
        
        # 템플릿으로 데이터 전달
        return render_template("board.html",
                               data_list=posts,
                               search_type=search_type,
                               keyword=keyword,
                               page=page,
                               total_pages=total_pages)
    finally:
        conn.close()

# 게시글 생성
@board_bp.route("/write", methods=["GET", "POST"])
@jwt_required()
def write():
    # GET 요청시 write.html 반환
    if request.method == "GET":
        return render_template('write.html')
    
    # POST 요청시 수행
    # html 각 name속성을 가진 폼에서 입력된 내용 가져옴
    title = request.form.get("title")
    author = get_jwt_identity()
    content = request.form.get("content")
    file = request.files.get("file")
    filename = None

    if file and file.filename != "":
        filename = secure_filename(file.filename)
        file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))

    # 입력 검사
    if not all([title, content]):
        return "모든 필드를 입력해주세요.", 400
    
    # mysql 연결
    conn = get_db_connection()
    if conn is None:
        return "DB 연결 실패", 500

    # 게시글 데이터 삽입 SQL문 실행
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO board (title, author, content, filename) VALUES (%s, %s, %s, %s)",
                (title, author, content, filename)
            )
        conn.commit()
        return redirect(url_for("board.board"))
    except mysql.connector.Error as e:
        return f"글 작성 중 오류 발생: {e}", 500
    finally:
        conn.close()

# 게시글 상세 보기
@board_bp.route("/post/<int:post_id>")
@jwt_required()
def post(post_id):
    conn = get_db_connection() # mysql 연결
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
            
        # 조회한 게시글 데이터를 post.html에 전달
        return render_template("post.html", post=post)
    except mysql.connector.Error as e:
        return f"게시글 조회 중 오류 발생: {e}", 500
    finally:
        conn.close()

# 게시글 수정
@board_bp.route("/edit/<int:post_id>", methods=["GET", "POST"])
@jwt_required()
def edit(post_id):
    conn = get_db_connection() # mysql 연결
    if conn is None:
        return "DB 연결 실패", 500

    try:
        with conn.cursor(dictionary=True) as cursor:
            # GET 요청 시
            if request.method == "GET":
                # 게시글 조회
                cursor.execute("SELECT * FROM board WHERE id = %s", (post_id,))
                post = cursor.fetchone()
                if not post:
                    return "존재하지 않는 게시글입니다.", 
                # 조회된 데이터를 edit.html에 전달
                return render_template("edit.html", post=post)
            
            # POST 요청 시
            # 수정된 내용
            title = request.form.get("title")
            author = request.form.get("author")
            content = request.form.get("content")
             
            # 입력 검사
            if not all([title, author, content]):
                return "모든 필드를 입력해주세요.", 400

            # 수정된 내용으로 업데이트
            cursor.execute("""
                UPDATE board SET title = %s, author = %s, content = %s
                WHERE id = %s
            """, (title, author, content, post_id))
            conn.commit() # db 변경 내용 저장
            # 해당 게시글의 id값과 함께 post 라우트로 이동
            return redirect(url_for('board.post', post_id=post_id))
    finally:
        conn.close()

# 게시글 삭제
@board_bp.route("/delete/<int:post_id>")
@jwt_required()
def delete(post_id):
    conn = get_db_connection() # mysql 연결
    if conn is None:
        return "DB 연결 실패", 500

    try:
        with conn.cursor() as cursor:
            # 테이블에서 해당 게시글 id를 가진 행 삭제
            cursor.execute("DELETE FROM board WHERE id = %s", (post_id,))
            conn.commit() # db 변경 내용 저장
        # 삭제 후 게시판으로 이동
        return redirect(url_for('board.board'))
    finally:
        conn.close()

@board_bp.route("/uploads/<filename>")
@jwt_required()
def download_file(filename):
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    return send_from_directory(upload_folder, filename, as_attachment=True)