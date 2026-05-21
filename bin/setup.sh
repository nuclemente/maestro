#!/usr/bin/env bash
# Maestro — setup do projeto base.
# Idempotente: pode ser rodado várias vezes sem efeitos colaterais.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

c_blue=$'\033[34m'; c_green=$'\033[32m'; c_yellow=$'\033[33m'; c_red=$'\033[31m'; c_reset=$'\033[0m'
say()  { printf "%s[maestro]%s %s\n" "$c_blue"  "$c_reset" "$*"; }
ok()   { printf "%s[ok]%s     %s\n" "$c_green" "$c_reset" "$*"; }
warn() { printf "%s[warn]%s   %s\n" "$c_yellow""$c_reset" "$*"; }
fail() { printf "%s[fail]%s   %s\n" "$c_red"   "$c_reset" "$*" >&2; exit 1; }

# ───────────────────────── Pré-requisitos ─────────────────────────
say "Verificando pré-requisitos..."

command -v python3 >/dev/null || fail "python3 não encontrado."
PY_VERSION=$(python3 -c 'import sys; print("{}.{}".format(sys.version_info.major, sys.version_info.minor))')
PY_MAJOR=${PY_VERSION%%.*}
PY_MINOR=${PY_VERSION##*.}
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 13 ]; }; then
  fail "Python 3.13+ necessário (encontrado: $PY_VERSION)."
fi
ok "Python $PY_VERSION"

command -v node >/dev/null || fail "node não encontrado."
NODE_MAJOR=$(node -p "process.versions.node.split('.')[0]")
if [ "$NODE_MAJOR" -lt 20 ]; then
  fail "Node 20+ necessário (encontrado: $(node -v))."
fi
ok "Node $(node -v)"

command -v claude >/dev/null \
  || warn "claude CLI não encontrado no PATH — instale antes de rodar skills/agents."

# ───────────────────────── .env / config.yaml ─────────────────────────
if [ ! -f "$ROOT_DIR/.env" ]; then
  cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
  ok ".env criado a partir de .env.example"
else
  ok ".env já existe (mantido)"
fi

if [ ! -f "$ROOT_DIR/config.yaml" ]; then
  fail "config.yaml ausente — esperado em $ROOT_DIR/config.yaml"
fi
ok "config.yaml encontrado"

# ───────────────────────── Backend (venv) ─────────────────────────
say "Instalando backend..."
if [ ! -d "$ROOT_DIR/.venv" ]; then
  python3 -m venv "$ROOT_DIR/.venv"
  ok "venv criada em .venv"
fi

# shellcheck disable=SC1091
source "$ROOT_DIR/.venv/bin/activate"

# Forçamos o PyPI público — este projeto usa apenas bibliotecas open-source e
# não depende de índices corporativos (que podem estar com creds expiradas).
PIP_INDEX="${MAESTRO_PIP_INDEX_URL:-https://pypi.org/simple/}"
pip install --quiet --upgrade --index-url "$PIP_INDEX" pip
pip install --quiet --index-url "$PIP_INDEX" -e "$ROOT_DIR/backend[dev]"
ok "Dependências Python instaladas (index: $PIP_INDEX)"

# ───────────────────────── Migrations ─────────────────────────
mkdir -p "$ROOT_DIR/data"
say "Rodando migrations (alembic upgrade head)..."
(cd "$ROOT_DIR/backend" && alembic upgrade head) >/dev/null
ok "Migrations aplicadas (sem versões na base)"

# ───────────────────────── Frontend ─────────────────────────
say "Instalando frontend..."
(cd "$ROOT_DIR/frontend" && npm ci --no-audit --no-fund --silent)
ok "Dependências node instaladas"

# ───────────────────────── Sanity tests ─────────────────────────
say "Rodando testes básicos..."
(cd "$ROOT_DIR/backend" && pytest -q) || warn "Testes do backend falharam"
(cd "$ROOT_DIR/frontend" && npm test --silent) || warn "Testes do frontend falharam"

ok "Setup completo. Próximo passo: bin/start.sh"
