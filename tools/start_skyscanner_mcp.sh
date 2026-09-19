#!/usr/bin/env bash
set -euo pipefail

# Launch the vendored Skyscanner MCP copy committed with this repo.
# Only Python packages are installed at runtime; no git clone or submodule work
# is needed in a Claude Routine session.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
MCP_DIR="${PROJECT_ROOT}/vendor/mcp-skyscanner"
CACHE_BASE="${XDG_CACHE_HOME:-${HOME}/.cache}/japan-flight-log/skyscanner-mcp"
VENV_DIR="${CACHE_BASE}/venv"

log() {
  printf '[skyscanner-mcp] %s\n' "$*" >&2
}

ensure_venv() {
  mkdir -p "$CACHE_BASE"

  if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    log "creating isolated Python environment"
    rm -rf "$VENV_DIR"
    python3 -m venv "$VENV_DIR" >&2
  fi

  if ! "$VENV_DIR/bin/python" -c 'import fastmcp, curl_cffi, typeguard, orjson' >/dev/null 2>&1; then
    log "installing MCP Python dependencies"
    "$VENV_DIR/bin/python" -m pip install \
      --disable-pip-version-check \
      --quiet \
      -r "$MCP_DIR/requirements.txt" >&2
  fi
}

ensure_venv

if [[ "${1:-}" == "--check" ]]; then
  "$VENV_DIR/bin/python" -m py_compile \
    "$MCP_DIR/mcp_server.py" \
    "$MCP_DIR/vendor/skyscanner/skyscanner/"*.py
  printf 'Skyscanner MCP local copy OK\n'
  exit 0
fi

exec "$VENV_DIR/bin/python" "$MCP_DIR/mcp_server.py"
