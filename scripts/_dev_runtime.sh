#!/usr/bin/env bash

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

project_root() {
  printf '%s\n' "$ROOT_DIR"
}

require_nvm() {
  export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"

  if [ ! -s "$NVM_DIR/nvm.sh" ]; then
    echo "Missing nvm bootstrap at $NVM_DIR/nvm.sh" >&2
    exit 1
  fi
}

require_python_venv() {
  if [ ! -f "$ROOT_DIR/.venv/bin/activate" ]; then
    echo "Missing Python virtualenv at .venv/bin/activate" >&2
    echo "Run: python3 -m venv .venv && source .venv/bin/activate && pip install -e packages/quant-core -e apps/server" >&2
    exit 1
  fi
}

activate_node_toolchain() {
  # shellcheck disable=SC1090
  . "$NVM_DIR/nvm.sh"
  nvm use >/dev/null
  corepack enable >/dev/null
}

activate_python_venv() {
  # shellcheck disable=SC1091
  . "$ROOT_DIR/.venv/bin/activate"
}

port_listener_info() {
  local port="$1"
  lsof -iTCP:"$port" -sTCP:LISTEN -n -P 2>/dev/null || true
}

port_is_in_use() {
  local port="$1"
  lsof -tiTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
}

print_port_conflict() {
  local port="$1"
  local label="$2"
  local reuse_url="$3"

  echo "$label port $port is already in use." >&2
  echo "Reuse: $reuse_url" >&2
  echo "Current listener:" >&2
  port_listener_info "$port" >&2
}
