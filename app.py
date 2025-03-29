from flask import Flask
from config import Config
from models.db import create_tables
from flask_jwt_extended import JWTManager
import os

# 기능 모듈들 임포트
from routes.main import main_bp
from routes.auth import auth_bp
from routes.board import board_bp

app = Flask(__name__)
app.config.from_object(Config) # jwt 관련 환경설정
app.config["JWT_COOKIE_CSRF_PROTECT"] = False # 개발중엔 CSRF 끄기


# 업로드 폴더가 없으면 생성
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
# 프로필 업로드 폴더가 없으면 생성
os.makedirs(os.path.join(app.root_path, app.config["PROFILE_UPLOAD_FOLDER"]), exist_ok=True)

# jwt 관련 기능 사용
jwt = JWTManager(app)

# 기능 모듈들 블루프린트로 등록
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(board_bp)

if __name__ == "__main__":
    create_tables()
    app.run(host="0.0.0.0", port=5000, debug=True)