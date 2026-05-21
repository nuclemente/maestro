#!/usr/bin/env bash
# Maestro — sobe backend (uvicorn) + frontend (vite) em background.
# Ctrl+C derruba ambos. Logs em logs/ e PIDs em .run/.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p "$ROOT_DIR/.run" "$ROOT_DIR/logs"

c_blue=$'\033[34m'; c_green=$'\033[32m'; c_yellow=$'\033[33m'; c_reset=$'\033[0m'
say() { printf "%s[maestro]%s %s\n" "$c_blue" "$c_reset" "$*"; }

[ -d "$ROOT_DIR/.venv" ] || { echo "Rode bin/setup.sh primeiro." >&2; exit 1; }
# shellcheck disable=SC1091
source "$ROOT_DIR/.venv/bin/activate"

# Carrega .env de forma defensiva (sem `export` em comentários/linhas vazias)
if [ -f "$ROOT_DIR/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env"
  set +a
fi

BACKEND_PORT="${MAESTRO_BACKEND_PORT:-8001}"
FRONTEND_PORT="${MAESTRO_FRONTEND_PORT:-5173}"

cleanup() {
  say "Encerrando processos..."
  if [ -f "$ROOT_DIR/.run/backend.pid" ]; then
    kill "$(cat "$ROOT_DIR/.run/backend.pid")" 2>/dev/null || true
    rm -f "$ROOT_DIR/.run/backend.pid"
  fi
  if [ -f "$ROOT_DIR/.run/frontend.pid" ]; then
    kill "$(cat "$ROOT_DIR/.run/frontend.pid")" 2>/dev/null || true
    rm -f "$ROOT_DIR/.run/frontend.pid"
  fi
}
trap cleanup EXIT INT TERM

say "Subindo backend em :$BACKEND_PORT..."
(cd "$ROOT_DIR/backend" && uvicorn app.main:app --host 127.0.0.1 --port "$BACKEND_PORT" --reload) \
  >"$ROOT_DIR/logs/backend.log" 2>&1 &
echo $! >"$ROOT_DIR/.run/backend.pid"

say "Subindo frontend em :$FRONTEND_PORT..."
(cd "$ROOT_DIR/frontend" && npm run dev -- --port "$FRONTEND_PORT") \
  >"$ROOT_DIR/logs/frontend.log" 2>&1 &
echo $! >"$ROOT_DIR/.run/frontend.pid"

printf "%s[ok]%s     backend → http://127.0.0.1:%s\n" "$c_green" "$c_reset" "$BACKEND_PORT"
printf "%s[ok]%s     frontend → http://127.0.0.1:%s\n" "$c_green" "$c_reset" "$FRONTEND_PORT"
printf "%s[hint]%s   tail -f logs/backend.log logs/frontend.log\n" "$c_yellow" "$c_reset"

wait
