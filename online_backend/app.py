
import os
import requests

from flask import Flask, request, jsonify
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

app = Flask(__name__)

SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

REST_URL = f"{SUPABASE_URL}/rest/v1/users"

HEADERS = {
    "apikey": SUPABASE_SERVICE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    "Content-Type": "application/json"
}


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "online",
        "application": "RUN TO RWANDA 6"
    })


@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True) or {}

    username = data.get("username")
    password = data.get("password")

    if not isinstance(username, str) or not isinstance(password, str):
        return jsonify({"error": "Invalid input."}), 400

    username = username.strip()

    if not 3 <= len(username) <= 24:
        return jsonify({"error": "Username must be 3-24 characters."}), 400

    if len(password) < 8 or len(password) > 256:
        return jsonify({"error": "Password must be 8-256 characters."}), 400

    password_hash = generate_password_hash(password)

    try:
        response = requests.post(
            REST_URL,
            headers={**HEADERS, "Prefer": "return=minimal"},
            json={
                "username": username,
                "password_hash": password_hash
            },
            timeout=10
        )

        if response.status_code == 201:
            return jsonify({"message": "Account created!"}), 201

        if response.status_code == 409:
            return jsonify({"error": "That username is already taken."}), 409

        app.logger.error(
            "Supabase signup error: HTTP %s",
            response.status_code
        )

        return jsonify({"error": "Account service unavailable."}), 503

    except requests.RequestException:
        app.logger.exception("Supabase signup request failed")
        return jsonify({"error": "Account service unavailable."}), 503


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    username = data.get("username")
    password = data.get("password")

    if not isinstance(username, str) or not isinstance(password, str):
        return jsonify({"error": "Incorrect username or password."}), 401

    username = username.strip()

    if not username or len(username) > 24 or len(password) > 256:
        return jsonify({"error": "Incorrect username or password."}), 401

    try:
        response = requests.get(
            REST_URL,
            headers=HEADERS,
            params={
                "username": f"eq.{username}",
                "select": "id,username,password_hash",
                "limit": "1"
            },
            timeout=10
        )

        if response.status_code != 200:
            app.logger.error(
                "Supabase login error: HTTP %s",
                response.status_code
            )
            return jsonify({"error": "Account service unavailable."}), 503

        users = response.json()

        if not users or not check_password_hash(
            users[0]["password_hash"], password
        ):
            return jsonify({"error": "Incorrect username or password."}), 401

        return jsonify({
            "message": "Login successful!",
            "user": {
                "id": users[0]["id"],
                "username": users[0]["username"]
            }
        }), 200

    except requests.RequestException:
        app.logger.exception("Supabase login request failed")
        return jsonify({"error": "Account service unavailable."}), 503
