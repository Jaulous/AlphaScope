#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"

if [ ! -s "$NVM_DIR/nvm.sh" ]; then
  echo "Missing nvm bootstrap at $NVM_DIR/nvm.sh" >&2
  exit 1
fi

if [ ! -f ".venv/bin/activate" ]; then
  echo "Missing Python virtualenv at .venv/bin/activate" >&2
  echo "Run: python3 -m venv .venv && source .venv/bin/activate && pip install -e packages/quant-core -e apps/server" >&2
  exit 1
fi

# shellcheck disable=SC1090
. "$NVM_DIR/nvm.sh"
nvm use >/dev/null
corepack enable >/dev/null

# shellcheck disable=SC1091
. ".venv/bin/activate"

exec pnpm --filter @limitboard/server dev
