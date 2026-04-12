#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_dev_runtime.sh"

cd "$(project_root)"
require_nvm
require_python_venv
activate_node_toolchain
activate_python_venv

SERVER_PORT="${SERVER_PORT:-8000}"
WEB_PORT="${WEB_PORT:-3000}"
SERVER_URL="http://localhost:${SERVER_PORT}/api/health"
WEB_URL="http://localhost:${WEB_PORT}"

server_busy=0
web_busy=0

if port_is_in_use "$SERVER_PORT"; then
  server_busy=1
fi

if port_is_in_use "$WEB_PORT"; then
  web_busy=1
fi

if [ "$server_busy" -eq 1 ] && [ "$web_busy" -eq 1 ]; then
  echo "AlphaScope already appears to be running." >&2
  echo "Frontend: $WEB_URL" >&2
  echo "Backend: $SERVER_URL" >&2
  echo "Current frontend listener:" >&2
  port_listener_info "$WEB_PORT" >&2
  echo "Current backend listener:" >&2
  port_listener_info "$SERVER_PORT" >&2
  exit 0
fi

if [ "$server_busy" -eq 1 ]; then
  print_port_conflict "$SERVER_PORT" "Backend" "$SERVER_URL"
  echo "Free port $SERVER_PORT or stop the existing backend before running pnpm start:project." >&2
  exit 1
fi

if [ "$web_busy" -eq 1 ]; then
  print_port_conflict "$WEB_PORT" "Frontend" "$WEB_URL"
  echo "Free port $WEB_PORT or stop the existing frontend before running pnpm start:project." >&2
  exit 1
fi

exec pnpm run dev:raw
