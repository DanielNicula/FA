import logging
import re
import requests
from flask import Flask, request, jsonify
import os
from constants import PROXY_IP, API_KEY

PROXY_URL = f"http://{PROXY_IP}/API"

app = Flask(__name__)
handler = logging.FileHandler("gatekeeper.log")  
app.logger.addHandler(handler)
app.logger.setLevel(logging.DEBUG)

UNSAFE_SQL_PATTERNS = [
    r"\bdrop\b",
    r"\btruncate\b",
    r"\bdelete\s+from\s+\w+\s*;\s*$",
    r"\bshutdown\b",
    r"\bgrant\b",
    r"\brevoke\b"
]

def is_authenticated(req):
    token = req.headers.get("Auth")
    return token == API_KEY   # Replace with proper checks later

def is_safe_sql(sql):
    sql_lower = sql.lower()
    for pattern in UNSAFE_SQL_PATTERNS:
        if re.search(pattern, sql_lower):
            return False
    return True


@app.route("/API", methods=["POST"])
def handle_query():
    app.logger.info("[REQUEST] User requested /API")

    if not PROXY_IP:
        return jsonify({"error": "Gatekeeper misconfigured, no PROXY_IP set"}), 500

    if not is_authenticated(request):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    if not data or "sql" not in data:
        return jsonify({"error": "Missing SQL"}), 400

    sql = data["sql"]
    app.logger.info(f"[REQUEST] SQL Received: {sql}")

    if not is_safe_sql(sql):
        app.logger.warning(f"[BLOCKED] Unsafe SQL detected: {sql}")
        return jsonify({"error": "Unsafe SQL operation blocked"}), 400

    try:
        res = requests.post(PROXY_URL, json={"sql": sql}, timeout=5)
        return jsonify(res.json()), res.status_code
    except Exception as e:
        app.logger.error(f"[ERROR] Could not reach proxy: {e}")
        return jsonify({"error": "Proxy unreachable"}), 500


@app.route("/")
def home():
    return jsonify({"message": "Gatekeeper online"})


if __name__ == "__main__":
    print(f"[STARTUP] Gatekeeper running → Proxy = {PROXY_URL}")
    app.run(host="0.0.0.0", port=80)