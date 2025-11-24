import requests
import time
import random
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

GATEKEEPER_URL = "http://52.23.247.62/API"  # replace with your gatekeeper IP
API_KEY = "lufAUEFC7HjraYos9FWYp0vMHP3sLsDJxZpLcjFe"                      # replace with your API key
OUTPUT_FILE = "benchmark_results.txt"

NUM_WRITES = 1000
NUM_READS = 1000

# Sample data for writes
# generate more varied/random names by composing syllables
SYLL_FIRST = ["an", "jo", "li", "mar", "al", "el", "ra", "sa", "da", "ka", "mi", "na", "la", "be", "ce", "ti", "zo", "re", "fu"]
SYLL_LAST = ["son", "man", "berg", "stein", "ford", "well", "ton", "ley", "wood", "stone", "field", "shaw", "hill", "banks", "wright", "smyth", "cole", "moor"]

def make_names(syllables, min_s=2, max_s=3, count=300):
    names = set()
    while len(names) < count:
        parts = [random.choice(syllables) for _ in range(random.randint(min_s, max_s))]
        name = "".join(parts).capitalize()
        names.add(name)
    return list(names)

# a small set of common names plus many generated ones for variability
COMMON_FIRST = ["John", "Jane", "Alice", "Bob", "Charlie", "Eve", "Liam", "Olivia", "Noah", "Emma"]
COMMON_LAST = ["Smith", "Doe", "Johnson", "Brown", "Williams", "Taylor", "Anderson", "Martin"]

FIRST_NAMES = COMMON_FIRST + make_names(SYLL_FIRST, min_s=2, max_s=3, count=200)
LAST_NAMES = COMMON_LAST + make_names(SYLL_LAST, min_s=1, max_s=2, count=200)

HEADERS = {
    "Content-Type": "application/json",
    "Auth": API_KEY
}

def create_write_request():
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    sql = f"INSERT INTO sakila.actor (first_name, last_name) VALUES ('{first_name}', '{last_name}');"
    return sql

def create_read_request():
    sql = "SELECT COUNT(*) FROM sakila.actor;"
    return sql

def send_request(sql):
    start = time.time()
    try:
        resp = requests.post(GATEKEEPER_URL, headers=HEADERS, json={"sql": sql}, timeout=10)
        elapsed = time.time() - start
        # parse the JSON response
        data = resp.json()
        host = data.get("host", "unknown")
        status = data.get("status", resp.status_code)
        return elapsed, host, status
    except Exception as e:
        elapsed = time.time() - start
        return elapsed, "error", str(e)

def benchmark():
    with open(OUTPUT_FILE, "w") as f:
        f.write("type,time,host,status\n")
    
    requests_list = [("write", create_write_request()) for _ in range(NUM_WRITES)] + \
                    [("read", create_read_request()) for _ in range(NUM_READS)]
    random.shuffle(requests_list)
    results = []
    results = []
    max_workers = min(200, len(requests_list))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_type = {executor.submit(send_request, sql): typ for typ, sql in requests_list}

        with open(OUTPUT_FILE, "a") as f:
            for future in as_completed(future_to_type):
                typ = future_to_type[future]
                try:
                    elapsed, host, status = future.result()
                except Exception as e:
                    elapsed = None
                    host = "error"
                    status = str(e)
                f.write(f"{typ},{elapsed},{host},{status}\n")
                f.flush()
                results.append((typ, elapsed, host, status))

    return results
    


if __name__ == "__main__":
    benchmark()
    print(f"Benchmark finished! Results saved to {OUTPUT_FILE}")