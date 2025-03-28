from flask import Blueprint, render_template, request, redirect, url_for, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, set_access_cookies, unset_jwt_cookies
from datetime import timedelta
from models.db import get_db_connection
import mysql.connector


auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        user_id = request.form.get("id")
        name = request.form.get("name")
        school = request.form.get("school")
        birthdate = request.form.get("birthdate")
        password = request.form.get("password")
        confirm = request.form.get("confirm_password")

        # 입력 검사
        if not all([user_id, name, school, birthdate, password, confirm]):
            return "모든 필드를 입력해주세요.", 400

        # 비밀번호 확인
        if password != confirm:
            return "비밀번호가 일치하지 않습니다.", 400

        # 비밀번호 해시로 암호화
        hashed_pw = generate_password_hash(password)

        # mysql 연결
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # 아이디 중복 확인
                cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
                if cursor.fetchone():
                    return "이미 사용 중인 아이디입니다.", 400

                # 회원 데이터 삽입
                cursor.execute("""
                    INSERT INTO users (id, name, school, birthdate, password)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, name, school, birthdate, hashed_pw))
            conn.commit()
            return redirect(url_for("auth.login"))
        except mysql.connector.Error as e:
            return f"회원가입 중 오류 발생: {e}", 500
        finally:
            conn.close()

    # GET 요청 시 signup.html 렌더링
    return render_template("signup.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("id")
        password = request.form.get("password")

        conn = get_db_connection()
        try:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT * FROM users WHERE id = %s", (username,))
                user = cursor.fetchone()

                if user and check_password_hash(user["password"], password):
                    access_token = create_access_token(
                        identity=user["id"],
                        expires_delta=timedelta(hours=24)
                    )

                    # JWT를 쿠키에 저장해서 응답
                    response = make_response(redirect(url_for("board.board")))
                    set_access_cookies(response, access_token)
                    return response
                else:
                    return "로그인 실패", 401
        finally:
            conn.close()
    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    response = make_response(redirect(url_for("main.home")))
    unset_jwt_cookies(response) # 쿠키 삭제
    return response