
import sqlite3
import secrets
from pathlib import Path
import os
import sys
import threading
import webbrowser

from flask import (
    Flask, request, redirect,
    session, send_from_directory
)
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

# ==================================
# RUN TO RWANDA 6 - BACKEND
# ==================================

# ==================================
# APPLICATION FILE LOCATIONS
# ==================================

if getattr(sys, "frozen", False):
    # Running as a packaged EXE
    RESOURCE_DIR = Path(sys._MEIPASS)

    DATA_DIR = (
        Path(os.environ.get("APPDATA", Path.home()))
        / "RUN TO RWANDA 6"
    )
else:
    # Running normally with Python
    RESOURCE_DIR = Path(__file__).resolve().parent
    DATA_DIR = RESOURCE_DIR

DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE = DATA_DIR / "accounts.db"

app = Flask(__name__, static_folder=None)

# Generate and preserve a secret key locally.
SECRET_FILE = DATA_DIR / ".secret_key"

if not SECRET_FILE.exists():
    SECRET_FILE.write_text(secrets.token_hex(32))

app.secret_key = SECRET_FILE.read_text().strip()

# ==================================
# DATABASE
# ==================================

def connect_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with connect_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL
            )
        """)


# ==================================
# HTML PAGES
# ==================================

@app.route("/")
def home():
    return redirect("/login.html")


@app.route("/login.html")
def login_page():
    return send_from_directory(RESOURCE_DIR, "login.html")


@app.route("/signup.html")
def signup_page():
    return send_from_directory(RESOURCE_DIR, "signup.html")


@app.route("/style.css")
def stylesheet():
    return send_from_directory(RESOURCE_DIR, "style.css")


@app.route("/script.js")
def javascript():
    return send_from_directory(RESOURCE_DIR, "script.js")


# ==================================
# SIGNUP SYSTEM
# ==================================

@app.route("/signup", methods=["POST"])
def signup():

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if not 3 <= len(username) <= 24:
        return "Username must be 3-24 characters.", 400

    if len(password) < 8:
        return "Password must be at least 8 characters.", 400

    # Hash the password before storing it.
    password_hash = generate_password_hash(password)

    try:
        with connect_db() as db:
            db.execute(
                """
                INSERT INTO users (username, password_hash)
                VALUES (?, ?)
                """,
                (username, password_hash)
            )

    except sqlite3.IntegrityError:
        return "That username is already taken.", 409

    return redirect("/login.html?signup=success")


# ==================================
# LOGIN SYSTEM
# ==================================

@app.route("/login", methods=["POST"])
def login():

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    with connect_db() as db:
        user = db.execute(
            """
            SELECT * FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()

    if user is None:
        return "Incorrect username or password.", 401

    if not check_password_hash(
        user["password_hash"], password
    ):
        return "Incorrect username or password.", 401

    # Login successful!
    session.clear()
    session["user_id"] = user["id"]
    session["username"] = user["username"]

    return redirect("/dashboard")


# ==================================
# DASHBOARD
# ==================================

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login.html")

    return send_from_directory(RESOURCE_DIR, "welcomepage.html")



# ==================================
# LOGOUT
# ==================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login.html")
@app.route("/gta6.mp4")
def background_video():
    return send_from_directory(RESOURCE_DIR, "gta6.mp4")
@app.route("/videoend.png")
def ending_image():
    return send_from_directory(RESOURCE_DIR, "videoend.png")


# ==================================
# START SERVER
# ==================================

if __name__ == "__main__":

    initialize_database()

    print("RUN TO RWANDA 6 BACKEND STARTED!")

    # Open the application automatically
    threading.Timer(
        1.5,
        lambda: webbrowser.open("http://127.0.0.1:5000")
    ).start()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False
    )
