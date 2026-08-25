#!/usr/bin/env bash
set -euo pipefail

# Paper Tunes Telegram Bot - Raspberry Pi / DietPi installer
# Works both from a cloned repository and via: curl .../install.sh | bash
# No listening port is opened. Telegram polling is used.

REPO_URL="${PT_REPO_URL:-https://github.com/elgrande87/paper-tunes-telegram-bot.git}"
REPO_DIR="${REPO_DIR:-$HOME/paper-tunes-telegram-bot}"
INSTALL_USER="${PT_INSTALL_USER:-paper-tunes}"
SERVICE_NAME="paper-tunes-bot"

if [[ "${PT_BOOTSTRAPPED:-0}" != "1" ]]; then
  # When executed through `curl | bash`, BASH_SOURCE is unavailable and there
  # is no local repository yet. Clone it and re-execute the real installer.
  if [[ -z "${BASH_SOURCE[0]:-}" || ! -d "${REPO_DIR}/.git" ]]; then
    if [[ -d "$REPO_DIR" && ! -d "$REPO_DIR/.git" ]]; then
      echo "Fehler: $REPO_DIR existiert bereits, ist aber kein Git-Repository."
      echo "Bitte REPO_DIR auf einen freien Pfad setzen oder das Verzeichnis entfernen."
      exit 1
    fi
    echo "==> Paper Tunes Repository klonen"
    git clone "$REPO_URL" "$REPO_DIR"
    export PT_BOOTSTRAPPED=1
    exec bash "$REPO_DIR/scripts/install.sh"
  fi
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="${REPO_DIR:-$(cd -- "$SCRIPT_DIR/.." && pwd)}"
VENV_DIR="$REPO_DIR/.venv"
ENV_FILE="$REPO_DIR/.env"

if [[ ! -d "$REPO_DIR/.git" ]]; then
  echo "Fehler: Repository konnte nicht vorbereitet werden: $REPO_DIR"
  exit 1
fi

if [[ "$(id -u)" -eq 0 ]]; then
  SUDO=""
else
  SUDO="sudo"
fi

command -v git >/dev/null || { echo "git fehlt."; exit 1; }
command -v python3 >/dev/null || { echo "python3 fehlt."; exit 1; }

cd "$REPO_DIR"

echo "==> Python-Version prüfen"
python3 - <<'PY'
import sys
if sys.version_info < (3, 11):
    raise SystemExit("Python >= 3.11 wird benötigt. Auf älteren DietPi-Versionen bitte zuerst Python 3.11+ installieren.")
print(sys.version)
PY

echo "==> Repository aktualisieren"
if [[ "${PT_NO_PULL:-0}" != "1" && "${PT_BOOTSTRAPPED:-0}" != "1" ]]; then
  git pull --ff-only
fi

echo "==> Systempakete installieren"
if command -v apt-get >/dev/null; then
  $SUDO apt-get update
  $SUDO apt-get install -y python3-venv python3-dev build-essential libsndfile1 ffmpeg libgl1 libglib2.0-0
fi

echo "==> Dienstbenutzer vorbereiten"
if ! id "$INSTALL_USER" >/dev/null 2>&1; then
  $SUDO useradd --system --create-home --home-dir /var/lib/paper-tunes --shell /usr/sbin/nologin "$INSTALL_USER"
fi

$SUDO chown -R "$INSTALL_USER":"$INSTALL_USER" "$REPO_DIR"

echo "==> Virtuelle Umgebung erstellen"
if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  python3 -m venv "$VENV_DIR"
fi
"$VENV_DIR/bin/python" -m pip install --upgrade pip setuptools wheel
"$VENV_DIR/bin/pip" install -e .

mkdir -p "$REPO_DIR/runtime"
$SUDO chown -R "$INSTALL_USER":"$INSTALL_USER" "$REPO_DIR/runtime"

if [[ ! -f "$ENV_FILE" ]]; then
  cp .env.example "$ENV_FILE"
fi
chmod 600 "$ENV_FILE"
$SUDO chown "$INSTALL_USER":"$INSTALL_USER" "$ENV_FILE"

echo "==> Standard-Test-WAV erzeugen"
"$VENV_DIR/bin/python" scripts/generate_test_wav.py runtime/test.wav
$SUDO chown "$INSTALL_USER":"$INSTALL_USER" runtime/test.wav

SERVICE_PATH="/etc/systemd/system/${SERVICE_NAME}.service"
echo "==> systemd-Service installieren"
$SUDO tee "$SERVICE_PATH" >/dev/null <<EOF
[Unit]
Description=Paper Tunes Telegram Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$INSTALL_USER
WorkingDirectory=$REPO_DIR
EnvironmentFile=$ENV_FILE
ExecStart=$VENV_DIR/bin/paper-tunes-bot
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=false
ReadWritePaths=$REPO_DIR/runtime

[Install]
WantedBy=multi-user.target
EOF

$SUDO systemctl daemon-reload
$SUDO systemctl enable "$SERVICE_NAME"

if grep -q '^PT_TELEGRAM_BOT_TOKEN=123456789:REPLACE_ME' "$ENV_FILE"; then
  echo
  echo "Installation vorbereitet, Bot noch nicht gestartet."
  echo "Token eintragen:"
  echo "  nano $ENV_FILE"
  echo "Danach:"
  echo "  sudo systemctl start $SERVICE_NAME"
else
  $SUDO systemctl restart "$SERVICE_NAME"
  echo "==> Bot gestartet"
fi

echo
echo "Fertig."
echo "Repo:       $REPO_DIR"
echo "Test-WAV:   $REPO_DIR/runtime/test.wav"
echo "Service:    sudo systemctl status $SERVICE_NAME"
echo "Logs:       journalctl -u $SERVICE_NAME -f"
