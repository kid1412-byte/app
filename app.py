from flask import Flask, render_template
import mysql.connector

app = Flask(__name__)

# mysql 연결
def get_db_connection():
    return mysql.connector.connect(
        host="mysql",
        user="root",
        password="rootpassword",
        database="flask_db"
    )

@app.route("/")
def home():
    return render_template('home.html')

@app.route("/board")
def board():
    return render_template('board.html')

@app.route("/write")
def write():
    return render_template('write.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
