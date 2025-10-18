# Treasure Hunt

## Quick deploy notes (Render)

- Ensure `requirements.txt` exists (Flask, flask-cors, gunicorn are included).
- `Procfile` is present to run gunicorn in production: `web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2`.
- `app.py` now reads `PORT` from the environment. Render will set `$PORT` automatically.
- Do not commit `teams.json` with real passwords. Use `teams.example.json` for public samples and create `teams.json` on the server.

To deploy on Render:
1. Create a new Web Service on Render and connect your GitHub repo.
2. Select branch `main` (or `master` if you prefer) and deploy. Render will install requirements and run the Procfile.

## Running locally

Windows (PowerShell):

Run the included script which installs requirements into your user site and starts the app:

```powershell
.\start_server.ps1
```

Linux / WSL:

```bash
./run_local.sh
```

