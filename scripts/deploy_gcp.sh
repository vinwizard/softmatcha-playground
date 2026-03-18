#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${HOME}/softmatcha-playground"
APP_SERVICE="softmatcha-playground"

cd "${APP_DIR}"

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

sudo cp deploy/caddy/Caddyfile /etc/caddy/Caddyfile
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl restart caddy

if systemctl list-unit-files | grep -q "^${APP_SERVICE}\.service"; then
  sudo systemctl restart "${APP_SERVICE}"
  sudo systemctl status "${APP_SERVICE}" --no-pager
else
  cat <<'EOF'
systemd service not found: softmatcha-playground.service

If you are running manually, use:

  cd ~/softmatcha-playground
  source .venv/bin/activate
  export BACKEND_MODE=softmatcha
  export HOST=127.0.0.1
  export PORT=8000
  export CORPUS_STORAGE_DIR=~/softmatcha-playground/data/corpora
  export SOFTMATCHA_PROJECT_DIR=~/softmatcha2
  export SOFTMATCHA_INDEX_DIR=corpus_index
  export SOFTMATCHA_INDEX_BUILD_CMD='uv run softmatcha-index'
  export SOFTMATCHA_SEARCH_CMD='uv run softmatcha-search'
  export SOFTMATCHA_EXACT_CMD='uv run softmatcha-exact'
  export SOFTMATCHA_INDEX_FLAG=--index
  export SOFTMATCHA_COMMAND_TIMEOUT=300
  uvicorn app.main:app --host 127.0.0.1 --port 8000

EOF
fi

sudo systemctl status caddy --no-pager

echo
echo "Health check:"
curl http://127.0.0.1:8000/health || true
