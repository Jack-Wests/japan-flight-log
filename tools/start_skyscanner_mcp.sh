#!/usr/bin/env bash
set -euo pipefail

# Self-contained launcher for the project-scoped Skyscanner MCP server.
# Third-party code and its Python environment live outside the repository.
# Keep all setup chatter on stderr: stdout belongs to the MCP stdio protocol.

UPSTREAM_REPO="https://github.com/shadyvb/mcp-skyscanner.git"
UPSTREAM_COMMIT="331352f41dc2bd3623680a91889c67822c3a96e6"
CACHE_BASE="${XDG_CACHE_HOME:-${HOME}/.cache}/japan-flight-log/skyscanner-mcp"
MCP_DIR="${CACHE_BASE}/source"
VENV_DIR="${CACHE_BASE}/venv"

log() {
  printf '[skyscanner-mcp] %s\n' "$*" >&2
}

ensure_source() {
  mkdir -p "$CACHE_BASE"

  if [[ ! -d "$MCP_DIR/.git" ]]; then
    log "cloning pinned MCP source"
    rm -rf "$MCP_DIR"
    git clone --quiet --recursive "$UPSTREAM_REPO" "$MCP_DIR" >&2
  fi

  local current=""
  current="$(git -C "$MCP_DIR" rev-parse HEAD 2>/dev/null || true)"
  if [[ "$current" != "$UPSTREAM_COMMIT" ]]; then
    log "checking out pinned MCP commit ${UPSTREAM_COMMIT:0:12}"
    git -C "$MCP_DIR" fetch --quiet origin "$UPSTREAM_COMMIT" >&2
    git -C "$MCP_DIR" checkout --quiet --detach "$UPSTREAM_COMMIT" >&2
  fi

  # The MCP repository itself vendors the reverse-engineered Skyscanner client
  # as a git submodule, so recursive initialisation is required.
  git -C "$MCP_DIR" submodule update --init --recursive --quiet >&2
}

ensure_venv() {
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

ensure_source
ensure_venv

if [[ "${1:-}" == "--check" ]]; then
  "$VENV_DIR/bin/python" - <<'PY'
import importlib.util

for package in ("fastmcp", "curl_cffi", "typeguard", "orjson"):
    if importlib.util.find_spec(package) is None:
        raise SystemExit(f"missing dependency: {package}")

print("Skyscanner MCP bootstrap OK")
PY
  exit 0
fi

exec "$VENV_DIR/bin/python" "$MCP_DIR/mcp_server.py"
