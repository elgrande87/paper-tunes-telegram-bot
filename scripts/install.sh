#!/usr/bin/env bash
set -euo pipefail

# Paper Tunes Telegram Bot - Raspberry Pi installer
# Installs the project locally in a Python virtual environment and creates
# a systemd service. No ports are opened and no external service is required.

REPO_DIR="${REPO_DIR:-$HOME/paper-tunes-telegram-bot}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="$REPO_DIR/.venv"
ENV_FILE="$REPO_DIR/.env"
SERVICE_NAME="paper-tunes-bot"

if [[ "$(id -u)" -eq 0 ]]; then
  echo "Bitte nicht als root ausführen. Der Installer legt die Anwendung im Benutzerverzeichnis an."
  exit 1
fi

command -v git >/dev/null || { echo "git fehlt."; exit 1; }
command -v "$PYTHON_BIN" >/dev/null || { echo "$PYTHON_BIN fehlt."; exit 1; }

if [[ ! -d "$REPO_DIR/.git" ]]; then
  echo "==> Repository klonen"
  git clone https://github.com/elgrande87/paper-tunes-telegram-bot.git "$REPO_DIR"
else
  echo "==> Bestehendes Repository aktualisieren"
  git -C "$REPO_DIR" pull --ff-only
fi

cd "$REPO_DIR"

echo "==> Python-Version prüfen"
"$PYTHON_BIN" - <<'PY'
import sys
if sys.version_info < (3, 11):
    raise SystemExit("Python >= 3.11 wird benötigt.")
print(sys.version)
PY

echo "==> Systempakete prüfen"
if command -v apt-get >/dev/null; then
  echo "Für OpenCV/Audio können Systembibliotheken benötigt werden."
  sudo apt-get update
  sudo apt-get install -y python3-venv python3-dev build-essential libsndfile1 ffmpeg libgl1 libglib2.0-0
fi

echo "==> Virtuelle Umgebung erstellen"
"$PYTHON_BIN" -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install --upgrade pip setuptools wheel

# Install the repository and its declared dependencies.
"$VENV_DIR/bin/pip" install -e .

mkdir -p "$REPO_DIR/runtime"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "==> .env anlegen"
  cp .env.example "$ENV_FILE"
  chmod 600 "$ENV_FILE"
  echo
  echo "WICHTIG: Telegram-Bot-Token eintragen:"
  echo "  nano $ENV_FILE"
fi

# Generate the deterministic test WAV. This does not download any audio.
echo "==> Standard-Testdatei erzeugen"
"$VENV_DIR/bin/python" scripts/generate_test_wav.py runtime/test.wav

SERVICE_PATH="/etc/systemd/system/${SERVICE_NAME}.service"
echo "==> systemd-Service installieren"
sudo tee "$SERVICE_PATH" >/dev/null <<EOF
[Unit]
Description=Paper Tunes Telegram Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$REPO_DIR
EnvironmentFile=$ENV_FILE
ExecStart=$VENV_DIR/bin/paper-tunes-bot
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$REPO_DIR/runtime

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"

if grep -q '^PT_TELEGRAM_BOT_TOKEN=123456789:REPLACE_ME' "$ENV_FILE"; then
  echo
  echo "Installation vorbereitet, aber noch NICHT gestartet."
  echo "1. Token eintragen: nano $ENV_FILE"
  echo "2. Starten: sudo systemctl start $SERVICE_NAME"
else
  sudo systemctl restart "$SERVICE_NAME"
  echo "==> Bot gestartet"
fi

echo
echo "Fertig."
echo "Repo:       $REPO_DIR"
echo "Test-WAV:   $REPO_DIR/runtime/test.wav"
echo "Service:    sudo systemctl status $SERVICE_NAME"
echo "Logs:       journalctl -u $SERVICE_NAME -f"
