#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_dev_runtime.sh"

cd "$(project_root)"
require_nvm
activate_node_toolchain

WEB_PORT="${WEB_PORT:-3000}"
WEB_URL="http://localhost:${WEB_PORT}"

if port_is_in_use "$WEB_PORT"; then
  print_port_conflict "$WEB_PORT" "Frontend" "$WEB_URL"
  echo "Stop the existing listener before running pnpm open:web." >&2
  exit 1
fi

exec pnpm --filter @limitboard/web dev
