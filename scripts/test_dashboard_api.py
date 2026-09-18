"""
Test script for run_dashboard.py endpoints:
- POST /api/add-cards
- GET /api/queue
- OPTIONS /api/add-cards
"""

import sys
import os
import json
import threading
import time
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')

def test_api():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, root_dir)
    import run_dashboard
    import socketserver

    test_port = 8188
    httpd = socketserver.TCPServer(("", test_port), run_dashboard.DashboardHandler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    time.sleep(0.5)

    base_url = f"http://127.0.0.1:{test_port}"
    print(f"Test server started at {base_url}")

    # 1. Test OPTIONS /api/add-cards
    req = urllib.request.Request(f"{base_url}/api/add-cards", method="OPTIONS")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        assert resp.headers.get("Access-Control-Allow-Origin") == "*"
        print("✓ OPTIONS /api/add-cards passed")

    # 2. Test POST /api/add-cards
    test_card = {
        "front": "Test front sentence for queue verification.",
        "back": "Test back sentence.<br><br><span style=\"color: #718096;\"><i>Diacritics</i></span><br><br><span style=\"color: #2b6cb0;\"><small>Gloss</small></span><br><br><span style=\"color: #6b46c1;\"><small><b>🎯 Target:</b> [A0-07] Test</small></span>",
        "lesson": "A0-07"
    }
    payload = json.dumps({"cards": [test_card]}).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/api/add-cards",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        body = json.loads(resp.read().decode("utf-8"))
        assert body["success"] is True
        print(f"✓ POST /api/add-cards passed: added={body.get('added_count')}, queued={body.get('queued_count')}")
        # Clean up any created note from live Anki
        created_notes = body.get("note_ids", [])
        if created_notes:
            try:
                from anki_client import invoke
                invoke("deleteNotes", notes=created_notes)
                print(f"✓ Cleaned up test note {created_notes} from live Anki")
            except Exception as e:
                print(f"Warning: clean test note failed: {e}")

    # 3. Test GET /api/queue
    req = urllib.request.Request(f"{base_url}/api/queue")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        queue = json.loads(resp.read().decode("utf-8"))
        print(f"✓ GET /api/queue passed: {len(queue)} items in queue")

    # Clean up test queue item if queued
    queue_file = os.path.join("lessons-dashboard", "data", "anki_queue.json")
    if os.path.exists(queue_file):
        with open(queue_file, "r", encoding="utf-8") as f:
            q = json.load(f)
        q = [item for item in q if item["front"] != test_card["front"]]
        with open(queue_file, "w", encoding="utf-8") as f:
            json.dump(q, f, indent=2, ensure_ascii=False)
        print("✓ Cleaned test items from queue file")

    httpd.shutdown()
    print("All API server tests passed successfully!")

if __name__ == "__main__":
    test_api()
