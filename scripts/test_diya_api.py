import sys
import os
import json
import urllib.request
import subprocess
import time

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

sys.path.insert(0, r"C:\Users\dabee\Dev\diya-hindi-app\diya")

# Start server as subprocess
proc = subprocess.Popen([sys.executable, r"C:\Users\dabee\Dev\diya-hindi-app\diya\server.py"])
time.sleep(2)

base_url = "http://localhost:8080"
endpoints = [
    "/api/status",
    "/api/lessons",
    "/api/stories",
    "/api/songs",
    "/api/profile",
    "/api/anki/cards"
]

all_passed = True
try:
    for ep in endpoints:
        req = urllib.request.Request(base_url + ep)
        try:
            with urllib.request.urlopen(req, timeout=5) as res:
                code = res.getcode()
                data = json.loads(res.read().decode('utf-8'))
                count = len(data) if isinstance(data, list) else (len(data.get('cards', [])) if 'cards' in data else len(data))
                print(f"[OK] {ep}: HTTP {code} (items/fields: {count})")
        except Exception as e:
            print(f"[FAIL] {ep} failed: {e}")
            all_passed = False

    # Also test single lesson detail
    with urllib.request.urlopen(base_url + "/api/lessons", timeout=5) as res:
        lessons = json.loads(res.read().decode('utf-8'))
        if lessons:
            slug = lessons[0]['slug']
            with urllib.request.urlopen(base_url + f"/api/lessons/{slug}", timeout=5) as lres:
                ld = json.loads(lres.read().decode('utf-8'))
                print(f"[OK] /api/lessons/{slug}: HTTP {lres.getcode()} Title: {ld.get('title')}")

    # Also test single song detail
    with urllib.request.urlopen(base_url + "/api/songs", timeout=5) as res:
        songs = json.loads(res.read().decode('utf-8'))
        if songs:
            sslug = songs[0]['slug']
            with urllib.request.urlopen(base_url + f"/api/songs/{sslug}", timeout=5) as sres:
                sd = json.loads(sres.read().decode('utf-8'))
                print(f"[OK] /api/songs/{sslug}: HTTP {sres.getcode()} Title: {sd.get('title')}")

    # Test static index.html
    with urllib.request.urlopen(base_url + "/", timeout=5) as res:
        print(f"[OK] GET /: HTTP {res.getcode()} (length: {len(res.read())} bytes)")

    # Send shutdown
    urllib.request.urlopen(base_url + "/api/shutdown", timeout=3)
    print("[OK] /api/shutdown: Server shutdown signal sent.")
finally:
    time.sleep(1)
    proc.terminate()

if all_passed:
    print("\nALL API ENDPOINTS PASSED VERIFICATION!")
else:
    sys.exit(1)
