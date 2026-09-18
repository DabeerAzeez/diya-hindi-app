"""
Launcher and Local API Bridge for Hindi Lessons Dashboard
Serves the web dashboard and handles /api/sync to bridge live AnkiConnect data without CORS issues.
"""

import http.server
import socketserver
import webbrowser
import os
import sys
import json
import threading
import time

PORT = 8080
DIRECTORY = os.path.abspath(os.path.dirname(__file__))
BASE_DIR = os.path.abspath(os.path.join(DIRECTORY, ".."))

# Add scripts and skills directory to path
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, "scripts"))
sys.path.append(os.path.join(BASE_DIR, ".agents", "skills", "anki-card-generator", "scripts"))

# Load local .env if present
env_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_path):
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())
    except Exception:
        pass

from scripts.sync_deck_snapshot import sync_snapshot
from scripts.build_curriculum_metadata import parse_curriculum

try:
    from anki_client import add_card
except ImportError:
    add_card = None

QUEUE_FILE = os.path.join(DIRECTORY, "data", "anki_queue.json")

# Heartbeat & Auto-termination Watchdog State
last_heartbeat = time.time()
client_connected = False
shutdown_requested = False
httpd_server = None

def watchdog():
    global last_heartbeat, client_connected, shutdown_requested, httpd_server
    time.sleep(6)  # Grace period for initial browser launch
    while True:
        time.sleep(1)
        if shutdown_requested:
            print("\n[Watchdog] Browser shutdown signal received. Terminating local server...")
            time.sleep(0.5)
            if httpd_server:
                httpd_server.shutdown()
            os._exit(0)
        # Check if browser was connected, but hasn't sent a heartbeat for > 9 seconds
        if client_connected and (time.time() - last_heartbeat > 9):
            print("\n[Watchdog] No heartbeat received from browser for >9s (tab closed). Terminating local server...")
            if httpd_server:
                httpd_server.shutdown()
            os._exit(0)


def load_queue():
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_queue(items):
    os.makedirs(os.path.dirname(QUEUE_FILE), exist_ok=True)
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)

def drain_queue():
    if not add_card:
        return 0
    queue = load_queue()
    if not queue:
        return 0
    remaining = []
    drained = 0
    for card in queue:
        try:
            add_card(
                front=card["front"],
                back=card["back"],
                lesson=card.get("lesson")
            )
            drained += 1
        except Exception:
            remaining.append(card)
    save_queue(remaining)
    if drained > 0:
        print(f"Auto-drained {drained} queued cards to AnkiConnect! {len(remaining)} cards remaining in queue.")
    return drained

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        global last_heartbeat, client_connected, shutdown_requested

        if self.path == "/api/heartbeat":
            last_heartbeat = time.time()
            client_connected = True
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "live": True}).encode("utf-8"))
            return

        if self.path == "/api/shutdown":
            shutdown_requested = True
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "shutting_down"}).encode("utf-8"))
            return

        if self.path == "/api/curriculum" or self.path.startswith("/api/curriculum?") or self.path == "/api/refresh-curriculum":
            try:
                last_heartbeat = time.time()
                client_connected = True
                print("Refreshing curriculum from progress.json and curriculum markdown...")
                lessons = parse_curriculum()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(lessons, ensure_ascii=False).encode("utf-8"))
                print(f"Returned {len(lessons)} fresh curriculum lessons to browser.")
            except Exception as e:
                print(f"Error during curriculum refresh: {e}")
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        if self.path == "/api/sync" or self.path.startswith("/api/sync?"):
            try:
                last_heartbeat = time.time()
                client_connected = True
                print("Received /api/sync request. Draining queue and fetching live cards from Anki...")
                drain_queue()
                sync_snapshot()
                snapshot_file = os.path.join(DIRECTORY, "data", "deck_snapshot.json")
                with open(snapshot_file, "r", encoding="utf-8") as f:
                    data = f.read()
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(data.encode("utf-8"))
                print("Live Anki sync completed and returned to browser.")
            except Exception as e:
                print(f"Error during Anki sync: {e}")
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                err_payload = json.dumps({"error": str(e)})
                self.wfile.write(err_payload.encode("utf-8"))
            return

        if self.path == "/api/queue":
            last_heartbeat = time.time()
            client_connected = True
            queue = load_queue()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(queue, ensure_ascii=False).encode("utf-8"))
            return

        super().do_GET()

    def do_POST(self):
        global last_heartbeat, client_connected, shutdown_requested

        if self.path == "/api/heartbeat":
            last_heartbeat = time.time()
            client_connected = True
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "live": True}).encode("utf-8"))
            return

        if self.path == "/api/shutdown":
            shutdown_requested = True
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "shutting_down"}).encode("utf-8"))
            return

        if self.path == "/api/refresh-curriculum":
            try:
                last_heartbeat = time.time()
                client_connected = True
                print("Refreshing curriculum from progress.json and curriculum markdown...")
                lessons = parse_curriculum()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(lessons, ensure_ascii=False).encode("utf-8"))
                print(f"Returned {len(lessons)} fresh curriculum lessons to browser.")
            except Exception as e:
                print(f"Error refreshing curriculum: {e}")
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        if self.path == "/api/add-cards":
            try:
                last_heartbeat = time.time()
                client_connected = True
                length = int(self.headers.get("content-length", 0))
                body = self.rfile.read(length).decode("utf-8")
                payload = json.loads(body)
                cards = payload.get("cards", [])

                added_notes = []
                queued_cards = []
                anki_available = True

                for card in cards:
                    front = card.get("front", "")
                    back = card.get("back", "")
                    lesson = card.get("lesson", "")

                    if anki_available and add_card:
                        try:
                            note_id = add_card(front=front, back=back, lesson=lesson)
                            added_notes.append(note_id)
                        except Exception as e:
                            print(f"AnkiConnect unavailable or failed: {e}. Queuing remaining cards.")
                            anki_available = False
                            queued_cards.append(card)
                    else:
                        queued_cards.append(card)

                if queued_cards:
                    existing_queue = load_queue()
                    existing_queue.extend(queued_cards)
                    save_queue(existing_queue)
                    print(f"Queued {len(queued_cards)} cards in local Anki queue.")

                if added_notes:
                    print(f"Added {len(added_notes)} notes directly to Anki! Triggering snapshot sync...")
                    try:
                        sync_snapshot()
                    except Exception as e:
                        print(f"Warning: snapshot sync after add failed: {e}")

                success = len(added_notes) > 0
                res = {
                    "success": success,
                    "added_count": len(added_notes),
                    "queued_count": len(queued_cards),
                    "note_ids": added_notes,
                    "error": None if success else "AnkiConnect could not be reached to add notes to your deck. Make sure Anki is open."
                }

                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(res, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                print(f"Error handling /api/add-cards: {e}")
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        super().do_POST()

def main():
    global PORT, httpd_server
    # Start auto-termination watchdog thread
    w = threading.Thread(target=watchdog, daemon=True)
    w.start()

    while PORT < 8090:
        try:
            with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
                httpd_server = httpd
                url = f"http://localhost:{PORT}/index.html"
                print(f"\n=======================================================")
                print(f"  🇮🇳 Hindi Lessons Dashboard is Live!")
                print(f"  URL: {url}")
                print(f"  Live Anki API Bridge: Active (/api/sync)")
                print(f"  Dynamic Curriculum Bridge: Active (/api/curriculum)")
                print(f"  Browser Heartbeat Watchdog: Active (auto-terminates on close)")
                print(f"  Press Ctrl+C in this terminal to stop.")
                print(f"=======================================================\n")
                webbrowser.open(url)
                httpd.serve_forever()
                break
        except OSError:
            PORT += 1

if __name__ == "__main__":
    main()
