import time
import random
from flask import Flask, request, jsonify
import mysql.connector
import os
from config import MANAGER_IP, WORKER_IPS, MYSQL_PASSWORD
import traceback

app = Flask(__name__)


LATENCY_THRESHOLD = 0.03   # 30ms threshold, we do chose a random worker below this latency and the lowest ping worker if above

def connect(host):
    print(f"[CONNECT] Attempting connection to {host}")
    try:
        conn = mysql.connector.connect(
            host=host,
            user="root",
            password=MYSQL_PASSWORD,
            database="sakila",
            autocommit=True,
            connection_timeout=2
        )
        print(f"[CONNECT] Connected to {host}")
        return conn
    except Exception as e:
        print(f"[CONNECT] Failed to connect to {host}: {e}")
        raise

def measure_latency(host):
    try:
        print(f"[LATENCY] Measuring latency to {host}")
        start = time.time()
        db = connect(host)
        cursor = db.cursor()
        cursor.execute("SELECT 1;")
        cursor.fetchone()
        db.close()
        latency = time.time() - start
        print(f"[LATENCY] {host} -> {latency:.4f}s")
        return latency
    except Exception:
        print(f"[LATENCY] {host} measurement failed, returning high latency")
        return 9999

def is_cluster_under_load(latencies):
    avg_latency = sum(latencies.values()) / len(latencies)
    return avg_latency > LATENCY_THRESHOLD

def select_worker():
    latencies = {ip: measure_latency(ip) for ip in WORKER_IPS}
    print(f"[SELECT] Latencies: {latencies}")

    # Random Forwarding
    under_load = is_cluster_under_load(latencies)
    print(f"[SELECT] Cluster under load: {under_load}")
    if not under_load:
        choice = random.choice(WORKER_IPS)
        print(f"[SELECT] Not under load -> random choice: {choice}")
        return choice

    # Customized Forwarding
    best = min(latencies, key=latencies.get)
    print(f"[SELECT] Under load -> chosen best: {best}")
    return best

def is_read_query(sql):
    is_read = sql.strip().lower().startswith("select")
    print(f"[QUERY] is_read_query: {is_read} for sql: {sql[:80]!r}")
    return is_read

@app.route("/query", methods=["POST"])
def handle_query():
    print("[REQUEST] Received /query request")
    data = request.get_json()
    print(f"[REQUEST] Received data: {data}")
    if not data or "sql" not in data:
        return jsonify({"error": "Missing 'sql' field"}), 400

    sql = data["sql"]

    # try:
    #     # We select to which MySql Instance to forward the query
    #     print(f"[REQUEST] Received SQL: {sql[:200]!r}")
    #     if is_read_query(sql):
    #         host = select_worker()
    #     else:
    #         # Direct Hit
    #         host = MANAGER_IP
    #     print(f"[REQUEST] Forwarding to host: {host}")

    try:
        host = MANAGER_IP
        db = connect(host)
        cursor = db.cursor(dictionary=True)
        cursor.execute(sql)

        if is_read_query(sql):
            return jsonify(cursor.fetchall())

        return jsonify({"status": "success"})

    except Exception as e:
        print(f"[ERROR] Exception while handling query: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
if __name__ == "__main__":
    print(f"[STARTUP] MANAGER_IP={MANAGER_IP}, WORKER_IPS={WORKER_IPS}")
    print("[STARTUP] Starting Flask app on 0.0.0.0:80")
    app.run(host="0.0.0.0", port=80)