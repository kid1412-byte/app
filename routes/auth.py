from flask import Blueprint, render_template, request, redirect, url_for, make_response, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_jwt_extended import create_access_token, set_access_cookies, unset_jwt_cookies, jwt_required, get_jwt_identity, verify_jwt_in_request
from datetime import timedelta
from models.db import get_db_connection
import mysql.connector
import os


auth_bp = Blueprint("auth", __name__)

# 회원가입
@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        user_id = request.form.get("id") # id
        name = request.form.get("name") # 이름
        school = request.form.get("school") # 학교
        birthdate = request.form.get("birthdate") # 생일
        password = request.form.get("password") # 비밀번호
        confirm = request.form.get("confirm_password") # 비밀번호 확인

        # 입력 검사
        if not all([user_id, name, school, birthdate, password, confirm]):
            return render_template("partials/alert.html", message="모든 필드를 입력해주세요.")

        # 비밀번호 확인
        if password != confirm:
            return render_template("partials/alert.html", message="비밀번호가 일치하지 않습니다.")

        # 비밀번호 해시로 암호화
        hashed_pw = generate_password_hash(password)

        # mysql 연결
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # 아이디 중복 확인
                cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
                if cursor.fetchone():
                    return render_template("partials/alert.html", message="이미 사용 중인 아이디입니다.")

                # 회원 데이터 삽입
                cursor.execute("""
                    INSERT INTO users (id, name, school, birthdate, password)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, name, school, birthdate, hashed_pw))
            conn.commit()
            return render_template("partials/alert.html", message="회원가입이 완료되었습니다.", redirect_url=url_for("auth.login"))
        except mysql.connector.Error as e:
            return render_template("partials/alert.html", message=f"회원가입 중 오류 발생: {e}")
        finally:
            conn.close()

    # GET 요청 시 signup.html 렌더링
    return render_template("signup.html")

# 로그인
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # POST 요청 시
    if request.method == "POST":
        # 폼에서 입력된 id, 비밀번호 가져옴
        username = request.form.get("id")
        password = request.form.get("password")
        
        # db 연결
        conn = get_db_connection()
        try:
            with conn.cursor(dictionary=True) as cursor:
                # db에서 사용자 조회
                cursor.execute("SELECT * FROM users WHERE id = %s", (username,))
                user = cursor.fetchone()

                # 사용자 데이터와 비교
                if user and check_password_hash(user["password"], password):
                    # 비밀번호 같을 시 jwt토큰 생성
                    access_token = create_access_token(
                        identity=user["id"],
                        expires_delta=timedelta(hours=24) # 토큰 유효시간
                    )

                    # jwt를 쿠키에 저장해서 응답
                    response = make_response(redirect(url_for("board.board")))
                    set_access_cookies(response, access_token)
                    return response
                else:
                    # 불일치 시 경고창 띄움
                    return render_template("partials/alert.html", message="아이디 또는 비밀번호가 일치하지 않습니다.")
        finally:
            conn.close()
    # GET 요청 시
    return render_template("login.html")

# 로그아웃
@auth_bp.route("/logout")
def logout():
    response = make_response(redirect(url_for("main.home")))
    unset_jwt_cookies(response) # 쿠키 삭제
    return response

# 토큰 유효성 검사
@auth_bp.route("/check-auth")
def check_auth():
    try:
        verify_jwt_in_request(optional=True)  # 선택적 토큰 검증
        identity = get_jwt_identity()
        if identity is None:
            return "", 401
        return "", 200
    except Exception:
        return "", 401

# 아이디 찾기
@auth_bp.route("/find_id", methods=["GET", "POST"])
def find_id():
    # POST 요청 시
    if request.method == "POST":
        name = request.form.get("name") # 이름
        birthdate = request.form.get("birthdate") # 생일

        # mysql 연결
        conn = get_db_connection()
        with conn.cursor(dictionary=True) as cursor:
            # 이름과 생일이 일치하는 사용자 조회
            cursor.execute("SELECT id FROM users WHERE name=%s AND birthdate=%s", (name, birthdate))
            user = cursor.fetchone()
        conn.close()

        if user: # 일치하는 사용자가 있으면 id 제공
            return render_template("partials/alert.html", message=f"아이디는 '{user['id']}' 입니다.", redirect_url=url_for("auth.login"))
        else: # 일치하는 사용자가 없으면 경고창 띄움
            return render_template("partials/alert.html", message="일치하는 사용자를 찾을 수 없습니다.")
    # GET 요청 시
    return render_template("find_id.html")

# 비밀번호 리셋
@auth_bp.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    # POST 요청 시
    if request.method == "POST":
        user_id = request.form.get("id") # id
        name = request.form.get("name") # 이름
        birthdate = request.form.get("birthdate") # 생일
        new_password = request.form.get("new_password") # 새 비밀번호
        confirm = request.form.get("confirm_password") # 새 비밀번호 확인

        conn = get_db_connection()
        with conn.cursor() as cursor:
            # id와 이름 생일이 일치하는 사용자 조회
            cursor.execute("SELECT * FROM users WHERE id=%s AND name=%s AND birthdate=%s", (user_id, name, birthdate))
            if cursor.fetchone():
                hashed_pw = generate_password_hash(new_password) # 비밀번호 해시함수로 암호화
                cursor.execute("UPDATE users SET password=%s WHERE id=%s", (hashed_pw, user_id)) # 비밀번호 업데이트
                conn.commit()
                return render_template("partials/alert.html", message="비밀번호가 성공적으로 변경되었습니다.", redirect_url=url_for("auth.login"))
            else: # 일치하는 사용자 없음
                return render_template("partials/alert.html", message="입력하신 정보와 일치하는 계정이 없습니다.")
        conn.close()
    # GET 요청 시
    return render_template("reset_password.html")

# 프로필
@auth_bp.route("/profile/<user_id>")
@jwt_required()
def profile(user_id):
    post_id = request.args.get("post_id") # 게시글로 돌아가기 위한 post_id
    current_user_id = get_jwt_identity() # jwt토큰에서 현재 사용자 추출
    
    # mysql 연결
    conn = get_db_connection()
    with conn.cursor(dictionary=True) as cursor:
        # 사용자 조회
        cursor.execute("SELECT id, name, school, birthdate, profile_image FROM users WHERE id=%s", (user_id,))
        user = cursor.fetchone()
    conn.close()

    if not user:
        return render_template("partials/alert.html", message="존재하지 않는 사용자입니다.")

    # 본인 여부 체크해서 전달
    is_owner = (current_user_id == user_id)
    return render_template("profile.html", user=user, is_owner=is_owner, post_id=post_id)

# 프로필 사진 업로드
@auth_bp.route("/profile/upload", methods=["POST"])
@jwt_required()
def upload_profile_image():
    user_id = get_jwt_identity() # 토큰에서 사용자 추출
    file = request.files.get("profile_image") # 프로필 사진 

    if file and file.filename != "":
        filename = secure_filename(file.filename) # 파일명에 포함된 특수문자, 공백, 경로 제거
        filepath = os.path.join(current_app.config["PROFILE_UPLOAD_FOLDER"], filename) # 저장 경로 설정
        file.save(filepath) # 프로필 사진 저장

        # DB에 파일 이름만 저장
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("UPDATE users SET profile_image=%s WHERE id=%s", (filename, user_id))
        conn.commit()
        conn.close()

        return redirect(url_for("auth.profile", user_id=user_id))

    return render_template("partials/alert.html", message="파일을 선택해주세요.")

# 마이페이지
@auth_bp.route("/mypage")
@jwt_required()
def mypage():
    user_id = get_jwt_identity() # 토큰에서 사용자 주출
    return redirect(url_for('auth.profile', user_id=user_id))
