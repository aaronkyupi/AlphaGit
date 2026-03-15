# AlphaGit Pro

A modern, Cyberpunk-themed web interface for managing Git repositories. 
Designed for developers who want a visual CLI experience to interact with GitHub.

## Features

*   **Cyberpunk UI:** Glowing green terminal aesthetic.
*   **Real-Time CLI:** Shows the exact Git commands being executed.
*   **Logging:** Records all actions to `github.log`.
*   **Repository Management:**
    *   **Upload:** Initialize local folder and push to new GitHub repo.
    *   **Update:** Push committed changes to the remote.
    *   **List:** Scan local machine for existing Git repos.
    *   **Delete:** Remove connection or simulate remote deletion.

## Prerequisites

1.  **Python 3.6+**
2.  **Git** installed and available in your system PATH.
3.  **GitHub Personal Access Token:**
    *   Go to GitHub Settings -> Developer Settings -> Personal Access Tokens.
    *   Generate a token with `repo` scope.
    *   *Note: Do not use your GitHub password. GitHub no longer accepts password authentication for Git.*

## Setup Instructions

1.  **Clone or Create Files:**
    Create a folder and place `app.py`, the `templates/main.html`, and `README.md` inside.
    
2.  **Install Python Dependencies:**
    Open your terminal/command prompt in the project directory:
    ```bash
    pip install flask python-dotenv
    ```

3.  **Configure Environment (Optional but Recommended):**
    Create a file named `.env` in your project root directory:
    ```env
    GITHUB_USER=your_github_username
    GITHUB_TOKEN=your_generated_token
    ```
    *If you do not create a `.env` file, you can manually type the credentials into the web UI every time.*

4.  **Run the Application:**
    ```bash
    python app.py
    ```

5.  **Access the Interface:**
    Open your web browser and navigate to `http://localhost:5000`.

## Usage Guide

### 1. Connection
*   Enter your **GitHub Username**.
*   Enter your **Personal Access Token** (not password).
*   Click **Initialize Link**.

### 2. Uploading (Creating) a Repository
*   Ensure you have a local folder with your project code.
*   Enter the **Project Folder Path** (e.g., `C:/Users/DarkUser/MyProject`).
*   Enter a **Repository Name**.
*   Click **[+] Create Repository**.
    *   *Note: This script creates the local git repo. If the remote repo does not exist on GitHub, it will ask you to create it manually.*

### 3. Updating (Pushing) a Repository
*   Ensure you have committed changes in your local Git repo.
*   Enter the **Target Project Folder Path**.
*   Click **[>] Push Updates**.

### 4. Listing Repositories
*   Click **[=] List Repositories**.
*   This scans your Home directory for folders containing `.git`.

### 5. Deleting a Repository
*   Enter the **Repository Name**.
*   Click **[X] Delete Repository**.
    *   *Note: This currently removes the local remote connection for safety. To delete the remote GitHub repo, you must use the GitHub Web Interface or specific API calls (requires Admin rights).*

## Technical Details

*   **Backend:** Python Flask
*   **Frontend:** HTML5, CSS3 (Cyberpunk Theme), Vanilla JS (Fetch API)
*   **System Interaction:** `subprocess` module to execute Git commands.
*   **Logs:** Data is written to `github.log` in the project directory.

## Security Notice

*   This application uses environment variables or input fields for credentials. In a production environment, do not store tokens in plain text files. This is a development tool.
*   The application runs locally on `localhost` port `5000`.

---
*AlphaGit Pro v1.0 - Access Granted*