from flask import Blueprint, render_template

# 블루프린트 객체 생성
main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def home():
    return render_template("home.html")