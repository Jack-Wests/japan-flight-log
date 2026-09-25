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

  # uv (preinstalled on Claude's cloud machines) builds this in a few seconds;
  # plain pip takes ~30s, which is as long as Claude Code waits for an MCP
  # server to start, so every fresh session used to time out on first launch.
  local uv=""
  uv="$(command -v uv || true)"
  [[ -z "$uv" && -x "${HOME}/.local/bin/uv" ]] && uv="${HOME}/.local/bin/uv"

  if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    log "creating isolated Python environment"
    rm -rf "$VENV_DIR"
    if [[ -n "$uv" ]]; then
      "$uv" venv --quiet --python "$(command -v python3)" "$VENV_DIR" >&2
    else
      python3 -m venv "$VENV_DIR" >&2
    fi
  fi

  if ! "$VENV_DIR/bin/python" -c 'import fastmcp, curl_cffi, typeguard, orjson' >/dev/null 2>&1; then
    log "installing MCP Python dependencies"
    if [[ -n "$uv" ]]; then
      "$uv" pip install --quiet --python "$VENV_DIR/bin/python" \
        -r "$MCP_DIR/requirements.txt" >&2
    else
      "$VENV_DIR/bin/python" -m pip install \
        --disable-pip-version-check \
        --quiet \
        -r "$MCP_DIR/requirements.txt" >&2
    fi
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
