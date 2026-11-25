
import os
import re
from pathlib import Path

from flask import Flask, request, redirect, session, send_from_directory
from supabase import create_client
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# RUN TO RWANDA 6 - ONLINE BACKEND
load_dotenv()
app = Flask(__name__)
from werkzeug.routing import BaseConverter

class ProductKeyConverter(BaseConverter):
    regex = r"[A-Za-z0-9]{5}(?:-[A-Za-z0-9]{5}){2}"

app.url_map.converters["key"] = ProductKeyConverter
app.secret_key = os.environ["SECRET_KEY"]

app.config.update(
    SESSION_COOKIE_SECURE=os.environ.get("VERCEL") == "1",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_PATH="/run-to-rwanda-6",
)

ROOT = Path(__file__).resolve().parent


def get_db():
    return create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    )


def valid_key(key):
    try:
        result = (
            get_db()
            .table("product_keys")
            .select("key")
            .eq("key", key)
            .limit(1)
            .execute()
        )
        return bool(result.data)
    except Exception:
        return False


# QR CODE AUTHENTICATION

@app.route("/run-to-rwanda-6/<key:product_key>")
def authenticate_key(product_key):
    product_key = product_key.upper()

    if not valid_key(product_key):
        return "Invalid product key.", 403

    session.clear()
    session["product_key"] = product_key

    return redirect("/run-to-rwanda-6/login.html")


# SIGNUP

@app.route("/run-to-rwanda-6/signup", methods=["POST"])
def signup():
    key = session.get("product_key")

    if not key or not valid_key(key):
        return "Please scan a valid product QR code first.", 403

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if not 3 <= len(username) <= 24:
        return "Username must be 3-24 characters.", 400

    if len(password) < 8:
        return "Password must be at least 8 characters.", 400

    if not re.fullmatch(r"[A-Za-z0-9_]+", username):
        return "Username can only contain letters, numbers and underscores.", 400

    try:
        get_db().table("users").insert({
            "username": username,
            "username_norm": username.lower(),
            "password_hash": generate_password_hash(password)
        }).execute()

    except Exception:
        return "That username may already be taken. Please try another.", 409

    return redirect("/run-to-rwanda-6/login.html?signup=success")


# LOGIN

@app.route("/run-to-rwanda-6/login", methods=["POST"])
def login():
    key = session.get("product_key")

    if not key or not valid_key(key):
        return "Please scan a valid product QR code first.", 403

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    try:
        result = (
            get_db()
            .table("users")
            .select("*")
            .eq("username_norm", username.lower())
            .limit(1)
            .execute()
        )

        if not result.data:
            return "Incorrect username or password.", 401

        user = result.data[0]

        if not check_password_hash(user["password_hash"], password):
            return "Incorrect username or password.", 401

        session.clear()
        session["product_key"] = key
        session["user_id"] = user["id"]
        session["username"] = user["username"]

        return redirect("/run-to-rwanda-6/dashboard")

    except Exception:
        return "Login service temporarily unavailable.", 500


# GAME PAGE

@app.route("/run-to-rwanda-6/dashboard")
def dashboard():
    key = session.get("product_key")

    if not session.get("user_id") or not key:
        return redirect("/run-to-rwanda-6/")

    if not valid_key(key):
        session.clear()
        return "Invalid product key.", 403

    return send_from_directory(ROOT, "welcomepage.html")


# LOGOUT

@app.route("/run-to-rwanda-6/logout")
def logout():
    session.clear()
    return redirect("/run-to-rwanda-6/")


@app.route("/")
@app.route("/run-to-rwanda-6/")
def home():
    return "RUN TO RWANDA 6 - Please scan your product QR code to continue."
@app.route("/run-to-rwanda-6/login.html")
def login_page():
    return send_from_directory(ROOT / "public", "login.html")
@app.route("/run-to-rwanda-6/signup.html")
def signup_page():
    return send_from_directory(ROOT / "public", "signup.html")


@app.route("/run-to-rwanda-6/<path:filename>")
def public_files(filename):
    return send_from_directory(ROOT / "public", filename)
if __name__ == "__main__":
    app.run(debug=True)