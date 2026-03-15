import os
import subprocess
import logging
import requests
import tkinter as tk
from tkinter import filedialog
from flask import Flask, render_template, request, jsonify
from datetime import datetime
from base64 import b64encode

# ==========================================
# CREDENTIAL CONFIGURATION (Dynamic)
# ==========================================
GITHUB_USER = ""
GITHUB_TOKEN = ""

app = Flask(__name__)
LOG_FILE = "github.log"

# CLEAN LOG FILE BEFORE STARTING
with open(LOG_FILE, 'w', encoding='utf-8') as f:
    f.write(f"--- AlphaGit Log Cleared at {datetime.now()} ---\n")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

def get_auth_header(username, token):
    credentials = f"{username}:{token}"
    encoded_credentials = b64encode(credentials.encode("ascii")).decode("ascii")
    return f"Basic {encoded_credentials}"

def run_git_command(command_args, repo_path=None):
    try:
        cmd = ["git"]
        cmd.extend(command_args)
        cwd = repo_path if repo_path else os.getcwd()
        logger.info(f"Executing: {' '.join(cmd)}")
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True,
            check=False, encoding='utf-8', errors='replace'
        )
        output = result.stdout
        if result.stderr:
            output += f"\n{result.stderr}"
        logger.info(f"Command Result:\n{output}")
        return output
    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        return f"Exception: {str(e)}"

@app.route('/')
def index():
    return render_template('main.html')

# --- SYSTEM UTILS ---
@app.route('/api/select_folder', methods=['GET'])
def select_folder():
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        folder_selected = filedialog.askdirectory()
        root.destroy()
        if folder_selected:
            return jsonify({"status": "success", "path": folder_selected.replace('\\', '/')})
        return jsonify({"status": "error", "message": "Cancelled"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/open_explorer', methods=['POST'])
def open_explorer():
    path = request.json.get('path')
    if path and os.path.exists(path):
        os.startfile(os.path.normpath(path))
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Path not found"})

# --- GITHUB OPERATIONS ---
@app.route('/api/connect', methods=['POST'])
def connect_github():
    global GITHUB_USER, GITHUB_TOKEN
    data = request.json
    GITHUB_USER = data.get('username')
    GITHUB_TOKEN = data.get('token')
    try:
        auth_header = get_auth_header(GITHUB_USER, GITHUB_TOKEN)
        headers = {"Authorization": auth_header, "Accept": "application/vnd.github.v3+json"}
        response = requests.get("https://api.github.com/user", headers=headers, timeout=10)
        if response.status_code == 200:
            return jsonify({"status": "success", "message": f"Linked to {response.json().get('login')}"})
        return jsonify({"status": "error", "message": "Auth Failed"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/create', methods=['POST'])
def create_repo():
    data = request.json
    repo_name, folder_path = data.get('repo_name'), data.get('folder_path')
    try:
        auth_header = get_auth_header(GITHUB_USER, GITHUB_TOKEN)
        headers = {"Authorization": auth_header, "Accept": "application/vnd.github.v3+json"}
        requests.post("https://api.github.com/user/repos", json={"name": repo_name}, headers=headers)
        run_git_command(["init"], folder_path)
        run_git_command(["branch", "-M", "main"], folder_path)
        run_git_command(["remote", "remove", "origin"], folder_path)
        auth_url = f"https://{GITHUB_USER}:{GITHUB_TOKEN}@github.com/{GITHUB_USER}/{repo_name}.git"
        run_git_command(["remote", "add", "origin", auth_url], folder_path)
        push_out = run_git_command(["push", "-u", "origin", "main"], folder_path)
        return jsonify({"status": "success", "message": "Repo created and pushed.", "details": push_out})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/clone', methods=['POST'])
def clone_repo():
    data = request.json
    repo_name, target_path = data.get('repo_name'), data.get('target_path')
    try:
        auth_url = f"https://{GITHUB_USER}:{GITHUB_TOKEN}@github.com/{GITHUB_USER}/{repo_name}.git"
        output = run_git_command(["clone", auth_url, target_path])
        return jsonify({"status": "success", "message": f"Cloned {repo_name}", "details": output})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/update', methods=['POST'])
def update_repo():
    data = request.json
    folder_path = data.get('folder_path')
    try:
        run_git_command(["add", "."], folder_path)
        msg = f"AlphaUpdate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        run_git_command(["commit", "-m", msg], folder_path)
        push_out = run_git_command(["push"], folder_path)
        return jsonify({"status": "success", "message": "Update complete.", "details": push_out})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/delete', methods=['POST'])
def delete_repo():
    repo_name = request.json.get('repo_name')
    headers = {"Authorization": get_auth_header(GITHUB_USER, GITHUB_TOKEN)}
    res = requests.delete(f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}", headers=headers)
    return jsonify({"status": "success", "message": f"Deleted {repo_name}"}) if res.status_code == 204 else jsonify({"status":"error"})

@app.route('/api/list', methods=['GET'])
def list_repos():
    if not GITHUB_USER: return jsonify({"status": "error", "message": "No Auth"})
    headers = {"Authorization": get_auth_header(GITHUB_USER, GITHUB_TOKEN)}
    r = requests.get("https://api.github.com/user/repos?per_page=100&sort=updated", headers=headers)
    repos = [{"name": x['name'], "visibility": "🔒 Private" if x['private'] else "🌐 Public", "last_activity": x['updated_at']} for x in r.json()]
    return jsonify({"status": "success", "data": repos})

if __name__ == '__main__':
    app.run(debug=True, port=5000)