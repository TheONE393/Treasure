# Treasure Hunt

This repo contains a small Flask backend and static front-end for running a local treasure-hunt style game.

Quick manual setup (system-wide Python install)

1. Install Python (if not installed). Make sure `python` is on your PATH.
2. Install required packages system-wide (the user requested installing in system Python rather than a venv):

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

3. Run the server:

```powershell
python app.py
```

4. Open the admin dashboard at: http://localhost:8080/admin.html
   Team login: http://localhost:8080/index.html

Notes about repository portability

- This repo contains a `gitpush.py` helper that stages, commits (with an optional message), and pushes to origin. It runs from the script's folder so you can move the folder into another git repo — but if you embed this folder inside another git repo that contains its own .git, git may create a gitlink; avoid nesting .git directories.
- A top-level `.gitignore` was added to ignore answers, virtualenv folders, and editor settings so you can move this folder into a higher-level repo without accidentally committing runtime files.

If you'd like me to change the workflow (re-enable venv-based setup, or make gitpush commit in the parent repo), tell me which behavior you prefer.
