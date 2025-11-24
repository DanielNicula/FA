import statistics
import requests
import time
import random
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from constants import GATEKEEPER_IP, API_KEY


GATEKEEPER_URL = f"http://{GATEKEEPER_IP}/API"
OUTPUT_FILE = "benchmark_results.txt"

HEADERS = {
    "Content-Type": "application/json",
    "Auth": API_KEY
}

def create_write_request():
    characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    first_name = ''.join(random.choices(characters, k=6))
    last_name = ''.join(random.choices(characters, k=6))
    sql = f"INSERT INTO sakila.actor (first_name, last_name) VALUES ('{first_name}', '{last_name}');"
    return sql

def create_read_request():
    return "SELECT COUNT(*) FROM sakila.actor;"

def send_request(sql):
    start = time.time()
    try:
        resp = requests.post(GATEKEEPER_URL, headers=HEADERS, json={"sql": sql}, timeout=10)
        elapsed = time.time() - start
        try:
            data = resp.json()
        except Exception:
            data = {"raw_text": resp.text}
        host = data.get("host", "unknown")
        status = data.get("status", resp.status_code)
        return elapsed, host, status, sql, data
    except Exception as e:
        elapsed = time.time() - start
        return elapsed, "error", str(e), sql, {"error": str(e)}

def benchmark():
    with open(OUTPUT_FILE, "w") as f:
        f.write("type,time,host,status,query,response\n")

    # Prepare interleaved requests
    requests_list = [("write", create_write_request()) for _ in range(1000)] + \
                    [("read", create_read_request()) for _ in range(1000)]
    random.shuffle(requests_list)

    results = []
    max_workers = 200

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_type = {executor.submit(send_request, sql): typ for typ, sql in requests_list}

        with open(OUTPUT_FILE, "a") as f:
            for future in as_completed(future_to_type):
                typ = future_to_type[future]
                try:
                    elapsed, host, status, query, response = future.result()
                except Exception as e:
                    elapsed = None
                    host = "error"
                    status = str(e)
                    query = ""
                    response = {"error": str(e)}

                response_str = json.dumps(response).replace("\n", "")
                f.write(f"{typ},{elapsed},{host},{status},{query},{response_str}\n")
                f.flush()
                results.append((typ, elapsed, host, status, query, response))

    append_host_stats(results, OUTPUT_FILE)
    return results

def append_host_stats(results, output_file):
    host_data = {}
    for typ, elapsed, host, status, query, response in results:
        if elapsed is None:
            continue
        if host not in host_data:
            host_data[host] = []
        host_data[host].append(elapsed)

    with open(output_file, "a") as f:
        f.write("\n# Per-host statistics\n")
        f.write("host,min_time,avg_time,max_time,num_requests\n")
        for host, times in host_data.items():
            min_time = min(times)
            max_time = max(times)
            avg_time = statistics.mean(times)
            f.write(f"{host},{min_time:.4f},{avg_time:.4f},{max_time:.4f},{len(times)}\n")

        f.write("\n# Overall statistics\n")
        all_times = [elapsed for _, elapsed, _, _, _, _ in results if elapsed is not None]
        if all_times:
            min_time = min(all_times)
            max_time = max(all_times)
            avg_time = statistics.mean(all_times)
            f.write(f"overall,{min_time:.4f},{avg_time:.4f},{max_time:.4f},{len(all_times)}\n")

if __name__ == "__main__":
    benchmark()
    print(f"Benchmark finished! Results saved to {OUTPUT_FILE}")
