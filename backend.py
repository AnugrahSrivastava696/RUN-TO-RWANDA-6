
import sqlite3
import secrets
from pathlib import Path
import os
import sys
import threading
import webbrowser
import json
import hashlib
import re
import subprocess
import urllib.request

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

GITHUB_RELEASE_API = (
    "https://api.github.com/repos/"
    "AnugrahSrivastava696/RUN-TO-RWANDA-6/releases/latest"
)

EXE_NAME = "RUN_TO_RWANDA_6.exe"

# ==================================
# APPLICATION FILE LOCATIONS
# ==================================

if getattr(sys, "frozen", False):
    RESOURCE_DIR = Path(sys._MEIPASS)

    DATA_DIR = (
        Path(os.environ.get("APPDATA", Path.home()))
        / "RUN TO RWANDA 6"
    )
else:
    RESOURCE_DIR = Path(__file__).resolve().parent
    DATA_DIR = RESOURCE_DIR

DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE = DATA_DIR / "accounts.db"
VERSION_FILE = DATA_DIR / "version.txt"

app = Flask(__name__, static_folder=None)

SECRET_FILE = DATA_DIR / ".secret_key"

if not SECRET_FILE.exists():
    SECRET_FILE.write_text(secrets.token_hex(32))

app.secret_key = SECRET_FILE.read_text().strip()


# ==================================
# GITHUB AUTO-UPDATER
# ==================================

def check_for_updates():

    # Only update packaged Windows EXEs.
    if not getattr(sys, "frozen", False):
        return

    if os.name != "nt":
        return

    try:
        req = urllib.request.Request(
            GITHUB_RELEASE_API,
            headers={"User-Agent": "RUN-TO-RWANDA-6"}
        )

        with urllib.request.urlopen(req, timeout=15) as response:
            release = json.loads(response.read().decode("utf-8"))

        latest_version = release.get("tag_name", "")

        if not re.fullmatch(r"[A-Za-z0-9._-]+", latest_version):
            return

        assets = [
            asset for asset in release.get("assets", [])
            if asset.get("name") == EXE_NAME
        ]

        if not assets:
            print("No EXE found in GitHub Release.")
            return

        asset = assets[0]

        # First launch: the currently installed EXE is the
        # version uploaded in the initial release.

        # The original installed game is version v.0.0.1.
        # Keep track of its version even on the first launch.
if not VERSION_FILE.exists():
    VERSION_FILE.write_text(latest_version)
    return

current_version = VERSION_FILE.read_text().strip()


        if current_version == latest_version:
            return

        print("A new RUN TO RWANDA 6 update is available!")

        game_path = Path(sys.executable).resolve()
        download_path = game_path.with_name("game_update.exe")

        download_request = urllib.request.Request(
            asset["browser_download_url"],
            headers={"User-Agent": "RUN-TO-RWANDA-6"}
        )

        sha256 = hashlib.sha256()

        with urllib.request.urlopen(
            download_request, timeout=120
        ) as response:
            with open(download_path, "wb") as output:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break

                    output.write(chunk)
                    sha256.update(chunk)

        # Verify the download when GitHub provides a SHA-256 digest.
        expected_digest = asset.get("digest")

        if expected_digest and expected_digest.startswith("sha256:"):
            if sha256.hexdigest() != expected_digest[7:]:
                download_path.unlink(missing_ok=True)
                print("Update verification failed.")
                return

        print("Update downloaded. Restarting with the new version...")

        batch_path = DATA_DIR / "replace_game.bat"

        pid = os.getpid()

        batch_code = f"""@echo off
:wait
tasklist /FI "PID eq {pid}" /FO CSV /NH | findstr /C:""" + f'''"{pid}"''' + f""" >nul
if not errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto wait
)

copy /Y "{download_path}" "{game_path}" >nul

if errorlevel 1 goto failed

del "{download_path}"
> "{VERSION_FILE}" echo {latest_version}
start "" "{game_path}"
del "%~f0"
exit /b

:failed
del "{download_path}"
start "" "{game_path}"
del "%~f0"
"""

        batch_path.write_text(batch_code, encoding="utf-8")

        subprocess.Popen(
            ["cmd.exe", "/c", str(batch_path)],
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        sys.exit(0)

    except Exception as error:
        print("Update check failed:", error)
        print("Starting the existing game instead.")


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

    check_for_updates()

    initialize_database()

    print("RUN TO RWANDA 6 BACKEND STARTED!")

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
