# DIYA Unified Web Application Backend Server
import http.server
import socketserver
import webbrowser
import os
import sys
import json
import threading
import time
import urllib.request
import urllib.error
import re

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

PORT = 8080
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DIYA_DIR = os.path.join(BASE_DIR, 'diya')
DATA_DIR = os.path.join(DIYA_DIR, 'data')
LESSONS_DIR = os.path.join(DATA_DIR, 'lessons')
STORIES_DIR = os.path.join(DATA_DIR, 'stories')
SONGS_DIR = os.path.join(DATA_DIR, 'songs')
FRONTEND_DIST = os.path.join(BASE_DIR, 'frontend', 'dist')
PROGRESS_FILE = os.path.join(BASE_DIR, 'memory', 'progress.json')
PROFILE_FILE = os.path.join(DATA_DIR, 'profile.json')
GEMINI_FILE = os.path.join(BASE_DIR, 'GEMINI.md')
QUEUE_FILE = os.path.join(DATA_DIR, 'anki_queue.json')
SNAPSHOT_FILE = os.path.join(DATA_DIR, 'deck_snapshot.json')

# Watchdog state
last_heartbeat = time.time()
client_connected = False
shutdown_requested = False
httpd_server = None

def watchdog():
    global last_heartbeat, client_connected, shutdown_requested, httpd_server
    time.sleep(8)  # Initial launch grace period
    while True:
        time.sleep(1)
        if shutdown_requested:
            print('\n[Watchdog] Browser shutdown signal received. Terminating DIYA server...')
            time.sleep(0.5)
            if httpd_server:
                httpd_server.shutdown()
            os._exit(0)
        if client_connected and (time.time() - last_heartbeat > 60):
            print('\n[Watchdog] No heartbeat from browser for >60s. Terminating DIYA server...')
            if httpd_server:
                httpd_server.shutdown()
            os._exit(0)

def anki_request(action, params=None):
    try:
        req_data = json.dumps({'action': action, 'version': 6, 'params': params or {}}).encode('utf-8')
        req = urllib.request.Request('http://127.0.0.1:8765', data=req_data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get('error'):
                return {'error': data['error']}
            return {'result': data.get('result')}
    except Exception as e:
        return {'error': str(e)}

def load_json(path, default=None):
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return default
    return default

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

class DiyaHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Serve from FRONTEND_DIST if it exists, otherwise DIYA_DIR
        serve_dir = FRONTEND_DIST if os.path.exists(FRONTEND_DIST) else DIYA_DIR
        super().__init__(*args, directory=serve_dir, **kwargs)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def send_json(self, data, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def do_GET(self):
        global last_heartbeat, client_connected, shutdown_requested
        path = self.path.split('?')[0]

        if path == '/api/heartbeat':
            last_heartbeat = time.time()
            client_connected = True
            return self.send_json({'status': 'ok', 'live': True})

        if path == '/api/shutdown':
            shutdown_requested = True
            return self.send_json({'status': 'shutting_down'})

        if path == '/api/status':
            anki_test = anki_request('version')
            anki_online = 'result' in anki_test and not anki_test.get('error')
            return self.send_json({
                'app': 'DIYA Hindi Hub',
                'version': '1.0.0',
                'anki_connected': anki_online,
                'anki_version': anki_test.get('result'),
                'time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            })

        if path == '/api/lessons':
            index_path = os.path.join(DATA_DIR, 'lessons_index.json')
            lessons = load_json(index_path, [])
            # If index not present or empty, dynamically scan lessons dir
            if not lessons and os.path.exists(LESSONS_DIR):
                for fn in sorted(os.listdir(LESSONS_DIR)):
                    if fn.endswith('.json'):
                        l_data = load_json(os.path.join(LESSONS_DIR, fn), {})
                        if l_data:
                            lessons.append({
                                'id': l_data.get('id', fn),
                                'code': l_data.get('code', ''),
                                'title': l_data.get('title', fn),
                                'slug': l_data.get('slug', fn[:-5]),
                                'filename': fn
                            })
            return self.send_json(lessons)

        if path.startswith('/api/lessons/'):
            slug = path[len('/api/lessons/'):].strip('/')
            # Check for direct file match or matching slug
            target_file = os.path.join(LESSONS_DIR, f'{slug}.json')
            if not os.path.exists(target_file):
                # Search by slug or code
                found = None
                for fn in os.listdir(LESSONS_DIR):
                    if fn.endswith('.json'):
                        dat = load_json(os.path.join(LESSONS_DIR, fn), {})
                        if dat.get('slug') == slug or dat.get('code', '').lower() == slug.lower():
                            found = dat
                            break
                if found:
                    return self.send_json(found)
                return self.send_json({'error': 'Lesson not found'}, 404)
            data = load_json(target_file)
            return self.send_json(data)

        if path == '/api/stories':
            index_path = os.path.join(DATA_DIR, 'stories_index.json')
            stories = load_json(index_path, [])
            return self.send_json(stories)

        if path.startswith('/api/stories/') and path.endswith('/raw'):
            story_id = path[len('/api/stories/'):-4].strip('/')
            story_file = os.path.join(STORIES_DIR, f'{story_id}.html')
            if os.path.exists(story_file):
                with open(story_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
                return
            return self.send_json({'error': 'Story not found'}, 404)

        if path.startswith('/api/stories/assets/') or ('/assets/' in path and 'stories' in path):
            asset_fn = path.split('/assets/')[-1]
            asset_path = os.path.join(STORIES_DIR, 'assets', asset_fn)
            if os.path.exists(asset_path):
                ext = os.path.splitext(asset_fn)[1].lower()
                mime = 'image/jpeg' if ext in ('.jpg', '.jpeg') else ('image/png' if ext == '.png' else 'application/octet-stream')
                with open(asset_path, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', mime)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(content)
                return
            return self.send_json({'error': 'Asset not found'}, 404)

        if path == '/api/songs':
            index_path = os.path.join(DATA_DIR, 'songs_index.json')
            songs = load_json(index_path, [])
            if not songs and os.path.exists(SONGS_DIR):
                for fn in sorted(os.listdir(SONGS_DIR)):
                    if fn.endswith('.json'):
                        s_data = load_json(os.path.join(SONGS_DIR, fn), {})
                        if s_data:
                            songs.append({
                                'id': s_data.get('id', fn),
                                'title': s_data.get('title', fn),
                                'slug': s_data.get('slug', fn[:-5]),
                                'spotify_url': s_data.get('spotify_url'),
                                'youtube_url': s_data.get('youtube_url'),
                                'cover_art': s_data.get('cover_art'),
                                'movie': s_data.get('movie'),
                                'artist': s_data.get('artist'),
                                'duration': s_data.get('duration'),
                                'filename': fn
                            })
            return self.send_json(songs)

        if path.startswith('/api/songs/'):
            slug = path[len('/api/songs/'):].strip('/')
            target_file = os.path.join(SONGS_DIR, f'{slug}.json')
            if not os.path.exists(target_file):
                for fn in os.listdir(SONGS_DIR):
                    if fn.endswith('.json'):
                        dat = load_json(os.path.join(SONGS_DIR, fn), {})
                        if dat.get('slug') == slug or dat.get('title', '').lower() == slug.lower():
                            return self.send_json(dat)
                return self.send_json({'error': 'Song not found'}, 404)
            data = load_json(target_file)
            return self.send_json(data)

        if path == '/api/anki/cards':
            # Check AnkiConnect live
            card_ids_res = anki_request('findCards', {'query': 'deck:Hindi'})
            if 'result' in card_ids_res and card_ids_res['result']:
                card_ids = card_ids_res['result']
                # Batch fetch cardsInfo (in chunks of 100)
                cards_info = []
                chunk_size = 100
                for i in range(0, len(card_ids), chunk_size):
                    chunk = card_ids[i:i + chunk_size]
                    info_res = anki_request('cardsInfo', {'cards': chunk})
                    if info_res.get('result'):
                        cards_info.extend(info_res['result'])

                # Batch fetch notesInfo to get tags
                note_ids = list(set(c.get('note') for c in cards_info if c.get('note')))
                notes_map = {}
                for i in range(0, len(note_ids), chunk_size):
                    n_chunk = note_ids[i:i + chunk_size]
                    n_res = anki_request('notesInfo', {'notes': n_chunk})
                    if n_res.get('result'):
                        for n in n_res['result']:
                            notes_map[n.get('noteId')] = n.get('tags', [])

                # Process into standardized cards schema
                processed_cards = []
                mastered_count = 0
                learning_count = 0
                struggling_count = 0

                for c in cards_info:
                    cid = c.get('cardId')
                    nid = c.get('note')
                    interval = c.get('interval', 0)
                    reps = c.get('reps', 0)
                    lapses = c.get('lapses', 0)
                    queue = c.get('queue', 0)
                    factor = c.get('factor', 2500)
                    tags = notes_map.get(nid, [])

                    # Status grading
                    if queue == 0 or reps == 0:
                        status = 'Learning'
                        learning_count += 1
                    elif queue == 1 or (lapses >= 2 and interval < 7) or (factor < 1700 and interval < 7):
                        status = 'Struggling'
                        struggling_count += 1
                    elif interval >= 14 and reps >= 3:
                        status = 'Mastered'
                        mastered_count += 1
                    else:
                        status = 'Learning'
                        learning_count += 1

                    # Extract lesson codes
                    lesson_codes = []
                    is_general = False
                    for t in tags:
                        if t.startswith('lesson::'):
                            code = t[len('lesson::'):].strip()
                            if code.lower() == 'general':
                                is_general = True
                            elif code:
                                lesson_codes.append(code)
                        elif t.startswith('lesson_'):
                            code = t[len('lesson_'):].strip().replace('_', '-')
                            if code.lower() == 'general':
                                is_general = True
                            elif code:
                                lesson_codes.append(code)

                    front_val = ''
                    back_val = ''
                    fields = c.get('fields', {})
                    if 'Front' in fields:
                        front_val = fields['Front'].get('value', '')
                    elif 'Text' in fields:
                        front_val = fields['Text'].get('value', '')
                    if 'Back' in fields:
                        back_val = fields['Back'].get('value', '')

                    processed_cards.append({
                        'cardId': cid,
                        'noteId': nid,
                        'front': front_val or c.get('question', ''),
                        'back': back_val or c.get('answer', ''),
                        'interval': interval,
                        'reps': reps,
                        'lapses': lapses,
                        'queue': queue,
                        'factor': factor,
                        'status': status,
                        'tags': tags,
                        'lesson_codes': lesson_codes,
                        'primary_lesson': lesson_codes[0] if lesson_codes else ('general' if is_general else ''),
                        'is_general': is_general
                    })

                # Save updated snapshot asynchronously or on-the-fly
                snapshot_data = {
                    'synced_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                    'stats': {
                        'total': len(processed_cards),
                        'Mastered': mastered_count,
                        'Learning': learning_count,
                        'Struggling': struggling_count
                    },
                    'cards': processed_cards
                }
                save_json(SNAPSHOT_FILE, snapshot_data)

                return self.send_json({
                    'live': True,
                    'synced_at': snapshot_data['synced_at'],
                    'stats': snapshot_data['stats'],
                    'cards': processed_cards
                })

            # Fallback to local snapshot
            snapshot = load_json(SNAPSHOT_FILE, {})
            cards_list = snapshot.get('cards', []) if isinstance(snapshot, dict) else (snapshot if isinstance(snapshot, list) else [])
            stats = snapshot.get('stats', {}) if isinstance(snapshot, dict) else {}
            return self.send_json({
                'live': False,
                'synced_at': snapshot.get('synced_at') if isinstance(snapshot, dict) else None,
                'stats': stats,
                'cards': cards_list
            })

        if path == '/api/profile':
            profile_data = load_json(PROFILE_FILE)
            if not profile_data:
                prog = load_json(PROGRESS_FILE, {})
                student = prog.get('student', {})
                profile_data = {
                    'name': student.get('name', 'Student'),
                    'pronouns': 'He/Him',
                    'gender': student.get('gender', 'Male'),
                    'diya_instructions': '<p>' + prog.get('learning_strategy', {}).get('approach', 'Immersion first, grammar consolidation second') + '</p>',
                    'notes': '',
                    'target': student.get('target', 'A0 to A2 Conversational Fluency'),
                    'primary_goal': student.get('primary_goal', 'Reunion trip with Shivani in Norwich, UK')
                }
            return self.send_json(profile_data)

        # Fallback to SPA index.html for client-side routing if serving frontend build
        if os.path.exists(FRONTEND_DIST):
            req_file = os.path.join(FRONTEND_DIST, path.lstrip('/'))
            if not os.path.exists(req_file) and not '.' in path:
                self.path = '/index.html'

        super().do_GET()

    def do_POST(self):
        global last_heartbeat, client_connected, shutdown_requested
        path = self.path.split('?')[0]

        length = int(self.headers.get('content-length', 0))
        body = self.rfile.read(length).decode('utf-8') if length > 0 else '{}'
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        if path == '/api/heartbeat':
            last_heartbeat = time.time()
            client_connected = True
            return self.send_json({'status': 'ok', 'live': True})

        if path == '/api/shutdown':
            shutdown_requested = True
            return self.send_json({'status': 'shutting_down'})

        if path == '/api/profile':
            try:
                name = payload.get('name', 'Student')
                gender = payload.get('gender', 'Male')
                pronouns = payload.get('pronouns', 'He/Him')
                instructions = payload.get('diya_instructions', '')
                notes = payload.get('notes', '')
                target = payload.get('target', 'A0 to A2 Conversational Fluency')
                primary_goal = payload.get('primary_goal', 'Reunion trip with Shivani in Norwich, UK')

                # 1. Save canonical profile.json in diya/data
                profile_data = {
                    'name': name,
                    'pronouns': pronouns,
                    'gender': gender,
                    'diya_instructions': instructions,
                    'notes': notes,
                    'target': target,
                    'primary_goal': primary_goal
                }
                save_json(PROFILE_FILE, profile_data)

                # Sync to frontend static data folders if they exist
                for target_dir in [os.path.join(BASE_DIR, 'frontend', 'public', 'data'), os.path.join(FRONTEND_DIST, 'data')]:
                    if os.path.exists(target_dir):
                        save_json(os.path.join(target_dir, 'profile.json'), profile_data)

                # 2. Update progress.json student info
                prog = load_json(PROGRESS_FILE, {})
                if 'student' not in prog:
                    prog['student'] = {}
                prog['student']['name'] = name
                prog['student']['gender'] = gender
                if 'learning_strategy' not in prog:
                    prog['learning_strategy'] = {}
                prog['learning_strategy']['custom_instructions'] = instructions
                save_json(PROGRESS_FILE, prog)

                return self.send_json({'success': True, 'message': 'Profile updated successfully'})
            except Exception as e:
                return self.send_json({'error': str(e)}, 500)

        if path == '/api/anki/add':
            front = payload.get('front', '')
            back = payload.get('back', '')
            lesson = payload.get('lesson', '')
            tags = ['hindi_coach', f'lesson_{lesson}'] if lesson else ['hindi_coach']

            anki_res = anki_request('addNote', {
                'note': {
                    'deckName': 'Hindi',
                    'modelName': 'Basic',
                    'fields': {'Front': front, 'Back': back},
                    'tags': tags
                }
            })
            if 'result' in anki_res and not anki_res.get('error'):
                return self.send_json({'success': True, 'note_id': anki_res['result'], 'queued': False})
            
            # Queue offline
            q = load_json(QUEUE_FILE, [])
            q.append({'front': front, 'back': back, 'lesson': lesson, 'timestamp': time.time()})
            save_json(QUEUE_FILE, q)
            return self.send_json({'success': True, 'queued': True, 'message': 'Queued in local Anki queue.'})

        return self.send_json({'error': 'Not found'}, 404)

def main():
    global PORT, httpd_server
    w = threading.Thread(target=watchdog, daemon=True)
    w.start()

    socketserver.TCPServer.allow_reuse_address = True
    while PORT < 8100:
        try:
            with socketserver.TCPServer(('', PORT), DiyaHandler) as httpd:
                httpd_server = httpd
                url = f'http://localhost:{PORT}'
                print(f'\n=======================================================')
                print(f'  🪔 DIYA Hindi Learning Hub Server is Live!')
                print(f'  URL: {url}')
                print(f'  Anki Bridge: Active (:8765)')
                print(f'  Watchdog: Active (auto-terminates when browser closes)')
                print(f'  Press Ctrl+C to stop.')
                print(f'=======================================================\n')
                webbrowser.open(url)
                httpd.serve_forever()
                break
        except OSError:
            PORT += 1

if __name__ == '__main__':
    main()
