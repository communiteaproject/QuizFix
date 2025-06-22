# QuizFix - Local Trivia Game

This project provides a fully-local trivia night experience that can run on a Raspberry Pi or any Linux box. The backend is built with **FastAPI** and **SQLite**, exposing a REST / WebSocket API, and allows a host to build and plan Trivia Night. A progressive-web-app (PWA) frontend allows players to form teams and answer your questions. 

## Features (MVP)

* Host creates a game (6 rounds × 10 questions each).
* Teams register and create their members.
* Host drives the game through the predefined phases:
  1. Gathering
  2. Questions Phase 1 (Rounds 1-3)
  3. Answers Phase 1
  4. Leaderboard Phase 1
  5. Questions Phase 2 (Rounds 4-6)
  6. Answers Phase 2
  7. Leaderboard Phase 2 (declares winner)
* Questions can include rich-media URLs stored locally.
* Fast, offline-friendly—perfect for BYOD pub trivia without Internet.

## Getting started
Add Caddy / Nginx if you want HTTPS on the local network.

## Raspberry Pi Deployment (One-click)

This repo includes `scripts/setup_pi.sh` which automates everything:

```bash
curl -sSL https://raw.githubusercontent.com/communiteaproject/zGame/main/scripts/setup_pi.sh | bash
```

What the script does:
1. Clones/updates the repo.
2. Creates a Python venv and installs backend dependencies.
3. Installs Node 20 (if missing), builds the React frontend, copies static files to the backend.
4. Generates `trivia.service` under systemd so the game starts on boot (Uvicorn on :8000).
5. Enables the service. Start immediately with:
   ```bash
   sudo systemctl start trivia
   ```

After boot the host can open `http://raspberrypi.local:8000/docs` for API docs, or `http://raspberrypi.local:8000` for the PWA.

### Desktop "double-click" shortcut

If the Pi is running the desktop edition you can create `Trivia.desktop`:

```ini
[Desktop Entry]
Type=Application
Name=Local Trivia Host
Exec=systemctl start --user trivia
Terminal=true
Icon=utilities-terminal
```
Save it to `~/Desktop`, make it executable (`chmod +x ~/Desktop/Trivia.desktop`). The host can then double-click to start the server.

### Built-in WiFi Access Point

The installer also configures the Pi as an AP (SSID `QuizFix`, password `quizfix123`).

Use the host endpoints (token-protected):

| Method | Path          | Description             |
|--------|---------------|-------------------------|
| POST   | /wifi/start   | Start WiFi AP           |
| POST   | /wifi/stop    | Stop WiFi AP            |
| GET    | /wifi/status  | Current state + clients |

Example curl:
```bash
curl -X POST http://quizfix.local:8000/wifi/start -H "X-Host-Token: changeme"
```
