from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import time

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)  # Enable CORS for all routes

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
TEAMS_FILE = os.path.join(BASE_DIR, 'teams.json')
ANSWERS_DIR = os.path.join(BASE_DIR, 'answers')

# ensure answers dir exists
os.makedirs(ANSWERS_DIR, exist_ok=True)

# helpers
def load_teams():
    if not os.path.exists(TEAMS_FILE):
        with open(TEAMS_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=2)
        return {}
    with open(TEAMS_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except Exception:
            return {}

def save_teams(data):
    with open(TEAMS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def _normalize_teams(teams):
    # ensure all expected fields exist with safe defaults so clients/admins don't toggle UI
    for name, info in teams.items():
        if not isinstance(info, dict):
            teams[name] = {}
            info = teams[name]
        info.setdefault('currentQuestion', 1)
        # ensure numeric types where appropriate
        if 'loginTime' in info:
            try:
                info['loginTime'] = int(info['loginTime'])
            except Exception:
                info.pop('loginTime', None)
        info.setdefault('pausedAccum', 0)
        # pauseStart should be int if present
        if 'pauseStart' in info:
            try:
                info['pauseStart'] = int(info['pauseStart'])
            except Exception:
                info.pop('pauseStart', None)
        # eliminated flag explicit boolean
        info['eliminated'] = bool(info.get('eliminated', False))
    return teams

# serve static files (admin.html, script.js, etc.)
@app.route('/')
def index():
    # serve index from the repository base directory to avoid CWD issues
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/questions/<path:filename>')
def serve_questions(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'questions'), filename)

@app.route('/<path:filename>')
def static_files(filename):
    # serve whatever is in the folder
    if os.path.exists(os.path.join(BASE_DIR, filename)):
        return send_from_directory(BASE_DIR, filename)
    return ('Not Found', 404)

# API Endpoints
@app.route('/teams', methods=['GET'])
def get_teams():
    teams = load_teams()
    teams = _normalize_teams(teams)
    return jsonify(teams)

@app.route('/reset_time', methods=['POST'])
def reset_time():
    teams = load_teams()
    data = request.get_json() or {}
    team = data.get('team', '')
    
    if team and team in teams:
        teams.setdefault(team, {})
        teams[team].pop('loginTime', None)
        save_teams(teams)
        return jsonify(status='ok')
    return jsonify(status='error'), 400


@app.route('/eliminate', methods=['POST'])
def eliminate_team():
    teams = load_teams()
    data = request.get_json() or {}
    team = data.get('team', '')

    if team and team in teams:
        teams.setdefault(team, {})
        # mark eliminated for this server session
        teams[team]['eliminated'] = True
        teams[team]['eliminatedAt'] = int(time.time())
        # also remove login time and pause data to stop timers
        teams[team].pop('loginTime', None)
        teams[team].pop('pauseStart', None)
        teams[team].pop('pausedAccum', None)
        save_teams(teams)
        return jsonify(status='ok')
    return jsonify(status='error'), 400

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    data = request.get_json() or {}
    team = data.get('team', '')
    try:
        question = int(data.get('question') or 0)
    except Exception:
        question = 0
    answer = data.get('answer', '')
    correct = bool(data.get('correct', False))

    if team:
        teams = load_teams()
        # If the team has been eliminated for this server session, reject submissions
        if teams.get(team, {}).get('eliminated'):
            return jsonify(status='eliminated', message='Team eliminated for this session'), 403
        safe = ''.join(c if c.isalnum() or c in ('_', '-') else '_' for c in team)
        file = os.path.join(ANSWERS_DIR, safe + '.json')
        entry = {
            'time': int(time.time()),
            'question': question,
            'answer': answer,
            'correct': correct
        }
        existing = []
        if os.path.exists(file):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    existing = json.load(f) or []
            except Exception:
                existing = []
        existing.append(entry)
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(existing, f, indent=2)
        return jsonify(status='ok')
    return jsonify(status='error'), 400


@app.route('/update_question', methods=['POST'])
def update_question():
    teams = load_teams()
    data = request.get_json() or {}
    team = data.get('team', '')
    try:
        question = int(data.get('question') or 1)
    except Exception:
        question = 1

    if team and team in teams:
        if teams.get(team, {}).get('eliminated'):
            return jsonify(status='eliminated', message='Team eliminated for this session'), 403
        teams.setdefault(team, {})
        teams[team]['currentQuestion'] = question
        save_teams(teams)
        return jsonify(status='ok')
    return jsonify(status='error'), 400


@app.route('/skip_question', methods=['POST'])
def skip_question():
    teams = load_teams()
    data = request.get_json() or {}
    team = data.get('team', '')

    if team and team in teams:
        if teams.get(team, {}).get('eliminated'):
            return jsonify(status='eliminated', message='Team eliminated for this session'), 403
        teams.setdefault(team, {})
        curr = int(teams[team].get('currentQuestion') or 1)
        teams[team]['currentQuestion'] = curr + 1
        save_teams(teams)
        return jsonify(status='ok')
    return jsonify(status='error'), 400


@app.route('/pause_timer', methods=['POST'])
def pause_timer():
    teams = load_teams()
    data = request.get_json() or {}
    team = data.get('team', '')
    action = data.get('action', '')  # 'pause' or 'resume'

    if not (team and team in teams):
        return jsonify(status='error'), 400

    if teams.get(team, {}).get('eliminated'):
        return jsonify(status='eliminated', message='Team eliminated for this session'), 403

    teams.setdefault(team, {})
    now = int(time.time())
    # ensure pausedAccum exists
    teams[team].setdefault('pausedAccum', 0)

    if action == 'pause':
        # start a pause window
        if 'pauseStart' not in teams[team]:
            teams[team]['pauseStart'] = now
            save_teams(teams)
        return jsonify(status='ok')
    elif action == 'resume':
        # end pause window and accumulate paused seconds
        if 'pauseStart' in teams[team]:
            try:
                duration = now - int(teams[team].get('pauseStart', now))
            except Exception:
                duration = 0
            teams[team]['pausedAccum'] = int(teams[team].get('pausedAccum', 0)) + int(duration)
            teams[team].pop('pauseStart', None)
            save_teams(teams)
        return jsonify(status='ok')

    return jsonify(status='error'), 400

@app.route('/answers')
def get_answers():
    team = request.args.get('team', '')
    if team:
        safe = ''.join(c if c.isalnum() or c in ('_', '-') else '_' for c in team)
        file = os.path.join(ANSWERS_DIR, safe + '.json')
        if not os.path.exists(file):
            return jsonify([])
        try:
            with open(file, 'r', encoding='utf-8') as f:
                return jsonify(json.load(f) or [])
        except Exception:
            return jsonify([])

    # return all
    out = {}
    for fname in os.listdir(ANSWERS_DIR):
        if fname.endswith('.json'):
            safe = fname[:-5]
            try:
                with open(os.path.join(ANSWERS_DIR, fname), 'r', encoding='utf-8') as f:
                    out[safe] = json.load(f) or []
            except Exception:
                out[safe] = []
    return jsonify(out)

@app.route('/login', methods=['POST'])
def team_login():
    teams = load_teams()
    data = request.get_json() or {}
    team = data.get('team', '')
    password = data.get('password', '')
    
    if team and team in teams and teams[team].get('password') == password:
        teams.setdefault(team, {})
        # If the team was eliminated for this server session, reject login
        if teams.get(team, {}).get('eliminated'):
            return jsonify(status='eliminated', message='Team eliminated for this session'), 403
        # record login time and reset question progress for a fresh session
        teams[team]['loginTime'] = int(time.time())
        teams[team]['currentQuestion'] = 1
        # clear any transient pause flags so the team starts clean (do NOT clear 'eliminated')
        teams[team].pop('pauseStart', None)
        teams[team].pop('pausedAccum', None)
        save_teams(teams)
        return jsonify(status='ok')
    return jsonify(status='error'), 400

def get_ip_address():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't need to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

if __name__ == '__main__':
    # Reset all team times and questions when server starts
    teams = load_teams()
    for team in teams:
        if 'loginTime' in teams[team]:
            del teams[team]['loginTime']
        if 'extraTime' in teams[team]:
            del teams[team]['extraTime']
        # Clear any session-scoped flags (eliminated should only persist for a running server session)
        if 'eliminated' in teams[team]:
            del teams[team]['eliminated']
        # Also ensure pause state is cleared
        teams[team].pop('pauseStart', None)
        teams[team].pop('pausedAccum', None)
        teams[team]['currentQuestion'] = 1  # Reset question number to 1
    save_teams(teams)

    # Remove all saved answers so server starts with a clean slate
    try:
        for fname in os.listdir(ANSWERS_DIR):
            if fname.endswith('.json'):
                path = os.path.join(ANSWERS_DIR, fname)
                try:
                    os.remove(path)
                except Exception:
                    # best-effort delete; continue on errors
                    pass
    except Exception:
        pass

    host = get_ip_address()
    port = 8080
    print(f"\n=== Treasure Hunt Server ===")
    print(f"Local URL: http://localhost:{port}")
    print(f"Network URL: http://{host}:{port}")
    print(f"Admin dashboard: http://{host}:{port}/admin.html")
    print(f"Team login: http://{host}:{port}/index.html")
    print("===========================\n")
    app.run(host='0.0.0.0', port=port, debug=True)