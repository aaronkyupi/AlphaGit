import os
import subprocess
import logging
import requests
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
            user_data = response.json()
            return jsonify({"status": "success", "message": f"Linked to {user_data.get('login')}"})
        return jsonify({"status": "error", "message": f"Auth Failed: {response.status_code}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/api/create', methods=['POST'])
def create_repo():
    data = request.json
    repo_name = data.get('repo_name')
    folder_path = data.get('folder_path')

    try:
        # 1. Create Remote via API
        auth_header = get_auth_header(GITHUB_USER, GITHUB_TOKEN)
        headers = {"Authorization": auth_header, "Accept": "application/vnd.github.v3+json"}
        repo_data = {"name": repo_name, "private": False}
        api_res = requests.post("https://api.github.com/user/repos", json=repo_data, headers=headers)

        if api_res.status_code not in [201, 409]:
            return jsonify({"status": "error", "message": f"GitHub API Fail: {api_res.status_code}"})

        # 2. Local Git Workflow
        run_git_command(["init"], folder_path)
        run_git_command(["branch", "-M", "main"], folder_path)

        # CLEANUP: Remove old origin to avoid "remote origin already exists" error
        run_git_command(["remote", "remove", "origin"], folder_path)

        # Setup .gitignore
        with open(os.path.join(folder_path, ".gitignore"), "w") as f:
            f.write("github.log\n*.log\n.env\nvenv/\n__pycache__/\n")

        run_git_command(["add", "."], folder_path)
        run_git_command(["commit", "-m", "Initial commit via AlphaGit"], folder_path)

        # 3. Authenticated Push [cite: 8, 21, 22]
        # Injects token into URL to bypass local credential manager failures
        auth_url = f"https://{GITHUB_USER}:{GITHUB_TOKEN}@github.com/{GITHUB_USER}/{repo_name}.git"

        run_git_command(["remote", "add", "origin", auth_url], folder_path)
        push_out = run_git_command(["push", "-u", "origin", "main"], folder_path)

        if "fatal:" in push_out or "error:" in push_out:
            return jsonify({"status": "error", "message": "Git Push Failed", "details": push_out})

        return jsonify({"status": "success", "message": "Repo created and files pushed.", "details": push_out})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/api/update', methods=['POST'])
def update_repo():
    data = request.json
    folder_path = data.get('folder_path')
    try:
        run_git_command(["add", "."], folder_path)
        msg = f"Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        run_git_command(["commit", "-m", msg], folder_path)

        # Use existing authenticated remote if possible
        push_out = run_git_command(["push"], folder_path)
        return jsonify({"status": "success", "message": "Changes pushed.", "details": push_out})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/api/clone', methods=['POST'])
def clone_repo():
    data = request.json
    repo_name = data.get('repo_name')
    target_path = data.get('target_path')
    try:
        auth_url = f"https://{GITHUB_USER}:{GITHUB_TOKEN}@github.com/{GITHUB_USER}/{repo_name}.git"
        output = run_git_command(["clone", auth_url, target_path])
        return jsonify({"status": "success", "message": f"Cloned {repo_name}", "details": output})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/api/delete', methods=['POST'])
def delete_repo():
    data = request.json
    repo_name = data.get('repo_name')
    try:
        auth_header = get_auth_header(GITHUB_USER, GITHUB_TOKEN)
        headers = {"Authorization": auth_header, "Accept": "application/vnd.github.v3+json"}
        url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}"
        res = requests.delete(url, headers=headers)
        if res.status_code == 204:
            return jsonify({"status": "success", "message": f"Repo {repo_name} deleted."})
        return jsonify({"status": "error", "message": f"Delete Fail: {res.status_code}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/api/list', methods=['GET'])
def list_repos():
    if not GITHUB_USER:
        return jsonify({"status": "error", "message": "Not connected."})

    auth_header = get_auth_header(GITHUB_USER, GITHUB_TOKEN)
    headers = {"Authorization": auth_header, "Accept": "application/vnd.github.v3+json"}
    try:
        r = requests.get("https://api.github.com/user/repos?per_page=100", headers=headers)
        repos = [{"name": x['name'], "visibility": "🔒" if x['private'] else "🌐"} for x in r.json()]
        return jsonify({"status": "success", "data": repos})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


if __name__ == '__main__':
    app.run(debug=True, port=5000)