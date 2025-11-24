import logging
import time
import random
from flask import Flask, request, jsonify
import mysql.connector
import os
from constants import MANAGER_IP, WORKER_IPS, MYSQL_PASSWORD
import traceback

app = Flask(__name__)
handler = logging.FileHandler("proxy.log")  
app.logger.addHandler(handler)
app.logger.setLevel(logging.DEBUG)

LATENCY_THRESHOLD = 0.03   # 30ms threshold, we do chose a random worker below this latency and the lowest ping worker if above

instance_names = {
    MANAGER_IP: "manager",
    WORKER_IPS[0]: "worker1",
    WORKER_IPS[1]: "worker2",
}
forwarding_strategy = ""

def connect(host):
    try:
        conn = mysql.connector.connect(
            host=host,
            user="root",
            password=MYSQL_PASSWORD,
            database="sakila",
            autocommit=True,
            connection_timeout=2
        )
        return conn
    except Exception as e:
        app.logger.info(f"[CONNECT] Failed to connect to {host}: {e}")
        raise

def measure_latency(host):
    try:
        start = time.time()
        db = connect(host)
        cursor = db.cursor()
        cursor.execute("SELECT 1;")
        cursor.fetchone()
        db.close()
        latency = time.time() - start
        return latency
    except Exception:
        return 9999

def is_cluster_under_load(latencies):
    avg_latency = sum(latencies.values()) / len(latencies)
    return avg_latency > LATENCY_THRESHOLD

def select_worker():
    latencies = {ip: measure_latency(ip) for ip in WORKER_IPS}
    under_load = is_cluster_under_load(latencies)
    if not under_load:
        # Random Forwarding
        forwarding_strategy = "random"
        choice = random.choice(WORKER_IPS)

        return choice

    # Customized Forwarding
    forwarding_strategy = "customized"
    best = min(latencies, key=latencies.get)
    return best

def is_read_query(sql):
    is_read = sql.strip().lower().startswith("select")
    return is_read

@app.route("/query", methods=["POST"])
def handle_query():
    app.logger.info("[REQUEST] Received /query request")
    data = request.get_json()
    if not data or "sql" not in data:
        return jsonify({"error": "Missing 'sql' field"}), 400
    sql = data["sql"]

    try:
        # We select to which MySql Instance to forward the query
        if is_read_query(sql):
            host = select_worker()
        else:
            # Direct Hit
            forwarding_strategy = "direct hit"
            host = MANAGER_IP
        app.logger.info(f"[REQUEST] Forwarding to host: {host}")

        db = connect(host)
        cursor = db.cursor(dictionary=True)
        cursor.execute(sql)

        host_label = instance_names.get(host)
        strategy = forwarding_strategy or "unknown"
        host_label = f"{host_label} with {strategy} forwarding"

        if is_read_query(sql):
            
            return jsonify({"data": cursor.fetchall(), "status": "success", "host": host_label})

        return jsonify({"status": "success", "host": host_label})

    except Exception as e:
        app.logger.info(f"[ERROR] Exception while handling query: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
if __name__ == "__main__":
    print(f"[STARTUP] MANAGER_IP={MANAGER_IP}, WORKER_IPS={WORKER_IPS}")
    print("[STARTUP] Starting Flask app on 0.0.0.0:80")
    app.run(host="0.0.0.0", port=80)