from flask import Flask
from config import Config
from models.db import create_tables
from flask_jwt_extended import JWTManager
import os

# 블루프린트 등록
from routes.main import main_bp
from routes.auth import auth_bp
from routes.board import board_bp

app = Flask(__name__)
app.config.from_object(Config)
app.config["JWT_COOKIE_CSRF_PROTECT"] = False # 개발중엔 CSRF 끄기


# 파일 업로드 경로 설정
app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

jwt = JWTManager(app)

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(board_bp)

if __name__ == "__main__":
    create_tables()
    app.run(host="0.0.0.0", port=5000, debug=True)