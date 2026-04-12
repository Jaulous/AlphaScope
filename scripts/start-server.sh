#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_dev_runtime.sh"

cd "$(project_root)"
require_nvm
require_python_venv
activate_node_toolchain
activate_python_venv

SERVER_PORT="${SERVER_PORT:-8000}"
SERVER_URL="http://localhost:${SERVER_PORT}/api/health"

if port_is_in_use "$SERVER_PORT"; then
  print_port_conflict "$SERVER_PORT" "Backend" "$SERVER_URL"
  echo "Stop the existing listener before running pnpm dev." >&2
  exit 1
fi

exec pnpm --filter @limitboard/server dev
